# Setup Instructions

Requirements: Python 3.10+ (developed on 3.13). Optional: MySQL 8 server. Windows, macOS and Linux all work.

## 1. SQLite (default - no server needed)
```bash
python -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/init_db.py            # --no-demo-payroll to start with nothing processed
python run.py                        # http://127.0.0.1:5000
```
Sign in as `admin` (or `hr`, `emp001`...`emp005`). The password is `DEMO_PASSWORD` from `.env` (default `Payroll@2026`).
`python scripts/init_db.py` rebuilds the database at any time - handy to reset the demo.

## 2. MySQL 8
1. In MySQL (as an admin) create an empty database and a user - choose your own password, never commit it:
   ```sql
   CREATE DATABASE payroll_db CHARACTER SET utf8mb4;
   CREATE USER 'payroll_user'@'localhost' IDENTIFIED BY '<your-password>';
   GRANT ALL ON payroll_db.* TO 'payroll_user'@'localhost';
   ```
2. Triggers: if the server has binary logging on (the MySQL 8 default) a non-SUPER user cannot create triggers.
   As an admin run once: `SET GLOBAL log_bin_trust_function_creators = 1;`  (init_db.py explains this if it hits error 1419).
3. `cp .env.example .env` (Windows: `copy .env.example .env`) and edit `DB_BACKEND=mysql` and the `MYSQL_*` values.
4. `python scripts/init_db.py` - **drops every table in that database** and recreates it - then `python run.py`.

Manual alternative with the mysql client: run `database/mysql/schema.sql`, `database/seed.sql`, `database/views.sql`, then the
triggers (use `DELIMITER //` around each trigger in `database/mysql/triggers.sql`; the `-- @@` lines mark the block boundaries),
and finally create users with `python scripts/init_db.py` (which does all of it).

**Verified:** the MySQL path was run on a real MySQL 8.0.46 server: schema, seed, views, triggers, demo payroll (identical totals to SQLite),
`queries.sql`, the web application, and an 11-test suite (`tests/test_mysql.py`). Other MySQL versions and MariaDB were not tested.

## 3. Tests
```bash
python -m unittest discover -s tests             # SQLite (74 tests)
PAYROLL_MYSQL_TESTS=1 MYSQL_USER=... MYSQL_PASSWORD=... MYSQL_DATABASE=payroll_test python -m unittest tests.test_mysql -v
```
Windows PowerShell: set variables with `$env:PAYROLL_MYSQL_TESTS="1"` etc.

## 4. Regenerating screenshots (optional)
```bash
pip install playwright && playwright install chromium
python scripts/capture_screenshots.py            # uses a throw-away database; instance/ is untouched
```

## 5. Rebuilding the presentations (optional, needs Node + pptxgenjs)
`scripts/pptx/review2.js` and `review3.js`. Not needed to run the application.

## Troubleshooting
| Symptom | Fix |
|---|---|
| "Database not found" | run `python scripts/init_db.py` first |
| MySQL error 1419 on triggers | `SET GLOBAL log_bin_trust_function_creators = 1;` as an admin |
| `cryptography` / "caching_sha2_password" error | `pip install -r requirements.txt` (includes `PyMySQL[rsa]`) |
| Signed out after restarting | set `SECRET_KEY` in `.env` for a stable session key |
| Forgot a password | On the sign-in page click **Forgot password?**, enter the username and open the link shown (valid 15 minutes, once). To reset everything: `python scripts/init_db.py` recreates the accounts with `DEMO_PASSWORD` |
