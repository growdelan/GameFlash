"""Integracja z Google Sheets dla trwalego stanu przetwarzania newsow."""

from dataclasses import dataclass
from datetime import datetime, timezone

import gspread
from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound

STATE_HEADERS = (
    "Status",
    "Attempts",
    "Summary",
    "LastError",
    "DiscoveredAt",
    "UpdatedAt",
)
MAX_ERROR_LENGTH = 500


@dataclass(frozen=True)
class NewsRecord:
    """Stan pojedynczego artykulu zapisany w Google Sheets."""

    row_number: int
    link: str
    status: str
    attempts: int
    summary: str
    last_error: str
    discovered_at: str
    updated_at: str


def utc_now() -> str:
    """Zwraca aktualny czas UTC w formacie ISO 8601."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def authenticate_gspread(service_account_file: str) -> gspread.Client:
    """Autoryzacja klienta Google Sheets przez konto serwisowe."""
    return gspread.service_account(filename=service_account_file)


def open_sheet(gc: gspread.Client, spreadsheet_id: str, worksheet_title: str):
    """Otwiera arkusz i wskazana zakladke po ID dokumentu."""
    try:
        sh = gc.open_by_key(spreadsheet_id)
    except SpreadsheetNotFound as exc:
        raise RuntimeError("Nie znaleziono arkusza Google Sheets.") from exc
    except APIError as exc:
        raise RuntimeError("Brak dostepu do arkusza Google Sheets.") from exc

    try:
        ws = sh.worksheet(worksheet_title)
    except WorksheetNotFound as exc:
        raise RuntimeError(f"Nie znaleziono zakladki: {worksheet_title}") from exc

    return sh, ws


def _header_map(values: list[list[str]]) -> dict[str, int]:
    if not values:
        raise RuntimeError("Arkusz jest pusty.")

    header_map = {
        str(value or "").strip().lower(): index
        for index, value in enumerate(values[0])
        if str(value or "").strip()
    }
    if "links" not in header_map:
        raise RuntimeError("Brak wymaganej kolumny: Links")
    return header_map


def ensure_state_schema(ws) -> None:
    """Dodaje brakujace kolumny stanu bez naruszania istniejacego naglowka."""
    values = ws.get_all_values()
    header_map = _header_map(values)
    next_column = len(values[0]) + 1

    for header in STATE_HEADERS:
        if header.lower() in header_map:
            continue
        ws.update_cell(1, next_column, header)
        header_map[header.lower()] = next_column - 1
        next_column += 1


def _cell(row: list[str], index: int | None) -> str:
    if index is None or index >= len(row):
        return ""
    return str(row[index] or "").strip()


def _parse_attempts(value: str) -> int:
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return 0


def read_news_records(ws) -> list[NewsRecord]:
    """Czyta rekordy newsow wraz z numerami wierszy potrzebnymi do aktualizacji."""
    values = ws.get_all_values()
    header_map = _header_map(values)
    records = []

    for row_number, row in enumerate(values[1:], start=2):
        link = _cell(row, header_map["links"])
        if not link:
            continue

        raw_status = _cell(row, header_map.get("status")).lower()
        records.append(
            NewsRecord(
                row_number=row_number,
                link=link,
                status=raw_status or "sent",
                attempts=_parse_attempts(_cell(row, header_map.get("attempts"))),
                summary=_cell(row, header_map.get("summary")),
                last_error=_cell(row, header_map.get("lasterror")),
                discovered_at=_cell(row, header_map.get("discoveredat")),
                updated_at=_cell(row, header_map.get("updatedat")),
            )
        )

    return records


def read_registered_links(ws) -> set[str]:
    """Zwraca wszystkie linki niezaleznie od ich aktualnego statusu."""
    return {record.link for record in read_news_records(ws)}


def append_pending_link(ws, link: str, timestamp: str | None = None) -> None:
    """Dopisuje nowy link jako rekord oczekujacy na przetworzenie."""
    values = ws.get_all_values()
    header_map = _header_map(values)
    timestamp = timestamp or utc_now()
    row = [""] * len(values[0])
    row[header_map["links"]] = link
    row[header_map["status"]] = "pending"
    row[header_map["attempts"]] = "0"
    row[header_map["discoveredat"]] = timestamp
    row[header_map["updatedat"]] = timestamp
    ws.append_row(row, value_input_option="RAW")


def append_link(ws, link: str) -> None:
    """Zachowuje publiczna nazwe operacji append dla nowego kontraktu stanu."""
    append_pending_link(ws, link)


def update_news_record(
    ws,
    record: NewsRecord,
    *,
    status: str,
    attempts: int,
    summary: str | None = None,
    last_error: str = "",
    timestamp: str | None = None,
) -> None:
    """Aktualizuje pola stanu rekordu w jego istniejacym wierszu."""
    values = ws.get_all_values()
    header_map = _header_map(values)
    updates = {
        "status": status,
        "attempts": str(max(attempts, 0)),
        "lasterror": str(last_error or "")[:MAX_ERROR_LENGTH],
        "updatedat": timestamp or utc_now(),
    }
    if summary is not None:
        updates["summary"] = summary

    for header, value in updates.items():
        ws.update_cell(record.row_number, header_map[header] + 1, value)
