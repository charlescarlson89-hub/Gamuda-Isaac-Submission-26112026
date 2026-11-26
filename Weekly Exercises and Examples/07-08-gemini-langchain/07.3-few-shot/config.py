"""Read private backend settings. No secrets are sent to React."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

# Project .env contains shareable settings such as the chosen model.
load_dotenv(Path(__file__).with_name(".env"))

# Documents is synced by OneDrive on this computer. Keep the real key outside it.
PRIVATE_ENV = Path(os.getenv("LOCALAPPDATA", Path.home() / ".config")) / "KazuAiLab" / ".env"
PRIVATE_SETTINGS = dotenv_values(PRIVATE_ENV)


@dataclass(frozen=True)
class Settings:
    api_key: str = field(repr=False)
    model: str = "gemini-3.5-flash-lite"

    @property
    def configured(self) -> bool:
        return bool(self.api_key.strip())


def get_settings() -> Settings:
    return Settings(
        api_key=(PRIVATE_SETTINGS.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", "")).strip(),
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip(),
    )
