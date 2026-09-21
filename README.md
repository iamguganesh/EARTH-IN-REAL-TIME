# 🌍 Earth in Real Time

A live web dashboard that pulls together real-time information about planet
Earth — world clocks, weather, sunrise/sunset, moon phase and moonrise/moonset,
an interactive map, Earth facts, and NASA's Picture of the Day — all on one
page, instead of five different tabs.

## Features

| Section | Description |
|---|---|
| Hero | Animated rotating Earth, gradient title, Explore CTA |
| Live World Clock | 8 major cities, updates every second via JS (`Intl.DateTimeFormat`) |
| Weather Search | Live temperature, condition, humidity, wind, feels-like |
| Sunrise & Sunset | Pulled directly from the weather API response |
| Moon Information | Phase & illumination calculated locally (no API needed); real moonrise/moonset calculated from the searched city's coordinates |
| World Time Zones | Live-updating cards with UTC offsets |
| Earth Facts | Random facts, refreshable with animation |
| Interactive Map | Pan & zoom world map (Leaflet.js + OpenStreetMap tiles) |
| NASA Picture of the Day | A gallery of the last 5 days of NASA's astronomy images, with click-to-zoom and full descriptions |

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML5 / CSS3 / vanilla JavaScript (no frontend framework)
- **Templates:** Jinja2
- **Map:** Leaflet.js (via CDN) + OpenStreetMap tiles
- **Astronomy:** `ephem` (PyEphem) for real moonrise/moonset calculations
- **APIs:** OpenWeatherMap (weather, sun times), NASA APOD (picture of the day)

## Project Structure

```
project/
├── app.py                 # Flask app + routes + API endpoints
├── config.py               # Configuration (API keys via environment vars)
├── requirements.txt
├── .env.example             # Copy to .env and fill in your API keys
├── templates/
│   ├── base.html
│   └── index.html
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── images/
└── README.md
```

## Setup

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API keys** (needed for live weather + NASA data)

   Copy `.env.example` to `.env` — the filename must be exactly `.env`,
   not `.env.example` — and fill in your keys:

   ```bash
   OPENWEATHER_API_KEY="your_key_here"
   NASA_API_KEY="your_key_here"   # DEMO_KEY works but is rate-limited to 30 req/hour
   ```

   - Get a free OpenWeatherMap key at https://openweathermap.org/api
   - Get a free NASA API key at https://api.nasa.gov

   Without an OpenWeatherMap key, weather search shows a friendly "service
   not configured" message instead of crashing. Without a personal NASA
   key, `DEMO_KEY` is used automatically (functional, but rate-limited).

3. **Run the app**

   ```bash
   python app.py
   ```

   Then open http://localhost:5000 in your browser.

## How the Moon Data Works

- **Moon phase & illumination %** are calculated entirely locally using a
  synodic-month approximation (based on Jean Meeus, *Astronomical
  Algorithms*), so this always works even with no internet connection.
- **Moonrise & moonset** are calculated for the *exact coordinates* of
  whichever city you search — using `ephem`, once `app.py` has that
  city's latitude/longitude from OpenWeatherMap's response. If the
  calculation fails for any reason, it falls back to an honest
  "Data unavailable" rather than showing a fabricated time.

## Notes

- All external API calls are wrapped in error handling — the app never
  crashes if a third-party service is down; it shows a clear, friendly
  message instead.
- No API keys are hardcoded anywhere in the source. They're read from
  environment variables in `config.py` via `.env`.

## References

- J. Meeus, *Astronomical Algorithms*, 2nd ed. Willmann-Bell, 1998.
- OpenWeatherMap, "Current Weather Data API." https://openweathermap.org/current
- NASA, "APOD API Documentation." https://api.nasa.gov
- Leaflet Contributors, "Leaflet." https://leafletjs.com
- OpenStreetMap Foundation, "Tile Usage Policy." https://operations.osmfoundation.org
