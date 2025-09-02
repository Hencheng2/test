# app.py

from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import random
import string
from config import SECRET_KEY, ADMIN_USERNAME, ADMIN_PASS

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sociafam.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)

@app.context_processor
def inject_user():
    return dict(User=User)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    real_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    profile_pic = db.Column(db.String(200), default='default.jpg')
    unique_key = db.Column(db.String(4), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    pronouns = db.Column(db.String(20))
    work = db.Column(db.String(200))
    education = db.Column(db.String(200))
    location = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    social_link = db.Column(db.String(200))
    website = db.Column(db.String(200))
    relationship = db.Column(db.String(20))
    spouse = db.Column(db.String(80))
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='user', lazy=True)
    reels = db.relationship('Reel', backref='user', lazy=True)
    stories = db.relationship('Story', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='requested')  # requested, following, blocked

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text)
    media_url = db.Column(db.String(200))
    media_type = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    privacy = db.Column(db.String(20), default='all')
    likes = db.relationship('Like', backref='post', lazy=True)
    comments = db.relationship('Comment', backref='post', lazy=True)

class Reel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_url = db.Column(db.String(200))
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)

class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    media_url = db.Column(db.String(200))
    media_type = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    reel_id = db.Column(db.Integer, db.ForeignKey('reel.id'))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    reel_id = db.Column(db.Integer, db.ForeignKey('reel.id'))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Repost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    original_reel_id = db.Column(db.Integer, db.ForeignKey('reel.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Save(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    reel_id = db.Column(db.Integer, db.ForeignKey('reel.id'))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    content = db.Column(db.Text)
    media_url = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    profile_pic = db.Column(db.String(200), default='default_group.jpg')
    description = db.Column(db.Text)
    link = db.Column(db.String(100), unique=True)
    allow_edit = db.Column(db.Boolean, default=False)
    allow_send = db.Column(db.Boolean, default=True)
    allow_add = db.Column(db.Boolean, default=True)
    approve_members = db.Column(db.Boolean, default=False)
    members = db.relationship('GroupMember', backref='group', lazy=True)

class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50))
    content = db.Column(db.Text)
    link = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reported_post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    reported_group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

def generate_unique_key():
    while True:
        key = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
        if not User.query.filter_by(unique_key=key).first():
            return key

def generate_group_link():
    while True:
        link = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        if not Group.query.filter_by(link=link).first():
            return link

