# PRD 003: Migracja modelu Groq na Qwen 3.6 27B

## Cel zmiany

Celem tej zmiany jest zastąpienie obecnie używanego modelu Groq `meta-llama/llama-4-scout-17b-16e-instruct` modelem `qwen/qwen3.6-27b`, ponieważ obecny model ma zostać wyłączony w lipcu 2026.

Po wdrożeniu GameFlash ma:
- domyślnie używać modelu `qwen/qwen3.6-27b`,
- nadal pozwalać na nadpisanie modelu przez zmienną środowiskową `LLM_MODEL`,
- zachować obecny przepływ generowania podsumowań i korekty językowej,
- zweryfikować, czy nowy model zwraca bloki rozumowania w formacie `<think>...</think>`,
- mieć potwierdzoną jednorazową walidację live nowego modelu przed pełną podmianą.

## Problem do rozwiązania

Obecna implementacja:
- używa domyślnego modelu `meta-llama/llama-4-scout-17b-16e-instruct`,
- wykonuje dwa wywołania modelu dla każdego nowego newsa:
  - generowanie podsumowania,
  - korektę językową,
- nie posiada warstwy czyszczenia odpowiedzi modelu z bloków rozumowania.

To podejście jest ryzykowne, ponieważ:
- obecny domyślny model ma zostać wycofany,
- po dacie wyłączenia aplikacja może przestać działać bez zmiany konfiguracji,
- nowy model `qwen/qwen3.6-27b` jest modelem rozumującym i może zwracać techniczne bloki `<think>...</think>`,
- treści rozumowania nie powinny trafiać do korekty, maila HTML ani fallbacku `plain text`.

## Zakres funkcjonalny

Zmiana obejmuje:
- podmianę domyślnej wartości modelu na `qwen/qwen3.6-27b`,
- aktualizację przykładowej konfiguracji `.env.example`,
- aktualizację dokumentacji operacyjnej opisującej `LLM_MODEL`,
- przygotowanie jednorazowego testu live nowego modelu,
- podjęcie decyzji o lokalnej sanitizacji odpowiedzi modelu na podstawie wyniku testu live,
- dodanie sanitizacji i testów jednostkowych dla usuwania bloków `<think>...</think>` tylko wtedy, gdy test live wykaże taki problem.

## Poza zakresem

Ta zmiana nie obejmuje:
- zmiany providera LLM,
- zmiany liczby wywołań modelu dla pojedynczego newsa,
- przebudowy promptów poza minimalnym dostosowaniem, jeśli test live pokaże taką potrzebę,
- zmiany logiki pobierania linków,
- zmiany integracji z Google Sheets,
- zmiany pobierania treści przez Jina,
- zmiany wysyłki SMTP i renderowania maila HTML,
- uruchamiania testu live dla każdego artykułu w normalnym przebiegu aplikacji.

## Docelowy przepływ

Normalny przebieg aplikacji po wdrożeniu pozostaje taki sam funkcjonalnie:

1. Aplikacja ładuje konfigurację z `.env`.
2. Aplikacja wykrywa nowe linki na listingu.
3. Aplikacja zapisuje nowe linki do Google Sheets.
4. Aplikacja pobiera treść artykułu przez Jina.
5. Aplikacja wywołuje model `qwen/qwen3.6-27b` do wygenerowania podsumowania.
6. Jeśli test live wykazał problem z blokami `<think>...</think>`, aplikacja usuwa je z odpowiedzi.
7. Aplikacja wywołuje model `qwen/qwen3.6-27b` do korekty językowej.
8. Jeśli test live wykazał problem z blokami `<think>...</think>`, aplikacja usuwa je z odpowiedzi.
9. Aplikacja wysyła e-mail multipart ze stylowanym HTML i fallbackiem `plain text`.

Liczba wywołań modelu dla jednego poprawnie przetworzonego newsa pozostaje bez zmian:
- 1 wywołanie dla podsumowania,
- 1 wywołanie dla korekty.

## Jednorazowa walidacja live

Przed pełną podmianą modelu implementacja ma umożliwić jednorazową walidację live nowego modelu.

Walidacja live ma:
- użyć modelu `qwen/qwen3.6-27b`,
- użyć jednego stałego, reprezentatywnego artykułu z `konsolowe.info`,
- pobrać treść artykułu przez Jina albo użyć równoważnej stałej próbki tekstu, jeśli test live ma być izolowany od dostępności strony,
- wykonać ścieżkę podsumowania i korekty,
- nie zapisywać niczego do Google Sheets,
- nie wysyłać e-maila,
- nie być wykonywana automatycznie dla każdego newsa w normalnym pipeline.

Kryteria zaliczenia walidacji live:
- odpowiedź zawiera tytuł,
- odpowiedź zawiera podsumowanie,
- odpowiedź zawiera link do artykułu na etapie danych gotowych do maila,
- tekst jest po polsku,
- wynik testu jasno wskazuje, czy w odpowiedzi pojawia się `<think>` lub `</think>`,
- wynik nadaje się do użycia w obecnym mailu GameFlash bez ręcznej korekty.

## Wymagania techniczne

### 1. Domyślny model

Decyzja:
- domyślny fallback `LLM_MODEL` w kodzie ma zostać zmieniony na `qwen/qwen3.6-27b`.

Uzasadnienie:
- obecny domyślny model ma zostać wyłączony,
- aplikacja powinna działać poprawnie po aktualizacji bez wymagania ręcznej zmiany domyślnej wartości w kodzie.

