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
from flask import Flask, request, jsonify, session, render_template, g, redirect, url_for, send_from_directory

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

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                real_name TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                profile_pic_url TEXT,
                bio TEXT,
                is_admin INTEGER DEFAULT 0,
                is_blocked INTEGER DEFAULT 0,
                join_date TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                content TEXT,
                media_url TEXT,
                timestamp TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reels (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                content TEXT,
                media_url TEXT,
                timestamp TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                media_url TEXT,
                timestamp TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT,
                user_id TEXT,
                FOREIGN KEY(post_id) REFERENCES posts(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT,
                user_id TEXT,
                text TEXT,
                timestamp TEXT,
                FOREIGN KEY(post_id) REFERENCES posts(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id TEXT,
                user2_id TEXT,
                status TEXT, -- 'pending', 'accepted'
                timestamp TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id TEXT,
                receiver_id TEXT,
                text TEXT,
                timestamp TEXT,
                read INTEGER DEFAULT 0,
                is_group INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                creator_id TEXT,
                profile_pic_url TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
                group_id TEXT,
                user_id TEXT,
                PRIMARY KEY (group_id, user_id),
                FOREIGN KEY(group_id) REFERENCES groups(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                type TEXT, -- 'like', 'comment', 'friend_request', 'message'
                source_id TEXT, -- post_id, message_id, etc.
                text TEXT,
                timestamp TEXT,
                read INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id TEXT,
                target_id TEXT, -- user_id or post_id
                target_type TEXT, -- 'user' or 'post'
                reason TEXT,
                timestamp TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)
        db.commit()

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
    @login_required
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        db = get_db()
        cursor = db.cursor()
        user = cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user or user['is_admin'] != 1:
            return jsonify({'error': 'Forbidden'}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- User & Auth Endpoints ---

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    real_name = data.get('real_name')
    password = data.get('password')
    if not all([username, email, real_name, password]):
        return jsonify({'error': 'Missing data'}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        hashed_password = generate_password_hash(password)
        user_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO users (id, username, real_name, email, password, join_date) VALUES (?, ?, ?, ?, ?, ?)",
                       (user_id, username, real_name, email, hashed_password, datetime.now().isoformat()))
        db.commit()
        return jsonify({'message': 'User registered successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username or email already exists'}), 409

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    db = get_db()
    cursor = db.cursor()
    user = cursor.execute("SELECT id, password, is_admin FROM users WHERE username = ?", (username,)).fetchone()
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['is_admin'] = user['is_admin']
        return jsonify({'message': 'Login successful', 'is_admin': bool(user['is_admin']), 'user_id': user['id']})
    return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/api/auth/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/user/profile/<user_id>')
def get_user_profile(user_id):
    db = get_db()
    cursor = db.cursor()
    user = cursor.execute("SELECT id, username, real_name, profile_pic_url, bio, is_admin FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if a friend request has been sent
    is_friend = False
    is_pending = False
    if 'user_id' in session and session['user_id'] != user_id:
        friend_status = cursor.execute("SELECT status FROM friends WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)",
                                       (session['user_id'], user_id, user_id, session['user_id'])).fetchone()
        if friend_status:
            is_friend = (friend_status['status'] == 'accepted')
            is_pending = (friend_status['status'] == 'pending')

    posts = cursor.execute("SELECT * FROM posts WHERE user_id = ? ORDER BY timestamp DESC", (user_id,)).fetchall()
    reels = cursor.execute("SELECT * FROM reels WHERE user_id = ? ORDER BY timestamp DESC", (user_id,)).fetchall()

    profile_data = dict(user)
    profile_data['is_friend'] = is_friend
    profile_data['is_pending'] = is_pending
    profile_data['posts'] = [dict(p) for p in posts]
    profile_data['reels'] = [dict(r) for r in reels]

    return jsonify(profile_data)

@app.route('/api/user/profile', methods=['POST'])
@login_required
def update_profile():
    data = request.form
    user_id = session['user_id']
    bio = data.get('bio')
    
    db = get_db()
    cursor = db.cursor()

    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{user_id}_{uuid.uuid4()}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            profile_pic_url = f'/static/uploads/{filename}'
            cursor.execute("UPDATE users SET profile_pic_url = ? WHERE id = ?", (profile_pic_url, user_id))

    if bio:
        cursor.execute("UPDATE users SET bio = ? WHERE id = ?", (bio, user_id))

    db.commit()
    return jsonify({'message': 'Profile updated successfully'})

# --- Content Endpoints (Posts, Reels, Stories) ---

@app.route('/api/posts/create', methods=['POST'])
@login_required
def create_post():
    data = request.form
    user_id = session['user_id']
    content = data.get('content', '')
    media_url = ''

    if 'media' in request.files:
        file = request.files['media']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{user_id}_{uuid.uuid4()}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            media_url = f'/static/uploads/{filename}'

    db = get_db()
    cursor = db.cursor()
    post_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO posts (id, user_id, content, media_url, timestamp) VALUES (?, ?, ?, ?, ?)",
                   (post_id, user_id, content, media_url, datetime.now().isoformat()))
    db.commit()
    return jsonify({'message': 'Post created successfully', 'post_id': post_id})

@app.route('/api/posts/feed')
@login_required
def get_posts_feed():
    user_id = session['user_id']
    page = int(request.args.get('page', 1))
    limit = 10
    offset = (page - 1) * limit
    db = get_db()
    cursor = db.cursor()
    
    # Get friends' posts and own posts
    friend_ids = [row['user2_id'] for row in cursor.execute("SELECT user2_id FROM friends WHERE user1_id = ? AND status = 'accepted'", (user_id,)).fetchall()]
    friend_ids.extend([row['user1_id'] for row in cursor.execute("SELECT user1_id FROM friends WHERE user2_id = ? AND status = 'accepted'", (user_id,)).fetchall()])
    friend_ids = list(set(friend_ids + [user_id])) # include own posts
    
    if not friend_ids:
        return jsonify([])

    placeholders = ','.join('?' for _ in friend_ids)
    
    posts = cursor.execute(f"""
        SELECT p.*, u.username, u.profile_pic_url, u.real_name,
               (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as like_count,
               (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count,
               (SELECT 1 FROM likes WHERE post_id = p.id AND user_id = ?) as is_liked
        FROM posts p JOIN users u ON p.user_id = u.id
        WHERE p.user_id IN ({placeholders})
        ORDER BY p.timestamp DESC
        LIMIT ? OFFSET ?
    """, (user_id,) + tuple(friend_ids) + (limit, offset)).fetchall()

    return jsonify([dict(p) for p in posts])

@app.route('/api/posts/like/<post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    like = cursor.execute("SELECT * FROM likes WHERE post_id = ? AND user_id = ?", (post_id, user_id)).fetchone()
    if like:
        cursor.execute("DELETE FROM likes WHERE post_id = ? AND user_id = ?", (post_id, user_id))
    else:
        cursor.execute("INSERT INTO likes (post_id, user_id) VALUES (?, ?)", (post_id, user_id))
        post_owner_id = cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,)).fetchone()['user_id']
        cursor.execute("INSERT INTO notifications (user_id, type, source_id, text, timestamp) VALUES (?, ?, ?, ?, ?)",
                       (post_owner_id, 'like', post_id, f'Your post was liked by a friend.', datetime.now().isoformat()))
    db.commit()
    return jsonify({'message': 'Toggled like'})

@app.route('/api/posts/comment/<post_id>', methods=['POST'])
@login_required
def comment_on_post(post_id):
    data = request.json
    user_id = session['user_id']
    text = data.get('text')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO comments (post_id, user_id, text, timestamp) VALUES (?, ?, ?, ?)",
                   (post_id, user_id, text, datetime.now().isoformat()))
    post_owner_id = cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,)).fetchone()['user_id']
    cursor.execute("INSERT INTO notifications (user_id, type, source_id, text, timestamp) VALUES (?, ?, ?, ?, ?)",
                   (post_owner_id, 'comment', post_id, f'Your post was commented on by a friend.', datetime.now().isoformat()))
    db.commit()
    return jsonify({'message': 'Comment added'})

