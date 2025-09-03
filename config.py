# config.py
import os

# Secret key for session management
SECRET_KEY = os.urandom(24)

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASS = 'Admin123!'  # Change this in production

# Database configuration
DATABASE = 'sociafam.db'
