from flask import Flask, render_template, request, redirect, session, flash, send_from_directory
import sqlite3
import os

app = Flask(__name__)
DB_PATH = '/opt/render/project/src/scoreboard.db'
app.secret_key = "my-key"

joker_rarity = {
    "Four Fingers": "Common",
    "Thumb": "Common",
    "Eight Ball": "Common",
    "Odd Todd": "Common",
    "Even Steven": "Common",
    "Blueprint": "Uncommon",
    "Hiker": "Uncommon",
    "The Arm": "Uncommon",
    "Hack": "Uncommon",
    "The Soul": "Uncommon",
    "Brainstorm": "Rare",
    "Egg": "Rare",
    "Seance": "Rare",
    "Erosion": "Rare",
    "Misprint": "Rare",
    "Joker": "Legendary",
    "The Ankh": "Legendary",
    "Midas Mask": "Legendary",
    "Astronomer": "Legendary",
    "The Immortal": "Legendary"
}

def load_jokers_by_rarity():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT name, rarity FROM jokers')
    rows = c.fetchall()
    conn.close()

    jokers = {"Common": [], "Uncommon": [], "Rare": [], "Legendary": []}
    for name, rarity in rows:
        if rarity in jokers:
            jokers[rarity].append(name)
        else:
            jokers["Common"].append(name)  # Default to Common if somehow missing

    return jokers

@app.route('/static/jokers/<rarity>/<filename>')
def cached_joker(rarity, filename):
    response = send_from_directory(f'static/jokers/{rarity}', filename)
    response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'davidsucks':  # <-- CHANGE THIS to your secret admin password
            session['admin'] = True
            flash('Logged in successfully!', 'success')
            return redirect('/')
        else:
            flash('Incorrect password. Try again.', 'error')
            return redirect('/login')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('Logged out.', 'info')
    return redirect('/')

def get_scores():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, score FROM players ORDER BY score DESC")
    scores = c.fetchall()
    conn.close()
    return scores

@app.route('/choose_joker/<player_name>', methods=['GET'])
def choose_joker(player_name):
    return render_template('choose_joker.html', player_name=player_name, jokers_by_rarity=load_jokers_by_rarity())

@app.route('/choose_joker/')
def choose_joker_missing():
    flash("You must choose a player first.", "error")
    return redirect('/')

@app.route('/admin/jokers', methods=['GET', 'POST'])
def manage_jokers():
    if not session.get('admin'):
        flash("Admin login required", "error")
        return redirect('/login')

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if request.method == 'POST':
        for joker_name in request.form:
            new_rarity = request.form[joker_name]
            c.execute("UPDATE jokers SET rarity = ? WHERE name = ?", (new_rarity, joker_name))
        conn.commit()
        flash("Rarities updated!", "success")

    c.execute("""
    SELECT name, rarity FROM jokers
    ORDER BY
        CASE rarity
            WHEN 'Common' THEN 1
            WHEN 'Uncommon' THEN 2
            WHEN 'Rare' THEN 3
            WHEN 'Legendary' THEN 4
            ELSE 5
        END,
        name ASC
""")
    jokers = c.fetchall()
    conn.close()

    return render_template('admin_jokers.html', jokers=jokers)

@app.route('/select_joker', methods=['POST'])
def select_joker():
    player_name = request.form['player_name']
    joker_name = request.form['joker_name']
    print(f"📌 select_joker(): {player_name=} | {joker_name=}")  # Add this line

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Update the player's score (+1)
    c.execute("UPDATE players SET score = score + 1 WHERE name = ?", (player_name,))

    # Insert selected Joker into player_jokers table
    c.execute("INSERT INTO player_jokers (player_name, joker_name) VALUES (?, ?)", (player_name, joker_name))

    conn.commit()
    conn.close()

    print(f"✅ SAVING: {player_name} → {joker_name}")

    return redirect('/')

@app.route('/all_joker_stats')
def all_joker_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        SELECT joker_name, COUNT(*) as count
        FROM player_jokers
        GROUP BY joker_name
        ORDER BY count DESC
    ''')
    joker_stats = c.fetchall()

    # New: also fetch rarities dynamically
    c.execute('SELECT name, rarity FROM jokers')
    rows = c.fetchall()
    conn.close()

    joker_rarity = {name: rarity for name, rarity in rows}

    return render_template('all_joker_stats.html', joker_stats=joker_stats, joker_rarity=joker_rarity)


@app.route('/player/<player_name>')
def player_stats(player_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get total number of Joker selections for player
    c.execute('''
        SELECT COUNT(*)
        FROM player_jokers
        WHERE player_name = ?
    ''', (player_name,))
    total_selections = c.fetchone()[0]

    # Query all jokers picked by the player, grouped by joker name, and count how many times each was picked
    c.execute('''
        SELECT joker_name, COUNT(*) as count
        FROM player_jokers
        WHERE player_name = ?
        GROUP BY joker_name
        ORDER BY count DESC
    ''', (player_name,))
    joker_stats = c.fetchall()
    conn.close()

    print(f"🧪 player_stats(): {player_name=}")

    return render_template('player_stats.html', player_name=player_name, joker_stats=joker_stats,total_selections=total_selections)


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
