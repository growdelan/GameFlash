# PRD 004: Odporne pobieranie treści artykułów i blokada podsumowań z błędnych źródeł

## Cel zmiany

Celem tej zmiany jest zabezpieczenie GameFlash przed generowaniem podsumowań na podstawie błędnych danych wejściowych, gdy mirror Jina zwraca technicznie poprawną odpowiedź `HTTP 200`, ale treścią odpowiedzi jest komunikat błędu źródłowej strony, na przykład `403 Forbidden`.

Po wdrożeniu GameFlash ma:
- rozpoznawać odpowiedzi Jina, które nie zawierają realnej treści artykułu,
- używać alternatywnej ścieżki pobierania treści dla artykułów z `konsolowe.info`,
- pomijać link, jeśli nie uda się pobrać wiarygodnej treści artykułu,
- nie wywoływać LLM dla stron błędów, pustych treści ani samych metadanych,
- nie wysyłać e-maili z podsumowaniami opartymi na zgadywaniu modelu.

## Problem do rozwiązania

Obecna implementacja pobiera pełną treść artykułu przez `https://r.jina.ai/<link>`. W zaobserwowanym przypadku Jina zwróciła status `HTTP 200`, ale zawartość odpowiedzi informowała, że źródłowa strona zwróciła `403 Forbidden`.

Przykładowe fragmenty błędnej odpowiedzi:
- `Title: 403 Forbidden`,
- `Warning: Target URL returned error 403: Forbidden`,
- `Markdown Content: * * * nginx`.

To podejście jest ryzykowne, ponieważ:
- aplikacja traktuje taką odpowiedź jak poprawną treść artykułu,
- LLM może wygenerować pozornie sensowne podsumowanie na podstawie tytułu i trendów rynkowych,
- w e-mailu może znaleźć się tekst zawierający domysły, a nie streszczenie faktycznego artykułu,
- etap korekty może dodatkowo skrócić lub zniekształcić niepoprawnie wygenerowane podsumowanie.

## Zakres funkcjonalny

Zmiana obejmuje:
- walidację treści zwróconej przez Jina przed przekazaniem jej do promptu podsumowania,
- wykrywanie odpowiedzi błędnych mimo statusu `HTTP 200`,
- fallback pobierania treści artykułu z `konsolowe.info`,
- blokadę wywołania LLM, jeśli nie uda się pobrać realnej treści artykułu,
- walidację kompletności wyniku po korekcie językowej,
- testy jednostkowe pokrywające błędne odpowiedzi Jina, fallback oraz brak wywołania LLM dla niepoprawnych danych wejściowych.

Minimalnie rozpoznawane błędne odpowiedzi Jina:
- treść zawiera `Title: 403 Forbidden`,
- treść zawiera `Warning: Target URL returned error 403`,
- treść jest pusta,
- treść jest skrajnie krótka i nie zawiera realnego artykułu.

## Poza zakresem

Ta zmiana nie obejmuje:
- zmiany integracji z Google Sheets,
- zmiany modelu `qwen/qwen3.6-27b`,
- zmiany liczby planowych wywołań LLM dla poprawnie przetworzonego newsa,
- zmiany renderowania e-maila HTML,
- zmiany fallbacku `plain text`,
- zmiany logiki deduplikacji linków,
- dodania retry workflow, kolejki zadań lub monitoringu,
- dodania panelu użytkownika,
- obsługi wielu źródeł newsów innych niż obecny przepływ dla `konsolowe.info`.

## Docelowy przepływ

Docelowy przebieg pobierania i przetwarzania treści artykułu:

