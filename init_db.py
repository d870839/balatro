import sqlite3
import os

DB_PATH = '/opt/render/project/src/scoreboard.db'

if not os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

# Create players table if missing

    c.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        score INTEGER DEFAULT 0
    )
    ''')

# ✅ Create player_jokers table
    c.execute('''
    CREATE TABLE IF NOT EXISTS player_jokers (
        id INTEGER PRIMARY KEY,
        player_name TEXT,
        joker_name TEXT
    )
    ''')

    # Create jokers table if missing (you might already have this)
    c.execute('''
    CREATE TABLE IF NOT EXISTS jokers (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        rarity TEXT
    )
    ''')

    conn.commit()
    conn.close()
    print("✅ New database initialized.")
else:
    print("✅ Database Already Exists. No Changes Made")
