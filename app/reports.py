"""Payroll reports. Each report is just a SQL query - the report page shows the
query next to its result, which makes the DBMS concepts easy to demonstrate.
`?` is replaced by the selected payroll period id (all reports use only
standard SQL that runs on both SQLite and MySQL)."""

REPORTS = [
    dict(
        key="period-summary", title="Payroll summary by period",
        concept="JOIN + GROUP BY + SUM / COUNT / AVG", uses_period=False,
        sql="""SELECT pp.period_name, pp.status, COUNT(*) AS employees,
       SUM(p.gross_salary)     AS total_gross,
       SUM(p.total_deductions) AS total_deductions,
       SUM(p.net_salary)       AS total_net,
       AVG(p.net_salary)       AS avg_net
FROM payroll_detail p
JOIN payroll_period pp ON pp.payroll_period_id = p.payroll_period_id
GROUP BY pp.payroll_period_id, pp.period_name, pp.status
ORDER BY pp.payroll_period_id""",
        cols=[("period_name", "Period", None), ("status", "Status", "badge"), ("employees", "Employees", None),
              ("total_gross", "Total gross", "money"), ("total_deductions", "Total deductions", "money"),
              ("total_net", "Total net", "money"), ("avg_net", "Average net", "money")]),
    dict(
        key="department-cost", title="Department-wise payroll cost (selected period)",
        concept="Multi-table JOIN + GROUP BY + HAVING-ready aggregates", uses_period=True,
        sql="""SELECT d.department_name, COUNT(*) AS employees,
       SUM(p.gross_salary) AS total_gross,
       SUM(p.net_salary)   AS total_net,
       MAX(p.net_salary)   AS highest_net
FROM payroll_detail p
JOIN employee e   ON e.employee_id   = p.employee_id
JOIN department d ON d.department_id = e.department_id
WHERE p.payroll_period_id = ?
GROUP BY d.department_id, d.department_name
ORDER BY total_gross DESC""",
        cols=[("department_name", "Department", None), ("employees", "Employees", None),
              ("total_gross", "Total gross", "money"), ("total_net", "Total net", "money"),
              ("highest_net", "Highest net", "money")]),
    dict(
        key="statutory", title="Statutory deductions breakdown (selected period)",
        concept="Aggregate + WHERE filter on a flag column", uses_period=True,
        sql="""SELECT deduction_type, COUNT(*) AS employees_affected,
       SUM(amount) AS total_amount
FROM deductions
WHERE payroll_period_id = ? AND is_statutory = 1
GROUP BY deduction_type
ORDER BY total_amount DESC""",
        cols=[("deduction_type", "Deduction", None), ("employees_affected", "Employees", None),
              ("total_amount", "Total amount", "money")]),
    dict(
        key="top-earners", title="Top 5 net salaries (selected period)",
        concept="JOIN + ORDER BY + LIMIT", uses_period=True,
        sql="""SELECT e.emp_code, e.first_name, e.last_name, g.title, p.gross_salary, p.net_salary
FROM payroll_detail p
JOIN employee e    ON e.employee_id    = p.employee_id
JOIN designation g ON g.designation_id = e.designation_id
WHERE p.payroll_period_id = ?
ORDER BY p.net_salary DESC
LIMIT 5""",
        cols=[("emp_code", "Code", None), ("first_name", "First name", None), ("last_name", "Last name", None),
              ("title", "Designation", None), ("gross_salary", "Gross", "money"), ("net_salary", "Net", "money")]),
    dict(
        key="above-dept-avg", title="Employees above their department's average gross (selected period)",
        concept="Correlated subquery", uses_period=True,
        sql="""SELECT e.emp_code, e.first_name, d.department_name, p.gross_salary,
       (SELECT ROUND(AVG(p2.gross_salary), 2)
        FROM payroll_detail p2
        JOIN employee e2 ON e2.employee_id = p2.employee_id
        WHERE p2.payroll_period_id = p.payroll_period_id
          AND e2.department_id = e.department_id) AS dept_avg_gross
FROM payroll_detail p
JOIN employee e   ON e.employee_id   = p.employee_id
JOIN department d ON d.department_id = e.department_id
WHERE p.payroll_period_id = ?
  AND p.gross_salary > (SELECT AVG(p3.gross_salary)
                        FROM payroll_detail p3
                        JOIN employee e3 ON e3.employee_id = p3.employee_id
                        WHERE p3.payroll_period_id = p.payroll_period_id
                          AND e3.department_id = e.department_id)
ORDER BY d.department_name, p.gross_salary DESC""",
        cols=[("emp_code", "Code", None), ("first_name", "Name", None), ("department_name", "Department", None),
              ("gross_salary", "Gross", "money"), ("dept_avg_gross", "Dept. average", "money")]),
    dict(
        key="active-loans", title="Active loans and outstanding balances",
        concept="JOIN + subquery for repayments made", uses_period=False,
        sql="""SELECT l.loan_id, e.emp_code, e.first_name, l.loan_amount, l.emi_amount, l.outstanding_balance,
       (SELECT COALESCE(SUM(r.amount), 0) FROM loan_repayment r WHERE r.loan_id = l.loan_id) AS repaid_so_far
FROM loan l
JOIN employee e ON e.employee_id = l.employee_id
WHERE l.status = 'ACTIVE'
ORDER BY l.outstanding_balance DESC""",
        cols=[("loan_id", "Loan", None), ("emp_code", "Code", None), ("first_name", "Name", None),
              ("loan_amount", "Loan amount", "money"), ("emi_amount", "EMI", "money"),
              ("repaid_so_far", "Repaid so far", "money"), ("outstanding_balance", "Outstanding", "money")]),
    dict(
        key="not-processed", title="Active employees without payroll in the selected period",
        concept="NOT EXISTS subquery", uses_period=True,
        sql="""SELECT e.emp_code, e.first_name, e.last_name, d.department_name
FROM employee e
JOIN department d ON d.department_id = e.department_id
WHERE e.status = 'ACTIVE'
  AND NOT EXISTS (SELECT 1 FROM payroll_detail p
                  WHERE p.employee_id = e.employee_id AND p.payroll_period_id = ?)
ORDER BY e.emp_code""",
        cols=[("emp_code", "Code", None), ("first_name", "First name", None), ("last_name", "Last name", None),
              ("department_name", "Department", None)]),
]
