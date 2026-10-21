import requests
from smolagents import tool

# Códigos WMO usados por Open-Meteo
WEATHER_CODES = {
    0: "despejado", 1: "mayormente despejado", 2: "parcialmente nublado", 3: "nublado",
    45: "niebla", 48: "niebla con escarcha",
    51: "llovizna ligera", 53: "llovizna", 55: "llovizna intensa",
    61: "lluvia ligera", 63: "lluvia", 65: "lluvia intensa",
    71: "nieve ligera", 73: "nieve", 75: "nieve intensa",
    80: "chubascos ligeros", 81: "chubascos", 82: "chubascos fuertes",
    95: "tormenta", 96: "tormenta con granizo", 99: "tormenta fuerte con granizo",
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
            params={"name": city, "count": 1, "language": "es"},
            timeout=15,
        ).json()
        if not geo.get("results"):
            return f"No se encontró la ciudad '{city}'."
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
        sky = WEATHER_CODES.get(current["weather_code"], "condiciones variables")
        return (
            f"{place['name']} ({place.get('country', '')}): {current['temperature_2m']}°C, {sky}, "
            f"viento {current['wind_speed_10m']} km/h. "
            f"Hoy entre {daily['temperature_2m_min'][0]}°C y {daily['temperature_2m_max'][0]}°C."
        )
    except Exception as e:
        return f"Error obteniendo el tiempo de '{city}': {e}"
