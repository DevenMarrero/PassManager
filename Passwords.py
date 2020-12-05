import base64
import os
import sqlite3
import random
import Login
# pip packages
import xlsxwriter
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


def search_pass(conn, sessionID, search, export):
    with sqlite3.connect("PassManager.db") as db:
        cursor = db.cursor()
    search = '%' + search + '%'
    passList = f"SELECT account, username, password, salt, note FROM passwords WHERE userID= ? AND account LIKE ?"
    cursor.execute(passList, [sessionID, search])
    results = cursor.fetchall()
    for ind, val in enumerate(results):
        results[ind] = list(val)
        results[ind][0] = results[ind][0].capitalize()
        salt = val[3]
        f = create_key_from_pass(Login.password, salt)
        decrypted = f.decrypt(val[2])
        results[ind][2] = decrypted.decode()
        results[ind].remove(results[ind][3])

    results = sorted(results)
    headers = ["Account", "Username", "Password", "Note"]
    if int(export) == 0:
        return str(results)
    # Send Client Search excel
    else:
        filename = F"ID{sessionID}SearchResults.xlsx"
        # Make spreadsheet
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
        send(f"SearchResults.xlsx<SEPARATOR>{filesize}", conn)
        with open(filename, 'rb') as f:
            file_data = f.read(filesize)
            conn.send(file_data)
            strconn = str(conn)
            print(f'''File ({filename}) has been transmitted to {strconn[strconn.find("raddr=('")+6:-1]}''')
        os.remove(filename)


def create_pass(sessionID, account, username, password, note):
    with sqlite3.connect("PassManager.db") as db:
        cursor = db.cursor()
    # Check if password already exists
    findUser = "SELECT * FROM passwords WHERE userID = ? AND account = ?"
    cursor.execute(findUser, [sessionID, account])
    if cursor.fetchall():
        return 'Error: Account Already Exists'

    # Create Password
    password = password.encode()
    salt = os.urandom(16)
    f = create_key_from_pass(Login.password, salt)
    insertData = '''INSERT INTO passwords(userID, account, username, password, salt, note)
        VALUES(?,?,?,?,?,?)'''
    cursor.execute(insertData, [sessionID, account, username, f.encrypt(password), salt, note])
    db.commit()
    return 'Password Created'


def remove_pass(sessionID, account):
    with sqlite3.connect("PassManager.db") as db:
        cursor = db.cursor()
    # Check if account does not exist
    search = "SELECT * FROM passwords WHERE userID=? AND account=?"
    cursor.execute(search, [sessionID, account])
    results = cursor.fetchall()
    if not results:
        return 'Error: Account does not Exist'

    else:
        deletePassword = '''DELETE FROM passwords WHERE userID=? AND account=?;'''
        cursor.execute(deletePassword, [sessionID, account])
        db.commit()
        return 'Password Deleted'


def toggle_favorite(sessionID, account):
    with sqlite3.connect("PassManager.db") as db:
        cursor = db.cursor()
    # Check if account does not exist
    search = "SELECT favorite FROM passwords WHERE userID=? AND account=?"
    cursor.execute(search, [sessionID, account])
    results = cursor.fetchall()
    if not results:
        return 'Error: Account does not Exist'
    else:
        favorite = 0 if int(results[0][0]) == 1 else 1
        toggle = "UPDATE passwords SET favorite=? WHERE userID=? AND account=?"
        cursor.execute(toggle, [favorite, sessionID, account])
        db.commit()
        return 'Favourite Toggled'


# Put on app side
def generate_pass():
    uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lowercasse = uppercase.lower()
    numbers = "0123456789"
    symbols = "!@#$%&*?"
    total = uppercase + lowercasse + numbers + symbols
    password = "".join(random.sample(total, 10))
    while not any(symbol in password for symbol in symbols) or not any(letter in password for letter in uppercase):
        password = "".join(random.sample(total, 10))
    return password

