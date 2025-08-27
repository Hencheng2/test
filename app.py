import sqlite3
import os
from datetime import datetime, timedelta, timezone
import random
import string
import json
import uuid # Import uuid for generating unique IDs
import base64 # Needed for base64 decoding camera/voice note data
import re # Needed for process_mentions_and_links

import firebase_admin
from firebase_admin import credentials, firestore, initialize_app # initialize_app is needed if credentials path exists

from flask import Flask, Blueprint, request, g, session, jsonify, send_from_directory, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash # Corrected: Removed extra 'werk'
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask_moment import Moment
from functools import wraps # For admin_required decorator

import config # Your configuration file

app = Flask(__name__)

# Use environment variable for SECRET_KEY or fall back to config.py
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', config.SECRET_KEY)

# Database path
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'family_tree.db')

# Upload folders configuration
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'Uploads') # General upload folder
app.config['PROFILE_PHOTOS_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'profile_photos')
app.config['POST_MEDIA_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'post_media')
app.config['REEL_MEDIA_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'reel_media')
app.config['STORY_MEDIA_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'story_media')
app.config['VOICE_NOTES_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'voice_notes')
app.config['CHAT_MEDIA_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'chat_media')
app.config['CHAT_BACKGROUND_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'chat_backgrounds')

# Ensure upload directories exist
for folder in [
    app.config['PROFILE_PHOTOS_FOLDER'],
    app.config['POST_MEDIA_FOLDER'],
    app.config['REEL_MEDIA_FOLDER'],
    app.config['STORY_MEDIA_FOLDER'],
    app.config['VOICE_NOTES_FOLDER'],
    app.config['CHAT_MEDIA_FOLDER'],
    app.config['CHAT_BACKGROUND_FOLDER']
]:
    os.makedirs(folder, exist_ok=True)


# Allowed extensions for uploads
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg'}

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect to login page if user is not authenticated

# Initialize Flask-Moment for date/time formatting
moment = Moment(app) # Use Moment object

# --- Firebase Admin SDK Initialization ---
# Only initialize if firebase_admin_key.json exists and is valid.
# No active Firestore/Storage operations are implemented in user-facing routes as per user's request.
db_firestore = None # Initialize to None by default
if config.FIREBASE_ADMIN_CREDENTIALS_PATH and os.path.exists(config.FIREBASE_ADMIN_CREDENTIALS_PATH):
    try:
        # Check if Firebase app is already initialized to prevent re-initialization
        if not firebase_admin._apps:
            cred = credentials.Certificate(config.FIREBASE_ADMIN_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred, {
                'projectId': config.FIREBASE_CLIENT_CONFIG['projectId'],
                'storageBucket': config.FIREBASE_CLIENT_CONFIG['storageBucket']
            })
            # db_firestore = firestore.client() # Firestore client not actively used for data ops
            app.logger.info("Firebase Admin SDK initialized successfully.")
        else:
            app.logger.info("Firebase Admin SDK already initialized.")
    except Exception as e:
        app.logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
else:
    app.logger.warning("Firebase Admin SDK credentials file not found or path not configured. Firebase Admin SDK not initialized.")

# --- Database Helper Functions ---
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row # Return rows as dict-like objects
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# --- Helper Function for Unique Keys ---
def generate_unique_key():
    """Generates a 4-character unique key (2 letters, 2 numbers)."""
    letters = random.choices(string.ascii_uppercase, k=2)
    numbers = random.choices(string.digits, k=2)
    key_chars = letters + numbers
    random.shuffle(key_chars)
    return "".join(key_chars)


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.executescript(f.read())
        
        # --- Create Admin User if not exists ---
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (config.ADMIN_USERNAME,))
        admin_exists = cursor.fetchone()

        if not admin_exists:
            # Generate a unique key for the admin
            admin_unique_key = generate_unique_key() # Reusing the helper for consistency
            
            # Hash the admin password from config.py
            hashed_admin_password = generate_password_hash(config.ADMIN_PASSWORD_RAW) # Corrected to config.ADMIN_PASSWORD_RAW

            cursor.execute(
                """
                INSERT INTO users (username, originalName, password_hash, unique_key, is_admin)
                VALUES (?, ?, ?, ?, ?)
                """,
                (config.ADMIN_USERNAME, "SociaFam Admin", hashed_admin_password, admin_unique_key, 1) # is_admin = 1
            )
            admin_user_id = cursor.lastrowid
            
            # Also create a member profile for the admin
            db.execute(
                """
                INSERT INTO members (user_id, fullName, gender)
                VALUES (?, ?, ?)
                """,
                (admin_user_id, "SociaFam Admin", "Prefer not to say") # Default gender for admin
            )
            app.logger.info(f"Admin user '{config.ADMIN_USERNAME}' created with unique key '{admin_unique_key}'.")
        else:
            app.logger.info(f"Admin user '{config.ADMIN_USERNAME}' already exists.")

        db.commit() # Commit all changes after script and admin creation
    app.logger.info("Database initialized/updated from schema.sql.")

# Register close_db with the app context
app.teardown_appcontext(close_db)

# Run init_db once when the app starts if tables don't exist
with app.app_context():
    db = get_db()
    cursor = db.cursor()
    # Check for a critical table like 'users'
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    if not cursor.fetchone():
        init_db()
    else: # If tables exist, still ensure admin is present, useful for existing databases
        # This handles cases where a database exists but the admin user might have been manually deleted
        # or wasn't created in previous versions.
        cursor.execute("SELECT id FROM users WHERE username = ?", (config.ADMIN_USERNAME,))
        if not cursor.fetchone():
            init_db() # Call init_db to create admin even if tables exist
    db.close()


# --- User Model for Flask-Login ---
class User(UserMixin):
    def __init__(self, id, username, password_hash, is_admin=0, theme_preference='light', chat_background_image_path=None, unique_key=None, password_reset_pending=0, reset_request_timestamp=None, last_login_at=None, last_seen_at=None, original_name=None, email=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.is_admin = bool(is_admin) # Convert to boolean
        self.theme_preference = theme_preference
        self.chat_background_image_path = chat_background_image_path
        self.unique_key = unique_key
        self.password_reset_pending = bool(password_reset_pending)
        self.reset_request_timestamp = reset_request_timestamp
        self.last_login_at = last_login_at
        self.last_seen_at = last_seen_at
        self.original_name = original_name
        self.email = email # Allow email to be stored for login

    def get_id(self):
        return str(self.id)

    def get_member_profile(self):
        db = get_db()
        member_profile = db.execute('SELECT * FROM members WHERE user_id = ?', (self.id,)).fetchone()
        return member_profile

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user_data = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user_data:
        # Fetch member details to get email if available
        member_data = db.execute('SELECT email FROM members WHERE user_id = ?', (user_id,)).fetchone()
        email = member_data['email'] if member_data else None
        return User(
            id=user_data['id'],
            username=user_data['username'],
            password_hash=user_data['password_hash'],
            is_admin=user_data['is_admin'],
            theme_preference=user_data['theme_preference'],
            chat_background_image_path=user_data['chat_background_image_path'],
            unique_key=user_data['unique_key'],
            password_reset_pending=user_data['password_reset_pending'],
            reset_request_timestamp=user_data['reset_request_timestamp'],
            last_login_at=user_data['last_login_at'],
            last_seen_at=user_data['last_seen_at'],
            original_name=user_data['originalName'],
            email=email
        )
    return None

# --- Decorator for Admin-Only Access ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'success': False, 'message': 'You do not have administrative privileges.'}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- Helper Functions for File Uploads ---
def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, upload_folder):
    if file and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS.union(ALLOWED_VIDEO_EXTENSIONS).union(ALLOWED_AUDIO_EXTENSIONS)):
        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + '_' + filename
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        return os.path.join('static', 'Uploads', os.path.basename(upload_folder), unique_filename)
    return None


def get_member_profile_pic(user_id):
    db = get_db()
    member = db.execute("SELECT profilePhoto FROM members WHERE user_id = ?", (user_id,)).fetchone()
    if member and member['profilePhoto']:
        # Ensure the path is relative to 'static/' as expected by url_for
        # The stored path should already be like 'static/uploads/profile_photos/...'
        if member['profilePhoto'].startswith('static/'):
            # Only take the part after 'static/' for url_for's filename
            return url_for('static', filename=member['profilePhoto'][len('static/'):])
        # Fallback if path doesn't start with static/, though it should if saved by save_uploaded_file
        return url_for('static', filename=member['profilePhoto'])
    return url_for('static', filename='img/default_profile.png')

def get_member_from_user_id(user_id):
    db = get_db()
    member = db.execute('SELECT * FROM members WHERE user_id = ?', (user_id,)).fetchone()
    return member

def get_user_from_member_id(member_id):
    db = get_db()
    user_id_row = db.execute('SELECT user_id FROM members WHERE id = ?', (member_id,)).fetchone()
    if user_id_row:
        return load_user(user_id_row['user_id'])
    return None

def process_mentions_and_links(text):
    """
    Processes text to:
    1. Replace @username with clickable links to user profiles.
    2. Convert URLs to clickable links.
    """
    db = get_db()
    
    # 1. Process mentions
    # Find all mentions like @username
    def replace_mention(match):
        username = match.group(1)
        user = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if user:
            return f'<a href="{url_for("profile", username=username)}">@{username}</a>'
        return match.group(0) # If username not found, keep original text
    
    processed_text = re.sub(r'@([a-zA-Z0-9_]+)', replace_mention, text)

    # 2. Process URLs
    # Regular expression to find URLs
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    def replace_url(match):
        url = match.group(0)
        # Prepend http:// if missing (for www. links)
        if not url.startswith('http'):
            url = 'http://' + url
        return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>'
    
    processed_text = re.sub(url_pattern, replace_url, processed_text)
    
    return processed_text

def get_relationship_status(current_id, other_id):
    db = get_db()
    friendship = db.execute(
        """
        SELECT status, user1_id FROM friendships
        WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
        """,
        (current_id, other_id, other_id, current_id)
    ).fetchone()
    if friendship:
        if friendship['status'] == 'accepted':
            return 'friend'
        elif friendship['status'] == 'pending':
            if friendship['user1_id'] == current_id:
                return 'pending_sent'
            else:
                return 'pending_received'
        else:
            return 'none'  # Treat declined as none for UI purposes
    return 'none'

def is_blocked(blocker_id, blocked_id):
    db = get_db()
    blocked = db.execute(
        "SELECT id FROM blocked_users WHERE blocker_id = ? AND blocked_id = ?",
        (blocker_id, blocked_id)
    ).fetchone()
    return bool(blocked)

def get_mutual_friends_count(user1_id, user2_id):
    db = get_db()
    query = """
        SELECT COUNT(*) FROM (
            SELECT CASE WHEN user1_id = ? THEN user2_id ELSE user1_id END AS friend_id
            FROM friendships WHERE (user1_id = ? OR user2_id = ?) AND status = 'accepted'
            INTERSECT
            SELECT CASE WHEN user1_id = ? THEN user2_id ELSE user1_id END AS friend_id
            FROM friendships WHERE (user1_id = ? OR user2_id = ?) AND status = 'accepted'
        )
    """
    count = db.execute(query, (user1_id, user1_id, user1_id, user2_id, user2_id, user2_id)).fetchone()[0]
    return count

# --- System Notification & Messaging Functions ---
def send_system_notification(receiver_id, message, link=None, type='system_message'):
    db = get_db()
    try:
        db.execute(
            "INSERT INTO notifications (receiver_id, type, message, timestamp, link, is_read) VALUES (?, ?, ?, ?, ?, ?)",
            (receiver_id, type, message, datetime.now(timezone.utc), link, 0)
        )
        db.commit()
        app.logger.info(f"System notification sent to user {receiver_id}: {message}")
    except Exception as e:
        app.logger.error(f"Error sending system notification to {receiver_id}: {e}")

def get_admin_user_id():
    db = get_db()
    admin_user = db.execute("SELECT id FROM users WHERE username = ?", (config.ADMIN_USERNAME,)).fetchone()
    if admin_user:
        return admin_user['id']
    return None

# --- Context Processor to pass variables to all templates ---
@app.context_processor
def inject_global_variables():
    current_year = datetime.now().year
    
    # These checks are crucial for the base template
    is_authenticated = current_user.is_authenticated
    show_nav_tabs = is_authenticated and not current_user.is_admin
    navbar_profile_photo = None
    has_unread_messages = False
    has_unread_notifications = False
    
    if is_authenticated:
        db = get_db()
        # Admin does not have a member profile photo in the same way regular users do
        if not current_user.is_admin:
            member_profile = get_member_from_user_id(current_user.id)
            if member_profile and member_profile['profilePhoto']:
                navbar_profile_photo = url_for('static', filename=member_profile['profilePhoto'][len('static/'):])
            else:
                navbar_profile_photo = url_for('static', filename='img/default_profile.png')
        
        # Check for unread messages and notifications
        has_unread_messages = check_for_unread_messages(current_user.id) # Placeholder function
        has_unread_notifications = check_for_unread_notifications(current_user.id) # Placeholder function

    return {
        'current_year': current_year,
        'is_authenticated': is_authenticated,
        'show_nav_tabs': show_nav_tabs,
        'navbar_profile_photo': navbar_profile_photo,
        'has_unread_messages': has_unread_messages,
        'has_unread_notifications': has_unread_notifications
    }

def check_for_unread_messages(user_id):
    # Placeholder for a function that checks for unread messages
    # This will be implemented in a future file.
    return False

def check_for_unread_notifications(user_id):
    # Placeholder for a function that checks for unread notifications
    # This will be implemented in a future file.
    return False


# --- Routes ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard')) # Admin lands on dashboard
        else:
            return redirect(url_for('home')) # Regular user lands on home/feed
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember_me')
        
        db = get_db()
        # First, try to find a user by username
        user_data = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        # If no user found, try to find a member by email to get the user ID
        if not user_data:
            member_data = db.execute('SELECT user_id FROM members WHERE email = ?', (username,)).fetchone()
            if member_data:
                user_data = db.execute('SELECT * FROM users WHERE id = ?', (member_data['user_id'],)).fetchone()
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = load_user(user_data['id'])
            login_user(user, remember=remember)
            
            # Update last login timestamp
            db.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (datetime.now(timezone.utc), user.id))
            db.commit()

            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username/email or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        db = get_db()
        
        # Check if username or email already exists
        user_exists = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        email_exists = db.execute('SELECT id FROM members WHERE email = ?', (email,)).fetchone()
        
        if user_exists:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        
        if email_exists:
            flash('Email address is already registered.', 'danger')
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        unique_key = generate_unique_key()
        
        try:
            # Insert into users table
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO users (username, originalName, password_hash, unique_key) VALUES (?, ?, ?, ?)",
                (username, full_name, hashed_password, unique_key)
            )
            user_id = cursor.lastrowid
            
            # Insert into members table
            db.execute(
                "INSERT INTO members (user_id, fullName, email) VALUES (?, ?, ?)",
                (user_id, full_name, email)
            )
            db.commit()
            
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('An error occurred during registration. Please try again.', 'danger')
            db.rollback()
            
    return render_template('register.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        db = get_db()

        # Try to find user by email first, then username
        user_data = db.execute(
            """
            SELECT u.* FROM users u
            LEFT JOIN members m ON u.id = m.user_id
            WHERE m.email = ? OR u.username = ?
            """,
            (identifier, identifier)
        ).fetchone()

        if user_data:
            # Set password reset pending flag and timestamp
            db.execute(
                "UPDATE users SET password_reset_pending = 1, reset_request_timestamp = ? WHERE id = ?",
                (datetime.now(timezone.utc), user_data['id'])
            )
            db.commit()
            # In a real app, this would trigger an email or SMS with the unique key
            # For now, we flash the unique key for demonstration purposes
            flash(f"A password reset request has been initiated. Your unique key is: {user_data['unique_key']}. Use this to set a new password.", 'info')
            return redirect(url_for('set_new_password'))
        else:
            flash('No account found with that username or email.', 'danger')

    return render_template('forgot_password.html')

@app.route('/set_new_password', methods=['GET', 'POST'])
def set_new_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        unique_key = request.form.get('unique_key')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('set_new_password.html')

        db = get_db()
        user_data = db.execute(
            "SELECT * FROM users WHERE unique_key = ? AND password_reset_pending = 1",
            (unique_key,)
        ).fetchone()

        if user_data:
            # Check if the reset request is within the valid time frame (e.g., 1 hour)
            reset_timestamp = datetime.fromisoformat(user_data['reset_request_timestamp'])
            if datetime.now(timezone.utc) - reset_timestamp > timedelta(hours=1):
                flash('The unique key has expired. Please request a new one.', 'danger')
                db.execute("UPDATE users SET password_reset_pending = 0, reset_request_timestamp = NULL WHERE id = ?", (user_data['id'],))
                db.commit()
                return redirect(url_for('forgot_password'))

            # Hash and update the new password
            hashed_password = generate_password_hash(new_password)
            db.execute(
                "UPDATE users SET password_hash = ?, password_reset_pending = 0, reset_request_timestamp = NULL WHERE id = ?",
                (hashed_password, user_data['id'])
            )
            db.commit()
            flash('Password reset successful! You can now log in with your new password.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid or expired unique key. Please check the key and try again.', 'danger')

    return render_template('set_new_password.html')


# --- Routes for new templates ---
@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Placeholder data for the dashboard
    db = get_db()
    counts = {
        'user_count': db.execute("SELECT COUNT(id) FROM users").fetchone()[0],
        'group_count': db.execute("SELECT COUNT(id) FROM groups").fetchone()[0],
        'post_count': db.execute("SELECT COUNT(id) FROM posts").fetchone()[0],
        'report_count': db.execute("SELECT COUNT(id) FROM reports WHERE status = 'pending'").fetchone()[0],
        'warning_count': db.execute("SELECT COUNT(id) FROM warnings WHERE status = 'active'").fetchone()[0]
    }
    recent_users = db.execute("SELECT * FROM users ORDER BY id DESC LIMIT 5").fetchall()
    recent_reports = db.execute("SELECT * FROM reports WHERE status = 'pending' ORDER BY timestamp DESC LIMIT 5").fetchall()

    return render_template('admin_dashboard.html', counts=counts, recent_users=recent_users, recent_reports=recent_reports)

@app.route('/add_to')
@login_required
def add_to():
    return render_template('add_to.html')

@app.route('/inbox')
@login_required
def inbox():
    # Placeholder logic for inbox
    chats = [] # List of chats
    groups = [] # List of groups
    return render_template('inbox.html', chats=chats, groups=groups)

@app.route('/friends')
@login_required
def friends():
    # Placeholder logic for friends page
    my_friends = [] # List of friends
    sent_requests = [] # List of sent requests
    received_requests = [] # List of received requests
    suggestions = [] # List of friend suggestions
    return render_template('friends.html', my_friends=my_friends, sent_requests=sent_requests, received_requests=received_requests, suggestions=suggestions)


# --- Placeholder Routes ---
@app.route('/home')
@login_required
def home():
    # Will be implemented in the future
    return "Home Page (Placeholder)"

@app.route('/reels')
@login_required
def reels():
    # Will be implemented in the future
    return "Reels Page (Placeholder)"

@app.route('/notifications')
@login_required
def notifications():
    # Will be implemented in the future
    return "Notifications Page (Placeholder)"

@app.route('/my_profile')
@login_required
def my_profile():
    # Will be implemented in the future
    return "My Profile Page (Placeholder)"

@app.route('/menu')
@login_required
def menu():
    # Will be implemented in the future
    return "Menu Page (Placeholder)"

@app.route('/profile/<username>')
@login_required
def profile(username):
    # Will be implemented in the future
    return f"Profile Page for {username} (Placeholder)"

@app.route('/terms_and_policies')
def terms_and_policies():
    # Will be implemented in the future
    return "Terms and Policies Page (Placeholder)"


# Run the app
if __name__ == '__main__':
    # Initialize the database if it doesn't exist
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            init_db()
        else: # If tables exist, still ensure admin is present, useful for existing databases
            # This handles cases where a database exists but the admin user might have been manually deleted
            # or wasn't created in previous versions.
            cursor.execute("SELECT id FROM users WHERE username = ?", (config.ADMIN_USERNAME,))
            if not cursor.fetchone():
                init_db() # Call init_db to create admin even if tables exist
    db.close()
    app.run(debug=True) # Set debug=False in production
