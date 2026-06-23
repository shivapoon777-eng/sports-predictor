"""
Sports Analytics Engine — Flask Web Application
Endpoint: POST /predict
"""

import json
import math
import random
import sqlite3
import os
from datetime import datetime

from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ─────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "predictions.db")


def get_db():
    """Open a thread-local SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create predictions table if it doesn't already exist."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp        TEXT    NOT NULL,
                sport            TEXT    NOT NULL,
                team_a           TEXT    NOT NULL,
                team_b           TEXT    NOT NULL,
                win_prob_a       REAL    NOT NULL,
                win_prob_b       REAL    NOT NULL,
                predicted_winner TEXT    NOT NULL
            )
        """)
        conn.commit()


def log_prediction(sport, team_a, team_b, win_prob_a, win_prob_b):
    """Insert one prediction row into the database."""
    predicted_winner = team_a if win_prob_a >= win_prob_b else team_b
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with get_db() as conn:
        conn.execute(
            """INSERT INTO predictions
               (timestamp, sport, team_a, team_b, win_prob_a, win_prob_b, predicted_winner)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (timestamp, sport.upper(), team_a, team_b,
             win_prob_a, win_prob_b, predicted_winner)
        )
        conn.commit()


# Initialise DB at startup — creates predictions.db + table if missing
init_db()

# ─────────────────────────────────────────────
# METRICS DATA
# ─────────────────────────────────────────────

NFL_METRICS = {
    "Kansas City Chiefs":     {"EPA": 0.18, "CPOE": 6.2,  "def_EPA": -0.14},
    "Philadelphia Eagles":    {"EPA": 0.15, "CPOE": 5.1,  "def_EPA": -0.12},
    "San Francisco 49ers":    {"EPA": 0.13, "CPOE": 4.8,  "def_EPA": -0.13},
    "Baltimore Ravens":       {"EPA": 0.14, "CPOE": 3.9,  "def_EPA": -0.11},
    "Dallas Cowboys":         {"EPA": 0.09, "CPOE": 3.2,  "def_EPA": -0.07},
    "Miami Dolphins":         {"EPA": 0.11, "CPOE": 5.5,  "def_EPA": -0.06},
    "Cincinnati Bengals":     {"EPA": 0.12, "CPOE": 5.8,  "def_EPA": -0.08},
    "Detroit Lions":          {"EPA": 0.16, "CPOE": 4.4,  "def_EPA": -0.09},
    "Green Bay Packers":      {"EPA": 0.08, "CPOE": 2.9,  "def_EPA": -0.08},
    "Houston Texans":         {"EPA": 0.10, "CPOE": 3.7,  "def_EPA": -0.05},
}

MLB_METRICS = {
    "Los Angeles Dodgers":    {"wOBA": 0.348, "FIP": 3.21},
    "Atlanta Braves":         {"wOBA": 0.341, "FIP": 3.38},
    "New York Yankees":       {"wOBA": 0.332, "FIP": 3.51},
    "Houston Astros":         {"wOBA": 0.326, "FIP": 3.44},
    "Baltimore Orioles":      {"wOBA": 0.319, "FIP": 3.67},
    "Tampa Bay Rays":         {"wOBA": 0.308, "FIP": 3.58},
    "Seattle Mariners":       {"wOBA": 0.302, "FIP": 3.29},
    "Texas Rangers":          {"wOBA": 0.315, "FIP": 3.71},
    "Minnesota Twins":        {"wOBA": 0.311, "FIP": 3.83},
    "Chicago Cubs":           {"wOBA": 0.306, "FIP": 3.94},
}

NBA_METRICS = {
    "Boston Celtics":         {"net_rtg": 11.2, "pace": 99.8,  "off_rtg": 122.4, "def_rtg": 111.2},
    "Oklahoma City Thunder":  {"net_rtg":  9.8, "pace": 101.2, "off_rtg": 120.1, "def_rtg": 110.3},
    "Denver Nuggets":         {"net_rtg":  8.1, "pace": 98.4,  "off_rtg": 118.7, "def_rtg": 110.6},
    "Minnesota Timberwolves": {"net_rtg":  7.6, "pace": 97.9,  "off_rtg": 115.8, "def_rtg": 108.2},
    "Cleveland Cavaliers":    {"net_rtg":  8.9, "pace": 100.1, "off_rtg": 119.3, "def_rtg": 110.4},
    "New York Knicks":        {"net_rtg":  6.8, "pace": 96.7,  "off_rtg": 114.9, "def_rtg": 108.1},
    "Indiana Pacers":         {"net_rtg":  5.2, "pace": 104.8, "off_rtg": 118.2, "def_rtg": 113.0},
    "Phoenix Suns":           {"net_rtg":  3.1, "pace": 99.2,  "off_rtg": 115.1, "def_rtg": 112.0},
    "Golden State Warriors":  {"net_rtg":  4.7, "pace": 100.4, "off_rtg": 116.8, "def_rtg": 112.1},
    "Los Angeles Lakers":     {"net_rtg":  2.9, "pace": 100.0, "off_rtg": 114.3, "def_rtg": 111.4},
}

SOCCER_METRICS = {
    "Argentina":   {"xG": 2.31, "xGA": 0.82},
    "France":      {"xG": 2.18, "xGA": 0.91},
    "England":     {"xG": 2.05, "xGA": 0.88},
    "Brazil":      {"xG": 2.09, "xGA": 0.95},
    "Spain":       {"xG": 2.24, "xGA": 0.79},
    "Germany":     {"xG": 1.98, "xGA": 1.02},
    "Portugal":    {"xG": 2.12, "xGA": 1.01},
    "Netherlands": {"xG": 1.87, "xGA": 1.08},
    "Morocco":     {"xG": 1.42, "xGA": 0.89},
    "USA":         {"xG": 1.61, "xGA": 1.12},
}

CRICKET_METRICS = {
    "India":        {"bat_sr": 148.2, "bowl_eco": 7.82, "avg_score": 184},
    "Australia":    {"bat_sr": 144.7, "bowl_eco": 7.95, "avg_score": 179},
    "England":      {"bat_sr": 151.3, "bowl_eco": 8.21, "avg_score": 188},
    "South Africa": {"bat_sr": 145.1, "bowl_eco": 8.04, "avg_score": 176},
    "West Indies":  {"bat_sr": 149.8, "bowl_eco": 8.44, "avg_score": 181},
    "Pakistan":     {"bat_sr": 138.6, "bowl_eco": 7.71, "avg_score": 168},
    "New Zealand":  {"bat_sr": 142.2, "bowl_eco": 7.88, "avg_score": 172},
    "Sri Lanka":    {"bat_sr": 136.4, "bowl_eco": 8.11, "avg_score": 165},
    "Bangladesh":   {"bat_sr": 129.7, "bowl_eco": 8.33, "avg_score": 157},
    "Afghanistan":  {"bat_sr": 134.9, "bowl_eco": 7.64, "avg_score": 163},
}

TENNIS_METRICS = {
    "Novak Djokovic":    {"dom_ratio": 0.672, "first_serve_pct": 0.641, "bp_save": 0.681},
    "Carlos Alcaraz":    {"dom_ratio": 0.658, "first_serve_pct": 0.628, "bp_save": 0.644},
    "Jannik Sinner":     {"dom_ratio": 0.651, "first_serve_pct": 0.651, "bp_save": 0.659},
    "Daniil Medvedev":   {"dom_ratio": 0.634, "first_serve_pct": 0.618, "bp_save": 0.671},
    "Alexander Zverev":  {"dom_ratio": 0.621, "first_serve_pct": 0.632, "bp_save": 0.628},
    "Andrey Rublev":     {"dom_ratio": 0.598, "first_serve_pct": 0.608, "bp_save": 0.612},
    "Hubert Hurkacz":    {"dom_ratio": 0.601, "first_serve_pct": 0.655, "bp_save": 0.618},
    "Taylor Fritz":      {"dom_ratio": 0.588, "first_serve_pct": 0.621, "bp_save": 0.605},
    "Stefanos Tsitsipas":{"dom_ratio": 0.595, "first_serve_pct": 0.612, "bp_save": 0.598},
    "Casper Ruud":       {"dom_ratio": 0.582, "first_serve_pct": 0.601, "bp_save": 0.589},
}

ALL_ROSTERS = {
    "nfl":     list(NFL_METRICS.keys()),
    "mlb":     list(MLB_METRICS.keys()),
    "nba":     list(NBA_METRICS.keys()),
    "soccer":  list(SOCCER_METRICS.keys()),
    "cricket": list(CRICKET_METRICS.keys()),
    "tennis":  list(TENNIS_METRICS.keys()),
}

SIMULATIONS = 1000


# ─────────────────────────────────────────────
# SIMULATION FUNCTIONS
# ─────────────────────────────────────────────

def _clamp(val, lo, hi):
    return max(lo, min(hi, val))


def simulate_nfl(a_name, b_name):
    a, b = NFL_METRICS.get(a_name), NFL_METRICS.get(b_name)
    if not a or not b:
        return None
    results = []
    for _ in range(SIMULATIONS):
        sa = round(_clamp(random.gauss(21 + (a["EPA"] - b["def_EPA"]) * 40, 7.5) + random.gauss(a["CPOE"] * 0.18, 1.0), 3, 55))
        sb = round(_clamp(random.gauss(21 + (b["EPA"] - a["def_EPA"]) * 40, 7.5) + random.gauss(b["CPOE"] * 0.18, 1.0), 3, 55))
        results.append((sa, sb))
    wa = sum(1 for a, b in results if a > b)
    wb = sum(1 for a, b in results if b > a)
    d  = SIMULATIONS - wa - wb
    avg_a = round(sum(r[0] for r in results) / SIMULATIONS, 1)
    avg_b = round(sum(r[1] for r in results) / SIMULATIONS, 1)
    return {"win_prob_a": round(wa/SIMULATIONS,4), "win_prob_b": round(wb/SIMULATIONS,4),
            "draw_prob": round(d/SIMULATIONS,4), "proj_score_a": avg_a, "proj_score_b": avg_b,
            "proj_total": round(avg_a+avg_b,1)}


def simulate_mlb(a_name, b_name):
    a, b = MLB_METRICS.get(a_name), MLB_METRICS.get(b_name)
    if not a or not b:
        return None
    results = []
    for _ in range(SIMULATIONS):
        ra = round(_clamp(random.gauss((a["wOBA"]/b["FIP"])*28, 2.2), 0, 20))
        rb = round(_clamp(random.gauss((b["wOBA"]/a["FIP"])*28, 2.2), 0, 20))
        results.append((ra, rb))
    wa = sum(1 for a, b in results if a > b)
    wb = sum(1 for a, b in results if b > a)
    d  = SIMULATIONS - wa - wb
    avg_a = round(sum(r[0] for r in results)/SIMULATIONS,1)
    avg_b = round(sum(r[1] for r in results)/SIMULATIONS,1)
    return {"win_prob_a": round(wa/SIMULATIONS,4), "win_prob_b": round(wb/SIMULATIONS,4),
            "draw_prob": round(d/SIMULATIONS,4), "proj_runs_a": avg_a, "proj_runs_b": avg_b,
            "proj_total": round(avg_a+avg_b,1)}


def simulate_nba(a_name, b_name):
    a, b = NBA_METRICS.get(a_name), NBA_METRICS.get(b_name)
    if not a or not b:
        return None
    results = []
    for _ in range(SIMULATIONS):
        pf = (a["pace"]+b["pace"])/2/100
        ap = round(_clamp(random.gauss(a["off_rtg"]*pf-(b["def_rtg"]-110)*0.5, 6.5), 80, 145))
        bp = round(_clamp(random.gauss(b["off_rtg"]*pf-(a["def_rtg"]-110)*0.5, 6.5), 80, 145))
        results.append((ap, bp))
    wa = sum(1 for a, b in results if a > b)
    wb = sum(1 for a, b in results if b > a)
    avg_a = round(sum(r[0] for r in results)/SIMULATIONS,1)
    avg_b = round(sum(r[1] for r in results)/SIMULATIONS,1)
    return {"win_prob_a": round(wa/SIMULATIONS,4), "win_prob_b": round(wb/SIMULATIONS,4),
            "draw_prob": 0.0, "proj_pts_a": avg_a, "proj_pts_b": avg_b,
            "proj_total": round(avg_a+avg_b,1)}


def simulate_soccer(a_name, b_name):
    a, b = SOCCER_METRICS.get(a_name), SOCCER_METRICS.get(b_name)
    if not a or not b:
        return None
    def poisson(lam):
        L, k, p = math.exp(-lam), 0, 1.0
        while p > L:
            k += 1; p *= random.random()
        return k - 1
    results = []
    for _ in range(SIMULATIONS):
        ga = poisson(_clamp((a["xG"]+b["xGA"])/2, 0.3, 4.5))
        gb = poisson(_clamp((b["xG"]+a["xGA"])/2, 0.3, 4.5))
        results.append((ga, gb))
    wa = sum(1 for a, b in results if a > b)
    wb = sum(1 for a, b in results if b > a)
    d  = SIMULATIONS - wa - wb
    avg_a = round(sum(r[0] for r in results)/SIMULATIONS,2)
    avg_b = round(sum(r[1] for r in results)/SIMULATIONS,2)
    return {"win_prob_a": round(wa/SIMULATIONS,4), "win_prob_b": round(wb/SIMULATIONS,4),
            "draw_prob": round(d/SIMULATIONS,4), "proj_goals_a": avg_a, "proj_goals_b": avg_b,
            "proj_total": round(avg_a+avg_b,2)}


def simulate_cricket(a_name, b_name):
    a, b = CRICKET_METRICS.get(a_name), CRICKET_METRICS.get(b_name)
    if not a or not b:
        return None
    results = []
    for _ in range(SIMULATIONS):
        bp_a = b["bowl_eco"]/8.0
        sa = round(max(80, random.gauss(a["avg_score"]*(a["bat_sr"]*(1-(1-bp_a)*0.15)/a["bat_sr"]), 18)))
        bp_b = a["bowl_eco"]/8.0
        sb = round(max(80, random.gauss(b["avg_score"]*(b["bat_sr"]*(1-(1-bp_b)*0.15)/b["bat_sr"]), 18)))
        results.append((sa, sb))
    wa = sum(1 for a, b in results if a > b)
    wb = sum(1 for a, b in results if b > a)
    avg_a = round(sum(r[0] for r in results)/SIMULATIONS,1)
    avg_b = round(sum(r[1] for r in results)/SIMULATIONS,1)
    return {"win_prob_a": round(wa/SIMULATIONS,4), "win_prob_b": round(wb/SIMULATIONS,4),
            "draw_prob": 0.0, "proj_score_a": avg_a, "proj_score_b": avg_b,
            "proj_combined": round(avg_a+avg_b,1)}


def simulate_tennis(a_name, b_name, best_of=5):
    a, b = TENNIS_METRICS.get(a_name), TENNIS_METRICS.get(b_name)
    if not a or not b:
        return None
    sets_needed = (best_of+1)//2
    logit = (a["dom_ratio"]-b["dom_ratio"])*6 + (a["first_serve_pct"]-b["first_serve_pct"])*2 + (a["bp_save"]-b["bp_save"])*2
    p_a = 1/(1+math.exp(-logit))
    results = []
    for _ in range(SIMULATIONS):
        sa, sb = 0, 0
        while sa < sets_needed and sb < sets_needed:
            if random.random() < p_a: sa += 1
            else: sb += 1
        results.append((sa, sb))
    wa = sum(1 for a, b in results if a > b)
    wb = sum(1 for a, b in results if b > a)
    return {"win_prob_a": round(wa/SIMULATIONS,4), "win_prob_b": round(wb/SIMULATIONS,4),
            "draw_prob": 0.0,
            "proj_sets_a": round(sum(r[0] for r in results)/SIMULATIONS,2),
            "proj_sets_b": round(sum(r[1] for r in results)/SIMULATIONS,2),
            "best_of": best_of}


SIMULATORS = {
    "nfl": simulate_nfl, "mlb": simulate_mlb, "nba": simulate_nba,
    "soccer": simulate_soccer, "cricket": simulate_cricket, "tennis": simulate_tennis,
}


# ─────────────────────────────────────────────
# HOMEPAGE — INTERACTIVE DOCS UI
# ─────────────────────────────────────────────

HOME_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sports Analytics Engine</title>
<style>
  :root {
    --bg: #0a0c10;
    --surface: #13161d;
    --border: #1e2330;
    --accent: #00e5a0;
    --accent-dim: #00b37a;
    --text: #e2e8f0;
    --muted: #64748b;
    --error: #f87171;
    --warn: #fbbf24;
    --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
    --font-sans: 'Inter', system-ui, sans-serif;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: var(--font-sans); min-height: 100vh; }

  header {
    border-bottom: 1px solid var(--border);
    padding: 20px 32px;
    display: flex;
    align-items: center;
    gap: 16px;
    position: sticky; top: 0;
    background: rgba(10,12,16,0.92);
    backdrop-filter: blur(12px);
    z-index: 100;
  }
  .logo-mark {
    width: 36px; height: 36px;
    background: var(--accent);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 18px; color: #0a0c10;
    font-family: var(--font-mono);
    flex-shrink: 0;
  }
  header h1 { font-size: 15px; font-weight: 600; letter-spacing: 0.02em; }
  header .version { margin-left: auto; font-size: 12px; color: var(--muted);
    font-family: var(--font-mono); background: var(--surface);
    padding: 4px 10px; border-radius: 20px; border: 1px solid var(--border); }

  .layout { display: grid; grid-template-columns: 260px 1fr; min-height: calc(100vh - 65px); }

  nav {
    border-right: 1px solid var(--border);
    padding: 28px 0;
    position: sticky; top: 65px; height: calc(100vh - 65px);
    overflow-y: auto;
  }
  nav .nav-label { font-size: 10px; font-weight: 700; letter-spacing: 0.12em;
    color: var(--muted); padding: 0 24px 10px; text-transform: uppercase; }
  nav a { display: flex; align-items: center; gap: 10px; padding: 9px 24px;
    font-size: 13px; color: var(--muted); text-decoration: none;
    transition: color 0.15s, background 0.15s; }
  nav a:hover { color: var(--text); background: var(--surface); }
  nav a .sport-pill { font-size: 10px; font-family: var(--font-mono);
    background: var(--border); padding: 2px 7px; border-radius: 4px; }
  nav .divider { height: 1px; background: var(--border); margin: 16px 24px; }

  main { padding: 48px 56px; max-width: 860px; }
  main h2 { font-size: 24px; font-weight: 700; margin-bottom: 8px; }
  main .subtitle { color: var(--muted); font-size: 14px; margin-bottom: 36px; line-height: 1.6; }

  .endpoint-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 32px;
    overflow: hidden;
  }
  .endpoint-header {
    display: flex; align-items: center; gap: 12px;
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
  }
  .method-badge {
    font-size: 11px; font-weight: 800; font-family: var(--font-mono);
    padding: 4px 10px; border-radius: 6px; letter-spacing: 0.05em;
  }
  .method-post { background: rgba(0,229,160,0.15); color: var(--accent); }
  .method-get  { background: rgba(96,165,250,0.15); color: #60a5fa; }
  .endpoint-path { font-family: var(--font-mono); font-size: 14px; color: var(--text); }
  .endpoint-desc { color: var(--muted); font-size: 13px; padding: 16px 20px; line-height: 1.6; }

  .param-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .param-table th { text-align: left; padding: 10px 20px; color: var(--muted);
    font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase;
    border-bottom: 1px solid var(--border); font-weight: 600; }
  .param-table td { padding: 12px 20px; border-bottom: 1px solid var(--border); vertical-align: top; }
  .param-table tr:last-child td { border-bottom: none; }
  .param-name { font-family: var(--font-mono); color: var(--accent); font-size: 12px; }
  .param-type { font-family: var(--font-mono); color: var(--warn); font-size: 11px; }
  .param-req  { font-family: var(--font-mono); color: var(--error); font-size: 11px; }
  .param-opt  { font-family: var(--font-mono); color: var(--muted); font-size: 11px; }

  .code-block {
    background: #080a0e;
    border-top: 1px solid var(--border);
    padding: 20px;
    font-family: var(--font-mono);
    font-size: 12px;
    line-height: 1.7;
    overflow-x: auto;
    white-space: pre;
    color: #94a3b8;
  }
  .code-block .k { color: #c084fc; }
  .code-block .s { color: #86efac; }
  .code-block .n { color: var(--accent); }
  .code-block .c { color: var(--muted); }

  /* Try It section */
  .try-it { padding: 20px; border-top: 1px solid var(--border); }
  .try-it h4 { font-size: 12px; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: var(--muted); margin-bottom: 16px; }
  .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }
  .form-group { display: flex; flex-direction: column; gap: 6px; }
  .form-group label { font-size: 11px; color: var(--muted); font-weight: 600;
    letter-spacing: 0.06em; text-transform: uppercase; }
  .form-group select, .form-group input {
    background: var(--bg); border: 1px solid var(--border);
    color: var(--text); padding: 9px 12px; border-radius: 8px;
    font-size: 13px; font-family: var(--font-sans);
    transition: border-color 0.15s;
  }
  .form-group select:focus, .form-group input:focus {
    outline: none; border-color: var(--accent);
  }
  .btn-run {
    background: var(--accent); color: #0a0c10;
    border: none; padding: 10px 24px; border-radius: 8px;
    font-weight: 700; font-size: 13px; cursor: pointer;
    transition: background 0.15s; margin-top: 4px;
  }
  .btn-run:hover { background: var(--accent-dim); }
  .btn-run:disabled { opacity: 0.4; cursor: not-allowed; }

  #result-box {
    margin-top: 16px; background: #080a0e;
    border: 1px solid var(--border); border-radius: 8px;
    padding: 16px; font-family: var(--font-mono); font-size: 12px;
    line-height: 1.6; color: #94a3b8; white-space: pre;
    overflow-x: auto; display: none; max-height: 420px; overflow-y: auto;
  }

  .sport-section { margin-bottom: 48px; }
  .sport-section h3 { font-size: 14px; font-weight: 700; color: var(--accent);
    margin-bottom: 16px; letter-spacing: 0.06em; text-transform: uppercase; }
  .roster-grid { display: flex; flex-wrap: wrap; gap: 8px; }
  .roster-tag { font-family: var(--font-mono); font-size: 11px;
    background: var(--surface); border: 1px solid var(--border);
    padding: 5px 10px; border-radius: 6px; color: var(--muted); }

  @media (max-width: 768px) {
    .layout { grid-template-columns: 1fr; }
    nav { display: none; }
    main { padding: 28px 20px; }
    .form-row { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>

<header>
  <div class="logo-mark">Σ</div>
  <h1>Sports Analyt
"""
