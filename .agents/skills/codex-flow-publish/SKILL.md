---
name: codex-flow-publish
description: Przygotuj zakończoną zmianę do publikacji, aktualizując dokumentację, weryfikując diff i walidację oraz wykonując commit lub push wyłącznie wtedy, gdy użytkownik jawnie o to poprosił. Użyj dla poleceń typu przygotuj zmianę, zrób commit, push albo opublikuj.
---

# Publikacja zmiany

1. Ustal dokładny poziom autoryzacji z polecenia użytkownika: przygotowanie, commit albo push. Nie rozszerzaj go.
2. Sprawdź `git status --short`, pełny diff oraz obecność zmian użytkownika spoza zakresu.
3. Upewnij się, że nie ma nierozwiązanych problemów blokujących i że adekwatna walidacja przeszła. W razie potrzeby uruchom `./scripts/verify.sh`.
4. Zaktualizuj `ROADMAP.md` i `STATUS.md` zgodnie z faktami. Zmień `spec.md` lub `README.md` tylko wtedy, gdy zmieniły się decyzje, zachowanie, uruchamianie albo konfiguracja.
5. Uruchom `./scripts/check-context-size.sh`. Jeśli występują ostrzeżenia, uporządkuj dokumentację zgodnie z `$codex-flow-compact-context` przed stagingiem, chyba że użytkownik jawnie wyłączył kompakcję z zakresu.
6. Jeśli użytkownik poprosił tylko o przygotowanie, zatrzymaj się przed stagingiem i commitem.
7. Jeśli użytkownik poprosił o commit, stage'uj wyłącznie pliki z uzgodnionego zakresu i utwórz logiczny commit.
8. Wykonaj push tylko na jawne polecenie `push`, `opublikuj` lub równoważne i tylko do właściwego remote/brancha.

Nie twórz pustych commitów, nie ukrywaj nieprzechodzącej walidacji i nie włączaj cudzych zmian do publikacji. Podaj zaktualizowane dokumenty, walidacje oraz faktyczny status commita i pusha.
