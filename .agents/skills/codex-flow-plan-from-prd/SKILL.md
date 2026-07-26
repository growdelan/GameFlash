---
name: codex-flow-plan-from-prd
description: Utwórz lub zaktualizuj spec.md i ROADMAP.md na podstawie pierwszego albo przyrostowego PRD z katalogu prd, bez implementowania kodu. Użyj, gdy użytkownik wskazuje PRD i chce otrzymać spójną specyfikację, mierzalne milestone'y, ryzyka i walidacje.
---

# Planowanie z PRD

1. Ustal wskazany plik PRD. Jeśli użytkownik go nie podał, wybierz go tylko wtedy, gdy w `prd/` istnieje jeden oczywisty kandydat.
2. Uruchom `./scripts/check-context-size.sh`. Przeczytaj PRD, `STATUS.md`, aktywne milestone'y w `ROADMAP.md` oraz indeks i istotne części `spec.md`. Nie czytaj archiwum ani niepowiązanych dokumentów domenowych.
3. Jeśli plik, który trzeba rozszerzyć, przekracza próg, najpierw uporządkuj go zgodnie z `$codex-flow-compact-context`, bez zmiany jego znaczenia.
4. Rozpoznaj, czy PRD inicjuje projekt, czy rozszerza istniejący zakres.
5. Zaktualizuj `spec.md`: cel, zachowanie, architekturę i tylko uzasadnione decyzje techniczne. Nie usuwaj wcześniejszych decyzji bez jawnej podstawy.
6. Zaktualizuj `ROADMAP.md`. Każdy milestone musi mieć cel, mierzalne kryteria akceptacji, zakres, poza zakresem, walidację oraz ryzyka lub zależności.
7. Zaproponuj minimalny pionowy slice tylko wtedy, gdy jest właściwy dla rodzaju projektu i realnie weryfikuje najważniejsze założenie.
8. Nie zgaduj brakujących wymagań. Zapisz konkretne `TODO: [pytanie]` albo poproś użytkownika o decyzję, jeśli wpływa ona na plan.
9. Nie zmieniaj kodu aplikacji.

Podsumuj użyty PRD, zmienione dokumenty, milestone'y, ryzyka, TODO i rekomendowany następny krok.
