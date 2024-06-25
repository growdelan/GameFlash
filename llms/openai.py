"""Funkcje dotyczące konfigurajic LLM - OpenAI"""

# pylint: disable=R0801

from openai import OpenAI


def openai_client(openai_api_key):
    """Inicjalizacja klienta openai"""
    client = OpenAI(
        api_key=openai_api_key,
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


def run_openai_model(
    openai_api_key: str,
    model: str,
    options: dict,
):
    """Uruchomienie LLM do wskazanych zadan z trybem JSON lub nie"""
    client = openai_client(openai_api_key)
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
