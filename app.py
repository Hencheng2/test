from flask import Flask, request, jsonify, session, send_from_directory, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
import random# app.py
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import hashlib
import os
import random
import string
import json
from datetime import datetime, timedelta
import re

app = Flask(__name__)
app.secret_key = '09da35833ef9cb699888f08d66a0cfb827fb10e53f6c1549'

# Configuration from config.py
ADMIN_USERNAME = 'Henry'
ADMIN_PASS = 'Dec@2003'

# Database initialization
def init_db():
    conn = sqlite3.connect('sociafam.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  email TEXT,
                  real_name TEXT,
                  profile_pic TEXT DEFAULT 'default.jpg',
                  bio TEXT,
                  dob TEXT,
                  gender TEXT,
                  pronouns TEXT,
                  work_info TEXT,
                  university TEXT,
                  secondary_school TEXT,
                  location TEXT,
                  phone TEXT,
                  website TEXT,
                  social_link TEXT,
                  relationship_status TEXT,
                  spouse TEXT,
                  unique_key TEXT UNIQUE,
                  is_admin INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_login TIMESTAMP,
                  is_banned INTEGER DEFAULT 0,
                  account_status TEXT DEFAULT 'active')''')
    
    # Posts table
    c.execute('''CREATE TABLE IF NOT EXISTS posts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  content_type TEXT,  -- 'text', 'image', 'video'
                  content TEXT,
                  media_url TEXT,
                  description TEXT,
                  visibility TEXT DEFAULT 'public',  -- 'public', 'friends'
                  likes INTEGER DEFAULT 0,
                  comments INTEGER DEFAULT 0,
                  shares INTEGER DEFAULT 0,
                  saves INTEGER DEFAULT 0,
                  views INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # Reels table
    c.execute('''CREATE TABLE IF NOT EXISTS reels
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  video_url TEXT,
                  description TEXT,
                  visibility TEXT DEFAULT 'public',
                  likes INTEGER DEFAULT 0,
                  comments INTEGER DEFAULT 0,
                  shares INTEGER DEFAULT 0,
                  saves INTEGER DEFAULT 0,
                  views INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # Stories table
    c.execute('''CREATE TABLE IF NOT EXISTS stories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  content_type TEXT,  -- 'image', 'video', 'audio'
                  content_url TEXT,
                  duration INTEGER DEFAULT 30,  -- seconds
                  expires_at TIMESTAMP,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # Followers table
    c.execute('''CREATE TABLE IF NOT EXISTS followers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  follower_id INTEGER,
                  followed_id INTEGER,
                  status TEXT DEFAULT 'pending',  -- 'pending', 'accepted', 'blocked'
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (follower_id) REFERENCES users(id),
                  FOREIGN KEY (followed_id) REFERENCES users(id))''')
    
    # Friend requests table
    c.execute('''CREATE TABLE IF NOT EXISTS friend_requests
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sender_id INTEGER,
                  receiver_id INTEGER,
                  status TEXT DEFAULT 'pending',  -- 'pending', 'accepted', 'declined', 'blocked'
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (sender_id) REFERENCES users(id),
                  FOREIGN KEY (receiver_id) REFERENCES users(id))''')
    
    # Messages table
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sender_id INTEGER,
                  receiver_id INTEGER,
                  content_type TEXT,  -- 'text', 'image', 'video', 'audio', 'sticker'
                  content TEXT,
                  media_url TEXT,
                  is_read INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (sender_id) REFERENCES users(id),
                  FOREIGN KEY (receiver_id) REFERENCES users(id))''')
    
    # Groups table
    c.execute('''CREATE TABLE IF NOT EXISTS groups
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  description TEXT,
                  profile_pic TEXT DEFAULT 'group_default.jpg',
                  creator_id INTEGER,
                  group_link TEXT UNIQUE,
                  allow_messages INTEGER DEFAULT 1,
                  allow_add_members INTEGER DEFAULT 1,
                  require_approval INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (creator_id) REFERENCES users(id))''')
    
    # Group members table
    c.execute('''CREATE TABLE IF NOT EXISTS group_members
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  group_id INTEGER,
                  user_id INTEGER,
                  is_admin INTEGER DEFAULT 0,
                  joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (group_id) REFERENCES groups(id),
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # Group messages table
    c.execute('''CREATE TABLE IF NOT EXISTS group_messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  group_id INTEGER,
                  sender_id INTEGER,
                  content_type TEXT,
                  content TEXT,
                  media_url TEXT,
                  is_read INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (group_id) REFERENCES groups(id),
                  FOREIGN KEY (sender_id) REFERENCES users(id))''')
    
    # Post likes table
    c.execute('''CREATE TABLE IF NOT EXISTS post_likes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  post_id INTEGER,
                  user_id INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (post_id) REFERENCES posts(id),
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # Reel likes table
    c.execute('''CREATE TABLE IF NOT EXISTS reel_likes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  reel_id INTEGER,
                  user_id INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (reel_id) REFERENCES reels(id),
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # Story views table
    c.execute('''CREATE TABLE IF NOT EXISTS story_views
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  story_id INTEGER,
                  user_id INTEGER,
                  viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (story_id) REFERENCES stories(id),
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # Comments table
    c.execute('''CREATE TABLE IF NOT EXISTS comments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  post_id INTEGER,
                  user_id INTEGER,
                  content TEXT,
                  parent_id INTEGER DEFAULT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (post_id) REFERENCES posts(id),
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (parent_id) REFERENCES comments(id))''')
    
    # Reel comments table
    c.execute('''CREATE TABLE IF NOT EXISTS reel_comments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  reel_id INTEGER,
                  user_id INTEGER,
                  content TEXT,
                  parent_id INTEGER DEFAULT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (reel_id) REFERENCES reels(id),
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (parent_id) REFERENCES reel_comments(id))''')
    
    # Saved posts table
    c.execute('''CREATE TABLE IF NOT EXISTS saved_posts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  post_id INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (post_id) REFERENCES posts(id))''')
    
    # Saved reels table
    c.execute('''CREATE TABLE IF NOT EXISTS saved_reels
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  reel_id INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (reel_id) REFERENCES reels(id))''')
    
    # Notifications table
    c.execute('''CREATE TABLE IF NOT EXISTS notifications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  type TEXT,
                  content TEXT,
                  is_read INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # Admin actions table
    c.execute('''CREATE TABLE IF NOT EXISTS admin_actions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  admin_id INTEGER,
                  action_type TEXT,
                  target_type TEXT,  -- 'user', 'post', 'reel', 'story', 'group', 'comment'
                  target_id INTEGER,
                  reason TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (admin_id) REFERENCES users(id))''')
    
    # Support tickets table
    c.execute('''CREATE TABLE IF NOT EXISTS support_tickets
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  subject TEXT,
                  message TEXT,
                  status TEXT DEFAULT 'open',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # Support messages table
    c.execute('''CREATE TABLE IF NOT EXISTS support_messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ticket_id INTEGER,
                  sender_id INTEGER,
                  content TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (ticket_id) REFERENCES support_tickets(id),
                  FOREIGN KEY (sender_id) REFERENCES users(id))''')
    
    # Reposts table
    c.execute('''CREATE TABLE IF NOT EXISTS reposts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  original_post_id INTEGER,
                  original_reel_id INTEGER,
                  content TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (original_post_id) REFERENCES posts(id),
                  FOREIGN KEY (original_reel_id) REFERENCES reels(id))''')
    
    # Create admin user if not exists
    c.execute("SELECT * FROM users WHERE username = ?", (ADMIN_USERNAME,))
    if c.fetchone() is None:
        hashed_password = hashlib.sha256(ADMIN_PASS.encode()).hexdigest()
        unique_key = generate_unique_key()
        c.execute('''INSERT INTO users (username, password, real_name, is_admin, unique_key, account_status) 
                     VALUES (?, ?, ?, ?, ?, ?)''', 
                  (ADMIN_USERNAME, hashed_password, "Admin Henry", 1, unique_key, "active"))
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('sociafam.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_unique_key():
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=2))
    return numbers + letters

def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def get_user_by_username(username):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user

def get_user_by_email(email):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return user

def get_mutual_friends_count(user1_id, user2_id):
    conn = get_db()
    count = conn.execute('''
        SELECT COUNT(*) as count 
        FROM followers f1 
        JOIN followers f2 ON f1.followed_id = f2.followed_id 
        WHERE f1.follower_id = ? AND f2.follower_id = ? 
        AND f1.status = 'accepted' AND f2.status = 'accepted'
    ''', (user1_id, user2_id)).fetchone()['count']
    conn.close()
    return count

def get_friends_list(user_id):
    conn = get_db()
    friends = conn.execute('''
        SELECT u.*, 
               (SELECT COUNT(*) FROM followers f2 WHERE f2.follower_id = u.id AND f2.followed_id = ? AND f2.status = 'accepted') as is_friend
        FROM users u 
        JOIN followers f ON u.id = f.followed_id 
        WHERE f.follower_id = ? AND f.status = 'accepted'
        AND u.id != ?
    ''', (user_id, user_id, user_id)).fetchall()
    conn.close()
    return friends

def get_followers_count(user_id):
    conn = get_db()
    count = conn.execute('''
        SELECT COUNT(*) as count 
        FROM followers 
        WHERE followed_id = ? AND status = 'accepted'
    ''', (user_id,)).fetchone()['count']
    conn.close()
    return count

def get_following_count(user_id):
    conn = get_db()
    count = conn.execute('''
        SELECT COUNT(*) as count 
        FROM followers 
        WHERE follower_id = ? AND status = 'accepted'
    ''', (user_id,)).fetchone()['count']
    conn.close()
    return count

def get_friends_count(user_id):
    conn = get_db()
    count = conn.execute('''
        SELECT COUNT(*) as count 
        FROM followers f1 
        JOIN followers f2 ON f1.followed_id = f2.follower_id 
        WHERE f1.follower_id = ? AND f2.followed_id = ? 
        AND f1.status = 'accepted' AND f2.status = 'accepted'
    ''', (user_id, user_id)).fetchone()['count']
    conn.close()
    return count

def get_posts_by_user(user_id):
    conn = get_db()
    posts = conn.execute('''
        SELECT p.*, u.username, u.real_name, u.profile_pic
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.user_id = ?
        ORDER BY p.created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()
    return posts

