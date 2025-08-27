import sqlite3
import os
from datetime import datetime, timedelta, timezone
import random
import string
import json
import uuid  # Import uuid for generating unique IDs
import base64  # Needed for base64 decoding camera/voice note data
import re  # Needed for process_mentions_and_links

# Flask, Werkzeug, etc. imports
from flask import Flask, Blueprint, request, g, session, jsonify, send_from_directory, url_for, redirect, render_template, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask_moment import Moment
from functools import wraps  # For admin_required decorator

import config  # Your configuration file

app = Flask(__name__)

# Use environment variable for SECRET_KEY or fall back to config.py
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', config.SECRET_KEY)

# Database path
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'family_tree.db')

# Upload folders configuration
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'Uploads')  # General upload folder
app.config['PROFILE_PHOTOS_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'profile_photos')
app.config['POST_MEDIA_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'post_media')
app.config['REEL_MEDIA_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'reel_media')
app.config['STORY_MEDIA_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'story_media')
app.config['CHAT_MEDIA_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'chat_media')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit for uploads

# Ensure upload directories exist
os.makedirs(app.config['PROFILE_PHOTOS_FOLDER'], exist_ok=True)
os.makedirs(app.config['POST_MEDIA_FOLDER'], exist_ok=True)
os.makedirs(app.config['REEL_MEDIA_FOLDER'], exist_ok=True)
os.makedirs(app.config['STORY_MEDIA_FOLDER'], exist_ok=True)
os.makedirs(app.config['CHAT_MEDIA_FOLDER'], exist_ok=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = "info"

# Initialize Flask-Moment
moment = Moment(app)

# --- User Model for Flask-Login ---
class User(UserMixin):
    def __init__(self, id, username, is_admin):
        self.id = id
        self.username = username
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user_data = db.execute("SELECT id, username, is_admin FROM users WHERE id = ?", (user_id,)).fetchone()
    if user_data:
        return User(id=user_data['id'], username=user_data['username'], is_admin=user_data['is_admin'])
    return None

# --- Database Setup ---
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with open('schema.sql', 'r') as f:
        db.executescript(f.read())
    # Create the admin user if they don't exist
    password_hash = generate_password_hash(config.ADMIN_PASSWORD)
    db.execute("INSERT INTO users (username, originalName, password_hash, is_admin, unique_key) VALUES (?, ?, ?, 1, ?)",
               (config.ADMIN_USERNAME, 'Admin', password_hash, 'ADMIN'))
    db.commit()

# Register close_db with the app context
app.teardown_appcontext(close_db)

# --- Decorators ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# --- Helper Functions ---
def send_system_notification(receiver_id, type, message, link=None):
    """Sends a system notification to a specific user."""
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
    """Retrieves the admin user's ID."""
    db = get_db()
    admin_user = db.execute("SELECT id FROM users WHERE username = ?", (config.ADMIN_USERNAME,)).fetchone()
    if admin_user:
        return admin_user['id']
    return None

def get_user_by_username(username):
    """Fetches a user by username."""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return user

def get_user_by_id(user_id):
    """Fetches a user by ID."""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return user

def is_valid_uuid(val):
    """Checks if a string is a valid UUID."""
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

def generate_unique_key():
    """Generates a random 4-character unique key for password reset."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

# --- Application Routes ---
@app.route('/')
def home():
    """Main home page route."""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user_data = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(id=user_data['id'], username=user_data['username'], is_admin=user_data['is_admin'])
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password.", "danger")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles new user registration."""
    if request.method == 'POST':
        username = request.form['username']
        original_name = request.form['originalName']
        password = request.form['password']
        confirm_password = request.form['confirmPassword']

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('register'))

        db = get_db()
        try:
            password_hash = generate_password_hash(password)
            unique_key = generate_unique_key()
            db.execute(
                "INSERT INTO users (username, originalName, password_hash, unique_key) VALUES (?, ?, ?, ?)",
                (username, original_name, password_hash, unique_key)
            )
            db.commit()
            flash(f"Registration successful! Your unique key is: {unique_key}. Keep it safe!", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists.", "danger")
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Handles user logout."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Handles the password reset request."""
    if request.method == 'POST':
        username = request.form.get('username')
        unique_key = request.form.get('unique_key').upper()
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ? AND unique_key = ?", (username, unique_key)).fetchone()
        if user:
            # Set a pending flag and redirect to the password reset page
            db.execute("UPDATE users SET password_reset_pending = 1, reset_request_timestamp = ? WHERE id = ?",
                       (datetime.now(timezone.utc), user['id']))
            db.commit()
            flash("Verification successful. You can now set a new password.", "success")
            return redirect(url_for('set_new_password', unique_id=user['id']))
        else:
            flash("Verification failed. Please check your username and unique key.", "danger")
    return render_template('forgot_password.html')

@app.route('/set_new_password/<int:unique_id>', methods=['GET', 'POST'])
def set_new_password(unique_id):
    """Allows a user to set a new password after successful verification."""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ? AND password_reset_pending = 1", (unique_id,)).fetchone()
    if not user:
        flash("Invalid or expired password reset link.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('set_new_password', unique_id=unique_id))

        password_hash = generate_password_hash(new_password)
        db.execute(
            "UPDATE users SET password_hash = ?, password_reset_pending = 0 WHERE id = ?",
            (password_hash, user['id'])
        )
        db.commit()
        flash("Your password has been reset successfully. You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('set_new_password.html', username=user['username'], unique_id=unique_id)

@app.route('/friends')
@login_required
def friends():
    """Renders the friends management page."""
    # Placeholder logic
    # TODO: Fetch friends, friend requests, and suggestions from the database
    friends_list = []
    friend_requests = []
    suggested_users = []
    return render_template('friends.html', friends=friends_list, requests=friend_requests, suggestions=suggested_users)

@app.route('/inbox')
@login_required
def inbox():
    """Renders the user's inbox page."""
    # Placeholder logic
    # TODO: Fetch recent chats and group conversations
    chats = []
    groups = []
    return render_template('inbox.html', chats=chats, groups=groups)

@app.route('/add_to')
@login_required
def add_to():
    """Renders the content creation selection page."""
    return render_template('add_to.html')

# --- Admin Routes ---
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """
    Renders the admin dashboard with overview data and lists of content/users.
    """
    db = get_db()

    # Get dashboard counts
    user_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    group_count = db.execute("SELECT COUNT(*) FROM groups").fetchone()[0]
    post_count = db.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    report_count = db.execute("SELECT COUNT(*) FROM reports WHERE status = 'pending'").fetchone()[0]

    counts = {
        'user_count': user_count,
        'group_count': group_count,
        'post_count': post_count,
        'report_count': report_count
    }

    # Get lists of users, groups, and pending reports
    users = db.execute("SELECT id, username, originalName, created_at, is_admin FROM users ORDER BY created_at DESC").fetchall()
    groups = db.execute("SELECT id, name, created_at FROM groups ORDER BY created_at DESC").fetchall()
    
    # Fetch reports with associated user/item data
    reports = db.execute("""
        SELECT 
            r.id, r.reported_item_type, r.reported_item_id, r.reason, r.timestamp,
            u.username AS reporter_username
        FROM reports r
        JOIN users u ON r.reported_by_user_id = u.id
        WHERE r.status = 'pending'
        ORDER BY r.timestamp DESC
    """).fetchall()

    return render_template('admin_dashboard.html', counts=counts, users=users, groups=groups, reports=reports)


@app.route('/api/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """
    API endpoint to delete a user and all associated data.
    """
    db = get_db()
    try:
        # Check if the user exists
        user = db.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return jsonify({"success": False, "message": "User not found."}), 404
        
        # Prevent admin from deleting themselves or other admins
        # This is a good safety measure to prevent accidental lockouts
        if user['id'] == current_user.id:
            return jsonify({"success": False, "message": "Cannot delete your own admin account."}), 403
        
        # Delete user and their associated content (handled by CASCADE in schema)
        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        db.commit()
        return jsonify({"success": True, "message": "User and all related data deleted successfully."}), 200
    except Exception as e:
        app.logger.error(f"Error deleting user {user_id}: {e}")
        return jsonify({"success": False, "message": "An error occurred."}), 500


@app.route('/api/admin/delete_group/<int:group_id>', methods=['POST'])
@login_required
@admin_required
def delete_group(group_id):
    """
    API endpoint to delete a group.
    """
    db = get_db()
    try:
        # Check if the group exists
        group = db.execute("SELECT id FROM groups WHERE id = ?", (group_id,)).fetchone()
        if not group:
            return jsonify({"success": False, "message": "Group not found."}), 404

        # Delete the group (handled by CASCADE in schema)
        db.execute("DELETE FROM groups WHERE id = ?", (group_id,))
        db.commit()
        return jsonify({"success": True, "message": "Group deleted successfully."}), 200
    except Exception as e:
        app.logger.error(f"Error deleting group {group_id}: {e}")
        return jsonify({"success": False, "message": "An error occurred."}), 500


@app.route('/api/admin/handle_report/<int:report_id>/<string:action>', methods=['POST'])
@login_required
@admin_required
def handle_report(report_id, action):
    """
    API endpoint to handle a pending report.
    Actions can be 'warn', 'ban', or 'ignore'.
    """
    if action not in ['warn', 'ban', 'ignore']:
        return jsonify({"success": False, "message": "Invalid action."}), 400

    db = get_db()
    try:
        report = db.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        if not report:
            return jsonify({"success": False, "message": "Report not found."}), 404

        # Get the reporter's user ID to send a notification
        reporter_id = report['reported_by_user_id']
        
        if action == 'warn':
            # Create a warning and send a notification
            db.execute(
                "INSERT INTO warnings (user_id, reason, status) VALUES (?, ?, 'active')",
                (report['reported_item_id'], f"Report of type '{report['reported_item_type']}' handled with a warning: {report['reason']}")
            )
            message = "Your report has been reviewed and a warning has been issued."
        elif action == 'ban':
            # Ban the user or content (logic to be implemented) and notify
            # For this example, let's just delete the reported item/user.
            if report['reported_item_type'] == 'user':
                db.execute("DELETE FROM users WHERE id = ?", (report['reported_item_id'],))
            elif report['reported_item_type'] == 'post':
                db.execute("DELETE FROM posts WHERE id = ?", (report['reported_item_id'],))
            # ... add other content types as needed
            message = "Your report has been reviewed and the reported content/user has been removed."
        else: # action == 'ignore'
            message = "Your report has been reviewed and marked as ignored."

        # Update the report status to handled
        db.execute(
            "UPDATE reports SET status = 'handled', admin_notes = ? WHERE id = ?",
            (f"Report marked as {action}", report_id)
        )
        db.commit()

        # Send a system notification to the user who filed the report
        send_system_notification(reporter_id, 'report_status', message)

        return jsonify({"success": True, "message": f"Report successfully handled with action: {action}."}), 200

    except Exception as e:
        app.logger.error(f"Error handling report {report_id} with action {action}: {e}")
        db.rollback()
        return jsonify({"success": False, "message": "An error occurred."}), 500

# Run the app
if __name__ == '__main__':
    # Initialize the database if it doesn't exist
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            init_db()
        else:  # If tables exist, still ensure admin is present, useful for existing databases
            # This handles cases where a database exists but the admin user might have been manually deleted
            # or wasn't created in previous versions.
            cursor.execute("SELECT id FROM users WHERE username = ?", (config.ADMIN_USERNAME,))
            if not cursor.fetchone():
                # This logic is a bit flawed if the schema has changed. A better approach would be to check
                # for missing tables and run a migration script, but for now, we will simply check for the admin user.
                # If the admin is missing, it's safer to re-run init_db() which will recreate tables based on schema.sql
                # and then add the admin user.
                init_db()
    db.close()
    app.run(debug=True)