@app.route('/')
def index():
    if 'user_id'in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if len(password) < 6 or not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password) or not any(not c.isalnum() for c in password):
            flash('Password must be 6+ chars with numbers, letters, special char')
            return redirect(url_for('register'))
        if username == ADMIN_USERNAME and password == ADMIN_PASS:
            flash('Cannot register with admin credentials')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username taken')
            return redirect(url_for('register'))
        user = User(username=username, unique_key=generate_unique_key())
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully. Your unique key is ' + user.unique_key)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']
        user = User.query.filter_by(username=identifier).first() or User.query.filter_by(email=identifier).first()
        if user and user.check_password(password) and not user.is_banned:
            session['user_id'] = user.id
            if user.username == ADMIN_USERNAME:
                user.is_admin = True
                db.session.commit()
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home'))
        flash('Invalid credentials or banned')
    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        key = request.form['key']
        user = User.query.filter_by(username=username, unique_key=key).first()
        if user:
            session['reset_user_id'] = user.id
            return redirect(url_for('reset_password'))
        flash('Invalid username or key')
    return render_template('forgot_password.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_user_id' not in session:
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        password = request.form['password']
        user = User.query.get(session['reset_user_id'])
        user.set_password(password)
        db.session.commit()
        del session['reset_user_id']
        flash('Password reset successful')
        return redirect(url_for('login'))
    return render_template('reset_password.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

from functools import wraps

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_id' in session:
            return f(*args, **kwargs)
        return redirect(url_for('login'))
    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user.is_admin:
                return f(*args, **kwargs)
        return redirect(url_for('login'))
    return wrap

@app.route('/home')
@login_required
def home():
    user = User.query.get(session['user_id'])
    friends = [f.followed_id for f in Follow.query.filter_by(follower_id=user.id, status='following').all()]
    stories = Story.query.filter(Story.user_id.in_(friends)).order_by(Story.timestamp.desc()).all()
    posts = Post.query.order_by(Post.timestamp.desc()).limit(20).all()
    return render_template('home.html', stories=stories, posts=posts)

@app.route('/api/posts/<int:page>')
@login_required
def api_posts(page):
    posts = Post.query.order_by(Post.timestamp.desc()).offset(page*10).limit(10).all()
    return render_template('post_snippet.html', posts=posts)

@app.route('/reels')
@login_required
def reels():
    reels = Reel.query.order_by(Reel.timestamp.desc()).all()
    return render_template('reels.html', reels=reels)

@app.route('/friends')
@login_required
def friends():
    return render_template('friends.html')

@app.route('/api/followers')
@login_required
def api_followers():
    user = User.query.get(session['user_id'])
    followers = Follow.query.filter_by(followed_id=user.id, status='following').all()
    users = [User.query.get(f.follower_id) for f in followers]
    return render_template('user_list.html', users=users, type='followers')

@app.route('/api/following')
@login_required
def api_following():
    user = User.query.get(session['user_id'])
    following = Follow.query.filter_by(follower_id=user.id, status='following').all()
    users = [User.query.get(f.followed_id) for f in following]
    return render_template('user_list.html', users=users, type='following')

@app.route('/api/friends')
@login_required
def api_friends():
    user_id = session['user_id']
    mutuals = db.session.query(User).join(Follow, Follow.followed_id == User.id).filter(Follow.follower_id == user_id, Follow.status=='following').join(Follow, Follow.follower_id == User.id, Follow.followed_id == user_id, Follow.status=='following').all()
    return render_template('user_list.html', users=mutuals, type='friends')

@app.route('/api/friend_requests')
@login_required
def api_friend_requests():
    user = User.query.get(session['user_id'])
    requests = Follow.query.filter_by(followed_id=user.id, status='requested').all()
    users = [User.query.get(f.follower_id) for f in requests]
    return render_template('user_list.html', users=users, type='requests')

@app.route('/api/suggested')
@login_required
def api_suggested():
    user_id = session['user_id']
    my_following = [f.followed_id for f in Follow.query.filter_by(follower_id=user_id, status='following').all()]
    suggested = db.session.query(User).join(Follow, Follow.followed_id == User.id).filter(Follow.follower_id.in_(my_following), User.id.notin_(my_following), User.id != user_id).group_by(User.id).order_by(db.func.count().desc()).limit(10).all()
    return render_template('user_list.html', users=suggested, type='suggested')

@app.route('/api/follow/<int:user_id>', methods=['POST'])
@login_required
def api_follow(user_id):
    current_user = session['user_id']
    if current_user == user_id:
        return jsonify({'error': 'Cannot follow self'}), 400
    existing = Follow.query.filter_by(follower_id=current_user, followed_id=user_id).first()
    if existing and existing.status == 'blocked':
        return jsonify({'error': 'Blocked'}), 400
    if not existing:
        follow = Follow(follower_id=current_user, followed_id=user_id, status='requested')
        db.session.add(follow)
        db.session.commit()
        notif = Notification(user_id=user_id, type='friend_request', content=f'{User.query.get(current_user).username} sent friend request', link=url_for('friends'))
        db.session.add(notif)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/accept_request/<int:user_id>', methods=['POST'])
@login_required
def api_accept_request(user_id):
    current_user = session['user_id']
    request_follow = Follow.query.filter_by(follower_id=user_id, followed_id=current_user, status='requested').first()
    if request_follow:
        request_follow.status = 'following'
        reciprocal = Follow.query.filter_by(follower_id=current_user, followed_id=user_id).first()
        if not reciprocal:
            reciprocal = Follow(follower_id=current_user, followed_id=user_id, status='following')
            db.session.add(reciprocal)
        db.session.commit()
        notif = Notification(user_id=user_id, type='friend_accept', content=f'{User.query.get(current_user).username} accepted your friend request')
        db.session.add(notif)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/decline_request/<int:user_id>', methods=['POST'])
@login_required
def api_decline_request(user_id):
    current_user = session['user_id']
    request_follow = Follow.query.filter_by(follower_id=user_id, followed_id=current_user, status='requested').first()
    if request_follow:
        db.session.delete(request_follow)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/unfollow/<int:user_id>', methods=['POST'])
@login_required
def api_unfollow(user_id):
    current_user = session['user_id']
    follow = Follow.query.filter_by(follower_id=current_user, followed_id=user_id, status='following').first()
    if follow:
        db.session.delete(follow)
        db.session.commit()
    reciprocal = Follow.query.filter_by(follower_id=user_id, followed_id=current_user).first()
    if reciprocal:
        reciprocal.status = 'requested'
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/block/<int:user_id>', methods=['POST'])
@login_required
def api_block(user_id):
    current_user = session['user_id']
    follow = Follow.query.filter_by(follower_id=current_user, followed_id=user_id).first()
    if follow:
        follow.status = 'blocked'
    else:
        follow = Follow(follower_id=current_user, followed_id=user_id, status='blocked')
        db.session.add(follow)
    db.session.commit()
    reciprocal = Follow.query.filter_by(follower_id=user_id, followed_id=current_user).first()
    if reciprocal:
        db.session.delete(reciprocal)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/inbox')
@login_required
def inbox():
    return render_template('inbox.html')

@app.route('/api/chats')
@login_required
def api_chats():
    user_id = session['user_id']
    chat_partners = db.session.query(Message.receiver_id).filter(Message.sender_id == user_id).union(db.session.query(Message.sender_id).filter(Message.receiver_id == user_id)).all()
    chat_users = [User.query.get(p[0]) for p in chat_partners]
    return render_template('chat_list.html', chat_users=chat_users)

@app.route('/api/groups')
@login_required
def api_groups():
    user_id = session['user_id']
    user_groups = Group.query.join(GroupMember).filter(GroupMember.user_id == user_id).all()
    return render_template('group_list.html', groups=user_groups)

@app.route('/api/chat/<int:user_id>')
@login_required
def api_chat(user_id):
    current_user = session['user_id']
    messages = Message.query.filter(((Message.sender_id == current_user) & (Message.receiver_id == user_id)) | ((Message.sender_id == user_id) & (Message.receiver_id == current_user))).order_by(Message.timestamp).all()
    for msg in messages:
        if msg.receiver_id == current_user and not msg.is_read:
            msg.is_read = True
    db.session.commit()
    return render_template('chat_modal.html', messages=messages, chat_user=User.query.get(user_id))

@app.route('/api/group_chat/<int:group_id>')
@login_required
def api_group_chat(group_id):
    current_user = session['user_id']
    messages = Message.query.filter_by(group_id=group_id).order_by(Message.timestamp).all()
    for msg in messages:
        if not msg.is_read and msg.sender_id != current_user:
            msg.is_read = True  # but for groups, perhaps separate read per user, but simplify
    db.session.commit()
    return render_template('group_chat_modal.html', messages=messages, group=Group.query.get(group_id))

@app.route('/api/send_message', methods=['POST'])
@login_required
def api_send_message():
    receiver_id = request.form.get('receiver_id')
    group_id = request.form.get('group_id')
    content = request.form.get('content')
    file = request.files.get('file')
    media_url = None
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        media_url = filename
    msg = Message(sender_id=session['user_id'], content=content, media_url=media_url)
    if receiver_id:
        msg.receiver_id = receiver_id
    elif group_id:
        msg.group_id = group_id
        group = Group.query.get(group_id)
        member = GroupMember.query.filter_by(group_id=group_id, user_id=session['user_id']).first()
        if not group.allow_send and not member.is_admin:
            return jsonify({'error': 'No permission'}), 403
    db.session.add(msg)
    db.session.commit()
    if receiver_id:
        notif = Notification(user_id=receiver_id, type='message', content='New message')
        db.session.add(notif)
        db.session.commit()
    elif group_id:
        members = GroupMember.query.filter_by(group_id=group_id).all()
        for m in members:
            if m.user_id != session['user_id']:
                notif = Notification(user_id=m.user_id, type='group_message', content='New group message')
                db.session.add(notif)
        db.session.commit()
    return jsonify({'success': True, 'msg_id': msg.id})

@app.route('/api/profile/<username>')
@login_required
def api_profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return 'Not found', 404
    current_user_id = session['user_id']
    is_own_profile = user.id == current_user_id
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).limit(10).all()
    friends_query = db.session.query(Follow).select_from(Follow).join(User, or_(Follow.follower_id == User.id, Follow.followed_id == User.id)).filter(or_(Follow.follower_id == user.id, Follow.followed_id == user.id), Follow.status == 'following')
    friends = friends_query.count()
    is_friend = Follow.query.filter(or_(and_(Follow.follower_id == current_user_id, Follow.followed_id == user.id), and_(Follow.follower_id == user.id, Follow.followed_id == current_user_id)), Follow.status == 'following').first() is not None
    is_following = Follow.query.filter_by(follower_id=current_user_id, followed_id=user.id, status='following').first() is not None
    is_pending = Follow.query.filter_by(follower_id=current_user_id, followed_id=user.id, status='pending').first() is not None
    stories = Story.query.filter_by(user_id=user.id).order_by(Story.created_at.desc()).limit(10).all()
    template = 'profile_own_modal.html' if is_own_profile else 'profile_other_modal.html'
    return render_template(template, user=user, posts=posts, friends=friends, is_friend=is_friend, is_following=is_following, is_pending=is_pending, stories=stories)
@app.route('/api/group_profile/<int:group_id>')
@login_required
def api_group_profile(group_id):
    group = Group.query.get(group_id)
    if not group:
        return 'Not found', 404
    current_user_id = session['user_id']
    member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user_id).first()
    is_member = bool(member)
    is_admin = member.is_admin if member else False
    members = GroupMember.query.filter_by(group_id=group_id).limit(10).all()
    media = Message.query.filter_by(group_id=group_id).filter(Message.media_url != None).all()
    return render_template('group_profile_modal.html', group=group, is_admin=is_admin, members=members, media=media)

