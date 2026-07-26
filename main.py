"""Głowny plik skryptu"""

import os
import re
from dotenv import load_dotenv

from llms import gemini
from scrapers import jina, listing
from emails import gmail
from storage import google_sheets

DEFAULT_LISTING_URL = "https://www.ppe.pl/gry"
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
DEFAULT_GOOGLE_SHEET_ID = "1N82WxjskvsIyjlfwh8CxlhHJB9LEUMwbAdCI8w0J_yk"
DEFAULT_GOOGLE_SHEET_WORKSHEET = "Sheet1"
MAX_ARTICLE_TEXT_CHARS = 6500
MAX_PIPELINE_ATTEMPTS = 3
KNOWN_NEWS_STATUSES = {"pending", "ready", "sent", "failed"}
ARTICLE_TRUNCATION_NOTICE = (
    "\n\n[Pozostala czesc artykulu zostala pominieta ze wzgledu na limit wejscia modelu.]"
)
TITLE_RE = re.compile(r"^Tytu[łl]:\s*(.+)$", re.MULTILINE)
SUMMARY_RE = re.compile(r"Podsumowanie:\s*(.+?)(?:\n\s*\nLink:|\nLink:|\Z)", re.DOTALL)
SUMMARY_END_RE = re.compile(r"[.!?…][\"'”’)]*\s*$")


def load_config():
    """
    Ładuje zmienne konfiguracyjne z pliku .env.
    """
    load_dotenv()
    return {
        "URL": os.getenv("URL", DEFAULT_LISTING_URL),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "GEMINI_MODEL": os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
        "SMTP_SERVER": os.getenv("SMTP_SERVER"),
        "SENDER_MAIL": os.getenv("SENDER_MAIL"),
        "SENDER_PASS": os.getenv("SENDER_PASS"),
        "RECIPIENTS": os.getenv("RECIPIENTS").split(","),
        "GOOGLE_SHEET_ID": os.getenv("GOOGLE_SHEET_ID", DEFAULT_GOOGLE_SHEET_ID),
        "GOOGLE_SHEET_WORKSHEET": os.getenv(
            "GOOGLE_SHEET_WORKSHEET", DEFAULT_GOOGLE_SHEET_WORKSHEET
        ),
        "GSPREAD_SERVICE_ACCOUNT_FILE": os.getenv(
            "GSPREAD_SERVICE_ACCOUNT_FILE", "service_account.json"
        ),
    }


def open_state_worksheet(config):
    """Otwiera arkusz i przygotowuje kolumny trwalego stanu pipeline'u."""
    gc = google_sheets.authenticate_gspread(config["GSPREAD_SERVICE_ACCOUNT_FILE"])
    _, ws = google_sheets.open_sheet(
        gc=gc,
        spreadsheet_id=config["GOOGLE_SHEET_ID"],
        worksheet_title=config["GOOGLE_SHEET_WORKSHEET"],
    )
    google_sheets.ensure_state_schema(ws)
    return ws


def discover_news(config, ws, records):
    """Dopisuje nowe linki z listingu jako rekordy pending."""
    registered_links = {record.link for record in records}

    news = listing.fetch_listing_html(url=config["URL"])
    parse_news_response = listing.extract_news_links(news, base_url=config["URL"])
    new_links = []
    seen_this_run = set()
    for link in parse_news_response:
        if link in registered_links or link in seen_this_run:
            continue
        try:
            google_sheets.append_pending_link(ws, link)
        except Exception as exc:
            print(f"Nie udalo sie dopisac linku do Google Sheets: {link} ({exc})")
            continue
        registered_links.add(link)
        seen_this_run.add(link)
        new_links.append(link)
    print(f"Nowe linki: {new_links}")
    return new_links


def fetch_and_process_news(config):
    """Otwiera stan i rejestruje nowe linki z listingu."""
    ws = open_state_worksheet(config)
    records = google_sheets.read_news_records(ws)
    return discover_news(config, ws, records)


def prepare_article_text_for_summary(article_text: str) -> str:
    """Ogranicza wejscie do LLM, zeby nie przekroczyc limitu rozmiaru promptu."""
    cleaned_text = str(article_text or "").strip()
    if len(cleaned_text) <= MAX_ARTICLE_TEXT_CHARS:
        return cleaned_text

    trimmed_text = cleaned_text[:MAX_ARTICLE_TEXT_CHARS].rsplit(" ", 1)[0].rstrip()
    return f"{trimmed_text}{ARTICLE_TRUNCATION_NOTICE}"


def summarize_news(config, new_links):
    """
    Podsumowuje nowe linki do newsów i wysyła email z podsumowaniami.
    """
    news_to_send = []
    for news in new_links:
        try:
            summary_news = summarize_link(config, news)
        except Exception as exc:
            print(f"Nie udalo sie przetworzyc artykulu {news}: {exc}")
            continue

        news_to_send.append(
            f"{summary_news}\n\nLink: {news}\n\n################################"
        )
        print(summary_news)
    print(f"Newsy do wyslania:\n{news_to_send}")
    return news_to_send


