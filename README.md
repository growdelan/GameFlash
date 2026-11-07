# GameFlash

Skrypt do podsumowywania newsow z branzy gier.

## Jak to dziala

Skrypt wykorzystuje Google Sheets jako trwaly magazyn linkow i stanu ich przetwarzania. Lista kandydatow jest wyciagana bezposrednio z HTML listingu `https://www.ppe.pl/gry`; parser bierze tylko linki newsow PPE w formacie `/news/<id>/<slug>.html`. Nowe linki sa zapisywane jako `pending`. Pelna tresc jest pobierana przez mirror [Jina AI](https://jina.ai), a dla historycznych linkow z `konsolowe.info` dostepny jest fallback WordPress REST API lub bezposredni HTML. OpenAI Responses API przygotowuje podsumowanie, ktore przed wysylka jest utrwalane jako `ready`. Sukces SMTP ustawia `sent`, a bledy pobierania, OpenAI i wysylki sa ponawiane maksymalnie trzy razy na etap. Retry SMTP korzysta z zapisanego podsumowania. Domyslnym modelem jest `gpt-6-luna` z `reasoning.effort=medium`.

## Wymagania

- `uv`
- konto OpenAI API i klucz projektu
- konto Google z arkuszem udostepnionym kontu serwisowemu
- konto SMTP do wysylki e-maili

## Konfiguracja

1. Skopiuj `.env.example` do `.env`.
2. Uzupelnij wartosci zmiennych:
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL` (domyslnie `gpt-6-luna`)
   - `OPENAI_REASONING_EFFORT` (domyslnie `medium`)
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

Klient OpenAI ma timeout 60 sekund i maksymalnie dwa ponowienia dla bledow przejsciowych. Akceptuje `Retry-After` do 30 sekund; dluzszy okres oczekiwania konczy probe i pozostawia retry kolejnemu cronowi. Wyczerpanie budzetu API i bledy autoryzacji nie sa ponawiane w tym samym przebiegu. Odpowiedz musi miec status `completed`, tytul i pelne podsumowanie. API otrzymuje `store=False`.

Entrypoint chroni plik `.gameflash.lock` (blokada `flock`) i limit 30 minut. Druga instancja zwraca kod 75, timeout kod 124, a blad przebiegu kod 1. Bledy przetwarzania artykulow sa raportowane monitoringowi nawet wtedy, gdy inne podsumowania udalo sie dostarczyc. Blokada dziala tylko na jednym hoscie; nie uruchamiaj rownolegle produkcji lokalnie i na Pi.

Opcjonalna walidacja live OpenAI, bez Google Sheets i SMTP:

```bash
RUN_LIVE_OPENAI_VALIDATION=1 uv run python -m unittest tests.test_openai_summary.OpenAILiveValidationTests
```

Pelny smoke wszystkich integracji na skonfigurowanym hoscie (odczyt Sheets, PPE/Jina, OpenAI, rendering MIME, TLS/login SMTP; bez zapisow i wysylki):

```bash
uv run --frozen python -m scripts.smoke
```

Walidacja wymaga `OPENAI_API_KEY` w `.env`. Standardowe testy pomijaja ten scenariusz. `.env` i kopie sekretow sa ignorowane przez Git; utrzymuj uprawnienia `0600` i nie wlaczaj logowania debug HTTP. Nie przekazuj kluczy w argumentach polecen.

Plan wdrozenia, kryteria odbioru i rollback: [docs/deployment-openai.md](docs/deployment-openai.md). Kontrakty: [docs/spec/pipeline.md](docs/spec/pipeline.md).

## Przykladowy wynik

![Przykladowy wynik](/Users/gohan/IT/DevOps/Programowanie/Python/Projekty/GameFlash/img/01.png)
