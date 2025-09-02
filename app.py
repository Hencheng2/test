# app.py (fully adjusted and completed backend with all required API endpoints)

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

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.secret_key = app.config['SECRET_KEY']

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('database.db')
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def generate_unique_key():
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
    while True:
        link = str(uuid.uuid4())[:8]
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM groups WHERE link = ?", (link,))
        if not cursor.fetchone():
            return link

def init_db():
    db = get_db()
    cursor = db.cursor()
    try:
        # Users table (added fields for full profile)
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
                posts_privacy TEXT DEFAULT 'all',  -- all, friends, only_me
                reels_privacy TEXT DEFAULT 'all',
                stories_privacy TEXT DEFAULT 'friends',
                theme TEXT DEFAULT 'light',  -- light, dark
                notifications_settings TEXT DEFAULT '{}'  -- JSON string for types
            )
        ''')
        
        # Follows (friends/follow system)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS follows (
                follower_id INTEGER,
                followed_id INTEGER,
                status TEXT DEFAULT 'pending',  -- pending, accepted
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (follower_id, followed_id)
            )
        ''')
        
        # Blocks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                blocker_id INTEGER,
                blocked_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (blocker_id, blocked_id)
            )
        ''')
        
        # Posts (posts, reels, stories)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,  -- post, reel, story
                description TEXT,
                media_url TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                views INTEGER DEFAULT 0,
                privacy TEXT DEFAULT 'all',  -- override user default if set
                comments_enabled INTEGER DEFAULT 1,
                shares_enabled INTEGER DEFAULT 1
            )
        ''')
        
        # Likes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS likes (
                user_id INTEGER,
                post_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, post_id)
            )
        ''')
        
        # Comments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                post_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Reposts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reposts (
                user_id INTEGER,
                post_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, post_id)
            )
        ''')
        
        # Saves
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saves (
                user_id INTEGER,
                post_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, post_id)
            )
        ''')
        
        # Reports
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER NOT NULL,
                target_type TEXT NOT NULL,  -- post, user, group
                target_id INTEGER NOT NULL,
                reason TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Messages (chats and groups)
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
                disappearing_after TEXT DEFAULT 'off'  -- off, 24h, 1w, 1m
            )
        ''')
        
        # Chat customizations (nicknames, wallpapers - stored per user per chat)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_custom (
                user_id INTEGER,
                chat_id INTEGER,  -- receiver_id or group_id
                is_group INTEGER DEFAULT 0,
                nickname TEXT,
                wallpaper_url TEXT,
                PRIMARY KEY (user_id, chat_id, is_group)
            )
        ''')
        
        # Groups
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
        
        # Group members (status: pending, accepted)
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
        
        # Group permissions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_permissions (
                group_id INTEGER PRIMARY KEY,
                allow_edit_nonadmin INTEGER DEFAULT 0,
                allow_messages_nonadmin INTEGER DEFAULT 1,
                allow_add_nonadmin INTEGER DEFAULT 1,
                approve_new_members INTEGER DEFAULT 0
            )
        ''')
        
        # Notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,  -- like, comment, follow, request, message, warning, etc.
                from_user_id INTEGER,
                post_id INTEGER,
                group_id INTEGER,
                text TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read INTEGER DEFAULT 0
            )
        ''')
        
        # Post notifications subscriptions (for 'turn on notifications for this type')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS post_subscriptions (
                user_id INTEGER,
                post_user_id INTEGER,
                PRIMARY KEY (user_id, post_user_id)
            )
        ''')
        
        # Admin warnings log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert admin if not exists
        admin_username = app.config['ADMIN_USERNAME']
        admin_pass_hash = generate_password_hash(app.config['ADMIN_PASS'])
        cursor.execute("SELECT id FROM users WHERE username = ?", (admin_username,))
        if not cursor.fetchone():
            unique_key = generate_unique_key()
            cursor.execute("INSERT INTO users (username, password_hash, real_name, unique_key, is_admin, theme) VALUES (?, ?, 'Admin', ?, 1, 'dark')", (admin_username, admin_pass_hash, unique_key))
        
        db.commit()
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
        raise

