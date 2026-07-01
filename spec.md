# Specyfikacja techniczna

## Cel
GameFlash automatyzuje zbieranie i streszczanie newsów z branży gier z jednego wskazanego źródła WWW, a następnie wysyła gotowe podsumowania e-mailem.

Projekt rozwiązuje problem ręcznego przeglądania strony z newsami, wybierania nowych artykułów i przygotowywania krótkiego zestawienia do dalszej dystrybucji.

Główna grupa docelowa:
- osoba lub mały zespół, który chce cyklicznie dostawać skrót nowych newsów gamingowych,
- użytkownik techniczny uruchamiający skrypt lokalnie lub z prostego harmonogramu.

Poza zakresem obecnej wersji:
- panel użytkownika,
- wiele konfigurowalnych źródeł treści,
- trwała baza danych inna niż lokalny plik JSON lub Google Sheets,
- kolejki zadań, retry workflow i rozbudowany monitoring,
- testy end-to-end i automatyczne wdrożenie.

Planowane rozszerzenie zakresu wynikające z PRD `001-google-sheets-link-store-prd.md`:
- przeniesienie stanu przetworzonych linków z lokalnego pliku do Google Sheets,
- usunięcie użycia LLM do ekstrakcji linków z listingu newsów,
- zastąpienie ekstrakcji linków parserem HTML,
- dopisywanie nowych linków do Google Sheets przed dalszym przetwarzaniem.

Rozszerzenie z PRD `001-google-sheets-link-store-prd.md` zostalo wdrozone.

Planowane rozszerzenie zakresu wynikające z PRD `002-gaming-email-styles-prd.md`:
- zastapienie obecnego e-maila `plain text` stylowanym mailem HTML,
- zachowanie fallbacku `plain text` w wiadomosci multipart,
- prezentowanie kazdego newsa jako osobnej sekcji lub karty,
- dostosowanie wygladu wiadomosci do nowoczesnego, gamingowego charakteru produktu.

Rozszerzenie z PRD `002-gaming-email-styles-prd.md` zostalo wdrozone.

Planowane rozszerzenie zakresu wynikające z PRD `003-qwen-model-migration-prd.md`:
- zastapienie domyslnego modelu Groq modelem `qwen/qwen3.6-27b`,
- zachowanie mozliwosci nadpisania modelu przez `LLM_MODEL`,
- wykonanie jednorazowej walidacji live nowego modelu przed pelna podmiana,
- warunkowe dodanie usuwania blokow `<think>...</think>` tylko wtedy, gdy test live wykaze taki problem.

Rozszerzenie z PRD `003-qwen-model-migration-prd.md` zostalo wdrozone.

Planowane rozszerzenie zakresu wynikające z PRD `004-article-content-fetch-resilience-prd.md`:
- wykrywanie błędnych odpowiedzi Jina mimo statusu `HTTP 200`,
- dodanie fallbacku pobierania treści artykułów z `konsolowe.info`,
- blokowanie wywołań LLM dla stron błędów, pustych treści i samych metadanych,
- walidacja kompletności wyniku korekty przed wysyłką e-maila.

Rozszerzenie z PRD `004-article-content-fetch-resilience-prd.md` zostalo wdrozone.

Planowane rozszerzenie zakresu wynikające z PRD `005-ppe-source-migration-prd.md`:
- zmiana aktywnego źródła listingu newsów na `https://www.ppe.pl/gry`,
- zmiana domyślnego arkusza stanu na `gameflash_sheet_ppe`,
- dostosowanie parsera HTML do linków PPE w formacie `/news/<id>/<slug>.html`,
- zachowanie dotychczasowego scenariusza deduplikacji, pobierania treści, podsumowania, korekty i wysyłki e-maila.

Rozszerzenie z PRD `005-ppe-source-migration-prd.md` zostalo wdrozone.

Zmiana operacyjna po PRD `005-ppe-source-migration-prd.md`:
- aktywna warstwa LLM zostala przeniesiona z Groq/Qwen na Google Gemini,
- domyslnym modelem jest `gemini-3.5-flash`,
- konfiguracja uzywa `GEMINI_API_KEY` i `GEMINI_MODEL`,
- zaleznosc `groq` zostala usunieta z aktywnego skryptu.

---

## Zakres funkcjonalny (high-level)
Kluczowe use-case'i:
- pobranie listy treści ze strony z newsami o grach,
- wyodrębnienie linków do nowych artykułów z bieżącego miesiąca,
- pobranie pełnej treści nowych artykułów,
- wygenerowanie krótkich podsumowań po polsku,
- wysłanie zbiorczego e-maila do wielu odbiorców.

Główny przepływ:
1. Aplikacja ładuje konfigurację z `.env`.
2. Uwierzytelnia się do Google Sheets kontem serwisowym.
3. Odczytuje istniejące linki z kolumny `Links`.
4. Pobiera HTML strony listingu bezpośrednio ze źródłowego URL.
5. Wyciąga linki z HTML na podstawie wzorca bieżącego roku i miesiąca.
6. Usuwa duplikaty z bieżącego przebiegu i odrzuca linki obecne już w Google Sheets.
7. Dla każdego nowego linku wykonuje append do Google Sheets.
8. Dla poprawnie dopisanych linków pobiera treść artykułów przez `https://r.jina.ai/<link>` albo fallback dla `konsolowe.info`, jeśli Jina zwróci błąd lub niewiarygodną treść.
9. Generuje podsumowania po polsku.
10. Odrzuca ucięte lub niekompletne podsumowania.
11. Wysyła pojedynczy e-mail ze wszystkimi poprawnie przygotowanymi podsumowaniami.

Docelowy przepływ wynikający z PRD `001-google-sheets-link-store-prd.md`:
1. Aplikacja ładuje konfigurację z `.env`.
2. Aplikacja uwierzytelnia się do Google Sheets kontem serwisowym.
3. Aplikacja odczytuje istniejące linki z kolumny `Links`.
4. Aplikacja pobiera HTML strony listingu newsów bezpośrednio ze źródłowego URL.
5. Aplikacja wyciąga linki z HTML na podstawie selektora odpowiadającego bieżącemu rokowi i miesiącowi.
6. Aplikacja usuwa duplikaty z bieżącego przebiegu i odrzuca linki obecne już w Google Sheets.
7. Każdy nowy link jest najpierw dopisywany do Google Sheets.
8. Dopiero po udanym append aplikacja pobiera pełną treść artykułu przez `https://r.jina.ai/<link>`.
9. Aplikacja generuje podsumowania po polsku i wysyła zbiorczy e-mail.

