import binascii
import hashlib
import os
import sqlite3
from tabulate import tabulate

FORMAT = 'utf-8'
HEADER = 64
password = ''


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


def hash_password(password):
    # Hash a password for storing.
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')


def verify_password(stored_password, provided_password):
    # Verify a stored password against one provided by user
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_password.encode('utf-8'),
                                  salt.encode('ascii'),
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


def login(conn):
    with sqlite3.connect("PassManager.db") as db:
        cursor = db.cursor()
    global password
    cursor.execute("SELECT COUNT(*) AS RowCnt FROM user")  # Check if no users exist
    results = cursor.fetchall()
    if results[0][0] == 0:
        send('[SERVER] No users found please create a new one', conn)
        create_user(conn)
        send('-Please log into new user-', conn)
    while True:
        send('Username: ', conn)
        username = receive(conn)
        send('Password (hidden): ', conn)
        password = receive(conn)

        find_user = "SELECT * FROM user WHERE username = ?"
        cursor.execute(find_user, [username])
        results = cursor.fetchall()
        try:
            correctPass = results[0][3]
        except IndexError:
            correctPass = ''

        if verify_password(correctPass, password):
            for i in results:
                send(f"\nWelcome, {i[2]}", conn)
                sessionID = i[0]
            break

        else:
            send("Username and password not recognized, do you want to try again (y/n): ", conn)
            again = receive(conn)
            if again.lower() == 'n':
                sessionID = None
                break

    return sessionID


def check_admin(userid):
    with sqlite3.connect("PassManager.db") as db:
        cursor = db.cursor()
    find = 'SELECT isadmin FROM user WHERE userID = ?'
    cursor.execute(find, [userid])
    results = cursor.fetchall()
    if results[0][0] == 1:
        return True
    else:
        return False


def admin_user_menu(conn, userID):
    while True:
        send('''
-ADMIN USER MENU-
1 - List all users
2 - Change Password
3 - Create new user
4 - Remove user
5 - Back
: ''', conn)
        while True:
            answer = receive(conn)
            if answer == '1':
                list_users(conn)
                break
            elif answer == '2':
                change_password(conn, userID)
                break
            elif answer == '3':
                create_user(conn, 1)
                break
            elif answer == '4':
                remove_user(conn)
                break
            elif answer == '5':
                return
            else:
                send("Invalid input please try again: ", conn)


def user_menu(conn, userID):
    while True:
        send('''
-USER MENU-
1 - Change Password
2 - Back
: ''', conn)
        while True:
            answer = receive(conn)
            if answer == '1':
                change_password(conn, userID)
                break
            elif answer == '2':
                return
            else:
                send("Invalid input please try again: ", conn)


def change_password(conn, userID):
    send("-Changing Password-", conn)
    with sqlite3.connect("PassManager.db") as db:
        cursor = db.cursor()

    loop = True
    while loop:
        send('Old password: ', conn)
        oldPass = receive(conn)

        find = "SELECT password FROM user WHERE userID = ?"
        cursor.execute(find, [userID])
        correctPass = cursor.fetchall()[0][0]
        if verify_password(correctPass, oldPass):
            loop = False
        else:
            send("Password incorrect, would you like to try again (y/n): ", conn)
            answer = receive(conn)
            if answer.lower() == 'y':
                continue
            else:
                return

    send('New password: ', conn)
    newPass = receive(conn)
    send('Confirm new password: ', conn)
    newPass1 = receive(conn)
    while newPass != newPass1 or newPass == "":
        send("-Passwords don't match or they are blank-", conn)
        send("New password: ", conn)
        newPass = receive(conn)
        send("Confirm new password: ", conn)
        newPass1 = receive(conn)
    change = "UPDATE user SET password = ? WHERE userID = ?;"
    cursor.execute(change, [hash_password(newPass), userID])
    db.commit()
    send(f"[SERVER] Password updated to ({newPass})", conn)


def create_user(conn, isadmin=0):
    send("-Creating User-", conn)
    found = 0
    while found == 0:  # Check if user already exists
        send("Please enter a username: ", conn)
        username = receive(conn)
        with sqlite3.connect("PassManager.db") as db:
            cursor = db.cursor()
        findUser = "SELECT * FROM user WHERE username = ?"
        cursor.execute(findUser, [username])

        if cursor.fetchall():
            send('Username taken, would you like to try again (y/n): ', conn)
            again = receive(conn)
            if again.lower() == 'n':
                return
        else:
            if username == '':
                send("Username Cannot be blank, would you like to try again (y/n):", conn)
                again = receive(conn)
                if again.lower() == 'n':
                    return
            else:
                found = 1

    send("Firstname: ", conn)
    firstname = receive(conn)
    admin = 0
    if isadmin == 1:
        send("Make user an Admin (y/n): ", conn)
        admin = receive(conn)
        admin = 1 if (admin == 'y') else 0
    send("Password (hidden): ", conn)
    password = receive(conn)
    send("Reenter Password (hidden): ", conn)
    password1 = receive(conn)
    while password != password1 or password == "":
        send("-Passwords don't match or they are blank-", conn)
        send("Password (hidden): ", conn)
        password = receive(conn)
        send("Reenter Password (hidden): ", conn)
        password1 = receive(conn)
    insertData = '''INSERT INTO user(username, firstname, password, isadmin)
    VALUES(?,?,?,?)'''
    cursor.execute(insertData, [username, firstname, hash_password(password), admin])
    db.commit()
    send(f'[SERVER] User {username} Created \n', conn)


def remove_user(conn):
    send("-Removing User-", conn)
    found = 0
    while found == 0:  # Check if user does not exist
        send('username: ', conn)
        username = receive(conn)
        send("Password (hidden): ", conn)
        password = receive(conn)
        with sqlite3.connect("PassManager.db") as db:
            cursor = db.cursor()

        find_user = "SELECT * FROM user WHERE username = ?"
        cursor.execute(find_user, [username])
        results = cursor.fetchall()
        correctPass = results[0][3]

        if verify_password(correctPass, password):
            found = 1
            for i in results:
                userID = i[0]
        else:
            send('Password incorrect or user does not exist, would you like to try again (y/n): ', conn)
            again = receive(conn)
            if again.lower() == 'n':
                return

    send('This will delete all information related to this user, confirm (y/n): ', conn)
    confirm = receive(conn)
    if confirm.lower() == 'y':
        deleteUser = '''DELETE FROM user WHERE username=?;'''
        cursor.execute(deleteUser, [username])
        deletePasswords = '''DELETE FROM passwords WHERE userID=?;'''
        cursor.execute(deletePasswords, [userID])
        db.commit()
        send(f'[SERVER] All data from {username} has been removed \n', conn)
    else:
        return


def list_users(conn):
    with sqlite3.connect("PassManager.db") as db:
        cursor = db.cursor()
    cursor.execute("SELECT username, firstname, isadmin FROM user")
    results = cursor.fetchall()
    send("\n", conn)
    send(tabulate(results, headers=["ID", "Username", "Firstname", "IsAdmin"], tablefmt="github", showindex=True), conn)
