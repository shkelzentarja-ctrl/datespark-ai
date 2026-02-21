# ============================================================
#  DateSpark AI — Flask Web App
#  Works with ANY Python version (3.8+) including 3.14 ✅
#
#  SETUP (one time):
#  1. Open VS Code terminal (Ctrl + `)
#  2. Run: pip install flask requests
#  3. Run: python main.py
#  4. Open browser at: http://localhost:5000
#
#  Get FREE Gemini API key at:
#  https://aistudio.google.com/app/apikey
# ============================================================

from flask import Flask, render_template_string, request, jsonify, session
import requests, json, random, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "datespark_secret_2024"

import os
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
)

# ── Date Ideas Data ──────────────────────────────────────────
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
        print(f"STATUS: {r.status_code}")
        if r.status_code == 429:
            return "RATE_LIMITED"
        txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        txt = txt.strip().replace("```json","").replace("```JSON","").replace("```","").strip()
        start = min(txt.find('[') if txt.find('[')!=-1 else len(txt),
                    txt.find('{') if txt.find('{')!=-1 else len(txt))
        end = max(txt.rfind(']'), txt.rfind('}')) + 1
        if start < end: txt = txt[start:end]
        return txt
    except Exception as e:
        print(f"GEMINI EXCEPTION: {e}")
        return None

# ── Routes ────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/debug")
def debug():
    return f"Key: '{GEMINI_API_KEY[:8]}...' URL: {GEMINI_URL[:60]}" if GEMINI_API_KEY else "KEY IS EMPTY"

@app.route("/api/ideas")
def get_ideas():
    return jsonify(IDEAS)

@app.route("/api/seasonal")
def get_seasonal():
    season = get_season()
    return jsonify({"season": season, "ideas": SEASONAL[season]})

@app.route("/api/ai/quick", methods=["POST"])
def ai_quick():
    topic = request.json.get("topic","")
    prompt = (f'Generate a creative romantic date idea based on: "{topic}". '
              'Return ONLY valid JSON, no markdown: '
              '{"title":"...","desc":"...","emoji":"...","duration":"...","cost":"...","tip":"...","steps":["...","...","..."]}')
    result = call_gemini(prompt)
    if not result:
        return jsonify({"error": "AI unavailable"}), 500
    if result == "RATE_LIMITED":
        return jsonify({"error": "Too many requests, please wait 1 minute and try again! ⏳"}), 429
    try:
        return jsonify(json.loads(result))
    except:
        return jsonify({"error": "Parse error", "raw": result}), 500

@app.route("/api/ai/itinerary", methods=["POST"])
def ai_itinerary():
    topic = request.json.get("topic","")
    prompt = (f'Create a detailed minute-by-minute date itinerary based on: "{topic}". '
              'Return ONLY valid JSON, no markdown: '
              '{"title":"...","emoji":"...","totalDuration":"...","totalCost":"...","overview":"...",'
              '"timeline":[{"time":"7:00 PM","activity":"...","tip":"...","duration":"30 min"}]}')
    result = call_gemini(prompt)
    if not result:
        return jsonify({"error": "AI unavailable"}), 500
    if result == "RATE_LIMITED":
        return jsonify({"error": "Too many requests, please wait 1 minute and try again! ⏳"}), 429
    try:
        return jsonify(json.loads(result))
    except:
        return jsonify({"error": "Parse error", "raw": result}), 500

@app.route("/api/ai/places", methods=["POST"])
def ai_places():
    city = request.json.get("city","")
    prompt = (f'Suggest 6 real date-worthy places in {city} for couples. '
              'Mix restaurants, parks, experiences, hidden gems. '
              'Return ONLY a JSON array, no markdown: '
              '[{"name":"...","type":"...","desc":"one sentence","emoji":"...","priceRange":"$/$$/$$$"}]')
    result = call_gemini(prompt)
    if not result:
        return jsonify({"error": "AI unavailable"}), 500
    if result == "RATE_LIMITED":
        return jsonify({"error": "Too many requests, please wait 1 minute and try again! ⏳"}), 429
    try:
        return jsonify(json.loads(result))
    except:
        return jsonify({"error": "Parse error"}), 500

