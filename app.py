from flask import Flask, request, jsonify, session, send_from_directory, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
import random
import string
import datetime
from sqlalchemy import and_, or_, func, text
from collections import Counter

app = Flask(__name__, static_folder='static')
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
    status = db.Column(db.String(20), default='pending')  # pending, accepted
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # post, reel, story
    description = db.Column(db.Text)
    media_url = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    visibility = db.Column(db.String(20), default='public')  # public, friends

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
    reported_type = db.Column(db.String(20), nullable=False)  # user, post, group
    reported_id = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

@app.before_first_request
def initialize_db():
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
        return jsonify({'error': 'Invalid password'}), 400
    hashed = bcrypt.generate_password_hash(password).decode('utf-8')
    key = generate_unique_key()
    while User.query.filter_by(unique_key=key).first():
        key = generate_unique_key()
    user = User(username=username, password_hash=hashed, unique_key=key, real_name=username)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Registered', 'unique_key': key})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    identifier = data.get('identifier')
    password = data.get('password')
    user = User.query.filter_by(username=identifier).first()
    if not user:
        user = User.query.filter_by(email=identifier).first()
    if user and not user.is_banned and bcrypt.check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        return jsonify({'message': 'Logged in', 'is_admin': user.is_admin})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('reset_user_id', None)
    return jsonify({'message': 'Logged out'})

@app.route('/api/forgot', methods=['POST'])
def forgot():
    data = request.json
    username = data.get('username')
    key = data.get('unique_key')
    user = User.query.filter_by(username=username, unique_key=key).first()
    if user:
        session['reset_user_id'] = user.id
        return jsonify({'message': 'Verified'})
    return jsonify({'error': 'Invalid details'}), 400

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    if 'reset_user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    data = request.json
    password = data.get('password')
    if len(password) < 6 or not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password) or not any(not c.isalnum() for c in password):
        return jsonify({'error': 'Invalid password'}), 400
    hashed = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User.query.get(session['reset_user_id'])
    user.password_hash = hashed
    db.session.commit()
    session.pop('reset_user_id', None)
    return jsonify({'message': 'Password reset'})

@app.route('/api/change_password', methods=['POST'])
def change_password():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    old_pass = data.get('old_password')
    new_pass = data.get('new_password')
    if not bcrypt.check_password_hash(user.password_hash, old_pass):
        return jsonify({'error': 'Invalid old password'}), 400
    if len(new_pass) < 6 or not any(c.isdigit() for c in new_pass) or not any(c.isalpha() for c in new_pass) or not any(not c.isalnum() for c in new_pass):
        return jsonify({'error': 'Invalid new password'}), 400
    user.password_hash = bcrypt.generate_password_hash(new_pass).decode('utf-8')
    db.session.commit()
    return jsonify({'message': 'Password changed'})

@app.route('/api/home', methods=['GET'])
def home():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    # Get mutual friends IDs
    following_sub = db.session.query(Follow.followed_id).filter_by(follower_id=user.id, status='accepted').subquery()
    friends_ids = [row[0] for row in db.session.query(Follow.follower_id).filter(and_(Follow.followed_id == user.id, Follow.status == 'accepted', Follow.follower_id.in_(following_sub)))]
    # Stories from friends
    stories = Post.query.filter_by(type='story').filter(Post.user_id.in_(friends_ids)).order_by(Post.timestamp.desc()).all()
    stories_data = [{'id': s.id, 'user': s.user.username, 'media_url': s.media_url, 'description': s.description} for s in stories]
    return jsonify({'stories': stories_data})

