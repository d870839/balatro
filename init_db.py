import sqlite3

conn = sqlite3.connect('scoreboard.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    score INTEGER DEFAULT 0
)
''')
conn.commit()
conn.close()

# hello hello 
