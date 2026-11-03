import tkinter as tk
from tkinter import simpledialog, messagebox
import socket
import threading
import json

HOST = "127.0.0.1"
PORT = 55555

EMOJI_SHORTCODES = {
    ":smile:": "😄",
    ":grin:": "😁",
    ":laugh:": "😂",
    ":wink:": "😉",
    ":heart:": "❤️",
    ":thumbsup:": "👍",
    ":thumbsdown:": "👎",
    ":fire:": "🔥",
    ":rocket:": "🚀",
    ":star:": "⭐",
    ":check:": "✅",
    ":wave:": "👋",
    ":sad:": "😢",
    ":cool:": "😎",
    ":party:": "🎉"
}


def render_emojis(text):
    """Replaces common emoji shortcodes with Unicode characters."""
    for code, char in EMOJI_SHORTCODES.items():
        text = text.replace(code, char)
    return text


class ChatClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Real-Time Chat")
        self.root.geometry("780x560")
        self.root.configure(bg="#ecf0f1")

        self.sock = None
        self.username = None
        self.current_room = "General"
        self.is_focused = True
        self.unread_count = 0

        # Track window focus for background message notifications
        self.root.bind("<FocusIn>", self.on_focus_in)
        self.root.bind("<FocusOut>", self.on_focus_out)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.connect_to_server()
        self.build_login_screen()

    # ==========================================
    # NETWORK CONNECTION & LISTENER
    # ==========================================
    def connect_to_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            threading.Thread(target=self.receive_loop, daemon=True).start()
        except Exception as e:
            messagebox.showerror(
                "Connection Error",
                f"Could not connect to server at {HOST}:{PORT}.\nMake sure chat_server.py is running first.\n\n({e})"
            )
            self.root.destroy()

    def send_json(self, payload):
        if not self.sock:
            return
        try:
            data = json.dumps(payload) + "\n"
            self.sock.sendall(data.encode("utf-8"))
        except Exception:
            messagebox.showerror("Disconnected", "Lost connection to the chat server.")

    def receive_loop(self):
        buffer = ""
        try:
            while True:
                chunk = self.sock.recv(4096).decode("utf-8")
                if not chunk:
                    break
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        packet = json.loads(line)
                        self.root.after(0, self.handle_server_packet, packet)
        except Exception:
            pass

    # ==========================================
    # FOCUS & NOTIFICATION HANDLING
    # ==========================================
    def on_focus_in(self, event):
        self.is_focused = True
        if self.unread_count > 0 and self.username:
            self.unread_count = 0
            self.root.title(f"Chat — {self.username} (#{self.current_room})")
            if hasattr(self, "notif_banner"):
                self.notif_banner.pack_forget()

    def on_focus_out(self, event):
        self.is_focused = False

    def trigger_unfocused_notification(self, sender, text):
        if not self.is_focused and sender != self.username:
            self.unread_count += 1
            self.root.bell()  # Audible system alert
            self.root.title(f"({self.unread_count} New!) Chat — {self.username}")
            self.notif_banner.config(text=f"🔔 New message from {sender}: {text[:40]}")
            self.notif_banner.pack(fill=tk.X, side=tk.TOP)

    # ==========================================
    # LOGIN / REGISTRATION VIEW
    # ==========================================
    def build_login_screen(self):
        self.login_frame = tk.Frame(self.root, bg="white", bd=1, relief=tk.SOLID, padx=35, pady=35)
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(self.login_frame, text="Chat Login / Register", font=("Segoe UI", 16, "bold"), bg="white", fg="#2c3e50").pack(pady=(0, 20))

        tk.Label(self.login_frame, text="Username:", font=("Segoe UI", 10, "bold"), bg="white").pack(anchor="w")
        self.user_entry = tk.Entry(self.login_frame, font=("Segoe UI", 11), width=26)
        self.user_entry.pack(pady=(2, 12), ipady=3)

        tk.Label(self.login_frame, text="Password:", font=("Segoe UI", 10, "bold"), bg="white").pack(anchor="w")
        self.pass_entry = tk.Entry(self.login_frame, font=("Segoe UI", 11), width=26, show="*")
        self.pass_entry.pack(pady=(2, 18), ipady=3)

        btn_row = tk.Frame(self.login_frame, bg="white")
        btn_row.pack(fill=tk.X)

        tk.Button(
            btn_row, text="Login", font=("Segoe UI", 10, "bold"), bg="#2980b9", fg="white",
            width=11, pady=5, cursor="hand2", command=lambda: self.submit_auth("login")
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            btn_row, text="Register", font=("Segoe UI", 10, "bold"), bg="#27ae60", fg="white",
            width=11, pady=5, cursor="hand2", command=lambda: self.submit_auth("register")
        ).pack(side=tk.RIGHT)

        self.auth_status = tk.Label(self.login_frame, text="", font=("Segoe UI", 9), bg="white", fg="#e74c3c")
        self.auth_status.pack(pady=(12, 0))

    def submit_auth(self, mode):
        u = self.user_entry.get().strip()
        p = self.pass_entry.get().strip()
        if not u or not p:
            self.auth_status.config(text="Please enter both username and password.")
            return
        self.send_json({"action": mode, "username": u, "password": p})

    # ==========================================
    # MAIN CHAT VIEW
    # ==========================================
    def build_chat_screen(self, rooms, history):
        self.login_frame.destroy()
        self.root.title(f"Chat — {self.username} (#{self.current_room})")

        # Unfocused Notification Banner
        self.notif_banner = tk.Label(
            self.root, text="", bg="#f39c12", fg="white", font=("Segoe UI", 10, "bold"), pady=5
        )

        # Left Sidebar: Rooms
        sidebar = tk.Frame(self.root, bg="#2c3e50", width=200, padx=12, pady=15)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text=f"👤 {self.username}", font=("Segoe UI", 12, "bold"), bg="#2c3e50", fg="#ecf0f1").pack(anchor="w", pady=(0, 15))
        tk.Label(sidebar, text="CHAT ROOMS", font=("Segoe UI", 9, "bold"), bg="#2c3e50", fg="#95a5a6").pack(anchor="w", pady=(0, 5))

        self.room_listbox = tk.Listbox(
            sidebar, font=("Segoe UI", 11), bg="#34495e", fg="white",
            selectbackground="#1abc9c", bd=0, highlightthickness=0, activestyle="none"
        )
        self.room_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.room_listbox.bind("<<ListboxSelect>>", self.on_room_select)

        tk.Button(
            sidebar, text="+ Create / Join Room", font=("Segoe UI", 9, "bold"),
            bg="#1abc9c", fg="white", bd=0, pady=6, cursor="hand2", command=self.prompt_new_room
        ).pack(fill=tk.X)

        # Right Area: Messages & Input
        chat_area = tk.Frame(self.root, bg="white", padx=15, pady=15)
        chat_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.room_header = tk.Label(
            chat_area, text=f"#{self.current_room}", font=("Segoe UI", 14, "bold"), bg="white", fg="#2c3e50"
        )
        self.room_header.pack(anchor="w", pady=(0, 8))

        self.chat_text = tk.Text(
            chat_area, font=("Segoe UI", 10), state="disabled", wrap="word",
            bg="#f8f9fa", bd=1, relief=tk.SOLID, padx=10, pady=10
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.chat_text.tag_config("system", foreground="#7f8c8d", font=("Segoe UI", 9, "italic"))
        self.chat_text.tag_config("self", foreground="#2980b9", font=("Segoe UI", 10, "bold"))
        self.chat_text.tag_config("other", foreground="#2c3e50", font=("Segoe UI", 10, "bold"))

        # Emoji helper hint
        tk.Label(
            chat_area,
            text="Shortcodes: :smile: 😄  :laugh: 😂  :heart: ❤️  :thumbsup: 👍  :fire: 🔥  :rocket: 🚀  :party: 🎉",
            font=("Segoe UI", 8), bg="white", fg="#7f8c8d"
        ).pack(anchor="w", pady=(0, 4))

        # Message Entry Row
        input_row = tk.Frame(chat_area, bg="white")
        input_row.pack(fill=tk.X)

        self.msg_entry = tk.Entry(input_row, font=("Segoe UI", 11), bd=1, relief=tk.SOLID)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 8))
        self.msg_entry.bind("<Return>", lambda e: self.send_chat_message())

        tk.Button(
            input_row, text="Send", font=("Segoe UI", 10, "bold"),
            bg="#2980b9", fg="white", padx=18, pady=5, cursor="hand2", command=self.send_chat_message
        ).pack(side=tk.RIGHT)

        self.update_room_listbox(rooms)
        self.load_history_into_view(history)

    # ==========================================
    # ROOM & MESSAGE OPERATIONS
    # ==========================================
    def update_room_listbox(self, rooms):
        self.room_listbox.delete(0, tk.END)
        for idx, r in enumerate(rooms):
            self.room_listbox.insert(tk.END, f"# {r}")
            if r == self.current_room:
                self.room_listbox.selection_set(idx)

    def on_room_select(self, event):
        sel = self.room_listbox.curselection()
        if not sel:
            return
        room_name = self.room_listbox.get(sel[0]).replace("# ", "").strip()
        if room_name != self.current_room:
            self.send_json({"action": "join_room", "room": room_name})

    def prompt_new_room(self):
        new_room = simpledialog.askstring("Create or Join Room", "Enter room name:")
        if new_room and new_room.strip():
            clean_name = new_room.strip().lstrip("#")
            self.send_json({"action": "join_room", "room": clean_name})

    def load_history_into_view(self, history):
        self.chat_text.config(state="normal")
        self.chat_text.delete("1.0", tk.END)
        self.chat_text.insert(tk.END, f"--- Loaded message history for #{self.current_room} ---\n", "system")
        for item in history:
            self.append_chat_line(item["timestamp"], item["sender"], item["content"])
        self.chat_text.config(state="disabled")
        self.chat_text.see(tk.END)

    def append_chat_line(self, timestamp, sender, content):
        formatted = render_emojis(content)
        self.chat_text.config(state="normal")
        tag = "self" if sender == self.username else "other"
        self.chat_text.insert(tk.END, f"[{timestamp}] {sender}: ", tag)
        self.chat_text.insert(tk.END, f"{formatted}\n")
        self.chat_text.config(state="disabled")
        self.chat_text.see(tk.END)

    def append_system_line(self, timestamp, content):
        self.chat_text.config(state="normal")
        self.chat_text.insert(tk.END, f"[{timestamp}] * {content}\n", "system")
        self.chat_text.config(state="disabled")
        self.chat_text.see(tk.END)

    def send_chat_message(self):
        raw = self.msg_entry.get().strip()
        if not raw:
            return
        self.msg_entry.delete(0, tk.END)
        self.send_json({"action": "message", "content": raw})

    def handle_server_packet(self, packet):
        ptype = packet.get("type")

        if ptype == "auth_response":
            if packet.get("success"):
                self.username = packet["username"]
                self.current_room = packet["room"]
                self.build_chat_screen(packet["rooms"], packet["history"])
            else:
                self.auth_status.config(text=packet.get("message", "Authentication failed."))

        elif ptype == "room_list":
            if hasattr(self, "room_listbox"):
                self.update_room_listbox(packet["rooms"])

        elif ptype == "room_joined":
            self.current_room = packet["room"]
            self.room_header.config(text=f"#{self.current_room}")
            self.root.title(f"Chat — {self.username} (#{self.current_room})")
            self.load_history_into_view(packet["history"])

        elif ptype == "chat":
            if packet.get("room") == self.current_room:
                self.append_chat_line(packet["timestamp"], packet["sender"], packet["content"])
                self.trigger_unfocused_notification(packet["sender"], render_emojis(packet["content"]))

        elif ptype == "system":
            self.append_system_line(packet["timestamp"], packet["content"])

    def on_close(self):
        try:
            if self.sock:
                self.sock.close()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClientGUI(root)
    root.mainloop()