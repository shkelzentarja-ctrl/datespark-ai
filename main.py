# ============================================================
#  DateSpark AI — Stable Version + Fixes
#  ✅ Delete individual memory
#  ✅ Clear all memories
#  ✅ Logout button
# ============================================================

from flask import Flask, render_template_string, request, jsonify, session
import requests, json, random, os, sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "datespark_secret_2024")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
)

DB_PATH = os.path.join(os.path.dirname(__file__), "datespark.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                share_code TEXT NOT NULL,
                chat_history TEXT DEFAULT '[]',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS saved_ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                idea TEXT NOT NULL,
                saved_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS date_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                memory TEXT NOT NULL,
                logged_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)
        db.commit()

init_db()

IDEAS = {
    "home": [
        {"title": "Candlelit Cooking Night",    "desc": "Pick a cuisine you've never tried, cook together with wine & music.", "emoji": "🕯️", "duration": "2-3 hrs", "cost": "$"},
        {"title": "Blanket Fort Movie Marathon", "desc": "Build the coziest fort, pick a trilogy, make popcorn with crazy toppings.", "emoji": "🎬", "duration": "4-5 hrs", "cost": "$"},
        {"title": "Paint & Sip Night",          "desc": "Buy canvases, pick a YouTube tutorial, see who paints better.", "emoji": "🎨", "duration": "2 hrs", "cost": "$"},
        {"title": "Home Spa Night",             "desc": "Face masks, foot soaks, DIY massages. Full spa at home.", "emoji": "🧖", "duration": "3 hrs", "cost": "$"},
    ],
    "city": [
        {"title": "Restaurant Roulette",  "desc": "Spin a map, go wherever it lands. No Yelp, no reviews — pure adventure.", "emoji": "🎲", "duration": "2-3 hrs", "cost": "$$"},
        {"title": "Night City Walk",      "desc": "Walk your city after midnight, find the most beautiful lit-up spots.", "emoji": "🌃", "duration": "2 hrs", "cost": "Free"},
        {"title": "Museum After Dark",    "desc": "Many museums have evening events. Wine + art = magic.", "emoji": "🖼️", "duration": "3 hrs", "cost": "$$"},
        {"title": "Street Food Crawl",    "desc": "Hit 5 different street food spots. Rate each one together.", "emoji": "🌮", "duration": "3 hrs", "cost": "$"},
    ],
    "outdoor": [
        {"title": "Sunrise Hike & Breakfast", "desc": "Wake up at 4am, hike to a viewpoint, watch sunrise with packed breakfast.", "emoji": "🌄", "duration": "Half day", "cost": "$"},
        {"title": "Stargazing Picnic",        "desc": "Drive out of the city, lie on a blanket, download a star map app.", "emoji": "🌠", "duration": "3 hrs", "cost": "$"},
        {"title": "Kayaking Adventure",       "desc": "Rent kayaks for the day, pack a lunch, explore hidden waterways.", "emoji": "🚣", "duration": "Full day", "cost": "$$"},
        {"title": "Wildflower Picnic",        "desc": "Find a scenic meadow, bring a fancy picnic basket, take photos.", "emoji": "🌸", "duration": "3 hrs", "cost": "$"},
    ],
    "budget": [
        {"title": "Free Museum Day",           "desc": "Most cities have free museum days. Pick the weirdest one.", "emoji": "🏛️", "duration": "3 hrs", "cost": "Free"},
        {"title": "Library Date",              "desc": "Each pick 3 books for the other. Read together at a café after.", "emoji": "📚", "duration": "2 hrs", "cost": "Free"},
        {"title": "Thrift Store Fashion Show", "desc": "$10 each to build the wildest outfit. Strut it in the store.", "emoji": "👗", "duration": "2 hrs", "cost": "$"},
        {"title": "Sunset Rooftop Drinks",     "desc": "Grab cheap wine, find the highest rooftop, watch the sunset.", "emoji": "🌅", "duration": "2 hrs", "cost": "$"},
    ],
    "luxury": [
        {"title": "Private Chef Experience", "desc": "Book a private chef to cook a 5-course dinner in your home.", "emoji": "👨‍🍳", "duration": "4 hrs", "cost": "$$$$"},
        {"title": "Helicopter City Tour",    "desc": "See your city from above at golden hour. Unforgettable.", "emoji": "🚁", "duration": "1 hr", "cost": "$$$$"},
        {"title": "Winery Weekend Escape",   "desc": "Boutique winery stay — tastings, vineyard walks, fine dining.", "emoji": "🍷", "duration": "Weekend", "cost": "$$$$"},
        {"title": "Spa Retreat Day",         "desc": "Full day luxury spa — couples massages, pools, treatments.", "emoji": "💆", "duration": "Full day", "cost": "$$$"},
    ],
    "travel": [
        {"title": "Spontaneous Flight",    "desc": "Open Google Flights, filter cheapest, book whatever. Go tomorrow.", "emoji": "✈️", "duration": "Weekend", "cost": "$$$"},
        {"title": "Road Trip with No Map", "desc": "Pick a direction, drive 4 hours, see where you end up.", "emoji": "🚗", "duration": "Weekend", "cost": "$$"},
        {"title": "Train Journey Date",    "desc": "Book a scenic train route, pack snacks, watch the world go by.", "emoji": "🚂", "duration": "Full day", "cost": "$$"},
        {"title": "Foreign Food Tour",     "desc": "Visit a neighborhood with a different culture, eat everything local.", "emoji": "🗺️", "duration": "Half day", "cost": "$$"},
    ],
    "surprise": [
        {"title": "Mystery Date Night",     "desc": "Plan every detail secretly, give them only a dress code.", "emoji": "🎭", "duration": "Evening", "cost": "$$"},
        {"title": "Memory Lane Date",       "desc": "Recreate your very first date — same place, same order, same feeling.", "emoji": "💌", "duration": "Evening", "cost": "$$"},
        {"title": "Bucket List Check-Off",  "desc": "Look at each other's bucket lists, pick one item each, do both.", "emoji": "📝", "duration": "Full day", "cost": "Varies"},
        {"title": "Random Acts of Romance", "desc": "Leave clues around the city leading to a surprise final destination.", "emoji": "💝", "duration": "Half day", "cost": "$$"},
    ],
}

SEASONAL = {
    "winter": [
        {"title": "Ice Skating Date",   "desc": "Find a local rink, rent skates, warm up with hot cocoa after.", "emoji": "⛸️", "duration": "2 hrs", "cost": "$$", "cat": "city"},
        {"title": "Cozy Cabin Getaway", "desc": "Book a cabin with a fireplace, bring board games and mulled wine.", "emoji": "🏕️", "duration": "Weekend", "cost": "$$$", "cat": "travel"},
    ],
    "spring": [
        {"title": "Cherry Blossom Picnic",  "desc": "Find the best bloom spot, bring a blanket and charcuterie.", "emoji": "🌸", "duration": "3 hrs", "cost": "$", "cat": "outdoor"},
        {"title": "Farmers Market Morning", "desc": "Explore a spring market, cook what you find together.", "emoji": "🥕", "duration": "Half day", "cost": "$", "cat": "budget"},
    ],
    "summer": [
        {"title": "Rooftop Cinema Night", "desc": "Find an outdoor movie screening, bring blankets and snacks.", "emoji": "🎥", "duration": "3 hrs", "cost": "$$", "cat": "city"},
        {"title": "Beach Sunrise Swim",   "desc": "Drive to the beach before dawn, swim at sunrise, breakfast by the sea.", "emoji": "🌊", "duration": "Half day", "cost": "$", "cat": "outdoor"},
    ],
    "autumn": [
        {"title": "Apple Orchard Date",   "desc": "Pick apples, drink fresh cider, get lost in a corn maze.", "emoji": "🍎", "duration": "Half day", "cost": "$$", "cat": "outdoor"},
        {"title": "Halloween Ghost Tour", "desc": "Book a spooky city ghost tour, dare each other to be brave.", "emoji": "👻", "duration": "2 hrs", "cost": "$$", "cat": "city"},
    ],
}

def get_season():
    m = datetime.now().month
    if m in [3,4,5]: return "spring"
    if m in [6,7,8]: return "summer"
    if m in [9,10,11]: return "autumn"
    return "winter"

