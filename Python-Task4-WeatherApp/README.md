# Task 4: Basic Weather App (Beginner + Advanced Tier)

A real-time weather and forecast application powered by the OpenWeatherMap REST API, `tkinter`, and `Pillow`.

## Features
- **Beginner CLI (`weather_cli.py`):** Fetches and displays live temperature (°C/°F), humidity, wind speed, and conditions by city name or ZIP/PIN code.
- **Advanced GUI (`weather_gui.py`):** Displays dynamic weather condition icons, a 6-hour forecast panel, and a 5-day forecast panel.
- **Unit Toggle & Auto-Location:** Instant `°C / °F` switching and automatic IP-based city detection via `ipinfo.io`.
- **In-GUI Error Handling:** Graceful handling of invalid locations, network timeouts, and API key states.

## How to Run
```bash
export OPENWEATHER_API_KEY="your_api_key"
python weather_gui.py