# app.py (fully adjusted and completed backend with all required API endpoints)

import os
import sqlite3
import random
import string
import uuid
import json
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, session, render_template, g, redirect, url_for

app = Flask(__name__)
# Load configuration from config.py
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                real_name TEXT NOT NULL,
                email TEXT UNIQUE,
                password TEXT NOT NULL,
                profile_pic_url TEXT,
                bio TEXT,
                active BOOLEAN DEFAULT 1,
                is_admin BOOLEAN DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                description TEXT,
                media_url TEXT NOT NULL,
                media_type TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reels (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                description TEXT,
                media_url TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                media_url TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friendships (
                user_id TEXT NOT NULL,
                friend_id TEXT NOT NULL,
                status TEXT NOT NULL,
                PRIMARY KEY (user_id, friend_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (friend_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                sender_id TEXT NOT NULL,
                receiver_id TEXT NOT NULL,
                text TEXT,
                media_url TEXT,
                is_group BOOLEAN DEFAULT 0,
                read BOOLEAN DEFAULT 0,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (sender_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                admin_id TEXT NOT NULL,
                profile_pic_url TEXT,
                FOREIGN KEY (admin_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_members (
                group_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                PRIMARY KEY (group_id, user_id),
                FOREIGN KEY (group_id) REFERENCES groups(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                read BOOLEAN DEFAULT 0,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS likes (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                content_id TEXT NOT NULL,
                content_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                content_id TEXT NOT NULL,
                content_type TEXT NOT NULL,
                text TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                reporter_id TEXT NOT NULL,
                reported_id TEXT NOT NULL,
                content_type TEXT NOT NULL,
                content_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                timestamp TEXT NOT NULL,
                FOREIGN KEY (reporter_id) REFERENCES users(id)
            )
        ''')
        # Check if admin user exists, if not, create it
        cursor.execute("SELECT * FROM users WHERE username = ?", (app.config['ADMIN_USERNAME'],))
        admin_user = cursor.fetchone()
        if not admin_user:
            admin_id = str(uuid.uuid4())
            admin_pass_hash = generate_password_hash(app.config['ADMIN_PASS'])
            cursor.execute("INSERT INTO users (id, username, real_name, password, is_admin) VALUES (?, ?, ?, ?, ?)",
                           (admin_id, app.config['ADMIN_USERNAME'], 'Admin', admin_pass_hash, True))
        db.commit()

init_db()

# --- Utility Functions ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required.'}), 401
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT is_admin FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        if not user or not user['is_admin']:
            return jsonify({'success': False, 'message': 'Admin access required.'}), 403
        return f(*args, **kwargs)
    return decorated_function

def get_user_info(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, username, real_name, profile_pic_url, bio FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    return dict(user) if user else None

def send_notification(user_id, type, content):
    db = get_db()
    cursor = db.cursor()
    notif_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO notifications (id, user_id, type, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                   (notif_id, user_id, type, content, datetime.now().isoformat()))
    db.commit()

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    real_name = data.get('real_name')
    password = data.get('password')
    if not username or not real_name or not password:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        user_id = str(uuid.uuid4())
        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO users (id, username, real_name, password) VALUES (?, ?, ?, ?)",
                       (user_id, username, real_name, hashed_password))
        db.commit()
        return jsonify({'success': True, 'message': 'Registration successful.'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Username already exists.'}), 409

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['is_admin'] = user['is_admin']
        return jsonify({'success': True, 'message': 'Login successful.', 'user_id': user['id'], 'is_admin': user['is_admin']})
    return jsonify({'success': False, 'message': 'Invalid credentials.'}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    return jsonify({'success': True, 'message': 'Logout successful.'})

@app.route('/api/profile/<user_id>', methods=['GET'])
@login_required
def get_profile(user_id):
    user = get_user_info(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404
    db = get_db()
    cursor = db.cursor()
    # Check friendship status
    status = 'none'
    current_user_id = session['user_id']
    if current_user_id != user_id:
        cursor.execute("SELECT status FROM friendships WHERE user_id = ? AND friend_id = ?",
                       (current_user_id, user_id))
        friendship = cursor.fetchone()
        if friendship:
            status = friendship['status']
        else:
            cursor.execute("SELECT status FROM friendships WHERE user_id = ? AND friend_id = ?",
                           (user_id, current_user_id))
            friendship = cursor.fetchone()
            if friendship:
                status = 'pending_response' if friendship['status'] == 'pending' else status
    
    # Get user posts
    cursor.execute("SELECT * FROM posts WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    posts = [dict(row) for row in cursor.fetchall()]
    return jsonify({'success': True, 'user': user, 'friendship_status': status, 'posts': posts})

@app.route('/api/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    data = request.json
    bio = data.get('bio')
    profile_pic = request.files.get('profile_pic')
    db = get_db()
    cursor = db.cursor()
    updates = []
    params = []
    
    if bio is not None:
        updates.append("bio = ?")
        params.append(bio)
    
    if profile_pic and allowed_file(profile_pic.filename):
        filename = secure_filename(profile_pic.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        profile_pic.save(filepath)
        updates.append("profile_pic_url = ?")
        params.append(f"/static/uploads/{filename}")

    if not updates:
        return jsonify({'success': False, 'message': 'No data to update.'}), 400
    
    updates_str = ", ".join(updates)
    params.append(session['user_id'])
    cursor.execute(f"UPDATE users SET {updates_str} WHERE id = ?", tuple(params))
    db.commit()
    return jsonify({'success': True, 'message': 'Profile updated successfully.'})

# --- Content Routes (Posts, Reels, Stories) ---

@app.route('/api/post/create', methods=['POST'])
@login_required
def create_post():
    if 'media' not in request.files:
        return jsonify({'success': False, 'message': 'No media file provided.'}), 400
    media = request.files['media']
    if media.filename == '' or not allowed_file(media.filename):
        return jsonify({'success': False, 'message': 'Invalid file type.'}), 400

    description = request.form.get('description', '')
    filename = secure_filename(media.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    media.save(filepath)
    
    db = get_db()
    cursor = db.cursor()
    post_id = str(uuid.uuid4())
    media_url = f"/static/uploads/{filename}"
    media_type = 'image' if media.filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'} else 'video'
    
    cursor.execute("INSERT INTO posts (id, user_id, description, media_url, media_type, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                   (post_id, session['user_id'], description, media_url, media_type, datetime.now().isoformat()))
    db.commit()
    return jsonify({'success': True, 'message': 'Post created successfully.'})

@app.route('/api/post/feed', methods=['GET'])
@login_required
def get_post_feed():
    page = request.args.get('page', 1, type=int)
    limit = 10
    offset = (page - 1) * limit
    db = get_db()
    cursor = db.cursor()
    
    # Get IDs of friends
    friend_ids_cursor = db.cursor()
    friend_ids_cursor.execute("SELECT friend_id FROM friendships WHERE user_id = ? AND status = 'friends'", (session['user_id'],))
    friend_ids = [row['friend_id'] for row in friend_ids_cursor.fetchall()]
    friend_ids.append(session['user_id']) # Include own posts

    placeholders = ', '.join('?' for _ in friend_ids)
    
    cursor.execute(f"SELECT * FROM posts WHERE user_id IN ({placeholders}) ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                   tuple(friend_ids + [limit, offset]))
    
    posts = []
    for post in cursor.fetchall():
        post_data = dict(post)
        user_info = get_user_info(post['user_id'])
        post_data['user'] = user_info
        
        # Get like count
        like_cursor = db.cursor()
        like_cursor.execute("SELECT COUNT(*) as count FROM likes WHERE content_id = ?", (post['id'],))
        post_data['like_count'] = like_cursor.fetchone()['count']
        
        # Check if current user has liked
        like_cursor.execute("SELECT COUNT(*) as count FROM likes WHERE content_id = ? AND user_id = ?", (post['id'], session['user_id']))
        post_data['liked_by_user'] = like_cursor.fetchone()['count'] > 0
        
        posts.append(post_data)
        
    return jsonify({'success': True, 'posts': posts})

@app.route('/api/post/like', methods=['POST'])
@login_required
def like_post():
    data = request.json
    post_id = data.get('post_id')
    db = get_db()
    cursor = db.cursor()
    
    # Check if already liked
    cursor.execute("SELECT * FROM likes WHERE user_id = ? AND content_id = ?", (session['user_id'], post_id))
    if cursor.fetchone():
        cursor.execute("DELETE FROM likes WHERE user_id = ? AND content_id = ?", (session['user_id'], post_id))
        db.commit()
        return jsonify({'success': True, 'message': 'Post unliked.'})
    else:
        like_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO likes (id, user_id, content_id, content_type, timestamp) VALUES (?, ?, ?, ?, ?)",
                       (like_id, session['user_id'], post_id, 'post', datetime.now().isoformat()))
        db.commit()
        # Send notification to post owner
        cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
        post_owner_id = cursor.fetchone()['user_id']
        if post_owner_id != session['user_id']:
            send_notification(post_owner_id, 'like', f"Someone liked your post.")
        return jsonify({'success': True, 'message': 'Post liked.'})

@app.route('/api/post/comments', methods=['GET'])
@login_required
def get_post_comments():
    post_id = request.args.get('post_id')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM comments WHERE content_id = ? AND content_type = 'post' ORDER BY timestamp DESC", (post_id,))
    comments = []
    for comment in cursor.fetchall():
        comment_data = dict(comment)
        user_info = get_user_info(comment['user_id'])
        comment_data['user'] = user_info
        comments.append(comment_data)
    return jsonify({'success': True, 'comments': comments})

@app.route('/api/post/comment', methods=['POST'])
@login_required
def comment_post():
    data = request.json
    post_id = data.get('post_id')
    text = data.get('text')
    if not post_id or not text:
        return jsonify({'success': False, 'message': 'Missing fields.'}), 400
    db = get_db()
    cursor = db.cursor()
    comment_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO comments (id, user_id, content_id, content_type, text, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                   (comment_id, session['user_id'], post_id, 'post', text, datetime.now().isoformat()))
    db.commit()
    # Send notification to post owner
    cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
    post_owner_id = cursor.fetchone()['user_id']
    if post_owner_id != session['user_id']:
        send_notification(post_owner_id, 'comment', f"Someone commented on your post.")
    return jsonify({'success': True, 'message': 'Comment added.'})

@app.route('/api/reel/create', methods=['POST'])
@login_required
def create_reel():
    if 'media' not in request.files:
        return jsonify({'success': False, 'message': 'No media file provided.'}), 400
    media = request.files['media']
    if media.filename == '' or not allowed_file(media.filename):
        return jsonify({'success': False, 'message': 'Invalid file type.'}), 400

    description = request.form.get('description', '')
    filename = secure_filename(media.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    media.save(filepath)

    db = get_db()
    cursor = db.cursor()
    reel_id = str(uuid.uuid4())
    media_url = f"/static/uploads/{filename}"
    
    cursor.execute("INSERT INTO reels (id, user_id, description, media_url, timestamp) VALUES (?, ?, ?, ?, ?)",
                   (reel_id, session['user_id'], description, media_url, datetime.now().isoformat()))
    db.commit()
    return jsonify({'success': True, 'message': 'Reel created successfully.'})

@app.route('/api/reel/feed', methods=['GET'])
@login_required
def get_reel_feed():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM reels ORDER BY timestamp DESC")
    reels = []
    for reel in cursor.fetchall():
        reel_data = dict(reel)
        user_info = get_user_info(reel['user_id'])
        reel_data['user'] = user_info
        reels.append(reel_data)
    return jsonify({'success': True, 'reels': reels})

@app.route('/api/story/create', methods=['POST'])
@login_required
def create_story():
    if 'media' not in request.files:
        return jsonify({'success': False, 'message': 'No media file provided.'}), 400
    media = request.files['media']
    if media.filename == '' or not allowed_file(media.filename):
        return jsonify({'success': False, 'message': 'Invalid file type.'}), 400

    filename = secure_filename(media.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    media.save(filepath)
    
    db = get_db()
    cursor = db.cursor()
    story_id = str(uuid.uuid4())
    media_url = f"/static/uploads/{filename}"
    
    cursor.execute("INSERT INTO stories (id, user_id, media_url, timestamp) VALUES (?, ?, ?, ?)",
                   (story_id, session['user_id'], media_url, datetime.now().isoformat()))
    db.commit()
    return jsonify({'success': True, 'message': 'Story created successfully.'})

@app.route('/api/story/feed', methods=['GET'])
@login_required
def get_story_feed():
    db = get_db()
    cursor = db.cursor()
    
    # Get IDs of friends
    friend_ids_cursor = db.cursor()
    friend_ids_cursor.execute("SELECT friend_id FROM friendships WHERE user_id = ? AND status = 'friends'", (session['user_id'],))
    friend_ids = [row['friend_id'] for row in friend_ids_cursor.fetchall()]
    friend_ids.append(session['user_id']) # Include own stories

    placeholders = ', '.join('?' for _ in friend_ids)
    
    # Get stories from friends within the last 24 hours
    twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).isoformat()
    
    cursor.execute(f"SELECT * FROM stories WHERE user_id IN ({placeholders}) AND timestamp >= ? ORDER BY timestamp DESC",
                   tuple(friend_ids + [twenty_four_hours_ago]))
    
    stories = []
    for story in cursor.fetchall():
        story_data = dict(story)
        user_info = get_user_info(story['user_id'])
        story_data['user'] = user_info
        stories.append(story_data)
        
    return jsonify({'success': True, 'stories': stories})

# --- Social & Messaging Routes ---

@app.route('/api/friends/request', methods=['POST'])
@login_required
def send_friend_request():
    data = request.json
    friend_id = data.get('user_id')
    current_user_id = session['user_id']
    if current_user_id == friend_id:
        return jsonify({'success': False, 'message': 'Cannot send a friend request to yourself.'}), 400
    
    db = get_db()
    cursor = db.cursor()
    # Check if request already exists
    cursor.execute("SELECT * FROM friendships WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)",
                   (current_user_id, friend_id, friend_id, current_user_id))
    if cursor.fetchone():
        return jsonify({'success': False, 'message': 'Friendship request already exists or you are already friends.'}), 409
    
    cursor.execute("INSERT INTO friendships (user_id, friend_id, status) VALUES (?, ?, ?)",
                   (current_user_id, friend_id, 'pending'))
    db.commit()
    send_notification(friend_id, 'friend_request', f"You have a new friend request.")
    return jsonify({'success': True, 'message': 'Friend request sent.'})

@app.route('/api/friends/accept', methods=['POST'])
@login_required
def accept_friend_request():
    data = request.json
    friend_id = data.get('user_id')
    current_user_id = session['user_id']
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("UPDATE friendships SET status = 'friends' WHERE user_id = ? AND friend_id = ? AND status = 'pending'",
                   (friend_id, current_user_id))
    if cursor.rowcount == 0:
        return jsonify({'success': False, 'message': 'Friend request not found or already accepted.'}), 404
        
    # Create friendship record for the other user as well
    cursor.execute("INSERT INTO friendships (user_id, friend_id, status) VALUES (?, ?, ?)",
                   (current_user_id, friend_id, 'friends'))
    db.commit()
    send_notification(friend_id, 'friend_request_accepted', f"Your friend request has been accepted.")
    return jsonify({'success': True, 'message': 'Friend request accepted.'})

@app.route('/api/friends/list', methods=['GET'])
@login_required
def list_friends():
    current_user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT friend_id FROM friendships WHERE user_id = ? AND status = 'friends'", (current_user_id,))
    friend_ids = [row['friend_id'] for row in cursor.fetchall()]
    
    friends = []
    for f_id in friend_ids:
        friends.append(get_user_info(f_id))
    
    return jsonify({'success': True, 'friends': friends})

@app.route('/api/user/search', methods=['GET'])
@login_required
def search_users():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify({'success': False, 'message': 'Query too short.'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, username, real_name, profile_pic_url FROM users WHERE username LIKE ? OR real_name LIKE ? LIMIT 20",
                   (f'%{query}%', f'%{query}%'))
    users = [dict(row) for row in cursor.fetchall()]
    return jsonify({'success': True, 'users': users})

@app.route('/api/chat/send', methods=['POST'])
@login_required
def send_message():
    data = request.json
    receiver_id = data.get('receiver_id')
    text = data.get('text')
    is_group = data.get('is_group', False)
    
    if not receiver_id:
        return jsonify({'success': False, 'message': 'Missing receiver_id.'}), 400
    
    db = get_db()
    cursor = db.cursor()
    message_id = str(uuid.uuid4())
    
    if is_group:
        cursor.execute("SELECT * FROM group_members WHERE group_id = ? AND user_id = ?", (receiver_id, session['user_id']))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'You are not a member of this group.'}), 403
        
        cursor.execute("INSERT INTO messages (id, sender_id, receiver_id, text, is_group, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                       (message_id, session['user_id'], receiver_id, text, True, datetime.now().isoformat()))
        
        # Notify all group members
        cursor.execute("SELECT user_id FROM group_members WHERE group_id = ? AND user_id != ?", (receiver_id, session['user_id']))
        for member in cursor.fetchall():
            send_notification(member['user_id'], 'group_message', f"New message in group.")
            
    else:
        cursor.execute("INSERT INTO messages (id, sender_id, receiver_id, text, is_group, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                       (message_id, session['user_id'], receiver_id, text, False, datetime.now().isoformat()))
        send_notification(receiver_id, 'message', f"You have a new message.")
        
    db.commit()
    return jsonify({'success': True, 'message': 'Message sent.'})

@app.route('/api/chat/history', methods=['GET'])
@login_required
def get_chat_history():
    chat_id = request.args.get('chat_id')
    is_group = request.args.get('is_group', 'false').lower() == 'true'
    db = get_db()
    cursor = db.cursor()
    
    if is_group:
        cursor.execute("SELECT * FROM messages WHERE is_group = 1 AND receiver_id = ? ORDER BY timestamp ASC", (chat_id,))
    else:
        cursor.execute("SELECT * FROM messages WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?) ORDER BY timestamp ASC",
                       (session['user_id'], chat_id, chat_id, session['user_id']))
    
    messages = []
    for msg in cursor.fetchall():
        msg_data = dict(msg)
        sender_info = get_user_info(msg['sender_id'])
        msg_data['sender'] = sender_info
        messages.append(msg_data)
    
    return jsonify({'success': True, 'messages': messages})

@app.route('/api/inbox/list', methods=['GET'])
@login_required
def list_inbox():
    current_user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    # Get direct chats
    cursor.execute("""
        SELECT DISTINCT CASE WHEN sender_id = ? THEN receiver_id ELSE sender_id END as chat_id
        FROM messages
        WHERE (sender_id = ? OR receiver_id = ?) AND is_group = 0
    """, (current_user_id, current_user_id, current_user_id))
    
    direct_chat_ids = [row['chat_id'] for row in cursor.fetchall()]
    direct_chats = []
    for chat_id in direct_chat_ids:
        user = get_user_info(chat_id)
        if user:
            cursor.execute("""
                SELECT text, timestamp FROM messages
                WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
                ORDER BY timestamp DESC LIMIT 1
            """, (current_user_id, chat_id, chat_id, current_user_id))
            last_msg = cursor.fetchone()
            user['last_message'] = last_msg['text'] if last_msg else ''
            user['last_timestamp'] = last_msg['timestamp'] if last_msg else ''
            cursor.execute("SELECT COUNT(*) as unread FROM messages WHERE sender_id = ? AND receiver_id = ? AND is_group = 0 AND read = 0",
                           (chat_id, current_user_id))
            user['unread'] = cursor.fetchone()['unread']
            direct_chats.append(user)

    # Get group chats
    cursor.execute("SELECT group_id FROM group_members WHERE user_id = ?", (current_user_id,))
    group_ids = [row['group_id'] for row in cursor.fetchall()]
    group_chats = []
    for group_id in group_ids:
        cursor.execute("SELECT id, name, profile_pic_url FROM groups WHERE id = ?", (group_id,))
        group = dict(cursor.fetchone())
        cursor.execute("SELECT text, timestamp FROM messages WHERE is_group = 1 AND receiver_id = ? ORDER BY timestamp DESC LIMIT 1", (group_id,))
        last_msg = cursor.fetchone()
        group['last_message'] = last_msg['text'] if last_msg else ''
        group['last_timestamp'] = last_msg['timestamp'] if last_msg else ''
        group_chats.append(group)
        
    return jsonify({'success': True, 'direct_chats': direct_chats, 'group_chats': group_chats})

@app.route('/api/group/create', methods=['POST'])
@login_required
def create_group():
    data = request.json
    name = data.get('name')
    description = data.get('description', '')
    if not name:
        return jsonify({'success': False, 'message': 'Group name is required.'}), 400

    db = get_db()
    cursor = db.cursor()
    group_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO groups (id, name, description, admin_id) VALUES (?, ?, ?, ?)",
                   (group_id, name, description, session['user_id']))
    cursor.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, session['user_id']))
    db.commit()
    return jsonify({'success': True, 'message': 'Group created successfully.', 'group_id': group_id})

@app.route('/api/group/edit', methods=['POST'])
@login_required
def edit_group():
    data = request.json
    group_id = data.get('group_id')
    name = data.get('name')
    description = data.get('description')
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT admin_id FROM groups WHERE id = ?", (group_id,))
    group = cursor.fetchone()
    if not group or group['admin_id'] != session['user_id']:
        return jsonify({'success': False, 'message': 'You are not the group admin.'}), 403

    updates = []
    params = []
    if name:
        updates.append("name = ?")
        params.append(name)
    if description:
        updates.append("description = ?")
        params.append(description)

    if not updates:
        return jsonify({'success': False, 'message': 'No data to update.'}), 400

    updates_str = ", ".join(updates)
    params.append(group_id)
    cursor.execute(f"UPDATE groups SET {updates_str} WHERE id = ?", tuple(params))
    db.commit()
    return jsonify({'success': True, 'message': 'Group updated successfully.'})

@app.route('/api/group/members/add', methods=['POST'])
@login_required
def add_group_member():
    data = request.json
    group_id = data.get('group_id')
    user_id = data.get('user_id')

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT admin_id FROM groups WHERE id = ?", (group_id,))
    group = cursor.fetchone()
    if not group or group['admin_id'] != session['user_id']:
        return jsonify({'success': False, 'message': 'You are not the group admin.'}), 403

    try:
        cursor.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, user_id))
        db.commit()
        return jsonify({'success': True, 'message': 'Member added successfully.'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'User is already a member.'}), 409

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
    
    return jsonify({'success': True, 'message': 'Left group successfully.'})

@app.route('/api/notifications/get', methods=['GET'])
@login_required
def get_notifications():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY timestamp DESC", (session['user_id'],))
    notifications = [dict(row) for row in cursor.fetchall()]
    return jsonify({'success': True, 'notifications': notifications})

@app.route('/api/notifications/read', methods=['POST'])
@login_required
def read_notification():
    data = request.json
    notif_id = data.get('notif_id')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE notifications SET read = 1 WHERE id = ? AND user_id = ?", (notif_id, session['user_id']))
    db.commit()
    return jsonify({'success': True, 'message': 'Notification marked as read.'})

# --- Admin Routes ---

@app.route('/api/admin/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    db = get_db()
    cursor = db.cursor()
    # Get user list
    cursor.execute("SELECT id, username, real_name, active, is_admin FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    # Get report list
    cursor.execute("SELECT * FROM reports WHERE status = 'pending' ORDER BY timestamp DESC")
    reports = [dict(row) for row in cursor.fetchall()]
    return jsonify({'success': True, 'users': users, 'reports': reports})

@app.route('/api/admin/toggle_active', methods=['POST'])
@admin_required
def admin_toggle_active():
    data = request.json
    user_id = data.get('user_id')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET active = NOT active WHERE id = ?", (user_id,))
    db.commit()
    return jsonify({'success': True, 'message': 'User active status toggled.'})

@app.route('/api/admin/block', methods=['POST'])
@admin_required
def admin_block():
    data = request.json
    user_id = data.get('user_id')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET active = 0 WHERE id = ?", (user_id,))
    db.commit()
    return jsonify({'success': True, 'message': 'User blocked.'})

@app.route('/api/admin/unblock', methods=['POST'])
@admin_required
def admin_unblock():
    data = request.json
    user_id = data.get('user_id')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET active = 1 WHERE id = ?", (user_id,))
    db.commit()
    return jsonify({'success': True, 'message': 'User unblocked.'})

@app.route('/api/admin/report/resolve', methods=['POST'])
@admin_required
def admin_resolve_report():
    data = request.json
    report_id = data.get('report_id')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE reports SET status = 'resolved' WHERE id = ?", (report_id,))
    db.commit()
    return jsonify({'success': True, 'message': 'Report resolved.'})

@app.route('/api/admin/report/delete_content', methods=['POST'])
@admin_required
def admin_delete_content():
    data = request.json
    report_id = data.get('report_id')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT content_type, content_id FROM reports WHERE id = ?", (report_id,))
    report = cursor.fetchone()
    if not report:
        return jsonify({'success': False, 'message': 'Report not found.'}), 404
        
    content_type = report['content_type']
    content_id = report['content_id']
    
    if content_type == 'post':
        cursor.execute("DELETE FROM posts WHERE id = ?", (content_id,))
    elif content_type == 'reel':
        cursor.execute("DELETE FROM reels WHERE id = ?", (content_id,))
    elif content_type == 'story':
        cursor.execute("DELETE FROM stories WHERE id = ?", (content_id,))
    
    cursor.execute("UPDATE reports SET status = 'resolved' WHERE id = ?", (report_id,))
    db.commit()
    return jsonify({'success': True, 'message': 'Content deleted and report resolved.'})

# --- Frontend Endpoints ---
@app.route('/static/style.css')
def serve_style():
    return render_template('style.css', mimetype='text/css')

@app.route('/static/script.js')
def serve_script():
    return render_template('script.js', mimetype='text/javascript')

if __name__ == '__main__':
    app.run(debug=True)
