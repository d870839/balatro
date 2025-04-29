import sqlite3

conn = sqlite3.connect('scoreboard.db')
c = conn.cursor()

# Create players table (already existing)
c.execute('''
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    score INTEGER DEFAULT 0
)
''')

# Create new player_jokers table
c.execute('''
CREATE TABLE IF NOT EXISTS player_jokers (
    id INTEGER PRIMARY KEY,
    player_name TEXT,
    joker_name TEXT
)
''')

conn.commit()
conn.close()


# hello hello 
