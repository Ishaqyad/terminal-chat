import threading
import sys
import json
from socket import *

def send_json_line(sock, obj):
    data = json.dumps(obj).encode("utf-8") + b"\n"
    sock.sendall(data)

def recv_json_line(sock_file):
    line = sock_file.readline()
    if not line:
        return None
    return json.loads(line.strip())

def do_login(sock, sock_file, username, password):      # Handles sending login credentials and receiving server response
    login_msg = {
        "type": "command",
        "command": "login",
        "username": username,
        "password": password
    }
    send_json_line(sock, login_msg)
    reply = recv_json_line(sock_file)
    if reply is None:
        print("No login response.")
        return False
    if reply.get("type") == "login_result" and reply.get("success") is True:
        print(f"[LOGIN OK] {reply.get('message','')}")
        return True
    print(f"[LOGIN FAILED] {reply}")
    return False

def receive_messages(sock, sock_file, stop_event):
    while not stop_event.is_set():
        try:
            msg = recv_json_line(sock_file)
            if msg is None:
                print("Server connection lost.")
                stop_event.set()
                break

            mtype = msg.get("type", "")

            if mtype == "broadcast":
                print(f"[ALL][{msg.get('from','?')}] {msg.get('message','')}")
            elif mtype == "direct":
                print(f"[DM from {msg.get('from','?')}] {msg.get('message','')}")
            elif mtype == "active_users":
                print(f"[ACTIVE USERS] {msg.get('users',[])}")
            elif mtype == "info":
                print(f"[INFO] {msg.get('message','')}")
            elif mtype == "error":
                print(f"[ERROR] {msg.get('message','')}")
            elif mtype == "login_result":
                print(f"[LOGIN] {msg.get('message','')}")
            else:
                print(f"[SERVER RAW] {msg}")

        except ConnectionError:
            print("Receive: connection error.")
            stop_event.set()
            break
        except Exception:
            print("Receive: unexpected error.")
            stop_event.set()
            break

def send_messages(sock, stop_event):            # listening for incomingmessages from the server and reads user commands. 
    while not stop_event.is_set():
        cmd = input("Enter command (PM / DM / EX): ").strip().upper()           

        if cmd == "PM":
            text = input("Message to everyone: ").strip()           # Three Operations
            out = {
                "type": "command",
                "command": "pm",
                "message": text
            }
            try:
                send_json_line(sock, out)
            except ConnectionError:
                print("Failed to send PM.")
                stop_event.set()
                break

        elif cmd == "DM":
            target = input("Send to who?: ").strip()
            text = input("Message: ").strip()
            out = {
                "type": "command",
                "command": "dm",
                "to": target,
                "message": text
            }
            try:
                send_json_line(sock, out)
            except ConnectionError:
                print("Failed to send DM.")
                stop_event.set()
                break

        elif cmd == "EX":
            out = {
                "type": "command",
                "command": "exit"
            }
            try:
                send_json_line(sock, out)
            except ConnectionError:
                pass
            stop_event.set()
            break

        else:
            print("Invalid command. Use PM / DM / EX.")

def run_client(server_name, server_port, username, password):
    client_sock = socket(AF_INET, SOCK_STREAM)
    client_sock.connect((server_name, server_port))
    sock_file = client_sock.makefile("r")

    ok = do_login(client_sock, sock_file, username, password)
    if not ok:
        client_sock.close()
        return

    stop_event = threading.Event()

    receive_thread = threading.Thread(
        target=receive_messages,
        args=(client_sock, sock_file, stop_event),
        daemon=True
    )

    send_thread = threading.Thread(
        target=send_messages,
        args=(client_sock, stop_event),
        daemon=True
    )

    receive_thread.start()
    send_thread.start()

    send_thread.join()
    stop_event.set()
    client_sock.close()

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Usage: python client.py <server_ip> <server_port> <username> <password>")
        sys.exit(1)

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    username = sys.argv[3]
    password = sys.argv[4]

    run_client(server_ip, server_port, username, password)