Docelowy przeplyw wynikajacy z PRD `002-gaming-email-styles-prd.md`:
1. Aplikacja laduje konfiguracje z `.env`.
2. Aplikacja uwierzytelnia sie do Google Sheets kontem serwisowym.
3. Aplikacja odczytuje istniejace linki z kolumny `Links`.
4. Aplikacja pobiera HTML strony listingu newsow bezposrednio ze zrodlowego URL.
5. Aplikacja wyciaga linki z HTML na podstawie selektora odpowiadajacego biezacemu rokowi i miesiacowi.
6. Aplikacja usuwa duplikaty z biezacego przebiegu i odrzuca linki obecne juz w Google Sheets.
7. Kazdy nowy link jest najpierw dopisywany do Google Sheets.
8. Dopiero po udanym append aplikacja pobiera pelna tresc artykulu przez `https://r.jina.ai/<link>`.
9. Aplikacja generuje podsumowania po polsku i przygotowuje dwa warianty wiadomosci: `text/plain` oraz `text/html`.
10. Aplikacja wysyla jeden e-mail multipart, w ktorym HTML stanowi glowna warstwe prezentacji, a `plain text` pozostaje fallbackiem kompatybilnosci.

Docelowy przeplyw wynikajacy z PRD `003-qwen-model-migration-prd.md`:
1. Przed podmiana modelu aplikacja przechodzi jednorazowa walidacje live modelu `qwen/qwen3.6-27b` na stalej probce artykulu.
2. Walidacja live nie zapisuje danych do Google Sheets i nie wysyla e-maila.
3. Wynik walidacji wskazuje, czy model zwraca bloki `<think>...</think>`.
4. Jesli walidacja live nie wykaze blokow `<think>...</think>`, implementacja ogranicza sie do podmiany domyslnego modelu i dokumentacji.
5. Jesli walidacja live wykaze bloki `<think>...</think>`, aplikacja usuwa takie bloki po odpowiedzi modelu przed dalszym przetwarzaniem.
6. Normalny pipeline nadal wykonuje dwa wywolania modelu na poprawnie przetworzony news: podsumowanie i korekte.
7. Aplikacja nadal wysyla jeden e-mail multipart z gotowymi podsumowaniami.

Docelowy przeplyw wynikajacy z PRD `004-article-content-fetch-resilience-prd.md`:
1. Aplikacja probuje pobrac tresc artykulu przez Jina.
2. Aplikacja waliduje, czy odpowiedz Jina zawiera realna tresc artykulu, a nie komunikat bledu zrodla.
3. Jesli Jina zwraca bledna tresc mimo statusu `HTTP 200`, aplikacja uruchamia fallback dla `konsolowe.info`.
4. Preferowany fallback pobiera tresc przez WordPress REST API, jesli da sie ustalic ID posta.
5. Alternatywny fallback pobiera bezposredni HTML artykulu i oczyszcza glowna tresc.
6. Jesli zadna sciezka nie dostarczy realnej tresci, aplikacja pomija link i nie wywoluje LLM.
7. Wynik korekty jezykowej jest sprawdzany pod katem kompletnosci przed dodaniem do maila.

Docelowy przeplyw wynikajacy z PRD `005-ppe-source-migration-prd.md`:
1. Aplikacja laduje konfiguracje z `.env`.
2. Aplikacja uwierzytelnia sie do Google Sheets kontem serwisowym.
3. Aplikacja domyslnie otwiera arkusz `gameflash_sheet_ppe` o ID `1N82WxjskvsIyjlfwh8CxlhHJB9LEUMwbAdCI8w0J_yk` i zakladke `Sheet1`.
4. Aplikacja odczytuje istniejace linki z kolumny `Links`.
5. Aplikacja pobiera HTML listingu `https://www.ppe.pl/gry`.
6. Parser HTML wyciaga tylko linki PPE pasujace do wzorca `/news/<id>/<slug>.html`.
7. Linki wzgledne sa normalizowane do pelnych URL w domenie `https://www.ppe.pl`.
8. Aplikacja usuwa duplikaty z biezacego przebiegu i odrzuca linki obecne juz w Google Sheets.
9. Kazdy nowy link jest najpierw dopisywany do Google Sheets.
10. Dopiero po udanym append aplikacja pobiera tresc artykulu przez `https://r.jina.ai/<link>`.
11. Aplikacja zachowuje obecny przeplyw podsumowania, korekty i wysylki e-maila multipart.

Czego aplikacja obecnie nie robi:
- nie waliduje kompleksowo konfiguracji przed startem,
- nie obsługuje wielu źródeł wejściowych ani wielu modeli,
- nie zapisuje wersji podsumowań ani historii wysyłek,
- nie ma osobnej warstwy CLI, API ani interfejsu WWW.

---

## Architektura i przepływ danych
Architektura ma postać prostego skryptu orkiestrującego z kilkoma modułami pomocniczymi.

1. Główne komponenty systemu
- `main.py` odpowiada za sekwencję wykonania całego procesu.
- `scrapers/listing.py` pobiera i parsuje HTML listingu newsów.
- `scrapers/jina.py` pobiera treść pojedynczego artykułu przez mirror Jina i fallback dla `konsolowe.info`.
- `llms/gemini.py` buduje prompty i wykonuje wywołania modelu Gemini.
- `storage/google_sheets.py` obsługuje odczyt i zapis stanu linków w Google Sheets.
- `emails/gmail.py` składa i wysyła wiadomość SMTP.

Planowane rozszerzenie komponentów wynikające z PRD `001-google-sheets-link-store-prd.md`:
- brak dodatkowych nierozliczonych elementow z tego PRD.

Rozszerzenie komponentow wynikajace z PRD `002-gaming-email-styles-prd.md`:
- `emails/gmail.py` ma skladac wiadomosc multipart z czescia `text/plain` oraz `text/html`,
- warstwa maili ma zostac rozszerzona o lekki renderer HTML dla stylowanej wiadomosci GameFlash.

Planowane rozszerzenie komponentow wynikajace z PRD `003-qwen-model-migration-prd.md`:
- `llms/groq.py` pozostaje miejscem integracji z modelem Groq,
- konfiguracja modelu ma wskazywac domyslnie `qwen/qwen3.6-27b`,
- ewentualna warstwa usuwania blokow `<think>...</think>` ma zostac dodana tylko wtedy, gdy test live wykaze taka potrzebe.

Planowane rozszerzenie komponentow wynikajace z PRD `004-article-content-fetch-resilience-prd.md`:
- `scrapers/jina.py` ma walidowac, czy odpowiedz z Jina zawiera realna tresc artykulu,
- warstwa pobierania tresci ma dostac fallback dla `konsolowe.info` oparty o WordPress REST API lub bezposredni HTML,
- `main.py` ma pomijac linki, dla ktorych nie udalo sie pobrac wiarygodnej tresci,
- etap korekty ma weryfikowac kompletnosc wyniku przed przekazaniem newsa do warstwy mailowej.

