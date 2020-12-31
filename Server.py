import socket
import threading
import sqlite3
import Login
import Passwords
import time
import os
import sys

FORMAT = 'utf-8'
connections = []


def get_port():
    while True:
        port = input('Server Port: ')
        if not port:
            print("Port must be entered")
        else:
            try:
                port = int(port)
                return port
            except ValueError:
                print("Port must be an integer")


if len(sys.argv) == 2:
    try:
        PORT = int(sys.argv[1])
    except ValueError:
        PORT = get_port()

else:
    PORT = get_port()

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
    try:
        conn.send(message)
    except ConnectionResetError:
        print(f"Could not contact client")


def receive(conn):
    msg = conn.recv(1024).decode(FORMAT)
    return msg if msg else "disconnect: "


def refine(msg, call):
    space_args = msg.replace(call, '').split('<>')
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
        connected = True
        sessionID = None

        while connected:  # Loop until they disconnect ------------------
            msg = receive(conn)

            # REMOVE THIS
            print(msg)

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

            elif 'change_username: ' in msg:
                # (New_username)
                args = refine(msg, 'change_username: ')
                send(Login.change_username(sessionID, args[0]), conn)
                # 'Username Changed'

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

            elif 'create_pass: ' in msg:
                # (account, username, password, note, favourite)
                args = refine(msg, 'create_pass: ')
                send(Passwords.create_pass(sessionID, args[0], args[1], args[2], args[3], args[4]), conn)
                # 'Error: Account Already Exists' or
                # 'Password Created'

            elif 'remove_pass: ' in msg:
                # (account)
                args = refine(msg, 'remove_pass: ')
                send(Passwords.remove_pass(sessionID, args[0]), conn)
                # 'Password Deleted'
                # 'Error: Account does not Exist'

            elif 'search_pass: ' in msg:
                # (account, export)
                # Export 1 or 0
                args = refine(msg, 'search_pass: ')
                send(Passwords.search_pass(conn, sessionID, args[0], args[1]), conn)
                # (search results)

            elif 'check_admin: ' in msg:
                # (ID)
                send(Login.check_admin(sessionID), conn)
                # '1' admin
                # '0' user

            elif 'toggle_favourite: ' in msg:
                # (account)
                args = refine(msg, 'toggle_favourite: ')
                send(Passwords.toggle_favourite(sessionID, args[0]), conn)
                # 'Error: Account does not Exist'
                # 'Favourite Toggled'

            elif 'disconnect: ' in msg:
                break

        print(f'[SERVER] User {addr} Has Disconnected')
        conn.close()

    except ConnectionResetError:
        print(f'[SERVER] User {addr} Has Disconnected')
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

#  Create user Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS user(
userID INTEGER PRIMARY KEY,
username VARCHAR(20) NOT NULL,
firstname VARCHAR(20) NOT NULL,
password VARCHAR(20) NOT NULL,
isadmin INTEGER NOT NULL);
''')

#  Create passwords Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS passwords(
passwordID INTEGER PRIMARY KEY,
userID INTEGER,
account VARCHAR(20) NOT NULL,
username VARCHAR(20) NOT NULL,
password VARCHAR(100) NOT NULL,
salt BLOB NOT NULL,
note TEXT,
favourite INTEGER NOT NULL,
FOREIGN KEY (userID) REFERENCES user(userID));
''')

print("[STARTING] Server is starting...")
start()
