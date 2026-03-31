import sqlite3
import os

DB_PATH = r'd:\bbms\bbms.db'
if os.path.exists(DB_PATH):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Check current columns
        cur.execute("PRAGMA table_info(donors)")
        cols = [c[1] for c in cur.fetchall()]
        print(f"Current columns in donors: {cols}")
        
        # Add latitude if missing
        if 'latitude' not in cols:
            print("Adding latitude column...")
            cur.execute("ALTER TABLE donors ADD COLUMN latitude REAL")
            print("Latitude column added.")
        else:
            print("Latitude column already exists.")
            
        # Add longitude if missing
        if 'longitude' not in cols:
            print("Adding longitude column...")
            cur.execute("ALTER TABLE donors ADD COLUMN longitude REAL")
            print("Longitude column added.")
        else:
            print("Longitude column already exists.")
            
        conn.commit()
        conn.close()
        print("Schema update complete.")
    except sqlite3.Error as e:
        print(f"Error during schema update: {e}")
else:
    print("Database file NOT found at", DB_PATH)
