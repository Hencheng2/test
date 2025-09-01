# app.py

import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, g
import os
import re
import hashlib
import random
import string
from functools import wraps
from datetime import datetime, timedelta

# Configuration
class Config:
    SECRET_KEY = '09da35833ef9cb699888f08d66a0cfb827fb10e53f6c1549'
    ADMIN_USERNAME = 'Henry'
    ADMIN_PASS = 'Dec@2003'

app = Flask(__name__)
app.config.from_object(Config)

DATABASE = 'sociafam.db'

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
        # Users table
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                real_name TEXT,
                email TEXT UNIQUE,
                biography TEXT,
                profile_pic TEXT,
                unique_key TEXT NOT NULL,
                date_of_birth TEXT,
                gender TEXT,
                pronouns TEXT,
                work TEXT,
                education TEXT,
                places_lived TEXT,
                phone_number TEXT,
                social_links TEXT,
                website_link TEXT,
                relationship TEXT,
                spouse TEXT,
                is_admin INTEGER DEFAULT 0
            );
        ''')
        # Posts table
        db.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                description TEXT,
                content_url TEXT,
                content_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                visibility TEXT DEFAULT 'public',
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        ''')
        # Stories table
        db.execute('''
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content_url TEXT NOT NULL,
                content_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        ''')
        # Reels table
        db.execute('''
            CREATE TABLE IF NOT EXISTS reels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                description TEXT,
                content_url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        ''')
        # Likes table
        db.execute('''
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                post_id INTEGER,
                reel_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (post_id) REFERENCES posts(id),
                FOREIGN KEY (reel_id) REFERENCES reels(id)
            );
        ''')
        # Follows table
        db.execute('''
            CREATE TABLE IF NOT EXISTS follows (
                follower_id INTEGER NOT NULL,
                followed_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                PRIMARY KEY (follower_id, followed_id),
                FOREIGN KEY (follower_id) REFERENCES users(id),
                FOREIGN KEY (followed_id) REFERENCES users(id)
            );
        ''')
        # Messages table
        db.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                group_id INTEGER,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id),
                FOREIGN KEY (group_id) REFERENCES groups(id)
            );
        ''')
        # Groups table
        db.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                profile_pic TEXT,
                description TEXT,
                creator_id INTEGER NOT NULL,
                creation_date TEXT NOT NULL,
                link TEXT UNIQUE NOT NULL,
                FOREIGN KEY (creator_id) REFERENCES users(id)
            );
        ''')
        # Group members table
        db.execute('''
            CREATE TABLE IF NOT EXISTS group_members (
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'member',
                PRIMARY KEY (group_id, user_id),
                FOREIGN KEY (group_id) REFERENCES groups(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        ''')
        # Notifications table
        db.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                link TEXT,
                is_read INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        ''')
        # Reports table
        db.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER NOT NULL,
                reported_type TEXT NOT NULL,
                reported_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (reporter_id) REFERENCES users(id)
            );
        ''')
        db.commit()

# Decorator to check if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator to check if user is an admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        db = get_db()
        user = db.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        if not user or not user['is_admin']:
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def generate_unique_key():
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=2))
    return letters + numbers

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not re.match(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[^a-zA-Z0-9]).{6,}$', password):
            return "Password must be at least 6 characters with numbers, alphabets, and a special character."

        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASS:
            return "This combination of username and password is reserved for the admin."

        db = get_db()
        try:
            hashed_password = hash_password(password)
            unique_key = generate_unique_key()
            db.execute('INSERT INTO users (username, password, unique_key) VALUES (?, ?, ?)', (username, hashed_password, unique_key))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists."
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email')
        password = request.form.get('password')
        hashed_password = hash_password(password)

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE (username = ? OR email = ?) AND password = ?',
                          (username_or_email, username_or_email, hashed_password)).fetchone()

        if user:
            session['user_id'] = user['id']
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home'))
        else:
            return "Invalid username or password."
    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        unique_key = request.form.get('unique_key')
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ? AND unique_key = ?', (username, unique_key)).fetchone()
        if user:
            session['recovery_user_id'] = user['id']
            return "Success. Redirecting to set new password..." # In a real app, this would be a redirect after a short delay
        else:
            return "Invalid username or unique key."
    return render_template('forgot_password.html')

@app.route('/set_new_password', methods=['GET', 'POST'])
def set_new_password():
    if 'recovery_user_id' not in session:
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        hashed_password = hash_password(new_password)
        db = get_db()
        db.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, session['recovery_user_id']))
        db.commit()
        session.pop('recovery_user_id', None)
        return redirect(url_for('login'))
    return render_template('set_new_password.html')

@app.route('/home')
@login_required
def home():
    # Placeholder for fetching stories and posts
    db = get_db()
    
    # Logic to fetch stories from friends only
    user_id = session['user_id']
    stories = db.execute('''
        SELECT s.*, u.username, u.real_name, u.profile_pic
        FROM stories s
        JOIN users u ON s.user_id = u.id
        JOIN follows f ON f.followed_id = u.id
        WHERE f.follower_id = ? AND f.status = 'accepted'
        ORDER BY s.created_at DESC
    ''', (user_id,)).fetchall()
    
    # Logic to fetch endless scrollable posts
    posts = db.execute('''
        SELECT p.*, u.username, u.real_name, u.profile_pic
        FROM posts p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC
    ''').fetchall()

    return render_template('home.html', stories=stories, posts=posts)

@app.route('/reels')
@login_required
def reels():
    # Placeholder for fetching reels
    db = get_db()
    reels = db.execute('SELECT r.*, u.username, u.real_name, u.profile_pic FROM reels r JOIN users u ON r.user_id = u.id ORDER BY r.created_at DESC').fetchall()
    return render_template('reels.html', reels=reels)

@app.route('/friends')
@login_required
def friends():
    return render_template('friends.html')

@app.route('/inbox')
@login_required
def inbox():
    return render_template('inbox.html')

@app.route('/profile')
@login_required
def profile():
    user_id = session['user_id']
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    # Placeholder for fetching user's posts, reels, etc.
    return render_template('profile.html', user=user)

@app.route('/search')
@login_required
def search():
    return render_template('search.html')

@app.route('/add_to')
@login_required
def add_to():
    return render_template('add_to.html')

@app.route('/notifications')
@login_required
def notifications():
    user_id = session['user_id']
    db = get_db()
    notifications_list = db.execute('SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()
    return render_template('notifications.html', notifications=notifications_list)

@app.route('/menu')
@login_required
def menu():
    return render_template('menu.html')

@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    # Placeholder for admin dashboard logic
    return render_template('admin_dashboard.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)
