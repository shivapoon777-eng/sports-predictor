import os, random, sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "predictions.db"))

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, sport TEXT,
            team_a TEXT, team_b TEXT, win_prob_a REAL, win_prob_b REAL, winner TEXT)''')
init_db()

TEAMS = {
    "NBA": {"Los Angeles Lakers": [114.2, 115.1], "Boston Celtics": [120.6, 110.2], "Golden State Warriors": [116.4, 115.8], "Miami Heat": [110.1, 108.4]},
    "NFL": {"Kansas City Chiefs": [24.8, 20.2], "San Francisco 49ers": [26.1, 19.8], "Philadelphia Eagles": [23.9, 21.4], "Buffalo Bills": [25.4, 22.1]},
    "MLB": {"New York Yankees": [4.8, 4.1], "Los Angeles Dodgers": [5.2, 4.3], "Houston Astros": [4.6, 4.2], "Atlanta Braves": [4.9, 3.9]},
    "SOCCER": {"Argentina": [2.1, 0.8], "France": [2.3, 0.9], "Brazil": [1.9, 1.0], "England": [2.0, 0.7], "Iran": [1.6, 1.1], "Belgium": [1.8, 1.2]},
    "CRICKET": {"India": [280.5], "Australia": [275.2], "England": [270.4], "Pakistan": [260.1]}

}

def simulate_game(sport, stats_a, stats_b):
    wins_a = 0
    sims = 1000
    for _ in range(sims):
        score_a = random.gauss(stats_a[0], 5 if sport in ["NFL","MLB","SOCCER"] else 12)
        score_b = random.gauss(stats_b[0], 5 if sport in ["NFL","MLB","SOCCER"] else 12)
        if score_a > score_b: wins_a += 1
    prob_a = wins_a / sims
    return round(prob_a, 3), round(1 - prob_a, 3), round(stats_a[0], 1), round(stats_b[0], 1)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json() or {}
    sport = data.get("sport", "").upper()
    ta, tb = data.get("team_a"), data.get("team_b")
    if sport not in TEAMS or ta not in TEAMS[sport] or tb not in TEAMS[sport]:
        return jsonify({"error": "Invalid sport or team name selected"}), 400
    pa, pb, sa, sb = simulate_game(sport, TEAMS[sport][ta], TEAMS[sport][tb])
    winner = ta if pa > pb else tb
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT INTO predictions (timestamp, sport, team_a, team_b, win_prob_a, win_prob_b, winner) VALUES (?,?,?,?,?,?,?)",
                         (datetime.utcnow().isoformat(), sport, ta, tb, pa, pb, winner))
    except Exception: pass
    return jsonify({"simulation": {"win_prob_a": pa, "win_prob_b": pb, "proj_pts_a": sa, "proj_pts_b": sb, "proj_total": round(sa+sb,1)}, "teams": {"a": ta, "b": tb}})

@app.route('/history', methods=['GET'])
def history():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT sport, team_a, team_b, win_prob_a, win_prob_b, winner FROM predictions ORDER BY id DESC LIMIT 10")
            rows = cursor.fetchall()
            return jsonify([{"sport": r[0], "team_a": r[1], "team_b": r[2], "win_prob_a": r[3], "win_prob_b": r[4], "winner": r[5]} for r in rows])
    except Exception: return jsonify([])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
  