@app.route('/api/posts', methods=['GET'])
def get_posts():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    page = request.args.get('page', 1, type=int)
    per_page = 10
    following_ids = [f.followed_id for f in Follow.query.filter_by(follower_id=user.id, status='accepted').all()]
    posts = Post.query.filter_by(type='post').filter(or_(Post.user_id.in_(following_ids), Post.user_id == user.id)).order_by(Post.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    posts_data = []
    for p in posts.items:
        post_user = User.query.get(p.user_id)
        is_own = p.user_id == user.id
        likes_count = Like.query.filter_by(post_id=p.id).count()
        is_liked = bool(Like.query.filter_by(post_id=p.id, user_id=user.id).first())
        comments_count = Comment.query.filter_by(post_id=p.id).count()
        is_following = bool(Follow.query.filter_by(follower_id=user.id, followed_id=p.user_id, status='accepted').first())
        posts_data.append({
            'id': p.id,
            'user': {'id': post_user.id, 'username': post_user.username, 'real_name': post_user.real_name, 'profile_pic': post_user.profile_pic_url},
            'description': p.description,
            'media_url': p.media_url,
            'timestamp': p.timestamp.isoformat(),
            'likes': likes_count,
            'is_liked': is_liked,
            'comments': comments_count,
            'views': p.views,
            'is_own': is_own,
            'is_following': is_following
        })
    return jsonify({'posts': posts_data, 'has_next': posts.has_next})

@app.route('/api/reels', methods=['GET'])
def get_reels():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    page = request.args.get('page', 1, type=int)
    per_page = 10
    following_ids = [f.followed_id for f in Follow.query.filter_by(follower_id=user.id, status='accepted').all()]
    reels = Post.query.filter_by(type='reel').filter(or_(Post.user_id.in_(following_ids), Post.user_id == user.id)).order_by(Post.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    reels_data = []
    for r in reels.items:
        reel_user = User.query.get(r.user_id)
        is_own = r.user_id == user.id
        likes_count = Like.query.filter_by(post_id=r.id).count()
        is_liked = bool(Like.query.filter_by(post_id=r.id, user_id=user.id).first())
        comments_count = Comment.query.filter_by(post_id=r.id).count()
        is_following = bool(Follow.query.filter_by(follower_id=user.id, followed_id=r.user_id, status='accepted').first())
        reels_data.append({
            'id': r.id,
            'user': {'id': reel_user.id, 'username': reel_user.username, 'real_name': reel_user.real_name, 'profile_pic': reel_user.profile_pic_url},
            'description': r.description,
            'media_url': r.media_url,
            'timestamp': r.timestamp.isoformat(),
            'likes': likes_count,
            'is_liked': is_liked,
            'comments': comments_count,
            'views': r.views,
            'is_own': is_own,
            'is_following': is_following
        })
    return jsonify({'reels': reels_data, 'has_next': reels.has_next})

@app.route('/api/stories', methods=['GET'])
def get_stories():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    # Same as home stories
    following_sub = db.session.query(Follow.followed_id).filter_by(follower_id=user.id, status='accepted').subquery()
    friends_ids = [row[0] for row in db.session.query(Follow.follower_id).filter(and_(Follow.followed_id == user.id, Follow.status == 'accepted', Follow.follower_id.in_(following_sub)))]
    stories = Post.query.filter_by(type='story').filter(Post.user_id.in_(friends_ids)).order_by(Post.timestamp.desc()).all()
    stories_data = [{'id': s.id, 'user': s.user.username, 'media_url': s.media_url, 'description': s.description, 'timestamp': s.timestamp.isoformat()} for s in stories]
    return jsonify({'stories': stories_data})

@app.route('/api/story/<int:story_id>', methods=['GET'])
def view_story(story_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    story = Post.query.get_or_404(story_id)
    # Check if from friend
    if story.user_id not in get_friends_ids(user.id):
        return jsonify({'error': 'Not authorized'}), 403
    story.views += 1
    db.session.commit()
    return jsonify({'id': story.id, 'media_url': story.media_url, 'description': story.description, 'user': story.user.username})

def get_friends_ids(user_id):
    following_sub = db.session.query(Follow.followed_id).filter_by(follower_id=user_id, status='accepted').subquery()
    friends_ids = [row[0] for row in db.session.query(Follow.follower_id).filter(and_(Follow.followed_id == user_id, Follow.status == 'accepted', Follow.follower_id.in_(following_sub)))]
    return friends_ids

@app.route('/api/create', methods=['POST'])
def create_content():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    content_type = request.form.get('type')
    if content_type not in ['post', 'reel', 'story']:
        return jsonify({'error': 'Invalid type'}), 400
    description = request.form.get('description')
    visibility = request.form.get('visibility', 'public')
    media_url = None
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            media_url = '/static/uploads/' + filename
    post = Post(user_id=user.id, type=content_type, description=description, media_url=media_url, visibility=visibility)
    db.session.add(post)
    db.session.commit()
    # Notify followers if post/reel
    if content_type in ['post', 'reel']:
        followers = Follow.query.filter_by(followed_id=user.id, status='accepted').all()
        for f in followers:
            notif = Notification(user_id=f.follower_id, type='new_post', from_user_id=user.id, content_id=post.id, message=f'{user.username} posted a new {content_type}')
            db.session.add(notif)
        db.session.commit()
    return jsonify({'message': 'Created', 'id': post.id})

@app.route('/api/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=user.id, post_id=post_id).first()
    if like:
        db.session.delete(like)
        action = 'unliked'
    else:
        like = Like(user_id=user.id, post_id=post_id)
        db.session.add(like)
        action = 'liked'
        if post.user_id != user.id:
            notif = Notification(user_id=post.user_id, type='like', from_user_id=user.id, content_id=post_id, message=f'{user.username} liked your post')
            db.session.add(notif)
    db.session.commit()
    return jsonify({'message': action})

@app.route('/api/comment/<int:post_id>', methods=['POST'])
def comment_post(post_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    post = Post.query.get_or_404(post_id)
    text = request.json.get('text')
    if not text:
        return jsonify({'error': 'Missing text'}), 400
    comment = Comment(user_id=user.id, post_id=post_id, text=text)
    db.session.add(comment)
    if post.user_id != user.id:
        notif = Notification(user_id=post.user_id, type='comment', from_user_id=user.id, content_id=post_id, message=f'{user.username} commented on your post')
        db.session.add(notif)
    db.session.commit()
    return jsonify({'message': 'Commented'})

@app.route('/api/repost/<int:post_id>', methods=['POST'])
def repost(post_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    post = Post.query.get_or_404(post_id)
    if post.user_id == user.id:
        return jsonify({'error': 'Cannot repost own'}), 400
    repost = Repost(user_id=user.id, original_post_id=post_id)
    db.session.add(repost)
    if post.user_id != user.id:
        notif = Notification(user_id=post.user_id, type='repost', from_user_id=user.id, content_id=post_id, message=f'{user.username} reposted your post')
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
        action = 'unsaved'
    else:
        save = Save(user_id=user.id, post_id=post_id)
        db.session.add(save)
        action = 'saved'
    db.session.commit()
    return jsonify({'message': action})

@app.route('/api/report/<int:reported_id>', methods=['POST'])
def report(reported_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    reported_type = request.json.get('type')  # post, user, group
    description = request.json.get('description')
    report = Report(reporter_id=user.id, reported_type=reported_type, reported_id=reported_id, description=description)
    db.session.add(report)
    db.session.commit()
    return jsonify({'message': 'Reported'})

@app.route('/api/hide/<int:post_id>', methods=['POST'])
def hide_post(post_id):
    # For simplicity, assume client-side hide, or add a Hide model if needed
    return jsonify({'message': 'Hidden'})

@app.route('/api/block/user/<int:user_id>', methods=['POST'])
def block_user(user_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if user_id == user.id:
        return jsonify({'error': 'Cannot block self'}), 400
    # Remove follows
    Follow.query.filter_by(follower_id=user.id, followed_id=user_id).delete()
    Follow.query.filter_by(follower_id=user_id, followed_id=user.id).delete()
    # Add to blocked list? For now, assume blocking means no follow/interaction
    db.session.commit()
    return jsonify({'message': 'Blocked'})

@app.route('/api/friends/followers', methods=['GET'])
def get_followers():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    followers = Follow.query.filter_by(followed_id=user.id, status='accepted').all()
    data = []
    for f in followers:
        fol_user = User.query.get(f.follower_id)
        mutual = get_mutual_count(user.id, f.follower_id)
        data.append({'id': fol_user.id, 'real_name': fol_user.real_name, 'profile_pic': fol_user.profile_pic_url, 'mutual': mutual})
    return jsonify({'followers': data, 'count': len(data)})

def get_mutual_count(user1_id, user2_id):
    user1_following = set([f.followed_id for f in Follow.query.filter_by(follower_id=user1_id, status='accepted').all()])
    user2_following = set([f.followed_id for f in Follow.query.filter_by(follower_id=user2_id, status='accepted').all()])
    return len(user1_following.intersection(user2_following))

@app.route('/api/friends/following', methods=['GET'])
def get_following():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    following = Follow.query.filter_by(follower_id=user.id, status='accepted').all()
    data = []
    for f in following:
        fol_user = User.query.get(f.followed_id)
        mutual = get_mutual_count(user.id, f.followed_id)
        data.append({'id': fol_user.id, 'real_name': fol_user.real_name, 'profile_pic': fol_user.profile_pic_url, 'mutual': mutual})
    return jsonify({'following': data, 'count': len(data)})

@app.route('/api/friends/friends', methods=['GET'])
def get_friends():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    friends_ids = get_friends_ids(user.id)
    data = []
    for fid in friends_ids:
        f_user = User.query.get(fid)
        mutual = get_mutual_count(user.id, fid)
        data.append({'id': f_user.id, 'real_name': f_user.real_name, 'profile_pic': f_user.profile_pic_url, 'mutual': mutual})
    return jsonify({'friends': data, 'count': len(data)})

@app.route('/api/friends/requests', methods=['GET'])
def get_requests():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    requests = Follow.query.filter_by(followed_id=user.id, status='pending').all()
    data = []
    for r in requests:
        req_user = User.query.get(r.follower_id)
        mutual = get_mutual_count(user.id, r.follower_id)
        data.append({'id': req_user.id, 'real_name': req_user.real_name, 'profile_pic': req_user.profile_pic_url, 'mutual': mutual})
    return jsonify({'requests': data, 'count': len(data)})

@app.route('/api/friends/suggested', methods=['GET'])
def get_suggested():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    following_ids = set([f.followed_id for f in Follow.query.filter_by(follower_id=user.id, status='accepted').all()])
    followers_ids = set([f.follower_id for f in Follow.query.filter_by(followed_id=user.id, status='accepted').all()])
    excluded = following_ids.union(followers_ids, {user.id})
    suggestions = Counter()
    for fid in following_ids:
        their_following = [f.followed_id for f in Follow.query.filter_by(follower_id=fid, status='accepted').all()]
        for tf in their_following:
            if tf not in excluded:
                suggestions[tf] += 1
    top_sug = suggestions.most_common(20)
    data = []
    for sid, count in top_sug:
        s_user = User.query.get(sid)
        data.append({'id': s_user.id, 'real_name': s_user.real_name, 'profile_pic': s_user.profile_pic_url, 'mutual': count})
    return jsonify({'suggested': data})

@app.route('/api/follow/<int:user_id>', methods=['POST'])
def follow(user_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if user_id == user.id:
        return jsonify({'error': 'Cannot follow self'}), 400
    existing = Follow.query.filter_by(follower_id=user.id, followed_id=user_id).first()
    if existing:
        if existing.status == 'accepted':
            return jsonify({'error': 'Already following'}), 400
        else:
            existing.status = 'pending'  # Re-request
    else:
        follow = Follow(follower_id=user.id, followed_id=user_id, status='pending')
        db.session.add(follow)
    notif = Notification(user_id=user_id, type='friend_request', from_user_id=user.id, message=f'{user.username} sent a friend request')
    db.session.add(notif)
    db.session.commit()
    return jsonify({'message': 'Request sent'})

@app.route('/api/unfollow/<int:user_id>', methods=['POST'])
def unfollow(user_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    follow = Follow.query.filter_by(follower_id=user.id, followed_id=user_id).first()
    if follow:
        db.session.delete(follow)
        db.session.commit()
    return jsonify({'message': 'Unfollowed'})

@app.route('/api/accept_request/<int:user_id>', methods=['POST'])
def accept_request(user_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    request_follow = Follow.query.filter_by(follower_id=user_id, followed_id=user.id, status='pending').first()
    if request_follow:
        request_follow.status = 'accepted'
        notif = Notification(user_id=user_id, type='request_accepted', from_user_id=user.id, message=f'{user.username} accepted your request')
        db.session.add(notif)
        db.session.commit()
        return jsonify({'message': 'Accepted'})
    return jsonify({'error': 'No request'}), 400

@app.route('/api/decline_request/<int:user_id>', methods=['POST'])
def decline_request(user_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    request_follow = Follow.query.filter_by(follower_id=user_id, followed_id=user.id, status='pending').first()
    if request_follow:
        db.session.delete(request_follow)
        db.session.commit()
        return jsonify({'message': 'Declined'})
    return jsonify({'error': 'No request'}), 400

@app.route('/api/inbox/chats', methods=['GET'])
def get_chats():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    # Get distinct chats
    chats_query = db.session.query(
        func.case(when=(PrivateMessage.sender_id == user.id, PrivateMessage.receiver_id), else_=PrivateMessage.sender_id).label('other_id'),
        func.max(PrivateMessage.timestamp).label('last_time')
    ).filter(or_(PrivateMessage.sender_id == user.id, PrivateMessage.receiver_id == user.id)).group_by('other_id').order_by(text('last_time desc'))
    data = []
    for other_id, last_time in chats_query:
        other_user = User.query.get(other_id)
        last_msg = PrivateMessage.query.filter(or_(and_(PrivateMessage.sender_id == user.id, PrivateMessage.receiver_id == other_id), and_(PrivateMessage.sender_id == other_id, PrivateMessage.receiver_id == user.id))).order_by(PrivateMessage.timestamp.desc()).first()
        unread = PrivateMessage.query.filter_by(receiver_id=user.id, sender_id=other_id, is_read=False).count()
        data.append({
            'other_id': other_id,
            'real_name': other_user.real_name,
            'profile_pic': other_user.profile_pic_url,
            'last_msg_snippet': last_msg.text[:50] if last_msg else '',
            'unread': unread,
            'last_time': last_time.isoformat() if last_time else ''
        })
    return jsonify({'chats': data, 'count': len(data)})

@app.route('/api/inbox/groups', methods=['GET'])
def get_group_chats():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    groups = GroupMember.query.filter_by(user_id=user.id).all()
    data = []
    for gm in groups:
        group = Group.query.get(gm.group_id)
        last_msg = GroupMessage.query.filter_by(group_id=gm.group_id).order_by(GroupMessage.timestamp.desc()).first()
        # Unread: simplistic, assume all read for now, or add read per user if needed
        unread = 0
        data.append({
            'group_id': group.id,
            'name': group.name,
            'profile_pic': group.profile_pic_url,
            'last_msg_snippet': last_msg.text[:50] if last_msg else '',
            'unread': unread,
            'last_time': last_msg.timestamp.isoformat() if last_msg else ''
        })
    return jsonify({'groups': data, 'count': len(data)})

@app.route('/api/messages/private/<int:other_id>', methods=['GET', 'POST'])
def private_messages(other_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'POST':
        text = request.json.get('text')
        media_url = None
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                media_url = '/static/uploads/' + filename
        msg = PrivateMessage(sender_id=user.id, receiver_id=other_id, text=text, media_url=media_url)
        db.session.add(msg)
        notif = Notification(user_id=other_id, type='message', from_user_id=user.id, message=f'{user.username} sent a message')
        db.session.add(notif)
        db.session.commit()
        return jsonify({'message': 'Sent'})
    # GET
    messages = PrivateMessage.query.filter(or_(and_(PrivateMessage.sender_id == user.id, PrivateMessage.receiver_id == other_id), and_(PrivateMessage.sender_id == other_id, PrivateMessage.receiver_id == user.id))).order_by(PrivateMessage.timestamp.asc()).all()
    data = [{'id': m.id, 'sender_id': m.sender_id, 'text': m.text, 'media_url': m.media_url, 'timestamp': m.timestamp.isoformat()} for m in messages]
    # Mark read
    PrivateMessage.query.filter_by(receiver_id=user.id, sender_id=other_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'messages': data})

@app.route('/api/messages/group/<int:group_id>', methods=['GET', 'POST'])
def group_messages(group_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first():
        return jsonify({'error': 'Not member'}), 403
    gm = GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first()
    group = Group.query.get(group_id)
    is_admin = gm.is_admin
    can_send = group.allow_nonadmin_messages or is_admin
    if request.method == 'POST':
        if not can_send:
            return jsonify({'error': 'Cannot send'}), 403
        text = request.json.get('text')
        media_url = None
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                media_url = '/static/uploads/' + filename
        msg = GroupMessage(group_id=group_id, sender_id=user.id, text=text, media_url=media_url)
        db.session.add(msg)
        # Notify members? For efficiency, client poll
        db.session.commit()
        return jsonify({'message': 'Sent'})
    messages = GroupMessage.query.filter_by(group_id=group_id).order_by(GroupMessage.timestamp.asc()).all()
    data = [{'id': m.id, 'sender_id': m.sender_id, 'sender_name': User.query.get(m.sender_id).username, 'text': m.text, 'media_url': m.media_url, 'timestamp': m.timestamp.isoformat()} for m in messages]
    return jsonify({'messages': data})

@app.route('/api/create_group', methods=['POST'])
def create_group():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    name = request.form.get('name')
    description = request.form.get('description')
    allow_nonadmin_messages = request.form.get('allow_nonadmin_messages', True) == 'true'
    allow_nonadmin_add_members = request.form.get('allow_nonadmin_add_members', True) == 'true'
    approve_new_members = request.form.get('approve_new_members', False) == 'true'
    profile_pic_url = None
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            profile_pic_url = '/static/uploads/' + filename
    group = Group(name=name, description=description, creator_id=user.id, profile_pic_url=profile_pic_url,
                  allow_nonadmin_messages=allow_nonadmin_messages, allow_nonadmin_add_members=allow_nonadmin_add_members, approve_new_members=approve_new_members)
    db.session.add(group)
    db.session.commit()
    member = GroupMember(group_id=group.id, user_id=user.id, is_admin=True)
    db.session.add(member)
    db.session.commit()
    return jsonify({'message': 'Group created', 'id': group.id})

@app.route('/api/group/<int:group_id>', methods=['GET'])
def get_group(group_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    group = Group.query.get_or_404(group_id)
    is_member = bool(GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first())
    is_admin = False
    if is_member:
        is_admin = GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first().is_admin
    members = [m.user_id for m in GroupMember.query.filter_by(group_id=group_id).all()]
    members_data = [{'id': m, 'name': User.query.get(m).real_name} for m in members[:10]]  # First 10
    permissions = {
        'allow_nonadmin_messages': group.allow_nonadmin_messages,
        'allow_nonadmin_add_members': group.allow_nonadmin_add_members,
        'approve_new_members': group.approve_new_members
    }
    # Media, links, docs: simplistic, get from messages
    media = [m.media_url for m in GroupMessage.query.filter_by(group_id=group_id).filter(GroupMessage.media_url != None).all()]
    data = {
        'id': group.id,
        'name': group.name,
        'profile_pic': group.profile_pic_url,
        'description': group.description,
        'members_count': len(members),
        'members': members_data,
        'is_member': is_member,
        'is_admin': is_admin,
        'permissions': permissions if is_admin or group.creator_id == user.id else None,
        'media': media,
        # Add links/docs if parsed from text
    }
    return jsonify(data)

@app.route('/api/group/join/<int:group_id>', methods=['POST'])
def join_group(group_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    group = Group.query.get_or_404(group_id)
    if GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first():
        return jsonify({'error': 'Already member'}), 400
    if group.approve_new_members:
        # Send request to admins, but for simple, assume auto
        pass
    member = GroupMember(group_id=group_id, user_id=user.id, is_admin=False)
    db.session.add(member)
    notif = Notification(user_id=group.creator_id, type='group_join', content_id=group_id, message=f'{user.username} joined {group.name}')
    db.session.add(notif)
    db.session.commit()
    return jsonify({'message': 'Joined'})

@app.route('/api/group/leave/<int:group_id>', methods=['POST'])
def leave_group(group_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    gm = GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first()
    if not gm:
        return jsonify({'error': 'Not member'}), 400
    if group.creator_id == user.id:
        # Pass admin to random
        other_admins = GroupMember.query.filter_by(group_id=group_id, is_admin=True).filter(GroupMember.user_id != user.id).first()
        if other_admins:
            # Pass to one
            pass
        else:
            # Delete group or pass to random member
            other_member = GroupMember.query.filter_by(group_id=group_id).filter(GroupMember.user_id != user.id).first()
            if other_member:
                other_member.is_admin = True
            else:
                db.session.delete(Group.query.get(group_id))
    db.session.delete(gm)
    db.session.commit()
    return jsonify({'message': 'Left'})

@app.route('/api/group/add_member/<int:group_id>/<int:new_user_id>', methods=['POST'])
def add_group_member(group_id, new_user_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    gm = GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first()
    if not gm:
        return jsonify({'error': 'Not member'}), 403
    group = Group.query.get(group_id)
    if not group.allow_nonadmin_add_members and not gm.is_admin:
        return jsonify({'error': 'Cannot add'}), 403
    if GroupMember.query.filter_by(group_id=group_id, user_id=new_user_id).first():
        return jsonify({'error': 'Already member'}), 400
    member = GroupMember(group_id=group_id, user_id=new_user_id, is_admin=False)
    db.session.add(member)
    notif = Notification(user_id=new_user_id, type='group_invite', content_id=group_id, message=f'You were added to {group.name}')
    db.session.add(notif)
    db.session.commit()
    return jsonify({'message': 'Added'})

@app.route('/api/group/permissions/<int:group_id>', methods=['POST'])
def update_group_permissions(group_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    gm = GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first()
    if not gm or not gm.is_admin:
        return jsonify({'error': 'Not admin'}), 403
    data = request.json
    group = Group.query.get(group_id)
    group.allow_nonadmin_messages = data.get('allow_nonadmin_messages', group.allow_nonadmin_messages)
    group.allow_nonadmin_add_members = data.get('allow_nonadmin_add_members', group.allow_nonadmin_add_members)
    group.approve_new_members = data.get('approve_new_members', group.approve_new_members)
    db.session.commit()
    return jsonify({'message': 'Updated'})

@app.route('/api/group/remove_member/<int:group_id>/<int:member_id>', methods=['POST'])
def remove_group_member(group_id, member_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    gm = GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first()
    if not gm or not gm.is_admin:
        return jsonify({'error': 'Not admin'}), 403
    target_gm = GroupMember.query.filter_by(group_id=group_id, user_id=member_id).first()
    if target_gm:
        db.session.delete(target_gm)
        db.session.commit()
    return jsonify({'message': 'Removed'})

@app.route('/api/profile', methods=['GET'])
def get_own_profile():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    return get_profile(user.id)

@app.route('/api/profile/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    current = get_current_user()
    if not current:
        return jsonify({'error': 'Unauthorized'}), 401
    profile_user = User.query.get_or_404(user_id)
    is_own = user_id == current.id
    friends_count = len(get_friends_ids(user_id))
    followers_count = Follow.query.filter_by(followed_id=user_id, status='accepted').count()
    following_count = Follow.query.filter_by(follower_id=user_id, status='accepted').count()
    likes_count = Like.query.filter_by(user_id=user_id).count()
    posts_count = Post.query.filter_by(user_id=user_id).count()
    data = {
        'id': profile_user.id,
        'username': profile_user.username,
        'real_name': profile_user.real_name,
        'bio': profile_user.bio,
        'profile_pic': profile_user.profile_pic_url,
        'unique_key': profile_user.unique_key if is_own else None,
        'friends_count': friends_count,
        'followers_count': followers_count,
        'following_count': following_count,
        'likes_count': likes_count if is_own else None,
        'posts_count': posts_count,
        'is_own': is_own,
        'is_following': bool(Follow.query.filter_by(follower_id=current.id, followed_id=user_id, status='accepted').first()),
        'user_info': {
            'dob': profile_user.dob,
            'gender': profile_user.gender,
            'pronouns': profile_user.pronouns,
            'work': profile_user.work,
            'education': profile_user.education,
            'location': profile_user.location,
            'email': profile_user.email if is_own else None,
            'phone': profile_user.phone if is_own else None,
            'social_links': profile_user.social_links,
            'website': profile_user.website,
            'relationship': profile_user.relationship,
            'spouse': profile_user.spouse
        } if is_own else {k: v for k, v in {
            'dob': profile_user.dob,
            'gender': profile_user.gender,
            'pronouns': profile_user.pronouns,
            'work': profile_user.work,
            'education': profile_user.education,
            'location': profile_user.location,
            'social_links': profile_user.social_links,
            'website': profile_user.website,
            'relationship': profile_user.relationship,
            'spouse': profile_user.spouse
        }.items() if v}  # Show only added
    }
    if is_own:
        data['posts'] = [p.id for p in Post.query.filter_by(user_id=user_id, type='post').all()]
        data['locked_posts'] = []  # Assume all public for simple
        data['saved'] = [s.post_id for s in Save.query.filter_by(user_id=user_id).all()]
        data['reposts'] = [r.original_post_id for r in Repost.query.filter_by(user_id=user_id).all()]
        data['liked'] = [l.post_id for l in Like.query.filter_by(user_id=user_id).all()]
        data['reels'] = [p.id for p in Post.query.filter_by(user_id=user_id, type='reel').all()]
    else:
        data['posts'] = [p.id for p in Post.query.filter_by(user_id=user_id, type='post').all()]
        data['reels'] = [p.id for p in Post.query.filter_by(user_id=user_id, type='reel').all()]
        mutual_friends = get_mutual_count(current.id, user_id)
        data['mutual_friends'] = mutual_friends
    return jsonify(data)

@app.route('/api/profile/update', methods=['POST'])
def update_profile():
    user = get_current_user()
    if not user:
        return jupytext({'error': 'Unauthorized'}), 401
    data = request.form
    user.real_name = data.get('real_name', user.real_name)
    user.bio = data.get('bio', user.bio)
    user.dob = datetime.datetime.strptime(data.get('dob'), '%Y-%m-%d').date() if data.get('dob') else user.dob
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

@app.route('/api/settings', methods=['POST'])
def update_settings():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    # Language, theme, etc. For simple, assume client-side
    # Profile locking, visibility, etc. Add fields if needed
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
    # Delete related
    Post.query.filter_by(user_id=user_id).delete()
    Follow.query.filter(or_(Follow.follower_id == user_id, Follow.followed_id == user_id)).delete()
    PrivateMessage.query.filter(or_(PrivateMessage.sender_id == user_id, PrivateMessage.receiver_id == user_id)).delete()
    Group.query.filter_by(creator_id=user_id).delete()
    GroupMember.query.filter_by(user_id=user_id).delete()
    GroupMessage.query.filter_by(sender_id=user_id).delete()
    Notification.query.filter_by(user_id=user_id).delete()
    Report.query.filter_by(reporter_id=user_id).delete()
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
    target.is_banned = True
    notif = Notification(user_id=user_id, type='system', message='Your account has been banned')
    db.session.add(notif)
    db.session.commit()
    return jsonify({'message': 'Banned'})

@app.route('/api/admin/warn/user/<int:user_id>', methods=['POST'])
def admin_warn_user(user_id):
    user = get_current_user()
    if not user or not user.is_admin:
        return jupytext({'error': 'Unauthorized'}), 403
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
