import socket
import threading
import sqlite3
import hashlib
import json
import datetime

HOST = "127.0.0.1"
PORT = 55555
DB_NAME = "chat_server.db"


class ChatServer:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Maps client_socket -> {"username": str, "room": str}
        self.clients = {}
        self.rooms = {"General", "Tech", "Random"}
        self.lock = threading.Lock()
        self.db_lock = threading.Lock()

        self.init_db()

    # ==========================================
    # DATABASE LAYER (Users & Message History)
    # ==========================================
    def init_db(self):
        with self.db_lock, sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            cursor.execute("SELECT DISTINCT room FROM messages")
            for (room_name,) in cursor.fetchall():
                self.rooms.add(room_name)
            conn.commit()

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def register_user(self, username, password):
        pwd_hash = self.hash_password(password)
        with self.db_lock, sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, pwd_hash))
                conn.commit()
                return True, "Registration successful."
            except sqlite3.IntegrityError:
                return False, "Username already exists."

    def authenticate_user(self, username, password):
        pwd_hash = self.hash_password(password)
        with self.db_lock, sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row and row[0] == pwd_hash:
                return True, "Login successful."
            return False, "Invalid username or password."

    def save_message(self, room, sender, content, timestamp):
        with self.db_lock, sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (room, sender, content, timestamp)
                VALUES (?, ?, ?, ?)
            """, (room, sender, content, timestamp))
            conn.commit()

    def get_room_history(self, room, limit=50):
        with self.db_lock, sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, sender, content
                FROM messages
                WHERE room = ?
                ORDER BY id ASC
                LIMIT ?
            """, (room, limit))
            return [
                {"timestamp": r[0], "sender": r[1], "content": r[2]}
                for r in cursor.fetchall()
            ]

    # ==========================================
    # SOCKET PROTOCOL & BROADCASTING
    # ==========================================
    def send_json(self, client_socket, payload):
        try:
            data = json.dumps(payload) + "\n"
            client_socket.sendall(data.encode("utf-8"))
        except Exception:
            self.remove_client(client_socket)

    def broadcast_to_room(self, room, payload, exclude_sock=None):
        with self.lock:
            targets = [
                sock for sock, info in self.clients.items()
                if info.get("room") == room and sock != exclude_sock
            ]
        for sock in targets:
            self.send_json(sock, payload)

    def broadcast_room_list(self):
        room_list = sorted(list(self.rooms))
        with self.lock:
            targets = list(self.clients.keys())
        for sock in targets:
            self.send_json(sock, {"type": "room_list", "rooms": room_list})

    def remove_client(self, client_socket):
        with self.lock:
            info = self.clients.pop(client_socket, None)
        try:
            client_socket.close()
        except Exception:
            pass

        if info and info.get("username"):
            username = info["username"]
            room = info.get("room", "General")
            now_str = datetime.datetime.now().strftime("%H:%M")
            print(f"[{now_str}] {username} disconnected.")
            self.broadcast_to_room(room, {
                "type": "system",
                "timestamp": now_str,
                "content": f"{username} has disconnected from the chat."
            })

    # ==========================================
    # CLIENT HANDLER THREAD
    # ==========================================
    def handle_client(self, client_socket, addr):
        buffer = ""
        try:
            while True:
                chunk = client_socket.recv(4096).decode("utf-8")
                if not chunk:
                    break
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        self.process_packet(client_socket, json.loads(line))
        except Exception:
            pass
        finally:
            self.remove_client(client_socket)

    def process_packet(self, sock, packet):
        action = packet.get("action")
        now_str = datetime.datetime.now().strftime("%H:%M")

        if action in ("login", "register"):
            username = packet.get("username", "").strip()
            password = packet.get("password", "").strip()

            if not username or not password:
                self.send_json(sock, {"type": "auth_response", "success": False, "message": "Username and password required."})
                return

            if action == "register":
                ok, msg = self.register_user(username, password)
            else:
                ok, msg = self.authenticate_user(username, password)

            if ok:
                with self.lock:
                    self.clients[sock] = {"username": username, "room": "General"}
                self.send_json(sock, {
                    "type": "auth_response",
                    "success": True,
                    "username": username,
                    "room": "General",
                    "rooms": sorted(list(self.rooms)),
                    "history": self.get_room_history("General")
                })
                self.broadcast_to_room("General", {
                    "type": "system",
                    "timestamp": now_str,
                    "content": f"{username} joined #General."
                }, exclude_sock=sock)
            else:
                self.send_json(sock, {"type": "auth_response", "success": False, "message": msg})

        elif action == "join_room":
            new_room = packet.get("room", "General").strip()
            if not new_room:
                return

            with self.lock:
                info = self.clients.get(sock)
                if not info:
                    return
                old_room = info["room"]
                username = info["username"]
                info["room"] = new_room
                is_new_room = new_room not in self.rooms
                self.rooms.add(new_room)

            if is_new_room:
                self.broadcast_room_list()

            if old_room != new_room:
                self.broadcast_to_room(old_room, {
                    "type": "system",
                    "timestamp": now_str,
                    "content": f"{username} left #{old_room}."
                }, exclude_sock=sock)

            self.send_json(sock, {
                "type": "room_joined",
                "room": new_room,
                "history": self.get_room_history(new_room)
            })

            self.broadcast_to_room(new_room, {
                "type": "system",
                "timestamp": now_str,
                "content": f"{username} joined #{new_room}."
            }, exclude_sock=sock)

        elif action == "message":
            content = packet.get("content", "").strip()
            if not content:
                return
            with self.lock:
                info = self.clients.get(sock)
            if not info:
                return

            username = info["username"]
            room = info["room"]
            self.save_message(room, username, content, now_str)

            msg_payload = {
                "type": "chat",
                "room": room,
                "sender": username,
                "timestamp": now_str,
                "content": content
            }
            self.broadcast_to_room(room, msg_payload)

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"=== Chat Server listening on {self.host}:{self.port} ===")
        try:
            while True:
                client_sock, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_sock, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.server_socket.close()


if __name__ == "__main__":
    ChatServer().start()