import socket
import threading
import datetime

HOST = "127.0.0.1"
PORT = 55556
clients = {}  # sock -> username


def broadcast(message, exclude_sock=None):
    for sock in list(clients.keys()):
        if sock != exclude_sock:
            try:
                sock.sendall(message.encode("utf-8"))
            except Exception:
                sock.close()
                clients.pop(sock, None)


def handle_client(sock):
    try:
        username = sock.recv(1024).decode("utf-8").strip()
        clients[sock] = username
        now = datetime.datetime.now().strftime("%H:%M")
        print(f"[{now}] {username} connected.")
        broadcast(f"[{now}] System: {username} has joined the chat!", exclude_sock=sock)

        while True:
            msg = sock.recv(1024).decode("utf-8")
            if not msg:
                break
            now = datetime.datetime.now().strftime("%H:%M")
            formatted = f"[{now}] {username}: {msg}"
            print(formatted)
            broadcast(formatted, exclude_sock=sock)
    except Exception:
        pass
    finally:
        user = clients.pop(sock, "A user")
        sock.close()
        now = datetime.datetime.now().strftime("%H:%M")
        disconnect_notice = f"[{now}] System: {user} has disconnected."
        print(disconnect_notice)
        broadcast(disconnect_notice)


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(2)
    print(f"CLI Chat Server running on {HOST}:{PORT}...")
    while True:
        client_sock, _ = server.accept()
        threading.Thread(target=handle_client, args=(client_sock,), daemon=True).start()


if __name__ == "__main__":
    main()