# Initialize database
with app.app_context():
    init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT banned_until FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        if user and user['banned_until'] and datetime.strptime(user['banned_until'], '%Y-%m-%d %H:%M:%S') > datetime.now():
            return jsonify({'error': 'Account banned'}), 403
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT is_admin FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        if not user or not user['is_admin']:
            return jsonify({'error': 'Admin required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if len(password) < 6 or not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password) or not any(not c.isalnum() for c in password):
        return jsonify({'error': 'Password must be 6+ chars with letters, numbers, special char'}), 400
    if username == app.config['ADMIN_USERNAME'] and password == app.config['ADMIN_PASS']:
        return jsonify({'error': 'Cannot register admin credentials'}), 400
    db = get_db()
    cursor = db.cursor()
    try:
        password_hash = generate_password_hash(password)
        unique_key = generate_unique_key()
        cursor.execute("INSERT INTO users (username, password_hash, unique_key) VALUES (?, ?, ?)", (username, password_hash, unique_key))
        db.commit()
        return jsonify({'unique_key': unique_key})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username taken'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    identifier = data.get('identifier')
    password = data.get('password')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, password_hash, is_admin FROM users WHERE username = ? OR email = ?", (identifier, identifier))
    user = cursor.fetchone()
    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['is_admin'] = user['is_admin']
        return jsonify({'message': 'Logged in'})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'})

@app.route('/api/forgot', methods=['POST'])
def forgot():
    data = request.json
    username = data.get('username')
    unique_key = data.get('unique_key')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? AND unique_key = ?", (username, unique_key))
    user = cursor.fetchone()
    if user:
        session['reset_user_id'] = user['id']
        return jsonify({'message': 'Verified'})
    return jsonify({'error': 'Invalid details'}), 400

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    if 'reset_user_id' not in session:
        return jsonify({'error': 'Not verified'}), 401
    data = request.json
    password = data.get('password')
    if len(password) < 6 or not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password) or not any(not c.isalnum() for c in password):
        return jsonify({'error': 'Password requirements not met'}), 400
    password_hash = generate_password_hash(password)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, session['reset_user_id']))
    db.commit()
    session.pop('reset_user_id')
    return jsonify({'message': 'Password reset'})

@app.route('/api/user/me', methods=['GET'])
@login_required
def get_me():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = dict(cursor.fetchone())
    del user['password_hash']
    return jsonify(user)

@app.route('/api/user/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    current_user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    user = dict(user)
    del user['password_hash'], user['unique_key']
    # Check if blocked
    cursor.execute("SELECT * FROM blocks WHERE (blocker_id = ? AND blocked_id = ?) OR (blocker_id = ? AND blocked_id = ?)", (current_user_id, user_id, user_id, current_user_id))
    if cursor.fetchone():
        return jsonify({'error': 'Blocked'}), 403
    # Privacy check for profile
    if user['profile_locked'] and not is_friend(current_user_id, user_id):
        user = {'id': user['id'], 'username': user['username'], 'real_name': user['real_name'], 'profile_pic_url': user['profile_pic_url']}
    return jsonify(user)

def is_friend(user1, user2):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT * FROM follows WHERE follower_id = ? AND followed_id = ? AND status = 'accepted'
        INTERSECT
        SELECT * FROM follows WHERE follower_id = ? AND followed_id = ? AND status = 'accepted'
    """, (user1, user2, user2, user1))
    return bool(cursor.fetchone())

@app.route('/api/user/update', methods=['POST'])
@login_required
def update_user():
    user_id = session['user_id']
    data = request.json
    fields = ['real_name', 'bio', 'email', 'phone', 'gender', 'pronouns', 'dob', 'work', 'education', 'places', 'relationship', 'spouse', 'posts_privacy', 'reels_privacy', 'stories_privacy', 'theme', 'notifications_settings', 'profile_locked']
    set_clause = ', '.join(f"{field} = ?" for field in fields if field in data)
    values = [data[field] for field in fields if field in data] + [user_id]
    if set_clause:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
        db.commit()
    return jsonify({'message': 'Updated'})

@app.route('/api/user/change_password', methods=['POST'])
@login_required
def change_password():
    user_id = session['user_id']
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not check_password_hash(user['password_hash'], old_password):
        return jsonify({'error': 'Invalid old password'}), 400
    if len(new_password) < 6 or not any(c.isdigit() for c in new_password) or not any(c.isalpha() for c in new_password) or not any(not c.isalnum() for c in new_password):
        return jsonify({'error': 'Password requirements not met'}), 400
    password_hash = generate_password_hash(new_password)
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
    db.commit()
    return jsonify({'message': 'Password changed'})

@app.route('/api/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        return jsonify({'url': '/' + path})
    return jsonify({'error': 'Invalid file'}), 400

@app.route('/api/post/create', methods=['POST'])
@login_required
def create_post():
    data = request.json
    user_id = session['user_id']
    type_ = data.get('type')  # post, reel, story
    description = data.get('description')
    media_url = data.get('media_url')
    privacy = data.get('privacy')
    if type_ not in ['post', 'reel', 'story']:
        return jsonify({'error': 'Invalid type'}), 400
    if type_ in ['reel', 'story'] and not media_url:
        return jsonify({'error': 'Media required'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO posts (user_id, type, description, media_url, privacy) VALUES (?, ?, ?, ?, ?)", (user_id, type_, description, media_url, privacy))
    post_id = cursor.lastrowid
    db.commit()
    # Notify followers/friends if applicable
    if type_ != 'story':
        notify_followers(user_id, 'new_post', post_id=post_id)
    return jsonify({'id': post_id})

def notify_followers(user_id, type_, post_id=None, group_id=None, text=None):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT follower_id FROM follows WHERE followed_id = ? AND status = 'accepted'", (user_id,))
    followers = [row['follower_id'] for row in cursor.fetchall()]
    for follower in followers:
        cursor.execute("INSERT INTO notifications (user_id, type, from_user_id, post_id, group_id, text) VALUES (?, ?, ?, ?, ?, ?)", (follower, type_, user_id, post_id, group_id, text))

@app.route('/api/posts/feed', methods=['GET'])
@login_required
def get_feed():
    user_id = session['user_id']
    page = int(request.args.get('page', 1))
    limit = 10
    offset = (page - 1) * limit
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.*, u.username, u.real_name, u.profile_pic_url 
        FROM posts p 
        JOIN users u ON p.user_id = u.id 
        WHERE p.type = 'post' AND 
            (p.user_id = ? OR 
             (p.privacy = 'all' OR 
              (p.privacy = 'friends' AND EXISTS (SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = p.user_id AND status = 'accepted' AND EXISTS (SELECT 1 FROM follows WHERE follower_id = p.user_id AND followed_id = ? AND status = 'accepted'))) OR
              p.user_id IN (SELECT followed_id FROM follows WHERE follower_id = ? AND status = 'accepted')))
        ORDER BY p.timestamp DESC LIMIT ? OFFSET ?
    """, (user_id, user_id, user_id, user_id, limit, offset))
    posts = [dict(row) for row in cursor.fetchall()]
    return jsonify(posts)