Planowane rozszerzenie komponentow wynikajace z PRD `005-ppe-source-migration-prd.md`:
- `main.py` ma domyslnie wskazywac listing PPE oraz nowy arkusz Google Sheets,
- `scrapers/listing.py` ma wyciagac i normalizowac linki PPE typu `/news/<id>/<slug>.html`,
- `storage/google_sheets.py` pozostaje bez zmiany kontraktu: zrodlem prawdy nadal jest kolumna `Links`.

Rozszerzenie komponentow wynikajace z Milestone 1.7:
- `llms/gemini.py` zastapil aktywna integracje Groq,
- `main.py` uzywa `GEMINI_API_KEY` i `GEMINI_MODEL`,
- prompt podsumowania pozostaje w warstwie LLM.

Rozszerzenie komponentow wynikajace z Milestone 1.8:
- osobny prompt korekty zostal usuniety z `llms/gemini.py`,
- `main.py` wysyla kompletne podsumowania bez drugiego wywolania LLM,
- warstwa maili nadal przyjmuje wpisy w formacie `Tytul`, `Podsumowanie`, `Link`.

2. Przepływ danych między komponentami
- Wejście konfiguracyjne pochodzi z `.env` i stałych zaszytych w `main.py`.
- Konfiguracja obejmuje także `GOOGLE_SHEET_ID`, `GOOGLE_SHEET_WORKSHEET` i `GSPREAD_SERVICE_ACCOUNT_FILE`.
- Google Sheets jest źródłem prawdy dla listy już zarejestrowanych linków.
- Listing newsów jest pobierany jako HTML bezpośrednio z URL źródłowego.
- Parser HTML wyodrębnia linki zgodne ze wzorcem `https://konsolowe.info/<YYYY>/<MM>/`.
- Każdy nowy link jest najpierw zapisywany w Google Sheets.
- Dla poprawnie zapisanych linków pobierana jest pełna treść artykułów przez mirror Jina, a przy błędnej odpowiedzi przez fallback `konsolowe.info`.
- Model Gemini generuje podsumowanie, ktore po walidacji kompletnosci trafia bezposrednio do e-maila.
- Kompletne sekcje podsumowań są łączone w jeden e-mail wysyłany przez SMTP.

Docelowy przepływ danych wynikający z PRD `001-google-sheets-link-store-prd.md`:
- Wejście konfiguracyjne ma obejmować także `GOOGLE_SHEET_ID`, `GOOGLE_SHEET_WORKSHEET` i `GSPREAD_SERVICE_ACCOUNT_FILE`.
- Google Sheets ma stać się źródłem prawdy dla listy już zarejestrowanych linków.
- Listing newsów ma być pobierany jako HTML bezpośrednio z URL źródłowego.
- Parser HTML ma wyodrębniać linki zgodne ze wzorcem `https://konsolowe.info/<YYYY>/<MM>/`.
- Każdy nowy link ma zostać zapisany w Google Sheets przed pobraniem treści artykułu.
- Pełna treść artykułu ma być pobierana przez mirror `https://r.jina.ai/<link>`.
- Model Groq ma pozostać odpowiedzialny wyłącznie za podsumowanie i korektę tekstu.

Docelowy przeplyw danych wynikajacy z PRD `002-gaming-email-styles-prd.md`:
- gotowe sekcje podsumowan maja zostac przeksztalcone do dwoch reprezentacji: `plain text` oraz `html`,
- warstwa HTML ma renderowac kazdy news jako osobny blok z tytulem, streszczeniem i CTA do pelnego artykulu,
- gotowa wiadomosc ma byc wysylana jako multipart przez SMTP bez zaleznosci od zewnetrznych assetow.

Docelowy przeplyw danych wynikajacy z PRD `003-qwen-model-migration-prd.md`:
- `LLM_MODEL` pozostaje konfigurowalnym wskazaniem modelu,
- domyslna wartosc modelu ma zostac zmieniona na `qwen/qwen3.6-27b`,
- test live ma uzyc stalej probki artykulu i nie moze modyfikowac stanu Google Sheets ani wysylac SMTP,
- walidacja live wykazala, ze surowa odpowiedz Qwen moze zawierac bloki `<think>...</think>`, dlatego odpowiedzi modelu sa zabezpieczone przed przekazaniem reasoning do korekty i warstwy maili,
- wywolania Qwen uzywaja ukrytego reasoning oraz lokalnej sanitizacji jako zabezpieczenia.

Docelowy przeplyw danych wynikajacy z PRD `004-article-content-fetch-resilience-prd.md`:
- tresc z Jina nie jest automatycznie traktowana jako wiarygodna tylko dlatego, ze odpowiedz miala status `HTTP 200`,
- komunikaty bledu takie jak `Title: 403 Forbidden` i `Warning: Target URL returned error 403` nie moga trafic do promptu podsumowania,
- dla artykulow z `konsolowe.info` alternatywna sciezka moze pobrac tresc przez WordPress REST API albo bezposredni HTML,
- brak realnej tresci artykulu konczy przetwarzanie danego linku przed etapem LLM,
- niekompletny wynik korekty nie trafia do reprezentacji `plain text` ani `html`.

Docelowy przeplyw danych wynikajacy z PRD `005-ppe-source-migration-prd.md`:
- domyslne wejscie listingu zmienia sie na `https://www.ppe.pl/gry`,
- domyslna konfiguracja Google Sheets wskazuje arkusz `1N82WxjskvsIyjlfwh8CxlhHJB9LEUMwbAdCI8w0J_yk` i zakladke `Sheet1`,
- parser listingu ignoruje linki do bazy gier, rankingow, menu i innych sekcji PPE,
- parser zwraca tylko pelne URL newsow PPE w formacie `https://www.ppe.pl/news/<id>/<slug>.html`,
- pobieranie tresci artykulu dla linkow PPE nadal zaczyna sie od mirrora Jina.

3. Granice odpowiedzialności
- Logika przepływu pozostaje w `main.py`.
- Integracje z zewnętrznymi usługami są rozdzielone na moduły `scrapers`, `llms` i `emails`.
- Trwałość danych dla stanu linków jest realizowana przez Google Sheets.
- Kod nie posiada obecnie oddzielonej warstwy domenowej ani interfejsów abstrakcji.

Po wdrożeniu PRD `001-google-sheets-link-store-prd.md`:
- LLM pozostanie wyłącznie komponentem generowania treści.
- pełna treść artykułów jest pobierana przez mirror Jina.

Po wdrozeniu PRD `002-gaming-email-styles-prd.md`:
- warstwa maili pozostanie odpowiedzialna za dostarczenie wiadomosci przez SMTP,
- renderer HTML bedzie odpowiadal wyłącznie za prezentacje wiadomosci,
- fallback `plain text` pozostanie czescia kontraktu wysylki dla kompatybilnosci.

