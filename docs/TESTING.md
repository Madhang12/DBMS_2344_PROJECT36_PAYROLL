# Testing Documentation

## How to run
```bash
python -m unittest discover -s tests -v                    # 74 tests on SQLite
PAYROLL_MYSQL_TESTS=1 MYSQL_USER=... MYSQL_PASSWORD=... MYSQL_DATABASE=payroll_test python -m unittest tests.test_mysql -v   # 11 tests on MySQL
```
Recorded output: `tests/test_results.txt` (74 / 74 OK on SQLite 3.45) and `tests/test_results_mysql.txt` (11 / 11 OK on MySQL 8.0.46).
Each SQLite test builds its own temporary database, so the demo database is never touched.
The MySQL suite re-creates every table in the database named by `MYSQL_DATABASE` - use a throw-away one.

## SQLite suites (74 tests)
| Suite | Tests | What it proves |
|---|---|---|
| CalcTests | 5 | Hand-computed high-salary case (LOP + loan + manual deduction); low salary gets ESI but no TDS; EMI never exceeds the outstanding balance; paid leave is not LOP; changing the config changes the result |
| DatabaseTests | 9 | All tables exist; seed counts; FK rejects a bad department; UNIQUE emp_code; CHECK rejects a negative salary and bad attendance totals; one salary structure per employee; RESTRICT blocks deleting an employee with payroll; `queries.sql` runs completely |
| PayrollProcessingTests | 9 | Demo periods processed/paid; net = gross - deductions on every row; itemised deductions match totals; October end to end; cannot process twice; inactive employee skipped; missing attendance skipped and reported; bank-transfer flow; failed run rolls back |
| TriggerAndViewTests | 6 | 6 triggers and 3 views exist; paid payroll cannot be updated, deleted or inserted into; salary / status / rate changes are audited and unaudited columns are not; views agree with the base tables |
| AuthTests | 13 | Anonymous users are sent to login; wrong password / unknown user refused; passwords stored hashed; login throttling; ADMIN / HR / EMPLOYEE access rules; an employee cannot open someone else's payslip or POST to management endpoints; CSRF token required; change password; create user and duplicate refusal; deactivated user and last-admin protection; app_user constraints |
| PasswordResetTests | 7 | Forgot-password page is public; unknown and inactive users get the same message and no link; a reset link changes the password and works only once; weak or mismatched passwords refused; tampered and expired links refused; the link is hidden when demo mode is off; reset requests are throttled |
| AmountInWordsTests | 2 | Indian system (thousand / lakh / crore, paise) gives the right words; the filter is registered for payslips |
| ExplorerTests | 6 | Introspection lists 16 tables / 6 triggers; console runs SELECT; refuses writes, multiple statements and `app_user`; the connection is genuinely read-only; 200-row limit; admin web page |
| WebTests | 17 | All pages load; 404; CRUD for employees, departments and designations; friendly duplicate-code error; required-field validation; blocked deletes; locked period rejects new earnings; open period accepts them and they reach the payslip; AUTO rows read-only; process via web then double-process refused; period creation and duplicate; manual loan repayment; settings change applies to the next run; CSV export; all 7 reports return data |

## MySQL suite (11 tests, real MySQL 8.0.46)
Row counts and period states; payroll totals identical to the SQLite results (Aug 18,36,259.13; Sep 18,06,179.32); net = gross - deductions;
UNIQUE / FK / CHECK / RESTRICT rejection; trigger lock on paid payroll; audit trigger and views; `database/queries.sql` runs completely;
introspection and the read-only console; web login and 12 pages; friendly messages for rule violations; processing October through the web app
(EMP003 net 90,623.50).

**Bug found by the MySQL run:** MySQL reports a violated CHECK constraint (error 3819) and a trigger `SIGNAL` (1644) as `OperationalError`,
not `IntegrityError`, which would have crashed pages with a 500 error. `app/db.py` now re-raises them as integrity errors on both engines.

## Hand-checked example (October 2026, EMP003)
fixed gross 58,900 + 23,560 + 5,890 + 11,780 = 1,00,130; PF 12% x 15,000 = 1,800; PT 200; TDS 5% x (1,00,130 - 50,000) = 2,506.50;
EMI 5,000; total deductions 9,506.50; net 90,623.50.

## Manual / visual verification
Real screenshots in `screenshots/` were captured by driving the real UI with headless Chromium (`scripts/capture_screenshots.py`):
sign-in, adding/deleting an employee, processing October, payslip, transfers, reports, the role views, a salary edit that produces an audit row,
and the read-only console refusing a DELETE.

## Not tested (be explicit in the viva)
- GitHub Actions workflow (`.github/workflows/tests.yml`) has not run yet - it runs the first time the repo is pushed
- MySQL versions other than 8.0.46, MariaDB
- Browsers other than headless Chromium; concurrent users; large data volumes
- Penetration / load testing; HTTPS deployment (the app is a local demo server)
