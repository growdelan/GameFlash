"""Funkcje dotyczace konfiguracji Gemini."""

import re
import time

from google import genai
from google.genai import errors
from google.genai import types

GEMINI_REQUEST_TIMEOUT_MS = 60000
GEMINI_MAX_RETRIES = 4
GEMINI_RETRY_DELAY_SECONDS = 25
THINK_BLOCK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL | re.IGNORECASE)
OPEN_THINK_BLOCK_RE = re.compile(r"<think>.*\Z", re.DOTALL | re.IGNORECASE)
RETRY_DELAY_RE = re.compile(r"retryDelay['\"]?:\s*['\"]?(\d+(?:\.\d+)?)s", re.IGNORECASE)


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

Your task is to create a summary of a provided text from the gaming industry in Polish language. The summary should include the most important information, key points and a general overview of the content to ensure a full understanding of the text in 3-4 complete sentences and up to 90 words.

### Context
The text provided is from the games industry and can cover various aspects such as game reviews, market analysis, interviews with game developers, game updates or industry trends. It is important to capture the main ideas and convey them in a concise and understandable way.

### Response format
The response must ALWAYS be in the following format:

Tytuł: <news title>.
<empty line>.
Podsumowanie: <summary content>.
<empty line>.

The answer must be in Polish!
The summary must end with a complete sentence. Do not stop mid-word or mid-sentence.

### Input data
{context}
"""
    return prompt


def sanitize_model_response(response: str) -> str:
    """Usuwa techniczne bloki reasoning z odpowiedzi modelu."""
    without_complete_blocks = THINK_BLOCK_RE.sub("", response)
    return OPEN_THINK_BLOCK_RE.sub("", without_complete_blocks).strip()


def gemini_client(gemini_api_key):
    """Inicjalizacja klienta Gemini."""
    return genai.Client(
        api_key=gemini_api_key,
        http_options=types.HttpOptions(timeout=GEMINI_REQUEST_TIMEOUT_MS),
    )


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


def is_gemini_rate_limit_error(error: Exception) -> bool:
    """Sprawdza, czy blad Gemini wynika z limitu zapytan."""
    message = str(error).lower()
    return (
        isinstance(error, errors.ClientError)
        and "resource_exhausted" in message
        or "quota exceeded" in message
        or "retrydelay" in message
    )


def retry_delay_seconds(error: Exception) -> float:
    """Wyciaga sugerowany czas retry z bledu Gemini albo zwraca wartosc domyslna."""
    match = RETRY_DELAY_RE.search(str(error))
    if not match:
        return GEMINI_RETRY_DELAY_SECONDS
    return max(float(match.group(1)) + 1.0, 1.0)


def _generate_content_with_retry(client, request_options: dict):
    """Wykonuje generate_content z retry dla czasowego limitu Gemini."""
    for attempt in range(GEMINI_MAX_RETRIES + 1):
        try:
            return client.models.generate_content(**request_options)
        except Exception as exc:
            if not is_gemini_rate_limit_error(exc) or attempt >= GEMINI_MAX_RETRIES:
                raise
            delay = retry_delay_seconds(exc)
            print(
                f"Gemini przekroczylo limit zapytan, ponawiam za {delay:.0f}s "
                f"(proba {attempt + 1}/{GEMINI_MAX_RETRIES})."
            )
            time.sleep(delay)


def run_gemini_model(
    gemini_api_key: str,
    model: str,
    options: dict,
    sanitize_response: bool = True,
):
    """Uruchamia Gemini dla wskazanego promptu."""
    client = gemini_client(gemini_api_key)
    request_options = {
        "model": model,
        "contents": [types.Content(parts=[types.Part(text=options["prompt"])])],
        "config": types.GenerateContentConfig(
            temperature=options.get("temperature", 1),
            max_output_tokens=options.get("max_tokens", 1500),
        ),
    }
    response = _generate_content_with_retry(client, request_options)

    model_response = response.text or ""
    if sanitize_response:
        model_response = sanitize_model_response(model_response)
    if not model_response.strip():
        raise RuntimeError("Model zwrocil pusta odpowiedz.")
    return model_response
