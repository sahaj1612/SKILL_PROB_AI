import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123-change-in-production'
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or ""
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or ""
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') or ""
    GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID') or ""
    GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET') or ""
    ADMIN_EMAILS = {email.strip().lower() for email in os.environ.get('ADMIN_EMAILS', '').split(',') if email.strip()}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', '').lower() == 'true'
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    SESSION_TYPE = 'filesystem'
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx'}
    
    # Interview settings
    QUESTION_TIME_LIMIT = 120  # seconds
    CODING_TIME_LIMIT = 600  # seconds
    
    # Database
    DATABASE = 'database.sqlite'
    
    # Gemini model
    GEMINI_MODEL = 'gemini-2.5-flash'  # Using the latest flash model
