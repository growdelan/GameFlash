---
name: codex-flow-review
description: Wykonaj niezależne, read-only review ostatnich zmian lub wskazanego diffu pod kątem błędów, regresji, bezpieczeństwa, testów, zakresu milestone'u i zgodności z dokumentacją. Użyj po większej lub ryzykownej implementacji albo gdy użytkownik prosi o przegląd kodu.
---

# Niezależne review

1. Ustal bazę porównania i zakres diffu. Sprawdź `git status`, diff, zmienione pliki oraz właściwy milestone.
2. Przeczytaj zmienione pliki w zakresie potrzebnym do oceny zachowania.
3. Oceń poprawność, regresje, bezpieczeństwo, obsługę błędów, prostotę, zbędne abstrakcje i martwy kod.
4. Oceń, czy testy sprawdzają istotne zachowanie i czy wykonane walidacje odpowiadają ryzyku.
5. Sprawdź zgodność z `AGENTS.md`, `spec.md`, `ROADMAP.md`, `STATUS.md` oraz `README.md`, jeśli zmieniło się użycie.
6. Nie modyfikuj żadnych plików.

Najpierw podaj problemy pogrupowane jako krytyczne, ważne i drobne. Dla każdego wskaż plik lub obszar, wpływ, rekomendowaną poprawkę i informację, czy mieści się w bieżącym zakresie. Jeśli nie ma problemów blokujących, napisz: `Review zakończony — brak problemów blokujących.`
