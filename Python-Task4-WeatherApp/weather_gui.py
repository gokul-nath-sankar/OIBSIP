import tkinter as tk
from tkinter import ttk
import requests
from io import BytesIO
from PIL import Image, ImageTk
import datetime
import os

# Replace with your free OpenWeatherMap API key or set as environment variable
API_KEY = os.getenv("OPENWEATHER_API_KEY","Your_api_key_here")
CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
ICON_URL = "https://openweathermap.org/img/wn/{}@2x.png"
IPINFO_URL = "https://ipinfo.io/json"


class WeatherAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather Forecast & Live Conditions")
        self.root.geometry("780x680")
        self.root.resizable(False, False)
        self.root.configure(bg="#f4f6f9")

        self.unit = "C"  # Primary unit toggle ('C' or 'F')
        self.weather_data = None
        self.forecast_data = None
        self.icon_cache = {}

        self.build_gui()

    # ==========================================
    # TEMPERATURE CONVERSION HELPERS
    # ==========================================
    @staticmethod
    def k_to_c(kelvin):
        return kelvin - 273.15

    @staticmethod
    def k_to_f(kelvin):
        return (kelvin - 273.15) * 9 / 5 + 32

    def format_temp(self, kelvin, show_both=False):
        c = self.k_to_c(kelvin)
        f = self.k_to_f(kelvin)
        if show_both:
            if self.unit == "C":
                return f"{c:.1f}°C ({f:.1f}°F)"
            return f"{f:.1f}°F ({c:.1f}°C)"
        return f"{c:.1f}°C" if self.unit == "C" else f"{f:.1f}°F"

    # ==========================================
    # API & NETWORK LAYER
    # ==========================================
    def show_error(self, message):
        """Displays error messages directly inside the GUI banner."""
        self.error_label.config(text=f"⚠ {message}", bg="#fdecea", fg="#c0392b")
        self.error_label.pack(fill=tk.X, padx=20, pady=(0, 10))

    def clear_error(self):
        self.error_label.pack_forget()

    def fetch_icon(self, icon_code, size=(70, 70)):
        """Downloads and caches weather condition icons using Pillow."""
        cache_key = (icon_code, size)
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]
        try:
            res = requests.get(ICON_URL.format(icon_code), timeout=4)
            if res.status_code == 200:
                img = Image.open(BytesIO(res.content)).resize(size, Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                self.icon_cache[cache_key] = tk_img
                return tk_img
        except Exception:
            pass
        return None

    def detect_location_by_ip(self):
        """Bonus Feature: Automatically detects user's city via ipinfo.io."""
        self.clear_error()
        try:
            res = requests.get(IPINFO_URL, timeout=5)
            res.raise_for_status()
            data = res.json()
            city = data.get("city")
            if city:
                self.city_entry.delete(0, tk.END)
                self.city_entry.insert(0, city)
                self.get_weather()
            else:
                self.show_error("Could not determine city from your IP address.")
        except requests.RequestException:
            self.show_error("Network error while detecting location via ipinfo.io.")

    def get_weather(self):
        self.clear_error()
        query = self.city_entry.get().strip()

        # Input validation: reject empty input
        if not query:
            self.show_error("Please enter a valid city name or ZIP code.")
            return

        # Fallback Demo Mode if user hasn't inserted an API key yet
        if API_KEY == "YOUR_OPENWEATHER_API_KEY":
            self.load_demo_data(query)
            self.show_error("Demo Mode Active: Replace YOUR_OPENWEATHER_API_KEY for live data.")
            self.render_all()
            return

        params = {"q": query, "appid": API_KEY}
        try:
            cur_res = requests.get(CURRENT_URL, params=params, timeout=6)
            if cur_res.status_code == 401:
                self.show_error("Invalid API Key. Please check your OpenWeatherMap API key.")
                return
            elif cur_res.status_code == 404:
                self.show_error(f"Location '{query}' not found. Please check spelling or ZIP code.")
                return
            cur_res.raise_for_status()

            fc_res = requests.get(FORECAST_URL, params=params, timeout=6)
            fc_res.raise_for_status()

            self.weather_data = cur_res.json()
            self.forecast_data = fc_res.json()
            self.render_all()

        except requests.exceptions.Timeout:
            self.show_error("Network timeout: The weather server took too long to respond.")
        except requests.exceptions.ConnectionError:
            self.show_error("Network error: Please check your internet connection.")
        except Exception as e:
            self.show_error(f"Unexpected API error: {e}")

    def load_demo_data(self, query):
        """Provides realistic fallback JSON data if API key is not configured yet."""
        now = int(datetime.datetime.now().timestamp())
        self.weather_data = {
            "name": query.title(),
            "sys": {"country": "IN"},
            "main": {"temp": 302.15, "humidity": 68},
            "weather": [{"description": "partly cloudy", "icon": "02d"}],
            "wind": {"speed": 4.2}
        }
        items = []
        for i in range(1, 41):
            items.append({
                "dt": now + i * 10800,
                "main": {"temp": 300.15 + (i % 5)},
                "weather": [{"description": "scattered clouds", "icon": "03d"}]
            })
        self.forecast_data = {"list": items}

    # ==========================================
    # UI RENDERING & FORECAST PARSING
    # ==========================================
    def toggle_unit(self):
        self.unit = "F" if self.unit == "C" else "C"
        self.unit_btn.config(text=f"Switch to °{'C' if self.unit == 'F' else 'F'}")
        if self.weather_data:
            self.render_all()

    def render_all(self):
        if not self.weather_data or not self.forecast_data:
            return

        # 1. Current Weather Panel
        city = self.weather_data.get("name", "Unknown")
        country = self.weather_data.get("sys", {}).get("country", "")
        temp_k = self.weather_data["main"]["temp"]
        humidity = self.weather_data["main"]["humidity"]
        wind = self.weather_data["wind"]["speed"]
        desc = self.weather_data["weather"][0]["description"].title()
        icon_code = self.weather_data["weather"][0]["icon"]

        self.city_title_lbl.config(text=f"{city}, {country}")
        self.temp_lbl.config(text=self.format_temp(temp_k, show_both=True))
        self.desc_lbl.config(text=desc)
        self.details_lbl.config(text=f"Humidity: {humidity}%   |   Wind Speed: {wind} m/s")

        icon_img = self.fetch_icon(icon_code, size=(80, 80))
        if icon_img:
            self.icon_lbl.config(image=icon_img, text="")
            self.icon_lbl.image = icon_img
        else:
            self.icon_lbl.config(image="", text="[Icon]")

        # 2. Hourly Forecast Panel (Next 6 Hours interpolated from 3-hr API blocks)
        for widget in self.hourly_frame.winfo_children():
            widget.destroy()

        raw_list = self.forecast_data["list"]
        base_temp = self.weather_data["main"]["temp"]
        next_3h_temp = raw_list[0]["main"]["temp"]
        next_6h_temp = raw_list[1]["main"]["temp"]
        now_dt = datetime.datetime.now()

        for hr in range(1, 7):
            hr_time = (now_dt + datetime.timedelta(hours=hr)).strftime("%I:%M %p")
            if hr <= 3:
                interp_k = base_temp + (next_3h_temp - base_temp) * (hr / 3.0)
                slot = raw_list[0]
            else:
                interp_k = next_3h_temp + (next_6h_temp - next_3h_temp) * ((hr - 3) / 3.0)
                slot = raw_list[1]

            card = tk.Frame(self.hourly_frame, bg="white", bd=1, relief=tk.SOLID, padx=10, pady=8)
            card.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=4)

            tk.Label(card, text=hr_time, font=("Segoe UI", 9, "bold"), bg="white").pack()
            ic = self.fetch_icon(slot["weather"][0]["icon"], size=(40, 40))
            lbl_ic = tk.Label(card, bg="white")
            if ic:
                lbl_ic.config(image=ic)
                lbl_ic.image = ic
            lbl_ic.pack()
            tk.Label(card, text=self.format_temp(interp_k), font=("Segoe UI", 10, "bold"), bg="white", fg="#2c3e50").pack()
            tk.Label(card, text=slot["weather"][0]["description"].title(), font=("Segoe UI", 8), bg="white", fg="#7f8c8d", wraplength=85).pack()

        # 3. Daily Forecast Panel (Next 5 Days)
        for widget in self.daily_frame.winfo_children():
            widget.destroy()

        daily_groups = {}
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        for item in raw_list:
            dt_obj = datetime.datetime.fromtimestamp(item["dt"])
            date_str = dt_obj.strftime("%Y-%m-%d")
            if date_str == today_str and len(daily_groups) == 0:
                continue
            daily_groups.setdefault(date_str, []).append(item)

        for date_str in list(daily_groups.keys())[:5]:
            entries = daily_groups[date_str]
            avg_k = sum(e["main"]["temp"] for e in entries) / len(entries)
            mid_entry = entries[len(entries) // 2]
            day_name = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%a, %b %d")

            card = tk.Frame(self.daily_frame, bg="white", bd=1, relief=tk.SOLID, padx=10, pady=8)
            card.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=4)

            tk.Label(card, text=day_name, font=("Segoe UI", 9, "bold"), bg="white").pack()
            ic = self.fetch_icon(mid_entry["weather"][0]["icon"], size=(45, 45))
            lbl_ic = tk.Label(card, bg="white")
            if ic:
                lbl_ic.config(image=ic)
                lbl_ic.image = ic
            lbl_ic.pack()
            tk.Label(card, text=self.format_temp(avg_k, show_both=True), font=("Segoe UI", 9, "bold"), bg="white", fg="#2980b9").pack()
            tk.Label(card, text=mid_entry["weather"][0]["description"].title(), font=("Segoe UI", 8), bg="white", fg="#7f8c8d", wraplength=100).pack()

    # ==========================================
    # GUI LAYOUT CONSTRUCTION
    # ==========================================
    def build_gui(self):
        # Top Search Bar
        top_bar = tk.Frame(self.root, bg="#2c3e50", padx=20, pady=14)
        top_bar.pack(fill=tk.X)

        tk.Label(top_bar, text="City / ZIP:", font=("Segoe UI", 11, "bold"), bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=(0, 8))

        self.city_entry = tk.Entry(top_bar, font=("Segoe UI", 11), width=24)
        self.city_entry.pack(side=tk.LEFT, ipady=4, padx=(0, 8))
        self.city_entry.bind("<Return>", lambda e: self.get_weather())

        tk.Button(
            top_bar, text="Get Weather", font=("Segoe UI", 10, "bold"),
            bg="#27ae60", fg="white", cursor="hand2", padx=12, pady=3, command=self.get_weather
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            top_bar, text="📍 Auto-Detect IP", font=("Segoe UI", 10),
            bg="#34495e", fg="white", cursor="hand2", padx=10, pady=3, command=self.detect_location_by_ip
        ).pack(side=tk.LEFT)

        self.unit_btn = tk.Button(
            top_bar, text="Switch to °F", font=("Segoe UI", 10, "bold"),
            bg="#e67e22", fg="white", cursor="hand2", padx=12, pady=3, command=self.toggle_unit
        )
        self.unit_btn.pack(side=tk.RIGHT)

        # In-GUI Error Banner (hidden by default)
        self.error_label = tk.Label(self.root, text="", font=("Segoe UI", 10, "bold"), pady=8)

        # Current Weather Card
        cur_card = tk.Frame(self.root, bg="white", bd=1, relief=tk.SOLID, padx=20, pady=15)
        cur_card.pack(fill=tk.X, padx=20, pady=15)

        left_cur = tk.Frame(cur_card, bg="white")
        left_cur.pack(side=tk.LEFT, fill=tk.Y)

        self.city_title_lbl = tk.Label(left_cur, text="Enter a location above", font=("Segoe UI", 16, "bold"), bg="white", fg="#2c3e50")
        self.city_title_lbl.pack(anchor="w")

        self.temp_lbl = tk.Label(left_cur, text="-- °C (-- °F)", font=("Segoe UI", 22, "bold"), bg="white", fg="#e74c3c")
        self.temp_lbl.pack(anchor="w", pady=(4, 4))

        self.desc_lbl = tk.Label(left_cur, text="Condition: --", font=("Segoe UI", 12, "italic"), bg="white", fg="#555")
        self.desc_lbl.pack(anchor="w")

        self.details_lbl = tk.Label(left_cur, text="Humidity: --%   |   Wind Speed: -- m/s", font=("Segoe UI", 10), bg="white", fg="#7f8c8d")
        self.details_lbl.pack(anchor="w", pady=(6, 0))

        self.icon_lbl = tk.Label(cur_card, bg="white")
        self.icon_lbl.pack(side=tk.RIGHT, padx=20)

        # Hourly Forecast Section (Next 6 Hours)
        tk.Label(self.root, text="Hourly Forecast (Next 6 Hours)", font=("Segoe UI", 11, "bold"), bg="#f4f6f9", fg="#2c3e50").pack(anchor="w", padx=20)
        self.hourly_frame = tk.Frame(self.root, bg="#f4f6f9", pady=8)
        self.hourly_frame.pack(fill=tk.X, padx=16)

        # Daily Forecast Section (Next 5 Days)
        tk.Label(self.root, text="5-Day Forecast", font=("Segoe UI", 11, "bold"), bg="#f4f6f9", fg="#2c3e50").pack(anchor="w", padx=20, pady=(10, 0))
        self.daily_frame = tk.Frame(self.root, bg="#f4f6f9", pady=8)
        self.daily_frame.pack(fill=tk.X, padx=16)


if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherAppGUI(root)
    root.mainloop()