"""Hourly Meta comment moderation → Google Sheet (akuazuk)."""

from __future__ import annotations

import argparse
import os
import socket
import sys
import time
import uuid
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from comment_moderation.classify import classify
from comment_moderation.collect import Graph, collect, page_token, MSK
from comment_moderation.sheets_report import Report, sheets_service, to_sheet_row

DEFAULT_SHEET = "1LkaVoEZ7hQWR2FL0Iejjviutdte91SLq9rM7W5u80lU"
DEFAULT_SINCE = "2026-09-01"


def load_env() -> None:
    load_dotenv(ROOT / ".env")
    load_dotenv(Path("/opt/kravira-meta-comments/.env"))


def delete_comment(g: Graph, item: dict) -> tuple[str, str]:
    cid = item["comment_id"]
    res = g.delete(cid)
    if res.get("success") is True:
        return "удалён", "deleted"
    hide = g.hide_comment(item)
    if hide.get("success") is True:
        return "скрыт", "hidden after delete failed"
    err = (res.get("error") or {}).get("message") or str(res)[:180]
    return "ошибка удаления", err


def hide_comment(g: Graph, item: dict) -> tuple[str, str]:
    hide = g.hide_comment(item)
    if hide.get("success") is True:
        return "скрыт", "hidden"
    err = (hide.get("error") or {}).get("message") or str(hide)[:180]
    return "ошибка скрытия", err


def apply_verdict(g: Graph, item: dict, verdict, dry_run: bool) -> tuple[str, str, str]:
    """→ (действие в таблице, технический результат, счётчик deleted|hidden|skipped|errors|kept)."""
    if verdict.skip_own:
        return "пропущен (свой)", "", "skipped"
    if dry_run:
        if verdict.should_delete:
            return "к удалению (dry-run)", "", "deleted"
        if verdict.should_hide:
            return "к скрытию (dry-run)", "", "hidden"
        return "оставлен", "", "kept"
    if verdict.should_delete:
        action, result = delete_comment(g, item)
        if action == "удалён":
            return action, result, "deleted"
        if action == "скрыт":
            return action, result, "hidden"
        return action, result, "errors"
    if verdict.should_hide:
        action, result = hide_comment(g, item)
        return action, result, "hidden" if action == "скрыт" else "errors"
    return "оставлен", "", "kept"


def classify_item(item: dict, use_llm: bool = True):
    return classify(
        item["text"],
        username=item["username"] or item["fio"],
        parent_text=item.get("parent_text") or "",
        doctor=item.get("doctor") or "",
        post_preview=item.get("post_preview") or "",
        use_llm=use_llm,
    )


