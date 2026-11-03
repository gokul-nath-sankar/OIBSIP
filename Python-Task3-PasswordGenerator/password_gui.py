import tkinter as tk
from tkinter import ttk, messagebox
import secrets
import string
import pyperclip
from collections import deque

AMBIGUOUS_CHARS = set("0Ool1I")


class PasswordGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure Password Generator")
        self.root.geometry("540x640")
        self.root.resizable(False, False)

        # In-memory session history (last 5 passwords, never written to disk)
        self.history = deque(maxlen=5)
        self.sys_random = secrets.SystemRandom()

        self.build_gui()

    # ==========================================
    # CRYPTOGRAPHIC GENERATION & STRENGTH LOGIC
    # ==========================================
    def get_character_pools(self):
        """Builds character pools based on selected checkboxes and ambiguity filter."""
        exclude_ambiguous = self.exclude_ambiguous_var.get()
        pools = {}

        if self.upper_var.get():
            chars = string.ascii_uppercase
            if exclude_ambiguous:
                chars = "".join(c for c in chars if c not in AMBIGUOUS_CHARS)
            pools["upper"] = chars

        if self.lower_var.get():
            chars = string.ascii_lowercase
            if exclude_ambiguous:
                chars = "".join(c for c in chars if c not in AMBIGUOUS_CHARS)
            pools["lower"] = chars

        if self.digits_var.get():
            chars = string.digits
            if exclude_ambiguous:
                chars = "".join(c for c in chars if c not in AMBIGUOUS_CHARS)
            pools["digits"] = chars

        if self.symbols_var.get():
            pools["symbols"] = "!@#$%^&*()-_=+[]{}|;:,.<>?/"

        return pools

    def evaluate_strength(self, length, num_types):
        """Evaluates password strength based on length and character pool diversity."""
        score = 0
        if length >= 8:
            score += 1
        if length >= 12:
            score += 1
        if length >= 16:
            score += 1
        if num_types >= 3:
            score += 1
        if num_types == 4:
            score += 1

        if score <= 2:
            return "Weak", 33, "#e74c3c"    # Red
        elif score <= 4:
            return "Medium", 66, "#f39c12"  # Orange
        else:
            return "Strong", 100, "#2ecc71" # Green

    def generate_password(self):
        # 1. Validate length (minimum 8 enforced)
        try:
            length = int(self.length_var.get())
        except ValueError:
            messagebox.showerror("Invalid Length", "Password length must be a valid integer.")
            return

        if length < 8:
            messagebox.showwarning("Minimum Length", "Password length must be at least 8 characters.")
            self.length_var.set(8)
            length = 8

        # 2. Validate character types (at least 2 types must be selected)
        pools = self.get_character_pools()
        if len(pools) < 2:
            messagebox.showwarning(
                "Selection Required",
                "Please select at least 2 character types (e.g., Uppercase + Numbers)."
            )
            return

        # 3. Guarantee at least one character from each selected category using secrets
        password_chars = [secrets.choice(pool) for pool in pools.values()]

        # 4. Fill remaining length from combined pool using secrets
        all_chars = "".join(pools.values())
        remaining_length = length - len(password_chars)
        password_chars.extend(secrets.choice(all_chars) for _ in range(remaining_length))

        # 5. Cryptographically shuffle so guaranteed characters aren't predictably at the start
        self.sys_random.shuffle(password_chars)
        password = "".join(password_chars)

        # 6. Update GUI display
        self.password_var.set(password)
        self.update_strength_indicator(length, len(pools))

        # 7. Auto-copy to clipboard via pyperclip
        self.copy_to_clipboard(auto=True)

        # 8. Update in-memory session history (last 5)
        self.history.appendleft(password)
        self.refresh_history_listbox()

    def copy_to_clipboard(self, auto=False):
        password = self.password_var.get()
        if not password or password == "Click Generate":
            if not auto:
                messagebox.showinfo("Clipboard", "Generate a password first before copying.")
            return

        try:
            pyperclip.copy(password)
            self.status_label.config(
                text="✓ Automatically copied to clipboard!" if auto else "✓ Copied to clipboard!",
                fg="#27ae60"
            )
        except Exception as e:
            self.status_label.config(text=f"Clipboard unavailable: {e}", fg="#e74c3c")

    # ==========================================
    # GUI LAYOUT & WIDGET SYNCHRONIZATION
    # ==========================================
    def build_gui(self):
        main_frame = tk.Frame(self.root, padx=25, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            main_frame, text="Cryptographic Password Generator", font=("Segoe UI", 15, "bold")
        ).pack(anchor="w", pady=(0, 15))

        # Output Display Box + Copy Button
        display_frame = tk.Frame(main_frame)
        display_frame.pack(fill=tk.X, pady=(0, 5))

        self.password_var = tk.StringVar(value="Click Generate")
        pwd_entry = tk.Entry(
            display_frame, textvariable=self.password_var, font=("Consolas", 13, "bold"),
            state="readonly", justify="center", bd=2, relief=tk.GROOVE
        )
        pwd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 8))

        copy_btn = tk.Button(
            display_frame, text="Copy to Clipboard", font=("Segoe UI", 9, "bold"),
            bg="#34495e", fg="white", cursor="hand2", padx=10, pady=6,
            command=lambda: self.copy_to_clipboard(auto=False)
        )
        copy_btn.pack(side=tk.RIGHT)

        self.status_label = tk.Label(main_frame, text="", font=("Segoe UI", 9))
        self.status_label.pack(anchor="w", pady=(0, 10))

        # Length Control (Slider + Spinbox synced)
        length_frame = tk.LabelFrame(main_frame, text="Password Length (Min: 8)", font=("Segoe UI", 10, "bold"), padx=12, pady=10)
        length_frame.pack(fill=tk.X, pady=(0, 12))

        self.length_var = tk.IntVar(value=16)

        slider = tk.Scale(
            length_frame, from_=8, to=64, orient=tk.HORIZONTAL,
            variable=self.length_var, showvalue=False
        )
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))

        spinbox = tk.Spinbox(
            length_frame, from_=8, to=64, textvariable=self.length_var,
            width=5, font=("Segoe UI", 11, "bold"), justify="center"
        )
        spinbox.pack(side=tk.RIGHT)

        # Character Types Checkboxes
        opts_frame = tk.LabelFrame(main_frame, text="Character Types (Select at least 2)", font=("Segoe UI", 10, "bold"), padx=12, pady=10)
        opts_frame.pack(fill=tk.X, pady=(0, 12))

        self.upper_var = tk.BooleanVar(value=True)
        self.lower_var = tk.BooleanVar(value=True)
        self.digits_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=True)
        self.exclude_ambiguous_var = tk.BooleanVar(value=False)

        tk.Checkbutton(opts_frame, text="Uppercase Letters (A–Z)", variable=self.upper_var, font=("Segoe UI", 10)).pack(anchor="w")
        tk.Checkbutton(opts_frame, text="Lowercase Letters (a–z)", variable=self.lower_var, font=("Segoe UI", 10)).pack(anchor="w")
        tk.Checkbutton(opts_frame, text="Numbers (0–9)", variable=self.digits_var, font=("Segoe UI", 10)).pack(anchor="w")
        tk.Checkbutton(opts_frame, text="Symbols (!@#$%^&*...)", variable=self.symbols_var, font=("Segoe UI", 10)).pack(anchor="w")

        ttk.Separator(opts_frame, orient="horizontal").pack(fill=tk.X, pady=6)
        tk.Checkbutton(
            opts_frame, text="Exclude Ambiguous Characters (0, O, o, l, 1, I)",
            variable=self.exclude_ambiguous_var, font=("Segoe UI", 10, "italic")
        ).pack(anchor="w")

        # Password Strength Indicator (Visual Bar + Label)
        strength_frame = tk.Frame(main_frame)
        strength_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(strength_frame, text="Password Strength:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.strength_label = tk.Label(strength_frame, text="--", font=("Segoe UI", 10, "bold"))
        self.strength_label.pack(side=tk.RIGHT)

        self.strength_canvas = tk.Canvas(main_frame, height=12, bg="#ecf0f1", highlightthickness=0)
        self.strength_canvas.pack(fill=tk.X, pady=(0, 15))
        self.strength_bar = self.strength_canvas.create_rectangle(0, 0, 0, 12, fill="#bdc3c7", width=0)

        # Generate Button
        gen_btn = tk.Button(
            main_frame, text="Generate Secure Password", font=("Segoe UI", 11, "bold"),
            bg="#2c3e50", fg="white", activebackground="#1a252f", activeforeground="white",
            cursor="hand2", pady=8, command=self.generate_password
        )
        gen_btn.pack(fill=tk.X, pady=(0, 15))

        # Session History (Last 5 Passwords - In-Memory Only)
        hist_frame = tk.LabelFrame(
            main_frame, text="Session History (Last 5 — Double-click to copy)",
            font=("Segoe UI", 9, "bold"), padx=10, pady=8
        )
        hist_frame.pack(fill=tk.BOTH, expand=True)

        self.history_listbox = tk.Listbox(hist_frame, font=("Consolas", 10), height=5, activestyle="none")
        self.history_listbox.pack(fill=tk.BOTH, expand=True)
        self.history_listbox.bind("<Double-Button-1>", self.copy_from_history)

    def update_strength_indicator(self, length, num_types):
        label, pct, color = self.evaluate_strength(length, num_types)
        self.strength_label.config(text=label, fg=color)
        self.root.update_idletasks()
        canvas_width = self.strength_canvas.winfo_width()
        fill_width = int((pct / 100) * canvas_width)
        self.strength_canvas.coords(self.strength_bar, 0, 0, fill_width, 12)
        self.strength_canvas.itemconfig(self.strength_bar, fill=color)

    def refresh_history_listbox(self):
        self.history_listbox.delete(0, tk.END)
        for idx, pwd in enumerate(self.history, start=1):
            self.history_listbox.insert(tk.END, f"{idx}. {pwd}")

    def copy_from_history(self, event):
        selection = self.history_listbox.curselection()
        if selection:
            idx = selection[0]
            pwd = self.history[idx]
            pyperclip.copy(pwd)
            self.status_label.config(text=f"✓ Copied history item #{idx + 1} to clipboard!", fg="#2980b9")


if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordGeneratorApp(root)
    root.mainloop()