@app.route('/api/edit_profile', methods=['POST'])
@login_required
def api_edit_profile():
    user = User.query.get(session['user_id'])
    user.real_name = request.form.get('real_name', user.real_name)
    user.bio = request.form.get('bio', user.bio)
    # other fields...
    file = request.files.get('profile_pic')
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        user.profile_pic = filename
    db.session.commit()
    return jsonify({'success': True})

@app.route('/search')
@login_required
def search():
    return render_template('search.html')

@app.route('/api/search')
@login_required
def api_search():
    q = request.args.get('q')
    tab = request.args.get('tab', 'all')
    if tab == 'users' or tab == 'all':
        users = User.query.filter(User.username.ilike(f'%{q}%') | User.real_name.ilike(f'%{q}%')).all()
    if tab == 'groups' or tab == 'all':
        groups = Group.query.filter(Group.name.ilike(f'%{q}%')).all()
    if tab == 'posts' or tab == 'all':
        posts = Post.query.filter(Post.content.ilike(f'%{q}%')).all()
    if tab == 'reels' or tab == 'all':
        reels = Reel.query.filter(Reel.description.ilike(f'%{q}%')).all()
    if tab != 'all':
        if tab == 'users':
            return render_template('search_users.html', users=users)
        elif tab == 'groups':
            return render_template('search_groups.html', groups=groups)
        elif tab == 'posts':
            return render_template('search_posts.html', posts=posts)
        elif tab == 'reels':
            return render_template('search_reels.html', reels=reels)
    return render_template('search_all.html', users=users, groups=groups, posts=posts, reels=reels)

