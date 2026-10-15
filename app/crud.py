"""Configuration for the generic list / add / edit / delete pages.

Each entry describes one table: how to list it (a JOIN query), which form
fields to show, and a few safety rules. One set of views (in __init__.py)
serves all of them, which keeps the code small and easy to explain.
"""


def F(name, label, type="text", required=False, options=None, **kw):
    return dict(name=name, label=label, type=type, required=required, options=options, **kw)


# ---- option providers for <select> fields -------------------------------
def opt_departments(db):
    return [(r["department_id"], r["department_name"]) for r in db.all("SELECT * FROM department ORDER BY department_name")]


def opt_designations(db):
    return [(r["designation_id"], f"{r['title']} (grade {r['grade_level']})") for r in
            db.all("SELECT * FROM designation ORDER BY grade_level")]


def opt_employees(db):
    return [(r["employee_id"], f"{r['emp_code']} - {r['first_name']} {r['last_name']}") for r in
            db.all("SELECT employee_id, emp_code, first_name, last_name FROM employee ORDER BY emp_code")]


def opt_periods(db):
    return [(r["payroll_period_id"], f"{r['period_name']} [{r['status']}]") for r in
            db.all("SELECT * FROM payroll_period ORDER BY period_year DESC, period_month DESC")]


YESNO = [(0, "No"), (1, "Yes")]

EMP_SQL = ("SELECT e.employee_id, e.emp_code, e.first_name, e.last_name, d.department_name, g.title, "
           "e.date_of_joining, e.status FROM employee e "
           "JOIN department d ON d.department_id = e.department_id "
           "JOIN designation g ON g.designation_id = e.designation_id ORDER BY e.emp_code")


def _employee_name(row):
    row["name"] = f"{row['first_name']} {row['last_name']}"
    return row


