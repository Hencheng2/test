# app.py
import os
import re
import uuid
import datetime
from functools import wraps
from collections import defaultdict

from flask import (
    Flask, g, jsonify, request, send_from_directory, redirect, url_for,
    render_template, abort
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user, UserMixin
)
from werkzeug.utils import secure_filename
import config  # expects config.py in same directory

# --- App & DB Setup ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = getattr(config, "SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "sociafam.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024  # 64MB uploads

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# Allowed extensions for uploads (images/videos)
ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_VIDEO_EXT = {"mp4", "mov", "webm", "ogg"}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXT.union(ALLOWED_VIDEO_EXT)


# --- Helpers ---
def allowed_file(filename):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def file_save(file_storage, subfolder=""):
    if not file_storage:
        return None
    filename = secure_filename(file_storage.filename)
    if not allowed_file(filename):
        return None
    folder = app.config["UPLOAD_FOLDER"]
    if subfolder:
        folder = os.path.join(folder, subfolder)
    os.makedirs(folder, exist_ok=True)
    unique = f"{uuid.uuid4().hex}_{filename}"
    path = os.path.join(folder, unique)
    file_storage.save(path)
    # return relative path to /static/uploads...
    rel = os.path.relpath(path, BASE_DIR)
    return rel.replace("\\", "/")


def generate_unique_key():
    # 4 characters: 2 letters + 2 numbers shuffled
    import random, string
    letters = "".join(random.choices(string.ascii_uppercase, k=2))
    numbers = "".join(random.choices("0123456789", k=2))
    s = list(letters + numbers)
    random.shuffle(s)
    return "".join(s)


def admin_required(f):
    @wraps(f)
    def _wrap(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({"error": "Admin privileges required"}), 403
        return f(*args, **kwargs)
    return _wrap


# --- Models ---
followers = db.Table(
    "followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("followed_id", db.Integer, db.ForeignKey("user.id"))
)

group_members = db.Table(
    "group_members",
    db.Column("group_id", db.Integer, db.ForeignKey("group.id")),
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("is_admin", db.Boolean, default=False)
)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(120), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_photo = db.Column(db.String(512), nullable=True)  # path to upload
    unique_key = db.Column(db.String(8), nullable=False, unique=True)

    # optional fields
    dob = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(32), nullable=True)
    pronouns = db.Column(db.String(32), nullable=True)
    work = db.Column(db.String(255), nullable=True)
    education = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    relationship = db.Column(db.String(64), nullable=True)

    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # followers/following relationship
    followed = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers_list", lazy="dynamic"),
        lazy="dynamic"
    )

    posts = db.relationship("Post", backref="author", lazy="dynamic")
    reels = db.relationship("Reel", backref="author", lazy="dynamic")
    stories = db.relationship("Story", backref="author", lazy="dynamic")
    sent_messages = db.relationship("Message", backref="sender", lazy="dynamic")

    notifications = db.relationship("Notification", backref="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def to_dict(self, minimal=False):
        d = {
            "id": self.id,
            "username": self.username,
            "real_name": self.real_name,
            "bio": self.bio,
            "profile_photo": url_for("uploaded_file", filename=os.path.relpath(self.profile_photo or "", "static").replace("\\", "/"), _external=True) if self.profile_photo else None,
            "followers_count": self.followers_list.count(),
            "following_count": self.followed.count(),
            "is_admin": bool(self.is_admin),
            "created_at": self.created_at.isoformat()
        }
        if minimal:
            return {"id": self.id, "username": self.username, "real_name": self.real_name, "profile_photo": d["profile_photo"]}
        return d


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    description = db.Column(db.Text, nullable=True)
    media_path = db.Column(db.String(512), nullable=True)  # image or video
    is_locked = db.Column(db.Boolean, default=False)  # visible only to owner if True
    likes = db.relationship("PostLike", backref="post", lazy="dynamic")
    comments = db.relationship("PostComment", backref="post", lazy="dynamic")
    views = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "owner": self.author.to_dict(minimal=True),
            "description": self.description,
            "media_url": url_for("uploaded_file", filename=os.path.relpath(self.media_path or "", "static").replace("\\", "/"), _external=True) if self.media_path else None,
            "likes_count": self.likes.count(),
            "comments_count": self.comments.count(),
            "views": self.views,
            "created_at": self.created_at.isoformat(),
            "is_locked": self.is_locked
        }


class PostLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class PostComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Reel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    media_path = db.Column(db.String(512), nullable=False)  # video or image+audio combo
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    likes = db.relationship("ReelLike", backref="reel", lazy="dynamic")
    comments = db.relationship("ReelComment", backref="reel", lazy="dynamic")
    views = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "owner": self.author.to_dict(minimal=True),
            "media_url": url_for("uploaded_file", filename=os.path.relpath(self.media_path or "", "static").replace("\\", "/"), _external=True),
            "description": self.description,
            "likes_count": self.likes.count(),
            "comments_count": self.comments.count(),
            "views": self.views,
            "created_at": self.created_at.isoformat()
        }


class ReelLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reel_id = db.Column(db.Integer, db.ForeignKey("reel.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class ReelComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reel_id = db.Column(db.Integer, db.ForeignKey("reel.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    media_path = db.Column(db.String(512), nullable=False)  # image or short video/audio
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    views = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "owner": self.author.to_dict(minimal=True),
            "media_url": url_for("uploaded_file", filename=os.path.relpath(self.media_path or "", "static").replace("\\", "/"), _external=True),
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "views": self.views
        }


class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    to_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(20), default="pending")  # pending/accepted/declined


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.Text, nullable=True)
    media_path = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    profile_photo = db.Column(db.String(512), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    members = db.relationship("User", secondary=group_members, backref="groups", lazy="dynamic")

    # group permissions stored in a JSON-ish style columns (simpler as separate columns)
    allow_nonadmin_edit = db.Column(db.Boolean, default=True)
    allow_nonadmin_post = db.Column(db.Boolean, default=True)
    allow_members_add = db.Column(db.Boolean, default=True)
    require_admin_approval = db.Column(db.Boolean, default=False)

    def to_dict(self, minimal=False):
        d = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "profile_photo": url_for("uploaded_file", filename=os.path.relpath(self.profile_photo or "", "static").replace("\\", "/"), _external=True) if self.profile_photo else None,
            "members_count": self.members.count(),
            "created_at": self.created_at.isoformat()
        }
        if minimal:
            return {"id": self.id, "name": self.name, "members_count": d["members_count"]}
        return d


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    type = db.Column(db.String(64), nullable=True)  # e.g., system, message, like, follow


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    reported_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    reported_post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=True)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    resolved = db.Column(db.Boolean, default=False)


class AdminAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    action = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


# --- Login manager ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- Startup: Create admin user if provided in config ---
@app.before_first_request
def ensure_admin():
    admin_name = getattr(config, "ADMIN_USERNAME", None)
    admin_pass = getattr(config, "ADMIN_PASS", None)
    if not admin_name or not admin_pass:
        return
    admin = User.query.filter_by(username=admin_name).first()
    if not admin:
        u = User(
            username=admin_name,
            real_name="SociaFam Admin",
            email=None,
            unique_key=generate_unique_key(),
            is_admin=True
        )
        u.set_password(admin_pass)
        db.session.add(u)
        db.session.commit()


# --- Routes: Static files & index ---
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    # serve from static/uploads/...
    # filename will be e.g., uploads/.. relative path; ensure safe
    root = BASE_DIR
    safe_path = os.path.join(root, filename)
    if not os.path.exists(safe_path):
        abort(404)
    # serve with send_from_directory using directory part
    directory = os.path.dirname(safe_path)
    fname = os.path.basename(safe_path)
    return send_from_directory(directory, fname)


@app.route("/")
def index():
    # serve the single-page app index.html
    # frontend will handle showing login if not authenticated
    return send_from_directory("static", "index.html")


