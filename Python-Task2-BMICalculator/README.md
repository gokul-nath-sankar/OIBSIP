# Task 2: BMI Calculator & Health Trend Tracker (Beginner + Advanced Tier)

A Python application that calculates Body Mass Index (BMI), classifies results into standard World Health Organization (WHO) health categories, and tracks historical multi-user BMI trends using SQLite and Matplotlib.

## Features
- **Beginner CLI (`bmi_cli.py`):** Command-line interface with strict numeric and positive-value input validation.
- **Advanced GUI (`bmi_gui.py`):** Built with `tkinter`, featuring color-coded category banners (Blue = Underweight, Green = Normal, Orange = Overweight, Red = Obese).
- **Multi-User Persistence:** Stores historical BMI records per user in a local `sqlite3` database (`bmi_records.db`).
- **Trend Visualization:** Embeds a live `matplotlib` line chart showing the selected user's BMI progression against standard health thresholds.

## How to Run
```bash
python bmi_gui.py