@app.route('/api/posts/comments/<post_id>')
@login_required
def get_comments(post_id):
    db = get_db()
    cursor = db.cursor()
    comments = cursor.execute("""
        SELECT c.*, u.username, u.profile_pic_url FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id = ? ORDER BY c.timestamp ASC
    """, (post_id,)).fetchall()
    return jsonify([dict(c) for c in comments])

# Reels
@app.route('/api/reels/create', methods=['POST'])
@login_required
def create_reel():
    data = request.form
    user_id = session['user_id']
    content = data.get('content', '')
    media_url = ''

    if 'media' in request.files:
        file = request.files['media']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{user_id}_{uuid.uuid4()}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            media_url = f'/static/uploads/{filename}'
    else:
        return jsonify({'error': 'No video file provided'}), 400

    db = get_db()
    cursor = db.cursor()
    reel_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO reels (id, user_id, content, media_url, timestamp) VALUES (?, ?, ?, ?, ?)",
                   (reel_id, user_id, content, media_url, datetime.now().isoformat()))
    db.commit()
    return jsonify({'message': 'Reel created successfully', 'reel_id': reel_id})

@app.route('/api/reels/feed')
@login_required
def get_reels_feed():
    user_id = session['user_id']
    page = int(request.args.get('page', 1))
    limit = 5
    offset = (page - 1) * limit
    db = get_db()
    cursor = db.cursor()

    friend_ids = [row['user2_id'] for row in cursor.execute("SELECT user2_id FROM friends WHERE user1_id = ? AND status = 'accepted'", (user_id,)).fetchall()]
    friend_ids.extend([row['user1_id'] for row in cursor.execute("SELECT user1_id FROM friends WHERE user2_id = ? AND status = 'accepted'", (user_id,)).fetchall()])
    friend_ids = list(set(friend_ids + [user_id]))
    
    if not friend_ids:
        return jsonify([])

    placeholders = ','.join('?' for _ in friend_ids)

    reels = cursor.execute(f"""
        SELECT r.*, u.username, u.profile_pic_url, u.real_name,
               (SELECT COUNT(*) FROM likes WHERE post_id = r.id) as like_count,
               (SELECT COUNT(*) FROM comments WHERE post_id = r.id) as comment_count,
               (SELECT 1 FROM likes WHERE post_id = r.id AND user_id = ?) as is_liked
        FROM reels r JOIN users u ON r.user_id = u.id
        WHERE r.user_id IN ({placeholders})
        ORDER BY r.timestamp DESC
        LIMIT ? OFFSET ?
    """, (user_id,) + tuple(friend_ids) + (limit, offset)).fetchall()

    return jsonify([dict(r) for r in reels])