# --- Authentication endpoints ---
@app.route("/api/register", methods=["POST"])
def register():
    data = request.form or request.json or {}
    username = (data.get("username") or "").strip()
    password = data.get("password")
    email = data.get("email")
    real_name = data.get("real_name", "")
    # validations
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    # check reserved admin combo
    if username == getattr(config, "ADMIN_USERNAME", None) and password == getattr(config, "ADMIN_PASS", None):
        return jsonify({"error": "This username and password combination is reserved"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 400
    if email and User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already taken"}), 400

    user = User(
        username=username,
        email=email,
        real_name=real_name,
        unique_key=generate_unique_key()
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"success": True, "unique_key": user.unique_key, "user": user.to_dict()}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.form or request.json or {}
    username = data.get("username") or ""
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401
    if user.is_banned:
        return jsonify({"error": "Account banned"}), 403
    login_user(user)
    return jsonify({"success": True, "user": user.to_dict()})


@app.route("/api/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"success": True})


@app.route("/api/forgot_password", methods=["POST"])
def forgot_password():
    # requires username and unique_key as per spec
    data = request.form or request.json or {}
    username = data.get("username")
    unique_key = data.get("unique_key")
    new_password = data.get("new_password")
    if not username or not unique_key or not new_password:
        return jsonify({"error": "username, unique_key and new_password required"}), 400
    user = User.query.filter_by(username=username).first()
    if not user or user.unique_key != unique_key:
        return jsonify({"error": "Invalid credentials"}), 401
    # set new password
    user.set_password(new_password)
    db.session.commit()
    return jsonify({"success": True})


# --- User profile endpoints ---
@app.route("/api/user/<int:user_id>", methods=["GET"])
def get_user_profile(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())


@app.route("/api/me", methods=["GET"])
@login_required
def me():
    return jsonify(current_user.to_dict())


@app.route("/api/user/edit", methods=["POST"])
@login_required
def edit_profile():
    data = request.form or request.json or {}
    # allow editing several fields
    fields = ["real_name", "bio", "dob", "gender", "pronouns", "work",
              "education", "location", "phone", "website", "relationship", "username", "email"]
    changed = False
    for f in fields:
        if f in data:
            val = data.get(f)
            if f == "dob" and val:
                try:
                    current_user.dob = datetime.datetime.strptime(val, "%Y-%m-%d").date()
                except:
                    pass
            elif f == "username" and val and val != current_user.username:
                # ensure unique username
                if User.query.filter(User.username == val).first():
                    return jsonify({"error": "Username taken"}), 400
                current_user.username = val
                changed = True
            elif f == "email":
                if val and val != current_user.email and User.query.filter(User.email == val).first():
                    return jsonify({"error": "Email taken"}), 400
                current_user.email = val
                changed = True
            else:
                setattr(current_user, f, val)
                changed = True
    # profile photo upload
    if "profile_photo" in request.files:
        f = request.files["profile_photo"]
        saved = file_save(f, subfolder="profiles")
        if saved:
            current_user.profile_photo = saved
            changed = True

    if changed:
        db.session.commit()
    return jsonify({"success": True, "user": current_user.to_dict()})


# --- Following / Friends / Friend-requests ---
@app.route("/api/follow/<int:user_id>", methods=["POST"])
@login_required
def follow_user(user_id):
    if current_user.id == user_id:
        return jsonify({"error": "Cannot follow yourself"}), 400
    user = User.query.get_or_404(user_id)
    current_user.follow(user)
    db.session.commit()
    # create notification
    n = Notification(user_id=user.id, content=f"{current_user.username} started following you", type="follow")
    db.session.add(n)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/unfollow/<int:user_id>", methods=["POST"])
@login_required
def unfollow_user(user_id):
    if current_user.id == user_id:
        return jsonify({"error": "Cannot unfollow yourself"}), 400
    user = User.query.get_or_404(user_id)
    current_user.unfollow(user)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/friend_request/send/<int:user_id>", methods=["POST"])
@login_required
def send_friend_request(user_id):
    if current_user.id == user_id:
        return jsonify({"error": "Cannot friend yourself"}), 400
    # create friend request
    existing = FriendRequest.query.filter_by(from_user_id=current_user.id, to_user_id=user_id, status="pending").first()
    if existing:
        return jsonify({"error": "Request already sent"}), 400
    fr = FriendRequest(from_user_id=current_user.id, to_user_id=user_id)
    db.session.add(fr)
    db.session.commit()
    # notify
    n = Notification(user_id=user_id, content=f"{current_user.username} sent you a friend request", type="friend_request")
    db.session.add(n)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/friend_request/respond/<int:request_id>", methods=["POST"])
@login_required
def respond_friend_request(request_id):
    data = request.form or request.json or {}
    action = data.get("action")  # accept/decline
    fr = FriendRequest.query.get_or_404(request_id)
    if fr.to_user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    if action == "accept":
        fr.status = "accepted"
        # when accepted, create mutual follow relationships
        from_user = User.query.get(fr.from_user_id)
        to_user = User.query.get(fr.to_user_id)
        from_user.follow(to_user)
        to_user.follow(from_user)
        db.session.commit()
        # notify
        n = Notification(user_id=fr.from_user_id, content=f"{current_user.username} accepted your friend request", type="friend_accepted")
        db.session.add(n)
        db.session.commit()
        return jsonify({"success": True})
    elif action == "decline":
        fr.status = "declined"
        db.session.commit()
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Unknown action"}), 400


@app.route("/api/friends/list/<string:which>", methods=["GET"])
@login_required
def friends_list(which):
    # which: followers, following, friends, requests, suggested
    if which == "followers":
        users = [u.to_dict(minimal=True) for u in current_user.followers_list]
        return jsonify(users)
    if which == "following":
        users = [u.to_dict(minimal=True) for u in current_user.followed]
        return jsonify(users)
    if which == "friends":
        # those that follow the user and the user follows back
        follower_ids = {u.id for u in current_user.followers_list}
        following_ids = {u.id for u in current_user.followed}
        mutual = follower_ids.intersection(following_ids)
        users = [User.query.get(uid).to_dict(minimal=True) for uid in mutual]
        return jsonify(users)
    if which == "requests":
        # show incoming friend requests
        frs = FriendRequest.query.filter_by(to_user_id=current_user.id, status="pending").all()
        outs = []
        for fr in frs:
            u = User.query.get(fr.from_user_id)
            outs.append({"request_id": fr.id, "user": u.to_dict(minimal=True), "created_at": fr.created_at.isoformat()})
        return jsonify(outs)
    if which == "suggested":
        # very simple suggestion: friends of friends not already followed
        suggestions = set()
        for f in current_user.followed:
            for foaf in f.followed:
                if foaf.id != current_user.id and not current_user.is_following(foaf):
                    suggestions.add(foaf)
        outs = [u.to_dict(minimal=True) for u in suggestions]
        return jsonify(outs)
    return jsonify({"error": "unknown type"}), 400


# --- Posts & interactions ---
@app.route("/api/post/create", methods=["POST"])
@login_required
def create_post():
    description = request.form.get("description") or request.json.get("description") if request.json else None
    is_locked = bool(request.form.get("is_locked")) or bool(request.json.get("is_locked")) if request.json else False
    media = request.files.get("media")
    media_path = None
    if media:
        media_path = file_save(media, subfolder="posts")
    post = Post(owner_id=current_user.id, description=description, media_path=media_path, is_locked=is_locked)
    db.session.add(post)
    db.session.commit()
    return jsonify({"success": True, "post": post.to_dict()}), 201


@app.route("/api/posts/feed", methods=["GET"])
@login_required
def feed_posts():
    # endless scroll: accept offset and limit
    try:
        offset = int(request.args.get("offset", 0))
        limit = int(request.args.get("limit", 20))
    except:
        offset, limit = 0, 20
    # show posts by followed users + own posts, exclude locked posts of others
    followed_ids = [u.id for u in current_user.followed]
    query = Post.query.filter(
        (Post.owner_id.in_(followed_ids + [current_user.id]))
    ).order_by(Post.created_at.desc())
    posts = query.offset(offset).limit(limit).all()
    return jsonify([p.to_dict() for p in posts])


@app.route("/api/post/<int:post_id>/like", methods=["POST"])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    existing = PostLike.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"success": True, "action": "unliked"})
    pl = PostLike(post_id=post_id, user_id=current_user.id)
    db.session.add(pl)
    db.session.commit()
    n = Notification(user_id=post.owner_id, content=f"{current_user.username} liked your post", type="like")
    db.session.add(n)
    db.session.commit()
    return jsonify({"success": True, "action": "liked"})


@app.route("/api/post/<int:post_id>/comment", methods=["POST"])
@login_required
def comment_post(post_id):
    data = request.form or request.json or {}
    content = data.get("content")
    if not content:
        return jsonify({"error": "Comment content required"}), 400
    post = Post.query.get_or_404(post_id)
    pc = PostComment(post_id=post_id, user_id=current_user.id, content=content)
    db.session.add(pc)
    db.session.commit()
    n = Notification(user_id=post.owner_id, content=f"{current_user.username} commented on your post", type="comment")
    db.session.add(n)
    db.session.commit()
    return jsonify({"success": True, "comment": {"id": pc.id, "content": pc.content, "created_at": pc.created_at.isoformat()}})


@app.route("/api/post/<int:post_id>/view", methods=["POST"])
@login_required
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.views = (post.views or 0) + 1
    db.session.commit()
    return jsonify({"success": True, "views": post.views})


@app.route("/api/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.owner_id != current_user.id and not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    # delete media file if exists
    if post.media_path:
        p = os.path.join(BASE_DIR, post.media_path)
        try:
            os.remove(p)
        except:
            pass
    db.session.delete(post)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/post/<int:post_id>/report", methods=["POST"])
@login_required
def report_post(post_id):
    data = request.form or request.json or {}
    reason = data.get("reason", "")
    post = Post.query.get_or_404(post_id)
    r = Report(reporter_id=current_user.id, reported_user_id=post.owner_id, reported_post_id=post_id, message=reason)
    db.session.add(r)
    db.session.commit()
    # notify admin
    # create a system notification to admin by creating admin notifications for all admins
    admins = User.query.filter_by(is_admin=True).all()
    for a in admins:
        db.session.add(Notification(user_id=a.id, content=f"Post reported by {current_user.username}: {reason}", type="system"))
    db.session.commit()
    return jsonify({"success": True})


# --- Reels endpoints ---
@app.route("/api/reel/create", methods=["POST"])
@login_required
def create_reel():
    media = request.files.get("media")
    description = request.form.get("description") or (request.json and request.json.get("description"))
    if not media:
        return jsonify({"error": "Media required"}), 400
    saved = file_save(media, subfolder="reels")
    if not saved:
        return jsonify({"error": "Invalid media file"}), 400
    reel = Reel(owner_id=current_user.id, media_path=saved, description=description)
    db.session.add(reel)
    db.session.commit()
    return jsonify({"success": True, "reel": reel.to_dict()}), 201


@app.route("/api/reels/feed", methods=["GET"])
def reels_feed():
    try:
        offset = int(request.args.get("offset", 0))
        limit = int(request.args.get("limit", 20))
    except:
        offset, limit = 0, 20
    query = Reel.query.order_by(Reel.created_at.desc())
    reels = query.offset(offset).limit(limit).all()
    return jsonify([r.to_dict() for r in reels])


@app.route("/api/reel/<int:reel_id>/like", methods=["POST"])
@login_required
def like_reel(reel_id):
    reel = Reel.query.get_or_404(reel_id)
    existing = ReelLike.query.filter_by(reel_id=reel_id, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"success": True, "action": "unliked"})
    rl = ReelLike(reel_id=reel_id, user_id=current_user.id)
    db.session.add(rl)
    db.session.commit()
    n = Notification(user_id=reel.owner_id, content=f"{current_user.username} liked your reel", type="like")
    db.session.add(n)
    db.session.commit()
    return jsonify({"success": True, "action": "liked"})


@app.route("/api/reel/<int:reel_id>/comment", methods=["POST"])
@login_required
def comment_reel(reel_id):
    data = request.form or request.json or {}
    content = data.get("content")
    if not content:
        return jsonify({"error": "Comment required"}), 400
    reel = Reel.query.get_or_404(reel_id)
    rc = ReelComment(reel_id=reel_id, user_id=current_user.id, content=content)
    db.session.add(rc)
    db.session.commit()
    n = Notification(user_id=reel.owner_id, content=f"{current_user.username} commented on your reel", type="comment")
    db.session.add(n)
    db.session.commit()
    return jsonify({"success": True, "comment": {"id": rc.id, "content": rc.content}})


@app.route("/api/reel/<int:reel_id>/view", methods=["POST"])
@login_required
def view_reel(reel_id):
    reel = Reel.query.get_or_404(reel_id)
    reel.views = (reel.views or 0) + 1
    db.session.commit()
    return jsonify({"success": True, "views": reel.views})


# --- Stories endpoints ---
@app.route("/api/story/create", methods=["POST"])
@login_required
def create_story():
    media = request.files.get("media")
    if not media:
        return jsonify({"error": "Media required"}), 400
    saved = file_save(media, subfolder="stories")
    if not saved:
        return jsonify({"error": "Invalid file type"}), 400
    now = datetime.datetime.utcnow()
    expires = now + datetime.timedelta(hours=24)
    story = Story(owner_id=current_user.id, media_path=saved, created_at=now, expires_at=expires)
    db.session.add(story)
    db.session.commit()
    return jsonify({"success": True, "story": story.to_dict()}), 201


@app.route("/api/stories/feed", methods=["GET"])
@login_required
def stories_feed():
    # show stories of friends only (following & followed -> mutual friends?), your spec: only stories from friends
    # interpret "friends" as mutual follows (both follow each other)
    now = datetime.datetime.utcnow()
    mutual_ids = []
    follower_ids = {u.id for u in current_user.followers_list}
    following_ids = {u.id for u in current_user.followed}
    mutual_ids = list(follower_ids.intersection(following_ids))
    stories = Story.query.filter(Story.owner_id.in_(mutual_ids), Story.expires_at > now).order_by(Story.created_at.desc()).all()
    return jsonify([s.to_dict() for s in stories])


@app.route("/api/story/<int:story_id>/view", methods=["POST"])
@login_required
def view_story(story_id):
    s = Story.query.get_or_404(story_id)
    s.views = (s.views or 0) + 1
    db.session.commit()
    return jsonify({"success": True, "views": s.views})


# --- Messaging endpoints (simple direct messages) ---
@app.route("/api/chats/list", methods=["GET"])
@login_required
def chats_list():
    # shows most recent chat per other user and groups separately
    # gather distinct conversation partners from messages where current_user is either sender or receiver
    partners = {}
    messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).order_by(Message.created_at.desc()).all()
    for m in messages:
        other_id = m.receiver_id if m.sender_id == current_user.id else m.sender_id
        if other_id not in partners:
            partners[other_id] = {"user": User.query.get(other_id).to_dict(minimal=True), "last_message": m.content or "[media]" if m.media_path else m.content, "created_at": m.created_at.isoformat(), "unread": 0}
    # compute unread counts
    for pid in partners:
        unread = Message.query.filter_by(sender_id=pid, receiver_id=current_user.id, is_read=False).count()
        partners[pid]["unread"] = unread
    return jsonify(list(partners.values()))


