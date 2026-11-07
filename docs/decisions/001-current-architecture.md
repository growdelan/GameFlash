# 001. Aktualna architektura GameFlash

- Status: obowiązuje
- Data konsolidacji: 2026-11-07
- Zakres: stan po migracji OpenAI

Dokument konsoliduje wyłącznie aktualne decyzje. Wcześniejsze warianty pozostają w historii Git i PRD.

## Zarządzanie środowiskiem przez `uv`

- Decyzja: środowisko i zależności są zarządzane przez `uv` oraz `pyproject.toml`.
- Uzasadnienie: jedno źródło prawdy upraszcza instalację, lockowanie i uruchamianie projektu.
- Konsekwencje: projekt przygotowuje się przez `uv sync`; nie utrzymuje się równoległego `requirements.txt` ani alternatywnych virtualenvów.

## Pojedynczy entrypoint

- Decyzja: aplikacja działa jako pojedynczy proces uruchamiany przez `main.py`.
- Uzasadnienie: obecny zakres jest mały i nie wymaga serwera, API ani osobnej warstwy CLI.
- Konsekwencje: uruchamianie pozostaje proste, ale orkiestracja ma ograniczoną rozszerzalność i część konfiguracji jest wczytywana bez wcześniejszej pełnej walidacji.

## Google Sheets jako źródło prawdy i magazyn stanu

- Decyzja: Google Sheets przechowuje link oraz stan `pending`, `ready`, `sent` albo `failed`, licznik prób, podsumowanie i dane diagnostyczne.
- Uzasadnienie: trwałe przejścia eliminują utratę artykułu po błędzie i pozwalają ponowić SMTP bez kolejnego wywołania OpenAI.
- Konsekwencje: aplikacja automatycznie dodaje kolumny stanu, ale nadal zależy od dostępu konta serwisowego i zakłada jedną aktywną instancję.

## Deterministyczny parser listingu

- Decyzja: linki PPE są wyciągane z HTML za pomocą `BeautifulSoup` i wzorca ścieżki, bez udziału LLM.
- Uzasadnienie: strukturalny kontrakt linku jest jednoznaczny, tańszy i łatwiejszy do testowania niż generowanie odpowiedzi modelu.
- Konsekwencje: zmiana struktury URL PPE może wymagać aktualizacji parsera i testów.

## Trwale przejscia przed kosztownymi efektami

- Decyzja: nowy link jest zapisywany jako `pending`, a kompletne podsumowanie jako `ready` przed SMTP.
- Uzasadnienie: kolejne uruchomienie moze bezpiecznie wznowic etap przetwarzania albo wysylki na podstawie utrwalonego stanu.
- Konsekwencje: bledy sa ponawiane maksymalnie trzy razy na etap; SMTP pozostaje at-least-once i rzadki crash przed zapisem `sent` moze zdublowac wiadomosc.

## Jina jako podstawowa ścieżka treści

- Decyzja: pełna treść artykułu jest pobierana przez `https://r.jina.ai/<link>` i walidowana przed użyciem.
- Uzasadnienie: mirror upraszcza pozyskanie tekstu artykułu, ale sam status HTTP nie gwarantuje wiarygodnej treści.
- Konsekwencje: pipeline odrzuca znane strony błędów i zbyt krótkie odpowiedzi; fallback WordPress/HTML pozostaje dostępny tylko dla `konsolowe.info`.

## OpenAI jako aktywna warstwa LLM

- Decyzja: OpenAI Responses API przez oficjalny SDK `openai`, `gpt-6-luna`, effort `medium`.
- Uzasadnienie zaleznosci: oficjalny SDK obsluguje kontrakt Responses, reasoning, status ukonczenia i klasy bledow bez utrzymywania wlasnego protokolu HTTP. Zastepuje `google-genai`.
- Konsekwencje: wymagany `OPENAI_API_KEY`; model i effort konfigurowane przez `OPENAI_MODEL` / `OPENAI_REASONING_EFFORT`. Timeout 60s, maksymalnie dwa retry, brak czekania dluzej niz 30s na retry. Brak przechowywania odpowiedzi po stronie API (`store=False`).

## Ograniczony przebieg crona

- Decyzja: jeden proces na host (flock), maksymalnie 30 minut, bez resetowania blokady przez kasowanie pliku.
- Uzasadnienie: awaria Gemini pozostawiala kilkanascie procesow spiacych przez wiele dni; heartbeat monitoringu byl wysylany dopiero po zakonczeniu.
- Konsekwencje: kod 75 dla zajetej blokady, 124 dla timeoutu, 1 dla bledu; przerwane rekordy pozostaja w trwalym stanie. Kodow nie maskujemy sztucznym heartbeat.

## Jedno wywołanie LLM na news

- Decyzja: aktywny pipeline nie wykonuje osobnego etapu korekty językowej.
- Uzasadnienie: kompletne podsumowanie OpenAI wystarcza w obecnym zastosowaniu, a drugi etap zwiększał koszt, czas i ryzyko limitów.
- Konsekwencje: aplikacja waliduje kompletność pierwszej odpowiedzi i pomija niepoprawny wynik zamiast go poprawiać drugim wywołaniem.

## Wiadomość multipart przez SMTP

- Decyzja: jeden e-mail zawiera wersję `text/plain` i `text/html`, a wysyłka odbywa się przez SMTP z TLS.
- Uzasadnienie: HTML poprawia prezentację, a fallback tekstowy zachowuje kompatybilność klientów pocztowych bez dodatkowej usługi pośredniczącej.
- Konsekwencje: konfiguracja SMTP i bezpieczne przechowywanie hasła nadawcy są wymagane; HTML pozostaje lekki i bez zależności od zewnętrznych zasobów.

## Brak nowych zależności dla rendererów i fallbacków

- Decyzja: rendering MIME/HTML wykorzystuje bibliotekę standardową, a pobieranie i czyszczenie treści korzysta z istniejących `requests` i `BeautifulSoup`.
- Uzasadnienie: obecny zakres nie wymaga dodatkowych frameworków ani bibliotek szablonów.
- Konsekwencje: każda przyszła zależność wymaga osobnego uzasadnienia w decyzjach technicznych i aktualizacji `pyproject.toml` przez `uv add`.
