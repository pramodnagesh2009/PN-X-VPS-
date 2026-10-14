"""
Pro VPS Panel - Railway deployable (single file, no templates folder needed)
Owner: shappno / shappno_codex
"""
import os, json, time, shutil, subprocess, threading, secrets, ssl, uuid, urllib.request
from collections import deque
from pathlib import Path
from functools import wraps
from flask import (
    Flask, request, redirect, url_for, session,
    render_template_string, jsonify, send_from_directory
)
from werkzeug.utils import secure_filename

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
USERS_FILE = DATA_DIR / "users.json"
PRICING_FILE = DATA_DIR / "pricing.json"
FILES_ROOT = APP_DIR / "user_files"
DATA_DIR.mkdir(exist_ok=True)
FILES_ROOT.mkdir(exist_ok=True)

OWNER_USER = "PN"
OWNER_PASS = "22"

DEFAULT_PRICING = {
    "currency": "₹",
    "contact": "TELEGRAM: @ONLY1_PN",
    "plans": [
        {"name": "STARTER", "duration": "24 HOURS",  "price": "49",  "features": "1 FILE RUN, 512MB RAM, REAL-TIME LOGS"},
        {"name": "BASIC",   "duration": "7 DAYS",    "price": "199", "features": "MULTI-FILE UPLOAD, PIP/NPM INSTALL, 24/7 UPTIME"},
        {"name": "PRO",     "duration": "30 DAYS",   "price": "599", "features": "UNLIMITED MODULES, PRIORITY SUPPORT, AUTO-RESTART"},
        {"name": "PREMIUM", "duration": "LIFETIME",  "price": "1999","features": "ALL FEATURES, CUSTOM DOMAIN, DEDICATED HELP"},
    ],
}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024


# ============================================================
#                      UI (CSS + shell)
# ============================================================

