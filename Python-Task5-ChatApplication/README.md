# Real-Time Python Socket Chat Application (Beginner + Advanced Tier)

A multi-room real-time chat system built using Python TCP sockets, multi-threading, `tkinter`, and `sqlite3`.

## Security Transparency & Data Storage Disclosure (End-to-End Awareness)
In accordance with security transparency best practices, below is an explicit breakdown of how user credentials, network traffic, and chat messages are handled and what is **not** encrypted:

1. **Password Storage (Hashed at Rest):**
   - User passwords are never stored in plaintext. Upon registration, passwords are hashed using `hashlib.sha256` before being written to the `users` table in `chat_server.db`.
2. **Message Storage (Plaintext at Rest):**
   - To enable persistent room history when users join or switch rooms, chat messages, sender usernames, room names, and timestamps (`[HH:MM]`) are stored in **unencrypted plaintext** inside the local SQLite database (`chat_server.db` -> `messages` table). Anyone with file-system access to the server machine can read historical messages.
3. **Network Transport (Unencrypted TCP Sockets):**
   - Client-server communication uses standard raw TCP sockets (`socket.AF_INET`, `socket.SOCK_STREAM`) with newline-delimited JSON payloads over `localhost` (`127.0.0.1:55555`).
   - Traffic is **not** wrapped in TLS/SSL (`ssl.wrap_socket`) and **does not** implement End-to-End Encryption (E2EE). In a production deployment over a public network, packets could be intercepted via packet sniffing (e.g., Wireshark) unless upgraded to TLS sockets and client-side cryptographic key exchange.