Po wdrozeniu PRD `003-qwen-model-migration-prd.md`:
- warstwa LLM pozostanie odpowiedzialna wylacznie za podsumowanie i korekte tekstu,
- liczba wywolan modelu w normalnym pipeline pozostanie bez zmian,
- test live nowego modelu pozostanie czynnoscia walidacyjna, a nie etapem przetwarzania kazdego artykulu.

Po wdrozeniu PRD `004-article-content-fetch-resilience-prd.md`:
- warstwa pobierania tresci odrzuca strony bledow i uruchamia fallback,
- warstwa LLM nadal odpowiada wylacznie za podsumowanie i korekte realnej tresci artykulu,
- warstwa maili nie przyjmuje niekompletnych wynikow korekty.

Po wdrozeniu PRD `005-ppe-source-migration-prd.md`:
- aktywnym zrodlem listingu bedzie PPE,
- warstwa deduplikacji i zapisu linkow nadal bedzie oparta o Google Sheets,
- dotychczasowy fallback dla `konsolowe.info` pozostanie zachowaniem historycznym, a nie wymaganiem dla nowego zrodla.

---

## Komponenty techniczne
Lista kluczowych komponentów technicznych i ich odpowiedzialności.

- Python 3.11+ jako runtime aplikacji.
- `uv` do zarządzania środowiskiem i zależnościami.
- `python-dotenv` do ładowania konfiguracji z `.env`.
- `requests` do pobrania HTML listingu newsów.
- `bs4` i `BeautifulSoup` do parsowania linków z listingu.
- `gspread` i `google-auth` do integracji z Google Sheets przez konto serwisowe.
- `requests` do pobierania treści artykułów przez mirror Jina.
- `google-genai` do komunikacji z modelem Gemini.
- standardowa biblioteka `smtplib` i `ssl` do wysyłki e-maili.

Planowane rozszerzenia techniczne wynikające z PRD `001-google-sheets-link-store-prd.md`:
- brak dodatkowych zaleznosci wymaganych do domkniecia tego PRD.

Rozszerzenia techniczne wynikajace z PRD `002-gaming-email-styles-prd.md`:
- wykorzystanie standardowych mechanizmow MIME do zbudowania wiadomosci multipart z `text/plain` i `text/html`,
- osadzony CSS zgodny z typowymi klientami pocztowymi,
- brak nowej zaleznosci wykonawczej, o ile prosty renderer HTML da sie zrealizowac w oparciu o standardowa biblioteke lub juz obecne zaleznosci.

Planowane rozszerzenia techniczne wynikajace z PRD `003-qwen-model-migration-prd.md`:
- zmiana domyslnej wartosci `LLM_MODEL` na `qwen/qwen3.6-27b`,
- przygotowanie jednorazowej walidacji live modelu bez zapisu do Google Sheets i bez wysylki SMTP,
- warunkowe dodanie lokalnego usuwania blokow `<think>...</think>`, jesli walidacja live wykaze taka potrzebe,
- brak nowych zaleznosci wykonawczych, o ile walidacja i ewentualna sanitizacja moga zostac zrealizowane obecnym stosem.

Rozszerzenia techniczne po wdrozeniu PRD `003-qwen-model-migration-prd.md`:
- domyslna wartosc `LLM_MODEL` zostala zmieniona na `qwen/qwen3.6-27b`,
- dla modelu `qwen/qwen3.6-27b` wywolanie Groq ukrywa reasoning w odpowiedzi zwracanej do aplikacji,
- odpowiedzi modelu sa dodatkowo czyszczone z kompletnych blokow `<think>...</think>` jako zabezpieczenie,
- dla modelu `qwen/qwen3.6-27b` minimalny budzet `max_tokens` zostal podniesiony, aby reasoning nie zuzywal calego limitu przed finalna odpowiedzia,
- wynik korekty jest zabezpieczony przed utrata linku: jesli model pominie `Link:`, aplikacja dopisuje link z wejscia.

Planowane rozszerzenia techniczne wynikajace z PRD `004-article-content-fetch-resilience-prd.md`:
- wykrywanie blednych odpowiedzi Jina po tresci odpowiedzi, niezaleznie od statusu HTTP zwroconego przez Jina,
- fallback pobierania tresci przez WordPress REST API dla `konsolowe.info`,
- fallback pobierania i oczyszczania bezposredniego HTML artykulu, jesli WordPress REST API nie moze zostac uzyte,
- walidacja minimalnej kompletności wyniku korekty przed wysylka,
- brak nowych zaleznosci wykonawczych, o ile oczyszczanie HTML da sie zrealizowac obecnym stosem `requests` i `BeautifulSoup`.

Rozszerzenia techniczne po wdrozeniu PRD `004-article-content-fetch-resilience-prd.md`:
- odpowiedzi Jina zawierajace `Title: 403 Forbidden` albo `Warning: Target URL returned error 403` sa odrzucane przed etapem LLM,
- bledy HTTP lub sieciowe Jina uruchamiaja fallback dla `konsolowe.info`,
- fallback probuje pobrac tresc przez WordPress REST API, a potem przez bezposredni HTML artykulu,
- wynik korekty musi zawierac tytul, podsumowanie, link i domkniete zdanie,
- korekta Qwen uzywa nizszej temperatury i wyzszego budzetu tokenow, aby ograniczyc ryzyko pustych lub ucietych odpowiedzi,
- tresc artykulu przekazywana do promptu podsumowania jest ograniczana do ustalonego limitu znakow, z jawnym dopiskiem o pominietej dalszej czesci,
- klient Groq uzywa timeoutu zadania, zeby pojedyncze wywolanie API nie blokowalo procesu bez konca,
- nie dodano nowych zaleznosci wykonawczych.

Planowane rozszerzenia techniczne wynikajace z PRD `005-ppe-source-migration-prd.md`:
- zmiana domyslnego URL listingu na `https://www.ppe.pl/gry`,
- zmiana domyslnego `GOOGLE_SHEET_ID` na `1N82WxjskvsIyjlfwh8CxlhHJB9LEUMwbAdCI8w0J_yk`,
- zmiana domyslnego `GOOGLE_SHEET_WORKSHEET` na `Sheet1`,
- zmiana parsera linkow z miesiecznego wzorca `konsolowe.info` na wzorzec PPE `/news/<id>/<slug>.html`,
- brak nowych zaleznosci wykonawczych.

