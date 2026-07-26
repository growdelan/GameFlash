# Pipeline i kontrakty integracji

Ten dokument rozwija aktualne kontrakty operacyjne z `spec.md`. Opisuje stan po Milestone 1.8, a nie historię wdrażania kolejnych PRD.

## Konfiguracja i start

`main.py` ładuje `.env` przez `python-dotenv`. Głównym entrypointem jest:

```bash
uv run main.py
```

Konfiguracja obejmuje URL listingu, dane Gemini, SMTP, odbiorców oraz dostęp do Google Sheets. Aplikacja nie wykonuje kompleksowej walidacji wszystkich wartości przed startem; błędy mogą ujawnić się dopiero przy użyciu danej integracji.

## Rejestr linków

1. `storage.google_sheets.authenticate_gspread()` tworzy klienta na podstawie pliku konta serwisowego.
2. `open_sheet()` otwiera dokument po ID i zakładkę po nazwie.
3. `read_registered_links()` wymaga pierwszego wiersza z kolumną `Links` i zwraca zbiór niepustych wartości z tej kolumny.
4. `append_link()` dopisuje link jako nowy wiersz z `value_input_option="RAW"`.

Brak dokumentu, dostępu albo zakładki jest prezentowany jako błąd domenowy. Pusty arkusz i brak kolumny `Links` również są błędami konfiguracji.

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

## Kolejność deduplikacji i zapisu

Dla każdego linku z listingu:

1. Link obecny w Google Sheets lub `seen_this_run` jest pomijany.
2. Aplikacja próbuje dopisać link do arkusza.
3. Błąd append jest logowany i kończy obsługę tego linku.
4. Po udanym append link trafia do zbiorów stanu i listy przeznaczonej do przetwarzania.

Ta kolejność zapewnia deduplikację między uruchomieniami, ale oznacza brak automatycznego retry, gdy później zawiedzie Jina, Gemini albo SMTP.

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

`llms.gemini.summary_prompt()` wymaga odpowiedzi po polsku w formacie:

```text
Tytuł: <tytuł>

Podsumowanie: <3–4 pełne zdania, maksymalnie 90 słów>
```

Klient:

- używa timeoutu 60 sekund,
- przekazuje temperaturę `0.8` i limit 2048 tokenów wyjściowych,
- ponawia czasowe błędy limitu maksymalnie cztery razy,
- respektuje `retryDelay` z odpowiedzi API, a bez niego czeka domyślnie 25 sekund,
- usuwa ewentualne bloki `<think>...</think>`,
- zgłasza błąd dla pustej odpowiedzi.

`main.is_complete_summary_result()` wymaga tytułu, niepustego podsumowania i znaku kończącego pełne zdanie. Niepoprawny wynik jest pomijany.

## Budowanie i wysyłka e-maila

Każde kompletne podsumowanie jest łączone z oryginalnym linkiem. `emails.gmail` wyodrębnia trzy pola: tytuł, podsumowanie i link.

Warstwa mailowa buduje:

- fallback `text/plain` zawierający wszystkie wpisy,
- stylowany HTML z osobną kartą dla każdego newsa,
- wiadomość `multipart/alternative` wysyłaną przez SMTP z TLS.

Treści są escapowane przed umieszczeniem w HTML. Styl nie wymaga zewnętrznych zasobów. Lista odbiorców pochodzi z rozdzielonej przecinkami zmiennej `RECIPIENTS`.

Jeżeli listing nie zawiera nowych linków albo żaden artykuł nie da kompletnego podsumowania, SMTP nie jest wywoływane.

## Obsługa błędów i ryzyka

- Błąd inicjalizacji lub odczytu Google Sheets przerywa przebieg.
- Błąd append dotyczy tylko jednego linku; kolejne mogą być przetwarzane.
- Błąd pobrania, Gemini lub walidacji podsumowania dotyczy jednego artykułu.
- Błąd SMTP nie cofa wcześniej zapisanych linków.
- Dostępność pipeline'u zależy od PPE, Google Sheets, Jina, Gemini i SMTP.
- Standardowe testy nie potwierdzają dostępności usług live.

## Walidacja

Podstawowa walidacja repo:

```bash
./scripts/verify.sh
```

Walidacje live wymagają jawnego uruchomienia i poprawnych sekretów. Nie należą do podstawowego zestawu testów.

