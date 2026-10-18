"""Local configuration; secrets belong in the ignored repository-root .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


def login_credentials():
    return os.environ.get("GAMBIT_USERNAME", ""), os.environ.get("GAMBIT_PASSWORD", "")