# Stories
@app.route('/api/stories/create', methods=['POST'])
@login_required
def create_story():
    user_id = session['user_id']
    media_url = ''
    if 'media' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['media']
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{user_id}_{uuid.uuid4()}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        media_url = f'/static/uploads/{filename}'
    else:
        return jsonify({'error': 'Invalid file type'}), 400

    db = get_db()
    cursor = db.cursor()
    story_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO stories (id, user_id, media_url, timestamp) VALUES (?, ?, ?, ?)",
                   (story_id, user_id, media_url, datetime.now().isoformat()))
    db.commit()
    return jsonify({'message': 'Story created successfully', 'story_id': story_id})

@app.route('/api/stories/feed')
@login_required
def get_stories_feed():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    friend_ids = [row['user2_id'] for row in cursor.execute("SELECT user2_id FROM friends WHERE user1_id = ? AND status = 'accepted'", (user_id,)).fetchall()]
    friend_ids.extend([row['user1_id'] for row in cursor.execute("SELECT user1_id FROM friends WHERE user2_id = ? AND status = 'accepted'", (user_id,)).fetchall()])
    friend_ids = list(set(friend_ids + [user_id]))

    if not friend_ids:
        return jsonify([])

    placeholders = ','.join('?' for _ in friend_ids)
    
    stories_raw = cursor.execute(f"""
        SELECT s.*, u.username, u.profile_pic_url, u.real_name
        FROM stories s JOIN users u ON s.user_id = u.id
        WHERE s.user_id IN ({placeholders}) AND s.timestamp > ?
        ORDER BY s.timestamp DESC
    """, tuple(friend_ids) + ((datetime.now() - timedelta(hours=24)).isoformat(),)).fetchall()
    
    stories_by_user = {}
    for story in stories_raw:
        if story['user_id'] not in stories_by_user:
            stories_by_user[story['user_id']] = {
                'username': story['username'],
                'profile_pic_url': story['profile_pic_url'],
                'stories': []
            }
        stories_by_user[story['user_id']]['stories'].append(dict(story))
    
    return jsonify(list(stories_by_user.values()))