CSS = """
:root{
  --bg:#04050a; --bg2:#0a0c14; --card:rgba(15,17,26,.82);
  --border:rgba(255,255,255,.06); --border-hi:rgba(255,255,255,.13);
  --txt:#eef2ff; --txt-dim:#98a0b8; --txt-mute:#5c6379;
  --p1:#7c5cff; --p2:#12b8ff; --p3:#ff4da6;
  --grad:linear-gradient(135deg,#7c5cff 0%,#12b8ff 50%,#ff4da6 100%);
  --ok:#22c55e; --warn:#f59e0b; --err:#ef4444;
  --r:12px;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{min-height:100%}
body{
  font-family:'El Messiri',system-ui,-apple-system,"Segoe UI",sans-serif;
  background:var(--bg); color:var(--txt); line-height:1.5;
  min-height:100vh; overflow-x:hidden; display:flex; flex-direction:column;
  -webkit-font-smoothing:antialiased;
  text-transform:uppercase; letter-spacing:.3px; font-size:14.5px;
}
a{color:inherit;text-decoration:none}
code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  font-size:.82em;background:rgba(124,92,255,.14);padding:2px 6px;
  border-radius:5px;color:#c2b4ff;text-transform:none}
em{font-style:normal}
input,select,textarea,button{text-transform:uppercase;letter-spacing:.3px;font-family:inherit}
input::placeholder,textarea::placeholder{text-transform:none;letter-spacing:0}

/* Background */
.bg-orbs{position:fixed;inset:0;z-index:-1;overflow:hidden;pointer-events:none}
.orb{position:absolute;border-radius:50%;filter:blur(120px);opacity:.32;animation:float 22s ease-in-out infinite}
.orb-1{width:560px;height:560px;background:radial-gradient(circle,#7c5cff,transparent 70%);top:-180px;left:-160px}
.orb-2{width:480px;height:480px;background:radial-gradient(circle,#12b8ff,transparent 70%);bottom:-180px;right:-140px;animation-delay:-8s}
.orb-3{width:400px;height:400px;background:radial-gradient(circle,#ff4da6,transparent 70%);top:45%;left:60%;animation-delay:-15s;opacity:.20}
@keyframes float{0%,100%{transform:translate(0,0) scale(1)}50%{transform:translate(50px,-40px) scale(1.07)}}

/* Navbar */
.navbar{position:sticky;top:0;z-index:50;backdrop-filter:blur(22px);
  background:rgba(4,5,10,.80);border-bottom:1px solid var(--border)}
.nav-inner{max-width:1180px;margin:0 auto;padding:12px 22px;
  display:flex;align-items:center;justify-content:space-between;gap:14px}
.brand{display:flex;align-items:center;gap:8px;font-weight:700;font-size:1.12rem}
.brand-icon{font-size:1.25rem;filter:drop-shadow(0 0 12px rgba(124,92,255,.9))}
.brand-text em{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.brand-text{letter-spacing:1px}
.nav-links{display:flex;align-items:center;gap:5px;font-weight:600;font-size:.82rem}
.nav-links a{padding:7px 13px;border-radius:9px;color:var(--txt-dim);transition:.2s}
.nav-links a:hover{color:var(--txt);background:rgba(255,255,255,.05)}
.btn-primary-sm{background:var(--grad);color:#04050a !important;padding:8px 16px !important;border-radius:9px;font-weight:700}
.btn-ghost{color:var(--txt-mute) !important}

/* Layout */
.main{flex:1;max-width:1180px;width:100%;margin:0 auto;padding:34px 22px}
.footer{text-align:center;padding:26px 20px;color:var(--txt-mute);font-size:.76rem;
  border-top:1px solid var(--border);margin-top:40px;letter-spacing:.5px}
.footer strong{color:var(--txt-dim)}

/* Buttons */
.btn-primary{display:inline-flex;align-items:center;gap:7px;background:var(--grad);
  color:#04050a !important;font-weight:700;padding:12px 24px;border-radius:11px;
  border:none;cursor:pointer;font-size:.86rem;letter-spacing:.6px;
  box-shadow:0 12px 30px -12px rgba(124,92,255,.7);transition:.22s}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 16px 40px -12px rgba(124,92,255,.9)}
.btn-ghost-lg{display:inline-flex;align-items:center;gap:7px;padding:12px 22px;border-radius:11px;
  border:1px solid var(--border-hi);color:var(--txt);font-weight:600;font-size:.86rem;
  background:rgba(255,255,255,.03);transition:.22s}
.btn-ghost-lg:hover{background:rgba(255,255,255,.07);border-color:var(--p1)}
.btn-sm{padding:6px 12px;font-size:.74rem;border-radius:8px;border:none;cursor:pointer;
  font-weight:700;transition:.2s;letter-spacing:.4px}
.btn-ok{background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff}
.btn-err{background:linear-gradient(135deg,#ef4444,#b91c1c);color:#fff}
.btn-warn{background:linear-gradient(135deg,#f59e0b,#d97706);color:#fff}
.btn-info{background:linear-gradient(135deg,#7c5cff,#12b8ff);color:#04050a}
.btn-sm:hover{transform:translateY(-1px);filter:brightness(1.12)}

/* Cards */
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);
  padding:22px;backdrop-filter:blur(16px);box-shadow:0 20px 48px -22px rgba(0,0,0,.7)}
.card h2{font-size:1.05rem;margin-bottom:4px;letter-spacing:.6px}
.card-sub{color:var(--txt-mute);font-size:.76rem;margin-bottom:16px;letter-spacing:.4px}

/* Hero */
.hero{text-align:center;padding:44px 0 20px}
.badge{display:inline-block;padding:6px 14px;border-radius:999px;
  background:rgba(124,92,255,.12);border:1px solid rgba(124,92,255,.32);
  color:#c2b4ff;font-size:.74rem;font-weight:700;margin-bottom:18px;letter-spacing:1px}
.hero h1{font-size:clamp(1.7rem,4.5vw,2.9rem);font-weight:700;line-height:1.2;
  letter-spacing:-.01em;max-width:820px;margin:0 auto 16px}
.grad{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero-sub{color:var(--txt-dim);font-size:.9rem;max-width:560px;margin:0 auto 26px;
  letter-spacing:.4px;text-transform:none}
.hero-cta{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.hero-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));
  gap:12px;max-width:720px;margin:44px auto 0}
.hero-stats>div{background:var(--card);border:1px solid var(--border);
  border-radius:11px;padding:16px;backdrop-filter:blur(10px)}
.hero-stats strong{display:block;font-size:1.3rem;
  background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent;letter-spacing:.5px}
.hero-stats span{color:var(--txt-mute);font-size:.7rem;letter-spacing:.5px}

/* Features */
.section-title{text-align:center;font-size:1.5rem;margin:54px 0 30px;font-weight:700;letter-spacing:.5px}
.feature-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px}
.feature-card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);
  padding:22px;backdrop-filter:blur(16px);transition:.3s}
.feature-card:hover{transform:translateY(-4px);border-color:var(--border-hi);
  box-shadow:0 24px 50px -22px rgba(124,92,255,.45)}
.fc-icon{font-size:1.8rem;margin-bottom:10px}
.feature-card h3{font-size:.96rem;margin-bottom:8px;letter-spacing:.5px}
.feature-card p{color:var(--txt-dim);font-size:.8rem;text-transform:none;letter-spacing:.2px}

/* Pricing */
.pricing-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px;margin-top:24px}
.price-card{background:var(--card);border:1px solid var(--border);border-radius:16px;
  padding:26px 20px;backdrop-filter:blur(16px);position:relative;overflow:hidden;transition:.3s}
.price-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--grad)}
.price-card:hover{transform:translateY(-5px);border-color:var(--border-hi);
  box-shadow:0 28px 60px -22px rgba(124,92,255,.55)}
.price-card.popular{border-color:rgba(124,92,255,.5);transform:scale(1.02)}
.popular-tag{position:absolute;top:12px;right:-30px;background:var(--grad);color:#04050a;
  padding:4px 38px;font-size:.62rem;font-weight:700;transform:rotate(38deg);letter-spacing:1px}
.price-name{font-size:1.02rem;font-weight:700;margin-bottom:3px;letter-spacing:.7px}
.price-dur{color:var(--txt-mute);font-size:.72rem;margin-bottom:16px;letter-spacing:.4px}
.price-amt{font-size:2rem;font-weight:700;line-height:1;
  background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.price-feat{list-style:none;margin:18px 0;padding:0}
.price-feat li{padding:6px 0;color:var(--txt-dim);font-size:.76rem;
  display:flex;gap:7px;align-items:flex-start;text-transform:none;letter-spacing:.2px}
.price-feat li::before{content:'✓';color:var(--ok);font-weight:700;flex-shrink:0}

/* Forms */
.form-row{display:flex;flex-direction:column;gap:6px;margin-bottom:14px}
.form-row label{font-size:.74rem;font-weight:700;color:var(--txt-dim);letter-spacing:.6px}
.input,select,textarea{width:100%;padding:11px 14px;border-radius:10px;
  border:1px solid var(--border);background:rgba(8,10,18,.75);
  color:var(--txt);font-size:.86rem;transition:.22s;outline:none;letter-spacing:.4px}
.input:focus,select:focus,textarea:focus{border-color:var(--p1);
  box-shadow:0 0 0 3px rgba(124,92,255,.18)}
.input::placeholder{color:var(--txt-mute)}

/* Auth */
.auth-wrap{max-width:380px;margin:44px auto}
.auth-wrap .card{padding:30px 26px}
.auth-title{font-size:1.35rem;text-align:center;margin-bottom:4px;letter-spacing:.8px}
.auth-sub{text-align:center;color:var(--txt-mute);margin-bottom:22px;font-size:.8rem;letter-spacing:.4px}
.alert{padding:10px 14px;border-radius:9px;font-size:.8rem;margin-bottom:16px;letter-spacing:.4px}
.alert-err{background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.35);color:#fca5a5}

/* Dashboard */
.dash-head{display:flex;flex-wrap:wrap;gap:14px;justify-content:space-between;
  align-items:center;margin-bottom:22px}
.dash-title{font-size:1.28rem;font-weight:700;letter-spacing:.6px}
.dash-title span{font-size:.76rem;color:var(--txt-mute);font-weight:400;display:block;letter-spacing:.4px;margin-top:2px}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:860px){.grid-2{grid-template-columns:1fr}}
.pill{display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:999px;
  font-size:.68rem;font-weight:700;letter-spacing:.5px}
.pill-ok{background:rgba(34,197,94,.14);color:#4ade80;border:1px solid rgba(34,197,94,.3)}
.pill-off{background:rgba(107,114,128,.14);color:#9ca3af;border:1px solid rgba(107,114,128,.3)}
.pill-warn{background:rgba(245,158,11,.14);color:#fbbf24;border:1px solid rgba(245,158,11,.3)}
.dot{width:7px;height:7px;border-radius:50%;background:currentColor;
  box-shadow:0 0 8px currentColor;animation:pulse 1.8s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

/* File list */
.file-list{list-style:none;padding:0;margin:0}
.file-list li{display:flex;justify-content:space-between;align-items:center;
  padding:10px 12px;border-radius:9px;border:1px solid var(--border);
  background:rgba(255,255,255,.02);margin-bottom:7px;gap:9px;flex-wrap:wrap}
.file-list .fname{font-weight:600;word-break:break-all;font-size:.82rem;letter-spacing:.4px}
.file-actions{display:flex;gap:6px;flex-wrap:wrap}

/* Terminal */
.terminal{background:#020309;border:1px solid var(--border);border-radius:11px;
  padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  font-size:.74rem;line-height:1.5;color:#b8f0c8;
  height:300px;overflow-y:auto;white-space:pre-wrap;word-break:break-word;
  text-transform:none;letter-spacing:0}
.terminal::-webkit-scrollbar{width:7px}
.terminal::-webkit-scrollbar-thumb{background:rgba(124,92,255,.4);border-radius:8px}

/* Toast */
.toast{position:fixed;bottom:22px;right:22px;padding:11px 18px;border-radius:10px;
  background:rgba(15,17,26,.97);border:1px solid var(--border-hi);color:var(--txt);
  font-weight:700;opacity:0;transform:translateY(10px);transition:.3s;z-index:200;
  box-shadow:0 20px 40px -12px rgba(0,0,0,.75);max-width:300px;font-size:.78rem;letter-spacing:.5px}
.toast.show{opacity:1;transform:translateY(0)}
.toast-ok{border-color:rgba(34,197,94,.5)}
.toast-err{border-color:rgba(239,68,68,.5)}

/* Table */
table{width:100%;border-collapse:collapse;font-size:.8rem}
th,td{padding:10px 8px;text-align:left;border-bottom:1px solid var(--border)}
th{color:var(--txt-mute);font-weight:700;font-size:.68rem;letter-spacing:.8px}
td{color:var(--txt-dim);letter-spacing:.3px}
td strong{color:var(--txt)}

/* Tabs */
.tabs{display:flex;gap:4px;margin-bottom:18px;flex-wrap:wrap;border-bottom:1px solid var(--border)}
.tab{padding:9px 15px;border-radius:10px 10px 0 0;background:transparent;border:none;
  color:var(--txt-mute);font-weight:700;cursor:pointer;font-size:.78rem;transition:.2s;letter-spacing:.5px}
.tab:hover{color:var(--txt)}
.tab.active{color:var(--txt);background:rgba(124,92,255,.12);border-bottom:2px solid var(--p1)}
.tab-panel{display:none}
.tab-panel.active{display:block;animation:fade .3s}
@keyframes fade{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}

@media(max-width:640px){
  body{font-size:13px}
  .main{padding:22px 14px}
  .nav-inner{padding:11px 14px}
  .brand{font-size:1rem}
  .nav-links a{padding:6px 10px;font-size:.72rem}
  .card{padding:18px}
  .hero h1{font-size:1.5rem}
}
"""

NAV_TPL = """
<nav class="navbar">
  <div class="nav-inner">
    <a href="{{ url_for('home') }}" class="brand">
      <span class="brand-icon">💀</span>
      <span class="brand-text">PN <em>X</em> VPS</span>
    </a>
    <div class="nav-links">
      {% if session.get('role') == 'owner' %}
        <a href="{{ url_for('owner_dashboard') }}">DASHBOARD</a>
        <a href="{{ url_for('pinger_page') }}">PINGER</a>
        <a href="{{ url_for('logout') }}" class="btn-ghost">LOGOUT</a>
      {% elif session.get('role') == 'user' %}
        <a href="{{ url_for('user_dashboard') }}">MY SERVER</a>
        <a href="{{ url_for('logout') }}" class="btn-ghost">LOGOUT</a>
      {% else %}
        <a href="{{ url_for('landing') }}">HOME</a>
        <a href="{{ url_for('pricing_page') }}">PRICING</a>
        <a href="{{ url_for('login') }}" class="btn-primary-sm">LOGIN</a>
      {% endif %}
    </div>
  </div>
</nav>
"""

