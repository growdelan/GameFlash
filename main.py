"""Głowny plik skryptu"""

import os
import re
from dotenv import load_dotenv

from llms import groq
from scrapers import jina, listing
from emails import gmail
from storage import google_sheets
from utils import utils

DEFAULT_LLM_MODEL = "qwen/qwen3.6-27b"
LINK_RE = re.compile(r"^Link:\s*(\S+)\s*$", re.MULTILINE)
TITLE_RE = re.compile(r"^Tytu[łl]:\s*(.+)$", re.MULTILINE)
SUMMARY_RE = re.compile(r"Podsumowanie:\s*(.+?)(?:\n\s*\nLink:|\nLink:|\Z)", re.DOTALL)
SUMMARY_END_RE = re.compile(r"[.!?…][\"'”’)]*\s*$")


def load_config():
    """
    Ładuje zmienne konfiguracyjne z pliku .env.
    """
    load_dotenv()
    return {
        "URL": "https://konsolowe.info/playstation/ps5/",
        "GROQ_API": os.getenv("GROQ_API_KEY"),
        "LLM_MODEL": os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL),
        "SMTP_SERVER": os.getenv("SMTP_SERVER"),
        "SENDER_MAIL": os.getenv("SENDER_MAIL"),
        "SENDER_PASS": os.getenv("SENDER_PASS"),
        "RECIPIENTS": os.getenv("RECIPIENTS").split(","),
        "GOOGLE_SHEET_ID": os.getenv(
            "GOOGLE_SHEET_ID", "1o0htAcR-8ej4u9GiRCYHxxvFKE7BhCaryB6nqkM-KTI"
        ),
        "GOOGLE_SHEET_WORKSHEET": os.getenv("GOOGLE_SHEET_WORKSHEET", "Arkusz1"),
        "GSPREAD_SERVICE_ACCOUNT_FILE": os.getenv(
            "GSPREAD_SERVICE_ACCOUNT_FILE", "service_account.json"
        ),
    }


def fetch_and_process_news(config):
    """
    Pobiera newsy z określonego URL i przetwarza je w celu wyodrębnienia nowych linków.
    """
    gc = google_sheets.authenticate_gspread(config["GSPREAD_SERVICE_ACCOUNT_FILE"])
    _, ws = google_sheets.open_sheet(
        gc=gc,
        spreadsheet_id=config["GOOGLE_SHEET_ID"],
        worksheet_title=config["GOOGLE_SHEET_WORKSHEET"],
    )
    registered_links = google_sheets.read_registered_links(ws)

    news = listing.fetch_listing_html(url=config["URL"])
    year, month = utils.current_yera_and_month()
    parse_news_response = listing.extract_news_links(news, year, month)
    new_links = []
    seen_this_run = set()
    for link in parse_news_response:
        if link in registered_links or link in seen_this_run:
            continue
        try:
            google_sheets.append_link(ws, link)
        except Exception as exc:
            print(f"Nie udalo sie dopisac linku do Google Sheets: {link} ({exc})")
            continue
        registered_links.add(link)
        seen_this_run.add(link)
        new_links.append(link)
    print(f"Nowe linki: {new_links}")
    return new_links


def summarize_news(config, new_links):
    """
    Podsumowuje nowe linki do newsów i wysyła email z podsumowaniami.
    """
    news_to_corrected = []
    for news in new_links:
        try:
            read_news = jina.fetch_article_text(url=news)
            summary_model_options = groq.model_options(
                prompt=groq.summary_prompt(read_news),
                temperature=0.8,
                max_tokens=1024,
            )
            summary_news = groq.run_groq_model(
                groq_api_key=config["GROQ_API"],
                model=config["LLM_MODEL"],
                options=summary_model_options,
            )
        except Exception as exc:
            print(f"Nie udalo sie przetworzyc artykulu {news}: {exc}")
            continue

        news_to_corrected.append(
            f"{summary_news}\n\nLink: {news}\n\n################################"
        )
        print(summary_news)
    print(f"Newsy do podsumowania:\n{news_to_corrected}")
    return news_to_corrected


def ensure_link_in_proofreading_result(proofreading_news: str, source_news: str) -> str:
    """Zachowuje link z wejscia, jesli model pominie go w korekcie."""
    if LINK_RE.search(proofreading_news):
        return proofreading_news

    link_match = LINK_RE.search(source_news)
    if not link_match:
        return proofreading_news

    return f"{proofreading_news.rstrip()}\n\nLink: {link_match.group(1)}"


def is_complete_proofreading_result(proofreading_news: str) -> bool:
    """Sprawdza minimalna kompletnosc wyniku korekty przed wysylka."""
    title_match = TITLE_RE.search(proofreading_news)
    summary_match = SUMMARY_RE.search(proofreading_news)
    link_match = LINK_RE.search(proofreading_news)
    if not title_match or not summary_match or not link_match:
        return False

    summary = summary_match.group(1).strip()
    if not summary:
        return False

    return bool(SUMMARY_END_RE.search(summary))


def news_proofreading(config, news_to_corrected):
    """Przeprowadza korektę na podsumowanych newsach"""
    news_to_send = []
    for news in news_to_corrected:
        try:
            proofreading_model_options = groq.model_options(
                prompt=groq.proofreading_prompt(news),
                temperature=0.2,
                max_tokens=7200,
            )
            proofreading_news = groq.run_groq_model(
                groq_api_key=config["GROQ_API"],
                model=config["LLM_MODEL"],
                options=proofreading_model_options,
            )
            proofreading_news = ensure_link_in_proofreading_result(
                proofreading_news, news
            )
            if not is_complete_proofreading_result(proofreading_news):
                print("Pominieto niekompletny wynik korekty newsa.")
                continue
        except Exception as exc:
            print(f"Nie udalo sie wykonac korekty newsa: {exc}")
            continue

        news_to_send.append(f"{proofreading_news}\n\n################################")
        print(news_to_send)
    print(f"Newsy po korekcie:\n{news_to_send}")
    return news_to_send


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
    new_links = fetch_and_process_news(config)
    if new_links:
        news_to_corrected = summarize_news(config, new_links)
        if not news_to_corrected:
            print("Brak poprawnie przetworzonych newsow do wyslania!")
            return
        news_to_send = news_proofreading(config, news_to_corrected)
        if not news_to_send:
            print("Brak newsow po korekcie do wyslania!")
            return
        sending_emails(config, news_to_send)
    else:
        print("Brak nowych newsów do wysłania!")


if __name__ == "__main__":
    main()
