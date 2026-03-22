# GameFlash

Skrypt do podsumowywania newsow z branzy gier.

## Jak to dziala

Skrypt wykorzystuje Google Sheets jako baze stanu przetworzonych linkow. Lista kandydatow do przetworzenia jest wyciagana bezposrednio z HTML strony listingu, a nowe linki sa zapisywane do arkusza przed dalszym przetwarzaniem. Pelna tresc artykulu jest pobierana przez mirror [Jina AI](https://jina.ai), nastepnie model Llama 3.3 70B uruchamiany przez [Groq](https://groq.com) przygotowuje podsumowanie i korekte, a wynik trafia do zbiorczego e-maila.

## Wymagania

- `uv`
- konto Groq i klucz API
- konto Google z arkuszem udostepnionym kontu serwisowemu
- konto SMTP do wysylki e-maili

## Konfiguracja

1. Skopiuj `.env.example` do `.env`.
2. Uzupelnij wartosci zmiennych:
   - `GROQ_API_KEY`
   - `GOOGLE_SHEET_ID`
   - `GOOGLE_SHEET_WORKSHEET`
   - `GSPREAD_SERVICE_ACCOUNT_FILE`
   - `SMTP_SERVER`
   - `SENDER_MAIL`
   - `SENDER_PASS`
   - `RECIPIENTS`

## Uruchomienie

Synchronizacja srodowiska:

```bash
uv sync
```

Uruchomienie aplikacji:

```bash
uv run main.py
```

## Testy

Projekt uzywa `unittest`. Standardowa komenda:

```bash
uv run python -m unittest discover -s tests -p "test_*.py"
```

Testy obejmuja Google Sheets, parser listingu oraz finalny pipeline przetwarzania linkow w trybie stubowanym.

## Przykladowy wynik

![Przykladowy wynik](/Users/gohan/IT/DevOps/Programowanie/Python/Projekty/GameFlash/img/01.png)
