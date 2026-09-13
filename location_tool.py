"""
Location tracking — IP-based (approximate), not GPS.

Honest limitation: a typical desktop/laptop has no GPS hardware, so this
gives your rough location based on your internet connection (usually
accurate to city level, sometimes off if you're using a VPN).
"""

import requests


def get_location() -> str:
    try:
        resp = requests.get("http://ip-api.com/json/", timeout=10)
        data = resp.json()
        if data.get("status") != "success":
            return "Couldn't determine your location right now."

        city = data.get("city", "unknown")
        region = data.get("regionName", "")
        country = data.get("country", "")
        isp = data.get("isp", "unknown")
        lat = data.get("lat")
        lon = data.get("lon")

        return (f"Approximate location: {city}, {region}, {country} "
                f"(coordinates: {lat}, {lon}). Via: {isp}. "
                f"Note: this is based on your internet connection, not exact GPS.")
    except Exception as e:
        return f"Couldn't fetch location: {e}"