# Review 3 - Presentation Script (Project 36)

_Speaker notes / presentation script - one section per slide. The same text is stored in the PowerPoint speaker notes._

## Slide 1 - (cover)

Good morning. I am G Madhan from AI ML Rhinos. This is the final review, DBMS Review 3, for Project 36, the Employee Payroll and Statutory Deduction Management System. In Review 1 I presented the design and in Review 2 the database and prototype. Today I will show the finished application, run through the payroll workflow, show the SQL and reports, the test results, the honest limitations, and the concepts I am ready to answer questions on.

## Slide 2 - Final Project Overview

The problem from Review 1 is unchanged: small and mid-sized organisations still calculate salary in spreadsheets, which causes mistakes in loss of pay, statutory deductions and loan recovery, and leaves no reliable payslip or audit trail. The solution is a relational database that is the single source of truth, plus a web application on top of it. All twelve requirements from Review 1 are implemented. Since Review 2 I added login with three roles, database triggers that lock paid payroll and write an audit trail, reporting views, a Database Explorer for the administrator, and I tested the MySQL scripts on a real MySQL 8 server. All data in the demo is synthetic.

## Slide 3 - Objectives vs Delivered Functionality

This table maps every functional requirement from Review 1 to what exists in the application. All twelve are implemented and each has a page or SQL evidence behind it. The bank transfer requirement is implemented as simulated records: the system creates a transfer row per payslip and lets the officer mark them paid, but there is no real bank connection. Loan management goes slightly beyond Review 1 with a repayment history table.

## Slide 4 - Completed Modules

The application is organised into eight modules that follow the sidebar. Master data covers departments and designations. Employees has search, add, edit, delete and a profile page. Salary and attendance hold the monthly inputs. Earnings and deductions hold bonuses and manual deductions, while statutory deductions are generated automatically and shown read-only. Loans track EMI and outstanding balance. Payroll periods drive processing. Payslips and bank transfers are the outputs. Reports includes the editable illustrative rates page for the administrator. New since Review 2 are login with roles and the Database Explorer.

## Slide 5 - Final ER Diagram

This is the final entity relationship diagram. The twelve Review 1 entities are all here, plus two additions: Loan Repayment and Payroll Config. App User and Audit Log are on the next slide. Department and Designation each have many employees. Employee has exactly one salary structure and many attendance, earnings, deduction and loan rows. A payroll period has many payroll detail rows, one per employee per month, and each payroll detail has exactly one payslip and one bank transfer. A loan repayment links a loan to the payroll run in which it was deducted, or to nothing when it is a manual repayment.

## Slide 6 - Login, Triggers and Views

Two tables were added after Review 2. App User stores login accounts: username, role and a salted password hash, never the password. An employee account is linked to an employee row. Audit Log has no foreign keys on purpose: it is written only by database triggers. There are six triggers. Three audit triggers fire after an update of a salary structure, an employee's status, or a payroll rate, and write the old and new values to Audit Log. Three lock triggers fire before an insert, update or delete on payroll detail and refuse the change when the payroll period is no longer OPEN, so paid payroll cannot be altered even by someone who bypasses the application. The trigger on the right is the SQLite version; MySQL uses SIGNAL instead of RAISE, so I wrote the two files separately. There are also three views for reporting. I tested all of this on SQLite and on a real MySQL 8 server.

## Slide 7 - Final Relational Schema

This table summarises the final relational schema: sixteen tables, sixteen primary keys and seventeen foreign keys. App User and Audit Log are the two tables added after Review 2. Most tables are in third normal form. Payroll detail is the one deliberate exception: it stores a snapshot of the calculated gross, deductions and net for each employee and month, so that a payslip never changes later even if the salary structure or rates are edited. Loss of pay days are not stored because they can be derived from working days, days present and paid leave. Row counts are the counts in the current demo database.

## Slide 8 - Final Application: Dashboard

This is the finished dashboard after October 2026 has been processed. The tiles and charts are live SQL aggregates, not typed-in numbers: active employees, gross, deductions and net for the latest processed period, departments, open loans and outstanding balance, and pending transfers. The charts compare gross, deductions and net across the three payroll months and show headcount by department. The screenshot was taken from the running application against the synthetic demo database.

## Slide 9 - Login, Roles and Security

The application now requires a login. There are three roles. The administrator can do everything, including editing rates, managing user accounts and using the Database Explorer. HR can manage employees, salaries, attendance, loans and run payroll, but cannot open rates, users or the explorer. An employee can see only their own profile, loans and payslips: on the left is the employee view for EMP003 Pranav, and on the right is what happens when that employee tries to open the payroll register: a 403 Not allowed page. Passwords are never stored; only salted PBKDF2 hashes are. Every form carries a CSRF token, five failed logins lock a username for five minutes, the session is renewed at login, and a Forgot password link creates a signed reset link that expires after fifteen minutes and works only once. The demo has no e-mail server, so the link is shown on screen. This is a local demo: there is no HTTPS and the login throttle is in memory, so I do not claim it is ready for the internet.

