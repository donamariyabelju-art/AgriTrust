import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'agritrust-secret-key-2026-production')
    
    # MySQL Database Config
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'agritrust_db')
    
    # Try MySQL URI by default
    MYSQL_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    SQLITE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'agritrust.db')}"
    
    # Database selection with auto fallback support
    USE_SQLITE_FALLBACK = os.getenv('USE_SQLITE_FALLBACK', 'True').lower() in ('true', '1', 't')
    
    # We will determine the active URI in app initialization or use SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or (SQLITE_URI if USE_SQLITE_FALLBACK and not DB_PASSWORD else MYSQL_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    # Optional Services
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', '')
    AI_API_KEY = os.getenv('AI_API_KEY', '')
    
    # Model path
    DISEASE_MODEL_PATH = os.path.join(BASE_DIR, 'ai', 'models', 'crop_disease_model.h5')
