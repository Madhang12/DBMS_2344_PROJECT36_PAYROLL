# Five-Minute Demo Video Script

Setup before recording: `python scripts/init_db.py`, `python run.py`, open http://127.0.0.1:5000. Window about 1440x810. Do not show `.env`.
Total target 5:00.

| Time | Screen | Say |
|---|---|---|
| 0:00-0:25 | Sign-in page | "I am G Madhan, AI ML Rhinos. Project 36: Employee Payroll and Statutory Deduction Management System. It is a relational database with a Flask web app on top. Data is synthetic, rates are illustrative. I sign in as the administrator; there are three roles: admin, HR and employee." |
| 0:25-0:50 | Dashboard | "Live SQL aggregates: employees, gross, deductions, net, loans, pending transfers. October 2026 is still open." |
| 0:50-1:20 | Employees > Add | "Employee master data with search, add, edit, delete. Try a duplicate employee code: the UNIQUE constraint rejects it with a readable message." |
| 1:20-1:50 | Salary structures, Attendance, Loans | "One salary structure per employee. Attendance holds working, present and leave days; loss of pay is derived. Loans have EMI and balance, repayments are recorded." |
| 1:50-2:40 | Payroll Periods > Process payroll (October) | "Processing is one transaction: PF, ESI, professional tax, TDS and loan EMI for every active employee; payslips are created; the period becomes PROCESSED. Any error rolls everything back; a period cannot be processed twice." |
| 2:40-3:15 | Payslip EMP003 | "Gross 1,00,130, PF 1,800, PT 200, TDS 2,506.50, EMI 5,000, total deductions 9,506.50, net 90,623.50. The page only reads stored values." |
| 3:15-3:35 | Transfers | "Simulated records: PENDING, then marked SUCCESS. There is no bank connection." |
| 3:35-4:25 | Database Explorer | "Admin-only. Tables, keys, 3 views and 6 triggers live from the database. Triggers lock paid payroll and write this audit trail when a salary changes. The console is read-only: this SELECT on a view works, and a DELETE is refused." |
| 4:25-4:45 | Sign in as emp003 (second window) | "An employee sees only their own payslips; opening the payroll register gives 403." |
| 4:45-5:00 | Test results | "74 tests pass on SQLite and 11 on a real MySQL 8 server. Limitations: simulated transfers, illustrative rates, demo-grade security. Thank you." |
