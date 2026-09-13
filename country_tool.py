"""
Real, accurate country facts via the REST Countries API — free, no API
key needed. Fixes the hallucination problem where the LLM guesses at
facts like capitals/population instead of knowing them for certain.
"""

import requests


def country_info(country_name: str) -> str:
    try:
        resp = requests.get(
            f"https://restcountries.com/v3.1/name/{country_name}",
            params={"fields": "name,capital,population,region,subregion,languages,currencies,area,borders"},
            timeout=10
        )
        if resp.status_code != 200:
            return f"Couldn't find a country called '{country_name}'."

        data = resp.json()
        if not data:
            return f"Couldn't find a country called '{country_name}'."

        c = data[0]
        name = c.get("name", {}).get("common", country_name)
        capital = ", ".join(c.get("capital", ["unknown"]))
        region = c.get("region", "unknown")
        subregion = c.get("subregion", "")

        population = c.get("population", "unknown")
        population_str = f"{population:,}" if isinstance(population, int) else str(population)

        area = c.get("area", "unknown")
        area_str = f"{area:,} km²" if isinstance(area, (int, float)) else str(area)

        languages = c.get("languages", {})
        lang_str = ", ".join(languages.values()) if languages else "unknown"

        currencies = c.get("currencies", {})
        currency_str = ", ".join(
            f"{v.get('name', k)} ({v.get('symbol', '')})" for k, v in currencies.items()
        ) if currencies else "unknown"

        borders = c.get("borders", [])
        borders_str = f"Borders: {', '.join(borders)}." if borders else "No land borders."

        lines = [
            name,
            f"Capital: {capital}",
            f"Population: {population_str}",
            f"Region: {region}" + (f" ({subregion})" if subregion else ""),
            f"Area: {area_str}",
            f"Languages: {lang_str}",
            f"Currency: {currency_str}",
            borders_str,
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Couldn't fetch country info: {e}"