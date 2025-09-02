import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime, timedelta
import json
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
app.config.from_pyfile('config.py')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sociafam.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '09da35833ef9cb699888f08d66a0cfb827fb10e53f6c1549'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    real_name = db.Column(db.String(120), nullable=True)
    profile_pic = db.Column(db.String(200), default='default_profile.png')
    bio = db.Column(db.Text, nullable=True)
    unique_key = db.Column(db.String(4), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Profile details
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    pronouns = db.Column(db.String(20), nullable=True)
    work = db.Column(db.String(120), nullable=True)
    education = db.Column(db.String(120), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    website = db.Column(db.String(200), nullable=True)
    relationship = db.Column(db.String(20), nullable=True)
    spouse = db.Column(db.String(80), nullable=True)
    
    # Privacy settings
    is_private = db.Column(db.Boolean, default=False)
    
    # Relationships
    followers = db.relationship('Follow', foreign_keys='Follow.followed_id', backref='followed', lazy='dynamic')
    following = db.relationship('Follow', foreign_keys='Follow.follower_id', backref='follower', lazy='dynamic')
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    stories = db.relationship('Story', backref='author', lazy='dynamic')
    reels = db.relationship('Reel', backref='author', lazy='dynamic')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    groups = db.relationship('GroupMember', backref='user', lazy='dynamic')

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('follower_id', 'followed_id'),)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    media_url = db.Column(db.String(200), nullable=True)
    media_type = db.Column(db.String(20), nullable=True)  # image, video, None
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_private = db.Column(db.Boolean, default=False)
    
    # Interactions
    likes = db.relationship('Like', backref='post', lazy='dynamic')
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    shares = db.relationship('Share', backref='post', lazy='dynamic')
    saves = db.relationship('Save', backref='post', lazy='dynamic')

class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=True)
    media_url = db.Column(db.String(200), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)  # image, video, audio
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=24))

