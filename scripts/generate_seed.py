"""Generate database/seed.sql - 100% synthetic demo data (fixed random seed).

Names are random combinations of common first/last names, e-mails use the
reserved example.com domain, phone numbers use a fake 90000xxxxx range, and
bank account numbers / IFSC codes are made-up. None of it is real.

Only *input* data is generated here (masters, employees, salary structures,
attendance, extra earnings, manual deductions, loans, periods, config).
Payroll results (payroll_detail, payslip, bank_transfer, AUTO deductions,
loan repayments) are produced by the application's payroll engine, never
hand-inserted - see scripts/init_db.py.
"""
import calendar
import random
from datetime import date
from pathlib import Path

random.seed(36)
out = []


def q(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def insert(table, cols, rows):
    out.append(f"-- {table}")
    for r in rows:
        out.append(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(q(x) for x in r)});")
    out.append("")


# ---------------- masters ----------------
departments = [
    (1, "Engineering", "Hyderabad"), (2, "Human Resources", "Hyderabad"),
    (3, "Finance", "Hyderabad"), (4, "Sales & Marketing", "Bengaluru"),
    (5, "Operations", "Chennai"), (6, "Customer Support", "Chennai"),
]
insert("department", ["department_id", "department_name", "location"], departments)

designations = [
    (1, "Intern", 1), (2, "Junior Associate", 2), (3, "Associate", 3),
    (4, "Senior Associate", 4), (5, "Team Lead", 5), (6, "Manager", 6),
    (7, "Senior Manager", 7), (8, "Director", 8),
]
insert("designation", ["designation_id", "title", "grade_level"], designations)

base_basic = {1: 9000, 2: 11500, 3: 20000, 4: 30000, 5: 42000, 6: 60000, 7: 85000, 8: 130000}

# ---------------- employees ----------------
firsts = ["Aarav", "Diya", "Vihaan", "Ananya", "Arjun", "Isha", "Kabir", "Meera", "Rohan", "Sara",
          "Aditya", "Kavya", "Nikhil", "Pooja", "Rahul", "Sneha", "Varun", "Tanvi", "Karthik", "Lavanya",
          "Manoj", "Nisha", "Pranav", "Riya", "Siddharth", "Swathi", "Tarun", "Uma", "Vikram", "Zoya"]
lasts = ["Sharma", "Reddy", "Iyer", "Nair", "Patel", "Rao", "Menon", "Gupta", "Verma", "Das",
         "Naidu", "Kulkarni", "Joshi", "Mehta", "Pillai", "Bose", "Chopra", "Kapoor", "Singh", "Yadav"]
banks = [("Demo National Bank", "DEMO0000001"), ("Sample Union Bank", "SMPL0000002"), ("Test Cooperative Bank", "TEST0000003")]
random.shuffle(firsts)

# (department, designation) assignment: dept -> list of designation ids (deterministic spread)
plan = {
    1: [8, 7, 6, 5, 5, 4, 4, 3, 3, 3, 2, 1],
    2: [7, 5, 3, 2],
    3: [7, 5, 4, 3, 2],
    4: [6, 5, 4, 3, 2],
    5: [6, 4, 3, 2],
}
# total = 12+4+5+5+4 = 30 employees (Customer Support has none yet -> shows empty-dept case)
employees, salaries = [], []
eid = 0
for dept, desigs in plan.items():
    for d in desigs:
        eid += 1
        first = firsts[(eid - 1) % len(firsts)]
        last = lasts[(eid * 7) % len(lasts)]
        joined = date(2022 + (eid % 4), 1 + (eid * 5) % 12, 1 + (eid * 3) % 28)
        if joined > date(2026, 7, 31):
            joined = date(2026, 3, 15)
        bank, ifsc = banks[eid % 3]
        employees.append((eid, f"EMP{eid:03d}", first, last, f"emp{eid:03d}@example.com",
                          f"90000{eid:05d}", joined.isoformat(), dept, d, bank,
                          f"000{random.randint(10**8, 10**9 - 1)}", ifsc, "ACTIVE"))
        basic = round(base_basic[d] * random.uniform(0.95, 1.12) / 100) * 100
        salaries.append((eid, eid, basic, round(basic * 0.40), round(basic * 0.10), round(basic * 0.20),
                         joined.isoformat() if joined.year >= 2026 else "2026-04-01"))

# one inactive employee (excluded from payroll runs)
employees[-1] = employees[-1][:-1] + ("INACTIVE",)

insert("employee", ["employee_id", "emp_code", "first_name", "last_name", "email", "phone", "date_of_joining",
                    "department_id", "designation_id", "bank_name", "bank_account_no", "ifsc_code", "status"], employees)
