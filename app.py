import os
import sqlite3
import random
import string
import uuid
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, session, render_template, g, redirect, url_for
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load configuration
try:
    app.config.from_pyfile('config.py')
except FileNotFoundError:
    logger.error("config.py not found. Using default configuration.")
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-default-secret-key')
    app.config['ADMIN_USERNAME'] = os.getenv('ADMIN_USERNAME', 'admin')
    app.config['ADMIN_PASS'] = os.getenv('ADMIN_PASS', 'adminpass')

# Set up upload folder
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'pdf', 'doc', 'docx'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database configuration (use environment variable for database path in production)
DATABASE = os.getenv('DATABASE_URL', 'database.db')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def generate_unique_key():
    with app.app_context():
        while True:
            letters = ''.join(random.choice(string.ascii_letters) for _ in range(2))
            numbers = ''.join(random.choice(string.digits) for _ in range(2))
            key = ''.join(random.sample(letters + numbers, 4))
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT id FROM users WHERE unique_key = ?", (key,))
            if not cursor.fetchone():
                return key

def generate_group_link():
    with app.app_context():
        while True:
            link = str(uuid.uuid4())[:8]
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT id FROM groups WHERE link = ?", (link,))
            if not cursor.fetchone():
                return link

def init_db():
    with app.app_context():  # Ensure application context
        db = get_db()
        cursor = db.cursor()
        try:
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    real_name TEXT,
                    bio TEXT,
                    profile_pic_url TEXT,
                    unique_key TEXT UNIQUE NOT NULL,
                    email TEXT,
                    phone TEXT,
                    gender TEXT,
                    pronouns TEXT,
                    dob TEXT,
                    work TEXT,
                    education TEXT,
                    places TEXT,
                    relationship TEXT,
                    spouse TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_admin INTEGER DEFAULT 0,
                    banned_until TIMESTAMP,
                    profile_locked INTEGER DEFAULT 0,
                    posts_privacy TEXT DEFAULT 'all',
                    reels_privacy TEXT DEFAULT 'all',
                    stories_privacy TEXT DEFAULT 'friends',
                    theme TEXT DEFAULT 'light',
                    notifications_settings TEXT DEFAULT '{}'
                )
            ''')
            # Follows table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS follows (
                    follower_id INTEGER,
                    followed_id INTEGER,
                    status TEXT DEFAULT 'pending',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (follower_id, followed_id)
                )
            ''')
            # Blocks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocks (
                    blocker_id INTEGER,
                    blocked_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (blocker_id, blocked_id)
                )
            ''')
            # Posts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    description TEXT,
                    media_url TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    views INTEGER DEFAULT 0,
                    privacy TEXT DEFAULT 'all',
                    comments_enabled INTEGER DEFAULT 1,
                    shares_enabled INTEGER DEFAULT 1
                )
            ''')
            # Likes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS likes (
                    user_id INTEGER,
                    post_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, post_id)
                )
            ''')
            # Comments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    post_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Reposts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reposts (
                    user_id INTEGER,
                    post_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, post_id)
                )
            ''')
            # Saves table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS saves (
                    user_id INTEGER,
                    post_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, post_id)
                )
            ''')
            # Reports table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reporter_id INTEGER NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id INTEGER NOT NULL,
                    reason TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    receiver_id INTEGER NOT NULL,
                    is_group INTEGER DEFAULT 0,
                    text TEXT,
                    media_url TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read INTEGER DEFAULT 0,
                    disappearing_after TEXT DEFAULT 'off'
                )
            ''')
            # Chat customizations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_custom (
                    user_id INTEGER,
                    chat_id INTEGER,
                    is_group INTEGER DEFAULT 0,
                    nickname TEXT,
                    wallpaper_url TEXT,
                    PRIMARY KEY (user_id, chat_id, is_group)
                )
            ''')
            # Groups table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    creator_id INTEGER NOT NULL,
                    profile_pic_url TEXT,
                    description TEXT,
                    link TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Group members table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_members (
                    group_id INTEGER,
                    user_id INTEGER,
                    is_admin INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'accepted',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (group_id, user_id)
                )
            ''')
            # Group permissions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_permissions (
                    group_id INTEGER PRIMARY KEY,
                    allow_edit_nonadmin INTEGER DEFAULT 0,
                    allow_messages_nonadmin INTEGER DEFAULT 1,
                    allow_add_nonadmin INTEGER DEFAULT 1,
                    approve_new_members INTEGER DEFAULT 0
                )
            ''')
            # Notifications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    from_user_id INTEGER,
                    post_id INTEGER,
                    group_id INTEGER,
                    text TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read INTEGER DEFAULT 0
                )
            ''')
            # Post subscriptions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS post_subscriptions (
                    user_id INTEGER,
                    post_user_id INTEGER,
                    PRIMARY KEY (user_id, post_user_id)
                )
            ''')
            # Admin warnings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Insert admin user
            admin_username = app.config['ADMIN_USERNAME']
            admin_pass_hash = generate_password_hash(app.config['ADMIN_PASS'])
            cursor.execute("SELECT id FROM users WHERE username = ?", (admin_username,))
            if not cursor.fetchone():
                unique_key = generate_unique_key()
                cursor.execute("INSERT INTO users (username, password_hash, unique_key, is_admin) VALUES (?, ?, ?, 1)", (admin_username, admin_pass_hash, unique_key))
            db.commit()
            logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

# Initialize database only if it hasn't been initialized
def initialize_app():
    if not os.path.exists(DATABASE):
        logger.info("Creating new database...")
        init_db()
    else:
        logger.info("Database already exists, skipping initialization.")

# Call initialization during app startup
initialize_app()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        # Check if user is banned
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT banned_until FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        if user and user['banned_until'] and user['banned_until'] > datetime.now().strftime('%Y-%m-%d %H:%M:%S'):
            return jsonify({'error': 'User is banned'}), 403
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT is_admin FROM users WHERE id = ?", (session['user_id'],))
        if cursor.fetchone()['is_admin'] == 0:
            return jsonify({'error': 'Forbidden'}), 403
        return f(*args, **kwargs)
    return decorated_function

def notify(user_id, type, from_user_id=None, post_id=None, group_id=None, text=None):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO notifications (user_id, type, from_user_id, post_id, group_id, text) VALUES (?, ?, ?, ?, ?, ?)", (user_id, type, from_user_id, post_id, group_id, text))
    db.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user/<username>')
def user_profile(username):
    return render_template('index.html')

@app.route('/group/<link>')
def group_route(link):
    return render_template('index.html')

@app.route('/api/user/by_username/<username>', methods=['GET'])
@login_required
def get_user_by_username(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'id': row['id']})

@app.route('/api/group/by_link/<link>', methods=['GET'])
@login_required
def get_group_by_link(link):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM groups WHERE link = ?", (link,))
    row = cursor.fetchone()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'id': row['id']})

@app.route('/api/user/me', methods=['GET'])
@login_required
def get_current_user():
    return get_user(session['user_id'])

@app.route('/api/user/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return jsonify({'error': 'Not found'}), 404
    user_dict = dict(user)
    del user_dict['password_hash']
    is_own = user_id == session['user_id']
    if not is_own:
        del user_dict['unique_key']
        cursor.execute("SELECT * FROM blocks WHERE (blocker_id = ? AND blocked_id = ?) OR (blocker_id = ? AND blocked_id = ?)", (session['user_id'], user_id, user_id, session['user_id']))
        if cursor.fetchone():
            return jsonify({'error': 'Blocked'}), 403
        cursor.execute("""
            SELECT u.id, u.real_name, u.username, u.profile_pic_url 
            FROM users u
            INNER JOIN follows f1 ON f1.followed_id = u.id AND f1.follower_id = ? AND f1.status = 'accepted'
            INNER JOIN follows f2 ON f2.followed_id = u.id AND f2.follower_id = ? AND f2.status = 'accepted'
            LIMIT 3
        """, (session['user_id'], user_id))
        user_dict['mutual_friends'] = [dict(row) for row in cursor.fetchall()]
    cursor.execute("SELECT COUNT(*) as posts FROM posts WHERE user_id = ? AND type = 'post'", (user_id,))
    user_dict['posts_count'] = cursor.fetchone()['posts']
    cursor.execute("SELECT COUNT(*) as likes FROM likes WHERE post_id IN (SELECT id FROM posts WHERE user_id = ?)", (user_id,))
    user_dict['likes_count'] = cursor.fetchone()['likes']
    cursor.execute("SELECT COUNT(*) as followers FROM follows WHERE followed_id = ? AND status = 'accepted'", (user_id,))
    user_dict['followers_count'] = cursor.fetchone()['followers']
    cursor.execute("SELECT COUNT(*) as following FROM follows WHERE follower_id = ? AND status = 'accepted'", (user_id,))
    user_dict['following_count'] = cursor.fetchone()['following']
    cursor.execute("""
        SELECT COUNT(*) as friends FROM follows f1
        WHERE f1.follower_id = ? AND f1.status = 'accepted'
        AND EXISTS (SELECT 1 FROM follows f2 WHERE f2.follower_id = f1.followed_id AND f2.followed_id = ? AND f2.status = 'accepted')
    """, (user_id, user_id))
    user_dict['friends_count'] = cursor.fetchone()['friends']
    return jsonify(user_dict)

@app.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile():
    data = request.json
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    if 'username' in data:
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        current_username = cursor.fetchone()['username']
        if data['username'] != current_username:
            cursor.execute("SELECT id FROM users WHERE username = ?", (data['username'],))
            if cursor.fetchone():
                return jsonify({'error': 'Username taken'}), 400
    update_fields = list(data.keys())
    update_str = ', '.join(f"{k} = ?" for k in update_fields)
    values = list(data.values()) + [user_id]
    cursor.execute(f"UPDATE users SET {update_str} WHERE id = ?", values)
    db.commit()
    return jsonify({'message': 'Updated'})

@app.route('/api/user/posts/<int:user_id>', methods=['GET'])
@login_required
def get_user_posts(user_id):
    type_ = request.args.get('type', 'post')
    privacy = request.args.get('privacy', None)
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    current_id = session['user_id']
    is_own = current_id == user_id
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT posts_privacy FROM users WHERE id = ?", (user_id,))
    user_privacy = cursor.fetchone()['posts_privacy']
    if not is_own:
        if user_privacy == 'only_me':
            return jsonify([])
        if user_privacy == 'friends':
            cursor.execute("SELECT * FROM follows WHERE follower_id = ? AND followed_id = ? AND status = 'accepted'", (current_id, user_id))
            if not cursor.fetchone():
                return jsonify([])
    where = "WHERE user_id = ? AND type = ?"
    params = [user_id, type_]
    if privacy:
        where += " AND privacy = ?"
        params.append(privacy)
    cursor.execute(f"""
        SELECT p.*, u.username, u.real_name, u.profile_pic_url 
        FROM posts p JOIN users u ON p.user_id = u.id 
        {where} ORDER BY timestamp DESC LIMIT ? OFFSET ?
    """, params + [per_page, offset])
    posts = [dict(row) for row in cursor.fetchall()]
    return jsonify(posts)

@app.route('/api/user/saves', methods=['GET'])
@login_required
def get_user_saves():
    user_id = session['user_id']
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.*, u.username, u.real_name, u.profile_pic_url 
        FROM posts p 
        JOIN saves s ON p.id = s.post_id 
        JOIN users u ON p.user_id = u.id 
        WHERE s.user_id = ? 
        ORDER BY s.timestamp DESC LIMIT ? OFFSET ?
    """, (user_id, per_page, offset))
    return jsonify([dict(row) for row in cursor.fetchall()])

@app.route('/api/user/reposts', methods=['GET'])
@login_required
def get_user_reposts():
    user_id = session['user_id']
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.*, u.username, u.real_name, u.profile_pic_url 
        FROM posts p 
        JOIN reposts r ON p.id = r.post_id 
        JOIN users u ON p.user_id = u.id 
        WHERE r.user_id = ? 
        ORDER BY r.timestamp DESC LIMIT ? OFFSET ?
    """, (user_id, per_page, offset))
    return jsonify([dict(row) for row in cursor.fetchall()])

@app.route('/api/user/likes', methods=['GET'])
@login_required
def get_user_likes():
    user_id = session['user_id']
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.*, u.username, u.real_name, u.profile_pic_url 
        FROM posts p 
        JOIN likes l ON p.id = l.post_id 
        JOIN users u ON p.user_id = u.id 
        WHERE l.user_id = ? 
        ORDER BY l.timestamp DESC LIMIT ? OFFSET ?
    """, (user_id, per_page, offset))
    return jsonify([dict(row) for row in cursor.fetchall()])

@app.route('/api/group/<int:group_id>', methods=['GET'])
@login_required
def get_group(group_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM groups WHERE id = ?", (group_id,))
    group = cursor.fetchone()
    if not group:
        return jsonify({'error': 'Not found'}), 404
    group_dict = dict(group)
    cursor.execute("SELECT COUNT(*) as count FROM group_members WHERE group_id = ? AND status = 'accepted'", (group_id,))
    group_dict['members_count'] = cursor.fetchone()['count']
    cursor.execute("SELECT is_admin FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, session['user_id']))
    member = cursor.fetchone()
    if not member:
        return jsonify({'error': 'Not member'}), 403
    group_dict['is_admin'] = member['is_admin']
    cursor.execute("SELECT username FROM users WHERE id = ?", (group_dict['creator_id'],))
    creator_username = cursor.fetchone()['username']
    group_dict['description_full'] = (group_dict['description'] or '') + f"\nCreated by @{creator_username} on {group_dict['created_at']}"
    cursor.execute("SELECT * FROM group_permissions WHERE group_id = ?", (group_id,))
    perms = cursor.fetchone()
    group_dict['permissions'] = dict(perms) if perms else {
        'allow_edit_nonadmin': 0,
        'allow_messages_nonadmin': 1,
        'allow_add_nonadmin': 1,
        'approve_new_members': 0
    }
    return jsonify(group_dict)

@app.route('/api/group/members/<int:group_id>', methods=['GET'])
@login_required
def get_group_members(group_id):
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT is_admin FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, session['user_id']))
    if not cursor.fetchone():
        return jsonify({'error': 'Not member'}), 403
    cursor.execute("""
        SELECT u.id, u.username, u.real_name, u.profile_pic_url, gm.is_admin 
        FROM group_members gm 
        JOIN users u ON gm.user_id = u.id 
        WHERE gm.group_id = ? AND gm.status = 'accepted' 
        ORDER BY gm.joined_at DESC LIMIT ? OFFSET ?
    """, (group_id, limit, offset))
    members = [dict(row) for row in cursor.fetchall()]
    return jsonify(members)

@app.route('/api/group/admin/toggle', methods=['POST'])
@login_required
def toggle_group_admin():
    data = request.json
    group_id = data.get('group_id')
    target_id = data.get('target_id')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT is_admin FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, session['user_id']))
    member = cursor.fetchone()
    if not member or member['is_admin'] == 0:
        return jsonify({'error': 'Not admin'}), 403
    cursor.execute("SELECT creator_id FROM groups WHERE id = ?", (group_id,))
    if target_id == cursor.fetchone()['creator_id']:
        return jsonify({'error': 'Cannot toggle creator'}), 400
    cursor.execute("UPDATE group_members SET is_admin = 1 - is_admin WHERE group_id = ? AND user_id = ?", (group_id, target_id))
    db.commit()
    notify(target_id, 'group_admin_toggle', from_user_id=session['user_id'], group_id=group_id)
    return jsonify({'message': 'Toggled'})

@app.route('/api/group/remove', methods=['POST'])
@login_required
def remove_group_member():
    data = request.json
    group_id = data.get('group_id')
    target_id = data.get('target_id')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT is_admin FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, session['user_id']))
    member = cursor.fetchone()
    if not member or member['is_admin'] == 0:
        return jsonify({'error': 'Not admin'}), 403
    cursor.execute("SELECT creator_id FROM groups WHERE id = ?", (group_id,))
    if target_id == cursor.fetchone()['creator_id']:
        return jsonify({'error': 'Cannot remove creator'}), 400
    cursor.execute("DELETE FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, target_id))
    db.commit()
    notify(target_id, 'group_remove', from_user_id=session['user_id'], group_id=group_id)
    return jsonify({'message': 'Removed'})

@app.route('/api/group/permissions/update', methods=['POST'])
@login_required
def update_group_permissions():
    data = request.json
    group_id = data.pop('group_id')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT is_admin FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, session['user_id']))
    member = cursor.fetchone()
    if not member or member['is_admin'] == 0:
        return jsonify({'error': 'Not admin'}), 403
    cursor.execute("SELECT * FROM group_permissions WHERE group_id = ?", (group_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO group_permissions (group_id) VALUES (?)", (group_id,))
    update_str = ', '.join(f"{k} = ?" for k in data)
    values = list(data.values()) + [group_id]
    cursor.execute(f"UPDATE group_permissions SET {update_str} WHERE group_id = ?", values)
    db.commit()
    return jsonify({'message': 'Updated'})

@app.route('/api/group/media/<int:group_id>', methods=['GET'])
@login_required
def get_group_media(group_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, session['user_id']))
    if not cursor.fetchone():
        return jsonify({'error': 'Not member'}), 403
    cursor.execute("SELECT media_url FROM messages WHERE receiver_id = ? AND is_group = 1 AND media_url IS NOT NULL", (group_id,))
    media = [dict(row) for row in cursor.fetchall()]
    return jsonify(media)

@app.route('/api/group/links/<int:group_id>', methods=['GET'])
@login_required
def get_group_links(group_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, session['user_id']))
    if not cursor.fetchone():
        return jsonify({'error': 'Not member'}), 403
    cursor.execute("SELECT text FROM messages WHERE receiver_id = ? AND is_group = 1 AND text LIKE '%http%'", (group_id,))
    links = [dict(row) for row in cursor.fetchall()]
    return jsonify(links)

@app.route('/api/group/docs/<int:group_id>', methods=['GET'])
@login_required
def get_group_docs(group_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, session['user_id']))
    if not cursor.fetchone():
        return jsonify({'error': 'Not member'}), 403
    cursor.execute("SELECT media_url FROM messages WHERE receiver_id = ? AND is_group = 1 AND (media_url LIKE '%.pdf' OR media_url LIKE '%.doc' OR media_url LIKE '%.docx')", (group_id,))
    docs = [dict(row) for row in cursor.fetchall()]
    return jsonify(docs)

@app.route('/api/group/report', methods=['POST'])
@login_required
def report_group():
    data = request.json
    group_id = data.get('group_id')
    reason = data.get('reason')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO reports (reporter_id, target_type, target_id, reason) VALUES (?, 'group', ?, ?)", (session['user_id'], group_id, reason))
    db.commit()
    return jsonify({'message': 'Reported'})

@app.route('/api/group/add', methods=['POST'])
@login_required
def add_member():
    data = request.json
    group_id = data.get('group_id')
    target_id = data.get('target_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT is_admin FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
    member = cursor.fetchone()
    if not member:
        return jsonify({'error': 'Not member'}), 403
    cursor.execute("SELECT allow_add_nonadmin, approve_new_members FROM group_permissions WHERE group_id = ?", (group_id,))
    perm = cursor.fetchone()
    if not perm:
        cursor.execute("INSERT INTO group_permissions (group_id) VALUES (?)", (group_id,))
        perm = {'allow_add_nonadmin': 1, 'approve_new_members': 0}
    if member['is_admin'] == 0 and perm['allow_add_nonadmin'] == 0:
        return jsonify({'error': 'Not allowed'}), 403
    status = 'pending' if perm['approve_new_members'] else 'accepted'
    try:
        cursor.execute("INSERT INTO group_members (group_id, user_id, status) VALUES (?, ?, ?)", (group_id, target_id, status))
        db.commit()
        notify(target_id, 'group_invite', from_user_id=user_id, group_id=group_id)
        return jsonify({'message': 'Added'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Already member'}), 400

@app.route('/api/group/leave', methods=['POST'])
@login_required
def leave_group():
    data = request.json
    group_id = data.get('group_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
    db.commit()
    cursor.execute("SELECT creator_id FROM groups WHERE id = ?", (group_id,))
    if cursor.fetchone()['creator_id'] == user_id:
        admin_delete_group(group_id=group_id)
    return jsonify({'message': 'Left'})

@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    notifs = [dict(row) for row in cursor.fetchall()]
    cursor.execute("UPDATE notifications SET read = 1 WHERE user_id = ? AND read = 0", (user_id,))
    db.commit()
    return jsonify(notifs)

@app.route('/api/notification/read', methods=['POST'])
@login_required
def read_notification():
    data = request.json
    notif_id = data.get('id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE notifications SET read = 1 WHERE id = ? AND user_id = ?", (notif_id, user_id))
    db.commit()
    return jsonify({'message': 'Read'})

@app.route('/api/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('query', '')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, username, real_name, profile_pic_url FROM users WHERE real_name LIKE ? LIMIT 20", (f"%{query}%",))
    users_real = [dict(row) for row in cursor.fetchall()]
    cursor.execute("SELECT id, username, real_name, profile_pic_url FROM users WHERE username LIKE ? AND real_name NOT LIKE ? LIMIT 20", (f"%{query}%", f"%{query}%"))
    users_username = [dict(row) for row in cursor.fetchall()]
    users = users_real + users_username
    return jsonify({'users': users})

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_get_users():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    for user in users:
        del user['password_hash'], user['unique_key']
    return jsonify(users)

@app.route('/api/admin/user/delete', methods=['POST'])
@admin_required
def admin_delete_user():
    data = request.json
    target_id = data.get('user_id')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM posts WHERE user_id = ?", (target_id,))
    cursor.execute("DELETE FROM likes WHERE user_id = ?", (target_id,))
    cursor.execute("DELETE FROM comments WHERE user_id = ?", (target_id,))
    cursor.execute("DELETE FROM reposts WHERE user_id = ?", (target_id,))
    cursor.execute("DELETE FROM saves WHERE user_id = ?", (target_id,))
    cursor.execute("DELETE FROM reports WHERE reporter_id = ?", (target_id,))
    cursor.execute("DELETE FROM messages WHERE sender_id = ? OR receiver_id = ?", (target_id, target_id))
    cursor.execute("DELETE FROM follows WHERE follower_id = ? OR followed_id = ?", (target_id, target_id))
    cursor.execute("DELETE FROM blocks WHERE blocker_id = ? OR blocked_id = ?", (target_id, target_id))
    cursor.execute("DELETE FROM group_members WHERE user_id = ?", (target_id,))
    cursor.execute("DELETE FROM notifications WHERE user_id = ? OR from_user_id = ?", (target_id, target_id))
    cursor.execute("DELETE FROM chat_custom WHERE user_id = ?", (target_id,))
    cursor.execute("DELETE FROM post_subscriptions WHERE user_id = ?", (target_id,))
    cursor.execute("DELETE FROM admin_warnings WHERE user_id = ?", (target_id,))
    cursor.execute("SELECT id FROM groups WHERE creator_id = ?", (target_id,))
    groups = [row['id'] for row in cursor.fetchall()]
    for g_id in groups:
        admin_delete_group(group_id=g_id)
    cursor.execute("DELETE FROM users WHERE id = ?", (target_id,))
    db.commit()
    return jsonify({'message': 'Deleted'})

@app.route('/api/admin/user/ban', methods=['POST'])
@admin_required
def admin_ban_user():
    data = request.json
    target_id = data.get('user_id')
    duration = data.get('duration')
    db = get_db()
    cursor = db.cursor()
    if duration == 'forever':
        banned_until = '9999-12-31 23:59:59'
    else:
        try:
            banned_until = (datetime.now() + timedelta(days=int(duration))).strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return jsonify({'error': 'Invalid duration'}), 400
    cursor.execute("UPDATE users SET banned_until = ? WHERE id = ?", (banned_until, target_id))
    db.commit()
    notify(target_id, 'ban', text=f'Banned for {duration}')
    return jsonify({'message': 'Banned'})

@app.route('/api/admin/warning', methods=['POST'])
@admin_required
def admin_warning():
    data = request.json
    target_id = data.get('user_id')
    message = data.get('message')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO notifications (user_id, type, text) VALUES (?, 'warning', ?)", (target_id, message))
    cursor.execute("INSERT INTO admin_warnings (user_id, message) VALUES (?, ?)", (target_id, message))
    db.commit()
    return jsonify({'message': 'Warning sent'})

@app.route('/api/admin/reports', methods=['GET'])
@admin_required
def admin_get_reports():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM reports ORDER BY timestamp DESC")
    reports = [dict(row) for row in cursor.fetchall()]
    return jsonify(reports)

@app.route('/api/admin/groups', methods=['GET'])
@admin_required
def admin_get_groups():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM groups")
    groups = [dict(row) for row in cursor.fetchall()]
    return jsonify(groups)

def admin_delete_group(group_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM groups WHERE id = ?", (group_id,))
    cursor.execute("DELETE FROM group_members WHERE group_id = ?", (group_id,))
    cursor.execute("DELETE FROM group_permissions WHERE group_id = ?", (group_id,))
    cursor.execute("DELETE FROM messages WHERE receiver_id = ? AND is_group = 1", (group_id,))
    cursor.execute("DELETE FROM notifications WHERE group_id = ?", (group_id,))
    cursor.execute("DELETE FROM chat_custom WHERE chat_id = ? AND is_group = 1", (group_id,))
    db.commit()

@app.route('/api/admin/group/delete', methods=['POST'])
@admin_required
def admin_delete_group_route():
    data = request.json
    group_id = data.get('group_id')
    admin_delete_group(group_id)
    return jsonify({'message': 'Deleted'})

@app.route('/api/admin/inbox', methods=['GET'])
@admin_required
def admin_inbox():
    admin_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT DISTINCT CASE WHEN sender_id = ? THEN receiver_id ELSE sender_id END as chat_user_id
        FROM messages WHERE is_group = 0 AND (sender_id = ? OR receiver_id = ?)
        ORDER BY (SELECT MAX(timestamp) FROM messages WHERE ((sender_id = ? AND receiver_id = chat_user_id) OR (sender_id = chat_user_id AND receiver_id = ?))) DESC
    """, (admin_id, admin_id, admin_id, admin_id, admin_id))
    chat_ids = [row['chat_user_id'] for row in cursor.fetchall()]
    chats = []
    for chat_id in chat_ids:
        cursor.execute("SELECT id, username, real_name, profile_pic_url FROM users WHERE id = ?", (chat_id,))
        user = dict(cursor.fetchone())
        cursor.execute("SELECT text, timestamp FROM messages WHERE ((sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)) AND is_group = 0 ORDER BY timestamp DESC LIMIT 1", (admin_id, chat_id, chat_id, admin_id))
        last_msg = cursor.fetchone()
        user['last_message'] = last_msg['text'] if last_msg else ''
        user['last_timestamp'] = last_msg['timestamp'] if last_msg else ''
        cursor.execute("SELECT COUNT(*) as unread FROM messages WHERE sender_id = ? AND receiver_id = ? AND is_group = 0 AND read = 0", (chat_id, admin_id))
        user['unread'] = cursor.fetchone()['unread']
        chats.append(user)
    return jsonify(chats)

@app.route('/api/admin/send_system', methods=['POST'])
@admin_required
def admin_send_system():
    data = request.json
    target_id = data.get('target_id')
    message = data.get('message')
    db = get_db()
    cursor = db.cursor()
    if target_id == 'all':
        cursor.execute("SELECT id FROM users")
        users = [row['id'] for row in cursor.fetchall()]
        for u in users:
            notify(u, 'system', text=message)
    else:
        notify(target_id, 'system', text=message)
    db.commit()
    return jsonify({'message': 'Sent'})

@app.route('/api/login', methods=['POST'])
@login_required
def login():
    data = request.json
    identifier = data.get('identifier')
    password = data.get('password')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ? OR phone = ?", (identifier, identifier, identifier))
    user = cursor.fetchone()
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid credentials'}), 401
    if user['banned_until'] and user['banned_until'] > datetime.now().strftime('%Y-%m-%d %H:%M:%S'):
        return jsonify({'error': 'User is banned'}), 403
    session['user_id'] = user['id']
    return jsonify({'message': 'Logged in'})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        return jsonify({'error': 'Username taken'}), 400
    unique_key = generate_unique_key()
    password_hash = generate_password_hash(password)
    cursor.execute("INSERT INTO users (username, password_hash, unique_key) VALUES (?, ?, ?)", (username, password_hash, unique_key))
    db.commit()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_id = cursor.fetchone()['id']
    session['user_id'] = user_id
    return jsonify({'message': 'Registered', 'unique_key': unique_key})

@app.route('/api/forgot', methods=['POST'])
def forgot():
    data = request.json
    username = data.get('username')
    unique_key = data.get('unique_key')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? AND unique_key = ?", (username, unique_key))
    user = cursor.fetchone()
    if not user:
        return jsonify({'error': 'Invalid username or key'}), 400
    session['reset_user_id'] = user['id']
    return jsonify({'message': 'Key verified. Please reset password.'})

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    password = data.get('password')
    user_id = session.get('reset_user_id')
    if not user_id:
        return jsonify({'error': 'No reset session'}), 400
    db = get_db()
    cursor = db.cursor()
    password_hash = generate_password_hash(password)
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
    db.commit()
    session.pop('reset_user_id', None)
    return jsonify({'message': 'Password reset'})

@app.route('/api/change_password', methods=['POST'])
@login_required
def change_password():
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not check_password_hash(user['password_hash'], old_password):
        return jsonify({'error': 'Invalid old password'}), 400
    password_hash = generate_password_hash(new_password)
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
    db.commit()
    return jsonify({'message': 'Password changed'})

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        url = f"/{app.config['UPLOAD_FOLDER']}/{unique_filename}"
        return jsonify({'url': url})
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/post/create', methods=['POST'])
@login_required
def create_post():
    data = request.json
    user_id = session['user_id']
    type_ = data.get('type')
    description = data.get('description')
    media_url = data.get('media_url')
    privacy = data.get('privacy', 'all')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO posts (user_id, type, description, media_url, privacy) VALUES (?, ?, ?, ?, ?)", (user_id, type_, description, media_url, privacy))
    db.commit()
    cursor.execute("SELECT last_insert_rowid() as id")
    post_id = cursor.fetchone()['id']
    cursor.execute("SELECT post_user_id FROM post_subscriptions WHERE user_id = ?", (user_id,))
    subscribers = [row['post_user_id'] for row in cursor.fetchall()]
    for sub_id in subscribers:
        notify(sub_id, 'post', from_user_id=user_id, post_id=post_id)
    return jsonify({'message': 'Posted', 'post_id': post_id})

@app.route('/api/posts/feed', methods=['GET'])
@login_required
def get_feed():
    user_id = session['user_id']
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.*, u.username, u.real_name, u.profile_pic_url
        FROM posts p JOIN users u ON p.user_id = u.id
        WHERE p.privacy != 'only_me'
        AND (p.privacy = 'all' OR 
             (p.privacy = 'friends' AND EXISTS (
                 SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = p.user_id AND status = 'accepted'
             )))
        AND NOT EXISTS (
            SELECT 1 FROM blocks WHERE (blocker_id = ? AND blocked_id = p.user_id) OR (blocker_id = p.user_id AND blocked_id = ?)
        )
        ORDER BY p.timestamp DESC LIMIT ? OFFSET ?
    """, (user_id, user_id, user_id, per_page, offset))
    posts = [dict(row) for row in cursor.fetchall()]
    return jsonify(posts)

@app.route('/api/post/like', methods=['POST'])
@login_required
def like_post():
    data = request.json
    post_id = data.get('post_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    cursor.execute("SELECT * FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
    if cursor.fetchone():
        cursor.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        action = 'unliked'
    else:
        cursor.execute("INSERT INTO likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        notify(post['user_id'], 'like', from_user_id=user_id, post_id=post_id)
        action = 'liked'
    db.commit()
    return jsonify({'message': action})

@app.route('/api/post/comment', methods=['POST'])
@login_required
def add_comment():
    data = request.json
    post_id = data.get('post_id')
    text = data.get('text')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id, comments_enabled FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    if post['comments_enabled'] == 0:
        return jsonify({'error': 'Comments disabled'}), 403
    cursor.execute("INSERT INTO comments (user_id, post_id, text) VALUES (?, ?, ?)", (user_id, post_id, text))
    db.commit()
    notify(post['user_id'], 'comment', from_user_id=user_id, post_id=post_id, text=text)
    return jsonify({'message': 'Commented'})

@app.route('/api/post/comments/<int:post_id>', methods=['GET'])
@login_required
def get_comments(post_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT c.*, u.username, u.real_name, u.profile_pic_url 
        FROM comments c JOIN users u ON c.user_id = u.id 
        WHERE c.post_id = ? 
        ORDER BY c.timestamp DESC
    """, (post_id,))
    comments = [dict(row) for row in cursor.fetchall()]
    return jsonify(comments)

@app.route('/api/post/save', methods=['POST'])
@login_required
def save_post():
    data = request.json
    post_id = data.get('post_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM saves WHERE user_id = ? AND post_id = ?", (user_id, post_id))
    if cursor.fetchone():
        cursor.execute("DELETE FROM saves WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        action = 'unsaved'
    else:
        cursor.execute("INSERT INTO saves (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        action = 'saved'
    db.commit()
    return jsonify({'message': action})

@app.route('/api/post/repost', methods=['POST'])
@login_required
def repost_post():
    data = request.json
    post_id = data.get('post_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id, shares_enabled FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    if post['shares_enabled'] == 0:
        return jsonify({'error': 'Shares disabled'}), 403
    cursor.execute("SELECT * FROM reposts WHERE user_id = ? AND post_id = ?", (user_id, post_id))
    if cursor.fetchone():
        return jsonify({'error': 'Already reposted'}), 400
    cursor.execute("INSERT INTO reposts (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
    db.commit()
    notify(post['user_id'], 'repost', from_user_id=user_id, post_id=post_id)
    return jsonify({'message': 'Reposted'})

@app.route('/api/post/report', methods=['POST'])
@login_required
def report_post():
    data = request.json
    post_id = data.get('post_id')
    reason = data.get('reason')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM posts WHERE id = ?", (post_id,))
    if not cursor.fetchone():
        return jsonify({'error': 'Post not found'}), 404
    cursor.execute("INSERT INTO reports (reporter_id, target_type, target_id, reason) VALUES (?, 'post', ?, ?)", (user_id, post_id, reason))
    db.commit()
    return jsonify({'message': 'Reported'})

@app.route('/api/post/hide', methods=['POST'])
@login_required
def hide_post():
    data = request.json
    post_id = data.get('post_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    if post['user_id'] == user_id:
        return jsonify({'error': 'Cannot hide own post'}), 400
    cursor.execute("INSERT INTO blocks (blocker_id, blocked_id) VALUES (?, ?)", (user_id, post['user_id']))
    db.commit()
    return jsonify({'message': 'Hidden'})

@app.route('/api/post/subscribe', methods=['POST'])
@login_required
def subscribe_to_posts():
    data = request.json
    post_user_id = data.get('post_user_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM post_subscriptions WHERE user_id = ? AND post_user_id = ?", (user_id, post_user_id))
    if cursor.fetchone():
        cursor.execute("DELETE FROM post_subscriptions WHERE user_id = ? AND post_user_id = ?", (user_id, post_user_id))
        action = 'unsubscribed'
    else:
        cursor.execute("INSERT INTO post_subscriptions (user_id, post_user_id) VALUES (?, ?)", (user_id, post_user_id))
        action = 'subscribed'
    db.commit()
    return jsonify({'message': action})

@app.route('/api/block', methods=['POST'])
@login_required
def block_user():
    data = request.json
    target_id = data.get('target_id')
    user_id = session['user_id']
    if target_id == user_id:
        return jsonify({'error': 'Cannot block self'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM blocks WHERE blocker_id = ? AND blocked_id = ?", (user_id, target_id))
    if cursor.fetchone():
        return jsonify({'error': 'Already blocked'}), 400
    cursor.execute("INSERT INTO blocks (blocker_id, blocked_id) VALUES (?, ?)", (user_id, target_id))
    cursor.execute("DELETE FROM follows WHERE (follower_id = ? AND followed_id = ?) OR (follower_id = ? AND followed_id = ?)", (user_id, target_id, target_id, user_id))
    db.commit()
    return jsonify({'message': 'Blocked'})

@app.route('/api/follow/request', methods=['POST'])
@login_required
def follow_request():
    data = request.json
    target_id = data.get('target_id')
    user_id = session['user_id']
    if target_id == user_id:
        return jsonify({'error': 'Cannot follow self'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM blocks WHERE (blocker_id = ? AND blocked_id = ?) OR (blocker_id = ? AND blocked_id = ?)", (user_id, target_id, target_id, user_id))
    if cursor.fetchone():
        return jsonify({'error': 'Blocked'}), 403
    cursor.execute("SELECT * FROM follows WHERE follower_id = ? AND followed_id = ?", (user_id, target_id))
    if cursor.fetchone():
        return jsonify({'error': 'Already following or requested'}), 400
    cursor.execute("SELECT profile_locked FROM users WHERE id = ?", (target_id,))
    status = 'accepted' if cursor.fetchone()['profile_locked'] == 0 else 'pending'
    cursor.execute("INSERT INTO follows (follower_id, followed_id, status) VALUES (?, ?, ?)", (user_id, target_id, status))
    db.commit()
    if status == 'pending':
        notify(target_id, 'follow_request', from_user_id=user_id)
    else:
        notify(target_id, 'follow', from_user_id=user_id)
    return jsonify({'message': 'Follow requested'})

@app.route('/api/follow/accept', methods=['POST'])
@login_required
def accept_follow():
    data = request.json
    follower_id = data.get('follower_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM follows WHERE follower_id = ? AND followed_id = ? AND status = 'pending'", (follower_id, user_id))
    if not cursor.fetchone():
        return jsonify({'error': 'No pending request'}), 400
    cursor.execute("UPDATE follows SET status = 'accepted' WHERE follower_id = ? AND followed_id = ?", (follower_id, user_id))
    db.commit()
    notify(follower_id, 'follow_accepted', from_user_id=user_id)
    return jsonify({'message': 'Accepted'})

@app.route('/api/messages/<int:chat_id>', methods=['GET'])
@login_required
def get_messages(chat_id):
    user_id = session['user_id']
    is_group = request.args.get('is_group', '0') == '1'
    db = get_db()
    cursor = db.cursor()
    if is_group:
        cursor.execute("SELECT is_admin FROM group_members WHERE group_id = ? AND user_id = ?", (chat_id, user_id))
        member = cursor.fetchone()
        if not member:
            return jsonify({'error': 'Not member'}), 403
        cursor.execute("SELECT allow_messages_nonadmin FROM group_permissions WHERE group_id = ?", (chat_id,))
        perm = cursor.fetchone()
        if not perm:
            cursor.execute("INSERT INTO group_permissions (group_id) VALUES (?)", (chat_id,))
            perm = {'allow_messages_nonadmin': 1}
        if member['is_admin'] == 0 and perm['allow_messages_nonadmin'] == 0:
            return jsonify({'error': 'Cannot view messages'}), 403
    else:
        cursor.execute("SELECT * FROM blocks WHERE (blocker_id = ? AND blocked_id = ?) OR (blocker_id = ? AND blocked_id = ?)", (user_id, chat_id, chat_id, user_id))
        if cursor.fetchone():
            return jsonify({'error': 'Blocked'}), 403
    cursor.execute("""
        SELECT m.*, u.username, u.real_name, u.profile_pic_url 
        FROM messages m 
        JOIN users u ON m.sender_id = u.id 
        WHERE (m.is_group = ? AND m.receiver_id = ?) 
        OR (m.is_group = 0 AND ((m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?))) 
        ORDER BY m.timestamp DESC LIMIT 50
    """, (is_group, chat_id, user_id, chat_id, chat_id, user_id))
    messages = [dict(row) for row in cursor.fetchall()]
    cursor.execute("UPDATE messages SET read = 1 WHERE receiver_id = ? AND sender_id = ? AND is_group = 0 AND read = 0", (user_id, chat_id))
    db.commit()
    return jsonify(messages)

@app.route('/api/message/send', methods=['POST'])
@login_required
def send_message():
    data = request.json
    receiver_id = data.get('receiver_id')
    is_group = data.get('is_group', False)
    text = data.get('text')
    media_url = data.get('media_url')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    if is_group:
        cursor.execute("SELECT is_admin FROM group_members WHERE group_id = ? AND user_id = ?", (receiver_id, user_id))
        member = cursor.fetchone()
        if not member:
            return jsonify({'error': 'Not member'}), 403
        cursor.execute("SELECT allow_messages_nonadmin FROM group_permissions WHERE group_id = ?", (receiver_id,))
        perm = cursor.fetchone()
        if not perm:
            cursor.execute("INSERT INTO group_permissions (group_id) VALUES (?)", (receiver_id,))
            perm = {'allow_messages_nonadmin': 1}
        if member['is_admin'] == 0 and perm['allow_messages_nonadmin'] == 0:
            return jsonify({'error': 'Cannot send messages'}), 403
    else:
        cursor.execute("SELECT * FROM blocks WHERE (blocker_id = ? AND blocked_id = ?) OR (blocker_id = ? AND blocked_id = ?)", (user_id, receiver_id, receiver_id, user_id))
        if cursor.fetchone():
            return jsonify({'error': 'Blocked'}), 403
    cursor.execute("INSERT INTO messages (sender_id, receiver_id, is_group, text, media_url) VALUES (?, ?, ?, ?, ?)", (user_id, receiver_id, is_group, text, media_url))
    db.commit()
    cursor.execute("SELECT last_insert_rowid() as id")
    msg_id = cursor.fetchone()['id']
    if is_group:
        cursor.execute("SELECT user_id FROM group_members WHERE group_id = ? AND user_id != ? AND status = 'accepted'", (receiver_id, user_id))
        recipients = [row['user_id'] for row in cursor.fetchall()]
        for r in recipients:
            notify(r, 'group_message', from_user_id=user_id, group_id=receiver_id, text=text)
    else:
        notify(receiver_id, 'message', from_user_id=user_id, text=text)
    return jsonify({'message': 'Sent', 'msg_id': msg_id})

@app.route('/api/inbox', methods=['GET'])
@login_required
def get_inbox():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT DISTINCT CASE WHEN m.sender_id = ? THEN m.receiver_id ELSE m.sender_id END as chat_user_id, m.is_group
        FROM messages m
        WHERE (m.sender_id = ? OR m.receiver_id = ?)
        ORDER BY (SELECT MAX(timestamp) FROM messages WHERE ((sender_id = ? AND receiver_id = chat_user_id AND is_group = m.is_group) OR (sender_id = chat_user_id AND receiver_id = ? AND is_group = m.is_group))) DESC
    """, (user_id, user_id, user_id, user_id, user_id))
    chats = []
    for row in cursor.fetchall():
        chat_id = row['chat_user_id']
        is_group = row['is_group']
        if is_group:
            cursor.execute("SELECT id, name as username, profile_pic_url FROM groups WHERE id = ?", (chat_id,))
        else:
            cursor.execute("SELECT id, username, real_name, profile_pic_url FROM users WHERE id = ?", (chat_id,))
        chat_info = cursor.fetchone()
        if not chat_info:
            continue
        chat = dict(chat_info)
        chat['is_group'] = is_group
        cursor.execute("""
            SELECT text, timestamp 
            FROM messages 
            WHERE ((sender_id = ? AND receiver_id = ? AND is_group = ?) OR (sender_id = ? AND receiver_id = ? AND is_group = ?)) 
            ORDER BY timestamp DESC LIMIT 1
        """, (user_id, chat_id, is_group, chat_id, user_id, is_group))
        last_msg = cursor.fetchone()
        chat['last_message'] = last_msg['text'] if last_msg else ''
        chat['last_timestamp'] = last_msg['timestamp'] if last_msg else ''
        cursor.execute("SELECT COUNT(*) as unread FROM messages WHERE sender_id = ? AND receiver_id = ? AND is_group = ? AND read = 0", (chat_id, user_id, is_group))
        chat['unread'] = cursor.fetchone()['unread']
        chats.append(chat)
    return jsonify(chats)

@app.route('/api/stories', methods=['GET'])
@login_required
def get_stories():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.*, u.username, u.real_name, u.profile_pic_url
        FROM posts p 
        JOIN users u ON p.user_id = u.id
        WHERE p.type = 'story' AND p.timestamp > ? 
        AND (p.privacy = 'all' OR 
             (p.privacy = 'friends' AND EXISTS (
                 SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = p.user_id AND status = 'accepted'
             )) OR p.user_id = ?)
        AND NOT EXISTS (
            SELECT 1 FROM blocks WHERE (blocker_id = ? AND blocked_id = p.user_id) OR (blocker_id = p.user_id AND blocked_id = ?)
        )
        ORDER BY p.timestamp DESC
    """, ((datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S'), user_id, user_id, user_id, user_id))
    stories = [dict(row) for row in cursor.fetchall()]
    return jsonify(stories)

@app.route('/api/reels', methods=['GET'])
@login_required
def get_reels():
    user_id = session['user_id']
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.*, u.username, u.real_name, u.profile_pic_url
        FROM posts p 
        JOIN users u ON p.user_id = u.id
        WHERE p.type = 'reel' 
        AND (p.privacy = 'all' OR 
             (p.privacy = 'friends' AND EXISTS (
                 SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = p.user_id AND status = 'accepted'
             )) OR p.user_id = ?)
        AND NOT EXISTS (
            SELECT 1 FROM blocks WHERE (blocker_id = ? AND blocked_id = p.user_id) OR (blocker_id = p.user_id AND blocked_id = ?)
        )
        ORDER BY p.timestamp DESC LIMIT ? OFFSET ?
    """, (user_id, user_id, user_id, user_id, per_page, offset))
    reels = [dict(row) for row in cursor.fetchall()]
    return jsonify(reels)

@app.route('/api/group/create', methods=['POST'])
@login_required
def create_group():
    data = request.json
    name = data.get('name')
    description = data.get('description')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    link = generate_group_link()
    cursor.execute("INSERT INTO groups (name, creator_id, description, link) VALUES (?, ?, ?, ?)", (name, user_id, description, link))
    group_id = cursor.lastrowid
    cursor.execute("INSERT INTO group_members (group_id, user_id, is_admin) VALUES (?, ?, 1)", (group_id, user_id))
    cursor.execute("INSERT INTO group_permissions (group_id) VALUES (?)", (group_id,))
    db.commit()
    return jsonify({'message': 'Group created', 'group_id': group_id})

@app.route('/api/group/edit', methods=['POST'])
@login_required
def edit_group():
    data = request.json
    group_id = data.get('group_id')
    name = data.get('name')
    description = data.get('description')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT is_admin FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
    member = cursor.fetchone()
    if not member:
        return jsonify({'error': 'Not member'}), 403
    cursor.execute("SELECT allow_edit_nonadmin FROM group_permissions WHERE group_id = ?", (group_id,))
    perm = cursor.fetchone()
    if not perm:
        cursor.execute("INSERT INTO group_permissions (group_id) VALUES (?)", (group_id,))
        perm = {'allow_edit_nonadmin': 0}
    if member['is_admin'] == 0 and perm['allow_edit_nonadmin'] == 0:
        return jsonify({'error': 'Not allowed'}), 403
    cursor.execute("UPDATE groups SET name = ?, description = ? WHERE id = ?", (name, description, group_id))
    db.commit()
    return jsonify({'message': 'Group updated'})

if __name__ == '__main__':
    app.run(debug=True)
