"""
Earth in Real Time
------------------
A Flask application that surfaces live information about planet Earth:
world clocks, weather, sunrise/sunset, moon phase, an interactive map,
random Earth facts and NASA's Picture of the Day.

Run with:
    pip install -r requirements.txt
    python app.py
"""
import math
import random
from datetime import datetime, timedelta, timezone

import ephem
from flask import send_from_directory
import requests
from flask import Flask, jsonify, render_template, request

from config import Config

app = Flask(__name__)
app.config.from_object(Config)


# ---------------------------------------------------------------------------
# Static reference data
# ---------------------------------------------------------------------------

EARTH_FACTS = [
    "Earth is the only planet not named after a Greek or Roman god.",
    "A day on Earth is slowly getting longer — about 1.7 milliseconds per century.",
    "Earth's core is almost as hot as the surface of the Sun, around 5,400°C.",
    "About 71% of Earth's surface is covered by water, yet 96.5% of it is ocean saltwater.",
    "Earth is the densest planet in the Solar System.",
    "The atmosphere doesn't have a hard edge — it just gradually thins into space.",
    "Earth travels around the Sun at roughly 107,000 km/h (67,000 mph).",
    "Mount Everest is the tallest peak above sea level, but Mauna Kea is the tallest mountain base to summit.",
    "Earth has one natural satellite, the Moon, formed roughly 4.5 billion years ago.",
    "The Amazon rainforest produces about 20% of the world's oxygen.",
    "Earth's magnetic field protects the planet from most solar radiation.",
    "A year on Earth is not exactly 365 days — it's about 365.25, which is why we have leap years.",
    "The highest point on Earth measured from the planet's center is Mount Chimborazo in Ecuador.",
    "Earth is the only known planet with plate tectonics currently active.",
    "Lightning strikes the Earth about 8 million times a day.",
]