Rozszerzenia techniczne po wdrozeniu Milestone 1.7:
- domyslna wartosc `GEMINI_MODEL` wskazuje `gemini-3.5-flash`,
- `GEMINI_API_KEY` jest wymaganym sekretem dla wywolan LLM,
- klient Gemini uzywa biblioteki `google-genai` i timeoutu zadania,
- klient Gemini ponawia czasowe bledy limitu `RESOURCE_EXHAUSTED` zgodnie z `retryDelay` zwracanym przez API,
- etap podsumowania odrzuca uciete odpowiedzi bez domknietego zdania przed wysylka,
- zaleznosc `groq` zostala usunieta z aktywnych zaleznosci projektu.

Rozszerzenia techniczne po wdrozeniu Milestone 1.8:
- aktywny pipeline wykonuje jedno wywolanie LLM na poprawnie pobrany news,
- osobna korekta jezykowa zostala usunieta,
- kompletne podsumowanie jest laczone z linkiem i przekazywane do maila HTML oraz fallbacku `plain text`.

---

## Decyzje techniczne
Jawne decyzje techniczne wraz z uzasadnieniem.

Każda decyzja powinna zawierać:
- Decyzja:
- Uzasadnienie:
- Konsekwencje:

- Decyzja: zarządzanie środowiskiem i zależnościami odbywa się przez `uv` i `pyproject.toml`.
- Uzasadnienie: jedno źródło prawdy dla zależności upraszcza instalację, lockowanie wersji i uruchamianie projektu zgodnie z `AGENTS.md`.
- Konsekwencje: `requirements.txt` nie jest już utrzymywany, a instalacja projektu odbywa się przez `uv sync`.

- Decyzja: aplikacja działa jako pojedynczy skrypt uruchamiany przez `main.py`.
- Uzasadnienie: obecny zakres projektu jest mały i nie wymaga osobnej warstwy CLI, API ani serwera.
- Konsekwencje: prostsze uruchamianie kosztem słabszej rozszerzalności i mniejszej testowalności przepływu.

- Decyzja: wykrywanie nowych treści opierało się na lokalnym pliku `news_links.json`.
- Uzasadnienie: to najprostszy sposób na deduplikację bez wprowadzania bazy danych.
- Konsekwencje: decyzja historyczna; została zastąpiona przez integrację z Google Sheets w ramach Milestone 1.0.

- Decyzja: ekstrakcja linków i generowanie treści były delegowane do modelu Groq.
- Uzasadnienie: zmniejsza to ilość ręcznej logiki parsowania HTML i pozwala szybko uzyskać streszczenia po polsku.
- Konsekwencje: decyzja historyczna; po Milestone 1.1 LLM pozostaje tylko w kroku generowania podsumowania i korekty.

- Decyzja: pobieranie treści listingu i artykułów jest rozdzielone na dwa różne mechanizmy.
- Uzasadnienie: listing jest pobierany bezpośrednio z HTML źródłowego URL, a pełna treść artykułu przez `WebBaseLoader`.
- Konsekwencje: pipeline zależy od dwóch różnych ścieżek pobierania i wymaga osobnej diagnostyki dla listingu i treści artykułu.

- Decyzja: wysyłka wyników odbywa się przez SMTP z użyciem danych z `.env`.
- Uzasadnienie: pozwala zachować prosty model wdrożenia bez dodatkowych usług pośredniczących.
- Konsekwencje: aplikacja wymaga poprawnej konfiguracji serwera SMTP i bezpiecznego zarządzania hasłem nadawcy.

- Decyzja (dotyczy Milestone 1.7): aktywna warstwa LLM uzywa Google Gemini przez pakiet `google-genai`.
- Uzasadnienie: użytkownik wskazal migracje z Groq na Gemini oraz model `gemini-3.5-flash`; oficjalny SDK zapewnia bezposredni klient Gemini Developer API z konfiguracja klucza API.
- Konsekwencje: `GEMINI_API_KEY` staje sie wymaganym sekretem dla generowania podsumowan, a zaleznosc `groq` nie jest juz potrzebna w aktywnym przeplywie.

- Decyzja (dotyczy Milestone 1.7): domyslny model LLM to `gemini-3.5-flash`, z mozliwoscia nadpisania przez `GEMINI_MODEL`.
- Uzasadnienie: uzytkownik wskazal konkretny model do uzycia, a zmienna srodowiskowa zachowuje dotychczasowy wzorzec konfigurowalnego modelu bez edycji kodu.
- Konsekwencje: dokumentacja, `.env.example` i testy odnosza sie do `GEMINI_MODEL` zamiast historycznego `LLM_MODEL`.

- Decyzja (dotyczy Milestone 1.8): osobna korekta LLM zostaje usunieta z aktywnego pipeline'u.
- Uzasadnienie: podsumowanie Gemini jest wystarczajace dla obecnego zastosowania, a drugi etap zwiekszal koszt, czas wykonania i ryzyko limitow API.
- Konsekwencje: aplikacja wykonuje jedno wywolanie modelu na news; walidacja kompletnosci podsumowania pozostaje zabezpieczeniem przed wysylka ucietych odpowiedzi.

- Decyzja (dotyczy PRD: `001-google-sheets-link-store-prd.md`): źródłem prawdy dla zarejestrowanych linków ma stać się Google Sheets zamiast lokalnego pliku `news_links.json`.
- Uzasadnienie: odpowiada to dotychczasowemu, sprawdzonemu workflow z `n8n` i upraszcza współdzielenie stanu między uruchomieniami.
- Konsekwencje: poprawność działania będzie zależna od dostępu do Google Sheets i konfiguracji konta serwisowego.

- Decyzja (dotyczy PRD: `001-google-sheets-link-store-prd.md`): ekstrakcja linków z listingu ma zostać przeniesiona z LLM do deterministycznego parsera HTML.
- Uzasadnienie: linki można jednoznacznie wyciągnąć z DOM bez kosztu i niepewności odpowiedzi modelu.
- Konsekwencje: potrzebne będzie utrzymywanie selektora zgodnego ze strukturą HTML strony źródłowej.

- Decyzja (dotyczy PRD: `001-google-sheets-link-store-prd.md`): nowy link ma być dopisywany do Google Sheets przed pobraniem treści artykułu i generowaniem podsumowania.
- Uzasadnienie: zapobiega to ponownemu podejmowaniu tego samego linku w kolejnym przebiegu i odwzorowuje wcześniejszy workflow.
- Konsekwencje: nieudane dalsze przetwarzanie po udanym append nie spowoduje automatycznego ponownego podjęcia linku.

- Decyzja (dotyczy PRD: `001-google-sheets-link-store-prd.md`): pełna treść nowego artykułu ma być pobierana przez `https://r.jina.ai/<link>`.
- Uzasadnienie: upraszcza to pobieranie treści i zachowuje zgodność funkcjonalną z wcześniejszym rozwiązaniem w `n8n`.
- Konsekwencje: pipeline będzie zależny jednocześnie od Google Sheets, źródłowego HTML listingu i mirrora Jina.

