# Roadmapa (milestones)

## Statusy milestone’ów
Dozwolone statusy:
- planned
- in_progress
- done
- blocked

---

## Milestone 0.5: Minimal end-to-end slice (done)

Cel:
- aplikacja uruchamia się
- wykonuje jedno bardzo proste zadanie
- zwraca poprawny wynik

Definition of Done:
- aplikację da się uruchomić jednym poleceniem (opisanym w README.md)
- istnieje co najmniej jeden smoke test
- testy przechodzą lokalnie
- brak placeholderów w kodzie

Zakres:
- minimalny entrypoint aplikacji
- minimalna logika domenowa
- minimalna obsługa IO (jeśli dotyczy)
- smoke test end-to-end

---

## Milestone <numer>: <nazwa> (<status>)

Cel:
Definition of Done:
Zakres:
Uwagi:

---

## Milestone 1.0: Google Sheets jako baza linków (done)

Cel:
- zastąpić lokalny plik `news_links.json` arkuszem Google Sheets jako źródłem stanu linków
- przygotować aplikację do pracy z arkuszem `Arkusz1` i kolumną `Links`

Definition of Done:
- aplikacja potrafi uwierzytelnić się do Google Sheets kontem serwisowym
- aplikacja potrafi odczytać istniejące linki z arkusza o ID `1o0htAcR-8ej4u9GiRCYHxxvFKE7BhCaryB6nqkM-KTI`
- nowy link jest dopisywany do Google Sheets przed dalszym przetwarzaniem
- lokalny mechanizm deduplikacji oparty o `news_links.json` nie jest już używany w tym przepływie

Zakres:
- integracja z Google Sheets wzorowana na `DramaChecker`
- obsługa konfiguracji `GOOGLE_SHEET_ID`, `GOOGLE_SHEET_WORKSHEET` i `GSPREAD_SERVICE_ACCOUNT_FILE`
- odczyt kolumny `Links`
- append nowych linków do arkusza

---

## Milestone 1.1: Deterministyczna ekstrakcja linków z HTML (done)

Cel:
- usunąć użycie LLM z kroku wykrywania linków do newsów
- odwzorować logikę ekstrakcji znaną z workflow `n8n`

Definition of Done:
- listing newsów jest pobierany bezpośrednio z URL źródłowego
- linki są wyciągane parserem HTML według wzorca `https://konsolowe.info/<YYYY>/<MM>/`
- duplikaty z bieżącego przebiegu są usuwane przed porównaniem z Google Sheets
- `groq.news_prompt()` i zależność od odpowiedzi JSON modelu nie są już potrzebne do wykrywania linków

Zakres:
- pobranie HTML strony listingu
- parser HTML z selektorem odpowiadającym obecnemu wzorcowi linków
- deduplikacja lokalna w jednym przebiegu
- filtrowanie nowych linków względem Google Sheets

---

## Milestone 1.2: Domknięcie nowego pipeline'u przetwarzania linków (done)

Cel:
- spiąć nowy przepływ od wykrycia linku do wysyłki e-maila bez regresji biznesowej
- zachować podsumowanie LLM i wysyłkę e-maili po migracji stanu i ekstrakcji

Definition of Done:
- po udanym append do Google Sheets aplikacja pobiera treść artykułu przez `https://r.jina.ai/<link>`
- link obecny już w Google Sheets nie jest ponownie przetwarzany
- błąd append do Google Sheets blokuje przetwarzanie tego linku w bieżącym przebiegu
- błąd po udanym append nie powoduje automatycznego ponownego podjęcia linku w kolejnym przebiegu
- dokumentacja operacyjna opisuje nowy przepływ i wymagane zmienne środowiskowe

Zakres:
- przełączenie pobierania pełnej treści artykułów na mirror Jina dla nowego przepływu
- integracja nowej deduplikacji z istniejącym etapem podsumowania i e-maila
- aktualizacja README i pozostałej dokumentacji operacyjnej po implementacji
- przygotowanie testów i smoke testów dla nowego przepływu bez realnego IO

---

## Milestone 1.3: Stylowany e-mail HTML dla GameFlash (done)

Cel:
- zastapic obecna wiadomosc `plain text` stylowanym mailem HTML dopasowanym do newsow gamingowych
- zachowac kompatybilny fallback `plain text` i brak regresji w istniejacym pipeline'ie wysylki