@app.route("/api/chat/send", methods=["POST"])
@login_required
def send_chat():
    receiver_id = int(request.form.get("receiver_id") or (request.json and request.json.get("receiver_id")))
    content = request.form.get("content") or (request.json and request.json.get("content"))
    media = request.files.get("media")
    if not receiver_id:
        return jsonify({"error": "receiver_id required"}), 400
    if current_user.id == receiver_id:
        return jsonify({"error": "Cannot send messages to yourself"}), 400
    saved = None
    if media:
        saved = file_save(media, subfolder="messages")
    m = Message(sender_id=current_user.id, receiver_id=receiver_id, content=content, media_path=saved)
    db.session.add(m)
    db.session.commit()
    # notification to receiver
    db.session.add(Notification(user_id=receiver_id, content=f"New message from {current_user.username}", type="message"))
    db.session.commit()
    return jsonify({"success": True, "message": {"id": m.id, "content": m.content, "created_at": m.created_at.isoformat()}})


@app.route("/api/chat/history/<int:other_id>", methods=["GET"])
@login_required
def chat_history(other_id):
    # return messages between current_user and other_id sorted asc
    msgs = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_id)) |
        ((Message.sender_id == other_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()
    out = []
    for m in msgs:
        out.append({
            "id": m.id,
            "from": m.sender_id,
            "to": m.receiver_id,
            "content": m.content,
            "media_url": url_for("uploaded_file", filename=os.path.relpath(m.media_path or "", "static").replace("\\", "/"), _external=True) if m.media_path else None,
            "created_at": m.created_at.isoformat(),
            "is_read": m.is_read
        })
    # mark messages sent to current user as read
    unread = Message.query.filter_by(sender_id=other_id, receiver_id=current_user.id, is_read=False).all()
    for m in unread:
        m.is_read = True
    db.session.commit()
    return jsonify(out)


# --- Group management ---
@app.route("/api/group/create", methods=["POST"])
@login_required
def create_group():
    data = request.form or request.json or {}
    name = data.get("name")
    description = data.get("description")
    # group profile picture optional
    profile = None
    if "profile_photo" in request.files:
        f = request.files["profile_photo"]
        profile = file_save(f, subfolder="groups")
    if not name:
        return jsonify({"error": "Group name required"}), 400
    g = Group(name=name, description=description, profile_photo=profile, creator_id=current_user.id)
    db.session.add(g)
    db.session.commit()
    # add creator to members
    insert_stmt = group_members.insert().values(group_id=g.id, user_id=current_user.id, is_admin=True)
    db.session.execute(insert_stmt)
    db.session.commit()
    return jsonify({"success": True, "group": g.to_dict()}), 201


@app.route("/api/group/<int:group_id>/add_member", methods=["POST"])
@login_required
def add_group_member(group_id):
    data = request.form or request.json or {}
    user_id = int(data.get("user_id"))
    group = Group.query.get_or_404(group_id)
    # permission check: only admins/creator can add if allow_members_add is False
    # find if current_user is admin
    gm = db.session.query(group_members).filter_by(group_id=group_id, user_id=current_user.id).first()
    is_admin = bool(gm and gm.is_admin) if gm else False
    if not (is_admin or group.allow_members_add):
        return jsonify({"error": "Not permitted to add members"}), 403
    # add
    existing = db.session.query(group_members).filter_by(group_id=group_id, user_id=user_id).first()
    if existing:
        return jsonify({"error": "User already member"}), 400
    insert_stmt = group_members.insert().values(group_id=group_id, user_id=user_id, is_admin=False)
    db.session.execute(insert_stmt)
    db.session.commit()
    db.session.add(Notification(user_id=user_id, content=f"You were added to group {group.name}", type="group"))
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/group/<int:group_id>/members", methods=["GET"])
@login_required
def group_members_list(group_id):
    group = Group.query.get_or_404(group_id)
    members = db.session.query(group_members).filter_by(group_id=group_id).all()
    out = []
    for mem in members:
        uid = mem.user_id
        u = User.query.get(uid)
        out.append({"user": u.to_dict(minimal=True), "is_admin": bool(mem.is_admin)})
    return jsonify(out)


@app.route("/api/group/<int:group_id>/leave", methods=["POST"])
@login_required
def group_leave(group_id):
    group = Group.query.get_or_404(group_id)
    db.session.execute(group_members.delete().where((group_members.c.group_id == group_id) & (group_members.c.user_id == current_user.id)))
    db.session.commit()
    return jsonify({"success": True})


# --- Notifications ---
@app.route("/api/notifications", methods=["GET"])
@login_required
def get_notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(100).all()
    out = []
    for n in notifs:
        out.append({"id": n.id, "content": n.content, "type": n.type, "is_read": n.is_read, "created_at": n.created_at.isoformat()})
    return jsonify(out)


@app.route("/api/notifications/mark_read", methods=["POST"])
@login_required
def mark_notifications_read():
    data = request.form or request.json or {}
    nid = data.get("id")
    if nid:
        n = Notification.query.get(int(nid))
        if n and n.user_id == current_user.id:
            n.is_read = True
            db.session.commit()
            return jsonify({"success": True})
        return jsonify({"error": "Not found"}), 404
    else:
        Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
        db.session.commit()
        return jsonify({"success": True})


# --- Admin actions & dashboard endpoints ---
@app.route("/api/admin/users", methods=["GET"])
@login_required
@admin_required
def admin_list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users])


