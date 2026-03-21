# PRD 001: Google Sheets jako źródło stanu linków

## Cel zmiany

Celem tej zmiany jest zastąpienie lokalnego pliku `news_links.json` arkuszem Google Sheets jako jedynym źródłem stanu przetworzonych linków oraz usunięcie kroku ekstrakcji linków przez model LLM.

Po wdrożeniu GameFlash ma:
- pobierać listing newsów z `https://konsolowe.info/playstation/ps5/`,
- wyciągać linki do artykułów bezpośrednio z HTML,
- porównywać je z arkuszem Google Sheets,
- przetwarzać wyłącznie nowe linki,
- dopisywać nowe linki do arkusza przed dalszym przetwarzaniem,
- zachować obecny krok generowania podsumowań przez model i wysyłkę e-maili.

Ta zmiana ma odwzorować funkcjonalnie dotychczasowy workflow z `n8n`, ale w kodzie GameFlash.

## Problem do rozwiązania

Obecna implementacja:
- przechowuje stan przetworzonych linków lokalnie w `news_links.json`,
- używa modelu LLM do wyciągania listy linków z listingu newsów.

To podejście jest niepożądane, ponieważ:
- stan lokalny jest trudniejszy do współdzielenia i kontroli niż arkusz Google Sheets,
- ekstrakcja linków przez model jest zbędna dla danych, które można jednoznacznie odczytać z HTML,
- obecny przepływ odbiega od wcześniej działającego rozwiązania w `n8n`.

## Zakres funkcjonalny

Zmiana obejmuje:
- odczyt istniejących linków z Google Sheets,
- traktowanie Google Sheets jako jedynej bazy deduplikacji,
- pobranie HTML strony z listingiem newsów,
- ekstrakcję linków przez parser HTML na podstawie selektora CSS,
- deduplikację linków w ramach jednego przebiegu,
- porównanie wykrytych linków z zawartością kolumny `Links`,
- append każdego nowego linku do arkusza,
- dalsze przetwarzanie wyłącznie linków, które zostały poprawnie dopisane do arkusza,
- pobranie pełnej treści artykułu przez `https://r.jina.ai/<link>`,
- pozostawienie generowania podsumowań przez model LLM,
- pozostawienie wysyłki zbiorczego e-maila.

## Poza zakresem

Ta zmiana nie obejmuje:
- przebudowy logiki wysyłki SMTP poza dostosowaniem do nowego źródła linków,
- rozbudowanego workflow statusów przetwarzania,
- wielu zakładek lub wielu arkuszy dla tej funkcji,
- panelu administracyjnego,
- migracji historycznych danych z lokalnego pliku do arkusza poza uznaniem bieżącego arkusza za źródło prawdy,
- zmiany kroku podsumowywania artykułów przez model,
- równoległego porządkowania innych refaktorów projektu.

## Źródło prawdy i model danych

Źródłem prawdy dla informacji o już zarejestrowanych linkach ma być Google Sheets:
- Spreadsheet ID: `1o0htAcR-8ej4u9GiRCYHxxvFKE7BhCaryB6nqkM-KTI`
- Domyślna zakładka: `Arkusz1`
- Domyślna kolumna: `Links`

Minimalny model danych:
- jedna wymagana kolumna nagłówkowa: `Links`

Znaczenie danych:
- jeśli link istnieje w kolumnie `Links`, uznaje się go za już zarejestrowany i nie wolno go ponownie kierować do przetwarzania,
- sam fakt obecności linku w arkuszu oznacza potwierdzony zapis do bazy stanu,
- nie są wymagane dodatkowe kolumny typu status, timestamp lub wynik przetwarzania w ramach tej zmiany.

## Wymagania konfiguracyjne

Zmiana wymaga wsparcia dla konfiguracji:
- `GOOGLE_SHEET_ID=1o0htAcR-8ej4u9GiRCYHxxvFKE7BhCaryB6nqkM-KTI`
- `GOOGLE_SHEET_WORKSHEET=Arkusz1`
- `GSPREAD_SERVICE_ACCOUNT_FILE=<sciezka_do_pliku_json>`

Zasady:
- uwierzytelnienie do Google Sheets ma działać przez konto serwisowe,
- sposób autoryzacji ma być taki sam koncepcyjnie jak w projekcie `DramaChecker`,
- plik JSON konta serwisowego pozostaje poza repozytorium,
- brak poprawnej autoryzacji do arkusza jest błędem blokującym wykonanie przebiegu.

## Docelowy przepływ

1. Aplikacja wczytuje konfigurację środowiskową.
2. Aplikacja uwierzytelnia się do Google Sheets kontem serwisowym.
3. Aplikacja otwiera arkusz o wskazanym ID i zakładkę `Arkusz1`.
4. Aplikacja odczytuje wszystkie istniejące wartości z kolumny `Links`.
5. Aplikacja pobiera HTML strony `https://konsolowe.info/playstation/ps5/`.
6. Aplikacja wyciąga z HTML linki pasujące do wzorca bieżącego roku i miesiąca:
   `a[href^="https://konsolowe.info/<YYYY>/<MM>/"]`
7. Aplikacja usuwa duplikaty wykryte w ramach bieżącego przebiegu.
8. Aplikacja odrzuca linki, które już istnieją w kolumnie `Links`.
9. Dla każdego nowego linku:
   - dopisuje link do Google Sheets,
   - dopiero po udanym append buduje URL `https://r.jina.ai/<link>`,
   - pobiera treść artykułu,
   - generuje podsumowanie przez model,
   - przygotowuje wynik do zbiorczego e-maila.