- Decyzja (dotyczy PRD: `001-google-sheets-link-store-prd.md`): uwierzytelnienie do Google Sheets ma wykorzystywać konto serwisowe, analogicznie do projektu `DramaChecker`.
- Uzasadnienie: w repo istnieje już sprawdzony wzorzec integracji z tym mechanizmem.
- Konsekwencje: uruchomienie będzie wymagało pliku JSON konta serwisowego poza repozytorium i nowych zmiennych środowiskowych.

- Konflikt specyfikacji (dotyczy PRD: `001-google-sheets-link-store-prd.md`): brak aktywnego konfliktu po wdrozeniu Milestone 1.2.
- Uzasadnienie: zrodlo stanu, ekstrakcja listingu i pobieranie tresci artykulu zostaly doprowadzone do stanu zgodnego z PRD.
- Konsekwencje: kolejne zmiany moga juz wychodzic od nowego, docelowego pipeline'u, a nie od stanu przejsciowego.

- Decyzja (dotyczy PRD: `002-gaming-email-styles-prd.md`): wysylka maili ma zostac rozszerzona z pojedynczego `plain text` body do wiadomosci multipart zawierajacej `text/plain` oraz `text/html`.
- Uzasadnienie: pozwala to poprawic prezentacje wiadomosci bez utraty kompatybilnosci z klientami pocztowymi i scenariuszami ograniczonego renderowania HTML.
- Konsekwencje: interfejs warstwy mailowej bedzie musial przygotowywac dwie reprezentacje tej samej tresci i testowac obie sciezki.

- Decyzja (dotyczy PRD: `002-gaming-email-styles-prd.md`): inspiracja z projektu `DramaChecker` ma dotyczyc techniki budowy maila HTML i osadzonego CSS, ale bez kopiowania layoutu 1:1.
- Uzasadnienie: w sasiednim projekcie istnieje juz sprawdzony wzorzec techniczny, ktory mozna wykorzystac bez utraty tozsamosci wizualnej GameFlash.
- Konsekwencje: implementacja moze przejac podejscie do renderowania HTML, ale musi przygotowac osobny styl i kolorystyke dla newsow gamingowych.

- Decyzja (dotyczy PRD: `002-gaming-email-styles-prd.md`): stylowana warstwa HTML ma pozostac lekka, bez zaleznosci od zewnetrznych fontow, CDN, zdalnych stylow i hostowanych obrazow jako wymogu v1.
- Uzasadnienie: ogranicza to ryzyko problemow z kompatybilnoscia klientow pocztowych i utrzymuje prosty charakter projektu.
- Konsekwencje: implementacja musi opierac sie na osadzonym CSS i tresci tekstowej, a efekt wizualny bedzie budowany glownie ukladem, kontrastem i kolorystyka.

- Konflikt specyfikacji (dotyczy PRD: `002-gaming-email-styles-prd.md`): brak aktywnego konfliktu na etapie planowania.
- Uzasadnienie: nowe PRD rozszerza jedynie sposob prezentacji i wysylki wiadomosci, bez zmiany logiki pobierania, deduplikacji i podsumowania newsow.
- Konsekwencje: nowy przyrost moze zostac zaplanowany jako kolejny milestone po Milestone 1.2 bez rewizji poprzednich decyzji funkcjonalnych.

- Konflikt specyfikacji (dotyczy PRD: `002-gaming-email-styles-prd.md`): brak aktywnego konfliktu po wdrozeniu Milestone 1.3.
- Uzasadnienie: nowy format maila zostal wdrozony bez zmiany logiki pobierania, deduplikacji i podsumowania newsow.
- Konsekwencje: kolejne zmiany moga rozwijac warstwe prezentacji maila lub kolejne funkcje produktu bez rewizji poprzedniego pipeline'u.

- Decyzja (dotyczy PRD: `003-qwen-model-migration-prd.md`): domyslnym modelem Groq ma zostac `qwen/qwen3.6-27b`, przy zachowaniu mozliwosci nadpisania przez `LLM_MODEL`.
- Uzasadnienie: dotychczasowy model `meta-llama/llama-4-scout-17b-16e-instruct` ma zostac wycofany, a zachowanie `LLM_MODEL` pozwala awaryjnie zmienic model bez edycji kodu.
- Konsekwencje: dokumentacja i przykladowa konfiguracja musza wskazywac nowy model jako rekomendowana wartosc.

- Decyzja (dotyczy PRD: `003-qwen-model-migration-prd.md`): przed pelna podmiana modelu ma zostac wykonana jednorazowa walidacja live modelu `qwen/qwen3.6-27b`.
- Uzasadnienie: nowy model jest modelem rozumujacym i trzeba sprawdzic, czy zachowuje oczekiwany format odpowiedzi dla podsumowania i korekty.
- Konsekwencje: walidacja live nie moze byc czescia normalnego pipeline'u dla kazdego artykulu, nie moze zapisywac danych do Google Sheets i nie moze wysylac SMTP.

- Decyzja (dotyczy PRD: `003-qwen-model-migration-prd.md`): usuwanie blokow `<think>...</think>` ma zostac dodane tylko wtedy, gdy walidacja live wykaze, ze nowy model zwraca takie bloki.
- Uzasadnienie: nie nalezy dodawac dodatkowej logiki czyszczenia, jesli model w praktyce zwraca tylko finalna odpowiedz w oczekiwanym formacie.
- Konsekwencje: implementacja musi udokumentowac wynik walidacji i albo dodac sanitizacje z testami, albo pozostawic pipeline bez dodatkowego czyszczenia.

- Konflikt specyfikacji (dotyczy PRD: `003-qwen-model-migration-prd.md`): brak aktywnego konfliktu na etapie planowania.
- Uzasadnienie: PRD zmienia domyslny model i wprowadza walidacje ryzyka reasoning, ale nie zmienia zrodla danych, deduplikacji, liczby wywolan modelu ani wysylki maili.
- Konsekwencje: przyrost moze zostac zaplanowany jako kolejny milestone po Milestone 1.3.

- Konflikt specyfikacji (dotyczy PRD: `003-qwen-model-migration-prd.md`): brak aktywnego konfliktu po wdrozeniu Milestone 1.4.
- Uzasadnienie: migracja modelu zostala wdrozona bez zmiany liczby wywolan modelu, zrodla danych, deduplikacji i wysylki maili.
- Konsekwencje: kolejne zmiany moga rozwijac jakosc promptow lub walidacje konfiguracji bez rewizji decyzji o modelu domyslnym.

