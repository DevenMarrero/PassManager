import binascii
import hashlib
import os
import sqlite3

FORMAT = 'utf-8'
HEADER = 64
password = ''


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


#  Done
def login(username, passw):
    with sqlite3.connect("PassManager.db") as db:
        cursor = db.cursor()
    global password
    password = passw
    find_user = "SELECT * FROM user WHERE username = ?"
    cursor.execute(find_user, [username])
    results = cursor.fetchall()
    try:
        correctPass = results[0][3]
    except IndexError:
        correctPass = ''

    if verify_password(correctPass, password):
        sessionID = results[0][0]
        return sessionID

    else:
        return


def check_admin(userID):
    with sqlite3.connect("PassManager.db") as db:
        cursor = db.cursor()
    find = 'SELECT isadmin FROM user WHERE userID = ?'
    cursor.execute(find, [userID])
    results = cursor.fetchall()
    if results[0][0] == 1:
        return True
    else:
        return False


#  Done
def change_password(userID, newPass):
    with sqlite3.connect("PassManager.db") as db:
        cursor = db.cursor()

    change = "UPDATE user SET password = ? WHERE userID = ?;"
    cursor.execute(change, [hash_password(newPass), userID])
    db.commit()
    return 'Password Changed'


#  Done
def create_user(username, firstname, password):
    with sqlite3.connect("PassManager.db") as db:
        cursor = db.cursor()

    # Check if name taken
    findUser = "SELECT * FROM user WHERE username = ?"
    cursor.execute(findUser, [username])
    if cursor.fetchall():
        return 'Error: Username Already Taken'

    # Create User
    # Check if no other users
    cursor.execute("SELECT COUNT(*) FROM user")
    results = cursor.fetchall()
    if results == 0:
        admin = 1
    else:
        admin = 0
    insertData = '''INSERT INTO user(username, firstname, password, isadmin)
    VALUES(?,?,?,?)'''
    cursor.execute(insertData, [username, firstname, hash_password(password), admin])
    db.commit()
    return 'User Created'


#  Done
def remove_user(sessionID, password):
    with sqlite3.connect("PassManager.db") as db:
        cursor = db.cursor()

    get_pass = "SELECT password FROM user WHERE userID = ?"
    cursor.execute(get_pass, [sessionID])
    results = cursor.fetchall()
    correctPass = results[0][0]

    if verify_password(correctPass, password):
        # Password Correct: Delete User
        deleteUser = '''DELETE FROM user WHERE userID=?;'''
        cursor.execute(deleteUser, [sessionID])
        deletePasswords = '''DELETE FROM passwords WHERE userID=?;'''
        cursor.execute(deletePasswords, [sessionID])
        db.commit()
        return 'User Deleted'

    else:
        return 'Error: Password Incorrect'


#  Done
def promote_user(username):
    with sqlite3.connect("PassManager.db") as db:
        cursor = db.cursor()
    find = "SELECT isadmin FROM user WHERE username = ?"
    cursor.execute(find, [username])
    results = cursor.fetchall()
    if not results:
        return f'Error: User does not Exist'
    if results[0][0] == 1:
        return f'Error: User is Already an Admin'
    else:
        promote = "UPDATE user SET isadmin = 1 WHERE username = ?"
        cursor.execute(promote, [username])
        db.commit()
        return 'User Promoted to Admin'
