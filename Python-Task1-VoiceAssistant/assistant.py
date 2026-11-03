import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import smtplib
from email.message import EmailMessage
import requests
import json
import os
import threading
import time
import re
import wikipedia
wikipedia.set_user_agent("OIBSIP_VoiceAssistant/1.0 (https://github.com/diwakar/OIBSIP)")
import nltk
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Ensure necessary NLTK packages are available quietly
for pkg in ['punkt', 'punkt_tab', 'wordnet']:
    nltk.download(pkg, quiet=True)

# ==========================================
# CONFIGURATION (Update with your credentials)
# ==========================================
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "YOUR_OPENWEATHER_API_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "your_test_email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your_app_password")  # Gmail App Password
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOM_CMD_FILE = os.path.join(BASE_DIR, "custom_commands.json")

# ==========================================
# NLP INTENT CLASSIFIER (Advanced Tier)
# ==========================================
class IntentClassifier:
    """Parses user intent from free-form sentences using TF-IDF & Cosine Similarity."""
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.intents = {
            "greeting": [
                "hello", "hi there", "hey assistant", "good morning", "good evening", "greetings"
            ],
            "time": [
                "what time is it", "tell me the current time", "current time please", "clock"
            ],
            "date": [
                "what is today's date", "tell me the date", "what day is it today", "current date"
            ],
            "search": [
                "search the web for", "google something for me", "look up on the internet", "find online"
            ],
            "weather": [
                "what is the weather like", "temperature outside", "weather forecast", "is it raining in"
            ],
            "email": [
                "send an email", "write a mail to someone", "compose an email", "send a message via email"
            ],
            "reminder": [
                "set a reminder", "remind me in a few minutes", "set a timer", "alert me after"
            ],
            "knowledge": [
                "who is", "what is", "tell me about", "explain", "general knowledge question"
            ],
            "add_command": [
                "add a custom command", "create a new voice command", "teach you a new command"
            ],
            "exit": [
                "goodbye", "exit program", "stop listening", "shut down", "quit"
            ]
        }
        self._build_model()

    def _preprocess(self, text):
        tokens = nltk.word_tokenize(text.lower())
        return " ".join([self.lemmatizer.lemmatize(t) for t in tokens if t.isalnum()])

    def _build_model(self):
        self.corpus = []
        self.labels = []
        for intent, phrases in self.intents.items():
            for phrase in phrases:
                self.corpus.append(self._preprocess(phrase))
                self.labels.append(intent)
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus)

    def predict(self, user_input, threshold=0.35):
        processed = self._preprocess(user_input)
        if not processed:
            return "unknown"
        user_vec = self.vectorizer.transform([processed])
        similarities = cosine_similarity(user_vec, self.tfidf_matrix).flatten()
        best_idx = similarities.argmax()
        if similarities[best_idx] >= threshold:
            return self.labels[best_idx]
        return "unknown"


