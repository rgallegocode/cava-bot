import os
from datetime import datetime, timedelta

import requests
from smolagents import tool

# Resultados compactos: el historial del agente se reenvía en cada paso y los planes gratuitos limitan los tokens
MAX_ARTICLES = 8
MAX_DESCRIPTION = 160


@tool
def get_financial_news(query: str = "economy OR stock market OR geopolitics", language: str = "es") -> str:
    """Gets the most popular news headlines of the last 24 hours from NewsAPI for a given topic. Returns title and a short description of up to 8 articles. Call it once per topic: the result is already sorted by popularity.
    Args:
        query: Search keywords, supports OR/AND, e.g. 'bitcoin', 'Fed OR inflation', 'economy OR stock market OR geopolitics'.
        language: Two-letter language code of the articles, e.g. 'es' or 'en'. Defaults to 'es'.
    """
    api_key = os.environ.get("NEWS_API_KEY")
    if not api_key:
        return "NEWS_API_KEY no configurada. Usa la herramienta web_search para buscar noticias."

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    params = {
        "q": query,
        "from": yesterday,
        "sortBy": "popularity",
        "language": language,
        "apiKey": api_key,
    }
    try:
        response = requests.get("https://newsapi.org/v2/everything", params=params, timeout=20).json()
    except Exception as e:
        return f"Error obteniendo noticias: {e}"

    if response.get("status") != "ok":
        return f"NewsAPI devolvió un error: {response.get('message', 'desconocido')}"

    articles = response.get("articles", [])[:MAX_ARTICLES]
    if not articles:
        return f"No hay noticias de las últimas 24h para '{query}'. Prueba otra búsqueda o web_search."

    headlines = [
        f"- {a.get('title', 'Sin título')}: {(a.get('description') or 'Sin descripción')[:MAX_DESCRIPTION]} ({a.get('source', {}).get('name', '')})"
        for a in articles
    ]
    return "\n".join(headlines)
