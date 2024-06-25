"""Funkcje dotyczące konfigurajic LLM"""

from groq import Groq


# pylint: disable=line-too-long
def news_prompt(context):
    """Prompt dla wyciągania linków do JSON"""
    prompt = f"""
Act as an expert in text processing and data extraction.

### Task
Your task is to extract all the links from the given text and save them in JSON format. The links should be placed in an array in the format: {{ "links": ["link1", "link2", "link3"] }}. Make sure each link is stored as a separate array element.

### Context
A user has provided text containing links that need to be extracted. The format of the link you are looking to extract looks like the following: https://konsolowe.info/<year>/<month>/<title/. Skip links that look different.

### Response format
The answer must be in dictionary format with the key "links", where the value will be an array containing all the extracted links.

Example of a response: {{ "links": ["https://konsolowe.info/2024/06/promocja-steelbook-w-preorderach-call-of-duty-black-ops-6/", "https://konsolowe.info/2024/06/xdefiant-juz-jutro-z-nowym-trybem/", "https://konsolowe.info/2024/06/charytatywna-akcja-pink-mercy-powroci-w-overwatch-2/"] }}

You must only reply in the format indicated. Do not add anything else!

### Input data
{context}
"""
    return prompt


# pylint: enable=line-too-long


def summary_prompt(context):
    """Prompt do podsumowywania newsów"""
    prompt = f"""
Act as an expert in the field of video games.

Your task is to create a summary of a provided text from the gaming industry in Polish language. The summary should include the most important information, key points and a general overview of the content to ensure a full understanding of the text in up to 300 words.

### Context
The text provided is from the games industry and can cover various aspects such as game reviews, market analysis, interviews with game developers, game updates or industry trends. It is important to capture the main ideas and convey them in a concise and understandable way.

### Response format
The response must ALWAYS be in the following format:

Tytuł: <news title>.
<empty line>.
Podsumowanie: <summary content>.
<empty line>.

The answer must be in Polish!

### Input data
{context}
"""
    return prompt


def proofreading_prompt(context):
    """Prompt do korekty podsumowanych tekstów"""
    prompt = f"""
Act as an expert in proofreading.

### The task
Your task is to carry out professional proofreading of the text provided. Proofreading should include correcting any grammatical, punctuation and stylistic errors. Make sure the text is coherent, clear and flowing. If you find any passages that could be worded better, please improve them. Pay attention to the tone and style of the text, adapting it appropriately for the intended audience.

### Context
The text is intended for publication and should be written in a professional tone. It is important to retain the intention and meaning of the original text, while improving readability and linguistic accuracy.

### Input
{context}

### Response format
1. the response must be in Polish
2. do not start with "Here is the".
3. do not add anything from yourself
4. do not write the changes you have made
5. response format:
Tytuł: <original news title>

Podsumowanie: <text after correction>.

Link: <link to news item>
"""
    return prompt


def groq_client(groq_api_key):
    """Inicjalizacja klienta Groq"""
    client = Groq(
        api_key=groq_api_key,
    )
    return client


def model_options(
    prompt: str,
    temperature: int,
    max_tokens: int,
):
    """Opcje dla Modeli"""
    return dict(
        {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
    )


def run_groq_model(
    groq_api_key: str,
    model: str,
    options: dict,
):
    """Uruchomienie LLM do wskazanych zadan z trybem JSON lub nie"""
    client = groq_client(groq_api_key)
    chat_completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": options["prompt"]},
        ],
        temperature=options.get("temperature", 1),
        max_tokens=options.get("max_tokens", 1500),
        stream=False,
        stop=None,
    )

    model_response = chat_completion.choices[0].message.content
    return model_response
