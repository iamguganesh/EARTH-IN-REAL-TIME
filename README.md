# 🌍 Earth in Real Time

A modern, dark-glassmorphism dashboard for exploring live information about
planet Earth — world clocks, weather, sunrise/sunset, moon phase, an
interactive map, Earth facts, and NASA's Picture of the Day.

## Tech Stack

- Python (Flask) backend
- HTML5 / CSS3 / vanilla JavaScript (no frontend framework)
- Jinja2 templates
- Leaflet.js (via CDN) for the interactive world map

## Project Structure

```
project/
├── app.py                 # Flask app + routes + API endpoints
├── config.py              # Configuration (API keys via environment vars)
├── requirements.txt
├── .env.example           # Copy to .env and fill in your API keys
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

2. **Configure API keys** (optional, but needed for live weather + NASA data)

   Copy `.env.example` to `.env` and fill in your keys, then export them:

   ```bash
   export OPENWEATHER_API_KEY=your_key_here
   export NASA_API_KEY=your_key_here   # DEMO_KEY works for light testing
   ```

   - Get a free OpenWeatherMap key at https://openweathermap.org/api
   - Get a free NASA API key at https://api.nasa.gov

   Without an OpenWeatherMap key, the weather search will show a friendly
   "service not configured" message instead of crashing. Without a NASA key,
   `DEMO_KEY` is used automatically (rate-limited but functional).

3. **Run the app**

   ```bash
   python app.py
   ```

   Then open http://localhost:5000 in your browser.

## Features

| Section | Description |
|---|---|
| Hero | Animated rotating Earth, gradient title, Explore CTA |
| Live World Clock | 8 major cities, updates every second via JS |
| Weather Search | Live temperature, condition, humidity, wind, feels-like |
| Sunrise & Sunset | Computed from the weather API response |
| Moon Information | Phase, illumination %, calculated locally (no API needed) |
| World Time Zones | Live-updating cards with UTC offsets |
| Earth Facts | Random facts, refreshable with animation |
| Interactive Map | Pan & zoom world map (Leaflet + OpenStreetMap tiles) |
| NASA Picture of the Day | Daily space image with title & description |

## Notes

- All external API calls are wrapped in error handling — the app never
  crashes if a third-party service is down or unreachable; it shows a clear,
  friendly message instead.
- No API keys are hardcoded anywhere in the source. They are read from
  environment variables in `config.py`.
