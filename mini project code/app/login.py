import sqlite3

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

def create_user(username,password):

    try:
        cursor.execute(
        "INSERT INTO users(username,password) VALUES (?,?)",
        (username,password))
        conn.commit()
        return True
    except:
        return False


def login_user(username,password):

    cursor.execute(
    "SELECT * FROM users WHERE username=? AND password=?",
    (username,password))

    return cursor.fetchone()