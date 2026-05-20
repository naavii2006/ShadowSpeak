from flask import Flask, render_template, request, session, redirect, send_from_directory, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import random
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'secretkey123')
app.permanent_session_lifetime = timedelta(days=30)

# ============= THEME-BASED WORD LISTS =============

THEMES = {
    "nature": {
        "name": "🌿 Nature",
        "icon": "🌿",
        "adjectives": [
            "Wild", "Gentle", "Ancient", "Misty", "Crimson", "Emerald", "Golden", "Silver",
            "Rustic", "Peaceful", "Calm", "Stormy", "Sunny", "Rainy", "Frosty", "Mossy",
            "Flowering", "Blooming", "Verdant", "Lush", "Tranquil", "Serene", "Majestic",
            "Towering", "Deep", "Wide", "Flowing", "Crystal", "Pure", "Fresh", "Clean"
        ],
        "nouns": [
            "Wolf", "Fox", "Hawk", "Owl", "Eagle", "Bear", "Deer", "Rabbit", "Squirrel",
            "Forest", "Mountain", "River", "Lake", "Ocean", "Valley", "Meadow", "Garden",
            "Flower", "Tree", "Leaf", "Rock", "Stone", "Crystal", "Gem", "Pearl",
            "Sunrise", "Sunset", "Dawn", "Dusk", "Rainbow", "Waterfall", "Cascade"
        ]
    },
    "space": {
        "name": "🚀 Space",
        "icon": "🚀",
        "adjectives": [
            "Stellar", "Cosmic", "Galactic", "Nebular", "Lunar", "Solar", "Asteroid", "Comet",
            "Distant", "Ancient", "Bright", "Dark", "Cold", "Vast", "Infinite", "Eternal",
            "Mysterious", "Unknown", "Deep", "Void", "Empty", "Radiant", "Glowing", "Shining",
            "Twinkling", "Orbiting", "Floating", "Drifting", "Frozen", "Icy", "Gaseous"
        ],
        "nouns": [
            "Star", "Moon", "Planet", "Galaxy", "Nebula", "Comet", "Asteroid", "Meteor",
            "Orbit", "Constellation", "Supernova", "Blackhole", "Quasar", "Pulsar", "Satellite",
            "Rocket", "Spaceship", "Astronaut", "Alien", "UFO", "Telescope", "Observatory",
            "Mars", "Venus", "Jupiter", "Saturn", "Pluto", "Andromeda", "MilkyWay"
        ]
    },
    "mythical": {
        "name": "🐉 Mythical",
        "icon": "🐉",
        "adjectives": [
            "Mystic", "Magic", "Enchanted", "Legendary", "Epic", "Heroic", "Divine", "Holy",
            "Ancient", "Elder", "Forgotten", "Lost", "Hidden", "Secret", "Sacred", "Blessed",
            "Cursed", "Hexed", "Charmed", "Spellbound", "Fabled", "Mythical", "Immortal",
            "Eternal", "Timeless", "Powerful", "Mighty", "Grand", "Noble", "Royal"
        ],
        "nouns": [
            "Dragon", "Phoenix", "Griffin", "Pegasus", "Unicorn", "Centaur", "Minotaur", "Hydra",
            "Cerberus", "Chimera", "Sphinx", "Manticore", "Kraken", "Leviathan", "Behemoth",
            "Fairy", "Elf", "Dwarf", "Giant", "Troll", "Ogre", "Goblin", "Wizard", "Witch",
            "Sorcerer", "Enchanter", "Necromancer", "Druid", "Shaman", "Oracle", "Prophet"
        ]
    },
    "cyberpunk": {
        "name": "💿 Cyberpunk",
        "icon": "💿",
        "adjectives": [
            "Neon", "Cyber", "Digital", "Virtual", "Synthetic", "Artificial", "Robotic", "Mechanical",
            "Electric", "Plasma", "Laser", "Glitch", "Quantum", "Atomic", "Nuclear", "Bio",
            "Hacked", "Coded", "Encrypted", "Decrypted", "Futuristic", "HighTech", "Advanced",
            "Smart", "Intelligent", "Automated", "Wireless", "Connected", "Networked"
        ],
        "nouns": [
            "Hacker", "Cyborg", "Android", "Robot", "Drone", "Chip", "Circuit", "Motherboard",
            "Code", "Byte", "Bit", "Pixel", "Data", "Server", "Network", "Firewall",
            "Virus", "Malware", "Trojan", "Ghost", "Shadow", "Phantom", "Reaper", "Raven",
            "Neon", "Laser", "Plasma", "Volt", "Watt", "Pixel", "Glitch", "Crash"
        ]
    },
    "dark": {
        "name": "🌙 Dark",
        "icon": "🌙",
        "adjectives": [
            "Shadow", "Dark", "Night", "Dusk", "Midnight", "Eclipse", "Void", "Abyss",
            "Black", "Obsidian", "Onyx", "Jet", "Raven", "Crow", "Gloomy", "Somber",
            "Mysterious", "Secret", "Hidden", "Unknown", "Silent", "Quiet", "Still", "Cold",
            "Icy", "Frozen", "Hollow", "Empty", "Deep", "Bottomless", "Endless", "Infinite"
        ],
        "nouns": [
            "Shadow", "Ghost", "Specter", "Wraith", "Phantom", "Spirit", "Demon", "Devil",
            "Nightmare", "Horror", "Terror", "Dread", "Fear", "Panic", "Anxiety", "Stress",
            "Raven", "Crow", "Bat", "Spider", "Snake", "Wolf", "Panther", "Leopard",
            "Moon", "Star", "Galaxy", "Nebula", "Void", "Abyss", "Pit", "Cave"
        ]
    },
    "cute": {
        "name": "🌸 Cute",
        "icon": "🌸",
        "adjectives": [
            "Fluffy", "Cute", "Adorable", "Sweet", "Soft", "Warm", "Cozy", "Snuggly",
            "Lovely", "Charming", "Delightful", "Precious", "Darling", "Dear", "Kind", "Gentle",
            "Happy", "Joyful", "Cheerful", "Merry", "Playful", "Bouncy", "Sparkly", "Shiny",
            "Tiny", "Small", "Little", "Mini", "Petite", "Compact", "Cuddly", "Huggable"
        ],
        "nouns": [
            "Puppy", "Kitten", "Bunny", "Hamster", "Mouse", "Bird", "Butterfly", "Ladybug",
            "Bee", "Bear", "Panda", "Koala", "Sloth", "Llama", "Alpaca", "Sheep",
            "Cotton", "Cloud", "Candy", "Cookie", "Cupcake", "Muffin", "Donut", "Sprinkle",
            "Rainbow", "Unicorn", "Sparkle", "Glitter", "Shine", "Star", "Heart", "Rose"
        ]
    },
    "warrior": {
        "name": "⚔️ Warrior",
        "icon": "⚔️",
        "adjectives": [
            "Brave", "Courageous", "Fearless", "Valiant", "Gallant", "Heroic", "Mighty", "Powerful",
            "Strong", "Tough", "Hard", "Solid", "Steel", "Iron", "Bronze", "Golden",
            "Fierce", "Savage", "Brutal", "Vicious", "Deadly", "Lethal", "Mortal", "Fatal",
            "Victorious", "Triumphant", "Conquering", "Winning", "Champion", "Elite", "Legend"
        ],
        "nouns": [
            "Knight", "Warrior", "Fighter", "Soldier", "Guardian", "Protector", "Defender", "Shield",
            "Sword", "Blade", "Axe", "Hammer", "Spear", "Arrow", "Bow", "Dagger",
            "Armor", "Helmet", "Gauntlet", "Greaves", "Shield", "Cloak", "Cape", "Crown",
            "Dragon", "Griffin", "Phoenix", "Eagle", "Hawk", "Falcon", "Wolf", "Lion"
        ]
    },
    "wizard": {
        "name": "🔮 Wizard",
        "icon": "🔮",
        "adjectives": [
            "Mystic", "Magic", "Enchanted", "Spellbound", "Charmed", "Cursed", "Hexed", "Witched",
            "Arcane", "Elder", "Ancient", "Forgotten", "Hidden", "Secret", "Sacred", "Blessed",
            "Wise", "Clever", "Smart", "Intelligent", "Brilliant", "Sharp", "Quick", "Bright",
            "Powerful", "Mighty", "Grand", "Great", "Supreme", "Ultimate", "Absolute"
        ],
        "nouns": [
            "Wizard", "Witch", "Sorcerer", "Enchanter", "Necromancer", "Druid", "Shaman", "Mage",
            "Spell", "Curse", "Hex", "Charm", "Magic", "Sorcery", "Witchcraft", "Alchemy",
            "Potion", "Elixir", "Tonic", "Remedy", "Cure", "Poison", "Venom", "Toxin",
            "Crystal", "Gem", "Stone", "Orb", "Staff", "Wand", "Book", "Scroll"
        ]
    }
}

