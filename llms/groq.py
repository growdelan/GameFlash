"""Funkcje dotyczące konfigurajic LLM"""

from groq import Groq


def news_system_prompt():
    """Prompt dla wyciągania linków do JSON"""
    system_prompt = """
    From the given text, extract links into JSON format.

    Example of links:
    - https://konsolowe.info/2024/06/kingdom-come-deliverance-2-30-fps-na-konsolach/
    - https://konsolowe.info/2024/05/astro-bot-juz-wkrotce-powroci-na-ps5/

    Response template:
    { "links": ["link1", "link2", "link3"]}

    the reply must be in the template format, don't say anything else it is very important
    """
    return system_prompt


def summary_system_prompt():
    """Prompt do podsumowywania newsów"""
    system_prompt = """
    The text provided, summarise in Polish language in a maximum of 300 words, extracting the "Title" field in the following format.

    Response template:
    Tytuł: <Title>
    <new line>
    Podsumowanie:<Markdown Content Summary>
    <new line>

    the reply must be in the template format, don't say anything else it is very important
    """
    return system_prompt


def proofreading_system_prompt():
    """Prompt do korekty podsumowanych tekstów"""
    proofreading_prompt = """
    You proofreading the submitted text (the text must remain in Polish!), your task is to improve the grammar and style of the text and make it visually attractive as a summary for the client.

    The reply must be in the corrected text, don't say anything else it is very important.
    """
    return proofreading_prompt


def groq_client(groq_api_key):
    """Inicjalizacja klienta Groq"""
    client = Groq(
        api_key=groq_api_key,
    )
    return client


def model_options(
    system_prompt: str,
    user_text: str,
    temperature: int,
    max_tokens: int,
    json_mode: bool,
):
    """Opcje dla Modeli"""
    return dict(
        {
            "system_prompt": system_prompt,
            "user_text": user_text,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "json_mode": json_mode,
        }
    )


def run_groq_model(
    groq_api_key: str,
    model: str,
    options: dict,
):
    """Uruchomienie LLM do wskazanych zadan z trybem JSON lub nie"""
    client = groq_client(groq_api_key)
    if options["json_mode"]:
        chat_completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": options["system_prompt"]},
                {"role": "user", "content": options["user_text"]},
            ],
            temperature=options.get("temperature", 1),
            max_tokens=options.get("max_tokens", 1024),
            stream=False,
            response_format={"type": "json_object"},
            stop=None,
        )
    else:
        chat_completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": options["system_prompt"]},
                {"role": "user", "content": options["user_text"]},
            ],
            temperature=options.get("temperature", 1),
            max_tokens=options.get("max_tokens", 1024),
            stream=False,
            stop=None,
        )

    model_response = chat_completion.choices[0].message.content
    return model_response