def call_gemini(prompt):
    try:
        body = {"contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.9, "maxOutputTokens": 3000}}
        r = requests.post(GEMINI_URL, json=body, timeout=30)
        txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        txt = txt.strip().replace("```json","").replace("```JSON","").replace("```","").strip()
        start = min(txt.find('[') if txt.find('[')!=-1 else len(txt),
                    txt.find('{') if txt.find('{')!=-1 else len(txt))
        end = max(txt.rfind(']'), txt.rfind('}')) + 1
        if start < end: txt = txt[start:end]
        return txt
    except: return None

# ── Auth Routes ───────────────────────────────────────────────
@app.route("/api/register", methods=["POST"])
def register():
    d = request.json
    u, p = d.get("username","").strip(), d.get("password","")
    if not u or not p: return jsonify({"error": "Username and password required"}), 400
    with get_db() as db:
        if db.execute("SELECT 1 FROM users WHERE username=?", (u,)).fetchone():
            return jsonify({"error": "Username already taken"}), 400
        code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
        db.execute("INSERT INTO users (username, password, share_code) VALUES (?,?,?)", (u, p, code))
        db.commit()
    session["user"] = u
    return jsonify({"success": True, "username": u, "share_code": code, "saved": [], "history": []})

@app.route("/api/login", methods=["POST"])
def login():
    d = request.json
    u, p = d.get("username","").strip(), d.get("password","")
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
        if not user: return jsonify({"error": "Invalid username or password"}), 401
        saved = [json.loads(r["idea"]) for r in db.execute(
            "SELECT idea FROM saved_ideas WHERE username=? ORDER BY saved_at", (u,)).fetchall()]
        history = []
        for row in db.execute("SELECT id, memory FROM date_history WHERE username=? ORDER BY logged_at", (u,)).fetchall():
            try:
                mem = json.loads(row["memory"])
                mem["db_id"] = row["id"]
                history.append(mem)
            except: pass
    session["user"] = u
    return jsonify({"success": True, "username": u, "share_code": user["share_code"],
                    "saved": saved, "history": history})

@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"success": True})

@app.route("/api/ideas")
def get_ideas(): return jsonify(IDEAS)

@app.route("/api/seasonal")
def get_seasonal():
    season = get_season()
    return jsonify({"season": season, "ideas": SEASONAL[season]})

@app.route("/api/save", methods=["POST"])
def save_idea():
    u = session.get("user")
    if not u: return jsonify({"error": "Not logged in"}), 401
    idea = request.json.get("idea")
    with get_db() as db:
        existing = [json.loads(r["idea"]) for r in db.execute(
            "SELECT idea FROM saved_ideas WHERE username=?", (u,)).fetchall()]
        if not any(s["title"]==idea["title"] for s in existing):
            db.execute("INSERT INTO saved_ideas (username, idea) VALUES (?,?)", (u, json.dumps(idea)))
            db.commit()
        saved = [json.loads(r["idea"]) for r in db.execute(
            "SELECT idea FROM saved_ideas WHERE username=? ORDER BY saved_at", (u,)).fetchall()]
    return jsonify({"success": True, "saved": saved})

@app.route("/api/history", methods=["POST"])
def add_history():
    u = session.get("user")
    if not u: return jsonify({"error": "Not logged in"}), 401
    with get_db() as db:
        db.execute("INSERT INTO date_history (username, memory) VALUES (?,?)",
                   (u, json.dumps(request.json)))
        db.commit()
    return jsonify({"success": True})

@app.route("/api/history/delete", methods=["POST"])
def delete_history():
    u = session.get("user")
    if not u: return jsonify({"error": "Not logged in"}), 401
    db_id = request.json.get("db_id")
    with get_db() as db:
        db.execute("DELETE FROM date_history WHERE id=? AND username=?", (db_id, u))
        db.commit()
    return jsonify({"success": True})

@app.route("/api/history/clear", methods=["POST"])
def clear_history():
    u = session.get("user")
    if not u: return jsonify({"error": "Not logged in"}), 401
    with get_db() as db:
        db.execute("DELETE FROM date_history WHERE username=?", (u,))
        db.commit()
    return jsonify({"success": True})

@app.route("/api/ai/quick", methods=["POST"])
def ai_quick():
    topic = request.json.get("topic","")
    prompt = (f'Generate a creative romantic date idea based on: "{topic}". '
              'Return ONLY valid JSON: {"title":"...","desc":"...","emoji":"...","duration":"...","cost":"...","tip":"...","steps":["...","...","..."]}')
    result = call_gemini(prompt)
    if not result: return jsonify({"error": "AI unavailable"}), 500
    try: return jsonify(json.loads(result))
    except: return jsonify({"error": "Parse error"}), 500

@app.route("/api/ai/itinerary", methods=["POST"])
def ai_itinerary():
    topic = request.json.get("topic","")
    prompt = (f'Create a detailed minute-by-minute date itinerary based on: "{topic}". '
              'Return ONLY valid JSON: {"title":"...","emoji":"...","totalDuration":"...","totalCost":"...","overview":"...",'
              '"timeline":[{"time":"7:00 PM","activity":"...","tip":"...","duration":"30 min"}]}')
    result = call_gemini(prompt)
    if not result: return jsonify({"error": "AI unavailable"}), 500
    try: return jsonify(json.loads(result))
    except: return jsonify({"error": "Parse error"}), 500

@app.route("/api/ai/places", methods=["POST"])
def ai_places():
    city = request.json.get("city","")
    prompt = (f'Suggest 6 real date-worthy places in {city} for couples. '
              'Return ONLY a JSON array: [{"name":"...","type":"...","desc":"one sentence","emoji":"...","priceRange":"$"}]')
    result = call_gemini(prompt)
    if not result: return jsonify({"error": "AI unavailable"}), 500
    try: return jsonify(json.loads(result))
    except: return jsonify({"error": "Parse error"}), 500

@app.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    u = session.get("user")
    msg = request.json.get("message","")
    lang = request.json.get("lang","en")
    chat_history = []
    if u:
        with get_db() as db:
            user = db.execute("SELECT chat_history FROM users WHERE username=?", (u,)).fetchone()
            chat_history = json.loads(user["chat_history"]) if user else []
    ctx = "\n".join([f"{'User' if m['role']=='user' else 'Assistant'}: {m['text']}"
                     for m in chat_history[-6:]])
    lang_name = {"en":"English","es":"Spanish","fr":"French","de":"German"}.get(lang,"English")
    prompt = (f'You are a friendly date idea assistant. Respond in {lang_name}. '
              f'Previous conversation:\n{ctx}\nUser: {msg}\n'
              f'Give a helpful, fun, concise response about date ideas. Keep it under 100 words.')
    result = call_gemini(prompt)
    if not result: return jsonify({"error": "AI unavailable"}), 500
    if u:
        chat_history.append({"role":"user","text":msg})
        chat_history.append({"role":"assistant","text":result})
        with get_db() as db:
            db.execute("UPDATE users SET chat_history=? WHERE username=?",
                       (json.dumps(chat_history[-20:]), u))
            db.commit()
    return jsonify({"response": result})