class Reel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=True)
    media_url = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Interactions
    likes = db.relationship('ReelLike', backref='reel', lazy='dynamic')
    comments = db.relationship('ReelComment', backref='reel', lazy='dynamic')
    shares = db.relationship('ReelShare', backref='reel', lazy='dynamic')
    saves = db.relationship('ReelSave', backref='reel', lazy='dynamic')

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Share(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Save(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Similar models for Reel interactions
class ReelLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reel_id = db.Column(db.Integer, db.ForeignKey('reel.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ReelComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reel_id = db.Column(db.Integer, db.ForeignKey('reel.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ReelShare(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reel_id = db.Column(db.Integer, db.ForeignKey('reel.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ReelSave(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reel_id = db.Column(db.Integer, db.ForeignKey('reel.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Null for group messages
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)  # Null for direct messages
    media_url = db.Column(db.String(200), nullable=True)
    media_type = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    profile_pic = db.Column(db.String(200), default='default_group.png')
    unique_link = db.Column(db.String(20), unique=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Group settings
    allow_messages = db.Column(db.Boolean, default=True)
    allow_add_members = db.Column(db.Boolean, default=True)
    approve_new_members = db.Column(db.Boolean, default=False)
    
    members = db.relationship('GroupMember', backref='group', lazy='dynamic')
    messages = db.relationship('Message', backref='group', lazy='dynamic')

class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # friend_request, like, comment, message, etc.
    reference_id = db.Column(db.Integer, nullable=True)  # ID of the related entity
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reported_post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    reported_group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Admin access required')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Utility functions
def generate_unique_key():
    import random
    import string
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=2))
    return letters + numbers

def allowed_file(filename, allowed_extensions={'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Routes
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
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('auth/register.html')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('auth/register.html')
        
        # Password validation
        if len(password) < 6 or not any(char.isdigit() for char in password) or not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?`~' for char in password):
            flash('Password must be at least 6 characters with numbers and special characters')
            return render_template('auth/register.html')
        
        # Create user
        hashed_password = generate_password_hash(password)
        unique_key = generate_unique_key()
        
        # Ensure unique key is unique
        while User.query.filter_by(unique_key=unique_key).first():
            unique_key = generate_unique_key()
        
        # Prevent registration with admin credentials
        if username == app.config.get('ADMIN_USERNAME', 'Henry') and password == app.config.get('ADMIN_PASS', 'Dec@2003'):
            flash('Cannot use admin credentials for registration')
            return render_template('auth/register.html')
        
        user = User(
            username=username,
            password=hashed_password,
            unique_key=unique_key,
            real_name=username  # Default to username
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful. Please login.')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        unique_key = request.form.get('unique_key')
        
        user = User.query.filter_by(username=username, unique_key=unique_key).first()
        
        if user:
            session['reset_user_id'] = user.id
            return redirect(url_for('reset_password'))
        else:
            flash('Invalid username or unique key')
    
    return render_template('auth/forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_user_id' not in session:
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('auth/reset_password.html')
        
        # Password validation
        if len(password) < 6 or not any(char.isdigit() for char in password) or not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?`~' for char in password):
            flash('Password must be at least 6 characters with numbers and special characters')
            return render_template('auth/reset_password.html')
        
        user = User.query.get(session['reset_user_id'])
        user.password = generate_password_hash(password)
        db.session.commit()
        
        session.pop('reset_user_id', None)
        flash('Password reset successful. Please login.')
        return redirect(url_for('login'))
    
    return render_template('auth/reset_password.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# API Routes for dynamic content loading
@app.route('/api/home')
@login_required
def api_home():
    # Get posts from users that the current user follows
    following_ids = [f.followed_id for f in Follow.query.filter_by(follower_id=session['user_id']).all()]
    following_ids.append(session['user_id'])  # Include user's own posts
    
    posts = Post.query.filter(Post.user_id.in_(following_ids), Post.is_private == False).order_by(Post.created_at.desc()).all()
    
    # Get stories from users that the current user follows (within last 24 hours)
    stories = Story.query.filter(Story.user_id.in_(following_ids), Story.expires_at > datetime.utcnow()).order_by(Story.created_at.desc()).all()
    
    posts_data = []
    for post in posts:
        post_dict = {
            'id': post.id,
            'content': post.content,
            'media_url': post.media_url,
            'media_type': post.media_type,
            'user': {
                'id': post.author.id,
                'username': post.author.username,
                'real_name': post.author.real_name,
                'profile_pic': post.author.profile_pic
            },
            'created_at': post.created_at.isoformat(),
            'likes_count': post.likes.count(),
            'comments_count': post.comments.count(),
            'shares_count': post.shares.count(),
            'is_liked': post.likes.filter_by(user_id=session['user_id']).first() is not None,
            'is_saved': post.saves.filter_by(user_id=session['user_id']).first() is not None
        }
        posts_data.append(post_dict)
    
    stories_data = []
    for story in stories:
        story_dict = {
            'id': story.id,
            'content': story.content,
            'media_url': story.media_url,
            'media_type': story.media_type,
            'user': {
                'id': story.author.id,
                'username': story.author.username,
                'real_name': story.author.real_name,
                'profile_pic': story.author.profile_pic
            },
            'created_at': story.created_at.isoformat()
        }
        stories_data.append(story_dict)
    
    return jsonify({
        'posts': posts_data,
        'stories': stories_data
    })

@app.route('/api/reels')
@login_required
def api_reels():
    reels = Reel.query.order_by(Reel.created_at.desc()).all()
    
    reels_data = []
    for reel in reels:
        reel_dict = {
            'id': reel.id,
            'content': reel.content,
            'media_url': reel.media_url,
            'user': {
                'id': reel.author.id,
                'username': reel.author.username,
                'real_name': reel.author.real_name,
                'profile_pic': reel.author.profile_pic
            },
            'created_at': reel.created_at.isoformat(),
            'likes_count': reel.likes.count(),
            'comments_count': reel.comments.count(),
            'shares_count': reel.shares.count(),
            'is_liked': reel.likes.filter_by(user_id=session['user_id']).first() is not None,
            'is_saved': reel.saves.filter_by(user_id=session['user_id']).first() is not None
        }
        reels_data.append(reel_dict)
    
    return jsonify({'reels': reels_data})

@app.route('/api/friends')
@login_required
def api_friends():
    user_id = session['user_id']
    
    # Get followers
    followers = Follow.query.filter_by(followed_id=user_id).all()
    followers_data = []
    for follow in followers:
        follower = User.query.get(follow.follower_id)
        mutual_count = get_mutual_friends_count(user_id, follower.id)
        followers_data.append({
            'id': follower.id,
            'username': follower.username,
            'real_name': follower.real_name,
            'profile_pic': follower.profile_pic,
            'mutual_count': mutual_count
        })
    
    # Get following
    following = Follow.query.filter_by(follower_id=user_id).all()
    following_data = []
    for follow in following:
        followed = User.query.get(follow.followed_id)
        mutual_count = get_mutual_friends_count(user_id, followed.id)
        following_data.append({
            'id': followed.id,
            'username': followed.username,
            'real_name': followed.real_name,
            'profile_pic': followed.profile_pic,
            'mutual_count': mutual_count
        })
    
    # Get friends (mutual follows)
    friends_data = []
    for follow in following:
        # Check if the followed user also follows back
        if Follow.query.filter_by(follower_id=follow.followed_id, followed_id=user_id).first():
            friend = User.query.get(follow.followed_id)
            mutual_count = get_mutual_friends_count(user_id, friend.id)
            friends_data.append({
                'id': friend.id,
                'username': friend.username,
                'real_name': friend.real_name,
                'profile_pic': friend.profile_pic,
                'mutual_count': mutual_count
            })
    
    # Get friend requests
    # This would require a separate FriendRequest model which we haven't implemented
    # For now, we'll return empty list
    friend_requests_data = []
    
    # Get suggested friends (users with mutual friends)
    suggested_data = get_suggested_friends(user_id)
    
    return jsonify({
        'followers': followers_data,
        'following': following_data,
        'friends': friends_data,
        'friend_requests': friend_requests_data,
        'suggested': suggested_data
    })

def get_mutual_friends_count(user1_id, user2_id):
    # Get users that both user1 and user2 follow
    user1_following = {f.followed_id for f in Follow.query.filter_by(follower_id=user1_id).all()}
    user2_following = {f.followed_id for f in Follow.query.filter_by(follower_id=user2_id).all()}
    
    # Get users that follow both user1 and user2
    user1_followers = {f.follower_id for f in Follow.query.filter_by(followed_id=user1_id).all()}
    user2_followers = {f.follower_id for f in Follow.query.filter_by(followed_id=user2_id).all()}
    
    # Mutual follows (both following each other)
    mutual_follows = user1_following.intersection(user2_followers).union(
        user2_following.intersection(user1_followers)
    )
    
    return len(mutual_follows)

def get_suggested_friends(user_id):
    # Get users followed by people you follow
    user_following = [f.followed_id for f in Follow.query.filter_by(follower_id=user_id).all()]
    
    suggested = set()
    for followed_id in user_following:
        # Get users that this person follows
        their_following = [f.followed_id for f in Follow.query.filter_by(follower_id=followed_id).all()]
        
        for potential_friend_id in their_following:
            # Don't suggest yourself or people you already follow
            if potential_friend_id != user_id and potential_friend_id not in user_following:
                # Check if not already friends (mutual follow)
                if not Follow.query.filter_by(follower_id=potential_friend_id, followed_id=user_id).first():
                    suggested.add(potential_friend_id)
    
    suggested_data = []
    for user_id in list(suggested)[:10]:  # Limit to 10 suggestions
        user = User.query.get(user_id)
        mutual_count = get_mutual_friends_count(session['user_id'], user_id)
        suggested_data.append({
            'id': user.id,
            'username': user.username,
            'real_name': user.real_name,
            'profile_pic': user.profile_pic,
            'mutual_count': mutual_count
        })
    
    return suggested_data

@app.route('/api/inbox')
@login_required
def api_inbox():
    user_id = session['user_id']
    
    # Get direct messages
    direct_messages = Message.query.filter(
        ((Message.sender_id == user_id) & (Message.receiver_id != None)) | 
        ((Message.receiver_id == user_id) & (Message.sender_id != None))
    ).order_by(Message.created_at.desc()).all()
    
    # Group messages by conversation
    conversations = {}
    for msg in direct_messages:
        other_user_id = msg.sender_id if msg.sender_id != user_id else msg.receiver_id
        if other_user_id not in conversations:
            conversations[other_user_id] = {
                'user': User.query.get(other_user_id),
                'last_message': msg,
                'unread_count': 0
            }
        
        if not msg.is_read and msg.receiver_id == user_id:
            conversations[other_user_id]['unread_count'] += 1
    
    # Convert to list
    chats_data = []
    for other_user_id, conv_data in conversations.items():
        other_user = conv_data['user']
        last_msg = conv_data['last_message']
        chats_data.append({
            'id': other_user.id,
            'username': other_user.username,
            'real_name': other_user.real_name,
            'profile_pic': other_user.profile_pic,
            'last_message': last_msg.content[:50] + '...' if len(last_msg.content) > 50 else last_msg.content,
            'last_message_time': last_msg.created_at.isoformat(),
            'unread_count': conv_data['unread_count']
        })
    
    # Get group messages
    user_groups = GroupMember.query.filter_by(user_id=user_id).all()
    groups_data = []
    for membership in user_groups:
        group = membership.group
        last_message = Message.query.filter_by(group_id=group.id).order_by(Message.created_at.desc()).first()
        
        if last_message:
            groups_data.append({
                'id': group.id,
                'name': group.name,
                'profile_pic': group.profile_pic,
                'last_message': last_message.content[:50] + '...' if len(last_message.content) > 50 else last_message.content,
                'last_message_time': last_message.created_at.isoformat(),
                'unread_count': 0  # Would need to track read status for groups
            })
    
    return jsonify({
        'chats': chats_data,
        'groups': groups_data
    })

@app.route('/api/profile/<int:user_id>')
@login_required
def api_profile(user_id):
    user = User.query.get_or_404(user_id)
    current_user_id = session['user_id']
    
    # Check if user is viewing their own profile
    is_own_profile = user_id == current_user_id
    
    # Get counts
    followers_count = Follow.query.filter_by(followed_id=user_id).count()
    following_count = Follow.query.filter_by(follower_id=user_id).count()
    posts_count = Post.query.filter_by(user_id=user_id).count()
    
    # Get mutual friends count if not own profile
    mutual_count = 0
    if not is_own_profile:
        mutual_count = get_mutual_friends_count(current_user_id, user_id)
    
    # Check if current user follows this user
    is_following = Follow.query.filter_by(follower_id=current_user_id, followed_id=user_id).first() is not None
    
    # Get user posts
    posts = Post.query.filter_by(user_id=user_id, is_private=False).order_by(Post.created_at.desc()).all()
    posts_data = []
    for post in posts:
        post_dict = {
            'id': post.id,
            'content': post.content,
            'media_url': post.media_url,
            'media_type': post.media_type,
            'created_at': post.created_at.isoformat(),
            'likes_count': post.likes.count(),
            'comments_count': post.comments.count()
        }
        posts_data.append(post_dict)
    
    # Get user reels
    reels = Reel.query.filter_by(user_id=user_id).order_by(Reel.created_at.desc()).all()
    reels_data = []
    for reel in reels:
        reel_dict = {
            'id': reel.id,
            'content': reel.content,
            'media_url': reel.media_url,
            'created_at': reel.created_at.isoformat(),
            'likes_count': reel.likes.count(),
            'comments_count': reel.comments.count()
        }
        reels_data.append(reel_dict)
    
    profile_data = {
        'id': user.id,
        'username': user.username,
        'real_name': user.real_name,
        'profile_pic': user.profile_pic,
        'bio': user.bio,
        'unique_key': user.unique_key if is_own_profile else None,
        'followers_count': followers_count,
        'following_count': following_count,
        'posts_count': posts_count,
        'is_own_profile': is_own_profile,
        'is_following': is_following,
        'mutual_count': mutual_count,
        'posts': posts_data,
        'reels': reels_data,
        # Additional profile info
        'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
        'gender': user.gender,
        'pronouns': user.pronouns,
        'work': user.work,
        'education': user.education,
        'location': user.location,
        'website': user.website,
        'relationship': user.relationship,
        'spouse': user.spouse
    }
    
    return jsonify(profile_data)

@app.route('/api/search')
@login_required
def api_search():
    query = request.args.get('q', '')
    tab = request.args.get('tab', 'all')
    
    results = {}
    
    if tab == 'all' or tab == 'users':
        users = User.query.filter(
            (User.username.ilike(f'%{query}%')) | 
            (User.real_name.ilike(f'%{query}%'))
        ).all()
        
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'real_name': user.real_name,
                'profile_pic': user.profile_pic
            })
        
        results['users'] = users_data
    
    if tab == 'all' or tab == 'groups':
        groups = Group.query.filter(Group.name.ilike(f'%{query}%')).all()
        
        groups_data = []
        for group in groups:
            groups_data.append({
                'id': group.id,
                'name': group.name,
                'profile_pic': group.profile_pic,
                'members_count': group.members.count()
            })
        
        results['groups'] = groups_data
    
    if tab == 'all' or tab == 'posts':
        posts = Post.query.filter(
            (Post.content.ilike(f'%{query}%')) & 
            (Post.is_private == False)
        ).all()
        
        posts_data = []
        for post in posts:
            posts_data.append({
                'id': post.id,
                'content': post.content,
                'media_url': post.media_url,
                'media_type': post.media_type,
                'user': {
                    'id': post.author.id,
                    'username': post.author.username,
                    'real_name': post.author.real_name,
                    'profile_pic': post.author.profile_pic
                },
                'created_at': post.created_at.isoformat(),
                'likes_count': post.likes.count()
            })
        
        results['posts'] = posts_data
    
    if tab == 'all' or tab == 'reels':
        reels = Reel.query.filter(Reel.content.ilike(f'%{query}%')).all()
        
        reels_data = []
        for reel in reels:
            reels_data.append({
                'id': reel.id,
                'content': reel.content,
                'media_url': reel.media_url,
                'user': {
                    'id': reel.author.id,
                    'username': reel.author.username,
                    'real_name': reel.author.real_name,
                    'profile_pic': reel.author.profile_pic
                },
                'created_at': reel.created_at.isoformat(),
                'likes_count': reel.likes.count()
            })
        
        results['reels'] = reels_data
    
    return jsonify(results)

@app.route('/api/notifications')
@login_required
def api_notifications():
    user_id = session['user_id']
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(50).all()
    
    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'content': notification.content,
            'type': notification.type,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat()
        })
    
    return jsonify({'notifications': notifications_data})

@app.route('/api/admin/dashboard')
@admin_required
def api_admin_dashboard():
    # Get all users
    users = User.query.all()
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'real_name': user.real_name,
            'email': user.email,
            'created_at': user.created_at.isoformat(),
            'is_admin': user.is_admin,
            'posts_count': user.posts.count(),
            'followers_count': user.followers.count(),
            'following_count': user.following.count()
        })
    
    # Get all groups
    groups = Group.query.all()
    groups_data = []
    for group in groups:
        groups_data.append({
            'id': group.id,
            'name': group.name,
            'created_by': group.created_by,
            'created_at': group.created_at.isoformat(),
            'members_count': group.members.count(),
            'messages_count': group.messages.count()
        })
    
    # Get pending reports
    reports = Report.query.filter_by(status='pending').all()
    reports_data = []
    for report in reports:
        reports_data.append({
            'id': report.id,
            'reporter': User.query.get(report.reporter_id).username,
            'reason': report.reason,
            'created_at': report.created_at.isoformat()
        })
    
    # Get statistics
    total_users = User.query.count()
    total_posts = Post.query.count()
    total_reels = Reel.query.count()
    total_groups = Group.query.count()
    total_messages = Message.query.count()
    
    return jsonify({
        'users': users_data,
        'groups': groups_data,
        'reports': reports_data,
        'stats': {
            'total_users': total_users,
            'total_posts': total_posts,
            'total_reels': total_reels,
            'total_groups': total_groups,
            'total_messages': total_messages
        }
    })

# Action routes (follow, like, comment, etc.)
@app.route('/api/follow/<int:user_id>', methods=['POST'])
@login_required
def api_follow(user_id):
    current_user_id = session['user_id']
    
    if current_user_id == user_id:
        return jsonify({'success': False, 'message': 'Cannot follow yourself'})
    
    # Check if already following
    existing_follow = Follow.query.filter_by(follower_id=current_user_id, followed_id=user_id).first()
    if existing_follow:
        return jsonify({'success': False, 'message': 'Already following'})
    
    # Create follow relationship
    follow = Follow(follower_id=current_user_id, followed_id=user_id)
    db.session.add(follow)
    
    # Create notification
    followed_user = User.query.get(user_id)
    notification = Notification(
        user_id=user_id,
        content=f'{User.query.get(current_user_id).username} started following you',
        type='follow'
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Followed successfully'})

@app.route('/api/unfollow/<int:user_id>', methods=['POST'])
@login_required
def api_unfollow(user_id):
    current_user_id = session['user_id']
    
    follow = Follow.query.filter_by(follower_id=current_user_id, followed_id=user_id).first()
    if not follow:
        return jsonify({'success': False, 'message': 'Not following this user'})
    
    db.session.delete(follow)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Unfollowed successfully'})

@app.route('/api/like/post/<int:post_id>', methods=['POST'])
@login_required
def api_like_post(post_id):
    current_user_id = session['user_id']
    
    # Check if already liked
    existing_like = Like.query.filter_by(user_id=current_user_id, post_id=post_id).first()
    if existing_like:
        return jsonify({'success': False, 'message': 'Already liked'})
    
    # Create like
    like = Like(user_id=current_user_id, post_id=post_id)
    db.session.add(like)
    
    # Create notification
    post = Post.query.get(post_id)
    if post.user_id != current_user_id:  # Don't notify yourself
        notification = Notification(
            user_id=post.user_id,
            content=f'{User.query.get(current_user_id).username} liked your post',
            type='like',
            reference_id=post_id
        )
        db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Liked successfully'})

@app.route('/api/unlike/post/<int:post_id>', methods=['POST'])
@login_required
def api_unlike_post(post_id):
    current_user_id = session['user_id']
    
    like = Like.query.filter_by(user_id=current_user_id, post_id=post_id).first()
    if not like:
        return jsonify({'success': False, 'message': 'Not liked'})
    
    db.session.delete(like)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Unliked successfully'})

@app.route('/api/comment/post/<int:post_id>', methods=['POST'])
@login_required
def api_comment_post(post_id):
    current_user_id = session['user_id']
    content = request.form.get('content')
    
    if not content:
        return jsonify({'success': False, 'message': 'Comment cannot be empty'})
    
    # Create comment
    comment = Comment(user_id=current_user_id, post_id=post_id, content=content)
    db.session.add(comment)
    
    # Create notification
    post = Post.query.get(post_id)
    if post.user_id != current_user_id:  # Don't notify yourself
        notification = Notification(
            user_id=post.user_id,
            content=f'{User.query.get(current_user_id).username} commented on your post: {content[:50]}...',
            type='comment',
            reference_id=post_id
        )
        db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Commented successfully'})

@app.route('/api/create-post', methods=['POST'])
@login_required
def api_create_post():
    current_user_id = session['user_id']
    content = request.form.get('content')
    is_private = request.form.get('is_private') == 'true'
    
    if not content:
        return jsonify({'success': False, 'message': 'Content cannot be empty'})
    
    # Handle file upload
    media_url = None
    media_type = None
    if 'media' in request.files:
        file = request.files['media']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            media_url = unique_filename
            
            # Determine media type
            ext = filename.rsplit('.', 1)[1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif']:
                media_type = 'image'
            elif ext in ['mp4', 'mov', 'avi']:
                media_type = 'video'
    
    # Create post
    post = Post(
        user_id=current_user_id,
        content=content,
        media_url=media_url,
        media_type=media_type,
        is_private=is_private
    )
    db.session.add(post)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Post created successfully'})

@app.route('/api/create-reel', methods=['POST'])
@login_required
def api_create_reel():
    current_user_id = session['user_id']
    content = request.form.get('content', '')
    
    # Handle file upload
    if 'media' not in request.files:
        return jsonify({'success': False, 'message': 'Media file is required'})
    
    file = request.files['media']
    if not file or not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Invalid media file'})
    
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
    
    # Create reel
    reel = Reel(
        user_id=current_user_id,
        content=content,
        media_url=unique_filename
    )
    db.session.add(reel)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Reel created successfully'})

@app.route('/api/send-message', methods=['POST'])
@login_required
def api_send_message():
    current_user_id = session['user_id']
    receiver_id = request.form.get('receiver_id')
    group_id = request.form.get('group_id')
    content = request.form.get('content')
    
    if not content and 'media' not in request.files:
        return jsonify({'success': False, 'message': 'Message cannot be empty'})
    
    # Handle file upload
    media_url = None
    media_type = None
    if 'media' in request.files:
        file = request.files['media']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            media_url = unique_filename
            
            # Determine media type
            ext = filename.rsplit('.', 1)[1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif']:
                media_type = 'image'
            elif ext in ['mp4', 'mov', 'avi']:
                media_type = 'video'
            elif ext in ['mp3', 'wav', 'ogg']:
                media_type = 'audio'
    
    # Create message
    message = Message(
        sender_id=current_user_id,
        receiver_id=receiver_id if not group_id else None,
        group_id=group_id,
        content=content,
        media_url=media_url,
        media_type=media_type
    )
    db.session.add(message)
    
    # Create notification if it's a direct message
    if receiver_id and int(receiver_id) != current_user_id:
        notification = Notification(
            user_id=receiver_id,
            content=f'{User.query.get(current_user_id).username} sent you a message',
            type='message'
        )
        db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Message sent successfully'})

@app.route('/api/create-group', methods=['POST'])
@login_required
def api_create_group():
    current_user_id = session['user_id']
    name = request.form.get('name')
    description = request.form.get('description', '')
    
    if not name:
        return jsonify({'success': False, 'message': 'Group name is required'})
    
    # Generate unique link
    import random
    import string
    unique_link = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    
    # Handle file upload
    profile_pic = 'default_group.png'
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif'}):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            profile_pic = unique_filename
    
    # Create group
    group = Group(
        name=name,
        description=description,
        profile_pic=profile_pic,
        unique_link=unique_link,
        created_by=current_user_id
    )
    db.session.add(group)
    db.session.flush()  # Get the group ID
    
    # Add creator as admin member
    member = GroupMember(
        user_id=current_user_id,
        group_id=group.id,
        is_admin=True
    )
    db.session.add(member)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Group created successfully', 'group_id': group.id})

@app.route('/api/join-group/<link>', methods=['POST'])
@login_required
def api_join_group(link):
    current_user_id = session['user_id']
    
    group = Group.query.filter_by(unique_link=link).first()
    if not group:
        return jsonify({'success': False, 'message': 'Group not found'})
    
    # Check if already a member
    existing_member = GroupMember.query.filter_by(user_id=current_user_id, group_id=group.id).first()
    if existing_member:
        return jsonify({'success': False, 'message': 'Already a member'})
    
    # Check if group requires approval
    if group.approve_new_members:
        # Create a join request (would need a separate model)
        return jsonify({'success': False, 'message': 'Join request sent for approval'})
    else:
        # Add as member directly
        member = GroupMember(
            user_id=current_user_id,
            group_id=group.id,
            is_admin=False
        )
        db.session.add(member)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Joined group successfully'})

@app.route('/api/update-profile', methods=['POST'])
@login_required
def api_update_profile():
    current_user_id = session['user_id']
    user = User.query.get(current_user_id)
    
    # Update basic info
    user.real_name = request.form.get('real_name', user.real_name)
    user.bio = request.form.get('bio', user.bio)
    user.email = request.form.get('email', user.email)
    
    # Update additional profile info
    user.date_of_birth = request.form.get('date_of_birth', user.date_of_birth)
    user.gender = request.form.get('gender', user.gender)
    user.pronouns = request.form.get('pronouns', user.pronouns)
    user.work = request.form.get('work', user.work)
    user.education = request.form.get('education', user.education)
    user.location = request.form.get('location', user.location)
    user.phone_number = request.form.get('phone_number', user.phone_number)
    user.website = request.form.get('website', user.website)
    user.relationship = request.form.get('relationship', user.relationship)
    user.spouse = request.form.get('spouse', user.spouse)
    
    # Handle profile picture upload
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif'}):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            user.profile_pic = unique_filename
    
    # Update privacy settings
    user.is_private = request.form.get('is_private') == 'true'
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Profile updated successfully'})

@app.route('/api/report', methods=['POST'])
@login_required
def api_report():
    current_user_id = session['user_id']
    reason = request.form.get('reason')
    reported_user_id = request.form.get('reported_user_id')
    reported_post_id = request.form.get('reported_post_id')
    reported_group_id = request.form.get('reported_group_id')
    
    if not reason:
        return jsonify({'success': False, 'message': 'Reason is required'})
    
    if not reported_user_id and not reported_post_id and not reported_group_id:
        return jsonify({'success': False, 'message': 'Must report a user, post, or group'})
    
    # Create report
    report = Report(
        reporter_id=current_user_id,
        reported_user_id=reported_user_id,
        reported_post_id=reported_post_id,
        reported_group_id=reported_group_id,
        reason=reason
    )
    db.session.add(report)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Report submitted successfully'})

# Admin routes
@app.route('/api/admin/delete-user/<int:user_id>', methods=['POST'])
@admin_required
def api_admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if user_id == session['user_id']:
        return jsonify({'success': False, 'message': 'Cannot delete yourself'})
    
    # Delete user's data (in a real app, this would be more comprehensive)
    # For simplicity, we'll just delete the user
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User deleted successfully'})

@app.route('/api/admin/delete-post/<int:post_id>', methods=['POST'])
@admin_required
def api_admin_delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    db.session.delete(post)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Post deleted successfully'})

@app.route('/api/admin/delete-group/<int:group_id>', methods=['POST'])
@admin_required
def api_admin_delete_group(group_id):
    group = Group.query.get_or_404(group_id)
    
    db.session.delete(group)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Group deleted successfully'})

@app.route('/api/admin/resolve-report/<int:report_id>', methods=['POST'])
@admin_required
def api_admin_resolve_report(report_id):
    report = Report.query.get_or_404(report_id)
    
    report.status = 'resolved'
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Report resolved successfully'})

# Initialize database
@app.before_first_request
def create_tables():
    db.create_all()
    
    # Create admin user if not exists
    admin_username = app.config.get('ADMIN_USERNAME', 'Henry')
    admin_password = app.config.get('ADMIN_PASS', 'Dec@2003')
    
    if not User.query.filter_by(username=admin_username).first():
        admin_user = User(
            username=admin_username,
            password=generate_password_hash(admin_password),
            real_name='Admin User',
            unique_key='ADMN',
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
