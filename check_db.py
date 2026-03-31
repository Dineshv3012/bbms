import sqlite3
import os

DB_PATH = r'd:\bbms\bbms.db'
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(donors)")
    cols = cur.fetchall()
    print("Donors table columns:")
    for col in cols:
        print(col)
    conn.close()
else:
    print("Database file NOT found at", DB_PATH)
