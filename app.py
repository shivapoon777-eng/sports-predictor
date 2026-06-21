"""
Sports Analytics Engine — Flask Web Application
Endpoint: POST /predict
"""

import json
import math
import random
from datetime import datetime

from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

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
  <h1>Sports Analytics Engine</h1>
  <span class="version">v1.0 · Monte Carlo</span>
</header>

<div class="layout">
  <nav>
    <div class="nav-label">Endpoints</div>
    <a href="#predict"><span class="sport-pill">POST</span> /predict</a>
    <a href="#health"><span class="sport-pill">GET</span> /health</a>
    <a href="#roster"><span class="sport-pill">GET</span> /roster</a>
    <div class="divider"></div>
    <div class="nav-label">Sports</div>
    <a href="#rosters">🏈 NFL</a>
    <a href="#rosters">⚾ MLB</a>
    <a href="#rosters">🏀 NBA</a>
    <a href="#rosters">⚽ Soccer</a>
    <a href="#rosters">🏏 Cricket</a>
    <a href="#rosters">🎾 Tennis</a>
  </nav>

  <main>
    <h2>API Reference</h2>
    <p class="subtitle">Monte Carlo simulation engine across 6 sports. Send a matchup, get win probabilities and projected scores back as JSON. All simulations run 1,000 iterations server-side.</p>

    <!-- POST /predict -->
    <div id="predict" class="endpoint-card">
      <div class="endpoint-header">
        <span class="method-badge method-post">POST</span>
        <span class="endpoint-path">/predict</span>
      </div>
      <div class="endpoint-desc">
        Simulate a matchup between two teams or players. Returns win probabilities, draw probability, projected scores, and implied decimal odds.
      </div>
      <table class="param-table">
        <tr><th>Parameter</th><th>Type</th><th>Required</th><th>Description</th></tr>
        <tr>
          <td class="param-name">sport</td>
          <td class="param-type">string</td>
          <td class="param-req">required</td>
          <td>One of: <code>nfl</code>, <code>mlb</code>, <code>nba</code>, <code>soccer</code>, <code>cricket</code>, <code>tennis</code></td>
        </tr>
        <tr>
          <td class="param-name">team_a</td>
          <td class="param-type">string</td>
          <td class="param-req">required</td>
          <td>Full name of team/player A (must match roster exactly)</td>
        </tr>
        <tr>
          <td class="param-name">team_b</td>
          <td class="param-type">string</td>
          <td class="param-req">required</td>
          <td>Full name of team/player B (must match roster exactly)</td>
        </tr>
        <tr>
          <td class="param-name">best_of</td>
          <td class="param-type">integer</td>
          <td class="param-opt">optional</td>
          <td>Tennis only. Match format: <code>3</code> or <code>5</code>. Default: <code>5</code></td>
        </tr>
      </table>
      <div class="code-block"><span class="c"># Example request</span>
<span class="k">curl</span> -X POST http://localhost:5000/predict \
  -H <span class="s">"Content-Type: application/json"</span> \
  -d <span class="s">&#39;{
    &quot;sport&quot;: &quot;soccer&quot;,
    &quot;team_a&quot;: &quot;Argentina&quot;,
    &quot;team_b&quot;: &quot;France&quot;
  }&#39;</span>

<span class="c"># Example response</span>
{
  <span class="n">"meta"</span>: { <span class="s">"sport"</span>: <span class="s">"SOCCER"</span>, <span class="s">"simulations"</span>: 1000, <span class="s">"generated"</span>: <span class="s">"..."</span> },
  <span class="n">"teams"</span>: { <span class="s">"a"</span>: <span class="s">"Argentina"</span>, <span class="s">"b"</span>: <span class="s">"France"</span> },
  <span class="n">"simulation"</span>: {
    <span class="s">"win_prob_a"</span>: 0.421, <span class="s">"win_prob_b"</span>: 0.338,
    <span class="s">"draw_prob"</span>: 0.241,
    <span class="s">"proj_goals_a"</span>: 1.58, <span class="s">"proj_goals_b"</span>: 1.21, <span class="s">"proj_total"</span>: 2.79
  },
  <span class="n">"implied_odds"</span>: { <span class="s">"team_a_decimal"</span>: 2.375, <span class="s">"team_b_decimal"</span>: 2.959 }
}</div>

      <!-- Try It -->
      <div class="try-it">
        <h4>Try It</h4>
        <div class="form-row">
          <div class="form-group">
            <label>Sport</label>
            <select id="ti-sport" onchange="updateRosters()">
              <option value="nfl">🏈 NFL</option>
              <option value="mlb">⚾ MLB</option>
              <option value="nba">🏀 NBA</option>
              <option value="soccer" selected>⚽ Soccer</option>
              <option value="cricket">🏏 Cricket</option>
              <option value="tennis">🎾 Tennis</option>
            </select>
          </div>
          <div class="form-group">
            <label>Best Of (Tennis only)</label>
            <select id="ti-bestof">
              <option value="5">5 Sets</option>
              <option value="3">3 Sets</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Team / Player A</label>
            <select id="ti-team-a"></select>
          </div>
          <div class="form-group">
            <label>Team / Player B</label>
            <select id="ti-team-b"></select>
          </div>
        </div>
        <button class="btn-run" id="run-btn" onclick="runPredict()">Run Simulation →</button>
        <pre id="result-box"></pre>
      </div>
    </div>

    <!-- GET /health -->
    <div id="health" class="endpoint-card">
      <div class="endpoint-header">
        <span class="method-badge method-get">GET</span>
        <span class="endpoint-path">/health</span>
      </div>
      <div class="endpoint-desc">Health check. Returns engine status and uptime.</div>
      <div class="code-block"><span class="k">curl</span> http://localhost:5000/health

