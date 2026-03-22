# PRD 002: Stylowany e-mail HTML dla GameFlash

## Cel zmiany

Celem tej zmiany jest zastąpienie obecnej wiadomości `plain text` estetycznym e-mailem HTML, który lepiej prezentuje podsumowania newsów gamingowych i buduje bardziej dopracowany charakter produktu GameFlash.

Po wdrożeniu GameFlash ma:
- wysyłać zbiorcze podsumowanie newsów w formacie HTML,
- zachować kompatybilny fallback `plain text`,
- prezentować każdy news jako osobną, czytelną sekcję,
- stosować nowoczesną stylistykę dopasowaną do tematu newsów o grach,
- pozostać prostym skryptem bez przebudowy całej architektury aplikacji.

Inspiracją implementacyjną jest sposób budowy maila HTML w projekcie `DramaChecker`, ale bez kopiowania jego layoutu i kolorystyki 1:1.

## Problem do rozwiązania

Obecna implementacja:
- wysyła wiadomość wyłącznie jako `plain text`,
- skleja podsumowania w jeden blok tekstu,
- nie eksponuje wyraźnie tytułów, streszczeń i linków,
- nie buduje wizualnej tożsamości produktu.

To podejście jest niepożądane, ponieważ:
- czytelność przy większej liczbie newsów jest ograniczona,
- wiadomość wygląda technicznie i surowo,
- trudniej szybko przeskanować treść i przejść do interesującego artykułu,
- forma wiadomości odstaje od jakości, jakiej oczekuje się od nowoczesnego newslettera o grach.

## Zakres funkcjonalny

Zmiana obejmuje:
- generowanie wiadomości HTML z osadzonym CSS zgodnym z klientami pocztowymi,
- zachowanie fallbacku `plain text` w wiadomości multipart,
- prezentowanie każdego newsa jako osobnej karty lub sekcji,
- dodanie nagłówka z brandingiem `GameFlash`,
- dodanie krótkiego opisu charakteru wiadomości w sekcji hero,
- wyeksponowanie w każdej karcie co najmniej:
  - tytułu,
  - streszczenia,
  - linku do pełnego artykułu,
- dodanie przycisku albo wyraźnego linku CTA do pełnego artykułu,
- dodanie stopki z krótką informacją systemową,
- przygotowanie stylu, który pozostaje czytelny zarówno na desktopie, jak i na urządzeniach mobilnych.

## Poza zakresem

Ta zmiana nie obejmuje:
- zmiany logiki pobierania newsów,
- zmiany logiki działania Groq,
- zmiany integracji z Google Sheets,
- zmiany pobierania treści przez Jina,
- zmiany deduplikacji linków,
- zmiany schedulerów, retry ani monitoringu,
- pełnego redesignu architektury aplikacji,
- dodawania panelu administracyjnego lub systemu szablonów,
- osadzania obrazów jako wymogu pierwszej wersji,
- personalizacji wiadomości per odbiorca.

## Docelowy wygląd i doświadczenie odbiorcy

Docelowy kierunek wizualny:
- nowoczesny gaming,
- nowoczesny, wyrazisty, ale czytelny,
- bliżej newslettera technologiczno-growego niż formalnego raportu systemowego.

Założenia stylistyczne:
- tło w ciemnych tonach: grafit, granat lub niemal czarne odcienie,
- akcenty kolorystyczne inspirowane estetyką gamingową, np. neonowy cyan, elektryczny niebieski, limonka lub magenta jako akcent,
- wyraźny kontrast pomiędzy tłem, kartami i CTA,
- uniknięcie stylu cukierkowego, pastelowego i korporacyjnie neutralnego,
- zachowanie wysokiej czytelności tekstu mimo bardziej charakterystycznej oprawy.

Wiadomość ma sprawiać wrażenie:
- nowoczesnej,
- dopracowanej,
- lekkiej wizualnie,
- łatwej do szybkiego przeskanowania.

## Docelowa struktura wiadomości

Wiadomość HTML ma mieć następującą strukturę:

1. Sekcja hero / header
- nazwa `GameFlash`,
- krótki opis, że jest to zestawienie najnowszych newsów gamingowych,
- wizualnie najmocniejsza sekcja wiadomości.

2. Lista kart newsów
- każdy news prezentowany jako osobna karta lub wyraźnie wydzielony blok,
- karta zawiera tytuł, streszczenie i link do pełnego artykułu,
- CTA powinno być łatwe do kliknięcia także na mobile.

3. Opcjonalny pusty stan
- jeśli w przyszłości scenariusz wysyłki wiadomości bez newsów zostanie wsparty, wiadomość powinna mieć przewidziany estetyczny pusty stan,
- ta zmiana ma przygotować taki kierunek w PRD, ale bez wymogu wdrażania dodatkowej logiki biznesowej w tej samej iteracji.

4. Stopka
- krótka informacja systemowa o pochodzeniu wiadomości,
- zachowanie prostoty i małej ilości tekstu.

## Wymagania techniczne