## Slide 10 - Demonstration Flow

This is the order I will follow in the live demo, and it takes about five minutes. One: sign in as the administrator and show the dashboard. Two: open the employee list and add a new employee. Three: show the salary structure and the October attendance. Four: show the loan with its repayment history. Five: process October payroll with one click. Six: open a payslip and check the arithmetic. Seven: generate bank transfers and mark them paid. Eight: open the Database Explorer to show the triggers, the audit trail and the read-only SQL console, then a report with its SQL. Every step in the deck corresponds to a real screenshot.

## Slide 11 - Payroll Workflow

Payroll runs through a fixed life cycle. First the officer enters or confirms the inputs for the month: attendance, extra earnings and manual deductions. A period starts as OPEN. Pressing Process payroll calculates every active employee in one database transaction, writes the payroll detail, the itemised deduction rows, the payslip numbers and the loan repayments, and moves the period to PROCESSED. Because it is one transaction, any failure rolls everything back, and from then on database triggers refuse any change to that period's payroll rows. Then Generate bank transfers creates one pending transfer per payslip, and Mark transfers paid completes the cycle and sets the period to PAID. Once processed, the inputs for that period are locked, and a period cannot be processed twice.

## Slide 12 - Calculation Rules and Worked Example

These are the payroll rules, and I want to be clear that the rates are illustrative and editable in the configuration table; they are not official statutory rates. Gross is the fixed salary components minus loss of pay plus any extra earnings. Provident fund is twelve percent of basic capped at fifteen thousand. ESI is zero point seven five percent of gross, only when gross is twenty-one thousand or less. Professional tax is a flat two hundred above fifteen thousand. TDS is a simple five percent of gross above fifty thousand. Loan EMI is the smaller of the EMI and the outstanding balance. On the right is a worked example for employee EMP003 in October 2026: fixed gross is one lakh one hundred thirty rupees, PF is eighteen hundred, PT two hundred, TDS twenty-five hundred and six point five, EMI five thousand, so total deductions are nine thousand five hundred six point five and net salary is ninety thousand six hundred twenty-three point five. These numbers are also hand-checked in the unit tests.

## Slide 13 - Payslip Output

This is the payslip for EMP003 in October, generated by the application from the payroll detail row. It shows the earnings and deductions side by side, the gross, total deductions and the net salary payable, the working and loss of pay days, the bank details, and the linked bank transfer reference. The payslip number is built from the year, month and employee code. It can be printed or saved as PDF from the browser. The footer states plainly that the rates are illustrative and the data is synthetic. The figures match the worked example on the previous slide.

## Slide 14 - Bank Transfer Records

After processing, the system generates one transfer record per payslip using the employee's stored bank details, the net salary as the amount, and a reference number. On the left they are PENDING. After the officer chooses Mark transfers paid, they become SUCCESS with a date, as on the right, and the period moves to PAID. I want to be explicit that this is a simulation of the record keeping: there is no connection to any real bank and no money moves. The bank account numbers are fake.

## Slide 15 - Reports

The reports page offers seven reports, and each one has a View SQL button that shows the exact query that produced it. They are: payroll summary by period, department wise payroll cost, statutory deduction breakdown, top five net salaries, employees above their department's average gross, active loans with outstanding balance, and active employees without payroll in the selected period. The screenshot on the right shows the subquery report with its SQL expanded, which is useful in the viva because the query and result are on one screen. The payroll register can also be exported to CSV.

## Slide 16 - SQL Queries Behind the Results

These are simplified excerpts from database/queries.sql, which I run in full as part of the automated tests. On the left is the cross-check I use to prove the payroll is internally consistent: for every payroll row, net must equal gross minus total deductions. The query returns zero rows when the data is correct. In the middle is NOT EXISTS, which finds active employees that have no payroll yet for a period. On the right is an aggregate with GROUP BY that totals gross, deductions and net per period. The same file also contains inner and left joins, HAVING, scalar, IN, correlated and derived-table subqueries, and a view for payslip summaries.

## Slide 17 - Database Explorer and Audit Trail

The Database Explorer is an administrator-only page that reads the live structure of the connected database: tables with row counts, columns, primary keys, foreign keys with their delete rules, the three views and the six triggers. Below it is a SQL console. It accepts a single SELECT, runs it on a separate read-only connection with a five second limit and a two hundred row limit, and refuses the user table so password hashes are never shown. On the left I ran a SELECT on the department cost view. On the right I typed a DELETE and it was refused. The strip at the bottom is a real audit row: I edited a salary structure through the normal form and the database trigger recorded the old and new salary. The same page works on MySQL; I tested introspection and the console there too.