{ <span class="n">"status"</span>: <span class="s">"ok"</span>, <span class="n">"engine"</span>: <span class="s">"Sports Analytics Engine v1.0"</span>, <span class="n">"sports_loaded"</span>: 6 }</div>
    </div>

    <!-- GET /roster -->
    <div id="roster" class="endpoint-card">
      <div class="endpoint-header">
        <span class="method-badge method-get">GET</span>
        <span class="endpoint-path">/roster</span>
      </div>
      <div class="endpoint-desc">Returns all valid team/player names for each sport.</div>
      <div class="code-block"><span class="k">curl</span> http://localhost:5000/roster</div>
    </div>

    <!-- Roster Reference -->
    <div id="rosters" style="margin-top: 48px;">
      <h2 style="margin-bottom:8px">Roster Reference</h2>
      <p class="subtitle">Exact names required in API requests.</p>
      {% for sport, teams in rosters.items() %}
      <div class="sport-section">
        <h3>{{ sport }}</h3>
        <div class="roster-grid">
          {% for t in teams %}<span class="roster-tag">{{ t }}</span>{% endfor %}
        </div>
      </div>
      {% endfor %}
    </div>
  </main>
</div>

<script>
const ROSTERS = {{ rosters_json | safe }};

function updateRosters() {
  const sport = document.getElementById('ti-sport').value;
  const teams = ROSTERS[sport] || [];
  const selA  = document.getElementById('ti-team-a');
  const selB  = document.getElementById('ti-team-b');
  selA.innerHTML = teams.map(t => `<option>${t}</option>`).join('');
  selB.innerHTML = teams.map((t,i) => `<option ${i===1?'selected':''}>${t}</option>`).join('');
  document.getElementById('ti-bestof').parentElement.parentElement.style.opacity =
    sport === 'tennis' ? '1' : '0.3';
}

async function runPredict() {
  const sport  = document.getElementById('ti-sport').value;
  const teamA  = document.getElementById('ti-team-a').value;
  const teamB  = document.getElementById('ti-team-b').value;
  const bestOf = parseInt(document.getElementById('ti-bestof').value);
  const btn    = document.getElementById('run-btn');
  const box    = document.getElementById('result-box');

  if (teamA === teamB) { box.style.display='block'; box.textContent='⚠ Select two different teams.'; return; }

  btn.disabled = true; btn.textContent = 'Simulating…';
  box.style.display = 'none';

  const body = { sport, team_a: teamA, team_b: teamB };
  if (sport === 'tennis') body.best_of = bestOf;

  try {
    const res  = await fetch('/predict', { method:'POST',
      headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
    const data = await res.json();
    box.style.display = 'block';
    box.textContent = JSON.stringify(data, null, 2);
  } catch(e) {
    box.style.display = 'block';
    box.textContent = '❌ Request failed: ' + e.message;
  } finally {
    btn.disabled = false; btn.textContent = 'Run Simulation →';
  }
}

updateRosters();
</script>
</body>
</html>"""


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(
        HOME_HTML,
        rosters=ALL_ROSTERS,
        rosters_json=json.dumps(ALL_ROSTERS)
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "engine": "Sports Analytics Engine v1.0",
        "sports_loaded": len(SIMULATORS),
        "simulations_per_run": SIMULATIONS,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    })


@app.route("/roster", methods=["GET"])
def roster():
    return jsonify({
        "sports": ALL_ROSTERS,
        "note": "Use exact names in /predict requests (case-sensitive)",
    })


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON with Content-Type: application/json"}), 400

    sport  = (data.get("sport") or "").lower().strip()
    team_a = (data.get("team_a") or "").strip()
    team_b = (data.get("team_b") or "").strip()

    # Validation
    if not sport:
        return jsonify({"error": "Missing required field: sport"}), 400
    if sport not in SIMULATORS:
        return jsonify({
            "error": f"Unknown sport: '{sport}'",
            "valid_sports": list(SIMULATORS.keys()),
        }), 400
    if not team_a or not team_b:
        return jsonify({"error": "Missing required fields: team_a and team_b"}), 400
    if team_a == team_b:
        return jsonify({"error": "team_a and team_b must be different"}), 400

    # Run simulation
    fn = SIMULATORS[sport]
    kwargs = {}
    if sport == "tennis":
        best_of = data.get("best_of", 5)
        if best_of not in (3, 5):
            return jsonify({"error": "best_of must be 3 or 5 for tennis"}), 400
        kwargs["best_of"] = best_of

    result = fn(team_a, team_b, **kwargs)

    if result is None:
        # Figure out which name was bad
        roster = ALL_ROSTERS[sport]
        bad = [n for n in (team_a, team_b) if n not in roster]
        return jsonify({
            "error": f"Unknown name(s) for {sport}: {bad}",
            "valid_names": roster,
        }), 404

    # Build implied odds
    implied = {}
    if result.get("win_prob_a", 0) > 0:
        implied["team_a_decimal"] = round(1 / result["win_prob_a"], 3)
    if result.get("win_prob_b", 0) > 0:
        implied["team_b_decimal"] = round(1 / result["win_prob_b"], 3)

    payload = {
        "meta": {
            "sport":       sport.upper(),
            "simulations": SIMULATIONS,
            "generated":   datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "teams":       {"a": team_a, "b": team_b},
        "simulation":  result,
        "implied_odds": implied,
    }

    return jsonify(payload), 200


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
