# GameFlash

Skrypt do podsumowywania newsow z branzy gier.

## Jak to dziala

Skrypt wykorzystuje Google Sheets jako baze stanu przetworzonych linkow. Lista kandydatow do przetworzenia jest wyciagana bezposrednio z HTML strony listingu, a nowe linki sa zapisywane do arkusza przed dalszym przetwarzaniem. Pelna tresc artykulu jest pobierana przez mirror [Jina AI](https://jina.ai), nastepnie model Groq wskazany w `LLM_MODEL` przygotowuje podsumowanie i korekte, a wynik trafia do zbiorczego e-maila wysylanego jako multipart: stylowany HTML z fallbackiem `plain text`. Domyslnym modelem jest `qwen/qwen3.6-27b`.

## Wymagania

- `uv`
- konto Groq i klucz API
- konto Google z arkuszem udostepnionym kontu serwisowemu
- konto SMTP do wysylki e-maili

## Konfiguracja

1. Skopiuj `.env.example` do `.env`.
2. Uzupelnij wartosci zmiennych:
   - `GROQ_API_KEY`
   - `LLM_MODEL` (domyslnie `qwen/qwen3.6-27b`)
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

Testy obejmuja Google Sheets, parser listingu, finalny pipeline przetwarzania linkow w trybie stubowanym oraz renderowanie i wysylke stylowanego e-maila HTML bez realnego SMTP.

Opcjonalna walidacja live modelu Qwen, bez zapisu do Google Sheets i bez wysylki SMTP:

```bash
RUN_LIVE_GROQ_VALIDATION=1 uv run python -m unittest tests.test_milestone_1_4.QwenLiveValidationTests
```

Walidacja wymaga `GROQ_API_KEY` w `.env`. Standardowe testy pomijaja ten scenariusz.

## Przykladowy wynik

![Przykladowy wynik](/Users/gohan/IT/DevOps/Programowanie/Python/Projekty/GameFlash/img/01.png)