BASE_SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=El+Messiri:wght@400;600;700&display=swap" rel="stylesheet">
<style>__CSS__</style>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>💀</text></svg>">
</head>
<body>
<div class="bg-orbs">
  <div class="orb orb-1"></div><div class="orb orb-2"></div><div class="orb orb-3"></div>
</div>
__NAV__
<main class="main">
__CONTENT__
</main>
<footer class="footer">
  <p>© 2026 PN X VPS 💀 · POWERED BY <strong>SHAPPNO / PN</strong></p>
</footer>
<script>
function toast(msg, type){
  type = type || 'info';
  var el = document.createElement('div');
  el.className = 'toast toast-' + type;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(function(){ el.classList.add('show'); }, 10);
  setTimeout(function(){
    el.classList.remove('show');
    setTimeout(function(){ el.remove(); }, 300);
  }, 2600);
}
</script>
__SCRIPTS__
</body>
</html>
"""


def render_page(title, content_tpl, extra_scripts="", **ctx):
    """Render a full page by rendering content + nav separately, then injecting into shell."""
    content = render_template_string(content_tpl, **ctx)
    nav = render_template_string(NAV_TPL)
    scripts = render_template_string(extra_scripts, **ctx) if extra_scripts else ""
    html = (BASE_SHELL
            .replace("__TITLE__", title)
            .replace("__CSS__", CSS)
            .replace("__NAV__", nav)
            .replace("__CONTENT__", content)
            .replace("__SCRIPTS__", scripts))
    return html


# ============================================================
#                    STORAGE
# ============================================================
_lock = threading.Lock()

def load_users():
    if not USERS_FILE.exists():
        return {}
    try:
        return json.loads(USERS_FILE.read_text())
    except Exception:
        return {}

def save_users(u):
    with _lock:
        USERS_FILE.write_text(json.dumps(u, indent=2))

def load_pricing():
    if not PRICING_FILE.exists():
        save_pricing(DEFAULT_PRICING)
        return DEFAULT_PRICING
    try:
        return json.loads(PRICING_FILE.read_text())
    except Exception:
        return DEFAULT_PRICING

def save_pricing(p):
    with _lock:
        PRICING_FILE.write_text(json.dumps(p, indent=2))

def user_dir(username):
    d = FILES_ROOT / username
    d.mkdir(parents=True, exist_ok=True)
    return d


# ============================================================
#                    PROCESS MANAGER (with AUTO-RESTART)
# ============================================================
PROCS = {}
MAX_RESTART_DELAY = 30  # cap for exponential backoff


def _spawn(username, filename):
    """Launch a process and register it. Returns (ok, msg_or_proc)."""
    udir = user_dir(username)
    fpath = udir / filename
    if not fpath.exists():
        return False, "File not found"
    ext = fpath.suffix.lower()
    if ext == ".py":
        cmd = ["python", "-u", str(fpath)]
    elif ext in (".js", ".mjs", ".cjs"):
        cmd = ["node", str(fpath)]
    elif ext == ".sh":
        cmd = ["bash", str(fpath)]
    else:
        return False, f"Unsupported file type: {ext}"
    try:
        proc = subprocess.Popen(
            cmd, cwd=str(udir),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1,
        )
    except FileNotFoundError as e:
        return False, f"Runtime not installed: {e}"
    return True, (proc, cmd)


def _reader(username, proc):
    """Read process output. On exit, auto-restart if enabled."""
    info = PROCS.get(username)
    if not info:
        return
    buf = info["logs"]

    try:
        for line in iter(proc.stdout.readline, b""):
            try:
                txt = line.decode("utf-8", errors="replace").rstrip()
            except Exception:
                txt = str(line)
            buf.append(f"[{time.strftime('%H:%M:%S')}] {txt}")
    except Exception as e:
        buf.append(f"[reader-error] {e}")

    code = proc.poll()
    buf.append(f"[exit] PROCESS ENDED WITH CODE {code}")

    # ------ AUTO-RESTART DECISION ------
    cur = PROCS.get(username)
    if not cur or cur.get("proc") is not proc:
        return  # user switched to a different process
    if cur.get("stopping"):
        return  # user manually stopped
    if not cur.get("auto_restart", True):
        return  # auto-restart disabled for this process

    fname = cur.get("file")
    if not fname:
        return

    # Increment restart counter
    cur["restart_count"] = cur.get("restart_count", 0) + 1
    rc = cur["restart_count"]
    delay = min(MAX_RESTART_DELAY, 2 ** min(rc, 5))  # 2,4,8,16,30,30...

    buf.append(f"[auto-restart] ♻ CRASH DETECTED — RESTARTING IN {delay}s (ATTEMPT #{rc})")

    # Sleep with stop-check
    for _ in range(delay):
        c2 = PROCS.get(username)
        if not c2 or c2.get("proc") is not proc or c2.get("stopping"):
            return
        time.sleep(1)

    # Relaunch
    c3 = PROCS.get(username)
    if not c3 or c3.get("proc") is not proc or c3.get("stopping"):
        return

    ok, res = _spawn(username, fname)
    if not ok:
        buf.append(f"[auto-restart] ✗ FAILED: {res}")
        return

    new_proc, cmd = res

    # Replace entry, keep logs and restart_count
    PROCS[username] = {
        "proc": new_proc,
        "logs": buf,
        "file": fname,
        "restart_count": rc,
        "auto_restart": True,
        "stopping": False,
    }
    buf.append(f"[auto-restart] ✓ RESTARTED — {' '.join(cmd)} (PID {new_proc.pid})")

    t = threading.Thread(target=_reader, args=(username, new_proc), daemon=True)
    t.start()
    PROCS[username]["thread"] = t


def start_process(username, filename):
    stop_process(username)
    ok, res = _spawn(username, filename)
    if not ok:
        return False, res
    proc, cmd = res
    logs = deque(maxlen=2000)
    logs.append(f"[start] {' '.join(cmd)}")
    PROCS[username] = {
        "proc": proc,
        "logs": logs,
        "file": filename,
        "restart_count": 0,
        "auto_restart": True,
        "stopping": False,
    }
    t = threading.Thread(target=_reader, args=(username, proc), daemon=True)
    t.start()
    PROCS[username]["thread"] = t
    return True, "started"


def stop_process(username):
    info = PROCS.get(username)
    if not info:
        return False
    info["stopping"] = True
    info["auto_restart"] = False
    p = info["proc"]
    if p.poll() is None:
        try:
            p.terminate()
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()
        except Exception:
            pass
        info["logs"].append("[stop] PROCESS TERMINATED (AUTO-RESTART DISABLED)")
    return True


def is_running(username):
    info = PROCS.get(username)
    return bool(info and info["proc"].poll() is None)

def get_logs(username):
    info = PROCS.get(username)
    return list(info["logs"]) if info else []


# ============================================================
#                    INSTALL MODULE
# ============================================================
INSTALL_LOGS = {}

def run_install(username, command):
    parts = command.strip().split()
    if not parts:
        return False, "empty command"
    if parts[0] not in ("pip", "pip3", "npm"):
        return False, "Only 'pip install <pkg>' or 'npm install <pkg>' allowed"
    if len(parts) < 3 or parts[1] != "install":
        return False, "Format: pip install <module>  OR  npm install <module>"
    if any(c in command for c in [";", "&", "|", "`", "$(", ">"]):
        return False, "Invalid characters"
    logs = INSTALL_LOGS.setdefault(username, deque(maxlen=1000))
    logs.append(f"[install] $ {command}")
    cwd = str(user_dir(username))
    def worker():
        try:
            p = subprocess.Popen(parts, cwd=cwd,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in iter(p.stdout.readline, b""):
                logs.append(line.decode("utf-8", errors="replace").rstrip())
            p.wait()
            logs.append(f"[install] finished with code {p.returncode}")
        except Exception as e:
            logs.append(f"[install-error] {e}")
    threading.Thread(target=worker, daemon=True).start()
    return True, "installing"


# ============================================
#  WEBSITE PINGER MANAGER
# ============================================
PINGERS = {}  # {id: {url, interval, hold, thread, stop_flag, logs, stats, ...}}

PINGER_DIR = APP_DIR / "pinger_data"
PINGER_DIR.mkdir(exist_ok=True)
PINGER_FILE = PINGER_DIR / "pingers.json"


def save_pingers():
    data = {}
    for pid, info in PINGERS.items():
        data[pid] = {
            "url": info["url"],
            "interval": info["interval"],
            "hold": info["hold"],
            "enabled": info.get("enabled", True),
        }
    try:
        PINGER_FILE.write_text(json.dumps(data, indent=2))
    except Exception as e:
        print(f"[PINGER SAVE ERROR] {e}")


def load_pingers():
    if not PINGER_FILE.exists():
        return
    try:
        data = json.loads(PINGER_FILE.read_text())
        for pid, cfg in data.items():
            add_pinger(
                url=cfg["url"],
                interval=cfg.get("interval", 300),
                hold=cfg.get("hold", 10),
                pid=pid,
                enabled=cfg.get("enabled", True),
                _silent=True,
            )
        print(f"[PINGER] Loaded {len(data)} pinger(s) from disk")
    except Exception as e:
        print(f"[PINGER LOAD ERROR] {e}")


def _pinger_worker(pid):
    info = PINGERS.get(pid)
    if not info:
        return

    logs = info["logs"]
    url = info["url"]
    interval = info["interval"]
    hold = info["hold"]

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    while not info["stop_flag"].is_set():
        if not info.get("enabled", True):
            time.sleep(1)
            continue

        ts = time.strftime("%H:%M:%S")
        logs.append(f"[{ts}] → PING: {url}")

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (NexusPinger/1.0)"}
            )
            with urllib.request.urlopen(req, timeout=hold + 5, context=ctx) as resp:
                status = resp.status
                try:
                    resp.read(1024)
                except Exception:
                    pass
            logs.append(f"[{ts}] ✓ ONLINE (HTTP {status}) — holding {hold}s")
            info["stats"]["success"] += 1
            info["stats"]["last_status"] = f"HTTP {status}"
            info["stats"]["last_ok"] = time.time()

            end_time = time.time() + hold
            while time.time() < end_time and not info["stop_flag"].is_set():
                time.sleep(1)

        except Exception as e:
            info["stats"]["fail"] += 1
            info["stats"]["last_status"] = f"ERROR: {type(e).__name__}"
            info["stats"]["last_fail"] = time.time()
            logs.append(f"[{ts}] ✗ FAILED: {type(e).__name__}: {e}")
            logs.append(f"[{ts}] ↻ RETRY IN 5s...")
            for _ in range(5):
                if info["stop_flag"].is_set():
                    break
                time.sleep(1)
            continue

        wait = max(0, interval - hold)
        logs.append(f"[{ts}] ⏱ NEXT PING IN {wait}s")
        for _ in range(wait):
            if info["stop_flag"].is_set():
                break
            time.sleep(1)

    logs.append(f"[{time.strftime('%H:%M:%S')}] ⏹ PINGER STOPPED")


def add_pinger(url, interval=300, hold=10, pid=None, enabled=True, _silent=False):
    if not url:
        return False, "URL REQUIRED"
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        interval = max(10, int(interval))
        hold = max(1, min(300, int(hold)))
    except Exception:
        return False, "INVALID INTERVAL/HOLD"

    pid = pid or uuid.uuid4().hex[:10]

    info = {
        "id": pid,
        "url": url,
        "interval": interval,
        "hold": hold,
        "enabled": enabled,
        "stop_flag": threading.Event(),
        "logs": deque(maxlen=500),
        "stats": {
            "success": 0,
            "fail": 0,
            "last_status": "—",
            "last_ok": None,
            "last_fail": None,
            "started": time.time(),
        },
    }
    info["logs"].append(f"[START] PINGER {url} | every {interval}s | hold {hold}s")
    PINGERS[pid] = info

    t = threading.Thread(target=_pinger_worker, args=(pid,), daemon=True)
    t.start()
    info["thread"] = t

    if not _silent:
        save_pingers()
    return True, pid


def remove_pinger(pid):
    info = PINGERS.get(pid)
    if not info:
        return False
    info["stop_flag"].set()
    PINGERS.pop(pid, None)
    save_pingers()
    return True


def toggle_pinger(pid):
    info = PINGERS.get(pid)
    if not info:
        return False, "NOT FOUND"
    info["enabled"] = not info.get("enabled", True)
    state = "ON" if info["enabled"] else "OFF"
    info["logs"].append(f"[{time.strftime('%H:%M:%S')}] ⚙ PINGER {state}")
    save_pingers()
    return True, state


def get_pinger_info(pid):
    info = PINGERS.get(pid)
    if not info:
        return None
    return {
        "id": info["id"],
        "url": info["url"],
        "interval": info["interval"],
        "hold": info["hold"],
        "enabled": info["enabled"],
        "logs": list(info["logs"]),
        "stats": info["stats"],
    }


def get_all_pingers():
    return {pid: get_pinger_info(pid) for pid in PINGERS}


# ============================================================
#                       AUTH
# ============================================================
def is_owner():
    return session.get("role") == "owner"

def current_user():
    return session.get("username")

def user_valid(username):
    users = load_users()
    u = users.get(username)
    if not u:
        return False, "User not found"
    if u.get("expires_at") and time.time() > u["expires_at"]:
        del users[username]
        save_users(users)
        stop_process(username)
        return False, "Account expired"
    return True, u

def require_owner(f):
    @wraps(f)
    def w(*a, **kw):
        if not is_owner():
            return redirect(url_for("login"))
        return f(*a, **kw)
    return w

def require_user(f):
    @wraps(f)
    def w(*a, **kw):
        u = current_user()
        if not u or session.get("role") != "user":
            return redirect(url_for("login"))
        ok, _ = user_valid(u)
        if not ok:
            session.clear()
            return redirect(url_for("login"))
        return f(*a, **kw)
    return w


# ============================================================
#                    PAGE TEMPLATES
# ============================================================

LANDING_TPL = """
<section class="hero">
  <span class="badge">🚀 PREMIUM VPS HOSTING</span>
  <h1>RUN YOUR <span class="grad">PYTHON</span>, <span class="grad">NODE.JS</span> &amp; <span class="grad">SHELL</span> SCRIPTS 24/7</h1>
  <p class="hero-sub">A clean, powerful control panel with live logs, module installer, and instant deployment — all from your browser.</p>
  <div class="hero-cta">
    <a href="{{ url_for('pricing_page') }}" class="btn-primary">💰 VIEW PRICING</a>
    <a href="{{ url_for('login') }}" class="btn-ghost-lg">🔐 CLIENT LOGIN →</a>
  </div>
  <div class="hero-stats">
    <div><strong>99.9%</strong><span>UPTIME</span></div>
    <div><strong>200MB</strong><span>UPLOAD LIMIT</span></div>
    <div><strong>24/7</strong><span>AUTO RESTART</span></div>
    <div><strong>1-CLICK</strong><span>DEPLOY</span></div>
  </div>
