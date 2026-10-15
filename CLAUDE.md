# Project 36 - Employee Payroll and Statutory Deduction Management System (DBMS PBL)

Student: G MADHAN (25WU0102344) per the Review 1 PDF.

## Run
```
python -m venv .venv && .venv\Scripts\Activate.ps1      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py
python run.py        # http://127.0.0.1:5000  (admin / hr / emp001..emp005, password = DEMO_PASSWORD, default Payroll@2026)
python -m unittest discover -s tests     # 74 pass, 11 MySQL tests skipped unless PAYROLL_MYSQL_TESTS=1
```

## State (final)
Flask app, SQLite default + MySQL 8, 16 tables, 3 views, 6 triggers, audit log, login with ADMIN/HR/EMPLOYEE, CSRF, Database Explorer + read-only console,
payroll engine, payslips, simulated bank transfers, 7 reports. MySQL path tested on a real 8.0.46 server (tests/test_mysql.py).
Decks: presentations/ (Review 2 = snapshot of the Review 2 stage using screenshots/review2_stage, facts_review2.json; Review 3 = final).

## Rules
- Never fabricate screenshots, results or links; never claim untested features work.
- Synthetic data only; no secrets in the repo (.env is git-ignored). Rates are illustrative, bank transfers simulated.
- Do not push to GitHub or invent repo/Drive URLs; placeholders stay until the user fills them.
