# Review 2 - Presentation Script (Project 36)

_Speaker notes / presentation script - one section per slide. The same text is stored in the PowerPoint speaker notes._

## Slide 1 - (cover)

Good morning. I am G Madhan from AI ML Rhinos, and this is DBMS Review 2 for Project 36, the Employee Payroll and Statutory Deduction Management System. In Review 1 I presented the problem, objectives, scope, ER diagram and the initial relational schema. Today I will show how that design became a working database and a running web application, with real screenshots and real test results.

## Slide 2 - From Review 1 to Review 2

Review 1 was about analysis and design: the problem, objectives, users, twelve functional requirements, a conceptual ER diagram and a skeleton schema with only primary and foreign keys. Review 2 is about implementation. I kept the same project and the same twelve entities, and extended them where implementation showed a gap: I added a loan repayment table so repayments can really be tracked, and a configuration table so the illustrative deduction rates are editable instead of hard-coded. Review 3 will cover the final demo and results.

## Slide 3 - System Architecture

The application has five simple layers. The browser shows Bootstrap pages and a Chart.js dashboard. Flask routes receive requests; one generic set of views handles add, edit, delete and list for most tables, driven by a configuration file. The business logic lives in two small modules: payroll.py, which calculates and processes payroll, and reports.py, which holds the seven report queries as plain SQL. The data access layer db.py hides the differences between SQLite and MySQL, so all SQL is written once. By default the database is SQLite so the project runs with no setup; MySQL is supported through environment variables.

## Slide 4 - Technology Stack

These are the tools I used. Python with Flask gives the web layer, and Jinja2 renders the pages. Bootstrap 5 and Bootstrap Icons are stored inside the project, so the app works offline. Chart.js draws the dashboard charts. SQLite is the default database so the prototype runs anywhere; the same SQL and an equivalent MySQL 8 schema are included. I want to be clear that I have written and syntax-checked the MySQL scripts, but in my development environment there was no MySQL server, so the live MySQL run is still on my to-do list.

## Slide 5 - Database Design Principles

The schema has 14 tables, 14 primary keys, 16 foreign keys, 13 unique constraints, 21 check constraints and 7 indexes. For normalisation: every table has a single-column primary key and atomic values, so it is in first normal form. Non-key columns depend on the whole key. For example, the number of loss-of-pay days is not stored in attendance, because it can be derived from working days, days present and paid leave, which avoids update anomalies. Department and designation names live only in their own tables. The one deliberate exception is payroll_detail, which stores the computed results as a snapshot so that old payslips never change when rates or salaries change later.

## Slide 6 - Implemented ER Diagram

This is the Review 1 conceptual diagram turned into the implemented one. Employee is still the centre: one department and one designation per employee, a one-to-one salary structure, and many attendance, earnings, deductions and loan rows. Payroll detail links an employee to a payroll period; each payroll detail has exactly one payslip and one bank transfer. The two additions are loan repayment, which hangs off both loan and payroll detail, and the payroll config table at top left, which holds the editable rates and has no foreign keys. Attendance, earnings and deductions also reference the payroll period, which I did not draw to keep the diagram readable.

## Slide 7 - Relational Schema: Master Data

Here are the master tables. Department and designation are small lookup tables with unique names. Employee holds personal and bank details and two foreign keys. All bank data is synthetic. Salary structure is one row per employee, enforced by a unique foreign key. Payroll period has a unique name and a unique month and year, and a status that moves from open to processed to paid. Payroll config stores the eight illustrative rates and limits.

## Slide 8 - Relational Schema: Monthly Inputs

These four tables are the monthly inputs the payroll officer enters. Attendance stores working days, days present and paid leave; a check constraint makes sure present plus leave never exceeds working days. Earnings holds extra pay like bonus and overtime. Deductions holds both manual deductions typed by the officer and automatic rows, which the payroll engine writes for provident fund, ESI, professional tax, income tax and loan EMI; the source column tells them apart. Loan keeps the amount, EMI and the outstanding balance. Employee inputs cascade on delete, but they always restrict deletion of a payroll period.

## Slide 9 - Relational Schema: Payroll Output

These tables are written by payroll processing. Payroll detail is the heart of the output: for each employee and period it stores the earnings components, loss of pay, gross, the three deduction groups, total deductions and net salary. I store these values deliberately so a payslip from August stays exactly as it was even if I change a rate in September. Payslip and bank transfer each have a unique foreign key to payroll detail, which makes both one-to-one. Loan repayment records each EMI, linked to the payroll row that deducted it, or to nothing when it is a manual repayment.

## Slide 10 - Table Implementation (DDL)

This is a real excerpt from schema.sql for the payroll detail table; the dots stand for columns I left out to fit the slide. You can see all four kinds of constraint: the primary key, a unique constraint on employee plus period so nobody can be paid twice for the same month, a check constraint that net salary can never be negative, and two foreign keys with RESTRICT so paid history can never be orphaned. The same file also exists in a SQLite version, which a small script generates from the MySQL one, so the two never drift apart.

## Slide 11 - Tables and Synthetic Data

After running init_db.py the database holds thirty synthetic employees across six departments, three payroll periods, ninety attendance records, loans and so on. All data is fictitious: names are random combinations, e-mails use the reserved example.com domain, and bank accounts are made up. Importantly, the payroll rows, payslips, bank transfers, automatic deductions and loan repayments for August and September were not typed in; they were produced by running the application's own payroll engine, so the demo data exercises the real logic. October is left open so I can process it live.