def summarize_link(config, link: str) -> str:
    """Pobiera artykul i zwraca kompletne podsumowanie jednego linku."""
    article_text = prepare_article_text_for_summary(jina.fetch_article_text(url=link))
    summary_model_options = gemini.model_options(
        prompt=gemini.summary_prompt(article_text),
        temperature=0.8,
        max_tokens=2048,
    )
    summary = gemini.run_gemini_model(
        gemini_api_key=config["GEMINI_API_KEY"],
        model=config["GEMINI_MODEL"],
        options=summary_model_options,
    )
    if not is_complete_summary_result(summary):
        raise RuntimeError("Model zwrocil niekompletne podsumowanie.")
    return summary


def _next_failure_state(attempts: int) -> tuple[str, int]:
    next_attempts = attempts + 1
    status = "failed" if next_attempts >= MAX_PIPELINE_ATTEMPTS else "pending"
    return status, next_attempts


def log_unknown_statuses(records) -> None:
    """Loguje rekordy, ktorych status nie nalezy do kontraktu pipeline'u."""
    for record in records:
        if record.status not in KNOWN_NEWS_STATUSES:
            print(
                f"Pominieto rekord z nieznanym statusem: "
                f"{record.link} ({record.status})"
            )


def process_pending_news(config, ws, records) -> None:
    """Przetwarza rekordy pending i utrwala gotowe podsumowania jako ready."""
    for record in records:
        if record.status not in KNOWN_NEWS_STATUSES:
            continue
        if record.status != "pending":
            continue

        attempts = 0 if record.attempts >= MAX_PIPELINE_ATTEMPTS else record.attempts
        try:
            summary = summarize_link(config, record.link)
            google_sheets.update_news_record(
                ws,
                record,
                status="ready",
                attempts=0,
                summary=summary,
                last_error="",
            )
        except Exception as exc:
            status, next_attempts = _next_failure_state(attempts)
            google_sheets.update_news_record(
                ws,
                record,
                status=status,
                attempts=next_attempts,
                summary="",
                last_error=str(exc),
            )
            print(f"Nie udalo sie przetworzyc artykulu {record.link}: {exc}")


def _news_entry(record) -> str:
    return f"{record.summary}\n\nLink: {record.link}\n\n################################"


def send_ready_news(config, ws, records) -> None:
    """Wysyla utrwalone rekordy ready i aktualizuje stan dostarczenia."""
    ready_records = []
    news_to_send = []

    for record in records:
        if record.status not in KNOWN_NEWS_STATUSES:
            continue
        if record.status != "ready":
            continue

        attempts = 0 if record.attempts >= MAX_PIPELINE_ATTEMPTS else record.attempts
        if not is_complete_summary_result(record.summary):
            status, next_attempts = _next_failure_state(attempts)
            if status == "pending":
                status = "ready"
            google_sheets.update_news_record(
                ws,
                record,
                status=status,
                attempts=next_attempts,
                last_error="Brak kompletnego podsumowania dla rekordu ready.",
            )
            print(f"Pominieto rekord ready bez kompletnego podsumowania: {record.link}")
            continue

        ready_records.append((record, attempts))
        news_to_send.append(_news_entry(record))

    if not ready_records:
        print("Brak gotowych newsow do wyslania!")
        return

    try:
        sending_emails(config, news_to_send)
    except Exception as exc:
        for record, attempts in ready_records:
            next_attempts = attempts + 1
            status = (
                "failed" if next_attempts >= MAX_PIPELINE_ATTEMPTS else "ready"
            )
            google_sheets.update_news_record(
                ws,
                record,
                status=status,
                attempts=next_attempts,
                last_error=str(exc),
            )
        raise

    for record, _ in ready_records:
        google_sheets.update_news_record(
            ws,
            record,
            status="sent",
            attempts=0,
            last_error="",
        )


def is_complete_summary_result(summary_news: str) -> bool:
    """Sprawdza, czy podsumowanie z modelu nie zostalo uciete."""
    title_match = TITLE_RE.search(summary_news)
    summary_match = SUMMARY_RE.search(summary_news)
    if not title_match or not summary_match:
        return False

    summary = summary_match.group(1).strip()
    if not summary:
        return False

    return bool(SUMMARY_END_RE.search(summary))


def sending_emails(config, news_to_send):
    """Wysyłka emaili"""
    gmail.send_email(
        recipients=config["RECIPIENTS"],
        news_to_send=news_to_send,
        sender_mail=config["SENDER_MAIL"],
        smtp_server=config["SMTP_SERVER"],
        sender_pass=config["SENDER_PASS"],
    )
    print("Newsy zostały wysłane!!!")


def main():
    """
    Główna funkcja orchestrująca kroki skrapowania newsów, ich przetwarzania,
    podsumowania i wysyłki.
    """
    config = load_config()
    ws = open_state_worksheet(config)
    records = google_sheets.read_news_records(ws)
    log_unknown_statuses(records)
    discover_news(config, ws, records)

    records = google_sheets.read_news_records(ws)
    process_pending_news(config, ws, records)

    records = google_sheets.read_news_records(ws)
    send_ready_news(config, ws, records)


if __name__ == "__main__":
    main()