Wymagania dla implementacji wynikającej z tego PRD:
- wiadomość ma być wysyłana jako multipart zawierający `text/plain` oraz `text/html`,
- HTML ma używać prostego, osadzonego CSS kompatybilnego z typowymi klientami pocztowymi,
- styl nie może zależeć od zewnętrznych fontów, CDN ani zdalnych plików CSS,
- pierwsza wersja nie wymaga zewnętrznych obrazów, bannerów ani assetów hostowanych poza wiadomością,
- układ ma być odporny na podstawowe ograniczenia klientów pocztowych,
- treść `plain text` ma nadal zawierać komplet informacji potrzebnych odbiorcy.

## Ważne interfejsy i wpływ na implementację

Docelowo ta zmiana ma prowadzić do modyfikacji interfejsu wysyłki z:
- pojedynczego `plain text` body

na:
- wiadomość multipart zawierającą `text/plain` oraz `text/html`.

Zmiana ma również wymagać wydzielenia lekkiego renderowania HTML wiadomości, ale bez narzucania nowej architektury aplikacji poza minimum potrzebnym do:
- zbudowania szablonu HTML,
- podstawienia danych newsów do sekcji wiadomości,
- przygotowania spójnego fallbacku tekstowego.

## Decyzje produktowe i techniczne

### 1. Referencja implementacyjna z `DramaChecker`

Decyzja:
- projekt `DramaChecker` stanowi wzorzec użycia HTML maila i osadzonego CSS, ale nie ma być kopiowany wizualnie 1:1.

Uzasadnienie:
- w repo istnieje już sprawdzony sposób budowy i wysyłki stylowanego maila,
- pozwala to ograniczyć ryzyko nietrafionej lub zbyt ciężkiej implementacji.

Konsekwencje:
- GameFlash zachowuje własną tożsamość wizualną,
- implementacja może przejąć podejście techniczne bez kopiowania estetyki produktu referencyjnego.

### 2. HTML jako warstwa prezentacji, nie zmiana logiki biznesowej

Decyzja:
- ta zmiana dotyczy wyłącznie warstwy prezentacji wiadomości i sposobu jej renderowania.

Uzasadnienie:
- celem jest poprawa jakości odbioru maila, a nie przebudowa pipeline'u przetwarzania newsów.

Konsekwencje:
- pobieranie, deduplikacja, podsumowanie i wysyłka do wielu odbiorców pozostają funkcjonalnie bez zmian,
- zakres implementacji pozostaje ograniczony i bezpieczny.

### 3. Fallback `plain text` pozostaje wymagany

Decyzja:
- nawet po wdrożeniu HTML wiadomość musi zawierać fallback `plain text`.

Uzasadnienie:
- poprawia to kompatybilność z klientami pocztowymi i scenariuszami ograniczonego renderowania HTML.

Konsekwencje:
- implementacja nie może ograniczyć się wyłącznie do `text/html`,
- testy muszą sprawdzać obecność obu wariantów wiadomości.

### 4. Lekki renderer zgodny ze skryptowym charakterem projektu

Decyzja:
- renderer maila ma pozostać prosty i lekki, adekwatny do obecnego, skryptowego charakteru GameFlash.

Uzasadnienie:
- projekt nie wymaga pełnego silnika templatingu ani rozbudowanego systemu widoków dla pojedynczego maila.

Konsekwencje:
- implementacja powinna preferować prosty szablon HTML i minimalną złożoność,
- ewentualne wydzielenie funkcji renderujących ma służyć czytelności, a nie zmianie architektury.

## Scenariusze akceptacyjne

1. Co najmniej jeden news
- jeśli dostępny jest co najmniej jeden news, wiadomość HTML renderuje czytelne karty z tytułem, streszczeniem i linkiem do artykułu.

2. Wiele newsów
- jeśli wiadomość zawiera wiele newsów, układ pozostaje czytelny i łatwy do skanowania na desktopie i mobile.

3. Fallback tekstowy
- jeśli klient pocztowy nie renderuje HTML, odbiorca nadal otrzymuje komplet informacji w wersji `plain text`.

4. Link CTA
- każdy news zawiera wyraźny link lub przycisk prowadzący do pełnego artykułu.

5. Brak regresji SMTP
- zmiana formatu wiadomości nie powoduje regresji w wysyłce do wielu odbiorców.

6. Brak zależności zewnętrznych
- wiadomość HTML nie wymaga zewnętrznych obrazów, hostowanych stylów ani fontów, aby zachować podstawową jakość prezentacji.

## Testy i scenariusze walidacyjne

Implementacja wynikająca z tego PRD ma zostać pokryta testami, które weryfikują co najmniej:
- render pojedynczego newsa do HTML,
- render wielu newsów do HTML,
- poprawne dołączenie fallbacku `plain text`,
- obecność kluczowych elementów wiadomości: nagłówek, karta newsa, CTA i stopka,
- brak zależności od realnego SMTP w testach,
- zachowanie kompatybilności z dotychczasowym przebiegiem wysyłki.

## Założenia

- nowy mail dotyczy wyłącznie warstwy prezentacji wiadomości,
- dane wejściowe pozostają oparte o już wygenerowane podsumowania i linki,
- pierwsza wersja nie wymaga personalizacji per odbiorca,
- pierwsza wersja nie wymaga osadzonych grafik,
- nowy styl ma być nowoczesny i gamingowy, ale nadal czytelny w konserwatywnych klientach pocztowych.
