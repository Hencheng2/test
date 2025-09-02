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
        key = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(4))
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
        # User and social tables
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
                status TEXT DEFAULT 'pending', -- 'pending', 'accepted'
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
        
        # Content tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL, -- 'post', 'reel', 'story'
                description TEXT,
                media_url TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                views INTEGER DEFAULT 0,
                privacy TEXT DEFAULT 'all', -- 'all', 'friends'
                duration_seconds INTEGER,
                parent_post_id INTEGER
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
        
        # Messaging and groups
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER, -- Null for group messages
                is_group INTEGER DEFAULT 0,
                group_id INTEGER, -- Null for direct messages
                text TEXT,
                media_url TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read_status INTEGER DEFAULT 0 -- 0=unread, 1=read
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
                status TEXT DEFAULT 'accepted', -- 'pending', 'accepted'
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
            CREATE TABLE IF NOT EXISTS chat_customization (
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                is_group INTEGER DEFAULT 0,
                custom_name TEXT,
                wallpaper_url TEXT,
                disappearing_messages_time TEXT,
                PRIMARY KEY (user_id, chat_id, is_group)
            )
        ''')
        
        # Admin and reports
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER NOT NULL,
                target_type TEXT NOT NULL, -- 'user', 'post', 'group', 'message'
                target_id INTEGER NOT NULL,
                reason TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
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

# User Authentication and Profile
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
        cursor.execute("SELECT status FROM follows WHERE follower_id = ? AND followed_id = ? AND status = 'accepted'", (current_user_id, user_id))
        if not cursor.fetchone():
            limited = {'profile_pic_url': user['profile_pic_url'], 'real_name': user['real_name']}
            return jsonify(limited)
    
    # Get counts
    cursor.execute("SELECT COUNT(*) FROM follows WHERE followed_id = ? AND status = 'accepted'", (user_id,))
    user_dict['followers_count'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM follows WHERE follower_id = ? AND status = 'accepted'", (user_id,))
    user_dict['following_count'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM posts WHERE user_id = ? AND type='post'", (user_id,))
    user_dict['posts_count'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id IN (SELECT id FROM posts WHERE user_id = ?)", (user_id,))
    user_dict['likes_count'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM follows WHERE follower_id = ? AND followed_id IN (SELECT follower_id FROM follows WHERE followed_id = ?)", (user_id, user_id))
    user_dict['friends_count'] = cursor.fetchone()[0]
    
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

# Content and Interactions
@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    return jsonify({'url': f"/static/uploads/{filename}"})

@app.route('/api/post/create', methods=['POST'])
@login_required
def create_post():
    data = request.json
    type_ = data.get('type')
    description = data.get('description', '')
    media_url = data.get('media_url', '')
    privacy = data.get('privacy', 'all')
    duration = data.get('duration_seconds')
    if type_ not in ['post', 'reel', 'story']:
        return jsonify({'error': 'Invalid type'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO posts (user_id, type, description, media_url, privacy, duration_seconds) VALUES (?, ?, ?, ?, ?, ?)", (session['user_id'], type_, description, media_url, privacy, duration))
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
    
    cursor.execute("SELECT followed_id FROM follows WHERE follower_id = ? AND status = 'accepted'", (user_id,))
    following_ids = [row[0] for row in cursor.fetchall()]
    following_ids.append(user_id) # Include own posts

    query = f"""
    SELECT p.*, u.username, u.real_name, u.profile_pic_url,
    (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as likes_count,
    (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comments_count,
    (SELECT COUNT(*) FROM reposts WHERE post_id = p.id) as reposts_count,
    EXISTS(SELECT 1 FROM likes WHERE user_id = ? AND post_id = p.id) as is_liked
    FROM posts p
    JOIN users u ON p.user_id = u.id
    WHERE p.type = 'post'
    AND p.user_id IN ({','.join(['?']*len(following_ids))})
    AND (p.privacy = 'all' OR p.privacy = 'friends')
    ORDER BY p.timestamp DESC
    LIMIT ? OFFSET ?
    """
    params = [user_id] + following_ids + [limit, offset]
    cursor.execute(query, params)
    
    posts = [dict(row) for row in cursor.fetchall()]
    return jsonify(posts)

@app.route('/api/reels/feed', methods=['GET'])
@login_required
def get_reels():
    page = request.args.get('page', 1, type=int)
    limit = 10
    offset = (page - 1) * limit
    db = get_db()
    cursor = db.cursor()
    
    query = f"""
    SELECT p.*, u.username, u.real_name, u.profile_pic_url,
    (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as likes_count,
    (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comments_count,
    (SELECT COUNT(*) FROM reposts WHERE post_id = p.id) as reposts_count,
    EXISTS(SELECT 1 FROM likes WHERE user_id = ? AND post_id = p.id) as is_liked
    FROM posts p
    JOIN users u ON p.user_id = u.id
    WHERE p.type = 'reel'
    AND p.privacy = 'all'
    ORDER BY p.timestamp DESC
    LIMIT ? OFFSET ?
    """
    cursor.execute(query, (session['user_id'], limit, offset))
    reels = [dict(row) for row in cursor.fetchall()]
    return jsonify(reels)

@app.route('/api/stories', methods=['GET'])
@login_required
def get_stories():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT followed_id FROM follows WHERE follower_id = ? AND status = 'accepted'", (user_id,))
    following_ids = [row[0] for row in cursor.fetchall()]
    
    if not following_ids:
        return jsonify([])
    
    now = datetime.now()
    cutoff_time = now - timedelta(hours=24)
    
    query = f"""
    SELECT p.*, u.username, u.real_name, u.profile_pic_url
    FROM posts p
    JOIN users u ON p.user_id = u.id
    WHERE p.type = 'story'
    AND p.user_id IN ({','.join(['?']*len(following_ids))})
    AND p.timestamp > ?
    ORDER BY p.timestamp DESC
    """
    params = following_ids + [cutoff_time.strftime('%Y-%m-%d %H:%M:%S')]
    cursor.execute(query, params)
    
    stories = [dict(row) for row in cursor.fetchall()]
    return jsonify(stories)

@app.route('/api/post/<int:post_id>/views', methods=['POST'])
@login_required
def increment_post_views(post_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE posts SET views = views + 1 WHERE id = ?", (post_id,))
    db.commit()
    return jsonify({'message': 'View counted'})

@app.route('/api/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT OR IGNORE INTO likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
    db.commit()
    # Add notification for the post owner
    cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
    post_owner_id = cursor.fetchone()['user_id']
    if post_owner_id != user_id:
        cursor.execute("INSERT INTO notifications (user_id, type, from_user_id, post_id) VALUES (?, 'like', ?, ?)", (post_owner_id, user_id, post_id))
        db.commit()
    return jsonify({'message': 'Liked'})

@app.route('/api/post/<int:post_id>/unlike', methods=['POST'])
@login_required
def unlike_post(post_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
    db.commit()
    return jsonify({'message': 'Unliked'})

@app.route('/api/post/<int:post_id>/comment', methods=['POST'])
@login_required
def comment_post(post_id):
    data = request.json
    text = data.get('text')
    if not text:
        return jsonify({'error': 'Comment text is required'}), 400
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO comments (user_id, post_id, text) VALUES (?, ?, ?)", (user_id, post_id, text))
    comment_id = cursor.lastrowid
    db.commit()
    # Add notification for the post owner
    cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
    post_owner_id = cursor.fetchone()['user_id']
    if post_owner_id != user_id:
        cursor.execute("INSERT INTO notifications (user_id, type, from_user_id, post_id, text) VALUES (?, 'comment', ?, ?, ?)", (post_owner_id, user_id, post_id, text))
        db.commit()
    return jsonify({'message': 'Commented', 'comment_id': comment_id})

@app.route('/api/post/<int:post_id>/repost', methods=['POST'])
@login_required
def repost_post(post_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT OR IGNORE INTO reposts (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
    db.commit()
    # Add notification for the post owner
    cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
    post_owner_id = cursor.fetchone()['user_id']
    if post_owner_id != user_id:
        cursor.execute("INSERT INTO notifications (user_id, type, from_user_id, post_id) VALUES (?, 'repost', ?, ?)", (post_owner_id, user_id, post_id))
        db.commit()
    return jsonify({'message': 'Reposted'})

@app.route('/api/post/<int:post_id>/save', methods=['POST'])
@login_required
def save_post(post_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT OR IGNORE INTO saves (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
    db.commit()
    return jsonify({'message': 'Saved'})

# Social Connections
@app.route('/api/follow/<int:target_id>', methods=['POST'])
@login_required
def follow_user(target_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT profile_locked FROM users WHERE id = ?", (target_id,))
    target_user = cursor.fetchone()
    if not target_user:
        return jsonify({'error': 'User not found'}), 404
        
    status = 'pending' if target_user['profile_locked'] == 1 else 'accepted'
    
    cursor.execute("INSERT OR IGNORE INTO follows (follower_id, followed_id, status) VALUES (?, ?, ?)", (user_id, target_id, status))
    db.commit()
    
    if status == 'accepted':
        cursor.execute("INSERT INTO notifications (user_id, type, from_user_id) VALUES (?, 'follow', ?)", (target_id, user_id))
    else:
        cursor.execute("INSERT INTO notifications (user_id, type, from_user_id) VALUES (?, 'request', ?)", (target_id, user_id))
    db.commit()
    
    return jsonify({'message': f'Follow request {status}'})

@app.route('/api/unfollow/<int:target_id>', methods=['POST'])
@login_required
def unfollow_user(target_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM follows WHERE follower_id = ? AND followed_id = ?", (user_id, target_id))
    db.commit()
    return jsonify({'message': 'Unfollowed'})
    
@app.route('/api/follow/accept/<int:follower_id>', methods=['POST'])
@login_required
def accept_follow(follower_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE follows SET status = 'accepted' WHERE follower_id = ? AND followed_id = ?", (follower_id, user_id))
    db.commit()
    cursor.execute("INSERT INTO notifications (user_id, type, from_user_id) VALUES (?, 'accept', ?)", (follower_id, user_id))
    db.commit()
    return jsonify({'message': 'Follow request accepted'})

@app.route('/api/follow/decline/<int:follower_id>', methods=['POST'])
@login_required
def decline_follow(follower_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM follows WHERE follower_id = ? AND followed_id = ?", (follower_id, user_id))
    db.commit()
    return jsonify({'message': 'Follow request declined'})

@app.route('/api/block', methods=['POST'])
@login_required
def block_user():
    data = request.json
    target_id = data.get('target_id')
    user_id = session['user_id']
    if not target_id:
        return jsonify({'error': 'Target ID required'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT OR IGNORE INTO blocks (blocker_id, blocked_id) VALUES (?, ?)", (user_id, target_id))
    cursor.execute("DELETE FROM follows WHERE (follower_id = ? AND followed_id = ?) OR (follower_id = ? AND followed_id = ?)", (user_id, target_id, target_id, user_id))
    db.commit()
    return jsonify({'message': 'User blocked'})

@app.route('/api/friends', methods=['GET'])
@login_required
def get_friends():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    def get_mutual_count(user1_id, user2_id):
        cursor.execute("""
            SELECT COUNT(*) FROM follows
            WHERE follower_id = ? AND followed_id IN
            (SELECT followed_id FROM follows WHERE follower_id = ? AND status = 'accepted')
        """, (user1_id, user2_id))
        return cursor.fetchone()[0]
    
    view = request.args.get('view', 'friends')
    
    if view == 'followers':
        cursor.execute("""
            SELECT u.id, u.username, u.real_name, u.profile_pic_url
            FROM follows f JOIN users u ON f.follower_id = u.id
            WHERE f.followed_id = ? AND f.status = 'accepted'
        """, (user_id,))
        users = [dict(row) for row in cursor.fetchall()]
        for user in users:
            user['mutual_count'] = get_mutual_count(user_id, user['id'])
        return jsonify(users)
        
    elif view == 'following':
        cursor.execute("""
            SELECT u.id, u.username, u.real_name, u.profile_pic_url
            FROM follows f JOIN users u ON f.followed_id = u.id
            WHERE f.follower_id = ? AND f.status = 'accepted'
        """, (user_id,))
        users = [dict(row) for row in cursor.fetchall()]
        for user in users:
            user['mutual_count'] = get_mutual_count(user_id, user['id'])
        return jsonify(users)
        
    elif view == 'requests':
        cursor.execute("""
            SELECT u.id, u.username, u.real_name, u.profile_pic_url
            FROM follows f JOIN users u ON f.follower_id = u.id
            WHERE f.followed_id = ? AND f.status = 'pending'
        """, (user_id,))
        users = [dict(row) for row in cursor.fetchall()]
        for user in users:
            user['mutual_count'] = get_mutual_count(user_id, user['id'])
        return jsonify(users)
        
    elif view == 'suggested':
        cursor.execute("""
            SELECT u.id, u.username, u.real_name, u.profile_pic_url
            FROM users u
            WHERE u.id != ?
            AND u.id NOT IN (SELECT followed_id FROM follows WHERE follower_id = ?)
            AND u.id IN (
                SELECT followed_id FROM follows
                WHERE follower_id IN (SELECT followed_id FROM follows WHERE follower_id = ?)
            )
            LIMIT 20
        """, (user_id, user_id, user_id))
        users = [dict(row) for row in cursor.fetchall()]
        for user in users:
            user['mutual_count'] = get_mutual_count(user_id, user['id'])
        return jsonify(users)
        
    else: # 'friends'
        cursor.execute("""
            SELECT u.id, u.username, u.real_name, u.profile_pic_url
            FROM follows f JOIN users u ON f.followed_id = u.id
            WHERE f.follower_id = ? AND f.status = 'accepted'
            AND EXISTS (SELECT 1 FROM follows WHERE follower_id = u.id AND followed_id = ? AND status = 'accepted')
        """, (user_id, user_id))
        users = [dict(row) for row in cursor.fetchall()]
        for user in users:
            user['mutual_count'] = get_mutual_count(user_id, user['id'])
        return jsonify(users)

# Messaging
@app.route('/api/messages/chats', methods=['GET'])
@login_required
def get_chats():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    # Direct chats
    cursor.execute("""
        SELECT DISTINCT u.id, u.username, u.real_name, u.profile_pic_url,
        (SELECT text FROM messages WHERE (sender_id = u.id AND receiver_id = ?) OR (sender_id = ? AND receiver_id = u.id) ORDER BY timestamp DESC LIMIT 1) as last_message,
        (SELECT timestamp FROM messages WHERE (sender_id = u.id AND receiver_id = ?) OR (sender_id = ? AND receiver_id = u.id) ORDER BY timestamp DESC LIMIT 1) as last_timestamp,
        (SELECT COUNT(*) FROM messages WHERE sender_id = u.id AND receiver_id = ? AND read_status = 0) as unread_count
        FROM messages m JOIN users u ON m.sender_id = u.id OR m.receiver_id = u.id
        WHERE (m.sender_id = ? OR m.receiver_id = ?) AND m.is_group = 0 AND u.id != ?
        ORDER BY last_timestamp DESC
    """, (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id))
    direct_chats = [dict(row) for row in cursor.fetchall()]
    
    # Group chats
    cursor.execute("""
        SELECT g.id, g.name, g.profile_pic_url,
        (SELECT text FROM messages WHERE group_id = g.id ORDER BY timestamp DESC LIMIT 1) as last_message,
        (SELECT timestamp FROM messages WHERE group_id = g.id ORDER BY timestamp DESC LIMIT 1) as last_timestamp,
        (SELECT COUNT(*) FROM messages WHERE group_id = g.id AND sender_id != ? AND read_status = 0) as unread_count
        FROM group_members gm JOIN groups g ON gm.group_id = g.id
        WHERE gm.user_id = ?
        ORDER BY last_timestamp DESC
    """, (user_id, user_id))
    group_chats = [dict(row) for row in cursor.fetchall()]
    
    return jsonify({'direct_chats': direct_chats, 'group_chats': group_chats})

@app.route('/api/messages/direct/<int:chat_id>', methods=['GET'])
@login_required
def get_direct_messages(chat_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM messages WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?) ORDER BY timestamp", (user_id, chat_id, chat_id, user_id))
    messages = [dict(row) for row in cursor.fetchall()]
    cursor.execute("UPDATE messages SET read_status = 1 WHERE sender_id = ? AND receiver_id = ?", (chat_id, user_id))
    db.commit()
    return jsonify(messages)

@app.route('/api/messages/group/<int:group_id>', methods=['GET'])
@login_required
def get_group_messages(group_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM messages WHERE group_id = ? ORDER BY timestamp", (group_id,))
    messages = [dict(row) for row in cursor.fetchall()]
    cursor.execute("UPDATE messages SET read_status = 1 WHERE group_id = ? AND sender_id != ?", (group_id, user_id))
    db.commit()
    return jsonify(messages)

@app.route('/api/message/send', methods=['POST'])
@login_required
def send_message():
    data = request.json
    sender_id = session['user_id']
    receiver_id = data.get('receiver_id')
    group_id = data.get('group_id')
    text = data.get('text')
    media_url = data.get('media_url')
    
    if not receiver_id and not group_id:
        return jsonify({'error': 'Recipient not specified'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    if receiver_id:
        cursor.execute("INSERT INTO messages (sender_id, receiver_id, text, media_url) VALUES (?, ?, ?, ?)", (sender_id, receiver_id, text, media_url))
        cursor.execute("INSERT INTO notifications (user_id, type, from_user_id) VALUES (?, 'message', ?)", (receiver_id, sender_id))
    elif group_id:
        cursor.execute("INSERT INTO messages (sender_id, is_group, group_id, text, media_url) VALUES (?, 1, ?, ?, ?)", (sender_id, group_id, text, media_url))
        cursor.execute("SELECT user_id FROM group_members WHERE group_id = ? AND user_id != ?", (group_id, sender_id))
        members = cursor.fetchall()
        for member in members:
            cursor.execute("INSERT INTO notifications (user_id, type, from_user_id, group_id) VALUES (?, 'group_message', ?, ?)", (member['user_id'], sender_id, group_id))
    
    db.commit()
    return jsonify({'message': 'Message sent'})

# Groups
@app.route('/api/groups/create', methods=['POST'])
@login_required
def create_group():
    data = request.json
    name = data.get('name')
    description = data.get('description', '')
    profile_pic_url = data.get('profile_pic_url', '')
    
    if not name:
        return jsonify({'error': 'Group name is required'}), 400
        
    db = get_db()
    cursor = db.cursor()
    link = generate_group_link()
    
    cursor.execute("INSERT INTO groups (name, creator_id, profile_pic_url, description, link) VALUES (?, ?, ?, ?, ?)", (name, session['user_id'], profile_pic_url, description, link))
    group_id = cursor.lastrowid
    
    cursor.execute("INSERT INTO group_members (group_id, user_id, is_admin) VALUES (?, ?, 1)", (group_id, session['user_id']))
    
    db.commit()
    return jsonify({'message': 'Group created', 'group_id': group_id})

# Notifications
@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT n.*, u.username as from_username, u.real_name as from_real_name
        FROM notifications n
        LEFT JOIN users u ON n.from_user_id = u.id
        WHERE n.user_id = ?
        ORDER BY n.timestamp DESC
        LIMIT 50
    """, (user_id,))
    notifications = [dict(row) for row in cursor.fetchall()]
    cursor.execute("UPDATE notifications SET read = 1 WHERE user_id = ?", (user_id,))
    db.commit()
    return jsonify(notifications)

# Admin
@app.route('/api/admin/reports', methods=['GET'])
@admin_required
def get_reports():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT r.*, u.username as reporter_username FROM reports r JOIN users u ON r.reporter_id = u.id WHERE r.status = 'pending'")
    reports = [dict(row) for row in cursor.fetchall()]
    return jsonify(reports)

@app.route('/api/admin/action', methods=['POST'])
@admin_required
def admin_action():
    data = request.json
    report_id = data.get('report_id')
    action = data.get('action')
    target_type = data.get('target_type')
    target_id = data.get('target_id')
    reason = data.get('reason')
    
    db = get_db()
    cursor = db.cursor()
    
    if action == 'ban_user':
        banned_until = datetime.now() + timedelta(days=30)
        cursor.execute("UPDATE users SET banned_until = ? WHERE id = ?", (banned_until.strftime('%Y-%m-%d %H:%M:%S'), target_id))
    elif action == 'delete_post':
        cursor.execute("DELETE FROM posts WHERE id = ?", (target_id,))
    elif action == 'dismiss':
        cursor.execute("UPDATE reports SET status = 'dismissed' WHERE id = ?", (report_id,))
    
    cursor.execute("UPDATE reports SET status = 'resolved' WHERE id = ?", (report_id,))
    db.commit()
    return jsonify({'message': 'Action completed'})

if __name__ == '__main__':
    app.run(debug=True)
