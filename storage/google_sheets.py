"""Integracja z Google Sheets dla stanu przetworzonych linkow."""

import gspread
from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound


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


def read_registered_links(ws) -> set[str]:
    """Czyta wszystkie zarejestrowane linki z kolumny Links."""
    values = ws.get_all_values()
    if not values:
        raise RuntimeError("Arkusz jest pusty.")

    header = [str(value or "").strip().lower() for value in values[0]]
    try:
        link_index = header.index("links")
    except ValueError as exc:
        raise RuntimeError("Brak wymaganej kolumny: Links") from exc

    registered_links = set()
    for row in values[1:]:
        if link_index >= len(row):
            continue
        link = str(row[link_index]).strip()
        if link:
            registered_links.add(link)
    return registered_links


def append_link(ws, link: str) -> None:
    """Dopisuje nowy link do arkusza."""
    ws.append_row([link], value_input_option="RAW")
