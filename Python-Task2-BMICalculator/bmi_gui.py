import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

DB_NAME = "bmi_records.db"


class BMICalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BMI Calculator & Health Trend Tracker")
        self.root.geometry("850x560")
        self.root.resizable(False, False)

        self.init_db()
        self.build_gui()
        self.refresh_user_list()

    # ==========================================
    # DATABASE LAYER (SQLite3 with Error Handling)
    # ==========================================
    def init_db(self):
        """Initializes SQLite database and creates the records table if missing."""
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bmi_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        weight REAL NOT NULL,
                        height REAL NOT NULL,
                        bmi REAL NOT NULL,
                        category TEXT NOT NULL,
                        timestamp TEXT NOT NULL
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to initialize database:\n{e}")

    def save_record(self, username, weight, height, bmi, category):
        """Saves a single BMI record to SQLite with error handling."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO bmi_history (username, weight, height, bmi, category, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, weight, height, bmi, category, timestamp))
                conn.commit()
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Write Error", f"Could not save record:\n{e}")
            return False

    def get_users(self):
        """Fetches distinct usernames from the database."""
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT username FROM bmi_history ORDER BY username ASC")
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            messagebox.showerror("Database Read Error", f"Could not load user list:\n{e}")
            return []

    def get_user_history(self, username):
        """Fetches chronological BMI history for a specific user."""
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT timestamp, bmi, weight, category
                    FROM bmi_history
                    WHERE username = ?
                    ORDER BY id ASC
                """, (username,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Read Error", f"Could not fetch history:\n{e}")
            return []

    # ==========================================
    # CORE BMI LOGIC & VALIDATION
    # ==========================================
    @staticmethod
    def classify_bmi(bmi):
        """Returns (Category Name, Hex Color Code) based on standard WHO thresholds."""
        if bmi < 18.5:
            return "Underweight", "#3498db"  # Blue
        elif 18.5 <= bmi < 25.0:
            return "Normal", "#2ecc71"       # Green
        elif 25.0 <= bmi < 30.0:
            return "Overweight", "#f39c12"   # Orange
        else:
            return "Obese", "#e74c3c"        # Red

    def calculate_and_save(self):
        """Validates inputs, computes BMI, updates GUI, and plots user history."""
        username = self.user_combo.get().strip()
        weight_str = self.weight_entry.get().strip()
        height_str = self.height_entry.get().strip()

        if not username:
            messagebox.showwarning("Input Validation", "Please enter or select a user name.")
            return

        # Validate numeric and positive inputs
        try:
            weight = float(weight_str)
            height = float(height_str)
        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Weight and Height must be valid numbers (e.g., Weight: 70, Height: 1.75)."
            )
            return

        if weight <= 0 or height <= 0:
            messagebox.showerror(
                "Invalid Input",
                "Weight and Height must be positive values greater than zero."
            )
            return

        # Sanity warning if user enters height in cm instead of meters
        if height > 3.0:
            messagebox.showwarning(
                "Check Height Unit",
                "Height should be in meters (e.g., 1.75 instead of 175). Please adjust and try again."
            )
            return

        # Formula: BMI = weight / (height^2)
        bmi = round(weight / (height ** 2), 2)
        category, color = self.classify_bmi(bmi)

        # Update result banner with color-coded feedback
        self.result_frame.config(bg=color)
        self.bmi_value_label.config(text=f"BMI: {bmi:.2f}", bg=color, fg="white")
        self.bmi_cat_label.config(text=f"Category: {category}", bg=color, fg="white")

        # Save to DB and refresh UI
        if self.save_record(username, weight, height, bmi, category):
            self.refresh_user_list(selected_user=username)
            self.update_chart(username)

    # ==========================================
    # GUI LAYOUT & MATPLOTLIB CHART
    # ==========================================
    def build_gui(self):
        # Left Panel: Inputs & Results
        left_panel = tk.Frame(self.root, padx=20, pady=20)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left_panel, text="BMI Calculator", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 15))

        # User selection / creation
        tk.Label(left_panel, text="User Name (Select or type new):", font=("Segoe UI", 10)).pack(anchor="w")
        self.user_combo = ttk.Combobox(left_panel, font=("Segoe UI", 11), width=24)
        self.user_combo.pack(pady=(2, 12), fill=tk.X)
        self.user_combo.bind("<<ComboboxSelected>>", lambda e: self.update_chart(self.user_combo.get()))

        # Weight input
        tk.Label(left_panel, text="Weight (kg):", font=("Segoe UI", 10)).pack(anchor="w")
        self.weight_entry = ttk.Entry(left_panel, font=("Segoe UI", 11))
        self.weight_entry.pack(pady=(2, 12), fill=tk.X)

        # Height input
        tk.Label(left_panel, text="Height (m) [e.g. 1.75]:", font=("Segoe UI", 10)).pack(anchor="w")
        self.height_entry = ttk.Entry(left_panel, font=("Segoe UI", 11))
        self.height_entry.pack(pady=(2, 18), fill=tk.X)

        # Calculate Button
        calc_btn = tk.Button(
            left_panel, text="Calculate & Save BMI", font=("Segoe UI", 11, "bold"),
            bg="#2c3e50", fg="white", activebackground="#34495e", activeforeground="white",
            cursor="hand2", pady=8, command=self.calculate_and_save
        )
        calc_btn.pack(fill=tk.X, pady=(0, 20))

        # Color-coded Result Card
        self.result_frame = tk.Frame(left_panel, bg="#ecf0f1", bd=1, relief=tk.SOLID, padx=15, pady=20)
        self.result_frame.pack(fill=tk.X, pady=(10, 15))

        self.bmi_value_label = tk.Label(
            self.result_frame, text="BMI: --", font=("Segoe UI", 18, "bold"), bg="#ecf0f1", fg="#2c3e50"
        )
        self.bmi_value_label.pack()

        self.bmi_cat_label = tk.Label(
            self.result_frame, text="Enter details above", font=("Segoe UI", 12), bg="#ecf0f1", fg="#7f8c8d"
        )
        self.bmi_cat_label.pack(pady=(5, 0))

        # Legend
        legend_text = (
            "Standard BMI Categories:\n"
            "• Underweight: < 18.5 (Blue)\n"
            "• Normal: 18.5 – 24.9 (Green)\n"
            "• Overweight: 25.0 – 29.9 (Orange)\n"
            "• Obese: ≥ 30.0 (Red)"
        )
        tk.Label(left_panel, text=legend_text, font=("Segoe UI", 9), justify=tk.LEFT, fg="#555555").pack(anchor="w", pady=(10, 0))

        # Right Panel: Matplotlib Trend Graph
        right_panel = tk.Frame(self.root, padx=15, pady=20, bg="white")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(5.2, 4.5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.draw_empty_chart()

    def refresh_user_list(self, selected_user=None):
        users = self.get_users()
        self.user_combo["values"] = users
        if selected_user:
            self.user_combo.set(selected_user)
        elif users and not self.user_combo.get():
            self.user_combo.set(users[0])
            self.update_chart(users[0])

    def draw_empty_chart(self):
        self.ax.clear()
        self.ax.set_title("BMI Trend Over Time", fontsize=12, fontweight="bold")
        self.ax.set_xlabel("Date / Entry")
        self.ax.set_ylabel("BMI")
        self.ax.text(0.5, 0.5, "Select or add a user to view BMI trend", ha="center", va="center", transform=self.ax.transAxes, color="gray")
        self.fig.tight_layout()
        self.canvas.draw()

    def update_chart(self, username):
        history = self.get_user_history(username)
        if not history:
            self.draw_empty_chart()
            return

        dates = [row[0][5:] for row in history]  # Format MM-DD HH:MM
        bmis = [row[1] for row in history]

        self.ax.clear()
        # Plot reference threshold lines
        self.ax.axhline(18.5, color="#3498db", linestyle="--", linewidth=0.8, label="Underweight (18.5)")
        self.ax.axhline(25.0, color="#2ecc71", linestyle="--", linewidth=0.8, label="Normal Max (25.0)")
        self.ax.axhline(30.0, color="#e74c3c", linestyle="--", linewidth=0.8, label="Obese (30.0)")

        # Plot user's BMI trend line
        x_indices = range(len(bmis))
        self.ax.plot(x_indices, bmis, marker="o", color="#2c3e50", linewidth=2, markersize=6, label=f"{username}'s BMI")

        # Annotate points with BMI values
        for i, val in enumerate(bmis):
            self.ax.annotate(f"{val}", (i, val), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)

        self.ax.set_title(f"BMI History for {username}", fontsize=12, fontweight="bold")
        self.ax.set_xticks(list(x_indices))
        self.ax.set_xticklabels(dates, rotation=30, ha="right", fontsize=8)
        self.ax.set_ylabel("BMI Value")
        self.ax.grid(True, linestyle=":", alpha=0.6)
        self.ax.legend(loc="upper left", fontsize=7)
        self.fig.tight_layout()
        self.canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = BMICalculatorApp(root)
    root.mainloop()