## Slide 12 - SQL Operations

These are simplified excerpts from database/queries.sql, and the test suite executes the whole file against a copy of the database, so every statement is known to run. Top left is CRUD: insert, update, delete. Top right is a three-table join for the employee directory. Bottom left is group by with a having clause: department payroll cost, only for departments with more than two people. Bottom right is a correlated subquery that compares each employee's gross salary to the average of their own department. The file also contains left joins, not-exists, scalar and derived-table subqueries, a view, and consistency checks.

## Slide 13 - Payroll Calculation Logic

Calculation follows a simple chain. Fixed gross is basic plus HRA plus DA plus special allowance. Each day of unpaid leave cuts one working day's share of fixed gross. Bonus or overtime for the month is added to give gross salary. Then five deductions are applied: provident fund, ESI, professional tax, an illustrative income tax, and loan EMI, plus any manual deductions. Net salary is gross minus total deductions. I must stress that every rate shown here is illustrative for a university project; they are not official statutory rates, and they can be edited on the settings page and are stored in the payroll_config table.

## Slide 14 - Development Progress

This table is the honest status of the Review 1 requirements. Every functional requirement from Review 1 is implemented and covered by at least one automated test or screenshot. Bank transfers are simulated: the system records transfer details and status, but it does not connect to a real bank. One thing is not done yet: Review 1 listed four user roles, HR, payroll officer, employee and management, but there is no login or role-based access in this prototype. That is the first item under future improvements.

## Slide 15 - Prototype: Dashboard

This is a real screenshot of the running application. The dashboard shows active employees, the gross, deductions and net totals for the latest processed period, open periods, pending bank transfers and outstanding loans. The bar chart compares gross, deductions and net for each processed month, and the doughnut shows headcount per department. All of these numbers come from SQL aggregate queries on the live database. Customer Support has no employees in the demo data, which is why it shows as an empty department.

## Slide 16 - Prototype: Employee Management

Employee management supports add, view, update and delete. On the left is the employee list with live search. On the right is the add form: required fields are marked, dropdowns are loaded from the department and designation tables, and the database constraints are checked on save. A duplicate employee code, for example, is rejected by the unique constraint and shown as a friendly message. An employee who already has payroll cannot be deleted; the app tells the user to set the status to inactive instead.

## Slide 17 - Prototype: Salary and Attendance

On the left is the salary structure page: each employee has basic, HRA, DA and special allowance, and fixed gross is calculated by a SQL expression. On the right is attendance for October 2026, with the loss-of-pay column derived in the query from working days, present days and paid leave. Earnings and deductions pages work the same way, and rows in a period that has been processed are locked, so history cannot be edited by accident.

## Slide 18 - Prototype: Loans and Repayments

The loans page lists each loan with its EMI and outstanding balance. Opening a loan shows its repayment history. EMIs are deducted automatically when payroll is processed: the engine writes a repayment row, reduces the outstanding balance, and closes the loan when the balance reaches zero. A payroll officer can also record a manual repayment. In the screenshot on the right you can see loan one with two payroll EMIs, for August and September, each reducing the balance.

## Slide 19 - Prototype: Payroll Processing

This is the core feature. On the left, October 2026 is open and ready. I click Process payroll and the engine runs for all active employees. On the right is the result: payroll processed for twenty-nine employees with the totals shown, and the period status changes to processed. The twenty-ninth employee count is because one employee in the data is inactive and is skipped. The whole run is one database transaction: if anything fails, nothing is saved. Processing the same period twice is refused.

## Slide 20 - Testing

I wrote forty automated tests and all forty pass. Five calculation tests check the payroll formulas against numbers I computed by hand, including a case with loss of pay, a loan and a bonus, and a low-salary case where ESI applies. Nine database tests prove that foreign keys, unique and check constraints really reject bad data. Nine payroll tests check processing end to end: totals are consistent, loans reduce correctly, double processing is refused, and a failed run rolls back completely. Seventeen web tests load all pages and exercise add, edit and delete flows. The full results are saved in tests/test_results.txt. What I have not tested yet: a live MySQL server and browsers other than headless Chromium.

## Slide 21 - Challenges and Solutions

Four design challenges shaped the implementation. First, MySQL and SQLite differ in small ways, such as auto-increment syntax. I wrote the schema once for MySQL and generate the SQLite file with a script, and I wrote all SQL in a portable subset. Second, rounding: payroll must be exact, so the engine uses decimal arithmetic rounded to paise, and SQLite cannot bind decimals, so the data layer converts them. Third, data consistency: once a month is processed, editing its inputs would make payslips wrong, so processed periods lock their inputs, and processing runs in one transaction. Fourth, Review 1 had no way to record loan repayments, so I added the loan repayment table. Each solution has an automated test.

## Slide 22 - Future Improvements

These are the planned improvements. The most important is login and roles, because Review 1 defined four user types and the prototype currently has no authentication. Second, I want to run and test the project against a real MySQL 8 server, since so far only the scripts exist. Third, replace the illustrative rates with proper statutory slabs. Others: PDF payslips with e-mail, an audit log of changes, bank file export, and a tax declaration module.

## Slide 23 - Summary and Next Review

To summarise: the Review 1 design is now a working system. There is a fourteen-table database with enforced constraints, a Flask application covering every functional requirement, synthetic data, a payroll engine that I verified by hand and by forty automated tests. For Review 3 I will demonstrate the complete payroll workflow live, show the reports and the final results, and discuss limitations. Thank you. I am happy to take questions.
