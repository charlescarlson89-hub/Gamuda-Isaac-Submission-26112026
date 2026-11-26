"""Server-only configuration; no secret values belong in browser assets."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ENV = Path(os.getenv("LOCALAPPDATA", Path.home() / ".config")) / "SoilSyncRemake" / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Private local values override project defaults; process env still wins in deployment.
        env_file=(BACKEND_ROOT / ".env", PRIVATE_ENV),
        env_file_encoding="utf-8",
        extra="ignore",
    )
    app_env: Literal["development", "test", "production"] = "development"
    database_url: SecretStr = SecretStr("")
    admin_database_url: SecretStr = SecretStr("")
    admin_user_ids: list[Annotated[int, Field(strict=True, gt=0)]] = Field(
        default_factory=list,
        description="Account IDs allowed to list users. Empty denies all admin access.",
    )
    frontend_origins: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173","http://127.0.0.1:8001","http://localhost:8001",]
    cookie_secure: bool = False
    session_hours: int = Field(default=24, ge=1, le=168)
    gemini_api_key: SecretStr = SecretStr("")
    gemini_model: str = ""
    gemini_demo_user_id: int | None = Field(default=None, gt=0)
    gemini_personal_key_encryption: SecretStr = SecretStr("")
    gemini_personal_key_user_ids: list[Annotated[int, Field(strict=True, gt=0)]] = Field(
        default_factory=list
    )
    gemini_require_personal_key: bool = False
    mongodb_recipe_uri: SecretStr = SecretStr("")
    mongodb_recipe_database: str = "soilsync"
    firebase_project_id: str = ""
    firebase_storage_bucket: str = ""
    storage_emulator_host: str = ""
    google_application_credentials: str = ""
    upload_storage: Literal["local", "firebase", "postgres"] = "local"

    @classmethod
    def settings_customise_sources(
        cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings
    ):
        if os.getenv("SOILSYNC_USE_SAVED_DATABASES") != "1":
            return init_settings, env_settings, dotenv_settings, file_secret_settings

        def saved_databases():
            saved = dotenv_settings()
            return {
                key: saved[key]
                for key in ("database_url", "mongodb_recipe_uri", "mongodb_recipe_database")
                if saved.get(key)
            }

        return init_settings, saved_databases, env_settings, dotenv_settings, file_secret_settings


@lru_cache
def get_settings() -> Settings:
    return Settings()
