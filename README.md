# GameFlash

Skrypt do podsumowywania newsow z branzy gier.

## Jak to dziala

Skrypt wykorzystuje [Jina AI](https://jina.ai) do konwersji strony internetowej na czysty Markdown. Nastepnie model Llama 3.3 70B uruchamiany przez [Groq](https://groq.com) wyodrebnia linki do artykulow. W kolejnym kroku aplikacja pobiera tresc kazdego artykulu, generuje podsumowanie po polsku i wysyla wynik e-mailem.

## Wymagania

- `uv`
- konto Groq i klucz API
- konto SMTP do wysylki e-maili

## Konfiguracja

1. Skopiuj `.env.example` do `.env`.
2. Uzupelnij wartosci zmiennych:
   - `GROQ_API_KEY`
   - `SMTP_SERVER`
   - `SENDER_MAIL`
   - `SENDER_PASS`
   - `RECIPIENTS`

## Uruchomienie

Synchronizacja srodowiska:

```bash
uv sync
```

Uruchomienie aplikacji:

```bash
uv run main.py
```

## Testy

Projekt uzywa `unittest`. Standardowa komenda:

```bash
uv run python -m unittest discover -s tests -p "test_*.py"
```

Obecnie repo nie zawiera jeszcze katalogu `tests/`.

## Przykladowy wynik

![Przykladowy wynik](/Users/gohan/IT/DevOps/Programowanie/Python/Projekty/GameFlash/img/01.png)
