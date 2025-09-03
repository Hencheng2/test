# app.py
import os
import uuid
import json
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
import re

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.config['DATABASE'] = os.path.join(app.instance_path, 'sociafam.db')
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure instance and upload folders exist
os.makedirs(app.instance_path, exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'posts'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'reels'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'stories'), exist_ok=True)

# Database initialization
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

# Database schema (will be executed on first run)
schema_sql = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    unique_key TEXT NOT NULL,
    real_name TEXT,
    profile_pic TEXT DEFAULT 'default_profile.png',
    bio TEXT,
    date_of_birth TEXT,
    gender TEXT,
    pronouns TEXT,
    work_info TEXT,
    university TEXT,
    secondary_school TEXT,
    location TEXT,
    phone_number TEXT,
    email TEXT,
    social_link TEXT,
    website_link TEXT,
    relationship_status TEXT,
    spouse TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_admin BOOLEAN DEFAULT FALSE,
    is_banned BOOLEAN DEFAULT FALSE,
    warnings INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content_type TEXT NOT NULL, -- 'text', 'image', 'video'
    content TEXT,
    description TEXT,
    visibility TEXT DEFAULT 'public', -- 'public', 'friends', 'private'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS reels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    video_url TEXT NOT NULL,
    description TEXT,
    audio_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    media_url TEXT NOT NULL,
    media_type TEXT NOT NULL, -- 'image', 'video'
    duration INTEGER DEFAULT 24, -- hours until expiration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS followers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    follower_id INTEGER NOT NULL,
    followed_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending', -- 'pending', 'accepted', 'blocked'
    FOREIGN KEY (follower_id) REFERENCES users (id),
    FOREIGN KEY (followed_id) REFERENCES users (id),
    UNIQUE(follower_id, followed_id)
);

CREATE TABLE IF NOT EXISTS friends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user1_id) REFERENCES users (id),
    FOREIGN KEY (user2_id) REFERENCES users (id),
    UNIQUE(user1_id, user2_id)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER, -- NULL for group messages
    group_id INTEGER, -- NULL for direct messages
    content TEXT NOT NULL,
    message_type TEXT DEFAULT 'text', -- 'text', 'image', 'video', 'audio'
    media_url TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP, -- for disappearing messages
    FOREIGN KEY (sender_id) REFERENCES users (id),
    FOREIGN KEY (receiver_id) REFERENCES users (id),
    FOREIGN KEY (group_id) REFERENCES groups (id)
);

CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    profile_pic TEXT DEFAULT 'default_group.png',
    unique_link TEXT UNIQUE NOT NULL,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    allow_messages BOOLEAN DEFAULT TRUE,
    allow_add_members BOOLEAN DEFAULT TRUE,
    approve_new_members BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (created_by) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS group_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES groups (id),
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(group_id, user_id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL, -- 'friend_request', 'like', 'comment', 'message', 'tag', 'group_invite', 'system'
    source_id INTEGER, -- user who triggered the notification
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (source_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    post_id INTEGER,
    reel_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (post_id) REFERENCES posts (id),
    FOREIGN KEY (reel_id) REFERENCES reels (id),
    CHECK (post_id IS NOT NULL OR reel_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    post_id INTEGER,
    reel_id INTEGER,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (post_id) REFERENCES posts (id),
    FOREIGN KEY (reel_id) REFERENCES reels (id),
    CHECK (post_id IS NOT NULL OR reel_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS saved_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    post_id INTEGER,
    reel_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (post_id) REFERENCES posts (id),
    FOREIGN KEY (reel_id) REFERENCES reels (id),
    CHECK (post_id IS NOT NULL OR reel_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS reposts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    original_post_id INTEGER,
    original_reel_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (original_post_id) REFERENCES posts (id),
    FOREIGN KEY (original_reel_id) REFERENCES reels (id),
    CHECK (original_post_id IS NOT NULL OR original_reel_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reporter_id INTEGER NOT NULL,
    reported_user_id INTEGER,
    reported_post_id INTEGER,
    reported_reel_id INTEGER,
    reported_group_id INTEGER,
    reason TEXT NOT NULL,
    status TEXT DEFAULT 'pending', -- 'pending', 'reviewed', 'resolved'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reporter_id) REFERENCES users (id),
    FOREIGN KEY (reported_user_id) REFERENCES users (id),
    FOREIGN KEY (reported_post_id) REFERENCES posts (id),
    FOREIGN KEY (reported_reel_id) REFERENCES reels (id),
    FOREIGN KEY (reported_group_id) REFERENCES groups (id),
    CHECK (reported_user_id IS NOT NULL OR reported_post_id IS NOT NULL OR 
           reported_reel_id IS NOT NULL OR reported_group_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    blocker_id INTEGER NOT NULL,
    blocked_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blocker_id) REFERENCES users (id),
    FOREIGN KEY (blocked_id) REFERENCES users (id),
    UNIQUE(blocker_id, blocked_id)
);

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    theme TEXT DEFAULT 'light',
    language TEXT DEFAULT 'en',
    profile_locked BOOLEAN DEFAULT FALSE,
    post_visibility TEXT DEFAULT 'public',
    allow_sharing BOOLEAN DEFAULT TRUE,
    allow_comments BOOLEAN DEFAULT TRUE,
    notifications_enabled BOOLEAN DEFAULT TRUE,
    notification_types TEXT DEFAULT 'all',
    disappearing_messages_duration INTEGER DEFAULT 0, -- 0: off, 24: 24h, 168: 1w, 720: 1m
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(user_id)
);
"""

# Write schema to file
with open(os.path.join(app.root_path, 'schema.sql'), 'w') as f:
    f.write(schema_sql)

# Initialize database
def init_db():
    with app.app_context():
        db = get_db()
        db.executescript(schema_sql)
        
        # Create admin user if not exists
        admin_exists = db.execute(
            'SELECT id FROM users WHERE username = ?', (app.config['ADMIN_USERNAME'],)
        ).fetchone()
        
        if not admin_exists:
            hashed_password = generate_password_hash(app.config['ADMIN_PASS'])
            unique_key = generate_unique_key()
            db.execute(
                'INSERT INTO users (username, password, unique_key, real_name, is_admin) VALUES (?, ?, ?, ?, ?)',
                (app.config['ADMIN_USERNAME'], hashed_password, unique_key, 'Admin', True)
            )
            db.commit()

# Helper functions
def generate_unique_key():
    import random
    import string
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=2))
    return letters + numbers

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        db = get_db()
        user = db.execute(
            'SELECT is_admin FROM users WHERE id = ?', (session['user_id'],)
        ).fetchone()
        
        if not user or not user['is_admin']:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Authentication routes
@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ? AND is_banned = FALSE', (username,)
        ).fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            return jsonify({'success': True, 'is_admin': user['is_admin']})
        
        return jsonify({'error': 'Invalid credentials'}), 401
    
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    real_name = request.form.get('real_name', '')
    
    # Password validation
    if len(password) < 6 or not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password) or not re.search(r'[^A-Za-z0-9]', password):
        return jsonify({'error': 'Password must be at least 6 characters with letters, numbers, and special characters'}), 400
    
    # Check if username is admin username
    if username == app.config['ADMIN_USERNAME']:
        return jsonify({'error': 'Username not available'}), 400
    
    db = get_db()
    
    # Check if username already exists
    existing_user = db.execute(
        'SELECT id FROM users WHERE username = ?', (username,)
    ).fetchone()
    
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400
    
    hashed_password = generate_password_hash(password)
    unique_key = generate_unique_key()
    
    try:
        db.execute(
            'INSERT INTO users (username, password, unique_key, real_name) VALUES (?, ?, ?, ?)',
            (username, hashed_password, unique_key, real_name)
        )
        db.commit()
        
        # Create default settings
        user_id = db.execute(
            'SELECT id FROM users WHERE username = ?', (username,)
        ).fetchone()['id']
        
        db.execute(
            'INSERT INTO settings (user_id) VALUES (?)', (user_id,)
        )
        db.commit()
        
        return jsonify({'success': True, 'unique_key': unique_key})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    username = request.form.get('username')
    unique_key = request.form.get('unique_key')
    
    db = get_db()
    user = db.execute(
        'SELECT * FROM users WHERE username = ? AND unique_key = ?', (username, unique_key)
    ).fetchone()
    
    if user:
        # In a real app, you would send an email with a reset link
        # For simplicity, we'll just return success
        return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid username or unique key'}), 400

@app.route('/reset-password', methods=['POST'])
def reset_password():
    username = request.form.get('username')
    unique_key = request.form.get('unique_key')
    new_password = request.form.get('new_password')
    
    # Password validation
    if len(new_password) < 6 or not re.search(r'[A-Za-z]', new_password) or not re.search(r'[0-9]', new_password) or not re.search(r'[^A-Za-z0-9]', new_password):
        return jsonify({'error': 'Password must be at least 6 characters with letters, numbers, and special characters'}), 400
    
    db = get_db()
    user = db.execute(
        'SELECT * FROM users WHERE username = ? AND unique_key = ?', (username, unique_key)
    ).fetchone()
    
    if user:
        hashed_password = generate_password_hash(new_password)
        db.execute(
            'UPDATE users SET password = ? WHERE id = ?',
            (hashed_password, user['id'])
        )
        db.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid username or unique key'}), 400

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# User routes
@app.route('/api/user/profile', methods=['GET'])
@login_required
def get_user_profile():
    user_id = request.args.get('user_id', session['user_id'])
    
    db = get_db()
    user = db.execute(
        'SELECT * FROM users WHERE id = ?', (user_id,)
    ).fetchone()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get counts
    followers_count = db.execute(
        'SELECT COUNT(*) FROM followers WHERE followed_id = ? AND status = "accepted"', (user_id,)
    ).fetchone()[0]
    
    following_count = db.execute(
        'SELECT COUNT(*) FROM followers WHERE follower_id = ? AND status = "accepted"', (user_id,)
    ).fetchone()[0]
    
    friends_count = db.execute(
        'SELECT COUNT(*) FROM friends WHERE user1_id = ? OR user2_id = ?', (user_id, user_id)
    ).fetchone()[0]
    
    posts_count = db.execute(
        'SELECT COUNT(*) FROM posts WHERE user_id = ?', (user_id,)
    ).fetchone()[0]
    
    likes_count = db.execute(
        '''SELECT COUNT(*) FROM likes 
           WHERE post_id IN (SELECT id FROM posts WHERE user_id = ?) 
           OR reel_id IN (SELECT id FROM reels WHERE user_id = ?)''',
        (user_id, user_id)
    ).fetchone()[0]
    
    # Check if current user is following this user
    is_following = False
    if str(user_id) != str(session['user_id']):
        follow = db.execute(
            'SELECT * FROM followers WHERE follower_id = ? AND followed_id = ? AND status = "accepted"',
            (session['user_id'], user_id)
        ).fetchone()
        is_following = follow is not None
    
    # Check if users are friends
    is_friend = db.execute(
        '''SELECT * FROM friends 
           WHERE (user1_id = ? AND user2_id = ?) 
           OR (user1_id = ? AND user2_id = ?)''',
        (session['user_id'], user_id, user_id, session['user_id'])
    ).fetchone()
    is_friend = is_friend is not None
    
    # Get mutual friends
    mutual_friends = db.execute(
        '''SELECT u.* FROM users u
           JOIN friends f1 ON (f1.user1_id = u.id OR f1.user2_id = u.id)
           JOIN friends f2 ON (f2.user1_id = u.id OR f2.user2_id = u.id)
           WHERE (f1.user1_id = ? OR f1.user2_id = ?)
           AND (f2.user1_id = ? OR f2.user2_id = ?)
           AND u.id != ? AND u.id != ?''',
        (session['user_id'], session['user_id'], user_id, user_id, session['user_id'], user_id)
    ).fetchall()
    
    user_data = dict(user)
    user_data['followers_count'] = followers_count
    user_data['following_count'] = following_count
    user_data['friends_count'] = friends_count
    user_data['posts_count'] = posts_count
    user_data['likes_count'] = likes_count
    user_data['is_following'] = is_following
    user_data['is_friend'] = is_friend
    user_data['mutual_friends'] = [dict(friend) for friend in mutual_friends[:3]]  # First 3 mutual friends
    
    return jsonify(user_data)

@app.route('/api/user/update', methods=['POST'])
@login_required
def update_user_profile():
    data = request.form.to_dict()
    
    db = get_db()
    
    # Check if username is being changed and if it's available
    if 'username' in data and data['username'] != session['username']:
        existing_user = db.execute(
            'SELECT id FROM users WHERE username = ? AND id != ?', (data['username'], session['user_id'])
        ).fetchone()
        
        if existing_user:
            return jsonify({'error': 'Username already taken'}), 400
    
    # Build update query dynamically
    update_fields = []
    values = []
    
    for field in ['username', 'real_name', 'bio', 'date_of_birth', 'gender', 'pronouns', 
                  'work_info', 'university', 'secondary_school', 'location', 'phone_number', 
                  'email', 'social_link', 'website_link', 'relationship_status', 'spouse']:
        if field in data:
            update_fields.append(f'{field} = ?')
            values.append(data[field])
    
    if update_fields:
        values.append(session['user_id'])
        query = f'UPDATE users SET {", ".join(update_fields)} WHERE id = ?'
        db.execute(query, values)
        db.commit()
        
        if 'username' in data:
            session['username'] = data['username']
    
    return jsonify({'success': True})

@app.route('/api/user/upload-profile-pic', methods=['POST'])
@login_required
def upload_profile_pic():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Generate unique filename
    filename = f"profile_{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.split('.')[-1]}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', filename)
    file.save(filepath)
    
    # Update database
    db = get_db()
    db.execute(
        'UPDATE users SET profile_pic = ? WHERE id = ?',
        (filename, session['user_id'])
    )
    db.commit()
    
    return jsonify({'success': True, 'filename': filename})

# Posts routes
@app.route('/api/posts', methods=['GET'])
@login_required
def get_posts():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    offset = (page - 1) * limit
    
    db = get_db()
    
    # Get posts from users that the current user follows
    posts = db.execute(
        '''SELECT p.*, u.username, u.real_name, u.profile_pic,
           (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as likes_count,
           (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comments_count,
           EXISTS(SELECT 1 FROM likes WHERE post_id = p.id AND user_id = ?) as is_liked,
           EXISTS(SELECT 1 FROM saved_items WHERE post_id = p.id AND user_id = ?) as is_saved
           FROM posts p
           JOIN users u ON p.user_id = u.id
           WHERE p.user_id IN (
               SELECT followed_id FROM followers 
               WHERE follower_id = ? AND status = 'accepted'
           ) OR p.user_id = ?
           ORDER BY p.created_at DESC
           LIMIT ? OFFSET ?''',
        (session['user_id'], session['user_id'], session['user_id'], session['user_id'], limit, offset)
    ).fetchall()
    
    return jsonify([dict(post) for post in posts])

@app.route('/api/posts/create', methods=['POST'])
@login_required
def create_post():
    content_type = request.form.get('content_type', 'text')
    content = request.form.get('content', '')
    description = request.form.get('description', '')
    visibility = request.form.get('visibility', 'public')
    
    db = get_db()
    
    # Handle file upload if applicable
    filename = None
    if content_type in ['image', 'video'] and 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filename = f"post_{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.split('.')[-1]}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', filename)
            file.save(filepath)
    
    db.execute(
        'INSERT INTO posts (user_id, content_type, content, description, visibility) VALUES (?, ?, ?, ?, ?)',
        (session['user_id'], content_type, filename or content, description, visibility)
    )
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/posts/<int:post_id>', methods=['GET'])
@login_required
def get_post(post_id):
    db = get_db()
    post = db.execute(
        '''SELECT p.*, u.username, u.real_name, u.profile_pic,
           (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as likes_count,
           (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comments_count,
           EXISTS(SELECT 1 FROM likes WHERE post_id = p.id AND user_id = ?) as is_liked,
           EXISTS(SELECT 1 FROM saved_items WHERE post_id = p.id AND user_id = ?) as is_saved
           FROM posts p
           JOIN users u ON p.user_id = u.id
           WHERE p.id = ?''',
        (session['user_id'], session['user_id'], post_id)
    ).fetchone()
    
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    return jsonify(dict(post))

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    db = get_db()
    
    # Check if already liked
    existing_like = db.execute(
        'SELECT * FROM likes WHERE post_id = ? AND user_id = ?', (post_id, session['user_id'])
    ).fetchone()
    
    if existing_like:
        db.execute(
            'DELETE FROM likes WHERE post_id = ? AND user_id = ?', (post_id, session['user_id'])
        )
        action = 'unliked'
    else:
        db.execute(
            'INSERT INTO likes (user_id, post_id) VALUES (?, ?)', (session['user_id'], post_id)
        )
        action = 'liked'
    
    db.commit()
    
    # Get updated like count
    like_count = db.execute(
        'SELECT COUNT(*) FROM likes WHERE post_id = ?', (post_id,)
    ).fetchone()[0]
    
    return jsonify({'action': action, 'like_count': like_count})

@app.route('/api/posts/<int:post_id>/comment', methods=['POST'])
@login_required
def comment_on_post(post_id):
    content = request.form.get('content', '')
    
    if not content:
        return jsonify({'error': 'Comment content is required'}), 400
    
    db = get_db()
    db.execute(
        'INSERT INTO comments (user_id, post_id, content) VALUES (?, ?, ?)',
        (session['user_id'], post_id, content)
    )
    db.commit()
    
    # Get comment count
    comment_count = db.execute(
        'SELECT COUNT(*) FROM comments WHERE post_id = ?', (post_id,)
    ).fetchone()[0]
    
    return jsonify({'success': True, 'comment_count': comment_count})

@app.route('/api/posts/<int:post_id>/comments', methods=['GET'])
@login_required
def get_post_comments(post_id):
    db = get_db()
    comments = db.execute(
        '''SELECT c.*, u.username, u.real_name, u.profile_pic
           FROM comments c
           JOIN users u ON c.user_id = u.id
           WHERE c.post_id = ?
           ORDER BY c.created_at DESC''',
        (post_id,)
    ).fetchall()
    
    return jsonify([dict(comment) for comment in comments])

@app.route('/api/posts/<int:post_id>/save', methods=['POST'])
@login_required
def save_post(post_id):
    db = get_db()
    
    # Check if already saved
    existing_save = db.execute(
        'SELECT * FROM saved_items WHERE post_id = ? AND user_id = ?', (post_id, session['user_id'])
    ).fetchone()
    
    if existing_save:
        db.execute(
            'DELETE FROM saved_items WHERE post_id = ? AND user_id = ?', (post_id, session['user_id'])
        )
        action = 'unsaved'
    else:
        db.execute(
            'INSERT INTO saved_items (user_id, post_id) VALUES (?, ?)', (session['user_id'], post_id)
        )
        action = 'saved'
    
    db.commit()
    
    return jsonify({'action': action})

@app.route('/api/posts/<int:post_id>/repost', methods=['POST'])
@login_required
def repost(post_id):
    db = get_db()
    
    # Check if original post exists
    original_post = db.execute(
        'SELECT * FROM posts WHERE id = ?', (post_id,)
    ).fetchone()
    
    if not original_post:
        return jsonify({'error': 'Post not found'}), 404
    
    # Check if already reposted
    existing_repost = db.execute(
        'SELECT * FROM reposts WHERE original_post_id = ? AND user_id = ?', (post_id, session['user_id'])
    ).fetchone()
    
    if existing_repost:
        db.execute(
            'DELETE FROM reposts WHERE original_post_id = ? AND user_id = ?', (post_id, session['user_id'])
        )
        action = 'unreposted'
    else:
        db.execute(
            'INSERT INTO reposts (user_id, original_post_id) VALUES (?, ?)', (session['user_id'], post_id)
        )
        action = 'reposted'
    
    db.commit()
    
    return jsonify({'action': action})

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    db = get_db()
    
    # Check if post belongs to user
    post = db.execute(
        'SELECT * FROM posts WHERE id = ? AND user_id = ?', (post_id, session['user_id'])
    ).fetchone()
    
    if not post:
        return jsonify({'error': 'Post not found or unauthorized'}), 404
    
    db.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    db.commit()
    
    return jsonify({'success': True})

# Stories routes
@app.route('/api/stories', methods=['GET'])
@login_required
def get_stories():
    db = get_db()
    
    # Get stories from users that the current user follows and that are not expired
    stories = db.execute(
        '''SELECT s.*, u.username, u.real_name, u.profile_pic
           FROM stories s
           JOIN users u ON s.user_id = u.id
           WHERE s.user_id IN (
               SELECT followed_id FROM followers 
               WHERE follower_id = ? AND status = 'accepted'
           ) AND datetime(s.created_at, '+' || s.duration || ' hours') > datetime('now')
           ORDER BY s.created_at DESC''',
        (session['user_id'],)
    ).fetchall()
    
    return jsonify([dict(story) for story in stories])

@app.route('/api/stories/create', methods=['POST'])
@login_required
def create_story():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Determine media type
    file_ext = file.filename.split('.')[-1].lower()
    media_type = 'video' if file_ext in ['mp4', 'mov', 'avi', 'mkv'] else 'image'
    
    # Generate unique filename
    filename = f"story_{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'stories', filename)
    file.save(filepath)
    
    db = get_db()
    db.execute(
        'INSERT INTO stories (user_id, media_url, media_type) VALUES (?, ?, ?)',
        (session['user_id'], filename, media_type)
    )
    db.commit()
    
    return jsonify({'success': True, 'filename': filename})

# Reels routes
@app.route('/api/reels', methods=['GET'])
@login_required
def get_reels():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    offset = (page - 1) * limit
    
    db = get_db()
    reels = db.execute(
        '''SELECT r.*, u.username, u.real_name, u.profile_pic,
           (SELECT COUNT(*) FROM likes WHERE reel_id = r.id) as likes_count,
           (SELECT COUNT(*) FROM comments WHERE reel_id = r.id) as comments_count,
           EXISTS(SELECT 1 FROM likes WHERE reel_id = r.id AND user_id = ?) as is_liked,
           EXISTS(SELECT 1 FROM saved_items WHERE reel_id = r.id AND user_id = ?) as is_saved
           FROM reels r
           JOIN users u ON r.user_id = u.id
           ORDER BY r.created_at DESC
           LIMIT ? OFFSET ?''',
        (session['user_id'], session['user_id'], limit, offset)
    ).fetchall()
    
    return jsonify([dict(reel) for reel in reels])

@app.route('/api/reels/create', methods=['POST'])
@login_required
def create_reel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    description = request.form.get('description', '')
    
    # Generate unique filename
    filename = f"reel_{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.split('.')[-1]}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'reels', filename)
    file.save(filepath)
    
    db = get_db()
    db.execute(
        'INSERT INTO reels (user_id, video_url, description) VALUES (?, ?, ?)',
        (session['user_id'], filename, description)
    )
    db.commit()
    
    return jsonify({'success': True, 'filename': filename})

# Friends and Followers routes
@app.route('/api/friends/follow', methods=['POST'])
@login_required
def follow_user():
    user_id = request.form.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    db = get_db()
    
    # Check if user exists
    user = db.execute(
        'SELECT * FROM users WHERE id = ? AND is_banned = FALSE', (user_id,)
    ).fetchone()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if already following
    existing_follow = db.execute(
        'SELECT * FROM followers WHERE follower_id = ? AND followed_id = ?', (session['user_id'], user_id)
    ).fetchone()
    
    if existing_follow:
        # If already following, unfollow
        db.execute(
            'DELETE FROM followers WHERE follower_id = ? AND followed_id = ?', (session['user_id'], user_id)
        )
        action = 'unfollowed'
    else:
        # Check if user has a locked profile
        settings = db.execute(
            'SELECT profile_locked FROM settings WHERE user_id = ?', (user_id,)
        ).fetchone()
        
        status = 'pending' if settings and settings['profile_locked'] else 'accepted'
        
        db.execute(
            'INSERT INTO followers (follower_id, followed_id, status) VALUES (?, ?, ?)',
            (session['user_id'], user_id, status)
        )
        action = 'followed'
    
    db.commit()
    
    return jsonify({'action': action})

@app.route('/api/friends/requests', methods=['GET'])
@login_required
def get_friend_requests():
    db = get_db()
    requests = db.execute(
        '''SELECT f.*, u.username, u.real_name, u.profile_pic
           FROM followers f
           JOIN users u ON f.follower_id = u.id
           WHERE f.followed_id = ? AND f.status = 'pending'
           ORDER BY f.created_at DESC''',
        (session['user_id'],)
    ).fetchall()
    
    return jsonify([dict(req) for req in requests])

@app.route('/api/friends/requests/respond', methods=['POST'])
@login_required
def respond_to_friend_request():
    follower_id = request.form.get('follower_id')
    action = request.form.get('action')  # 'accept' or 'reject'
    
    if not follower_id or not action:
        return jsonify({'error': 'Follower ID and action are required'}), 400
    
    db = get_db()
    
    if action == 'accept':
        db.execute(
            'UPDATE followers SET status = "accepted" WHERE follower_id = ? AND followed_id = ?',
            (follower_id, session['user_id'])
        )
        
        # Check if this creates a mutual follow (friends)
        mutual_follow = db.execute(
            'SELECT * FROM followers WHERE follower_id = ? AND followed_id = ? AND status = "accepted"',
            (session['user_id'], follower_id)
        ).fetchone()
        
        if mutual_follow:
            # Add to friends table (avoid duplicates)
            existing_friend = db.execute(
                '''SELECT * FROM friends 
                   WHERE (user1_id = ? AND user2_id = ?) 
                   OR (user1_id = ? AND user2_id = ?)''',
                (session['user_id'], follower_id, follower_id, session['user_id'])
            ).fetchone()
            
            if not existing_friend:
                db.execute(
                    'INSERT INTO friends (user1_id, user2_id) VALUES (?, ?)',
                    (min(session['user_id'], follower_id), max(session['user_id'], follower_id))
                )
    else:  # reject
        db.execute(
            'DELETE FROM followers WHERE follower_id = ? AND followed_id = ?',
            (follower_id, session['user_id'])
        )
    
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/friends/suggestions', methods=['GET'])
@login_required
def get_friend_suggestions():
    limit = request.args.get('limit', 10, type=int)
    
    db = get_db()
    
    # Get suggestions: friends of friends, people in same location/school, etc.
    suggestions = db.execute(
        '''SELECT u.*, 
           (SELECT COUNT(*) FROM friends f 
            WHERE (f.user1_id = u.id OR f.user2_id = u.id) 
            AND (f.user1_id IN (SELECT user2_id FROM friends WHERE user1_id = ?) 
                 OR f.user2_id IN (SELECT user1_id FROM friends WHERE user2_id = ?)
                 OR f.user1_id IN (SELECT user1_id FROM friends WHERE user2_id = ?) 
                 OR f.user2_id IN (SELECT user2_id FROM friends WHERE user1_id = ?))
           ) as mutual_count
           FROM users u
           WHERE u.id != ? 
           AND u.is_banned = FALSE
           AND u.id NOT IN (
               SELECT followed_id FROM followers WHERE follower_id = ?
           )
           ORDER BY mutual_count DESC, u.created_at DESC
           LIMIT ?''',
        (session['user_id'], session['user_id'], session['user_id'], session['user_id'], 
         session['user_id'], session['user_id'], limit)
    ).fetchall()
    
    return jsonify([dict(suggestion) for suggestion in suggestions])

# Messages routes
@app.route('/api/messages', methods=['GET'])
@login_required
def get_messages():
    user_id = request.args.get('user_id')
    group_id = request.args.get('group_id')
    limit = request.args.get('limit', 50, type=int)
    
    db = get_db()
    
    if user_id:
        # Direct messages
        messages = db.execute(
            '''SELECT m.*, u.username, u.real_name, u.profile_pic
               FROM messages m
               JOIN users u ON m.sender_id = u.id
               WHERE (m.sender_id = ? AND m.receiver_id = ?)
               OR (m.sender_id = ? AND m.receiver_id = ?)
               ORDER BY m.created_at DESC
               LIMIT ?''',
            (session['user_id'], user_id, user_id, session['user_id'], limit)
        ).fetchall()
    elif group_id:
        # Group messages
        messages = db.execute(
            '''SELECT m.*, u.username, u.real_name, u.profile_pic
               FROM messages m
               JOIN users u ON m.sender_id = u.id
               WHERE m.group_id = ?
               ORDER BY m.created_at DESC
               LIMIT ?''',
            (group_id, limit)
        ).fetchall()
    else:
        # Get recent conversations
        conversations = db.execute(
            '''SELECT u.id as user_id, u.username, u.real_name, u.profile_pic, 
                      MAX(m.created_at) as last_message_time,
                      (SELECT COUNT(*) FROM messages 
                       WHERE (sender_id = u.id AND receiver_id = ?) 
                       OR (sender_id = ? AND receiver_id = u.id) 
                       AND is_read = FALSE) as unread_count
               FROM users u
               JOIN messages m ON (m.sender_id = u.id OR m.receiver_id = u.id)
               WHERE (m.sender_id = ? AND m.receiver_id != ?)
               OR (m.receiver_id = ? AND m.sender_id != ?)
               GROUP BY u.id
               ORDER BY last_message_time DESC''',
            (session['user_id'], session['user_id'], session['user_id'], session['user_id'], 
             session['user_id'], session['user_id'])
        ).fetchall()
        
        return jsonify([dict(conv) for conv in conversations])
    
    return jsonify([dict(msg) for msg in messages])

@app.route('/api/messages/send', methods=['POST'])
@login_required
def send_message():
    receiver_id = request.form.get('receiver_id')
    group_id = request.form.get('group_id')
    content = request.form.get('content', '')
    message_type = request.form.get('message_type', 'text')
    
    if not content and 'file' not in request.files:
        return jsonify({'error': 'Message content or file is required'}), 400
    
    db = get_db()
    
    # Handle file upload if applicable
    media_url = None
    if message_type != 'text' and 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filename = f"message_{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.split('.')[-1]}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'messages', filename)
            file.save(filepath)
            media_url = filename
    
    # Set expiration for disappearing messages
    expires_at = None
    if message_type == 'text' and receiver_id:
        settings = db.execute(
            'SELECT disappearing_messages_duration FROM settings WHERE user_id = ?', (receiver_id,)
        ).fetchone()
        
        if settings and settings['disappearing_messages_duration'] > 0:
            expires_at = datetime.now() + timedelta(hours=settings['disappearing_messages_duration'])
    
    db.execute(
        'INSERT INTO messages (sender_id, receiver_id, group_id, content, message_type, media_url, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (session['user_id'], receiver_id, group_id, content, message_type, media_url, expires_at)
    )
    db.commit()
    
    return jsonify({'success': True})

# Groups routes
@app.route('/api/groups', methods=['GET'])
@login_required
def get_groups():
    db = get_db()
    groups = db.execute(
        '''SELECT g.*, gm.is_admin
           FROM groups g
           JOIN group_members gm ON g.id = gm.group_id
           WHERE gm.user_id = ?
           ORDER BY g.created_at DESC''',
        (session['user_id'],)
    ).fetchall()
    
    return jsonify([dict(group) for group in groups])

@app.route('/api/groups/create', methods=['POST'])
@login_required
def create_group():
    name = request.form.get('name', '')
    description = request.form.get('description', '')
    
    if not name:
        return jsonify({'error': 'Group name is required'}), 400
    
    db = get_db()
    
    # Generate unique link
    import random
    import string
    unique_link = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    
    # Create group
    db.execute(
        'INSERT INTO groups (name, description, unique_link, created_by) VALUES (?, ?, ?, ?)',
        (name, description, unique_link, session['user_id'])
    )
    
    group_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    
    # Add creator as admin
    db.execute(
        'INSERT INTO group_members (group_id, user_id, is_admin) VALUES (?, ?, ?)',
        (group_id, session['user_id'], True)
    )
    db.commit()
    
    return jsonify({'success': True, 'group_id': group_id, 'unique_link': unique_link})

@app.route('/api/groups/<int:group_id>', methods=['GET'])
@login_required
def get_group(group_id):
    db = get_db()
    group = db.execute(
        '''SELECT g.*, 
           (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count,
           EXISTS(SELECT 1 FROM group_members WHERE group_id = g.id AND user_id = ?) as is_member,
           EXISTS(SELECT 1 FROM group_members WHERE group_id = g.id AND user_id = ? AND is_admin = TRUE) as is_admin
           FROM groups g
           WHERE g.id = ?''',
        (session['user_id'], session['user_id'], group_id)
    ).fetchone()
    
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    
    return jsonify(dict(group))

@app.route('/api/groups/<int:group_id>/join', methods=['POST'])
@login_required
def join_group(group_id):
    db = get_db()
    
    # Check if group exists
    group = db.execute(
        'SELECT * FROM groups WHERE id = ?', (group_id,)
    ).fetchone()
    
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    
    # Check if already a member
    existing_member = db.execute(
        'SELECT * FROM group_members WHERE group_id = ? AND user_id = ?', (group_id, session['user_id'])
    ).fetchone()
    
    if existing_member:
        return jsonify({'error': 'Already a member'}), 400
    
    # Check if group requires approval
    if group['approve_new_members']:
        # In a real app, you would create a membership request
        # For simplicity, we'll just add as pending
        return jsonify({'success': True, 'status': 'pending_approval'})
    else:
        db.execute(
            'INSERT INTO group_members (group_id, user_id) VALUES (?, ?)',
            (group_id, session['user_id'])
        )
        db.commit()
        return jsonify({'success': True, 'status': 'joined'})

# Notifications routes
@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    limit = request.args.get('limit', 20, type=int)
    
    db = get_db()
    notifications = db.execute(
        '''SELECT n.*, u.username, u.real_name, u.profile_pic
           FROM notifications n
           LEFT JOIN users u ON n.source_id = u.id
           WHERE n.user_id = ?
           ORDER BY n.created_at DESC
           LIMIT ?''',
        (session['user_id'], limit)
    ).fetchall()
    
    # Mark as read
    db.execute(
        'UPDATE notifications SET is_read = TRUE WHERE user_id = ? AND is_read = FALSE',
        (session['user_id'],)
    )
    db.commit()
    
    return jsonify([dict(notif) for notif in notifications])

@app.route('/api/notifications/count', methods=['GET'])
@login_required
def get_unread_notification_count():
    db = get_db()
    count = db.execute(
        'SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = FALSE',
        (session['user_id'],)
    ).fetchone()[0]
    
    return jsonify({'count': count})

# Search routes
@app.route('/api/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('q', '')
    type_filter = request.args.get('type', 'all')  # all, users, groups, posts
    limit = request.args.get('limit', 20, type=int)
    
    if not query:
        return jsonify({'error': 'Search query is required'}), 400
    
    db = get_db()
    results = {}
    
    if type_filter in ['all', 'users']:
        users = db.execute(
            '''SELECT u.*, 
               EXISTS(SELECT 1 FROM followers WHERE follower_id = ? AND followed_id = u.id AND status = 'accepted') as is_following
               FROM users u
               WHERE (u.username LIKE ? OR u.real_name LIKE ?) 
               AND u.is_banned = FALSE
               ORDER BY u.username
               LIMIT ?''',
            (session['user_id'], f'%{query}%', f'%{query}%', limit)
        ).fetchall()
        results['users'] = [dict(user) for user in users]
    
    if type_filter in ['all', 'groups']:
        groups = db.execute(
            '''SELECT g.*, 
               (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count,
               EXISTS(SELECT 1 FROM group_members WHERE group_id = g.id AND user_id = ?) as is_member
               FROM groups g
               WHERE g.name LIKE ? OR g.description LIKE ?
               ORDER BY g.name
               LIMIT ?''',
            (session['user_id'], f'%{query}%', f'%{query}%', limit)
        ).fetchall()
        results['groups'] = [dict(group) for group in groups]
    
    if type_filter in ['all', 'posts']:
        posts = db.execute(
            '''SELECT p.*, u.username, u.real_name, u.profile_pic,
               (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as likes_count,
               (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comments_count,
               EXISTS(SELECT 1 FROM likes WHERE post_id = p.id AND user_id = ?) as is_liked
               FROM posts p
               JOIN users u ON p.user_id = u.id
               WHERE p.description LIKE ? AND p.visibility IN ('public', 
                   CASE WHEN p.user_id IN (SELECT followed_id FROM followers WHERE follower_id = ? AND status = 'accepted') THEN 'friends' ELSE 'public' END,
                   CASE WHEN p.user_id = ? THEN 'private' ELSE 'public' END)
               ORDER BY p.created_at DESC
               LIMIT ?''',
            (session['user_id'], f'%{query}%', session['user_id'], session['user_id'], limit)
        ).fetchall()
        results['posts'] = [dict(post) for post in posts]
    
    return jsonify(results)

# Settings routes
@app.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    db = get_db()
    settings = db.execute(
        'SELECT * FROM settings WHERE user_id = ?', (session['user_id'],)
    ).fetchone()
    
    if not settings:
        # Create default settings if they don't exist
        db.execute(
            'INSERT INTO settings (user_id) VALUES (?)', (session['user_id'],)
        )
        db.commit()
        settings = db.execute(
            'SELECT * FROM settings WHERE user_id = ?', (session['user_id'],)
        ).fetchone()
    
    return jsonify(dict(settings))

@app.route('/api/settings/update', methods=['POST'])
@login_required
def update_settings():
    data = request.form.to_dict()
    
    db = get_db()
    
    # Build update query dynamically
    update_fields = []
    values = []
    
    for field in ['theme', 'language', 'profile_locked', 'post_visibility', 
                  'allow_sharing', 'allow_comments', 'notifications_enabled', 
                  'notification_types', 'disappearing_messages_duration']:
        if field in data:
            update_fields.append(f'{field} = ?')
            # Convert boolean values
            if data[field].lower() in ['true', 'false']:
                values.append(data[field].lower() == 'true')
            else:
                values.append(data[field])
    
    if update_fields:
        values.append(session['user_id'])
        query = f'UPDATE settings SET {", ".join(update_fields)} WHERE user_id = ?'
        db.execute(query, values)
        db.commit()
    
    return jsonify({'success': True})

# Admin routes
@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_get_users():
    db = get_db()
    users = db.execute(
        'SELECT id, username, real_name, created_at, is_banned, warnings FROM users ORDER BY created_at DESC'
    ).fetchall()
    
    return jsonify([dict(user) for user in users])

@app.route('/api/admin/users/<int:user_id>/ban', methods=['POST'])
@admin_required
def admin_ban_user(user_id):
    reason = request.form.get('reason', '')
    
    db = get_db()
    db.execute(
        'UPDATE users SET is_banned = TRUE WHERE id = ?', (user_id,)
    )
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/admin/users/<int:user_id>/warn', methods=['POST'])
@admin_required
def admin_warn_user(user_id):
    db = get_db()
    
    # Get current warnings
    user = db.execute(
        'SELECT warnings FROM users WHERE id = ?', (user_id,)
    ).fetchone()
    
    warnings = user['warnings'] + 1
    
    db.execute(
        'UPDATE users SET warnings = ? WHERE id = ?', (warnings, user_id)
    )
    db.commit()
    
    return jsonify({'success': True, 'warnings': warnings})

@app.route('/api/admin/reports', methods=['GET'])
@admin_required
def admin_get_reports():
    status = request.args.get('status', 'pending')
    
    db = get_db()
    reports = db.execute(
        '''SELECT r.*, 
           u1.username as reporter_username,
           u2.username as reported_user_username,
           p.description as reported_post_description,
           reel.description as reported_reel_description,
           g.name as reported_group_name
           FROM reports r
           LEFT JOIN users u1 ON r.reporter_id = u1.id
           LEFT JOIN users u2 ON r.reported_user_id = u2.id
           LEFT JOIN posts p ON r.reported_post_id = p.id
           LEFT JOIN reels reel ON r.reported_reel_id = reel.id
           LEFT JOIN groups g ON r.reported_group_id = g.id
           WHERE r.status = ?
           ORDER BY r.created_at DESC''',
        (status,)
    ).fetchall()
    
    return jsonify([dict(report) for report in reports])

@app.route('/api/admin/reports/<int:report_id>/resolve', methods=['POST'])
@admin_required
def admin_resolve_report(report_id):
    action = request.form.get('action', 'dismiss')  # 'dismiss' or 'take_action'
    
    db = get_db()
    db.execute(
        'UPDATE reports SET status = ? WHERE id = ?',
        ('resolved' if action == 'take_action' else 'reviewed', report_id)
    )
    db.commit()
    
    return jsonify({'success': True})

# File serving route
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
