---
name: codex-flow-create-prd
description: Przeprowadź z użytkownikiem wywiad produktowy i utwórz pierwszy albo kolejny plik PRD w katalogu prd, bez implementowania kodu i bez aktualizowania spec.md lub ROADMAP.md. Użyj, gdy użytkownik ma pomysł na aplikację lub funkcjonalność i chce dopracować wymagania przed planowaniem implementacji.
---

# Tworzenie PRD

## Rozpoznanie

1. Przyjmij początkowy opis aplikacji lub funkcjonalności jako punkt wyjścia, nie jako kompletną specyfikację.
2. Sprawdź katalog `prd/`, aby rozpoznać istniejące dokumenty i kolejny numer. Nie czytaj kodu, jeśli nie jest niezbędny do zadania konkretnego pytania o istniejące zachowanie.
3. Ustal, czy powstaje pierwszy PRD projektu, czy przyrostowy PRD nowej funkcjonalności.

## Wywiad

1. Zadawaj dokładnie jedno krótkie pytanie naraz i czekaj na odpowiedź użytkownika.
2. Najpierw ustal problem, odbiorców, oczekiwany rezultat i granice zakresu. Następnie doprecyzuj główne przepływy, wymagania, przypadki brzegowe, dane, integracje, ograniczenia, kryteria akceptacji i ryzyka — tylko gdy dotyczą danego produktu.
3. Nie pytaj ponownie o informacje już podane. Jeśli odpowiedź jest niejednoznaczna, doprecyzuj ją przed przejściem dalej.
4. Nie wymuszaj decyzji technicznych, które lepiej podjąć podczas tworzenia specyfikacji. Zapisz istotne ograniczenia techniczne tylko wtedy, gdy podał je użytkownik lub wynikają z rzeczywistego środowiska.
5. Zakończ wywiad, gdy dokument pozwala jednoznacznie określić cele, zakres, zachowanie i kryteria akceptacji. Nie przedłużaj rozmowy dla opcjonalnych szczegółów.

## Zapis dokumentu

1. Dla pierwszego PRD wypełnij `prd/000-initial-prd.md`.
2. Dla kolejnego PRD utwórz plik z następnym wolnym numerem i krótką nazwą w `kebab-case`, np. `prd/001-import-danych.md`. Nie zmieniaj wcześniejszych PRD.
3. Zapisz co najmniej: kontekst i problem, odbiorców, cele, poza zakresem, przepływy użytkownika, wymagania funkcjonalne, kryteria akceptacji, ograniczenia, ryzyka oraz otwarte pytania.
4. Oddziel fakty ustalone z użytkownikiem od założeń i otwartych pytań. Nie wymyślaj wymagań, aby sztucznie domknąć dokument.
5. Nie implementuj kodu, nie aktualizuj `spec.md`, `ROADMAP.md` ani `STATUS.md` i nie uruchamiaj innych skillów planistycznych w tym samym kroku.

Po zapisaniu podaj ścieżkę PRD, krótkie podsumowanie ustaleń, otwarte pytania oraz wskaż `$codex-flow-plan-from-prd` jako następny opcjonalny krok.