Definition of Done:
- aplikacja generuje wiadomosc multipart zawierajaca `text/plain` oraz `text/html`
- wariant HTML prezentuje kazdy news jako osobna, czytelna sekcje z tytulem, streszczeniem i CTA do pelnego artykulu
- styl HTML wykorzystuje osadzony CSS bez zaleznosci od zewnetrznych fontow, CDN, zdalnych stylow i hostowanych obrazow jako wymogu v1
- uklad wiadomosci pozostaje czytelny dla wielu newsow oraz na waskich ekranach
- testy lokalne pokrywaja render HTML, fallback `plain text` i brak zaleznosci od realnego SMTP

Zakres:
- rozszerzenie warstwy mailowej o renderer HTML dla wiadomosci GameFlash
- przygotowanie maila multipart z warstwa `text/plain` i `text/html`
- zaprojektowanie nowoczesnej, gamingowej stylistyki wiadomosci
- dostosowanie testow jednostkowych i smoke testow do nowego formatu e-maila

---

## Milestone 1.4: Migracja modelu Groq na Qwen 3.6 27B (done)

Cel:
- zastapic domyslny model `meta-llama/llama-4-scout-17b-16e-instruct` modelem `qwen/qwen3.6-27b`
- potwierdzic w jednorazowej walidacji live zachowanie oczekiwanego formatu odpowiedzi przez nowy model
- rozstrzygnac na podstawie testu live, czy potrzebne jest usuwanie blokow `<think>...</think>`

Definition of Done:
- domyslny fallback `LLM_MODEL` wskazuje `qwen/qwen3.6-27b`
- konfiguracja przez `LLM_MODEL` nadal pozwala nadpisac model
- jednorazowa walidacja live nowego modelu nie zapisuje danych do Google Sheets i nie wysyla SMTP
- wynik walidacji live wskazuje, czy odpowiedz zawiera bloki `<think>...</think>`
- jesli walidacja live wykaze bloki `<think>...</think>`, aplikacja usuwa je przed dalszym przetwarzaniem i ma testy jednostkowe dla tego zachowania
- jesli walidacja live nie wykaze blokow `<think>...</think>`, pipeline pozostaje bez dodatkowej sanitizacji
- normalny pipeline nadal wykonuje dwa wywolania modelu na jeden poprawnie przetworzony news
- dokumentacja operacyjna opisuje nowy model i sposob walidacji
- testy lokalne przechodza komenda `uv run python -m unittest discover -s tests -p "test_*.py"`

Zakres:
- podmiana domyslnej wartosci modelu w konfiguracji aplikacji
- aktualizacja `.env.example`, README i dokumentacji operacyjnej modelu
- przygotowanie izolowanej walidacji live na stalej probce artykulu
- warunkowe dodanie usuwania blokow `<think>...</think>` w odpowiedziach modelu
- dostosowanie testow jednostkowych do wyniku walidacji live

---

## Milestone 1.5: Odporne pobieranie treści artykułów (done)

Cel:
- zabezpieczyc pipeline przed podsumowywaniem stron bledow zwroconych przez Jina jako tresc odpowiedzi `HTTP 200`
- dodac fallback pobierania tresci artykulow z `konsolowe.info`
- zablokowac wysylke niekompletnych wynikow korekty

Definition of Done:
- odpowiedzi Jina zawierajace `Title: 403 Forbidden` albo `Warning: Target URL returned error 403` sa traktowane jako blad pobrania tresci
- tresc bledu Jina nie trafia do promptu podsumowania
- po blednej odpowiedzi Jina aplikacja probuje fallbacku przez WordPress REST API dla `konsolowe.info`
- jesli WordPress REST API nie moze zostac uzyte, aplikacja moze sprobowac pobrac i oczyscic bezposredni HTML artykulu
- jesli zadna sciezka nie zwroci realnej tresci artykulu, link jest pomijany bez wywolania LLM
- niekompletny wynik korekty nie trafia do e-maila HTML ani fallbacku `plain text`
- testy lokalne przechodza komenda `uv run python -m unittest discover -s tests -p "test_*.py"`

Zakres:
- walidacja tresci zwracanej przez Jina mimo poprawnego statusu odpowiedzi
- fallback pobierania tresci przez WordPress REST API dla `konsolowe.info`
- fallback pobierania i oczyszczania bezposredniego HTML artykulu
- integracja pomijania linku z obecnym etapem podsumowania
- walidacja kompletności wyniku korekty przed wysylka
- testy jednostkowe bez realnego IO dla bledow Jina, fallbacku i blokady LLM