insert("salary_structure", ["salary_structure_id", "employee_id", "basic_salary", "hra", "da",
                            "special_allowance", "effective_from"], salaries)

# ---------------- payroll periods ----------------
periods = []
for pid, (m, name) in enumerate([(8, "August 2026"), (9, "September 2026"), (10, "October 2026")], start=1):
    last_day = calendar.monthrange(2026, m)[1]
    periods.append((pid, name, m, 2026, date(2026, m, 1).isoformat(), date(2026, m, last_day).isoformat(), "OPEN"))
insert("payroll_period", ["payroll_period_id", "period_name", "period_month", "period_year",
                          "start_date", "end_date", "status"], periods)


def weekdays(y, m):
    return sum(1 for d in range(1, calendar.monthrange(y, m)[1] + 1) if date(y, m, d).weekday() < 5)


# ---------------- attendance ----------------
att, aid = [], 0
for p in periods:
    wd = weekdays(2026, p[2])
    for e in employees:
        aid += 1
        roll = random.random()
        paid_leave = random.choice([0, 0, 0, 1, 1, 2])
        lop = 0 if roll < 0.82 else random.choice([1, 1, 2, 3])
        present = wd - paid_leave - lop
        att.append((aid, e[0], p[0], wd, present, paid_leave))
insert("attendance_summary", ["attendance_id", "employee_id", "payroll_period_id", "working_days",
                              "days_present", "paid_leave_days"], att)

# ---------------- extra earnings & manual deductions ----------------
earn, eidx = [], 0
for p in periods:
    for emp in random.sample(range(1, 30), 6):
        eidx += 1
        t = random.choice(["Bonus", "Overtime", "Incentive", "Arrears"])
        amt = {"Bonus": 5000, "Overtime": 2500, "Incentive": 3500, "Arrears": 1800}[t]
        earn.append((eidx, emp, p[0], t, amt, f"{t} - {p[1]}"))
insert("earnings", ["earning_id", "employee_id", "payroll_period_id", "earning_type", "amount", "remarks"], earn)

ded, didx = [], 0
for p in periods:
    for emp in random.sample(range(1, 30), 4):
        didx += 1
        t, amt = random.choice([("Canteen Dues", 800), ("Salary Advance Recovery", 2000), ("Voluntary Insurance Premium", 1200)])
        ded.append((didx, emp, p[0], t, amt, 0, "MANUAL"))
insert("deductions", ["deduction_id", "employee_id", "payroll_period_id", "deduction_type", "amount",
                      "is_statutory", "source"], ded)

# ---------------- loans ----------------
loans = [
    (1, 3, 60000, 5000, 60000, "2026-08-01", "Personal loan", "ACTIVE"),
    (2, 9, 120000, 10000, 120000, "2026-08-01", "Two-wheeler purchase", "ACTIVE"),
    (3, 14, 30000, 3000, 30000, "2026-08-01", "Medical emergency", "ACTIVE"),
    (4, 18, 200000, 10000, 200000, "2026-09-01", "Home renovation", "ACTIVE"),
    (5, 22, 45000, 4500, 45000, "2026-09-01", "Education fees", "ACTIVE"),
    (6, 26, 90000, 7500, 90000, "2026-10-01", "Laptop purchase", "ACTIVE"),
]
insert("loan", ["loan_id", "employee_id", "loan_amount", "emi_amount", "outstanding_balance",
                "start_date", "purpose", "status"], loans)

# ---------------- illustrative configuration ----------------
cfg = [
    ("pf_rate", 0.12, "Employee PF rate applied on basic salary (illustrative)"),
    ("pf_wage_ceiling", 15000, "Monthly basic-salary ceiling for PF (illustrative)"),
    ("esi_rate", 0.0075, "Employee ESI rate on gross salary (illustrative)"),
    ("esi_gross_limit", 21000, "ESI applies only when gross salary <= this limit"),
    ("pt_amount", 200, "Flat professional tax per month (illustrative)"),
    ("pt_gross_limit", 15000, "Professional tax applies when gross salary > this limit"),
    ("tds_rate", 0.05, "Illustrative income-tax (TDS) rate on gross above the threshold"),
    ("tds_monthly_threshold", 50000, "Monthly gross above which illustrative TDS applies"),
]
insert("payroll_config", ["config_key", "config_value", "description"], cfg)

path = Path(__file__).resolve().parent.parent / "database" / "seed.sql"
header = ("-- Synthetic demo data for Project 36 (generated by scripts/generate_seed.py).\n"
          "-- All names, e-mails, phones and bank details are fictitious.\n\n")
path.write_text(header + "\n".join(out))
print(f"wrote {path} ({len(employees)} employees, {len(att)} attendance rows)")