CRUD = {
    "employees": dict(
        table="employee", pk="employee_id", title="Employees", singular="Employee", icon="people",
        sql=EMP_SQL, row_hook=_employee_name, view="employee_view",
        columns=[("emp_code", "Code", None), ("name", "Name", None), ("department_name", "Department", None),
                 ("title", "Designation", None), ("date_of_joining", "Joined", "date"), ("status", "Status", "badge")],
        fields=[
            F("emp_code", "Employee code", required=True, placeholder="EMP031"),
            F("first_name", "First name", required=True),
            F("last_name", "Last name", required=True),
            F("email", "E-mail", "email", required=True),
            F("phone", "Phone"),
            F("date_of_joining", "Date of joining", "date", required=True),
            F("department_id", "Department", "select", True, options=opt_departments),
            F("designation_id", "Designation", "select", True, options=opt_designations),
            F("bank_name", "Bank name"),
            F("bank_account_no", "Bank account no. (synthetic)"),
            F("ifsc_code", "IFSC code"),
            F("status", "Status", "select", True, options=lambda db: [("ACTIVE", "ACTIVE"), ("INACTIVE", "INACTIVE")]),
        ],
        defaults={"status": "ACTIVE"},
        delete_hint="An employee with payroll history cannot be deleted - set the status to INACTIVE instead.",
    ),
    "departments": dict(
        table="department", pk="department_id", title="Departments", singular="Department", icon="building",
        sql="SELECT d.department_id, d.department_name, d.location, "
            "(SELECT COUNT(*) FROM employee e WHERE e.department_id = d.department_id) AS employees "
            "FROM department d ORDER BY d.department_name",
        columns=[("department_id", "ID", None), ("department_name", "Department", None),
                 ("location", "Location", None), ("employees", "Employees", None)],
        fields=[F("department_name", "Department name", required=True), F("location", "Location")],
        delete_hint="A department that still has employees cannot be deleted.",
    ),
    "designations": dict(
        table="designation", pk="designation_id", title="Designations", singular="Designation", icon="award",
        sql="SELECT g.designation_id, g.title, g.grade_level, "
            "(SELECT COUNT(*) FROM employee e WHERE e.designation_id = g.designation_id) AS employees "
            "FROM designation g ORDER BY g.grade_level",
        columns=[("designation_id", "ID", None), ("title", "Title", None),
                 ("grade_level", "Grade", None), ("employees", "Employees", None)],
        fields=[F("title", "Designation title", required=True),
                F("grade_level", "Grade level (1-10)", "number", True, int=True, min=1, max=10)],
        delete_hint="A designation that is still assigned to employees cannot be deleted.",
    ),
    "salary-structures": dict(
        table="salary_structure", pk="salary_structure_id", title="Salary Structures", singular="Salary Structure",
        icon="cash-coin",
        sql="SELECT s.salary_structure_id, e.emp_code, e.first_name, e.last_name, s.basic_salary, s.hra, s.da, "
            "s.special_allowance, (s.basic_salary + s.hra + s.da + s.special_allowance) AS fixed_gross, s.effective_from "
            "FROM salary_structure s JOIN employee e ON e.employee_id = s.employee_id ORDER BY e.emp_code",
        row_hook=_employee_name,
        columns=[("emp_code", "Code", None), ("name", "Employee", None), ("basic_salary", "Basic", "money"),
                 ("hra", "HRA", "money"), ("da", "DA", "money"), ("special_allowance", "Special", "money"),
                 ("fixed_gross", "Fixed gross", "money"), ("effective_from", "From", "date")],
        fields=[F("employee_id", "Employee", "select", True, options=opt_employees),
                F("basic_salary", "Basic salary", "number", True, step="0.01", min=1),
                F("hra", "House rent allowance (HRA)", "number", True, step="0.01", min=0, default=0),
                F("da", "Dearness allowance (DA)", "number", True, step="0.01", min=0, default=0),
                F("special_allowance", "Special allowance", "number", True, step="0.01", min=0, default=0),
                F("effective_from", "Effective from", "date", True)],
        delete_hint="",
    ),
    "attendance": dict(
        table="attendance_summary", pk="attendance_id", title="Attendance", singular="Attendance Record",
        icon="calendar-check", period_col="payroll_period_id", lock_period=True,
        sql="SELECT a.attendance_id, a.payroll_period_id, p.period_name, e.emp_code, e.first_name, e.last_name, "
            "a.working_days, a.days_present, a.paid_leave_days, "
            "(a.working_days - a.days_present - a.paid_leave_days) AS lop_days "
            "FROM attendance_summary a JOIN employee e ON e.employee_id = a.employee_id "
            "JOIN payroll_period p ON p.payroll_period_id = a.payroll_period_id ORDER BY e.emp_code",
        row_hook=_employee_name,
        columns=[("period_name", "Period", None), ("emp_code", "Code", None), ("name", "Employee", None),
                 ("working_days", "Working days", None), ("days_present", "Present", None),
                 ("paid_leave_days", "Paid leave", None), ("lop_days", "LOP days", "lop")],
        fields=[F("employee_id", "Employee", "select", True, options=opt_employees),
                F("payroll_period_id", "Payroll period", "select", True, options=opt_periods),
                F("working_days", "Working days in month", "number", True, int=True, min=1, max=31),
                F("days_present", "Days present", "number", True, step="0.5", min=0),
                F("paid_leave_days", "Paid leave days", "number", True, step="0.5", min=0, default=0)],
        delete_hint="Attendance of a processed period is locked.",
    ),
    "earnings": dict(
        table="earnings", pk="earning_id", title="Earnings", singular="Earning",
        icon="graph-up-arrow", period_col="payroll_period_id", lock_period=True,
        sql="SELECT x.earning_id, x.payroll_period_id, p.period_name, e.emp_code, e.first_name, e.last_name, "
            "x.earning_type, x.amount, x.remarks FROM earnings x "
            "JOIN employee e ON e.employee_id = x.employee_id "
            "JOIN payroll_period p ON p.payroll_period_id = x.payroll_period_id ORDER BY x.earning_id DESC",
        row_hook=_employee_name,
        columns=[("period_name", "Period", None), ("emp_code", "Code", None), ("name", "Employee", None),
                 ("earning_type", "Type", None), ("amount", "Amount", "money"), ("remarks", "Remarks", None)],
        fields=[F("employee_id", "Employee", "select", True, options=opt_employees),
                F("payroll_period_id", "Payroll period", "select", True, options=opt_periods),
                F("earning_type", "Earning type", "select", True,
                  options=lambda db: [(t, t) for t in ("Bonus", "Overtime", "Incentive", "Arrears", "Other")]),
                F("amount", "Amount", "number", True, step="0.01", min=0.01),
                F("remarks", "Remarks")],
        delete_hint="Earnings of a processed period are locked.",
    ),
    "deductions": dict(
        table="deductions", pk="deduction_id", title="Deductions", singular="Deduction",
        icon="graph-down-arrow", period_col="payroll_period_id", lock_period=True,
        protect=("source", "AUTO"), fixed={"source": "MANUAL"},
        sql="SELECT x.deduction_id, x.payroll_period_id, p.period_name, e.emp_code, e.first_name, e.last_name, "
            "x.deduction_type, x.amount, x.is_statutory, x.source FROM deductions x "
            "JOIN employee e ON e.employee_id = x.employee_id "
            "JOIN payroll_period p ON p.payroll_period_id = x.payroll_period_id ORDER BY x.deduction_id DESC",
        row_hook=_employee_name,
        columns=[("period_name", "Period", None), ("emp_code", "Code", None), ("name", "Employee", None),
                 ("deduction_type", "Deduction", None), ("amount", "Amount", "money"),
                 ("is_statutory", "Statutory", "yesno"), ("source", "Source", "badge")],
        fields=[F("employee_id", "Employee", "select", True, options=opt_employees),
                F("payroll_period_id", "Payroll period", "select", True, options=opt_periods),
                F("deduction_type", "Deduction type", required=True, placeholder="e.g. Canteen Dues"),
                F("amount", "Amount", "number", True, step="0.01", min=0.01),
                F("is_statutory", "Statutory deduction?", "select", True, options=lambda db: YESNO, int=True)],
        defaults={"is_statutory": 0},
        delete_hint="AUTO rows (PF, ESI, PT, TDS, Loan EMI) are created by payroll processing and are read-only.",
    ),
    "loans": dict(
        table="loan", pk="loan_id", title="Loans", singular="Loan", icon="bank", view="loan_view",
        before_insert=lambda v: v.update(outstanding_balance=v["loan_amount"]),
        sql="SELECT l.loan_id, e.emp_code, e.first_name, e.last_name, l.loan_amount, l.emi_amount, "
            "l.outstanding_balance, l.start_date, l.purpose, l.status FROM loan l "
            "JOIN employee e ON e.employee_id = l.employee_id ORDER BY l.loan_id",
        row_hook=_employee_name,
        columns=[("loan_id", "Loan", None), ("emp_code", "Code", None), ("name", "Employee", None),
                 ("loan_amount", "Amount", "money"), ("emi_amount", "EMI", "money"),
                 ("outstanding_balance", "Outstanding", "money"), ("start_date", "Start", "date"),
                 ("status", "Status", "badge")],
        fields=[F("employee_id", "Employee", "select", True, options=opt_employees),
                F("loan_amount", "Loan amount", "number", True, step="0.01", min=1, insert_only=False),
                F("emi_amount", "Monthly EMI", "number", True, step="0.01", min=1),
                F("start_date", "First EMI month starts on", "date", True),
                F("purpose", "Purpose"),
                F("status", "Status", "select", True, options=lambda db: [("ACTIVE", "ACTIVE"), ("CLOSED", "CLOSED")])],
        defaults={"status": "ACTIVE"},
        delete_hint="",
    ),
}
