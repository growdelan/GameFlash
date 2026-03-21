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

---

## Zakres funkcjonalny (high-level)
Kluczowe use-case'i:
- pobranie listy treści ze strony z newsami o grach,
- wyodrębnienie linków do nowych artykułów z bieżącego miesiąca,
- pobranie pełnej treści nowych artykułów,
- wygenerowanie krótkich podsumowań po polsku,
- korekta językowa podsumowań,
- wysłanie zbiorczego e-maila do wielu odbiorców.

Główny przepływ:
1. Aplikacja ładuje konfigurację z `.env`.
2. Tworzy lub odczytuje lokalny plik `news_links.json`.
3. Pobiera stronę listingu newsów przez Jina AI.
4. Wysyła treść listingu do modelu Groq, aby uzyskać JSON z linkami.
5. Odfiltrowuje linki już zapisane lokalnie.
6. Dla nowych linków pobiera treść artykułów przez `WebBaseLoader`.
7. Generuje podsumowania i wykonuje ich korektę językową.
8. Wysyła pojedynczy e-mail ze wszystkimi nowymi podsumowaniami.

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
- `scrapers/jina.py` pobiera listing newsów przez usługę `https://r.jina.ai/`.
- `scrapers/lang_webbaseloader.py` pobiera treść pojedynczego artykułu.
- `llms/groq.py` buduje prompty i wykonuje wywołania modelu Groq.
- `utils/utils.py` zarządza lokalnym plikiem JSON z historią przetworzonych linków.
- `emails/gmail.py` składa i wysyła wiadomość SMTP.

Planowane rozszerzenie komponentów wynikające z PRD `001-google-sheets-link-store-prd.md`:
- moduł integracji z Google Sheets wzorowany na podejściu z `DramaChecker`,
- parser HTML do deterministycznej ekstrakcji linków z listingu,
- usunięcie odpowiedzialności LLM za identyfikację linków wejściowych.

2. Przepływ danych między komponentami
- Wejście konfiguracyjne pochodzi z `.env` i stałych zaszytych w `main.py`.
- Listing newsów jest pobierany jako surowa treść tekstowa przez Jina AI.
- Model Groq zamienia listing na JSON z listą linków.
- Moduł `utils` porównuje nowe linki z lokalną bazą `news_links.json`.
- Dla nowych linków pobierana jest pełna treść artykułów.
- Model Groq generuje podsumowanie, a następnie osobny prompt wykonuje korektę tekstu.
- Gotowe sekcje podsumowań są łączone w jeden e-mail wysyłany przez SMTP.

Docelowy przepływ danych wynikający z PRD `001-google-sheets-link-store-prd.md`:
- Wejście konfiguracyjne ma obejmować także `GOOGLE_SHEET_ID`, `GOOGLE_SHEET_WORKSHEET` i `GSPREAD_SERVICE_ACCOUNT_FILE`.
- Google Sheets ma stać się źródłem prawdy dla listy już zarejestrowanych linków.
- Listing newsów ma być pobierany jako HTML bezpośrednio z URL źródłowego.
- Parser HTML ma wyodrębniać linki zgodne ze wzorcem `https://konsolowe.info/<YYYY>/<MM>/`.
- Każdy nowy link ma zostać zapisany w Google Sheets przed pobraniem treści artykułu.
- Pełna treść artykułu ma być pobierana przez mirror `https://r.jina.ai/<link>`.
- Model Groq ma pozostać odpowiedzialny wyłącznie za podsumowanie i korektę tekstu.

3. Granice odpowiedzialności
- Logika przepływu pozostaje w `main.py`.
- Integracje z zewnętrznymi usługami są rozdzielone na moduły `scrapers`, `llms` i `emails`.
- Trwałość danych jest ograniczona do lokalnego pliku JSON.
- Kod nie posiada obecnie oddzielonej warstwy domenowej ani interfejsów abstrakcji.

Po wdrożeniu PRD `001-google-sheets-link-store-prd.md`:
- Google Sheets przejmie rolę trwałego magazynu stanu linków.
- LLM przestanie odpowiadać za wykrywanie linków wejściowych i pozostanie wyłącznie komponentem generowania treści.
- parser HTML będzie odpowiedzialny za wykrycie kandydatów do przetwarzania.