- Decyzja (dotyczy PRD: `004-article-content-fetch-resilience-prd.md`): odpowiedz Jina ma byc walidowana po tresci przed przekazaniem jej do LLM.
- Uzasadnienie: Jina moze zwrocic status `HTTP 200`, mimo ze trescia odpowiedzi jest blad zrodla, na przyklad `403 Forbidden`.
- Konsekwencje: strony bledow, puste tresci i skrajnie krotkie odpowiedzi nie beda traktowane jako artykul do podsumowania.

- Decyzja (dotyczy PRD: `004-article-content-fetch-resilience-prd.md`): dla `konsolowe.info` fallbackiem pobierania tresci ma byc WordPress REST API, a nastepnie bezposredni HTML artykulu.
- Uzasadnienie: artykuly zrodla sa publikowane w WordPressie, a publiczny endpoint moze zwrocic pelna tresc nawet wtedy, gdy Jina jest blokowana.
- Konsekwencje: warstwa pobierania tresci bedzie miec wiecej niz jedna sciezke dla artykulu, ale bez dodawania nowego zrodla newsow.

- Decyzja (dotyczy PRD: `004-article-content-fetch-resilience-prd.md`): jesli nie udalo sie pobrac realnej tresci artykulu, link ma zostac pominiety bez wywolania LLM.
- Uzasadnienie: brak tresci artykulu jest bezpieczniejszy niz wygenerowanie halucynowanego podsumowania na podstawie tytulu, bledu lub metadanych.
- Konsekwencje: link dopisany juz do Google Sheets nie bedzie automatycznie usuwany, a dany news moze nie zostac wyslany w biezacym przebiegu.

- Decyzja (dotyczy PRD: `004-article-content-fetch-resilience-prd.md`): wynik korekty jezykowej musi zostac sprawdzony pod katem minimalnej kompletności przed wysylka.
- Uzasadnienie: model moze zwrocic tekst uciety albo pominac wymagane pola, nawet jesli link zostanie dopisany przez zabezpieczenie.
- Konsekwencje: niekompletny wynik korekty nie trafi do e-maila HTML ani fallbacku `plain text`.

- Konflikt specyfikacji (dotyczy PRD: `004-article-content-fetch-resilience-prd.md`): PRD doprecyzowuje historyczna decyzje o pobieraniu pelnej tresci artykulow przez Jina.
- Uzasadnienie: Milestone 1.2 zakladal Jina jako sciezke pobierania tresci, ale zaobserwowano przypadek, w ktorym Jina zwrocila blad zrodla jako tresc odpowiedzi `HTTP 200`.
- Konsekwencje: Jina pozostaje pierwsza proba pobrania tresci, ale nie bedzie jedynym ani bezwarunkowo zaufanym zrodlem tresci artykulu.

- Decyzja (dotyczy PRD: `005-ppe-source-migration-prd.md`): aktywnym zrodlem listingu newsow ma zostac `https://www.ppe.pl/gry`.
- Uzasadnienie: dotychczasowe zrodlo `konsolowe.info` przestalo dostarczac swieze newsy w oczekiwanym rytmie.
- Konsekwencje: parser listingu musi zostac dostosowany do struktury PPE, a dokumentacja operacyjna ma wskazywac nowe aktywne zrodlo.

- Decyzja (dotyczy PRD: `005-ppe-source-migration-prd.md`): domyslnym arkuszem stanu ma zostac `gameflash_sheet_ppe` o ID `1N82WxjskvsIyjlfwh8CxlhHJB9LEUMwbAdCI8w0J_yk`, zakladka `Sheet1`.
- Uzasadnienie: nowy arkusz oddziela stan przetwarzania PPE od historycznego stanu poprzedniego zrodla.
- Konsekwencje: `GOOGLE_SHEET_ID` i `GOOGLE_SHEET_WORKSHEET` nadal moga nadpisac domyslne wartosci, ale konto serwisowe musi miec dostep do nowego arkusza z kolumna `Links`.

- Decyzja (dotyczy PRD: `005-ppe-source-migration-prd.md`): parser PPE ma zwracac wylacznie linki newsowe pasujace do `/news/<id>/<slug>.html`.
- Uzasadnienie: strona `https://www.ppe.pl/gry` zawiera rowniez baze gier, rankingi, menu i linki promocyjne, ktore nie sa newsami do maila GameFlash.
- Konsekwencje: linki `/gry/...`, `/news.html`, rankingi i nawigacja sa ignorowane, a wzgledne linki newsow sa normalizowane do pelnych URL w domenie `https://www.ppe.pl`.

- Decyzja (dotyczy PRD: `005-ppe-source-migration-prd.md`): pierwszy przebieg na pustym arkuszu PPE ma normalnie przetworzyc widoczne newsy.
- Uzasadnienie: celem migracji jest natychmiastowe przejscie na aktywne zrodlo, bez osobnego trybu inicjalizacji stanu.
- Konsekwencje: jesli arkusz zawiera tylko naglowek `Links`, wszystkie widoczne, nowe linki `/news/` z listingu PPE moga trafic do pierwszego maila.

- Konflikt specyfikacji (dotyczy PRD: `005-ppe-source-migration-prd.md`): PRD zmienia historyczne zalozenie, ze parser linkow opiera sie na wzorcu `https://konsolowe.info/<YYYY>/<MM>/`.
- Uzasadnienie: PPE nie koduje roku i miesiaca w linkach newsow, dlatego dotychczasowy selektor miesieczny nie moze obslugiwac nowego aktywnego zrodla.
- Konsekwencje: po wdrozeniu PRD `005-ppe-source-migration-prd.md` aktywny parser ma byc zgodny z PPE, a wzorzec `konsolowe.info` pozostaje elementem historycznego opisu poprzedniego zrodla.

---

## Jakość i kryteria akceptacji
Wspólne wymagania jakościowe dla obecnej wersji:
- aplikację da się przygotować komendą `uv sync`,
- aplikację da się uruchomić komendą `uv run main.py`,
- konfiguracja sekretów nie jest przechowywana w repo,
- nowe linki nie są ponownie wysyłane, jeśli wcześniej trafiły do Google Sheets,
- wiadomość e-mail zawiera wszystkie nowe podsumowania z jednego przebiegu,
- brak nowych zależności bez aktualizacji sekcji `Decyzje techniczne`,
- kod pozostaje prosty, modułowy i bez ukrytej magii.

Kryteria akceptacji dla stanu aktualnego:
- projekt posiada działającą konfigurację `uv`,
- `main.py` integruje pobieranie danych, wywołania LLM, deduplikację i wysyłkę e-maili,
- dokumentacja w `README.md` opisuje uruchomienie i wymagane zmienne środowiskowe,
- specyfikacja odzwierciedla faktyczny stan repo, łącznie z ograniczeniami i ryzykami.

