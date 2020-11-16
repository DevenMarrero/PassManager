import base64
import os
import sqlite3
import Login
# pip packages
import xlsxwriter
from tabulate import tabulate
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


FORMAT = 'utf-8'
HEADER = 64


def send(msg, conn):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    conn.send(send_length)
    conn.send(message)


def receive(conn):
    msg_length = conn.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg = conn.recv(msg_length).decode(FORMAT)
        return msg


def create_key_from_pass(userPass, salt):
    userPass = userPass.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend())
    key = base64.urlsafe_b64encode(kdf.derive(userPass))
    return Fernet(key)


# Functions
# SQL passwords is passID, userID, account, username, password
def pass_menu(conn, sessionID):
    while True:
        send('''
-PASSWORD MENU-
1 - Search Password
2 - Create Password
3 - Remove password
4 - Exit
: ''', conn)
        while True:
            answer = receive(conn)
            if answer == '1':
                send("Enter Search (Leave blank for all; !excel for spreadsheet): ", conn)
                search = receive(conn).lower()
                if '!excel' in search:
                    export = True
                    search = search.replace('!excel', '').strip()
                else:
                    export = False
                search = '%' + search + '%'
                search_pass(conn, sessionID, search, export)
                break
            elif answer == '2':
                create_pass(conn, sessionID)
                break
            elif answer == '3':
                remove_pass(conn, sessionID)
                break
            elif answer == '4':
                return
            else:
                send("Invalid input please try again ", conn)
                continue


def search_pass(conn, sessionID, search, export):
    with sqlite3.connect("PassManager.db") as db:
        cursor = db.cursor()
    passList = f"SELECT account, username, password, salt, note FROM passwords WHERE userID= ? AND account LIKE ?"
    cursor.execute(passList, [sessionID, search])
    results = cursor.fetchall()
    for ind, entrance in enumerate(results):
        results[ind] = list(entrance)
        salt = entrance[3]
        f = create_key_from_pass(Login.password, salt)
        decrypted = f.decrypt(entrance[2])
        results[ind][2] = decrypted.decode()
        results[ind].remove(results[ind][3])

    send("\n", conn)
    results = sorted(results)
    headers = ["Account", "Username", "Password", "Note"]
    send(tabulate(results, headers=headers), conn)
    if export:
        filename = "SearchResults.xlsx"
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        row = 0
        col = 0
        for header in headers:
            worksheet.write(row, col, header)
            col += 1
        row += 1
        col = 0
        for entry in results:
            for item in entry:
                worksheet.write(row, col, item)
                col += 1
            row += 1
            col = 0
        workbook.close()

        filesize = os.path.getsize(filename)
        send(f"{filename}<SEPARATOR>{filesize}", conn)
        with open(filename, 'rb') as f:
            file_data = f.read(filesize)
            conn.send(file_data)
            sconn = str(conn)
            print(f'''File ({filename}) has been transmitted to {sconn[sconn.find("raddr=('")+6:-1]}''')
        os.remove(filename)


def create_pass(conn, sessionID):
    send("\n-Creating New Password-", conn)
    found = 0
    while found == 0:  # Check if password already exists
        send("Name of Account: ", conn)
        account = receive(conn).lower()
        with sqlite3.connect("PassManager.db") as db:
            cursor = db.cursor()
        findUser = "SELECT * FROM passwords WHERE userID = ? AND account = ?"
        cursor.execute(findUser, [sessionID, account])

        if cursor.fetchall():
            send('Account already stored, would you like to add something else (y/n): ', conn)
            again = receive(conn)
            if again.lower() == 'n':
                return
        else:
            found = 1

    send("Account Username: ", conn)
    username = receive(conn)
    while username == '':
        send('-Username cannot be blank-', conn)
        send("Account Username: ", conn)
        username = receive(conn)
    send("Account Password: ", conn)
    password = receive(conn)
    send("Reenter Password: ", conn)
    password1 = receive(conn)
    while password != password1 or password == "":
        send("-Passwords don't match or they are blank-", conn)
        send("Account Password: ", conn)
        password = receive(conn)
        send("Reenter Password: ", conn)
        password1 = receive(conn)
    send("Note (optional): ", conn)
    note = receive(conn)
    password = password.encode()
    salt = os.urandom(16)
    f = create_key_from_pass(Login.password, salt)
    insertData = '''INSERT INTO passwords(userID, account, username, password, salt, note)
        VALUES(?,?,?,?,?,?)'''
    cursor.execute(insertData, [sessionID, account, username, f.encrypt(password), salt, note])
    db.commit()
    if note == '':
        note = 'None'
    send(f'\n[SERVER] Password for ({account}) Created with: \nUsername: {username} \nPassword: {password1} \n'
         f'Note: {note}', conn)


def remove_pass(conn, sessionID):
    send("\n-Removing Password-", conn)
    found = 0
    while found == 0:  # Check if account does not exist
        send('Account name: ', conn)
        account = receive(conn).lower()
        with sqlite3.connect("PassManager.db") as db:
            cursor = db.cursor()
            search = "SELECT * FROM passwords WHERE userID=? AND account=?"
            cursor.execute(search, [sessionID, account])
            results = cursor.fetchall()

        if not results:
            send('Account does not exist, would you like to try again (y/n): ', conn)
            again = receive(conn)
            if again.lower() == 'n':
                return
        else:
            break

    send(f'This will delete all information related to the account: {account}, confirm (y/n): ', conn)
    confirm = receive(conn)
    if confirm.lower() == 'y':
        deletePasswords = '''DELETE FROM passwords WHERE userID=? AND account=?;'''
        cursor.execute(deletePasswords, [sessionID, account])
        db.commit()

        salt = results[0][5]
        f = create_key_from_pass(Login.password, salt)
        decrypted = f.decrypt(results[0][4])

        send(f'\n[SERVER] Account ({account}) has been removed:\nUsername: {results[0][3]} \nPassword: {decrypted.decode()} \n',
             conn)
    else:
        return
