# Pipeline i kontrakty integracji

Aktualne kontrakty po migracji do OpenAI Responses API (2026-11-07).

## Konfiguracja i start

`main.py` ładuje `.env` przez `python-dotenv`. Głównym entrypointem jest:

```bash
uv run main.py
```

Konfiguracja obejmuje URL listingu, dane OpenAI, SMTP, odbiorców oraz dostęp do Google Sheets. Aplikacja nie wykonuje kompleksowej walidacji wszystkich wartości przed startem; błędy mogą ujawnić się dopiero przy użyciu danej integracji.

## Trwaly stan w Google Sheets

1. `storage.google_sheets.authenticate_gspread()` tworzy klienta na podstawie pliku konta serwisowego.
2. `open_sheet()` otwiera dokument po ID i zakładkę po nazwie.
3. `ensure_state_schema()` wymaga kolumny `Links` i dopisuje brakujące nagłówki stanu na końcu pierwszego wiersza.
4. `read_news_records()` zwraca link, status, licznik, podsumowanie, informacje diagnostyczne i numer wiersza.
5. `append_pending_link()` dopisuje nowy rekord z `Status=pending`, `Attempts=0` i czasem UTC.
6. `update_news_record()` aktualizuje stan istniejącego rekordu według numeru wiersza.

Brak dokumentu, dostępu albo zakładki jest prezentowany jako błąd domenowy. Pusty arkusz i brak kolumny `Links` również są błędami konfiguracji. Historyczny wiersz bez statusu jest interpretowany jako `sent`, dzięki czemu migracja nagłówka nie wysyła ponownie starych newsów.

W trakcie jednego przebiegu `main.py` utrzymuje dodatkowy zbiór `seen_this_run`. Zapobiega to powtórnemu append tego samego linku, gdy listing zawiera duplikaty.

## Listing PPE

`scrapers.listing.fetch_listing_html()` pobiera HTML przez `requests` z timeoutem 30 sekund i wymaga poprawnego statusu HTTP.

`extract_news_links()`:

- analizuje wszystkie elementy `a[href]`,
- normalizuje link przez `urljoin`,
- odrzuca inną domenę niż domena `base_url`,
- akceptuje ścieżkę zgodną z `^/news/\d+/[^/]+\.html$`,
- usuwa query string i fragment,
- usuwa duplikaty bez zmiany kolejności.

Parser nie filtruje linków według daty. Aktywnym kryterium jest typ ścieżki PPE.

## Kolejność deduplikacji i przejścia stanów

Dla każdego linku z listingu:

1. Link obecny w Google Sheets lub `seen_this_run` jest pomijany.
2. Aplikacja próbuje dopisać link jako `pending`.
3. Błąd append jest logowany i kończy obsługę tego linku.
4. Po udanym append rekord może zostać przetworzony w tym samym przebiegu.

Rekord `pending` po udanym pobraniu i podsumowaniu przechodzi do `ready`. Blad zwieksza `Attempts`; pierwsza i druga porazka pozostawiaja rekord w biezacym etapie, a trzecia ustawia `failed`. `Attempts` jest zerowane po przejsciu z `pending` do `ready`.

Reczna zmiana `failed` na `pending` ponawia pobranie i OpenAI. Zmiana na `ready` ponawia wysylke zachowanego `Summary`. Wyczerpany licznik jest wtedy zerowany przy nastepnym podjeciu.

## Pobieranie treści artykułu

Podstawowa ścieżka w `scrapers.jina.fetch_article_text()` pobiera `https://r.jina.ai/<url>` z timeoutem 30 sekund.

Treść jest normalizowana i odrzucana, gdy:

- zawiera `Title: 403 Forbidden`,
- zawiera `Warning: Target URL returned error 403`,
- po normalizacji ma mniej niż 200 znaków.

Dla adresów `konsolowe.info` błąd Jina uruchamia fallback:

1. bezpośrednie pobranie strony,
2. próba ustalenia ID wpisu WordPress,
3. próba WordPress REST API,
4. w razie niepowodzenia ekstrakcja treści z HTML.

Dla PPE nie istnieje fallback po błędzie Jina. Brak wiarygodnej treści powoduje pominięcie linku bez wywołania LLM.