Minimalne kryteria akceptacji dla rozszerzenia z PRD `001-google-sheets-link-store-prd.md`:
- dla poprawnej konfiguracji Google Sheets aplikacja odczytuje kolumnę `Links` bez lokalnej bazy JSON,
- link obecny już w Google Sheets nie jest pobierany ani podsumowywany ponownie,
- nowy link jest dopisywany do Google Sheets przed pobraniem treści artykułu,
- błąd append do Google Sheets blokuje przetwarzanie tego linku w bieżącym przebiegu,
- po udanym append aplikacja kontynuuje dalsze przetwarzanie linku,
- LLM nie uczestniczy już w ekstrakcji linków z listingu,
- pelna treść artykułu jest pobierana przez `https://r.jina.ai/<link>`,
- błąd pobrania lub podsumowania po udanym append nie powoduje ponownego podjęcia linku w kolejnym przebiegu.

Minimalne kryteria akceptacji dla rozszerzenia z PRD `002-gaming-email-styles-prd.md`:
- dla co najmniej jednego nowego newsa aplikacja przygotowuje wiadomosc HTML z czytelnymi sekcjami zawierajacymi tytul, streszczenie i link do artykulu,
- wiadomosc e-mail jest wysylana jako multipart zawierajacy `text/plain` oraz `text/html`,
- fallback `plain text` nadal zawiera komplet informacji o wszystkich newsach z danego przebiegu,
- styl HTML nie zalezy od zewnetrznych obrazow, fontow ani zdalnych stylow,
- uklad wiadomosci pozostaje czytelny przy wielu newsach i na waskich ekranach,
- zmiana formatu wiadomosci nie wprowadza regresji w wysylce do wielu odbiorcow.

Minimalne kryteria akceptacji dla rozszerzenia z PRD `003-qwen-model-migration-prd.md`:
- aplikacja domyslnie uzywa modelu `qwen/qwen3.6-27b`, jesli `LLM_MODEL` nie zostal ustawiony,
- `LLM_MODEL` nadal pozwala nadpisac domyslny model,
- jednorazowa walidacja live nowego modelu sprawdza format odpowiedzi, jezyk polski oraz obecnosc albo brak blokow `<think>...</think>`,
- walidacja live nie zapisuje linkow do Google Sheets i nie wysyla e-maila,
- jesli walidacja live wykaze bloki `<think>...</think>`, implementacja usuwa je przed dalszym przetwarzaniem i pokrywa testami,
- jesli walidacja live nie wykaze blokow `<think>...</think>`, pipeline nie otrzymuje dodatkowej sanitizacji,
- normalny pipeline nadal wykonuje dwa wywolania modelu na poprawnie przetworzony news.

Minimalne kryteria akceptacji dla rozszerzenia z PRD `004-article-content-fetch-resilience-prd.md`:
- odpowiedz Jina zawierajaca `Title: 403 Forbidden` albo `Warning: Target URL returned error 403` jest traktowana jako blad pobrania tresci,
- tresc bledu Jina nie trafia do promptu podsumowania,
- po blednej odpowiedzi Jina aplikacja probuje pobrac tresc przez fallback dla `konsolowe.info`,
- jesli fallback zwroci realna tresc artykulu, aplikacja kontynuuje podsumowanie i korekte,
- jesli nie uda sie pobrac realnej tresci artykulu, aplikacja pomija link bez wywolania LLM,
- niekompletny wynik korekty nie jest wysylany w mailu HTML ani `plain text`,
- testy jednostkowe pokrywaja bledna odpowiedz Jina, fallback i brak realnego IO.

Minimalne kryteria akceptacji dla rozszerzenia z PRD `005-ppe-source-migration-prd.md`:
- aplikacja domyslnie pobiera listing z `https://www.ppe.pl/gry`,
- aplikacja domyslnie uzywa arkusza `1N82WxjskvsIyjlfwh8CxlhHJB9LEUMwbAdCI8w0J_yk` i zakladki `Sheet1`,
- parser zwraca pelne URL dla linkow PPE `/news/<id>/<slug>.html`,
- parser ignoruje linki `/gry/...`, rankingi, menu, `/news.html` i obce domeny,
- link obecny juz w kolumnie `Links` nie jest przetwarzany ponownie,
- nowy link PPE jest dopisywany do Google Sheets przed pobraniem tresci artykulu,
- pierwszy pusty arkusz PPE przetwarza widoczne newsy zamiast tylko inicjalizowac stan,
- testy jednostkowe pokrywaja parser PPE, limit wejscia artykulu, timeout Groq i nowy przeplyw bez realnego IO,
- walidacja live potwierdza wysylke zbiorczego maila dla 3 newsow PPE.

---

## Zasady zmian i ewolucji
- zmiany funkcjonalne → aktualizacja `ROADMAP.md`
- zmiany architektoniczne → aktualizacja tej specyfikacji
- nowe zależności → wpis do `## Decyzje techniczne`
- refactory tylko w ramach aktualnego milestone’u

---

## Powiązanie z roadmapą
- Szczegóły milestone'ów i ich statusy znajdują się w `ROADMAP.md`.
- Aktualny kod odpowiada etapowi wczesnego, działającego workflow end-to-end, ale nadal nie spełnia wszystkich oczekiwań jakościowych z Milestone 0.5, głównie z powodu braku testów i twardo zakodowanej części konfiguracji.
- PRD `001-google-sheets-link-store-prd.md` wprowadza kolejny przyrost funkcjonalny: migrację deduplikacji linków do Google Sheets i usunięcie LLM z kroku ekstrakcji linków.
- Realizacja tego PRD wymaga nowych milestone'ów po Milestone 0.5, obejmujących integrację z Google Sheets, migrację przepływu i domknięcie jakości operacyjnej.
- PRD `002-gaming-email-styles-prd.md` wprowadza kolejny przyrost funkcjonalny: przejscie z maila `plain text` na stylowana wiadomosc HTML z fallbackiem `plain text`.
- PRD `003-qwen-model-migration-prd.md` wprowadza kolejny przyrost funkcjonalny: migracje domyslnego modelu Groq na `qwen/qwen3.6-27b` wraz z walidacja live ryzyka reasoning.
- PRD `004-article-content-fetch-resilience-prd.md` wprowadza kolejny przyrost funkcjonalny: odporne pobieranie tresci artykulow, fallback dla `konsolowe.info` i blokade podsumowan z blednych zrodel.
- PRD `005-ppe-source-migration-prd.md` wprowadza kolejny przyrost funkcjonalny: migracje aktywnego zrodla newsow na PPE i nowy arkusz Google Sheets.
- Milestone 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7 i 1.8 sa wdrozone.

---

## Status specyfikacji
- Data utworzenia: 2026-03-21
- Ostatnia aktualizacja: 2026-07-01
- Aktualny zakres obowiązywania: stan repo po wdrozeniu Milestone 1.8 i usunieciu osobnej korekty LLM
