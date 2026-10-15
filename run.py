"""Start the app:  python run.py   ->  http://127.0.0.1:5000"""
from pathlib import Path

from app import config, create_app

app = create_app()

if __name__ == "__main__":
    if config.DB_BACKEND == "sqlite" and not Path(config.SQLITE_PATH).exists():
        raise SystemExit("Database not found. Run:  python scripts/init_db.py")
    app.run(host="127.0.0.1", port=5000, debug=False)
