# GameFlash

Skrypt do podsumowywania newsow z branzy gier.

## Jak to dziala

Skrypt wykorzystuje Google Sheets jako trwaly magazyn linkow i stanu ich przetwarzania. Lista kandydatow jest wyciagana bezposrednio z HTML listingu `https://www.ppe.pl/gry`; parser bierze tylko linki newsow PPE w formacie `/news/<id>/<slug>.html`. Nowe linki sa zapisywane jako `pending`. Pelna tresc jest pobierana przez mirror [Jina AI](https://jina.ai), a dla historycznych linkow z `konsolowe.info` dostepny jest fallback WordPress REST API lub bezposredni HTML. Gemini przygotowuje podsumowanie, ktore przed wysylka jest utrwalane jako `ready`. Sukces SMTP ustawia `sent`, a bledy pobierania, Gemini i wysylki sa ponawiane maksymalnie trzy razy na etap. Retry SMTP korzysta z zapisanego podsumowania. Domyslnym modelem jest `gemini-3.5-flash`.

## Wymagania

- `uv`
- konto Google AI Studio/Gemini i klucz API
- konto Google z arkuszem udostepnionym kontu serwisowemu
- konto SMTP do wysylki e-maili

## Konfiguracja

1. Skopiuj `.env.example` do `.env`.
2. Uzupelnij wartosci zmiennych:
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL` (domyslnie `gemini-3.5-flash`)
   - `URL` (domyslnie `https://www.ppe.pl/gry`)
   - `GOOGLE_SHEET_ID` (domyslnie arkusz `gameflash_sheet_ppe`: `1N82WxjskvsIyjlfwh8CxlhHJB9LEUMwbAdCI8w0J_yk`)
   - `GOOGLE_SHEET_WORKSHEET` (domyslnie `Sheet1`)
   - `GSPREAD_SERVICE_ACCOUNT_FILE`
   - `SMTP_SERVER`
   - `SENDER_MAIL`
   - `SENDER_PASS`
   - `RECIPIENTS`

Arkusz musi zawierac kolumne `Links`. Przy pierwszym uruchomieniu aplikacja automatycznie dopisze brakujace kolumny `Status`, `Attempts`, `Summary`, `LastError`, `DiscoveredAt` i `UpdatedAt`. Istniejace wiersze bez statusu sa traktowane jak `sent` i nie zostana wyslane ponownie.

Rekord po trzech bledach aktualnego etapu otrzymuje status `failed`. Aby ponowic pelne przetwarzanie, zmien jego status recznie na `pending`. Aby ponowic tylko wysylke zachowanego podsumowania, zmien status na `ready`.

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

Testy obejmuja migracje schematu i przejscia stanu Google Sheets, retry przetwarzania i SMTP, parser listingu PPE, fallback pobierania tresci oraz renderowanie i wysylke stylowanego e-maila HTML bez realnego SMTP.

Klient Gemini ponawia czasowe bledy limitu `RESOURCE_EXHAUSTED` zgodnie z `retryDelay` zwracanym przez API. Pipeline odrzuca ucięte podsumowania przed wysylka maila.

Opcjonalna walidacja live modelu Gemini, bez zapisu do Google Sheets i bez wysylki SMTP:

```bash
RUN_LIVE_GEMINI_VALIDATION=1 uv run python -m unittest tests.test_milestone_1_4.GeminiLiveValidationTests
```

Walidacja wymaga `GEMINI_API_KEY` w `.env`. Standardowe testy pomijaja ten scenariusz.

## Przykladowy wynik

![Przykladowy wynik](/Users/gohan/IT/DevOps/Programowanie/Python/Projekty/GameFlash/img/01.png)
