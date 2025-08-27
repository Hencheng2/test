-- schema.sql

-- Drop existing tables (order matters due to foreign key constraints)
-- Dropping tables in reverse order of creation to respect foreign key dependencies.
DROP TABLE IF EXISTS blocked_users;
DROP TABLE IF EXISTS reports;
DROP TABLE IF EXISTS warnings;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS stories;
DROP TABLE IF EXISTS reels;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS groups;
DROP TABLE IF EXISTS chat_messages;
DROP TABLE IF EXISTS chat_room_members;
DROP TABLE IF EXISTS chat_rooms;
DROP TABLE IF EXISTS friendships;
DROP TABLE IF EXISTS members;
DROP TABLE IF EXISTS users;


-- Table: users
-- Stores core user account information and general settings.
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,           -- Unique username for login and profile URLs
    originalName TEXT NOT NULL,             -- User's real name for display
    password_hash TEXT NOT NULL,            -- Hashed password for security
    is_admin INTEGER DEFAULT 0,             -- 0 for regular user, 1 for administrator
    theme_preference TEXT DEFAULT 'light',  -- 'light' or 'dark' theme choice
    chat_background_image_path TEXT,        -- Path to a custom chat background image
    unique_key TEXT UNIQUE NOT NULL,        -- Unique key for password recovery (e.g., "AB12")
    password_reset_pending INTEGER DEFAULT 0, -- 1 if a password reset has been initiated
    reset_request_timestamp TIMESTAMP,      -- When the password reset was requested
    last_login_at TIMESTAMP,                -- Last time the user logged in
    last_seen_at TIMESTAMP                  -- Last time the user was active on the site (for online status)
);


-- Table: members
-- Stores extended profile information for regular users. Admins do not have an entry here.
CREATE TABLE members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fullName TEXT NOT NULL,                 -- Full name of the family member
    email TEXT UNIQUE,                      -- Email for communication/password reset
    dateOfBirth TEXT,
    gender TEXT,                            -- Male, Female, Prefer not to say
    profilePhoto TEXT,                      -- Path to profile picture
    bio TEXT,
    location TEXT,
    coverPhoto TEXT,                        -- Path to cover photo
    status TEXT DEFAULT 'active',           -- 'active', 'inactive', 'suspended'
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- Table: friendships
-- Stores friendship status between users.
CREATE TABLE friendships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,
    status TEXT NOT NULL,                   -- 'pending', 'accepted', 'declined'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (user1_id, user2_id)
);


-- Table: chat_rooms
-- Stores information about individual and group chat rooms.
CREATE TABLE chat_rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    is_group INTEGER DEFAULT 0,             -- 0 for individual chat, 1 for group chat
    name TEXT,                              -- Name of the chat room (only for groups)
    creator_id INTEGER,                     -- The user who created the group chat
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE SET NULL
);


-- Table: chat_room_members
-- Links users to chat rooms.
CREATE TABLE chat_room_members (
    chat_room_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (chat_room_id, user_id),
    FOREIGN KEY (chat_room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- Table: chat_messages
-- Stores individual chat messages.
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_room_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    content TEXT,                           -- Text content of the message
    media_path TEXT,                        -- Path to image, video, or voice note
    media_type TEXT,                        -- 'image', 'video', 'audio'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read INTEGER DEFAULT 0,              -- 0 for unread, 1 for read
    FOREIGN KEY (chat_room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
);


-- Table: groups
-- Stores information about groups within the family tree.
CREATE TABLE groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    photo TEXT,                             -- Path to group's profile photo
    created_by INTEGER NOT NULL,            -- User who created the group
    visibility TEXT DEFAULT 'public',       -- 'public', 'private', 'hidden'
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);


-- Table: posts
-- Stores user posts, including text and media.
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,               -- The user who created the post
    content TEXT,                           -- The text content of the post
    media_path TEXT,                        -- Path to image or video
    media_type TEXT,                        -- 'image', 'video'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    visibility TEXT DEFAULT 'public',       -- 'public', 'friends_only', 'private'
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- Table: reels
-- Stores short video content (reels).
CREATE TABLE reels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    media_path TEXT NOT NULL,
    caption TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- Table: stories
-- Stores temporary photo or video stories.
CREATE TABLE stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    media_path TEXT NOT NULL,
    media_type TEXT NOT NULL,               -- 'image', 'video'
    caption TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,          -- When the story will be deleted (e.g., 24 hours after creation)
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- Table: notifications
-- Stores notifications for users.
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receiver_id INTEGER NOT NULL,           -- The user who receives the notification
    sender_id INTEGER,                      -- The user who triggered the notification (optional)
    type TEXT NOT NULL,                     -- 'friend_request', 'like', 'comment', 'system_message', 'group_invite'
    message TEXT NOT NULL,                  -- The message to display
    link TEXT,                              -- Optional link to the related content
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read INTEGER DEFAULT 0,              -- 0 for unread, 1 for read
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE SET NULL
);


-- Table: warnings
-- Stores formal warnings issued by an admin to a user.
CREATE TABLE warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,               -- The user who received the warning
    issued_by_admin_id INTEGER NOT NULL,    -- The admin who issued the warning
    reason TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active',           -- 'active' or 'resolved'
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- Table: reports
-- Stores reports made by users against other content (users, groups, posts, reels, stories).
CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reported_by_user_id INTEGER NOT NULL,   -- The user who filed the report
    reported_item_type TEXT NOT NULL,       -- 'user', 'group', 'post', 'reel', 'story'
    reported_item_id INTEGER NOT NULL,      -- The ID of the specific item being reported
    reason TEXT NOT NULL,                   -- The reason for the report
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',          -- 'pending', 'handled', 'ignored'
    admin_notes TEXT,                       -- Notes added by an admin after reviewing the report
    FOREIGN KEY (reported_by_user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- Table: blocked_users
-- Records users who have been blocked by other users.
CREATE TABLE blocked_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    blocker_id INTEGER NOT NULL,            -- The user who performed the blocking
    blocked_id INTEGER NOT NULL,            -- The user who was blocked
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (blocker_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (blocked_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (blocker_id, blocked_id)         -- Ensures a user can only block another user once
);
