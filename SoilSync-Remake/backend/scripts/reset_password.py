"""Local operator recovery: hidden password entry and atomic session revocation.

Requires the operator's database configuration. There is no public reset API,
password command-line argument, temporary shared password or login bypass.
"""

import argparse
import getpass
import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import SecretStr
from sqlalchemy import delete, select

from app.config import BACKEND_ROOT
from app.database import session_factory
from app.models import AuthSession, User
from app.schemas import Registration
from app.security import passwords


def reset_account_password(db, user_id: int, new_password: SecretStr):
    """Caller commits both changes together; never alter progress or admin access."""
    Registration.valid_password(new_password)
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None:
        raise ValueError("Account not found. No password was changed.")
    user.password = passwords.hash(new_password.get_secret_value())
    db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    db.flush()
    return user.username


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--user-id", type=int, required=True, help="Existing account ID to recover."
    )
    args = parser.parse_args()
    if args.user_id < 1:
        parser.error("Use a positive account ID.")
    if not sys.stdin.isatty():
        print("Open an interactive terminal to reset a password. Piped password input is refused.")
        return 1
    try:
        factory = session_factory()
        with factory() as db:
            username = db.scalar(select(User.username).where(User.id == args.user_id))
        if username is None:
            print("Account not found. No password was changed.")
            return 1
        print(f"SoilSync password recovery: {username} (user ID {args.user_id})")
        print("Choose a password of 12-128 characters. Input stays hidden.")
        print("Saving will sign this account out on all devices and keep its progress.")
        with warnings.catch_warnings():
            # Never fall back to visible/echoed password entry in an unsupported console.
            warnings.simplefilter("error", getpass.GetPassWarning)
            for _ in range(3):
                password = SecretStr(getpass.getpass("New password: "))
                try:
                    Registration.valid_password(password)
                except ValueError:
                    print("Use between 12 and 128 characters. Nothing has been changed.")
                    continue
                confirmation = SecretStr(getpass.getpass("Confirm new password: "))
                if password != confirmation:
                    print("Passwords did not match. Nothing has been changed.")
                    continue
                with factory.begin() as db:
                    username = reset_account_password(db, args.user_id, password)
                break
            else:
                print("No password was changed. Run the command again when ready.")
                return 1
    except (KeyboardInterrupt, EOFError):
        print("\nRecovery cancelled.")
        return 1
    except getpass.GetPassWarning:
        print("Hidden input is unavailable. Run this command in a normal interactive terminal.")
        return 1
    except Exception as error:
        # Database/provider exceptions may include connection details. Never print them.
        print(f"Recovery could not complete ({type(error).__name__}). Check the local database.")
        return 1

    # Non-secret completion receipt lets the helper confirm success without seeing a password.
    receipt = BACKEND_ROOT / ".runtime" / "account-recovery" / f"user-{args.user_id}.json"
    try:
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(
            json.dumps(
                {
                    "status": "completed",
                    "user_id": args.user_id,
                    "username": username,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }
            ),
            encoding="utf-8",
        )
    except OSError:
        print("Password saved, but the local completion receipt could not be written.")
    print(f"Password saved for {username}. Previous sessions are signed out.")
    print("Log in at http://127.0.0.1:5173/#/login using your new password.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
