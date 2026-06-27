"""Funkcje dotyczące konfigurajic LLM"""

import re

from groq import Groq

QWEN_REASONING_MODEL = "qwen/qwen3.6-27b"
QWEN_MIN_MAX_TOKENS = 4096
THINK_BLOCK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL | re.IGNORECASE)
OPEN_THINK_BLOCK_RE = re.compile(r"<think>.*\Z", re.DOTALL | re.IGNORECASE)


def news_prompt(year: str, month: str, context: str) -> str:
    """Prompt dla wyciągania linków do JSON"""
    prompt = f"""
extract all the links with the following scheme from the given text :

https://konsolowe.info/{year}/{month}/

response format:
 {{ "links": [ "link1", "link2" ] }}

Reply only as in the above schema, do not add anything else, this is very important

Input data:
{context}
"""
    return prompt


def summary_prompt(context: str) -> str:
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


def proofreading_prompt(context: str) -> str:
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


def sanitize_model_response(response: str) -> str:
    """Usuwa techniczne bloki reasoning z odpowiedzi modelu."""
    without_complete_blocks = THINK_BLOCK_RE.sub("", response)
    return OPEN_THINK_BLOCK_RE.sub("", without_complete_blocks).strip()


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
    sanitize_response: bool = True,
):
    """Uruchomienie LLM do wskazanych zadan z trybem JSON lub nie"""
    client = groq_client(groq_api_key)
    request_options = {
        "model": model,
        "messages": [
            {"role": "user", "content": options["prompt"]},
        ],
        "temperature": options.get("temperature", 1),
        "max_tokens": options.get("max_tokens", 1500),
        "stream": False,
        "stop": None,
    }
    if model == QWEN_REASONING_MODEL:
        request_options["reasoning_format"] = "hidden"
        request_options["max_tokens"] = max(
            request_options["max_tokens"], QWEN_MIN_MAX_TOKENS
        )

    chat_completion = client.chat.completions.create(**request_options)

    model_response = chat_completion.choices[0].message.content or ""
    if sanitize_response:
        model_response = sanitize_model_response(model_response)
    if not model_response.strip():
        raise RuntimeError("Model zwrocil pusta odpowiedz.")
    return model_response
