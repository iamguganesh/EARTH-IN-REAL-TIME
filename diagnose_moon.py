"""
Run this on YOUR machine to see exactly what values your environment
produces, step by step, for Chennai's moonrise calculation.

Usage:
    python diagnose_moon.py YOUR_OPENWEATHER_API_KEY
"""
import sys
from datetime import datetime, timedelta, timezone

import ephem
import requests

if len(sys.argv) < 2:
    print("Usage: python diagnose_moon.py YOUR_OPENWEATHER_API_KEY")
    sys.exit(1)

api_key = sys.argv[1]

print("=" * 60)
print("STEP 1: What time does YOUR machine think it is (UTC)?")
print("=" * 60)
now_utc = datetime.now(timezone.utc)
print("datetime.now(timezone.utc):", now_utc)
print()

print("=" * 60)
print("STEP 2: Real OpenWeatherMap response for Chennai")
print("=" * 60)
resp = requests.get(
    "https://api.openweathermap.org/data/2.5/weather",
    params={"q": "Chennai", "appid": api_key, "units": "metric"},
    timeout=20,
)
print("HTTP status:", resp.status_code)
data = resp.json()
print("Full 'coord':", data.get("coord"))
print("Full 'timezone' field:", data.get("timezone"))
print()

tz_offset = data.get("timezone", 0)
coord = data.get("coord", {})
lat, lon = coord.get("lat"), coord.get("lon")

print("=" * 60)
print("STEP 3: ephem version and moon calculation")
print("=" * 60)
print("ephem version:", ephem.__version__)
print(f"Using lat={lat}, lon={lon}, tz_offset={tz_offset} seconds")
print()

observer = ephem.Observer()
observer.lat = str(lat)
observer.lon = str(lon)
observer.date = now_utc

moon = ephem.Moon()

rise_raw = observer.next_rising(moon)
rise_dt_utc = rise_raw.datetime().replace(tzinfo=timezone.utc)
rise_local = rise_dt_utc + timedelta(seconds=tz_offset)

print("Raw ephem next_rising (ephem.Date):", rise_raw)
print("As UTC datetime:", rise_dt_utc)
print("After adding tz_offset -> LOCAL:", rise_local.strftime("%I:%M %p, %d %b %Y"))
print()

print("=" * 60)
print("DONE — compare 'LOCAL' above to what your app shows.")
print("=" * 60)