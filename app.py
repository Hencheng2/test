import os
import sqlite3
import random
import string
import uuid
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, session, render_template, g

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.secret_key = app.config['SECRET_KEY']

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
                posts_privacy TEXT DEFAULT 'all'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS follows (
                follower_id INTEGER,
                followed_id INTEGER,
                status TEXT DEFAULT 'pending',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (follower_id, followed_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                blocker_id INTEGER,
                blocked_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (blocker_id, blocked_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                media_url TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                views INTEGER DEFAULT 0,
                privacy TEXT DEFAULT 'all'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS likes (
                user_id INTEGER,
                post_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, post_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                post_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reposts (
                user_id INTEGER,
                post_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, post_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saves (
                user_id INTEGER,
                post_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, post_id)
            )
        ''')
        
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                is_group INTEGER DEFAULT 0,
                text TEXT,
                media_url TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read INTEGER DEFAULT 0
            )
        ''')
        
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_permissions (
                group_id INTEGER PRIMARY KEY,
                allow_edit_nonadmin INTEGER DEFAULT 0,
                allow_messages_nonadmin INTEGER DEFAULT 1,
                allow_add_nonadmin INTEGER DEFAULT 1,
                approve_new_members INTEGER DEFAULT 0
            )
        ''')
        
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
        
        admin_username = app.config['ADMIN_USERNAME']
        admin_pass_hash = generate_password_hash(app.config['ADMIN_PASS'])
        cursor.execute("SELECT id FROM users WHERE username = ?", (admin_username,))
        if not cursor.fetchone():
            unique_key = generate_unique_key()
            cursor.execute("INSERT INTO users (username, password_hash, real_name, unique_key, is_admin) VALUES (?, ?, 'Admin', ?, 1)", (admin_username, admin_pass_hash, unique_key))
        
        db.commit()
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
        raise

# Initialize database on app startup
with app.app_context():
    init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT is_admin FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        if not user or user['is_admin'] == 0:
            return jsonify({'error': 'Admin required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing fields'}), 400
    if len(password) < 6 or not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password) or not any(not c.isalnum() for c in password):
        return jsonify({'error': 'Password requirements not met'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        return jsonify({'error': 'Username taken'}), 400
    if username == app.config['ADMIN_USERNAME']:
        return jsonify({'error': 'Reserved username'}), 400
    password_hash = generate_password_hash(password)
    unique_key = generate_unique_key()
    cursor.execute("INSERT INTO users (username, password_hash, unique_key) VALUES (?, ?, ?)", (username, password_hash, unique_key))
    user_id = cursor.lastrowid
    db.commit()
    session['user_id'] = user_id
    return jsonify({'message': 'Registered', 'unique_key': unique_key})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    identifier = data.get('identifier')
    password = data.get('password')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (identifier, identifier))
    user = cursor.fetchone()
    if user and check_password_hash(user['password_hash'], password) and (user['banned_until'] is None or datetime.strptime(user['banned_until'], '%Y-%m-%d %H:%M:%S') < datetime.now()):
        session['user_id'] = user['id']
        return jsonify({'message': 'Logged in'})
    return jsonify({'error': 'Invalid credentials or banned'}), 401

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
        return jsonify({'error': 'Not authorized'}), 403
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

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    session.pop('user_id')
    return jsonify({'message': 'Logged out'})

@app.route('/api/user/me', methods=['GET'])
@login_required
def get_current_user():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    return jsonify(dict(user))

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
    user_dict = dict(user)
    if user['profile_locked'] == 1:
        cursor.execute("SELECT status FROM follows WHERE follower_id = ? AND followed_id = ?", (current_user_id, user_id))
        follow = cursor.fetchone()
        if not follow or follow['status'] != 'accepted':
            limited = {'profile_pic_url': user['profile_pic_url'], 'real_name': user['real_name']}
            return jsonify(limited)
    return jsonify(user_dict)

@app.route('/api/user/update', methods=['POST'])
@login_required
def update_user():
    data = request.json
    fields = ['real_name', 'bio', 'email', 'phone', 'gender', 'pronouns', 'dob', 'work', 'education', 'places', 'relationship', 'spouse', 'profile_locked', 'posts_privacy']
    db = get_db()
    cursor = db.cursor()
    set_clause = ', '.join(f"{field} = ?" for field in fields if field in data)
    values = [data[field] for field in fields if field in data]
    if set_clause:
        cursor.execute(f"UPDATE users SET {set_clause} WHERE id = ?", (*values, session['user_id']))
        db.commit()
    return jsonify({'message': 'Updated'})

@app.route('/api/user/search', methods=['GET'])
@login_required
def search_users():
    query = request.args.get('query', '')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, username, real_name, profile_pic_url FROM users WHERE real_name LIKE ? OR username LIKE ? LIMIT 20", (f"%{query}%", f"%{query}%"))
    users = [dict(row) for row in cursor.fetchall()]
    return jsonify(users)

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    return jsonify({'url': f"/{file_path}"})

@app.route('/api/post/create', methods=['POST'])
@login_required
def create_post():
    data = request.json
    type_ = data.get('type')
    description = data.get('description', '')
    media_url = data.get('media_url', '')
    privacy = data.get('privacy', 'all')
    if type_ not in ['post', 'reel', 'story']:
        return jsonify({'error': 'Invalid type'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO posts (user_id, type, description, media_url, privacy) VALUES (?, ?, ?, ?, ?)", (session['user_id'], type_, description, media_url, privacy))
    post_id = cursor.lastrowid
    db.commit()
    return jsonify({'message': 'Posted', 'post_id': post_id})

@app.route('/api/posts/feed', methods=['GET'])
@login_required
def get_feed():
    page = request.args.get('page', 1, type=int)
    limit = 10
    offset = (page - 1) * limit
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT p.*, u.username, u.real_name, u.profile_pic_url
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.type = 'post' 
        AND (p.user_id = ? OR (p.user_id IN (SELECT followed_id FROM follows WHERE follower_id = ? AND status = 'accepted') 
            AND (p.privacy = 'all' OR (p.privacy = 'friends' AND EXISTS (SELECT 1 FROM follows WHERE follower_id = p.user_id AND followed_id = ? AND status = 'accepted')))))
        ORDER BY p.timestamp DESC LIMIT ? OFFSET ?
    ''', (user_id, user_id, user_id, limit, offset))
    posts = [dict(row) for row in cursor.fetchall()]
    return jsonify(posts)

@app.route('/api/posts/reels', methods=['GET'])
@login_required
def get_reels():
    page = request.args.get('page', 1, type=int)
    limit = 10
    offset = (page - 1) * limit
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT p.*, u.username, u.real_name, u.profile_pic_url
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.type = 'reel' 
        AND (p.user_id = ? OR (p.user_id IN (SELECT followed_id FROM follows WHERE follower_id = ? AND status = 'accepted') 
            AND (p.privacy = 'all' OR (p.privacy = 'friends' AND EXISTS (SELECT 1 FROM follows WHERE follower_id = p.user_id AND followed_id = ? AND status = 'accepted')))))
        ORDER BY p.timestamp DESC LIMIT ? OFFSET ?
    ''', (user_id, user_id, user_id, limit, offset))
    reels = [dict(row) for row in cursor.fetchall()]
    return jsonify(reels)

@app.route('/api/stories', methods=['GET'])
@login_required
def get_stories():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT p.*, u.username, u.real_name, u.profile_pic_url
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.type = 'story' AND p.timestamp > datetime('now', '-1 day')
        AND EXISTS (SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = p.user_id AND status = 'accepted'
            AND EXISTS (SELECT 1 FROM follows WHERE follower_id = p.user_id AND followed_id = ? AND status = 'accepted'))
        ORDER BY p.timestamp DESC
    ''', (user_id, user_id))
    stories = [dict(row) for row in cursor.fetchall()]
    return jsonify(stories)

@app.route('/api/post/<int:post_id>', methods=['GET'])
@login_required
def get_post(post_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    return jsonify(dict(post))

@app.route('/api/post/like', methods=['POST'])
@login_required
def like_post():
    data = request.json
    post_id = data.get('post_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        db.commit()
        cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
        owner_id = cursor.fetchone()['user_id']
        if owner_id != user_id:
            cursor.execute("INSERT INTO notifications (user_id, type, from_user_id, post_id, text) VALUES (?, 'like', ?, ?, 'liked your post')", (owner_id, user_id, post_id))
            db.commit()
    except sqlite3.IntegrityError:
        pass
    return jsonify({'message': 'Liked'})

@app.route('/api/post/unlike', methods=['POST'])
@login_required
def unlike_post():
    data = request.json
    post_id = data.get('post_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
    db.commit()
    return jsonify({'message': 'Unliked'})

@app.route('/api/post/comment', methods=['POST'])
@login_required
def comment_post():
    data = request.json
    post_id = data.get('post_id')
    text = data.get('text')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO comments (user_id, post_id, text) VALUES (?, ?, ?)", (user_id, post_id, text))
    db.commit()
    cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
    owner_id = cursor.fetchone()['user_id']
    if owner_id != user_id:
        cursor.execute("INSERT INTO notifications (user_id, type, from_user_id, post_id, text) VALUES (?, 'comment', ?, ?, 'commented on your post')", (owner_id, user_id, post_id))
        db.commit()
    return jsonify({'message': 'Commented'})

@app.route('/api/post/repost', methods=['POST'])
@login_required
def repost_post():
    data = request.json
    post_id = data.get('post_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO reposts (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        db.commit()
        cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
        owner_id = cursor.fetchone()['user_id']
        if owner_id != user_id:
            cursor.execute("INSERT INTO notifications (user_id, type, from_user_id, post_id, text) VALUES (?, 'repost', ?, ?, 'reposted your post')", (owner_id, user_id, post_id))
            db.commit()
    except sqlite3.IntegrityError:
        pass
    return jsonify({'message': 'Reposted'})

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
    except sqlite3.IntegrityError:
        pass
    return jsonify({'message': 'Saved'})

@app.route('/api/post/report', methods=['POST'])
@login_required
def report_post():
    data = request.json
    post_id = data.get('post_id')
    reason = data.get('reason', '')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO reports (reporter_id, target_type, target_id, reason) VALUES (?, 'post', ?, ?)", (user_id, post_id, reason))
    db.commit()
    return jsonify({'message': 'Reported'})

@app.route('/api/post/view', methods=['POST'])
@login_required
def view_post():
    data = request.json
    post_id = data.get('post_id')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE posts SET views = views + 1 WHERE id = ?", (post_id,))
    db.commit()
    return jsonify({'message': 'Viewed'})

@app.route('/api/follow/request', methods=['POST'])
@login_required
def request_follow():
    data = request.json
    target_id = data.get('target_id')
    user_id = session['user_id']
    if target_id == user_id:
        return jsonify({'error': 'Cannot follow self'}), 400
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO follows (follower_id, followed_id) VALUES (?, ?)", (user_id, target_id))
        db.commit()
        cursor.execute("INSERT INTO notifications (user_id, type, from_user_id, text) VALUES (?, 'friend_request', ?, 'sent you a friend request')", (target_id, user_id))
        db.commit()
    except sqlite3.IntegrityError:
        pass
    return jsonify({'message': 'Request sent'})

@app.route('/api/follow/accept', methods=['POST'])
@login_required
def accept_follow():
    data = request.json
    requester_id = data.get('requester_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE follows SET status = 'accepted' WHERE follower_id = ? AND followed_id = ?", (requester_id, user_id))
    if cursor.rowcount > 0:
        db.commit()
        cursor.execute("INSERT INTO notifications (user_id, type, from_user_id, text) VALUES (?, 'friend_accept', ?, 'accepted your friend request')", (requester_id, user_id))
        db.commit()
    return jsonify({'message': 'Accepted'})

@app.route('/api/follow/decline', methods=['POST'])
@login_required
def decline_follow():
    data = request.json
    requester_id = data.get('requester_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM follows WHERE follower_id = ? AND followed_id = ?", (requester_id, user_id))
    db.commit()
    return jsonify({'message': 'Declined'})

@app.route('/api/unfollow', methods=['POST'])
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
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO blocks (blocker_id, blocked_id) VALUES (?, ?)", (user_id, target_id))
        db.commit()
    except sqlite3.IntegrityError:
        pass
    cursor.execute("DELETE FROM follows WHERE (follower_id = ? AND followed_id = ?) OR (follower_id = ? AND followed_id = ?)", (user_id, target_id, target_id, user_id))
    db.commit()
    return jsonify({'message': 'Blocked'})

@app.route('/api/followers', methods=['GET'])
@login_required
def get_followers():
    user_id = request.args.get('user_id', session['user_id'], type=int)
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT u.id, u.username, u.real_name, u.profile_pic_url
        FROM users u
        JOIN follows f ON f.follower_id = u.id
        WHERE f.followed_id = ? AND f.status = 'accepted'
    ''', (user_id,))
    followers = [dict(row) for row in cursor.fetchall()]
    return jsonify(followers)

@app.route('/api/following', methods=['GET'])
@login_required
def get_following():
    user_id = request.args.get('user_id', session['user_id'], type=int)
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT u.id, u.username, u.real_name, u.profile_pic_url
        FROM users u
        JOIN follows f ON f.followed_id = u.id
        WHERE f.follower_id = ? AND f.status = 'accepted'
    ''', (user_id,))
    following = [dict(row) for row in cursor.fetchall()]
    return jsonify(following)

@app.route('/api/friends', methods=['GET'])
@login_required
def get_friends():
    user_id = request.args.get('user_id', session['user_id'], type=int)
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT u.id, u.username, u.real_name, u.profile_pic_url
        FROM users u
        WHERE EXISTS (SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = u.id AND status = 'accepted')
        AND EXISTS (SELECT 1 FROM follows WHERE follower_id = u.id AND followed_id = ? AND status = 'accepted')
    ''', (user_id, user_id))
    friends = [dict(row) for row in cursor.fetchall()]
    return jsonify(friends)

@app.route('/api/requests', methods=['GET'])
@login_required
def get_requests():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT u.id, u.username, u.real_name, u.profile_pic_url
        FROM users u
        JOIN follows f ON f.follower_id = u.id
        WHERE f.followed_id = ? AND f.status = 'pending'
    ''', (user_id,))
    requests = [dict(row) for row in cursor.fetchall()]
    return jsonify(requests)

@app.route('/api/suggested', methods=['GET'])
@login_required
def get_suggested():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT f2.followed_id as id, COUNT(*) as mutual
        FROM follows f1
        JOIN follows f2 ON f1.followed_id = f2.follower_id
        WHERE f1.follower_id = ? AND f1.status = 'accepted'
        AND f2.followed_id != ? 
        AND f2.followed_id NOT IN (SELECT followed_id FROM follows WHERE follower_id = ? AND status = 'accepted')
        AND f2.followed_id NOT IN (SELECT blocked_id FROM blocks WHERE blocker_id = ?)
        AND f2.status = 'accepted'
        GROUP BY f2.followed_id
        ORDER BY mutual DESC LIMIT 20
    ''', (user_id, user_id, user_id, user_id))
    suggested_ids = [row['id'] for row in cursor.fetchall()]
    if suggested_ids:
        placeholders = ','.join('?' for _ in suggested_ids)
        cursor.execute(f"SELECT id, username, real_name, profile_pic_url FROM users WHERE id IN ({placeholders})", suggested_ids)
        suggested = [dict(row) for row in cursor.fetchall()]
    else:
        suggested = []
    return jsonify(suggested)

@app.route('/api/chat/users', methods=['GET'])
@login_required
def get_chat_users():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT DISTINCT CASE WHEN sender_id = ? THEN receiver_id ELSE sender_id END as chat_user_id
        FROM messages WHERE is_group = 0 AND (sender_id = ? OR receiver_id = ?)
        ORDER BY MAX(timestamp) DESC
    ''', (user_id, user_id, user_id))
    chat_ids = [row['chat_user_id'] for row in cursor.fetchall()]
    chats = []
    for chat_id in chat_ids:
        cursor.execute("SELECT id, username, real_name, profile_pic_url FROM users WHERE id = ?", (chat_id,))
        user = dict(cursor.fetchone())
        cursor.execute("SELECT text, timestamp FROM messages WHERE ((sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)) AND is_group = 0 ORDER BY timestamp DESC LIMIT 1", (user_id, chat_id, chat_id, user_id))
        last_msg = cursor.fetchone()
        user['last_message'] = last_msg['text'] if last_msg else ''
        user['last_timestamp'] = last_msg['timestamp'] if last_msg else ''
        cursor.execute("SELECT COUNT(*) as unread FROM messages WHERE sender_id = ? AND receiver_id = ? AND is_group = 0 AND read = 0", (chat_id, user_id))
        user['unread'] = cursor.fetchone()['unread']
        chats.append(user)
    return jsonify(chats)

@app.route('/api/chat/messages', methods=['GET'])
@login_required
def get_chat_messages():
    with_user_id = request.args.get('with_user_id', type=int)
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT * FROM messages 
        WHERE is_group = 0 AND ((sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?))
        ORDER BY timestamp ASC
    ''', (user_id, with_user_id, with_user_id, user_id))
    messages = [dict(row) for row in cursor.fetchall()]
    cursor.execute("UPDATE messages SET read = 1 WHERE sender_id = ? AND receiver_id = ? AND is_group = 0 AND read = 0", (with_user_id, user_id))
    db.commit()
    return jsonify(messages)

@app.route('/api/chat/send', methods=['POST'])
@login_required
def send_message():
    data = request.json
    to_user_id = data.get('to_user_id')
    text = data.get('text', '')
    media_url = data.get('media_url', '')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO messages (sender_id, receiver_id, text, media_url) VALUES (?, ?, ?, ?)", (user_id, to_user_id, text, media_url))
    db.commit()
    cursor.execute("INSERT INTO notifications (user_id, type, from_user_id, text) VALUES (?, 'message', ?, 'sent you a message')", (to_user_id, user_id))
    db.commit()
    return jsonify({'message': 'Sent'})

@app.route('/api/group/create', methods=['POST'])
@login_required
def create_group():
    data = request.json
    name = data.get('name')
    profile_pic_url = data.get('profile_pic_url', '')
    permissions = data.get('permissions', {})
    user_id = session['user_id']
    link = generate_group_link()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO groups (name, creator_id, profile_pic_url, description, link) VALUES (?, ?, ?, ?, ?)", (name, user_id, profile_pic_url, f"Created by {user_id} on {datetime.now()}", link))
    group_id = cursor.lastrowid
    cursor.execute("INSERT INTO group_members (group_id, user_id, is_admin) VALUES (?, ?, 1)", (group_id, user_id))
    cursor.execute("INSERT INTO group_permissions (group_id, allow_edit_nonadmin, allow_messages_nonadmin, allow_add_nonadmin, approve_new_members) VALUES (?, ?, ?, ?, ?)", 
                   (group_id, permissions.get('allow_edit', 0), permissions.get('allow_messages', 1), permissions.get('allow_add', 1), permissions.get('approve_new', 0)))
    db.commit()
    return jsonify({'message': 'Group created', 'group_id': group_id})

@app.route('/api/group/<int:group_id>', methods=['GET'])
@login_required
def get_group(group_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM groups WHERE id = ?", (group_id,))
    group = cursor.fetchone()
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    cursor.execute("SELECT * FROM group_permissions WHERE group_id = ?", (group_id,))
    perms = dict(cursor.fetchone())
    cursor.execute("SELECT u.* , gm.is_admin FROM users u JOIN group_members gm ON u.id = gm.user_id WHERE gm.group_id = ? AND gm.status = 'accepted'", (group_id,))
    members = [dict(row) for row in cursor.fetchall()]
    group_dict = dict(group)
    group_dict['permissions'] = perms
    group_dict['members'] = members
    return jsonify(group_dict)

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
        if approve:
            cursor.execute("SELECT user_id FROM group_members WHERE group_id = ? AND is_admin = 1", (group_id,))
            admins = [row['user_id'] for row in cursor.fetchall()]
            for admin in admins:
                cursor.execute("INSERT INTO notifications (user_id, type, from_user_id, group_id, text) VALUES (?, 'group_join_request', ?, ?, 'requested to join group')", (admin, user_id, group_id))
            db.commit()
    except sqlite3.IntegrityError:
        pass
    return jsonify({'message': 'Joined or requested'})

@app.route('/api/group/invite', methods=['POST'])
@login_required
def invite_to_group():
    data = request.json
    group_id = data.get('group_id')
    target_id = data.get('target_id')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT allow_add_nonadmin FROM group_permissions WHERE group_id = ?", (group_id,))
    allow_add = cursor.fetchone()['allow_add_nonadmin']
    cursor.execute("SELECT is_admin FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
    member = cursor.fetchone()
    is_admin = member['is_admin'] if member else 0
    if not is_admin and not allow_add:
        return jsonify({'error': 'Not allowed'}), 403
    cursor.execute("INSERT INTO notifications (user_id, type, from_user_id, group_id, text) VALUES (?, 'group_invite', ?, ?, 'invited you to group')", (target_id, user_id, group_id))
    db.commit()
    return jsonify({'message': 'Invited'})

@app.route('/api/group/messages', methods=['GET'])
@login_required
def get_group_messages():
    group_id = request.args.get('group_id', type=int)
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT status FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
    member = cursor.fetchone()
    if not member or member['status'] != 'accepted':
        return jsonify({'error': 'Not member'}), 403
    cursor.execute("SELECT * FROM messages WHERE receiver_id = ? AND is_group = 1 ORDER BY timestamp ASC", (group_id,))
    messages = [dict(row) for row in cursor.fetchall()]
    cursor.execute("UPDATE messages SET read = 1 WHERE receiver_id = ? AND is_group = 1 AND sender_id != ? AND read = 0", (group_id, user_id))
    db.commit()
    return jsonify(messages)

@app.route('/api/group/send', methods=['POST'])
@login_required
def send_group_message():
    data = request.json
    group_id = data.get('group_id')
    text = data.get('text', '')
    media_url = data.get('media_url', '')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT allow_messages_nonadmin FROM group_permissions WHERE group_id = ?", (group_id,))
    allow_msg = cursor.fetchone()['allow_messages_nonadmin']
    cursor.execute("SELECT is_admin FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
    member = cursor.fetchone()
    is_admin = member['is_admin'] if member else 0
    if not is_admin and not allow_msg:
        return jsonify({'error': 'Not allowed'}), 403
    cursor.execute("INSERT INTO messages (sender_id, receiver_id, is_group, text, media_url) VALUES (?, ?, 1, ?, ?)", (user_id, group_id, text, media_url))
    db.commit()
    return jsonify({'message': 'Sent'})

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

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_get_users():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")
    users = [dict(row) for row in cursor.fetchall()]
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
    cursor.execute("SELECT id FROM groups WHERE creator_id = ?", (target_id,))
    groups = [row['id'] for row in cursor.fetchall()]
    for g_id in groups:
        cursor.execute("DELETE FROM groups WHERE id = ?", (g_id,))
        cursor.execute("DELETE FROM group_members WHERE group_id = ?", (g_id,))
        cursor.execute("DELETE FROM group_permissions WHERE group_id = ?", (g_id,))
        cursor.execute("DELETE FROM messages WHERE receiver_id = ? AND is_group = 1", (g_id,))
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

@app.route('/api/admin/group/delete', methods=['POST'])
@admin_required
def admin_delete_group():
    data = request.json
    group_id = data.get('group_id')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM groups WHERE id = ?", (group_id,))
    cursor.execute("DELETE FROM group_members WHERE group_id = ?", (group_id,))
    cursor.execute("DELETE FROM group_permissions WHERE group_id = ?", (group_id,))
    cursor.execute("DELETE FROM messages WHERE receiver_id = ? AND is_group = 1", (group_id,))
    cursor.execute("DELETE FROM notifications WHERE group_id = ?", (group_id,))
    db.commit()
    return jsonify({'message': 'Deleted'})

@app.route('/api/admin/inbox', methods=['GET'])
@admin_required
def admin_inbox():
    admin_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT DISTINCT CASE WHEN sender_id = ? THEN receiver_id ELSE sender_id END as chat_user_id
        FROM messages WHERE is_group = 0 AND (sender_id = ? OR receiver_id = ?)
        ORDER BY MAX(timestamp) DESC
    ''', (admin_id, admin_id, admin_id))
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

@app.route('/api/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('query', '')
    type_ = request.args.get('type', 'all')
    db = get_db()
    cursor = db.cursor()
    results = {}
    if type_ in ['all', 'users']:
        cursor.execute("SELECT id, username, real_name, profile_pic_url FROM users WHERE real_name LIKE ? OR username LIKE ? LIMIT 20", (f"%{query}%", f"%{query}%"))
        results['users'] = [dict(row) for row in cursor.fetchall()]
    if type_ in ['all', 'groups']:
        cursor.execute("SELECT id, name, profile_pic_url FROM groups WHERE name LIKE ? LIMIT 20", (f"%{query}%",))
        results['groups'] = [dict(row) for row in cursor.fetchall()]
    if type_ in ['all', 'posts']:
        cursor.execute("SELECT p.id, p.description, u.username FROM posts p JOIN users u ON p.user_id = u.id WHERE p.type = 'post' AND p.description LIKE ? LIMIT 20", (f"%{query}%",))
        results['posts'] = [dict(row) for row in cursor.fetchall()]
    if type_ in ['all', 'reels']:
        cursor.execute("SELECT p.id, p.description, u.username FROM posts p JOIN users u ON p.user_id = u.id WHERE p.type = 'reel' AND p.description LIKE ? LIMIT 20", (f"%{query}%",))
        results['reels'] = [dict(row) for row in cursor.fetchall()]
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