</section>

<section>
  <h2 class="section-title">EVERYTHING YOU NEED TO <span class="grad">SHIP FAST</span></h2>
  <div class="feature-grid">
    <div class="feature-card"><div class="fc-icon">🐍</div><h3>MULTI-RUNTIME</h3>
      <p>Run <code>.py</code>, <code>.js</code>, and <code>.sh</code> files with a single click. Python, Node.js and Bash supported.</p></div>
    <div class="feature-card"><div class="fc-icon">📡</div><h3>LIVE LOGS</h3>
      <p>Real-time stdout/stderr streaming so you always know exactly what your script is doing.</p></div>
    <div class="feature-card"><div class="fc-icon">♻</div><h3>AUTO-RESTART</h3>
      <p>If your script crashes, the panel restarts it automatically with smart backoff. Never stays down.</p></div>
    <div class="feature-card"><div class="fc-icon">📦</div><h3>MODULE INSTALLER</h3>
      <p>Install Python packages with <code>pip</code> or Node modules with <code>npm</code> — right from the panel.</p></div>
    <div class="feature-card"><div class="fc-icon">🔐</div><h3>PER-USER ISOLATION</h3>
      <p>Every client gets their own sandboxed directory, tokens, and process slot. No cross-access.</p></div>
    <div class="feature-card"><div class="fc-icon">🎛️</div><h3>OWNER CONTROL</h3>
      <p>Create users, set expiry, extend time, and edit pricing plans in real time.</p></div>
  </div>
</section>
"""

PRICING_TPL = """
<h1 class="section-title" style="margin-top:6px">SIMPLE, <span class="grad">HONEST PRICING</span></h1>
<p style="text-align:center;color:var(--txt-dim);max-width:520px;margin:0 auto 6px;font-size:.84rem">
  PICK A PLAN AND START HOSTING YOUR SCRIPTS IN MINUTES.
