import os

# Basic configuration
SECRET_KEY = os.environ.get('SECRET_KEY', '09da35833ef9cb699888f08d66a0cfb827fb10e53f6c1549')
UPLOAD_FOLDER = 'static/uploads'

# Admin credentials
ADMIN_USERNAME = 'Henry'
ADMIN_PASS = 'Dec@2003'

# Ensure upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
