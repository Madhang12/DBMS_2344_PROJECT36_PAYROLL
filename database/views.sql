-- Reporting views (identical on MySQL 8 and SQLite). Loaded after the seed data.

CREATE VIEW v_payroll_summary AS
SELECT p.payroll_id, p.payroll_period_id, pp.period_name, e.emp_code, e.first_name, e.last_name,
       d.department_name, p.gross_salary, p.total_deductions, p.net_salary
FROM payroll_detail p
JOIN employee e        ON e.employee_id = p.employee_id
JOIN department d      ON d.department_id = e.department_id
JOIN payroll_period pp ON pp.payroll_period_id = p.payroll_period_id;

CREATE VIEW v_department_cost AS
SELECT pp.payroll_period_id, pp.period_name, d.department_name,
       COUNT(*) AS employees, SUM(p.gross_salary) AS total_gross,
       SUM(p.total_deductions) AS total_deductions, SUM(p.net_salary) AS total_net
FROM payroll_detail p
JOIN employee e        ON e.employee_id = p.employee_id
JOIN department d      ON d.department_id = e.department_id
JOIN payroll_period pp ON pp.payroll_period_id = p.payroll_period_id
GROUP BY pp.payroll_period_id, pp.period_name, d.department_name;

CREATE VIEW v_loan_ledger AS
SELECT l.loan_id, e.emp_code, e.first_name, e.last_name, l.loan_amount, l.emi_amount,
       l.outstanding_balance, COALESCE(SUM(r.amount), 0) AS repaid_through_payroll, l.status
FROM loan l
JOIN employee e ON e.employee_id = l.employee_id
LEFT JOIN loan_repayment r ON r.loan_id = l.loan_id
GROUP BY l.loan_id, e.emp_code, e.first_name, e.last_name, l.loan_amount, l.emi_amount, l.outstanding_balance, l.status;
