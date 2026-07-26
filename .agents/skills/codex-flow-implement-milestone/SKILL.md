---
name: codex-flow-implement-milestone
description: Implementuj jeden konkretny milestone lub jasno ograniczone zadanie z ROADMAP.md. Użyj, gdy użytkownik wskazuje identyfikator albo nazwę milestone'u i oczekuje zmian w kodzie wraz z walidacją, bez automatycznego commita lub pusha.
---

# Implementacja milestone'u

1. Przeczytaj `AGENTS.md`, `STATUS.md`, wskazany fragment `ROADMAP.md` oraz istotne sekcje `spec.md`.
2. Sprawdź pliki kodu i testów związane z zakresem. Nie czytaj niepowiązanych obszarów.
3. Dla większej lub niejasnej zmiany podaj krótko: cel, zakres, poza zakresem, kryteria akceptacji, walidację i warunki zatrzymania.
4. Jeśli użytkownik nie wskazał milestone'u, nie wybieraj samodzielnie spośród kilku sensownych kandydatów. Poproś o decyzję.
5. Zaimplementuj wyłącznie uzgodniony zakres małymi, precyzyjnymi zmianami.
6. Dodaj lub popraw testy odpowiadające ryzyku zmiany.
7. Uruchom komendy walidacyjne z repo, domyślnie `./scripts/verify.sh`.
8. Zaktualizuj `STATUS.md`, jeżeli zmiana jest istotna lub praca pozostaje niedomknięta.

Nie wykonuj commita ani pusha. W wyniku podaj zmienione pliki, walidacje, ograniczenia i ewentualne problemy wymagające review.