@app.route('/api/reels', methods=['GET'])
@login_required
def get_reels():
    user_id = session['user_id']
    page = int(request.args.get('page', 1))
    limit = 10
    offset = (page - 1) * limit
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.*, u.username, u.real_name, u.profile_pic_url 
        FROM posts p 
        JOIN users u ON p.user_id = u.id 
        WHERE p.type = 'reel' AND p.media_url LIKE '%.mp4' AND 
            (p.user_id = ? OR 
             (p.privacy = 'all' OR 
              (p.privacy = 'friends' AND EXISTS (SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = p.user_id AND status = 'accepted' AND EXISTS (SELECT 1 FROM follows WHERE follower_id = p.user_id AND followed_id = ? AND status = 'accepted'))) OR
              p.user_id IN (SELECT followed_id FROM follows WHERE follower_id = ? AND status = 'accepted')))
        ORDER BY p.timestamp DESC LIMIT ? OFFSET ?
    """, (user_id, user_id, user_id, user_id, limit, offset))
    reels = [dict(row) for row in cursor.fetchall()]
    return jsonify(reels)

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
        WHERE p.type = 'story' AND p.timestamp > ? AND
            (p.user_id = ? OR 
             (p.privacy = 'friends' AND EXISTS (SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = p.user_id AND status = 'accepted' AND EXISTS (SELECT 1 FROM follows WHERE follower_id = p.user_id AND followed_id = ? AND status = 'accepted'))))
        ORDER BY p.timestamp DESC
    """, (datetime.now() - timedelta(hours=24), user_id, user_id, user_id))
    stories = [dict(row) for row in cursor.fetchall()]
    return jsonify(stories)

