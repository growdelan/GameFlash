# PRD 006: Trwaly stan przetwarzania i retry

## Cel zmiany

GameFlash ma automatycznie ponawiac artykuly utracone po bledzie pobierania, Gemini albo SMTP. Google Sheets pozostaje zrodlem prawdy, ale oprocz linku przechowuje etap przetwarzania, liczbe prob, gotowe podsumowanie i informacje diagnostyczne.

## Problem

Dotychczas link byl dopisywany do arkusza przed pobraniem tresci. Blad wystepujacy pozniej pozostawial go jako zarejestrowany, dlatego kolejne uruchomienie pomijalo artykul. Blad SMTP powodowal dodatkowo utrate gotowego podsumowania i wymagalby ponownego wywolania Gemini.

## Zakres funkcjonalny

- automatyczne dodanie kolumn `Status`, `Attempts`, `Summary`, `LastError`, `DiscoveredAt` i `UpdatedAt`,
- stany `pending`, `ready`, `sent` i `failed`,
- maksymalnie trzy proby na etap w kolejnych uruchomieniach,
- utrwalenie podsumowania przed wysylka,
- ponowienie SMTP bez Jina i Gemini,
- reczna reaktywacja rekordu przez zmiane `failed` na `pending` albo `ready`,
- zachowanie historycznych wierszy bez statusu jako juz wyslanych.

## Docelowy przeplyw

1. Aplikacja otwiera arkusz i dopisuje brakujace naglowki stanu.
2. Istniejace linki z pustym statusem sa interpretowane jako `sent`.
3. Nowe linki sa dopisywane jako `pending` z licznikiem zero.
4. Rekordy `pending` przechodza przez pobranie tresci i Gemini.
5. Blad zwieksza licznik; trzecia porazka ustawia `failed`.
6. Kompletne podsumowanie jest zapisywane jako `Summary`, a rekord przechodzi do `ready`.
7. Wszystkie rekordy `ready` sa wysylane w jednym e-mailu.
8. Sukces SMTP ustawia `sent`; blad pozostawia podsumowanie i zwieksza licznik etapu wysylki.

## Kontrakt arkusza

- `Links` pozostaje wymagana kolumna i identyfikatorem artykulu.
- Brakujace kolumny stanu sa dodawane na koncu naglowka bez nadpisywania innych danych.
- `Attempts` liczy kolejne porazki aktualnego etapu i jest zerowane po przejsciu do `ready`.
- `Summary` pozostaje zapisane rowniez po wysylce.
- `DiscoveredAt` i `UpdatedAt` uzywaja ISO 8601 w UTC.
- Nieznany niepusty status jest logowany i pomijany.

## Obsluga bledow

- Bledy pojedynczego artykulu nie blokuja pozostalych rekordow.
- Rekord nie trafia do SMTP, dopoki kompletne podsumowanie nie zostanie utrwalone jako `ready`.
- Blad SMTP jest zapisany dla wszystkich rekordow objetych wiadomoscia, a nastepnie ponownie zglaszany procesowi.
- Awaria po przyjeciu e-maila przez SMTP, lecz przed zapisem `sent`, moze spowodowac duplikat w kolejnym przebiegu.
- Reczna zmiana terminalnego rekordu na `pending` lub `ready` zeruje wyczerpany licznik przy nastepnym podjeciu.

## Poza zakresem

- rownolegle instancje i blokady rekordow,
- kolejki zadan i czasowy backoff,
- gwarancja exactly-once dla SMTP,
- panel administracyjny i automatyczna reaktywacja `failed`,
- nowe zaleznosci oraz zmiany zrodla newsow, promptu lub wygladu e-maila.

## Kryteria akceptacji

- arkusz zawierajacy tylko `Links` jest rozszerzany bez ponownej wysylki starych wierszy,
- pierwszy i drugi blad pozostawiaja etap do retry, a trzeci ustawia `failed`,
- udane przetworzenie zapisuje kompletne `Summary` i ustawia `ready`,
- blad SMTP nie powoduje ponownego wywolania Jina ani Gemini,
- udana wysylka ustawia wszystkie objete rekordy na `sent`,
- reczna reaktywacja `failed` dziala dla etapow przetwarzania i wysylki,
- testy jednostkowe nie korzystaja z prawdziwych sekretow ani uslug zewnetrznych,
- `./scripts/verify.sh` przechodzi.

## Założenia

- Arkusz jest obslugiwany przez jedna instancje GameFlash naraz.
- Retry odbywa sie przy kolejnych uruchomieniach, bez dodatkowego harmonogramu w aplikacji.
- Dostarczanie e-maili ma semantyke at-least-once.
