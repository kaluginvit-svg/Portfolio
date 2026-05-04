"""
Обёртка над Google Sheets API (сервисный аккаунт, JSON-ключ).

Операции: метаданные таблицы, чтение диапазона, clear / append / update,
batchUpdate (форматирование: merge, цвет фона, жирный шрифт заголовка).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


SCOPES = ("https://www.googleapis.com/auth/spreadsheets",)


def resolve_service_account_json(folder: str | Path) -> Path | None:
    """
    Путь к ключу в папке проекта: приоритет ``service_account.json``,
    иначе любой ``*.json`` в этой папке с ``"type": "service_account"``.
    Подпапки не сканируются (чтобы не подхватить OAuth client из ``credential/``).
    """
    base = Path(folder).expanduser().resolve()
    preferred = base / "service_account.json"
    if preferred.is_file():
        return preferred
    for path in sorted(base.glob("*.json")):
        try:
            text = path.read_text(encoding="utf-8")
            data = json.loads(text)
        except (OSError, json.JSONDecodeError, TypeError):
            continue
        if isinstance(data, dict) and data.get("type") == "service_account":
            return path
    return None


_SPREADSHEET_URL_ID_RE = re.compile(
    r"/spreadsheets/d/([a-zA-Z0-9_-]+)",
    re.IGNORECASE,
)


def spreadsheet_id_from_url_or_id(text: str) -> str:
    """
    Принимает полный URL Google Таблицы или сырой spreadsheetId.
    Убирает пробелы; из URL извлекает идентификатор между /d/ и следующим слэшем.
    """
    raw = "".join((text or "").split())
    if not raw:
        return ""
    m = _SPREADSHEET_URL_ID_RE.search(raw)
    if m:
        return m.group(1)
    return raw


class GoogleSheets:
    """CRUD-подобная работа с одной таблицей."""

    def __init__(self, credentials_path: str | Path, spreadsheet_id: str) -> None:
        # ID из URL без пробелов/переносов (частая ошибка при копировании в поле GUI)
        self.spreadsheet_id = "".join(spreadsheet_id.split())
        path = Path(credentials_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Файл ключа сервисного аккаунта не найден: {path}")
        creds = Credentials.from_service_account_file(str(path), scopes=SCOPES)
        self._service = build("sheets", "v4", credentials=creds, cache_discovery=False)

    @property
    def service(self) -> Any:
        return self._service

    def get_spreadsheet(self) -> dict[str, Any]:
        return (
            self._service.spreadsheets()
            .get(spreadsheetId=self.spreadsheet_id)
            .execute()
        )

    def list_sheets(self) -> list[dict[str, Any]]:
        meta = self.get_spreadsheet()
        return meta.get("sheets", [])

    def get_sheet_id_by_title(self, title: str) -> int | None:
        for sheet in self.list_sheets():
            props = sheet.get("properties", {})
            if props.get("title") == title:
                return int(props["sheetId"])
        return None

    def ensure_sheet(self, title: str, rows: int = 1000, cols: int = 26) -> int:
        """Возвращает sheetId листа; создаёт лист при отсутствии."""
        sid = self.get_sheet_id_by_title(title)
        if sid is not None:
            return sid
        body = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": title,
                            "gridProperties": {
                                "rowCount": rows,
                                "columnCount": cols,
                            },
                        }
                    }
                }
            ]
        }
        resp = (
            self._service.spreadsheets()
            .batchUpdate(spreadsheetId=self.spreadsheet_id, body=body)
            .execute()
        )
        replies = resp.get("replies", [])
        if not replies or "addSheet" not in replies[0]:
            raise RuntimeError(f"Не удалось создать лист {title!r}: {resp}")
        return int(replies[0]["addSheet"]["properties"]["sheetId"])

    def read_range(self, range_a1: str) -> list[list[Any]]:
        result = (
            self._service.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheet_id, range=range_a1)
            .execute()
        )
        return result.get("values", [])

    def clear_range(self, range_a1: str) -> dict[str, Any]:
        return (
            self._service.spreadsheets()
            .values()
            .clear(spreadsheetId=self.spreadsheet_id, range=range_a1, body={})
            .execute()
        )

    def append(
        self,
        range_a1: str,
        values: list[list[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> dict[str, Any]:
        body = {"values": values}
        return (
            self._service.spreadsheets()
            .values()
            .append(
                spreadsheetId=self.spreadsheet_id,
                range=range_a1,
                valueInputOption=value_input_option,
                insertDataOption="INSERT_ROWS",
                body=body,
            )
            .execute()
        )

    def update_range(
        self,
        range_a1: str,
        values: list[list[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> dict[str, Any]:
        if not values:
            raise ValueError("values не может быть пустым")
        width = len(values[0])
        for row in values:
            if len(row) != width:
                raise ValueError(
                    "Все строки values должны быть одинаковой длины "
                    "(соответствие диапазону)."
                )
        body = {"values": values}
        return (
            self._service.spreadsheets()
            .values()
            .update(
                spreadsheetId=self.spreadsheet_id,
                range=range_a1,
                valueInputOption=value_input_option,
                body=body,
            )
            .execute()
        )

    def batch_update(self, requests: list[dict[str, Any]]) -> dict[str, Any]:
        if not requests:
            return {}
        return (
            self._service.spreadsheets()
            .batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={"requests": requests},
            )
            .execute()
        )

    def format_report_sheet(
        self,
        *,
        sheet_id: int,
        num_cols: int,
        title_rows: int = 1,
        column_header_rows: int = 1,
        data_rows: int = 0,
    ) -> None:
        """
        Форматирование отчёта (batchUpdate): объединённый заголовок, строка колонок, тело таблицы.
        Строки 0..title_rows — шапка (MERGE_ALL на первые title_rows строк, если title_rows>=1 и num_cols>=1).
        Следующие column_header_rows — подзаголовки колонок.
        Далее — data_rows строк данных.
        """
        requests: list[dict[str, Any]] = []

        idx_title_end = title_rows
        idx_header_end = title_rows + column_header_rows
        last_row_idx = idx_header_end + data_rows

        if title_rows >= 1 and num_cols >= 1:
            requests.append(
                {
                    "mergeCells": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": title_rows,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols,
                        },
                        "mergeType": "MERGE_ALL",
                    }
                }
            )
            requests.append(
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": idx_title_end,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 0.15,
                                    "green": 0.35,
                                    "blue": 0.65,
                                },
                                "horizontalAlignment": "CENTER",
                                "verticalAlignment": "MIDDLE",
                                "textFormat": {
                                    "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                                    "fontSize": 14,
                                    "bold": True,
                                },
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment,textFormat)",
                    }
                }
            )

        if column_header_rows >= 1:
            requests.append(
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": idx_title_end,
                            "endRowIndex": idx_header_end,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 0.85,
                                    "green": 0.88,
                                    "blue": 0.92,
                                },
                                "horizontalAlignment": "CENTER",
                                "textFormat": {"bold": True, "fontSize": 11},
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,textFormat)",
                    }
                }
            )

        if data_rows > 0:
            requests.append(
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": idx_header_end,
                            "endRowIndex": last_row_idx,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "horizontalAlignment": "CENTER",
                                "textFormat": {"fontSize": 11},
                            }
                        },
                        "fields": "userEnteredFormat(horizontalAlignment,textFormat)",
                    }
                }
            )

        if requests:
            self.batch_update(requests)

    def set_column_widths(self, sheet_id: int, widths_px: list[int], start_col: int = 0) -> None:
        """Ширина столбцов по списку пикселей (под длину текста в отчёте)."""
        requests: list[dict[str, Any]] = []
        for i, w in enumerate(widths_px):
            requests.append(
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": start_col + i,
                            "endIndex": start_col + i + 1,
                        },
                        "properties": {"pixelSize": int(w)},
                        "fields": "pixelSize",
                    }
                }
            )
        self.batch_update(requests)

    def format_document_report(
        self,
        *,
        sheet_id: int,
        num_cols: int,
        n_main_title: int = 1,
        n_meta: int = 2,
        n_gap: int = 1,
        n_header: int = 1,
        n_data: int,
        n_footer: int = 1,
        zebra_data: bool = True,
    ) -> None:
        """
        Оформление «как документ»: шапка, строки-подзаголовки (период, реквизиты),
        пустая строка, таблица с рамкой, опционально зебра по строкам данных, подвал.
        Индексы строк — 0-based, как в API.
        """
        r = 0
        r_main_end = r + n_main_title
        r_meta_end = r_main_end + n_meta
        r_gap_end = r_meta_end + n_gap
        r_header_end = r_gap_end + n_header
        r_data_end = r_header_end + n_data
        r_footer_end = r_data_end + n_footer

        gray = {"red": 0.55, "green": 0.55, "blue": 0.55}
        border = {"style": "SOLID", "width": 1, "color": gray}
        requests: list[dict[str, Any]] = []

        if n_main_title >= 1 and num_cols >= 1:
            requests.append(
                {
                    "mergeCells": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": r,
                            "endRowIndex": r_main_end,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols,
                        },
                        "mergeType": "MERGE_ALL",
                    }
                }
            )
            requests.append(
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": r,
                            "endRowIndex": r_main_end,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 0.12,
                                    "green": 0.32,
                                    "blue": 0.52,
                                },
                                "horizontalAlignment": "CENTER",
                                "verticalAlignment": "MIDDLE",
                                "wrapStrategy": "WRAP",
                                "textFormat": {
                                    "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                                    "fontSize": 16,
                                    "bold": True,
                                },
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment,wrapStrategy,textFormat)",
                    }
                },
            )

        if n_meta > 0:
            for meta_row in range(r_main_end, r_meta_end):
                requests.append(
                    {
                        "mergeCells": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": meta_row,
                                "endRowIndex": meta_row + 1,
                                "startColumnIndex": 0,
                                "endColumnIndex": num_cols,
                            },
                            "mergeType": "MERGE_ALL",
                        }
                    }
                )

            requests.append(
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": r_main_end,
                            "endRowIndex": r_meta_end,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 0.94,
                                    "green": 0.95,
                                    "blue": 0.96,
                                },
                                "horizontalAlignment": "LEFT",
                                "verticalAlignment": "MIDDLE",
                                "wrapStrategy": "WRAP",
                                "textFormat": {
                                    "foregroundColor": {"red": 0.2, "green": 0.2, "blue": 0.22},
                                    "fontSize": 11,
                                },
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment,wrapStrategy,textFormat)",
                    }
                }
            )

        if n_gap > 0:
            requests.append(
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": r_meta_end,
                            "endRowIndex": r_gap_end,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "verticalAlignment": "MIDDLE",
                            }
                        },
                        "fields": "userEnteredFormat(verticalAlignment)",
                    }
                },
            )

        requests.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": r_gap_end,
                        "endRowIndex": r_header_end,
                        "startColumnIndex": 0,
                        "endColumnIndex": num_cols,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {
                                "red": 0.82,
                                "green": 0.86,
                                "blue": 0.90,
                            },
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE",
                            "textFormat": {"bold": True, "fontSize": 11},
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment,textFormat)",
                },
            },
        )

        if n_data > 0:
            data_fmt: dict[str, Any] = {
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
                "wrapStrategy": "WRAP",
                "textFormat": {"fontSize": 11},
            }
            requests.append(
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": r_header_end,
                            "endRowIndex": r_data_end,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols,
                        },
                        "cell": {"userEnteredFormat": data_fmt},
                        "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment,wrapStrategy,textFormat)",
                    }
                },
            )

        if zebra_data and n_data > 1:
            for dr in range(r_header_end + 1, r_data_end, 2):
                requests.append(
                    {
                        "repeatCell": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": dr,
                                "endRowIndex": min(dr + 1, r_data_end),
                                "startColumnIndex": 0,
                                "endColumnIndex": num_cols,
                            },
                            "cell": {
                                "userEnteredFormat": {
                                    "backgroundColor": {
                                        "red": 0.97,
                                        "green": 0.98,
                                        "blue": 1.0,
                                    }
                                },
                            },
                            "fields": "userEnteredFormat(backgroundColor)",
                        }
                    },
                )

        if n_footer > 0:
            requests.append(
                {
                    "mergeCells": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": r_data_end,
                            "endRowIndex": r_footer_end,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols,
                        },
                        "mergeType": "MERGE_ALL",
                    }
                },
            )
            requests.append(
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": r_data_end,
                            "endRowIndex": r_footer_end,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "horizontalAlignment": "CENTER",
                                "verticalAlignment": "MIDDLE",
                                "wrapStrategy": "WRAP",
                                "textFormat": {
                                    "foregroundColor": {
                                        "red": 0.45,
                                        "green": 0.45,
                                        "blue": 0.48,
                                    },
                                    "fontSize": 10,
                                    "italic": True,
                                },
                            }
                        },
                        "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment,wrapStrategy,textFormat)",
                    }
                }
            )

        if n_header >= 1 or n_data > 0 or n_footer >= 1:
            requests.append(
                {
                    "updateBorders": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": r_gap_end,
                            "endRowIndex": r_data_end,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols,
                        },
                        "top": border,
                        "bottom": border,
                        "left": border,
                        "right": border,
                        "innerHorizontal": border,
                        "innerVertical": border,
                    }
                },
            )

        if n_footer > 0:
            requests.append(
                {
                    "updateBorders": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": r_data_end,
                            "endRowIndex": r_footer_end,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols,
                        },
                        "top": border,
                        "bottom": border,
                        "left": border,
                        "right": border,
                    }
                }
            )

        requests.append(
            {
                "updateDimensionProperties": {
                    "properties": {"pixelSize": 28},
                    "fields": "pixelSize",
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": 0,
                        "endIndex": r_main_end + n_meta + n_gap,
                    },
                }
            },
        )

        self.batch_update(requests)
