"""
Configuration Settings
Centralized configuration for the Contact Management System
"""
import os
from dataclasses import dataclass


@dataclass
class DatabaseSettings:
    """Database configuration settings"""
    HOST: str = os.getenv("DB_HOST", "localhost")
    USER: str = os.getenv("DB_USER", "root")
    PASSWORD: str = os.getenv("DB_PASSWORD", "")
    CHARSET: str = os.getenv("DB_CHARSET", "utf8mb4")
    CONNECT_TIMEOUT: int = int(os.getenv("DB_TIMEOUT", "5"))
    MASTER_DB: str = os.getenv("MASTER_DB", "ondem_master_rb")


@dataclass
class AuthSettings:
    """Authentication configuration settings"""
    SECRET_KEY: str = os.getenv("SECRET_KEY", "paramantra-secret")
    ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    TOKEN_EXPIRE_MINUTES: int = int(os.getenv("TOKEN_EXPIRE_MINUTES", "30"))


@dataclass
class APISettings:
    """API configuration settings"""
    HOST: str = os.getenv("API_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("API_PORT", "8000"))
    RELOAD: bool = os.getenv("API_RELOAD", "true").lower() == "true"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # CORS settings
    CORS_ORIGINS: list = ["*"]  # Restrict in production
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]


@dataclass
class AppSettings:
    """Application settings"""
    APP_NAME: str = "Contact Management System"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API for contact management with authentication"


# Create instances
db_settings = DatabaseSettings()
auth_settings = AuthSettings()
api_settings = APISettings()
app_settings = AppSettings()


def get_database_config():
    """Get database configuration as dict"""
    return {
        "host": db_settings.HOST,
        "user": db_settings.USER,
        "password": db_settings.PASSWORD,
        "charset": db_settings.CHARSET,
        "connect_timeout": db_settings.CONNECT_TIMEOUT
    }


def get_auth_config():
    """Get authentication configuration as dict"""
    return {
        "secret_key": auth_settings.SECRET_KEY,
        "algorithm": auth_settings.ALGORITHM,
        "token_expire_minutes": auth_settings.TOKEN_EXPIRE_MINUTES
    }


def print_config():
    """Print current configuration (for debugging)"""
    print("\n=== Configuration Settings ===")
    print(f"\nDatabase:")
    print(f"  Host: {db_settings.HOST}")
    print(f"  User: {db_settings.USER}")
    print(f"  Password: {'*' * len(db_settings.PASSWORD) if db_settings.PASSWORD else 'Not Set'}")
    print(f"  Master DB: {db_settings.MASTER_DB}")
    
    print(f"\nAuthentication:")
    print(f"  Algorithm: {auth_settings.ALGORITHM}")
    print(f"  Token Expiry: {auth_settings.TOKEN_EXPIRE_MINUTES} minutes")
    print(f"  Secret Key: {'Set' if auth_settings.SECRET_KEY else 'Not Set'}")
    
    print(f"\nAPI:")
    print(f"  Host: {api_settings.HOST}")
    print(f"  Port: {api_settings.PORT}")
    print(f"  Debug: {api_settings.DEBUG}")
    print(f"  Reload: {api_settings.RELOAD}")
    
    print(f"\nApplication:")
    print(f"  Name: {app_settings.APP_NAME}")
    print(f"  Version: {app_settings.VERSION}")
    print("=" * 40 + "\n")


if __name__ == "__main__":
    print_config()