def main() -> int:
    load_env()
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Не удалять, только записать в таблицу")
    p.add_argument("--layout-only", action="store_true", help="Только оформить таблицу, без сбора")
    p.add_argument("--reformat", action="store_true", help="Переоформить таблицу и починить формулы")
    p.add_argument("--rescore", action="store_true", help="Переоценить уже записанные комментарии (Gemini) и скрыть/удалить")
    p.add_argument("--no-llm", action="store_true", help="Только правила, без Gemini")
    p.add_argument("--since", default=os.getenv("COMMENT_SINCE", DEFAULT_SINCE))
    p.add_argument("--sheet-id", default=os.getenv("GOOGLE_SHEETS_ID", DEFAULT_SHEET))
    p.add_argument("--sa", default=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""))
    args = p.parse_args()

    sa = args.sa or str(Path.home() / ".config/mcp-google-sheets/service-account.json")
    if not Path(sa).exists():
        raise SystemExit(f"Нет service account: {sa}")

    svc = sheets_service(sa)
    report = Report(svc, args.sheet_id)
    if args.reformat or args.layout_only:
        report.ensure_layout(force=True)
        print(f"layout ready sheet={args.sheet_id}")
        return 0

    token = os.getenv("META_ACCESS_TOKEN_MRS") or os.getenv("META_ACCESS_TOKEN")
    act = os.getenv("META_AD_ACCOUNT_ID_MRS") or os.getenv("META_AD_ACCOUNT_ID")
    page_id = os.getenv("META_PAGE_ID", "265643990153763")
    ig_id = os.getenv("META_INSTAGRAM_ID", "17841404399569974")
    version = os.getenv("META_GRAPH_API_VERSION") or "v25.0"
    if not token or not act:
        raise SystemExit("Нет META_ACCESS_TOKEN_MRS / META_AD_ACCOUNT_ID_MRS")

    since = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=MSK)
    started = datetime.now(MSK)
    run_id = started.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]

    g = Graph(token, token, version=version)
    g.page_token = page_token(g, page_id)

    report.ensure_layout()
    removed = report.dedup_comments()
    if removed:
        print(f"dedup removed={removed}")
    known_rows = report.comment_rows()
    known = set(known_rows)
    use_llm = not args.no_llm

    t0 = time.monotonic()
    items = collect(g, act_id=act, page_id=page_id, ig_user_id=ig_id, since=since)
    collect_s = time.monotonic() - t0
    checked = datetime.now(MSK)
    FINAL = {"удалён", "скрыт"}
    todo: list[dict] = []
    for item in items:
        cid = item["comment_id"]
        existing = known_rows.get(cid)
        prev_action = existing[1][22] if existing and len(existing[1]) > 22 else ""
        if existing and not args.rescore:
            continue
        if prev_action in FINAL:
            continue
        todo.append(item)

    verdicts: list = []
    for item in todo:
        verdicts.append(classify_item(item, use_llm=use_llm))
    hide_ids = {
        item["comment_id"]
        for item, v in zip(todo, verdicts)
        if v.should_hide or v.should_delete
    }
    bad_authors = {
        ((item.get("post_url") or ""), (item.get("username") or "").strip().lstrip("@").lower())
        for item, v in zip(todo, verdicts)
        if (v.should_hide or v.should_delete) and (item.get("username") or item.get("fio"))
    }

    def _mark_thread_hide(i: int, why: str) -> None:
        v = verdicts[i]
        if v.skip_own or v.should_delete or v.should_hide:
            return
        if v.rating in ("вопрос", "позитив", "шутка"):
            return
        verdicts[i] = replace(
            v,
            should_hide=True,
            rating="намёк" if v.rating in ("нейтральный", "смешанный", "средний") else v.rating,
            score=min(v.score, 2),
            tone="ответ в ветке с намёком",
            reason=((v.reason + "; ") if v.reason else "") + why,
        )
        hide_ids.add(todo[i]["comment_id"])

    for i, item in enumerate(todo):
        pid = item.get("parent_id") or ""
        if pid and pid in hide_ids:
            _mark_thread_hide(i, "ответ в негативной ветке")
        key = (
            (item.get("post_url") or ""),
            (item.get("username") or item.get("fio") or "").strip().lstrip("@").lower(),
        )
        if key in bad_authors and key[1]:
            _mark_thread_hide(i, "тот же автор в посте с намёком")

    rows = []
    deleted = skipped = errors = hidden = 0
    for item, verdict in zip(todo, verdicts):
        cid = item["comment_id"]
        existing = known_rows.get(cid)
        action, delete_result, bucket = apply_verdict(g, item, verdict, args.dry_run)
        note = ""
        if bucket == "deleted":
            deleted += 1
        elif bucket == "hidden":
            hidden += 1
        elif bucket == "skipped":
            skipped += 1
        elif bucket == "errors":
            errors += 1
        if delete_result == "hidden after delete failed":
            note = "Graph DELETE не прошёл, комментарий скрыт"
        sheet_row = to_sheet_row(
            item,
            verdict,
            checked=checked,
            run_id=run_id,
            action=action,
            delete_result=delete_result,
            note=note,
        )
        if existing:
            report.patch_comment_row(existing[0], sheet_row)
        else:
            rows.append(sheet_row)
        print(
            f"  {action} [{verdict.source}] {verdict.rating} "
            f"@{item.get('username') or item.get('fio') or '-'} {(item.get('text') or '')[:70]}"
        )

    report.append_comments(rows)
    ended = datetime.now(MSK)
    happened = bool(rows or deleted or hidden or errors or args.rescore)
    if happened:
        report.append_run([
            started.strftime("%Y-%m-%d %H:%M:%S"),
            ended.strftime("%Y-%m-%d %H:%M:%S"),
            run_id,
            len(items),
            len(rows),
            deleted,
            skipped,
            errors,
            socket.gethostname(),
            "dry-run" if args.dry_run else "live",
            f"since={args.since}; known_before={len(known)}; collect_s={collect_s:.0f}; llm={int(use_llm)}; hidden={hidden}; rescore={int(args.rescore)}",
        ])
        log_note = "logged"
    else:
        log_note = "idle, not logged"
    print(
        f"run={run_id} found={len(items)} new={len(rows)} "
        f"deleted={deleted} hidden={hidden} skipped_own={skipped} errors={errors} "
        f"collect_s={collect_s:.0f} llm={int(use_llm)} dry={args.dry_run} {log_note}"
    )
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