def get_available_themes():
    return [{"key": key, "name": theme["name"], "icon": theme["icon"]} 
            for key, theme in THEMES.items()]

# ============= DATABASE SETUP =============
def get_db():
    """Get database connection - works with SQLite locally and PostgreSQL on Render"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Production: PostgreSQL on Neon
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return conn
    else:
        # Local development: SQLite
        conn = sqlite3.connect("database.db", timeout=20)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    """Initialize database - works with both SQLite and PostgreSQL"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # PostgreSQL syntax
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Create tables with PostgreSQL syntax
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                display_name TEXT UNIQUE NOT NULL,
                theme TEXT NOT NULL,
                warnings INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts(
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                content TEXT,
                media_path TEXT,
                hidden INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments(
                id SERIAL PRIMARY KEY,
                post_id INTEGER,
                user_id INTEGER,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports(
                id SERIAL PRIMARY KEY,
                post_id INTEGER,
                reporter_id INTEGER,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS likes(
                id SERIAL PRIMARY KEY,
                post_id INTEGER,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(post_id, user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_posts(
                id SERIAL PRIMARY KEY,
                post_id INTEGER,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(post_id, user_id)
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ PostgreSQL database initialized!")
    else:
        # SQLite syntax
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        # Drop existing tables
        cursor.execute("DROP TABLE IF EXISTS saved_posts")
        cursor.execute("DROP TABLE IF EXISTS likes")
        cursor.execute("DROP TABLE IF EXISTS reports")
        cursor.execute("DROP TABLE IF EXISTS comments")
        cursor.execute("DROP TABLE IF EXISTS posts")
        cursor.execute("DROP TABLE IF EXISTS users")
        
        # Create users table
        cursor.execute("""
            CREATE TABLE users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                display_name TEXT UNIQUE NOT NULL,
                theme TEXT NOT NULL,
                warnings INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create posts table
        cursor.execute("""
            CREATE TABLE posts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT,
                media_path TEXT,
                hidden INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create comments table
        cursor.execute("""
            CREATE TABLE comments(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                user_id INTEGER,
                comment TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create reports table
        cursor.execute("""
            CREATE TABLE reports(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                reporter_id INTEGER,
                reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create likes table
        cursor.execute("""
            CREATE TABLE likes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                user_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(post_id, user_id)
            )
        """)
        
        # Create saved_posts table
        cursor.execute("""
            CREATE TABLE saved_posts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                user_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(post_id, user_id)
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ SQLite database initialized!")

def generate_unique_display_name(theme_key=None):
    """Generate unique display name based on theme"""
    conn = get_db()
    cursor = conn.cursor()
    
    if not theme_key or theme_key not in THEMES:
        theme_key = random.choice(list(THEMES.keys()))
    
    theme = THEMES[theme_key]
    adjectives = theme["adjectives"]
    nouns = theme["nouns"]
    
    max_attempts = 100
    
    for _ in range(max_attempts):
        adjective = random.choice(adjectives)
        noun = random.choice(nouns)
        number = random.randint(10, 9999)
        display_name = f"{adjective}{noun}{number}"
        
        cursor.execute("SELECT id FROM users WHERE display_name = %s", (display_name,))
        if not cursor.fetchone():
            conn.close()
            return display_name, theme_key, theme["icon"]
    
    fallback_name = f"User{random.randint(100000, 999999)}"
    conn.close()
    return fallback_name, theme_key, theme["icon"]

# Initialize database
init_db()

# ============= HELPER FUNCTIONS =============
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def time_ago(timestamp):
    try:
        if isinstance(timestamp, str):
            post_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        else:
            post_time = timestamp
        now = datetime.now()
        diff = now - post_time
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hours ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} minutes ago"
        else:
            return "Just now"
    except:
        return "Recently"

# ============= UPLOAD FOLDER =============
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ============= HOME =============
@app.route("/")
def home():
    return redirect("/login")

# ============= SIGNUP =============
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        theme_key = request.form.get("theme", "")
        
        if len(password) < 4:
            return render_template("signup.html", error="Password must be at least 4 characters", themes=get_available_themes())
        
        if not theme_key or theme_key not in THEMES:
            return render_template("signup.html", error="Please select a theme", themes=get_available_themes())
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            conn.close()
            return render_template("signup.html", error="Username already taken", themes=get_available_themes())
        
        display_name, selected_theme, theme_icon = generate_unique_display_name(theme_key)
        
        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, password, display_name, theme) VALUES (%s, %s, %s, %s)",
            (username, hashed_password, display_name, theme_key)
        )
        conn.commit()
        conn.close()
        
        return redirect("/login")
    
    return render_template("signup.html", themes=get_available_themes())

# ============= LOGIN =============
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not username or not password:
            return render_template("login.html", error="Please fill in all fields")
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s LIMIT 1", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user["password"], password):
            session.permanent = True
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["display_name"] = user["display_name"]
            session["theme"] = user["theme"]
            return redirect("/feed")
        
        return render_template("login.html", error="Invalid username or password")
    
    return render_template("login.html")

# ============= FEED =============
@app.route("/feed")
@login_required
def feed():
    conn = get_db()
    cursor = conn.cursor()
    
    # PostgreSQL-compatible query - using subquery for like count
    cursor.execute("""
        SELECT posts.*, 
               users.display_name as author_name,
               users.theme as author_theme,
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) as like_count,
               EXISTS(SELECT 1 FROM saved_posts WHERE saved_posts.post_id = posts.id AND saved_posts.user_id = %s) as is_saved
        FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE posts.hidden = 0
        ORDER BY posts.created_at DESC
        LIMIT 20
    """, (session["user_id"],))
    posts = cursor.fetchall()
    
    cursor.execute("""
        SELECT comments.*, 
               users.display_name as author_name,
               users.theme as author_theme
        FROM comments 
        JOIN users ON comments.user_id = users.id
        ORDER BY comments.created_at ASC
    """)
    comments = cursor.fetchall()
    
    conn.close()
    
    return render_template("feed.html", posts=posts, comments=comments, time_ago=time_ago, themes=THEMES)

# ============= API POSTS (INFINITE SCROLL) =============
@app.route("/api/posts")
@login_required
def api_posts():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT posts.*, 
               users.display_name as author_name,
               users.theme as author_theme,
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) as like_count,
               EXISTS(SELECT 1 FROM saved_posts WHERE saved_posts.post_id = posts.id AND saved_posts.user_id = %s) as is_saved
        FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE posts.hidden = 0
        ORDER BY posts.created_at DESC
        LIMIT %s OFFSET %s
    """, (session["user_id"], per_page, offset))
    
    posts = cursor.fetchall()
    conn.close()
    
    posts_list = []
    for post in posts:
        posts_list.append({
            "id": post["id"],
            "content": post["content"],
            "media_path": post["media_path"],
            "author_name": post["author_name"],
            "author_theme": post["author_theme"],
            "like_count": post["like_count"],
            "is_saved": post["is_saved"],
            "created_at": str(post["created_at"])
        })
    
    return jsonify({"posts": posts_list, "has_more": len(posts) == per_page})

# ============= CREATE POST =============
@app.route("/create_post", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        content = request.form.get("content", "").strip()
        file = request.files.get("media")
        
        if not content and (not file or not file.filename):
            return "Post must contain text or media", 400
        
        media_path = None
        if file and file.filename:
            filename = f"{datetime.now().timestamp()}_{file.filename}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            media_path = filename
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO posts (user_id, content, media_path) VALUES (%s, %s, %s)",
            (session["user_id"], content, media_path)
        )
        conn.commit()
        conn.close()
        
        return redirect("/feed")
    
    return render_template("create_post.html")

# ============= EDIT POST =============
@app.route("/edit_post/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM posts WHERE id = %s AND user_id = %s", (post_id, session["user_id"]))
    post = cursor.fetchone()
    
    if not post:
        conn.close()
        return "Post not found or you don't have permission", 404
    
    if request.method == "POST":
        new_content = request.form.get("content", "").strip()
        
        if not new_content:
            conn.close()
            return "Content cannot be empty", 400
        
        cursor.execute("""
            UPDATE posts 
            SET content = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (new_content, post_id))
        conn.commit()
        conn.close()
        
        return redirect(f"/feed#post-{post_id}")
    
    conn.close()
    return render_template("edit_post.html", post=post)

# ============= DELETE POST =============
@app.route("/delete_post/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
    post = cursor.fetchone()
    
    if post and post["user_id"] == session["user_id"]:
        cursor.execute("DELETE FROM comments WHERE post_id = %s", (post_id,))
        cursor.execute("DELETE FROM likes WHERE post_id = %s", (post_id,))
        cursor.execute("DELETE FROM saved_posts WHERE post_id = %s", (post_id,))
        cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
        conn.commit()
    
    conn.close()
    return redirect("/feed")

# ============= SAVE POST =============
@app.route("/save_post/<int:post_id>")
@login_required
def save_post(post_id):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO saved_posts (post_id, user_id) VALUES (%s, %s)",
            (post_id, session["user_id"])
        )
        conn.commit()
        saved = True
    except Exception:
        cursor.execute(
            "DELETE FROM saved_posts WHERE post_id = %s AND user_id = %s",
            (post_id, session["user_id"])
        )
        conn.commit()
        saved = False
    
    conn.close()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"saved": saved})
    
    return redirect(f"/feed#post-{post_id}")

# ============= SAVED POSTS PAGE =============
@app.route("/saved")
@login_required
def saved_posts():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT posts.*, 
               users.display_name as author_name,
               users.theme as author_theme,
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) as like_count,
               saved_posts.created_at as saved_at
        FROM saved_posts
        JOIN posts ON saved_posts.post_id = posts.id
        JOIN users ON posts.user_id = users.id
        WHERE saved_posts.user_id = %s AND posts.hidden = 0
        ORDER BY saved_posts.created_at DESC
    """, (session["user_id"],))
    saved_posts_list = cursor.fetchall()
    
    conn.close()
    
    return render_template("saved.html", posts=saved_posts_list, time_ago=time_ago, themes=THEMES)

# ============= USER PROFILE =============
@app.route("/profile/<display_name>")
@login_required
def profile(display_name):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE display_name = %s", (display_name,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return "User not found", 404
    
    cursor.execute("""
        SELECT posts.*, 
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) as like_count
        FROM posts
        WHERE posts.user_id = %s AND posts.hidden = 0
        ORDER BY posts.created_at DESC
    """, (user["id"],))
    user_posts = cursor.fetchall()
    
    cursor.execute("""
        SELECT COUNT(*) as total_likes FROM likes 
        WHERE post_id IN (SELECT id FROM posts WHERE user_id = %s)
    """, (user["id"],))
    total_likes = cursor.fetchone()["total_likes"]
    
    conn.close()
    
    return render_template("profile.html", 
                          profile_user=user, 
                          posts=user_posts, 
                          total_likes=total_likes,
                          time_ago=time_ago,
                          themes=THEMES)

# ============= TRENDING =============
@app.route("/trending")
@login_required
def trending():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT posts.*, 
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) as like_count,
               users.display_name as author_name,
               users.theme as author_theme
        FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE posts.created_at > NOW() - INTERVAL '1 day' AND posts.hidden = 0
        ORDER BY like_count DESC
        LIMIT 30
    """)
    trending_posts = cursor.fetchall()
    
    conn.close()
    
    return render_template("trending.html", posts=trending_posts, time_ago=time_ago, themes=THEMES)

# ============= COMMENT =============
@app.route("/comment/<int:post_id>", methods=["POST"])
@login_required
def comment(post_id):
    comment_text = request.form.get("comment", "").strip()
    if not comment_text:
        return redirect("/feed")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO comments (post_id, user_id, comment) VALUES (%s, %s, %s)",
        (post_id, session["user_id"], comment_text)
    )
    conn.commit()
    conn.close()
    
    return redirect(f"/feed#post-{post_id}")

# ============= LIKE =============
@app.route("/like/<int:post_id>")
@login_required
def like(post_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id FROM likes WHERE post_id = %s AND user_id = %s",
        (post_id, session["user_id"])
    )
    
    if not cursor.fetchone():
        try:
            cursor.execute(
                "INSERT INTO likes (post_id, user_id) VALUES (%s, %s)",
                (post_id, session["user_id"])
            )
            conn.commit()
            liked = True
        except:
            liked = False
    else:
        liked = False
    
    conn.close()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"success": liked})
    
    return redirect(f"/feed#post-{post_id}")

# ============= REPORT =============
@app.route("/report/<int:post_id>", methods=["POST"])
@login_required
def report(post_id):
    reason = request.form.get("reason", "").strip()
    if not reason:
        return redirect("/feed")
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id FROM reports WHERE post_id = %s AND reporter_id = %s",
        (post_id, session["user_id"])
    )
    
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO reports (post_id, reporter_id, reason) VALUES (%s, %s, %s)",
            (post_id, session["user_id"], reason)
        )
        
        cursor.execute("SELECT COUNT(*) FROM reports WHERE post_id = %s", (post_id,))
        count = cursor.fetchone()["count"]
        
        if count >= 5:
            cursor.execute("UPDATE posts SET hidden = 1 WHERE id = %s", (post_id,))
        
        conn.commit()
    
    conn.close()
    
    return redirect(f"/feed#post-{post_id}")

# ============= SEARCH =============
@app.route("/search")
@login_required
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return redirect("/feed")
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT posts.*, 
               users.display_name as author_name,
               users.theme as author_theme,
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) as like_count
        FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE posts.hidden = 0 AND posts.content LIKE %s
        ORDER BY posts.created_at DESC
    """, (f'%{query}%',))
    posts = cursor.fetchall()
    
    cursor.execute("""
        SELECT comments.*, 
               users.display_name as author_name,
               users.theme as author_theme
        FROM comments 
        JOIN users ON comments.user_id = users.id
        ORDER BY comments.created_at ASC
    """)
    comments = cursor.fetchall()
    
    conn.close()
    return render_template("feed.html", posts=posts, comments=comments, time_ago=time_ago, themes=THEMES)

# ============= ADMIN =============
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'mayur123')

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get("admin"):
        return redirect("/admin/reports")
    
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin/reports")
        return render_template("admin_login.html", error="Wrong password")
    
    return render_template("admin_login.html")

@app.route("/admin/reports")
def admin_reports():
    if not session.get("admin"):
        return redirect("/admin")
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT reports.*, posts.content as post_content, 
               users.display_name as reporter_name,
               posts.user_id as post_owner_id
        FROM reports
        JOIN posts ON reports.post_id = posts.id
        JOIN users ON reports.reporter_id = users.id
        ORDER BY reports.created_at DESC
    """)
    reports = cursor.fetchall()
    
    conn.close()
    
    return render_template("admin_reports.html", reports=reports)

@app.route("/admin/delete_post/<int:post_id>/<int:user_id>")
def admin_delete_post(post_id, user_id):
    if not session.get("admin"):
        return redirect("/admin")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
    cursor.execute("UPDATE users SET warnings = warnings + 1 WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()
    
    return redirect("/admin/reports")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin")

# ============= LOGOUT =============
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ============= RUN APP =============
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