# Major world cities used for the live world clock / timezone cards
WORLD_CITIES = [
    {"name": "UTC", "tz": "UTC", "label": "Coordinated Universal Time"},
    {"name": "New York", "tz": "America/New_York", "label": "USA"},
    {"name": "London", "tz": "Europe/London", "label": "United Kingdom"},
    {"name": "Paris", "tz": "Europe/Paris", "label": "France"},
    {"name": "Dubai", "tz": "Asia/Dubai", "label": "UAE"},
    {"name": "Mumbai", "tz": "Asia/Kolkata", "label": "India"},
    {"name": "Tokyo", "tz": "Asia/Tokyo", "label": "Japan"},
    {"name": "Sydney", "tz": "Australia/Sydney", "label": "Australia"},
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def calculate_moon_phase():
    """
    Calculate the current moon phase and illumination using a well-known
    synodic-month approximation. This needs no external API, so moon phase
    data is always available even if a live moon API cannot be reached.
    """
    synodic_month = 29.53058867  # average length of a lunar cycle in days
    known_new_moon = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    days_since = (now - known_new_moon).total_seconds() / 86400
    phase_position = (days_since % synodic_month) / synodic_month  # 0..1

    illumination = round((1 - math.cos(2 * math.pi * phase_position)) / 2 * 100, 1)

    if phase_position < 0.03 or phase_position > 0.97:
        phase_name = "New Moon"
        emoji = "🌑"
    elif phase_position < 0.22:
        phase_name = "Waxing Crescent"
        emoji = "🌒"
    elif phase_position < 0.28:
        phase_name = "First Quarter"
        emoji = "🌓"
    elif phase_position < 0.47:
        phase_name = "Waxing Gibbous"
        emoji = "🌔"
    elif phase_position < 0.53:
        phase_name = "Full Moon"
        emoji = "🌕"
    elif phase_position < 0.72:
        phase_name = "Waning Gibbous"
        emoji = "🌖"
    elif phase_position < 0.78:
        phase_name = "Last Quarter"
        emoji = "🌗"
    else:
        phase_name = "Waning Crescent"
        emoji = "🌘"

    return {
        "phase_name": phase_name,
        "emoji": emoji,
        "illumination": illumination,
        "age_days": round(days_since % synodic_month, 1),
        # Precise moonrise/moonset need an observer's exact lat/long and a
        # dedicated ephemeris service. api_weather() fills these in for real
        # once it has a city's coordinates; this is the offline fallback.
        "moonrise": "Data unavailable",
        "moonset": "Data unavailable",
    }


def compute_moon_rise_set(lat, lon, tz_offset_seconds):
    """
    Compute the next moonrise/moonset for a given lat/lon, converted to
    that location's local time. Returns "N/A" for either value if the
    moon doesn't rise or set there in the near term (rare, near the poles).
    """
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = datetime.now(timezone.utc)

    moon = ephem.Moon()

    try:
        rise_dt = observer.next_rising(moon).datetime().replace(tzinfo=timezone.utc)
        rise_local = rise_dt + timedelta(seconds=tz_offset_seconds)
        rise_str = rise_local.strftime("%I:%M %p")
    except (ephem.AlwaysUpError, ephem.NeverUpError):
        rise_str = "N/A"

    try:
        set_dt = observer.next_setting(moon).datetime().replace(tzinfo=timezone.utc)
        set_local = set_dt + timedelta(seconds=tz_offset_seconds)
        set_str = set_local.strftime("%I:%M %p")
    except (ephem.AlwaysUpError, ephem.NeverUpError):
        set_str = "N/A"

    return rise_str, set_str


def format_unix_time(unix_ts, tz_offset_seconds):
    """Convert a UTC unix timestamp + city UTC offset into an HH:MM string."""
    if unix_ts is None:
        return "N/A"
    local_dt = datetime.utcfromtimestamp(unix_ts + tz_offset_seconds)
    return local_dt.strftime("%I:%M %p")


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Render the single-page dashboard."""
    return render_template("index.html", world_cities=WORLD_CITIES)


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.route("/api/weather")
def api_weather():
    """
    Fetch current weather, sunrise/sunset and day length for a given city.
    Query param: ?city=<city name>
    """
    city = request.args.get("city", "").strip()
    if not city:
        return jsonify({"success": False, "error": "Please enter a city name."}), 400

    api_key = app.config["OPENWEATHER_API_KEY"]
    if not api_key:
        return jsonify({
            "success": False,
            "error": "Weather service is not configured. Add OPENWEATHER_API_KEY to your environment.",
        }), 503

    try:
        response = requests.get(
            app.config["OPENWEATHER_BASE_URL"],
            params={"q": city, "appid": api_key, "units": "metric"},
            timeout=app.config["REQUEST_TIMEOUT"],
        )
    except requests.exceptions.RequestException:
        return jsonify({
            "success": False,
            "error": "Could not reach the weather service. Please try again shortly.",
        }), 502

    if response.status_code == 404:
        return jsonify({"success": False, "error": f'City "{city}" was not found.'}), 404

    if response.status_code != 200:
        return jsonify({
            "success": False,
            "error": "Weather service returned an unexpected error.",
        }), 502

    data = response.json()

    try:
        tz_offset = data.get("timezone", 0)
        sunrise_ts = data["sys"].get("sunrise")
        sunset_ts = data["sys"].get("sunset")

        day_length = "N/A"
        if sunrise_ts and sunset_ts:
            seconds = sunset_ts - sunrise_ts
            hours, remainder = divmod(seconds, 3600)
            minutes = remainder // 60
            day_length = f"{hours}h {minutes}m"

        moon = calculate_moon_phase()

        # Override the honest placeholder with a real calculation now that we
        # have this city's exact coordinates from OpenWeatherMap's response.
        coord = data.get("coord", {})
        lat, lon = coord.get("lat"), coord.get("lon")
        if lat is not None and lon is not None:
            try:
                moonrise, moonset = compute_moon_rise_set(lat, lon, tz_offset)
                moon["moonrise"] = moonrise
                moon["moonset"] = moonset
            except Exception:
                pass  # fall back silently to the existing "Data unavailable"

        result = {
            "success": True,
            "city": data.get("name", city),
            "country": data.get("sys", {}).get("country", ""),
            "temperature": round(data["main"]["temp"]),
            "feels_like": round(data["main"]["feels_like"]),
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
            "condition": data["weather"][0]["description"].title(),
            "icon": data["weather"][0]["icon"],
            "sunrise": format_unix_time(sunrise_ts, tz_offset),
            "sunset": format_unix_time(sunset_ts, tz_offset),
            "day_length": day_length,
            "moon": moon,
        }
        return jsonify(result)

    except (KeyError, IndexError, TypeError):
        return jsonify({
            "success": False,
            "error": "Received an unexpected response from the weather service.",
        }), 502


@app.route("/api/apod")
def api_apod():
    """
    Fetch NASA's last N Astronomy Pictures of the Day (a small gallery).
    Query param: ?count=<1-10>  (default 5)
    """
    api_key = app.config["NASA_API_KEY"]

    count = request.args.get("count", default=5, type=int) or 5
    count = max(1, min(count, 10))  # keep requests small and sane

    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=count - 1)

    try:
        response = requests.get(
            app.config["NASA_APOD_URL"],
            params={
                "api_key": api_key,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            timeout=app.config["REQUEST_TIMEOUT"],
        )
    except requests.exceptions.RequestException as exc:
        app.logger.error("NASA APOD request failed: %s", exc)
        return jsonify({
            "success": False,
            "error": "Could not reach NASA's servers right now. Please try again later.",
        }), 502

    if response.status_code != 200:
        try:
            nasa_message = response.json().get("error", {}).get("message")
        except ValueError:
            nasa_message = response.text[:200]

        app.logger.error("NASA APOD returned %s: %s", response.status_code, nasa_message)

        if response.status_code == 429:
            error = "NASA's rate limit was hit (DEMO_KEY allows only 30 requests/hour). Get a free personal key at https://api.nasa.gov and set NASA_API_KEY."
        elif response.status_code == 403:
            error = "NASA rejected the API key. Check that NASA_API_KEY is set correctly."
        else:
            error = f"NASA's Picture of the Day service returned an error ({response.status_code})."

        return jsonify({"success": False, "error": error}), 502

    data = response.json()

    # A single-day request returns a dict; a date-range request returns a
    # list. We always request a range, but handle both just in case.
    entries = data if isinstance(data, list) else [data]
    entries.sort(key=lambda d: d.get("date", ""), reverse=True)

    items = []
    for entry in entries:
        media_type = entry.get("media_type", "unknown")
        url = (entry.get("hdurl") or entry.get("url", "")) if media_type == "image" else entry.get("url", "")
        items.append({
            "media_type": media_type,
            "url": url,
            "title": entry.get("title", "NASA Picture of the Day"),
            "explanation": entry.get("explanation", ""),
            "date": entry.get("date", ""),
        })

    return jsonify({"success": True, "items": items})


@app.route("/api/fact")
def api_fact():
    """Return one random Earth fact."""
    return jsonify({"fact": random.choice(EARTH_FACTS)})


@app.route("/api/moon")
def api_moon():
    """Standalone endpoint for current moon phase data."""
    return jsonify(calculate_moon_phase())


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_error):
    return render_template("index.html", world_cities=WORLD_CITIES), 404


@app.errorhandler(500)
def server_error(_error):
    return jsonify({"success": False, "error": "Something went wrong on our end."}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

if __name__ == "__main__":

@app.route("/google59f5e3900c90b4e8.html")
def google_verification():
    return send_from_directory(".", "google59f5e3900c90b4e8.html")