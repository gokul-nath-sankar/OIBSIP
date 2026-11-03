
# Task 3: Cryptographic Random Password Generator (Beginner + Advanced Tier)

A secure password generation utility in Python featuring custom complexity rules, strength evaluation, and automatic clipboard integration.

## Features
- **Beginner CLI (`password_cli.py`):** Interactive command-line generator enforcing minimum length and character diversity.
- **Cryptographically Secure GUI (`password_gui.py`):** Built with `tkinter` and Python's `secrets` module (`secrets.choice` and `secrets.SystemRandom`).
- **Guaranteed Complexity:** Enforces a minimum length of 8 and guarantees at least one character from every selected character pool (Uppercase, Lowercase, Digits, Symbols).
- **Ambiguous Character Filter:** Option to exclude visually similar characters (`0, O, o, l, 1, I`).
- **Clipboard & Session History:** Automatically copies generated passwords via `pyperclip` and maintains an in-memory session history of the last 5 passwords.

## How to Run
```bash
python password_gui.py