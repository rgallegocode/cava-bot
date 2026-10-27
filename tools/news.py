import os
from datetime import datetime, timedelta

import requests
from smolagents import tool

# Compact results: the agent resends its whole history on every step and free tiers cap tokens per request
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
        return "NEWS_API_KEY is not set. Use the web_search tool to look for news instead."

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    params = {
        "q": query,
        # Matching the article body pulls in off-topic pieces that merely mention "bolsa" or "mercados"
        "searchIn": "title,description",
        "from": yesterday,
        "sortBy": "popularity",
        "language": language,
        "apiKey": api_key,
    }
    try:
        response = requests.get("https://newsapi.org/v2/everything", params=params, timeout=20).json()
    except Exception as e:
        return f"Error fetching news: {e}"

    if response.get("status") != "ok":
        return f"NewsAPI returned an error: {response.get('message', 'unknown')}"

    articles = response.get("articles", [])[:MAX_ARTICLES]
    if not articles:
        return f"No news in the last 24h for '{query}'. Try another query or web_search."

    headlines = [
        f"- {a.get('title', 'Untitled')}: {(a.get('description') or 'No description')[:MAX_DESCRIPTION]} ({a.get('source', {}).get('name', '')})"
        for a in articles
    ]
    return "\n".join(headlines)
