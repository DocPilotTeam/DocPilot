import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # GitHub OAuth
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
    GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI")
    GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    DEFAULT_GITHUB_TOKEN = os.getenv("DEFAULT_GITHUB_TOKEN", None)

    # JWT
    JWT_SECRET = os.getenv("JWT_SECRET", "magic")  # Change in production!
    JWT_ALGORITHM = "HS256"

    # Celery
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
settings = Settings()
