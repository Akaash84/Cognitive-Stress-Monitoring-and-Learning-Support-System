import sqlite3

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT UNIQUE,
password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS test_history(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
score INTEGER,
time_taken_seconds INTEGER DEFAULT 0,
date TIMESTAMP DEFAULT (datetime('now','localtime'))
)
""")

conn.commit()