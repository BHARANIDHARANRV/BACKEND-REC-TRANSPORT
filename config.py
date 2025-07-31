import os
from typing import List
from pydantic_settings import BaseSettings
from pathlib import Path

# Get the current directory
current_dir = Path(__file__).parent
env_path = current_dir / ".env"

print(f"🔍 Looking for .env file at:")
print(f"   Current directory: {env_path}")

if env_path.exists():
    print(f"✅ .env file found: {env_path}")
else:
    print(f"❌ .env file not found")

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "RideShare API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # MongoDB Configuration
    # Don't set default here - let it be loaded from .env file
    MONGODB_URL: str = "mongodb://localhost:27017"  # Default fallback
    MONGODB_DATABASE: str = "rideshare"
    MONGODB_MAX_POOL_SIZE: int = 100
    MONGODB_MIN_POOL_SIZE: int = 10
    MONGODB_MAX_IDLE_TIME_MS: int = 30000
    MONGODB_CONNECT_TIMEOUT_MS: int = 20000
    MONGODB_SERVER_SELECTION_TIMEOUT_MS: int = 5000
    
    # Redis (for caching and sessions)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: str = ""
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Google Maps API
    GOOGLE_MAPS_API_KEY: str = ""
    
    # Monitoring
    SENTRY_DSN: str = ""
    ENABLE_METRICS: bool = True
    
    # Background tasks
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # File uploads
    MAX_FILE_SIZE: int = 10 * 1024 * 1024 # 10MB
    UPLOAD_DIR: str = "uploads"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    class Config:
        # Look for .env file in current directory
        env_file = str(env_path)
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra fields from environment

# Create settings instance
settings = Settings()

# Environment-specific configurations
def get_mongodb_url():
    """Get MongoDB URL based on environment"""
    # Priority: Settings (from .env) > Environment variable > Local MongoDB
    mongodb_url = settings.MONGODB_URL
    
    if mongodb_url and mongodb_url != "mongodb://localhost:27017":
        print(f"🔗 Using MongoDB URL from .env file: {mongodb_url[:50]}...")
        return mongodb_url
    elif os.getenv("MONGODB_URL"):
        mongodb_url = os.getenv("MONGODB_URL")
        print(f"🔗 Using MongoDB URL from environment: {mongodb_url[:50]}...")
        return mongodb_url
    elif os.getenv("ENVIRONMENT") == "production":
        # For production, you can set up MongoDB Atlas
        # mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        print(f"🔗 Using production MongoDB URL: {mongodb_url[:50]}...")
        return mongodb_url
    else:
        # For development, use local MongoDB
        print("🔗 Using local MongoDB URL: mongodb://localhost:27017")
        return "mongodb://localhost:27017"

def get_redis_url():
    """Get Redis URL based on environment"""
    if os.getenv("REDIS_URL"):
        return os.getenv("REDIS_URL")
    elif os.getenv("ENVIRONMENT") == "production":
        return os.getenv("REDIS_URL", "redis://localhost:6379")
    else:
        return "redis://localhost:6379"

# Update settings with environment-specific values
settings.MONGODB_URL = get_mongodb_url()
settings.REDIS_URL = get_redis_url()

# Print current configuration for debugging
print(f"🔧 Current MongoDB Configuration:")
print(f"   MONGODB_URL: {settings.MONGODB_URL[:50]}...")
print(f"   MONGODB_DATABASE: {settings.MONGODB_DATABASE}")
print(f"   ENVIRONMENT: {os.getenv('ENVIRONMENT', 'development')}") 