from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)
DB_PATH = 'scoreboard.db'

def get_scores():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, score FROM players ORDER BY score DESC")
    scores = c.fetchall()
    conn.close()
    return scores

@app.route('/', methods=['GET'])
def index():
    scores = get_scores()
    return render_template('index.html', scores=scores)

@app.route('/add', methods=['POST'])
def add():
    name = request.form['name']
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO players (name, score) VALUES (?, 0)", (name,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/update', methods=['POST'])
def update():
    name = request.form['name']
    change = int(request.form['change'])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE players SET score = score + ? WHERE name = ?", (change, name))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/remove', methods=['POST'])
def remove():
    name = request.form['name']
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM players WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    return redirect('/')



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