@app.route('/add_to')
@login_required
def add_to():
    return render_template('add_to.html')

@app.route('/api/create_post', methods=['POST'])
@login_required
def api_create_post():
    content = request.form.get('content')
    privacy = request.form.get('privacy', 'all')
    file = request.files.get('file')
    media_url = None
    media_type = None
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        media_url = filename
        if filename.lower().endswith(('.jpg', '.png', '.gif')):
            media_type = 'image'
        elif filename.lower().endswith(('.mp4', '.avi')):
            media_type = 'video'
    post = Post(user_id=session['user_id'], content=content, media_url=media_url, media_type=media_type, privacy=privacy)
    db.session.add(post)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/create_reel', methods=['POST'])
@login_required
def api_create_reel():
    description = request.form.get('description')
    file = request.files.get('file')
    if not file or not file.filename.lower().endswith(('.mp4', '.avi')):
        return jsonify({'error': 'Video required'}), 400
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    reel = Reel(user_id=session['user_id'], video_url=filename, description=description)
    db.session.add(reel)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/create_story', methods=['POST'])
@login_required
def api_create_story():
    file = request.files.get('file')
    media_url = None
    media_type = None
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        media_url = filename
        if filename.lower().endswith(('.jpg', '.png', '.gif')):
            media_type = 'image'
        elif filename.lower().endswith(('.mp4', '.avi')):
            media_type = 'video'
        elif filename.lower().endswith(('.mp3', '.wav')):
            media_type = 'audio'
    story = Story(user_id=session['user_id'], media_url=media_url, media_type=media_type)
    db.session.add(story)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/view_story/<int:story_id>')
@login_required
def api_view_story(story_id):
    story = Story.query.get(story_id)
    return render_template('story_modal.html', story=story)

