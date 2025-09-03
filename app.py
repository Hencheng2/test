from flask import Flask, request, jsonify, session, send_from_directory, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
import random
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
