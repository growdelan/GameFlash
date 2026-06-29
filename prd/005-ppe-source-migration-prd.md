# PRD 005: Migracja źródła newsów na PPE i nowy arkusz Google Sheets

## Cel zmiany

Celem tej zmiany jest przeniesienie aktywnego źródła newsów GameFlash z `konsolowe.info` na PPE, ponieważ dotychczasowa strona przestała dostarczać świeże treści w oczekiwanym rytmie.

Po wdrożeniu GameFlash ma:
- pobierać listing newsów z `https://www.ppe.pl/gry`,
- wyciągać z listingu wyłącznie linki do newsów PPE,
- zapisywać stan przetworzonych linków w arkuszu `gameflash_sheet_ppe`,
- zachować dotychczasowy scenariusz przetwarzania: deduplikacja, append do Google Sheets, pobranie treści, podsumowanie, korekta i wysyłka e-maila,
- nie mieszać newsów PPE z bazą gier, rankingami ani innymi linkami ze strony `/gry`.

## Problem do rozwiązania

Obecna implementacja jest skonfigurowana pod źródło `https://konsolowe.info/playstation/ps5/` i parser linków zgodny z adresem `https://konsolowe.info/<YYYY>/<MM>/...`.

To podejście stało się problematyczne, ponieważ:
- dotychczasowa strona praktycznie przestała publikować nowe newsy,
- pipeline może regularnie kończyć się brakiem nowych treści,
- parser linków jest związany ze strukturą URL `konsolowe.info`, której PPE nie używa,
- nowy arkusz Google Sheets ma oddzielać stan przetwarzania PPE od historycznego stanu `konsolowe.info`.

## Zakres funkcjonalny

Zmiana obejmuje:
- zmianę domyślnego URL listingu na `https://www.ppe.pl/gry`,
- zmianę domyślnego arkusza Google Sheets na ID `1N82WxjskvsIyjlfwh8CxlhHJB9LEUMwbAdCI8w0J_yk`,
- zmianę domyślnej zakładki arkusza na `Sheet1`,
- zachowanie kolumny `Links` jako źródła prawdy dla przetworzonych linków,
- zmianę parsera listingu tak, aby wyciągał linki PPE w formacie `/news/<id>/<slug>.html`,
- normalizację linków względnych PPE do pełnej postaci `https://www.ppe.pl/news/<id>/<slug>.html`,
- ignorowanie linków do bazy gier, rankingów, menu, `/news.html`, promocji i innych sekcji,
- zachowanie pierwszego przebiegu na pustym arkuszu jako normalnego przetwarzania widocznych newsów.

## Poza zakresem

Ta zmiana nie obejmuje:
- obsługi wielu aktywnych źródeł newsów równocześnie,
- importu historycznych linków z poprzedniego arkusza,
- migracji danych ze starego arkusza do `gameflash_sheet_ppe`,
- dodania dedykowanego fallbacku pobierania treści dla PPE,
- zmiany modelu LLM,
- zmiany promptów podsumowania i korekty,
- zmiany renderowania e-maila HTML,
- zmiany konfiguracji SMTP,
- dodania nowych zależności,
- przebudowy aplikacji na CLI, API albo usługę wieloźródłową.

## Docelowy przepływ

Docelowy przebieg po migracji źródła:

1. Aplikacja ładuje konfigurację z `.env`.
2. Aplikacja uwierzytelnia się do Google Sheets kontem serwisowym.
3. Aplikacja otwiera arkusz o ID `1N82WxjskvsIyjlfwh8CxlhHJB9LEUMwbAdCI8w0J_yk` i zakładkę `Sheet1`, chyba że zmienne środowiskowe nadpiszą te wartości.
4. Aplikacja odczytuje istniejące linki z kolumny `Links`.
5. Aplikacja pobiera HTML strony `https://www.ppe.pl/gry`.
6. Parser HTML wyciąga linki pasujące do wzorca PPE `/news/<id>/<slug>.html`.
7. Linki względne są normalizowane do pełnych URL w domenie `https://www.ppe.pl`.
8. Aplikacja usuwa duplikaty z bieżącego przebiegu i odrzuca linki obecne już w Google Sheets.
9. Każdy nowy link jest najpierw dopisywany do arkusza.
10. Dopiero po udanym append aplikacja pobiera pełną treść artykułu przez `https://r.jina.ai/<link>`.
11. Aplikacja generuje podsumowanie, wykonuje korektę i wysyła zbiorczy e-mail multipart zgodnie z obecnym przepływem.

## Wymagania techniczne

### 1. Nowe źródło listingu

Decyzja:
- domyślny listing newsów ma wskazywać `https://www.ppe.pl/gry`.

Uzasadnienie:
- PPE publikuje aktywne newsy gamingowe, a dotychczasowe źródło przestało dostarczać świeże treści.

Konsekwencje:
- parser listingu musi zostać dostosowany do struktury PPE,
- dokumentacja operacyjna musi wskazywać nowe aktywne źródło.

### 2. Nowy arkusz Google Sheets

Decyzja:
- domyślnym arkuszem stanu ma być `gameflash_sheet_ppe` o ID `1N82WxjskvsIyjlfwh8CxlhHJB9LEUMwbAdCI8w0J_yk`, zakładka `Sheet1`.

Uzasadnienie:
- nowy arkusz oddziela stan PPE od historycznego stanu poprzedniego źródła.