@app.route('/api/like/<string:type_>/<int:item_id>', methods=['POST'])
@login_required
def api_like(type_, item_id):
    user_id = session['user_id']
    existing = Like.query.filter_by(user_id=user_id, post_id=item_id if type_=='post' else None, reel_id=item_id if type_=='reel' else None).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'success': True, 'liked': False})
    like = Like(user_id=user_id)
    if type_ == 'post':
        item = Post.query.get(item_id)
        like.post_id = item_id
    elif type_ == 'reel':
        item = Reel.query.get(item_id)
        like.reel_id = item_id
    else:
        return jsonify({'error': 'Invalid type'}), 400
    if item:
        db.session.add(like)
        db.session.commit()
        notif = Notification(user_id=item.user_id, type='like', content=f'{User.query.get(user_id).username} liked your {type_}')
        db.session.add(notif)
        db.session.commit()
    return jsonify({'success': True, 'liked': True})

@app.route('/api/comment/<string:type_>/<int:item_id>', methods=['POST'])
@login_required
def api_comment(type_, item_id):
    content = request.form['content']
    comment = Comment(user_id=session['user_id'], content=content)
    if type_ == 'post':
        comment.post_id = item_id
        item = Post.query.get(item_id)
    elif type_ == 'reel':
        comment.reel_id = item_id
        item = Reel.query.get(item_id)
    db.session.add(comment)
    db.session.commit()
    notif = Notification(user_id=item.user_id, type='comment', content=f'{User.query.get(session["user_id"]).username} commented on your {type_}')
    db.session.add(notif)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/repost/<string:type_>/<int:item_id>', methods=['POST'])
@login_required
def api_repost(type_, item_id):
    repost = Repost(user_id=session['user_id'])
    if type_ == 'post':
        repost.original_post_id = item_id
        item = Post.query.get(item_id)
    elif type_ == 'reel':
        repost.original_reel_id = item_id
        item = Reel.query.get(item_id)
    db.session.add(repost)
    db.session.commit()
    notif = Notification(user_id=item.user_id, type='repost', content=f'{User.query.get(session["user_id"]).username} reposted your {type_}')
    db.session.add(notif)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/save/<string:type_>/<int:item_id>', methods=['POST'])
@login_required
def api_save(type_, item_id):
    save = Save(user_id=session['user_id'])
    if type_ == 'post':
        save.post_id = item_id
    elif type_ == 'reel':
        save.reel_id = item_id
    db.session.add(save)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/report/<string:type_>/<int:item_id>', methods=['POST'])
@login_required
def api_report(type_, item_id):
    description = request.form['description']
    report = Report(reporter_id=session['user_id'], description=description)
    if type_ == 'user':
        report.reported_user_id = item_id
    elif type_ == 'post':
        report.reported_post_id = item_id
    elif type_ == 'group':
        report.reported_group_id = item_id
    db.session.add(report)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=session['user_id']).order_by(Notification.timestamp.desc()).all()
    for n in notifs:
        n.is_read = True
    db.session.commit()
    return render_template('notifications.html', notifs=notifs)

@app.route('/menu')
@login_required
def menu():
    return render_template('menu.html')

@app.route('/api/change_password', methods=['POST'])
@login_required
def api_change_password():
    old_pass = request.form['old_pass']
    new_pass = request.form['new_pass']
    user = User.query.get(session['user_id'])
    if user.check_password(old_pass):
        user.set_password(new_pass)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid old password'}), 400

@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    users = User.query.all()
    groups = Group.query.all()
    reports = Report.query.all()
    return render_template('admin_dashboard.html', users=users, groups=groups, reports=reports)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/ban_user/<int:user_id>', methods=['POST'])
@admin_required
def admin_ban_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_banned = True
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/unban_user/<int:user_id>', methods=['POST'])
@admin_required
def admin_unban_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_banned = False
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/send_warning/<int:user_id>', methods=['POST'])
@admin_required
def admin_send_warning(user_id):
    content = request.form['content']
    notif = Notification(user_id=user_id, type='warning', content=content)
    db.session.add(notif)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/send_to_all', methods=['POST'])
@admin_required
def admin_send_to_all():
    content = request.form['content']
    users = User.query.all()
    for u in users:
        notif = Notification(user_id=u.id, type='system', content=content)
        db.session.add(notif)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_group/<int:group_id>', methods=['POST'])