Konsekwencje:
- użytkownik nadal może wskazać inny model przez `.env`,
- dokumentacja musi pokazywać `qwen/qwen3.6-27b` jako rekomendowaną wartość.

### 2. Zachowanie konfiguracji `LLM_MODEL`

Decyzja:
- nie usuwamy zmiennej `LLM_MODEL`.

Uzasadnienie:
- zachowanie konfiguracji pozwala awaryjnie przełączyć model bez zmiany kodu,
- obecna architektura już wspiera ten mechanizm.

Konsekwencje:
- podmiana modelu ma być zmianą domyślnej wartości i dokumentacji, a nie usztywnieniem aplikacji na jeden model.

### 3. Obsługa reasoning

Decyzja:
- reasoning modelu może pozostać aktywny,
- aplikacja ma najpierw sprawdzić w teście live, czy model zwraca bloki `<think>...</think>`.

Uzasadnienie:
- `qwen/qwen3.6-27b` jest modelem rozumującym,
- nie należy dodawać dodatkowej logiki czyszczenia, jeśli model w praktyce zwraca wyłącznie finalną odpowiedź,
- mail do odbiorcy nie powinien zawierać technicznych bloków rozumowania.

Konsekwencje:
- jeśli test live nie wykaże obecności `<think>...</think>`, sanitizacja nie jest wymagana w tym przyroście,
- jeśli test live wykaże obecność `<think>...</think>`, implementacja musi dodać lokalne usuwanie tych bloków i pokryć je testami.

### 4. Decyzja po teście live

Decyzja:
- test live rozstrzyga, czy sanitizacja jest potrzebna.

Zachowanie:
- jeśli test live nie pokaże bloków `<think>...</think>`, implementacja ogranicza się do podmiany modelu i dokumentacji,
- jeśli test live pokaże bloki `<think>...</think>`, implementacja dodaje usuwanie tych bloków po odpowiedzi modelu,
- w wariancie z sanitizacją czyszczenie dotyczy zarówno podsumowania, jak i korekty,
- do maila HTML i `plain text` nie może trafić widoczny blok reasoning, jeśli taki blok pojawi się w odpowiedzi modelu.

## Scenariusze akceptacyjne

1. Domyślny model
- jeśli `LLM_MODEL` nie jest ustawiony w `.env`, aplikacja używa `qwen/qwen3.6-27b`.

2. Nadpisanie modelu przez `.env`
- jeśli `LLM_MODEL` jest ustawiony, aplikacja używa wartości ze środowiska.

3. Odpowiedź z blokiem `<think>`
- jeśli test live wykaże, że model zwraca tekst zawierający `<think>...</think>`, implementacja usuwa taki blok przed kolejnym etapem i e-mailem.

4. Odpowiedź bez bloku `<think>`
- jeśli test live pokaże standardową odpowiedź bez reasoning, aplikacja zachowuje dotychczasowy przepływ bez dodawania sanitizacji.

5. Podsumowanie
- po wywołaniu modelu dla artykułu wynik podsumowania jest przekazywany dalej bez bloków `<think>...</think>`, jeśli test live wykazał potrzebę ich usuwania.

6. Korekta
- po wywołaniu modelu dla korekty wynik jest dodawany do listy newsów bez bloków `<think>...</think>`, jeśli test live wykazał potrzebę ich usuwania.

7. Test live
- walidacja live nowego modelu może zostać uruchomiona ręcznie lub jako osobny test diagnostyczny,
- walidacja live nie zapisuje danych w Google Sheets,
- walidacja live nie wysyła wiadomości SMTP.

8. Brak regresji liczby wywołań
- normalny pipeline nadal wykonuje dwa wywołania modelu na jeden poprawnie przetworzony news.

## Testy i scenariusze walidacyjne

Implementacja wynikająca z tego PRD ma zostać pokryta testami, które weryfikują co najmniej:
- domyślną wartość modelu `qwen/qwen3.6-27b`,
- możliwość nadpisania modelu przez `LLM_MODEL`,
- scenariusz testu live, który raportuje obecność albo brak bloków `<think>...</think>`,
- usuwanie pojedynczego bloku `<think>...</think>`, jeśli test live wykaże taki problem,
- usuwanie bloku reasoning poprzedzającego finalną odpowiedź, jeśli test live wykaże taki problem,
- brak zmian dla odpowiedzi bez bloku reasoning,
- brak `<think>` w danych przekazywanych do maila, jeśli sanitizacja zostanie wdrożona,
- brak realnego SMTP w testach jednostkowych,
- brak realnego zapisu do Google Sheets w testach walidacyjnych.

Standardowa komenda testów pozostaje:

```bash
uv run python -m unittest discover -s tests -p "test_*.py"
```

## Założenia

- `qwen/qwen3.6-27b` jest docelowym modelem wskazanym dla GameFlash.
- Test live jest jednorazową walidacją przed wdrożeniem podmiany modelu, a nie elementem normalnego przetwarzania każdego artykułu.
- Normalny pipeline nadal używa modelu wyłącznie na etapach podsumowania i korekty.
- Bloki `<think>...</think>` są treścią techniczną i nie powinny być widoczne dla odbiorcy maila, jeśli nowy model zacznie je zwracać.
- Aktualna architektura z `LLM_MODEL` pozostaje właściwa i nie wymaga przebudowy.
- Ta zmiana nie rozwiązuje innych problemów jakościowych promptów ani konfiguracji aplikacji.
