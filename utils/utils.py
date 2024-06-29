"""Funckje zawsierające opreacje na plikach"""

import os
import json
from datetime import datetime


def current_yera_and_month():
    """Obecny rok i miesiąc"""
    current_date = datetime.now()
    year = current_date.year
    month = current_date.strftime("%m")
    return year, month


def parse_news_response(news_resposne: str) -> list:
    """Wyciągnięcie listy linków z JSON"""
    news_dict = json.loads(news_resposne)
    return news_dict.get("links", [])


def initialize_database(database_path: str) -> None:
    """Inicjowanie bazy danych z linkami jeśli nie istnieje"""
    if not os.path.exists(database_path):
        with open(database_path, "w", encoding="utf-8") as file:
            json.dump({"links": []}, file)
            print(f"Utworzono bazę: {database_path}")
    else:
        print(f"Znaleziono bazę: {database_path}")


def filter_new_links(database_path: str, news_links: list) -> list:
    """
    Sprawdzenie które liniki istnieją w bazie a które nie i pozostawienie
    tylko nowych linków
    """
    if os.path.exists(database_path):
        with open(database_path, "r", encoding="utf-8") as file:
            json_list = json.load(file)
            existing_links = json_list["links"]
            print(f"Linki załadowane z bazy:\n{existing_links}\n")
    else:
        existing_links = []

    return [link for link in news_links if link not in existing_links]


def update_database(database_path: str, new_links: list):
    """Aktualizacja bazy danych o nowe linki"""
    with open(database_path, "r", encoding="utf-8") as file:
        database = json.load(file)

    database["links"].extend(new_links)

    with open(database_path, "w", encoding="utf-8") as file:
        json.dump(database, file, indent=4)