Przed zbudowaniem promptu `main.prepare_article_text_for_summary()` ogranicza tekst do 6500 znaków, nie przecina ostatniego słowa i dodaje informację o pominiętej części.

## Generowanie podsumowania

`llms.openai_summary.summary_prompt()` wymaga odpowiedzi po polsku w formacie:

```text
Tytuł: <tytuł>

Podsumowanie: <3–4 pełne zdania, maksymalnie 90 słów>
```

Klient `openai` (oficjalny SDK, zaleznosc zarzadzana przez uv):

- wywoluje Responses API z `model=gpt-6-luna`, `reasoning.effort=medium`, `store=False`,
- uzywa timeoutu 60 sekund, bez automatycznych retry SDK,
- rezerwuje 4096 tokenow na odpowiedz wraz z reasoning; nie przekazuje temperatury,
- wykonuje maksymalnie dwa retry dla HTTP 408, 409, 429, 5xx i bledow polaczenia,
- respektuje `Retry-After` / `retry-after-ms` do 30 sekund; dluzsze opoznienie przerywa probe,
- nie ponawia bledow uprawnien ani `insufficient_quota`,
- wymaga statusu `completed` i niepustego `output_text`; odrzuca odpowiedzi uciete,
- usuwa ewentualne bloki `<think>...</think>`,
- nie loguje surowych odpowiedzi HTTP ani tresci bledow dostawcy.

`main.is_complete_summary_result()` wymaga tytułu, niepustego podsumowania i znaku kończącego pełne zdanie. Niepoprawny wynik jest pomijany.

## Budowanie i wysyłka e-maila

Każde kompletne podsumowanie jest łączone z oryginalnym linkiem. `emails.gmail` wyodrębnia trzy pola: tytuł, podsumowanie i link.

Warstwa mailowa buduje:

- fallback `text/plain` zawierający wszystkie wpisy,
- stylowany HTML z osobną kartą dla każdego newsa,
- wiadomość `multipart/alternative` wysyłaną przez SMTP z TLS.

Treści są escapowane przed umieszczeniem w HTML. Styl nie wymaga zewnętrznych zasobów. Lista odbiorców pochodzi z rozdzielonej przecinkami zmiennej `RECIPIENTS`.

Do jednego e-maila trafiaja wszystkie poprawne rekordy `ready`, w tym pozostawione przez wczesniejszy przebieg. Sukces ustawia je na `sent`. Blad SMTP zwieksza licznik etapu wysylki, zachowuje `Summary` i jest ponownie zglaszany procesowi. Kolejna proba nie wywoluje Jina ani OpenAI.

Jeżeli listing nie zawiera nowych linków i arkusz nie zawiera poprawnych rekordow `ready`, SMTP nie jest wywoływane. Dostarczanie ma semantyke at-least-once: awaria po przyjeciu wiadomosci przez SMTP, ale przed zapisem `sent`, moze spowodowac duplikat.

## Obsługa błędów i ryzyka

- Błąd inicjalizacji lub odczytu Google Sheets przerywa przebieg.
- Błąd append dotyczy tylko jednego linku; kolejne mogą być przetwarzane.
- Błąd pobrania, OpenAI lub walidacji podsumowania dotyczy jednego artykułu i podlega limitowi trzech prób.
- Błąd SMTP zachowuje gotowe podsumowania i podlega osobnemu limitowi trzech prób.
- Nieznany niepusty status jest logowany i pomijany.
- Entrypoint stosuje lokalny flock i limit 1800 sekund (kody 75/124); blokada nie synchronizuje roznych hostow.
- Zapis pol jednego rekordu jest atomowym batch update; ogranicza ryzyko ready bez Summary i zuzycie limitow Sheets.
- Bledy przetwarzania artykulow skutkuja niezerowym kodem po probie wyslania pozostalych gotowych podsumowan.
- Dostępność pipeline'u zależy od PPE, Google Sheets, Jina, OpenAI i SMTP.
- Standardowe testy nie potwierdzają dostępności usług live.

## Walidacja

Podstawowa walidacja repo:

```bash
./scripts/verify.sh
```

Walidacje live wymagają jawnego uruchomienia i poprawnych sekretów. Nie należą do podstawowego zestawu testów.
