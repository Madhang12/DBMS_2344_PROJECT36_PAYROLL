// Review 3 deck: final application, results, testing, limitations, conclusion, viva readiness
const path = require("path");
const { makePres, HEX, drawER, save, writeNotes, ROOT } = require("./lib.js");
const fs = require("fs");
const facts = require("./facts.json");
const T = facts.test_suites;
const sqliteTests = Object.values(T).reduce((a, b) => a + b, 0);
const mysqlTests = (fs.readFileSync(path.join(__dirname, "..", "..", "tests", "test_results_mysql.txt"), "utf8").match(/\.\.\. ok/g) || []).length;

(async () => {
  const H = makePres("DBMS REVIEW 3", "Project 36 - DBMS Review 3");
  const { pres, C } = H;
  const OUT = path.join(ROOT, "presentations", "Project36_DBMS_Review3.pptx");
  const inr = (n) => "Rs " + Number(n).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  // ------------------------------------------------------------ 1 cover
  {
    const s = H.slide("COVER", "Introduction", null,
      "Good morning. I am G Madhan from AI ML Rhinos. This is the final review, DBMS Review 3, for Project 36, the Employee Payroll and Statutory Deduction Management System. In Review 1 I presented the design and in Review 2 the database and prototype. Today I will show the finished application, run through the payroll workflow, show the SQL and reports, the test results, the honest limitations, and the concepts I am ready to answer questions on.");
    s.addShape(pres.ShapeType.ellipse, { x: 7.0, y: -2.0, w: 4.6, h: 4.6, fill: { color: C.accent3 }, line: { color: C.accent3, width: 0 } });
    s.addShape(pres.ShapeType.ellipse, { x: -1.6, y: 3.6, w: 3.6, h: 3.6, fill: { color: C.accent3 }, line: { color: C.accent3, width: 0 } });
    H.pill(s, "PROJECT 36   |   DBMS REVIEW 3   |   FINAL", 2.7, 0.45, 4.6, { fill: { color: C.accent1 }, color: C.background1, h: 0.36 });
    H.text(s, "EMPLOYEE PAYROLL AND STATUTORY DEDUCTION MANAGEMENT SYSTEM", { x: 1.0, y: 1.0, w: 8.0, h: 1.5, fontSize: 32, bold: true, color: C.background1, align: "center", valign: "middle", fontFace: "Cambria" });
    H.text(s, "Final application, security, results and viva readiness", { x: 1.0, y: 2.55, w: 8.0, h: 0.4, fontSize: 16, italic: true, color: C.accent4, align: "center" });
    const icons = [["FaDatabase", "16 tables"], ["FaCalculator", "Payroll engine"], ["FaFileInvoice", "Payslips"], ["FaUniversity", "Transfers"], ["FaChartBar", "Reports"], ["FaCheckCircle", sqliteTests + " + " + mysqlTests + " tests"]];
    for (let i = 0; i < icons.length; i++) {
      const x = 1.3 + i * 1.3;
      await H.circleIcon(s, icons[i][0], x, 3.15, 0.6, C.background1, "#1E2761");
      H.text(s, icons[i][1], { x: x - 0.3, y: 3.8, w: 1.2, h: 0.25, fontSize: 11, color: C.accent4, align: "center" });
    }
    H.dark(s, 1.0, 4.3, 8.0, 0.85, { fill: { color: C.accent3 } });
    H.text(s, [{ text: "PRESENTED BY   ", options: { color: C.accent2, bold: true, fontSize: 11 } },
      { text: "G MADHAN   25WU0102344", options: { color: C.accent2, bold: true, fontSize: 18 } }], { x: 1.3, y: 4.42, w: 5.5, h: 0.6, valign: "middle" });
    H.text(s, [{ text: "Department", options: { color: C.accent2, bold: true, fontSize: 11, breakLine: true } },
      { text: "AI ML RHINOS", options: { color: C.background1, fontSize: 14 } }], { x: 7.2, y: 4.42, w: 1.7, h: 0.6, valign: "middle" });
  }

  // ------------------------------------------------------------ 2 overview
  {
    const s = H.slide("CONTENT", "Introduction", "Final Project Overview",
      "The problem from Review 1 is unchanged: small and mid-sized organisations still calculate salary in spreadsheets, which causes mistakes in loss of pay, statutory deductions and loan recovery, and leaves no reliable payslip or audit trail. The solution is a relational database that is the single source of truth, plus a web application on top of it. All twelve requirements from Review 1 are implemented. Since Review 2 I added login with three roles, database triggers that lock paid payroll and write an audit trail, reporting views, a Database Explorer for the administrator, and I tested the MySQL scripts on a real MySQL 8 server. All data in the demo is synthetic.");
    await H.titleIcon(s, "FaClipboardList");
    H.card(s, 0.5, 1.25, 4.4, 1.55);
    H.text(s, "Problem (Review 1)", { x: 0.7, y: 1.33, w: 4.0, h: 0.3, fontSize: 15, bold: true, color: C.text2 });
    H.text(s, "Manual or spreadsheet payroll gives calculation errors, inconsistent statutory deductions, untracked loans and no reliable payslip history.", { x: 0.7, y: 1.68, w: 4.0, h: 1.05, fontSize: 13, color: C.text1 });
    H.dark(s, 5.1, 1.25, 4.4, 1.55);
    H.text(s, "Solution", { x: 5.3, y: 1.33, w: 4.0, h: 0.3, fontSize: 15, bold: true, color: C.accent2 });
    H.text(s, "A normalised 16-table database with constraints, triggers and views, a payroll engine that writes gross, deductions and net per employee per month, and a secure Flask web interface.", { x: 5.3, y: 1.68, w: 4.0, h: 1.05, fontSize: 13, color: C.background1 });
    const st = [[facts.constraints.tables, "tables (3NF)"], ["12 / 12", "requirements built"], [sqliteTests + " + " + mysqlTests, "tests: SQLite + MySQL"], ["6", "triggers, 3 views"], ["3", "roles with login"]];
    st.forEach((t, i) => H.stat(s, String(t[0]), t[1], 0.5 + i * 1.83, 3.05, 1.7, 1.0, { size: 26 }));
    H.card(s, 0.5, 4.25, 9.0, 0.85);
    H.text(s, [{ text: "Users: ", options: { bold: true, color: C.text2 } }, { text: "ADMIN (everything, rates, users, explorer), HR / payroll officer (manage data, run payroll), EMPLOYEE (own payslips only). ", options: { color: C.text1 } },
      { text: "Scope: ", options: { bold: true, color: C.accent2 } }, { text: "a local demo, not hardened for the internet.", options: { color: C.text1 } }],
      { x: 0.7, y: 4.3, w: 8.6, h: 0.75, fontSize: 13, valign: "middle" });
  }

  // ------------------------------------------------------------ 3 requirements matrix
  {
    const s = H.slide("CONTENT", "Introduction", "Objectives vs Delivered Functionality",
      "This table maps every functional requirement from Review 1 to what exists in the application. All twelve are implemented and each has a page or SQL evidence behind it. The bank transfer requirement is implemented as simulated records: the system creates a transfer row per payslip and lets the officer mark them paid, but there is no real bank connection. Loan management goes slightly beyond Review 1 with a repayment history table.");
    await H.titleIcon(s, "FaTasks");
    const ok = { text: "Done", options: { color: C.accent5, bold: true } };
    const rows = [
      ["1", "Employee records", "Employees, profile page", ok], ["2", "Departments and designations", "Master data pages", ok],
      ["3", "Salary structures", "Basic, HRA, DA, special", ok], ["4", "Attendance summaries", "Per period; LOP derived", ok],
      ["5", "Earnings", "Bonus, overtime, incentive", ok], ["6", "Statutory and other deductions", "AUTO and MANUAL rows", ok],
      ["7", "Loans and repayments", "EMI, balance, history", ok], ["8", "Payroll periods", "OPEN > PROCESSED > PAID", ok],
      ["9", "Gross, deductions, net", "payroll.py, one transaction", ok], ["10", "Payslips", "Printable, numbered", ok],
      ["11", "Bank transfer details", "Simulated, no bank API", { text: "Done (simulated)", options: { color: C.accent5, bold: true } }],
      ["12", "Payroll reports", "7 reports + CSV export", ok],
    ];
    H.table(s, ["#", "Review 1 requirement", "Where in the app", "Status"], rows, 0.5, 1.2, 9.0, [0.4, 3.3, 3.6, 1.7], { fontSize: 11, rowH: 0.28 });
    H.text(s, "Beyond Review 1: login with roles, triggers, audit trail, views, Database Explorer (later slides).", { x: 0.5, y: 4.95, w: 9.0, h: 0.25, fontSize: 11, italic: true, color: C.text1 });
  }

  // ------------------------------------------------------------ 4 completed modules
  {
    const s = H.slide("CONTENT", "Application", "Completed Modules",
      "The application is organised into eight modules that follow the sidebar. Master data covers departments and designations. Employees has search, add, edit, delete and a profile page. Salary and attendance hold the monthly inputs. Earnings and deductions hold bonuses and manual deductions, while statutory deductions are generated automatically and shown read-only. Loans track EMI and outstanding balance. Payroll periods drive processing. Payslips and bank transfers are the outputs. Reports includes the editable illustrative rates page for the administrator. New since Review 2 are login with roles and the Database Explorer.");
    await H.titleIcon(s, "FaThLarge");
    const mods = [["FaUsers", "Employees", "CRUD, search, profile"], ["FaSitemap", "Departments", "Designations, master data"], ["FaRupeeSign", "Salary", "Structure per employee"],
      ["FaCalendarCheck", "Attendance", "Working, present, leave"], ["FaPlusCircle", "Earnings / deductions", "Auto + manual rows"], ["FaHandHoldingUsd", "Loans", "EMI and repayments"],
      ["FaPlayCircle", "Payroll periods", "Process, transfer, pay"], ["FaFileInvoice", "Payslips", "Printable payslip"],
      ["FaUniversity", "Bank transfers", "Pending then paid"], ["FaChartBar", "Reports", "7 reports, rates, CSV"], ["FaUserShield", "Login and roles", "ADMIN, HR, EMPLOYEE"], ["FaDatabase", "Database Explorer", "Schema, triggers, SQL"]];
    for (let i = 0; i < mods.length; i++) {
      const col = i % 4, row = Math.floor(i / 4);
      const x = 0.5 + col * 2.28, y = 1.25 + row * 1.3;
      H.card(s, x, y, 2.1, 1.15);
      await H.circleIcon(s, mods[i][0], x + 0.12, y + 0.14, 0.5, i % 2 ? C.accent2 : C.accent3, "#FFFFFF");
      H.text(s, mods[i][1], { x: x + 0.7, y: y + 0.12, w: 1.35, h: 0.55, fontSize: 12.5, bold: true, color: C.text2, valign: "middle" });
      H.text(s, mods[i][2], { x: x + 0.12, y: y + 0.72, w: 1.9, h: 0.35, fontSize: 11, color: C.text1 });
    }
  }

  // ------------------------------------------------------------ 5 final ER
  {
    const s = H.slide("CONTENT", "Database", "Final ER Diagram",
      "This is the final entity relationship diagram. The twelve Review 1 entities are all here, plus two additions: Loan Repayment and Payroll Config. App User and Audit Log are on the next slide. Department and Designation each have many employees. Employee has exactly one salary structure and many attendance, earnings, deduction and loan rows. A payroll period has many payroll detail rows, one per employee per month, and each payroll detail has exactly one payslip and one bank transfer. A loan repayment links a loan to the payroll run in which it was deducted, or to nothing when it is a manual repayment.");
    await H.titleIcon(s, "FaProjectDiagram");
    H.text(s, "Core payroll tables (14). Login and audit tables: next slide.", { x: 5.6, y: 0.5, w: 3.9, h: 0.3, fontSize: 11, italic: true, color: C.text1, align: "right" });
    drawER(H, s);
  }

  // ------------------------------------------------------------ 5b security, triggers, views
  {
    const s = H.slide("CONTENT", "Database", "Login, Triggers and Views",
      "Two tables were added after Review 2. App User stores login accounts: username, role and a salted password hash, never the password. An employee account is linked to an employee row. Audit Log has no foreign keys on purpose: it is written only by database triggers. There are six triggers. Three audit triggers fire after an update of a salary structure, an employee's status, or a payroll rate, and write the old and new values to Audit Log. Three lock triggers fire before an insert, update or delete on payroll detail and refuse the change when the payroll period is no longer OPEN, so paid payroll cannot be altered even by someone who bypasses the application. The trigger on the right is the SQLite version; MySQL uses SIGNAL instead of RAISE, so I wrote the two files separately. There are also three views for reporting. I tested all of this on SQLite and on a real MySQL 8 server.");
    await H.titleIcon(s, "FaBolt");
    const box = (t, x, y, w, h, kind) => s.addText(t, { isTextBox: true, x, y, w, h, shape: pres.ShapeType.roundRect, rectRadius: 0.07,
      fill: { color: kind === "dark" ? C.accent3 : kind === "mid" ? C.accent1 : C.background1 }, line: { color: kind === "out" ? C.accent2 : C.accent3, width: kind === "out" ? 1.75 : 1 },
      color: kind === "dark" || kind === "mid" ? C.background1 : C.text2, bold: true, fontSize: 11, align: "center", valign: "middle", margin: 0.03 });
    const tag = (t, x, y, w) => s.addText(t, { isTextBox: true, x, y, w, h: 0.22, fontSize: 9.5, bold: true, color: C.accent3, align: "center", valign: "middle", margin: 0 });
    // login
    box("employee", 0.5, 1.3, 1.5, 0.45, "dark"); box("app_user\n(role, hash)", 2.9, 1.25, 1.7, 0.55, "out");
    H.line(s, 2.0, 1.52, 2.9, 1.52, { color: C.accent4, width: 1.5 }); tag("0..1 login", 2.0, 1.28, 0.9);
    // audit
    ["salary_structure", "employee (status)", "payroll_config"].forEach((t, i) => { box(t, 0.5, 2.15 + i * 0.5, 1.7, 0.4, "mid"); H.arrow(s, 2.2, 2.35 + i * 0.5, 2.9, 2.85, { color: C.accent2, width: 1.5 }); });
    box("audit_log", 2.9, 2.6, 1.7, 0.5, "out"); tag("3 audit triggers (AFTER UPDATE)", 0.5, 3.65, 4.1);
    // lock
    box("payroll_period\n(status)", 0.5, 4.15, 1.7, 0.55, "mid"); box("payroll_detail", 2.9, 4.15, 1.7, 0.55, "out");
    H.arrow(s, 2.2, 4.42, 2.9, 4.42, { color: C.accent2, width: 2 }); tag("3 lock triggers (BEFORE INSERT/UPDATE/DELETE)", 0.5, 4.78, 4.1);
    H.pill(s, "SQLite trigger: lock paid payroll", 5.1, 1.2, 3.0, { fill: { color: C.accent2 }, color: C.background1 });
    H.sql(s, `CREATE TRIGGER trg_payroll_detail_lock_update
BEFORE UPDATE ON payroll_detail
FOR EACH ROW
WHEN (SELECT status FROM payroll_period
      WHERE payroll_period_id =
            OLD.payroll_period_id) <> 'OPEN'
BEGIN
  SELECT RAISE(ABORT,
   'Payroll history is locked:
    the period is no longer OPEN');
END;`, 5.1, 1.53, 4.4, 2.2, 9);
    H.card(s, 5.1, 3.9, 4.4, 1.2);
    H.text(s, [{ text: "Views  ", options: { bold: true, color: C.text2 } }, { text: "v_payroll_summary, v_department_cost, v_loan_ledger", options: { color: C.text1, breakLine: true } },
      { text: "Tested  ", options: { bold: true, color: C.text2 } }, { text: "on SQLite and on a real MySQL 8 server (SIGNAL variant)", options: { color: C.text1 } }],
      { x: 5.25, y: 3.98, w: 4.1, h: 1.05, fontSize: 11.5, valign: "middle", paraSpaceAfter: 4 });
  }

  // ------------------------------------------------------------ 6 relational schema summary
  {
    const s = H.slide("CONTENT", "Database", "Final Relational Schema",
      "This table summarises the final relational schema: sixteen tables, sixteen primary keys and seventeen foreign keys. App User and Audit Log are the two tables added after Review 2. Most tables are in third normal form. Payroll detail is the one deliberate exception: it stores a snapshot of the calculated gross, deductions and net for each employee and month, so that a payslip never changes later even if the salary structure or rates are edited. Loss of pay days are not stored because they can be derived from working days, days present and paid leave. Row counts are the counts in the current demo database.");
    await H.titleIcon(s, "FaTable");
    const t = facts.tables;
    const rows = [
      ["department", "department_id", "-", t.department], ["designation", "designation_id", "-", t.designation], ["payroll_config", "config_key", "-", t.payroll_config],
      ["employee", "employee_id", "department_id, designation_id", t.employee], ["salary_structure", "salary_structure_id", "employee_id (unique)", t.salary_structure],
      ["payroll_period", "payroll_period_id", "-", t.payroll_period], ["attendance_summary", "attendance_id", "employee_id, payroll_period_id", t.attendance_summary],
      ["earnings", "earning_id", "employee_id, payroll_period_id", t.earnings], ["deductions", "deduction_id", "employee_id, payroll_period_id", t.deductions],
      ["loan", "loan_id", "employee_id", t.loan], ["payroll_detail", "payroll_id", "employee_id, payroll_period_id", t.payroll_detail],
      ["loan_repayment", "repayment_id", "loan_id, payroll_id (nullable)", t.loan_repayment], ["payslip", "payslip_id", "payroll_id (unique)", t.payslip], ["bank_transfer", "transfer_id", "payroll_id (unique)", t.bank_transfer],
      ["app_user", "user_id", "employee_id (nullable)", t.app_user], ["audit_log", "audit_id", "- (written by triggers)", t.audit_log],
    ];
    H.table(s, ["Table", "Primary key", "Foreign keys", "Rows"], rows, 0.5, 1.15, 9.0, [2.1, 2.3, 3.9, 0.7], { fontSize: 9.5, rowH: 0.205 });
    H.text(s, "Constraints in the schema:  " + facts.constraints.primary_keys + " PK  |  " + facts.constraints.foreign_keys + " FK  |  " + facts.constraints.unique + " UNIQUE  |  " + facts.constraints.check + " CHECK  |  " + facts.constraints.indexes + " indexes",
      { x: 0.5, y: 5.04, w: 9.0, h: 0.22, fontSize: 10.5, bold: true, color: C.accent3 });
  }

  // ------------------------------------------------------------ 7 dashboard
  {
    const s = H.slide("CONTENT", "Application", "Final Application: Dashboard",
      "This is the finished dashboard after October 2026 has been processed. The tiles and charts are live SQL aggregates, not typed-in numbers: active employees, gross, deductions and net for the latest processed period, departments, open loans and outstanding balance, and pending transfers. The charts compare gross, deductions and net across the three payroll months and show headcount by department. The screenshot was taken from the running application against the synthetic demo database.");
    await H.titleIcon(s, "FaChartPie");
    H.shot(s, "27_dashboard_after_october.png", 0.5, 1.3, 5.4);
    H.bullets(s, [["Live SQL: ", "every tile and chart is an aggregate query"], ["Latest period: ", "October 2026, 29 employees paid"],
      ["Totals: ", inr(facts.oct_result.gross) + " gross, " + inr(facts.oct_result.net) + " net"], ["Charts: ", "three months, headcount by department"]], 6.2, 1.3, 3.3, 3.0, { fontSize: 13 });
    H.card(s, 0.5, 4.45, 9.0, 0.65);
    H.text(s, "Synthetic data only: names, e-mails and bank accounts are invented for the demonstration.", { x: 0.7, y: 4.5, w: 8.6, h: 0.55, fontSize: 12, color: C.text1, valign: "middle" });
  }

  // ------------------------------------------------------------ 7b roles and security
  {
    const s = H.slide("CONTENT", "Application", "Login, Roles and Security",
      "The application now requires a login. There are three roles. The administrator can do everything, including editing rates, managing user accounts and using the Database Explorer. HR can manage employees, salaries, attendance, loans and run payroll, but cannot open rates, users or the explorer. An employee can see only their own profile, loans and payslips: on the left is the employee view for EMP003 Pranav, and on the right is what happens when that employee tries to open the payroll register: a 403 Not allowed page. Passwords are never stored; only salted PBKDF2 hashes are. Every form carries a CSRF token, five failed logins lock a username for five minutes, the session is renewed at login, and a Forgot password link creates a signed reset link that expires after fifteen minutes and works only once. The demo has no e-mail server, so the link is shown on screen. This is a local demo: there is no HTTPS and the login throttle is in memory, so I do not claim it is ready for the internet.");
    await H.titleIcon(s, "FaUserShield");
    H.shotC(s, "30_employee_self_service.png", 0.5, 1.25, 4.4);
    H.shotC(s, "31_access_denied_for_employee.png", 5.1, 1.25, 4.4);
    H.text(s, "EMPLOYEE role: only own payslips", { x: 0.5, y: 3.78, w: 4.4, h: 0.26, fontSize: 12, bold: true, color: C.text2, align: "center" });
    H.text(s, "Same user opens the payroll register: 403", { x: 5.1, y: 3.78, w: 4.4, h: 0.26, fontSize: 12, bold: true, color: C.text2, align: "center" });
    H.table(s, ["Role", "Can do"], [["ADMIN", "everything + rates, users, Database Explorer"], ["HR", "manage data, run payroll, payslips, reports"], ["EMPLOYEE", "own profile, loans and payslips only"]], 0.5, 4.1, 5.3, [1.0, 4.3], { fontSize: 10, rowH: 0.24 });
    H.card(s, 6.0, 4.1, 3.5, 1.0);
    H.text(s, "Salted PBKDF2 hashes · CSRF tokens · login throttle · own-payslip check · signed one-time password-reset links", { x: 6.15, y: 4.13, w: 3.2, h: 0.94, fontSize: 11, color: C.text1, valign: "middle" });
  }

  // ------------------------------------------------------------ 8 demo flow
  {
    const s = H.slide("CONTENT", "Application", "Demonstration Flow",
      "This is the order I will follow in the live demo, and it takes about five minutes. One: sign in as the administrator and show the dashboard. Two: open the employee list and add a new employee. Three: show the salary structure and the October attendance. Four: show the loan with its repayment history. Five: process October payroll with one click. Six: open a payslip and check the arithmetic. Seven: generate bank transfers and mark them paid. Eight: open the Database Explorer to show the triggers, the audit trail and the read-only SQL console, then a report with its SQL. Every step in the deck corresponds to a real screenshot.");
    await H.titleIcon(s, "FaPlayCircle");
    const steps = [["1", "Sign in", "admin / hr / employee"], ["2", "Employees", "add / edit"], ["3", "Salary + attendance", "monthly inputs"], ["4", "Loans", "EMI, balance"],
      ["5", "Process payroll", "one click"], ["6", "Payslip", "check the maths"], ["7", "Bank transfers", "pending > paid"], ["8", "Explorer + reports", "triggers, audit, SQL"]];
    steps.forEach((st, i) => {
      const col = i % 4, row = Math.floor(i / 4);
      const x = 0.5 + col * 2.3, y = 1.25 + row * 1.55;
      H.card(s, x, y, 2.0, 1.4);
      s.addShape(pres.ShapeType.ellipse, { x: x + 0.75, y: y + 0.12, w: 0.5, h: 0.5, fill: { color: i === 4 ? C.accent2 : C.accent3 }, line: { color: C.background1, width: 0 } });
      H.text(s, st[0], { x: x + 0.75, y: y + 0.12, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: C.background1, align: "center", valign: "middle" });
      H.text(s, st[1], { x: x + 0.1, y: y + 0.72, w: 1.8, h: 0.3, fontSize: 13, bold: true, color: C.text2, align: "center" });
      H.text(s, st[2], { x: x + 0.1, y: y + 1.02, w: 1.8, h: 0.28, fontSize: 11, color: C.text1, align: "center" });
      if (col < 3) H.arrow(s, x + 2.02, y + 0.7, x + 2.28, y + 0.7, { color: C.accent4, width: 2 });
    });
    H.card(s, 0.5, 4.5, 9.0, 0.6);
    H.text(s, "Reset the demo database at any time:  python scripts/init_db.py", { x: 0.7, y: 4.52, w: 8.6, h: 0.56, fontSize: 13, color: C.text2, valign: "middle", fontFace: "Courier New" });
  }

  // ------------------------------------------------------------ 9 payroll workflow
  {
    const s = H.slide("CONTENT", "Payroll", "Payroll Workflow",
      "Payroll runs through a fixed life cycle. First the officer enters or confirms the inputs for the month: attendance, extra earnings and manual deductions. A period starts as OPEN. Pressing Process payroll calculates every active employee in one database transaction, writes the payroll detail, the itemised deduction rows, the payslip numbers and the loan repayments, and moves the period to PROCESSED. Because it is one transaction, any failure rolls everything back, and from then on database triggers refuse any change to that period's payroll rows. Then Generate bank transfers creates one pending transfer per payslip, and Mark transfers paid completes the cycle and sets the period to PAID. Once processed, the inputs for that period are locked, and a period cannot be processed twice.");
    await H.titleIcon(s, "FaStream");
    const st = [["OPEN", "Enter attendance,\nearnings, deductions", C.accent4, C.text2], ["PROCESSED", "Gross, deductions,\nnet + payslips written", C.accent1, C.background1], ["PAID", "Transfers marked\npaid, history locked", C.accent3, C.background1]];
    st.forEach((t, i) => {
      const x = 0.7 + i * 3.1;
      s.addText([{ text: t[0], options: { bold: true, fontSize: 16, breakLine: true } }, { text: t[1], options: { fontSize: 11 } }],
        { isTextBox: true, x, y: 1.25, w: 2.5, h: 1.0, shape: pres.ShapeType.roundRect, rectRadius: 0.1, fill: { color: t[2] }, color: t[3], align: "center", valign: "middle", margin: 0.05 });
      if (i < 2) H.arrow(s, x + 2.55, 1.75, x + 3.05, 1.75, { color: C.accent2, width: 2.5 });
    });
    H.text(s, "Process payroll", { x: 3.3, y: 2.3, w: 1.8, h: 0.22, fontSize: 10, bold: true, color: C.accent3, align: "center" });
    H.text(s, "Mark transfers paid", { x: 6.4, y: 2.3, w: 2.0, h: 0.22, fontSize: 10, bold: true, color: C.accent3, align: "center" });
    const steps = ["Load active employees,\nsalary and attendance", "Compute gross, LOP,\nstatutory deductions", "Apply loan EMI and\nmanual deductions", "Insert payroll_detail,\ndeductions, payslip", "Update loan balance,\nwrite repayment row"];
    H.text(s, "Inside the single transaction", { x: 0.5, y: 2.65, w: 5, h: 0.3, fontSize: 14, bold: true, color: C.text2, fontFace: "Cambria" });
    steps.forEach((t, i) => {
      const x = 0.5 + i * 1.82;
      H.card(s, x, 3.0, 1.65, 0.9);
      H.text(s, t, { x: x + 0.05, y: 3.02, w: 1.55, h: 0.86, fontSize: 10.5, color: C.text1, align: "center", valign: "middle" });
      if (i < 4) H.arrow(s, x + 1.66, 3.45, x + 1.81, 3.45, { color: C.accent4, width: 1.5 });
    });
    H.dark(s, 0.5, 4.15, 9.0, 0.95);
    H.bullets(s, [["Safe: ", "any error rolls the whole run back"], ["Locked: ", "a processed period cannot be processed again; triggers block edits to its rows"], ["Skipped and reported: ", "inactive employees, missing salary or attendance"]],
      0.7, 4.22, 8.6, 0.85, { fontSize: 12, color: C.background1, leadColor: C.accent2, paraSpaceAfter: 2 });
  }

  // ------------------------------------------------------------ 10 calculation + worked example
  {
    const sp = facts.sample_payslip;
    const s = H.slide("CONTENT", "Payroll", "Calculation Rules and Worked Example",
      "These are the payroll rules, and I want to be clear that the rates are illustrative and editable in the configuration table; they are not official statutory rates. Gross is the fixed salary components minus loss of pay plus any extra earnings. Provident fund is twelve percent of basic capped at fifteen thousand. ESI is zero point seven five percent of gross, only when gross is twenty-one thousand or less. Professional tax is a flat two hundred above fifteen thousand. TDS is a simple five percent of gross above fifty thousand. Loan EMI is the smaller of the EMI and the outstanding balance. On the right is a worked example for employee EMP003 in October 2026: fixed gross is one lakh one hundred thirty rupees, PF is eighteen hundred, PT two hundred, TDS twenty-five hundred and six point five, EMI five thousand, so total deductions are nine thousand five hundred six point five and net salary is ninety thousand six hundred twenty-three point five. These numbers are also hand-checked in the unit tests.");
    await H.titleIcon(s, "FaCalculator");
    H.card(s, 0.5, 1.25, 4.5, 3.85);
    H.text(s, "Rules (illustrative, editable)", { x: 0.7, y: 1.33, w: 4.1, h: 0.3, fontSize: 14, bold: true, color: C.text2 });
    H.bullets(s, [["Gross = ", "fixed - loss of pay + extra earnings"], ["LOP = ", "fixed / working days x LOP days"], ["PF = ", "12% of basic, basic capped at 15,000"], ["ESI = ", "0.75% of gross, only if gross <= 21,000"],
      ["PT = ", "200 if gross > 15,000"], ["TDS = ", "5% of gross above 50,000"], ["EMI = ", "min(EMI, outstanding), ACTIVE loans"], ["Net = ", "gross - total deductions"]], 0.7, 1.7, 4.2, 3.35, { fontSize: 12.5, paraSpaceAfter: 6 });
    H.dark(s, 5.2, 1.25, 4.3, 3.85);
    H.text(s, "Worked example: EMP003, Oct 2026", { x: 5.4, y: 1.33, w: 3.9, h: 0.3, fontSize: 14, bold: true, color: C.accent2 });
    const rows = [["Basic", sp.basic_salary], ["HRA", sp.hra], ["DA", sp.da], ["Special", sp.special_allowance], ["Gross", sp.gross_salary], ["PF", 1800], ["PT", 200], ["TDS", 2506.5], ["Loan EMI", 5000], ["Total deductions", sp.total_deductions], ["Net salary", sp.net_salary]];
    const tb = rows.map((r) => { const bold = ["Gross", "Total deductions", "Net salary"].includes(r[0]);
      return [{ text: r[0], options: { color: bold ? C.accent2 : C.background1, bold, fontSize: 11.5 } }, { text: Number(r[1]).toLocaleString("en-IN", { minimumFractionDigits: 2 }), options: { color: bold ? C.accent2 : C.background1, bold, align: "right", fontSize: 11.5 } }]; });
    s.addTable(tb, { x: 5.4, y: 1.7, w: 3.9, colW: [2.2, 1.7], rowH: 0.29, border: { type: "none" }, margin: [0.02, 0.05, 0.02, 0.05] });
  }

  // ------------------------------------------------------------ 11 payslip
  {
    const s = H.slide("CONTENT", "Payroll", "Payslip Output",
      "This is the payslip for EMP003 in October, generated by the application from the payroll detail row. It shows the earnings and deductions side by side, the gross, total deductions and the net salary payable, the working and loss of pay days, the bank details, and the linked bank transfer reference. The payslip number is built from the year, month and employee code. It can be printed or saved as PDF from the browser. The footer states plainly that the rates are illustrative and the data is synthetic. The figures match the worked example on the previous slide.");
    await H.titleIcon(s, "FaFileInvoice");
    H.shotC(s, "22_payslip.png", 0.5, 1.25, 5.2);
    H.bullets(s, [["Numbered: ", "PS-202610-EMP003"], ["Itemised: ", "each earning and deduction line"], ["Net payable: ", "Rs 90,623.50"], ["Linked: ", "bank transfer reference TXN00300061"], ["Printable: ", "Print / Save PDF button"]], 6.0, 1.3, 3.5, 2.9, { fontSize: 12.5 });
    H.card(s, 0.5, 4.3, 9.0, 0.8);
    H.text(s, "Payslip figures are read from payroll_detail and deductions; the page performs no recalculation, so a payslip cannot drift from what was paid.", { x: 0.7, y: 4.33, w: 8.6, h: 0.74, fontSize: 12.5, color: C.text1, valign: "middle" });
  }

  // ------------------------------------------------------------ 12 bank transfers
  {
    const s = H.slide("CONTENT", "Payroll", "Bank Transfer Records",
      "After processing, the system generates one transfer record per payslip using the employee's stored bank details, the net salary as the amount, and a reference number. On the left they are PENDING. After the officer chooses Mark transfers paid, they become SUCCESS with a date, as on the right, and the period moves to PAID. I want to be explicit that this is a simulation of the record keeping: there is no connection to any real bank and no money moves. The bank account numbers are fake.");
    await H.titleIcon(s, "FaUniversity");
    H.shotC(s, "23_bank_transfers_pending.png", 0.5, 1.3, 4.4);
    H.arrow(s, 4.95, 2.1, 5.05, 2.1, { color: C.accent2, width: 2 });
    H.shotC(s, "24_bank_transfers_paid.png", 5.1, 1.3, 4.4);
    H.text(s, "Before: status PENDING", { x: 0.5, y: 3.95, w: 4.4, h: 0.28, fontSize: 12, bold: true, color: C.text2, align: "center" });
    H.text(s, "After: status SUCCESS, period PAID", { x: 5.1, y: 3.95, w: 4.4, h: 0.28, fontSize: 12, bold: true, color: C.text2, align: "center" });
    H.card(s, 0.5, 4.4, 9.0, 0.7);
    H.text(s, [{ text: "Simulated: ", options: { bold: true, color: C.accent2 } }, { text: "records only, no real bank API, synthetic account numbers. One transfer per payslip (UNIQUE payroll_id).", options: { color: C.text1 } }],
      { x: 0.7, y: 4.43, w: 8.6, h: 0.64, fontSize: 12.5, valign: "middle" });
  }

  // ------------------------------------------------------------ 13 reports
  {
    const s = H.slide("CONTENT", "Reports", "Reports",
      "The reports page offers seven reports, and each one has a View SQL button that shows the exact query that produced it. They are: payroll summary by period, department wise payroll cost, statutory deduction breakdown, top five net salaries, employees above their department's average gross, active loans with outstanding balance, and active employees without payroll in the selected period. The screenshot on the right shows the subquery report with its SQL expanded, which is useful in the viva because the query and result are on one screen. The payroll register can also be exported to CSV.");
    await H.titleIcon(s, "FaChartBar");
    H.shotC(s, "25_reports_top.png", 0.5, 1.3, 4.4);
    H.shotC(s, "26_report_sql_subquery.png", 5.1, 1.3, 4.4);
    H.text(s, "Reports page, period selector", { x: 0.5, y: 3.95, w: 4.4, h: 0.28, fontSize: 12, bold: true, color: C.text2, align: "center" });
    H.text(s, "Subquery report with its SQL shown", { x: 5.1, y: 3.95, w: 4.4, h: 0.28, fontSize: 12, bold: true, color: C.text2, align: "center" });
    H.card(s, 0.5, 4.4, 9.0, 0.7);
    H.text(s, "7 reports: period summary, department cost, statutory breakdown, top 5 net, above department average, active loans, not yet processed.", { x: 0.7, y: 4.43, w: 8.6, h: 0.64, fontSize: 12, color: C.text1, valign: "middle" });
  }

  // ------------------------------------------------------------ 14 SQL
  {
    const s = H.slide("CONTENT", "Reports", "SQL Queries Behind the Results",
      "These are simplified excerpts from database/queries.sql, which I run in full as part of the automated tests. On the left is the cross-check I use to prove the payroll is internally consistent: for every payroll row, net must equal gross minus total deductions. The query returns zero rows when the data is correct. In the middle is NOT EXISTS, which finds active employees that have no payroll yet for a period. On the right is an aggregate with GROUP BY that totals gross, deductions and net per period. The same file also contains inner and left joins, HAVING, scalar, IN, correlated and derived-table subqueries, and a view for payslip summaries.");
    await H.titleIcon(s, "FaDatabase");
    const P = [
      ["Consistency check", `SELECT payroll_id
FROM payroll_detail
WHERE ROUND(gross_salary
        - total_deductions, 2)
      <> net_salary;
-- expected: 0 rows`],
      ["NOT EXISTS", `SELECT e.emp_code
FROM employee e
WHERE e.status = 'ACTIVE'
 AND NOT EXISTS (
  SELECT 1 FROM payroll_detail p
  WHERE p.employee_id =
        e.employee_id
    AND p.payroll_period_id = 3);`],
      ["GROUP BY aggregate", `SELECT pp.period_name,
  COUNT(*) AS employees,
  SUM(p.gross_salary) AS gross,
  SUM(p.total_deductions) AS ded,
  SUM(p.net_salary) AS net
FROM payroll_detail p
JOIN payroll_period pp
  ON pp.payroll_period_id =
     p.payroll_period_id
GROUP BY pp.period_name;`],
    ];
    P.forEach((p, i) => {
      const x = 0.5 + i * 3.05;
      H.pill(s, p[0], x, 1.2, 2.2, { fill: { color: C.accent2 }, color: C.background1 });
      H.sql(s, p[1], x, 1.53, 2.9, 2.5, 9);
    });
    H.card(s, 0.5, 4.3, 9.0, 0.7);
    H.text(s, "Also in queries.sql: INNER/LEFT JOIN, HAVING, scalar, IN, correlated and derived-table subqueries, a VIEW. All executed by the test suite.", { x: 0.7, y: 4.33, w: 8.6, h: 0.64, fontSize: 12, color: C.text1, valign: "middle" });
  }

  // ------------------------------------------------------------ 14b database explorer
  {
    const s = H.slide("CONTENT", "Reports", "Database Explorer and Audit Trail",
      "The Database Explorer is an administrator-only page that reads the live structure of the connected database: tables with row counts, columns, primary keys, foreign keys with their delete rules, the three views and the six triggers. Below it is a SQL console. It accepts a single SELECT, runs it on a separate read-only connection with a five second limit and a two hundred row limit, and refuses the user table so password hashes are never shown. On the left I ran a SELECT on the department cost view. On the right I typed a DELETE and it was refused. The strip at the bottom is a real audit row: I edited a salary structure through the normal form and the database trigger recorded the old and new salary. The same page works on MySQL; I tested introspection and the console there too.");
    await H.titleIcon(s, "FaDatabase");
    H.shotC(s, "33_sql_console_view_query.png", 0.5, 1.25, 4.4);
    H.shotC(s, "34_sql_console_blocks_writes.png", 5.1, 1.25, 4.4);
    H.text(s, "SELECT on a view runs", { x: 0.5, y: 3.78, w: 4.4, h: 0.26, fontSize: 12, bold: true, color: C.text2, align: "center" });
    H.text(s, "DELETE is refused (read-only)", { x: 5.1, y: 3.78, w: 4.4, h: 0.26, fontSize: 12, bold: true, color: C.text2, align: "center" });
    const ah = 9.0 * 165 / 1722;
    s.addShape(pres.ShapeType.rect, { x: 0.46, y: 4.1, w: 9.08, h: ah + 0.08, fill: { color: C.background1 }, line: { color: HEX.line, width: 1 } });
    s.addImage({ path: path.join(ROOT, "screenshots", "35_audit_trail_from_trigger.png"), x: 0.5, y: 4.14, w: 9.0, h: ah, altText: "Audit trail row written by a database trigger after a salary edit" });
    H.text(s, "Audit row written by a trigger after a salary edit in the web form", { x: 0.5, y: 4.14 + ah + 0.1, w: 9.0, h: 0.25, fontSize: 11, italic: true, color: C.text1, align: "center" });
  }

  // ------------------------------------------------------------ 15 results chart
  {
    const s = H.slide("CONTENT", "Results", "Payroll Results by Month",
      "These are the real results from the three payroll months in the demo database, taken directly from the database. Each month has twenty-nine paid employees; the thirtieth employee is inactive and is skipped. Gross is about nineteen and a half lakh to nineteen point six lakh a month, total deductions rise from about 1.19 lakh in August to 1.39 lakh in October, and net salary stays around eighteen lakh. The table beside the chart gives the exact numbers. The data is synthetic, so these are demonstration results, not statistics of any real organisation.");
    await H.titleIcon(s, "FaChartLine");
    const labels = facts.periods.map((p) => p.period_name.replace(" 2026", ""));
    s.addChart(pres.charts.BAR, [
      { name: "Gross", labels, values: facts.periods.map((p) => Math.round(p.gross / 1000)) },
      { name: "Deductions", labels, values: facts.periods.map((p) => Math.round(p.ded / 1000)) },
      { name: "Net", labels, values: facts.periods.map((p) => Math.round(p.net / 1000)) }],
      { x: 0.5, y: 1.2, w: 5.2, h: 3.3, barDir: "col", barGrouping: "clustered", chartColors: [HEX.blue, HEX.gold, HEX.navy], showTitle: true, title: "Rs thousands per month", titleFontSize: 13, titleColor: HEX.navy, titleFontFace: "+mn-lt",
        showLegend: true, legendPos: "b", legendFontSize: 11, legendColor: HEX.ink, legendFontFace: "+mn-lt", showValue: false,
        catAxisLabelColor: HEX.ink, catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", valAxisLabelColor: HEX.muted, valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt",
        valGridLine: { color: HEX.line, size: 0.5 }, catGridLine: { style: "none" } });
    const rows = facts.periods.map((p) => [p.period_name.replace(" 2026", ""), String(p.n), Math.round(p.gross).toLocaleString("en-IN"), Math.round(p.ded).toLocaleString("en-IN"), Math.round(p.net).toLocaleString("en-IN")]);
    H.table(s, ["Month", "Paid", "Gross", "Deductions", "Net"], rows, 5.9, 1.25, 3.6, [0.8, 0.5, 0.8, 0.8, 0.7], { fontSize: 9.5, rowH: 0.34 });
    H.card(s, 5.9, 2.8, 3.6, 1.7);
    H.bullets(s, [["29 paid ", "each month; employee 30 is inactive"], ["Rs figures ", "rounded to whole rupees"], ["Synthetic ", "demonstration data"]], 6.05, 2.9, 3.3, 1.55, { fontSize: 12 });
    H.card(s, 0.5, 4.6, 9.0, 0.5);
    H.text(s, "Source: payroll_detail totals per period, read from the demo database (scripts/collect_facts.py).", { x: 0.7, y: 4.62, w: 8.6, h: 0.46, fontSize: 11.5, color: C.text1, valign: "middle" });
  }

  // ------------------------------------------------------------ 16 integrity demos
  {
    const s = H.slide("CONTENT", "Results", "Data Integrity in Action",
      "Two screenshots show the database protecting the data. On the left I tried to add an employee with a code that already exists. The UNIQUE constraint rejected it and the application shows a readable message instead of a stack trace. On the right I tried to add a bonus to August 2026, which is already paid. The application refuses because processed periods are locked. Together with foreign keys, CHECK constraints and ON DELETE RESTRICT on payroll history, these rules mean a payroll record cannot be silently changed or orphaned.");
    await H.titleIcon(s, "FaShieldAlt");
    H.shotC(s, "07_constraint_duplicate_code.png", 0.5, 1.3, 4.4);
    H.shotC(s, "16_period_locked_error.png", 5.1, 1.3, 4.4);
    H.text(s, "Duplicate employee code rejected (UNIQUE)", { x: 0.5, y: 3.95, w: 4.4, h: 0.28, fontSize: 12, bold: true, color: C.text2, align: "center" });
    H.text(s, "Edit to a paid period refused (lock)", { x: 5.1, y: 3.95, w: 4.4, h: 0.28, fontSize: 12, bold: true, color: C.text2, align: "center" });
    H.card(s, 0.5, 4.4, 9.0, 0.7);
    H.text(s, "PK, FK, UNIQUE, CHECK and ON DELETE RESTRICT/CASCADE are enforced by the database, not only by the Python code.", { x: 0.7, y: 4.43, w: 8.6, h: 0.64, fontSize: 12.5, color: C.text1, valign: "middle" });
  }

  // ------------------------------------------------------------ 17 testing
  {
    const ts = facts.test_suites;
    const s = H.slide("CONTENT", "Results", "Testing Results",
      "All " + sqliteTests + " automated SQLite tests pass, and a separate suite of " + mysqlTests + " tests also passes on a real MySQL 8.0.46 server. The recorded outputs are in tests slash test_results dot txt and test_results_mysql dot txt. The SQLite suites cover calculation against hand-computed numbers, database constraints, payroll processing including rollback and double processing, the triggers and views, authentication and roles, password reset, amounts in words, the explorer, and the web layer. The MySQL suite checks that the payroll totals are identical to SQLite, that constraints and triggers work, that queries dot sql runs completely, and that the web app works and processes October. The MySQL run found one real bug: MySQL reports a violated CHECK constraint and a trigger signal as an operational error instead of an integrity error, which would have crashed pages; it is fixed. What I have not tested: the GitHub Actions workflow has not run yet, other MySQL versions or MariaDB, other browsers than headless Chromium, and many concurrent users.");
    await H.titleIcon(s, "FaBug");
    s.addChart(pres.charts.BAR, [{ name: "Tests passed", labels: ["Web / CRUD", "Authentication + roles", "Payroll processing", "Database", "Triggers + views", "Explorer", "Password reset + words", "Calculation"], values: [ts.WebTests, ts.AuthTests, ts.PayrollProcessingTests, ts.DatabaseTests, ts.TriggerAndViewTests, ts.ExplorerTests, (ts.PasswordResetTests || 0) + (ts.AmountInWordsTests || 0), ts.CalcTests] }],
      { x: 0.5, y: 1.2, w: 5.0, h: 3.15, barDir: "bar", chartColors: [HEX.blue], showTitle: true, title: "SQLite tests by suite", titleFontSize: 13, titleColor: HEX.navy, titleFontFace: "+mn-lt",
        showValue: true, dataLabelPosition: "outEnd", dataLabelColor: HEX.ink, dataLabelFontSize: 11, dataLabelFontFace: "+mn-lt", showLegend: false,
        catAxisLabelColor: HEX.ink, catAxisLabelFontSize: 11, catAxisLabelFontFace: "+mn-lt", valAxisLabelColor: HEX.muted, valAxisLabelFontSize: 10, valAxisLabelFontFace: "+mn-lt",
        valGridLine: { color: HEX.line, size: 0.5 }, catGridLine: { style: "none" }, valAxisMaxVal: 20, valAxisMinVal: 0, valAxisMajorUnit: 5 });
    H.stat(s, sqliteTests + " / " + sqliteTests, "SQLite tests passed", 5.7, 1.25, 1.85, 1.05, { size: 24 });
    H.stat(s, mysqlTests + " / " + mysqlTests, "MySQL 8.0.46 tests passed", 7.65, 1.25, 1.85, 1.05, { size: 24 });
    H.card(s, 5.7, 2.45, 3.8, 1.9);
    H.text(s, "Verified", { x: 5.85, y: 2.5, w: 3.5, h: 0.28, fontSize: 13, bold: true, color: C.text2 });
    H.bullets(s, ["Formulas vs hand-computed values", "Constraints and triggers reject bad data", "Rollback and double-process guard", "Roles, CSRF, own-payslip rule", "Same payroll totals on SQLite and MySQL", "MySQL run found and fixed a real bug"], 5.85, 2.8, 3.55, 1.55, { fontSize: 10.5, paraSpaceAfter: 0 });
    H.card(s, 0.5, 4.45, 9.0, 0.65);
    H.text(s, [{ text: "Not tested: ", options: { bold: true, color: C.accent2 } }, { text: "GitHub Actions run  |  other MySQL versions, MariaDB  |  browsers other than headless Chromium  |  concurrent users", options: { color: C.text1 } }],
      { x: 0.7, y: 4.47, w: 8.6, h: 0.6, fontSize: 12, valign: "middle" });
  }

  // ------------------------------------------------------------ 18 limitations
  {
    const s = H.slide("CONTENT", "Conclusion", "Limitations",
      "I want to be honest about what this project is not. Security is demo-grade: there are roles, hashed passwords and CSRF tokens, but no HTTPS, and the login throttle is in memory. The bank transfers are simulated records. The deduction rates are illustrative and editable, and are not official statutory rates, so the output must not be used for real payroll. The MySQL scripts were run and tested on one server, version 8.0.46; other versions and MariaDB are untested. The data is synthetic with about thirty employees. Finally, the audit trail records what changed but not which web user changed it, because triggers cannot see the web user.");
    await H.titleIcon(s, "FaExclamationTriangle");
    const L = [["FaUserLock", "Demo-grade security", "Roles, hashes, CSRF done; but no HTTPS, in-memory login throttle"], ["FaUniversity", "Simulated transfers", "Records only; no real bank API"],
      ["FaPercent", "Illustrative rates", "Editable, not official statutory slabs"], ["FaServer", "One MySQL version", "Tested on 8.0.46 only; MariaDB and others untested"],
      ["FaUsers", "Small scale", "30 synthetic employees, local single server"], ["FaHistory", "Audit lacks user name", "Triggers cannot see the web user who made the change"]];
    for (let i = 0; i < L.length; i++) {
      const col = i % 3, row = Math.floor(i / 3);
      const x = 0.5 + col * 3.05, y = 1.3 + row * 1.85;
      H.card(s, x, y, 2.9, 1.65);
      await H.circleIcon(s, L[i][0], x + 0.15, y + 0.15, 0.5, C.accent2, "#FFFFFF");
      H.text(s, L[i][1], { x: x + 0.78, y: y + 0.15, w: 2.0, h: 0.5, fontSize: 13, bold: true, color: C.text2, valign: "middle" });
      H.text(s, L[i][2], { x: x + 0.15, y: y + 0.8, w: 2.6, h: 0.8, fontSize: 12, color: C.text1 });
    }
  }

  // ------------------------------------------------------------ 19 conclusion
  {
    const s = H.slide("DARK", "Conclusion", "Conclusion",
      "To conclude: I took the Review 1 design and delivered a working payroll system. The database has sixteen tables with primary keys, foreign keys, unique and check constraints, plus triggers and views. The payroll engine computes gross, statutory and loan deductions and net salary for each employee in one safe transaction. Payslips, simulated bank transfers and seven reports are produced from that data, with login roles on top. " + sqliteTests + " automated tests pass on SQLite and " + mysqlTests + " on a real MySQL 8 server. The project taught me that the database should enforce the rules, not only the application. With more time I would replace the illustrative rates with official ones, record the acting user in the audit trail, add PDF payslips and deploy behind HTTPS.");
    await H.titleIcon(s, "FaCheckCircle", true);
    const st = [[String(facts.constraints.tables), "tables, " + facts.constraints.foreign_keys + " foreign keys"], ["12 / 12", "requirements delivered"], [sqliteTests + " + " + mysqlTests, "tests: SQLite + MySQL"], ["6", "triggers, 3 views"]];
    st.forEach((t, i) => {
      const x = 0.5 + i * 2.28;
      H.dark(s, x, 1.3, 2.1, 1.2, { fill: { color: C.accent3 } });
      H.text(s, t[0], { x, y: 1.4, w: 2.1, h: 0.6, fontSize: 28, bold: true, color: C.accent2, align: "center", valign: "middle", fontFace: "Cambria" });
      H.text(s, t[1], { x: x + 0.1, y: 2.02, w: 1.9, h: 0.4, fontSize: 11.5, color: C.background1, align: "center" });
    });
    H.text(s, "What was achieved", { x: 0.5, y: 2.75, w: 4.4, h: 0.3, fontSize: 15, bold: true, color: C.accent2, fontFace: "Cambria" });
    H.bullets(s, ["Schema enforced by constraints and triggers", "Transaction-safe payroll with audit trail", "Roles, payslips, transfers, reports"], 0.5, 3.1, 4.4, 1.2, { fontSize: 13, color: C.background1, paraSpaceAfter: 5 });
    H.dark(s, 0.5, 4.4, 9.0, 0.6, { fill: { color: C.accent3 } });
    H.text(s, "Lesson learned: let the database enforce the rules, not only the application.", { x: 0.7, y: 4.43, w: 8.6, h: 0.54, fontSize: 14, italic: true, color: C.background1, valign: "middle" });
    H.text(s, "Future work", { x: 5.1, y: 2.75, w: 4.4, h: 0.3, fontSize: 15, bold: true, color: C.accent2, fontFace: "Cambria" });
    H.bullets(s, ["Official tax slabs and statutory rules", "PDF / e-mail payslips, bank file export", "Audit with user name; HTTPS deployment"], 5.1, 3.1, 4.4, 1.6, { fontSize: 13, color: C.background1, paraSpaceAfter: 5 });
  }

  // (conclusion closing line added below)
  // ------------------------------------------------------------ 20 viva concepts
  {
    const s = H.slide("CONTENT", "Viva", "Viva Readiness: Key Concepts",
      "These are the DBMS concepts in this project that I can explain and show in the code. Normalisation: the schema is in third normal form, with payroll detail as a deliberate snapshot. Keys: every table has a primary key, and sixteen foreign keys link them. Constraints: UNIQUE on employee code and email, CHECK on amounts and status values. Referential actions: RESTRICT protects paid history, CASCADE removes employee inputs. Transactions: payroll processing is atomic with commit and rollback. Joins and subqueries are in queries.sql. Indexes speed up lookups by period and employee. Derived data: loss of pay days are computed, not stored, to avoid redundancy.");
    await H.titleIcon(s, "FaGraduationCap");
    const K = [["Normalisation", "3NF; payroll_detail is a deliberate snapshot"], ["Keys", facts.constraints.primary_keys + " primary keys, " + facts.constraints.foreign_keys + " foreign keys"], ["Constraints", "UNIQUE, CHECK, NOT NULL, DEFAULT"],
      ["Referential actions", "RESTRICT for history, CASCADE for inputs"], ["Transactions", "atomic payroll run: commit or rollback"], ["Joins", "INNER, LEFT, multi-table payslip join"],
      ["Subqueries", "scalar, IN, EXISTS, correlated, derived"], ["Aggregates", "SUM, COUNT, AVG with GROUP BY, HAVING"], ["Triggers, views, indexes", "6 triggers, 3 views, 8 indexes"]];
    K.forEach((k, i) => {
      const col = i % 3, row = Math.floor(i / 3);
      const x = 0.5 + col * 3.05, y = 1.25 + row * 1.25;
      H.card(s, x, y, 2.9, 1.1);
      s.addShape(pres.ShapeType.rect, { x, y: y + 0.12, w: 0.07, h: 0.86, fill: { color: C.accent2 }, line: { color: C.accent2, width: 0 } });
      H.text(s, k[0], { x: x + 0.2, y: y + 0.1, w: 2.6, h: 0.3, fontSize: 13.5, bold: true, color: C.text2 });
      H.text(s, k[1], { x: x + 0.2, y: y + 0.45, w: 2.6, h: 0.6, fontSize: 11.5, color: C.text1 });
    });
  }

  // ------------------------------------------------------------ 21 viva Q&A
  {
    const s = H.slide("CONTENT", "Viva", "Viva Readiness: Likely Questions",
      "Here are questions I expect, with short answers. Why is payroll detail stored if it can be calculated? Because a payslip must not change if rates or salaries are edited later, so it is a deliberate snapshot. Why RESTRICT on payroll history? So paid records cannot be deleted by accident. How do you avoid a half-finished payroll? The whole run is one transaction. Where are the deduction rates? In payroll_config, and they are illustrative. Is the bank transfer real? No, it is a simulated record. Does it use MySQL? The scripts support MySQL 8 and the app runs on SQLite by default; I tested both, SQLite with " + sqliteTests + " tests and a real MySQL 8.0.46 server with " + mysqlTests + ". What would you add next? Official tax rules, and recording the acting user in the audit trail.");
    await H.titleIcon(s, "FaQuestionCircle");
    const Q = [["Why store payroll_detail if it can be calculated?", "A payslip must not change when salaries or rates are edited later: it is a deliberate snapshot."],
      ["Why triggers if the app already locks periods?", "The database stays protected even if someone bypasses the app: paid payroll rows cannot be changed."],
      ["How do you avoid a half-finished payroll?", "The whole run is one transaction; any error rolls back."],
      ["Are the rates official? Is the transfer real?", "No. Rates are illustrative and editable; transfers are simulated records."],
      ["MySQL or SQLite?", "Both: " + sqliteTests + " tests on SQLite and " + mysqlTests + " on a real MySQL 8.0.46. The app defaults to SQLite."]];
    Q.forEach((q, i) => {
      const y = 1.2 + i * 0.78;
      H.card(s, 0.5, y, 9.0, 0.68);
      s.addShape(pres.ShapeType.rect, { x: 0.5, y: y + 0.1, w: 0.07, h: 0.48, fill: { color: C.accent2 }, line: { color: C.accent2, width: 0 } });
      H.text(s, q[0], { x: 0.72, y: y + 0.04, w: 3.5, h: 0.6, fontSize: 12, bold: true, color: C.text2, valign: "middle" });
      H.text(s, q[1], { x: 4.3, y: y + 0.04, w: 5.1, h: 0.6, fontSize: 11.5, color: C.text1, valign: "middle" });
    });
  }

  // ------------------------------------------------------------ 22 references
  {
    const s = H.slide("CONTENT", "Conclusion", "References",
      "These are the references I used: the official documentation for Flask, SQLite, MySQL 8, PyMySQL, Bootstrap and Chart.js, and two standard textbooks for the database theory. The deduction rates in this project are illustrative and are not taken from any statutory document, so I have not cited any tax or provident fund rules as a source.");
    await H.titleIcon(s, "FaBookOpen");
    const refs = [
      "Flask documentation, Pallets Projects: flask.palletsprojects.com",
      "SQLite documentation: sqlite.org/docs.html",
      "MySQL 8.0 Reference Manual, Oracle: dev.mysql.com/doc",
      "PyMySQL documentation: pymysql.readthedocs.io",
      "Bootstrap 5 and Bootstrap Icons documentation: getbootstrap.com",
      "Chart.js documentation: chartjs.org",
      "R. Elmasri and S. Navathe, Fundamentals of Database Systems, Pearson",
      "A. Silberschatz, H. Korth and S. Sudarshan, Database System Concepts, McGraw-Hill",
      "Project 36 Review 1 presentation (problem, objectives, ER, initial schema)",
    ];
    H.card(s, 0.5, 1.25, 9.0, 3.2);
    H.text(s, refs.map((t, i) => ({ text: t, options: { bullet: { type: "number" }, breakLine: i < refs.length - 1 } })), { x: 0.75, y: 1.35, w: 8.5, h: 3.0, fontSize: 12.5, color: C.text1, paraSpaceAfter: 4 });
    H.card(s, 0.5, 4.55, 9.0, 0.55);
    H.text(s, "Deduction rates are illustrative and not sourced from statutory documents.", { x: 0.7, y: 4.57, w: 8.6, h: 0.5, fontSize: 12, italic: true, color: C.text1, valign: "middle" });
  }

  // ------------------------------------------------------------ 23 thank you
  {
    const s = H.slide("DARK", "Conclusion", "Thank You",
      "Thank you. The source code, SQL scripts, screenshots, report and test results are in the submission folder. I am happy to demonstrate any part of the application live or to answer questions on the database design, the SQL, or the payroll calculation.");
    await H.titleIcon(s, "FaCheck", true);
    H.text(s, "Thank You", { x: 0.5, y: 1.5, w: 9.0, h: 1.2, fontSize: 54, bold: true, color: C.background1, align: "center", valign: "middle", fontFace: "Cambria" });
    H.text(s, "Questions and live demonstration", { x: 0.5, y: 2.75, w: 9.0, h: 0.5, fontSize: 20, italic: true, color: C.accent2, align: "center" });
    H.dark(s, 2.0, 3.6, 6.0, 1.2, { fill: { color: C.accent3 } });
    H.text(s, [{ text: "G MADHAN   25WU0102344", options: { bold: true, color: C.accent2, fontSize: 18, breakLine: true } }, { text: "AI ML RHINOS", options: { color: C.background1, fontSize: 14 } }],
      { x: 2.0, y: 3.65, w: 6.0, h: 1.1, align: "center", valign: "middle" });
  }

  await save(H, OUT);
  writeNotes(H, path.join(ROOT, "docs", "Review3_Presentation_Script.md"), "Review 3 - Presentation Script (Project 36)");
  console.log("wrote", OUT, H.notes.length, "slides");
})().catch((e) => { console.error(e); process.exit(1); });