# --- Friend Endpoints ---

@app.route('/api/friends/add/<target_id>', methods=['POST'])
@login_required
def send_friend_request(target_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    # Check if request already exists
    req = cursor.execute("SELECT * FROM friends WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)",
                         (user_id, target_id, target_id, user_id)).fetchone()
    if req:
        return jsonify({'error': 'Friend request already sent or users are already friends'}), 409
    
    cursor.execute("INSERT INTO friends (user1_id, user2_id, status, timestamp) VALUES (?, ?, 'pending', ?)",
                   (user_id, target_id, datetime.now().isoformat()))
    db.commit()
    return jsonify({'message': 'Friend request sent'})

@app.route('/api/friends/requests')
@login_required
def get_friend_requests():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    requests = cursor.execute("""
        SELECT f.*, u.username, u.real_name, u.profile_pic_url FROM friends f
        JOIN users u ON f.user1_id = u.id
        WHERE f.user2_id = ? AND f.status = 'pending'
    """, (user_id,)).fetchall()
    return jsonify([dict(r) for r in requests])

@app.route('/api/friends/accept/<request_id>', methods=['POST'])
@login_required
def accept_friend_request(request_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE friends SET status = 'accepted' WHERE id = ? AND user2_id = ?", (request_id, user_id))
    db.commit()
    return jsonify({'message': 'Friend request accepted'})

@app.route('/api/friends/reject/<request_id>', methods=['POST'])
@login_required
def reject_friend_request(request_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM friends WHERE id = ? AND user2_id = ?", (request_id, user_id))
    db.commit()
    return jsonify({'message': 'Friend request rejected'})

@app.route('/api/friends')
@login_required
def get_friends():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    friends = cursor.execute("""
        SELECT u.id, u.username, u.real_name, u.profile_pic_url FROM friends f
        JOIN users u ON (u.id = f.user1_id OR u.id = f.user2_id)
        WHERE (f.user1_id = ? OR f.user2_id = ?) AND f.status = 'accepted' AND u.id != ?
    """, (user_id, user_id, user_id)).fetchall()
    return jsonify([dict(f) for f in friends])

# --- Messaging Endpoints ---

@app.route('/api/inbox/chats')
@login_required
def get_inbox_chats():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    # Get all direct chat IDs
    chat_ids = [row['sender_id'] for row in cursor.execute("SELECT DISTINCT sender_id FROM messages WHERE receiver_id = ? AND is_group = 0", (user_id,)).fetchall()]
    chat_ids.extend([row['receiver_id'] for row in cursor.execute("SELECT DISTINCT receiver_id FROM messages WHERE sender_id = ? AND is_group = 0", (user_id,)).fetchall()])
    chat_ids = list(set(chat_ids))
    
    chats = []
    for chat_id in chat_ids:
        if chat_id == user_id: continue
        user = cursor.execute("SELECT id, username, real_name, profile_pic_url FROM users WHERE id = ?", (chat_id,)).fetchone()
        if user:
            user = dict(user)
            last_msg = cursor.execute("SELECT text, timestamp FROM messages WHERE ((sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)) AND is_group = 0 ORDER BY timestamp DESC LIMIT 1", (user_id, chat_id, chat_id, user_id)).fetchone()
            user['last_message'] = last_msg['text'] if last_msg else ''
            user['last_timestamp'] = last_msg['timestamp'] if last_msg else ''
            user['unread'] = cursor.execute("SELECT COUNT(*) as unread FROM messages WHERE sender_id = ? AND receiver_id = ? AND is_group = 0 AND read = 0", (chat_id, user_id)).fetchone()['unread']
            chats.append(user)

    # Get all group chat IDs
    group_ids = [row['group_id'] for row in cursor.execute("SELECT group_id FROM group_members WHERE user_id = ?", (user_id,)).fetchall()]

    for group_id in group_ids:
        group = cursor.execute("SELECT id, name, profile_pic_url FROM groups WHERE id = ?", (group_id,)).fetchone()
        if group:
            group = dict(group)
            last_msg = cursor.execute("SELECT text, timestamp FROM messages WHERE receiver_id = ? AND is_group = 1 ORDER BY timestamp DESC LIMIT 1", (group_id,)).fetchone()
            group['last_message'] = last_msg['text'] if last_msg else ''
            group['last_timestamp'] = last_msg['timestamp'] if last_msg else ''
            group['unread'] = cursor.execute("SELECT COUNT(*) as unread FROM messages WHERE receiver_id = ? AND is_group = 1 AND read = 0 AND sender_id != ?", (group_id, user_id)).fetchone()['unread']
            group['is_group'] = True
            chats.append(group)

    chats.sort(key=lambda x: x['last_timestamp'], reverse=True)
    return jsonify(chats)

@app.route('/api/inbox/messages/<target_id>')
@login_required
def get_messages(target_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    messages = cursor.execute("""
        SELECT m.*, u.username, u.profile_pic_url, (SELECT 1 FROM group_members WHERE group_id = ? AND user_id = m.sender_id) AS is_group_member
        FROM messages m JOIN users u ON m.sender_id = u.id
        WHERE (m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?)
        ORDER BY m.timestamp ASC
    """, (target_id, user_id, target_id, target_id, user_id)).fetchall()
    
    # Mark messages as read
    cursor.execute("UPDATE messages SET read = 1 WHERE sender_id = ? AND receiver_id = ?", (target_id, user_id))
    db.commit()

    return jsonify([dict(m) for m in messages])

@app.route('/api/inbox/send', methods=['POST'])
@login_required
def send_message():
    data = request.json
    sender_id = session['user_id']
    receiver_id = data.get('receiver_id')
    text = data.get('text')
    is_group = data.get('is_group', False)

    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO messages (sender_id, receiver_id, text, timestamp, is_group) VALUES (?, ?, ?, ?, ?)",
                   (sender_id, receiver_id, text, datetime.now().isoformat(), is_group))
    db.commit()
    return jsonify({'message': 'Message sent'})

# --- Group Endpoints ---

@app.route('/api/group/create', methods=['POST'])
@login_required
def create_group():
    data = request.json
    creator_id = session['user_id']
    name = data.get('name')
    description = data.get('description', '')
    
    db = get_db()
    cursor = db.cursor()
    group_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO groups (id, name, description, creator_id) VALUES (?, ?, ?, ?)",
                   (group_id, name, description, creator_id))
    cursor.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, creator_id))
    db.commit()
    return jsonify({'message': 'Group created successfully', 'group_id': group_id})

