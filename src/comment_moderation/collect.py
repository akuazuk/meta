"""Сбор комментариев Instagram + Facebook: органика и реклама."""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from typing import Any

import requests

MSK = timezone(timedelta(hours=3))
DOCTORS = (
    ("Яровой", ("яров",)),
    ("Казак", ("казак",)),
    ("Осипенко", ("осипенк", "дарья осип")),
    ("Луговская", ("луговск",)),
    ("Мытник", ("мытник",)),
    ("Баценко", ("баценк",)),
    ("Школьник", ("школьник",)),
    ("Чернявская", ("чернявск",)),
    ("Богдашич", ("богдашич",)),
    ("Орловский", ("орловск",)),
)


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    s = value.strip().replace("Z", "+00:00")
    if re.search(r"[+-]\d{4}$", s):
        s = s[:-5] + s[-5:-2] + ":" + s[-2:]
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(MSK)


def doctor_from(name: str, caption: str) -> str:
    blob = f"{name} {caption}".lower()
    for label, keys in DOCTORS:
        if any(k in blob for k in keys):
            return label
    return ""


class Graph:
    def __init__(self, token: str, page_token: str, version: str = "v25.0"):
        self.user_token = token
        self.page_token = page_token
        self.base = f"https://graph.facebook.com/{version}"
        self.session = requests.Session()

    def get(self, path: str, token: str | None = None, **params: Any) -> dict:
        params["access_token"] = token or self.page_token
        url = f"{self.base}/{path.lstrip('/')}" if path else self.base
        r = self.session.get(url, params=params, timeout=45)
        try:
            data = r.json()
        except Exception:
            data = {"error": {"message": r.text[:300], "code": r.status_code}}
        if r.status_code >= 400 and "error" not in data:
            data = {"error": {"message": str(data), "code": r.status_code}}
        return data

    def delete(self, path: str) -> dict:
        r = self.session.delete(
            f"{self.base}/{path.lstrip('/')}",
            params={"access_token": self.page_token},
            timeout=45,
        )
        try:
            return {"http": r.status_code, **r.json()}
        except Exception:
            return {"http": r.status_code, "raw": r.text[:300]}

    def hide_fb(self, comment_id: str, hidden: bool = True) -> dict:
        r = self.session.post(
            f"{self.base}/{comment_id}",
            params={"access_token": self.page_token, "is_hidden": "true" if hidden else "false"},
            timeout=45,
        )
        try:
            return {"http": r.status_code, **r.json()}
        except Exception:
            return {"http": r.status_code, "raw": r.text[:300]}

    def hide_ig(self, comment_id: str, hidden: bool = True) -> dict:
        params = {"hide": "true" if hidden else "false"}
        last: dict = {}
        for tok in (self.page_token, self.user_token):
            r = self.session.post(
                f"{self.base}/{comment_id}",
                params={**params, "access_token": tok},
                timeout=45,
            )
            try:
                last = {"http": r.status_code, **r.json()}
            except Exception:
                last = {"http": r.status_code, "raw": r.text[:300]}
            if last.get("success") is True:
                return last
        return last

    def hide_comment(self, item: dict, hidden: bool = True) -> dict:
        cid = item["comment_id"]
        if item.get("platform") == "Instagram":
            return self.hide_ig(cid, hidden=hidden)
        return self.hide_fb(cid, hidden=hidden)


def page_token(g: Graph, page_id: str) -> str:
    data = g.get(page_id, token=g.user_token, fields="access_token")
    tok = data.get("access_token")
    if not tok:
        raise RuntimeError(f"Не удалось взять Page token: {data}")
    return tok


def _paged(g: Graph, path: str, token: str, **params: Any) -> list[dict]:
    out: list[dict] = []
    data = g.get(path, token=token, **params)
    out.extend(data.get("data") or [])
    nxt = (data.get("paging") or {}).get("next")
    while nxt and len(out) < 800:
        data = g.session.get(nxt, timeout=45).json()
        out.extend(data.get("data") or [])
        nxt = (data.get("paging") or {}).get("next")
    return out


def iter_ads(g: Graph, act_id: str) -> list[dict]:
    act = act_id if act_id.startswith("act_") else f"act_{act_id}"
    return _paged(
        g,
        f"{act}/ads",
        g.user_token,
        fields=(
            "id,name,effective_status,campaign{id,name},adset{id,name},"
            "creative{effective_instagram_media_id,instagram_permalink_url,"
            "effective_object_story_id,title,body}"
        ),
        limit=100,
    )