Konsekwencje:
- `GOOGLE_SHEET_ID` i `GOOGLE_SHEET_WORKSHEET` nadal mogą nadpisać domyślne wartości,
- konto serwisowe musi mieć dostęp do nowego arkusza,
- zakładka musi zawierać nagłówek `Links`.

### 3. Parser linków PPE

Decyzja:
- parser ma zbierać wyłącznie linki do newsów PPE pasujące do wzorca `/news/<id>/<slug>.html`.

Uzasadnienie:
- strona `/gry` zawiera także bazę gier, rankingi, linki menu i inne treści, które nie są newsami do maila GameFlash.

Konsekwencje:
- linki `/gry/...`, `/news.html`, linki promocyjne, rankingi i nawigacja są ignorowane,
- względne linki PPE muszą zostać zamienione na pełne URL,
- deduplikacja w obrębie jednego przebiegu pozostaje wymagana.

### 4. Pobieranie treści artykułu

Decyzja:
- dla PPE pierwszą ścieżką pobierania treści pozostaje Jina.

Uzasadnienie:
- sprawdzony przykładowy artykuł PPE zwraca przez Jina normalną treść tekstową z metadanymi i artykułem.

Konsekwencje:
- w ramach tej zmiany nie powstaje dedykowany fallback PPE,
- istniejący fallback WordPress/HTML dla `konsolowe.info` pozostaje jako zachowanie historyczne i nie musi być usuwany.

### 5. Pierwszy przebieg na pustym arkuszu

Decyzja:
- jeśli nowy arkusz zawiera tylko nagłówek `Links`, pierwszy przebieg ma normalnie przetworzyć i wysłać widoczne newsy PPE.

Uzasadnienie:
- użytkownik chce przejść na nowe źródło i zacząć otrzymywać bieżące newsy bez osobnego przebiegu inicjalizującego.

Konsekwencje:
- aplikacja nie ma trybu "tylko zarejestruj" dla pierwszego uruchomienia,
- wszystkie widoczne, nowe linki `/news/` z listingu PPE mogą trafić do pierwszego maila.

## Scenariusze akceptacyjne

1. Nowy domyślny listing
- jeśli `URL` nie jest nadpisany w konfiguracji, aplikacja pobiera listing z `https://www.ppe.pl/gry`.

2. Nowy domyślny arkusz
- jeśli `GOOGLE_SHEET_ID` i `GOOGLE_SHEET_WORKSHEET` nie są nadpisane, aplikacja używa arkusza `1N82WxjskvsIyjlfwh8CxlhHJB9LEUMwbAdCI8w0J_yk` i zakładki `Sheet1`.

3. Ekstrakcja linków PPE
- jeśli HTML zawiera linki `/news/<id>/<slug>.html`, parser zwraca pełne adresy `https://www.ppe.pl/news/<id>/<slug>.html`.

4. Ignorowanie treści nienewsowych
- jeśli HTML zawiera linki `/gry/...`, `/gry/ranking`, `/news.html` albo linki menu, parser ich nie zwraca.

5. Deduplikacja
- jeśli ten sam link PPE występuje wiele razy w HTML, do dalszego przetwarzania trafia tylko raz.

6. Pomijanie linków istniejących w arkuszu
- jeśli link PPE istnieje już w kolumnie `Links`, aplikacja nie pobiera artykułu i nie wysyła go ponownie.

7. Pierwszy pusty arkusz
- jeśli arkusz zawiera tylko nagłówek `Links`, aplikacja dopisuje i przetwarza widoczne linki PPE.

8. Brak regresji pipeline'u
- po udanym append linku PPE aplikacja zachowuje dotychczasowy przepływ: Jina, podsumowanie, korekta i e-mail multipart.

## Testy i scenariusze walidacyjne

Implementacja wynikająca z tego PRD ma zostać pokryta testami `unittest` bez realnego IO.

Testy powinny weryfikować co najmniej:
- parser zwraca pełne URL dla linków PPE `/news/<id>/<slug>.html`,
- parser ignoruje linki `/gry/...`, rankingi, menu, `/news.html` i obce domeny,
- parser usuwa duplikaty w kolejności wystąpienia,
- pipeline przetwarza nowy link PPE po udanym append do Google Sheets,
- pipeline pomija link PPE obecny już w kolumnie `Links`,
- błąd append do Google Sheets nadal blokuje dalsze przetwarzanie linku,
- pierwszy pusty arkusz przetwarza widoczne linki PPE,
- standardowe testy nie wykonują realnego SMTP,
- standardowe testy nie zapisują danych do Google Sheets,
- standardowe testy nie zależą od dostępności PPE, Jina ani Groq.

Standardowa komenda testów pozostaje:

```bash
uv run python -m unittest discover -s tests -p "test_*.py"
```

## Założenia

- Aktywnym źródłem GameFlash ma być PPE.
- Strona `https://www.ppe.pl/gry` jest listingiem, z którego pobierane są linki do newsów.
- Tylko linki `/news/<id>/<slug>.html` są traktowane jako newsy do maila.
- Nowy arkusz `gameflash_sheet_ppe` istnieje i jest dostępny dla konta serwisowego.
- Zakładka `Sheet1` zawiera nagłówek `Links`.
- Pierwszy przebieg na nowym arkuszu ma wysłać widoczne newsy, a nie tylko zainicjalizować stan.
- Obecna architektura skryptowa pozostaje właściwa i nie wymaga przebudowy.
- PRD opisuje przyszłą poprawkę implementacyjną, ale samo dodanie dokumentu nie zmienia działania aplikacji.