1. Aplikacja wykrywa nowy link i zapisuje go do Google Sheets zgodnie z obecnym przepływem.
2. Aplikacja próbuje pobrać treść artykułu przez Jina.
3. Aplikacja waliduje treść zwróconą przez Jina.
4. Jeśli treść z Jina jest poprawna, zostaje przekazana do etapu podsumowania.
5. Jeśli treść z Jina wygląda jak błąd źródła, aplikacja uruchamia fallback dla `konsolowe.info`.
6. Preferowany fallback pobiera treść przez WordPress REST API `wp-json/wp/v2/posts/<id>`, jeśli ID posta da się ustalić z HTML lub nagłówka `Link`.
7. Alternatywny fallback pobiera bezpośrednio HTML artykułu i oczyszcza główną treść.
8. Jeśli fallback zwróci realną treść artykułu, dopiero wtedy aplikacja wywołuje LLM.
9. Jeśli Jina i fallback nie dostarczą realnej treści, aplikacja pomija dany link w bieżącym przebiegu.
10. Wynik korekty jest walidowany przed dodaniem do listy newsów do wysyłki.
11. Niekompletny wynik korekty nie trafia do e-maila.

## Wymagania techniczne

### 1. Walidacja odpowiedzi Jina

Decyzja:
- odpowiedź Jina musi zostać sprawdzona pod kątem treści błędu przed użyciem jej jako wejścia dla LLM.

Uzasadnienie:
- status `HTTP 200` z Jina nie gwarantuje, że pobranie źródłowego artykułu się udało.

Konsekwencje:
- moduł pobierania treści musi odróżniać realny artykuł od komunikatu błędu,
- wykryty błąd powinien uruchomić fallback zamiast generowania podsumowania.

### 2. Fallback przez WordPress REST API

Decyzja:
- dla linków z `konsolowe.info` preferowanym fallbackiem jest publiczne WordPress REST API.

Uzasadnienie:
- artykuły z `konsolowe.info` są publikowane w WordPressie,
- endpoint `wp-json/wp/v2/posts/<id>` może zwrócić pełną treść posta nawet wtedy, gdy Jina dostaje `403 Forbidden`.

Konsekwencje:
- implementacja musi umieć ustalić ID posta, jeśli jest dostępne w HTML lub nagłówku `Link`,
- treść HTML z pola `content.rendered` musi zostać oczyszczona z tagów i elementów technicznych przed przekazaniem do LLM.

### 3. Fallback przez bezpośredni HTML

Decyzja:
- jeśli WordPress REST API nie może zostać użyte, aplikacja może spróbować pobrać artykuł bezpośrednio i oczyścić treść HTML.

Uzasadnienie:
- bezpośrednie pobranie strony może działać poprawnie, nawet jeśli Jina jest blokowana przez źródło.

Konsekwencje:
- parser HTML powinien wyciągać właściwą treść artykułu, a nie menu, stopkę, reklamy, komentarze ani listę powiązanych wpisów,
- jeśli nie da się jednoznacznie uzyskać treści artykułu, link powinien zostać pominięty.

### 4. Blokada LLM dla niepoprawnej treści

Decyzja:
- LLM nie może być wywołany, jeśli wejściem miałaby być strona błędu, pusta treść, sam tytuł lub same metadane SEO.

Uzasadnienie:
- model może wygenerować wiarygodnie brzmiące, ale niezweryfikowane podsumowanie.

Konsekwencje:
- etap `summarize_news` powinien pomijać link, dla którego nie udało się pobrać realnej treści,
- w logach powinien pojawić się czytelny komunikat o pominięciu linku.

### 5. Walidacja kompletności korekty

Decyzja:
- wynik po korekcie językowej musi zostać zweryfikowany przed wysyłką.

Minimalne wymagania dla poprawnego wyniku:
- zawiera `Tytuł:`,
- zawiera `Podsumowanie:`,
- zawiera `Link:`,
- podsumowanie nie jest puste,
- tekst nie wygląda na ucięty w połowie zdania.

Uzasadnienie:
- model może zakończyć odpowiedź przedwcześnie albo pominąć część wymaganego formatu.