@admin_required
def admin_delete_group(group_id):
    group = Group.query.get(group_id)
    if group:
        db.session.delete(group)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/api/create_group', methods=['POST'])
@login_required
def api_create_group():
    name = request.form['name']
    file = request.files.get('profile_pic')
    profile_pic = 'default_group.jpg'
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        profile_pic = filename
    group = Group(name=name, creator_id=session['user_id'], profile_pic=profile_pic, link=generate_group_link(), description=f'Created by {User.query.get(session["user_id"]).username} on {datetime.now()}')
    group.allow_edit = 'allow_edit' in request.form
    group.allow_send = 'allow_send' in request.form
    group.allow_add = 'allow_add' in request.form
    db.session.add(group)
    db.session.commit()
    member = GroupMember(group_id=group.id, user_id=session['user_id'], is_admin=True)
    db.session.add(member)
    db.session.commit()
    return jsonify({'success': True, 'group_id': group.id})

@app.route('/api/join_group/<string:link>')
@login_required
def api_join_group(link):
    group = Group.query.filter_by(link=link).first()
    if group:
        existing = GroupMember.query.filter_by(group_id=group.id, user_id=session['user_id']).first()
        if not existing:
            member = GroupMember(group_id=group.id, user_id=session['user_id'], is_admin=False)
            if group.approve_members:
                # send request to admins, but simplify to add
                pass
            db.session.add(member)
            db.session.commit()
            notif = Notification(user_id=group.creator_id, type='group_join', content=f'{User.query.get(session["user_id"]).username} joined group')
            db.session.add(notif)
            db.session.commit()
    return jsonify({'success': True})

@app.route('/api/leave_group/<int:group_id>', methods=['POST'])
@login_required
def api_leave_group(group_id):
    member = GroupMember.query.filter_by(group_id=group_id, user_id=session['user_id']).first()
    if member:
        db.session.delete(member)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/add_to_group/<int:group_id>/<int:user_id>', methods=['POST'])
@login_required
def api_add_to_group(group_id, user_id):
    group = Group.query.get(group_id)
    current_member = GroupMember.query.filter_by(group_id=group_id, user_id=session['user_id']).first()
    if group.allow_add or current_member.is_admin:
        existing = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
        if not existing:
            member = GroupMember(group_id=group_id, user_id=user_id)
            db.session.add(member)
            db.session.commit()
            notif = Notification(user_id=user_id, type='group_add', content=f'Added to group {group.name}')
            db.session.add(notif)
            db.session.commit()
    return jsonify({'success': True})

@app.route('/api/remove_from_group/<int:group_id>/<int:user_id>', methods=['POST'])
@login_required
def api_remove_from_group(group_id, user_id):
    current_member = GroupMember.query.filter_by(group_id=group_id, user_id=session['user_id']).first()
    if current_member.is_admin:
        member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
        if member:
            db.session.delete(member)
            db.session.commit()
    return jsonify({'success': True})

@app.route('/api/update_group_permissions/<int:group_id>', methods=['POST'])
@login_required
def api_update_group_permissions(group_id):
    group = Group.query.get(group_id)
    current_member = GroupMember.query.filter_by(group_id=group_id, user_id=session['user_id']).first()
    if current_member.is_admin:
        group.allow_edit = 'allow_edit' in request.form
        group.allow_send = 'allow_send' in request.form
        group.allow_add = 'allow_add' in request.form
        group.approve_members = 'approve_members' in request.form
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/make_group_admin/<int:group_id>/<int:user_id>', methods=['POST'])
@login_required
def api_make_group_admin(group_id, user_id):
    current_member = GroupMember.query.filter_by(group_id=group_id, user_id=session['user_id']).first()
    if current_member.is_admin:
        member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
        if member:
            member.is_admin = True
            db.session.commit()
    return jsonify({'success': True})

@app.route('/api/remove_group_admin/<int:group_id>/<int:user_id>', methods=['POST'])
@login_required
def api_remove_group_admin(group_id, user_id):
    current_member = GroupMember.query.filter_by(group_id=group_id, user_id=session['user_id']).first()
    if current_member.is_admin and Group.query.get(group_id).creator_id == session['user_id']:
        member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
        if member:
            member.is_admin = False
            db.session.commit()
    return jsonify({'success': True})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username=ADMIN_USERNAME).first():
        admin = User(username=ADMIN_USERNAME, is_admin=True, unique_key=generate_unique_key())
        admin.set_password(ADMIN_PASS)
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
