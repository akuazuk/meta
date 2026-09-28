"""Google Sheets: оформление и запись отчёта модерации."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build

MSK = timezone(timedelta(hours=3))

SHEET_COMMENTS = "Комментарии"
SHEET_BY_POST = "По постам"
SHEET_DELETED = "Удалённые"
SHEET_SUMMARY = "Сводка"
SHEET_RUNS = "Прогоны"
SHEET_HELP = "Справка"

HEADERS = [
    "ID комментария",
    "Дата",
    "Время МСК",
    "День недели",
    "Проверено",
    "Платформа",
    "Канал",
    "Кампания",
    "Объявление",
    "Врач / тема",
    "Превью поста",
    "Ссылка на пост",
    "Ссылка на комментарий",
    "Это ответ?",
    "Родительский текст",
    "Username",
    "Текст комментария",
    "Оценка",
    "Балл 1–5",
    "Тон",
    "Категория",
    "Маркеры",
    "Действие",
    "Лайки",
]
GRID_ROWS = 40

# Только светлые заливки + тёмный текст (контраст, без тёмных плашек).
INK = {"red": 0.118, "green": 0.161, "blue": 0.200}  # #1E2933
WHITE = {"red": 1, "green": 1, "blue": 1}
HEAD_BG = {"red": 0.820, "green": 0.941, "blue": 0.902}  # мята
HEAD_FG = {"red": 0.086, "green": 0.275, "blue": 0.239}
SECTION_BG = {"red": 0.741, "green": 0.910, "blue": 0.859}
MINT = {"red": 0.910, "green": 0.973, "blue": 0.949}
TEAL = {"red": 0.620, "green": 0.851, "blue": 0.780}  # вкладка, не заливка текста
TEAL_DARK = HEAD_FG  # совместимость: это цвет текста, не фон
RED = {"red": 0.545, "green": 0.153, "blue": 0.188}
RED_BG = {"red": 1.0, "green": 0.910, "blue": 0.918}
GOLD = {"red": 0.478, "green": 0.318, "blue": 0.027}
GOLD_BG = {"red": 1.0, "green": 0.957, "blue": 0.863}
GREEN = {"red": 0.122, "green": 0.365, "blue": 0.255}
GREEN_BG = {"red": 0.875, "green": 0.965, "blue": 0.890}
BLUE = {"red": 0.098, "green": 0.325, "blue": 0.478}
BLUE_BG = {"red": 0.875, "green": 0.941, "blue": 0.988}
PURPLE = {"red": 0.365, "green": 0.188, "blue": 0.478}
PURPLE_BG = {"red": 0.949, "green": 0.910, "blue": 0.976}
GRAY = {"red": 0.290, "green": 0.333, "blue": 0.388}
ORANGE = {"red": 0.545, "green": 0.275, "blue": 0.063}
ORANGE_BG = {"red": 1.0, "green": 0.941, "blue": 0.863}
PINK = {"red": 0.545, "green": 0.165, "blue": 0.365}
PINK_BG = {"red": 0.996, "green": 0.910, "blue": 0.953}
SKY = {"red": 0.063, "green": 0.365, "blue": 0.545}
SKY_BG = {"red": 0.863, "green": 0.941, "blue": 0.988}
LILAC = PURPLE
LILAC_BG = PURPLE_BG
WEEKEND_BG = {"red": 1.0, "green": 0.953, "blue": 0.890}
SOFT_RED = {"red": 1.0, "green": 0.941, "blue": 0.945}
SOFT_GREEN = {"red": 0.925, "green": 0.976, "blue": 0.937}
SOFT_BLUE = {"red": 0.918, "green": 0.957, "blue": 0.992}
SOFT_GOLD = {"red": 1.0, "green": 0.976, "blue": 0.918}
SOFT_PURPLE = {"red": 0.969, "green": 0.941, "blue": 0.984}
NEUTRAL_BG = {"red": 0.945, "green": 0.953, "blue": 0.965}

# Таблица ru_RU: разделитель аргументов в формулах — точка с запятой.
FS = ";"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def sheets_service(sa_path: str):
    creds = service_account.Credentials.from_service_account_file(sa_path, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def _color(rgb: dict) -> dict:
    return {"red": rgb["red"], "green": rgb["green"], "blue": rgb["blue"]}


def _cell_text(text: str, *, bold=False, size=10, color=None, italic=False) -> dict:
    return {
        "userEnteredValue": {"stringValue": text},
        "userEnteredFormat": {
            "textFormat": {
                "foregroundColor": _color(color or INK),
                "fontSize": size,
                "bold": bold,
                "italic": italic,
                "fontFamily": "Calibri",
            },
            "backgroundColor": _color(HEAD_BG),
            "verticalAlignment": "MIDDLE",
            "horizontalAlignment": "LEFT",
        },
    }


class Report:
    def __init__(self, service, spreadsheet_id: str):
        self.svc = service
        self.sid = spreadsheet_id
        self._meta = None

    def meta(self, refresh: bool = False) -> dict:
        if self._meta is None or refresh:
            self._meta = self.svc.spreadsheets().get(spreadsheetId=self.sid).execute()
        return self._meta

    def sheet_id(self, title: str) -> int | None:
        for sh in self.meta()["sheets"]:
            if sh["properties"]["title"] == title:
                return sh["properties"]["sheetId"]
        return None

    def ensure_layout(self, force: bool = False) -> None:
        existing = {sh["properties"]["title"] for sh in self.meta()["sheets"]}
        requests: list[dict] = []
        # Rename default Sheet1 if still there.
        if "Sheet1" in existing and SHEET_COMMENTS not in existing:
            requests.append({
                "updateSheetProperties": {
                    "properties": {"sheetId": self.sheet_id("Sheet1"), "title": SHEET_COMMENTS},
                    "fields": "title",
                }
            })
            existing.discard("Sheet1")
            existing.add(SHEET_COMMENTS)
        if "Лист1" in existing and SHEET_COMMENTS not in existing:
            requests.append({
                "updateSheetProperties": {
                    "properties": {"sheetId": self.sheet_id("Лист1"), "title": SHEET_COMMENTS},
                    "fields": "title",
                }
            })
            existing.discard("Лист1")
            existing.add(SHEET_COMMENTS)

        tab_colors = {
            SHEET_COMMENTS: TEAL,
            SHEET_BY_POST: SKY_BG,
            SHEET_DELETED: RED_BG,
            SHEET_SUMMARY: GOLD_BG,
            SHEET_RUNS: BLUE_BG,
            SHEET_HELP: NEUTRAL_BG,
        }
        for title in (SHEET_COMMENTS, SHEET_BY_POST, SHEET_DELETED, SHEET_SUMMARY, SHEET_RUNS, SHEET_HELP):
            if title not in existing:
                requests.append({
                    "addSheet": {
                        "properties": {
                            "title": title,
                            "gridProperties": {"frozenRowCount": 1, "frozenColumnCount": 0},
                            "tabColor": _color(tab_colors[title]),
                        }
                    }
                })
        if requests:
            self.svc.spreadsheets().batchUpdate(
                spreadsheetId=self.sid, body={"requests": requests}
            ).execute()
            self.meta(refresh=True)

        if force:
            self._set_locale()
            self._remap_comments()
            self._repair_comment_dates()
        else:
            header = self.svc.spreadsheets().values().get(
                spreadsheetId=self.sid, range=f"'{SHEET_HELP}'!A1"
            ).execute().get("values") or []
            if header and header[0] and header[0][0] == "Справка по журналу":
                return
        self._format_comments()
        self._format_by_post()
        self._format_deleted()
        self._format_summary()
        self._format_runs()
        self._format_help()

    def _set_locale(self) -> None:
        self.svc.spreadsheets().batchUpdate(
            spreadsheetId=self.sid,
            body={"requests": [{
                "updateSpreadsheetProperties": {
                    "properties": {"locale": "ru_RU", "timeZone": "Europe/Minsk"},
                    "fields": "locale,timeZone",
                }
            }]},
        ).execute()
        self.meta(refresh=True)

    def _remap_comments(self) -> None:
        res = self.svc.spreadsheets().values().get(
            spreadsheetId=self.sid,
            range=f"'{SHEET_COMMENTS}'!A1:AZ",
        ).execute()
        rows = res.get("values") or []
        if not rows:
            return
        old_h = rows[0]
        idx = {name: i for i, name in enumerate(old_h)}
        new_rows = [HEADERS]
        for row in rows[1:]:
            if not row or not str(row[0]).strip():
                continue
            new_rows.append([
                (row[idx[h]] if h in idx and idx[h] < len(row) else "")
                for h in HEADERS
            ])
        self.svc.spreadsheets().values().clear(
            spreadsheetId=self.sid, range=f"'{SHEET_COMMENTS}'!A1:AZ1000"
        ).execute()
        self.svc.spreadsheets().values().update(
            spreadsheetId=self.sid,
            range=f"'{SHEET_COMMENTS}'!A1",
            valueInputOption="USER_ENTERED",
            body={"values": new_rows},
        ).execute()

    def _repair_comment_dates(self) -> None:
        res = self.svc.spreadsheets().values().get(
            spreadsheetId=self.sid,
            range=f"'{SHEET_COMMENTS}'!A2:E",
            valueRenderOption="UNFORMATTED_VALUE",
        ).execute()
        rows = res.get("values") or []
        if not rows:
            return
        out = []
        for row in rows:
            row = list(row) + [""] * (5 - len(row))
            out.append([
                _txt(_norm_id(row[0])) if row[0] not in ("", None) else "",
                "'" + _as_date_text(row[1]) if row[1] not in ("", None) else "",
                "'" + _as_time_text(row[2]) if row[2] not in ("", None) else "",
                row[3] if len(row) > 3 else "",
                "'" + _as_dt_text(row[4]) if len(row) > 4 and row[4] not in ("", None) else "",
            ])
        self.svc.spreadsheets().values().update(
            spreadsheetId=self.sid,
            range=f"'{SHEET_COMMENTS}'!A2:E",
            valueInputOption="USER_ENTERED",
            body={"values": out},
        ).execute()

    def existing_comment_ids(self) -> set[str]:
        res = self.svc.spreadsheets().values().get(
            spreadsheetId=self.sid,
            range=f"'{SHEET_COMMENTS}'!A2:A",
            valueRenderOption="UNFORMATTED_VALUE",
        ).execute()
        out = set()
        for r in res.get("values") or []:
            if not r or r[0] in ("", None):
                continue
            out.add(_norm_id(r[0]))
        return out

    def comment_rows(self) -> dict[str, tuple[int, list]]:
        """comment_id → (sheet row number 1-based, values)."""
        res = self.svc.spreadsheets().values().get(
            spreadsheetId=self.sid,
            range=f"'{SHEET_COMMENTS}'!A2:X",
        ).execute()
        out: dict[str, tuple[int, list]] = {}
        for i, row in enumerate(res.get("values") or []):
            if not row:
                continue
            cid = _norm_id(row[0] if row else "")
            if cid:
                out[cid] = (i + 2, list(row) + [""] * (len(HEADERS) - len(row)))
        return out

    def patch_comment_row(self, row_number: int, values: list) -> None:
        self.svc.spreadsheets().values().update(
            spreadsheetId=self.sid,
            range=f"'{SHEET_COMMENTS}'!A{row_number}:X{row_number}",
            valueInputOption="USER_ENTERED",
            body={"values": [values]},
        ).execute()

    def dedup_comments(self) -> int:
        res = self.svc.spreadsheets().values().get(
            spreadsheetId=self.sid,
            range=f"'{SHEET_COMMENTS}'!A2:X",
        ).execute()
        rows = res.get("values") or []
        seen: set[str] = set()
        uniq: list[list[Any]] = []
        for row in rows:
            if not row:
                continue
            cid = _norm_id(row[0] if row else "")
            if not cid or cid in seen:
                continue
            seen.add(cid)
            if row[0] != "" and not str(row[0]).startswith("'"):
                row = list(row) + [""] * (len(HEADERS) - len(row))
                row[0] = "'" + str(row[0]).split(".")[0]
            uniq.append(row)
        if len(uniq) == len(rows):
            return 0
        self.svc.spreadsheets().values().clear(
            spreadsheetId=self.sid, range=f"'{SHEET_COMMENTS}'!A2:X"
        ).execute()
        if uniq:
            self.append_comments(uniq)
        return len(rows) - len(uniq)

    def append_comments(self, rows: list[list[Any]]) -> None:
        if not rows:
            return
        self.svc.spreadsheets().values().append(
            spreadsheetId=self.sid,
            range=f"'{SHEET_COMMENTS}'!A2",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": rows},
        ).execute()

    def append_run(self, row: list[Any]) -> None:
        self.svc.spreadsheets().values().append(
            spreadsheetId=self.sid,
            range=f"'{SHEET_RUNS}'!A2",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        ).execute()

    def _values(self, rng: str, values: list[list[Any]], option: str = "USER_ENTERED") -> None:
        self.svc.spreadsheets().values().update(
            spreadsheetId=self.sid,
            range=rng,
            valueInputOption=option,
            body={"values": values},
        ).execute()

    def _format_comments(self) -> None:
        sid = self.sheet_id(SHEET_COMMENTS)
        n = len(HEADERS)
        last = _col(n)
        meta_sheet = next(s for s in self.meta()["sheets"] if s["properties"]["sheetId"] == sid)
        prep: list[dict] = []
        if meta_sheet.get("basicFilter"):
            prep.append({"clearBasicFilter": {"sheetId": sid}})
        for i in range(len(meta_sheet.get("conditionalFormats") or []) - 1, -1, -1):
            prep.append({"deleteConditionalFormatRule": {"sheetId": sid, "index": i}})
        for br in meta_sheet.get("bandedRanges") or []:
            prep.append({"deleteBanding": {"bandedRangeId": br["bandedRangeId"]}})
        if prep:
            self.svc.spreadsheets().batchUpdate(spreadsheetId=self.sid, body={"requests": prep}).execute()
            self.meta(refresh=True)
        self._fit_grid(sid, cols=n, rows=GRID_ROWS)
        widths = [
            140, 100, 90, 70, 150, 110, 90, 160, 140, 120, 200, 180, 180,
            80, 180, 140, 320, 110, 70, 160, 120, 140, 110, 60,
        ]
        requests = [
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sid,
                        "gridProperties": {"frozenRowCount": 1, "frozenColumnCount": 0},
                        "tabColor": _color(TEAL),
                    },
                    "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount,tabColor",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": n},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": _color(HEAD_BG),
                            "textFormat": {
                                "foregroundColor": _color(HEAD_FG),
                                "fontSize": 10,
                                "bold": True,
                                "fontFamily": "Calibri",
                            },
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE",
                            "wrapStrategy": "WRAP",
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)",
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 0, "endIndex": 1},
                    "properties": {"pixelSize": 42},
                    "fields": "pixelSize",
                }
            },
            {
                "setBasicFilter": {
                    "filter": {
                        "range": {"sheetId": sid, "startRowIndex": 0, "startColumnIndex": 0, "endColumnIndex": n}
                    }
                }
            },
        ]
        meta_sheet = next(s for s in self.meta()["sheets"] if s["properties"]["sheetId"] == sid)
        if meta_sheet.get("basicFilter"):
            requests.insert(0, {"clearBasicFilter": {"sheetId": sid}})
        for i, w in enumerate(widths):
            requests.append({
                "updateDimensionProperties": {
                    "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
                    "properties": {"pixelSize": w},
                    "fields": "pixelSize",
                }
            })
        # Conditional formatting — wipe old first, then paint by content.
        meta_sheet = next(s for s in self.meta()["sheets"] if s["properties"]["sheetId"] == sid)
        n_rules = len(meta_sheet.get("conditionalFormats") or [])
        for i in range(n_rules - 1, -1, -1):
            requests.append({"deleteConditionalFormatRule": {"sheetId": sid, "index": i}})
        for br in meta_sheet.get("bandedRanges") or []:
            requests.append({"deleteBanding": {"bandedRangeId": br["bandedRangeId"]}})
        requests.append({
            "updateCells": {
                "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": n},
                "rows": [{"values": [{"userEnteredValue": {"stringValue": h}} for h in HEADERS]}],
                "fields": "userEnteredValue",
            }
        })
        requests.append(_wipe_body(sid, GRID_ROWS, n))
        prefix = [r for r in requests if "deleteConditionalFormatRule" in r or "deleteBanding" in r]
        rest = [r for r in requests if "deleteConditionalFormatRule" not in r and "deleteBanding" not in r]
        requests = prefix + rest
        # Целая строка по оценке — только если в строке есть комментарий.
        row_tints = [
            ('=AND($A2<>"";$R2="оскорбление")', SOFT_RED, RED),
            ('=AND($A2<>"";$R2="негатив")', SOFT_RED, RED),
            ('=AND($A2<>"";$R2="спам")', SOFT_PURPLE, PURPLE),
            ('=AND($A2<>"";$R2="намёк")', SOFT_GOLD, GOLD),
            ('=AND($A2<>"";$R2="смешанный")', SOFT_GOLD, GOLD),
            ('=AND($A2<>"";$R2="средний")', SOFT_GOLD, GOLD),
            ('=AND($A2<>"";$R2="шутка")', SOFT_BLUE, BLUE),
            ('=AND($A2<>"";$R2="вопрос")', SOFT_BLUE, BLUE),
            ('=AND($A2<>"";$R2="позитив")', SOFT_GREEN, GREEN),
            ('=AND($A2<>"";$R2="свой")', MINT, HEAD_FG),
        ]
        for formula, bg, fg in row_tints:
            requests.append(_cf_custom(sid, formula, bg, fg, 0, n, GRID_ROWS))
        for text, bg, fg in [
            ("оскорбление", RED_BG, RED),
            ("негатив", RED_BG, RED),
            ("спам", PURPLE_BG, PURPLE),
            ("намёк", GOLD_BG, GOLD),
            ("смешанный", GOLD_BG, GOLD),
            ("средний", GOLD_BG, GOLD),
            ("шутка", BLUE_BG, BLUE),
            ("вопрос", BLUE_BG, BLUE),
            ("позитив", GREEN_BG, GREEN),
            ("нейтральный", NEUTRAL_BG, GRAY),
            ("свой", MINT, HEAD_FG),
        ]:
            requests.append(_cf_eq(sid, 17, 18, text, bg, fg, GRID_ROWS))
        for text, bg, fg in [
            ("Instagram", PINK_BG, PINK),
            ("Facebook", SKY_BG, SKY),
        ]:
            requests.append(_cf_eq(sid, 5, 6, text, bg, fg, GRID_ROWS))
        for text, bg, fg in [
            ("реклама", ORANGE_BG, ORANGE),
            ("органика", MINT, HEAD_FG),
        ]:
            requests.append(_cf_eq(sid, 6, 7, text, bg, fg, GRID_ROWS))
        for text, bg, fg in [
            ("да", GOLD_BG, GOLD),
            ("нет", NEUTRAL_BG, GRAY),
        ]:
            requests.append(_cf_eq(sid, 13, 14, text, bg, fg, GRID_ROWS))
        for text, bg, fg in [
            ("удалён", RED_BG, RED),
            ("скрыт", ORANGE_BG, ORANGE),
            ("ошибка удаления", RED_BG, RED),
            ("оставлен", GREEN_BG, GREEN),
            ("пропущен (свой)", MINT, HEAD_FG),
            ("к удалению (dry-run)", GOLD_BG, GOLD),
            ("к скрытию (dry-run)", GOLD_BG, GOLD),
            ("ошибка скрытия", RED_BG, RED),
        ]:
            requests.append(_cf_eq(sid, 22, 23, text, bg, fg, GRID_ROWS))
        for text, bg, fg in [("сб", WEEKEND_BG, ORANGE), ("вс", WEEKEND_BG, ORANGE)]:
            requests.append(_cf_eq(sid, 3, 4, text, bg, fg, GRID_ROWS))
        requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": sid,
                        "startRowIndex": 1,
                        "endRowIndex": GRID_ROWS,
                        "startColumnIndex": 18,
                        "endColumnIndex": 19,
                    }],
                    "gradientRule": {
                        "minpoint": {"color": _color(RED_BG), "type": "NUMBER", "value": "1"},
                        "midpoint": {"color": _color(GOLD_BG), "type": "NUMBER", "value": "3"},
                        "maxpoint": {"color": _color(GREEN_BG), "type": "NUMBER", "value": "5"},
                    },
                },
                "index": 0,
            }
        })
        _ = last
        self.svc.spreadsheets().batchUpdate(spreadsheetId=self.sid, body={"requests": requests}).execute()
        self.meta(refresh=True)

    def _fit_grid(self, sid: int, cols: int, rows: int) -> None:
        props = next(s["properties"] for s in self.meta()["sheets"] if s["properties"]["sheetId"] == sid)
        gp = props.get("gridProperties") or {}
        cc = int(gp.get("columnCount") or 26)
        rc = int(gp.get("rowCount") or 1000)
        frozen_c = int(gp.get("frozenColumnCount") or 0)
        frozen_r = int(gp.get("frozenRowCount") or 0)
        if frozen_c or frozen_r >= rows:
            self.svc.spreadsheets().batchUpdate(
                spreadsheetId=self.sid,
                body={"requests": [{
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sid,
                            "gridProperties": {"frozenColumnCount": 0, "frozenRowCount": 1 if rows > 1 else 0},
                        },
                        "fields": "gridProperties.frozenColumnCount,gridProperties.frozenRowCount",
                    }
                }]},
            ).execute()
            self.meta(refresh=True)
            props = next(s["properties"] for s in self.meta()["sheets"] if s["properties"]["sheetId"] == sid)
            gp = props.get("gridProperties") or {}
            cc = int(gp.get("columnCount") or 26)
            rc = int(gp.get("rowCount") or 1000)
        req: list[dict] = []
        if cc < cols:
            req.append({"appendDimension": {"sheetId": sid, "dimension": "COLUMNS", "length": cols - cc}})
        elif cc > cols:
            req.append({"deleteDimension": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": cols, "endIndex": cc}}})
        if rc < rows:
            req.append({"appendDimension": {"sheetId": sid, "dimension": "ROWS", "length": rows - rc}})
        elif rc > rows:
            req.append({"deleteDimension": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": rows, "endIndex": rc}}})
        if req:
            self.svc.spreadsheets().batchUpdate(spreadsheetId=self.sid, body={"requests": req}).execute()
            self.meta(refresh=True)

    def _expand_grid(self, sid: int, cols: int, rows: int = 1000) -> None:
        self._fit_grid(sid, cols, rows)

    def _drop_conditional(self, sid: int) -> None:
        sh = next(s for s in self.meta()["sheets"] if s["properties"]["sheetId"] == sid)
        n = len(sh.get("conditionalFormats") or [])
        if not n:
            return
        self.svc.spreadsheets().batchUpdate(
            spreadsheetId=self.sid,
            body={"requests": [
                {"deleteConditionalFormatRule": {"sheetId": sid, "index": i}}
                for i in range(n - 1, -1, -1)
            ]},
        ).execute()
        self.meta(refresh=True)

    def _format_by_post(self) -> None:
        sid = self.sheet_id(SHEET_BY_POST)
        headers = [
            "Ссылка на пост", "Превью поста", "Врач / тема", "Платформа", "Канал",
            "Дата", "Время", "Username", "Комментарий", "Это ответ?",
            "Родительский текст", "Оценка", "Действие", "Ссылка на комментарий",
        ]
        n = len(headers)
        self._fit_grid(sid, cols=n, rows=GRID_ROWS)
        formula = (
            f"=IFERROR(QUERY('{SHEET_COMMENTS}'!A2:X;"
            f'"select Col12, Col11, Col10, Col6, Col7, Col2, Col3, Col16, Col17, Col14, '
            f"Col15, Col18, Col23, Col13 where Col1 is not null order by Col12, Col2, Col3\";"
            f'0);"Нет комментариев")'
        )
        self._values(f"'{SHEET_BY_POST}'!A1:{_col(n)}1", [headers])
        self._values(f"'{SHEET_BY_POST}'!A2", [[formula]])
        self._drop_conditional(sid)
        meta_sheet = next(s for s in self.meta()["sheets"] if s["properties"]["sheetId"] == sid)
        widths = [220, 220, 110, 100, 90, 100, 80, 130, 340, 80, 180, 110, 110, 220]
        requests = []
        if meta_sheet.get("basicFilter"):
            requests.append({"clearBasicFilter": {"sheetId": sid}})
        requests += [
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sid,
                        "index": 1,
                        "gridProperties": {"frozenRowCount": 1, "frozenColumnCount": 0},
                        "tabColor": _color(SKY_BG),
                    },
                    "fields": "index,gridProperties.frozenRowCount,gridProperties.frozenColumnCount,tabColor",
                }
            },
            _wipe_body(sid, GRID_ROWS, n),
            {
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": n},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": _color(SKY_BG),
                            "textFormat": {"foregroundColor": _color(SKY), "bold": True, "fontFamily": "Calibri", "fontSize": 10},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE",
                            "wrapStrategy": "WRAP",
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)",
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 0, "endIndex": 1},
                    "properties": {"pixelSize": 42},
                    "fields": "pixelSize",
                }
            },
            {
                "setBasicFilter": {
                    "filter": {
                        "range": {"sheetId": sid, "startRowIndex": 0, "startColumnIndex": 0, "endColumnIndex": n}
                    }
                }
            },
        ]
        for i, w in enumerate(widths):
            requests.append({
                "updateDimensionProperties": {
                    "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
                    "properties": {"pixelSize": w},
                    "fields": "pixelSize",
                }
            })
        for text, bg, fg in [
            ("оскорбление", RED_BG, RED),
            ("негатив", RED_BG, RED),
            ("спам", PURPLE_BG, PURPLE),
            ("намёк", GOLD_BG, GOLD),
            ("смешанный", GOLD_BG, GOLD),
            ("средний", GOLD_BG, GOLD),
            ("шутка", BLUE_BG, BLUE),
            ("вопрос", BLUE_BG, BLUE),
            ("позитив", GREEN_BG, GREEN),
            ("нейтральный", NEUTRAL_BG, GRAY),
            ("свой", MINT, HEAD_FG),
        ]:
            requests.append(_cf_eq(sid, 11, 12, text, bg, fg, GRID_ROWS))
        self.svc.spreadsheets().batchUpdate(spreadsheetId=self.sid, body={"requests": requests}).execute()
        self.meta(refresh=True)

    def _format_deleted(self) -> None:
        sid = self.sheet_id(SHEET_DELETED)
        n = len(HEADERS)
        self._fit_grid(sid, cols=n, rows=GRID_ROWS)
        formula = (
            f'=IFERROR(QUERY(\'{SHEET_COMMENTS}\'!A2:X;'
            f'"select * where Col23 = \'удалён\' or Col23 = \'скрыт\' or Col23 = \'ошибка удаления\' '
            f'or Col18 = \'негатив\' or Col18 = \'оскорбление\' or Col18 = \'спам\' or Col18 = \'намёк\'";0);'
            f'"Пока нет негатива и удалений с 1 сентября 2026")'
        )
        self._values(f"'{SHEET_DELETED}'!A1:{_col(n)}1", [HEADERS])
        self._values(f"'{SHEET_DELETED}'!A2", [[formula]])
        requests = [
            _wipe_body(sid, GRID_ROWS, n),
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sid,
                        "gridProperties": {"frozenRowCount": 1, "frozenColumnCount": 0},
                        "tabColor": _color(RED_BG),
                    },
                    "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount,tabColor",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": _color(RED_BG),
                            "textFormat": {"foregroundColor": _color(RED), "bold": True, "fontFamily": "Calibri", "fontSize": 10},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE",
                            "wrapStrategy": "WRAP",
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)",
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 0, "endIndex": 1},
                    "properties": {"pixelSize": 42},
                    "fields": "pixelSize",
                }
            },
        ]
        self.svc.spreadsheets().batchUpdate(spreadsheetId=self.sid, body={"requests": requests}).execute()

    def _format_summary(self) -> None:
        sid = self.sheet_id(SHEET_SUMMARY)
        self._fit_grid(sid, cols=6, rows=70)
        title = "Кравира · модерация комментариев Meta  ·  с 1 сентября 2026"
        rows = [
            [title],
            ["Владелец таблицы: akuazuk@gmail.com", "Часовой пояс: МСК (UTC+3)", "Проверка: каждый час на GCE protocol-app"],
            [],
            ["Показатель", "Значение", "Пояснение"],
            ["Всего комментариев с 01.09.2026", f"=COUNTA('{SHEET_COMMENTS}'!A2:A)", "Все строки журнала, без дублей по ID"],
            ["Негатив + оскорбления", f'={_countif("R","негатив")[1:]}+{_countif("R","оскорбление")[1:]}', "Удаляем"],
            ["Спам", _countif("R", "спам"), "Удаляется"],
            ["Намёки / сарказм про врача", _countif("R", "намёк"), "Скрываем, не удаляем"],
            ["Смешанные отзывы", f'={_countif("R","смешанный")[1:]}+{_countif("R","средний")[1:]}', "Оставляем, следим"],
            ["Шутки", _countif("R", "шутка"), "Оставляем, если не про врача"],
            ["Вопросы", _countif("R", "вопрос"), "Не удаляем – это лиды"],
            ["Позитив", _countif("R", "позитив"), "Хвала, благодарности"],
            ["Нейтральные", _countif("R", "нейтральный"), "Без окраски, не скрываем"],
            ["Свои ответы клиники", _countif("R", "свой"), "Не трогаем"],
            ["Удалено скриптом", _countif("W", "удалён"), "DELETE через Graph API"],
            ["Ошибки удаления", _countif("W", "ошибка удаления"), "Нужен ручной просмотр"],
            ["За сегодня (МСК)", f'=COUNTIF(\'{SHEET_COMMENTS}\'!B:B{FS}TEXT(NOW(){FS}"yyyy-mm-dd"))', "Дата комментария = сегодня"],
            [],
            ["По врачам / темам", "Всего", "Негатив", "Вопросы", "Позитив", "Удалено"],
            ["Яровой", _doc("Яровой"), _doc_r("Яровой", "негатив"), _doc_r("Яровой", "вопрос"), _doc_r("Яровой", "позитив"), _doc_a("Яровой")],
            ["Казак", _doc("Казак"), _doc_r("Казак", "негатив"), _doc_r("Казак", "вопрос"), _doc_r("Казак", "позитив"), _doc_a("Казак")],
            ["Осипенко", _doc("Осипенко"), _doc_r("Осипенко", "негатив"), _doc_r("Осипенко", "вопрос"), _doc_r("Осипенко", "позитив"), _doc_a("Осипенко")],
            ["Луговская", _doc("Луговская"), _doc_r("Луговская", "негатив"), _doc_r("Луговская", "вопрос"), _doc_r("Луговская", "позитив"), _doc_a("Луговская")],
            ["Мытник", _doc("Мытник"), _doc_r("Мытник", "негатив"), _doc_r("Мытник", "вопрос"), _doc_r("Мытник", "позитив"), _doc_a("Мытник")],
            ["Баценко", _doc("Баценко"), _doc_r("Баценко", "негатив"), _doc_r("Баценко", "вопрос"), _doc_r("Баценко", "позитив"), _doc_a("Баценко")],
            ["Школьник", _doc("Школьник"), _doc_r("Школьник", "негатив"), _doc_r("Школьник", "вопрос"), _doc_r("Школьник", "позитив"), _doc_a("Школьник")],
            ["Чернявская", _doc("Чернявская"), _doc_r("Чернявская", "негатив"), _doc_r("Чернявская", "вопрос"), _doc_r("Чернявская", "позитив"), _doc_a("Чернявская")],
            ["Богдашич", _doc("Богдашич"), _doc_r("Богдашич", "негатив"), _doc_r("Богдашич", "вопрос"), _doc_r("Богдашич", "позитив"), _doc_a("Богдашич")],
            ["(без врача)", _countifs("A", "<>", "J", ""), _countifs("A", "<>", "J", "", "R", "негатив"), _countifs("A", "<>", "J", "", "R", "вопрос"), _countifs("A", "<>", "J", "", "R", "позитив"), _countifs("A", "<>", "J", "", "W", "удалён")],
            [],
            ["По платформе", "Instagram", "Facebook"],
            ["Всего", _countif("F", "Instagram"), _countif("F", "Facebook")],
            ["Реклама", _countifs("F", "Instagram", "G", "реклама"), _countifs("F", "Facebook", "G", "реклама")],
            ["Органика", _countifs("F", "Instagram", "G", "органика"), _countifs("F", "Facebook", "G", "органика")],
            [],
            ["Календарь с 1 сентября 2026", "Комментариев", "Негатив", "Вопросы", "Удалено"],
        ]
        date_row = len(rows) + 1
        rows.append([
            f"=DATE(2026{FS}9{FS}1)",
            f"=COUNTIF('{SHEET_COMMENTS}'!B:B{FS}TEXT(A{date_row}{FS}\"yyyy-mm-dd\"))",
            f"=COUNTIFS('{SHEET_COMMENTS}'!B:B{FS}TEXT(A{date_row}{FS}\"yyyy-mm-dd\"){FS}'{SHEET_COMMENTS}'!R:R{FS}\"негатив\")"
            f"+COUNTIFS('{SHEET_COMMENTS}'!B:B{FS}TEXT(A{date_row}{FS}\"yyyy-mm-dd\"){FS}'{SHEET_COMMENTS}'!R:R{FS}\"оскорбление\")",
            f"=COUNTIFS('{SHEET_COMMENTS}'!B:B{FS}TEXT(A{date_row}{FS}\"yyyy-mm-dd\"){FS}'{SHEET_COMMENTS}'!R:R{FS}\"вопрос\")",
            f"=COUNTIFS('{SHEET_COMMENTS}'!B:B{FS}TEXT(A{date_row}{FS}\"yyyy-mm-dd\"){FS}'{SHEET_COMMENTS}'!W:W{FS}\"удалён\")",
        ])
        cal = []
        for i in range(1, 31):
            r = date_row + i
            cal.append([
                f"=A{date_row}+{i}",
                f"=COUNTIF('{SHEET_COMMENTS}'!B:B{FS}TEXT(A{r}{FS}\"yyyy-mm-dd\"))",
                f"=COUNTIFS('{SHEET_COMMENTS}'!B:B{FS}TEXT(A{r}{FS}\"yyyy-mm-dd\"){FS}'{SHEET_COMMENTS}'!R:R{FS}\"негатив\")"
                f"+COUNTIFS('{SHEET_COMMENTS}'!B:B{FS}TEXT(A{r}{FS}\"yyyy-mm-dd\"){FS}'{SHEET_COMMENTS}'!R:R{FS}\"оскорбление\")",
                f"=COUNTIFS('{SHEET_COMMENTS}'!B:B{FS}TEXT(A{r}{FS}\"yyyy-mm-dd\"){FS}'{SHEET_COMMENTS}'!R:R{FS}\"вопрос\")",
                f"=COUNTIFS('{SHEET_COMMENTS}'!B:B{FS}TEXT(A{r}{FS}\"yyyy-mm-dd\"){FS}'{SHEET_COMMENTS}'!W:W{FS}\"удалён\")",
            ])
        padded = [(r + [""] * 6)[:6] for r in rows]
        self._values(f"'{SHEET_SUMMARY}'!A1:F{len(padded)}", padded)
        if cal:
            self._values(f"'{SHEET_SUMMARY}'!A{date_row + 1}:E{date_row + 30}", cal)

        meta_sheet = next(s for s in self.meta()["sheets"] if s["properties"]["sheetId"] == sid)
        del_cf = [{"deleteConditionalFormatRule": {"sheetId": sid, "index": i}} for i in range(len(meta_sheet.get("conditionalFormats") or []) - 1, -1, -1)]

        requests = del_cf + [
            {
                "unmergeCells": {
                    "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 6},
                }
            },
            {
                "updateSheetProperties": {
                    "properties": {"sheetId": sid, "tabColor": _color(GOLD_BG), "gridProperties": {"frozenRowCount": 4, "frozenColumnCount": 0}},
                    "fields": "tabColor,gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
                }
            },
            {
                "mergeCells": {
                    "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 6},
                    "mergeType": "MERGE_ALL",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 6},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": _color(HEAD_BG),
                            "textFormat": {"foregroundColor": _color(HEAD_FG), "fontSize": 16, "bold": True, "fontFamily": "Calibri"},
                            "verticalAlignment": "MIDDLE",
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment)",
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 0, "endIndex": 1},
                    "properties": {"pixelSize": 48},
                    "fields": "pixelSize",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": 3, "endRowIndex": 4, "startColumnIndex": 0, "endColumnIndex": 3},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": _color(SECTION_BG),
                            "textFormat": {"foregroundColor": _color(HEAD_FG), "bold": True, "fontFamily": "Calibri"},
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": 18, "endRowIndex": 19, "startColumnIndex": 0, "endColumnIndex": 6},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": _color(SECTION_BG),
                            "textFormat": {"foregroundColor": _color(HEAD_FG), "bold": True, "fontFamily": "Calibri"},
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": date_row - 2, "endRowIndex": date_row - 1, "startColumnIndex": 0, "endColumnIndex": 5},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": _color(SECTION_BG),
                            "textFormat": {"foregroundColor": _color(HEAD_FG), "bold": True, "fontFamily": "Calibri"},
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": date_row - 1, "endRowIndex": date_row + 30, "startColumnIndex": 0, "endColumnIndex": 1},
                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}}},
                    "fields": "userEnteredFormat.numberFormat",
                }
            },
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{
                            "sheetId": sid,
                            "startRowIndex": date_row - 1,
                            "endRowIndex": date_row + 30,
                            "startColumnIndex": 1,
                            "endColumnIndex": 2,
                        }],
                        "gradientRule": {
                            "minpoint": {"color": _color(WHITE), "type": "NUMBER", "value": "0"},
                            "midpoint": {"color": _color(GOLD_BG), "type": "NUMBER", "value": "2"},
                            "maxpoint": {"color": _color(SECTION_BG), "type": "NUMBER", "value": "8"},
                        },
                    },
                    "index": 0,
                }
            },
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{
                            "sheetId": sid,
                            "startRowIndex": date_row - 1,
                            "endRowIndex": date_row + 30,
                            "startColumnIndex": 2,
                            "endColumnIndex": 3,
                        }],
                        "booleanRule": {
                            "condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "0"}]},
                            "format": {"backgroundColor": _color(RED_BG), "textFormat": {"foregroundColor": _color(RED), "bold": True}},
                        },
                    },
                    "index": 0,
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": 6, "startColumnIndex": 1, "endColumnIndex": 2},
                    "cell": {"userEnteredFormat": {"backgroundColor": _color(RED_BG), "textFormat": {"foregroundColor": _color(RED), "bold": True, "fontSize": 14}}},
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": 8, "endRowIndex": 9, "startColumnIndex": 1, "endColumnIndex": 2},
                    "cell": {"userEnteredFormat": {"backgroundColor": _color(BLUE_BG), "textFormat": {"foregroundColor": _color(BLUE), "bold": True, "fontSize": 14}}},
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": 9, "endRowIndex": 10, "startColumnIndex": 1, "endColumnIndex": 2},
                    "cell": {"userEnteredFormat": {"backgroundColor": _color(GREEN_BG), "textFormat": {"foregroundColor": _color(GREEN), "bold": True, "fontSize": 14}}},
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 1, "endColumnIndex": 2},
                    "cell": {"userEnteredFormat": {"backgroundColor": _color(ORANGE_BG), "textFormat": {"foregroundColor": _color(ORANGE), "bold": True, "fontSize": 14}}},
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 1, "endColumnIndex": 2},
                    "cell": {"userEnteredFormat": {"backgroundColor": _color(MINT), "textFormat": {"foregroundColor": _color(TEAL_DARK), "bold": True, "fontSize": 16}}},
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            },
        ]
        for i, w in enumerate([280, 160, 220, 140, 140, 160]):
            requests.append({
                "updateDimensionProperties": {
                    "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
                    "properties": {"pixelSize": w},
                    "fields": "pixelSize",
                }
            })
        self.svc.spreadsheets().batchUpdate(spreadsheetId=self.sid, body={"requests": requests}).execute()

    def _format_runs(self) -> None:
        sid = self.sheet_id(SHEET_RUNS)
        self._fit_grid(sid, cols=11, rows=40)
        headers = [
            "Начало прогона МСК", "Конец МСК", "ID прогона", "Найдено", "Новых в таблице",
            "Удалено", "Пропущено (свои)", "Ошибки", "Хост", "Режим", "Комментарий",
        ]
        self._values(f"'{SHEET_RUNS}'!A1:K1", [headers])
        self._drop_conditional(sid)
        requests = [
            _wipe_body(sid, 40, 11),
            {
                "updateSheetProperties": {
                    "properties": {"sheetId": sid, "tabColor": _color(BLUE_BG), "gridProperties": {"frozenRowCount": 1}},
                    "fields": "tabColor,gridProperties.frozenRowCount",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": _color(BLUE_BG),
                            "textFormat": {"foregroundColor": _color(BLUE), "bold": True, "fontFamily": "Calibri"},
                            "horizontalAlignment": "CENTER",
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
                }
            },
        ]
        for i, w in enumerate([160, 160, 160, 90, 120, 90, 130, 90, 140, 100, 280]):
            requests.append({
                "updateDimensionProperties": {
                    "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
                    "properties": {"pixelSize": w},
                    "fields": "pixelSize",
                }
            })
        for col in (5, 7):
            requests.append({
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{"sheetId": sid, "startRowIndex": 1, "endRowIndex": 40, "startColumnIndex": col, "endColumnIndex": col + 1}],
                        "booleanRule": {
                            "condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "0"}]},
                            "format": {"backgroundColor": _color(RED_BG), "textFormat": {"foregroundColor": _color(RED), "bold": True}},
                        },
                    },
                    "index": 0,
                }
            })
        requests.append(_cf_eq(sid, 9, 10, "live", GREEN_BG, GREEN, 40))
        requests.append(_cf_eq(sid, 8, 9, "protocol-app", MINT, HEAD_FG, 40))
        self.svc.spreadsheets().batchUpdate(spreadsheetId=self.sid, body={"requests": requests}).execute()

    def _format_help(self) -> None:
        sid = self.sheet_id(SHEET_HELP)
        self._fit_grid(sid, cols=2, rows=22)
        text = [
            ["Справка по журналу"],
            ["Поле", "Смысл"],
            ["Оценка", "оскорбление / негатив / спам / намёк / смешанный / нейтральный / шутка / вопрос / позитив / свой"],
            ["Балл 1–5", "1 удалить · 2 скрыть намёк · 3 оставить (нейтраль/вопрос/шутка/смешанный) · 4–5 хвала"],
            ["Действие", "удалён · скрыт · оставлен · пропущен (свой) · ошибка удаления"],
            ["Канал", "реклама = комментарий под объявлением (в т.ч. dark post) · органика = пост профиля/страницы"],
            ["По постам", "лист «По постам»: все комментарии к одному ролику/посту стоят подряд, ответы рядом с постом"],
            ["Фильтр", "на «Комментарии» стрелка в шапке: врач, оценка, канал, платформа"],
            ["Нейтральный", "нет оценки врача: «+++», тег, факт. Не скрываем"],
            ["Намёк", "сарказм про честность/компетентность врача. Скрываем"],
            ["Смешанный", "и плюс и минус про приём, без издёвки. Оставляем"],
            ["Шутка", "смех не про врача (ИИ, ролик). Оставляем"],
            ["Скрываем", "только намёк на нечестность/некомпетентность врача"],
            ["Не удаляем", "вопросы, записи, хвалу, нейтраль, шутку, смешанный отзыв, ответы клиники"],
            ["Удаляем", "оскорбления, насмешки над внешностью, «не ходите», мошенничество, спам, жёсткие жалобы"],
            ["Старт журнала", "2026-09-01 00:00 МСК"],
            ["Расписание", "3 раза в день: 09:00, 15:00, 21:00 МСК. В «Прогоны» пишем только если нашлись новые или скрыли/удалили"],
            ["Аккаунт таблицы", "akuazuk@gmail.com (владелец) · запись через mcp-sheets@protocol-home-e1.iam.gserviceaccount.com"],
        ]
        self._values(f"'{SHEET_HELP}'!A1:B18", text)
        requests = [
            {
                "mergeCells": {
                    "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 2},
                    "mergeType": "MERGE_ALL",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": _color(HEAD_BG),
                            "textFormat": {"foregroundColor": _color(HEAD_FG), "fontSize": 14, "bold": True, "fontFamily": "Calibri"},
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": 1, "endRowIndex": 2},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": _color(SECTION_BG),
                            "textFormat": {"foregroundColor": _color(HEAD_FG), "bold": True},
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
                    "properties": {"pixelSize": 200},
                    "fields": "pixelSize",
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2},
                    "properties": {"pixelSize": 720},
                    "fields": "pixelSize",
                }
            },
            {
                "updateSheetProperties": {
                    "properties": {"sheetId": sid, "tabColor": _color(NEUTRAL_BG)},
                    "fields": "tabColor",
                }
            },
        ]
        self.svc.spreadsheets().batchUpdate(spreadsheetId=self.sid, body={"requests": requests}).execute()


def _countif(col: str, val: str) -> str:
    return f"=COUNTIF('{SHEET_COMMENTS}'!{col}:{col}{FS}\"{val}\")"


def _countifs(*args: str) -> str:
    parts: list[str] = []
    for i in range(0, len(args), 2):
        col, val = args[i], args[i + 1]
        parts.append(f"'{SHEET_COMMENTS}'!{col}:{col}")
        parts.append(f'"{val}"')
    return "=COUNTIFS(" + FS.join(parts) + ")"


def _wipe_body(sid: int, rows: int, cols: int, start_row: int = 1) -> dict:
    return {
        "repeatCell": {
            "range": {
                "sheetId": sid,
                "startRowIndex": start_row,
                "endRowIndex": rows,
                "startColumnIndex": 0,
                "endColumnIndex": cols,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": _color(WHITE),
                    "textFormat": {
                        "foregroundColor": _color(INK),
                        "fontSize": 10,
                        "bold": False,
                        "italic": False,
                        "fontFamily": "Calibri",
                    },
                    "horizontalAlignment": "LEFT",
                    "verticalAlignment": "TOP",
                    "wrapStrategy": "WRAP",
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)",
        }
    }


def _cf_eq(sid: int, c0: int, c1: int, text: str, bg: dict, fg: dict, row_end: int = GRID_ROWS) -> dict:
    return {
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sid,
                    "startRowIndex": 1,
                    "endRowIndex": row_end,
                    "startColumnIndex": c0,
                    "endColumnIndex": c1,
                }],
                "booleanRule": {
                    "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": text}]},
                    "format": {
                        "backgroundColor": _color(bg),
                        "textFormat": {"foregroundColor": _color(fg), "bold": True},
                    },
                },
            },
            "index": 0,
        }
    }


def _cf_custom(sid: int, formula: str, bg: dict, fg: dict, c0: int, c1: int, row_end: int = GRID_ROWS) -> dict:
    return {
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sid,
                    "startRowIndex": 1,
                    "endRowIndex": row_end,
                    "startColumnIndex": c0,
                    "endColumnIndex": c1,
                }],
                "booleanRule": {
                    "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": formula}]},
                    "format": {
                        "backgroundColor": _color(bg),
                        "textFormat": {"foregroundColor": _color(fg or INK)},
                    },
                },
            },
            "index": 0,
        }
    }


_EPOCH = datetime(1899, 12, 30)


def _as_date_text(value: Any) -> str:
    if value in ("", None):
        return ""
    if isinstance(value, str) and len(value) >= 10 and value[4] == "-":
        return value[:10]
    try:
        n = float(str(value).replace(",", "."))
    except ValueError:
        return str(value)
    if n > 20000:
        return (_EPOCH + timedelta(days=int(n))).strftime("%Y-%m-%d")
    return str(value)


def _as_time_text(value: Any) -> str:
    if value in ("", None):
        return ""
    if isinstance(value, str) and ":" in value:
        part = value.split()[-1]
        return part[:8]
    try:
        n = float(str(value).replace(",", "."))
    except ValueError:
        return str(value)
    if 0 <= n < 1:
        secs = int(round(n * 86400))
        h, rem = divmod(secs, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    dt = _EPOCH + timedelta(days=n)
    return dt.strftime("%H:%M:%S")


def _as_dt_text(value: Any) -> str:
    if value in ("", None):
        return ""
    if isinstance(value, str) and "-" in value and ":" in value:
        return value[:19]
    try:
        n = float(str(value).replace(",", "."))
    except ValueError:
        return str(value)
    return (_EPOCH + timedelta(days=n)).strftime("%Y-%m-%d %H:%M:%S")


def _col(n: int) -> str:
    s = ""
    while n:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s


def _norm_id(value: Any) -> str:
    s = str(value).strip().lstrip("'")
    if s.endswith(".0"):
        s = s[:-2]
    if "E+" in s.upper() or "e+" in s:
        try:
            s = str(int(float(s)))
        except Exception:
            pass
    return s


def _doc(name: str) -> str:
    return _countif("J", name)


def _doc_r(name: str, rating: str) -> str:
    return _countifs("J", name, "R", rating)


def _doc_a(name: str) -> str:
    return _countifs("J", name, "W", "удалён")


def _txt(value: Any) -> str:
    if value is None or value == "":
        return ""
    return "'" + str(value)


def to_sheet_row(item: dict, verdict, *, checked: datetime, run_id: str, action: str, delete_result: str, note: str) -> list[Any]:
    markers = verdict.markers or ""
    reason = getattr(verdict, "reason", "") or ""
    if reason and reason not in markers:
        markers = f"{markers}; {reason}".strip("; ")[:240]
    return [
        _txt(item["comment_id"]),
        "'" + item["date"] if item.get("date") else "",
        "'" + item["time"] if item.get("time") else "",
        item["weekday"],
        "'" + checked.strftime("%Y-%m-%d %H:%M:%S"),
        item["platform"],
        item["channel"],
        item["campaign"],
        item["ad"],
        item["doctor"],
        item["post_preview"],
        item["post_url"],
        item["comment_url"],
        item["is_reply"],
        item["parent_text"],
        item["username"],
        item["text"],
        verdict.rating,
        verdict.score,
        verdict.tone,
        verdict.category,
        markers,
        action,
        item["likes"],
    ]
