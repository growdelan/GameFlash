"""Prompty dla modeli"""


# pylint: disable=line-too-long
def news_prompt(context):
    """Prompt dla wyciągania linków do JSON"""
    prompt = f"""
Działaj jako ekspert w przetwarzaniu tekstu i ekstrakcji danych.

### Zadanie
Twoim zadaniem jest wyekstrahowanie wszystkich linków z podanego tekstu i zapisanie ich w formacie JSON. Linki należy umieścić w tablicy w formacie: {{ "links": ["link1", "link2", "link3"] }}. Upewnij się, że każdy link jest zapisany jako osobny element tablicy.

### Kontekst
Użytkownik podał tekst zawierający linki, które trzeba wyekstrahować. Format linku który szukasz do ekstrakcji wygląda następująco: https://konsolowe.info/<rok>/<miesiąc>/<tytuł/. Linki wyglądające inaczej pomiń.

### Format odpowiedzi
Odpowiedź musi być w formacie słownika z kluczem "links", gdzie wartością będzie tablica zawierająca wszystkie wyekstrahowane linki.

Przykład odpowiedzi: {{ "links": ["https://konsolowe.info/2024/06/promocja-steelbook-w-preorderach-call-of-duty-black-ops-6/", "https://konsolowe.info/2024/06/xdefiant-juz-jutro-z-nowym-trybem/", "https://konsolowe.info/2024/06/charytatywna-akcja-pink-mercy-powroci-w-overwatch-2/"] }}

Musisz odpowiedzieć tylko we wskazanym formacie. Nie dodawaj nic więcej!

### Dane wejściowe
{context}
"""
    return prompt


# pylint: enable=line-too-long


def summary_prompt(context):
    """Prompt do podsumowywania newsów"""
    prompt = f"""
Działaj jako ekspert w dziedzinie gier wideo.

Twoim zadaniem jest stworzenie podsumowania dostarczonego tekstu z branży gier w języku polskim. Podsumowanie powinno zawierać najważniejsze informacje, kluczowe punkty oraz ogólny przegląd treści, aby zapewnić pełne zrozumienie tekstu w maksymalnie 300 słowach.

### Kontekst
Podany tekst pochodzi z branży gier i może obejmować różne aspekty, takie jak recenzje gier, analizy rynkowe, wywiady z twórcami gier, aktualizacje dotyczące gier czy trendy w branży. Ważne jest, aby uchwycić główne idee i przekazać je w zwięzły i zrozumiały sposób.

### Format odpowiedzi
Odpowiedź ZAWSZE musi być w następującym formacie:

Tytuł: <tutuł newsa>
<pusta linia>
Podsumowanie: <podsumowana treść>
<pusta linia>

### Dane wejściowe
{context}
"""
    return prompt


def proofreading_prompt(context):
    """Prompt do korekty podsumowanych tekstów"""
    prompt = f"""
Działaj jako ekspert w korekcie tekstów.

### Zadanie
Twoim zadaniem jest przeprowadzenie profesjonalnej korekty dostarczonego tekstu. Korekta powinna obejmować poprawienie wszelkich błędów gramatycznych, interpunkcyjnych i stylistycznych. Upewnij się, że tekst jest spójny, jasny i płynny. Jeśli znajdziesz jakiekolwiek fragmenty, które mogą zostać sformułowane lepiej, proszę o ich poprawę. Zwróć uwagę na ton i styl tekstu, dostosowując go odpowiednio do zamierzonej publiczności.

### Kontekst
Tekst jest przeznaczony do publikacji i powinien być napisany w profesjonalnym tonie. Ważne jest, aby zachować intencję i znaczenie oryginalnego tekstu, jednocześnie poprawiając jego czytelność i poprawność językową.

### Dane wejściowe
{context}

### Format odpowiedzi
Odpowiedz musi być w języku polskim i gotowa do publikacji. ZAWSZE używaj poniższego formatu:

Tytuł: <oryginalny tytuł newsa>
<pusta linia>
Podsumowanie: <tekst po korekcie>
<pusta linia>
Link: <link do newsa>

Nie dodwaj nic więcej, TO BARDZO WAŻNE!!!
"""
    return prompt