</p>
<div class="pricing-grid">
  {% for p in pricing.plans %}
  <div class="price-card {% if loop.index == 3 %}popular{% endif %}">
    {% if loop.index == 3 %}<div class="popular-tag">POPULAR</div>{% endif %}
    <div class="price-name">{{ p.name }}</div>
    <div class="price-dur">{{ p.duration }}</div>
    <div class="price-amt">{{ pricing.currency }}{{ p.price }}</div>
    <ul class="price-feat">
      {% for f in p.features.split(',') %}
        {% if f.strip() %}<li>{{ f.strip() }}</li>{% endif %}
      {% endfor %}
    </ul>
    <a href="{{ url_for('login') }}" class="btn-primary" style="width:100%;justify-content:center">GET STARTED</a>
  </div>
  {% endfor %}
</div>
<div style="text-align:center;margin-top:30px;color:var(--txt-mute);font-size:.78rem">
  NEED HELP? <strong style="color:var(--txt-dim)">{{ pricing.contact }}</strong>
</div>
"""

LOGIN_TPL = """
<div class="auth-wrap">
  <div class="card">
    <h1 class="auth-title">💀 WELCOME BACK</h1>
    <p class="auth-sub">SIGN IN TO ACCESS YOUR VPS PANEL</p>
    {% if error %}<div class="alert alert-err">{{ error }}</div>{% endif %}
    <form method="post">
      <div class="form-row">
        <label>USERNAME</label>
        <input class="input" name="username" placeholder="your username" required autofocus>
      </div>
      <div class="form-row">
        <label>PASSWORD</label>
        <input class="input" name="password" type="password" placeholder="••••••••" required>
      </div>
      <button class="btn-primary" style="width:100%;justify-content:center;margin-top:6px">SIGN IN →</button>
    </form>
    <p style="text-align:center;margin-top:16px;color:var(--txt-mute);font-size:.76rem">
      NEW HERE? <a href="{{ url_for('pricing_page') }}" style="color:#c2b4ff">VIEW PLANS</a>
    </p>
  </div>
</div>
"""

USER_TPL = """
<div class="dash-head">
  <div class="dash-title">
    HEY, <span class="grad">{{ username }}</span>
    <span>
      {% if running %}<span class="pill pill-ok"><span class="dot"></span>RUNNING · {{ running_file }}</span>
      {% else %}<span class="pill pill-off">● STOPPED</span>{% endif %}
    </span>
  </div>
  <div style="text-align:right;color:var(--txt-mute);font-size:.74rem">
    EXPIRES: <strong style="color:var(--txt-dim)" id="expires-at" data-ts="{{ expires_at }}">—</strong>
  </div>
</div>

<div class="tabs">
  <button class="tab active" data-tab="files">📁 FILES</button>
  <button class="tab" data-tab="control">🎛️ CONTROL</button>
  <button class="tab" data-tab="logs">📡 LIVE LOGS</button>
  <button class="tab" data-tab="install">📦 INSTALL</button>
</div>

<div class="tab-panel active" id="panel-files">
  <div class="card" style="margin-bottom:16px">
    <h2>UPLOAD FILES</h2>
    <p class="card-sub">SUPPORTED: .PY, .JS, .MJS, .CJS, .SH — MAX 200MB</p>
    <form method="post" action="{{ url_for('upload') }}" enctype="multipart/form-data">
      <div class="form-row"><input class="input" type="file" name="files" multiple required></div>
      <button class="btn-primary">⬆ UPLOAD</button>
    </form>
  </div>
  <div class="card">
    <h2>YOUR FILES ({{ files|length }})</h2>
    <p class="card-sub">CLICK RUN TO START. CRASHES AUTO-RESTART WITH BACKOFF.</p>
    {% if files %}
    <ul class="file-list">
      {% for f in files %}
      <li>
        <span class="fname">📄 {{ f }}</span>
        <div class="file-actions">
          <button class="btn-sm btn-ok" onclick="startFile('{{ f }}')">▶ RUN</button>
          <a class="btn-sm btn-info" href="{{ url_for('file_view', name=f) }}" target="_blank" style="text-decoration:none">👁 VIEW</a>
          <form method="post" action="{{ url_for('file_delete', name=f) }}" style="display:inline" onsubmit="return confirm('Delete {{ f }}?')">
            <button class="btn-sm btn-err">🗑</button>
          </form>
        </div>
      </li>
      {% endfor %}
    </ul>
    {% else %}
    <p style="color:var(--txt-mute);padding:16px 0;font-size:.8rem">NO FILES YET. UPLOAD YOUR FIRST SCRIPT ABOVE.</p>
    {% endif %}
  </div>
</div>

<div class="tab-panel" id="panel-control">
  <div class="card">
    <h2>PROCESS CONTROL</h2>
    <p class="card-sub">♻ AUTO-RESTART IS ALWAYS ON — MANUAL STOP DISABLES IT.</p>
    <div style="display:flex;gap:9px;flex-wrap:wrap">
      <button class="btn-sm btn-ok"   onclick="ctl('restart')">🔄 RESTART</button>
      <button class="btn-sm btn-warn" onclick="ctl('stop')">⏹ STOP</button>
      <button class="btn-sm btn-err"  onclick="ctl('delete')">🗑 KILL &amp; CLEAR</button>
    </div>
    <div style="margin-top:20px;font-size:.8rem">
      <strong>STATUS:</strong>
      <span id="status-text" style="color:var(--txt-dim);margin-left:5px">LOADING…</span>
    </div>
    <div style="margin-top:8px;font-size:.8rem">
      <strong>RESTARTS:</strong>
      <span id="restart-text" style="color:var(--txt-dim);margin-left:5px">—</span>
    </div>
  </div>
</div>

<div class="tab-panel" id="panel-logs">
  <div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px">
      <h2 style="margin:0">📡 LIVE OUTPUT</h2>
      <span class="pill" id="log-status">—</span>
    </div>
    <div class="terminal" id="term">Waiting for logs…</div>
    <div style="margin-top:12px;color:var(--txt-mute);font-size:.7rem">AUTO-REFRESHING EVERY 1.5s · LAST 2000 LINES KEPT</div>
  </div>
</div>

<div class="tab-panel" id="panel-install">
  <div class="card">
    <h2>📦 INSTALL MODULES</h2>
    <p class="card-sub">ALLOWED: <code>pip install &lt;pkg&gt;</code> OR <code>npm install &lt;pkg&gt;</code></p>
    <form id="install-form" onsubmit="return doInstall(event)">
      <div class="form-row"><input class="input" id="install-cmd" placeholder="pip install requests" required></div>
      <button class="btn-primary">▶ INSTALL</button>
    </form>
    <div class="terminal" id="install-term" style="margin-top:14px;height:220px;color:#c2b4ff">Install log will appear here…</div>
  </div>
</div>
"""

USER_SCRIPTS = """
<script>
document.querySelectorAll('.tab').forEach(function(t){
  t.addEventListener('click', function(){
    document.querySelectorAll('.tab').forEach(function(x){ x.classList.remove('active'); });
    document.querySelectorAll('.tab-panel').forEach(function(x){ x.classList.remove('active'); });
    t.classList.add('active');
    document.getElementById('panel-' + t.dataset.tab).classList.add('active');
  });
});

var expEl = document.getElementById('expires-at');
if(expEl){
  var ts = parseFloat(expEl.dataset.ts);
  expEl.textContent = ts > 0 ? new Date(ts*1000).toLocaleString() : 'LIFETIME';
}

async function startFile(name){
  var r = await fetch('{{ url_for("server_start") }}', {method:'POST',
    headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:'file=' + encodeURIComponent(name)});
  var j = await r.json();
  toast(j.msg, j.ok ? 'ok' : 'err');
  refresh();
}

async function ctl(action){
  if(action==='stop' && !confirm('Stop the running process?')) return;
  if(action==='delete' && !confirm('Kill process and clear logs?')) return;
  var map = {
    restart: '{{ url_for("server_restart") }}',
    stop: '{{ url_for("server_stop") }}',
    delete: '{{ url_for("server_delete") }}'
  };
  var rr = await fetch(map[action], {method:'POST'});
  var j = await rr.json();
  toast(j.msg || 'done', j.ok ? 'ok' : 'err');
  refresh();
}

async function doInstall(e){
  e.preventDefault();
  var cmd = document.getElementById('install-cmd').value;
  var r = await fetch('{{ url_for("install") }}', {method:'POST',
    headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:'command=' + encodeURIComponent(cmd)});
  var j = await r.json();
  toast(j.msg, j.ok ? 'ok' : 'err');
  return false;
}

