# Aktualny stan projektu

## Co działa
- Glowny skrypt pobiera newsy, podsumowuje je i wysyla e-mail.
- Zarzadzanie zaleznosciami zostalo przeniesione na `uv`.
- Stan przetworzonych linkow jest odczytywany i zapisywany w Google Sheets.
- Listing newsow jest parsowany bezposrednio z HTML bez uzycia LLM.
- Testy `unittest` dla Milestone 1.0 i 1.1 przechodza lokalnie.

## Co jest skończone
- Dodanie dokumentow operacyjnych repo.
- Migracja z `requirements.txt` do `pyproject.toml`.
- Milestone 1.0: integracja z Google Sheets jako baza linkow.
- Milestone 1.1: deterministyczna ekstrakcja linkow z HTML.
- Bazowy zestaw testow `unittest` dla Google Sheets i deduplikacji.

## Co jest w trakcie
- Milestone 1.2: domkniecie nowego pipeline'u przetwarzania linkow.

## Co jest następne
- Przejscie pobierania pelnej tresci artykulow na mirror Jina.
- Domkniecie testow i dokumentacji dla finalnego przeplywu z PRD 001.

## Blokery i ryzyka
- Uruchomienie produkcyjne wymaga poprawnie uzupelnionego `.env`.
- Walidacja live Google Sheets zalezy od dostepu konta serwisowego do wskazanego arkusza.
- Pobieranie pelnej tresci artykulow nadal korzysta z `WebBaseLoader`, a nie z docelowego mirroru Jina.

## Ostatnie aktualizacje
- 2026-03-21: migracja konfiguracji projektu na `uv`.
- 2026-03-22: wdrozenie Milestone 1.0, testy lokalne i walidacja live Google Sheets.
- 2026-03-22: wdrozenie Milestone 1.1, testy lokalne i walidacja live parsera listingu.
