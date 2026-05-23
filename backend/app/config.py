"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_name: str = "MPC Autofill"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    allowed_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: str = "sqlite+aiosqlite:///./mpc_autofill.db"

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"

    # Google Drive (service account for community drives)
    google_service_account_key_path: str = ""

    # S3-compatible storage
    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket_name: str = "mpc-autofill-uploads"
    s3_public_url: str = ""

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24 * 7  # 7 days

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
