"""Create the database, load the synthetic seed data and run demo payroll.

Usage (from the project root):
    python scripts/init_db.py              # SQLite (default) -> instance/payroll.db
    DB_BACKEND=mysql python scripts/init_db.py   # MySQL (needs a running server + .env)

What it does
  1. (SQLite) deletes the old database file; (MySQL) drops & recreates tables
  2. runs schema.sql, seed.sql (masters, employees, attendance, loans ...), views.sql, triggers.sql,
     then creates the demo login accounts
  3. processes August and September 2026 using the app's payroll engine,
     generates their bank transfers and marks them PAID
  4. leaves October 2026 OPEN so you can demonstrate processing live
Use --no-demo-payroll to stop after step 2.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import auth, config, db as dbmod, payroll  # noqa: E402


def init(backend=None, sqlite_path=None, demo_payroll=True, quiet=False):
    backend = backend or config.DB_BACKEND
    if backend == "sqlite":
        path = Path(sqlite_path or config.SQLITE_PATH)
        if path.exists():
            path.unlink()
        conn = dbmod.connect("sqlite", str(path))
        schema = ROOT / "database" / "sqlite" / "schema.sql"
    else:
        conn = dbmod.connect("mysql")
        schema = ROOT / "database" / "mysql" / "schema.sql"
        conn.run("SET FOREIGN_KEY_CHECKS = 0")
        for t in conn.all("SHOW FULL TABLES"):
            name, kind = list(t.values())[0], list(t.values())[1]
            conn.run(f"DROP {'VIEW' if kind == 'VIEW' else 'TABLE'} IF EXISTS `{name}`")
        conn.run("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()

    conn.script(schema.read_text())
    conn.script((ROOT / "database" / "seed.sql").read_text())
    conn.script((ROOT / "database" / "views.sql").read_text())
    try:
        conn.script_blocks((ROOT / "database" / backend / "triggers.sql").read_text())
    except Exception as e:                      # MySQL with binary logging needs extra privilege for triggers
        if backend == "mysql" and "1419" in str(e):
            raise SystemExit("MySQL refused to create triggers (binary logging is on and your user lacks SUPER).\n"
                             "Fix: as an admin run   SET GLOBAL log_bin_trust_function_creators = 1;   then retry. See docs/SETUP.md.")
        raise
    if backend == "mysql":
        conn.commit()
    auth.create_demo_users(conn)

    if demo_payroll:
        for pid in (1, 2):
            res = payroll.process_period(conn, pid)
            payroll.create_bank_transfers(conn, pid)
            payroll.mark_transfers_paid(conn, pid)
            if not quiet:
                print(f"  period {pid}: processed {res['processed']} employees, "
                      f"gross {res['gross']}, deductions {res['deductions']}, net {res['net']}, skipped {res['skipped']}")
    conn.close()
    if not quiet:
        print(f"Database ready ({backend}).")
        print(f"Demo logins (local, synthetic): admin / hr / emp001..emp005  - password from DEMO_PASSWORD (default {auth.DEMO_PASSWORD})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-demo-payroll", action="store_true")
    a = ap.parse_args()
    init(demo_payroll=not a.no_demo_payroll)