@app.route("/api/admin/ban_user", methods=["POST"])
@login_required
@admin_required
def admin_ban_user():
    data = request.form or request.json or {}
    user_id = data.get("user_id")
    action = data.get("action")  # ban/unban/delete
    u = User.query.get_or_404(user_id)
    if action == "ban":
        u.is_banned = True
        db.session.commit()
        db.session.add(AdminAction(admin_id=current_user.id, action=f"Banned user {u.username}"))
        db.session.commit()
        return jsonify({"success": True})
    elif action == "unban":
        u.is_banned = False
        db.session.commit()
        db.session.add(AdminAction(admin_id=current_user.id, action=f"Unbanned user {u.username}"))
        db.session.commit()
        return jsonify({"success": True})
    elif action == "delete":
        # delete everything about that user
        # remove files
        for p in u.posts:
            if p.media_path:
                try:
                    os.remove(os.path.join(BASE_DIR, p.media_path))
                except:
                    pass
        db.session.delete(u)
        db.session.commit()
        db.session.add(AdminAction(admin_id=current_user.id, action=f"Deleted user {u.username}"))
        db.session.commit()
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Unknown action"}), 400


@app.route("/api/admin/reports", methods=["GET"])
@login_required
@admin_required
def admin_reports():
    reports = Report.query.filter_by(resolved=False).order_by(Report.created_at.desc()).all()
    out = []
    for r in reports:
        out.append({"id": r.id, "reporter_id": r.reporter_id, "reported_user_id": r.reported_user_id, "reported_post_id": r.reported_post_id, "message": r.message, "created_at": r.created_at.isoformat()})
    return jsonify(out)


