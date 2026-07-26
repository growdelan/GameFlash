# Specyfikacja techniczna

## Cel

GameFlash automatyzuje zbieranie newsów z branży gier z jednego źródła WWW, przygotowuje krótkie podsumowania po polsku i wysyła je w jednym e-mailu.

Projekt jest przeznaczony dla osoby lub małego zespołu uruchamiającego skrypt lokalnie albo z prostego harmonogramu.

## Aktualny zakres

Aplikacja:

- pobiera listing `https://www.ppe.pl/gry`,
- deterministycznie wyodrębnia linki PPE pasujące do `/news/<id>/<slug>.html`,
- używa Google Sheets jako źródła prawdy o linkach i ich stanie przetwarzania,
- zapisuje nowy link jako `pending` przed pobraniem i podsumowaniem artykułu,
- pobiera treść przez mirror Jina,
- generuje jedno podsumowanie Gemini na poprawnie pobrany news,
- odrzuca puste, ucięte lub niekompletne podsumowania,
- utrwala kompletne podsumowanie jako `ready` przed próbą wysyłki,
- ponawia błędy przetwarzania i SMTP maksymalnie trzy razy na etap,
- wysyła jeden e-mail multipart z warstwą HTML i fallbackiem `plain text`.

Poza aktualnym zakresem pozostają:

- panel użytkownika, CLI, API i interfejs WWW,
- wiele konfigurowalnych źródeł,
- osobny interfejs historii podsumowań i wysyłek,
- kolejki zadań, rozbudowany monitoring, testy end-to-end i automatyczne wdrożenie.

## Granice systemu

GameFlash jest pojedynczym procesem Pythona. Orkiestracja znajduje się w `main.py`, a integracje zewnętrzne są rozdzielone na moduły pomocnicze. System nie ma osobnej warstwy domenowej ani interfejsów abstrakcji.

Usługi zewnętrzne:

- PPE — listing i źródłowe artykuły,
- Google Sheets — trwały stan linków,
- Jina — podstawowa ścieżka pobierania treści artykułów,
- Gemini Developer API — generowanie podsumowań,
- SMTP — dostarczenie e-maila.

Fallback WordPress REST API lub bezpośredni HTML działa wyłącznie dla historycznych adresów `konsolowe.info`; nie stanowi alternatywnego źródła listingu.

## Przepływ danych

1. `main.py` ładuje konfigurację z `.env`.
2. Aplikacja otwiera wskazaną zakładkę Google Sheets i dodaje brakujące kolumny stanu.
3. Pobiera HTML listingu, wyciąga unikalne linki PPE i zapisuje nowe rekordy jako `pending`.
4. Dla każdego `pending` pobiera i waliduje treść, ogranicza wejście modelu do 6500 znaków i wywołuje Gemini.
5. Błąd zwiększa licznik aktualnego etapu; trzecia kolejna porażka ustawia `failed`.
6. Kompletne podsumowanie jest utrwalane jako `Summary`, a rekord przechodzi do `ready`.
7. Wszystkie poprawne rekordy `ready` trafiają do jednego e-maila multipart.
8. Sukces SMTP ustawia `sent`; błąd zachowuje podsumowanie do ponownej wysyłki bez kolejnego wywołania Gemini.

Szczegółowe kontrakty i przypadki błędów opisuje [docs/spec/pipeline.md](docs/spec/pipeline.md).

## Mapa komponentów

- `main.py` — konfiguracja i orkiestracja całego procesu.
- `scrapers/listing.py` — pobranie listingu i parser linków PPE.
- `scrapers/jina.py` — pobranie oraz walidacja treści artykułu; fallback dla `konsolowe.info`.
- `storage/google_sheets.py` — uwierzytelnienie, migracja nagłówka i trwały model stanu rekordów.
- `llms/gemini.py` — prompt, klient Gemini, retry limitów i sanitizacja odpowiedzi.
- `emails/gmail.py` — parsowanie wpisów, rendering HTML i tekstu oraz wysyłka SMTP.
- `tests/` — testy jednostkowe bez wymogu prawdziwych sekretów i stabilnych usług zewnętrznych.

## Najważniejsze kontrakty

### Konfiguracja

Wymagane zmienne środowiskowe:

- `GEMINI_API_KEY`,
- `SMTP_SERVER`,
- `SENDER_MAIL`,
- `SENDER_PASS`,
- `RECIPIENTS`.

Wartości opcjonalne i domyślne:

- `URL` — `https://www.ppe.pl/gry`,
- `GEMINI_MODEL` — `gemini-3.5-flash`,
- `GOOGLE_SHEET_ID` — arkusz stanu PPE wskazany w `main.py`,
- `GOOGLE_SHEET_WORKSHEET` — `Sheet1`,
- `GSPREAD_SERVICE_ACCOUNT_FILE` — `service_account.json`.

Plik konta serwisowego oraz pozostałe sekrety muszą pozostawać poza repozytorium.

### Google Sheets

- Arkusz musi istnieć, być udostępniony kontu serwisowemu i zawierać nagłówek `Links`.
- Aplikacja dopisuje brakujące kolumny `Status`, `Attempts`, `Summary`, `LastError`, `DiscoveredAt` i `UpdatedAt`.
- Pusty arkusz bez nagłówka jest błędem konfiguracji.
- Arkusz zawierający tylko nagłówek oznacza brak zarejestrowanych linków; widoczne newsy mogą zostać przetworzone w pierwszym przebiegu.
- Historyczny wiersz z pustym statusem jest traktowany jak `sent`.
- Nowy link jest dopisywany jako `pending`; kompletne podsumowanie przechodzi przez `ready` do `sent`.
- `Attempts` liczy kolejne porażki bieżącego etapu; trzecia ustawia `failed`.
- Operator może reaktywować rekord, zmieniając `failed` na `pending` albo `ready`.

