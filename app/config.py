"""Configuration - read from environment variables (see .env.example).

Default backend is SQLite so the project runs with zero setup.
Set DB_BACKEND=mysql (and the MYSQL_* variables) to use MySQL instead.
No passwords or secrets are stored in the source code.
"""
import os
import secrets
from pathlib import Path

try:  # optional: load a local .env file if python-dotenv is installed
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

DB_BACKEND = os.getenv("DB_BACKEND", "sqlite").lower()          # 'sqlite' or 'mysql'
SQLITE_PATH = os.getenv("SQLITE_PATH", str(BASE_DIR / "instance" / "payroll.db"))

MYSQL = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "payroll_db"),
}

# Signs the login session cookie. If SECRET_KEY is not set, a random one is generated at start-up
# (everyone is simply signed out when the app restarts). Set your own in .env for a stable value.
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)

# Forgot-password: reset links are signed, expire and work once. This demo has no e-mail server, so the link is
# shown on screen (SHOW_RESET_LINK=1). In a real deployment set it to 0 and e-mail the link instead.
RESET_TOKEN_MINUTES = int(os.getenv("RESET_TOKEN_MINUTES", "15"))
SHOW_RESET_LINK = os.getenv("SHOW_RESET_LINK", "1") == "1"
