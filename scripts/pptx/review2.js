// Review 2 deck: design, architecture, database implementation, prototype progress, testing
const path = require("path");
const { makePres, THEME, HEX, drawER, schemaCard, save, writeNotes, ROOT } = require("./lib.js");
const facts = require("./facts_review2.json");

(async () => {
  const H = makePres("DBMS REVIEW 2", "Project 36 - DBMS Review 2",
    { shots: path.join(ROOT, "screenshots", "review2_stage"), crops: path.join(ROOT, "presentations", "assets", "crops_review2") });
  const { pres, C } = H;
  const OUT = path.join(ROOT, "presentations", "Project36_DBMS_Review2.pptx");

  // ------------------------------------------------------------ 1 cover
  {
    const s = H.slide("COVER", "Introduction", null,
      "Good morning. I am G Madhan from AI ML Rhinos, and this is DBMS Review 2 for Project 36, the Employee Payroll and Statutory Deduction Management System. In Review 1 I presented the problem, objectives, scope, ER diagram and the initial relational schema. Today I will show how that design became a working database and a running web application, with real screenshots and real test results.");
    s.addShape(pres.ShapeType.ellipse, { x: 7.0, y: -2.0, w: 4.6, h: 4.6, fill: { color: C.accent3 }, line: { color: C.accent3, width: 0 } });
    s.addShape(pres.ShapeType.ellipse, { x: -1.6, y: 3.6, w: 3.6, h: 3.6, fill: { color: C.accent3 }, line: { color: C.accent3, width: 0 } });
    H.pill(s, "PROJECT 36   |   DBMS REVIEW 2", 3.0, 0.45, 4.0, { fill: { color: C.accent1 }, color: C.background1, h: 0.36 });
    H.text(s, "EMPLOYEE PAYROLL AND STATUTORY DEDUCTION MANAGEMENT SYSTEM", { x: 1.0, y: 1.0, w: 8.0, h: 1.5, fontSize: 32, bold: true, color: C.background1, align: "center", valign: "middle", fontFace: "Cambria" });
    H.text(s, "Design, database implementation and working prototype", { x: 1.0, y: 2.55, w: 8.0, h: 0.4, fontSize: 16, italic: true, color: C.accent4, align: "center" });
    const icons = [["FaFileInvoice", "Payslip"], ["FaRupeeSign", "Salary"], ["FaCalculator", "Calculations"], ["FaCalendarAlt", "Attendance"], ["FaMinusCircle", "Deductions"], ["FaDatabase", "Database"], ["FaUniversity", "Bank Transfer"]];
    for (let i = 0; i < icons.length; i++) {
      const x = 0.95 + i * 1.18;
      await H.circleIcon(s, icons[i][0], x, 3.15, 0.6, C.background1, "#1E2761");
      H.text(s, icons[i][1], { x: x - 0.25, y: 3.8, w: 1.1, h: 0.25, fontSize: 11, color: C.accent4, align: "center" });
    }
    H.dark(s, 1.0, 4.3, 8.0, 0.85, { fill: { color: C.accent3 } });
    H.text(s, [{ text: "PRESENTED BY   ", options: { color: C.accent2, bold: true, fontSize: 11 } },
      { text: "G MADHAN   25WU0102344", options: { color: C.accent2, bold: true, fontSize: 18 } }], { x: 1.3, y: 4.42, w: 5.5, h: 0.6, valign: "middle" });
    H.text(s, [{ text: "Department", options: { color: C.accent2, bold: true, fontSize: 11, breakLine: true } },
      { text: "AI ML RHINOS", options: { color: C.background1, fontSize: 14 } }], { x: 7.2, y: 4.42, w: 1.7, h: 0.6, valign: "middle" });
  }

  // ------------------------------------------------------------ 2 review 1 -> review 2
  {
    const s = H.slide("CONTENT", "Introduction", "From Review 1 to Review 2",
      "Review 1 was about analysis and design: the problem, objectives, users, twelve functional requirements, a conceptual ER diagram and a skeleton schema with only primary and foreign keys. Review 2 is about implementation. I kept the same project and the same twelve entities, and extended them where implementation showed a gap: I added a loan repayment table so repayments can really be tracked, and a configuration table so the illustrative deduction rates are editable instead of hard-coded. Review 3 will cover the final demo and results.");
    await H.titleIcon(s, "FaProjectDiagram");
    // milestone strip
    const ms = [["Review 1", "Analysis & design", "Completed", C.accent5], ["Review 2", "Implementation & prototype", "Today", C.accent2], ["Review 3", "Final demo & results", "Next", C.accent4]];
    ms.forEach((m, i) => {
      const x = 0.5 + i * 3.1;
      H.card(s, x, 1.3, 2.8, 0.85);
      s.addShape(pres.ShapeType.ellipse, { x: x + 0.15, y: 1.5, w: 0.45, h: 0.45, fill: { color: m[3] }, line: { color: m[3], width: 0 } });
      H.text(s, String(i + 1), { x: x + 0.15, y: 1.5, w: 0.45, h: 0.45, fontSize: 16, bold: true, color: C.background1, align: "center", valign: "middle" });
      H.text(s, m[0], { x: x + 0.72, y: 1.38, w: 1.9, h: 0.3, fontSize: 15, bold: true, color: C.text2 });
      H.text(s, m[1] + "  ·  " + m[2], { x: x + 0.72, y: 1.7, w: 2.0, h: 0.38, fontSize: 11, color: C.text1 });
      if (i < 2) H.arrow(s, x + 2.82, 1.72, x + 3.08, 1.72, { color: C.accent4, width: 2 });
    });
    // two columns
    H.card(s, 0.5, 2.4, 4.4, 2.7);
    H.text(s, "Carried over from Review 1", { x: 0.7, y: 2.5, w: 4.0, h: 0.3, fontSize: 15, bold: true, color: C.text2 });
    H.bullets(s, [["Same project: ", "Project 36, same title and scope"], ["12 entities ", "Employee, Department, Designation, Salary Structure, Attendance, Earnings, Deductions, Loan, Payroll Period, Payroll Detail, Payslip, Bank Transfer"], ["All 12 requirements ", "kept as the build checklist"]], 0.7, 2.85, 4.0, 2.2, { fontSize: 13 });
    H.dark(s, 5.1, 2.4, 4.4, 2.7);
    H.text(s, "Added in Review 2", { x: 5.3, y: 2.5, w: 4.0, h: 0.3, fontSize: 15, bold: true, color: C.accent2 });
    H.bullets(s, [["loan_repayment ", "table so EMIs and manual repayments are recorded"], ["payroll_config ", "table for editable illustrative rates"], ["Period links: ", "attendance, earnings and deductions reference a payroll period"], ["Working app: ", "Flask + SQL, 40 automated tests"]],
      5.3, 2.85, 4.0, 2.2, { fontSize: 13, color: C.background1, leadColor: C.accent2 });
  }

  // ------------------------------------------------------------ 3 architecture
  {
    const s = H.slide("CONTENT", "Architecture", "System Architecture",
      "The application has five simple layers. The browser shows Bootstrap pages and a Chart.js dashboard. Flask routes receive requests; one generic set of views handles add, edit, delete and list for most tables, driven by a configuration file. The business logic lives in two small modules: payroll.py, which calculates and processes payroll, and reports.py, which holds the seven report queries as plain SQL. The data access layer db.py hides the differences between SQLite and MySQL, so all SQL is written once. By default the database is SQLite so the project runs with no setup; MySQL is supported through environment variables.");
    await H.titleIcon(s, "FaServer");
    const cols = [
      ["Browser", "FaLaptopCode", ["HTML5 + CSS3", "Bootstrap 5 layout", "JavaScript: search, confirm", "Chart.js dashboard"]],
      ["Flask routes", "FaCogs", ["Dashboard, periods", "Generic CRUD views", "Payslip, transfers", "Jinja2 templates"]],
      ["Business logic", "FaCalculator", ["payroll.py: calculate, process, bank transfers", "reports.py: 7 SQL reports"]],
      ["Data access", "FaLink", ["db.py", "'?' to '%s' for MySQL", "Decimal handling", "Commit / rollback"]],
      ["Database", "FaDatabase", ["SQLite (default)", "MySQL 8 (optional)", "14 tables", "PK, FK, CHECK, UNIQUE"]],
    ];
    for (let i = 0; i < cols.length; i++) {
      const x = 0.4 + i * 1.88;
      H.card(s, x, 1.35, 1.62, 2.75, i === 4 ? { fill: { color: C.accent3 } } : {});
      await H.circleIcon(s, cols[i][1], x + 0.51, 1.5, 0.6, i === 4 ? C.accent2 : C.accent3);
      H.text(s, cols[i][0], { x: x + 0.05, y: 2.2, w: 1.52, h: 0.3, fontSize: 13, bold: true, color: i === 4 ? C.background1 : C.text2, align: "center", fontFace: "Cambria" });
      H.text(s, cols[i][2].map((t, k) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: k < cols[i][2].length - 1, color: i === 4 ? C.background1 : C.text1 } })),
        { x: x + 0.1, y: 2.55, w: 1.46, h: 1.5, fontSize: 11, paraSpaceAfter: 3 });
      if (i < 4) {
        H.arrow(s, x + 1.64, 2.7, x + 1.86, 2.7, { color: C.accent2, width: 2 });
      }
    }
    H.card(s, 0.4, 4.5, 9.2, 0.6);
    H.text(s, [{ text: "Supporting scripts:  ", options: { bold: true, color: C.text2 } },
      { text: "init_db.py (schema + seed + demo payroll)   ·   generate_seed.py (synthetic data)   ·   capture_screenshots.py   ·   tests/test_app.py", options: { color: C.text1 } }],
      { x: 0.6, y: 4.5, w: 8.8, h: 0.6, fontSize: 12, valign: "middle" });
  }

  // ------------------------------------------------------------ 4 tech stack
  {
    const s = H.slide("CONTENT", "Architecture", "Technology Stack",
      "These are the tools I used. Python with Flask gives the web layer, and Jinja2 renders the pages. Bootstrap 5 and Bootstrap Icons are stored inside the project, so the app works offline. Chart.js draws the dashboard charts. SQLite is the default database so the prototype runs anywhere; the same SQL and an equivalent MySQL 8 schema are included. I want to be clear that I have written and syntax-checked the MySQL scripts, but in my development environment there was no MySQL server, so the live MySQL run is still on my to-do list.");
    await H.titleIcon(s, "FaLayerGroup");
    const cards = [
      ["FaPython", "Python 3 + Flask", "Routes, validation, payroll engine"],
      ["FaHtml5", "HTML, Jinja2, CSS", "Server-rendered pages, custom navy-gold theme"],
      ["FaBootstrap", "Bootstrap 5 + Icons", "Responsive layout, bundled locally"],
      ["FaJs", "JavaScript + Chart.js", "Live table search, confirmations, dashboard charts"],
      ["FaDatabase", "SQLite / MySQL 8", "SQLite default; MySQL scripts provided, not yet run live"],
      ["FaBug", "unittest + Playwright", "40 automated tests; real screenshots from headless Chromium"],
    ];
    for (let i = 0; i < 6; i++) {
      const x = 0.5 + (i % 3) * 3.07, y = 1.3 + Math.floor(i / 3) * 1.95;
      H.card(s, x, y, 2.85, 1.75);
      await H.circleIcon(s, cards[i][0], x + 0.2, y + 0.2, 0.6, C.accent3);
      H.text(s, cards[i][1], { x: x + 0.95, y: y + 0.2, w: 1.8, h: 0.6, fontSize: 14, bold: true, color: C.text2, valign: "middle" });
      H.text(s, cards[i][2], { x: x + 0.2, y: y + 0.95, w: 2.5, h: 0.7, fontSize: 12, color: C.text1 });
    }
  }

  // ------------------------------------------------------------ 5 design principles
  {
    const c = facts.constraints;
    const s = H.slide("CONTENT", "Database", "Database Design Principles",
      "The schema has " + c.tables + " tables, " + c.primary_keys + " primary keys, " + c.foreign_keys + " foreign keys, " + c.unique + " unique constraints, " + c.check + " check constraints and " + c.indexes + " indexes. For normalisation: every table has a single-column primary key and atomic values, so it is in first normal form. Non-key columns depend on the whole key. For example, the number of loss-of-pay days is not stored in attendance, because it can be derived from working days, days present and paid leave, which avoids update anomalies. Department and designation names live only in their own tables. The one deliberate exception is payroll_detail, which stores the computed results as a snapshot so that old payslips never change when rates or salaries change later.");
    await H.titleIcon(s, "FaShieldAlt");
    const st = [[c.tables, "tables"], [c.primary_keys, "primary keys"], [c.foreign_keys, "foreign keys"], [c.unique, "UNIQUE"], [c.check, "CHECK"], [c.indexes, "indexes"]];
    st.forEach((t, i) => H.stat(s, String(t[0]), t[1], 0.5 + i * 1.53, 1.25, 1.4, 0.95, { size: 26 }));
    const cols = [
      ["Normalisation (3NF)", ["Atomic columns, one PK per table", "LOP days derived, not stored", "Names stored once, referenced by ID", "payroll_detail = intentional snapshot"]],
      ["Keys & relationships", ["Every relation uses a foreign key", "salary_structure.employee_id UNIQUE gives 1:1", "payslip and bank_transfer 1:1 with payroll_detail", "UNIQUE(employee, period) stops duplicates"]],
      ["Integrity rules", ["CHECK: amounts > 0, grade 1-10, present + leave <= working days", "RESTRICT: no delete of paid history", "CASCADE: employee inputs removed with employee", "Processed periods are locked"]],
    ];
    cols.forEach((col, i) => {
      const x = 0.5 + i * 3.07;
      H.card(s, x, 2.4, 2.85, 2.7);
      H.text(s, col[0], { x: x + 0.15, y: 2.5, w: 2.55, h: 0.3, fontSize: 14, bold: true, color: C.text2, fontFace: "Cambria" });
      H.text(s, col[1].map((t, k) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: k < col[1].length - 1 } })), { x: x + 0.15, y: 2.88, w: 2.55, h: 2.15, fontSize: 12, color: C.text1, paraSpaceAfter: 4 });
    });
  }

  // ------------------------------------------------------------ 6 ER diagram
  {
    const s = H.slide("CONTENT", "Database", "Implemented ER Diagram",
      "This is the Review 1 conceptual diagram turned into the implemented one. Employee is still the centre: one department and one designation per employee, a one-to-one salary structure, and many attendance, earnings, deductions and loan rows. Payroll detail links an employee to a payroll period; each payroll detail has exactly one payslip and one bank transfer. The two additions are loan repayment, which hangs off both loan and payroll detail, and the payroll config table at top left, which holds the editable rates and has no foreign keys. Attendance, earnings and deductions also reference the payroll period, which I did not draw to keep the diagram readable.");
    await H.titleIcon(s, "FaProjectDiagram");
    drawER(H, s);
    H.text(s, "Attendance, Earnings and Deductions also reference Payroll Period (FK).", { x: 6.7, y: 4.92, w: 3.0, h: 0.34, fontSize: 10, italic: true, color: C.accent1 });
  }

  // ------------------------------------------------------------ 7-9 relational schema
  {
    const s = H.slide("CONTENT", "Database", "Relational Schema: Master Data",
      "Here are the master tables. Department and designation are small lookup tables with unique names. Employee holds personal and bank details and two foreign keys. All bank data is synthetic. Salary structure is one row per employee, enforced by a unique foreign key. Payroll period has a unique name and a unique month and year, and a status that moves from open to processed to paid. Payroll config stores the eight illustrative rates and limits.");
    await H.titleIcon(s, "FaTable");
    const g = [["department", 0.5, 1.2, 2.9, 1.3], ["designation", 0.5, 2.65, 2.9, 1.3], ["payroll_config", 0.5, 4.1, 2.9, 1.0],
      ["salary_structure", 3.55, 1.2, 2.9, 1.8], ["payroll_period", 3.55, 3.15, 2.9, 1.95], ["employee", 6.6, 1.2, 2.9, 2.35]];
    H.dark(s, 6.6, 3.7, 2.9, 1.4);
    H.text(s, [{ text: "Why separate tables?", options: { bold: true, color: C.accent2, breakLine: true, fontSize: 13 } },
      { text: "Names are stored once and referenced by ID, so renaming a department never touches employee rows (3NF).", options: { color: C.background1, fontSize: 12 } }],
      { x: 6.75, y: 3.78, w: 2.6, h: 1.25, valign: "top" });
    g.forEach((a) => schemaCard(H, s, a[0], a[1], a[2], a[3], a[4]));
  }
  {
    const s = H.slide("CONTENT", "Database", "Relational Schema: Monthly Inputs",
      "These four tables are the monthly inputs the payroll officer enters. Attendance stores working days, days present and paid leave; a check constraint makes sure present plus leave never exceeds working days. Earnings holds extra pay like bonus and overtime. Deductions holds both manual deductions typed by the officer and automatic rows, which the payroll engine writes for provident fund, ESI, professional tax, income tax and loan EMI; the source column tells them apart. Loan keeps the amount, EMI and the outstanding balance. Employee inputs cascade on delete, but they always restrict deletion of a payroll period.");
    await H.titleIcon(s, "FaClipboardList");
    const g = [["attendance_summary", 0.5, 1.2, 4.4, 1.85], ["earnings", 5.1, 1.2, 4.4, 1.85], ["deductions", 0.5, 3.2, 4.4, 1.85], ["loan", 5.1, 3.2, 4.4, 1.85]];
    g.forEach((a) => schemaCard(H, s, a[0], a[1], a[2], a[3], a[4]));
  }
  {
    const s = H.slide("CONTENT", "Database", "Relational Schema: Payroll Output",
      "These tables are written by payroll processing. Payroll detail is the heart of the output: for each employee and period it stores the earnings components, loss of pay, gross, the three deduction groups, total deductions and net salary. I store these values deliberately so a payslip from August stays exactly as it was even if I change a rate in September. Payslip and bank transfer each have a unique foreign key to payroll detail, which makes both one-to-one. Loan repayment records each EMI, linked to the payroll row that deducted it, or to nothing when it is a manual repayment.");
    await H.titleIcon(s, "FaFileInvoiceDollar");
    schemaCard(H, s, "payroll_detail", 0.5, 1.2, 3.0, 2.95);
    schemaCard(H, s, "loan_repayment", 3.65, 1.2, 2.9, 1.6);
    schemaCard(H, s, "payslip", 3.65, 2.95, 2.9, 1.2);
    schemaCard(H, s, "bank_transfer", 6.7, 1.2, 2.8, 2.0);
    H.dark(s, 6.7, 3.3, 2.8, 0.85);
    H.text(s, "Snapshot design: results are stored, so history never changes.", { x: 6.85, y: 3.35, w: 2.5, h: 0.75, fontSize: 12, color: C.background1, valign: "middle" });
    H.card(s, 0.5, 4.3, 9.0, 0.75);
    H.text(s, [{ text: "Referential rules:  ", options: { bold: true, color: C.text2 } },
      { text: "payroll_detail.employee_id and payroll_period_id use ON DELETE RESTRICT; payslip and bank_transfer follow their payroll_detail row (CASCADE); loan_repayment.payroll_id uses RESTRICT.", options: { color: C.text1 } }],
      { x: 0.7, y: 4.3, w: 8.6, h: 0.75, fontSize: 12, valign: "middle" });
  }

  // ------------------------------------------------------------ 10 DDL
  {
    const s = H.slide("CONTENT", "Database", "Table Implementation (DDL)",
      "This is a real excerpt from schema.sql for the payroll detail table; the dots stand for columns I left out to fit the slide. You can see all four kinds of constraint: the primary key, a unique constraint on employee plus period so nobody can be paid twice for the same month, a check constraint that net salary can never be negative, and two foreign keys with RESTRICT so paid history can never be orphaned. The same file also exists in a SQLite version, which a small script generates from the MySQL one, so the two never drift apart.");
    await H.titleIcon(s, "FaCode");
    H.sql(s, `CREATE TABLE payroll_detail (
  payroll_id        INT AUTO_INCREMENT PRIMARY KEY,
  employee_id       INT NOT NULL,
  payroll_period_id INT NOT NULL,
  ...
  gross_salary      DECIMAL(12,2) NOT NULL,
  total_deductions  DECIMAL(12,2) NOT NULL,
  net_salary        DECIMAL(12,2) NOT NULL,
  processed_on      DATE NOT NULL,
  CONSTRAINT uq_payroll_emp_period
    UNIQUE (employee_id, payroll_period_id),
  CONSTRAINT chk_payroll_net
    CHECK (net_salary >= 0 AND gross_salary >= 0
           AND total_deductions >= 0),
  CONSTRAINT fk_pay_emp FOREIGN KEY (employee_id)
    REFERENCES employee(employee_id) ON DELETE RESTRICT,
  CONSTRAINT fk_pay_period FOREIGN KEY (payroll_period_id)
    REFERENCES payroll_period(payroll_period_id)
    ON DELETE RESTRICT
);`, 0.5, 1.25, 5.7, 3.85, 10.5);
    const ann = [["PRIMARY KEY", "Auto-numbered payroll_id identifies each payslip row"], ["UNIQUE (employee, period)", "No employee is paid twice for one month"], ["CHECK", "Net, gross and deductions can never be negative"], ["FOREIGN KEY + RESTRICT", "Paid history cannot be orphaned or deleted"]];
    ann.forEach((a, i) => {
      const y = 1.25 + i * 0.98;
      H.card(s, 6.4, y, 3.1, 0.85);
      H.text(s, a[0], { x: 6.55, y: y + 0.06, w: 2.8, h: 0.28, fontSize: 12, bold: true, color: C.accent1 });
      H.text(s, a[1], { x: 6.55, y: y + 0.35, w: 2.85, h: 0.45, fontSize: 11, color: C.text1 });
    });
  }

  // ------------------------------------------------------------ 11 sample data
  {
    const t = facts.tables_init;
    const s = H.slide("CONTENT", "Database", "Tables and Synthetic Data",
      "After running init_db.py the database holds thirty synthetic employees across six departments, three payroll periods, ninety attendance records, loans and so on. All data is fictitious: names are random combinations, e-mails use the reserved example.com domain, and bank accounts are made up. Importantly, the payroll rows, payslips, bank transfers, automatic deductions and loan repayments for August and September were not typed in; they were produced by running the application's own payroll engine, so the demo data exercises the real logic. October is left open so I can process it live.");
    await H.titleIcon(s, "FaTable");
    const names = Object.keys(t);
    const half = Math.ceil(names.length / 2);
    const mk = (arr) => arr.map((n) => [n, String(t[n])]);
    H.table(s, ["Table", "Rows"], mk(names.slice(0, half)), 0.5, 1.3, 4.3, [3.1, 1.2], { fontSize: 12, rowH: 0.31 });
    H.table(s, ["Table", "Rows"], mk(names.slice(half)), 5.2, 1.3, 4.3, [3.1, 1.2], { fontSize: 12, rowH: 0.31 });
    H.dark(s, 0.5, 3.9, 9.0, 1.2);
    H.text(s, [{ text: "Demo state after init_db.py", options: { bold: true, color: C.accent2, breakLine: true, fontSize: 14 } },
      { text: "30 employees (1 inactive) · August and September 2026 processed and PAID · October 2026 OPEN for live processing · 6 loans · all names, e-mails and bank details fictitious", options: { color: C.background1, fontSize: 13 } }],
      { x: 0.7, y: 3.98, w: 8.6, h: 1.05, valign: "middle" });
  }

  // ------------------------------------------------------------ 12 SQL operations
  {
    const s = H.slide("CONTENT", "Database", "SQL Operations",
      "These are simplified excerpts from database/queries.sql, and the test suite executes the whole file against a copy of the database, so every statement is known to run. Top left is CRUD: insert, update, delete. Top right is a three-table join for the employee directory. Bottom left is group by with a having clause: department payroll cost, only for departments with more than two people. Bottom right is a correlated subquery that compares each employee's gross salary to the average of their own department. The file also contains left joins, not-exists, scalar and derived-table subqueries, a view, and consistency checks.");
    await H.titleIcon(s, "FaDatabase");
    const P = [
      ["CRUD", `INSERT INTO department
  (department_name, location)
VALUES ('Research Lab', 'Hyderabad');
UPDATE employee SET phone = '9000011111'
WHERE emp_code = 'EMP900';
DELETE FROM employee
WHERE emp_code = 'EMP900';`],
      ["JOIN (3 tables)", `SELECT e.emp_code, e.first_name,
       d.department_name, g.title
FROM employee e
JOIN department d
  ON d.department_id = e.department_id
JOIN designation g
  ON g.designation_id = e.designation_id
ORDER BY e.emp_code;`],
      ["GROUP BY + HAVING", `SELECT e.department_id, COUNT(*) AS staff,
       SUM(p.gross_salary) AS total_gross
FROM payroll_detail p
JOIN employee e ON e.employee_id = p.employee_id
WHERE p.payroll_period_id = 1
GROUP BY e.department_id
HAVING COUNT(*) > 2;`],
      ["Correlated subquery", `SELECT e.emp_code, p.gross_salary,
 (SELECT AVG(a.gross_salary)
  FROM payroll_detail a
  JOIN employee b ON b.employee_id = a.employee_id
  WHERE b.department_id = e.department_id
    AND a.payroll_period_id = p.payroll_period_id)
   AS dept_avg
FROM payroll_detail p
JOIN employee e ON e.employee_id = p.employee_id;`],
    ];
    P.forEach((p, i) => {
      const x = 0.5 + (i % 2) * 4.6, y = 1.2 + Math.floor(i / 2) * 2.05;
      H.pill(s, p[0], x, y, 2.2, { fill: { color: C.accent2 }, color: C.background1 });
      H.sql(s, p[1], x, y + 0.33, 4.4, 1.62, 9.5);
    });
  }

  // ------------------------------------------------------------ 13 calc logic
  {
    const s = H.slide("CONTENT", "Application", "Payroll Calculation Logic",
      "Calculation follows a simple chain. Fixed gross is basic plus HRA plus DA plus special allowance. Each day of unpaid leave cuts one working day's share of fixed gross. Bonus or overtime for the month is added to give gross salary. Then five deductions are applied: provident fund, ESI, professional tax, an illustrative income tax, and loan EMI, plus any manual deductions. Net salary is gross minus total deductions. I must stress that every rate shown here is illustrative for a university project; they are not official statutory rates, and they can be edited on the settings page and are stored in the payroll_config table.");
    await H.titleIcon(s, "FaCalculator");
    const f = [["Fixed gross", "basic + HRA + DA + special"], ["− Loss of pay", "fixed gross ÷ working days × LOP days"], ["+ Extra earnings", "bonus, overtime, incentive"], ["= Gross salary", "before deductions"]];
    const f2 = [["PF", "12% of basic, basic capped at ₹15,000"], ["ESI", "0.75% of gross, only if gross ≤ ₹21,000"], ["Prof. tax", "₹200 if gross > ₹15,000"], ["TDS (illustr.)", "5% of gross above ₹50,000"], ["Loan EMI + manual", "from loan and deductions tables"]];
    f.forEach((r, i) => {
      const x = 0.5 + i * 2.35;
      const last = i === 3;
      if (last) H.dark(s, x, 1.3, 2.1, 0.95); else H.card(s, x, 1.3, 2.1, 0.95);
      H.text(s, r[0], { x: x + 0.1, y: 1.36, w: 1.9, h: 0.35, fontSize: 14, bold: true, color: last ? C.accent2 : C.text2, align: "center", valign: "middle" });
      H.text(s, r[1], { x: x + 0.1, y: 1.72, w: 1.9, h: 0.5, fontSize: 10.5, color: last ? C.background1 : C.text1, align: "center" });
      if (i < 3) H.arrow(s, x + 2.12, 1.77, x + 2.33, 1.77, { color: C.accent2, width: 2 });
    });
    H.arrow(s, 8.9, 2.3, 8.9, 2.62, { color: C.accent2, width: 2 });
    H.text(s, "Deductions", { x: 0.5, y: 2.5, w: 3, h: 0.3, fontSize: 14, bold: true, color: C.text2, fontFace: "Cambria" });
    f2.forEach((r, i) => {
      const x = 0.5 + i * 1.84;
      H.card(s, x, 2.85, 1.7, 1.15);
      H.text(s, r[0], { x: x + 0.08, y: 2.9, w: 1.55, h: 0.3, fontSize: 12.5, bold: true, color: C.accent1, align: "center" });
      H.text(s, r[1], { x: x + 0.08, y: 3.22, w: 1.55, h: 0.75, fontSize: 10.5, color: C.text1, align: "center" });
    });
    H.dark(s, 0.5, 4.2, 9.0, 0.85);
    H.text(s, [{ text: "Net salary = Gross − (PF + ESI + PT + TDS + Loan EMI + other deductions)", options: { bold: true, color: C.background1, fontSize: 15, breakLine: true } },
      { text: "All rates are illustrative and editable in payroll_config. They are not official statutory rates.", options: { color: C.accent2, italic: true, fontSize: 12 } }],
      { x: 0.7, y: 4.25, w: 8.6, h: 0.75, valign: "middle", align: "center" });
  }

  // ------------------------------------------------------------ 14 progress
  {
    const s = H.slide("CONTENT", "Application", "Development Progress",
      "This table is the honest status of the Review 1 requirements. Every functional requirement from Review 1 is implemented and covered by at least one automated test or screenshot. Bank transfers are simulated: the system records transfer details and status, but it does not connect to a real bank. One thing is not done yet: Review 1 listed four user roles, HR, payroll officer, employee and management, but there is no login or role-based access in this prototype. That is the first item under future improvements.");
    await H.titleIcon(s, "FaTasks");
    const DONE = { text: "Done", options: { bold: true, color: C.accent5 } };
    const rows = [
      ["1", "Employee add / view / update / delete", DONE, "Employees, profile page"],
      ["2", "Department and designation management", DONE, "Master data pages"],
      ["3", "Salary structures", DONE, "1:1 with employee"],
      ["4", "Monthly attendance summaries", DONE, "Per period, LOP derived"],
      ["5", "Employee earnings", DONE, "Bonus, overtime, ..."],
      ["6", "Statutory and other deductions", DONE, "AUTO + MANUAL rows"],
      ["7", "Loans and repayments", DONE, "EMI + manual repayment"],
      ["8", "Payroll records per period", DONE, "Create, process, lock"],
      ["9", "Gross, deductions, net calculation", DONE, "payroll.py, 5 unit tests"],
      ["10", "Employee payslips", DONE, "Printable payslip"],
      ["11", "Bank transfer details", { text: "Done (simulated)", options: { bold: true, color: C.accent5 } }, "No real bank API"],
      ["12", "Payroll reports", DONE, "7 SQL reports + CSV"],
      ["+", "Login and user roles", { text: "Not started", options: { bold: true, color: C.accent6 } }, "Planned"],
    ];
    H.table(s, ["#", "Review 1 requirement", "Status", "Evidence"], rows, 0.5, 1.2, 9.0, [0.45, 4.1, 1.7, 2.75], { fontSize: 11, rowH: 0.285 });
  }

  // ------------------------------------------------------------ 15-19 screenshots
  {
    const s = H.slide("CONTENT", "Prototype", "Prototype: Dashboard",
      "This is a real screenshot of the running application. The dashboard shows active employees, the gross, deductions and net totals for the latest processed period, open periods, pending bank transfers and outstanding loans. The bar chart compares gross, deductions and net for each processed month, and the doughnut shows headcount per department. All of these numbers come from SQL aggregate queries on the live database. Customer Support has no employees in the demo data, which is why it shows as an empty department.");
    await H.titleIcon(s, "FaChartPie");
    H.shot(s, "01_dashboard_before_october.png", 0.5, 1.3, 5.8);
    H.bullets(s, [["Live SQL: ", "every tile and chart is an aggregate query"], ["Latest period: ", "totals update after each payroll run"], ["Charts: ", "gross vs deductions vs net; headcount by department"], ["Quick action: ", "Process payroll button"]], 6.55, 1.3, 3.0, 3.4, { fontSize: 13 });
  }
  {
    const s = H.slide("CONTENT", "Prototype", "Prototype: Employee Management",
      "Employee management supports add, view, update and delete. On the left is the employee list with live search. On the right is the add form: required fields are marked, dropdowns are loaded from the department and designation tables, and the database constraints are checked on save. A duplicate employee code, for example, is rejected by the unique constraint and shown as a friendly message. An employee who already has payroll cannot be deleted; the app tells the user to set the status to inactive instead.");
    await H.titleIcon(s, "FaUsers");
    H.shotC(s, "02_employees_list.png", 0.5, 1.3, 4.4);
    H.shotC(s, "04_employee_add_form.png", 5.1, 1.3, 4.4);
    H.text(s, "Employee list with search, view, edit and delete", { x: 0.5, y: 3.85, w: 4.4, h: 0.3, fontSize: 12, bold: true, color: C.text2, align: "center" });
    H.text(s, "Add form with department and designation dropdowns", { x: 5.1, y: 3.85, w: 4.4, h: 0.3, fontSize: 12, bold: true, color: C.text2, align: "center" });
    H.card(s, 0.5, 4.3, 9.0, 0.75);
    H.text(s, [{ text: "Validation: ", options: { bold: true, color: C.text2 } }, { text: "required fields checked first, then database constraints (UNIQUE, FK, CHECK) with a readable error message; employees with payroll history cannot be deleted.", options: { color: C.text1 } }],
      { x: 0.7, y: 4.3, w: 8.6, h: 0.75, fontSize: 12, valign: "middle" });
  }
  {
    const s = H.slide("CONTENT", "Prototype", "Prototype: Salary and Attendance",
      "On the left is the salary structure page: each employee has basic, HRA, DA and special allowance, and fixed gross is calculated by a SQL expression. On the right is attendance for October 2026, with the loss-of-pay column derived in the query from working days, present days and paid leave. Earnings and deductions pages work the same way, and rows in a period that has been processed are locked, so history cannot be edited by accident.");
    await H.titleIcon(s, "FaCalendarCheck");
    H.shotC(s, "10_salary_structures.png", 0.5, 1.3, 4.4);
    H.shotC(s, "11_attendance_october.png", 5.1, 1.3, 4.4);
    H.text(s, "Salary structures with derived fixed gross", { x: 0.5, y: 3.85, w: 4.4, h: 0.3, fontSize: 12, bold: true, color: C.text2, align: "center" });
    H.text(s, "Attendance for a period; LOP days derived", { x: 5.1, y: 3.85, w: 4.4, h: 0.3, fontSize: 12, bold: true, color: C.text2, align: "center" });
    H.card(s, 0.5, 4.3, 9.0, 0.75);
    H.text(s, [{ text: "Also built: ", options: { bold: true, color: C.text2 } }, { text: "Earnings and Deductions pages (AUTO rows are read-only) and period locking once payroll is processed.", options: { color: C.text1 } }],
      { x: 0.7, y: 4.3, w: 8.6, h: 0.75, fontSize: 12, valign: "middle" });
  }
  {
    const s = H.slide("CONTENT", "Prototype", "Prototype: Loans and Repayments",
      "The loans page lists each loan with its EMI and outstanding balance. Opening a loan shows its repayment history. EMIs are deducted automatically when payroll is processed: the engine writes a repayment row, reduces the outstanding balance, and closes the loan when the balance reaches zero. A payroll officer can also record a manual repayment. In the screenshot on the right you can see loan one with two payroll EMIs, for August and September, each reducing the balance.");
    await H.titleIcon(s, "FaHandHoldingUsd");
    H.shotC(s, "14_loans.png", 0.5, 1.3, 4.4);
    H.shotC(s, "15_loan_repayments.png", 5.1, 1.3, 4.4);
    H.text(s, "Loans: amount, EMI, outstanding balance", { x: 0.5, y: 3.85, w: 4.4, h: 0.3, fontSize: 12, bold: true, color: C.text2, align: "center" });
    H.text(s, "Repayment history linked to payroll runs", { x: 5.1, y: 3.85, w: 4.4, h: 0.3, fontSize: 12, bold: true, color: C.text2, align: "center" });
    H.card(s, 0.5, 4.3, 9.0, 0.75);
    H.text(s, [{ text: "Rule: ", options: { bold: true, color: C.text2 } }, { text: "EMI = min(EMI, outstanding balance); a loan starts deducting from the period that contains its start date; balance never goes below zero (CHECK).", options: { color: C.text1 } }],
      { x: 0.7, y: 4.3, w: 8.6, h: 0.75, fontSize: 12, valign: "middle" });
  }
  {
    const s = H.slide("CONTENT", "Prototype", "Prototype: Payroll Processing",
      "This is the core feature. On the left, October 2026 is open and ready. I click Process payroll and the engine runs for all active employees. On the right is the result: payroll processed for twenty-nine employees with the totals shown, and the period status changes to processed. The twenty-ninth employee count is because one employee in the data is inactive and is skipped. The whole run is one database transaction: if anything fails, nothing is saved. Processing the same period twice is refused.");
    await H.titleIcon(s, "FaPlayCircle");
    H.shotC(s, "18_periods_october_open.png", 0.5, 1.3, 4.4);
    H.arrow(s, 4.92, 2.6, 5.08, 2.6, { color: C.accent2, width: 3 });
    H.shotC(s, "19_payroll_processed.png", 5.1, 1.3, 4.4);
    H.text(s, "Before: October 2026 is OPEN", { x: 0.5, y: 3.85, w: 4.4, h: 0.3, fontSize: 12, bold: true, color: C.text2, align: "center" });
    H.text(s, "After: 29 payslips created, status PROCESSED", { x: 5.1, y: 3.85, w: 4.4, h: 0.3, fontSize: 12, bold: true, color: C.text2, align: "center" });
    H.card(s, 0.5, 4.3, 9.0, 0.75);
    H.text(s, [{ text: "Safety: ", options: { bold: true, color: C.text2 } }, { text: "one transaction (all or nothing), inactive employees skipped, missing salary or attendance reported, a period can only be processed once.", options: { color: C.text1 } }],
      { x: 0.7, y: 4.3, w: 8.6, h: 0.75, fontSize: 12, valign: "middle" });
  }

  // ------------------------------------------------------------ 20 testing
  {
    const ts = facts.test_suites;
    const s = H.slide("CONTENT", "Testing", "Testing",
      "I wrote forty automated tests and all forty pass. Five calculation tests check the payroll formulas against numbers I computed by hand, including a case with loss of pay, a loan and a bonus, and a low-salary case where ESI applies. Nine database tests prove that foreign keys, unique and check constraints really reject bad data. Nine payroll tests check processing end to end: totals are consistent, loans reduce correctly, double processing is refused, and a failed run rolls back completely. Seventeen web tests load all pages and exercise add, edit and delete flows. The full results are saved in tests/test_results.txt. What I have not tested yet: a live MySQL server and browsers other than headless Chromium.");
    await H.titleIcon(s, "FaBug");
    s.addChart(pres.charts.BAR, [{ name: "Tests passed", labels: ["Web / CRUD", "Payroll processing", "Database", "Calculation"], values: [ts.WebTests, ts.PayrollProcessingTests, ts.DatabaseTests, ts.CalcTests] }],
      { x: 0.5, y: 1.25, w: 5.2, h: 3.0, barDir: "bar", chartColors: [HEX.blue], showTitle: true, title: "Automated tests by suite", titleFontSize: 13, titleColor: HEX.navy, titleFontFace: "+mn-lt",
        showValue: true, dataLabelPosition: "outEnd", dataLabelColor: HEX.ink, dataLabelFontSize: 12, dataLabelFontFace: "+mn-lt", showLegend: false,
        catAxisLabelColor: HEX.ink, catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", valAxisLabelColor: HEX.muted, valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt",
        valGridLine: { color: HEX.line, size: 0.5 }, catGridLine: { style: "none" }, valAxisMaxVal: 20, valAxisMinVal: 0, valAxisMajorUnit: 5});
    H.stat(s, facts.tests_run + " / " + facts.tests_run, "tests passed", 6.0, 1.25, 3.5, 1.15, { size: 34 });
    H.card(s, 6.0, 2.55, 3.5, 1.7);
    H.text(s, [{ text: "Verified", options: { bold: true, color: C.text2, breakLine: true, fontSize: 13 } },
      { text: "Hand-computed formulas", options: { bullet: { indent: 14 }, breakLine: true } }, { text: "Constraint rejection", options: { bullet: { indent: 14 }, breakLine: true } },
      { text: "Rollback on failure", options: { bullet: { indent: 14 }, breakLine: true } }, { text: "queries.sql runs fully", options: { bullet: { indent: 14 } } }],
      { x: 6.2, y: 2.65, w: 3.2, h: 1.55, fontSize: 12, color: C.text1, paraSpaceAfter: 2 });
    H.card(s, 0.5, 4.4, 9.0, 0.7);
    H.text(s, [{ text: "Not yet tested: ", options: { bold: true, color: C.accent6 } }, { text: "live MySQL server run · browsers other than headless Chromium · many concurrent users.", options: { color: C.text1 } }],
      { x: 0.7, y: 4.4, w: 8.6, h: 0.7, fontSize: 12, valign: "middle" });
  }

  // ------------------------------------------------------------ 21 challenges
  {
    const s = H.slide("CONTENT", "Testing", "Challenges and Solutions",
      "Four design challenges shaped the implementation. First, MySQL and SQLite differ in small ways, such as auto-increment syntax. I wrote the schema once for MySQL and generate the SQLite file with a script, and I wrote all SQL in a portable subset. Second, rounding: payroll must be exact, so the engine uses decimal arithmetic rounded to paise, and SQLite cannot bind decimals, so the data layer converts them. Third, data consistency: once a month is processed, editing its inputs would make payslips wrong, so processed periods lock their inputs, and processing runs in one transaction. Fourth, Review 1 had no way to record loan repayments, so I added the loan repayment table. Each solution has an automated test.");
    await H.titleIcon(s, "FaLightbulb");
    const rows = [
      ["MySQL and SQLite differ in syntax", "MySQL schema is the master; script generates the SQLite file; SQL kept portable", "Schema loads in SQLite in tests"],
      ["Exact money arithmetic", "Decimal maths rounded to 2 places; DB layer converts Decimal for SQLite", "5 hand-computed calculation tests"],
      ["Edits after payroll would corrupt history", "Period status locks inputs; processing is one all-or-nothing transaction", "Locked-period, double-process and rollback tests"],
      ["Review 1 had no repayment record", "Added loan_repayment table linked to payroll_detail", "EMI and balance tests"],
    ];
    H.table(s, ["Challenge", "Solution", "Verified by"], rows, 0.5, 1.3, 9.0, [2.7, 3.7, 2.6], { fontSize: 12, rowH: 0.78 });
  }

  // ------------------------------------------------------------ 22 future
  {
    const s = H.slide("CONTENT", "Next steps", "Future Improvements",
      "These are the planned improvements. The most important is login and roles, because Review 1 defined four user types and the prototype currently has no authentication. Second, I want to run and test the project against a real MySQL 8 server, since so far only the scripts exist. Third, replace the illustrative rates with proper statutory slabs. Others: PDF payslips with e-mail, an audit log of changes, bank file export, and a tax declaration module.");
    await H.titleIcon(s, "FaRocket");
    const items = [["FaUserShield", "Login and roles", "HR, payroll officer, employee, management from Review 1"], ["FaDatabase", "Live MySQL test", "Run the provided MySQL scripts on a real server"], ["FaBalanceScale", "Official slabs", "Replace illustrative rates with statutory rules"],
      ["FaFilePdf", "PDF payslips", "Download or e-mail each payslip"], ["FaHistory", "Audit log", "Who changed what and when"], ["FaUniversity", "Bank file export", "Generate a bulk-payment file"]];
    for (let i = 0; i < 6; i++) {
      const x = 0.5 + (i % 3) * 3.07, y = 1.3 + Math.floor(i / 3) * 1.95;
      H.card(s, x, y, 2.85, 1.75);
      await H.circleIcon(s, items[i][0], x + 0.2, y + 0.2, 0.6, i === 0 ? C.accent2 : C.accent3);
      H.text(s, items[i][1], { x: x + 0.95, y: y + 0.2, w: 1.8, h: 0.6, fontSize: 14, bold: true, color: C.text2, valign: "middle" });
      H.text(s, items[i][2], { x: x + 0.2, y: y + 0.95, w: 2.5, h: 0.7, fontSize: 12, color: C.text1 });
    }
  }

  // ------------------------------------------------------------ 23 closing
  {
    const s = H.slide("DARK", "Closing", "Summary and Next Review",
      "To summarise: the Review 1 design is now a working system. There is a fourteen-table database with enforced constraints, a Flask application covering every functional requirement, synthetic data, a payroll engine that I verified by hand and by forty automated tests. For Review 3 I will demonstrate the complete payroll workflow live, show the reports and the final results, and discuss limitations. Thank you. I am happy to take questions.");
    await H.titleIcon(s, "FaCheckCircle", true);
    const pts = [["14", "tables with PK, FK, CHECK, UNIQUE"], ["12 / 12", "Review 1 requirements implemented"], ["40 / 40", "automated tests passing"], ["27", "real screenshots captured"]];
    pts.forEach((p, i) => {
      const x = 0.5 + i * 2.32;
      H.dark(s, x, 1.4, 2.1, 1.5, { fill: { color: C.accent3 } });
      H.text(s, p[0], { x, y: 1.5, w: 2.1, h: 0.7, fontSize: 30, bold: true, color: C.accent2, align: "center", valign: "middle", fontFace: "Cambria" });
      H.text(s, p[1], { x: x + 0.1, y: 2.2, w: 1.9, h: 0.65, fontSize: 12, color: C.background1, align: "center" });
    });
    H.text(s, "Review 3 will show", { x: 0.5, y: 3.2, w: 4, h: 0.35, fontSize: 16, bold: true, color: C.accent2, fontFace: "Cambria" });
    H.text(s, ["Complete payroll workflow, live", "Payslip, bank transfers and reports", "Final results, limitations, viva readiness"].map((t, i, a) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: i < a.length - 1 } })),
      { x: 0.5, y: 3.6, w: 5.5, h: 1.2, fontSize: 14, color: C.background1, paraSpaceAfter: 5 });
    H.text(s, "Thank You", { x: 6.2, y: 3.6, w: 3.3, h: 0.9, fontSize: 36, bold: true, color: C.background1, align: "right", valign: "middle", fontFace: "Cambria" });
  }

  await save(H, OUT);
  writeNotes(H, path.join(ROOT, "docs", "Review2_Presentation_Script.md"), "Review 2 - Presentation Script (Project 36)");
  console.log("wrote", OUT, H.notes.length, "slides");
})().catch((e) => { console.error(e); process.exit(1); });
