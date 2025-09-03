# app.py
import os
import sqlite3
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, session, url_for, g
from functools import wraps
import json

# Import config
from config import SECRET_KEY, ADMIN_USERNAME, ADMIN_PASS

app = Flask(__name__)
app.secret_key = SECRET_KEY
DATABASE = 'sociafam.db'

# Database setup
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
                status TEXT DEFAULT 'pending', -- 'accepted', 'blocked'
                FOREIGN KEY (follower_id) REFERENCES users (id),
                FOREIGN KEY (followed_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS friendships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER,
                user2_id INTEGER,
                status TEXT DEFAULT 'pending', -- 'accepted', 'blocked'
                FOREIGN KEY (user1_id) REFERENCES users (id),
                FOREIGN KEY (user2_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER,
                receiver_id INTEGER,
                group_id INTEGER,
                content TEXT,
                content_type TEXT, -- 'text', 'image', 'video', 'audio', 'sticker'
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
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

# Utility functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_unique_key():
    letters = string.ascii_uppercase
    digits = string.digits
    return ''.join(secrets.choice(digits) for _ in range(2)) + ''.join(secrets.choice(letters) for _ in range(2))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ? AND is_banned = 0", (username,)).fetchone()
        if user and user['password'] == hash_password(password):
            session['user_id'] = user['id']
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid credentials or account banned.'})
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
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
    return render_template('register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        key = data.get('key')
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ? AND unique_key = ?", (username, key)).fetchone()
        if user:
            session['reset_user_id'] = user['id']
            return jsonify({'success': True})
        return jsonify({'success': False})
    return render_template('forgot_password.html')

@app.route('/set-new-password', methods=['POST'])
@login_required
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
        SELECT s.*, u.real_name, u.profile_pic, u.username
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
    data = request.get_json()
    content_type = data.get('content_type')
    content_url = data.get('content_url')
    db = get_db()
    db.execute("INSERT INTO stories (user_id, content_type, content_url) VALUES (?, ?, ?)",
               (session['user_id'], content_type, content_url))
    db.commit()
    return jsonify({'success': True})

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
    data = request.get_json()
    content_type = data.get('content_type')
    content_url = data.get('content_url')
    description = data.get('description')
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
        # Notify
        post = db.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,)).fetchone()
        if post and post['user_id'] != session['user_id']:
            db.execute("INSERT INTO notifications (user_id, type, from_user_id, content) VALUES (?, 'like', ?, ?)",
                       (post['user_id'], session['user_id'], 'liked your post'))
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
    data = request.get_json()
    video_url = data.get('video_url')
    description = data.get('description')
    db = get_db()
    db.execute("INSERT INTO reels (user_id, video_url, description) VALUES (?, ?, ?)",
               (session['user_id'], video_url, description))
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
    # Get mutuals of followers
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
    db.execute("INSERT OR IGNORE INTO follows (follower_id, followed_id, status) VALUES (?, ?, 'pending')",
               (session['user_id'], user_id))
    db.commit()
    return jsonify({'success': True})

@app.route('/api/accept/<int:req_id>', methods=['POST'])
@login_required
def accept_request(req_id):
    db = get_db()
    req = db.execute("SELECT * FROM follows WHERE id = ? AND followed_id = ?", (req_id, session['user_id'])).fetchone()
    if req:
        db.execute("UPDATE follows SET status = 'accepted' WHERE id = ?", (req_id,))
        # Create mutual follow
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
        SELECT g.*, gm.is_admin, COUNT(*) as member_count
        FROM groups g
        JOIN group_members gm ON g.id = gm.group_id
        WHERE gm.user_id = ?
        GROUP BY g.id
    """, (session['user_id'],)).fetchall()
    return jsonify([dict(row) for row in groups])

@app.route('/api/group/create', methods=['POST'])
@login_required
def create_group():
    data = request.get_json()
    name = data.get('name')
    profile_pic = data.get('profile_pic', '/static/group_default.png')
    db = get_db()
    link = secrets.token_urlsafe(8)
    db.execute("INSERT INTO groups (name, profile_pic, created_by, group_link) VALUES (?, ?, ?, ?)",
               (name, profile_pic, session['user_id'], link))
    group_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.execute("INSERT INTO group_members (group_id, user_id, is_admin) VALUES (?, ?, 1)", (group_id, session['user_id']))
    db.commit()
    return jsonify({'success': True, 'id': group_id})

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

# API: Profile
@app.route('/api/profile/<int:user_id>')
@login_required
def get_profile(user_id):
    db = get_db()
    profile = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not profile:
        return jsonify({'error': 'User not found'}), 404
    # Mutual friends count
    mutuals = db.execute("""
        SELECT COUNT(*) as count FROM follows f1
        JOIN follows f2 ON f1.follower_id = f2.followed_id AND f1.followed_id = f2.follower_id
        WHERE f1.follower_id = ? AND f1.followed_id = ?
    """, (session['user_id'], user_id)).fetchone()
    # Posts
    posts = db.execute("SELECT * FROM posts WHERE user_id = ? ORDER BY timestamp DESC", (user_id,)).fetchall()
    return jsonify({
        'profile': dict(profile),
        'mutual_friends': mutuals['count'],
        'posts': [dict(p) for p in posts]
    })

@app.route('/api/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    data = request.get_json()
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

# API: Settings
@app.route('/api/settings/privacy', methods=['POST'])
@login_required
def update_privacy():
    data = request.get_json()
    db = get_db()
    db.execute("UPDATE users SET profile_lock = ? WHERE id = ?", (data.get('profile_lock'), session['user_id']))
    db.commit()
    return jsonify({'success': True})

# Static file fallback
@app.route('/static/<path:filename>')
def static_files(filename):
    return app.send_static_file(filename)

# Run app
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