### Listing

- Akceptowane są wyłącznie linki z tej samej domeny co `base_url`.
- Ścieżka musi pasować do `/news/<id>/<slug>.html`.
- Query string i fragment nie należą do znormalizowanego URL.
- Kolejność pierwszego wystąpienia jest zachowana, a duplikaty są usuwane.

### Treść i LLM

- Odpowiedzi Jina zawierające znane komunikaty błędu oraz treści krótsze niż 200 znaków są niewiarygodne.
- Brak wiarygodnej treści kończy przetwarzanie linku przed wywołaniem Gemini.
- Aktywny pipeline wykonuje jedno wywołanie Gemini na artykuł.
- Czasowe błędy `RESOURCE_EXHAUSTED` są ponawiane maksymalnie cztery razy z uwzględnieniem `retryDelay`.
- Odpowiedź musi zawierać `Tytuł:` i `Podsumowanie:`, a podsumowanie musi kończyć się pełnym zdaniem.

### E-mail

- Wiadomość zawiera reprezentacje `text/plain` i `text/html` tej samej treści.
- Każdy wpis zawiera tytuł, podsumowanie i link.
- HTML używa osadzonego CSS i nie wymaga zewnętrznych fontów, obrazów ani CDN.
- E-mail nie jest wysyłany, jeśli żaden artykuł nie dał kompletnego podsumowania.
- Błąd SMTP zachowuje `Summary` i jest ponawiany bez ponownego generowania treści.

## Stos techniczny

- Python 3.11+,
- `uv` i `pyproject.toml`,
- `requests`,
- `beautifulsoup4`,
- `gspread` i `google-auth`,
- `google-genai`,
- standardowe moduły MIME, `smtplib` i `ssl`.

Nie dodaje się zależności bez uzasadnienia w dokumencie decyzji technicznych.

## Decyzje techniczne

Aktualne, samodzielne decyzje wraz z uzasadnieniem i konsekwencjami znajdują się w [docs/decisions/001-current-architecture.md](docs/decisions/001-current-architecture.md).

Najważniejsze obowiązujące decyzje:

- środowisko i zależności są zarządzane przez `uv`,
- aplikacja pozostaje pojedynczym skryptem orkiestrującym,
- Google Sheets jest źródłem prawdy dla deduplikacji i stanów `pending`, `ready`, `sent`, `failed`,
- parser listingu jest deterministyczny i nie używa LLM,
- zapis `pending` poprzedza przetwarzanie, a zapis `ready` poprzedza SMTP,
- aktywna warstwa LLM używa Gemini i jednego wywołania na news,
- wiadomość jest wysyłana przez SMTP jako multipart.

Historia wcześniejszych wariantów Groq/Qwen, lokalnego pliku stanu, parsera miesięcznego i osobnej korekty pozostaje w Git oraz odpowiednich PRD; nie jest częścią aktualnego kontraktu systemu.

## Jakość i kryteria akceptacji

- `uv sync` przygotowuje środowisko.
- `uv run main.py` jest głównym sposobem uruchomienia.
- `./scripts/verify.sh` przechodzi bez prawdziwych sekretów i niestabilnych usług zewnętrznych.
- Link obecny w Google Sheets nie jest ponownie pobierany ani podsumowywany.
- Błąd append blokuje dalsze przetwarzanie danego linku.
- Błąd pobierania lub Gemini jest ponawiany do trzech prób, a następnie ustawia `failed`.
- Błąd SMTP wykorzystuje zapisane podsumowanie i nie powtarza wywołania Gemini.
- Parser akceptuje wyłącznie prawidłowe newsy PPE i odrzuca obce domeny oraz pozostałe sekcje serwisu.
- Błędna lub zbyt krótka treść nie trafia do promptu.
- Niekompletne podsumowanie nie trafia do e-maila.
- E-mail zachowuje komplet informacji w HTML i `plain text`.
- Sekrety nie są przechowywane w repozytorium.

Walidacje live Google Sheets, Gemini i SMTP są operacyjne i opcjonalne; standardowy zestaw testów korzysta ze stubów lub mocków.

## Indeks dokumentów

- [docs/spec/pipeline.md](docs/spec/pipeline.md) — szczegółowy przepływ, kontrakty integracji i obsługa błędów.
- [docs/decisions/001-current-architecture.md](docs/decisions/001-current-architecture.md) — aktualne decyzje techniczne.
- [ROADMAP.md](ROADMAP.md) — milestone'y i ich statusy.
- [STATUS.md](STATUS.md) — bieżący stan, ryzyka, ostatnia walidacja i następny krok.
- `prd/` — wymagania kolejnych wdrożonych przyrostów; materiał źródłowy, nie bieżący opis operacyjny.

## Zasady zmian i ewolucji

- zmiany funkcjonalne wymagają aktualizacji `ROADMAP.md`,
- trwałe zmiany architektury i kontraktów wymagają aktualizacji `spec.md` lub wskazanego dokumentu szczegółowego,
- nowe zależności wymagają wpisu w decyzjach technicznych,
- refaktory pozostają w granicach aktywnego milestone'u.

## Powiązanie z roadmapą

Milestone'y 0.5 oraz 1.0–1.9 są ukończone. Brak aktywnego milestone'u; kolejna zmiana funkcjonalna powinna rozpocząć się od nowego PRD lub jawnej aktualizacji roadmapy.

## Status specyfikacji

- Data utworzenia: 2026-03-21
- Ostatnia kompakcja: 2026-07-26
- Aktualny zakres obowiązywania: stan repo po Milestone 1.9