var term = document.getElementById('term');
var installTerm = document.getElementById('install-term');
var logStatus = document.getElementById('log-status');
var statusText = document.getElementById('status-text');
var restartText = document.getElementById('restart-text');

async function refresh(){
  try{
    var r = await fetch('{{ url_for("logs_api") }}');
    var j = await r.json();
    logStatus.textContent = j.running ? '● RUNNING' : '● STOPPED';
    logStatus.className = 'pill ' + (j.running ? 'pill-ok' : 'pill-off');
    if(statusText) statusText.textContent = j.running ? ('RUNNING: ' + j.file) : 'STOPPED';
    if(restartText) restartText.textContent = (j.restart_count || 0) + ' TIME(S)';
    if(term){ term.textContent = j.logs.length ? j.logs.join('\\n') : 'No logs yet.'; term.scrollTop = term.scrollHeight; }
    if(installTerm){
      installTerm.textContent = j.install.length ? j.install.join('\\n') : 'Install log will appear here…';
      installTerm.scrollTop = installTerm.scrollHeight;
    }
  } catch(e) {}
}
refresh();
setInterval(refresh, 1500);
</script>
"""

OWNER_TPL = """
<div class="dash-head">
  <div class="dash-title">👑 OWNER PANEL <span>FULL CONTROL OVER USERS, PLANS &amp; BILLING</span></div>
</div>

<div class="tabs">
  <button class="tab active" data-tab="users">👥 USERS</button>
  <button class="tab" data-tab="create">➕ CREATE</button>
  <button class="tab" data-tab="pricing">💰 PRICING</button>
</div>

<div class="tab-panel active" id="panel-users">
  <div class="card">
    <h2>ACTIVE USERS ({{ users|length }})</h2>
    <p class="card-sub">COPY OR OPEN AUTO-LOGIN LINKS FOR YOUR CLIENTS.</p>
    {% if users %}
    <div style="overflow-x:auto">
    <table>
      <thead><tr><th>USERNAME</th><th>STATUS</th><th>EXPIRES</th><th>AUTO-LOGIN</th><th>ACTIONS</th></tr></thead>
      <tbody>
      {% for uname, info in users.items() %}
        {% set exp = info.expires_at or 0 %}
        {% set expired = exp > 0 and now > exp %}
        {% set link = base_url + '/auto/' + info.token %}
        <tr>
          <td><strong>{{ uname }}</strong></td>
          <td>
            {% if expired %}<span class="pill pill-warn">EXPIRED</span>
            {% elif exp == 0 %}<span class="pill pill-ok">LIFETIME</span>
            {% else %}<span class="pill pill-ok"><span class="dot"></span>ACTIVE</span>{% endif %}
          </td>
          <td>{% if exp == 0 %}NEVER{% else %}<span data-ts="{{ exp }}" class="ts"></span>{% endif %}</td>
          <td>
            <div style="display:flex;gap:6px;flex-wrap:wrap">
              <button class="btn-sm btn-info" onclick="copyLink('{{ link }}')">📋 COPY</button>
              <a class="btn-sm btn-ok" href="{{ link }}" target="_blank" style="text-decoration:none">🔗 OPEN</a>
            </div>
          </td>
          <td>
            <form method="post" action="{{ url_for('owner_extend', username=uname) }}" style="display:inline">
              <input class="input" name="hours" value="24" style="width:60px;padding:5px;display:inline-block;font-size:.74rem">
              <button class="btn-sm btn-info">+EXT</button>
            </form>
            <form method="post" action="{{ url_for('owner_delete', username=uname) }}" style="display:inline"
                  onsubmit="return confirm('Delete {{ uname }} and all files?')">
              <button class="btn-sm btn-err">🗑</button>
            </form>
          </td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
    </div>
    {% else %}
    <p style="color:var(--txt-mute);padding:16px 0;font-size:.8rem">NO USERS YET. CREATE ONE FROM THE "CREATE" TAB.</p>
    {% endif %}
  </div>
</div>

<div class="tab-panel" id="panel-create">
  <div class="card" style="max-width:480px">
    <h2>CREATE NEW USER</h2>
    <p class="card-sub">DURATION IN HOURS (0 = LIFETIME, 24 = 1 DAY, 168 = 7 DAYS, 720 = 30 DAYS)</p>
    <form method="post" action="{{ url_for('owner_create') }}">
      <div class="form-row"><label>USERNAME</label>
        <input class="input" name="username" placeholder="e.g. client01" required></div>
      <div class="form-row"><label>PASSWORD</label>
        <input class="input" name="password" placeholder="strong password" required></div>
      <div class="form-row"><label>DURATION (HOURS)</label>
        <input class="input" name="hours" type="number" value="24" min="0" step="1"></div>
      <button class="btn-primary">✨ CREATE USER</button>
    </form>
  </div>
</div>

<div class="tab-panel" id="panel-pricing">
  <div class="card">
    <h2>EDIT PRICING PLANS</h2>
    <p class="card-sub">THESE PLANS SHOW ON THE PUBLIC /PRICING PAGE.</p>
    <form method="post" action="{{ url_for('owner_pricing') }}">
      <div class="grid-2" style="margin-bottom:12px">
        <div class="form-row"><label>CURRENCY SYMBOL</label>
          <input class="input" name="currency" value="{{ pricing.currency }}"></div>
        <div class="form-row"><label>CONTACT INFO</label>
          <input class="input" name="contact" value="{{ pricing.contact }}"></div>
      </div>
      {% for p in pricing.plans %}
      <div style="border:1px solid var(--border);border-radius:11px;padding:14px;margin-bottom:12px">
        <div class="grid-2" style="gap:10px">
          <div class="form-row"><label>PLAN NAME</label><input class="input" name="p_name" value="{{ p.name }}"></div>
          <div class="form-row"><label>DURATION</label><input class="input" name="p_duration" value="{{ p.duration }}"></div>
          <div class="form-row"><label>PRICE</label><input class="input" name="p_price" value="{{ p.price }}"></div>
          <div class="form-row"><label>FEATURES (COMMA-SEPARATED)</label><input class="input" name="p_features" value="{{ p.features }}"></div>
        </div>
      </div>
      {% endfor %}
      <div id="new-plans"></div>
      <button type="button" class="btn-ghost-lg" onclick="addPlan()" style="margin-right:8px">+ ADD PLAN</button>
      <button class="btn-primary">💾 SAVE PLANS</button>
    </form>
  </div>
</div>
"""

OWNER_SCRIPTS = """
<script>
document.querySelectorAll('.tab').forEach(function(t){
  t.addEventListener('click', function(){
    document.querySelectorAll('.tab').forEach(function(x){ x.classList.remove('active'); });
    document.querySelectorAll('.tab-panel').forEach(function(x){ x.classList.remove('active'); });
    t.classList.add('active');
    document.getElementById('panel-' + t.dataset.tab).classList.add('active');
  });
});
document.querySelectorAll('.ts').forEach(function(el){
  el.textContent = new Date(parseFloat(el.dataset.ts)*1000).toLocaleString();
});
function addPlan(){
  var wrap = document.getElementById('new-plans');
  var div = document.createElement('div');
  div.style.cssText = 'border:1px dashed var(--border-hi);border-radius:11px;padding:14px;margin-bottom:12px';
  div.innerHTML = '<div class="grid-2" style="gap:10px">'
    + '<div class="form-row"><label>PLAN NAME</label><input class="input" name="p_name" placeholder="NEW PLAN"></div>'
    + '<div class="form-row"><label>DURATION</label><input class="input" name="p_duration" placeholder="30 DAYS"></div>'
    + '<div class="form-row"><label>PRICE</label><input class="input" name="p_price" placeholder="499"></div>'
    + '<div class="form-row"><label>FEATURES</label><input class="input" name="p_features" placeholder="feature1, feature2"></div>'
    + '</div>';
  wrap.appendChild(div);
}

/* COPY AUTO-LOGIN LINK — no link text visible */
async function copyLink(link){
  try{
    if(navigator.clipboard && window.isSecureContext){
      await navigator.clipboard.writeText(link);
    } else {
      // Fallback for non-secure contexts (some Railway edge cases)
      var tmp = document.createElement('textarea');
      tmp.value = link;
      tmp.style.position = 'fixed';
      tmp.style.opacity = '0';
      document.body.appendChild(tmp);
      tmp.focus();
      tmp.select();
      document.execCommand('copy');
      document.body.removeChild(tmp);
    }
    toast('LINK COPIED ✓', 'ok');
  } catch(e){
    toast('COPY FAILED — OPEN INSTEAD', 'err');
  }
}
</script>
"""

PINGER_TPL = """
<div class="dash-head">
  <div class="dash-title">🌐 WEBSITE PINGER <span>KEEP YOUR SITES AWAKE 24/7</span></div>
