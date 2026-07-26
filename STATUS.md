# Aktualny stan projektu

## Co działa
- Glowny skrypt pobiera newsy PPE, podsumowuje je przez Gemini i wysyla jeden e-mail multipart.
- Google Sheets jest trwalym magazynem linkow, stanow przetwarzania, licznikow prob, podsumowan i bledow.
- Przy starcie aplikacja automatycznie dodaje brakujace kolumny `Status`, `Attempts`, `Summary`, `LastError`, `DiscoveredAt` i `UpdatedAt`.
- Historyczne wiersze bez statusu sa traktowane jak `sent` i nie sa wysylane ponownie.
- Nowe rekordy przechodza przez `pending`, `ready` oraz `sent` albo terminalne `failed`.
- Bledy pobierania, Gemini i SMTP sa ponawiane maksymalnie trzy razy na etap w kolejnych uruchomieniach.
- Gotowe podsumowanie jest utrwalane przed SMTP, wiec retry wysylki nie wywoluje ponownie Jina ani Gemini.
- Operator moze reaktywowac `failed`, zmieniajac status na `pending` albo `ready`.
- Listing PPE jest parsowany deterministycznie bez uzycia LLM.
- Tresc artykulu jest pobierana przez Jina, z historycznym fallbackiem WordPress/HTML dla `konsolowe.info`.
- Gemini ponawia czasowe bledy `RESOURCE_EXHAUSTED`, a niekompletne odpowiedzi nie trafiaja do e-maila.
- Testy jednostkowe dla Milestone 1.0-1.9 przechodza lokalnie.

## Co jest skończone
- Dokumenty operacyjne repo i zarzadzanie zaleznosciami przez `uv`.
- Milestone 1.0-1.8: Google Sheets, deterministyczny parser, pipeline PPE, e-mail HTML, odporne pobieranie tresci i migracja na Gemini z jednym wywolaniem LLM.
- Milestone 1.9: trwaly stan przetwarzania i retry pelnego pipeline'u.
- PRD 006, aktualizacja roadmapy, specyfikacji, decyzji technicznych i README dla nowego kontraktu stanu.
- Testy migracji schematu, limitu prob, retry SMTP, recznej reaktywacji i niepoprawnych statusow.

## Co jest w trakcie
- Brak otwartych milestone'ow z aktualnej roadmapy.

## Co jest następne
- Ewentualne kolejne PRD; naturalnym kandydatem jest obsluga wielu konfigurowalnych zrodel newsow.

## Blokery i ryzyka
- Uruchomienie produkcyjne wymaga poprawnie uzupelnionego `.env` i dostepu konta serwisowego do arkusza.
- Pipeline zalezy od dostepnosci PPE, Google Sheets, Jina, Gemini i SMTP.
- Standardowe testy korzystaja ze stubow i nie potwierdzaja dostepnosci uslug live.
- Arkusz zaklada jedna aktywna instancje GameFlash; brak blokady dla rownoleglych procesow.
- SMTP ma semantyke at-least-once: crash po przyjeciu wiadomosci, ale przed zapisem `sent`, moze spowodowac duplikat.
- Rekord `failed` wymaga recznej zmiany statusu, jesli ma zostac ponowiony.

## Ostatnia istotna walidacja
- 2026-07-26: `uv run main.py` live po usunieciu dwoch ostatnich wierszy — aplikacja wykryla 3 linki PPE, zapisala kompletne podsumowania Gemini, wyslala e-mail i ustawila wszystkie rekordy na `sent` z `Attempts=0` oraz pustym `LastError`.
- 2026-07-26: `./scripts/verify.sh` — 46 testow przeszlo, 1 opcjonalny test live pominiety; dokumenty kontekstowe pozostaja w limitach.
- 2026-07-26: `git diff --check` — brak bledow bialych znakow.

## Handoff
- Dokumentacja i kod opisuja stan po Milestone 1.9.
- Zmiana nie zostala zacommitowana ani wypchnieta.