@app.route("/api/admin/resolve_report", methods=["POST"])
@login_required
@admin_required
def resolve_report():
    data = request.form or request.json or {}
    report_id = data.get("report_id")
    action = data.get("action")  # warn/ban/delete_post/ignore
    r = Report.query.get_or_404(report_id)
    r.resolved = True
    db.session.commit()
    if action == "warn":
        # send system notification to reported user
        db.session.add(Notification(user_id=r.reported_user_id, content="You have received a warning from admin", type="system"))
        db.session.commit()
    elif action == "ban":
        u = User.query.get(r.reported_user_id)
        if u:
            u.is_banned = True
            db.session.commit()
    elif action == "delete_post" and r.reported_post_id:
        p = Post.query.get(r.reported_post_id)
        if p:
            try:
                if p.media_path:
                    os.remove(os.path.join(BASE_DIR, p.media_path))
            except:
                pass
            db.session.delete(p)
            db.session.commit()
    db.session.add(AdminAction(admin_id=current_user.id, action=f"Resolved report {r.id} with action {action}"))
    db.session.commit()
    return jsonify({"success": True})


# --- Search endpoint ---
@app.route("/api/search", methods=["GET"])
@login_required
def search():
    q = request.args.get("q", "").strip()
    tab = request.args.get("tab", "all")  # all, users, groups, posts, reels
    if not q:
        return jsonify([])
    results = []
    if tab in ("all", "users"):
        users = User.query.filter(User.real_name.ilike(f"{q}%") | User.username.ilike(f"{q}%")).limit(50).all()
        results.extend([{"type": "user", "data": u.to_dict(minimal=True)} for u in users])
    if tab in ("all", "groups"):
        groups = Group.query.filter(Group.name.ilike(f"%{q}%")).limit(50).all()
        results.extend([{"type": "group", "data": g.to_dict(minimal=True)} for g in groups])
    if tab in ("all", "posts"):
        posts = Post.query.filter(Post.description.ilike(f"%{q}%")).limit(50).all()
        results.extend([{"type": "post", "data": p.to_dict()} for p in posts])
    if tab in ("all", "reels"):
        reels = Reel.query.filter(Reel.description.ilike(f"%{q}%")).limit(50).all()
        results.extend([{"type": "reel", "data": r.to_dict()} for r in reels])
    return jsonify(results)


