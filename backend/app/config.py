from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_URL = f"sqlite:///{(BACKEND_DIR / 'internship_portal.db').as_posix()}"


class Settings(BaseSettings):
    app_name: str = "Student Internship Portal"
    environment: str = "development"
    secret_key: str = "change-this-secret-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    refresh_cookie_name: str = "refresh_token"
    refresh_cookie_secure: bool = True
    refresh_cookie_samesite: str = "lax"
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 300
    database_url: str = DEFAULT_DATABASE_URL
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    backend_cors_origin_regex: str | None = (
        r"https?://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|"
        r"192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?"
    )
    aws_region: str = "ap-southeast-1"
    s3_bucket_name: str | None = None
    s3_presigned_url_expire_seconds: int = 300
    aws_access_key_id: str | None = Field(default=None, repr=False)
    aws_secret_access_key: str | None = Field(default=None, repr=False)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("backend_cors_origin_regex", mode="before")
    @classmethod
    def empty_cors_regex_to_none(cls, value):
        if value == "":
            return None
        return value

    @field_validator("refresh_cookie_samesite", mode="before")
    @classmethod
    def normalize_cookie_samesite(cls, value):
        return str(value or "lax").strip().lower()

    @model_validator(mode="after")
    def validate_cookie_and_cors_settings(self):
        allowed_samesite_values = {"lax", "strict", "none"}
        if self.refresh_cookie_samesite not in allowed_samesite_values:
            raise ValueError("REFRESH_COOKIE_SAMESITE must be one of: lax, strict, none")
        if self.refresh_cookie_samesite == "none" and not self.refresh_cookie_secure:
            raise ValueError("REFRESH_COOKIE_SECURE must be true when REFRESH_COOKIE_SAMESITE=none")

        if self.environment.lower() == "production":
            origins = self.cors_origins
            if not origins:
                raise ValueError("BACKEND_CORS_ORIGINS must include the production frontend HTTPS domain")
            if "*" in origins:
                raise ValueError("BACKEND_CORS_ORIGINS cannot use wildcard origins in production")
            insecure_origins = [origin for origin in origins if not origin.startswith("https://")]
            if insecure_origins:
                raise ValueError("Production CORS origins must use https://")
            if self.backend_cors_origin_regex:
                raise ValueError("BACKEND_CORS_ORIGIN_REGEX must be empty in production")
            if not self.refresh_cookie_secure:
                raise ValueError("REFRESH_COOKIE_SECURE must be true in production")
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.environment.lower() == "production":
        weak_secret = settings.secret_key == "change-this-secret-in-production" or len(settings.secret_key) < 32
        if weak_secret:
            raise RuntimeError("Set SECRET_KEY to a strong production secret with at least 32 characters")
    return settings
