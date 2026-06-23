from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Student Internship Portal"
    environment: str = "development"
    secret_key: str = "change-this-secret-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    database_url: str = "sqlite:///./internship_portal.db"
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    backend_cors_origin_regex: str | None = (
        r"https?://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|"
        r"192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?"
    )
    aws_region: str = "ap-southeast-1"
    s3_bucket_name: str | None = None
    s3_public_base_url: str | None = None
    aws_access_key_id: str | None = Field(default=None, repr=False)
    aws_secret_access_key: str | None = Field(default=None, repr=False)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
