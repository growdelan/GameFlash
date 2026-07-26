# AGENTS.md

## Język

- Komunikuj się z użytkownikiem wyłącznie po polsku.
- Dodawaj komentarze w kodzie tylko wtedy, gdy wyjaśniają nieoczywistą logikę.

## Kontekst projektu

- Trwałe decyzje produktowe i techniczne zapisuj w `spec.md`.
- Plan i statusy prac utrzymuj w `ROADMAP.md`.
- Bieżący stan, ostatnią walidację, blokery i następny krok zapisuj w `STATUS.md`.
- Czytaj tylko pliki potrzebne do aktualnej decyzji. Przy kontynuacji zacznij od `STATUS.md` i właściwego fragmentu `ROADMAP.md`.
- Traktuj limity kontekstu jako progi ostrzegawcze: `STATUS.md` 150 linii / 12 KB, `ROADMAP.md` 350 linii / 30 KB, `spec.md` 500 linii / 40 KB.
- Gdy dokument przekracza próg, użyj `$codex-flow-compact-context` przed dalszym rozbudowywaniem go.
- Nie czytaj `docs/archive/` podczas zwykłego resume, planowania ani implementacji, chyba że bieżąca decyzja wymaga historii.
- Ukończone szczegóły roadmapy archiwizuj w `docs/archive/roadmap/`; szczegóły aktualnej specyfikacji dziel między `docs/spec/` i `docs/decisions/`, zachowując `spec.md` jako indeks aktualnej prawdy.

## Środowisko Python

- Używaj `uv` do środowiska i zależności. Dodawaj zależności przez `uv add <pakiet>`.
- Nie twórz alternatywnych virtualenvów ani zależności „na zapas”.
- Uzasadniaj nowe zależności w `spec.md` w sekcji `## Decyzje techniczne`.
- Kod aplikacji trzymaj w `src/`, a testy w `tests/`.
- Preferuj jeden główny entrypoint opisany w `README.md`.

## Implementacja

- Ustal zakres i kryteria akceptacji przed większą lub niejasną zmianą.
- Wprowadzaj małe, precyzyjne zmiany bez szerokich refaktorów „przy okazji”.
- Nie rozszerzaj zakresu milestone'u bez uzasadnienia i aktualizacji planu.
- Nie przechowuj sekretów w repo. Używaj zmiennych środowiskowych i dokumentuj je w `README.md`.
- Stosuj 4 spacje, `snake_case` dla modułów i funkcji oraz `PascalCase` dla klas.

## Walidacja i review

- Używaj komend zdefiniowanych przez repo. Podstawowa komenda tego szablonu to `./scripts/verify.sh`.
- Testy i smoke testy nie mogą wymagać prawdziwych sekretów ani niestabilnych usług zewnętrznych.
- Po istotnej zmianie zapisz w `STATUS.md` wykonaną walidację i jej wynik.
- Nie używaj `STATUS.md` jako dziennika. Zachowuj bieżący stan, ostatnią istotną walidację, aktywne ryzyka i następny krok.
- Dla ryzykownych lub większych zmian wykonaj niezależne review diffu przed publikacją.
- Nie ukrywaj nieprzechodzącej walidacji ani problemów blokujących.

## Git i dokumentacja

- Nie wykonuj commita ani pusha bez jawnego polecenia użytkownika.
- Przed publikacją sprawdź `git status --short`, diff i wynik walidacji.
- Aktualizuj `README.md` tylko wtedy, gdy zmienia się uruchamianie, konfiguracja, użycie lub ważne zachowanie systemu.
- Nie nadpisuj zmian użytkownika ani nie włączaj do commita zmian spoza uzgodnionego zakresu.