10. Aplikacja wysyła e-mail wyłącznie z nowymi, faktycznie przetworzonymi wpisami.

## Decyzje produktowe i techniczne

### 1. Rezygnacja z LLM do ekstrakcji linków

Lista linków nie ma być już wyciągana przez model. Ten krok zostaje zastąpiony lokalnym parserem HTML opartym o selektor CSS.

Decyzja:
- usuwamy krok `groq.news_prompt()` z przepływu wykrywania linków,
- usuwamy zależność od odpowiedzi JSON generowanej przez model dla tego etapu.

Uzasadnienie:
- listing zawiera linki możliwe do wyciągnięcia deterministycznie,
- usuwa to zbędny koszt, opóźnienie i ryzyko błędnej odpowiedzi modelu,
- odwzorowuje to działające wcześniej rozwiązanie z `n8n`.

### 2. Google Sheets jako jedyna baza deduplikacji

Decyzja:
- Google Sheets zastępuje `news_links.json` jako źródło informacji o tym, które linki zostały już zarejestrowane.

Uzasadnienie:
- arkusz jest łatwiejszy do ręcznej kontroli i współdzielenia,
- stan nie jest związany z jednym lokalnym środowiskiem uruchomieniowym.

Konsekwencje:
- lokalny plik JSON przestaje być potrzebny w tym obszarze funkcjonalnym,
- poprawność działania zależy od dostępności Google Sheets.

### 3. Zapis przed przetwarzaniem

Decyzja:
- nowy link musi zostać dopisany do arkusza przed pobraniem pełnej treści i przed generowaniem podsumowania.

Uzasadnienie:
- gwarantuje to, że kolejny przebieg nie podejmie ponownie tego samego linku,
- zachowanie ma być zgodne z wcześniejszym workflow z `n8n`.

Konsekwencje:
- jeśli dalsze przetwarzanie zawiedzie po append, link pozostaje oznaczony jako już zarejestrowany,
- ponowne podjęcie takiego przypadku wymaga ręcznej interwencji.

### 4. Kryterium wejścia do przetwarzania

Decyzja:
- tylko link, który nie istnieje jeszcze w arkuszu i który został skutecznie dopisany, może przejść do dalszych kroków pipeline'u.

Jeśli append do Google Sheets nie powiedzie się:
- link nie jest pobierany,
- link nie jest podsumowywany,
- link nie trafia do e-maila w tym przebiegu.

### 5. Pobieranie pełnej treści artykułu

Decyzja:
- pełna treść nowego artykułu ma być pobierana przez mirror `https://r.jina.ai/<link>`.

Uzasadnienie:
- odwzorowuje to działanie wcześniejszego workflow z `n8n`,
- upraszcza pobieranie treści z artykułu do postaci przydatnej dla dalszego podsumowania.

## Wpływ na architekturę

Zmiana wprowadza następujące kierunki architektoniczne:
- dodanie integracji z Google Sheets wzorowanej na `DramaChecker`,
- usunięcie lokalnej bazy linków opartej o plik JSON z tego przepływu,
- zastąpienie ekstrakcji linków przez LLM lokalnym parserem HTML,
- pozostawienie etapu podsumowania LLM i wysyłki e-maila bez zmiany celu biznesowego.

Architektonicznie oznacza to rozdzielenie:
- wykrywania linków jako kroku deterministycznego,
- generowania podsumowań jako kroku modelowego.

## Scenariusze akceptacyjne

1. Link już istnieje w arkuszu
- jeśli listing zawiera link obecny w kolumnie `Links`, aplikacja pomija go i nie pobiera artykułu.

2. Nowy link
- jeśli listing zawiera nowy link, aplikacja dopisuje go do arkusza i dopiero potem go przetwarza.

3. Duplikat na listingu
- jeśli ten sam link pojawia się wielokrotnie w jednym przebiegu, aplikacja przetwarza go tylko raz.

4. Błąd append do Google Sheets
- jeśli dopisanie linku do arkusza kończy się błędem, link nie jest podsumowywany ani wysyłany e-mailem.

5. Błąd po udanym append
- jeśli append się uda, ale pobranie treści lub podsumowanie nie powiedzie się, link pozostaje zapisany i nie wraca automatycznie w kolejnym przebiegu.

6. Brak nowych linków
- jeśli nie ma nowych linków, aplikacja kończy przebieg bez generowania nowych podsumowań.

7. Brak dostępu do arkusza
- jeśli konto serwisowe nie ma dostępu do arkusza lub zakładki, błąd jest traktowany jako blokujący dla całego przebiegu.

## Założenia

- używany jest istniejący arkusz i zakładka `Arkusz1`, dopóki nie zostanie wskazana inna zakładka,
- kolumna `Links` już istnieje albo implementacja może uznać pierwszy wiersz za wymagany nagłówek,
- wzorzec z `n8n` jest referencyjny funkcjonalnie, nie musi być odwzorowany 1:1 technicznie,
- ta zmiana opisuje wyłącznie migrację stanu linków do Google Sheets i usunięcie LLM z ekstrakcji linków,
- dalsze porządkowanie architektury projektu nie wchodzi w zakres tego PRD.