Konsekwencje:
- niekompletny wynik korekty nie powinien trafić do maila HTML ani fallbacku `plain text`,
- link może nadal być zachowywany przez istniejący mechanizm dopisywania `Link:`, ale samo zachowanie linku nie wystarcza do uznania wyniku za poprawny.

## Scenariusze akceptacyjne

1. Jina zwraca błąd `403` jako treść odpowiedzi
- jeśli Jina zwraca `HTTP 200`, ale treść zawiera `Title: 403 Forbidden`, wynik jest traktowany jako błąd pobrania artykułu.

2. Jina zwraca ostrzeżenie o błędzie źródła
- jeśli treść zawiera `Warning: Target URL returned error 403`, aplikacja nie przekazuje tej treści do LLM.

3. Fallback WordPress REST API
- jeśli Jina zwraca błędną treść, a WordPress REST API zwraca pełną treść posta, aplikacja używa oczyszczonej treści z API do podsumowania.

4. Fallback bezpośredniego HTML
- jeśli WordPress REST API nie jest dostępne, aplikacja może użyć bezpośredniego HTML artykułu, o ile parser potrafi uzyskać realną treść.

5. Brak realnej treści
- jeśli Jina i fallback nie dostarczą realnej treści, link jest pomijany w bieżącym przebiegu.

6. Brak wywołania LLM dla błędu
- strona błędu `403 Forbidden` nie trafia do promptu podsumowania.

7. Brak zgadywania z tytułu
- jeśli dostępny jest tylko tytuł lub metadane SEO bez treści artykułu, aplikacja nie generuje podsumowania.

8. Niekompletna korekta
- jeśli wynik korekty jest ucięty lub nie zawiera wymaganych pól, nie trafia do e-maila.

9. Brak regresji poprawnego przepływu
- jeśli Jina zwraca realną treść artykułu, aplikacja zachowuje dotychczasowy przepływ: podsumowanie, korekta, wysyłka multipart.

## Testy i scenariusze walidacyjne

Implementacja wynikająca z tego PRD ma zostać pokryta testami `unittest` bez realnego IO.

Testy powinny weryfikować co najmniej:
- Jina zwraca `HTTP 200` z treścią `403 Forbidden` i wynik jest uznany za błąd źródła,
- Jina zwraca ostrzeżenie `Warning: Target URL returned error 403` i treść nie trafia do LLM,
- po błędzie Jina uruchamia się fallback WordPress REST API,
- fallback WordPress REST API zwraca oczyszczoną treść artykułu,
- gdy Jina i fallback zawodzą, link jest pomijany bez wywołania LLM,
- treść błędu `403` nigdy nie trafia do promptu podsumowania,
- pusta lub skrajnie krótka treść jest odrzucana,
- niekompletna odpowiedź korekty nie trafia do maila,
- poprawny artykuł nadal przechodzi przez istniejący przepływ podsumowania i korekty,
- testy nie wykonują realnego SMTP,
- testy nie zapisują danych do Google Sheets,
- testy nie zależą od dostępności `konsolowe.info`, Jina ani Groq.

Standardowa komenda testów pozostaje:

```bash
uv run python -m unittest discover -s tests -p "test_*.py"
```

## Założenia

- Jina pozostaje pierwszą próbą pobrania treści artykułu.
- Jina nie jest traktowana jako w pełni zaufane źródło, ponieważ może zwrócić stronę błędu jako treść odpowiedzi `HTTP 200`.
- Dla `konsolowe.info` WordPress REST API jest akceptowalnym fallbackiem, jeśli publicznie zwraca treść posta.
- Jeśli nie da się pobrać realnego artykułu, lepiej pominąć newsa niż wysłać halucynowane podsumowanie.
- Link zapisany wcześniej w Google Sheets nie jest automatycznie usuwany w ramach tej zmiany.
- Obecna architektura skryptowa pozostaje właściwa i nie wymaga przebudowy.
- PRD opisuje przyszłą poprawkę implementacyjną, ale samo dodanie dokumentu nie zmienia działania aplikacji.
