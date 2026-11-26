"""Private settings precedence without accessing or exposing real credentials."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_database_import_does_not_inject_project_defaults_into_process_environment():
    # dotenv injection previously let blank project defaults hide the private key/DB.
    env = dict(os.environ)
    for key in ("GEMINI_API_KEY", "DATABASE_URL"):
        env.pop(key, None)
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import os; import app.database; "
            "assert 'GEMINI_API_KEY' not in os.environ; assert 'DATABASE_URL' not in os.environ",
        ],
        env=env,
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        capture_output=True,
        timeout=20,
    )


def test_private_file_overrides_project_defaults_and_keeps_other_settings(tmp_path, monkeypatch):
    for key in ("GEMINI_API_KEY", "DATABASE_URL", "GEMINI_MODEL"):
        monkeypatch.delenv(key, raising=False)
    project, private = tmp_path / "project.env", tmp_path / "private.env"
    project.write_text(
        "GEMINI_API_KEY=project-fixture\nDATABASE_URL=project-fixture\nGEMINI_MODEL=fixture-model\n"
    )
    private.write_text("GEMINI_API_KEY=private-fixture\nDATABASE_URL=private-db-fixture\n")
    settings = Settings(_env_file=(project, private))
    assert settings.gemini_api_key.get_secret_value() == "private-fixture"
    assert settings.database_url.get_secret_value() == "private-db-fixture"
    assert settings.gemini_model == "fixture-model"
    assert "private-fixture" not in repr(settings)
    assert "private-db-fixture" not in repr(settings)


def test_missing_private_file_keeps_existing_project_config_compatible(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    project = tmp_path / "project.env"
    project.write_text("GEMINI_API_KEY=project-fixture\n")
    assert (
        Settings(_env_file=(project, tmp_path / "absent.env")).gemini_api_key.get_secret_value()
        == "project-fixture"
    )


def test_process_environment_overrides_files_for_deployment(tmp_path, monkeypatch):
    private = tmp_path / "private.env"
    private.write_text("GEMINI_API_KEY=file-fixture\n")
    monkeypatch.setenv("GEMINI_API_KEY", "process-fixture")
    assert Settings(_env_file=private).gemini_api_key.get_secret_value() == "process-fixture"


def test_dev_launcher_prefers_saved_database_connections(tmp_path, monkeypatch):
    config = tmp_path / "project.env"
    config.write_text("DATABASE_URL=saved-db-fixture\nMONGODB_RECIPE_URI=saved-atlas-fixture\n")
    monkeypatch.setenv("DATABASE_URL", "terminal-db-fixture")
    monkeypatch.setenv("MONGODB_RECIPE_URI", "terminal-atlas-fixture")
    monkeypatch.setenv("GEMINI_API_KEY", "terminal-gemini-fixture")
    monkeypatch.delenv("SOILSYNC_USE_SAVED_DATABASES", raising=False)
    assert Settings(_env_file=config).database_url.get_secret_value() == "terminal-db-fixture"

    monkeypatch.setenv("SOILSYNC_USE_SAVED_DATABASES", "1")
    settings = Settings(_env_file=config)
    assert settings.database_url.get_secret_value() == "saved-db-fixture"
    assert settings.mongodb_recipe_uri.get_secret_value() == "saved-atlas-fixture"
    assert settings.gemini_api_key.get_secret_value() == "terminal-gemini-fixture"
    assert Settings(_env_file=None).database_url.get_secret_value() == "terminal-db-fixture"


def test_admin_allowlist_is_disabled_by_default_and_accepts_only_positive_integer_ids(monkeypatch):
    monkeypatch.delenv("ADMIN_USER_IDS", raising=False)
    assert Settings(_env_file=None).admin_user_ids == []
    assert Settings(_env_file=None, admin_user_ids=[26]).admin_user_ids == [26]
    for invalid in ([0], [-1], [True], ["26"]):
        with pytest.raises(ValidationError):
            Settings(_env_file=None, admin_user_ids=invalid)