def get_reels_by_user(user_id):
    conn = get_db()
    reels = conn.execute('''
        SELECT r.*, u.username, u.real_name, u.profile_pic
        FROM reels r
        JOIN users u ON r.user_id = u.id
        WHERE r.user_id = ?
        ORDER BY r.created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()
    return reels

def get_stories_by_user(user_id):
    conn = get_db()
    stories = conn.execute('''
        SELECT s.*, u.username, u.real_name, u.profile_pic
        FROM stories s
        JOIN users u ON s.user_id = u.id
        WHERE s.user_id = ? AND s.expires_at > ?
        ORDER BY s.created_at DESC
    ''', (user_id, datetime.now())).fetchall()
    conn.close()
    return stories

def get_friend_requests(user_id):
    conn = get_db()
    requests = conn.execute('''
        SELECT fr.*, u.username, u.real_name, u.profile_pic
        FROM friend_requests fr
        JOIN users u ON fr.sender_id = u.id
        WHERE fr.receiver_id = ? AND fr.status = 'pending'
        ORDER BY fr.created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()
    return requests

def get_suggested_users(user_id):
    conn = get_db()
    # Get friends of friends who aren't already followed
    suggested = conn.execute('''
        SELECT DISTINCT u.*, 
               (SELECT COUNT(*) FROM followers f2 WHERE f2.follower_id = u.id AND f2.followed_id = ? AND f2.status = 'accepted') as is_following,
               (SELECT COUNT(*) FROM followers f3 WHERE f3.follower_id = ? AND f3.followed_id = u.id AND f3.status = 'accepted') as is_friend
        FROM users u
        JOIN followers f1 ON u.id = f1.followed_id
        JOIN followers f2 ON f1.follower_id = f2.followed_id
        WHERE f2.follower_id = ? 
        AND u.id != ?
        AND u.id NOT IN (SELECT followed_id FROM followers WHERE follower_id = ? AND status = 'accepted')
        AND u.id NOT IN (SELECT sender_id FROM friend_requests WHERE receiver_id = ? AND status = 'pending')
        AND u.is_admin = 0
        LIMIT 10
    ''', (user_id, user_id, user_id, user_id, user_id, user_id)).fetchall()
    conn.close()
    return suggested

def get_user_notifications(user_id):
    conn = get_db()
    notifications = conn.execute('''
        SELECT * FROM notifications 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()
    return notifications

def mark_notifications_as_read(user_id):
    conn = get_db()
    conn.execute('UPDATE notifications SET is_read = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_unread_notifications_count(user_id):
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = 0', (user_id,)).fetchone()['count']
    conn.close()
    return count

def get_user_chats(user_id):
    conn = get_db()
    chats = conn.execute('''
        SELECT u.id, u.username, u.real_name, u.profile_pic,
               m.content, m.created_at,
               (SELECT COUNT(*) FROM messages m2 WHERE m2.receiver_id = ? AND m2.sender_id = u.id AND m2.is_read = 0) as unread_count
        FROM users u
        JOIN messages m ON (m.sender_id = u.id AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = u.id)
        WHERE (m.sender_id = u.id OR m.receiver_id = u.id)
        AND u.id != ?
        GROUP BY u.id
        ORDER BY m.created_at DESC
    ''', (user_id, user_id, user_id, user_id)).fetchall()
    conn.close()
    return chats

def get_group_chats(user_id):
    conn = get_db()
    chats = conn.execute('''
        SELECT g.id, g.name, g.profile_pic, gm.joined_at,
               gm.is_admin,
               mg.content, mg.created_at,
               (SELECT COUNT(*) FROM group_messages mg2 WHERE mg2.group_id = g.id AND mg2.sender_id != ? AND mg2.is_read = 0 AND NOT EXISTS (SELECT 1 FROM group_messages_read gr WHERE gr.message_id = mg2.id AND gr.user_id = ?)) as unread_count
        FROM groups g
        JOIN group_members gm ON g.id = gm.group_id
        JOIN group_messages mg ON g.id = mg.group_id
        WHERE gm.user_id = ? AND gm.joined_at <= mg.created_at
        GROUP BY g.id
        ORDER BY mg.created_at DESC
    ''', (user_id, user_id, user_id)).fetchall()
    conn.close()
    return chats

def get_messages_between_users(user1_id, user2_id):
    conn = get_db()
    messages = conn.execute('''
        SELECT m.*, u.username, u.real_name, u.profile_pic
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE (m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?)
        ORDER BY m.created_at ASC
    ''', (user1_id, user2_id, user2_id, user1_id)).fetchall()
    
    # Mark messages as read
    conn.execute('UPDATE messages SET is_read = 1 WHERE sender_id = ? AND receiver_id = ? AND is_read = 0', (user2_id, user1_id))
    conn.commit()
    conn.close()
    
    return messages

def get_group_messages(group_id):
    conn = get_db()
    messages = conn.execute('''
        SELECT gm.*, u.username, u.real_name, u.profile_pic
        FROM group_messages gm
        JOIN users u ON gm.sender_id = u.id
        WHERE gm.group_id = ?
        ORDER BY gm.created_at ASC
    ''', (group_id,)).fetchall()
    
    # Mark messages as read for the current user
    if 'user_id' in session:
        user_id = session['user_id']
        conn.execute('''INSERT OR IGNORE INTO group_messages_read (message_id, user_id) 
                        SELECT id, ? FROM group_messages WHERE group_id = ? AND sender_id != ? AND NOT EXISTS (SELECT 1 FROM group_messages_read gr WHERE gr.message_id = group_messages.id AND gr.user_id = ?)''', 
                     (user_id, group_id, user_id, user_id))
        conn.commit()
    
    conn.close()
    return messages

def get_user_groups(user_id):
    conn = get_db()
    groups = conn.execute('''
        SELECT g.*, gm.is_admin, gm.joined_at
        FROM groups g
        JOIN group_members gm ON g.id = gm.group_id
        WHERE gm.user_id = ?
        ORDER BY gm.joined_at DESC
    ''', (user_id,)).fetchall()
    conn.close()
    return groups

def get_all_users():
    conn = get_db()
    users = conn.execute('SELECT * FROM users WHERE is_admin = 0 ORDER BY real_name').fetchall()
    conn.close()
    return users

def get_all_groups():
    conn = get_db()
    groups = conn.execute('SELECT * FROM groups ORDER BY name').fetchall()
    conn.close()
    return groups

def get_all_posts():
    conn = get_db()
    posts = conn.execute('''
        SELECT p.*, u.username, u.real_name, u.profile_pic
        FROM posts p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC
    ''').fetchall()
    conn.close()
    return posts

def get_all_reels():
    conn = get_db()
    reels = conn.execute('''
        SELECT r.*, u.username, u.real_name, u.profile_pic
        FROM reels r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC
    ''').fetchall()
    conn.close()
    return reels

def get_all_stories():
    conn = get_db()
    stories = conn.execute('''
        SELECT s.*, u.username, u.real_name, u.profile_pic
        FROM stories s
        JOIN users u ON s.user_id = u.id
        WHERE s.expires_at > ?
        ORDER BY s.created_at DESC
    ''', (datetime.now(),)).fetchall()
    conn.close()
    return stories

def get_all_comments():
    conn = get_db()
    comments = conn.execute('''
        SELECT c.*, p.description as post_description, u.username, u.real_name, u.profile_pic
        FROM comments c
        JOIN posts p ON c.post_id = p.id
        JOIN users u ON c.user_id = u.id
        ORDER BY c.created_at DESC
    ''').fetchall()
    conn.close()
    return comments

def get_all_reel_comments():
    conn = get_db()
    comments = conn.execute('''
        SELECT rc.*, r.description as reel_description, u.username, u.real_name, u.profile_pic
        FROM reel_comments rc
        JOIN reels r ON rc.reel_id = r.id
        JOIN users u ON rc.user_id = u.id
        ORDER BY rc.created_at DESC
    ''').fetchall()
    conn.close()
    return comments

def get_user_saved_posts(user_id):
    conn = get_db()
    saved_posts = conn.execute('''
        SELECT p.*, u.username, u.real_name, u.profile_pic
        FROM saved_posts sp
        JOIN posts p ON sp.post_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE sp.user_id = ?
        ORDER BY sp.created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()
    return saved_posts

def get_user_saved_reels(user_id):
    conn = get_db()
    saved_reels = conn.execute('''
        SELECT r.*, u.username, u.real_name, u.profile_pic
        FROM saved_reels sr
        JOIN reels r ON sr.reel_id = r.id
        JOIN users u ON r.user_id = u.id
        WHERE sr.user_id = ?
        ORDER BY sr.created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()
    return saved_reels

def get_user_reposts(user_id):
    conn = get_db()
    reposts = conn.execute('''
        SELECT rp.*, 
               COALESCE(p.description, r.description) as original_content,
               COALESCE(u_p.username, u_r.username) as original_username,
               COALESCE(u_p.real_name, u_r.real_name) as original_real_name,
               COALESCE(u_p.profile_pic, u_r.profile_pic) as original_profile_pic
        FROM reposts rp
        LEFT JOIN posts p ON rp.original_post_id = p.id
        LEFT JOIN reels r ON rp.original_reel_id = r.id
        LEFT JOIN users u_p ON p.user_id = u_p.id
        LEFT JOIN users u_r ON r.user_id = u_r.id
        WHERE rp.user_id = ?
        ORDER BY rp.created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()
    return reposts

def get_user_liked_posts(user_id):
    conn = get_db()
    liked_posts = conn.execute('''
        SELECT p.*, u.username, u.real_name, u.profile_pic
        FROM post_likes pl
        JOIN posts p ON pl.post_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE pl.user_id = ?
        ORDER BY pl.created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()
    return liked_posts

def get_user_liked_reels(user_id):
    conn = get_db()
    liked_reels = conn.execute('''
        SELECT r.*, u.username, u.real_name, u.profile_pic
        FROM reel_likes rl
        JOIN reels r ON rl.reel_id = r.id
        JOIN users u ON r.user_id = u.id
        WHERE rl.user_id = ?
        ORDER BY rl.created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()
    return liked_reels

@app.before_request
def before_request():
    if request.endpoint not in ['login', 'register', 'forgot_password', 'static'] and 'user_id' not in session:
        return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    return render_template('index.html', user=dict(user))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.json.get('username')
        password = request.json.get('password')
        
        # Check if user exists
        user = get_user_by_username(username)
        if not user:
            user = get_user_by_email(username)
        
        if user and user['password'] == hash_password(password):
            if user['is_banned'] == 1:
                return jsonify({'success': False, 'message': 'Your account has been banned.'})
            
            session['user_id'] = user['id']
            session['username'] = user['username']
            
            # Update last login
            conn = get_db()
            conn.execute('UPDATE users SET last_login = ? WHERE id = ?', (datetime.now(), user['id']))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'redirect': '/'})
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password.'})
    
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.json.get('username')
        password = request.json.get('password')
        
        # Validate password
        if len(password) < 6 or not re.search(r'\d', password) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters long and contain numbers, letters, and special characters.'})
        
        # Check if username is admin credentials
        if username == ADMIN_USERNAME and password == ADMIN_PASS:
            return jsonify({'success': False, 'message': 'This username and password combination is reserved for admin.'})
        
        # Check if username already exists
        if get_user_by_username(username):
            return jsonify({'success': False, 'message': 'Username already exists.'})
        
        # Hash password and generate unique key
        hashed_password = hash_password(password)
        unique_key = generate_unique_key()
        
        # Create user
        conn = get_db()
        conn.execute('''INSERT INTO users (username, password, real_name, unique_key) 
                        VALUES (?, ?, ?, ?)''', 
                     (username, hashed_password, username, unique_key))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Registration successful. Please login.'})
    
    return render_template('index.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.json.get('username')
        unique_key = request.json.get('unique_key')
        
        user = get_user_by_username(username)
        if user and user['unique_key'] == unique_key:
            # In a real app, we would send an email with a reset link
            # Here we'll just redirect after a delay
            return jsonify({'success': True, 'message': 'Redirecting to reset password...'})
        else:
            return jsonify({'success': False, 'message': 'Invalid username or recovery key.'})
    
    return render_template('index.html')

@app.route('/reset_password', methods=['POST'])
def reset_password():
    username = request.json.get('username')
    new_password = request.json.get('new_password')
    
    # Validate password
    if len(new_password) < 6 or not re.search(r'\d', new_password) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters long and contain numbers, letters, and special characters.'})
    
    user = get_user_by_username(username)
    if user:
        hashed_password = hash_password(new_password)
        conn = get_db()
        conn.execute('UPDATE users SET password = ? WHERE username = ?', (hashed_password, username))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Password reset successful. Please login.'})
    else:
        return jsonify({'success': False, 'message': 'User not found.'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# API endpoints for home page
@app.route('/api/stories')
def get_stories():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    # Get friends of the current user
    conn = get_db()
    friends = conn.execute('''
        SELECT u.id, u.username, u.real_name, u.profile_pic
        FROM users u
        JOIN followers f1 ON u.id = f1.followed_id
        JOIN followers f2 ON f1.followed_id = f2.follower_id
        WHERE f1.follower_id = ? AND f2.followed_id = ?
        AND f1.status = 'accepted' AND f2.status = 'accepted'
    ''', (user_id, user_id)).fetchall()
    
    stories = []
    for friend in friends:
        friend_stories = get_stories_by_user(friend['id'])
        if friend_stories:
            stories.append({
                'user': dict(friend),
                'stories': [dict(story) for story in friend_stories]
            })
    
    conn.close()
    return jsonify({'success': True, 'stories': stories})

@app.route('/api/posts')
def get_posts():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    # Get posts from friends and followed users
    conn = get_db()
    posts = conn.execute('''
        SELECT p.*, u.username, u.real_name, u.profile_pic,
               (SELECT COUNT(*) FROM post_likes WHERE post_id = p.id) as like_count,
               (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count,
               (SELECT COUNT(*) FROM reposts WHERE original_post_id = p.id) as repost_count,
               (SELECT COUNT(*) FROM saved_posts WHERE post_id = p.id AND user_id = ?) as is_saved,
               (SELECT COUNT(*) FROM post_likes WHERE post_id = p.id AND user_id = ?) as is_liked
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE (p.visibility = 'public') 
        OR (p.visibility = 'friends' AND (
            EXISTS (SELECT 1 FROM followers f1 WHERE f1.follower_id = ? AND f1.followed_id = p.user_id AND f1.status = 'accepted') OR
            EXISTS (SELECT 1 FROM followers f2 WHERE f2.follower_id = p.user_id AND f2.followed_id = ? AND f2.status = 'accepted')
        ))
        ORDER BY p.created_at DESC
        LIMIT 20
    ''', (user_id, user_id, user_id, user_id)).fetchall()
    
    result = []
    for post in posts:
        # Get comments for this post
        comments = conn.execute('''
            SELECT c.*, u.username, u.real_name, u.profile_pic
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.created_at DESC
            LIMIT 3
        ''', (post['id'],)).fetchall()
        
        result.append({
            'post': dict(post),
            'comments': [dict(comment) for comment in comments]
        })
    
    conn.close()
    return jsonify({'success': True, 'posts': result})

@app.route('/api/create_post', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    content_type = request.json.get('content_type')
    content = request.json.get('content', '')
    description = request.json.get('description', '')
    media_url = request.json.get('media_url', '')
    visibility = request.json.get('visibility', 'public')
    
    conn = get_db()
    conn.execute('''INSERT INTO posts (user_id, content_type, content, description, media_url, visibility)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (user_id, content_type, content, description, media_url, visibility))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Post created successfully'})

@app.route('/api/like_post/<int:post_id>', methods=['POST'])
def like_post(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    conn = get_db()
    # Check if already liked
    existing = conn.execute('SELECT * FROM post_likes WHERE post_id = ? AND user_id = ?', (post_id, user_id)).fetchone()
    
    if existing:
        # Remove like
        conn.execute('DELETE FROM post_likes WHERE post_id = ? AND user_id = ?', (post_id, user_id))
        conn.execute('UPDATE posts SET likes = likes - 1 WHERE id = ?', (post_id,))
        
        # Create notification for unlike (if needed)
        post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
        if post:
            conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                            VALUES (?, ?, ?, ?)''',
                         (post['user_id'], 'post_unlike', f'{get_user_by_id(user_id)["real_name"]} unliked your post', datetime.now()))
    else:
        # Add like
        conn.execute('INSERT INTO post_likes (post_id, user_id) VALUES (?, ?)', (post_id, user_id))
        conn.execute('UPDATE posts SET likes = likes + 1 WHERE id = ?', (post_id,))
        
        # Create notification for like
        post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
        if post and post['user_id'] != user_id:
            conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                            VALUES (?, ?, ?, ?)''',
                         (post['user_id'], 'post_like', f'{get_user_by_id(user_id)["real_name"]} liked your post', datetime.now()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/comment_post/<int:post_id>', methods=['POST'])
def comment_post(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    content = request.json.get('content')
    
    conn = get_db()
    conn.execute('INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)', (post_id, user_id, content))
    conn.execute('UPDATE posts SET comments = comments + 1 WHERE id = ?', (post_id,))
    
    # Create notification for comment
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    if post and post['user_id'] != user_id:
        conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                        VALUES (?, ?, ?, ?)''',
                     (post['user_id'], 'post_comment', f'{get_user_by_id(user_id)["real_name"]} commented on your post: {content[:50]}{"..." if len(content) > 50 else ""}', datetime.now()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Comment added successfully'})

@app.route('/api/share_post/<int:post_id>', methods=['POST'])
def share_post(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    content = request.json.get('content', '')
    
    conn = get_db()
    # Create a repost
    conn.execute('''INSERT INTO reposts (user_id, original_post_id, content)
                    VALUES (?, ?, ?)''', (user_id, post_id, content))
    
    # Update share count
    conn.execute('UPDATE posts SET shares = shares + 1 WHERE id = ?', (post_id,))
    
    # Create notification for share
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    if post and post['user_id'] != user_id:
        conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                        VALUES (?, ?, ?, ?)''',
                     (post['user_id'], 'post_share', f'{get_user_by_id(user_id)["real_name"]} shared your post', datetime.now()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Post shared successfully'})

@app.route('/api/save_post/<int:post_id>', methods=['POST'])
def save_post(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    conn = get_db()
    # Check if already saved
    existing = conn.execute('SELECT * FROM saved_posts WHERE post_id = ? AND user_id = ?', (post_id, user_id)).fetchone()
    
    if existing:
        # Remove from saved
        conn.execute('DELETE FROM saved_posts WHERE post_id = ? AND user_id = ?', (post_id, user_id))
        action = 'unsaved'
    else:
        # Add to saved
        conn.execute('INSERT INTO saved_posts (post_id, user_id) VALUES (?, ?)', (post_id, user_id))
        action = 'saved'
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'action': action})

@app.route('/api/follow/<int:user_id>', methods=['POST'])
def follow_user(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    current_user_id = session['user_id']
    
    conn = get_db()
    # Check if already following
    existing = conn.execute('SELECT * FROM followers WHERE follower_id = ? AND followed_id = ?', (current_user_id, user_id)).fetchone()
    
    if existing:
        if existing['status'] == 'accepted':
            # Unfollow
            conn.execute('DELETE FROM followers WHERE follower_id = ? AND followed_id = ?', (current_user_id, user_id))
            action = 'unfollowed'
        else:
            # Cancel follow request
            conn.execute('DELETE FROM followers WHERE follower_id = ? AND followed_id = ?', (current_user_id, user_id))
            action = 'request_canceled'
    else:
        # Create follow request
        conn.execute('''INSERT INTO followers (follower_id, followed_id, status)
                        VALUES (?, ?, ?)''', (current_user_id, user_id, 'accepted'))
        action = 'followed'
        
        # Create notification for follow
        if user_id != current_user_id:
            conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                            VALUES (?, ?, ?, ?)''',
                         (user_id, 'follow', f'{get_user_by_id(current_user_id)["real_name"]} started following you', datetime.now()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'action': action})

@app.route('/api/block/<int:user_id>', methods=['POST'])
def block_user(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    current_user_id = session['user_id']
    
    conn = get_db()
    # Check if already following
    existing = conn.execute('SELECT * FROM followers WHERE (follower_id = ? AND followed_id = ?) OR (follower_id = ? AND followed_id = ?)', 
                           (current_user_id, user_id, user_id, current_user_id)).fetchall()
    
    # Delete any existing relationships
    conn.execute('DELETE FROM followers WHERE (follower_id = ? AND followed_id = ?) OR (follower_id = ? AND followed_id = ?)', 
                 (current_user_id, user_id, user_id, current_user_id))
    
    # Create block relationship
    conn.execute('''INSERT INTO followers (follower_id, followed_id, status)
                    VALUES (?, ?, ?)''', (current_user_id, user_id, 'blocked'))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'User blocked successfully'})

@app.route('/api/report_post/<int:post_id>', methods=['POST'])
def report_post(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    reason = request.json.get('reason', 'No reason provided')
    
    # In a real app, this would notify admins
    # For now, we'll just log it
    print(f"Post {post_id} reported by user {user_id} for reason: {reason}")
    
    return jsonify({'success': True, 'message': 'Post reported successfully'})

@app.route('/api/hide_post/<int:post_id>', methods=['POST'])
def hide_post(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # In a real app, this would add the post to a hidden list
    # For now, we'll just return success
    return jsonify({'success': True, 'message': 'Post hidden successfully'})

@app.route('/api/turn_on_notifications/<int:post_id>', methods=['POST'])
def turn_on_notifications(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # In a real app, this would subscribe the user to notifications for this post
    # For now, we'll just return success
    return jsonify({'success': True, 'message': 'Notifications turned on for this post'})

@app.route('/api/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    conn = get_db()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    
    if post and (post['user_id'] == user_id or get_user_by_id(user_id)['is_admin'] == 1):
        conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
        conn.execute('DELETE FROM comments WHERE post_id = ?', (post_id,))
        conn.execute('DELETE FROM post_likes WHERE post_id = ?', (post_id,))
        conn.execute('DELETE FROM saved_posts WHERE post_id = ?', (post_id,))
        conn.execute('DELETE FROM reposts WHERE original_post_id = ?', (post_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Post deleted successfully'})
    else:
        conn.close()
        return jsonify({'success': False, 'message': 'You do not have permission to delete this post'})

# API endpoints for reels
@app.route('/api/reels')
def get_reels():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    conn = get_db()
    reels = conn.execute('''
        SELECT r.*, u.username, u.real_name, u.profile_pic,
               (SELECT COUNT(*) FROM reel_likes WHERE reel_id = r.id) as like_count,
               (SELECT COUNT(*) FROM reel_comments WHERE reel_id = r.id) as comment_count,
               (SELECT COUNT(*) FROM reposts WHERE original_reel_id = r.id) as repost_count,
               (SELECT COUNT(*) FROM saved_reels WHERE reel_id = r.id AND user_id = ?) as is_saved,
               (SELECT COUNT(*) FROM reel_likes WHERE reel_id = r.id AND user_id = ?) as is_liked
        FROM reels r
        JOIN users u ON r.user_id = u.id
        WHERE r.visibility = 'public'
        OR (r.visibility = 'friends' AND (
            EXISTS (SELECT 1 FROM followers f1 WHERE f1.follower_id = ? AND f1.followed_id = r.user_id AND f1.status = 'accepted') OR
            EXISTS (SELECT 1 FROM followers f2 WHERE f2.follower_id = r.user_id AND f2.followed_id = ? AND f2.status = 'accepted')
        ))
        ORDER BY r.created_at DESC
        LIMIT 20
    ''', (user_id, user_id, user_id, user_id)).fetchall()
    
    result = []
    for reel in reels:
        # Get comments for this reel
        comments = conn.execute('''
            SELECT rc.*, u.username, u.real_name, u.profile_pic
            FROM reel_comments rc
            JOIN users u ON rc.user_id = u.id
            WHERE rc.reel_id = ?
            ORDER BY rc.created_at DESC
            LIMIT 3
        ''', (reel['id'],)).fetchall()
        
        result.append({
            'reel': dict(reel),
            'comments': [dict(comment) for comment in comments]
        })
    
    conn.close()
    return jsonify({'success': True, 'reels': result})

@app.route('/api/create_reel', methods=['POST'])
def create_reel():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    video_url = request.json.get('video_url')
    description = request.json.get('description', '')
    visibility = request.json.get('visibility', 'public')
    
    conn = get_db()
    conn.execute('''INSERT INTO reels (user_id, video_url, description, visibility)
                    VALUES (?, ?, ?, ?)''',
                 (user_id, video_url, description, visibility))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Reel created successfully'})

@app.route('/api/like_reel/<int:reel_id>', methods=['POST'])
def like_reel(reel_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    conn = get_db()
    # Check if already liked
    existing = conn.execute('SELECT * FROM reel_likes WHERE reel_id = ? AND user_id = ?', (reel_id, user_id)).fetchone()
    
    if existing:
        # Remove like
        conn.execute('DELETE FROM reel_likes WHERE reel_id = ? AND user_id = ?', (reel_id, user_id))
        conn.execute('UPDATE reels SET likes = likes - 1 WHERE id = ?', (reel_id,))
        
        # Create notification for unlike
        reel = conn.execute('SELECT * FROM reels WHERE id = ?', (reel_id,)).fetchone()
        if reel:
            conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                            VALUES (?, ?, ?, ?)''',
                         (reel['user_id'], 'reel_unlike', f'{get_user_by_id(user_id)["real_name"]} unliked your reel', datetime.now()))
    else:
        # Add like
        conn.execute('INSERT INTO reel_likes (reel_id, user_id) VALUES (?, ?)', (reel_id, user_id))
        conn.execute('UPDATE reels SET likes = likes + 1 WHERE id = ?', (reel_id,))
        
        # Create notification for like
        reel = conn.execute('SELECT * FROM reels WHERE id = ?', (reel_id,)).fetchone()
        if reel and reel['user_id'] != user_id:
            conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                            VALUES (?, ?, ?, ?)''',
                         (reel['user_id'], 'reel_like', f'{get_user_by_id(user_id)["real_name"]} liked your reel', datetime.now()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/comment_reel/<int:reel_id>', methods=['POST'])
def comment_reel(reel_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    content = request.json.get('content')
    
    conn = get_db()
    conn.execute('INSERT INTO reel_comments (reel_id, user_id, content) VALUES (?, ?, ?)', (reel_id, user_id, content))
    conn.execute('UPDATE reels SET comments = comments + 1 WHERE id = ?', (reel_id,))
    
    # Create notification for comment
    reel = conn.execute('SELECT * FROM reels WHERE id = ?', (reel_id,)).fetchone()
    if reel and reel['user_id'] != user_id:
        conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                        VALUES (?, ?, ?, ?)''',
                     (reel['user_id'], 'reel_comment', f'{get_user_by_id(user_id)["real_name"]} commented on your reel: {content[:50]}{"..." if len(content) > 50 else ""}', datetime.now()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Comment added successfully'})

@app.route('/api/share_reel/<int:reel_id>', methods=['POST'])
def share_reel(reel_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    content = request.json.get('content', '')
    
    conn = get_db()
    # Create a repost
    conn.execute('''INSERT INTO reposts (user_id, original_reel_id, content)
                    VALUES (?, ?, ?)''', (user_id, reel_id, content))
    
    # Update share count
    conn.execute('UPDATE reels SET shares = shares + 1 WHERE id = ?', (reel_id,))
    
    # Create notification for share
    reel = conn.execute('SELECT * FROM reels WHERE id = ?', (reel_id,)).fetchone()
    if reel and reel['user_id'] != user_id:
        conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                        VALUES (?, ?, ?, ?)''',
                     (reel['user_id'], 'reel_share', f'{get_user_by_id(user_id)["real_name"]} shared your reel', datetime.now()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Reel shared successfully'})

@app.route('/api/save_reel/<int:reel_id>', methods=['POST'])
def save_reel(reel_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    conn = get_db()
    # Check if already saved
    existing = conn.execute('SELECT * FROM saved_reels WHERE reel_id = ? AND user_id = ?', (reel_id, user_id)).fetchone()
    
    if existing:
        # Remove from saved
        conn.execute('DELETE FROM saved_reels WHERE reel_id = ? AND user_id = ?', (reel_id, user_id))
        action = 'unsaved'
    else:
        # Add to saved
        conn.execute('INSERT INTO saved_reels (reel_id, user_id) VALUES (?, ?)', (reel_id, user_id))
        action = 'saved'
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'action': action})

@app.route('/api/report_reel/<int:reel_id>', methods=['POST'])
def report_reel(reel_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    reason = request.json.get('reason', 'No reason provided')
    
    # In a real app, this would notify admins
    # For now, we'll just log it
    print(f"Reel {reel_id} reported by user {user_id} for reason: {reason}")
    
    return jsonify({'success': True, 'message': 'Reel reported successfully'})

@app.route('/api/delete_reel/<int:reel_id>', methods=['POST'])
def delete_reel(reel_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    conn = get_db()
    reel = conn.execute('SELECT * FROM reels WHERE id = ?', (reel_id,)).fetchone()
    
    if reel and (reel['user_id'] == user_id or get_user_by_id(user_id)['is_admin'] == 1):
        conn.execute('DELETE FROM reels WHERE id = ?', (reel_id,))
        conn.execute('DELETE FROM reel_comments WHERE reel_id = ?', (reel_id,))
        conn.execute('DELETE FROM reel_likes WHERE reel_id = ?', (reel_id,))
        conn.execute('DELETE FROM saved_reels WHERE reel_id = ?', (reel_id,))
        conn.execute('DELETE FROM reposts WHERE original_reel_id = ?', (reel_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Reel deleted successfully'})
    else:
        conn.close()
        return jsonify({'success': False, 'message': 'You do not have permission to delete this reel'})

# API endpoints for stories
@app.route('/api/create_story', methods=['POST'])
def create_story():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    content_type = request.json.get('content_type')
    content_url = request.json.get('content_url')
    duration = request.json.get('duration', 30)  # Default 30 seconds
    
    # Stories expire after duration
    expires_at = datetime.now() + timedelta(seconds=duration)
    
    conn = get_db()
    conn.execute('''INSERT INTO stories (user_id, content_type, content_url, duration, expires_at)
                    VALUES (?, ?, ?, ?, ?)''',
                 (user_id, content_type, content_url, duration, expires_at))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Story created successfully'})

@app.route('/api/view_story/<int:story_id>', methods=['POST'])
def view_story(story_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    conn = get_db()
    # Check if user is friend of story owner
    story = conn.execute('SELECT * FROM stories WHERE id = ?', (story_id,)).fetchone()
    if not story:
        conn.close()
        return jsonify({'success': False, 'message': 'Story not found'})
    
    story_user_id = story['user_id']
    
    # Check if users are friends
    is_friend = conn.execute('''
        SELECT COUNT(*) as count 
        FROM followers f1 
        JOIN followers f2 ON f1.followed_id = f2.follower_id 
        WHERE f1.follower_id = ? AND f2.followed_id = ? 
        AND f1.status = 'accepted' AND f2.status = 'accepted'
    ''', (user_id, story_user_id)).fetchone()['count'] > 0
    
    if not is_friend and story_user_id != user_id:
        conn.close()
        return jsonify({'success': False, 'message': 'You can only view stories from friends'})
    
    # Record view if not already viewed
    existing = conn.execute('SELECT * FROM story_views WHERE story_id = ? AND user_id = ?', (story_id, user_id)).fetchone()
    if not existing:
        conn.execute('INSERT INTO story_views (story_id, user_id) VALUES (?, ?)', (story_id, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# API endpoints for friends
@app.route('/api/friends')
def get_friends():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    conn = get_db()
    
    # Followers
    followers = conn.execute('''
        SELECT u.*, 
               (SELECT COUNT(*) FROM followers f2 WHERE f2.follower_id = u.id AND f2.followed_id = ? AND f2.status = 'accepted') as is_following,
               (SELECT COUNT(*) FROM followers f3 WHERE f3.follower_id = ? AND f3.followed_id = u.id AND f3.status = 'accepted') as is_friend,
               (SELECT COUNT(*) FROM followers f4 WHERE f4.follower_id = ? AND f4.followed_id = u.id AND f4.status = 'blocked') as is_blocked,
               (SELECT COUNT(*) FROM followers f5 WHERE f5.follower_id = u.id AND f5.followed_id = ? AND f5.status = 'blocked') as blocked_me
        FROM users u
        JOIN followers f ON u.id = f.followed_id
        WHERE f.follower_id = ? AND f.status = 'accepted'
        AND u.id != ?
        ORDER BY u.real_name
    ''', (user_id, user_id, user_id, user_id, user_id, user_id)).fetchall()
    
    # Following
    following = conn.execute('''
        SELECT u.*, 
               (SELECT COUNT(*) FROM followers f2 WHERE f2.follower_id = u.id AND f2.followed_id = ? AND f2.status = 'accepted') as is_following,
               (SELECT COUNT(*) FROM followers f3 WHERE f3.follower_id = ? AND f3.followed_id = u.id AND f3.status = 'accepted') as is_friend,
               (SELECT COUNT(*) FROM followers f4 WHERE f4.follower_id = ? AND f4.followed_id = u.id AND f4.status = 'blocked') as is_blocked,
               (SELECT COUNT(*) FROM followers f5 WHERE f5.follower_id = u.id AND f5.followed_id = ? AND f5.status = 'blocked') as blocked_me
        FROM users u
        JOIN followers f ON u.id = f.followed_id
        WHERE f.follower_id = ? AND f.status = 'accepted'
        AND u.id != ?
        ORDER BY u.real_name
    ''', (user_id, user_id, user_id, user_id, user_id, user_id)).fetchall()
    
    # Friends (mutual follows)
    friends = conn.execute('''
        SELECT u.*, 
               (SELECT COUNT(*) FROM followers f2 WHERE f2.follower_id = u.id AND f2.followed_id = ? AND f2.status = 'accepted') as is_following,
               (SELECT COUNT(*) FROM followers f3 WHERE f3.follower_id = ? AND f3.followed_id = u.id AND f3.status = 'accepted') as is_friend,
               (SELECT COUNT(*) FROM followers f4 WHERE f4.follower_id = ? AND f4.followed_id = u.id AND f4.status = 'blocked') as is_blocked,
               (SELECT COUNT(*) FROM followers f5 WHERE f5.follower_id = u.id AND f5.followed_id = ? AND f5.status = 'blocked') as blocked_me
        FROM users u
        JOIN followers f1 ON u.id = f1.followed_id
        JOIN followers f2 ON f1.followed_id = f2.follower_id
        WHERE f1.follower_id = ? AND f2.followed_id = ?
        AND f1.status = 'accepted' AND f2.status = 'accepted'
        AND u.id != ?
        ORDER BY u.real_name
    ''', (user_id, user_id, user_id, user_id, user_id, user_id, user_id)).fetchall()
    
    # Friend requests received
    friend_requests = conn.execute('''
        SELECT fr.*, u.username, u.real_name, u.profile_pic,
               (SELECT COUNT(*) FROM followers f WHERE f.follower_id = u.id AND f.followed_id = ? AND f.status = 'accepted') as mutual_friends
        FROM friend_requests fr
        JOIN users u ON fr.sender_id = u.id
        WHERE fr.receiver_id = ? AND fr.status = 'pending'
        ORDER BY fr.created_at DESC
    ''', (user_id, user_id)).fetchall()
    
    # Suggested friends
    suggested = get_suggested_users(user_id)
    
    conn.close()
    
    return jsonify({
        'success': True,
        'followers': [dict(follower) for follower in followers],
        'following': [dict(follow) for follow in following],
        'friends': [dict(friend) for friend in friends],
        'friend_requests': [dict(req) for req in friend_requests],
        'suggested': [dict(sugg) for sugg in suggested],
        'counts': {
            'followers': len(followers),
            'following': len(following),
            'friends': len(friends),
            'friend_requests': len(friend_requests),
            'suggested': len(suggested)
        }
    })

@app.route('/api/send_friend_request/<int:user_id>', methods=['POST'])
def send_friend_request(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    current_user_id = session['user_id']
    
    conn = get_db()
    # Check if already have a relationship
    existing = conn.execute('SELECT * FROM friend_requests WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)', 
                           (current_user_id, user_id, user_id, current_user_id)).fetchone()
    
    if existing:
        conn.close()
        return jsonify({'success': False, 'message': 'Friend request already sent or pending'})
    
    # Create friend request
    conn.execute('''INSERT INTO friend_requests (sender_id, receiver_id, status)
                    VALUES (?, ?, ?)''', (current_user_id, user_id, 'pending'))
    
    # Create notification
    conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                    VALUES (?, ?, ?, ?)''',
                 (user_id, 'friend_request', f'{get_user_by_id(current_user_id)["real_name"]} sent you a friend request', datetime.now()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Friend request sent successfully'})

@app.route('/api/accept_friend_request/<int:request_id>', methods=['POST'])
def accept_friend_request(request_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    conn = get_db()
    request = conn.execute('SELECT * FROM friend_requests WHERE id = ? AND receiver_id = ?', (request_id, user_id)).fetchone()
    
    if not request:
        conn.close()
        return jsonify({'success': False, 'message': 'Request not found'})
    
    # Update request status
    conn.execute('UPDATE friend_requests SET status = ? WHERE id = ?', ('accepted', request_id))
    
    # Create mutual follow relationship
    sender_id = request['sender_id']
    conn.execute('''INSERT INTO followers (follower_id, followed_id, status)
                    VALUES (?, ?, ?)''', (sender_id, user_id, 'accepted'))
    conn.execute('''INSERT INTO followers (follower_id, followed_id, status)
                    VALUES (?, ?, ?)''', (user_id, sender_id, 'accepted'))
    
    # Create notification
    conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                    VALUES (?, ?, ?, ?)''',
                 (sender_id, 'friend_accepted', f'{get_user_by_id(user_id)["real_name"]} accepted your friend request', datetime.now()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Friend request accepted'})

@app.route('/api/decline_friend_request/<int:request_id>', methods=['POST'])
def decline_friend_request(request_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    conn = get_db()
    conn.execute('UPDATE friend_requests SET status = ? WHERE id = ? AND receiver_id = ?', ('declined', request_id, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Friend request declined'})

@app.route('/api/unfollow/<int:user_id>', methods=['POST'])
def unfollow(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    current_user_id = session['user_id']
    
    conn = get_db()
    conn.execute('DELETE FROM followers WHERE follower_id = ? AND followed_id = ?', (current_user_id, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Unfollowed successfully'})

@app.route('/api/remove_suggestion/<int:user_id>', methods=['POST'])
def remove_suggestion(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # In a real app, this would add the user to a "do not suggest" list
    # For now, we'll just return success
    return jsonify({'success': True, 'message': 'User removed from suggestions'})

# API endpoints for inbox
@app.route('/api/inbox')
def get_inbox():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    chats = get_user_chats(user_id)
    group_chats = get_group_chats(user_id)
    unread_count = sum(chat['unread_count'] for chat in chats) + sum(chat['unread_count'] for chat in group_chats)
    
    return jsonify({
        'success': True,
        'chats': [dict(chat) for chat in chats],
        'group_chats': [dict(chat) for chat in group_chats],
        'unread_count': unread_count
    })

@app.route('/api/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    receiver_id = request.json.get('receiver_id')
    content = request.json.get('content', '')
    content_type = request.json.get('content_type', 'text')
    media_url = request.json.get('media_url', '')
    
    conn = get_db()
    if content_type == 'text' and content.strip():
        conn.execute('''INSERT INTO messages (sender_id, receiver_id, content_type, content)
                        VALUES (?, ?, ?, ?)''',
                     (user_id, receiver_id, content_type, content))
        
        # Create notification
        conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                        VALUES (?, ?, ?, ?)''',
                     (receiver_id, 'message', f'{get_user_by_id(user_id)["real_name"]} sent you a message', datetime.now()))
    elif media_url:
        conn.execute('''INSERT INTO messages (sender_id, receiver_id, content_type, media_url)
                        VALUES (?, ?, ?, ?)''',
                     (user_id, receiver_id, content_type, media_url))
        
        # Create notification
        conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                        VALUES (?, ?, ?, ?)''',
                     (receiver_id, 'message', f'{get_user_by_id(user_id)["real_name"]} sent you a {content_type}', datetime.now()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Message sent successfully'})

@app.route('/api/send_group_message', methods=['POST'])
def send_group_message():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    group_id = request.json.get('group_id')
    content = request.json.get('content', '')
    content_type = request.json.get('content_type', 'text')
    media_url = request.json.get('media_url', '')
    
    conn = get_db()
    # Check if user is in group
    member = conn.execute('SELECT * FROM group_members WHERE group_id = ? AND user_id = ?', (group_id, user_id)).fetchone()
    if not member:
        conn.close()
        return jsonify({'success': False, 'message': 'You are not a member of this group'})
    
    if content_type == 'text' and content.strip():
        conn.execute('''INSERT INTO group_messages (group_id, sender_id, content_type, content)
                        VALUES (?, ?, ?, ?)''',
                     (group_id, user_id, content_type, content))
        
        # Create notification for group members (except sender)
        group_members = conn.execute('SELECT user_id FROM group_members WHERE group_id = ? AND user_id != ?', (group_id, user_id)).fetchall()
        for member in group_members:
            conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                            VALUES (?, ?, ?, ?)''',
                         (member['user_id'], 'group_message', f'{get_user_by_id(user_id)["real_name"]} sent a message in {get_group_by_id(group_id)["name"]}', datetime.now()))
    elif media_url:
        conn.execute('''INSERT INTO group_messages (group_id, sender_id, content_type, media_url)
                        VALUES (?, ?, ?, ?)''',
                     (group_id, user_id, content_type, media_url))
        
        # Create notification for group members (except sender)
        group_members = conn.execute('SELECT user_id FROM group_members WHERE group_id = ? AND user_id != ?', (group_id, user_id)).fetchall()
        for member in group_members:
            conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                            VALUES (?, ?, ?, ?)''',
                         (member['user_id'], 'group_message', f'{get_user_by_id(user_id)["real_name"]} sent a {content_type} in {get_group_by_id(group_id)["name"]}', datetime.now()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Message sent successfully'})

@app.route('/api/create_group', methods=['POST'])
def create_group():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    name = request.json.get('name')
    description = request.json.get('description', '')
    profile_pic = request.json.get('profile_pic', 'group_default.jpg')
    allow_messages = request.json.get('allow_messages', 1)
    allow_add_members = request.json.get('allow_add_members', 1)
    require_approval = request.json.get('require_approval', 0)
    
    # Generate unique group link
    group_link = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    conn = get_db()
    conn.execute('''INSERT INTO groups (name, description, profile_pic, creator_id, group_link, allow_messages, allow_add_members, require_approval)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (name, description, profile_pic, user_id, group_link, allow_messages, allow_add_members, require_approval))
    
    group_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    
    # Add creator as admin
    conn.execute('''INSERT INTO group_members (group_id, user_id, is_admin)
                    VALUES (?, ?, ?)''', (group_id, user_id, 1))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Group created successfully', 'group_id': group_id})

@app.route('/api/join_group/<group_link>')
def join_group(group_link):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    conn = get_db()
    group = conn.execute('SELECT * FROM groups WHERE group_link = ?', (group_link,)).fetchone()
    if not group:
        conn.close()
        return jsonify({'success': False, 'message': 'Group not found'})
    
    # Check if already a member
    existing = conn.execute('SELECT * FROM group_members WHERE group_id = ? AND user_id = ?', (group['id'], user_id)).fetchone()
    if existing:
        conn.close()
        return jsonify({'success': False, 'message': 'You are already a member of this group'})
    
    # If approval required, create pending request
    if group['require_approval'] == 1:
        # In a real app, this would create a pending request
        # For simplicity, we'll just add the user
        conn.execute('''INSERT INTO group_members (group_id, user_id, is_admin)
                        VALUES (?, ?, ?)''', (group['id'], user_id, 0))
    else:
        conn.execute('''INSERT INTO group_members (group_id, user_id, is_admin)
                        VALUES (?, ?, ?)''', (group['id'], user_id, 0))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Joined group successfully'})

@app.route('/api/leave_group/<int:group_id>', methods=['POST'])
def leave_group(group_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    conn = get_db()
    # Check if user is the creator
    group = conn.execute('SELECT * FROM groups WHERE id = ?', (group_id,)).fetchone()
    if not group:
        conn.close()
        return jsonify({'success': False, 'message': 'Group not found'})
    
    if group['creator_id'] == user_id:
        # If creator is leaving, transfer ownership to another admin or random member
        other_admins = conn.execute('SELECT user_id FROM group_members WHERE group_id = ? AND user_id != ? AND is_admin = 1', (group_id, user_id)).fetchall()
        if other_admins:
            new_creator = other_admins[0]['user_id']
            conn.execute('UPDATE groups SET creator_id = ? WHERE id = ?', (new_creator, group_id))
        else:
            # No other admins, make a random member the admin
            members = conn.execute('SELECT user_id FROM group_members WHERE group_id = ? AND user_id != ?', (group_id, user_id)).fetchall()
            if members:
                new_creator = members[0]['user_id']
                conn.execute('UPDATE groups SET creator_id = ? WHERE id = ?', (new_creator, group_id))
                conn.execute('UPDATE group_members SET is_admin = 1 WHERE group_id = ? AND user_id = ?', (group_id, new_creator))
        
        # Remove creator from members
        conn.execute('DELETE FROM group_members WHERE group_id = ? AND user_id = ?', (group_id, user_id))
    else:
        # Regular member leaving
        conn.execute('DELETE FROM group_members WHERE group_id = ? AND user_id = ?', (group_id, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Left group successfully'})

@app.route('/api/remove_from_group/<int:group_id>/<int:user_id>', methods=['POST'])
def remove_from_group(group_id, user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    current_user_id = session['user_id']
    
    conn = get_db()
    # Check if current user is admin or creator
    member = conn.execute('SELECT * FROM group_members WHERE group_id = ? AND user_id = ?', (group_id, current_user_id)).fetchone()
    group = conn.execute('SELECT * FROM groups WHERE id = ?', (group_id,)).fetchone()
    
    if not member or not group:
        conn.close()
        return jsonify({'success': False, 'message': 'Access denied'})
    
    if member['is_admin'] == 0 and group['creator_id'] != current_user_id:
        conn.close()
        return jsonify({'success': False, 'message': 'Only admins can remove members'})
    
    # Don't allow removing the creator
    if group['creator_id'] == user_id:
        conn.close()
        return jsonify({'success': False, 'message': 'Cannot remove the group creator'})
    
    # Remove member
    conn.execute('DELETE FROM group_members WHERE group_id = ? AND user_id = ?', (group_id, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Member removed successfully'})

@app.route('/api/toggle_group_admin/<int:group_id>/<int:user_id>', methods=['POST'])
def toggle_group_admin(group_id, user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    current_user_id = session['user_id']
    
    conn = get_db()
    # Check if current user is creator
    group = conn.execute('SELECT * FROM groups WHERE id = ?', (group_id,)).fetchone()
    if not group or group['creator_id'] != current_user_id:
        conn.close()
        return jsonify({'success': False, 'message': 'Only the creator can edit admin privileges'})
    
    # Don't allow editing creator's privileges
    if group['creator_id'] == user_id:
        conn.close()
        return jsonify({'success': False, 'message': 'Cannot edit the creator\'s admin privileges'})
    
    # Toggle admin status
    member = conn.execute('SELECT * FROM group_members WHERE group_id = ? AND user_id = ?', (group_id, user_id)).fetchone()
    if member:
        new_status = 0 if member['is_admin'] == 1 else 1
        conn.execute('UPDATE group_members SET is_admin = ? WHERE group_id = ? AND user_id = ?', (new_status, group_id, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Admin privileges updated'})

@app.route('/api/update_group_permissions/<int:group_id>', methods=['POST'])
def update_group_permissions(group_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    current_user_id = session['user_id']
    allow_messages = request.json.get('allow_messages', 1)
    allow_add_members = request.json.get('allow_add_members', 1)
    require_approval = request.json.get('require_approval', 0)
    
    conn = get_db()
    # Check if current user is admin or creator
    member = conn.execute('SELECT * FROM group_members WHERE group_id = ? AND user_id = ?', (group_id, current_user_id)).fetchone()
    group = conn.execute('SELECT * FROM groups WHERE id = ?', (group_id,)).fetchone()
    
    if not member or not group:
        conn.close()
        return jsonify({'success': False, 'message': 'Access denied'})
    
    if member['is_admin'] == 0 and group['creator_id'] != current_user_id:
        conn.close()
        return jsonify({'success': False, 'message': 'Only admins can edit group permissions'})
    
    # Update permissions
    conn.execute('''UPDATE groups 
                    SET allow_messages = ?, allow_add_members = ?, require_approval = ?
                    WHERE id = ?''', (allow_messages, allow_add_members, require_approval, group_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Group permissions updated'})

# API endpoints for profile
@app.route('/api/profile/<int:user_id>')
def get_profile(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    current_user_id = session['user_id']
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Get counts
    followers_count = get_followers_count(user_id)
    following_count = get_following_count(user_id)
    friends_count = get_friends_count(user_id)
    
    # Check relationship
    is_following = conn.execute('SELECT COUNT(*) as count FROM followers WHERE follower_id = ? AND followed_id = ? AND status = "accepted"', (current_user_id, user_id)).fetchone()['count'] > 0
    is_followed_by = conn.execute('SELECT COUNT(*) as count FROM followers WHERE follower_id = ? AND followed_id = ? AND status = "accepted"', (user_id, current_user_id)).fetchone()['count'] > 0
    is_friend = is_following and is_followed_by
    is_blocked = conn.execute('SELECT COUNT(*) as count FROM followers WHERE follower_id = ? AND followed_id = ? AND status = "blocked"', (current_user_id, user_id)).fetchone()['count'] > 0
    
    # Get mutual friends
    mutual_friends = conn.execute('''
        SELECT u.id, u.real_name, u.profile_pic
        FROM users u
        JOIN followers f1 ON u.id = f1.followed_id
        JOIN followers f2 ON f1.followed_id = f2.follower_id
        WHERE f1.follower_id = ? AND f2.followed_id = ?
        AND f1.status = 'accepted' AND f2.status = 'accepted'
        LIMIT 3
    ''', (current_user_id, user_id)).fetchall()
    
    conn.close()
    
    profile_data = {
        'user': dict(user),
        'counts': {
            'followers': followers_count,
            'following': following_count,
            'friends': friends_count
        },
        'relationship': {
            'is_following': is_following,
            'is_followed_by': is_followed_by,
            'is_friend': is_friend,
            'is_blocked': is_blocked
        },
        'mutual_friends': [dict(mf) for mf in mutual_friends]
    }
    
    return jsonify({'success': True, 'profile': profile_data})

@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    real_name = request.json.get('real_name')
    username = request.json.get('username')
    bio = request.json.get('bio', '')
    dob = request.json.get('dob', '')
    gender = request.json.get('gender', '')
    pronouns = request.json.get('pronouns', '')
    work_info = request.json.get('work_info', '')
    university = request.json.get('university', '')
    secondary_school = request.json.get('secondary_school', '')
    location = request.json.get('location', '')
    phone = request.json.get('phone', '')
    email = request.json.get('email', '')
    website = request.json.get('website', '')
    social_link = request.json.get('social_link', '')
    relationship_status = request.json.get('relationship_status', '')
    spouse = request.json.get('spouse', '')
    
    conn = get_db()
    
    # Check if username is already taken by someone else
    existing_user = conn.execute('SELECT id FROM users WHERE username = ? AND id != ?', (username, user_id)).fetchone()
    if existing_user:
        conn.close()
        return jsonify({'success': False, 'message': 'Username already taken'})
    
    # Update profile
    conn.execute('''UPDATE users 
                    SET real_name = ?, username = ?, bio = ?, dob = ?, gender = ?, pronouns = ?,
                        work_info = ?, university = ?, secondary_school = ?,
                        location = ?, phone = ?, email = ?, website = ?, social_link = ?,
                        relationship_status = ?, spouse = ?
                    WHERE id = ?''',
                 (real_name, username, bio, dob, gender, pronouns,
                  work_info, university, secondary_school,
                  location, phone, email, website, social_link,
                  relationship_status, spouse, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Profile updated successfully'})

@app.route('/api/update_profile_pic', methods=['POST'])
def update_profile_pic():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    profile_pic = request.json.get('profile_pic')
    
    conn = get_db()
    conn.execute('UPDATE users SET profile_pic = ? WHERE id = ?', (profile_pic, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Profile picture updated successfully'})

@app.route('/api/get_user_posts/<int:user_id>')
def get_user_posts(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    current_user_id = session['user_id']
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Check privacy settings
    posts = conn.execute('''
        SELECT p.*, u.username, u.real_name, u.profile_pic
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.user_id = ?
        AND (p.visibility = 'public' OR 
             (p.visibility = 'friends' AND 
              (EXISTS (SELECT 1 FROM followers f1 WHERE f1.follower_id = ? AND f1.followed_id = p.user_id AND f1.status = 'accepted') OR
               EXISTS (SELECT 1 FROM followers f2 WHERE f2.follower_id = p.user_id AND f2.followed_id = ? AND f2.status = 'accepted')
              )
             )
            )
        ORDER BY p.created_at DESC
    ''', (user_id, current_user_id, current_user_id)).fetchall()
    
    result = [dict(post) for post in posts]
    conn.close()
    
    return jsonify({'success': True, 'posts': result})

@app.route('/api/get_user_reels/<int:user_id>')
def get_user_reels(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    current_user_id = session['user_id']
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Check privacy settings
    reels = conn.execute('''
        SELECT r.*, u.username, u.real_name, u.profile_pic
        FROM reels r
        JOIN users u ON r.user_id = u.id
        WHERE r.user_id = ?
        AND (r.visibility = 'public' OR 
             (r.visibility = 'friends' AND 
              (EXISTS (SELECT 1 FROM followers f1 WHERE f1.follower_id = ? AND f1.followed_id = r.user_id AND f1.status = 'accepted') OR
               EXISTS (SELECT 1 FROM followers f2 WHERE f2.follower_id = r.user_id AND f2.followed_id = ? AND f2.status = 'accepted')
              )
             )
            )
        ORDER BY r.created_at DESC
    ''', (user_id, current_user_id, current_user_id)).fetchall()
    
    result = [dict(reel) for reel in reels]
    conn.close()
    
    return jsonify({'success': True, 'reels': result})

@app.route('/api/get_user_saved_posts')
def get_user_saved_posts():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    posts = get_user_saved_posts(user_id)
    result = []
    for post in posts:
        # Get comments for this post
        conn = get_db()
        comments = conn.execute('''
            SELECT c.*, u.username, u.real_name, u.profile_pic
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.created_at DESC
            LIMIT 3
        ''', (post['id'],)).fetchall()
        
        result.append({
            'post': dict(post),
            'comments': [dict(comment) for comment in comments]
        })
        conn.close()
    
    return jsonify({'success': True, 'posts': result})

@app.route('/api/get_user_saved_reels')
def get_user_saved_reels():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    reels = get_user_saved_reels(user_id)
    result = []
    for reel in reels:
        # Get comments for this reel
        conn = get_db()
        comments = conn.execute('''
            SELECT rc.*, u.username, u.real_name, u.profile_pic
            FROM reel_comments rc
            JOIN users u ON rc.user_id = u.id
            WHERE rc.reel_id = ?
            ORDER BY rc.created_at DESC
            LIMIT 3
        ''', (reel['id'],)).fetchall()
        
        result.append({
            'reel': dict(reel),
            'comments': [dict(comment) for comment in comments]
        })
        conn.close()
    
    return jsonify({'success': True, 'reels': result})

@app.route('/api/get_user_reposts')
def get_user_reposts():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    reposts = get_user_reposts(user_id)
    result = []
    for repost in reposts:
        # Get comments for the original content
        conn = get_db()
        comments = []
        if repost['original_post_id']:
            comments = conn.execute('''
                SELECT c.*, u.username, u.real_name, u.profile_pic
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.post_id = ?
                ORDER BY c.created_at DESC
                LIMIT 3
            ''', (repost['original_post_id'],)).fetchall()
        elif repost['original_reel_id']:
            comments = conn.execute('''
                SELECT rc.*, u.username, u.real_name, u.profile_pic
                FROM reel_comments rc
                JOIN users u ON rc.user_id = u.id
                WHERE rc.reel_id = ?
                ORDER BY rc.created_at DESC
                LIMIT 3
            ''', (repost['original_reel_id'],)).fetchall()
        
        result.append({
            'repost': dict(repost),
            'comments': [dict(comment) for comment in comments]
        })
        conn.close()
    
    return jsonify({'success': True, 'reposts': result})

@app.route('/api/get_user_liked_posts')
def get_user_liked_posts():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    posts = get_user_liked_posts(user_id)
    result = []
    for post in posts:
        # Get comments for this post
        conn = get_db()
        comments = conn.execute('''
            SELECT c.*, u.username, u.real_name, u.profile_pic
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.created_at DESC
            LIMIT 3
        ''', (post['id'],)).fetchall()
        
        result.append({
            'post': dict(post),
            'comments': [dict(comment) for comment in comments]
        })
        conn.close()
    
    return jsonify({'success': True, 'posts': result})

@app.route('/api/get_user_liked_reels')
def get_user_liked_reels():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    reels = get_user_liked_reels(user_id)
    result = []
    for reel in reels:
        # Get comments for this reel
        conn = get_db()
        comments = conn.execute('''
            SELECT rc.*, u.username, u.real_name, u.profile_pic
            FROM reel_comments rc
            JOIN users u ON rc.user_id = u.id
            WHERE rc.reel_id = ?
            ORDER BY rc.created_at DESC
            LIMIT 3
        ''', (reel['id'],)).fetchall()
        
        result.append({
            'reel': dict(reel),
            'comments': [dict(comment) for comment in comments]
        })
        conn.close()
    
    return jsonify({'success': True, 'reels': result})

@app.route('/api/delete_profile_content/<content_type>/<int:content_id>', methods=['POST'])
def delete_profile_content(content_type, content_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    conn = get_db()
    
    if content_type == 'post':
        post = conn.execute('SELECT * FROM posts WHERE id = ?', (content_id,)).fetchone()
        if post and post['user_id'] == user_id:
            conn.execute('DELETE FROM posts WHERE id = ?', (content_id,))
            conn.execute('DELETE FROM comments WHERE post_id = ?', (content_id,))
            conn.execute('DELETE FROM post_likes WHERE post_id = ?', (content_id,))
            conn.execute('DELETE FROM saved_posts WHERE post_id = ?', (content_id,))
            conn.execute('DELETE FROM reposts WHERE original_post_id = ?', (content_id,))
    elif content_type == 'reel':
        reel = conn.execute('SELECT * FROM reels WHERE id = ?', (content_id,)).fetchone()
        if reel and reel['user_id'] == user_id:
            conn.execute('DELETE FROM reels WHERE id = ?', (content_id,))
            conn.execute('DELETE FROM reel_comments WHERE reel_id = ?', (content_id,))
            conn.execute('DELETE FROM reel_likes WHERE reel_id = ?', (content_id,))
            conn.execute('DELETE FROM saved_reels WHERE reel_id = ?', (content_id,))
            conn.execute('DELETE FROM reposts WHERE original_reel_id = ?', (content_id,))
    elif content_type == 'comment':
        comment = conn.execute('SELECT * FROM comments WHERE id = ?', (content_id,)).fetchone()
        if comment and comment['user_id'] == user_id:
            conn.execute('DELETE FROM comments WHERE id = ?', (content_id,))
            conn.execute('UPDATE posts SET comments = comments - 1 WHERE id = ?', (comment['post_id'],))
    elif content_type == 'reel_comment':
        comment = conn.execute('SELECT * FROM reel_comments WHERE id = ?', (content_id,)).fetchone()
        if comment and comment['user_id'] == user_id:
            conn.execute('DELETE FROM reel_comments WHERE id = ?', (content_id,))
            conn.execute('UPDATE reels SET comments = comments - 1 WHERE id = ?', (comment['reel_id'],))
    elif content_type == 'repost':
        repost = conn.execute('SELECT * FROM reposts WHERE id = ?', (content_id,)).fetchone()
        if repost and repost['user_id'] == user_id:
            conn.execute('DELETE FROM reposts WHERE id = ?', (content_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Content deleted successfully'})

# API endpoints for search
@app.route('/api/search')
def search():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    query = request.args.get('q', '')
    tab = request.args.get('tab', 'all')
    
    if not query:
        return jsonify({'success': True, 'results': []})
    
    conn = get_db()
    results = {}
    
    if tab in ['all', 'users']:
        users = conn.execute('''
            SELECT u.*, 
                   (SELECT COUNT(*) FROM followers f1 WHERE f1.follower_id = ? AND f1.followed_id = u.id AND f1.status = 'accepted') as is_following,
                   (SELECT COUNT(*) FROM followers f2 WHERE f2.follower_id = u.id AND f2.followed_id = ? AND f2.status = 'accepted') as is_friend,
                   (SELECT COUNT(*) FROM followers f3 WHERE f3.follower_id = ? AND f3.followed_id = u.id AND f3.status = 'blocked') as is_blocked
            FROM users u
            WHERE (u.real_name LIKE ? OR u.username LIKE ?)
            AND u.id != ?
            ORDER BY 
                CASE 
                    WHEN u.real_name LIKE ? THEN 1
                    WHEN u.username LIKE ? THEN 2
                    ELSE 3
                END
            LIMIT 20
        ''', (session['user_id'], session['user_id'], session['user_id'], f'{query}%', f'{query}%', session['user_id'], f'{query}%', f'{query}%')).fetchall()
        
        results['users'] = [dict(user) for user in users]
    
    if tab in ['all', 'groups']:
        groups = conn.execute('''
            SELECT g.*, 
                   (SELECT COUNT(*) FROM group_members gm WHERE gm.group_id = g.id) as members_count,
                   (SELECT COUNT(*) FROM group_members gm WHERE gm.group_id = g.id AND gm.user_id = ?) as is_member
            FROM groups g
            WHERE g.name LIKE ?
            ORDER BY g.name
            LIMIT 20
        ''', (session['user_id'], f'{query}%')).fetchall()
        
        results['groups'] = [dict(group) for group in groups]
    
    if tab in ['all', 'posts']:
        posts = conn.execute('''
            SELECT p.*, u.username, u.real_name, u.profile_pic
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.description LIKE ?
            AND (p.visibility = 'public' OR 
                 (p.visibility = 'friends' AND 
                  (EXISTS (SELECT 1 FROM followers f1 WHERE f1.follower_id = ? AND f1.followed_id = p.user_id AND f1.status = 'accepted') OR
                   EXISTS (SELECT 1 FROM followers f2 WHERE f2.follower_id = p.user_id AND f2.followed_id = ? AND f2.status = 'accepted')
                  )
                 )
                )
            ORDER BY p.created_at DESC
            LIMIT 20
        ''', (f'%{query}%', session['user_id'], session['user_id'])).fetchall()
        
        results['posts'] = [dict(post) for post in posts]
    
    if tab in ['all', 'reels']:
        reels = conn.execute('''
            SELECT r.*, u.username, u.real_name, u.profile_pic
            FROM reels r
            JOIN users u ON r.user_id = u.id
            WHERE r.description LIKE ?
            AND (r.visibility = 'public' OR 
                 (r.visibility = 'friends' AND 
                  (EXISTS (SELECT 1 FROM followers f1 WHERE f1.follower_id = ? AND f1.followed_id = r.user_id AND f1.status = 'accepted') OR
                   EXISTS (SELECT 1 FROM followers f2 WHERE f2.follower_id = r.user_id AND f2.followed_id = ? AND f2.status = 'accepted')
                  )
                 )
                )
            ORDER BY r.created_at DESC
            LIMIT 20
        ''', (f'%{query}%', session['user_id'], session['user_id'])).fetchall()
        
        results['reels'] = [dict(reel) for reel in reels]
    
    conn.close()
    
    return jsonify({'success': True, 'results': results})

# API endpoints for notifications
@app.route('/api/notifications')
def get_notifications():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    notifications = get_user_notifications(user_id)
    unread_count = get_unread_notifications_count(user_id)
    
    # Mark all as read
    mark_notifications_as_read(user_id)
    
    return jsonify({
        'success': True,
        'notifications': [dict(notification) for notification in notifications],
        'unread_count': unread_count
    })

@app.route('/api/clear_notifications', methods=['POST'])
def clear_notifications():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    conn = get_db()
    conn.execute('DELETE FROM notifications WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Notifications cleared'})

# API endpoints for settings
@app.route('/api/update_settings', methods=['POST'])
def update_settings():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    language = request.json.get('language', 'en')
    theme = request.json.get('theme', 'light')
    profile_locking = request.json.get('profile_locking', 0)
    post_visibility = request.json.get('post_visibility', 'public')
    comment_restriction = request.json.get('comment_restriction', 'everyone')
    notification_preferences = request.json.get('notification_preferences', {})
    
    # In a real app, these would be stored in the database
    # For now, we'll just return success
    return jsonify({'success': True, 'message': 'Settings updated successfully'})

@app.route('/api/change_password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    current_password = request.json.get('current_password')
    new_password = request.json.get('new_password')
    
    # Validate password
    if len(new_password) < 6 or not re.search(r'\d', new_password) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters long and contain numbers, letters, and special characters.'})
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if user and user['password'] == hash_password(current_password):
        hashed_password = hash_password(new_password)
        conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
    else:
        conn.close()
        return jsonify({'success': False, 'message': 'Current password is incorrect'})

@app.route('/api/get_blocked_users')
def get_blocked_users():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    conn = get_db()
    blocked_users = conn.execute('''
        SELECT u.*
        FROM users u
        JOIN followers f ON u.id = f.followed_id
        WHERE f.follower_id = ? AND f.status = 'blocked'
        ORDER BY u.real_name
    ''', (user_id,)).fetchall()
    
    result = [dict(user) for user in blocked_users]
    conn.close()
    
    return jsonify({'success': True, 'blocked_users': result})

@app.route('/api/unblock_user/<int:user_id>', methods=['POST'])
def unblock_user(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    current_user_id = session['user_id']
    
    conn = get_db()
    conn.execute('DELETE FROM followers WHERE follower_id = ? AND followed_id = ?', (current_user_id, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'User unblocked successfully'})

# API endpoints for admin dashboard
@app.route('/api/admin/users')
def admin_get_users():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user = get_user_by_id(session['user_id'])
    if not user or user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    users = get_all_users()
    return jsonify({'success': True, 'users': [dict(user) for user in users]})

@app.route('/api/admin/groups')
def admin_get_groups():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user = get_user_by_id(session['user_id'])
    if not user or user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    groups = get_all_groups()
    return jsonify({'success': True, 'groups': [dict(group) for group in groups]})

@app.route('/api/admin/posts')
def admin_get_posts():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user = get_user_by_id(session['user_id'])
    if not user or user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    posts = get_all_posts()
    return jsonify({'success': True, 'posts': [dict(post) for post in posts]})

@app.route('/api/admin/reels')
def admin_get_reels():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user = get_user_by_id(session['user_id'])
    if not user or user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    reels = get_all_reels()
    return jsonify({'success': True, 'reels': [dict(reel) for reel in reels]})

@app.route('/api/admin/stories')
def admin_get_stories():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user = get_user_by_id(session['user_id'])
    if not user or user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    stories = get_all_stories()
    return jsonify({'success': True, 'stories': [dict(story) for story in stories]})

@app.route('/api/admin/comments')
def admin_get_comments():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user = get_user_by_id(session['user_id'])
    if not user or user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    comments = get_all_comments()
    return jsonify({'success': True, 'comments': [dict(comment) for comment in comments]})

@app.route('/api/admin/reel_comments')
def admin_get_reel_comments():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user = get_user_by_id(session['user_id'])
    if not user or user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    comments = get_all_reel_comments()
    return jsonify({'success': True, 'comments': [dict(comment) for comment in comments]})

@app.route('/api/admin/delete_user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    admin_user = get_user_by_id(session['user_id'])
    if not admin_user or admin_user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    conn = get_db()
    
    # Delete all content associated with the user
    conn.execute('DELETE FROM posts WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM reels WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM stories WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM comments WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM reel_comments WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM messages WHERE sender_id = ? OR receiver_id = ?', (user_id, user_id))
    conn.execute('DELETE FROM group_messages WHERE sender_id = ?', (user_id,))
    conn.execute('DELETE FROM followers WHERE follower_id = ? OR followed_id = ?', (user_id, user_id))
    conn.execute('DELETE FROM friend_requests WHERE sender_id = ? OR receiver_id = ?', (user_id, user_id))
    conn.execute('DELETE FROM saved_posts WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM saved_reels WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM post_likes WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM reel_likes WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM reposts WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM group_members WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM notifications WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM support_tickets WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM support_messages WHERE sender_id = ?', (user_id,))
    
    # Finally delete the user
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'User deleted successfully'})

@app.route('/api/admin/delete_post/<int:post_id>', methods=['POST'])
def admin_delete_post(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    admin_user = get_user_by_id(session['user_id'])
    if not admin_user or admin_user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    conn = get_db()
    conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.execute('DELETE FROM comments WHERE post_id = ?', (post_id,))
    conn.execute('DELETE FROM post_likes WHERE post_id = ?', (post_id,))
    conn.execute('DELETE FROM saved_posts WHERE post_id = ?', (post_id,))
    conn.execute('DELETE FROM reposts WHERE original_post_id = ?', (post_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Post deleted successfully'})

@app.route('/api/admin/delete_reel/<int:reel_id>', methods=['POST'])
def admin_delete_reel(reel_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    admin_user = get_user_by_id(session['user_id'])
    if not admin_user or admin_user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    conn = get_db()
    conn.execute('DELETE FROM reels WHERE id = ?', (reel_id,))
    conn.execute('DELETE FROM reel_comments WHERE reel_id = ?', (reel_id,))
    conn.execute('DELETE FROM reel_likes WHERE reel_id = ?', (reel_id,))
    conn.execute('DELETE FROM saved_reels WHERE reel_id = ?', (reel_id,))
    conn.execute('DELETE FROM reposts WHERE original_reel_id = ?', (reel_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Reel deleted successfully'})

@app.route('/api/admin/delete_story/<int:story_id>', methods=['POST'])
def admin_delete_story(story_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    admin_user = get_user_by_id(session['user_id'])
    if not admin_user or admin_user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    conn = get_db()
    conn.execute('DELETE FROM stories WHERE id = ?', (story_id,))
    conn.execute('DELETE FROM story_views WHERE story_id = ?', (story_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Story deleted successfully'})

@app.route('/api/admin/delete_comment/<int:comment_id>', methods=['POST'])
def admin_delete_comment(comment_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    admin_user = get_user_by_id(session['user_id'])
    if not admin_user or admin_user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    conn = get_db()
    comment = conn.execute('SELECT * FROM comments WHERE id = ?', (comment_id,)).fetchone()
    if comment:
        conn.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
        conn.execute('UPDATE posts SET comments = comments - 1 WHERE id = ?', (comment['post_id'],))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Comment deleted successfully'})

@app.route('/api/admin/delete_reel_comment/<int:comment_id>', methods=['POST'])
def admin_delete_reel_comment(comment_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    admin_user = get_user_by_id(session['user_id'])
    if not admin_user or admin_user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    conn = get_db()
    comment = conn.execute('SELECT * FROM reel_comments WHERE id = ?', (comment_id,)).fetchone()
    if comment:
        conn.execute('DELETE FROM reel_comments WHERE id = ?', (comment_id,))
        conn.execute('UPDATE reels SET comments = comments - 1 WHERE id = ?', (comment['reel_id'],))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Comment deleted successfully'})

@app.route('/api/admin/ban_user/<int:user_id>', methods=['POST'])
def admin_ban_user(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    admin_user = get_user_by_id(session['user_id'])
    if not admin_user or admin_user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    reason = request.json.get('reason', 'Violation of community guidelines')
    duration = request.json.get('duration', 'permanent')  # '24h', '7d', '30d', 'permanent'
    
    conn = get_db()
    conn.execute('UPDATE users SET is_banned = 1, account_status = ? WHERE id = ?', (f'banned_{duration}', user_id))
    
    # Create notification for banned user
    conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                    VALUES (?, ?, ?, ?)''',
                 (user_id, 'system', f'Your account has been banned: {reason}', datetime.now()))
    
    # Log admin action
    conn.execute('''INSERT INTO admin_actions (admin_id, action_type, target_type, target_id, reason)
                    VALUES (?, ?, ?, ?, ?)''',
                 (admin_user['id'], 'ban', 'user', user_id, reason))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'User banned successfully'})

@app.route('/api/admin/unban_user/<int:user_id>', methods=['POST'])
def admin_unban_user(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    admin_user = get_user_by_id(session['user_id'])
    if not admin_user or admin_user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    conn = get_db()
    conn.execute('UPDATE users SET is_banned = 0, account_status = "active" WHERE id = ?', (user_id,))
    
    # Create notification for unbanned user
    conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                    VALUES (?, ?, ?, ?)''',
                 (user_id, 'system', 'Your account has been unbanned', datetime.now()))
    
    # Log admin action
    conn.execute('''INSERT INTO admin_actions (admin_id, action_type, target_type, target_id, reason)
                    VALUES (?, ?, ?, ?, ?)''',
                 (admin_user['id'], 'unban', 'user', user_id, 'Manual unban'))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'User unbanned successfully'})

@app.route('/api/admin/issue_warning/<int:user_id>', methods=['POST'])
def admin_issue_warning(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    admin_user = get_user_by_id(session['user_id'])
    if not admin_user or admin_user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    reason = request.json.get('reason', 'Potential violation of community guidelines')
    
    conn = get_db()
    # Create notification for user
    conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                    VALUES (?, ?, ?, ?)''',
                 (user_id, 'system', f'Warning: {reason}', datetime.now()))
    
    # Log admin action
    conn.execute('''INSERT INTO admin_actions (admin_id, action_type, target_type, target_id, reason)
                    VALUES (?, ?, ?, ?, ?)''',
                 (admin_user['id'], 'warning', 'user', user_id, reason))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Warning issued successfully'})

@app.route('/api/admin/send_system_message', methods=['POST'])
def admin_send_system_message():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    admin_user = get_user_by_id(session['user_id'])
    if not admin_user or admin_user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    message = request.json.get('message', '')
    send_to_all = request.json.get('send_to_all', False)
    target_user_id = request.json.get('target_user_id')
    
    conn = get_db()
    
    if send_to_all:
        # Send to all users
        users = conn.execute('SELECT id FROM users').fetchall()
        for user in users:
            conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                            VALUES (?, ?, ?, ?)''',
                         (user['id'], 'system', message, datetime.now()))
    elif target_user_id:
        # Send to specific user
        conn.execute('''INSERT INTO notifications (user_id, type, content, created_at)
                        VALUES (?, ?, ?, ?)''',
                     (target_user_id, 'system', message, datetime.now()))
    
    # Log admin action
    conn.execute('''INSERT INTO admin_actions (admin_id, action_type, target_type, target_id, reason)
                    VALUES (?, ?, ?, ?, ?)''',
                 (admin_user['id'], 'system_message', 'all_users' if send_to_all else 'user', target_user_id if target_user_id else None, message))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'System message sent successfully'})

@app.route('/api/admin/create_admin_story', methods=['POST'])
def admin_create_admin_story():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    admin_user = get_user_by_id(session['user_id'])
    if not admin_user or admin_user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    content_type = request.json.get('content_type')
    content_url = request.json.get('content_url')
    duration = request.json.get('duration', 30)
    
    # Stories expire after duration
    expires_at = datetime.now() + timedelta(seconds=duration)
    
    conn = get_db()
    # Create story with admin user (SociaFam)
    conn.execute('''INSERT INTO stories (user_id, content_type, content_url, duration, expires_at)
                    VALUES (?, ?, ?, ?, ?)''',
                 (admin_user['id'], content_type, content_url, duration, expires_at))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Admin story created successfully'})

@app.route('/api/admin/support_tickets')
def admin_get_support_tickets():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    admin_user = get_user_by_id(session['user_id'])
    if not admin_user or admin_user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    conn = get_db()
    tickets = conn.execute('''
        SELECT st.*, u.username, u.real_name, u.profile_pic
        FROM support_tickets st
        JOIN users u ON st.user_id = u.id
        ORDER BY st.created_at DESC
    ''').fetchall()
    
    result = []
    for ticket in tickets:
        messages = conn.execute('''
            SELECT sm.*, u.username, u.real_name, u.profile_pic
            FROM support_messages sm
            JOIN users u ON sm.sender_id = u.id
            WHERE sm.ticket_id = ?
            ORDER BY sm.created_at ASC
        ''', (ticket['id'],)).fetchall()
        
        result.append({
            'ticket': dict(ticket),
            'messages': [dict(message) for message in messages]
        })
    
    conn.close()
    return jsonify({'success': True, 'tickets': result})

@app.route('/api/admin/reply_support_ticket/<int:ticket_id>', methods=['POST'])
def admin_reply_support_ticket(ticket_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    admin_user = get_user_by_id(session['user_id'])
    if not admin_user or admin_user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    message = request.json.get('message', '')
    
    conn = get_db()
    # Check if ticket exists
    ticket = conn.execute('SELECT * FROM support_tickets WHERE id = ?', (ticket_id,)).fetchone()
    if not ticket:
        conn.close()
        return jsonify({'success': False, 'message': 'Ticket not found'})
    
    # Add reply
    conn.execute('''INSERT INTO support_messages (ticket_id, sender_id, content)
                    VALUES (?, ?, ?)''', (ticket_id, admin_user['id'], message))
    
    # Update ticket status if it was open
    if ticket['status'] == 'open':
        conn.execute('UPDATE support_tickets SET status = ? WHERE id = ?', ('in_progress', ticket_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Reply sent successfully'})

@app.route('/api/admin/close_support_ticket/<int:ticket_id>', methods=['POST'])
def admin_close_support_ticket(ticket_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    admin_user = get_user_by_id(session['user_id'])
    if not admin_user or admin_user['is_admin'] == 0:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    conn = get_db()
    conn.execute('UPDATE support_tickets SET status = ? WHERE id = ?', ('closed', ticket_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Ticket closed successfully'})

@app.route('/api/support_ticket', methods=['POST'])
def create_support_ticket():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    subject = request.json.get('subject', '')
    message = request.json.get('message', '')
    
    conn = get_db()
    conn.execute('''INSERT INTO support_tickets (user_id, subject, message)
                    VALUES (?, ?, ?)''', (user_id, subject, message))
    
    ticket_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    
    # Add initial message
    conn.execute('''INSERT INTO support_messages (ticket_id, sender_id, content)
                    VALUES (?, ?, ?)''', (ticket_id, user_id, message))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Support ticket created successfully'})

@app.route('/api/support_messages/<int:ticket_id>')
def get_support_messages(ticket_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    conn = get_db()
    # Check if user owns this ticket
    ticket = conn.execute('SELECT * FROM support_tickets WHERE id = ? AND user_id = ?', (ticket_id, user_id)).fetchone()
    if not ticket:
        conn.close()
        return jsonify({'success': False, 'message': 'Access denied'})
    
    messages = conn.execute('''
        SELECT sm.*, u.username, u.real_name, u.profile_pic
        FROM support_messages sm
        JOIN users u ON sm.sender_id = u.id
        WHERE sm.ticket_id = ?
        ORDER BY sm.created_at ASC
    ''', (ticket_id,)).fetchall()
    
    conn.close()
    return jsonify({'success': True, 'messages': [dict(message) for message in messages]})

@app.route('/api/send_support_message/<int:ticket_id>', methods=['POST'])
def send_support_message(ticket_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    message = request.json.get('message', '')
    
    conn = get_db()
    # Check if user owns this ticket
    ticket = conn.execute('SELECT * FROM support_tickets WHERE id = ? AND user_id = ?', (ticket_id, user_id)).fetchone()
    if not ticket:
        conn.close()
        return jsonify({'success': False, 'message': 'Access denied'})
    
    conn.execute('''INSERT INTO support_messages (ticket_id, sender_id, content)
                    VALUES (?, ?, ?)''', (ticket_id, user_id, message))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Message sent successfully'})

# Initialize database
init_db()

if __name__ == '__main__':
    app.run(debug=True)
import string
import datetime
from sqlalchemy import and_, or_, func

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config.from_pyfile('config.py')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sociafam.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = app.config['SECRET_KEY']

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

ALLOWED_EXTENSIONS = {'jpg', 'png', 'gif', 'mp4', 'mp3'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_key():
    letters = random.choices(string.ascii_letters, k=2)
    digits = random.choices(string.digits, k=2)
    all_chars = letters + digits
    random.shuffle(all_chars)
    return ''.join(all_chars)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    real_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    profile_pic_url = db.Column(db.String(200))
    unique_key = db.Column(db.String(4), unique=True, nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    gender = db.Column(db.String(20))
    pronouns = db.Column(db.String(20))
    dob = db.Column(db.Date)
    work = db.Column(db.Text)
    education = db.Column(db.Text)
    location = db.Column(db.Text)
    social_links = db.Column(db.Text)
    website = db.Column(db.String(200))
    relationship = db.Column(db.String(50))
    spouse = db.Column(db.String(50))
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    media_url = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    visibility = db.Column(db.String(20), default='public')

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Repost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Save(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class PrivateMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text)
    media_url = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    profile_pic_url = db.Column(db.String(200))
    description = db.Column(db.Text)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    allow_nonadmin_messages = db.Column(db.Boolean, default=True)
    allow_nonadmin_add_members = db.Column(db.Boolean, default=True)
    approve_new_members = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class GroupMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text)
    media_url = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content_id = db.Column(db.Integer)
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reported_type = db.Column(db.String(20), nullable=False)
    reported_id = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class HiddenPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class BlockedUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blocker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blocked_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

def initialize_db():
    with app.app_context():
        db.create_all()
        admin_username = app.config.get('ADMIN_USERNAME', 'Henry')
        admin_pass = app.config.get('ADMIN_PASS', 'Dec@2003')
        if not User.query.filter_by(username=admin_username).first():
            hashed = bcrypt.generate_password_hash(admin_pass).decode('utf-8')
            key = generate_unique_key()
            while User.query.filter_by(unique_key=key).first():
                key = generate_unique_key()
            admin = User(username=admin_username, password_hash=hashed, unique_key=key, is_admin=True, real_name='Admin')
            db.session.add(admin)
            db.session.commit()

initialize_db()

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing fields'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username taken'}), 400
    if username == app.config.get('ADMIN_USERNAME', 'Henry'):
        return jsonify({'error': 'Username reserved'}), 400
    if len(password) < 6 or not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password) or not any(not c.isalnum() for c in password):
        return jsonify({'error': 'Password must be at least 6 characters, include a number, a letter, and a special character'}), 400
    hashed = bcrypt.generate_password_hash(password).decode('utf-8')
    key = generate_unique_key()
    while User.query.filter_by(unique_key=key).first():
        key = generate_unique_key()
    user = User(username=username, password_hash=hashed, unique_key=key, real_name=username)
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    return jsonify({'message': 'Registered', 'unique_key': key})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    identifier = data.get('identifier')
    password = data.get('password')
    user = User.query.filter(or_(User.username == identifier, User.email == identifier)).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        return jsonify({'message': 'Logged in', 'is_admin': user.is_admin})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out'})

@app.route('/api/profile')
def profile():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    posts = Post.query.filter_by(user_id=user.id).all()
    friends = Follow.query.filter_by(follower_id=user.id, status='accepted').all()
    followers = Follow.query.filter_by(followed_id=user.id, status='accepted').count()
    following = Follow.query.filter_by(follower_id=user.id, status='accepted').count()
    saved = Save.query.filter_by(user_id=user.id).all()
    data = {
        'id': user.id,
        'username': user.username,
        'real_name': user.real_name,
        'bio': user.bio,
        'profile_pic': user.profile_pic_url,
        'posts_count': len(posts),
        'friends_count': len(friends),
        'followers_count': followers,
        'following_count': following,
        'posts': [p.id for p in posts if p.type == 'post'],
        'reels': [p.id for p in posts if p.type == 'reel'],
        'saved': [s.post_id for s in saved],
        'is_admin': user.is_admin,
        'user_info': {
            'dob': user.dob.isoformat() if user.dob else None,
            'gender': user.gender,
            'pronouns': user.pronouns,
            'work': user.work,
            'education': user.education,
            'location': user.location,
            'email': user.email,
            'phone': user.phone,
            'social_links': user.social_links,
            'website': user.website,
            'relationship': user.relationship,
            'spouse': user.spouse
        }
    }
    return jsonify(data)

@app.route('/api/profile/update', methods=['POST'])
def update_profile():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.form
    user.real_name = data.get('real_name', user.real_name)
    user.bio = data.get('bio', user.bio)
    if data.get('dob'):
        user.dob = datetime.datetime.strptime(data.get('dob'), '%Y-%m-%d')
    user.gender = data.get('gender', user.gender)
    user.pronouns = data.get('pronouns', user.pronouns)
    user.work = data.get('work', user.work)
    user.education = data.get('education', user.education)
    user.location = data.get('location', user.location)
    user.email = data.get('email', user.email)
    user.phone = data.get('phone', user.phone)
    user.social_links = data.get('social_links', user.social_links)
    user.website = data.get('website', user.website)
    user.relationship = data.get('relationship', user.relationship)
    user.spouse = data.get('spouse', user.spouse)
    if data.get('username') and data.get('username') != user.username:
        if not User.query.filter_by(username=data['username']).first():
            user.username = data['username']
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            user.profile_pic_url = '/static/uploads/' + filename
    db.session.commit()
    return jsonify({'message': 'Updated'})

@app.route('/api/home')
def home():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    friends = Follow.query.filter_by(follower_id=user.id, status='accepted').all()
    friend_ids = [f.followed_id for f in friends] + [user.id]
    stories = Post.query.filter(and_(Post.user_id.in_(friend_ids), Post.type == 'story')).order_by(Post.timestamp.desc()).all()
    data = {
        'stories': [{'id': s.id, 'user': s.user.username, 'media_url': s.media_url, 'description': s.description} for s in stories]
    }
    return jsonify(data)

@app.route('/api/posts')
def get_posts():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    page = int(request.args.get('page', 1))
    per_page = 10
    blocked_users = BlockedUser.query.filter_by(blocker_id=user.id).all()
    blocked_ids = [bu.blocked_id for bu in blocked_users]
    hidden_posts = HiddenPost.query.filter_by(user_id=user.id).all()
    hidden_post_ids = [hp.post_id for hp in hidden_posts]
    friends = Follow.query.filter_by(follower_id=user.id, status='accepted').all()
    friend_ids = [f.followed_id for f in friends]
    posts_query = Post.query.filter(
        and_(
            Post.type == 'post',
            Post.user_id.notin_(blocked_ids),
            Post.id.notin_(hidden_post_ids),
            or_(Post.visibility == 'public', and_(Post.visibility == 'friends', Post.user_id.in_(friend_ids)))
        )
    ).order_by(Post.timestamp.desc())
    posts = posts_query.paginate(page=page, per_page=per_page, error_out=False)
    data = {
        'posts': [{
            'id': p.id,
            'user': {'username': p.user.username, 'real_name': p.user.real_name, 'profile_pic': p.user.profile_pic_url},
            'description': p.description,
            'media_url': p.media_url,
            'timestamp': p.timestamp.isoformat(),
            'likes': Like.query.filter_by(post_id=p.id).count(),
            'comments': Comment.query.filter_by(post_id=p.id).count(),
            'is_liked': Like.query.filter_by(post_id=p.id, user_id=user.id).first() is not None,
            'is_saved': Save.query.filter_by(post_id=p.id, user_id=user.id).first() is not None,
            'is_own': p.user_id == user.id,
            'views': p.views
        } for p in posts.items],
        'has_next': posts.has_next
    }
    for post in posts.items:
        post.views += 1
    db.session.commit()
    return jsonify(data)

@app.route('/api/reels')
def get_reels():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    page = int(request.args.get('page', 1))
    per_page = 10
    blocked_users = BlockedUser.query.filter_by(blocker_id=user.id).all()
    blocked_ids = [bu.blocked_id for bu in blocked_users]
    hidden_posts = HiddenPost.query.filter_by(user_id=user.id).all()
    hidden_post_ids = [hp.post_id for hp in hidden_posts]
    friends = Follow.query.filter_by(follower_id=user.id, status='accepted').all()
    friend_ids = [f.followed_id for f in friends]
    reels_query = Post.query.filter(
        and_(
            Post.type == 'reel',
            Post.user_id.notin_(blocked_ids),
            Post.id.notin_(hidden_post_ids),
            or_(Post.visibility == 'public', and_(Post.visibility == 'friends', Post.user_id.in_(friend_ids)))
        )
    ).order_by(Post.timestamp.desc())
    reels = reels_query.paginate(page=page, per_page=per_page, error_out=False)
    data = {
        'reels': [{
            'id': r.id,
            'user': {'username': r.user.username, 'real_name': r.user.real_name, 'profile_pic': r.user.profile_pic_url},
            'description': r.description,
            'media_url': r.media_url,
            'likes': Like.query.filter_by(post_id=r.id).count(),
            'comments': Comment.query.filter_by(post_id=r.id).count(),
            'is_liked': Like.query.filter_by(post_id=r.id, user_id=user.id).first() is not None,
            'is_saved': Save.query.filter_by(post_id=r.id, user_id=user.id).first() is not None,
            'is_own': r.user_id == user.id,
            'views': r.views
        } for r in reels.items],
        'has_next': reels.has_next
    }
    for reel in reels.items:
        reel.views += 1
    db.session.commit()
    return jsonify(data)

@app.route('/api/create', methods=['POST'])
def create_content():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.form
    content_type = data.get('type')
    description = data.get('description')
    visibility = data.get('visibility', 'public')
    post = Post(user_id=user.id, type=content_type, description=description, visibility=visibility)
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            post.media_url = '/static/uploads/' + filename
    db.session.add(post)
    db.session.commit()
    return jsonify({'message': 'Created'})

@app.route('/api/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=user.id, post_id=post_id).first()
    if like:
        db.session.delete(like)
        db.session.commit()
        return jsonify({'message': 'Unliked'})
    else:
        like = Like(user_id=user.id, post_id=post_id)
        db.session.add(like)
        notif = Notification(user_id=post.user_id, type='like', from_user_id=user.id, content_id=post_id, message=f'{user.username} liked your {post.type}')
        db.session.add(notif)
        db.session.commit()
        return jsonify({'message': 'Liked'})

@app.route('/api/comment/<int:post_id>', methods=['POST'])
def comment_post(post_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    post = Post.query.get_or_404(post_id)
    data = request.json
    text = data.get('text')
    if not text:
        return jsonify({'error': 'Missing text'}), 400
    comment = Comment(user_id=user.id, post_id=post_id, text=text)
    db.session.add(comment)
    notif = Notification(user_id=post.user_id, type='comment', from_user_id=user.id, content_id=post_id, message=f'{user.username} commented on your {post.type}')
    db.session.add(notif)
    db.session.commit()
    return jsonify({'message': 'Commented'})

@app.route('/api/repost/<int:post_id>', methods=['POST'])
def repost(post_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    post = Post.query.get_or_404(post_id)
    repost = Repost(user_id=user.id, original_post_id=post_id)
    db.session.add(repost)
    notif = Notification(user_id=post.user_id, type='repost', from_user_id=user.id, content_id=post_id, message=f'{user.username} reposted your {post.type}')
    db.session.add(notif)
    db.session.commit()
    return jsonify({'message': 'Reposted'})

@app.route('/api/save/<int:post_id>', methods=['POST'])
def save_post(post_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    post = Post.query.get_or_404(post_id)
    save = Save.query.filter_by(user_id=user.id, post_id=post_id).first()
    if save:
        db.session.delete(save)
        db.session.commit()
        return jsonify({'message': 'Unsaved'})
    else:
        save = Save(user_id=user.id, post_id=post_id)
        db.session.add(save)
        db.session.commit()
        return jsonify({'message': 'Saved'})

@app.route('/api/follow/<int:user_id>', methods=['POST'])
def follow_user(user_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if user.id == user_id:
        return jsonify({'error': 'Cannot follow yourself'}), 400
    existing = Follow.query.filter_by(follower_id=user.id, followed_id=user_id).first()
    if existing:
        return jsonify({'error': 'Already following or requested'}), 400
    follow = Follow(follower_id=user.id, followed_id=user_id, status='pending')
    db.session.add(follow)
    notif = Notification(user_id=user_id, type='follow_request', from_user_id=user.id, message=f'{user.username} requested to follow you')
    db.session.add(notif)
    db.session.commit()
    return jsonify({'message': 'Follow request sent'})

@app.route('/api/unfollow/<int:user_id>', methods=['POST'])
def unfollow_user(user_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    follow = Follow.query.filter_by(follower_id=user.id, followed_id=user_id).first()
    if not follow:
        return jsonify({'error': 'Not following'}), 400
    db.session.delete(follow)
    db.session.commit()
    return jsonify({'message': 'Unfollowed'})

@app.route('/api/accept_request/<int:user_id>', methods=['POST'])
def accept_request(user_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    follow = Follow.query.filter_by(follower_id=user_id, followed_id=user.id, status='pending').first()
    if not follow:
        return jsonify({'error': 'No such request'}), 400
    follow.status = 'accepted'
    db.session.commit()
    notif = Notification(user_id=user_id, type='follow_accepted', from_user_id=user.id, message=f'{user.username} accepted your follow request')
    db.session.add(notif)
    db.session.commit()
    return jsonify({'message': 'Request accepted'})

@app.route('/api/decline_request/<int:user_id>', methods=['POST'])
def decline_request(user_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    follow = Follow.query.filter_by(follower_id=user_id, followed_id=user.id, status='pending').first()
    if not follow:
        return jsonify({'error': 'No such request'}), 400
    db.session.delete(follow)
    db.session.commit()
    return jsonify({'message': 'Request declined'})

@app.route('/api/friends/<tab>')
def friends_tab(tab):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = {}
    if tab == 'followers':
        followers = Follow.query.filter_by(followed_id=user.id, status='accepted').all()
        data['followers'] = [{'id': f.follower_id, 'real_name': f.follower.real_name, 'profile_pic': f.follower.profile_pic_url} for f in followers]
    elif tab == 'following':
        following = Follow.query.filter_by(follower_id=user.id, status='accepted').all()
        data['following'] = [{'id': f.followed_id, 'real_name': f.followed.real_name, 'profile_pic': f.followed.profile_pic_url} for f in following]
    elif tab == 'friends':
        friends1 = Follow.query.filter_by(follower_id=user.id, status='accepted').all()
        friends2 = Follow.query.filter_by(followed_id=user.id, status='accepted').all()
        friend_ids = set(f.followed_id for f in friends1).intersection(f.follower_id for f in friends2)
        data['friends'] = [{'id': f.id, 'real_name': f.real_name, 'profile_pic': f.profile_pic_url} for f in User.query.filter(User.id.in_(friend_ids)).all()]
    elif tab == 'requests':
        requests = Follow.query.filter_by(followed_id=user.id, status='pending').all()
        data['requests'] = [{'id': r.follower_id, 'real_name': r.follower.real_name, 'profile_pic': r.follower.profile_pic_url} for r in requests]
    elif tab == 'suggested':
        friends = Follow.query.filter_by(follower_id=user.id, status='accepted').all()
        friend_ids = [f.followed_id for f in friends]
        friend_ids.append(user.id)
        suggestions = User.query.filter(~User.id.in_(friend_ids)).limit(10).all()
        data['suggested'] = [{'id': s.id, 'real_name': s.real_name, 'profile_pic': s.profile_pic_url, 'mutual': Follow.query.filter_by(follower_id=s.id, followed_id=user.id, status='accepted').count()} for s in suggestions]
    return jsonify(data)

@app.route('/api/inbox/<tab>')
def inbox_tab(tab):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = {}
    if tab == 'chats':
        messages = PrivateMessage.query.filter(or_(PrivateMessage.sender_id == user.id, PrivateMessage.receiver_id == user.id)).order_by(PrivateMessage.timestamp.desc()).all()
        chats = {}
        for msg in messages:
            other_id = msg.sender_id if msg.sender_id != user.id else msg.receiver_id
            if other_id not in chats:
                other_user = User.query.get(other_id)
                chats[other_id] = {
                    'other_id': other_id,
                    'real_name': other_user.real_name,
                    'profile_pic': other_user.profile_pic_url,
                    'last_msg_snippet': msg.text or 'Media',
                    'unread': PrivateMessage.query.filter_by(receiver_id=user.id, sender_id=other_id, is_read=False).count()
                }
        data['chats'] = list(chats.values())
    elif tab == 'groups':
        groups = GroupMember.query.filter_by(user_id=user.id).all()
        data['groups'] = [{
            'group_id': gm.group.id,
            'name': gm.group.name,
            'profile_pic': gm.group.profile_pic_url,
            'last_msg_snippet': GroupMessage.query.filter_by(group_id=gm.group.id).order_by(GroupMessage.timestamp.desc()).first().text or 'Media' if GroupMessage.query.filter_by(group_id=gm.group.id).first() else ''
        } for gm in groups]
    return jsonify(data)

@app.route('/api/messages/private/<int:other_id>')
def get_private_messages(other_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    messages = PrivateMessage.query.filter(
        or_(
            and_(PrivateMessage.sender_id == user.id, PrivateMessage.receiver_id == other_id),
            and_(PrivateMessage.sender_id == other_id, PrivateMessage.receiver_id == user.id)
        )
    ).order_by(PrivateMessage.timestamp.asc()).all()
    for msg in messages:
        if msg.receiver_id == user.id and not msg.is_read:
            msg.is_read = True
    db.session.commit()
    data = [{
        'sender_id': msg.sender_id,
        'sender_name': msg.sender.real_name,
        'sender_profile_pic': msg.sender.profile_pic_url,
        'receiver_id': msg.receiver_id,
        'receiver_name': msg.receiver.real_name,
        'receiver_profile_pic': msg.receiver.profile_pic_url,
        'text': msg.text,
        'media_url': msg.media_url,
        'timestamp': msg.timestamp.isoformat()
    } for msg in messages]
    return jsonify({'messages': data})

@app.route('/api/messages/private/<int:other_id>', methods=['POST'])
def send_private_message(other_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    text = request.form.get('text')
    file = request.files.get('file')
    message = PrivateMessage(sender_id=user.id, receiver_id=other_id)
    if text:
        message.text = text
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        message.media_url = '/static/uploads/' + filename
    db.session.add(message)
    db.session.commit()
    return jsonify({'message': 'Sent'})

@app.route('/api/group/<int:group_id>')
def get_group(group_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    group = Group.query.get_or_404(group_id)
    if not GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first():
        return jsonify({'error': 'Not a member'}), 403
    return jsonify({
        'id': group.id,
        'name': group.name,
        'profile_pic': group.profile_pic_url,
        'description': group.description
    })

@app.route('/api/messages/group/<int:group_id>')
def get_group_messages(group_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first():
        return jsonify({'error': 'Not a member'}), 403
    messages = GroupMessage.query.filter_by(group_id=group_id).order_by(GroupMessage.timestamp.asc()).all()
    data = [{
        'sender_id': msg.sender_id,
        'sender_name': msg.sender.real_name,
        'text': msg.text,
        'media_url': msg.media_url,
        'timestamp': msg.timestamp.isoformat()
    } for msg in messages]
    return jsonify({'messages': data})

@app.route('/api/messages/group/<int:group_id>', methods=['POST'])
def send_group_message(group_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    group = Group.query.get_or_404(group_id)
    member = GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first()
    if not member:
        return jsonify({'error': 'Not a member'}), 403
    if not group.allow_nonadmin_messages and not member.is_admin:
        return jsonify({'error': 'Non-admins cannot send messages'}), 403
    text = request.form.get('text')
    file = request.files.get('file')
    message = GroupMessage(group_id=group_id, sender_id=user.id)
    if text:
        message.text = text
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        message.media_url = '/static/uploads/' + filename
    db.session.add(message)
    db.session.commit()
    return jsonify({'message': 'Sent'})

@app.route('/api/create_group', methods=['POST'])
def create_group():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.form
    name = data.get('name')
    description = data.get('description')
    allow_nonadmin_messages = data.get('allow_nonadmin_messages') == 'on'
    allow_nonadmin_add_members = data.get('allow_nonadmin_add_members') == 'on'
    approve_new_members = data.get('approve_new_members') == 'on'
    group = Group(
        name=name,
        description=description,
        creator_id=user.id,
        allow_nonadmin_messages=allow_nonadmin_messages,
        allow_nonadmin_add_members=allow_nonadmin_add_members,
        approve_new_members=approve_new_members
    )
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            group.profile_pic_url = '/static/uploads/' + filename
    db.session.add(group)
    db.session.flush()
    member = GroupMember(group_id=group.id, user_id=user.id, is_admin=True)
    db.session.add(member)
    db.session.commit()
    return jsonify({'message': 'Group created'})

@app.route('/api/search', methods=['GET'])
def search():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    query = request.args.get('query', '')
    tab = request.args.get('tab', 'all')
    results = {}
    if tab in ['all', 'users']:
        users = User.query.filter(or_(User.real_name.ilike(f'%{query}%'), User.username.ilike(f'%{query}%'))).all()
        results['users'] = [{'id': u.id, 'real_name': u.real_name, 'username': u.username, 'profile_pic': u.profile_pic_url} for u in users]
    if tab in ['all', 'groups']:
        groups = Group.query.filter(Group.name.ilike(f'%{query}%')).all()
        results['groups'] = [{'id': g.id, 'name': g.name, 'profile_pic': g.profile_pic_url} for g in groups]
    if tab in ['all', 'posts']:
        posts = Post.query.filter_by(type='post').filter(Post.description.ilike(f'%{query}%')).all()
        results['posts'] = [{'id': p.id, 'description': p.description, 'user': p.user.username} for p in posts]
    if tab in ['all', 'reels']:
        reels = Post.query.filter_by(type='reel').filter(Post.description.ilike(f'%{query}%')).all()
        results['reels'] = [{'id': r.id, 'description': r.description, 'user': r.user.username} for r in reels]
    return jsonify(results)

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    notifs = Notification.query.filter_by(user_id=user.id).order_by(Notification.timestamp.desc()).all()
    data = [{'id': n.id, 'type': n.type, 'message': n.message, 'from_user': User.query.get(n.from_user_id).username if n.from_user_id else None, 'content_id': n.content_id, 'is_read': n.is_read, 'timestamp': n.timestamp.isoformat()} for n in notifs]
    return jsonify({'notifications': data})

@app.route('/api/notification/mark_read/<int:notif_id>', methods=['POST'])
def mark_read(notif_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != user.id:
        return jsonify({'error': 'Not yours'}), 403
    notif.is_read = True
    db.session.commit()
    return jsonify({'message': 'Marked read'})

@app.route('/api/report/<int:reported_id>', methods=['POST'])
def report_content(reported_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    reported_type = data.get('type')
    description = data.get('description')
    if not reported_type or not description:
        return jsonify({'error': 'Missing type or description'}), 400
    report = Report(reporter_id=user.id, reported_type=reported_type, reported_id=reported_id, description=description)
    db.session.add(report)
    db.session.commit()
    return jsonify({'message': 'Reported'})

@app.route('/api/hide/<int:post_id>', methods=['POST'])
def hide_post(post_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    post = Post.query.get_or_404(post_id)
    if post.user_id == user.id:
        return jsonify({'error': 'Cannot hide own post'}), 400
    existing = HiddenPost.query.filter_by(user_id=user.id, post_id=post_id).first()
    if existing:
        return jsonify({'error': 'Post already hidden'}), 400
    hidden_post = HiddenPost(user_id=user.id, post_id=post_id)
    db.session.add(hidden_post)
    db.session.commit()
    return jsonify({'message': 'Post hidden'})

@app.route('/api/block/user/<int:user_id>', methods=['POST'])
def block_user(user_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if user.id == user_id:
        return jsonify({'error': 'Cannot block yourself'}), 400
    existing = BlockedUser.query.filter_by(blocker_id=user.id, blocked_id=user_id).first()
    if existing:
        return jsonify({'error': 'User already blocked'}), 400
    blocked_user = BlockedUser(blocker_id=user.id, blocked_id=user_id)
    Follow.query.filter(or_(
        and_(Follow.follower_id == user.id, Follow.followed_id == user_id),
        and_(Follow.follower_id == user_id, Follow.followed_id == user.id)
    )).delete()
    db.session.add(blocked_user)
    db.session.commit()
    return jsonify({'message': 'User blocked'})

@app.route('/api/settings', methods=['POST'])
def update_settings():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    return jsonify({'message': 'Settings updated'})

@app.route('/api/admin/users', methods=['GET'])
def admin_users():
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    users = User.query.all()
    data = [{'id': u.id, 'username': u.username, 'real_name': u.real_name, 'created_at': u.created_at.isoformat(), 'is_banned': u.is_banned} for u in users]
    return jsonify({'users': data})

@app.route('/api/admin/delete/user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    target = User.query.get_or_404(user_id)
    if target.is_admin:
        return jsonify({'error': 'Cannot delete admin'}), 400
    Post.query.filter_by(user_id=user_id).delete()
    Follow.query.filter(or_(Follow.follower_id == user_id, Follow.followed_id == user_id)).delete()
    PrivateMessage.query.filter(or_(PrivateMessage.sender_id == user_id, PrivateMessage.receiver_id == user_id)).delete()
    Group.query.filter_by(creator_id=user_id).delete()
    GroupMember.query.filter_by(user_id=user_id).delete()
    GroupMessage.query.filter_by(sender_id=user_id).delete()
    Notification.query.filter_by(user_id=user_id).delete()
    Report.query.filter_by(reporter_id=user_id).delete()
    HiddenPost.query.filter_by(user_id=user_id).delete()
    BlockedUser.query.filter(or_(BlockedUser.blocker_id == user_id, BlockedUser.blocked_id == user_id)).delete()
    db.session.delete(target)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

@app.route('/api/admin/ban/user/<int:user_id>', methods=['POST'])
def admin_ban_user(user_id):
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    target = User.query.get_or_404(user_id)
    if target.is_admin:
        return jsonify({'error': 'Cannot ban admin'}), 400
    target.is_banned = not target.is_banned
    notif = Notification(user_id=user_id, type='system', message=f'Your account has been {"banned" if target.is_banned else "unbanned"}')
    db.session.add(notif)
    db.session.commit()
    return jsonify({'message': 'Banned' if target.is_banned else 'Unbanned'})

@app.route('/api/admin/warn/user/<int:user_id>', methods=['POST'])
def admin_warn_user(user_id):
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    message = request.json.get('message')
    notif = Notification(user_id=user_id, type='warning', message=message)
    db.session.add(notif)
    db.session.commit()
    return jsonify({'message': 'Warning sent'})

@app.route('/api/admin/send_message', methods=['POST'])
def admin_send_message():
    admin = get_current_user()
    if not admin or not admin.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')
    to_all = data.get('to_all', False)
    if to_all:
        users = User.query.all()
        for u in users:
            notif = Notification(user_id=u.id, type='system', message=message)
            db.session.add(notif)
    else:
        notif = Notification(user_id=user_id, type='system', message=message)
        db.session.add(notif)
    db.session.commit()
    return jsonify({'message': 'Sent'})

@app.route('/api/admin/reports', methods=['GET'])
def admin_reports():
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    reports = Report.query.all()
    data = [{'id': r.id, 'reporter': User.query.get(r.reporter_id).username, 'type': r.reported_type, 'reported_id': r.reported_id, 'description': r.description, 'timestamp': r.timestamp.isoformat()} for r in reports]
    return jsonify({'reports': data})

@app.route('/api/admin/delete/content/<int:post_id>', methods=['POST'])
def admin_delete_content(post_id):
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

@app.route('/api/admin/delete/group/<int:group_id>', methods=['POST'])
def admin_delete_group(group_id):
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    group = Group.query.get_or_404(group_id)
    GroupMember.query.filter_by(group_id=group_id).delete()
    GroupMessage.query.filter_by(group_id=group_id).delete()
    db.session.delete(group)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