# ==========================================
# MAIN VOICE ASSISTANT
# ==========================================
class VoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.tts_lock = threading.Lock()
        self.classifier = IntentClassifier()
        self.custom_commands = self.load_custom_commands()

    def speak(self, text):
        """Thread-safe text-to-speech output."""
        print(f"Assistant: {text}")
        with self.tts_lock:
            engine = pyttsx3.init()
            engine.setProperty('rate', 175)
            engine.say(text)
            engine.runAndWait()

    def listen(self, prompt=None):
        """Captures microphone audio and converts it to lowercase text."""
        if prompt:
            self.speak(prompt)
        with sr.Microphone() as source:
            print("\n[Listening...]")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=6, phrase_time_limit=10)
                print("[Processing audio...]")
                query = self.recognizer.recognize_google(audio)
                print(f"User: {query}")
                return query.lower()
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                self.speak("I didn't catch that. Could you please repeat?")
                return None
            except sr.RequestError:
                self.speak("Speech recognition service is currently unavailable.")
                return None

    # --- Custom Commands Management ---
    def load_custom_commands(self):
        default_commands = {
            "open github": {
                "type": "url",
                "target": "https://github.com"
            },
            "open youtube": {
                "type": "url",
                "target": "https://youtube.com"
            },
            "who created you": {
                "type": "speech",
                "target": "I was built in Python by Diwakar as part of the Oasis Infobyte internship."
            }
        }
        if os.path.exists(CUSTOM_CMD_FILE):
            try:
                with open(CUSTOM_CMD_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        with open(CUSTOM_CMD_FILE, "w") as f:
            json.dump(default_commands, f, indent=2)
        return default_commands

    def save_custom_command(self, trigger, cmd_type, target):
        self.custom_commands[trigger.lower()] = {"type": cmd_type, "target": target}
        with open(CUSTOM_CMD_FILE, "w") as f:
            json.dump(self.custom_commands, f, indent=2)

    # --- Feature Implementations ---
    def tell_time(self):
        now = datetime.datetime.now().strftime("%I:%M %p")
        self.speak(f"The current time is {now}.")

    def tell_date(self):
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        self.speak(f"Today's date is {today}.")

    def web_search(self, query):
        topic = re.sub(r"^(search the web for|search for|google|look up|search)\s*", "", query).strip()
        if not topic:
            topic = self.listen("What topic would you like me to search for?")
        if topic:
            self.speak(f"Opening browser to search for {topic}.")
            webbrowser.open(f"https://www.google.com/search?q={topic}")

    def get_weather(self, query):
        match = re.search(r"in ([a-zA-Z\s]+)", query)
        city = match.group(1).strip() if match else self.listen("Which city's weather would you like to check?")
        if not city:
            return

        if OPENWEATHER_API_KEY == "YOUR_OPENWEATHER_API_KEY":
            self.speak(f"Demo mode: Please add your OpenWeatherMap API key to fetch live weather for {city}.")
            return

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        try:
            res = requests.get(url, timeout=5).json()
            if res.get("cod") == 200:
                temp = res["main"]["temp"]
                desc = res["weather"][0]["description"]
                self.speak(f"The current weather in {city} is {desc} with a temperature of {temp} degrees Celsius.")
            else:
                self.speak(f"Sorry, I couldn't find weather data for {city}.")
        except Exception:
            self.speak("Failed to connect to the weather service.")

    def set_reminder(self, query):
        match = re.search(r"(\d+)\s*(second|seconds|minute|minutes)", query)
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
        else:
            resp = self.listen("In how many seconds or minutes should I remind you?")
            if not resp:
                return
            match = re.search(r"(\d+)\s*(second|seconds|minute|minutes)", resp)
            if not match:
                self.speak("Could not understand the duration.")
                return
            amount, unit = int(match.group(1)), match.group(2)

        task = self.listen("What should I remind you about?") or "your scheduled task"
        seconds = amount * 60 if "minute" in unit else amount
        self.speak(f"Reminder set for {amount} {unit} from now.")

        def trigger_alert():
            time.sleep(seconds)
            self.speak(f"Alert! Reminder: {task}")

        threading.Thread(target=trigger_alert, daemon=True).start()

    def send_email_flow(self):
        recipient = self.listen("Please type the recipient email address in the console, or say 'test' to use the default test address.")
        if recipient and "test" in recipient:
            to_email = EMAIL_ADDRESS
        else:
            to_email = input("Enter recipient email address: ").strip()

        subject = self.listen("What is the subject of the email?")
        body = self.listen("What message would you like to send?")

        if not (to_email and subject and body):
            self.speak("Email cancelled due to missing details.")
            return

        if EMAIL_ADDRESS == "your_test_email@gmail.com":
            self.speak(f"Demo mode: Email to {to_email} with subject '{subject}' was simulated successfully.")
            return

        try:
            msg = EmailMessage()
            msg.set_content(body)
            msg["Subject"] = subject
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = to_email

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.send_message(msg)
            self.speak("Your email has been sent successfully.")
        except Exception as e:
            print(f"SMTP Error: {e}")
            self.speak("Failed to send the email. Please verify your SMTP credentials.")

    def answer_knowledge(self, query):
        # Strip common question starters
        topic = re.sub(
            r"^(who is|who was|who created|what is|what are|tell me about|explain|define)\s*",
            "",
            query,
            flags=re.IGNORECASE
        ).strip()

        if not topic:
            return

        headers = {"User-Agent": "OIBSIP_VoiceAssistant/1.0 (Python; Educational Project)"}
        try:
            # Step 1: Search Wikipedia API for the closest matching article title
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": topic,
                "format": "json"
            }
            search_res = requests.get(search_url, params=search_params, headers=headers, timeout=5).json()
            search_hits = search_res.get("query", {}).get("search", [])

            if not search_hits:
                raise ValueError("No Wikipedia page found")

            best_title = search_hits[0]["title"]

            # Step 2: Fetch the clean plain-text summary for that title
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(best_title)}"
            sum_res = requests.get(summary_url, headers=headers, timeout=5).json()
            extract = sum_res.get("extract", "")

            if extract:
                # Speak the first 2 sentences cleanly
                sentences = re.split(r'(?<=[.!?])\s+', extract)
                short_answer = " ".join(sentences[:2])
                self.speak(short_answer)
            else:
                raise ValueError("Empty summary")

        except Exception as e:
            print(f"[Debug Wiki Error: {e}]")
            self.speak(f"I couldn't find a direct summary for {topic}, searching the web instead.")
            self.web_search(topic)

    def add_custom_command_flow(self):
        trigger = self.listen("What phrase should trigger the new command?")
        if not trigger:
            return
        response = self.listen("What should I say when you use that phrase?")
        if not response:
            return
        self.save_custom_command(trigger, "speech", response)
        self.speak(f"Custom command '{trigger}' has been saved.")

    # --- Main Execution Loop ---
    def run(self):
        self.speak("Voice assistant initialized. How can I help you?")
        while True:
            query = self.listen()
            if not query:
                continue

            # 1. Check user-defined custom commands first
            if query in self.custom_commands:
                cmd = self.custom_commands[query]
                if cmd["type"] == "speech":
                    self.speak(cmd["target"])
                elif cmd["type"] == "url":
                    self.speak(f"Opening {query}")
                    webbrowser.open(cmd["target"])
                continue

            # 2. Predict intent via NLP classifier (with fallback keyword checks)
            intent = self.classifier.predict(query)
            if intent == "unknown":
                if any(w in query for w in ["time", "clock"]):
                    intent = "time"
                elif any(w in query for w in ["date", "day", "today"]):
                    intent = "date"
                elif any(w in query for w in ["search", "google", "look up"]):
                    intent = "search"
                elif any(w in query for w in ["weather", "temperature", "forecast"]):
                    intent = "weather"
                elif any(w in query for w in ["remind", "timer", "alert"]):
                    intent = "reminder"
                elif any(w in query for w in ["email", "mail"]):
                    intent = "email"
                elif any(w in query for w in ["who is", "what is", "tell me about"]):
                    intent = "knowledge"

            # 3. Route to appropriate action
            if intent == "greeting":
                self.speak("Hello! Great to hear from you. What can I do for you today?")
            elif intent == "time":
                self.tell_time()
            elif intent == "date":
                self.tell_date()
            elif intent == "search":
                self.web_search(query)
            elif intent == "weather":
                self.get_weather(query)
            elif intent == "reminder":
                self.set_reminder(query)
            elif intent == "email":
                self.send_email_flow()
            elif intent == "add_command":
                self.add_custom_command_flow()
            elif intent == "knowledge":
                self.answer_knowledge(query)
            elif intent == "exit":
                self.speak("Shutting down. Goodbye!")
                break
            else:
                self.answer_knowledge(query)


if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()