</div>

<div class="grid-2" style="margin-bottom:16px">
  <div class="card">
    <h2>➕ ADD NEW PINGER</h2>
    <p class="card-sub">PING A URL EVERY N SECONDS TO KEEP IT ALIVE</p>
    <form onsubmit="return addPinger(event)">
      <div class="form-row">
        <label>URL</label>
        <input class="input" id="p-url" placeholder="https://example.com" required>
      </div>
      <div class="grid-2" style="gap:10px">
        <div class="form-row">
          <label>INTERVAL (SEC)</label>
          <input class="input" id="p-interval" type="number" value="300" min="10">
        </div>
        <div class="form-row">
          <label>HOLD (SEC)</label>
          <input class="input" id="p-hold" type="number" value="10" min="1" max="300">
        </div>
      </div>
      <button class="btn-primary">▶ START PINGING</button>
    </form>
  </div>

  <div class="card">
    <h2>📊 QUICK STATS</h2>
    <p class="card-sub">LIVE STATUS OF ALL PINGERS</p>
    <div id="pinger-stats">
      <p style="color:var(--txt-mute);font-size:.8rem">LOADING…</p>
    </div>
  </div>
</div>

<div class="card">
  <h2>🌐 ACTIVE PINGERS</h2>
  <p class="card-sub">CLICK A PINGER TO VIEW LIVE LOGS</p>
  <div id="pinger-list">
    <p style="color:var(--txt-mute);padding:16px 0;font-size:.8rem">NO PINGERS YET. ADD ONE ABOVE.</p>
  </div>
</div>

<div class="card" id="log-card" style="display:none;margin-top:16px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px">
    <h2 style="margin:0">📡 <span id="log-title">LOGS</span></h2>
    <button class="btn-sm btn-err" onclick="closeLogs()">✕ CLOSE</button>
  </div>
  <div class="terminal" id="pinger-term" style="height:340px;color:#b8f0c8">Loading…</div>
</div>
"""

PINGER_SCRIPTS = """
<script>
var currentPid = null;
var currentTerm = null;

async function addPinger(e){
  e.preventDefault();
  var url = document.getElementById('p-url').value.trim();
  var interval = document.getElementById('p-interval').value;
  var hold = document.getElementById('p-hold').value;
  var r = await fetch('{{ url_for("pinger_add") }}', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'url=' + encodeURIComponent(url) + '&interval=' + encodeURIComponent(interval) + '&hold=' + encodeURIComponent(hold)
  });
  var j = await r.json();
  toast(j.msg, j.ok ? 'ok' : 'err');
  if(j.ok){ document.getElementById('p-url').value = ''; refreshPingers(); }
  return false;
}

async function togglePinger(pid){
  var r = await fetch('/pinger/' + pid + '/toggle', {method:'POST'});
  var j = await r.json();
  toast(j.msg, j.ok ? 'ok' : 'err');
  refreshPingers();
}

async function stopPinger(pid){
  if(!confirm('Stop and delete this pinger?')) return;
  var r = await fetch('/pinger/' + pid + '/stop', {method:'POST'});
  var j = await r.json();
  toast(j.msg, j.ok ? 'ok' : 'err');
  if(currentPid === pid) closeLogs();
  refreshPingers();
}

async function showLogs(pid, url){
  currentPid = pid;
  document.getElementById('log-card').style.display = 'block';
  document.getElementById('log-title').textContent = url;
  currentTerm = document.getElementById('pinger-term');
  currentTerm.scrollIntoView({behavior:'smooth', block:'start'});
  refreshLogs();
}

function closeLogs(){
  currentPid = null;
  document.getElementById('log-card').style.display = 'none';
}

async function refreshLogs(){
  if(!currentPid) return;
  try{
    var r = await fetch('/pinger/' + currentPid + '/logs');
    var j = await r.json();
    if(j.ok && currentTerm){
      currentTerm.textContent = j.logs.length ? j.logs.join('\\n') : 'No logs yet.';
      currentTerm.scrollTop = currentTerm.scrollHeight;
    }
  }catch(e){}
}

async function refreshPingers(){
  try{
    var r = await fetch('{{ url_for("pinger_list") }}');
    var data = await r.json();
    var list = document.getElementById('pinger-list');
    var stats = document.getElementById('pinger-stats');
    var keys = Object.keys(data);

    if(!keys.length){
      list.innerHTML = '<p style="color:var(--txt-mute);padding:16px 0;font-size:.8rem">NO PINGERS YET. ADD ONE ABOVE.</p>';
      stats.innerHTML = '<p style="color:var(--txt-mute);font-size:.8rem">NO PINGERS ACTIVE</p>';
      return;
    }

    var totalOk = 0, totalFail = 0;
    var html = '<ul class="file-list">';
    keys.forEach(function(pid){
      var p = data[pid];
      totalOk += p.stats.success;
      totalFail += p.stats.fail;
      var statePill = p.enabled
        ? '<span class="pill pill-ok"><span class="dot"></span>RUNNING</span>'
        : '<span class="pill pill-off">● PAUSED</span>';
      html += '<li>'
        + '<div style="flex:1;min-width:180px">'
        + '<div class="fname">🌐 ' + p.url + '</div>'
        + '<div style="font-size:.72rem;color:var(--txt-mute);margin-top:3px;letter-spacing:.3px">'
        + 'EVERY ' + p.interval + 'S · HOLD ' + p.hold + 'S · '
        + '✓' + p.stats.success + ' ✗' + p.stats.fail
        + ' · LAST: ' + p.stats.last_status
        + '</div></div>'
        + '<div class="file-actions">'
        + statePill
        + '<button class="btn-sm btn-info" onclick="showLogs(\\'' + pid + '\\', \\'' + p.url.replace(/'/g, "\\\\'") + '\\')">📡 LOGS</button>'
        + '<button class="btn-sm btn-warn" onclick="togglePinger(\\'' + pid + '\\')">' + (p.enabled ? '⏸' : '▶') + '</button>'
        + '<button class="btn-sm btn-err" onclick="stopPinger(\\'' + pid + '\\')">🗑</button>'
        + '</div>'
        + '</li>';
    });
    html += '</ul>';
    list.innerHTML = html;

    stats.innerHTML = '<div style="display:grid;gap:9px">'
      + '<div><strong style="font-size:1.5rem;color:#4ade80">' + keys.length + '</strong>'
      + '<span style="color:var(--txt-mute);margin-left:7px;font-size:.74rem">TOTAL PINGERS</span></div>'
      + '<div><strong style="font-size:1.5rem;color:#4ade80">' + totalOk + '</strong>'
      + '<span style="color:var(--txt-mute);margin-left:7px;font-size:.74rem">SUCCESSFUL PINGS</span></div>'
      + '<div><strong style="font-size:1.5rem;color:#ef4444">' + totalFail + '</strong>'
      + '<span style="color:var(--txt-mute);margin-left:7px;font-size:.74rem">FAILED PINGS</span></div>'
      + '</div>';
  }catch(e){ console.error(e); }
}

