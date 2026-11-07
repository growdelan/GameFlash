# Migracja GameFlash do OpenAI — plan i odbior

Data: 2026-11-07. Wydanie docelowe: v1.14.0. Branch: codex/openai-luna-migration.

## Rozpoznanie i zakres

Raspberry dzialalo na 7cbb166, podczas gdy main lokalny zawieral juz obsluge pending/ready/sent/failed (wydanie v1.13.0). Migracja wdraza takze te zalegle zmiany. Zastajemy 17 procesow Gemini, najstarszy od 3 listopada, i wielogodzinne retry bez limitu. Cron pozostaje co trzy godziny, heartbeat Gatus co cztery godziny.

## Kolejnosc i kryteria odbioru

1. Nowy branch z aktualnego main; zachowanie formatu maila i parsera PPE.
2. Klient Responses API: gpt-6-luna, effort medium; bez klucza w kodzie, Git, argumentach polecen lub logach. Zaleznosc openai zamiast google-genai; uv.lock obowiazkowy.
3. Ograniczone retry, walidacja kompletnej odpowiedzi, lokalny flock i deadline 30 minut; niezerowe kody bledow dla monitoringu.
4. Testy offline, opt-in live API bez efektow zewnetrznych i niezalezny review.
5. Kandydat w osobnym katalogu na Pi. `uv sync --frozen`; komplet testow. Sprawdzenie prawdziwego PPE/Jina, OpenAI, odczytu Sheets, renderowania MIME oraz uwierzytelnienia SMTP bez wysylania wiadomosci.
6. Przed przelaczeniem: prywatny backup plikow, konfiguracji crona i arkusza (poza repo, katalog 0700, pliki 0600). Krotka przerwa w cronie GameFlash. Zakonczenie tylko starych procesow tego projektu, bez restartow pozostalych uslug.
7. Wdrozenie identycznego kandydata w ~/LLM/GameFlash; nowy .env z zachowaniem konfiguracji Sheets/SMTP i usunieciem zmiennych Gemini. Start przez dotychczasowy wrapper monitoringu; weryfikacja heartbeat bez wymuszania sukcesu. Przy nowych artykulach reczny smoke nie wysyla maili: normalna dostawa pozostaje zadaniem crona.
8. Commit/push po udanej walidacji, PR do main, przeglad komentarzy i checkow, merge. Pi i lokalne repo aktualizowane do main. Tag/release v1.14.0 na scalonym commicie, usuniecie brancha roboczego.

## Migracja danych i granice

Kolumny stanu sa dopisywane bez nadpisywania Links. Historyczny brak statusu znaczy sent. Nie odtwarzamy automatycznie starych niedostarczonych artykulow: dawna ewidencja nie rozroznia ich od dostarczonych. Przerwanie starych procesow moze odrzucic podsumowania trzymane tylko w ich pamieci; nie przywracamy ich przez masowa ponowna wysylke.

Nowe rekordy przechodza pending → ready → sent. Blad ma do trzech prob na etap, pozniej failed. Retry SMTP korzysta z utrwalonego Summary. Dostawa pozostaje at-least-once (crash po SMTP przed sent moze zdublowac wiadomosc). Blokada jest lokalna; nie uruchamiac produkcji na dwoch hostach.

## Rollback

Zatrzymac tylko wpis crona GameFlash i upewnic sie, ze nie trwa jego proces. Przywrocic pliki i .env z prywatnego backupu oraz poprzedni commit. Przywrocic crontab. Nie usuwac kolumn stanu ani nie przywracac calego arkusza po wysylkach bez porownania zmian — grozi utrata nowych rekordow i duplikatami. Stary klient Gemini zachowuje pierwotny problem limitow, dlatego rollback nie jest naprawa dostawcy.

## Walidacja

- Lokalnie: 55 testow, jeden live domyslnie pominiety; osobny live OpenAI zakonczony sukcesem.
- Raspberry kandydat: testy offline przeszly; smoke potwierdzil odczyt 4319 rekordow, prawdziwy PPE/Jina + kompletne podsumowanie OpenAI, MIME i TLS/login SMTP. Bez wysylki i bez zapisu w Sheets.
- Niezalezny review: brak ustalen blokujacych.
- Produkcja: 55 testow OK (1 opt-in live pominiety), pelny smoke integracji OK. Zakonczono 17 starych procesow, przywrocono oryginalny crontab.
- Rzeczywisty przebieg main przez run-monitored zakonczony sukcesem 2026-11-07 o 06:25 Europe/Warsaw (10s); brak nowych/pending/ready, nie wysylano maili. Gatus przyjal success=true. Reczna walidacja miala blokade wysylki SMTP.
- Backup: prywatny katalog ~/.local/state/gameflash/rollback-20261107-openai (kod, konfiguracja, crontab, arkusz); nie jest publikowany.
- Ostateczny niezalezny review po uzupelnieniu smoke i testu batch: brak ustalen blokujacych.
