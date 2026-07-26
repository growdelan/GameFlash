---
name: codex-flow-run-roadmap
description: Wykonaj w kontrolowanej pętli wszystkie wykonalne milestone'y ze statusem planned z ROADMAP.md. Użyj, gdy użytkownik jawnie prosi o realizację całej roadmapy, wszystkich zaplanowanych milestone'ów albo autonomiczną pracę aż do ukończenia planu lub napotkania blokera.
---

# Wykonanie roadmapy

## Przygotowanie

1. Uruchom `./scripts/check-context-size.sh`. Przeczytaj `AGENTS.md`, `STATUS.md`, aktywne milestone'y w `ROADMAP.md` oraz istotne sekcje lub odnośniki z `spec.md`; nie czytaj archiwum domyślnie.
2. Sprawdź stan repo i nie włączaj do pracy niepowiązanych zmian użytkownika.
3. Zbierz rzeczywiste milestone'y `planned` w kolejności zależności. Pomiń wpisy szablonowe i elementy zablokowane.
4. Przed implementacją pokaż krótki plan kolejności. Nie czekaj na dodatkowe potwierdzenie, jeśli polecenie użytkownika jest jednoznaczne i nie ma konfliktu zakresu.
5. Używaj subagentów tylko do niezależnego planowania, eksploracji lub read-only review, gdy poprawia to jakość albo izoluje szum. Implementację i aktualizacje wspólnych plików prowadź sekwencyjnie.

## Pętla milestone'ów

Dla każdego kolejnego milestone'u:

1. Potwierdź cel, zakres, poza zakresem, kryteria akceptacji, walidację i warunki zatrzymania.
2. Oznacz milestone jako `in_progress` i zaktualizuj krótki stan w `STATUS.md`.
3. Zaimplementuj wyłącznie jego zakres zgodnie z `$codex-flow-implement-milestone`.
4. Uruchom walidację zmienionego obszaru oraz `./scripts/verify.sh`, jeśli jest adekwatny.
5. Wykonaj niezależne read-only review zgodnie z `$codex-flow-review`; preferuj subagenta `reviewer`, jeśli jest dostępny.
6. Jeśli review wykryje problemy mieszczące się w zakresie, popraw je zgodnie z `$codex-flow-address-review`, ponów walidację i sprawdź rozwiązanie problemów blokujących.
7. Oznacz milestone jako `done` dopiero po spełnieniu kryteriów akceptacji, pozytywnej walidacji i usunięciu problemów blokujących.
8. Zaktualizuj `STATUS.md` i przejdź do następnego `planned` bez ponownego pytania użytkownika.
9. Uruchom `./scripts/check-context-size.sh`. Jeśli pojawi się ostrzeżenie, użyj `$codex-flow-compact-context` przed rozpoczęciem kolejnego milestone'u.

## Warunki zatrzymania

Zatrzymaj pętlę i zachowaj bezpieczny stan, gdy:

- wymaganie jest niejednoznaczne i decyzja istotnie zmienia produkt lub zakres,
- walidacja nie przechodzi, a naprawa wymaga pracy poza bieżącym milestone'em,
- review wykryje nierozwiązany problem blokujący,
- zależność lub sekret uniemożliwia dalszą pracę,
- working tree zawiera nieoczekiwane zmiany, których nie można bezpiecznie odseparować,
- użytkownik przerwie albo zmieni zadanie.

W takim przypadku oznacz właściwy milestone jako `blocked` tylko wtedy, gdy blokada jest rzeczywista, opisz ją w `STATUS.md` i podaj konkretną decyzję lub działanie potrzebne do wznowienia.

## Zakończenie

Po wyczerpaniu milestone'ów `planned` uporządkuj przekroczone pliki kontekstu, uruchom pełną dostępną walidację, sprawdź spójność `ROADMAP.md`, `STATUS.md`, `spec.md` i `README.md`, a następnie podsumuj ukończone milestone'y, testy, review i pozostałe ryzyka.

Nie wykonuj commita ani pusha bez osobnego, jawnego polecenia użytkownika.
