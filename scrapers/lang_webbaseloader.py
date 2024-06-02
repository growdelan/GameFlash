"""Scrapowanie za pomocą Langchain WebBaseLoader w celu podsumowania"""

from langchain_community.document_loaders import WebBaseLoader


def webbaseloader(url: str) -> str:
    """Scrapowanie za pomocą WebBaseLoadera z paklietu langchain community"""
    loader = WebBaseLoader(url, encoding="UTF-8")
    data = loader.load()
    return data[0].page_content
