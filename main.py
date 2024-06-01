"""Głowny plik skryptu"""

import os
from dotenv import load_dotenv

from llms import groq
from scrapers import jina
from utils import utils
from emails import gmail


def load_config():
    """
    Ładuje zmienne konfiguracyjne z pliku .env.
    """
    load_dotenv()
    return {
        "DATABASE_PATH": "news_links.json",
        "URL": "https://www.eurogamer.pl/news",
        "GROQ_API": os.getenv("GROQ_API_KEY"),
        "LLM_MODEL": "llama3-70b-8192",
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
    news_prompt = groq.news_system_prompt()
    print(f"Prompt dla ekstrakcji linków:\n{news_prompt}\n")
    news_model_options = groq.model_options(
        system_prompt=news_prompt,
        user_text=news,
        temperature=0,
        max_tokens=1024,
        json_mode=True,
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


def summarize_news_and_send(config, new_links):
    """
    Podsumowuje nowe linki do newsów i wysyła email z podsumowaniami.
    """
    if new_links:
        utils.update_database(
            database_path=config["DATABASE_PATH"], new_links=new_links
        )
        print("Baza została zaktualizowana")
        news_to_send = []
        summary_prompt = groq.summary_system_prompt()
        print(f"Prompt do podsumowania newsów:\n{summary_prompt}\n")
        for news in new_links:
            read_news = jina.jina_scraper(url=news)
            summary_model_options = groq.model_options(
                system_prompt=summary_prompt,
                user_text=read_news,
                temperature=0,
                max_tokens=1024,
                json_mode=False,
            )
            summary_news = groq.run_groq_model(
                groq_api_key=config["GROQ_API"],
                model=config["LLM_MODEL"],
                options=summary_model_options,
            )
            news_to_send.append(f"{summary_news}\n\n################################")
            print(summary_news)
        print(f"Newsy do wysłania:\n{news_to_send}")

        if news_to_send:
            gmail.send_email(
                recipients=config["RECIPIENTS"],
                news_to_send=news_to_send,
                sender_mail=config["SENDER_MAIL"],
                smtp_server=config["SMTP_SERVER"],
                sender_pass=config["SENDER_PASS"],
            )
            print("Newsy zostały wysłane!!!")
    else:
        print("Brak nowych linków")


def main():
    """
    Główna funkcja orchestrująca kroki skrapowania newsów, ich przetwarzania,
    podsumowania i wysyłki.
    """
    config = load_config()
    new_links = fetch_and_process_news(config)
    summarize_news_and_send(config, new_links)


if __name__ == "__main__":
    main()