---

## Komponenty techniczne
Lista kluczowych komponentów technicznych i ich odpowiedzialności.

- Python 3.11+ jako runtime aplikacji.
- `uv` do zarządzania środowiskiem i zależnościami.
- `python-dotenv` do ładowania konfiguracji z `.env`.
- `requests` do pobrania listingu newsów przez Jina AI.
- `langchain-community` i `WebBaseLoader` do pobierania treści artykułów.
- `groq` do komunikacji z modelem LLM.
- standardowa biblioteka `smtplib` i `ssl` do wysyłki e-maili.
- standardowa biblioteka `json` do obsługi lokalnej bazy linków.

Planowane rozszerzenia techniczne wynikające z PRD `001-google-sheets-link-store-prd.md`:
- klient Google Sheets oparty o `gspread` i konto serwisowe,
- parser HTML oparty o `BeautifulSoup` lub równoważny mechanizm selektorów CSS.

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

- Decyzja: wykrywanie nowych treści opiera się na lokalnym pliku `news_links.json`.
- Uzasadnienie: to najprostszy sposób na deduplikację bez wprowadzania bazy danych.
- Konsekwencje: rozwiązanie jest lokalne, stanowe i podatne na problemy przy równoległym uruchamianiu.

- Decyzja: ekstrakcja linków i generowanie treści są delegowane do modelu Groq.
- Uzasadnienie: zmniejsza to ilość ręcznej logiki parsowania HTML i pozwala szybko uzyskać streszczenia po polsku.
- Konsekwencje: jakość wyniku zależy od promptów, formatu odpowiedzi modelu i dostępności zewnętrznej usługi.

- Decyzja: pobieranie treści listingu i artykułów jest rozdzielone na dwa różne mechanizmy.
- Uzasadnienie: listing jest pobierany przez Jina AI jako uproszczony tekst, a pełna treść artykułu przez `WebBaseLoader`.
- Konsekwencje: pipeline zależy od dwóch zewnętrznych ścieżek pobierania i może wymagać osobnej diagnostyki dla każdej z nich.

- Decyzja: wysyłka wyników odbywa się przez SMTP z użyciem danych z `.env`.
- Uzasadnienie: pozwala zachować prosty model wdrożenia bez dodatkowych usług pośredniczących.
- Konsekwencje: aplikacja wymaga poprawnej konfiguracji serwera SMTP i bezpiecznego zarządzania hasłem nadawcy.

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

- Konflikt specyfikacji (dotyczy PRD: `001-google-sheets-link-store-prd.md`): obecna implementacja i wcześniejsze decyzje opisują lokalny plik `news_links.json` oraz ekstrakcję linków przez LLM, podczas gdy nowe PRD definiuje docelowe przejście na Google Sheets i parser HTML.
- Uzasadnienie: PRD rozszerza projekt o nowy, docelowy mechanizm deduplikacji i pobierania linków, który nie jest jeszcze wdrożony w kodzie.
- Konsekwencje: do czasu implementacji specyfikacja opisuje jednocześnie stan bieżący i zatwierdzony kierunek zmiany; nie należy usuwać wcześniejszych decyzji, dopóki migracja nie zostanie zrealizowana.

---

## Jakość i kryteria akceptacji
Wspólne wymagania jakościowe dla obecnej wersji:
- aplikację da się przygotować komendą `uv sync`,
- aplikację da się uruchomić komendą `uv run main.py`,
- konfiguracja sekretów nie jest przechowywana w repo,
- nowe linki nie są ponownie wysyłane, jeśli wcześniej trafiły do `news_links.json`,
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
- po udanym append aplikacja pobiera pełną treść przez `https://r.jina.ai/<link>`,
- LLM nie jest już używany do ekstrakcji linków z listingu.

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

---

## Status specyfikacji
- Data utworzenia: 2026-03-21
- Ostatnia aktualizacja: 2026-03-21
- Aktualny zakres obowiązywania: obecny stan aplikacji po migracji operacyjnej na `uv` oraz zatwierdzony kierunek rozszerzenia wynikający z PRD `001-google-sheets-link-store-prd.md`
