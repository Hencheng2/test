# app.py
import os
import sqlite3
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, session, send_from_directory, g
from werkzeug.utils import secure_filename
from functools import wraps

# Import config
from config import SECRET_KEY, ADMIN_USERNAME, ADMIN_PASS

app = Flask(__name__)
app.secret_key = SECRET_KEY
DATABASE = 'sociafam.db'

# Upload configuration
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(os.path.join(UPLOAD_FOLDER, 'posts'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'reels'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'stories'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'profiles'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'groups'), exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'webm', 'mp3', 'wav', '3gp'}

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

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                real_name TEXT NOT NULL,
                profile_pic TEXT DEFAULT '/static/default_pic.png',
                bio TEXT,
                dob TEXT,
                gender TEXT,
                pronouns TEXT,
                work TEXT,
                education_uni TEXT,
                education_secondary TEXT,
                location TEXT,
                phone TEXT,
                email TEXT,
                social_link TEXT,
                website TEXT,
                relationship_status TEXT,
                spouse TEXT,
                unique_key TEXT UNIQUE NOT NULL,
                is_admin INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                warning TEXT
            );

            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content_type TEXT, -- 'text', 'image', 'video'
                content_url TEXT,
                description TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                views INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content_type TEXT, -- 'image', 'video', 'audio'
                content_url TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME DEFAULT (datetime('now', '+24 hours')),
                FOREIGN KEY (user_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS reels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                video_url TEXT NOT NULL,
                description TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                views INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS follows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                follower_id INTEGER,
                followed_id INTEGER,
                status TEXT DEFAULT 'accepted', -- 'accepted', 'blocked'
                FOREIGN KEY (follower_id) REFERENCES users (id),
                FOREIGN KEY (followed_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER,
                receiver_id INTEGER,
                group_id INTEGER,
                content TEXT,
                content_type TEXT, -- 'text', 'image', 'video', 'audio'
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_read INTEGER DEFAULT 0,
                FOREIGN KEY (sender_id) REFERENCES users (id),
                FOREIGN KEY (receiver_id) REFERENCES users (id),
                FOREIGN KEY (group_id) REFERENCES groups (id)
            );

            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                profile_pic TEXT DEFAULT '/static/group_default.png',
                description TEXT,
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                group_link TEXT UNIQUE,
                allow_messages INTEGER DEFAULT 1,
                add_members INTEGER DEFAULT 1,
                approve_members INTEGER DEFAULT 0,
                FOREIGN KEY (created_by) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                user_id INTEGER,
                is_admin INTEGER DEFAULT 0,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT, -- 'friend_request', 'message', 'like', 'comment', 'group_invite', 'tag', 'system'
                content TEXT,
                from_user_id INTEGER,
                is_read INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (from_user_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                post_id INTEGER,
                reel_id INTEGER,
                story_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (post_id) REFERENCES posts (id),
                FOREIGN KEY (reel_id) REFERENCES reels (id),
                FOREIGN KEY (story_id) REFERENCES stories (id)
            );

            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                post_id INTEGER,
                reel_id INTEGER,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (post_id) REFERENCES posts (id),
                FOREIGN KEY (reel_id) REFERENCES reels (id)
            );

            CREATE TABLE IF NOT EXISTS saved_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                post_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (post_id) REFERENCES posts (id)
            );

            CREATE TABLE IF NOT EXISTS saved_reels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                reel_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (reel_id) REFERENCES reels (id)
            );

            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reported_by INTEGER,
                user_id INTEGER,
                group_id INTEGER,
                reason TEXT,
                description TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (reported_by) REFERENCES users (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (group_id) REFERENCES groups (id)
            );

            CREATE TABLE IF NOT EXISTS blocked_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blocker_id INTEGER,
                blocked_id INTEGER,
                FOREIGN KEY (blocker_id) REFERENCES users (id),
                FOREIGN KEY (blocked_id) REFERENCES users (id)
            );

            INSERT OR IGNORE INTO users (username, password, real_name, unique_key, is_admin) 
            VALUES (?, ?, ?, ?, 1);
        """, (ADMIN_USERNAME, hashlib.sha256(ADMIN_PASS.encode()).hexdigest(), "Admin", "ADM1"))

        db.commit()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        user = get_db().execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
        if not user['is_admin']:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_unique_key():
    letters = string.ascii_uppercase
    digits = string.digits
    return ''.join(secrets.choice(digits) for _ in range(2)) + ''.join(secrets.choice(letters) for _ in range(2))

@app.route('/login')
def login_page():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ? AND is_banned = 0", (username,)).fetchone()
    if user and user['password'] == hash_password(password):
        session['user_id'] = user['id']
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Invalid credentials or account banned.'})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    real_name = data.get('real_name')

    if len(password) < 6 or not any(c.isdigit() for c in password) or not any(c in "!@#$%^&*()_+-=" for c in password):
        return jsonify({'success': False, 'message': 'Password must be 6+ chars with number and special char.'})

    if username == ADMIN_USERNAME:
        return jsonify({'success': False, 'message': 'This username is reserved.'})

    db = get_db()
    existing = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        return jsonify({'success': False, 'message': 'Username already exists.'})

    unique_key = generate_unique_key()
    db.execute("""
        INSERT INTO users (username, password, real_name, unique_key) 
        VALUES (?, ?, ?, ?)
    """, (username, hash_password(password), real_name, unique_key))
    db.commit()
    return jsonify({'success': True})

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    username = data.get('username')
    key = data.get('key')
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ? AND unique_key = ?", (username, key)).fetchone()
    if user:
        session['reset_user_id'] = user['id']
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/set-new-password', methods=['POST'])
def set_new_password():
    if 'reset_user_id' not in session:
        return jsonify({'success': False})
    data = request.get_json()
    password = data.get('password')
    if len(password) < 6 or not any(c.isdigit() for c in password) or not any(c in "!@#$%^&*()_+-=" for c in password):
        return jsonify({'success': False, 'message': 'Weak password.'})
    db = get_db()
    db.execute("UPDATE users SET password = ? WHERE id = ?", (hash_password(password), session['reset_user_id']))
    db.commit()
    session.pop('reset_user_id', None)
    return jsonify({'success': True})

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# API: Stories
@app.route('/api/stories', methods=['GET'])
@login_required
def get_stories():
    db = get_db()
    cur_user = session['user_id']
    stories = db.execute("""
        SELECT s.*, u.real_name, u.username, u.profile_pic
        FROM stories s
        JOIN users u ON s.user_id = u.id
        JOIN follows f ON u.id = f.followed_id
        WHERE f.follower_id = ? AND f.status = 'accepted' AND s.expires_at > datetime('now')
        ORDER BY s.timestamp DESC
    """, (cur_user,)).fetchall()
    return jsonify([dict(row) for row in stories])

@app.route('/api/story', methods=['POST'])
@login_required
def create_story():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"story_{secrets.token_hex(8)}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'stories', new_filename)
        file.save(filepath)
        content_url = f'/static/uploads/stories/{new_filename}'
        content_type = 'video' if ext in ['mp4', 'mov', 'webm'] else 'audio' if ext in ['mp3', 'wav'] else 'image'

        db = get_db()
        db.execute("INSERT INTO stories (user_id, content_type, content_url) VALUES (?, ?, ?)",
                   (session['user_id'], content_type, content_url))
        db.commit()
        return jsonify({'success': True, 'url': content_url})
    return jsonify({'success': False, 'message': 'Invalid file type'})

# API: Posts
@app.route('/api/posts', methods=['GET'])
@login_required
def get_posts():
    db = get_db()
    posts = db.execute("""
        SELECT p.*, u.real_name, u.username, u.profile_pic, 
        (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as like_count,
        (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count
        FROM posts p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.timestamp DESC
    """).fetchall()
    return jsonify([dict(row) for row in posts])

@app.route('/api/post', methods=['POST'])
@login_required
def create_post():
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[1].lower()
            new_filename = f"post_{secrets.token_hex(8)}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', new_filename)
            file.save(filepath)
            content_url = f'/static/uploads/posts/{new_filename}'
            content_type = 'video' if ext in ['mp4', 'mov', 'webm'] else 'image'
        else:
            content_url = None
            content_type = 'text'
    else:
        content_url = None
        content_type = 'text'

    description = request.form.get('description', '')

    db = get_db()
    db.execute("INSERT INTO posts (user_id, content_type, content_url, description) VALUES (?, ?, ?, ?)",
               (session['user_id'], content_type, content_url, description))
    db.commit()
    return jsonify({'success': True})

@app.route('/api/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    db = get_db()
    existing = db.execute("SELECT * FROM likes WHERE user_id = ? AND post_id = ?", (session['user_id'], post_id)).fetchone()
    if existing:
        db.execute("DELETE FROM likes WHERE id = ?", (existing['id'],))
    else:
        db.execute("INSERT INTO likes (user_id, post_id) VALUES (?, ?)", (session['user_id'], post_id))
        post = db.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,)).fetchone()
        if post and post['user_id'] != session['user_id']:
            db.execute("INSERT INTO notifications (user_id, type, from_user_id, content) VALUES (?, 'like', ?, ?)",
                       (post['user_id'], session['user_id'], 'liked your post'))
    db.commit()
    return jsonify({'success': True})

@app.route('/api/post/<int:post_id>/comment', methods=['POST'])
@login_required
def comment_on_post(post_id):
    data = request.get_json()
    content = data.get('content')
    db = get_db()
    db.execute("INSERT INTO comments (user_id, post_id, content) VALUES (?, ?, ?)",
               (session['user_id'], post_id, content))
    post = db.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post and post['user_id'] != session['user_id']:
        db.execute("INSERT INTO notifications (user_id, type, from_user_id, content) VALUES (?, 'comment', ?, ?)",
                   (post['user_id'], session['user_id'], 'commented on your post'))
    db.commit()
    return jsonify({'success': True})

@app.route('/api/post/<int:post_id>/save', methods=['POST'])
@login_required
def save_post(post_id):
    db = get_db()
    db.execute("INSERT OR IGNORE INTO saved_posts (user_id, post_id) VALUES (?, ?)", (session['user_id'], post_id))
    db.commit()
    return jsonify({'success': True})

@app.route('/api/post/<int:post_id>/hide', methods=['POST'])
@login_required
def hide_post(post_id):
    return jsonify({'success': True})

@app.route('/api/post/<int:post_id>/report', methods=['POST'])
@login_required
def report_post(post_id):
    db = get_db()
    db.execute("INSERT INTO reports (reported_by, user_id, reason, description) SELECT ?, user_id, 'Inappropriate content', 'Reported post' FROM posts WHERE id = ?", (session['user_id'], post_id))
    db.commit()
    return jsonify({'success': True})

@app.route('/api/post/<int:post_id>/block', methods=['POST'])
@login_required
def block_post_author(post_id):
    db = get_db()
    user_id = db.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,)).fetchone()['user_id']
    db.execute("DELETE FROM follows WHERE (follower_id = ? AND followed_id = ?) OR (follower_id = ? AND followed_id = ?)",
               (session['user_id'], user_id, user_id, session['user_id']))
    db.execute("INSERT INTO blocked_users (blocker_id, blocked_id) VALUES (?, ?)", (session['user_id'], user_id))
    db.commit()
    return jsonify({'success': True})

# API: Reels
@app.route('/api/reels', methods=['GET'])
@login_required
def get_reels():
    db = get_db()
    reels = db.execute("""
        SELECT r.*, u.real_name, u.username, u.profile_pic,
        (SELECT COUNT(*) FROM likes WHERE reel_id = r.id) as like_count,
        (SELECT COUNT(*) FROM comments WHERE reel_id = r.id) as comment_count
        FROM reels r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.timestamp DESC
    """).fetchall()
    return jsonify([dict(row) for row in reels])

@app.route('/api/reel', methods=['POST'])
@login_required
def create_reel():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"reel_{secrets.token_hex(8)}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'reels', new_filename)
        file.save(filepath)
        video_url = f'/static/uploads/reels/{new_filename}'
        description = request.form.get('description', '')

        db = get_db()
        db.execute("INSERT INTO reels (user_id, video_url, description) VALUES (?, ?, ?)",
                   (session['user_id'], video_url, description))
        db.commit()
        return jsonify({'success': True, 'url': video_url})
    return jsonify({'success': False, 'message': 'Invalid file type'})

@app.route('/api/reel/<int:reel_id>/like', methods=['POST'])
@login_required
def like_reel(reel_id):
    db = get_db()
    existing = db.execute("SELECT * FROM likes WHERE user_id = ? AND reel_id = ?", (session['user_id'], reel_id)).fetchone()
    if existing:
        db.execute("DELETE FROM likes WHERE id = ?", (existing['id'],))
    else:
        db.execute("INSERT INTO likes (user_id, reel_id) VALUES (?, ?)", (session['user_id'], reel_id))
        reel = db.execute("SELECT user_id FROM reels WHERE id = ?", (reel_id,)).fetchone()
        if reel and reel['user_id'] != session['user_id']:
            db.execute("INSERT INTO notifications (user_id, type, from_user_id, content) VALUES (?, 'like', ?, ?)",
                       (reel['user_id'], session['user_id'], 'liked your reel'))
    db.commit()
    return jsonify({'success': True})

# API: Friends
@app.route('/api/friends/followers')
@login_required
def get_followers():
    db = get_db()
    followers = db.execute("""
        SELECT u.*, f.status,
        (SELECT COUNT(*) FROM follows WHERE follower_id = u.id AND followed_id IN (SELECT followed_id FROM follows WHERE follower_id = ?)) as mutuals
        FROM follows f
        JOIN users u ON f.follower_id = u.id
        WHERE f.followed_id = ? AND f.status = 'accepted'
    """, (session['user_id'], session['user_id'])).fetchall()
    return jsonify([dict(row) for row in followers])

@app.route('/api/friends/following')
@login_required
def get_following():
    db = get_db()
    following = db.execute("""
        SELECT u.*, f.status,
        (SELECT COUNT(*) FROM follows WHERE follower_id = u.id AND followed_id IN (SELECT followed_id FROM follows WHERE follower_id = ?)) as mutuals
        FROM follows f
        JOIN users u ON f.followed_id = u.id
        WHERE f.follower_id = ? AND f.status = 'accepted'
    """, (session['user_id'], session['user_id'])).fetchall()
    return jsonify([dict(row) for row in following])

@app.route('/api/friends/requests')
@login_required
def get_friend_requests():
    db = get_db()
    requests = db.execute("""
        SELECT u.*, f.id as req_id,
        (SELECT COUNT(*) FROM follows WHERE follower_id = u.id AND followed_id IN (SELECT followed_id FROM follows WHERE follower_id = ?)) as mutuals
        FROM follows f
        JOIN users u ON f.follower_id = u.id
        WHERE f.followed_id = ? AND f.status = 'pending'
    """, (session['user_id'], session['user_id'])).fetchall()
    return jsonify([dict(row) for row in requests])

@app.route('/api/friends/suggested')
@login_required
def get_suggested():
    db = get_db()
    suggested = db.execute("""
        SELECT u.*, 
        (SELECT COUNT(*) FROM follows WHERE follower_id = u.id AND followed_id IN (SELECT followed_id FROM follows WHERE follower_id = ?)) as mutuals
        FROM users u
        WHERE u.id NOT IN (SELECT followed_id FROM follows WHERE follower_id = ?)
          AND u.id != ?
        ORDER BY mutuals DESC LIMIT 10
    """, (session['user_id'], session['user_id'], session['user_id'])).fetchall()
    return jsonify([dict(row) for row in suggested])

@app.route('/api/follow/<int:user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    db = get_db()
    db.execute("INSERT OR IGNORE INTO follows (follower_id, followed_id, status) VALUES (?, ?, 'accepted')",
               (session['user_id'], user_id))
    db.execute("INSERT OR IGNORE INTO follows (follower_id, followed_id, status) VALUES (?, ?, 'accepted')",
               (user_id, session['user_id']))
    db.execute("INSERT INTO notifications (user_id, type, from_user_id, content) VALUES (?, 'friend_request', ?, 'started following you')",
               (user_id, session['user_id']))
    db.commit()
    return jsonify({'success': True})

@app.route('/api/accept/<int:req_id>', methods=['POST'])
@login_required
def accept_request(req_id):
    db = get_db()
    req = db.execute("SELECT * FROM follows WHERE id = ? AND followed_id = ?", (req_id, session['user_id'])).fetchone()
    if req:
        db.execute("UPDATE follows SET status = 'accepted' WHERE id = ?", (req_id,))
        db.execute("INSERT OR IGNORE INTO follows (follower_id, followed_id, status) VALUES (?, ?, 'accepted')",
                   (req['followed_id'], req['follower_id']))
        db.execute("INSERT INTO notifications (user_id, type, from_user_id, content) VALUES (?, 'friend_request', ?, 'accepted your follow request')",
                   (req['follower_id'], session['user_id']))
    db.commit()
    return jsonify({'success': True})

@app.route('/api/decline/<int:req_id>', methods=['POST'])
@login_required
def decline_request(req_id):
    db = get_db()
    db.execute("DELETE FROM follows WHERE id = ?", (req_id,))
    db.commit()
    return jsonify({'success': True})

@app.route('/api/block/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    db = get_db()
    db.execute("DELETE FROM follows WHERE (follower_id = ? AND followed_id = ?) OR (follower_id = ? AND followed_id = ?)",
               (session['user_id'], user_id, user_id, session['user_id']))
    db.execute("INSERT INTO blocked_users (blocker_id, blocked_id) VALUES (?, ?)", (session['user_id'], user_id))
    db.commit()
    return jsonify({'success': True})

# API: Messages
@app.route('/api/messages/chats')
@login_required
def get_chats():
    db = get_db()
    chats = db.execute("""
        SELECT u.real_name, u.username, u.profile_pic, m.content, m.timestamp,
        (SELECT COUNT(*) FROM messages WHERE receiver_id = ? AND sender_id = u.id AND is_read = 0) as unread
        FROM messages m
        JOIN users u ON (m.sender_id = u.id OR m.receiver_id = u.id)
        WHERE (m.sender_id = ? OR m.receiver_id = ?) AND u.id != ?
        GROUP BY u.id
        ORDER BY m.timestamp DESC
    """, (session['user_id'], session['user_id'], session['user_id'], session['user_id'])).fetchall()
    return jsonify([dict(row) for row in chats])

@app.route('/api/messages/send', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    receiver_id = data.get('to')
    content = data.get('content')
    db = get_db()
    db.execute("INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)",
               (session['user_id'], receiver_id, content))
    db.execute("INSERT INTO notifications (user_id, type, from_user_id, content) VALUES (?, 'message', ?, ?)",
               (receiver_id, session['user_id'], 'sent you a message'))
    db.commit()
    return jsonify({'success': True})

# API: Groups
@app.route('/api/groups')
@login_required
def get_groups():
    db = get_db()
    groups = db.execute("""
        SELECT g.*, gm.is_admin, (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count
        FROM groups g
        JOIN group_members gm ON g.id = gm.group_id
        WHERE gm.user_id = ?
        GROUP BY g.id
    """, (session['user_id'],)).fetchall()
    return jsonify([dict(row) for row in groups])

@app.route('/api/group/create', methods=['POST'])
@login_required
def create_group():
    name = request.form.get('name')
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[1].lower()
            new_filename = f"group_{secrets.token_hex(8)}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'groups', new_filename)
            file.save(filepath)
            profile_pic = f'/static/uploads/groups/{new_filename}'
        else:
            profile_pic = '/static/group_default.png'
    else:
        profile_pic = '/static/group_default.png'

    db = get_db()
    link = secrets.token_urlsafe(8)
    db.execute("INSERT INTO groups (name, profile_pic, created_by, group_link) VALUES (?, ?, ?, ?)",
               (name, profile_pic, session['user_id'], link))
    group_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.execute("INSERT INTO group_members (group_id, user_id, is_admin) VALUES (?, ?, 1)", (group_id, session['user_id']))
    db.commit()
    return jsonify({'success': True, 'id': group_id})

# API: Profile
@app.route('/api/profile/<int:user_id>')
@login_required
def get_profile(user_id):
    db = get_db()
    profile = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not profile:
        return jsonify({'error': 'User not found'}), 404
    mutuals = db.execute("""
        SELECT COUNT(*) as count FROM follows f1
        JOIN follows f2 ON f1.follower_id = f2.followed_id AND f1.followed_id = f2.follower_id
        WHERE f1.follower_id = ? AND f1.followed_id = ?
    """, (session['user_id'], user_id)).fetchone()
    posts = db.execute("SELECT * FROM posts WHERE user_id = ? ORDER BY timestamp DESC", (user_id,)).fetchall()
    return jsonify({
        'profile': dict(profile),
        'mutual_friends': mutuals['count'],
        'posts': [dict(p) for p in posts]
    })

@app.route('/api/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    data = request.form.to_dict()
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[1].lower()
            new_filename = f"profile_{secrets.token_hex(8)}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', new_filename)
            file.save(filepath)
            data['profile_pic'] = f'/static/uploads/profiles/{new_filename}'
        else:
            data['profile_pic'] = None

    db = get_db()
    db.execute("""
        UPDATE users SET real_name = ?, bio = ?, dob = ?, gender = ?, pronouns = ?,
        work = ?, education_uni = ?, education_secondary = ?, location = ?,
        phone = ?, email = ?, social_link = ?, website = ?, relationship_status = ?, spouse = ?
        WHERE id = ?
    """, (
        data.get('real_name'), data.get('bio'), data.get('dob'), data.get('gender'), data.get('pronouns'),
        data.get('work'), data.get('education_uni'), data.get('education_secondary'), data.get('location'),
        data.get('phone'), data.get('email'), data.get('social_link'), data.get('website'),
        data.get('relationship_status'), data.get('spouse'), session['user_id']
    ))
    if data['profile_pic']:
        db.execute("UPDATE users SET profile_pic = ? WHERE id = ?", (data['profile_pic'], session['user_id']))
    db.commit()
    return jsonify({'success': True})

# API: Search
@app.route('/api/search/<query>')
@login_required
def search(query):
    db = get_db()
    users = db.execute("SELECT * FROM users WHERE real_name LIKE ? OR username LIKE ?", (f'%{query}%', f'%{query}%')).fetchall()
    posts = db.execute("SELECT p.*, u.real_name FROM posts p JOIN users u ON p.user_id = u.id WHERE p.description LIKE ?", (f'%{query}%',)).fetchall()
    reels = db.execute("SELECT r.*, u.real_name FROM reels r JOIN users u ON r.user_id = u.id WHERE r.description LIKE ?", (f'%{query}%',)).fetchall()
    return jsonify({
        'users': [dict(u) for u in users],
        'posts': [dict(p) for p in posts],
        'reels': [dict(r) for r in reels]
    })

# API: Notifications
@app.route('/api/notifications')
@login_required
def get_notifications():
    db = get_db()
    notifs = db.execute("""
        SELECT n.*, u.real_name, u.profile_pic
        FROM notifications n
        LEFT JOIN users u ON n.from_user_id = u.id
        WHERE n.user_id = ?
        ORDER BY n.timestamp DESC
    """, (session['user_id'],)).fetchall()
    return jsonify([dict(row) for row in notifs])

@app.route('/api/mark-notif-read/<int:notif_id>', methods=['POST'])
@login_required
def mark_notif_read(notif_id):
    db = get_db()
    db.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (notif_id, session['user_id']))
    db.commit()
    return jsonify({'success': True})

# API: Admin
@app.route('/admin/users')
@admin_required
def admin_users():
    db = get_db()
    users = db.execute("SELECT * FROM users").fetchall()
    return jsonify([dict(u) for u in users])

@app.route('/admin/delete/user/<int:uid>', methods=['POST'])
@admin_required
def admin_delete_user(uid):
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (uid,))
    db.execute("DELETE FROM posts WHERE user_id = ?", (uid,))
    db.execute("DELETE FROM stories WHERE user_id = ?", (uid,))
    db.execute("DELETE FROM reels WHERE user_id = ?", (uid,))
    db.execute("DELETE FROM messages WHERE sender_id = ? OR receiver_id = ?", (uid, uid))
    db.execute("DELETE FROM follows WHERE follower_id = ? OR followed_id = ?", (uid, uid))
    db.commit()
    return jsonify({'success': True})

@app.route('/admin/warn/<int:uid>', methods=['POST'])
@admin_required
def admin_warn(uid):
    db = get_db()
    db.execute("INSERT INTO notifications (user_id, type, content) VALUES (?, 'system', ?)",
               (uid, "You have been issued a warning by admin."))
    db.commit()
    return jsonify({'success': True})

@app.route('/admin/ban/<int:uid>', methods=['POST'])
@admin_required
def admin_ban(uid):
    db = get_db()
    db.execute("UPDATE users SET is_banned = 1 WHERE id = ?", (uid,))
    db.commit()
    return jsonify({'success': True})

@app.route('/admin/send-system-notification', methods=['POST'])
@admin_required
def send_system_notification():
    data = request.get_json()
    content = data.get('content')
    db = get_db()
    db.execute("INSERT INTO notifications (user_id, type, content) SELECT id, 'system', ? FROM users", (content,))
    db.commit()
    return jsonify({'success': True})

@app.route('/admin/reports')
@admin_required
def admin_reports():
    db = get_db()
    reports = db.execute("""
        SELECT r.*, u.real_name as reporter, u2.real_name as reported
        FROM reports r
        JOIN users u ON r.reported_by = u.id
        LEFT JOIN users u2 ON r.user_id = u2.id
    """).fetchall()
    return jsonify([dict(r) for r in reports])

# Static files
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# Health check
@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

# Initialize DB and run
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