@app.route('/api/group/members/<group_id>')
@login_required
def get_group_members(group_id):
    db = get_db()
    cursor = db.cursor()
    members = cursor.execute("""
        SELECT u.id, u.username, u.real_name, u.profile_pic_url FROM group_members gm
        JOIN users u ON gm.user_id = u.id
        WHERE gm.group_id = ?
    """, (group_id,)).fetchall()
    return jsonify([dict(m) for m in members])

@app.route('/api/group/add_member', methods=['POST'])
@login_required
def add_group_member():
    data = request.json
    group_id = data.get('group_id')
    user_id = data.get('user_id')
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, user_id))
        db.commit()
        return jsonify({'message': 'User added to group'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'User is already a member'}), 409

@app.route('/api/group/leave/<group_id>', methods=['POST'])
@login_required
def leave_group(group_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
    db.commit()
    return jsonify({'message': 'Left group successfully'})


# --- Search & Notifications Endpoints ---

@app.route('/api/search')
@login_required
def search():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify({'users': [], 'posts': []})
    db = get_db()
    cursor = db.cursor()
    
    users = cursor.execute("SELECT id, username, real_name, profile_pic_url FROM users WHERE username LIKE ? OR real_name LIKE ?", 
                           (f'%{query}%', f'%{query}%')).fetchall()
    
    posts = cursor.execute("""
        SELECT p.*, u.username, u.profile_pic_url FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.content LIKE ?
    """, (f'%{query}%',)).fetchall()

    return jsonify({'users': [dict(u) for u in users], 'posts': [dict(p) for p in posts]})

@app.route('/api/notifications')
@login_required
def get_notifications():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    notifications = cursor.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY timestamp DESC", (user_id,)).fetchall()
    # Mark as read
    cursor.execute("UPDATE notifications SET read = 1 WHERE user_id = ?", (user_id,))
    db.commit()
    return jsonify([dict(n) for n in notifications])


# --- Admin Endpoints ---

@app.route('/api/admin/reports/posts')
@admin_required
def get_reported_posts():
    db = get_db()
    cursor = db.cursor()
    reports = cursor.execute("""
        SELECT r.*, p.content, p.media_url, u.username, u.real_name FROM reports r
        JOIN posts p ON r.target_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE r.target_type = 'post'
    """).fetchall()
    return jsonify([dict(r) for r in reports])

@app.route('/api/admin/reports/users')
@admin_required
def get_reported_users():
    db = get_db()
    cursor = db.cursor()
    reports = cursor.execute("""
        SELECT r.*, u.username, u.real_name, u.profile_pic_url FROM reports r
        JOIN users u ON r.target_id = u.id
        WHERE r.target_type = 'user'
    """).fetchall()
    return jsonify([dict(r) for r in reports])

@app.route('/api/admin/delete_post/<post_id>', methods=['POST'])
@admin_required
def admin_delete_post(post_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    cursor.execute("DELETE FROM reports WHERE target_id = ?", (post_id,))
    db.commit()
    return jsonify({'message': 'Post deleted'})

@app.route('/api/admin/ban_user/<user_id>', methods=['POST'])
@admin_required
def admin_ban_user(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET is_blocked = 1 WHERE id = ?", (user_id,))
    cursor.execute("DELETE FROM reports WHERE target_id = ?", (user_id,))
    db.commit()
    return jsonify({'message': 'User banned'})

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
        for user_id in users:
            cursor.execute("INSERT INTO messages (sender_id, receiver_id, text, timestamp) VALUES ('admin', ?, ?, ?)",
                           (user_id, message, datetime.now().isoformat()))
    else:
        cursor.execute("INSERT INTO messages (sender_id, receiver_id, text, timestamp) VALUES ('admin', ?, ?, ?)",
                       (target_id, message, datetime.now().isoformat()))
    db.commit()
    return jsonify({'message': 'System message sent'})

# --- General Utility Endpoints ---
@app.route('/api/report', methods=['POST'])
@login_required
def report_content():
    data = request.json
    reporter_id = session['user_id']
    target_id = data.get('target_id')
    target_type = data.get('target_type') # 'post' or 'user'
    reason = data.get('reason')
    
    if target_type not in ['post', 'user'] or not target_id or not reason:
        return jsonify({'error': 'Invalid report data'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO reports (reporter_id, target_id, target_type, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
                   (reporter_id, target_id, target_type, reason, datetime.now().isoformat()))
    db.commit()
    return jsonify({'message': 'Report submitted'})

# Serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
