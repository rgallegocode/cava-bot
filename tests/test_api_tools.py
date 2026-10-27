from conftest import FakeResponse

from tools import news, weather


def test_news_without_api_key_suggests_web_search(monkeypatch):
    monkeypatch.delenv("NEWS_API_KEY", raising=False)

    assert "web_search" in news.get_financial_news(query="bitcoin")


def test_news_formats_and_truncates_articles(monkeypatch):
    monkeypatch.setenv("NEWS_API_KEY", "test")
    articles = [
        {"title": f"Headline {i}", "description": "x" * 500, "source": {"name": "Expansión"}} for i in range(20)
    ]
    captured = {}

    def fake_get(url, params, timeout):
        captured.update(params)
        return FakeResponse({"status": "ok", "articles": articles})

    monkeypatch.setattr(news.requests, "get", fake_get)

    result = news.get_financial_news(query="bitcoin", language="en")
    lines = result.splitlines()

    assert len(lines) == news.MAX_ARTICLES
    assert lines[0].startswith("- Headline 0: ")
    assert "x" * (news.MAX_DESCRIPTION + 1) not in result
    assert "(Expansión)" in lines[0]
    assert captured["q"] == "bitcoin" and captured["language"] == "en"
    assert captured["searchIn"] == "title,description"


def test_news_reports_api_errors(monkeypatch):
    monkeypatch.setenv("NEWS_API_KEY", "test")
    monkeypatch.setattr(
        news.requests, "get", lambda *a, **k: FakeResponse({"status": "error", "message": "apiKeyInvalid"})
    )

    assert "apiKeyInvalid" in news.get_financial_news()


def test_weather_returns_real_conditions(monkeypatch):
    def fake_get(url, params, timeout):
        if "geocoding" in url:
            return FakeResponse({"results": [{"name": "Málaga", "country": "Spain", "latitude": 36.7, "longitude": -4.4}]})
        return FakeResponse(
            {
                "current": {"temperature_2m": 21.3, "weather_code": 0, "wind_speed_10m": 9.5},
                "daily": {"temperature_2m_min": [15.0], "temperature_2m_max": [25.0]},
            }
        )

    monkeypatch.setattr(weather.requests, "get", fake_get)

    result = weather.get_weather(city="Málaga")

    assert result.startswith("Málaga (Spain): 21.3°C, clear sky")
    assert "between 15.0°C and 25.0°C" in result


def test_weather_unknown_city(monkeypatch):
    monkeypatch.setattr(weather.requests, "get", lambda *a, **k: FakeResponse({}))

    assert "not found" in weather.get_weather(city="Atlantis")
