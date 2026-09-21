"""
Configuration for Earth in Real Time.

API keys are read from environment variables so nothing secret is ever
hardcoded in source control. Copy `.env.example` to `.env` (or export the
variables in your shell) before running the app.
"""

import os

from dotenv import load_dotenv

# Load variables from a .env file (if present) into the environment. This
# means you can just create `.env` from `.env.example` and fill in your
# keys -- no need to manually `export` them in your shell.
load_dotenv()


class Config:
    # OpenWeatherMap API key -> https://openweathermap.org/api
    OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")

    # NASA API key -> https://api.nasa.gov  (DEMO_KEY works for light testing)
    NASA_API_KEY = os.environ.get("NASA_API_KEY", "DEMO_KEY")

    # Base API endpoints
    OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"

    # Request timeout (seconds) for outbound API calls
    REQUEST_TIMEOUT = 20