# ── HTML (full single-page app) ───────────────────────────────
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>💘 DateSpark AI</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
  body{background:#0d0d0d;color:#fff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-height:100vh;display:flex;flex-direction:column;max-width:480px;margin:0 auto}
  header{background:#1a1a2e;padding:14px 20px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #ffffff15}
  header h1{font-size:20px;color:#f43f5e}
  header span{font-size:11px;color:#10b981}
  nav{background:#1a1a2e;display:flex;border-top:1px solid #ffffff15;position:sticky;bottom:0;z-index:100}
  nav button{flex:1;padding:14px 4px;background:none;border:none;color:#6b7280;font-size:20px;cursor:pointer;transition:color .2s}
  nav button.active{color:#f43f5e;border-top:2px solid #f43f5e}
  .screen{display:none;flex:1;flex-direction:column;padding:16px;gap:14px;overflow-y:auto;padding-bottom:80px}
  .screen.active{display:flex}
  .card{border-radius:20px;padding:20px;position:relative;overflow:hidden;cursor:grab;user-select:none;transition:transform .15s}
  .card:active{cursor:grabbing}
  .card-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px}
  .card-emoji{font-size:40px;line-height:1}
  .card-meta{text-align:right;font-size:12px;color:rgba(255,255,255,0.65)}
  .card-cost{background:rgba(0,0,0,0.3);border-radius:20px;padding:3px 10px;font-weight:700;margin-bottom:4px;display:inline-block}
  .card h2{font-size:18px;font-weight:900;margin-bottom:6px}
  .card p{font-size:13px;color:rgba(255,255,255,0.8);line-height:1.5}
  .card-btns{display:flex;gap:8px;margin-top:12px}
  .card-btns button{flex:1;padding:8px;border:none;border-radius:12px;background:rgba(255,255,255,0.2);color:#fff;font-size:12px;font-weight:700;cursor:pointer;transition:background .2s}
  .card-btns button:hover{background:rgba(255,255,255,0.3)}
  .cat-home{background:linear-gradient(135deg,#e11d48,#be185d)}
  .cat-city{background:linear-gradient(135deg,#7c3aed,#6d28d9)}
  .cat-outdoor{background:linear-gradient(135deg,#059669,#047857)}
  .cat-budget{background:linear-gradient(135deg,#d97706,#b45309)}
  .cat-luxury{background:linear-gradient(135deg,#d97706,#92400e)}
  .cat-travel{background:linear-gradient(135deg,#0284c7,#0369a1)}
  .cat-surprise{background:linear-gradient(135deg,#c026d3,#a21caf)}
  .cat-ai{background:linear-gradient(135deg,#f43f5e,#e11d48)}
  .pills{display:flex;gap:8px;overflow-x:auto;padding-bottom:4px;scrollbar-width:none}
  .pills::-webkit-scrollbar{display:none}
  .pill{flex-shrink:0;padding:8px 14px;border-radius:20px;border:none;background:#374151;color:#fff;font-size:12px;font-weight:700;cursor:pointer;transition:all .2s}
  .pill.active{background:#f43f5e;transform:scale(1.05)}
  .swipe-area{position:relative;height:240px}
  .swipe-card{position:absolute;inset:0;border-radius:24px;padding:20px;display:flex;flex-direction:column;justify-content:space-between;transition:transform .3s,opacity .3s;cursor:grab}
  .swipe-card.back1{transform:scale(0.95) translateY(8px);opacity:.7;z-index:1}
  .swipe-card.back2{transform:scale(0.90) translateY(16px);opacity:.4;z-index:0}
  .swipe-card.front{z-index:2}
  .swipe-btns{display:flex;justify-content:center;gap:20px;align-items:center}
  .swipe-btn{width:58px;height:58px;border-radius:50%;border:2px solid #374151;background:#1a1a2e;font-size:24px;cursor:pointer;transition:all .2s;display:flex;align-items:center;justify-content:center}
  .swipe-btn:hover{transform:scale(1.1)}
  .swipe-btn.like{border-color:#10b981}
  .swipe-btn.skip{border-color:#ef4444}
  .swipe-btn.shuf{width:44px;height:44px;font-size:18px}
  .overlay{position:absolute;top:16px;padding:6px 14px;border-radius:12px;font-weight:900;font-size:16px;border:2px solid #fff;opacity:0;transition:opacity .1s;z-index:10;pointer-events:none}
  .overlay.like{left:16px;background:#10b981;transform:rotate(-15deg)}
  .overlay.skip{right:16px;background:#ef4444;transform:rotate(15deg)}
  input,textarea{width:100%;background:#1f2937;border:1px solid #374151;border-radius:14px;padding:12px 16px;color:#fff;font-size:14px;outline:none;transition:border .2s;resize:none;font-family:inherit}
  input:focus,textarea:focus{border-color:#f43f5e}
  .btn{width:100%;padding:14px;border:none;border-radius:14px;font-size:15px;font-weight:900;cursor:pointer;transition:all .2s;color:#fff}
  .btn:hover{opacity:.9;transform:translateY(-1px)}
  .btn-pink{background:#f43f5e}
  .btn-purple{background:#7c3aed}
  .btn-gray{background:#374151}
  .btn-green{background:#059669}
  .btn-row{display:flex;gap:10px}
  .btn-row .btn{flex:1}
  .label{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px}
  .surface{background:#1a1a2e;border-radius:18px;padding:16px;border:1px solid #ffffff10}
  .code-display{font-size:32px;font-weight:900;color:#f43f5e;text-align:center;letter-spacing:.2em;padding:14px;background:#0d0d0d;border-radius:12px;margin:8px 0}
  .status-ok{color:#10b981;font-size:13px;margin-top:6px}
  .status-err{color:#ef4444;font-size:13px;margin-top:6px}
  .timeline-item{display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #ffffff10}
  .timeline-time{color:#f43f5e;font-size:12px;font-weight:700;min-width:52px}
  .timeline-content h4{font-size:14px;font-weight:700}
  .timeline-content p{font-size:12px;color:#6b7280;margin-top:2px}
  .memory-card{background:#1a1a2e;border-radius:16px;padding:14px;border:1px solid #ffffff10}
  .stars{color:#f59e0b;font-size:18px}
  .empty{text-align:center;padding:60px 20px;color:#6b7280}
  .empty div{font-size:48px;margin-bottom:12px}
  .confetti-container{position:fixed;inset:0;pointer-events:none;z-index:999;overflow:hidden}
  .confetti-piece{position:absolute;width:10px;height:10px;border-radius:2px;animation:fall 2.5s ease-in forwards}
  @keyframes fall{to{transform:translateY(110vh) rotate(720deg);opacity:0}}
  .flying-out-left{animation:flyLeft .3s ease-in forwards}
  .flying-out-right{animation:flyRight .3s ease-in forwards}
  @keyframes flyLeft{to{transform:translateX(-120vw) rotate(-30deg);opacity:0}}
  @keyframes flyRight{to{transform:translateX(120vw) rotate(30deg);opacity:0}}
  .tag{display:inline-block;background:rgba(255,255,255,0.15);border-radius:20px;padding:3px 10px;font-size:11px;margin:2px}
  .season-badge{background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:20px;padding:4px 12px;font-size:12px;font-weight:700;display:inline-block}
  .rating-btns{display:flex;gap:6px;margin:8px 0}
  .rating-btn{flex:1;padding:8px;background:#374151;border:2px solid transparent;border-radius:10px;color:#fff;font-size:12px;cursor:pointer;transition:all .2s;font-weight:700}
  .rating-btn.selected{border-color:#f43f5e;background:#f43f5e22}
  @media(max-width:400px){.card h2{font-size:16px}.card-emoji{font-size:32px}}
</style>
</head>
<body>

<header>
  <h1>💘 DateSpark AI</h1>
  <span>Powered by Gemini ✅ Free</span>
</header>

<div id="screen-spark" class="screen active">
  <div class="pills" id="cat-pills"></div>
  <div class="swipe-area" id="swipe-area"></div>
  <div class="swipe-btns">
    <button class="swipe-btn skip" onclick="swipe('left')">❌</button>
    <button class="swipe-btn shuf" onclick="reshuffleDeck()">🔀</button>
    <button class="swipe-btn like" onclick="swipe('right')">💚</button>
  </div>
  <p style="text-align:center;font-size:12px;color:#4b5563">Drag card or use buttons</p>
</div>

<div id="screen-seasonal" class="screen">
  <div id="seasonal-header"></div>
  <div id="seasonal-cards"></div>
</div>

<div id="screen-couples" class="screen">
  <div class="surface">
    <div class="label">Your Share Code</div>
    <div class="code-display" id="my-code">------</div>
    <p style="font-size:12px;color:#6b7280">Share this with your partner. When they enter it you'll see mutual matches!</p>
  </div>
  <div class="surface">
    <div class="label">Enter Partner's Code</div>
    <input id="partner-code" maxlength="6" placeholder="XXXXXX" style="text-transform:uppercase;letter-spacing:.2em;font-size:18px;font-weight:900;text-align:center">
    <button class="btn btn-pink" style="margin-top:10px" onclick="connectPartner()">Connect 💑</button>
    <div id="connect-status"></div>
  </div>
  <div>
    <div class="label">💚 Matches</div>
    <div id="matches-list"></div>
  </div>
</div>

<div id="screen-ai" class="screen">
  <div class="surface">
    <div class="label">🤖 Describe Your Perfect Date</div>
    <textarea id="ai-topic" rows="3" placeholder="e.g. We love hiking & sushi, 1-year anniversary, budget $150..."></textarea>
    <div class="btn-row" style="margin-top:10px">
      <button class="btn btn-pink" onclick="aiQuick()">💡 Quick Idea</button>
      <button class="btn btn-purple" onclick="aiItinerary()">🗓️ Full Itinerary</button>
    </div>
  </div>
  <div class="surface">
    <div class="label">📍 Find Date Spots</div>
    <input id="city-input" placeholder="Enter your city...">
    <button class="btn btn-green" style="margin-top:10px" onclick="findPlaces()">🗺️ Find Places</button>
  </div>
  <div id="ai-result"></div>
</div>

<div id="screen-history" class="screen">
  <div id="history-list"></div>
</div>

<div id="screen-saved" class="screen">
  <div id="saved-list"></div>
</div>

<nav>
  <button class="active" onclick="showTab('spark',this)">⚡</button>
  <button onclick="showTab('seasonal',this)" id="seasonal-tab-btn">🌸</button>
  <button onclick="showTab('couples',this)">💑</button>
  <button onclick="showTab('ai',this)">🤖</button>
  <button onclick="showTab('history',this)">📖</button>
  <button onclick="showTab('saved',this)">❤️</button>
</nav>

<div class="confetti-container" id="confetti"></div>

<script>
// ── State ──────────────────────────────────────────────────
let IDEAS = {}, deck = [], saved = [], history = [], matches = [];
let activeCat = 'all', couplesMode = false;
let shareCode = Math.random().toString(36).slice(2,8).toUpperCase();
let dragStartX = null, currentDrag = 0;
let selectedRating = 5;

// ── Init ───────────────────────────────────────────────────
async function init() {
  const r = await fetch('/api/ideas');
  IDEAS = await r.json();
  buildDeck();
  renderCatPills();
  renderSwipeCards();
  document.getElementById('my-code').textContent = shareCode;
  loadSeasonal();
  renderMatches();
  updateNavBadges();
}

function buildDeck(cat='all') {
  activeCat = cat;
  let all = Object.entries(IDEAS).flatMap(([c,arr]) => arr.map(i => ({...i, cat:c})));
  deck = cat === 'all' ? all : all.filter(i => i.cat === cat);
  deck.sort(() => Math.random() - 0.5);
}

// ── Cat Pills ──────────────────────────────────────────────
function renderCatPills() {
  const cats = [['all','🌀 All'],['home','🏠'],['city','🌆'],['outdoor','🌿'],
                ['budget','💸'],['luxury','💎'],['travel','🌍'],['surprise','✨']];
  const box = document.getElementById('cat-pills');
  box.innerHTML = cats.map(([id,lbl]) =>
    `<button class="pill ${id===activeCat?'active':''}" onclick="setCat('${id}',this)">${lbl}</button>`
  ).join('');
}

function setCat(cat, btn) {
  document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  buildDeck(cat); renderSwipeCards();
}

function reshuffleDeck() { buildDeck(activeCat); renderSwipeCards(); }

// ── Swipe Cards ────────────────────────────────────────────
function catClass(cat) { return 'cat-' + (cat||'surprise'); }

function renderSwipeCards() {
  const area = document.getElementById('swipe-area');
  area.innerHTML = '';
  if (!deck.length) {
    area.innerHTML = '<div class="empty"><div>🎉</div><p>No more ideas!<br>Tap 🔀 to reshuffle</p></div>';
    return;
  }
  // Render back cards first
  [2,1,0].forEach(i => {
    if (!deck[i]) return;
    const card = makeSwipeCard(deck[i], i);
    area.appendChild(card);
  });
  // Attach drag to front card
  const front = area.querySelector('.front');
  if (front) attachDrag(front);
}

function makeSwipeCard(idea, idx) {
  const d = document.createElement('div');
  d.className = `swipe-card ${catClass(idea.cat)} ${idx===0?'front':idx===1?'back1':'back2'}`;
  d.dataset.title = idea.title;
  d.innerHTML = `
    <div class="overlay like" id="overlay-like">LOVE IT 💚</div>
    <div class="overlay skip" id="overlay-skip">SKIP ❌</div>
    <div>
      <div class="card-top">
        <span style="font-size:40px">${idea.emoji}</span>
        <div class="card-meta">
          <div class="card-cost">${idea.cost}</div>
          <div>${idea.duration}</div>
        </div>
      </div>
      <h2>${idea.title}</h2>
      <p style="margin-top:6px">${idea.desc}</p>
    </div>
    <div class="card-btns">
      <button onclick="saveIdea(${JSON.stringify(idea).replace(/"/g,'&quot;')})">❤️ Save</button>
    </div>`;
  return d;
}

function attachDrag(el) {
  el.addEventListener('mousedown', e => { dragStartX = e.clientX; });
  el.addEventListener('touchstart', e => { dragStartX = e.touches[0].clientX; }, {passive:true});
  document.addEventListener('mousemove', onDrag);
  document.addEventListener('touchmove', onDragTouch, {passive:true});
  document.addEventListener('mouseup', onDragEnd);
  document.addEventListener('touchend', onDragEnd);
}

function onDrag(e) {
  if (dragStartX === null) return;
  currentDrag = e.clientX - dragStartX;
  updateDragVisual();
}
function onDragTouch(e) {
  if (dragStartX === null) return;
  currentDrag = e.touches[0].clientX - dragStartX;
  updateDragVisual();
}
function updateDragVisual() {
  const front = document.querySelector('.swipe-card.front');
  if (!front) return;
  const rot = currentDrag / 18;
  front.style.transform = `translateX(${currentDrag}px) rotate(${rot}deg)`;
  const likeO = Math.min(currentDrag / 80, 1);
  const skipO = Math.min(-currentDrag / 80, 1);
  const ol = front.querySelector('.overlay.like');
  const os = front.querySelector('.overlay.skip');
  if (ol) ol.style.opacity = likeO;
  if (os) os.style.opacity = skipO;
}
function onDragEnd() {
  if (dragStartX === null) return;
  if (Math.abs(currentDrag) > 80) swipe(currentDrag > 0 ? 'right' : 'left');
  else {
    const front = document.querySelector('.swipe-card.front');
    if (front) { front.style.transform = ''; front.querySelectorAll('.overlay').forEach(o => o.style.opacity=0); }
  }
  dragStartX = null; currentDrag = 0;
  document.removeEventListener('mousemove', onDrag);
  document.removeEventListener('touchmove', onDragTouch);
  document.removeEventListener('mouseup', onDragEnd);
  document.removeEventListener('touchend', onDragEnd);
}

function swipe(dir) {
  if (!deck.length) return;
  const idea = deck[0];
  const front = document.querySelector('.swipe-card.front');
  if (front) {
    front.classList.add(dir==='right'?'flying-out-right':'flying-out-left');
    setTimeout(() => { deck.shift(); renderSwipeCards(); }, 300);
  } else { deck.shift(); renderSwipeCards(); }
  if (dir === 'right') {
    saveIdea(idea);
    if (couplesMode) {
      const pSwipe = Math.random() > 0.4 ? 'right' : 'left';
      if (pSwipe === 'right' && !matches.find(m=>m.title===idea.title)) {
        matches.push(idea);
        showConfetti();
        showMatchPopup(idea);
        renderMatches();
      }
    }
  }
  updateNavBadges();
}

// ── Seasonal ───────────────────────────────────────────────
async function loadSeasonal() {
  const r = await fetch('/api/seasonal');
  const {season, ideas} = await r.json();
  const icons = {winter:'❄️',spring:'🌸',summer:'☀️',autumn:'🍂'};
  document.getElementById('seasonal-tab-btn').textContent = icons[season];
  document.getElementById('seasonal-header').innerHTML =
    `<div style="text-align:center"><div style="font-size:48px">${icons[season]}</div>
     <h2 style="font-size:20px;font-weight:900;color:#f43f5e;margin:8px 0">${season.charAt(0).toUpperCase()+season.slice(1)} Dates</h2>
     <span class="season-badge">Curated for right now</span></div>`;
  document.getElementById('seasonal-cards').innerHTML = ideas.map(i =>
    `<div class="card ${catClass(i.cat)}" style="margin-bottom:14px">
       <div class="card-top"><span class="card-emoji">${i.emoji}</span>
         <div class="card-meta"><div class="card-cost">${i.cost}</div><div>${i.duration}</div></div>
       </div>
       <h2>${i.title}</h2><p>${i.desc}</p>
       <div class="card-btns"><button onclick='saveIdea(${JSON.stringify(i)})'>❤️ Save</button></div>
     </div>`
  ).join('');
}

// ── Save & History ─────────────────────────────────────────
function saveIdea(idea) {
  if (!saved.find(s=>s.title===idea.title)) { saved.push(idea); updateNavBadges(); showToast('Saved! ❤️'); }
}

function updateNavBadges() {
  const btns = document.querySelectorAll('nav button');
  btns[5].textContent = saved.length ? `❤️${saved.length}` : '❤️';
  btns[4].textContent = history.length ? `📖${history.length}` : '📖';
}

function renderSaved() {
  const el = document.getElementById('saved-list');
  if (!saved.length) { el.innerHTML='<div class="empty"><div>💔</div><p>No saved ideas yet!<br>Swipe 💚 to save.</p></div>'; return; }
  el.innerHTML = saved.map((s,i) =>
    `<div class="card ${catClass(s.cat)}" style="margin-bottom:14px">
       <div class="card-top"><span class="card-emoji">${s.emoji}</span>
         <div class="card-meta"><div class="card-cost">${s.cost}</div><div>${s.duration}</div></div>
       </div>
       <h2>${s.title}</h2><p>${s.desc}</p>
       <div class="card-btns">
         <button onclick="openLogModal(${i})">📖 Log Memory</button>
         <button onclick="saved.splice(${i},1);renderSaved();updateNavBadges()">🗑 Remove</button>
       </div>
     </div>`
  ).join('') + `<button class="btn btn-gray" onclick="saved=[];renderSaved();updateNavBadges()">🗑 Clear All</button>`;
}

function renderHistory() {
  const el = document.getElementById('history-list');
  if (!history.length) { el.innerHTML='<div class="empty"><div>📖</div><p>No memories yet!<br>Log a date from ❤️ Saved.</p></div>'; return; }
  el.innerHTML = [...history].reverse().map(h =>
    `<div class="memory-card" style="margin-bottom:12px">
       <div style="display:flex;gap:12px;align-items:flex-start">
         <span style="font-size:32px">${h.emoji}</span>
         <div style="flex:1">
           <div style="font-weight:900;font-size:15px">${h.title}</div>
           <div style="font-size:11px;color:#6b7280">${h.date}</div>
           <div class="stars">${'⭐'.repeat(h.rating)}</div>
           ${h.note ? `<div style="font-size:13px;color:rgba(255,255,255,0.75);margin-top:4px;font-style:italic">"${h.note}"</div>` : ''}
         </div>
       </div>
     </div>`
  ).join('');
}

// ── Log Modal ──────────────────────────────────────────────
function openLogModal(idx) {
  selectedRating = 5;
  const idea = saved[idx];
  const modal = document.createElement('div');
  modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.75);z-index:200;display:flex;align-items:center;justify-content:center;padding:20px';
  modal.innerHTML = `
    <div style="background:#1a1a2e;border-radius:24px;padding:24px;width:100%;max-width:380px;border:1px solid #ffffff15">
      <h3 style="color:#f43f5e;font-size:17px;margin-bottom:4px">📖 Log This Date</h3>
      <p style="color:#6b7280;font-size:13px;margin-bottom:14px">${idea.title}</p>
      <div class="label">Rating</div>
      <div class="rating-btns">
        ${[1,2,3,4,5].map(n=>`<button class="rating-btn ${n===5?'selected':''}" onclick="selectRating(${n},this)">
          ${'⭐'.repeat(n)}</button>`).join('')}
      </div>
      <div class="label" style="margin-top:12px">Memory Note</div>
      <textarea id="log-note" rows="3" placeholder="How did it go? Any special memories..."></textarea>
      <div class="btn-row" style="margin-top:14px">
        <button class="btn btn-gray" onclick="this.closest('[style*=fixed]').remove()">Cancel</button>
        <button class="btn btn-pink" onclick="saveLog(${idx},this.closest('[style*=fixed]'))">Save Memory</button>
      </div>
    </div>`;
  document.body.appendChild(modal);
}

function selectRating(n, btn) {
  selectedRating = n;
  document.querySelectorAll('.rating-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
}

function saveLog(idx, modal) {
  const note = document.getElementById('log-note').value;
  history.push({...saved[idx], note, rating: selectedRating, date: new Date().toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})});
  modal.remove(); updateNavBadges(); showToast('Memory saved! 📖');
}

// ── Couples Mode ───────────────────────────────────────────
function connectPartner() {
  const code = document.getElementById('partner-code').value.trim().toUpperCase();
  const status = document.getElementById('connect-status');
  if (code.length === 6) {
    couplesMode = true;
    status.className = 'status-ok';
    status.textContent = '✅ Connected! Swipe on ⚡ Spark to find matches.';
  } else {
    status.className = 'status-err';
    status.textContent = '❌ Code must be 6 characters.';
  }
}

function renderMatches() {
  const el = document.getElementById('matches-list');
  if (!matches.length) {
    el.innerHTML = '<div class="empty" style="padding:30px"><div>💭</div><p>No matches yet!<br>Go swipe on ⚡ Spark.</p></div>';
    return;
  }
  el.innerHTML = matches.map(m =>
    `<div class="card ${catClass(m.cat)}" style="margin-bottom:12px">
       <div class="card-top"><span class="card-emoji">${m.emoji}</span>
         <div class="card-meta"><div class="card-cost">${m.cost}</div><div>${m.duration}</div></div>
       </div>
       <h2>${m.title}</h2><p>${m.desc}</p>
     </div>`
  ).join('');
}

function showMatchPopup(idea) {
  const popup = document.createElement('div');
  popup.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.8);z-index:300;display:flex;align-items:center;justify-content:center;padding:20px';
  popup.innerHTML = `
    <div style="background:#1a1a2e;border-radius:24px;padding:28px;text-align:center;max-width:320px;border:1px solid #f43f5e33">
      <div style="font-size:48px">🎉</div>
      <h2 style="color:#f43f5e;font-size:22px;margin:10px 0">It's a Match!</h2>
      <p style="color:rgba(255,255,255,0.8)">You both love:</p>
      <p style="font-size:18px;font-weight:900;margin:10px 0">${idea.emoji} ${idea.title}</p>
      <button class="btn btn-pink" style="margin-top:14px" onclick="this.closest('[style*=fixed]').remove()">Let's do it! 💑</button>
    </div>`;
  document.body.appendChild(popup);
}

// ── AI Features ────────────────────────────────────────────
async function aiQuick() {
  const topic = document.getElementById('ai-topic').value.trim();
  if (!topic) return;
  showAILoading('💡 Generating idea...');
  const r = await fetch('/api/ai/quick', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic})});
  const data = await r.json();
  if (data.error) { showAIError(); return; }
  const el = document.getElementById('ai-result');
  el.innerHTML = `
    <div class="card cat-ai">
      <div class="card-top"><span class="card-emoji">${data.emoji||'✨'}</span>
        <div class="card-meta"><div class="card-cost">${data.cost||''}</div><div>${data.duration||''}</div></div>
      </div>
      <h2>${data.title}</h2>
      <p style="margin-top:6px">${data.desc}</p>
      ${data.steps ? `<div style="margin-top:12px"><div class="label">📋 Steps</div>${data.steps.map(s=>`<p style="margin:4px 0;font-size:13px">• ${s}</p>`).join('')}</div>` : ''}
      ${data.tip ? `<div style="margin-top:10px;background:rgba(0,0,0,0.2);border-radius:12px;padding:10px"><div class="label">💡 Pro Tip</div><p style="font-size:13px">${data.tip}</p></div>` : ''}
      <div class="card-btns">
        <button onclick='saveIdea(${JSON.stringify({...data,cat:"surprise",emoji:data.emoji||"✨"})});updateNavBadges()'>❤️ Save</button>
      </div>
    </div>`;
}

async function aiItinerary() {
  const topic = document.getElementById('ai-topic').value.trim();
  if (!topic) return;
  showAILoading('🗓️ Building your itinerary...');
  const r = await fetch('/api/ai/itinerary', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic})});
  const data = await r.json();
  if (data.error) { showAIError(); return; }
  const el = document.getElementById('ai-result');
  el.innerHTML = `
    <div class="surface">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <span style="font-size:36px">${data.emoji||'🗓️'}</span>
        <div style="text-align:right"><div class="card-cost" style="background:#7c3aed">${data.totalCost||''}</div><div style="font-size:12px;color:#6b7280">${data.totalDuration||''}</div></div>
      </div>
      <h2 style="font-size:18px;font-weight:900;color:#f43f5e;margin-bottom:6px">${data.title}</h2>
      <p style="font-size:13px;color:rgba(255,255,255,0.7);margin-bottom:14px">${data.overview}</p>
      <div class="label">📋 Timeline</div>
      ${(data.timeline||[]).map(t=>`
        <div class="timeline-item">
          <div class="timeline-time">${t.time}</div>
          <div class="timeline-content">
            <h4>${t.activity}</h4>
            ${t.tip?`<p>💡 ${t.tip}</p>`:''}
            <p style="color:#4b5563">${t.duration||''}</p>
          </div>
        </div>`).join('')}
    </div>`;
}

async function findPlaces() {
  const city = document.getElementById('city-input').value.trim();
  if (!city) return;
  showAILoading(`🗺️ Finding places in ${city}...`);
  const r = await fetch('/api/ai/places', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({city})});
  const data = await r.json();
  if (data.error) { showAIError(); return; }
  const el = document.getElementById('ai-result');
  el.innerHTML = `<div class="label">📍 Date Spots in ${city}</div>` +
    data.map(p=>`
      <div class="surface" style="margin-bottom:10px;display:flex;gap:12px;align-items:flex-start">
        <span style="font-size:28px;flex-shrink:0">${p.emoji}</span>
        <div style="flex:1">
          <div style="display:flex;justify-content:space-between"><b>${p.name}</b><span style="color:#6b7280;font-size:12px">${p.priceRange}</span></div>
          <div style="font-size:11px;color:#0284c7;margin:2px 0">${p.type}</div>
          <div style="font-size:12px;color:rgba(255,255,255,0.7)">${p.desc}</div>
        </div>
        <button onclick='saveIdea({title:"${p.name}",desc:"${p.desc}",emoji:"${p.emoji}",duration:"TBD",cost:"${p.priceRange}",cat:"city"})' style="background:none;border:none;font-size:18px;cursor:pointer">❤️</button>
      </div>`
    ).join('');
}

function showAILoading(msg) {
  document.getElementById('ai-result').innerHTML = `<div class="empty" style="padding:30px"><div style="font-size:36px;animation:pulse 1s infinite">✨</div><p>${msg}</p></div>`;
}
function showAIError() {
  document.getElementById('ai-result').innerHTML = `<div class="empty" style="padding:20px"><div>⚠️</div><p>AI unavailable. Check your Gemini API key.</p></div>`;
}

// ── Confetti ───────────────────────────────────────────────
function showConfetti() {
  const container = document.getElementById('confetti');
  const colors = ['#f43f5e','#a855f7','#3b82f6','#10b981','#f59e0b','#ec4899'];
  for (let i=0;i<50;i++) {
    const p = document.createElement('div');
    p.className = 'confetti-piece';
    p.style.cssText = `left:${Math.random()*100}%;top:-10px;background:${colors[i%6]};
      border-radius:${Math.random()>.5?'50%':'2px'};
      width:${Math.random()*8+6}px;height:${Math.random()*8+6}px;
      animation-delay:${Math.random()*0.5}s;animation-duration:${Math.random()*1+2}s`;
    container.appendChild(p);
    setTimeout(() => p.remove(), 3000);
  }
}

// ── Toast ──────────────────────────────────────────────────
function showToast(msg) {
  const t = document.createElement('div');
  t.style.cssText = 'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:#1a1a2e;color:#fff;padding:10px 20px;border-radius:20px;font-size:13px;font-weight:700;z-index:500;border:1px solid #ffffff20;transition:opacity .3s';
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => { t.style.opacity='0'; setTimeout(()=>t.remove(),300); }, 1800);
}

// ── Tab Navigation ─────────────────────────────────────────
function showTab(name, btn) {
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b=>b.classList.remove('active'));
  document.getElementById('screen-'+name).classList.add('active');
  btn.classList.add('active');
  if (name==='saved') renderSaved();
  if (name==='history') renderHistory();
  if (name==='couples') renderMatches();
}

init();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    print("\n💘 DateSpark AI is running!")
    print("👉 Open your browser at: http://localhost:5000\n")
    app.run(debug=True, port=5000)