# --- Misc utility endpoints (save post, repost, report user, block) ---
@app.route("/api/post/<int:post_id>/save", methods=["POST"])
@login_required
def save_post(post_id):
    # simplistic save: create a notification to the user (or a saved table)
    # For full functionality we should have a saved_posts table; create minimal implementation
    # create PostComment with special flag? Instead, store saved posts in user's bio string (not ideal).
    # Implement saved_posts table quickly:
    if not hasattr(db, "SavedPost"):
        class SavedPost(db.Model):
            __tablename__ = "saved_post"
            id = db.Column(db.Integer, primary_key=True)
            user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
            post_id = db.Column(db.Integer, db.ForeignKey("post.id"))
            created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
        db.SavedPost = SavedPost
        db.create_all()
    SavedPost = getattr(db, "SavedPost")
    exists = SavedPost.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if exists:
        db.session.delete(exists)
        db.session.commit()
        return jsonify({"success": True, "action": "unsaved"})
    sp = SavedPost(user_id=current_user.id, post_id=post_id)
    db.session.add(sp)
    db.session.commit()
    return jsonify({"success": True, "action": "saved"})


@app.route("/api/user/<int:user_id>/block", methods=["POST"])
@login_required
def block_user(user_id):
    # simplistic block: unsubscribe and mark in a blocks table
    if not hasattr(db, "Block"):
        class Block(db.Model):
            __tablename__ = "blocks"
            id = db.Column(db.Integer, primary_key=True)
            blocker_id = db.Column(db.Integer, db.ForeignKey("user.id"))
            blocked_id = db.Column(db.Integer, db.ForeignKey("user.id"))
            created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
        db.Block = Block
        db.create_all()
    Block = getattr(db, "Block")
    exists = Block.query.filter_by(blocker_id=current_user.id, blocked_id=user_id).first()
    if exists:
        db.session.delete(exists)
        db.session.commit()
        return jsonify({"success": True, "action": "unblocked"})
    b = Block(blocker_id=current_user.id, blocked_id=user_id)
    # also unfollow both ways
    u = User.query.get(user_id)
    if u:
        current_user.unfollow(u)
        u.unfollow(current_user)
    db.session.add(b)
    db.session.commit()
    return jsonify({"success": True, "action": "blocked"})


# --- Admin system broadcast ---
@app.route("/api/admin/broadcast", methods=["POST"])
@login_required
@admin_required
def admin_broadcast():
    data = request.form or request.json or {}
    message = data.get("message")
    if not message:
        return jsonify({"error": "message required"}), 400
    users = User.query.all()
    for u in users:
        db.session.add(Notification(user_id=u.id, content=message, type="system"))
    db.session.commit()
    db.session.add(AdminAction(admin_id=current_user.id, action=f"Broadcasted message"))
    db.session.commit()
    return jsonify({"success": True})


# --- Health check ---
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": datetime.datetime.utcnow().isoformat()})


# --- Error handlers ---
@app.errorhandler(413)
def file_too_large(e):
    return jsonify({"error": "File too large"}), 413


# --- Run app ---
if __name__ == "__main__":
    # Ensure DB exists
    db.create_all()
    # Create uploads subfolders
    for s in ["profiles", "posts", "reels", "stories", "messages", "groups"]:
        os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], s), exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5000)
