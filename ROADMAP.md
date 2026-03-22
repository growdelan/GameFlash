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

## Milestone 1.1: Deterministyczna ekstrakcja linków z HTML (planned)

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

## Milestone 1.2: Domknięcie nowego pipeline'u przetwarzania linków (planned)

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