refreshPingers();
setInterval(refreshPingers, 3000);
setInterval(refreshLogs, 1500);
</script>
"""


# ============================================================
#                       ROUTES
# ============================================================
@app.route("/")
def home():
    if is_owner():
        return redirect(url_for("owner_dashboard"))
    if current_user():
        return redirect(url_for("user_dashboard"))
    return redirect(url_for("landing"))

@app.route("/home")
def landing():
    return render_page("PN X VPS 💀 — PREMIUM HOSTING",
                       LANDING_TPL, pricing=load_pricing())

@app.route("/pricing")
def pricing_page():
    return render_page("PRICING — PN X VPS 💀",
                       PRICING_TPL, pricing=load_pricing())

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "")
        if u == OWNER_USER and p == OWNER_PASS:
            session.clear()
            session["role"] = "owner"
            session["username"] = u
            return redirect(url_for("owner_dashboard"))
        users = load_users()
        info = users.get(u)
        if info and info["password"] == p:
            ok, _ = user_valid(u)
            if not ok:
                error = "ACCOUNT EXPIRED"
            else:
                session.clear()
                session["role"] = "user"
                session["username"] = u
                return redirect(url_for("user_dashboard"))
        else:
            error = "INVALID CREDENTIALS"
    return render_page("LOGIN — PN X VPS 💀", LOGIN_TPL, error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

@app.route("/auto/<token>")
def auto_login(token):
    users = load_users()
    for uname, info in users.items():
        if info.get("token") == token:
            ok, _ = user_valid(uname)
            if not ok:
                return "ACCOUNT EXPIRED", 403
            session.clear()
            session["role"] = "user"
            session["username"] = uname
            return redirect(url_for("user_dashboard"))
    return "INVALID LINK", 404

# ---------- owner ----------
@app.route("/owner")
@require_owner
def owner_dashboard():
    users = load_users()
    now = time.time()
    changed = False
    for uname in list(users.keys()):
        if users[uname].get("expires_at") and now > users[uname]["expires_at"]:
            del users[uname]
            stop_process(uname)
            changed = True
    if changed:
        save_users(users)
    base = request.host_url.rstrip("/")
    return render_page("OWNER DASHBOARD — PN X VPS 💀", OWNER_TPL,
                       extra_scripts=OWNER_SCRIPTS,
                       users=users, now=now, base_url=base, pricing=load_pricing())

@app.route("/owner/create", methods=["POST"])
@require_owner
def owner_create():
    u = request.form.get("username", "").strip()
    p = request.form.get("password", "").strip()
    try:
        hours = float(request.form.get("hours", "24"))
    except ValueError:
        hours = 24
    if not u or not p or u == OWNER_USER:
        return redirect(url_for("owner_dashboard"))
    users = load_users()
    users[u] = {
        "password": p,
        "created_at": time.time(),
        "expires_at": time.time() + hours * 3600 if hours > 0 else 0,
        "token": secrets.token_urlsafe(16),
    }
    save_users(users)
    user_dir(u)
    return redirect(url_for("owner_dashboard"))

@app.route("/owner/delete/<username>", methods=["POST"])
@require_owner
def owner_delete(username):
    users = load_users()
    if username in users:
        stop_process(username)
        del users[username]
        save_users(users)
        d = FILES_ROOT / username
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
    return redirect(url_for("owner_dashboard"))

@app.route("/owner/extend/<username>", methods=["POST"])
@require_owner
def owner_extend(username):
    try:
        hours = float(request.form.get("hours", "24"))
    except ValueError:
        hours = 24
    users = load_users()
    if username in users:
        base = max(users[username].get("expires_at") or time.time(), time.time())
        users[username]["expires_at"] = base + hours * 3600
        save_users(users)
    return redirect(url_for("owner_dashboard"))

@app.route("/owner/pricing", methods=["POST"])
@require_owner
def owner_pricing():
    pricing = load_pricing()
    pricing["currency"] = request.form.get("currency", "₹").strip() or "₹"
    pricing["contact"] = request.form.get("contact", "").strip()
    plans = []
    names = request.form.getlist("p_name")
    durs = request.form.getlist("p_duration")
    prices = request.form.getlist("p_price")
    feats = request.form.getlist("p_features")
    for i in range(len(names)):
        if not names[i].strip():
            continue
        plans.append({
            "name": names[i].strip(),
            "duration": durs[i].strip() if i < len(durs) else "",
            "price": prices[i].strip() if i < len(prices) else "0",
            "features": feats[i].strip() if i < len(feats) else "",
        })
    pricing["plans"] = plans
    save_pricing(pricing)
    return redirect(url_for("owner_dashboard"))

# ---------- user ----------
@app.route("/dashboard")
@require_user
def user_dashboard():
    u = current_user()
    users = load_users()
    info = users.get(u, {})
    udir = user_dir(u)
    files = sorted([f.name for f in udir.iterdir() if f.is_file()])
    return render_page("MY SERVER — PN X VPS 💀", USER_TPL,
                       extra_scripts=USER_SCRIPTS,
                       username=u, info=info, files=files,
                       running=is_running(u),
                       running_file=(PROCS.get(u, {}).get("file") if is_running(u) else None),
                       expires_at=info.get("expires_at", 0),
                       now=time.time())

@app.route("/upload", methods=["POST"])
@require_user
def upload():
    u = current_user()
    udir = user_dir(u)
    for f in request.files.getlist("files"):
        if not f or not f.filename:
            continue
        name = secure_filename(f.filename)
        if name:
            f.save(udir / name)
    return redirect(url_for("user_dashboard"))

@app.route("/file/delete/<name>", methods=["POST"])
@require_user
def file_delete(name):
    u = current_user()
    name = secure_filename(name)
    p = user_dir(u) / name
    if p.exists() and p.is_file():
        p.unlink()
    return redirect(url_for("user_dashboard"))

@app.route("/file/view/<name>")
@require_user
def file_view(name):
    u = current_user()
    name = secure_filename(name)
    return send_from_directory(user_dir(u), name, as_attachment=False)

@app.route("/server/start", methods=["POST"])
@require_user
def server_start():
    u = current_user()
    fname = secure_filename(request.form.get("file", ""))
    ok, msg = start_process(u, fname)
    return jsonify({"ok": ok, "msg": msg})

@app.route("/server/stop", methods=["POST"])
@require_user
def server_stop():
    u = current_user()
    stop_process(u)
    return jsonify({"ok": True, "msg": "stopped (auto-restart disabled)"})

@app.route("/server/restart", methods=["POST"])
@require_user
def server_restart():
    u = current_user()
    info = PROCS.get(u)
    fname = info["file"] if info else secure_filename(request.form.get("file", ""))
    if not fname:
        return jsonify({"ok": False, "msg": "no file"})
    stop_process(u)
    time.sleep(0.3)
    ok, msg = start_process(u, fname)
    return jsonify({"ok": ok, "msg": msg})

@app.route("/server/delete", methods=["POST"])
@require_user
def server_delete():
    u = current_user()
    stop_process(u)
    PROCS.pop(u, None)
    return jsonify({"ok": True, "msg": "cleared"})

@app.route("/logs")
@require_user
def logs_api():
    u = current_user()
    info = PROCS.get(u, {})
    return jsonify({
        "running": is_running(u),
        "file": info.get("file"),
        "logs": get_logs(u),
        "install": list(INSTALL_LOGS.get(u, [])),
        "restart_count": info.get("restart_count", 0),
    })

@app.route("/install", methods=["POST"])
@require_user
def install():
    u = current_user()
    cmd = request.form.get("command", "").strip()
    ok, msg = run_install(u, cmd)
    return jsonify({"ok": ok, "msg": msg})


# ============================================================
#                    PINGER ROUTES
# ============================================================
@app.route("/pinger")
@require_owner
def pinger_page():
    return render_page("WEBSITE PINGER — PN X VPS 💀", PINGER_TPL,
                       extra_scripts=PINGER_SCRIPTS)

@app.route("/pinger/list")
@require_owner
def pinger_list():
    return jsonify(get_all_pingers())

@app.route("/pinger/add", methods=["POST"])
@require_owner
def pinger_add():
    url = request.form.get("url", "").strip()
    try:
        interval = int(request.form.get("interval", 300))
    except ValueError:
        interval = 300
    try:
        hold = int(request.form.get("hold", 10))
    except ValueError:
        hold = 10
    ok, result = add_pinger(url, interval=interval, hold=hold)
    if ok:
        return jsonify({"ok": True, "msg": f"PINGER STARTED: {result}", "id": result})
    return jsonify({"ok": False, "msg": result})

@app.route("/pinger/<pid>/stop", methods=["POST"])
@require_owner
def pinger_stop(pid):
    if remove_pinger(pid):
        return jsonify({"ok": True, "msg": "PINGER REMOVED"})
    return jsonify({"ok": False, "msg": "PINGER NOT FOUND"})

@app.route("/pinger/<pid>/toggle", methods=["POST"])
@require_owner
def pinger_toggle(pid):
    ok, state = toggle_pinger(pid)
    if ok:
        return jsonify({"ok": True, "msg": f"PINGER {state}"})
    return jsonify({"ok": False, "msg": state})

@app.route("/pinger/<pid>/logs")
@require_owner
def pinger_logs(pid):
    info = get_pinger_info(pid)
    if not info:
        return jsonify({"ok": False, "msg": "PINGER NOT FOUND"})
    return jsonify({"ok": True, **info})


# ============================================================
#                    HEALTH CHECK
# ============================================================
@app.route("/health")
def health():
    return jsonify({
        "success": True,
        "status": "ok",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }), 200


# ============================================================
#                    STARTUP
# ============================================================
try:
    load_pingers()
except Exception as _e:
    print(f"[PINGER BOOT ERROR] {_e}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)