import socket
import threading
import sqlite3
import Login
import Passwords
import time
import os
# GUI
HEADER = 64
FORMAT = 'utf-8'
connections = []
while True:
    PORT = input('Server Port: ')
    if not PORT:
        print("Port must be entered")
    else:
        try:
            PORT = int(PORT)
            break
        except ValueError:
            print("Port must be an integer")

SERVER = socket.gethostbyname(socket.gethostname())
ADDR = ('', PORT)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)


def close_server():
    for client in connections:
        send("[SERVER] Admin has closed the server, closing in 30 seconds", client)
    time.sleep(30)
    for client in connections:
        send("[SERVER] You have disconnected", client)
    time.sleep(2)
    os._exit(0)


def send(msg, conn):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    try:
        conn.send(send_length)
        conn.send(message)
    except ConnectionResetError:
        print(f"Could not contact client")


def receive(conn):
    msg_length = conn.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg = conn.recv(msg_length).decode(FORMAT)
        return msg


def handle_client(conn, addr):
    try:
        with sqlite3.connect("PassManager.db") as db:  # Setup Connection
            cursor = db.cursor()
        cursor.execute("CREATE TEMP TABLE IF NOT EXISTS Variables (Name TEXT PRIMARY KEY, Value TEXT);")
        print(f"[NEW CONNECTION] {addr} connected.")
        send(f'[SERVER] Connected to Server at {SERVER}', conn)
        connected = True
        send('''
-LOGIN MENU-
1 - Login
2 - Create new User
: ''', conn)
        answer = receive(conn)
        if answer == '2':
            Login.create_user(conn)

        sessionID = Login.login(conn)  # Login User

        if sessionID:  # Save sessionID
            execute = "INSERT OR REPLACE INTO Variables VALUES ('sessionID', ?);"
            cursor.execute(execute, [sessionID])
        else:  # If they wanted to not login
            connected = False
            send(f'[SERVER] You have disconnected', conn)
            print(f'[SERVER] User ({addr}) Has Disconnected')

        while connected:  # Loop until they disconnect ------------------
            if not Login.check_admin(sessionID):
                send('''
-MAIN MENU-
1 - Open Passwords Menu
2 - Open User Menu
3 - Disconnect From Server
: ''', conn)
                msg = receive(conn)

                if msg == "3":
                    connected = False
                    send(f'[SERVER] You have disconnected', conn)
                    print(f'[SERVER] User ({addr}) Has Disconnected')
                    continue

                elif msg == '1':
                    Passwords.pass_menu(conn, sessionID)
                    continue
                elif msg == "2":
                    if Login.check_admin(sessionID):
                        Login.admin_user_menu(conn, sessionID)
                    else:
                        Login.user_menu(conn, sessionID)
                    continue
                else:
                    send("[SERVER] Invalid input please try again ", conn)
                    continue

            else:
                send('''
-MAIN MENU-
1 - Open Passwords Menu
2 - Open User Menu
3 - Disconnect From Server
4 - Close Server
: ''', conn)
                msg = receive(conn)

                if msg == "3":
                    connected = False
                    send(f'[SERVER] You have disconnected', conn)
                    print(f'[SERVER] User ({addr}) Has Disconnected')
                    continue
                elif msg == '1':
                    Passwords.pass_menu(conn, sessionID)
                    continue
                elif msg == "2":
                    if Login.check_admin(sessionID):
                        Login.admin_user_menu(conn, sessionID)
                    else:
                        Login.user_menu(conn, sessionID)
                    continue
                elif msg == '4':
                    close_server()
                    continue
                else:
                    send("[SERVER] Invalid input please try again ", conn)
                    continue
        conn.close()
    except ConnectionResetError:
        print(f'[SERVER] User ({addr}) Has Disconnected')
        conn.close()


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}:{PORT}")
    while True:
        conn, addr = server.accept()
        connections.append(conn)
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        time.sleep(0.5)
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")


with sqlite3.connect("PassManager.db") as db:
    cursor = db.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS user(
userID INTEGER PRIMARY KEY,
username VARCHAR(20) NOT NULL,
firstname VARCHAR(20) NOT NULL,
password VARCHAR(20) NOT NULL,
isadmin INTEGER NOT NULL);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS passwords(
passwordID INTEGER PRIMARY KEY,
userID INTEGER,
account VARCHAR(20) NOT NULL,
username VARCHAR(20) NOT NULL,
password VARCHAR(100) NOT NULL,
salt BLOB NOT NULL,
note TEXT,
FOREIGN KEY (userID) REFERENCES user(userID));
''')

print("[STARTING] server is starting...")
start()
