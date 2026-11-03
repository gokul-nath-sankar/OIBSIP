import os
import requests

API_KEY = os.getenv("OPENWEATHER_API_KEY", "Your_api_key_here")  # Replace with your OpenWeatherMap API key or set as environment variable
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def fetch_cli_weather(location):
    params = {"q": location, "appid": API_KEY}
    try:
        response = requests.get(BASE_URL, params=params, timeout=6)
        if response.status_code == 401:
            print("Error: Invalid API key. Please verify your OpenWeatherMap key.")
            return
        elif response.status_code == 404:
            print(f"Error: Location '{location}' not found. Please check the city name or ZIP code.")
            return
        response.raise_for_status()
        data = response.json()

        city = data.get("name", location)
        country = data.get("sys", {}).get("country", "")
        temp_k = data["main"]["temp"]
        temp_c = temp_k - 273.15
        temp_f = temp_c * 9 / 5 + 32
        humidity = data["main"]["humidity"]
        condition = data["weather"][0]["description"].title()
        wind_speed = data["wind"]["speed"]

        print(f"\n--- Current Weather for {city}, {country} ---")
        print(f"Temperature : {temp_c:.1f}°C / {temp_f:.1f}°F")
        print(f"Condition   : {condition}")
        print(f"Humidity    : {humidity}%")
        print(f"Wind Speed  : {wind_speed} m/s\n")

    except requests.exceptions.Timeout:
        print("Error: Network request timed out. Please try again later.")
    except requests.exceptions.RequestException as e:
        print(f"Network Error: Failed to reach weather service ({e}).")


def main():
    print("=== Command-Line Weather App ===")
    while True:
        location = input("Enter a city name or ZIP code (or 'q' to quit): ").strip()
        if location.lower() == 'q':
            break
        if not location:
            print("Error: City or ZIP code input cannot be empty.")
            continue
        fetch_cli_weather(location)


if __name__ == "__main__":
    main()