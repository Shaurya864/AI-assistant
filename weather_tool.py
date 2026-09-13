"""
Real weather data via Open-Meteo — completely free, no API key needed.

Two ways it finds your location:
1. config.WEATHER_LOCATION (a city name you set) — used by default
2. IP-based auto-detection as a fallback if that's not set

You can also just ask "weather in [any city]" to override both.
"""

import requests
import config

WEATHER_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "depositing rime fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
    61: "slight rain", 63: "moderate rain", 65: "heavy rain",
    71: "slight snow", 73: "moderate snow", 75: "heavy snow",
    80: "rain showers", 81: "moderate rain showers", 82: "violent rain showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "thunderstorm with heavy hail",
}


def _geocode(city: str):
    """Turn a city name into coordinates using Open-Meteo's free geocoding API."""
    try:
        resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1}, timeout=10
        )
        resp.raise_for_status()
        results = resp.json().get("results")
        if not results:
            return None
        r = results[0]
        return r["latitude"], r["longitude"], r.get("name", city), r.get("country", "")
    except Exception:
        return None


def _auto_locate():
    """Fallback: rough location from your IP address, no API key needed."""
    try:
        resp = requests.get("http://ip-api.com/json/", timeout=10)
        data = resp.json()
        if data.get("status") == "success":
            return data["lat"], data["lon"], data.get("city", "your area"), data.get("country", "")
    except Exception:
        pass
    return None


def get_weather(city: str = None) -> str:
    """Get real current weather for a named city, your configured city, or auto-detected location."""
    location = None

    if city:
        location = _geocode(city)
        if not location:
            return f"Couldn't find a location called '{city}'."
    else:
        configured_city = getattr(config, "WEATHER_LOCATION", "").strip()
        if configured_city:
            location = _geocode(configured_city)
        if not location:
            location = _auto_locate()
        if not location:
            return "Couldn't determine your location — try 'weather in [city]' instead."

    lat, lon, name, country = location
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current_weather": "true"},
            timeout=10
        )
        resp.raise_for_status()
        current = resp.json()["current_weather"]
        temp = current["temperature"]
        windspeed = current["windspeed"]
        code = current["weathercode"]
        description = WEATHER_CODES.get(code, "unknown conditions")
        return f"Weather in {name}, {country}: {temp}°C, {description}, wind {windspeed} km/h."
    except Exception as e:
        return f"Couldn't fetch weather: {e}"