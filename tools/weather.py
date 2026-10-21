import requests
from smolagents import tool

# WMO weather codes used by Open-Meteo
WEATHER_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "freezing fog",
    51: "light drizzle", 53: "drizzle", 55: "dense drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow",
    80: "light showers", 81: "showers", 82: "violent showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "severe thunderstorm with hail",
}


@tool
def get_weather(city: str = "Málaga") -> str:
    """Gets the current real weather (temperature, sky, wind) and today's min/max for a city using the Open-Meteo API.
    Args:
        city: City name, e.g. 'Málaga', 'Madrid', 'New York'. Defaults to 'Málaga'.
    """
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en"},
            timeout=15,
        ).json()
        if not geo.get("results"):
            return f"City '{city}' not found."
        place = geo["results"][0]

        forecast = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min",
                "timezone": "auto",
                "forecast_days": 1,
            },
            timeout=15,
        ).json()
        current = forecast["current"]
        daily = forecast["daily"]
        sky = WEATHER_CODES.get(current["weather_code"], "variable conditions")
        return (
            f"{place['name']} ({place.get('country', '')}): {current['temperature_2m']}°C, {sky}, "
            f"wind {current['wind_speed_10m']} km/h. "
            f"Today between {daily['temperature_2m_min'][0]}°C and {daily['temperature_2m_max'][0]}°C."
        )
    except Exception as e:
        return f"Error fetching the weather for '{city}': {e}"
