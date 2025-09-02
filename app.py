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
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'pdf', 'doc', 'docx'}
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
            cursor.execute("INSERT INTO users (username, password_hash, unique_key, is_admin) VALUES (?, ?, ?, 1)", (admin_username, admin_pass_hash, unique_key))
            db.commit()
    except Exception as e:
        print(e)

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
        # Mutual friends
        cursor.execute("""
            SELECT u.id, u.real_name, u.username, u.profile_pic_url 
            FROM users u
            INNER JOIN follows f1 ON f1.followed_id = u.id AND f1.follower_id = ? AND f1.status = 'accepted'
            INNER JOIN follows f2 ON f2.followed_id = u.id AND f2.follower_id = ? AND f2.status = 'accepted'
            LIMIT 3
        """, (session['user_id'], user_id))
        user_dict['mutual_friends'] = [dict(row) for row in cursor.fetchall()]
    # Counts
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
    cursor.execute(f"SELECT * FROM posts {where} ORDER BY timestamp DESC LIMIT ? OFFSET ?", params + [per_page, offset])
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
    cursor.execute("SELECT p.* FROM posts p JOIN saves s ON p.id = s.post_id WHERE s.user_id = ? ORDER BY s.timestamp DESC LIMIT ? OFFSET ?", (user_id, per_page, offset))
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
    cursor.execute("SELECT p.* FROM posts p JOIN reposts r ON p.id = r.post_id WHERE r.user_id = ? ORDER BY r.timestamp DESC LIMIT ? OFFSET ?", (user_id, per_page, offset))
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
    cursor.execute("SELECT p.* FROM posts p JOIN likes l ON p.id = l.post_id WHERE l.user_id = ? ORDER BY l.timestamp DESC LIMIT ? OFFSET ?", (user_id, per_page, offset))
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
    group_dict['permissions'] = dict(cursor.fetchone())
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
        FROM group_members gm JOIN users u ON gm.user_id = u.id 
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
    if cursor.fetchone()['is_admin'] == 0:
        return jsonify({'error': 'Not admin'}), 403
    cursor.execute("SELECT creator_id FROM groups WHERE id = ?", (group_id,))
    if target_id == cursor.fetchone()['creator_id']:
        return jsonify({'error': 'Cannot toggle creator'}), 400
    cursor.execute("UPDATE group_members SET is_admin = 1 - is_admin WHERE group_id = ? AND user_id = ?", (group_id, target_id))
    db.commit()
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
    if cursor.fetchone()['is_admin'] == 0:
        return jsonify({'error': 'Not admin'}), 403
    cursor.execute("SELECT creator_id FROM groups WHERE id = ?", (group_id,))
    if target_id == cursor.fetchone()['creator_id']:
        return jsonify({'error': 'Cannot remove creator'}), 400
    cursor.execute("DELETE FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, target_id))
    db.commit()
    notify(target_id, 'group_remove', group_id=group_id)
    return jsonify({'message': 'Removed'})

@app.route('/api/group/permissions/update', methods=['POST'])
@login_required
def update_group_permissions():
    data = request.json
    group_id = data.pop('group_id')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT is_admin FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, session['user_id']))
    if cursor.fetchone()['is_admin'] == 0:
        return jsonify({'error': 'Not admin'}), 403
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

# The rest of the app.py code remains the same, including the routes like /api/group/add, etc.

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
