import socket
import threading
import datetime
import sys

HOST = "127.0.0.1"
PORT = 55556


def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(1024).decode("utf-8")
            if not msg:
                print("\nDisconnected from server.")
                sys.exit(0)
            print(f"\r{msg}\n> ", end="", flush=True)
        except Exception:
            break


def main():
    username = input("Enter your username: ").strip() or "User"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.sendall(username.encode("utf-8"))

    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()
    print("Connected! Type messages below (or 'quit' to exit):")

    try:
        while True:
            msg = input("> ").strip()
            if msg.lower() == "quit":
                break
            if msg:
                now = datetime.datetime.now().strftime("%H:%M")
                print(f"[{now}] {username} (You): {msg}")
                sock.sendall(msg.encode("utf-8"))
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()


if __name__ == "__main__":
    main()