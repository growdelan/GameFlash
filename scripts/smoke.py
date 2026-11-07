"""Jawna walidacja integracji live, bez zapisu w Sheets i bez wysylki maila."""

import smtplib
import ssl

import main
from emails import gmail
from storage import google_sheets
from utils.runtime import run_exclusive


def smoke():
    config = main.load_config()
    gc = google_sheets.authenticate_gspread(config["GSPREAD_SERVICE_ACCOUNT_FILE"])
    _, ws = google_sheets.open_sheet(
        gc, config["GOOGLE_SHEET_ID"], config["GOOGLE_SHEET_WORKSHEET"]
    )
    records = google_sheets.read_news_records(ws)
    print(f"Sheets: odczyt OK, {len(records)} rekordow.")

    listing = main.listing.fetch_listing_html(config["URL"])
    links = main.listing.extract_news_links(listing, config["URL"])
    if not links:
        raise RuntimeError("Listing PPE nie zwrocil artykulow.")
    summary = main.summarize_link(config, links[0])
    print(
        f"PPE/Jina/OpenAI: OK, model={config['OPENAI_MODEL']}, "
        f"effort={config['OPENAI_REASONING_EFFORT']}, kompletne podsumowanie."
    )
    entry = f"{summary}\n\nLink: {links[0]}"
    if not gmail.build_email_html([entry]) or not gmail.build_plain_text_body([entry]):
        raise RuntimeError("Nie udalo sie zbudowac wiadomosci.")

    with smtplib.SMTP(config["SMTP_SERVER"], 587, timeout=30) as server:
        server.ehlo()
        server.starttls(context=ssl.create_default_context())
        server.ehlo()
        server.login(config["SENDER_MAIL"], config["SENDER_PASS"])
    print("SMTP: TLS i login OK. MIME: OK. Nie wyslano maila ani nie zmieniono Sheets.")


if __name__ == "__main__":
    raise SystemExit(run_exclusive(smoke, timeout=300))
