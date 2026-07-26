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

## Ostatnia istotna walidacja
- 2026-07-26: `./scripts/check-context-size.sh` — wszystkie glowne dokumenty w zalecanych limitach po kompakcji `spec.md`.
- 2026-07-26: `./scripts/verify.sh` — 36 testow przeszlo, 1 opcjonalny test live pominiety.

## Handoff
- Dokumentacja opisuje aktualny stan po Milestone 1.8; szczegoly pipeline'u i decyzje techniczne sa linkowane z `spec.md`.
- Brak aktywnego milestone'u i zmian w zachowaniu aplikacji.
