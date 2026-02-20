# ============================================================
#  DateSpark AI — Ultimate Edition
#  All 10 features included:
#  ✅ User accounts & login
#  ✅ Multi-language support
#  ✅ Add photos to date memories
#  ✅ Google Calendar integration
#  ✅ Date ideas chat assistant
#  ✅ Personalized recommendations
#  ✅ Date stats dashboard
#  ✅ Push notifications
#  ✅ Light/Dark mode toggle
#  ✅ Share via WhatsApp/Email
#
#  Install: pip install flask requests
#  Run:     python main.py
#  Visit:   http://localhost:5000
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

# ── SQLite Database Setup ────────────────────────────────────
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
                avatar TEXT DEFAULT NULL,
                couple_partner TEXT DEFAULT NULL,
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
        db.execute("""
            CREATE TABLE IF NOT EXISTS couple_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                couple_code TEXT NOT NULL,
                username TEXT NOT NULL,
                photo TEXT NOT NULL,
                caption TEXT DEFAULT '',
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()

# Initialize DB on startup
init_db()

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

TRANSLATIONS = {
    "en": {"title": "DateSpark AI", "spark": "Spark", "seasonal": "Seasonal", "couples": "Couples",
           "ai": "AI", "chat": "Chat", "stats": "Stats", "history": "History", "saved": "Saved",
           "login": "Login", "register": "Register", "logout": "Logout", "username": "Username",
           "password": "Password", "dark_mode": "Dark Mode", "light_mode": "Light Mode",
           "share": "Share", "save": "Save", "log": "Log Memory", "find_places": "Find Places",
           "quick_idea": "Quick Idea", "full_itinerary": "Full Itinerary", "send": "Send",
           "type_message": "Ask me anything about dates...", "your_code": "Your Share Code",
           "enter_code": "Enter Partner's Code", "connect": "Connect", "matches": "Matches",
           "no_matches": "No matches yet! Go swipe together.", "clear_all": "Clear All",
           "add_to_calendar": "Add to Calendar", "whatsapp": "WhatsApp", "email": "Email"},
    "es": {"title": "DateSpark IA", "spark": "Descubrir", "seasonal": "Temporada", "couples": "Pareja",
           "ai": "IA", "chat": "Chat", "stats": "Stats", "history": "Historia", "saved": "Guardado",
           "login": "Entrar", "register": "Registrar", "logout": "Salir", "username": "Usuario",
           "password": "Contraseña", "dark_mode": "Modo Oscuro", "light_mode": "Modo Claro",
           "share": "Compartir", "save": "Guardar", "log": "Registrar", "find_places": "Buscar Lugares",
           "quick_idea": "Idea Rápida", "full_itinerary": "Itinerario", "send": "Enviar",
           "type_message": "Pregúntame sobre citas...", "your_code": "Tu Código", "whatsapp": "WhatsApp",
           "enter_code": "Código de tu Pareja", "connect": "Conectar", "matches": "Coincidencias",
           "no_matches": "Sin coincidencias todavía.", "clear_all": "Borrar Todo",
           "add_to_calendar": "Añadir al Calendario", "email": "Email"},
    "fr": {"title": "DateSpark IA", "spark": "Découvrir", "seasonal": "Saison", "couples": "Couple",
           "ai": "IA", "chat": "Chat", "stats": "Stats", "history": "Histoire", "saved": "Sauvé",
           "login": "Connexion", "register": "S'inscrire", "logout": "Déconnexion", "username": "Utilisateur",
           "password": "Mot de passe", "dark_mode": "Mode Sombre", "light_mode": "Mode Clair",
           "share": "Partager", "save": "Sauver", "log": "Journal", "find_places": "Trouver des Lieux",
           "quick_idea": "Idée Rapide", "full_itinerary": "Itinéraire", "send": "Envoyer",
           "type_message": "Demandez-moi des idées de rendez-vous...", "your_code": "Votre Code",
           "enter_code": "Code de votre Partenaire", "connect": "Connecter", "matches": "Correspondances",
           "no_matches": "Pas encore de correspondances.", "clear_all": "Tout Effacer",
           "add_to_calendar": "Ajouter au Calendrier", "whatsapp": "WhatsApp", "email": "Email"},
    "de": {"title": "DateSpark KI", "spark": "Entdecken", "seasonal": "Saison", "couples": "Paar",
           "ai": "KI", "chat": "Chat", "stats": "Stats", "history": "Geschichte", "saved": "Gespeichert",
           "login": "Anmelden", "register": "Registrieren", "logout": "Abmelden", "username": "Benutzername",
           "password": "Passwort", "dark_mode": "Dunkelmodus", "light_mode": "Hellmodus",
           "share": "Teilen", "save": "Speichern", "log": "Erinnerung", "find_places": "Orte finden",
           "quick_idea": "Schnelle Idee", "full_itinerary": "Reiseplan", "send": "Senden",
           "type_message": "Fragen Sie mich nach Date-Ideen...", "your_code": "Ihr Code",
           "enter_code": "Code Ihres Partners", "connect": "Verbinden", "matches": "Übereinstimmungen",
           "no_matches": "Noch keine Übereinstimmungen.", "clear_all": "Alle löschen",
           "add_to_calendar": "Zum Kalender", "whatsapp": "WhatsApp", "email": "Email"},
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
        saved = [json.loads(r["idea"]) for r in db.execute("SELECT idea FROM saved_ideas WHERE username=? ORDER BY saved_at", (u,)).fetchall()]
        history = [json.loads(r["memory"]) for r in db.execute("SELECT memory FROM date_history WHERE username=? ORDER BY logged_at", (u,)).fetchall()]
    session["user"] = u
    return jsonify({"success": True, "username": u, "share_code": user["share_code"], "saved": saved, "history": history})

@app.route("/api/avatar", methods=["POST"])
def update_avatar():
    u = session.get("user")
    if not u: return jsonify({"error": "Not logged in"}), 401
    photo = request.json.get("photo")
    with get_db() as db:
        db.execute("UPDATE users SET avatar=? WHERE username=?", (photo, u))
        db.commit()
    return jsonify({"success": True})

@app.route("/api/couple/photos", methods=["GET"])
def get_couple_photos():
    u = session.get("user")
    if not u: return jsonify({"error": "Not logged in"}), 401
    with get_db() as db:
        user = db.execute("SELECT share_code FROM users WHERE username=?", (u,)).fetchone()
        if not user: return jsonify([])
        photos = db.execute(
            "SELECT * FROM couple_photos WHERE couple_code=? ORDER BY uploaded_at DESC",
            (user["share_code"],)
        ).fetchall()
    return jsonify([dict(p) for p in photos])

@app.route("/api/couple/photos", methods=["POST"])
def add_couple_photo():
    u = session.get("user")
    if not u: return jsonify({"error": "Not logged in"}), 401
    d = request.json
    photo = d.get("photo")
    caption = d.get("caption", "")
    with get_db() as db:
        user = db.execute("SELECT share_code FROM users WHERE username=?", (u,)).fetchone()
        db.execute(
            "INSERT INTO couple_photos (couple_code, username, photo, caption) VALUES (?,?,?,?)",
            (user["share_code"], u, photo, caption)
        )
        db.commit()
    return jsonify({"success": True})

@app.route("/api/couple/photos/<int:photo_id>", methods=["DELETE"])
def delete_couple_photo(photo_id):
    u = session.get("user")
    if not u: return jsonify({"error": "Not logged in"}), 401
    with get_db() as db:
        db.execute("DELETE FROM couple_photos WHERE id=? AND username=?", (photo_id, u))
        db.commit()
    return jsonify({"success": True})

@app.route("/api/gallery")
def get_gallery():
    u = session.get("user")
    if not u: return jsonify({"error": "Not logged in"}), 401
    with get_db() as db:
        memories = [json.loads(r["memory"]) for r in db.execute(
            "SELECT memory FROM date_history WHERE username=? ORDER BY logged_at DESC", (u,)
        ).fetchall()]
    photos = [{"photo": m["photo"], "title": m["title"], "date": m["date"], "rating": m.get("rating",5)}
              for m in memories if m.get("photo")]
    return jsonify(photos)

@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"success": True})

# ── Data Routes ───────────────────────────────────────────────
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
        existing = [json.loads(r["idea"]) for r in db.execute("SELECT idea FROM saved_ideas WHERE username=?", (u,)).fetchall()]
        if not any(s["title"]==idea["title"] for s in existing):
            db.execute("INSERT INTO saved_ideas (username, idea) VALUES (?,?)", (u, json.dumps(idea)))
            db.commit()
        saved = [json.loads(r["idea"]) for r in db.execute("SELECT idea FROM saved_ideas WHERE username=? ORDER BY saved_at", (u,)).fetchall()]
    return jsonify({"success": True, "saved": saved})

@app.route("/api/history", methods=["POST"])
def add_history():
    u = session.get("user")
    if not u: return jsonify({"error": "Not logged in"}), 401
    with get_db() as db:
        db.execute("INSERT INTO date_history (username, memory) VALUES (?,?)", (u, json.dumps(request.json)))
        db.commit()
    return jsonify({"success": True})

@app.route("/api/userdata")
def get_userdata():
    u = session.get("user")
    if not u: return jsonify({"error": "Not logged in"}), 401
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
        saved = [json.loads(r["idea"]) for r in db.execute("SELECT idea FROM saved_ideas WHERE username=? ORDER BY saved_at", (u,)).fetchall()]
        history = [json.loads(r["memory"]) for r in db.execute("SELECT memory FROM date_history WHERE username=? ORDER BY logged_at", (u,)).fetchall()]
    return jsonify({"saved": saved, "history": history, "share_code": user["share_code"]})

# ── AI Routes ─────────────────────────────────────────────────
@app.route("/api/translate-ideas", methods=["POST"])
def translate_ideas():
    d = request.json
    ideas = d.get("ideas", [])
    lang = d.get("lang", "en")
    lang_names = {"es": "Spanish", "fr": "French", "de": "German"}
    if lang == "en" or lang not in lang_names:
        return jsonify(ideas)
    lang_name = lang_names[lang]
    prompt = (f'Translate these date ideas to {lang_name}. '
              f'Only translate "title" and "desc" fields, keep all other fields exactly the same. '
              f'Return ONLY a valid JSON array, no markdown: {json.dumps(ideas)}')
    result = call_gemini(prompt)
    if not result:
        return jsonify(ideas)
    try:
        return jsonify(json.loads(result))
    except:
        return jsonify(ideas)

@app.route("/api/ai/generate-ideas", methods=["POST"])
def ai_generate_ideas():
    d = request.json
    cat = d.get("cat", "surprise")
    exclude = d.get("exclude", [])
    u = session.get("user")
    done = []
    if u:
        with get_db() as db:
            done = [json.loads(r["memory"])["title"] for r in db.execute("SELECT memory FROM date_history WHERE username=?", (u,)).fetchall()]
    exclude_all = list(set(exclude + done))
    prompt = (f'Generate 6 creative and unique {cat} date ideas for couples. '
              f'{"Avoid these: " + ", ".join(exclude_all[:10]) + "." if exclude_all else ""} '
              f'Make them fresh, fun and specific. '
              f'Return ONLY a JSON array, no markdown: '
              f'[{{"title":"...","desc":"one engaging sentence","emoji":"...","duration":"...","cost":"$/$/$$/$$/Free","cat":"{cat}"}}]')
    result = call_gemini(prompt)
    if not result: return jsonify({"error": "AI unavailable"}), 500
    try: return jsonify(json.loads(result))
    except: return jsonify({"error": "Parse error"}), 500

@app.route("/api/ai/quick", methods=["POST"])
def ai_quick():
    topic = request.json.get("topic","")
    u = session.get("user")
    history_ctx = ""
    if u and USERS[u]["history"]:
        done = [h["title"] for h in USERS[u]["history"][-5:]]
        history_ctx = f' Avoid these already done: {", ".join(done)}.'
    prompt = (f'Generate a creative romantic date idea based on: "{topic}".{history_ctx} '
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

@app.route("/api/ai/recommend", methods=["POST"])
def ai_recommend():
    u = session.get("user")
    history, saved = [], []
    if u:
        with get_db() as db:
            history = [json.loads(r["memory"]) for r in db.execute("SELECT memory FROM date_history WHERE username=? ORDER BY logged_at DESC LIMIT 10", (u,)).fetchall()]
    cats = [h.get("cat","surprise") for h in history]
    fav_cat = max(set(cats), key=cats.count) if cats else "surprise"
    done_titles = [h["title"] for h in history]
    prompt = (f'Based on someone who loves {fav_cat} dates and has done: {", ".join(done_titles[-3:]) if done_titles else "nothing yet"}, '
              f'suggest 3 personalized date ideas they have NOT done yet. '
              'Return ONLY a JSON array: [{"title":"...","desc":"...","emoji":"...","duration":"...","cost":"...","cat":"...","reason":"why this suits them"}]')
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
    ctx = "\n".join([f"{'User' if m['role']=='user' else 'Assistant'}: {m['text']}" for m in chat_history[-6:]])
    prompt = (f'You are a friendly date idea assistant. Respond in {"English" if lang=="en" else "Spanish" if lang=="es" else "French" if lang=="fr" else "German"}. '
              f'Previous conversation:\n{ctx}\nUser: {msg}\n'
              f'Give a helpful, fun, concise response about date ideas. Keep it under 100 words.')
    result = call_gemini(prompt)
    if not result: return jsonify({"error": "AI unavailable"}), 500
    if u:
        chat_history.append({"role":"user","text":msg})
        chat_history.append({"role":"assistant","text":result})
        with get_db() as db:
            db.execute("UPDATE users SET chat_history=? WHERE username=?", (json.dumps(chat_history[-20:]), u))
            db.commit()
    return jsonify({"response": result})

@app.route("/")
def index(): return render_template_string(HTML)

# ── HTML ──────────────────────────────────────────────────────
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>💘 DateSpark AI</title>
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#f43f5e">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="DateSpark">
<style>
:root{--bg:#0d0d0d;--surface:#1a1a2e;--text:#ffffff;--subtext:#9ca3af;--border:#ffffff15;--input:#1f2937;--card-overlay:rgba(0,0,0,0.3)}
.light{--bg:#f0f0f5;--surface:#ffffff;--text:#111827;--subtext:#6b7280;--border:#d1d5db;--input:#e5e7eb;--card-overlay:rgba(0,0,0,0.15)}
.light body{background:#f0f0f5}
.light .surface{background:#ffffff;box-shadow:0 2px 8px rgba(0,0,0,0.08)}
.light input,.light textarea,.light select{background:#e5e7eb;color:#111827;border-color:#d1d5db}
.light nav{background:#ffffff;box-shadow:0 -2px 8px rgba(0,0,0,0.06)}
.light header{background:#ffffff;box-shadow:0 2px 8px rgba(0,0,0,0.06)}
.light .pill{background:#e5e7eb;color:#374151}
.light .pill.active{background:#f43f5e;color:#fff}
.light .swipe-btn{background:#ffffff;border-color:#d1d5db}
.light .memory-card{background:#ffffff;border-color:#e5e7eb}
.light .stat-card{background:#ffffff;border-color:#e5e7eb}
.light .recommend-card{background:#ffffff}
.light .chat-box{background:#f0f0f5}
.light .chat-msg.ai{background:#e5e7eb;color:#111827}
.light .modal-box{background:#ffffff}
.light .rating-btn{background:#e5e7eb;color:#111827}
.light .code-display{background:#f0f0f5;color:#f43f5e}
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent;transition:background-color .3s,color .3s}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-height:100vh;display:flex;flex-direction:column;max-width:480px;margin:0 auto}
header{background:var(--surface);padding:12px 16px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--border);position:sticky;top:0;z-index:50}
header h1{font-size:18px;color:#f43f5e;font-weight:900}
.header-right{display:flex;gap:8px;align-items:center}
.icon-btn{background:none;border:none;font-size:18px;cursor:pointer;padding:4px;border-radius:8px}
nav{background:var(--surface);display:flex;border-top:1px solid var(--border);position:sticky;bottom:0;z-index:100;overflow-x:auto;height:58px}
nav button{flex:1;min-width:44px;padding:12px 2px;background:none;border:none;color:var(--subtext);font-size:20px;cursor:pointer;transition:color .2s;white-space:nowrap}
nav button.active{color:#f43f5e;border-top:2px solid #f43f5e}
.screen{display:none;flex:1;flex-direction:column;padding:14px;gap:12px;overflow-y:auto;padding-bottom:80px}
.screen.active{display:flex}
.card{border-radius:20px;padding:18px;position:relative;overflow:hidden;margin-bottom:10px}
.card-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px}
.card-emoji{font-size:36px;line-height:1}
.card-meta{text-align:right;font-size:11px;color:rgba(255,255,255,0.7)}
.card-cost{background:var(--card-overlay);border-radius:20px;padding:2px 8px;font-weight:700;margin-bottom:3px;display:inline-block;color:#fff}
.card h2{font-size:17px;font-weight:900;margin-bottom:5px;color:#fff}
.card p{font-size:12px;color:rgba(255,255,255,0.82);line-height:1.5}
.card-btns{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}
.card-btns button{padding:6px 10px;border:none;border-radius:10px;background:rgba(255,255,255,0.2);color:#fff;font-size:11px;font-weight:700;cursor:pointer}
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
.pill{flex-shrink:0;padding:7px 12px;border-radius:20px;border:none;background:var(--input);color:var(--text);font-size:11px;font-weight:700;cursor:pointer}
.pill.active{background:#f43f5e;color:#fff;transform:scale(1.05)}
.swipe-area{position:relative;height:230px;margin-bottom:8px}
.swipe-card{position:absolute;inset:0;border-radius:22px;padding:18px;display:flex;flex-direction:column;justify-content:space-between;cursor:grab;user-select:none}
.swipe-card.back1{transform:scale(0.95) translateY(8px);opacity:.7;z-index:1;pointer-events:none}
.swipe-card.back2{transform:scale(0.90) translateY(16px);opacity:.4;z-index:0;pointer-events:none}
.swipe-card.front{z-index:2}
.swipe-btns{display:flex;justify-content:center;gap:16px;align-items:center}
.swipe-btn{width:54px;height:54px;border-radius:50%;border:2px solid var(--border);background:var(--surface);font-size:22px;cursor:pointer;transition:all .2s;display:flex;align-items:center;justify-content:center}
.swipe-btn:hover{transform:scale(1.1)}
.swipe-btn.like{border-color:#10b981}
.swipe-btn.skip{border-color:#ef4444}
.swipe-btn.shuf{width:42px;height:42px;font-size:16px}
.overlay{position:absolute;top:14px;padding:5px 12px;border-radius:10px;font-weight:900;font-size:15px;border:2px solid #fff;opacity:0;pointer-events:none;z-index:10}
.overlay.like{left:14px;background:#10b981;transform:rotate(-15deg)}
.overlay.skip{right:14px;background:#ef4444;transform:rotate(15deg)}
input,textarea,select{width:100%;background:var(--input);border:1px solid var(--border);border-radius:12px;padding:11px 14px;color:var(--text);font-size:13px;outline:none;resize:none;font-family:inherit}
input:focus,textarea:focus{border-color:#f43f5e}
.btn{width:100%;padding:13px;border:none;border-radius:12px;font-size:14px;font-weight:900;cursor:pointer;color:#fff;transition:all .2s}
.btn:hover{opacity:.9;transform:translateY(-1px)}
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
/* Chat */
.chat-box{height:300px;overflow-y:auto;display:flex;flex-direction:column;gap:8px;padding:8px;background:var(--bg);border-radius:12px;margin-bottom:8px}
.chat-msg{max-width:80%;padding:8px 12px;border-radius:14px;font-size:13px;line-height:1.4}
.chat-msg.user{background:#f43f5e;color:#fff;align-self:flex-end;border-bottom-right-radius:4px}
.chat-msg.ai{background:var(--surface);color:var(--text);align-self:flex-start;border-bottom-left-radius:4px}
.chat-input-row{display:flex;gap:8px}
.chat-input-row input{flex:1}
.chat-input-row button{width:44px;flex-shrink:0;border-radius:12px;border:none;background:#f43f5e;color:#fff;font-size:18px;cursor:pointer}
/* Stats */
.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.stat-card{background:var(--surface);border-radius:14px;padding:14px;text-align:center;border:1px solid var(--border)}
.stat-num{font-size:32px;font-weight:900;color:#f43f5e}
.stat-label{font-size:11px;color:var(--subtext);margin-top:4px}
.stat-bar{height:6px;background:var(--border);border-radius:3px;margin-top:6px;overflow:hidden}
.stat-bar-fill{height:100%;background:#f43f5e;border-radius:3px;transition:width 1s}
/* Auth */
.auth-container{display:flex;flex-direction:column;gap:12px;padding:20px 0}
.auth-toggle{text-align:center;color:var(--subtext);font-size:13px;margin-top:8px}
.auth-toggle span{color:#f43f5e;cursor:pointer;font-weight:700}
/* Memory modal */
.modal{position:fixed;inset:0;background:rgba(0,0,0,0.75);z-index:200;display:flex;align-items:center;justify-content:center;padding:16px}
.modal-box{background:var(--surface);border-radius:22px;padding:22px;width:100%;max-width:380px;border:1px solid var(--border)}
.rating-btns{display:flex;gap:4px;margin:8px 0}
.rating-btn{flex:1;padding:7px;background:var(--input);border:2px solid transparent;border-radius:9px;color:var(--text);font-size:10px;cursor:pointer;font-weight:700}
.rating-btn.selected{border-color:#f43f5e;background:#f43f5e22}
.photo-preview{width:100%;height:120px;object-fit:cover;border-radius:10px;margin-top:8px;display:none}
/* Confetti */
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
.user-badge{background:#f43f5e22;color:#f43f5e;border-radius:20px;padding:3px 10px;font-size:11px;font-weight:700}
.lang-select{width:auto;padding:5px 8px;font-size:12px;border-radius:8px}
.share-btns{display:flex;gap:8px;margin-top:8px}
.share-btn{flex:1;padding:10px;border:none;border-radius:10px;font-weight:700;font-size:12px;cursor:pointer;color:#fff}
.share-btn.wa{background:#25d366}
.share-btn.em{background:#0284c7}
.share-btn.cp{background:#6b7280}
.recommend-card{background:var(--surface);border-radius:14px;padding:12px;border:1px solid #f43f5e33;margin-bottom:10px}
.reason-tag{background:#f43f5e22;color:#f43f5e;border-radius:10px;padding:3px 8px;font-size:10px;margin-top:6px;display:inline-block}
</style>
</head>
<body class="">
<header>
  <h1>💘 <span id="app-title">DateSpark AI</span></h1>
  <div class="header-right">
    <select class="lang-select" id="lang-select" onchange="setLang(this.value)">
      <option value="en">🇬🇧 EN</option>
      <option value="es">🇪🇸 ES</option>
      <option value="fr">🇫🇷 FR</option>
      <option value="de">🇩🇪 DE</option>
    </select>
    <button class="icon-btn" onclick="toggleTheme()" id="theme-btn">🌙</button>
    <div id="user-badge-area"></div>
  </div>
</header>

<!-- Auth Screen -->
<div id="screen-auth" class="screen active" style="justify-content:center">
  <div style="text-align:center;margin-bottom:20px">
    <div style="font-size:60px">💘</div>
    <h2 style="font-size:24px;font-weight:900;color:#f43f5e;margin-top:8px">DateSpark AI</h2>
    <p style="color:var(--subtext);font-size:13px;margin-top:4px">Your AI-powered date companion</p>
  </div>
  <div class="auth-container">
    <div>
      <div class="label" id="lbl-username">Username</div>
      <input id="auth-username" placeholder="Enter username" autocomplete="username">
    </div>
    <div>
      <div class="label" id="lbl-password">Password</div>
      <input id="auth-password" type="password" placeholder="Enter password" autocomplete="current-password">
    </div>
    <div id="auth-error" style="color:#ef4444;font-size:12px;display:none"></div>
    <button class="btn btn-pink" id="auth-submit-btn" onclick="submitAuth()">Login</button>
    <button class="btn btn-gray" onclick="continueGuest()">Continue as Guest</button>
    <div class="auth-toggle">
      <span id="auth-toggle-link" onclick="toggleAuthMode()">Don't have an account? Register</span>
    </div>
  </div>
</div>

<!-- Gallery Screen -->
<div id="screen-gallery" class="screen">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
    <div class="label">📸 Date Photo Gallery</div>
    <span id="gallery-count" style="font-size:11px;color:var(--subtext)"></span>
  </div>
  <div class="photo-grid" id="gallery-grid"></div>
</div>

<!-- Couple Album Screen -->
<div id="screen-album" class="screen">
  <div class="surface">
    <div class="label">💑 Couples Photo Album</div>
    <p style="font-size:12px;color:var(--subtext);margin-bottom:10px">Share photos with your partner. Both of you can add & view!</p>
    <input type="file" accept="image/*" id="album-photo-input" onchange="previewAlbumPhoto(this)" style="font-size:12px;padding:6px">
    <img id="album-preview" style="display:none;width:100%;max-height:150px;object-fit:cover;border-radius:10px;margin-top:8px">
    <input id="album-caption" placeholder="Add a caption..." style="margin-top:8px">
    <button class="btn btn-pink" style="margin-top:8px" onclick="uploadAlbumPhoto()">📤 Add to Album</button>
  </div>
  <div id="album-list"></div>
</div>

<!-- Spark Screen -->
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

<!-- Seasonal -->
<div id="screen-seasonal" class="screen">
  <div id="seasonal-header"></div>
  <div id="seasonal-cards"></div>
</div>

<!-- Couples -->
<div id="screen-couples" class="screen">
  <div class="surface">
    <div class="label" id="lbl-your-code">Your Share Code</div>
    <div class="code-display" id="my-code">------</div>
    <p style="font-size:11px;color:var(--subtext)">Share with your partner to sync swipes!</p>
  </div>
  <div class="surface">
    <div class="label" id="lbl-enter-code">Enter Partner's Code</div>
    <input id="partner-code" maxlength="6" placeholder="XXXXXX" style="text-transform:uppercase;letter-spacing:.2em;font-size:18px;font-weight:900;text-align:center">
    <button class="btn btn-pink" style="margin-top:10px" onclick="connectPartner()" id="connect-btn">Connect 💑</button>
    <div id="connect-status" style="font-size:12px;margin-top:6px"></div>
  </div>
  <div class="label" id="lbl-matches">Matches</div>
  <div id="matches-list"></div>
</div>

<!-- AI Screen -->
<div id="screen-ai" class="screen">
  <div class="surface">
    <div class="label">🤖 AI Date Planner</div>
    <textarea id="ai-topic" rows="3" placeholder="e.g. We love hiking & sushi, 1-year anniversary, budget $150..."></textarea>
    <div class="btn-row" style="margin-top:10px">
      <button class="btn btn-pink" id="quick-btn" onclick="aiQuick()">💡 Quick Idea</button>
      <button class="btn btn-purple" id="itin-btn" onclick="aiItinerary()">🗓️ Full Itinerary</button>
    </div>
  </div>
  <div class="surface">
    <div class="label">🎯 Personalized For You</div>
    <button class="btn btn-green" onclick="aiRecommend()">✨ Get Recommendations</button>
    <div id="recommend-result" style="margin-top:10px"></div>
  </div>
  <div class="surface">
    <div class="label">📍 Find Date Spots</div>
    <input id="city-input" placeholder="Enter your city...">
    <button class="btn btn-blue" style="margin-top:10px" onclick="findPlaces()">🗺️ Find Places</button>
  </div>
  <div id="ai-result"></div>
</div>

<!-- Chat Screen -->
<div id="screen-chat" class="screen">
  <div class="surface" style="flex:1;display:flex;flex-direction:column">
    <div class="label">💬 Date Ideas Assistant</div>
    <div class="chat-box" id="chat-box">
      <div class="chat-msg ai">Hi! 👋 I'm your date ideas assistant. Ask me anything — budget ideas, romantic spots, anniversary plans... I'm here to help! 💘</div>
    </div>
    <div class="chat-input-row">
      <input id="chat-input" placeholder="Ask me about date ideas..." onkeydown="if(event.key==='Enter')sendChat()">
      <button onclick="sendChat()">➤</button>
    </div>
  </div>
</div>

<!-- Stats Screen -->
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

<!-- History Screen -->
<div id="screen-history" class="screen">
  <div id="history-list"></div>
</div>

<!-- Saved Screen -->
<div id="screen-saved" class="screen">
  <div id="saved-list"></div>
</div>

<nav id="main-nav" style="display:none">
  <button onclick="showTab('spark',this)">⚡</button>
  <button onclick="showTab('seasonal',this)" id="seasonal-tab-btn">🌺</button>
  <button onclick="showTab('couples',this)">💑</button>
  <button onclick="showTab('ai',this)">🤖</button>
  <button onclick="showTab('chat',this)">💬</button>
  <button onclick="showTab('stats',this)">📊</button>
  <button onclick="showTab('history',this)">📖</button>
  <button onclick="showTab('saved',this)">❤️</button>
  <button onclick="showTab('gallery',this)">🖼️</button>
  <button onclick="showTab('album',this)">💑📸</button>
</nav>

<div class="confetti-container" id="confetti"></div>

<script>
// ── State ──────────────────────────────────────────────────
let IDEAS={}, deck=[], saved=[], history=[], matches=[];
let activeCat='all', couplesMode=false, currentUser=null;
let shareCode=Math.random().toString(36).slice(2,8).toUpperCase();
let dragStartX=null, currentDrag=0, isDragging=false;
let selectedRating=5, currentMemoryIdea=null, currentMemoryPhoto=null;
let lang='en', darkMode=true, authMode='login';

const T = {
  en:{title:"DateSpark AI",spark:"⚡",seasonal:"🌸",couples:"💑",ai:"🤖",chat:"💬",stats:"📊",history:"📖",saved:"❤️",
      login:"Login",register:"Register",logout:"Logout",username:"Username",password:"Password",
      save:"❤️ Save",log:"📖 Log",share:"Share",find_places:"🗺️ Find Places",
      quick_idea:"💡 Quick Idea",full_itinerary:"🗓️ Full Itinerary",send:"➤",
      type_message:"Ask me about date ideas...",your_code:"Your Share Code",
      enter_code:"Enter Partner's Code",connect:"Connect 💑",matches:"Matches",
      no_matches:"No matches yet! Go swipe together.",clear_all:"🗑 Clear All",
      add_to_calendar:"📅 Calendar",whatsapp:"WhatsApp",email:"Email",copy:"Copy",
      guest:"Continue as Guest",no_account:"Don't have an account?",have_account:"Already have an account?"},
  es:{title:"DateSpark IA",spark:"⚡",seasonal:"🌸",couples:"💑",ai:"🤖",chat:"💬",stats:"📊",history:"📖",saved:"❤️",
      login:"Entrar",register:"Registrar",logout:"Salir",username:"Usuario",password:"Contraseña",
      save:"❤️ Guardar",log:"📖 Registrar",share:"Compartir",find_places:"🗺️ Buscar",
      quick_idea:"💡 Idea Rápida",full_itinerary:"🗓️ Itinerario",send:"➤",
      type_message:"Pregúntame sobre citas...",your_code:"Tu Código",
      enter_code:"Código de tu Pareja",connect:"Conectar 💑",matches:"Coincidencias",
      no_matches:"Sin coincidencias todavía.",clear_all:"🗑 Borrar Todo",
      add_to_calendar:"📅 Calendario",whatsapp:"WhatsApp",email:"Email",copy:"Copiar",
      guest:"Continuar como Invitado",no_account:"¿No tienes cuenta?",have_account:"¿Ya tienes cuenta?"},
  fr:{title:"DateSpark IA",spark:"⚡",seasonal:"🌸",couples:"💑",ai:"🤖",chat:"💬",stats:"📊",history:"📖",saved:"❤️",
      login:"Connexion",register:"S'inscrire",logout:"Déconnexion",username:"Utilisateur",password:"Mot de passe",
      save:"❤️ Sauver",log:"📖 Journal",share:"Partager",find_places:"🗺️ Trouver",
      quick_idea:"💡 Idée Rapide",full_itinerary:"🗓️ Itinéraire",send:"➤",
      type_message:"Demandez des idées...",your_code:"Votre Code",
      enter_code:"Code de votre Partenaire",connect:"Connecter 💑",matches:"Correspondances",
      no_matches:"Pas encore de correspondances.",clear_all:"🗑 Tout Effacer",
      add_to_calendar:"📅 Calendrier",whatsapp:"WhatsApp",email:"Email",copy:"Copier",
      guest:"Continuer en Invité",no_account:"Pas de compte?",have_account:"Déjà un compte?"},
  de:{title:"DateSpark KI",spark:"⚡",seasonal:"🌸",couples:"💑",ai:"🤖",chat:"💬",stats:"📊",history:"📖",saved:"❤️",
      login:"Anmelden",register:"Registrieren",logout:"Abmelden",username:"Benutzername",password:"Passwort",
      save:"❤️ Speichern",log:"📖 Erinnerung",share:"Teilen",find_places:"🗺️ Suchen",
      quick_idea:"💡 Schnelle Idee",full_itinerary:"🗓️ Reiseplan",send:"➤",
      type_message:"Fragen Sie nach Date-Ideen...",your_code:"Ihr Code",
      enter_code:"Code Ihres Partners",connect:"Verbinden 💑",matches:"Übereinstimmungen",
      no_matches:"Noch keine Übereinstimmungen.",clear_all:"🗑 Alle löschen",
      add_to_calendar:"📅 Kalender",whatsapp:"WhatsApp",email:"Email",copy:"Kopieren",
      guest:"Als Gast fortfahren",no_account:"Kein Konto?",have_account:"Bereits ein Konto?"},
};

function t(key){ return (T[lang]||T.en)[key]||key; }

// ── Theme ──────────────────────────────────────────────────
function toggleTheme(){
  darkMode=!darkMode;
  document.body.classList.toggle('light',!darkMode);
  document.getElementById('theme-btn').textContent=darkMode?'🌙':'☀️';
}

// ── Language ───────────────────────────────────────────────
function setLang(l){
  lang = l;
  applyTranslations();
  translateCurrentIdeas();
}

async function translateCurrentIdeas(){
  if(lang === 'en'){
    // Reset to original English ideas
    buildDeck(activeCat);
    renderSwipeCards();
    return;
  }
  // Show loading on card area
  const area = document.getElementById('swipe-area');
  area.innerHTML = '<div class="empty"><div style="font-size:28px">🌍</div><p>Translating ideas...</p></div>';
  // Translate current deck (first 6 cards)
  const toTranslate = deck.slice(0, 6);
  try {
    const r = await fetch('/api/translate-ideas', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ideas: toTranslate, lang})
    });
    const translated = await r.json();
    // Replace start of deck with translated versions
    deck.splice(0, translated.length, ...translated);
    renderSwipeCards();
  } catch(e){
    renderSwipeCards();
  }
}
function applyTranslations(){
  // Header
  document.getElementById('app-title').textContent = t('title');

  // Nav buttons
  const navKeys = ['spark','seasonal','couples','ai','chat','stats','history','saved'];
  document.querySelectorAll('nav button').forEach((b,i) => {
    const base = T.en[navKeys[i]]; // original emoji stays
    b.textContent = t(navKeys[i]);
  });

  // Auth screen
  const authBtn = document.getElementById('auth-submit-btn');
  if(authBtn) authBtn.textContent = authMode==='login' ? t('login') : t('register');
  const toggleLink = document.getElementById('auth-toggle-link');
  if(toggleLink) toggleLink.textContent = authMode==='login'
    ? `${t('no_account')} ${t('register')}`
    : `${t('have_account')} ${t('login')}`;
  const lblU = document.getElementById('lbl-username');
  if(lblU) lblU.textContent = t('username');
  const lblP = document.getElementById('lbl-password');
  if(lblP) lblP.textContent = t('password');

  // Couples screen
  const lblCode = document.getElementById('lbl-your-code');
  if(lblCode) lblCode.textContent = t('your_code');
  const lblEnter = document.getElementById('lbl-enter-code');
  if(lblEnter) lblEnter.textContent = t('enter_code');
  const lblMatches = document.getElementById('lbl-matches');
  if(lblMatches) lblMatches.textContent = t('matches');
  const connectBtn = document.getElementById('connect-btn');
  if(connectBtn) connectBtn.textContent = t('connect');

  // AI screen buttons
  const quickBtn = document.getElementById('quick-btn');
  if(quickBtn) quickBtn.textContent = t('quick_idea');
  const itinBtn = document.getElementById('itin-btn');
  if(itinBtn) itinBtn.textContent = t('full_itinerary');

  // Chat placeholder
  const chatInput = document.getElementById('chat-input');
  if(chatInput) chatInput.placeholder = t('type_message');

  // Re-render dynamic screens to update buttons inside cards
  const activeScreen = document.querySelector('.screen.active');
  if(activeScreen){
    const id = activeScreen.id.replace('screen-','');
    if(id==='saved') renderSaved();
    if(id==='history') renderHistory();
    if(id==='couples') renderMatches();
    if(id==='spark') renderSwipeCards();
    if(id==='seasonal') loadSeasonal();
  }
}

// ── Auth ───────────────────────────────────────────────────
function toggleAuthMode(){
  authMode=authMode==='login'?'register':'login';
  const isLogin=authMode==='login';
  document.getElementById('auth-submit-btn').textContent=isLogin?t('login'):t('register');
  document.getElementById('auth-toggle-link').textContent=isLogin?`${t('no_account')} ${t('register')}`:`${t('have_account')} ${t('login')}`;
}

async function submitAuth(){
  const u=document.getElementById('auth-username').value.trim();
  const p=document.getElementById('auth-password').value;
  const err=document.getElementById('auth-error');
  if(!u||!p){err.textContent='Please fill in all fields';err.style.display='block';return;}
  const endpoint=authMode==='login'?'/api/login':'/api/register';
  const r=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
  const data=await r.json();
  if(data.error){err.textContent=data.error;err.style.display='block';return;}
  currentUser=data.username;
  shareCode=data.share_code;
  saved=data.saved||[];
  history=data.history||[];
  enterApp();
}

function continueGuest(){
  currentUser=null;
  enterApp();
}

function enterApp(){
  document.getElementById('screen-auth').classList.remove('active');
  document.getElementById('main-nav').style.display='flex';
  renderUserBadge(currentUser, null);
  document.getElementById('my-code').textContent=shareCode;
  init();
  showTab('spark',document.querySelector('nav button'));
}

function showAuthScreen(){
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  document.getElementById('screen-auth').classList.add('active');
  document.getElementById('main-nav').style.display='none';
}

// ── Init ───────────────────────────────────────────────────
async function init(){
  try {
    const r = await fetch('/api/ideas');
    IDEAS = await r.json();
    buildDeck();
    renderCatPills();
    renderSwipeCards();
    await loadSeasonal();
    renderMatches();
    updateNavBadges();
  } catch(e) {
    console.error('Init error:', e);
  }
}

function buildDeck(cat='all'){
  activeCat = cat;
  if(!IDEAS || !Object.keys(IDEAS).length) return;
  let all = Object.entries(IDEAS).flatMap(([c,arr]) => arr.map(i => ({...i, cat:c})));
  deck = cat==='all' ? all : all.filter(i => i.cat === cat);
  deck.sort(() => Math.random() - 0.5);
}

// ── Cat Pills ──────────────────────────────────────────────
function renderCatPills(){
  const cats=[['all','🌀 All'],['home','🏠 Home'],['city','🌆 City'],
              ['outdoor','🌿 Out'],['budget','💸 Budget'],
              ['luxury','💎 Luxury'],['travel','🌍 Travel'],['surprise','✨ Surprise']];
  document.getElementById('cat-pills').innerHTML = cats.map(([id,lbl])=>
    `<button class="pill ${id===activeCat?'active':''}" onclick="setCat('${id}',this)">${lbl}</button>`
  ).join('');
}

function setCat(cat, btn){
  activeCat = cat;
  seenTitles = [];
  isGenerating = false;
  document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  // Rebuild deck from local IDEAS first
  if(!IDEAS || !Object.keys(IDEAS).length){
    console.error('IDEAS not loaded!');
    return;
  }
  let all = Object.entries(IDEAS).flatMap(([c,arr]) => arr.map(i => ({...i, cat:c})));
  deck = cat==='all' ? all : all.filter(i => i.cat === cat);
  deck.sort(() => Math.random() - 0.5);
  console.log(`Category: ${cat}, Deck size: ${deck.length}`);
  renderSwipeCards();
}

function reshuffleDeck(){
  seenTitles = [];
  isGenerating = false;
  buildDeck(activeCat);
  renderSwipeCards();
}

// ── Swipe Cards ────────────────────────────────────────────
let isGenerating = false;
let seenTitles = [];

function renderSwipeCards(){
  const area=document.getElementById('swipe-area');
  area.innerHTML='';
  if(!deck.length){
    if(!isGenerating) generateMoreIdeas();
    area.innerHTML=`<div class="empty">
      <div style="font-size:36px;animation:pulse 1s infinite">✨</div>
      <p>Generating fresh ideas<br>just for you...</p>
    </div>`;
    return;
  }
  [2,1,0].forEach(i=>{
    if(!deck[i])return;
    area.appendChild(makeSwipeCard(deck[i],i));
  });
  // Pre-generate when only 3 cards left
  if(deck.length <= 3 && !isGenerating) generateMoreIdeas(false);
  const front=area.querySelector('.front');
  if(front)attachDrag(front);
}

async function generateMoreIdeas(rerender=true){
  if(isGenerating) return;
  isGenerating = true;
  // Use active category, not random
  const catToGenerate = activeCat === 'all'
    ? ['home','city','outdoor','budget','luxury','travel','surprise'][Math.floor(Math.random()*7)]
    : activeCat;
  try {
    const r = await fetch('/api/ai/generate-ideas', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        cat: catToGenerate,
        exclude: seenTitles.slice(-20)
      })
    });
    const data = await r.json();
    if(Array.isArray(data)){
      const newIdeas = data.filter(i => !seenTitles.includes(i.title));
      newIdeas.forEach(i => seenTitles.push(i.title));
      deck.push(...newIdeas);
      if(rerender) renderSwipeCards();
    }
  } catch(e){
    console.log('Generate error:', e);
  }
  isGenerating = false;
}

function makeSwipeCard(idea,idx){
  const d=document.createElement('div');
  d.className=`swipe-card cat-${idea.cat||'surprise'} ${idx===0?'front':idx===1?'back1':'back2'}`;
  d.innerHTML=`
    <div class="overlay like">LOVE IT 💚</div>
    <div class="overlay skip">SKIP ❌</div>
    <div>
      <div class="card-top">
        <span style="font-size:36px">${idea.emoji}</span>
        <div class="card-meta"><div class="card-cost">${idea.cost}</div><div>${idea.duration}</div></div>
      </div>
      <h2 style="color:#fff">${idea.title}</h2>
      <p style="margin-top:5px">${idea.desc}</p>
    </div>
    <div class="card-btns">
      <button onclick='saveIdea(${JSON.stringify(idea).replace(/"/g,"&quot;")})'>${t('save')}</button>
      <button onclick='shareIdea(${JSON.stringify(idea).replace(/"/g,"&quot;")})'>🔗 ${t('share')}</button>
    </div>`;
  return d;
}

function attachDrag(el){
  el.addEventListener('mousedown',e=>{dragStartX=e.clientX;isDragging=true;});
  el.addEventListener('touchstart',e=>{dragStartX=e.touches[0].clientX;isDragging=true;},{passive:true});
  document.addEventListener('mousemove',onDrag);
  document.addEventListener('touchmove',onDragTouch,{passive:true});
  document.addEventListener('mouseup',onDragEnd);
  document.addEventListener('touchend',onDragEnd);
}

function onDrag(e){if(!isDragging||dragStartX===null)return;currentDrag=e.clientX-dragStartX;updateDragVisual();}
function onDragTouch(e){if(!isDragging||dragStartX===null)return;currentDrag=e.touches[0].clientX-dragStartX;updateDragVisual();}

function updateDragVisual(){
  const front=document.querySelector('.swipe-card.front');
  if(!front)return;
  front.style.transform=`translateX(${currentDrag}px) rotate(${currentDrag/18}deg)`;
  front.querySelectorAll('.overlay').forEach(o=>o.style.opacity=0);
  if(currentDrag>30)front.querySelector('.overlay.like').style.opacity=Math.min(currentDrag/80,1);
  if(currentDrag<-30)front.querySelector('.overlay.skip').style.opacity=Math.min(-currentDrag/80,1);
}

function onDragEnd(){
  if(!isDragging)return; isDragging=false;
  if(Math.abs(currentDrag)>80)swipe(currentDrag>0?'right':'left');
  else{const f=document.querySelector('.swipe-card.front');if(f){f.style.transform='';f.querySelectorAll('.overlay').forEach(o=>o.style.opacity=0);}}
  dragStartX=null;currentDrag=0;
  document.removeEventListener('mousemove',onDrag);
  document.removeEventListener('touchmove',onDragTouch);
  document.removeEventListener('mouseup',onDragEnd);
  document.removeEventListener('touchend',onDragEnd);
}

function swipe(dir){
  if(!deck.length)return;
  const idea=deck[0];
  const front=document.querySelector('.swipe-card.front');
  if(front){front.classList.add(dir==='right'?'flying-out-right':'flying-out-left');setTimeout(()=>{deck.shift();renderSwipeCards();},300);}
  else{deck.shift();renderSwipeCards();}
  if(dir==='right'){
    saveIdea(idea);
    if(couplesMode&&Math.random()>0.4&&!matches.find(m=>m.title===idea.title)){
      matches.push(idea);showConfetti();showMatchPopup(idea);renderMatches();
    }
  }
  updateNavBadges();
}

// ── Save ───────────────────────────────────────────────────
async function saveIdea(idea){
  if(saved.find(s=>s.title===idea.title)){showToast('Already saved! ❤️');return;}
  saved.push(idea);
  if(currentUser){await fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({idea})});}
  updateNavBadges();showToast('Saved! ❤️');
}

function updateNavBadges(){
  const btns=document.querySelectorAll('nav button');
  if(btns[7])btns[7].textContent=saved.length?`❤️${saved.length}`:'❤️';
  if(btns[6])btns[6].textContent=history.length?`📖${history.length}`:'📖';
}

// ── Share ──────────────────────────────────────────────────
function shareIdea(idea){
  const text=`💘 Date Idea: ${idea.emoji} ${idea.title}\n${idea.desc}\n⏱ ${idea.duration} | 💰 ${idea.cost}\n\nvia DateSpark AI`;
  const modal=document.createElement('div');
  modal.className='modal';
  modal.innerHTML=`<div class="modal-box">
    <h3 style="color:#f43f5e;margin-bottom:12px">🔗 Share This Date Idea</h3>
    <div class="card cat-${idea.cat||'surprise'}" style="margin-bottom:12px">
      <h2>${idea.emoji} ${idea.title}</h2><p>${idea.desc}</p>
    </div>
    <div class="share-btns">
      <button class="share-btn wa" onclick="window.open('https://wa.me/?text='+encodeURIComponent(\`${text}\`),'_blank')">📱 WhatsApp</button>
      <button class="share-btn em" onclick="window.open('mailto:?subject=Date Idea&body='+encodeURIComponent(\`${text}\`),'_blank')">📧 Email</button>
      <button class="share-btn cp" onclick="navigator.clipboard?.writeText(\`${text}\`);showToast('Copied!')">📋 Copy</button>
    </div>
    <button class="btn btn-gray" style="margin-top:10px" onclick="this.closest('.modal').remove()">Close</button>
  </div>`;
  document.body.appendChild(modal);
}

function addToCalendar(idea){
  const title=encodeURIComponent(`💘 ${idea.title}`);
  const details=encodeURIComponent(idea.desc);
  const date=new Date();
  date.setDate(date.getDate()+7);
  const dateStr=date.toISOString().replace(/-|:|\.\d\d\d/g,'');
  const url=`https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&details=${details}&dates=${dateStr}/${dateStr}`;
  window.open(url,'_blank');
}

// ── Seasonal ───────────────────────────────────────────────
async function loadSeasonal(){
  const r=await fetch('/api/seasonal');
  const {season,ideas}=await r.json();
  const icons={winter:'❄️',spring:'🌺',summer:'☀️',autumn:'🍂'};
  document.getElementById('seasonal-tab-btn').textContent=icons[season];
  document.getElementById('seasonal-header').innerHTML=`
    <div style="text-align:center;margin-bottom:12px">
      <div style="font-size:44px">${icons[season]}</div>
      <h2 style="font-size:19px;font-weight:900;color:#f43f5e;margin:6px 0">${season.charAt(0).toUpperCase()+season.slice(1)} Dates</h2>
    </div>`;
  document.getElementById('seasonal-cards').innerHTML=ideas.map(i=>
    `<div class="card cat-${i.cat}" style="margin-bottom:12px">
       <div class="card-top">
         <span style="font-size:36px">${i.emoji}</span>
         <div class="card-meta">
           <div class="card-cost">${i.cost}</div>
           <div style="color:rgba(255,255,255,0.7);font-size:11px">${i.duration}</div>
         </div>
       </div>
       <h2 style="color:#fff!important;font-size:17px;font-weight:900;margin-bottom:5px">${i.title}</h2>
       <p style="color:rgba(255,255,255,0.85)!important;font-size:12px;line-height:1.5">${i.desc}</p>
       <div style="display:flex;gap:6px;margin-top:10px;flex-wrap:wrap">
         <button onclick='saveIdea(${JSON.stringify(i)})' style="padding:6px 10px;border:none;border-radius:10px;background:rgba(255,255,255,0.25);color:#fff;font-size:11px;font-weight:700;cursor:pointer">${t('save')}</button>
         <button onclick='shareIdea(${JSON.stringify(i)})' style="padding:6px 10px;border:none;border-radius:10px;background:rgba(255,255,255,0.25);color:#fff;font-size:11px;font-weight:700;cursor:pointer">🔗 ${t('share')}</button>
         <button onclick='addToCalendar(${JSON.stringify(i)})' style="padding:6px 10px;border:none;border-radius:10px;background:rgba(255,255,255,0.25);color:#fff;font-size:11px;font-weight:700;cursor:pointer">${t('add_to_calendar')}</button>
       </div>
     </div>`
  ).join('');
}

// ── Couples ────────────────────────────────────────────────
function connectPartner(){
  const code=document.getElementById('partner-code').value.trim().toUpperCase();
  const status=document.getElementById('connect-status');
  if(code.length===6){
    couplesMode=true;
    status.style.color='#10b981';
    status.textContent='✅ Connected! Swipe on ⚡ Spark to find matches.';
  }else{status.style.color='#ef4444';status.textContent='❌ Code must be 6 characters.';}
}

function renderMatches(){
  const el=document.getElementById('matches-list');
  if(!matches.length){el.innerHTML=`<div class="empty" style="padding:20px"><div>💭</div><p>${t('no_matches')}</p></div>`;return;}
  el.innerHTML=matches.map(m=>`
    <div class="card cat-${m.cat||'surprise'}">
      <div class="card-top"><span style="font-size:32px">${m.emoji}</span>
        <div class="card-meta"><div class="card-cost">${m.cost}</div><div>${m.duration}</div></div>
      </div>
      <h2>${m.title}</h2><p>${m.desc}</p>
      <div class="card-btns">
        <button onclick='addToCalendar(${JSON.stringify(m)})'>${t('add_to_calendar')}</button>
        <button onclick='shareIdea(${JSON.stringify(m)})'>🔗 ${t('share')}</button>
      </div>
    </div>`).join('');
}

function showMatchPopup(idea){
  const popup=document.createElement('div');
  popup.className='modal';
  popup.innerHTML=`<div class="modal-box" style="text-align:center">
    <div style="font-size:48px">🎉</div>
    <h2 style="color:#f43f5e;font-size:22px;margin:10px 0">It's a Match!</h2>
    <p>You both love:</p>
    <p style="font-size:18px;font-weight:900;margin:8px 0">${idea.emoji} ${idea.title}</p>
    <button class="btn btn-pink" style="margin-top:12px" onclick="this.closest('.modal').remove()">Let's do it! 💑</button>
  </div>`;
  document.body.appendChild(popup);
}

// ── AI Features ────────────────────────────────────────────
async function aiQuick(){
  const topic=document.getElementById('ai-topic').value.trim();
  if(!topic)return;
  document.getElementById('ai-result').innerHTML='<div class="empty" style="padding:20px"><div style="animation:spin 1s linear infinite;display:inline-block">✨</div><p>Generating idea...</p></div>';
  const r=await fetch('/api/ai/quick',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic})});
  const data=await r.json();
  if(data.error){document.getElementById('ai-result').innerHTML='<div class="empty"><p>⚠️ AI unavailable. Check your Gemini API key.</p></div>';return;}
  const idea={...data,cat:'surprise',emoji:data.emoji||'✨'};
  document.getElementById('ai-result').innerHTML=`
    <div class="card cat-ai">
      <div class="card-top"><span style="font-size:36px">${data.emoji||'✨'}</span>
        <div class="card-meta"><div class="card-cost">${data.cost||''}</div><div>${data.duration||''}</div></div>
      </div>
      <h2>${data.title}</h2><p style="margin-top:5px">${data.desc}</p>
      ${data.steps?`<div style="margin-top:10px">${data.steps.map(s=>`<p style="font-size:12px;margin:3px 0">• ${s}</p>`).join('')}</div>`:''}
      ${data.tip?`<div style="margin-top:8px;background:rgba(0,0,0,0.2);border-radius:8px;padding:8px"><p style="font-size:11px;color:rgba(255,255,255,0.7)">💡 ${data.tip}</p></div>`:''}
      <div class="card-btns">
        <button onclick='saveIdea(${JSON.stringify(idea).replace(/"/g,"&quot;")})'>${t('save')}</button>
        <button onclick='shareIdea(${JSON.stringify(idea).replace(/"/g,"&quot;")})'>🔗 ${t('share')}</button>
        <button onclick='addToCalendar(${JSON.stringify(idea).replace(/"/g,"&quot;")})'>${t('add_to_calendar')}</button>
      </div>
    </div>`;
}

async function aiItinerary(){
  const topic=document.getElementById('ai-topic').value.trim();
  if(!topic)return;
  document.getElementById('ai-result').innerHTML='<div class="empty" style="padding:20px"><div>🗓️</div><p>Building your itinerary...</p></div>';
  const r=await fetch('/api/ai/itinerary',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic})});
  const data=await r.json();
  if(data.error){document.getElementById('ai-result').innerHTML='<div class="empty"><p>⚠️ AI unavailable.</p></div>';return;}
  document.getElementById('ai-result').innerHTML=`
    <div class="surface">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <span style="font-size:32px">${data.emoji||'🗓️'}</span>
        <div style="text-align:right"><span style="background:#7c3aed;color:#fff;border-radius:12px;padding:3px 8px;font-size:11px;font-weight:700">${data.totalCost||''} • ${data.totalDuration||''}</span></div>
      </div>
      <h2 style="font-size:17px;font-weight:900;color:#f43f5e;margin-bottom:5px">${data.title}</h2>
      <p style="font-size:12px;color:var(--subtext);margin-bottom:12px">${data.overview}</p>
      ${(data.timeline||[]).map(t=>`
        <div style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid var(--border)">
          <div style="color:#f43f5e;font-size:11px;font-weight:700;min-width:48px">${t.time}</div>
          <div><div style="font-size:13px;font-weight:700">${t.activity}</div>${t.tip?`<div style="font-size:11px;color:var(--subtext)">💡 ${t.tip}</div>`:''}</div>
        </div>`).join('')}
    </div>`;
}

async function aiRecommend(){
  document.getElementById('recommend-result').innerHTML='<p style="color:var(--subtext);font-size:12px">✨ Finding perfect ideas for you...</p>';
  const r=await fetch('/api/ai/recommend',{method:'POST',headers:{'Content-Type':'application/json'}});
  const data=await r.json();
  if(data.error||!Array.isArray(data)){document.getElementById('recommend-result').innerHTML='<p style="color:var(--subtext);font-size:12px">Log some dates first for personalized ideas!</p>';return;}
  document.getElementById('recommend-result').innerHTML=data.map(i=>`
    <div class="recommend-card">
      <div style="display:flex;gap:10px;align-items:flex-start">
        <span style="font-size:28px">${i.emoji||'✨'}</span>
        <div style="flex:1">
          <div style="font-weight:900;font-size:14px">${i.title}</div>
          <div style="font-size:12px;color:var(--subtext)">${i.desc}</div>
          <span class="reason-tag">💡 ${i.reason||'Recommended for you'}</span>
        </div>
        <button onclick='saveIdea(${JSON.stringify(i).replace(/"/g,"&quot;")})' style="background:none;border:none;font-size:18px;cursor:pointer">❤️</button>
      </div>
    </div>`).join('');
}

async function findPlaces(){
  const city=document.getElementById('city-input').value.trim();
  if(!city)return;
  document.getElementById('ai-result').innerHTML=`<div class="empty" style="padding:20px"><div>🗺️</div><p>Finding places in ${city}...</p></div>`;
  const r=await fetch('/api/ai/places',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({city})});
  const data=await r.json();
  if(data.error){document.getElementById('ai-result').innerHTML='<div class="empty"><p>⚠️ AI unavailable.</p></div>';return;}
  document.getElementById('ai-result').innerHTML=`<div class="label">📍 Date Spots in ${city}</div>`+
    data.map(p=>`
      <div class="surface" style="display:flex;gap:10px;align-items:flex-start">
        <span style="font-size:26px;flex-shrink:0">${p.emoji}</span>
        <div style="flex:1">
          <div style="display:flex;justify-content:space-between"><b style="font-size:13px">${p.name}</b><span style="color:var(--subtext);font-size:11px">${p.priceRange}</span></div>
          <div style="font-size:10px;color:#0284c7">${p.type}</div>
          <div style="font-size:12px;color:var(--subtext)">${p.desc}</div>
        </div>
        <button onclick='saveIdea({title:"${p.name}",desc:"${p.desc}",emoji:"${p.emoji}",duration:"TBD",cost:"${p.priceRange}",cat:"city"})' style="background:none;border:none;font-size:18px;cursor:pointer">❤️</button>
      </div>`).join('');
}

// ── Chat ───────────────────────────────────────────────────
async function sendChat(){
  const input=document.getElementById('chat-input');
  const msg=input.value.trim();
  if(!msg)return;
  const box=document.getElementById('chat-box');
  box.innerHTML+=`<div class="chat-msg user">${msg}</div>`;
  input.value='';
  box.innerHTML+=`<div class="chat-msg ai" id="typing">✨ thinking...</div>`;
  box.scrollTop=box.scrollHeight;
  const r=await fetch('/api/ai/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg,lang})});
  const data=await r.json();
  document.getElementById('typing')?.remove();
  box.innerHTML+=`<div class="chat-msg ai">${data.response||'Sorry, I could not respond right now.'}</div>`;
  box.scrollTop=box.scrollHeight;
}

// ── Stats ──────────────────────────────────────────────────
function renderStats(){
  const total=history.length;
  const avgRating=total?Math.round(history.reduce((a,h)=>a+(h.rating||5),0)/total*10)/10:0;
  const cats=history.map(h=>h.cat||'surprise');
  const catCounts={};
  cats.forEach(c=>catCounts[c]=(catCounts[c]||0)+1);
  const favCat=Object.entries(catCounts).sort((a,b)=>b[1]-a[1])[0];
  const totalSaved=saved.length;
  document.getElementById('stat-grid').innerHTML=`
    <div class="stat-card"><div class="stat-num">${total}</div><div class="stat-label">Dates Logged</div></div>
    <div class="stat-card"><div class="stat-num">${avgRating||'—'}</div><div class="stat-label">Avg Rating ⭐</div></div>
    <div class="stat-card"><div class="stat-num">${totalSaved}</div><div class="stat-label">Ideas Saved</div></div>
    <div class="stat-card"><div class="stat-num">${favCat?favCat[0]:'—'}</div><div class="stat-label">Fav Category</div></div>`;
  document.getElementById('cat-stats').innerHTML=Object.entries(catCounts).sort((a,b)=>b[1]-a[1]).map(([cat,count])=>`
    <div style="margin-bottom:8px">
      <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px">
        <span>${cat}</span><span>${count}</span>
      </div>
      <div class="stat-bar"><div class="stat-bar-fill" style="width:${Math.round(count/total*100)}%"></div></div>
    </div>`).join('')||'<p style="color:var(--subtext);font-size:12px">Log some dates to see stats!</p>';
  document.getElementById('rating-stats').innerHTML=history.slice(-5).reverse().map(h=>`
    <div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border)">
      <span style="font-size:13px">${h.emoji||'📅'} ${h.title}</span>
      <span style="color:#f59e0b">${'⭐'.repeat(h.rating||5)}</span>
    </div>`).join('')||'<p style="color:var(--subtext);font-size:12px">No dates logged yet!</p>';
}

// ── History ────────────────────────────────────────────────
function renderHistory(){
  const el=document.getElementById('history-list');
  if(!history.length){el.innerHTML='<div class="empty"><div>📖</div><p>No memories yet!<br>Log a date from ❤️ Saved.</p></div>';return;}
  el.innerHTML=[...history].reverse().map((h,i)=>`
    <div class="memory-card">
      <div style="display:flex;gap:10px;align-items:flex-start">
        <span style="font-size:28px">${h.emoji||'📅'}</span>
        <div style="flex:1">
          <div style="font-weight:900;font-size:14px">${h.title}</div>
          <div style="font-size:11px;color:var(--subtext)">${h.date}</div>
          <div style="color:#f59e0b;font-size:14px">${'⭐'.repeat(h.rating||5)}</div>
          ${h.note?`<div style="font-size:12px;color:var(--subtext);font-style:italic;margin-top:3px">"${h.note}"</div>`:''}
        </div>
        <button onclick="removeHistory(${history.length-1-i})" style="background:none;border:none;color:var(--subtext);cursor:pointer;font-size:14px">✕</button>
      </div>
      ${h.photo?`<img src="${h.photo}" class="memory-photo" alt="Date photo">`:''}
    </div>`).join('');
}

function removeHistory(idx){ history.splice(idx,1); renderHistory(); updateNavBadges(); }

// ── Saved ──────────────────────────────────────────────────
function renderSaved(){
  const el=document.getElementById('saved-list');
  if(!saved.length){el.innerHTML='<div class="empty"><div>💔</div><p>No saved ideas yet!<br>Swipe 💚 to save.</p></div>';return;}
  el.innerHTML=saved.map((s,i)=>`
    <div class="card cat-${s.cat||'surprise'}">
      <div class="card-top"><span style="font-size:32px">${s.emoji}</span>
        <div class="card-meta"><div class="card-cost">${s.cost}</div><div>${s.duration}</div></div>
      </div>
      <h2>${s.title}</h2><p>${s.desc}</p>
      <div class="card-btns">
        <button onclick="openLogModal(${i})">📖 ${t('log')}</button>
        <button onclick='shareIdea(${JSON.stringify(s).replace(/"/g,"&quot;")})'>🔗 ${t('share')}</button>
        <button onclick='addToCalendar(${JSON.stringify(s).replace(/"/g,"&quot;")})'>${t('add_to_calendar')}</button>
        <button onclick="saved.splice(${i},1);renderSaved();updateNavBadges()">🗑</button>
      </div>
    </div>`).join('')+
    `<button class="btn btn-gray" onclick="saved=[];renderSaved();updateNavBadges()">${t('clear_all')}</button>`;
}

// ── Log Modal ──────────────────────────────────────────────
function openLogModal(idx){
  selectedRating=5; currentMemoryIdea=saved[idx]; currentMemoryPhoto=null;
  const modal=document.createElement('div');
  modal.className='modal';
  modal.innerHTML=`<div class="modal-box">
    <h3 style="color:#f43f5e;font-size:16px;margin-bottom:4px">📖 Log This Date</h3>
    <p style="color:var(--subtext);font-size:12px;margin-bottom:12px">${currentMemoryIdea.title}</p>
    <div class="label">Rating</div>
    <div class="rating-btns">
      ${[1,2,3,4,5].map(n=>`<button class="rating-btn ${n===5?'selected':''}" onclick="selectRating(${n},this)">${'⭐'.repeat(n)}</button>`).join('')}
    </div>
    <div class="label" style="margin-top:10px">Memory Note</div>
    <textarea id="log-note" rows="3" placeholder="How did it go? Any special memories..."></textarea>
    <div class="label" style="margin-top:10px">📸 Add Photo</div>
    <input type="file" accept="image/*" onchange="handlePhoto(this)" style="font-size:12px;padding:6px">
    <img id="photo-preview" class="photo-preview">
    <div class="btn-row" style="margin-top:12px">
      <button class="btn btn-gray" onclick="this.closest('.modal').remove()">Cancel</button>
      <button class="btn btn-pink" onclick="saveLog(this.closest('.modal'))">Save Memory</button>
    </div>
  </div>`;
  document.body.appendChild(modal);
}

function selectRating(n,btn){
  selectedRating=n;
  document.querySelectorAll('.rating-btn').forEach(b=>b.classList.remove('selected'));
  btn.classList.add('selected');
}

function handlePhoto(input){
  const file=input.files[0];
  if(!file)return;
  const reader=new FileReader();
  reader.onload=e=>{
    currentMemoryPhoto=e.target.result;
    const preview=document.getElementById('photo-preview');
    preview.src=currentMemoryPhoto; preview.style.display='block';
  };
  reader.readAsDataURL(file);
}

async function saveLog(modal){
  const note=document.getElementById('log-note').value;
  const mem={...currentMemoryIdea,note,rating:selectedRating,
             date:new Date().toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}),
             photo:currentMemoryPhoto||null};
  history.push(mem);
  if(currentUser){await fetch('/api/history',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(mem)});}
  modal.remove(); updateNavBadges(); showToast('Memory saved! 📖');
}

// ── Confetti ───────────────────────────────────────────────
function showConfetti(){
  const container=document.getElementById('confetti');
  const colors=['#f43f5e','#a855f7','#3b82f6','#10b981','#f59e0b'];
  for(let i=0;i<50;i++){
    const p=document.createElement('div');
    p.className='confetti-piece';
    p.style.cssText=`left:${Math.random()*100}%;top:-10px;background:${colors[i%5]};
      width:${Math.random()*8+6}px;height:${Math.random()*8+6}px;
      animation-delay:${Math.random()*0.5}s;animation-duration:${Math.random()*1+2}s`;
    container.appendChild(p);
    setTimeout(()=>p.remove(),3000);
  }
}

function showToast(msg){
  const t=document.createElement('div');
  t.className='toast'; t.textContent=msg;
  document.body.appendChild(t);
  setTimeout(()=>{t.style.opacity='0';t.style.transition='opacity .3s';setTimeout(()=>t.remove(),300);},1800);
}

// ── Tab Navigation ─────────────────────────────────────────
function showTab(name, btn){
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  const screen = document.getElementById('screen-'+name);
  if(screen) screen.classList.add('active');
  if(btn) btn.classList.add('active');
  // Reload content for each tab
  if(name==='saved') renderSaved();
  if(name==='history') renderHistory();
  if(name==='couples') renderMatches();
  if(name==='stats') renderStats();
  if(name==='gallery') renderGallery();
  if(name==='album') loadAlbum();
  if(name==='seasonal') loadSeasonal();
  if(name==='spark'){ renderCatPills(); renderSwipeCards(); }
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    print("\n💘 DateSpark AI — Ultimate Edition")
    print("👉 Open your browser at: http://localhost:5000\n")
    app.run(debug=True, port=5000)