@app.route("/")
def index(): return render_template_string(HTML)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>DateSpark AI</title>
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#f43f5e">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="DateSpark">
<style>
:root{--bg:#0d0d0d;--surface:#1a1a2e;--text:#ffffff;--subtext:#9ca3af;--border:#ffffff15;--input:#1f2937;--card-overlay:rgba(0,0,0,0.3)}
.light{--bg:#f0f0f5;--surface:#ffffff;--text:#111827;--subtext:#6b7280;--border:#d1d5db;--input:#e5e7eb}
.light header,.light nav{background:#ffffff;box-shadow:0 2px 8px rgba(0,0,0,0.08)}
.light .surface{background:#ffffff;box-shadow:0 1px 4px rgba(0,0,0,0.06)}
.light .swipe-btn{background:#ffffff}
.light .memory-card,.light .stat-card{background:#ffffff}
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-height:100vh;display:flex;flex-direction:column;max-width:480px;margin:0 auto}
header{background:var(--surface);padding:12px 16px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--border);position:sticky;top:0;z-index:50}
header h1{font-size:18px;color:#f43f5e;font-weight:900}
.header-right{display:flex;gap:8px;align-items:center}
.icon-btn{background:none;border:none;font-size:18px;cursor:pointer;padding:4px}
nav{background:var(--surface);display:flex;border-top:1px solid var(--border);position:sticky;bottom:0;z-index:100;overflow-x:auto}
nav button{flex:1;min-width:44px;padding:12px 2px;background:none;border:none;color:var(--subtext);font-size:20px;cursor:pointer;white-space:nowrap}
nav button.active{color:#f43f5e;border-top:2px solid #f43f5e}
.screen{display:none;flex:1;flex-direction:column;padding:14px;gap:12px;overflow-y:auto;padding-bottom:80px}
.screen.active{display:flex}
.card{border-radius:20px;padding:18px;position:relative;overflow:hidden;margin-bottom:10px}
.card h2{font-size:17px;font-weight:900;margin-bottom:5px;color:#fff}
.card p{font-size:12px;color:rgba(255,255,255,0.85);line-height:1.5}
.card-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px}
.card-cost{background:rgba(0,0,0,0.3);border-radius:20px;padding:2px 8px;font-weight:700;color:#fff;font-size:11px;display:inline-block}
.card-meta{text-align:right;font-size:11px;color:rgba(255,255,255,0.7)}
.card-btns{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}
.card-btns button{padding:7px 10px;border:none;border-radius:10px;background:rgba(255,255,255,0.22);color:#fff;font-size:11px;font-weight:700;cursor:pointer}
.cat-home{background:linear-gradient(135deg,#e11d48,#be185d)}
.cat-city{background:linear-gradient(135deg,#7c3aed,#6d28d9)}
.cat-outdoor{background:linear-gradient(135deg,#059669,#047857)}
.cat-budget{background:linear-gradient(135deg,#d97706,#b45309)}
.cat-luxury{background:linear-gradient(135deg,#d97706,#92400e)}
.cat-travel{background:linear-gradient(135deg,#0284c7,#0369a1)}
.cat-surprise{background:linear-gradient(135deg,#c026d3,#a21caf)}
.cat-ai{background:linear-gradient(135deg,#f43f5e,#e11d48)}
.pills{display:flex;gap:6px;overflow-x:auto;padding-bottom:4px;scrollbar-width:none}
.pills::-webkit-scrollbar{display:none}
.pill{flex-shrink:0;padding:7px 12px;border-radius:20px;border:none;background:var(--input);color:var(--text);font-size:12px;font-weight:700;cursor:pointer}
.pill.active{background:#f43f5e;color:#fff}
.swipe-area{position:relative;height:250px;margin-bottom:8px}
.swipe-card{position:absolute;inset:0;border-radius:22px;padding:16px;display:flex;flex-direction:column;justify-content:space-between;cursor:grab;user-select:none;overflow:hidden}
.swipe-card.back1{transform:scale(0.95) translateY(8px);opacity:.7;z-index:1;pointer-events:none}
.swipe-card.back2{transform:scale(0.90) translateY(16px);opacity:.4;z-index:0;pointer-events:none}
.swipe-card.front{z-index:2}
.swipe-btns{display:flex;justify-content:center;gap:16px;align-items:center}
.swipe-btn{width:56px;height:56px;border-radius:50%;border:2px solid var(--border);background:var(--surface);font-size:22px;cursor:pointer;transition:transform .2s;display:flex;align-items:center;justify-content:center}
.swipe-btn:hover{transform:scale(1.1)}
.swipe-btn.like{border-color:#10b981}
.swipe-btn.skip{border-color:#ef4444}
.swipe-btn.shuf{width:44px;height:44px;font-size:18px}
.overlay{position:absolute;top:14px;padding:5px 12px;border-radius:10px;font-weight:900;font-size:15px;border:2px solid #fff;opacity:0;pointer-events:none;z-index:10}
.overlay.like{left:14px;background:#10b981;transform:rotate(-15deg)}
.overlay.skip{right:14px;background:#ef4444;transform:rotate(15deg)}
input,textarea,select{width:100%;background:var(--input);border:1px solid var(--border);border-radius:12px;padding:11px 14px;color:var(--text);font-size:13px;outline:none;resize:none;font-family:inherit}
input:focus,textarea:focus{border-color:#f43f5e}
.btn{width:100%;padding:13px;border:none;border-radius:12px;font-size:14px;font-weight:900;cursor:pointer;color:#fff}
.btn-pink{background:#f43f5e}
.btn-purple{background:#7c3aed}
.btn-gray{background:var(--input);color:var(--text)}
.btn-green{background:#059669}
.btn-blue{background:#0284c7}
.btn-row{display:flex;gap:8px}
.btn-row .btn{flex:1}
.label{font-size:10px;color:var(--subtext);text-transform:uppercase;letter-spacing:.08em;margin-bottom:5px}
.surface{background:var(--surface);border-radius:16px;padding:14px;border:1px solid var(--border);margin-bottom:10px}
.code-display{font-size:28px;font-weight:900;color:#f43f5e;text-align:center;letter-spacing:.2em;padding:12px;background:var(--bg);border-radius:10px;margin:6px 0}
.chat-box{height:300px;overflow-y:auto;display:flex;flex-direction:column;gap:8px;padding:8px;background:var(--bg);border-radius:12px;margin-bottom:8px}
.chat-msg{max-width:80%;padding:8px 12px;border-radius:14px;font-size:13px;line-height:1.4}
.chat-msg.user{background:#f43f5e;color:#fff;align-self:flex-end}
.chat-msg.ai{background:var(--surface);color:var(--text);align-self:flex-start}
.chat-input-row{display:flex;gap:8px}
.chat-input-row input{flex:1}
.chat-input-row button{width:44px;flex-shrink:0;border-radius:12px;border:none;background:#f43f5e;color:#fff;font-size:18px;cursor:pointer}
.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.stat-card{background:var(--surface);border-radius:14px;padding:14px;text-align:center;border:1px solid var(--border)}
.stat-num{font-size:32px;font-weight:900;color:#f43f5e}
.stat-label{font-size:11px;color:var(--subtext);margin-top:4px}
.stat-bar{height:6px;background:var(--border);border-radius:3px;margin-top:6px;overflow:hidden}
.stat-bar-fill{height:100%;background:#f43f5e;border-radius:3px}
.auth-container{display:flex;flex-direction:column;gap:12px;padding:20px 0}
.auth-toggle{text-align:center;color:var(--subtext);font-size:13px;margin-top:8px}
.auth-toggle span{color:#f43f5e;cursor:pointer;font-weight:700}
.modal{position:fixed;inset:0;background:rgba(0,0,0,0.75);z-index:200;display:flex;align-items:center;justify-content:center;padding:16px}
.modal-box{background:var(--surface);border-radius:22px;padding:22px;width:100%;max-width:380px;border:1px solid var(--border)}
.rating-btns{display:flex;gap:4px;margin:8px 0}
.rating-btn{flex:1;padding:7px;background:var(--input);border:2px solid transparent;border-radius:9px;color:var(--text);font-size:10px;cursor:pointer;font-weight:700}
.rating-btn.selected{border-color:#f43f5e;background:#f43f5e22}
.photo-preview{width:100%;height:120px;object-fit:cover;border-radius:10px;margin-top:8px;display:none}
.confetti-container{position:fixed;inset:0;pointer-events:none;z-index:999;overflow:hidden}
.confetti-piece{position:absolute;border-radius:2px;animation:fall 2.5s ease-in forwards}
@keyframes fall{to{transform:translateY(110vh) rotate(720deg);opacity:0}}
.flying-out-left{animation:flyLeft .3s ease-in forwards!important}
.flying-out-right{animation:flyRight .3s ease-in forwards!important}
@keyframes flyLeft{to{transform:translateX(-120vw) rotate(-30deg);opacity:0}}
@keyframes flyRight{to{transform:translateX(120vw) rotate(30deg);opacity:0}}
.empty{text-align:center;padding:40px 20px;color:var(--subtext)}
.empty div{font-size:44px;margin-bottom:10px}
.memory-card{background:var(--surface);border-radius:14px;padding:12px;border:1px solid var(--border);margin-bottom:10px}
.memory-photo{width:100%;height:100px;object-fit:cover;border-radius:8px;margin-top:6px}
.toast{position:fixed;bottom:75px;left:50%;transform:translateX(-50%);background:var(--surface);color:var(--text);padding:9px 18px;border-radius:20px;font-size:12px;font-weight:700;z-index:500;border:1px solid var(--border);white-space:nowrap}
.lang-select{width:auto;padding:5px 8px;font-size:12px;border-radius:8px;background:var(--input);color:var(--text);border:1px solid var(--border)}
.share-btns{display:flex;gap:8px;margin-top:8px}
.share-btn{flex:1;padding:10px;border:none;border-radius:10px;font-weight:700;font-size:12px;cursor:pointer;color:#fff}
.share-btn.wa{background:#25d366}
.share-btn.em{background:#0284c7}
.share-btn.cp{background:#6b7280}
.recommend-card{background:var(--surface);border-radius:14px;padding:12px;border:1px solid #f43f5e33;margin-bottom:10px}
.reason-tag{background:#f43f5e22;color:#f43f5e;border-radius:10px;padding:3px 8px;font-size:10px;margin-top:6px;display:inline-block}
</style>
</head>
<body>
<header>
  <h1>💘 DateSpark AI</h1>
  <div class="header-right">
    <select class="lang-select" id="lang-select" onchange="setLang(this.value)">
      <option value="en">EN</option>
      <option value="es">ES</option>
      <option value="fr">FR</option>
      <option value="de">DE</option>
    </select>
    <button class="icon-btn" onclick="toggleTheme()" id="theme-btn">🌙</button>
    <div id="user-badge-area"></div>
  </div>
</header>

<div id="screen-auth" class="screen active" style="justify-content:center">
  <div style="text-align:center;margin-bottom:20px">
    <div style="font-size:60px">💘</div>
    <h2 style="font-size:24px;font-weight:900;color:#f43f5e;margin-top:8px">DateSpark AI</h2>
    <p style="color:var(--subtext);font-size:13px;margin-top:4px">Your AI-powered date companion</p>
  </div>
  <div class="auth-container">
    <div><div class="label">Username</div><input id="auth-username" placeholder="Enter username"></div>
    <div><div class="label">Password</div><input id="auth-password" type="password" placeholder="Enter password"></div>
    <div id="auth-error" style="color:#ef4444;font-size:12px;display:none"></div>
    <button class="btn btn-pink" id="auth-submit-btn" onclick="submitAuth()">Login</button>
    <button class="btn btn-gray" onclick="continueGuest()">Continue as Guest</button>
    <div class="auth-toggle"><span id="auth-toggle-link" onclick="toggleAuthMode()">Don't have an account? Register</span></div>
  </div>
</div>

<div id="screen-spark" class="screen">
  <div class="pills" id="cat-pills"></div>
  <div class="swipe-area" id="swipe-area"></div>
  <div class="swipe-btns">
    <button class="swipe-btn skip" onclick="swipe('left')">❌</button>
    <button class="swipe-btn shuf" onclick="reshuffleDeck()">🔀</button>
    <button class="swipe-btn like" onclick="swipe('right')">💚</button>
  </div>
  <p style="text-align:center;font-size:11px;color:var(--subtext)">Drag or use buttons</p>
</div>

<div id="screen-seasonal" class="screen">
  <div id="seasonal-header"></div>
  <div id="seasonal-cards"></div>
</div>

<div id="screen-couples" class="screen">
  <div class="surface">
    <div class="label">Your Share Code</div>
    <div class="code-display" id="my-code">------</div>
    <p style="font-size:11px;color:var(--subtext)">Share with your partner to sync swipes!</p>
  </div>
  <div class="surface">
    <div class="label">Enter Partner's Code</div>
    <input id="partner-code" maxlength="6" placeholder="XXXXXX" style="text-transform:uppercase;letter-spacing:.2em;font-size:18px;font-weight:900;text-align:center">
    <button class="btn btn-pink" style="margin-top:10px" onclick="connectPartner()">Connect 💑</button>
    <div id="connect-status" style="font-size:12px;margin-top:6px"></div>
  </div>
  <div class="label">Matches</div>
  <div id="matches-list"></div>
</div>

<div id="screen-ai" class="screen">
  <div class="surface">
    <div class="label">🤖 AI Date Planner</div>
    <textarea id="ai-topic" rows="3" placeholder="e.g. We love hiking and sushi, 1-year anniversary, budget $150..."></textarea>
    <div class="btn-row" style="margin-top:10px">
      <button class="btn btn-pink" onclick="aiQuick()">💡 Quick Idea</button>
      <button class="btn btn-purple" onclick="aiItinerary()">🗓️ Full Itinerary</button>
    </div>
  </div>
  <div class="surface">
    <div class="label">📍 Find Date Spots</div>
    <input id="city-input" placeholder="Enter your city...">
    <button class="btn btn-blue" style="margin-top:10px" onclick="findPlaces()">🗺️ Find Places</button>
  </div>
  <div id="ai-result"></div>
</div>

<div id="screen-chat" class="screen">
  <div class="surface" style="flex:1;display:flex;flex-direction:column">
    <div class="label">💬 Date Ideas Assistant</div>
    <div class="chat-box" id="chat-box">
      <div class="chat-msg ai">Hi! 👋 Ask me anything about date ideas — budget, romantic spots, anniversary plans... I am here to help! 💘</div>
    </div>
    <div class="chat-input-row">
      <input id="chat-input" placeholder="Ask me about date ideas..." onkeydown="if(event.key==='Enter')sendChat()">
      <button onclick="sendChat()">➤</button>
    </div>
  </div>
</div>

<div id="screen-stats" class="screen">
  <div class="label">📊 Your Date Stats</div>
  <div class="stat-grid" id="stat-grid"></div>
  <div class="surface" style="margin-top:4px">
    <div class="label">Favourite Categories</div>
    <div id="cat-stats"></div>
  </div>
  <div class="surface">
    <div class="label">Recent Ratings</div>
    <div id="rating-stats"></div>
  </div>
</div>

<div id="screen-history" class="screen">
  <div id="history-list"></div>
</div>

<div id="screen-saved" class="screen">
  <div id="saved-list"></div>
</div>

<nav id="main-nav" style="display:none">
  <button onclick="showTab('spark',this)">⚡</button>
  <button onclick="showTab('seasonal',this)" id="seasonal-tab-btn">❄️</button>
  <button onclick="showTab('couples',this)">💑</button>
  <button onclick="showTab('ai',this)">🤖</button>
  <button onclick="showTab('chat',this)">💬</button>
  <button onclick="showTab('stats',this)">📊</button>
  <button onclick="showTab('history',this)">📖</button>
  <button onclick="showTab('saved',this)">❤️</button>
</nav>

<div class="confetti-container" id="confetti"></div>

<script>
var IDEAS={}, deck=[], saved=[], history=[], matches=[];
var activeCat='all', couplesMode=false, currentUser=null;
var shareCode=Math.random().toString(36).slice(2,8).toUpperCase();
var dragStartX=null, currentDrag=0, isDragging=false;
var selectedRating=5, currentMemoryIdea=null, currentMemoryPhoto=null;
var lang='en', darkMode=true, authMode='login';

function toggleTheme(){
  darkMode=!darkMode;
  document.body.classList.toggle('light',!darkMode);
  document.getElementById('theme-btn').textContent=darkMode?'🌙':'☀️';
}

function setLang(l){ lang=l; }

function toggleAuthMode(){
  authMode=authMode==='login'?'register':'login';
  var isLogin=authMode==='login';
  document.getElementById('auth-submit-btn').textContent=isLogin?'Login':'Register';
  document.getElementById('auth-toggle-link').textContent=isLogin
    ?'Don\'t have an account? Register':'Already have an account? Login';
}

function submitAuth(){
  var u=document.getElementById('auth-username').value.trim();
  var p=document.getElementById('auth-password').value;
  var err=document.getElementById('auth-error');
  err.style.display='none';
  if(!u||!p){err.textContent='Please fill in all fields';err.style.display='block';return;}
  var endpoint=authMode==='login'?'/api/login':'/api/register';
  var btn=document.getElementById('auth-submit-btn');
  btn.textContent='...';btn.disabled=true;
  fetch(endpoint,{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({username:u,password:p})
  }).then(function(r){
    return r.json();
  }).then(function(data){
    btn.textContent=authMode==='login'?'Login':'Register';
    btn.disabled=false;
    if(data.error){err.textContent=data.error;err.style.display='block';return;}
    currentUser=data.username;
    shareCode=data.share_code;
    saved=data.saved||[];
    history=data.history||[];
    enterApp();
  }).catch(function(){
    btn.textContent=authMode==='login'?'Login':'Register';
    btn.disabled=false;
    err.textContent='Connection error. Try again.';
    err.style.display='block';
  });
}

function continueGuest(){ currentUser=null; enterApp(); }

function enterApp(){
  document.getElementById('screen-auth').classList.remove('active');
  document.getElementById('main-nav').style.display='flex';
  var badgeArea=document.getElementById('user-badge-area');
  if(currentUser){
    badgeArea.innerHTML='<span style="background:#f43f5e22;color:#f43f5e;border-radius:20px;padding:3px 8px;font-size:11px;font-weight:700">👤 '+currentUser+'</span>'
      +' <button class="icon-btn" onclick="logoutUser()" title="Logout">🚪</button>';
  } else {
    badgeArea.innerHTML='<button class="icon-btn" onclick="showAuthScreen()">🔑</button>';
  }
  document.getElementById('my-code').textContent=shareCode;
  init();
  showTab('spark',document.querySelector('#main-nav button'));
}

function logoutUser(){
  fetch('/api/logout',{method:'POST'})
    .then(function(){
      currentUser=null; saved=[]; history=[]; matches=[];
      document.getElementById('auth-username').value='';
      document.getElementById('auth-password').value='';
      document.getElementById('auth-error').style.display='none';
      document.getElementById('main-nav').style.display='none';
      document.querySelectorAll('.screen').forEach(function(s){s.classList.remove('active');});
      document.getElementById('screen-auth').classList.add('active');
      showToast('Logged out! 👋');
    });
}

function showAuthScreen(){
  document.getElementById('main-nav').style.display='none';
  document.querySelectorAll('.screen').forEach(function(s){s.classList.remove('active');});
  document.getElementById('screen-auth').classList.add('active');
}

function init(){
  fetch('/api/ideas')
    .then(function(r){return r.json();})
    .then(function(data){
      IDEAS=data;
      buildDeck();
      renderCatPills();
      renderSwipeCards();
      loadSeasonal();
      renderMatches();
      updateNavBadges();
    });
}

function buildDeck(cat){
  cat=cat||'all';
  activeCat=cat;
  var all=[];
  Object.keys(IDEAS).forEach(function(c){
    IDEAS[c].forEach(function(i){
      all.push(Object.assign({},i,{cat:c}));
    });
  });
  deck=cat==='all'?all:all.filter(function(i){return i.cat===cat;});
  deck.sort(function(){return Math.random()-0.5;});
}

function renderCatPills(){
  var cats=[['all','🌀 All'],['home','🏠'],['city','🌆'],['outdoor','🌿'],
            ['budget','💸'],['luxury','💎'],['travel','🌍'],['surprise','✨']];
  document.getElementById('cat-pills').innerHTML=cats.map(function(c){
    return '<button class="pill '+(c[0]===activeCat?'active':'')+'" onclick="setCat(\''+c[0]+'\',this)">'+c[1]+'</button>';
  }).join('');
}

function setCat(cat,btn){
  document.querySelectorAll('.pill').forEach(function(p){p.classList.remove('active');});
  btn.classList.add('active');
  buildDeck(cat);
  renderSwipeCards();
}

function reshuffleDeck(){ buildDeck(activeCat); renderSwipeCards(); }

function renderSwipeCards(){
  var area=document.getElementById('swipe-area');
  area.innerHTML='';
  if(!deck.length){
    area.innerHTML='<div class="empty"><div>🎉</div><p>No more ideas!<br>Tap 🔀 to reshuffle</p></div>';
    return;
  }
  if(deck[2]){var b2=document.createElement('div');b2.className='swipe-card back2 cat-'+(deck[2].cat||'surprise');area.appendChild(b2);}
  if(deck[1]){var b1=document.createElement('div');b1.className='swipe-card back1 cat-'+(deck[1].cat||'surprise');area.appendChild(b1);}
  var card=makeCard(deck[0]);
  area.appendChild(card);
  attachDrag(card);
}

function makeCard(idea){
  var d=document.createElement('div');
  d.className='swipe-card front cat-'+(idea.cat||'surprise');
  var saveBtn=document.createElement('button');
  saveBtn.textContent='❤️ Save';
  saveBtn.style.cssText='flex:1;padding:8px;border:none;border-radius:10px;background:rgba(255,255,255,0.22);color:#fff;font-size:11px;font-weight:700;cursor:pointer';
  saveBtn.onclick=function(e){e.stopPropagation();saveIdea(idea);};
  var shareBtn=document.createElement('button');
  shareBtn.textContent='🔗 Share';
  shareBtn.style.cssText='flex:1;padding:8px;border:none;border-radius:10px;background:rgba(255,255,255,0.22);color:#fff;font-size:11px;font-weight:700;cursor:pointer';
  shareBtn.onclick=function(e){e.stopPropagation();shareIdea(idea);};
  var top=document.createElement('div');
  top.innerHTML='<div class="overlay like">LOVE IT 💚</div><div class="overlay skip">SKIP ❌</div>'
    +'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">'
    +'<span style="font-size:36px;line-height:1">'+(idea.emoji||'✨')+'</span>'
    +'<div style="text-align:right"><div class="card-cost">'+(idea.cost||'')+'</div>'
    +'<div style="color:rgba(255,255,255,0.7);font-size:11px;margin-top:2px">'+(idea.duration||'')+'</div></div></div>'
    +'<div style="font-size:17px;font-weight:900;color:#fff;margin-bottom:6px">'+(idea.title||'')+'</div>'
    +'<div style="font-size:12px;color:rgba(255,255,255,0.85);line-height:1.5">'+(idea.desc||'')+'</div>';
  var btns=document.createElement('div');
  btns.style.cssText='display:flex;gap:6px;margin-top:10px;flex-shrink:0';
  btns.appendChild(saveBtn);
  btns.appendChild(shareBtn);
  d.appendChild(top);
  d.appendChild(btns);
  return d;
}

function attachDrag(el){
  el.addEventListener('mousedown',function(e){dragStartX=e.clientX;isDragging=true;});
  el.addEventListener('touchstart',function(e){dragStartX=e.touches[0].clientX;isDragging=true;},{passive:true});
  document.addEventListener('mousemove',onDrag);
  document.addEventListener('touchmove',onDragTouch,{passive:true});
  document.addEventListener('mouseup',onDragEnd);
  document.addEventListener('touchend',onDragEnd);
}

function onDrag(e){if(!isDragging)return;currentDrag=e.clientX-dragStartX;updateDragVisual();}
function onDragTouch(e){if(!isDragging)return;currentDrag=e.touches[0].clientX-dragStartX;updateDragVisual();}

function updateDragVisual(){
  var f=document.querySelector('.swipe-card.front');
  if(!f)return;
  f.style.transform='translateX('+currentDrag+'px) rotate('+(currentDrag/18)+'deg)';
  var lo=f.querySelector('.overlay.like'),so=f.querySelector('.overlay.skip');
  if(lo)lo.style.opacity=currentDrag>30?Math.min(currentDrag/80,1):0;
  if(so)so.style.opacity=currentDrag<-30?Math.min(-currentDrag/80,1):0;
}

function onDragEnd(){
  if(!isDragging)return;
  isDragging=false;
  if(Math.abs(currentDrag)>80)swipe(currentDrag>0?'right':'left');
  else{
    var f=document.querySelector('.swipe-card.front');
    if(f){f.style.transform='';f.querySelectorAll('.overlay').forEach(function(o){o.style.opacity=0;});}
  }
  dragStartX=null;currentDrag=0;
  document.removeEventListener('mousemove',onDrag);
  document.removeEventListener('touchmove',onDragTouch);
  document.removeEventListener('mouseup',onDragEnd);
  document.removeEventListener('touchend',onDragEnd);
}

function swipe(dir){
  if(!deck.length)return;
  var idea=deck[0];
  var front=document.querySelector('.swipe-card.front');
  if(front){
    front.classList.add(dir==='right'?'flying-out-right':'flying-out-left');
    setTimeout(function(){deck.shift();renderSwipeCards();},300);
  } else {deck.shift();renderSwipeCards();}
  if(dir==='right'){
    saveIdea(idea);
    if(couplesMode&&Math.random()>0.4&&!matches.find(function(m){return m.title===idea.title;})){
      matches.push(idea);showConfetti();showMatchPopup(idea);renderMatches();
    }
  }
  updateNavBadges();
}

function saveIdea(idea){
  if(saved.find(function(s){return s.title===idea.title;})){showToast('Already saved! ❤️');return;}
  saved.push(idea);
  if(currentUser){
    fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({idea:idea})});
  }
  updateNavBadges();showToast('Saved! ❤️');
}

function updateNavBadges(){
  var btns=document.querySelectorAll('#main-nav button');
  if(btns[7])btns[7].textContent=saved.length?'❤️'+saved.length:'❤️';
  if(btns[6])btns[6].textContent=history.length?'📖'+history.length:'📖';
}

function shareIdea(idea){
  var text='💘 '+idea.title+'\n'+(idea.desc||'')+'\n⏱ '+(idea.duration||'')+' | 💰 '+(idea.cost||'')+'\n\nvia DateSpark AI';
  var modal=document.createElement('div');
  modal.className='modal';
  var box=document.createElement('div');
  box.className='modal-box';
  box.innerHTML='<h3 style="color:#f43f5e;margin-bottom:12px">🔗 Share This Idea</h3>'
    +'<p style="font-size:13px;margin-bottom:12px">'+(idea.emoji||'')+'  '+(idea.title||'')+'</p>'
    +'<div class="share-btns">'
    +'<button class="share-btn wa" id="sb-wa">📱 WhatsApp</button>'
    +'<button class="share-btn em" id="sb-em">📧 Email</button>'
    +'<button class="share-btn cp" id="sb-cp">📋 Copy</button>'
    +'</div>'
    +'<button class="btn btn-gray" style="margin-top:10px" id="sb-cl">Close</button>';
  modal.appendChild(box);
  document.body.appendChild(modal);
  document.getElementById('sb-wa').onclick=function(){window.open('https://wa.me/?text='+encodeURIComponent(text),'_blank');};
  document.getElementById('sb-em').onclick=function(){window.open('mailto:?subject=Date Idea&body='+encodeURIComponent(text),'_blank');};
  document.getElementById('sb-cp').onclick=function(){if(navigator.clipboard)navigator.clipboard.writeText(text);showToast('Copied!');};
  document.getElementById('sb-cl').onclick=function(){modal.remove();};
}

function addToCalendar(idea){
  var title=encodeURIComponent('💘 '+(idea.title||''));
  var details=encodeURIComponent(idea.desc||'');
  var d=new Date();d.setDate(d.getDate()+7);
  var ds=d.toISOString().replace(/-|:|[.][0-9][0-9][0-9]/g,'');
  window.open('https://calendar.google.com/calendar/render?action=TEMPLATE&text='+title+'&details='+details+'&dates='+ds+'/'+ds,'_blank');
}

function loadSeasonal(){
  fetch('/api/seasonal')
    .then(function(r){return r.json();})
    .then(function(d){
      var icons={winter:'❄️',spring:'🌺',summer:'☀️',autumn:'🍂'};
      var icon=icons[d.season]||'❄️';
      var name=d.season.charAt(0).toUpperCase()+d.season.slice(1);
      document.getElementById('seasonal-tab-btn').textContent=icon;
      document.getElementById('seasonal-header').innerHTML='<div style="text-align:center;margin-bottom:14px"><div style="font-size:48px">'+icon+'</div><h2 style="font-size:20px;font-weight:900;color:#f43f5e;margin:8px 0">'+name+' Dates</h2></div>';
      document.getElementById('seasonal-cards').innerHTML=d.ideas.map(function(i){
        return '<div class="card cat-'+(i.cat||'surprise')+'" style="margin-bottom:12px">'
          +'<div class="card-top"><span style="font-size:36px">'+i.emoji+'</span>'
          +'<div class="card-meta"><div class="card-cost">'+i.cost+'</div><div style="color:rgba(255,255,255,0.7);font-size:11px">'+i.duration+'</div></div></div>'
          +'<div style="font-size:17px;font-weight:900;color:#fff;margin-bottom:6px">'+i.title+'</div>'
          +'<div style="font-size:12px;color:rgba(255,255,255,0.85);line-height:1.5;margin-bottom:10px">'+i.desc+'</div>'
          +'<div class="card-btns" id="sc-'+i.title.replace(/\s/g,'')+'">'
          +'</div></div>';
      }).join('');
      d.ideas.forEach(function(i){
        var el=document.getElementById('sc-'+i.title.replace(/\s/g,''));
        if(!el)return;
        var sb=document.createElement('button');sb.textContent='❤️ Save';
        sb.onclick=function(){saveIdea(i);};el.appendChild(sb);
        var sh=document.createElement('button');sh.textContent='🔗 Share';
        sh.onclick=function(){shareIdea(i);};el.appendChild(sh);
        var ca=document.createElement('button');ca.textContent='📅 Calendar';
        ca.onclick=function(){addToCalendar(i);};el.appendChild(ca);
      });
    });
}

function connectPartner(){
  var code=document.getElementById('partner-code').value.trim().toUpperCase();
  var s=document.getElementById('connect-status');
  if(code.length===6){couplesMode=true;s.style.color='#10b981';s.textContent='✅ Connected! Swipe on ⚡ Spark.';}
  else{s.style.color='#ef4444';s.textContent='❌ Code must be 6 characters.';}
}

function renderMatches(){
  var el=document.getElementById('matches-list');
  if(!matches.length){el.innerHTML='<div class="empty" style="padding:20px"><div>💭</div><p>No matches yet! Go swipe together.</p></div>';return;}
  el.innerHTML='';
  matches.forEach(function(m){
    var div=document.createElement('div');
    div.className='card cat-'+(m.cat||'surprise');
    div.style.marginBottom='10px';
    div.innerHTML='<div class="card-top"><span style="font-size:32px">'+(m.emoji||'✨')+'</span>'
      +'<div class="card-meta"><div class="card-cost">'+(m.cost||'')+'</div><div>'+(m.duration||'')+'</div></div></div>'
      +'<div style="font-size:16px;font-weight:900;color:#fff">'+(m.title||'')+'</div>';
    el.appendChild(div);
  });
}

function showMatchPopup(idea){
  var p=document.createElement('div');
  p.className='modal';
  p.innerHTML='<div class="modal-box" style="text-align:center">'
    +'<div style="font-size:48px">🎉</div>'
    +'<h2 style="color:#f43f5e;font-size:22px;margin:10px 0">It\'s a Match!</h2>'
    +'<p style="margin:8px 0;font-size:18px;font-weight:900">'+(idea.emoji||'')+'  '+(idea.title||'')+'</p>'
    +'<button class="btn btn-pink" style="margin-top:12px" id="match-close">Let\'s do it! 💑</button></div>';
  document.body.appendChild(p);
  document.getElementById('match-close').onclick=function(){p.remove();};
}

function aiQuick(){
  var topic=document.getElementById('ai-topic').value.trim();
  if(!topic)return;
  document.getElementById('ai-result').innerHTML='<div class="empty" style="padding:20px"><div>✨</div><p>Generating idea...</p></div>';
  fetch('/api/ai/quick',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic:topic})})
    .then(function(r){return r.json();})
    .then(function(data){
      if(data.error){document.getElementById('ai-result').innerHTML='<div class="empty"><p>⚠️ AI unavailable.</p></div>';return;}
      var idea=Object.assign({},data,{cat:'surprise',emoji:data.emoji||'✨'});
      var el=document.getElementById('ai-result');
      var div=document.createElement('div');
      div.className='card cat-ai';
      div.innerHTML='<div class="card-top"><span style="font-size:36px">'+(data.emoji||'✨')+'</span>'
        +'<div class="card-meta"><div class="card-cost">'+(data.cost||'')+'</div><div>'+(data.duration||'')+'</div></div></div>'
        +'<div style="font-size:17px;font-weight:900;color:#fff;margin-bottom:6px">'+(data.title||'')+'</div>'
        +'<div style="font-size:12px;color:rgba(255,255,255,0.85);line-height:1.5">'+(data.desc||'')+'</div>'
        +(data.steps?'<div style="margin-top:10px">'+data.steps.map(function(s){return '<p style="font-size:12px;margin:3px 0;color:rgba(255,255,255,0.85)">• '+s+'</p>';}).join('')+'</div>':'')
        +(data.tip?'<div style="margin-top:8px;background:rgba(0,0,0,0.2);border-radius:8px;padding:8px;font-size:11px;color:rgba(255,255,255,0.7)">💡 '+data.tip+'</div>':'');
      var btns=document.createElement('div');
      btns.className='card-btns';
      var sb=document.createElement('button');sb.textContent='❤️ Save';sb.onclick=function(){saveIdea(idea);};
      var sh=document.createElement('button');sh.textContent='🔗 Share';sh.onclick=function(){shareIdea(idea);};
      var ca=document.createElement('button');ca.textContent='📅 Calendar';ca.onclick=function(){addToCalendar(idea);};
      btns.appendChild(sb);btns.appendChild(sh);btns.appendChild(ca);
      div.appendChild(btns);
      el.innerHTML='';el.appendChild(div);
    });
}

function aiItinerary(){
  var topic=document.getElementById('ai-topic').value.trim();
  if(!topic)return;
  document.getElementById('ai-result').innerHTML='<div class="empty" style="padding:20px"><div>🗓️</div><p>Building itinerary...</p></div>';
  fetch('/api/ai/itinerary',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic:topic})})
    .then(function(r){return r.json();})
    .then(function(data){
      if(data.error){document.getElementById('ai-result').innerHTML='<div class="empty"><p>⚠️ AI unavailable.</p></div>';return;}
      var html='<div class="surface">'
        +'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">'
        +'<span style="font-size:32px">'+(data.emoji||'🗓️')+'</span>'
        +'<span style="background:#7c3aed;color:#fff;border-radius:12px;padding:3px 10px;font-size:11px;font-weight:700">'+(data.totalCost||'')+' • '+(data.totalDuration||'')+'</span></div>'
        +'<div style="font-size:17px;font-weight:900;color:#f43f5e;margin-bottom:5px">'+(data.title||'')+'</div>'
        +'<div style="font-size:12px;color:var(--subtext);margin-bottom:12px">'+(data.overview||'')+'</div>';
      (data.timeline||[]).forEach(function(t){
        html+='<div style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid var(--border)">'
          +'<div style="color:#f43f5e;font-size:11px;font-weight:700;min-width:50px">'+(t.time||'')+'</div>'
          +'<div><div style="font-size:13px;font-weight:700">'+(t.activity||'')+'</div>'
          +(t.tip?'<div style="font-size:11px;color:var(--subtext)">💡 '+t.tip+'</div>':'')
          +'</div></div>';
      });
      html+='</div>';
      document.getElementById('ai-result').innerHTML=html;
    });
}

function findPlaces(){
  var city=document.getElementById('city-input').value.trim();
  if(!city)return;
  document.getElementById('ai-result').innerHTML='<div class="empty" style="padding:20px"><div>🗺️</div><p>Finding spots in '+city+'...</p></div>';
  fetch('/api/ai/places',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({city:city})})
    .then(function(r){return r.json();})
    .then(function(data){
      if(data.error){document.getElementById('ai-result').innerHTML='<div class="empty"><p>⚠️ AI unavailable.</p></div>';return;}
      var el=document.getElementById('ai-result');
      el.innerHTML='<div class="label">📍 Date Spots in '+city+'</div>';
      data.forEach(function(p){
        var div=document.createElement('div');
        div.className='surface';
        div.style.cssText='display:flex;gap:10px;align-items:flex-start;margin-bottom:8px';
        div.innerHTML='<span style="font-size:26px;flex-shrink:0">'+(p.emoji||'📍')+'</span>'
          +'<div style="flex:1">'
          +'<div style="display:flex;justify-content:space-between"><b style="font-size:13px">'+(p.name||'')+'</b>'
          +'<span style="color:var(--subtext);font-size:11px">'+(p.priceRange||'')+'</span></div>'
          +'<div style="font-size:10px;color:#0284c7">'+(p.type||'')+'</div>'
          +'<div style="font-size:12px;color:var(--subtext)">'+(p.desc||'')+'</div></div>';
        var hb=document.createElement('button');
        hb.textContent='❤️';
        hb.style.cssText='background:none;border:none;font-size:18px;cursor:pointer;flex-shrink:0';
        hb.onclick=function(){saveIdea({title:p.name,desc:p.desc,emoji:p.emoji,duration:'TBD',cost:p.priceRange,cat:'city'});};
        div.appendChild(hb);
        el.appendChild(div);
      });
    });
}

function sendChat(){
  var input=document.getElementById('chat-input');
  var msg=input.value.trim();
  if(!msg)return;
  var box=document.getElementById('chat-box');
  var um=document.createElement('div');um.className='chat-msg user';um.textContent=msg;box.appendChild(um);
  input.value='';
  var tm=document.createElement('div');tm.className='chat-msg ai';tm.id='typing';tm.textContent='✨ thinking...';box.appendChild(tm);
  box.scrollTop=box.scrollHeight;
  fetch('/api/ai/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg,lang:lang})})
    .then(function(r){return r.json();})
    .then(function(data){
      var t=document.getElementById('typing');if(t)t.remove();
      var am=document.createElement('div');am.className='chat-msg ai';am.textContent=data.response||'Sorry, could not respond.';
      box.appendChild(am);box.scrollTop=box.scrollHeight;
    });
}

function renderStats(){
  var total=history.length;
  var avg=total?Math.round(history.reduce(function(a,h){return a+(h.rating||5);},0)/total*10)/10:0;
  var cc={};history.forEach(function(h){var c=h.cat||'surprise';cc[c]=(cc[c]||0)+1;});
  var fav=Object.entries(cc).sort(function(a,b){return b[1]-a[1];})[0];
  document.getElementById('stat-grid').innerHTML=
    '<div class="stat-card"><div class="stat-num">'+total+'</div><div class="stat-label">Dates Logged</div></div>'
    +'<div class="stat-card"><div class="stat-num">'+(avg||'—')+'</div><div class="stat-label">Avg Rating ⭐</div></div>'
    +'<div class="stat-card"><div class="stat-num">'+saved.length+'</div><div class="stat-label">Ideas Saved</div></div>'
    +'<div class="stat-card"><div class="stat-num">'+(fav?fav[0]:'—')+'</div><div class="stat-label">Fav Category</div></div>';
  document.getElementById('cat-stats').innerHTML=Object.entries(cc).sort(function(a,b){return b[1]-a[1];}).map(function(e){
    return '<div style="margin-bottom:8px"><div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px"><span>'+e[0]+'</span><span>'+e[1]+'</span></div>'
      +'<div class="stat-bar"><div class="stat-bar-fill" style="width:'+(total?Math.round(e[1]/total*100):0)+'%"></div></div></div>';
  }).join('')||'<p style="color:var(--subtext);font-size:12px">Log some dates to see stats!</p>';
  document.getElementById('rating-stats').innerHTML=history.slice(-5).reverse().map(function(h){
    return '<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border)">'
      +'<span style="font-size:13px">'+(h.emoji||'📅')+' '+h.title+'</span>'
      +'<span style="color:#f59e0b">'+'⭐'.repeat(h.rating||5)+'</span></div>';
  }).join('')||'<p style="color:var(--subtext);font-size:12px">No dates logged yet!</p>';
}

function renderHistory(){
  var el=document.getElementById('history-list');
  if(!history.length){
    el.innerHTML='<div class="empty"><div>📖</div><p>No memories yet!<br>Log a date from ❤️ Saved.</p></div>';
    return;
  }
  el.innerHTML='';
  var reversed=[].concat(history).reverse();
  reversed.forEach(function(h,i){
    var realIdx=history.length-1-i;
    var div=document.createElement('div');
    div.className='memory-card';
    div.innerHTML='<div style="display:flex;gap:10px;align-items:flex-start">'
      +'<span style="font-size:28px">'+(h.emoji||'📅')+'</span>'
      +'<div style="flex:1">'
      +'<div style="font-weight:900;font-size:14px">'+h.title+'</div>'
      +'<div style="font-size:11px;color:var(--subtext)">'+(h.date||'')+'</div>'
      +'<div style="color:#f59e0b;font-size:14px">'+'⭐'.repeat(h.rating||5)+'</div>'
      +(h.note?'<div style="font-size:12px;color:var(--subtext);font-style:italic;margin-top:3px">"'+h.note+'"</div>':'')
      +'</div>'
      +'<button style="background:none;border:none;color:#ef4444;cursor:pointer;font-size:18px;padding:4px" id="del-'+realIdx+'">🗑</button>'
      +'</div>'
      +(h.photo?'<img src="'+h.photo+'" class="memory-photo" alt="Date photo">':'');
    el.appendChild(div);
    document.getElementById('del-'+realIdx).onclick=function(){deleteMemory(realIdx,h.db_id);};
  });
  var clearBtn=document.createElement('button');
  clearBtn.className='btn btn-gray';
  clearBtn.style.marginTop='8px';
  clearBtn.textContent='🗑 Clear All Memories';
  clearBtn.onclick=clearAllHistory;
  el.appendChild(clearBtn);
}

function deleteMemory(idx,dbId){
  history.splice(idx,1);
  renderHistory();
  updateNavBadges();
  if(currentUser&&dbId){
    fetch('/api/history/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({db_id:dbId})});
  }
  showToast('Memory deleted!');
}

function clearAllHistory(){
  if(!confirm('Delete all memories? This cannot be undone.'))return;
  history=[];
  renderHistory();
  updateNavBadges();
  if(currentUser){
    fetch('/api/history/clear',{method:'POST'});
  }
  showToast('All memories cleared!');
}

function renderSaved(){
  var el=document.getElementById('saved-list');
  if(!saved.length){el.innerHTML='<div class="empty"><div>💔</div><p>No saved ideas yet!<br>Swipe 💚 to save.</p></div>';return;}
  el.innerHTML='';
  saved.forEach(function(s,i){
    var div=document.createElement('div');
    div.className='card cat-'+(s.cat||'surprise');
    div.style.marginBottom='10px';
    div.innerHTML='<div class="card-top"><span style="font-size:32px">'+(s.emoji||'✨')+'</span>'
      +'<div class="card-meta"><div class="card-cost">'+(s.cost||'')+'</div><div>'+(s.duration||'')+'</div></div></div>'
      +'<div style="font-size:16px;font-weight:900;color:#fff;margin-bottom:4px">'+(s.title||'')+'</div>'
      +'<div style="font-size:12px;color:rgba(255,255,255,0.85)">'+(s.desc||'')+'</div>';
    var btns=document.createElement('div');btns.className='card-btns';
    var lb=document.createElement('button');lb.textContent='📖 Log';lb.onclick=function(){openLogModal(i);};
    var sh=document.createElement('button');sh.textContent='🔗 Share';sh.onclick=function(){shareIdea(s);};
    var ca=document.createElement('button');ca.textContent='📅';ca.onclick=function(){addToCalendar(s);};
    var db=document.createElement('button');db.textContent='🗑';db.onclick=function(){saved.splice(i,1);renderSaved();updateNavBadges();};
    btns.appendChild(lb);btns.appendChild(sh);btns.appendChild(ca);btns.appendChild(db);
    div.appendChild(btns);
    el.appendChild(div);
  });
  var clr=document.createElement('button');
  clr.className='btn btn-gray';clr.textContent='🗑 Clear All';
  clr.onclick=function(){saved=[];renderSaved();updateNavBadges();};
  el.appendChild(clr);
}

function openLogModal(idx){
  selectedRating=5;currentMemoryIdea=saved[idx];currentMemoryPhoto=null;
  var modal=document.createElement('div');
  modal.className='modal';
  modal.innerHTML='<div class="modal-box">'
    +'<h3 style="color:#f43f5e;font-size:16px;margin-bottom:4px">📖 Log This Date</h3>'
    +'<p style="color:var(--subtext);font-size:12px;margin-bottom:12px">'+currentMemoryIdea.title+'</p>'
    +'<div class="label">Rating</div>'
    +'<div class="rating-btns" id="rating-btns">'
    +[1,2,3,4,5].map(function(n){return '<button class="rating-btn '+(n===5?'selected':'')+'" onclick="selectRating('+n+',this)">'+'⭐'.repeat(n)+'</button>';}).join('')
    +'</div>'
    +'<div class="label" style="margin-top:10px">Note</div>'
    +'<textarea id="log-note" rows="3" placeholder="How did it go?"></textarea>'
    +'<div class="label" style="margin-top:10px">📸 Add Photo</div>'
    +'<input type="file" accept="image/*" onchange="handlePhoto(this)" style="font-size:12px;padding:6px">'
    +'<img id="photo-preview" class="photo-preview">'
    +'<div class="btn-row" style="margin-top:12px">'
    +'<button class="btn btn-gray" id="log-cancel">Cancel</button>'
    +'<button class="btn btn-pink" id="log-save">Save Memory</button>'
    +'</div></div>';
  document.body.appendChild(modal);
  document.getElementById('log-cancel').onclick=function(){modal.remove();};
  document.getElementById('log-save').onclick=function(){saveLog(modal);};
}

function selectRating(n,btn){
  selectedRating=n;
  document.querySelectorAll('.rating-btn').forEach(function(b){b.classList.remove('selected');});
  btn.classList.add('selected');
}

function handlePhoto(input){
  var file=input.files[0];if(!file)return;
  var reader=new FileReader();
  reader.onload=function(e){
    currentMemoryPhoto=e.target.result;
    var p=document.getElementById('photo-preview');
    p.src=currentMemoryPhoto;p.style.display='block';
  };
  reader.readAsDataURL(file);
}

function saveLog(modal){
  var note=document.getElementById('log-note').value;
  var mem=Object.assign({},currentMemoryIdea,{
    note:note,rating:selectedRating,
    date:new Date().toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}),
    photo:currentMemoryPhoto||null
  });
  history.push(mem);
  if(currentUser){
    fetch('/api/history',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(mem)});
  }
  modal.remove();updateNavBadges();showToast('Memory saved! 📖');
}

function showConfetti(){
  var c=document.getElementById('confetti');
  var cols=['#f43f5e','#a855f7','#3b82f6','#10b981','#f59e0b'];
  for(var i=0;i<50;i++){
    var p=document.createElement('div');p.className='confetti-piece';
    p.style.cssText='left:'+Math.random()*100+'%;top:-10px;background:'+cols[i%5]+';width:'+(Math.random()*8+6)+'px;height:'+(Math.random()*8+6)+'px;animation-delay:'+(Math.random()*.5)+'s;animation-duration:'+(Math.random()+2)+'s';
    c.appendChild(p);setTimeout(function(){if(p.parentNode)p.parentNode.removeChild(p);},3000);
  }
}

function showToast(msg){
  var t=document.createElement('div');t.className='toast';t.textContent=msg;
  document.body.appendChild(t);
  setTimeout(function(){t.style.opacity='0';t.style.transition='opacity .3s';setTimeout(function(){if(t.parentNode)t.parentNode.removeChild(t);},300);},1800);
}

function showTab(name,btn){
  document.querySelectorAll('.screen').forEach(function(s){s.classList.remove('active');});
  document.querySelectorAll('nav button').forEach(function(b){b.classList.remove('active');});
  document.getElementById('screen-'+name).classList.add('active');
  if(btn)btn.classList.add('active');
  if(name==='saved')renderSaved();
  if(name==='history')renderHistory();
  if(name==='couples')renderMatches();
  if(name==='stats')renderStats();
  if(name==='seasonal')loadSeasonal();
}

var deferredPrompt=null;
window.addEventListener('beforeinstallprompt',function(e){
  e.preventDefault();deferredPrompt=e;
  var banner=document.createElement('div');
  banner.style.cssText='position:fixed;bottom:65px;left:0;right:0;margin:0 12px;background:#f43f5e;color:#fff;border-radius:16px;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;z-index:400';
  banner.innerHTML='<div><div style="font-weight:900;font-size:14px">📱 Install DateSpark</div><div style="font-size:11px;opacity:.85">Add to your home screen!</div></div>'
    +'<div style="display:flex;gap:8px"><button id="install-btn" style="background:#fff;color:#f43f5e;border:none;border-radius:10px;padding:7px 12px;font-weight:900;font-size:12px;cursor:pointer">Install</button>'
    +'<button id="dismiss-btn" style="background:rgba(255,255,255,.2);color:#fff;border:none;border-radius:10px;padding:7px 10px;font-size:12px;cursor:pointer">✕</button></div>';
  document.body.appendChild(banner);
  document.getElementById('install-btn').onclick=function(){deferredPrompt.prompt();banner.remove();};
  document.getElementById('dismiss-btn').onclick=function(){banner.remove();};
});
if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js');
</script>
</body>
</html>
"""

if __name__ == "__main__":
    print("\n💘 DateSpark AI is running!")
    print("👉 Open your browser at: http://localhost:5000\n")
    app.run(debug=True, port=5000)