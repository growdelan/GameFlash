# 001. Aktualna architektura GameFlash

- Status: obowiązuje
- Data konsolidacji: 2026-07-26
- Zakres: stan po Milestone 1.8

Dokument konsoliduje wyłącznie aktualne decyzje. Wcześniejsze warianty pozostają w historii Git i PRD.

## Zarządzanie środowiskiem przez `uv`

- Decyzja: środowisko i zależności są zarządzane przez `uv` oraz `pyproject.toml`.
- Uzasadnienie: jedno źródło prawdy upraszcza instalację, lockowanie i uruchamianie projektu.
- Konsekwencje: projekt przygotowuje się przez `uv sync`; nie utrzymuje się równoległego `requirements.txt` ani alternatywnych virtualenvów.

## Pojedynczy entrypoint

- Decyzja: aplikacja działa jako pojedynczy proces uruchamiany przez `main.py`.
- Uzasadnienie: obecny zakres jest mały i nie wymaga serwera, API ani osobnej warstwy CLI.
- Konsekwencje: uruchamianie pozostaje proste, ale orkiestracja ma ograniczoną rozszerzalność i część konfiguracji jest wczytywana bez wcześniejszej pełnej walidacji.

## Google Sheets jako źródło prawdy

- Decyzja: kolumna `Links` w Google Sheets jest źródłem prawdy dla zarejestrowanych artykułów.
- Uzasadnienie: stan może być współdzielony między uruchomieniami bez utrzymywania lokalnej bazy danych.
- Konsekwencje: wykonanie zależy od dostępu konta serwisowego; lokalny plik JSON nie uczestniczy w aktywnym przepływie.

## Deterministyczny parser listingu

- Decyzja: linki PPE są wyciągane z HTML za pomocą `BeautifulSoup` i wzorca ścieżki, bez udziału LLM.
- Uzasadnienie: strukturalny kontrakt linku jest jednoznaczny, tańszy i łatwiejszy do testowania niż generowanie odpowiedzi modelu.
- Konsekwencje: zmiana struktury URL PPE może wymagać aktualizacji parsera i testów.

## Zapis linku przed dalszym przetwarzaniem

- Decyzja: nowy link jest dopisywany do Google Sheets przed pobraniem artykułu i wywołaniem Gemini.
- Uzasadnienie: zapobiega to równoległemu lub kolejnemu podjęciu tego samego linku po udanym append.
- Konsekwencje: błąd pobrania treści, LLM lub SMTP po zapisie nie powoduje automatycznego retry w następnym przebiegu.

## Jina jako podstawowa ścieżka treści

- Decyzja: pełna treść artykułu jest pobierana przez `https://r.jina.ai/<link>` i walidowana przed użyciem.
- Uzasadnienie: mirror upraszcza pozyskanie tekstu artykułu, ale sam status HTTP nie gwarantuje wiarygodnej treści.
- Konsekwencje: pipeline odrzuca znane strony błędów i zbyt krótkie odpowiedzi; fallback WordPress/HTML pozostaje dostępny tylko dla `konsolowe.info`.

## Gemini jako aktywna warstwa LLM

- Decyzja: podsumowania generuje Google Gemini przez `google-genai`; domyślny model to `gemini-3.5-flash`, nadpisywalny przez `GEMINI_MODEL`.
- Uzasadnienie: oficjalny SDK zapewnia bezpośredni klient, konfigurację timeoutu i spójny kontrakt generowania.
- Konsekwencje: `GEMINI_API_KEY` jest wymaganym sekretem, a dostępność generowania zależy od Gemini Developer API.

## Jedno wywołanie LLM na news

- Decyzja: aktywny pipeline nie wykonuje osobnego etapu korekty językowej.
- Uzasadnienie: kompletne podsumowanie Gemini wystarcza w obecnym zastosowaniu, a drugi etap zwiększał koszt, czas i ryzyko limitów.
- Konsekwencje: aplikacja waliduje kompletność pierwszej odpowiedzi i pomija niepoprawny wynik zamiast go poprawiać drugim wywołaniem.

## Wiadomość multipart przez SMTP

- Decyzja: jeden e-mail zawiera wersję `text/plain` i `text/html`, a wysyłka odbywa się przez SMTP z TLS.
- Uzasadnienie: HTML poprawia prezentację, a fallback tekstowy zachowuje kompatybilność klientów pocztowych bez dodatkowej usługi pośredniczącej.
- Konsekwencje: konfiguracja SMTP i bezpieczne przechowywanie hasła nadawcy są wymagane; HTML pozostaje lekki i bez zależności od zewnętrznych zasobów.

## Brak nowych zależności dla rendererów i fallbacków

- Decyzja: rendering MIME/HTML wykorzystuje bibliotekę standardową, a pobieranie i czyszczenie treści korzysta z istniejących `requests` i `BeautifulSoup`.
- Uzasadnienie: obecny zakres nie wymaga dodatkowych frameworków ani bibliotek szablonów.
- Konsekwencje: każda przyszła zależność wymaga osobnego uzasadnienia w decyzjach technicznych i aktualizacji `pyproject.toml` przez `uv add`.
