"""Głowny plik skryptu"""

import os
from dotenv import load_dotenv

from llms import groq
from scrapers import jina, lang_webbaseloader
from utils import utils
from emails import gmail


def load_config():
    """
    Ładuje zmienne konfiguracyjne z pliku .env.
    """
    load_dotenv()
    return {
        "DATABASE_PATH": "news_links.json",
        "URL": "https://konsolowe.info/playstation/ps5/",
        "GROQ_API": os.getenv("GROQ_API_KEY"),
        "LLM_MODEL": "llama-3.1-70b-versatile",
        "SMTP_SERVER": os.getenv("SMTP_SERVER"),
        "SENDER_MAIL": os.getenv("SENDER_MAIL"),
        "SENDER_PASS": os.getenv("SENDER_PASS"),
        "RECIPIENTS": os.getenv("RECIPIENTS").split(","),
    }


def fetch_and_process_news(config):
    """
    Pobiera newsy z określonego URL i przetwarza je w celu wyodrębnienia nowych linków.
    """
    utils.initialize_database(config["DATABASE_PATH"])

    news = jina.jina_scraper(url=config["URL"])
    year, month = utils.current_yera_and_month()
    news_model_options = groq.model_options(
        prompt=groq.news_prompt(year, month, news),
        temperature=0.2,
        max_tokens=1600,
    )
    news_response = groq.run_groq_model(
        groq_api_key=config["GROQ_API"],
        model=config["LLM_MODEL"],
        options=news_model_options,
    )
    print(f"Odpowiedź JSON:\n{news_response}\n")

    parse_news_response = utils.parse_news_response(news_response)
    new_links = utils.filter_new_links(
        database_path=config["DATABASE_PATH"], news_links=parse_news_response
    )
    print(f"Nowe linki: {new_links}")
    return new_links


def summarize_news(config, new_links):
    """
    Podsumowuje nowe linki do newsów i wysyła email z podsumowaniami.
    """
    utils.update_database(database_path=config["DATABASE_PATH"], new_links=new_links)
    print("Baza została zaktualizowana")
    news_to_corrected = []
    for news in new_links:
        read_news = lang_webbaseloader.webbaseloader(url=news)
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
        news_to_corrected.append(
            f"{summary_news}\n\nLink: {news}\n\n################################"
        )
        print(summary_news)
    print(f"Newsy do podsumowania:\n{news_to_corrected}")
    return news_to_corrected


def news_proofreading(config, news_to_corrected):
    """Przeprowadza korektę na podsumowanych newsach"""
    news_to_send = []
    for news in news_to_corrected:
        proofreading_model_options = groq.model_options(
            prompt=groq.proofreading_prompt(news),
            temperature=1,
            max_tokens=1024,
        )
        proofreading_news = groq.run_groq_model(
            groq_api_key=config["GROQ_API"],
            model=config["LLM_MODEL"],
            options=proofreading_model_options,
        )
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
        news_to_send = news_proofreading(config, news_to_corrected)
        sending_emails(config, news_to_send)
    else:
        print("Brak nowych newsów do wysłania!")


if __name__ == "__main__":
    main()
