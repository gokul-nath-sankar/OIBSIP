# Python NLP Voice Assistant (Beginner + Advanced Tier)

A modular voice assistant built in Python capable of natural language intent recognition, live weather reporting, threaded reminders, automated email dispatch, general knowledge retrieval, and dynamic custom commands.

## Features Implemented
### Beginner Tier
- **Microphone Capture:** Real-time ambient noise adjustment and speech capture via `SpeechRecognition`.
- **Conversational Greeting:** Responds naturally to greetings.
- **Time & Date Reporting:** Announces current local time and formatted calendar date.
- **Web Search Integration:** Launches default system browser with user-specified search queries.
- **Graceful Error Handling:** Prompts the user to repeat commands on timeout or unintelligible audio.
- **Text-to-Speech (TTS):** Offline voice synthesis powered by `pyttsx3`.

### Advanced Tier
- **Natural Language Understanding (NLU):** Uses `nltk` lemmatization and `scikit-learn` TF-IDF vectorization with Cosine Similarity to classify free-form spoken sentences into intents without relying on rigid keyword matching.
- **Voice Email Dispatch:** Sends emails via `smtplib` over SSL (`smtp.gmail.com`).
- **Non-Blocking Timed Reminders:** Uses Python `threading` to run countdown timers in the background and trigger audible TTS alerts.
- **Live Weather Integration:** Queries the OpenWeatherMap REST API for real-time temperature and weather conditions.
- **General Knowledge QA:** Answers factual "Who is / What is" questions using the Wikipedia API.
- **Custom Command Engine:** Supports loading custom triggers from `custom_commands.json` and adding new voice commands dynamically at runtime.

## Privacy & Data Processing Statement
To ensure transparency and user privacy, below is how data is handled by this application:
1. **Voice Audio Data:** Microphone audio is captured locally in memory buffers and transmitted to the Google Speech Recognition API solely for real-time speech-to-text transcription. Audio buffers are immediately discarded from local RAM after transcription and are never written to disk.
2. **Natural Language Processing & TTS:** All intent classification (`NLTK` / `scikit-learn`) and speech synthesis (`pyttsx3`) execute **100% locally** on your machine.
3. **Third-Party API Requests:**
   - **Weather Queries:** Only the extracted city name is sent to the OpenWeatherMap API.
   - **Knowledge Queries:** Only the search topic is sent to the Wikipedia API.
   - **Email Dispatch:** Email content and recipient addresses are transmitted over encrypted TLS/SSL (`smtplib.SMTP_SSL`) directly to the configured SMTP server. Credentials should be stored in environment variables (`OPENWEATHER_API_KEY`, `EMAIL_ADDRESS`, `EMAIL_PASSWORD`) rather than hardcoded.
4. **Local Storage:** Only user-defined custom commands are stored locally in `custom_commands.json`. No conversation logs or personal telemetry are saved.