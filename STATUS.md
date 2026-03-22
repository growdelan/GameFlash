# Aktualny stan projektu

## Co działa
- Glowny skrypt pobiera newsy, podsumowuje je i wysyla e-mail.
- Zarzadzanie zaleznosciami zostalo przeniesione na `uv`.
- Stan przetworzonych linkow jest odczytywany i zapisywany w Google Sheets.
- Testy `unittest` dla Milestone 1.0 przechodza lokalnie.

## Co jest skończone
- Dodanie dokumentow operacyjnych repo.
- Migracja z `requirements.txt` do `pyproject.toml`.
- Milestone 1.0: integracja z Google Sheets jako baza linkow.
- Bazowy zestaw testow `unittest` dla Google Sheets i deduplikacji.

## Co jest w trakcie
- Milestone 1.1: przejscie z ekstrakcji linkow przez LLM na parser HTML.

## Co jest następne
- Milestone 1.2: domkniecie nowego pipeline'u przetwarzania linkow.
- Aktualizacja dokumentacji po przejsciu na pelny przeplyw z PRD 001.

## Blokery i ryzyka
- Uruchomienie produkcyjne wymaga poprawnie uzupelnionego `.env`.
- Dalszy przeplyw nadal korzysta z LLM do ekstrakcji linkow z listingu.
- Walidacja live Google Sheets zalezy od dostepu konta serwisowego do wskazanego arkusza.

## Ostatnie aktualizacje
- 2026-03-21: migracja konfiguracji projektu na `uv`.
- 2026-03-22: wdrozenie Milestone 1.0, testy lokalne i walidacja live Google Sheets.
