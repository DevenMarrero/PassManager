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


def refine(msg, call):
    space_args = msg.replace(call, '').split(',')
    args = []
    for arg in space_args:
        args.append(arg.strip())
    return args


def handle_client(conn, addr):
    try:
        with sqlite3.connect("PassManager.db") as db:  # Setup Connection
            cursor = db.cursor()
        cursor.execute("CREATE TEMP TABLE IF NOT EXISTS Variables (Name TEXT PRIMARY KEY, Value TEXT);")
        print(f"[NEW CONNECTION] {addr} connected.")
        # send(f'[SERVER] Connected to Server at {SERVER}', conn)
        connected = True
        sessionID = None

        while connected:  # Loop until they disconnect ------------------
            send('test: ', conn)
            msg = receive(conn)

            if 'login: ' in msg:
                # (username, password)
                args = refine(msg, 'login: ')
                sessionID = Login.login(args[0], args[1])  # Login User
                if sessionID:  # Save sessionID
                    execute = "INSERT OR REPLACE INTO Variables VALUES ('sessionID', ?);"
                    cursor.execute(execute, [sessionID])
                    send('Login Successful', conn)
                else:  # Invalid login
                    send('Error: Username or Password Incorrect', conn)

            elif 'change_password: ' in msg:
                # (New_password)
                args = refine(msg, 'change_password: ')
                send(Login.change_password(sessionID, args[0]), conn)
                # 'Password Changed'

            elif 'create_user: ' in msg:
                # (username, firstName, password)
                args = refine(msg, 'create_user: ')
                send(Login.create_user(args[0], args[1], args[2]), conn)
                # 'User Created' or 'Error: Username Already Taken'

            elif 'remove_user: ' in msg:
                # (password)
                args = refine(msg, 'remove_user: ')
                send(Login.remove_user(sessionID, args[0]), conn)
                # 'User Deleted' or 'Error: Password Incorrect'

            elif 'promote_user: ' in msg:
                # (username)
                args = refine(msg, 'promote_user: ')
                send(Login.promote_user(args[0]), conn)
                # 'Error: User Does not Exist' or
                # 'Error: User is Already an Admin' or
                # 'User Promoted to Admin'

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
favorite INTEGER NOT NULL,
FOREIGN KEY (userID) REFERENCES user(userID));
''')

print("[STARTING] Server is starting...")
start()
