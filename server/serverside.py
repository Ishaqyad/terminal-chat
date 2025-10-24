import threading
import sys
import json
import os
from socket import *

HOST = ""
USER_DB_FILE = os.path.join(os.path.dirname(__file__), "users.db")

active_lock = threading.Lock()
active_clients = {}

users_lock = threading.Lock()

def load_users():
    users = {}
    if not os.path.exists(USER_DB_FILE):
        return users
    with open(USER_DB_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if ":" in line:
                u, p = line.split(":", 1)
                users[u] = p
    return users

def save_user(username, password):
    with users_lock:
        users = load_users()
        users[username] = password
        with open(USER_DB_FILE, "w", encoding="utf-8") as f:
            for u, p in users.items():
                f.write(f"{u}:{p}\n")

def send_json(sock, obj):
    try:
        data = json.dumps(obj).encode("utf-8") + b"\n"
        sock.sendall(data)
    except:
        pass

def broadcast_users():
    with active_lock:
        msg = {"type": "active_users", "users": list(active_clients.keys())}
        for info in active_clients.values():
            send_json(info["sock"], msg)

def broadcast_pm(sender, text): #Broadcast public message
    with active_lock:
        for name, info in active_clients.items():
            if name != sender:
                send_json(info["sock"], {
                    "type": "broadcast",
                    "from": sender,
                    "message": text
                })

def send_dm(sender, target, text):
    with active_lock:
        if target not in active_clients:
            return False
        send_json(active_clients[target]["sock"], {
            "type": "direct",
            "from": sender,
            "message": text
        })
    return True

def handle_login(sock_file, sock):
    line = sock_file.readline()
    if not line:
        return None
    try:
        msg = json.loads(line.strip())
    except:
        return None
    if msg.get("command") != "login":
        return None

    username = msg.get("username")
    password = msg.get("password")
    if not username or not password:
        send_json(sock, {"type": "login_result", "success": False, "message": "Missing credentials"})
        return None

    with users_lock:
        users = load_users()
        if username in users and users[username] != password:
            send_json(sock, {"type": "login_result", "success": False, "message": "Invalid password"})
            return None
        elif username not in users:
            save_user(username, password)

    send_json(sock, {"type": "login_result", "success": True, "message": f"Welcome {username}"})
    return username

def handle_client(sock, addr): # Handle communication with a single person
    file = sock.makefile("r")
    user = handle_login(file, sock)
    if not user:
        sock.close()
        return

    with active_lock:
        active_clients[user] = {"sock": sock, "addr": addr}
    broadcast_users()

    try:
        while True:
            line = file.readline()
            if not line:
                break
            try:
                msg = json.loads(line.strip())
            except:
                send_json(sock, {"type": "error", "message": "Invalid JSON"})
                continue

            cmd = msg.get("command")
            if cmd == "pm":
                broadcast_pm(user, msg.get("message", ""))
            elif cmd == "dm":
                to = msg.get("to", "")
                text = msg.get("message", "")
                if not send_dm(user, to, text):
                    send_json(sock, {"type": "error", "message": "User not found"})
                else:
                    send_json(sock, {"type": "info", "message": "DM delivered"})
            elif cmd == "exit":
                break
            else:
                send_json(sock, {"type": "error", "message": "Unknown command"})
    finally:
        with active_lock:
            if user in active_clients:
                del active_clients[user]
        broadcast_users()
        sock.close()

def run_server(port): # Start main server loop to accept and manage clients
    s = socket(AF_INET, SOCK_STREAM)
    s.bind((HOST, port))
    s.listen(100)
    print(f"Server listening on port {port}")
    while True:
        client, addr = s.accept()
        t = threading.Thread(target=handle_client, args=(client, addr), daemon=True)
        t.start()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python server.py <port>")
        sys.exit(1)
    port = int(sys.argv[1])
    run_server(port)
