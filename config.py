# app/core/config.py
import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    # Application settings
    APP_NAME: str = "AI Role Matcher"
    API_PREFIX: str = "/api"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # MongoDB settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "role_matcher_db")
    
    # Google Gemini settings
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # File upload settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "very_secret_key_change_in_production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

# Create settings instance
settings = Settings()

# Create .env.example file for reference
def create_env_example():
    with open(".env.example", "w") as f:
        f.write("""# Application settings
DEBUG=False

# MongoDB settings
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=role_matcher_db

# Google Gemini settings
GOOGLE_API_KEY=your_gemini_api_key_here

# File upload settings
UPLOAD_DIR=uploads

# Security settings
SECRET_KEY=very_secret_key_change_in_production
ACCESS_TOKEN_EXPIRE_MINUTES=10080
""")

if __name__ == "__main__":
    create_env_example()