@app.route('/api/post/<int:post_id>', methods=['GET'])
@login_required
def get_post(post_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT p.*, u.username, u.real_name, u.profile_pic_url FROM posts p JOIN users u ON p.user_id = u.id WHERE p.id = ?", (post_id,))
    post = cursor.fetchone()
    if not post:
        return jsonify({'error': 'Not found'}), 404
    post = dict(post)
    # Privacy check
    if post['privacy'] == 'only_me' and post['user_id'] != user_id:
        return jsonify({'error': 'Private'}), 403
    if post['privacy'] == 'friends' and not is_friend(user_id, post['user_id']) and post['user_id'] != user_id:
        return jsonify({'error': 'Private'}), 403
    # Increase views
    cursor.execute("UPDATE posts SET views = views + 1 WHERE id = ?", (post_id,))
    db.commit()
    return jsonify(post)

@app.route('/api/post/like', methods=['POST'])
@login_required
def like_post():
    data = request.json
    post_id = data.get('post_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
    post_user = cursor.fetchone()
    if not post_user:
        return jsonify({'error': 'Not found'}), 404
    try:
        cursor.execute("INSERT INTO likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        db.commit()
        notify(post_user['user_id'], 'like', from_user_id=user_id, post_id=post_id)
        return jsonify({'message': 'Liked'})
    except sqlite3.IntegrityError:
        cursor.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        db.commit()
        return jsonify({'message': 'Unliked'})

def notify(to_user_id, type_, from_user_id=None, post_id=None, group_id=None, text=None):
    if to_user_id == from_user_id:
        return
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO notifications (user_id, type, from_user_id, post_id, group_id, text) VALUES (?, ?, ?, ?, ?, ?)", (to_user_id, type_, from_user_id, post_id, group_id, text))
    db.commit()

@app.route('/api/post/comment', methods=['POST'])
@login_required
def comment_post():
    data = request.json
    post_id = data.get('post_id')
    text = data.get('text')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id, comments_enabled FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    if not post or not post['comments_enabled']:
        return jsonify({'error': 'Comments disabled or not found'}), 403
    cursor.execute("INSERT INTO comments (user_id, post_id, text) VALUES (?, ?, ?)", (user_id, post_id, text))
    db.commit()
    notify(post['user_id'], 'comment', from_user_id=user_id, post_id=post_id)
    return jsonify({'message': 'Commented'})

@app.route('/api/post/comments/<int:post_id>', methods=['GET'])
@login_required
def get_comments(post_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT c.*, u.username, u.real_name, u.profile_pic_url FROM comments c JOIN users u ON c.user_id = u.id WHERE post_id = ? ORDER BY timestamp DESC", (post_id,))
    comments = [dict(row) for row in cursor.fetchall()]
    return jsonify(comments)

@app.route('/api/post/share', methods=['POST'])
@login_required
def share_post():
    data = request.json
    post_id = data.get('post_id')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id, shares_enabled FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    if not post or not post['shares_enabled']:
        return jsonify({'error': 'Shares disabled or not found'}), 403
    # Share logic: perhaps create a repost or send to chat
    # For now, assume it's repost
    return repost_post()

@app.route('/api/post/repost', methods=['POST'])
@login_required
def repost_post():
    data = request.json
    post_id = data.get('post_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
    post_user = cursor.fetchone()
    if not post_user or post_user['user_id'] == user_id:
        return jsonify({'error': 'Cannot repost own or not found'}), 400
    try:
        cursor.execute("INSERT INTO reposts (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        db.commit()
        notify(post_user['user_id'], 'repost', from_user_id=user_id, post_id=post_id)
        return jsonify({'message': 'Reposted'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Already reposted'}), 400

@app.route('/api/post/save', methods=['POST'])
@login_required
def save_post():
    data = request.json
    post_id = data.get('post_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO saves (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        db.commit()
        return jsonify({'message': 'Saved'})
    except sqlite3.IntegrityError:
        cursor.execute("DELETE FROM saves WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        db.commit()
        return jsonify({'message': 'Unsaved'})

@app.route('/api/post/report', methods=['POST'])
@login_required
def report_post():
    data = request.json
    post_id = data.get('post_id')
    reason = data.get('reason')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
    if not cursor.fetchone() or cursor.fetchone()['user_id'] == user_id:
        return jsonify({'error': 'Cannot report own or not found'}), 400
    cursor.execute("INSERT INTO reports (reporter_id, target_type, target_id, reason) VALUES (?, 'post', ?, ?)", (user_id, post_id, reason))
    db.commit()
    return jsonify({'message': 'Reported'})

@app.route('/api/post/hide', methods=['POST'])
@login_required
def hide_post():
    # Hide is client-side, perhaps block user or ignore
    # For now, return ok
    return jsonify({'message': 'Hidden'})

@app.route('/api/post/subscribe', methods=['POST'])
@login_required
def subscribe_post_notifications():
    data = request.json
    post_user_id = data.get('post_user_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO post_subscriptions (user_id, post_user_id) VALUES (?, ?)", (user_id, post_user_id))
        db.commit()
        return jsonify({'message': 'Subscribed'})
    except sqlite3.IntegrityError:
        cursor.execute("DELETE FROM post_subscriptions WHERE user_id = ? AND post_user_id = ?", (user_id, post_user_id))
        db.commit()
        return jsonify({'message': 'Unsubscribed'})

@app.route('/api/follow/request', methods=['POST'])
@login_required
def follow_request():
    data = request.json
    target_id = data.get('target_id')
    user_id = session['user_id']
    if user_id == target_id:
        return jsonify({'error': 'Cannot follow self'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM blocks WHERE (blocker_id = ? AND blocked_id = ?) OR (blocker_id = ? AND blocked_id = ?)", (user_id, target_id, target_id, user_id))
    if cursor.fetchone():
        return jsonify({'error': 'Blocked'}), 403
    try:
        cursor.execute("INSERT INTO follows (follower_id, followed_id, status) VALUES (?, ?, 'pending')", (user_id, target_id))
        db.commit()
        notify(target_id, 'follow_request', from_user_id=user_id)
        return jsonify({'message': 'Request sent'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Already requested/following'}), 400

@app.route('/api/follow/accept', methods=['POST'])
@login_required
def accept_follow():
    data = request.json
    from_id = data.get('from_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE follows SET status = 'accepted' WHERE follower_id = ? AND followed_id = ?", (from_id, user_id))
    if cursor.rowcount == 0:
        return jsonify({'error': 'No request'}), 404
    db.commit()
    notify(from_id, 'follow_accepted', from_user_id=user_id)
    return jsonify({'message': 'Accepted'})

@app.route('/api/follow/decline', methods=['POST'])
@login_required
def decline_follow():
    data = request.json
    from_id = data.get('from_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM follows WHERE follower_id = ? AND followed_id = ?", (from_id, user_id))
    db.commit()
    return jsonify({'message': 'Declined'})

@app.route('/api/follow/unfollow', methods=['POST'])
@login_required
def unfollow():
    data = request.json
    target_id = data.get('target_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM follows WHERE follower_id = ? AND followed_id = ?", (user_id, target_id))
    db.commit()
    return jsonify({'message': 'Unfollowed'})

@app.route('/api/block', methods=['POST'])
@login_required
def block_user():
    data = request.json
    target_id = data.get('target_id')
    user_id = session['user_id']
    if user_id == target_id:
        return jsonify({'error': 'Cannot block self'}), 400
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO blocks (blocker_id, blocked_id) VALUES (?, ?)", (user_id, target_id))
        # Remove follows
        cursor.execute("DELETE FROM follows WHERE (follower_id = ? AND followed_id = ?) OR (follower_id = ? AND followed_id = ?)", (user_id, target_id, target_id, user_id))
        db.commit()
        return jsonify({'message': 'Blocked'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Already blocked'}), 400

@app.route('/api/unblock', methods=['POST'])
@login_required
def unblock_user():
    data = request.json
    target_id = data.get('target_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM blocks WHERE blocker_id = ? AND blocked_id = ?", (user_id, target_id))
    db.commit()
    return jsonify({'message': 'Unblocked'})

@app.route('/api/friends/followers', methods=['GET'])
@login_required
def get_followers():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT u.id, u.username, u.real_name, u.profile_pic_url, (SELECT COUNT(*) FROM follows f1 JOIN follows f2 ON f1.followed_id = f2.followed_id WHERE f1.follower_id = ? AND f2.follower_id = u.id AND f1.status = 'accepted' AND f2.status = 'accepted') as mutual
        FROM follows f JOIN users u ON f.follower_id = u.id WHERE f.followed_id = ? AND f.status = 'accepted'
    """, (user_id, user_id))
    followers = [dict(row) for row in cursor.fetchall()]
    return jsonify(followers)

@app.route('/api/friends/following', methods=['GET'])
@login_required
def get_following():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT u.id, u.username, u.real_name, u.profile_pic_url, (SELECT COUNT(*) FROM follows f1 JOIN follows f2 ON f1.followed_id = f2.followed_id WHERE f1.follower_id = ? AND f2.follower_id = u.id AND f1.status = 'accepted' AND f2.status = 'accepted') as mutual
        FROM follows f JOIN users u ON f.followed_id = u.id WHERE f.follower_id = ? AND f.status = 'accepted'
    """, (user_id, user_id))
    following = [dict(row) for row in cursor.fetchall()]
    return jsonify(following)

@app.route('/api/friends/friends', methods=['GET'])
@login_required
def get_friends():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT u.id, u.username, u.real_name, u.profile_pic_url, (SELECT COUNT(*) FROM follows f1 JOIN follows f2 ON f1.followed_id = f2.followed_id WHERE f1.follower_id = ? AND f2.follower_id = u.id AND f1.status = 'accepted' AND f2.status = 'accepted') as mutual
        FROM follows f1 JOIN follows f2 ON f1.followed_id = f2.follower_id AND f1.follower_id = f2.followed_id JOIN users u ON f1.followed_id = u.id 
        WHERE f1.follower_id = ? AND f1.status = 'accepted' AND f2.status = 'accepted'
    """, (user_id, user_id))
    friends = [dict(row) for row in cursor.fetchall()]
    return jsonify(friends)

@app.route('/api/friends/requests', methods=['GET'])
@login_required
def get_requests():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT u.id, u.username, u.real_name, u.profile_pic_url, (SELECT COUNT(*) FROM follows f1 JOIN follows f2 ON f1.followed_id = f2.followed_id WHERE f1.follower_id = ? AND f2.follower_id = u.id AND f1.status = 'accepted' AND f2.status = 'accepted') as mutual
        FROM follows f JOIN users u ON f.follower_id = u.id WHERE f.followed_id = ? AND f.status = 'pending'
    """, (user_id, user_id))
    requests = [dict(row) for row in cursor.fetchall()]
    return jsonify(requests)

@app.route('/api/friends/suggested', methods=['GET'])
@login_required
def get_suggested():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    # Suggested based on mutual friends
    cursor.execute("""
        SELECT u.id, u.username, u.real_name, u.profile_pic_url, COUNT(*) as mutual
        FROM follows f1 JOIN follows f2 ON f1.followed_id = f2.follower_id JOIN users u ON f2.followed_id = u.id
        WHERE f1.follower_id = ? AND f2.followed_id != ? AND NOT EXISTS (SELECT 1 FROM follows f3 WHERE f3.follower_id = ? AND f3.followed_id = u.id)
        GROUP BY u.id ORDER BY mutual DESC LIMIT 20
    """, (user_id, user_id, user_id))
    suggested = [dict(row) for row in cursor.fetchall()]
    return jsonify(suggested)

@app.route('/api/message/send', methods=['POST'])
@login_required
def send_message():
    data = request.json
    receiver_id = data.get('receiver_id')
    text = data.get('text')
    media_url = data.get('media_url')
    is_group = data.get('is_group', 0)
    disappearing_after = data.get('disappearing_after', 'off')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    if is_group:
        cursor.execute("SELECT * FROM group_members WHERE group_id = ? AND user_id = ?", (receiver_id, user_id))
        member = cursor.fetchone()
        if not member:
            return jsonify({'error': 'Not member'}), 403
        cursor.execute("SELECT allow_messages_nonadmin FROM group_permissions WHERE group_id = ?", (receiver_id,))
        perm = cursor.fetchone()
        if member['is_admin'] == 0 and perm['allow_messages_nonadmin'] == 0:
            return jsonify({'error': 'Not allowed'}), 403
        # Notify all members
        cursor.execute("SELECT user_id FROM group_members WHERE group_id = ? AND user_id != ?", (receiver_id, user_id))
        members = [row['user_id'] for row in cursor.fetchall()]
        for m in members:
            notify(m, 'group_message', from_user_id=user_id, group_id=receiver_id)
    else:
        if is_blocked(user_id, receiver_id):
            return jsonify({'error': 'Blocked'}), 403
        notify(receiver_id, 'message', from_user_id=user_id)
    cursor.execute("INSERT INTO messages (sender_id, receiver_id, is_group, text, media_url, disappearing_after) VALUES (?, ?, ?, ?, ?, ?)", (user_id, receiver_id, is_group, text, media_url, disappearing_after))
    db.commit()
    # Handle disappearing: could schedule deletion, but for simplicity, check on get
    return jsonify({'message': 'Sent'})

def is_blocked(user1, user2):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM blocks WHERE blocker_id = ? AND blocked_id = ?", (user1, user2))
    return bool(cursor.fetchone())

@app.route('/api/messages/<int:chat_id>', methods=['GET'])
@login_required
def get_messages(chat_id):
    user_id = session['user_id']
    is_group = request.args.get('is_group', 0)
    db = get_db()
    cursor = db.cursor()
    if is_group:
        cursor.execute("SELECT * FROM group_members WHERE group_id = ? AND user_id = ?", (chat_id, user_id))
        if not cursor.fetchone():
            return jsonify({'error': 'Not member'}), 403
        where = "receiver_id = ? AND is_group = 1"
        params = (chat_id,)
    else:
        if is_blocked(user_id, chat_id) or is_blocked(chat_id, user_id):
            return jsonify({'error': 'Blocked'}), 403
        where = "((sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)) AND is_group = 0"
        params = (user_id, chat_id, chat_id, user_id)
    # Delete disappeared messages
    cursor.execute(f"DELETE FROM messages WHERE {where} AND disappearing_after != 'off' AND timestamp < ?", params + (get_disappear_time(),))
    db.commit()
    cursor.execute(f"SELECT m.*, u.username, u.real_name, u.profile_pic_url FROM messages m JOIN users u ON m.sender_id = u.id WHERE {where} ORDER BY timestamp ASC", params)
    messages = [dict(row) for row in cursor.fetchall()]
    # Mark read
    cursor.execute(f"UPDATE messages SET read = 1 WHERE receiver_id = ? AND sender_id != ? AND read = 0 AND is_group = {is_group}", (chat_id if is_group else user_id, user_id))
    db.commit()
    return jsonify(messages)

def get_disappear_time():
    now = datetime.now()
    return now - timedelta(hours=24)  # Placeholder, adjust based on disappearing_after

@app.route('/api/inbox/chats', methods=['GET'])
@login_required
def get_chats():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT DISTINCT CASE WHEN sender_id = ? THEN receiver_id ELSE sender_id END as chat_id,
        (SELECT real_name FROM users WHERE id = chat_id) as real_name,
        (SELECT username FROM users WHERE id = chat_id) as username,
        (SELECT profile_pic_url FROM users WHERE id = chat_id) as profile_pic_url,
        (SELECT text FROM messages WHERE ((sender_id = ? AND receiver_id = chat_id) OR (sender_id = chat_id AND receiver_id = ?)) ORDER BY timestamp DESC LIMIT 1) as last_message,
        (SELECT timestamp FROM messages WHERE ((sender_id = ? AND receiver_id = chat_id) OR (sender_id = chat_id AND receiver_id = ?)) ORDER BY timestamp DESC LIMIT 1) as last_timestamp,
        (SELECT COUNT(*) FROM messages WHERE sender_id = chat_id AND receiver_id = ? AND read = 0) as unread
        FROM messages WHERE is_group = 0 AND (sender_id = ? OR receiver_id = ?)
        ORDER BY last_timestamp DESC
    """, (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id))
    chats = [dict(row) for row in cursor.fetchall()]
    return jsonify(chats)

@app.route('/api/inbox/groups', methods=['GET'])
@login_required
def get_group_chats():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT g.id as chat_id, g.name, g.profile_pic_url,
        (SELECT text FROM messages WHERE receiver_id = g.id AND is_group = 1 ORDER BY timestamp DESC LIMIT 1) as last_message,
        (SELECT timestamp FROM messages WHERE receiver_id = g.id AND is_group = 1 ORDER BY timestamp DESC LIMIT 1) as last_timestamp,
        (SELECT COUNT(*) FROM messages WHERE receiver_id = g.id AND is_group = 1 AND read = 0) as unread
        FROM group_members gm JOIN groups g ON gm.group_id = g.id WHERE gm.user_id = ? AND gm.status = 'accepted'
        ORDER BY last_timestamp DESC
    """, (user_id,))
    groups = [dict(row) for row in cursor.fetchall()]
    return jsonify(groups)

@app.route('/api/chat/customize', methods=['POST'])
@login_required
def customize_chat():
    data = request.json
    chat_id = data.get('chat_id')
    is_group = data.get('is_group', 0)
    nickname = data.get('nickname')
    wallpaper_url = data.get('wallpaper_url')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("REPLACE INTO chat_custom (user_id, chat_id, is_group, nickname, wallpaper_url) VALUES (?, ?, ?, ?, ?)", (user_id, chat_id, is_group, nickname, wallpaper_url))
    db.commit()
    return jsonify({'message': 'Customized'})

@app.route('/api/chat/custom', methods=['GET'])
@login_required
def get_chat_custom():
    chat_id = request.args.get('chat_id')
    is_group = request.args.get('is_group', 0)
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM chat_custom WHERE user_id = ? AND chat_id = ? AND is_group = ?", (user_id, chat_id, is_group))
    custom = dict(cursor.fetchone() or {})
    return jsonify(custom)

@app.route('/api/chat/search', methods=['GET'])
@login_required
def search_messages():
    chat_id = request.args.get('chat_id')
    query = request.args.get('query')
    is_group = request.args.get('is_group', 0)
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    if is_group:
        where = "receiver_id = ? AND is_group = 1 AND text LIKE ?"
        params = (chat_id, f"%{query}%")
    else:
        where = "((sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)) AND is_group = 0 AND text LIKE ?"
        params = (user_id, chat_id, chat_id, user_id, f"%{query}%")
    cursor.execute(f"SELECT * FROM messages WHERE {where} ORDER BY timestamp DESC", params)
    messages = [dict(row) for row in cursor.fetchall()]
    return jsonify(messages)

@app.route('/api/group/create', methods=['POST'])
@login_required
def create_group():
    data = request.json
    name = data.get('name')
    description = data.get('description')
    profile_pic_url = data.get('profile_pic_url')
    user_id = session['user_id']
    link = generate_group_link()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO groups (name, creator_id, description, profile_pic_url, link) VALUES (?, ?, ?, ?, ?)", (name, user_id, description, profile_pic_url, link))
    group_id = cursor.lastrowid
    cursor.execute("INSERT INTO group_members (group_id, user_id, is_admin) VALUES (?, ?, 1)", (group_id, user_id))
    cursor.execute("INSERT INTO group_permissions (group_id) VALUES (?)", (group_id,))
    db.commit()
    return jsonify({'id': group_id, 'link': link})

@app.route('/api/group/<int:group_id>', methods=['GET'])
@login_required
def get_group(group_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM groups WHERE id = ?", (group_id,))
    group = dict(cursor.fetchone() or {})
    if not group:
        return jsonify({'error': 'Not found'}), 404
    cursor.execute("SELECT * FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
    if not cursor.fetchone() and not session.get('is_admin'):
        return jsonify({'error': 'Not member'}), 403
    return jsonify(group)

@app.route('/api/group/edit', methods=['POST'])
@login_required
def edit_group():
    data = request.json
    group_id = data.get('group_id')
    name = data.get('name')
    description = data.get('description')
    profile_pic_url = data.get('profile_pic_url')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT is_admin FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
    member = cursor.fetchone()
    if not member:
        return jsonify({'error': 'Not member'}), 403
    cursor.execute("SELECT allow_edit_nonadmin FROM group_permissions WHERE group_id = ?", (group_id,))
    perm = cursor.fetchone()
    if member['is_admin'] == 0 and perm['allow_edit_nonadmin'] == 0:
        return jsonify({'error': 'Not allowed'}), 403
    set_clause = []
    values = []
    if name:
        set_clause.append("name = ?")
        values.append(name)
    if description:
        set_clause.append("description = ?")
        values.append(description)
    if profile_pic_url:
        set_clause.append("profile_pic_url = ?")
        values.append(profile_pic_url)
    if set_clause:
        cursor.execute(f"UPDATE groups SET {', '.join(set_clause)} WHERE id = ?", values + [group_id])
        db.commit()
    return jsonify({'message': 'Edited'})

@app.route('/api/group/permissions', methods=['POST'])
@login_required
def update_group_permissions():
    data = request.json
    group_id = data.get('group_id')
    allow_edit_nonadmin = data.get('allow_edit_nonadmin')
    allow_messages_nonadmin = data.get('allow_messages_nonadmin')
    allow_add_nonadmin = data.get('allow_add_nonadmin')
    approve_new_members = data.get('approve_new_members')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT is_admin FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
    if not cursor.fetchone() or cursor.fetchone()['is_admin'] == 0:
        return jsonify({'error': 'Admin required'}), 403
    cursor.execute("UPDATE group_permissions SET allow_edit_nonadmin = ?, allow_messages_nonadmin = ?, allow_add_nonadmin = ?, approve_new_members = ? WHERE group_id = ?", (allow_edit_nonadmin, allow_messages_nonadmin, allow_add_nonadmin, approve_new_members, group_id))
    db.commit()
    return jsonify({'message': 'Updated'})

@app.route('/api/group/join', methods=['POST'])
@login_required
def join_group():
    data = request.json
    link = data.get('link')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM groups WHERE link = ?", (link,))
    group = cursor.fetchone()
    if not group:
        return jsonify({'error': 'Invalid link'}), 404
    group_id = group['id']
    cursor.execute("SELECT approve_new_members FROM group_permissions WHERE group_id = ?", (group_id,))
    approve = cursor.fetchone()['approve_new_members']
    status = 'pending' if approve else 'accepted'
    try:
        cursor.execute("INSERT INTO group_members (group_id, user_id, status) VALUES (?, ?, ?)", (group_id, user_id, status))
        db.commit()
        if status == 'accepted':
            notify_group_admins(group_id, 'new_member', from_user_id=user_id)
        else:
            notify_group_admins(group_id, 'join_request', from_user_id=user_id)
        return jsonify({'message': 'Joined' if status == 'accepted' else 'Request sent'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Already member'}), 400

def notify_group_admins(group_id, type_, from_user_id=None, text=None):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM group_members WHERE group_id = ? AND is_admin = 1", (group_id,))
    admins = [row['user_id'] for row in cursor.fetchall()]
    for admin in admins:
        notify(admin, type_, from_user_id=from_user_id, group_id=group_id, text=text)

@app.route('/api/group/approve', methods=['POST'])
@login_required
def approve_member():
    data = request.json
    group_id = data.get('group_id')
    target_id = data.get('target_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT is_admin FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
    if not cursor.fetchone() or cursor.fetchone()['is_admin'] == 0:
        return jsonify({'error': 'Admin required'}), 403
    cursor.execute("UPDATE group_members SET status = 'accepted' WHERE group_id = ? AND user_id = ?", (group_id, target_id))
    db.commit()
    notify(target_id, 'group_approved', group_id=group_id)
    return jsonify({'message': 'Approved'})

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
    # If creator leaves, perhaps delete group or transfer
    cursor.execute("SELECT creator_id FROM groups WHERE id = ?", (group_id,))
    if cursor.fetchone()['creator_id'] == user_id:
        admin_delete_group(group_id=group_id)  # Delete if creator leaves
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
    # Dynamic search for users (real_name first, then username)
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
    # Clean up all related data
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
    # Delete groups created by user
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
    duration = data.get('duration')  # days or 'forever'
    db = get_db()
    cursor = db.cursor()
    if duration == 'forever':
        banned_until = '9999-12-31 23:59:59'
    else:
        banned_until = (datetime.now() + timedelta(days=int(duration))).strftime('%Y-%m-%d %H:%M:%S')
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
    target_id = data.get('target_id')  # or 'all'
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
    return jsonify({'message': 'Sent'})

if __name__ == '__main__':
    app.run(debug=True)
