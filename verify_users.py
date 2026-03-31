import sqlite3

DB_PATH = r'd:\bbms\bbms.db'
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT username FROM users")
users = cur.fetchall()
print(f"Users found: {users}")
conn.close()
