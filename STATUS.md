# Aktualny stan projektu

## Co działa
- Glowny skrypt pobiera newsy, podsumowuje je i wysyla e-mail.
- Zarzadzanie zaleznosciami zostalo przeniesione na `uv`.
- Stan przetworzonych linkow jest odczytywany i zapisywany w Google Sheets.
- Listing newsow jest parsowany bezposrednio z HTML bez uzycia LLM.
- Pelna tresc artykulow jest pobierana przez mirror Jina.
- Testy `unittest` dla Milestone 1.0-1.2 przechodza lokalnie.

## Co jest skończone
- Dodanie dokumentow operacyjnych repo.
- Migracja z `requirements.txt` do `pyproject.toml`.
- Milestone 1.0: integracja z Google Sheets jako baza linkow.
- Milestone 1.1: deterministyczna ekstrakcja linkow z HTML.
- Milestone 1.2: finalny pipeline przetwarzania linkow i obsluga bledow po append.
- Bazowy zestaw testow `unittest` dla Google Sheets i deduplikacji.

## Co jest w trakcie
- Brak otwartych milestone'ow z aktualnej roadmapy.

## Co jest następne
- Ewentualne kolejne PRD lub dalszy refaktor po obecnej serii zmian.

## Blokery i ryzyka
- Uruchomienie produkcyjne wymaga poprawnie uzupelnionego `.env`.
- Walidacja live Google Sheets zalezy od dostepu konta serwisowego do wskazanego arkusza.
- Dalsze powodzenie pipeline'u zalezy od dostepnosci Google Sheets, strony z listingiem, mirroru Jina, Groq i SMTP.

## Ostatnie aktualizacje
- 2026-03-21: migracja konfiguracji projektu na `uv`.
- 2026-03-22: wdrozenie Milestone 1.0, testy lokalne i walidacja live Google Sheets.
- 2026-03-22: wdrozenie Milestone 1.1, testy lokalne i walidacja live parsera listingu.
- 2026-03-22: wdrozenie Milestone 1.2, testy lokalne i walidacja live finalnego pipeline'u.
