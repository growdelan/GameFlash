---
name: codex-flow-address-review
description: Wdróż wyłącznie zaakceptowane poprawki wynikające z wcześniejszego review i ponownie zweryfikuj zmieniony zakres. Użyj, gdy istnieje konkretna lista problemów z review, ale nie należy dodawać nowych funkcji ani wykonywać szerokiego refaktoru.
---

# Poprawki po review

1. Przeczytaj wynik review i aktualny diff.
2. Dla każdego problemu potwierdź, że poprawka mieści się w bieżącym zakresie. Problemy wymagające nowej funkcji lub decyzji architektonicznej odłóż i wyraźnie zgłoś.
3. Wprowadź minimalne poprawki kodu, testów lub dokumentacji potrzebne do rozwiązania zaakceptowanych problemów.
4. Uruchom walidację zmienionego zakresu, a następnie pełne `./scripts/verify.sh`, jeśli zmiana może wpływać szerzej.
5. Nie wykonuj commita ani pusha.

Podsumuj naprawione problemy, odłożone elementy, zmienione pliki i wyniki walidacji.