## Slide 18 - Payroll Results by Month

These are the real results from the three payroll months in the demo database, taken directly from the database. Each month has twenty-nine paid employees; the thirtieth employee is inactive and is skipped. Gross is about nineteen and a half lakh to nineteen point six lakh a month, total deductions rise from about 1.19 lakh in August to 1.39 lakh in October, and net salary stays around eighteen lakh. The table beside the chart gives the exact numbers. The data is synthetic, so these are demonstration results, not statistics of any real organisation.

## Slide 19 - Data Integrity in Action

Two screenshots show the database protecting the data. On the left I tried to add an employee with a code that already exists. The UNIQUE constraint rejected it and the application shows a readable message instead of a stack trace. On the right I tried to add a bonus to August 2026, which is already paid. The application refuses because processed periods are locked. Together with foreign keys, CHECK constraints and ON DELETE RESTRICT on payroll history, these rules mean a payroll record cannot be silently changed or orphaned.

## Slide 20 - Testing Results

All 74 automated SQLite tests pass, and a separate suite of 11 tests also passes on a real MySQL 8.0.46 server. The recorded outputs are in tests slash test_results dot txt and test_results_mysql dot txt. The SQLite suites cover calculation against hand-computed numbers, database constraints, payroll processing including rollback and double processing, the triggers and views, authentication and roles, password reset, amounts in words, the explorer, and the web layer. The MySQL suite checks that the payroll totals are identical to SQLite, that constraints and triggers work, that queries dot sql runs completely, and that the web app works and processes October. The MySQL run found one real bug: MySQL reports a violated CHECK constraint and a trigger signal as an operational error instead of an integrity error, which would have crashed pages; it is fixed. What I have not tested: the GitHub Actions workflow has not run yet, other MySQL versions or MariaDB, other browsers than headless Chromium, and many concurrent users.

## Slide 21 - Limitations

I want to be honest about what this project is not. Security is demo-grade: there are roles, hashed passwords and CSRF tokens, but no HTTPS, and the login throttle is in memory. The bank transfers are simulated records. The deduction rates are illustrative and editable, and are not official statutory rates, so the output must not be used for real payroll. The MySQL scripts were run and tested on one server, version 8.0.46; other versions and MariaDB are untested. The data is synthetic with about thirty employees. Finally, the audit trail records what changed but not which web user changed it, because triggers cannot see the web user.

## Slide 22 - Conclusion

To conclude: I took the Review 1 design and delivered a working payroll system. The database has sixteen tables with primary keys, foreign keys, unique and check constraints, plus triggers and views. The payroll engine computes gross, statutory and loan deductions and net salary for each employee in one safe transaction. Payslips, simulated bank transfers and seven reports are produced from that data, with login roles on top. 74 automated tests pass on SQLite and 11 on a real MySQL 8 server. The project taught me that the database should enforce the rules, not only the application. With more time I would replace the illustrative rates with official ones, record the acting user in the audit trail, add PDF payslips and deploy behind HTTPS.

## Slide 23 - Viva Readiness: Key Concepts

These are the DBMS concepts in this project that I can explain and show in the code. Normalisation: the schema is in third normal form, with payroll detail as a deliberate snapshot. Keys: every table has a primary key, and sixteen foreign keys link them. Constraints: UNIQUE on employee code and email, CHECK on amounts and status values. Referential actions: RESTRICT protects paid history, CASCADE removes employee inputs. Transactions: payroll processing is atomic with commit and rollback. Joins and subqueries are in queries.sql. Indexes speed up lookups by period and employee. Derived data: loss of pay days are computed, not stored, to avoid redundancy.

## Slide 24 - Viva Readiness: Likely Questions

Here are questions I expect, with short answers. Why is payroll detail stored if it can be calculated? Because a payslip must not change if rates or salaries are edited later, so it is a deliberate snapshot. Why RESTRICT on payroll history? So paid records cannot be deleted by accident. How do you avoid a half-finished payroll? The whole run is one transaction. Where are the deduction rates? In payroll_config, and they are illustrative. Is the bank transfer real? No, it is a simulated record. Does it use MySQL? The scripts support MySQL 8 and the app runs on SQLite by default; I tested both, SQLite with 74 tests and a real MySQL 8.0.46 server with 11. What would you add next? Official tax rules, and recording the acting user in the audit trail.

## Slide 25 - References

These are the references I used: the official documentation for Flask, SQLite, MySQL 8, PyMySQL, Bootstrap and Chart.js, and two standard textbooks for the database theory. The deduction rates in this project are illustrative and are not taken from any statutory document, so I have not cited any tax or provident fund rules as a source.

## Slide 26 - Thank You

Thank you. The source code, SQL scripts, screenshots, report and test results are in the submission folder. I am happy to demonstrate any part of the application live or to answer questions on the database design, the SQL, or the payroll calculation.
