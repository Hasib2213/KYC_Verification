import os
from dotenv import load_dotenv

load_dotenv()

# Environment - sandbox বা production
ENV = os.getenv("SUMSUB_ENV", "sandbox").lower()

class Settings:
    # Environment configuration
    ENVIRONMENT = ENV
    
    # API credentials - আপনার credentials এ sbx: prefix মানে sandbox
    SUMSUB_API_KEY = os.getenv("SUMSUB_API_KEY")
    SUMSUB_API_SECRET = os.getenv("SUMSUB_API_SECRET")
    
    # Base URL - environment অনুযায়ী পরিবর্তিত হবে
    if ENV == "sandbox":
        SUMSUB_BASE_URL = "https://api.sandbox.sumsub.com"
    else:
        SUMSUB_BASE_URL = "https://api.sumsub.com"
    
    SUMSUB_WEBHOOK_SECRET = os.getenv("SUMSUB_WEBHOOK_SECRET")
    SUMSUB_LEVEL_NAME = os.getenv("SUMSUB_LEVEL_NAME", "basic-kyc-level")
    
    # ==================== PostgreSQL Configuration ====================
    # Database connection string
    # Format: postgresql://username:password@localhost:5432/database_name
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "kyc_verification")
    
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # SQLAlchemy configuration
    SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False") == "True"
    SQLALCHEMY_POOL_SIZE = int(os.getenv("SQLALCHEMY_POOL_SIZE", "10"))
    SQLALCHEMY_MAX_OVERFLOW = int(os.getenv("SQLALCHEMY_MAX_OVERFLOW", "20"))
    
    APP_NAME = "KYC Verification API"
    VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False") == "True"
    
    @classmethod
    def get_environment_info(cls):
        """Get current environment info"""
        return {
            "environment": cls.ENVIRONMENT,
            "base_url": cls.SUMSUB_BASE_URL,
            "is_sandbox": cls.ENVIRONMENT == "sandbox",
            "debug": cls.DEBUG
        }

settings = Settings()