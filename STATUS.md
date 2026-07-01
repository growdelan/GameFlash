# Aktualny stan projektu

## Co działa
- Glowny skrypt pobiera newsy, podsumowuje je i wysyla e-mail.
- Zarzadzanie zaleznosciami zostalo przeniesione na `uv`.
- Model LLM jest konfigurowany przez `GEMINI_MODEL` w `.env`; domyslnym modelem jest `gemini-3.5-flash`.
- Stan przetworzonych linkow jest odczytywany i zapisywany w Google Sheets, domyslnie w arkuszu `gameflash_sheet_ppe`.
- Listing newsow jest pobierany z `https://www.ppe.pl/gry` i parsowany bezposrednio z HTML bez uzycia LLM.
- Parser listingu wyciaga tylko linki newsow PPE w formacie `/news/<id>/<slug>.html`.
- Pelna tresc artykulow jest pobierana przez mirror Jina z fallbackiem przez WordPress REST API lub bezposredni HTML dla `konsolowe.info`.
- Dlugie tresci artykulow sa przycinane przed promptem podsumowania, zeby ograniczyc ryzyko przekroczenia limitu wejscia modelu.
- Klient Gemini ponawia czasowe bledy limitu `RESOURCE_EXHAUSTED` na podstawie `retryDelay`.
- Uciete lub niekompletne podsumowania LLM nie sa przekazywane do wysylki.
- Wiadomosc e-mail jest wysylana jako multipart z fallbackiem `plain text` i stylowana warstwa HTML.
- Pipeline wykonuje jedno wywolanie LLM na poprawnie przetworzony news: samo podsumowanie bez osobnej korekty.
- Testy `unittest` dla Milestone 1.0-1.8 przechodza lokalnie.

## Co jest skończone
- Dodanie dokumentow operacyjnych repo.
- Migracja z `requirements.txt` do `pyproject.toml`.
- Milestone 1.0: integracja z Google Sheets jako baza linkow.
- Milestone 1.1: deterministyczna ekstrakcja linkow z HTML.
- Milestone 1.2: finalny pipeline przetwarzania linkow i obsluga bledow po append.
- Milestone 1.3: stylowany e-mail HTML dla GameFlash z fallbackiem `plain text`.
- Milestone 1.4: migracja domyslnego modelu Groq na `qwen/qwen3.6-27b`, walidacja live Qwen i obsluga reasoning.
- Milestone 1.5: odporne pobieranie tresci artykulow, fallback dla `konsolowe.info` i blokada niekompletnych korekt.
- Milestone 1.6: migracja aktywnego zrodla newsow na PPE i arkusz `gameflash_sheet_ppe`.
- Milestone 1.7: migracja warstwy LLM z Groq/Qwen na Google Gemini.
- Milestone 1.8: usuniecie osobnego etapu korekty podsumowan.
- Bazowy zestaw testow `unittest` dla Google Sheets i deduplikacji.
- Aktualizacja bezposrednich zaleznosci do najnowszych kompatybilnych wersji.

## Co jest w trakcie
- Brak otwartych milestone'ow z aktualnej roadmapy.

## Co jest następne
- Ewentualne kolejne PRD lub dalszy refaktor po obecnej serii zmian.

## Blokery i ryzyka
- Uruchomienie produkcyjne wymaga poprawnie uzupelnionego `.env`.
- Walidacja live Google Sheets zalezy od dostepu konta serwisowego do wskazanego arkusza.
- Dalsze powodzenie pipeline'u zalezy od dostepnosci Google Sheets, strony z listingiem, mirroru Jina, Gemini i SMTP.
- Model `gemini-3.5-flash` wymaga poprawnego `GEMINI_API_KEY`; standardowe testy uzywaja stubow i nie potwierdzaja dostepnosci uslugi live.
- Link dopisany do Google Sheets przed bledem dalszego przetwarzania nie jest automatycznie ponawiany w kolejnym przebiegu.

## Ostatnie aktualizacje
- 2026-03-21: migracja konfiguracji projektu na `uv`.
- 2026-03-22: wdrozenie Milestone 1.0, testy lokalne i walidacja live Google Sheets.
- 2026-03-22: wdrozenie Milestone 1.1, testy lokalne i walidacja live parsera listingu.
- 2026-03-22: wdrozenie Milestone 1.2, testy lokalne i walidacja live finalnego pipeline'u.
- 2026-03-22: model LLM przeniesiony do `LLM_MODEL` w `.env` i odswiezone zaleznosci wykonawcze.
- 2026-03-22: wdrozenie Milestone 1.3, stylowany e-mail HTML, fallback `plain text` i testy lokalne warstwy maili.
- 2026-06-27: wdrozenie Milestone 1.4, domyslny model `qwen/qwen3.6-27b`, walidacja live Qwen, ukrycie reasoning i testy lokalne.
- 2026-06-27: wdrozenie Milestone 1.5, walidacja blednych odpowiedzi Jina, fallback WordPress/HTML, blokada niekompletnych korekt, testy lokalne i walidacja live problematycznego artykulu.
- 2026-06-29: wdrozenie Milestone 1.6, migracja listingu na `https://www.ppe.pl/gry`, arkusz `gameflash_sheet_ppe`, parser linkow PPE i testy lokalne.
- 2026-06-29: poprawki po self-review: limit wejscia artykulu przed LLM, timeout klienta Groq oraz walidacja live wysylki maila dla 3 newsow PPE.
- 2026-07-01: wdrozenie Milestone 1.7, migracja LLM na Gemini `gemini-3.5-flash`, przeniesienie lokalnego `GEMINI_API_KEY`, usuniecie zaleznosci `groq` i testy lokalne.
- 2026-07-01: poprawka po tescie skryptu: retry dla limitow Gemini, wiekszy budzet wyjscia podsumowania i blokada ucietych podsumowan przed wysylka.
- 2026-07-01: usuniecie osobnej korekty LLM; mail jest budowany bezposrednio z kompletnego podsumowania.