def iter_ig_media(g: Graph, ig_user_id: str, limit: int = 100) -> list[dict]:
    rows = _paged(
        g,
        f"{ig_user_id}/media",
        g.page_token,
        fields="id,caption,permalink,timestamp,comments_count,media_type,like_count",
        limit=min(limit, 100),
    )
    return rows[:limit]


def _objects(g: Graph, ids: list[str], fields: str, token: str | None = None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    clean = [str(i) for i in ids if i]
    tok = token or g.page_token
    for i in range(0, len(clean), 40):
        chunk = clean[i : i + 40]
        data = g.get("", token=tok, ids=",".join(chunk), fields=fields)
        if data.get("error"):
            continue
        for key, val in data.items():
            if key == "error" or not isinstance(val, dict):
                continue
            out[str(val.get("id") or key)] = val
    return out


def _follow_next(g: Graph, paging: dict | None, rows: list[dict], cap: int = 400) -> list[dict]:
    nxt = (paging or {}).get("next")
    while nxt and len(rows) < cap:
        data = g.session.get(nxt, timeout=45).json()
        rows.extend(data.get("data") or [])
        nxt = (data.get("paging") or {}).get("next")
    return rows


def ig_replies(g: Graph, comment_id: str) -> list[dict]:
    if not comment_id:
        return []
    return _paged(
        g,
        f"{comment_id}/replies",
        g.page_token,
        fields="id,text,timestamp,username,hidden,like_count",
        limit=100,
    )


def ig_comments(g: Graph, media_id: str) -> list[dict]:
    rows = _paged(
        g,
        f"{media_id}/comments",
        g.page_token,
        fields=(
            "id,text,timestamp,username,hidden,like_count,"
            "replies{id,text,timestamp,username,hidden,like_count}"
        ),
        limit=100,
    )
    extra: list[dict] = []
    for cm in rows:
        by_id: dict[str, dict] = {}
        for rp in (cm.get("replies") or {}).get("data") or []:
            if rp.get("id"):
                by_id[str(rp["id"])] = rp
        nested = list(by_id.values())
        _follow_next(g, (cm.get("replies") or {}).get("paging"), nested)
        for rp in nested:
            if rp.get("id"):
                by_id[str(rp["id"])] = rp
        for rp in ig_replies(g, str(cm.get("id") or "")):
            if rp.get("id"):
                by_id[str(rp["id"])] = rp
        for rp in by_id.values():
            rp["_parent"] = cm
            extra.append(rp)
    return rows + extra


def fb_comments(g: Graph, story_id: str) -> list[dict]:
    rows = _paged(
        g,
        f"{story_id}/comments",
        g.page_token,
        filter="stream",
        summary="true",
        fields=(
            "id,message,created_time,from,is_hidden,permalink_url,like_count,"
            "comments{id,message,created_time,from,is_hidden,permalink_url,like_count}"
        ),
        limit=100,
    )
    extra: list[dict] = []
    for cm in rows:
        replies = list((cm.get("comments") or {}).get("data") or [])
        _follow_next(g, (cm.get("comments") or {}).get("paging"), replies)
        for rp in replies:
            rp["_parent"] = cm
            extra.append(rp)
    return rows + extra


def _fetch_pool(fn, items: list, workers: int = 6) -> list:
    if not items:
        return []
    if len(items) == 1:
        try:
            return [fn(items[0])]
        except Exception:
            return [None]
    out: list = [None] * len(items)
    with ThreadPoolExecutor(max_workers=min(workers, len(items))) as pool:
        futs = {pool.submit(fn, item): i for i, item in enumerate(items)}
        for fut in as_completed(futs):
            i = futs[fut]
            try:
                out[i] = fut.result()
            except Exception:
                out[i] = None
    return out


def collect(
    g: Graph,
    *,
    act_id: str,
    page_id: str,
    ig_user_id: str,
    since: datetime,
) -> list[dict]:
    """Плоский список комментариев с метаданными поста/объявления."""
    found: list[dict] = []
    seen: set[str] = set()

    ads = iter_ads(g, act_id)
    ad_by_media: dict[str, dict] = {}
    ad_by_story: dict[str, dict] = {}
    for ad in ads:
        cr = ad.get("creative") or {}
        mid = cr.get("effective_instagram_media_id")
        sid = cr.get("effective_object_story_id")
        if mid:
            ad_by_media.setdefault(mid, ad)
        if sid:
            ad_by_story.setdefault(sid, ad)

    organic = iter_ig_media(g, ig_user_id)
    jobs: dict[str, tuple[dict, dict | None, str]] = {}
    for m in organic:
        mid = m.get("id")
        if mid:
            jobs[mid] = (m, ad_by_media.get(mid), "реклама" if mid in ad_by_media else "органика")
    for ad in ads:
        cr = ad.get("creative") or {}
        mid = cr.get("effective_instagram_media_id")
        if not mid or mid in jobs:
            continue
        jobs[mid] = (
            {
                "id": mid,
                "permalink": cr.get("instagram_permalink_url"),
                "caption": cr.get("body") or cr.get("title") or ad.get("name"),
            },
            ad,
            "реклама",
        )

    unknown = [mid for mid, (media, _, _) in jobs.items() if media.get("comments_count") is None]
    if unknown:
        meta = _objects(g, unknown, "id,comments_count,permalink,caption", token=g.user_token)
        for mid, info in meta.items():
            if mid not in jobs:
                continue
            media, ad, channel = jobs[mid]
            media["comments_count"] = info.get("comments_count")
            media["permalink"] = media.get("permalink") or info.get("permalink")
            media["caption"] = media.get("caption") or info.get("caption")
            jobs[mid] = (media, ad, channel)

    ig_targets = []
    for mid, (media, ad, channel) in jobs.items():
        cc = media.get("comments_count")
        if cc is not None and int(cc or 0) == 0:
            continue
        ig_targets.append((media, ad, channel))

    def _ig_job(item):
        media, ad, channel = item
        try:
            return (media, ad, channel, ig_comments(g, media["id"]))
        except Exception:
            return (media, ad, channel, [])

    for pack in _fetch_pool(_ig_job, ig_targets):
        if not pack:
            continue
        media, ad, channel, comments = pack
        mid = media.get("id")
        caption = media.get("caption") or (ad.get("name") if ad else "") or ""
        permalink = media.get("permalink") or ((ad or {}).get("creative") or {}).get("instagram_permalink_url") or ""
        for cm in comments:
            cid = str(cm.get("id") or "")
            if not cid or cid in seen:
                continue
            ts = parse_ts(cm.get("timestamp"))
            if ts and ts < since:
                continue
            seen.add(cid)
            parent = cm.get("_parent") or {}
            from_ = cm.get("from") or {}
            username = cm.get("username") or from_.get("username") or ""
            fio = from_.get("name") or ""
            found.append(
                _row(
                    comment_id=cid,
                    ts=ts,
                    platform="Instagram",
                    channel=channel,
                    ad=ad,
                    caption=caption,
                    permalink=permalink,
                    comment_url=f"{permalink}?comment_id={cid}" if permalink else "",
                    is_reply=bool(parent),
                    parent_text=(parent.get("text") or "")[:240],
                    parent_id=str(parent.get("id") or ""),
                    username=username,
                    fio=fio,
                    user_id=str(from_.get("id") or ""),
                    text=cm.get("text") or "",
                    likes=cm.get("like_count") or 0,
                    hidden=bool(cm.get("hidden")),
                    media_id=mid,
                    story_id=(ad or {}).get("creative", {}).get("effective_object_story_id") if ad else "",
                    collect_source="ig_media",
                )
            )

    # Facebook dark posts + сторис объявлений
    stories: dict[str, dict] = {}
    for ad in ads:
        sid = ((ad.get("creative") or {}).get("effective_object_story_id") or "")
        if sid:
            stories.setdefault(sid, ad)
    if stories:
        smeta = _objects(g, list(stories), "id,comments.summary(true)", token=g.page_token)
        fb_targets = []
        for sid, ad in stories.items():
            total = ((smeta.get(sid) or {}).get("comments") or {}).get("summary", {}).get("total_count")
            if total is not None and int(total or 0) == 0:
                continue
            fb_targets.append((sid, ad, "реклама", ad.get("name") or "", "fb_ad_story"))
    else:
        fb_targets = []

    feed = g.get(
        f"{page_id}/feed",
        fields="id,message,created_time,permalink_url,comments.summary(true)",
        limit=40,
    )
    stories_done = set(stories)
    for post in feed.get("data") or []:
        pid = post.get("id")
        if not pid or pid in stories_done:
            continue
        total = ((post.get("comments") or {}).get("summary") or {}).get("total_count")
        if total is not None and int(total or 0) == 0:
            continue
        fb_targets.append((pid, None, "органика", (post.get("message") or "")[:200], "fb_feed"))

    def _fb_job(item):
        pid, ad, channel, caption, source = item
        try:
            return (pid, ad, channel, caption, source, fb_comments(g, pid))
        except Exception:
            return (pid, ad, channel, caption, source, [])

    for pack in _fetch_pool(_fb_job, fb_targets):
        if not pack:
            continue
        pid, ad, channel, caption, source, comments = pack
        permalink_fallback = ""
        if source == "fb_feed":
            for post in feed.get("data") or []:
                if post.get("id") == pid:
                    permalink_fallback = post.get("permalink_url") or ""
                    break
        for cm in comments:
            cid = str(cm.get("id") or "")
            if not cid or cid in seen:
                continue
            ts = parse_ts(cm.get("created_time"))
            if ts and ts < since:
                continue
            seen.add(cid)
            parent = cm.get("_parent") or {}
            from_ = cm.get("from") or {}
            found.append(
                _row(
                    comment_id=cid,
                    ts=ts,
                    platform="Facebook",
                    channel=channel,
                    ad=ad,
                    caption=caption,
                    permalink=cm.get("permalink_url") or permalink_fallback,
                    comment_url=cm.get("permalink_url") or permalink_fallback,
                    is_reply=bool(parent),
                    parent_text=(parent.get("message") or "")[:240],
                    parent_id=str(parent.get("id") or ""),
                    username="",
                    fio=from_.get("name") or "",
                    user_id=str(from_.get("id") or ""),
                    text=cm.get("message") or "",
                    likes=cm.get("like_count") or 0,
                    hidden=bool(cm.get("is_hidden")),
                    media_id=((ad.get("creative") or {}).get("effective_instagram_media_id") or "") if ad else "",
                    story_id=pid,
                    collect_source=source,
                )
            )

    found.sort(key=lambda r: r["ts"] or datetime(1970, 1, 1, tzinfo=MSK))
    return found


def _row(**kwargs: Any) -> dict:
    ad = kwargs.get("ad")
    campaign = ((ad or {}).get("campaign") or {})
    adset = ((ad or {}).get("adset") or {})
    name = (ad or {}).get("name") or ""
    caption = kwargs.get("caption") or ""
    ts: datetime | None = kwargs.get("ts")
    weekdays = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")
    return {
        "comment_id": kwargs["comment_id"],
        "ts": ts,
        "date": ts.strftime("%Y-%m-%d") if ts else "",
        "time": ts.strftime("%H:%M:%S") if ts else "",
        "weekday": weekdays[ts.weekday()] if ts else "",
        "platform": kwargs["platform"],
        "channel": kwargs["channel"],
        "campaign": campaign.get("name") or "",
        "adset": adset.get("name") or "",
        "ad": name,
        "doctor": doctor_from(name, caption),
        "post_preview": re.sub(r"\s+", " ", caption)[:160],
        "post_url": kwargs.get("permalink") or "",
        "comment_url": kwargs.get("comment_url") or "",
        "is_reply": "да" if kwargs.get("is_reply") else "нет",
        "parent_text": kwargs.get("parent_text") or "",
        "parent_id": kwargs.get("parent_id") or "",
        "username": kwargs.get("username") or "",
        "fio": kwargs.get("fio") or "",
        "user_id": kwargs.get("user_id") or "",
        "text": kwargs.get("text") or "",
        "likes": kwargs.get("likes") or 0,
        "hidden": "да" if kwargs.get("hidden") else "нет",
        "ad_id": (ad or {}).get("id") or "",
        "media_id": kwargs.get("media_id") or "",
        "story_id": kwargs.get("story_id") or "",
        "campaign_id": campaign.get("id") or "",
        "collect_source": kwargs.get("collect_source") or "",
    }
