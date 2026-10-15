-- =====================================================================
-- Project 36 : SQL operations demonstrated in the DBMS review / viva
-- Works on MySQL 8 and SQLite (standard SQL only). Run AFTER schema + seed
-- + the demo payroll (python scripts/init_db.py).  Section 1 modifies data
-- and cleans up after itself; tests/test_app.py executes this whole file.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. CRUD  (Create / Read / Update / Delete)
-- ---------------------------------------------------------------------
-- CREATE
INSERT INTO department (department_name, location) VALUES ('Research Lab', 'Hyderabad');
INSERT INTO employee (emp_code, first_name, last_name, email, phone, date_of_joining, department_id, designation_id, status)
VALUES ('EMP900', 'Demo', 'Person', 'emp900@example.com', '9000099900', '2026-10-01',
        (SELECT department_id FROM department WHERE department_name = 'Research Lab'), 3, 'ACTIVE');
-- READ
SELECT employee_id, emp_code, first_name, last_name, status FROM employee WHERE emp_code = 'EMP900';
-- UPDATE
UPDATE employee SET phone = '9000011111', designation_id = 4 WHERE emp_code = 'EMP900';
-- DELETE (child rows first would be needed only if the employee had payroll)
DELETE FROM employee WHERE emp_code = 'EMP900';
DELETE FROM department WHERE department_name = 'Research Lab';

-- ---------------------------------------------------------------------
-- 2. JOINs
-- ---------------------------------------------------------------------
-- 2.1 INNER JOIN (3 tables): employee directory
SELECT e.emp_code, e.first_name, e.last_name, d.department_name, g.title
FROM employee e
JOIN department  d ON d.department_id  = e.department_id
JOIN designation g ON g.designation_id = e.designation_id
ORDER BY e.emp_code;

-- 2.2 LEFT JOIN: departments with their employee count (includes empty departments)
SELECT d.department_name, COUNT(e.employee_id) AS employees
FROM department d
LEFT JOIN employee e ON e.department_id = d.department_id
GROUP BY d.department_id, d.department_name
ORDER BY employees DESC;

-- 2.3 Payslip header: payroll + payslip + employee + period (5-table join)
SELECT ps.payslip_no, e.first_name, e.last_name, pp.period_name, p.gross_salary, p.total_deductions, p.net_salary
FROM payslip ps
JOIN payroll_detail p  ON p.payroll_id = ps.payroll_id
JOIN employee e        ON e.employee_id = p.employee_id
JOIN payroll_period pp ON pp.payroll_period_id = p.payroll_period_id
ORDER BY pp.payroll_period_id, e.emp_code;

-- 2.4 Fixed gross (derived from salary structure) with employee name
SELECT e.emp_code, e.first_name,
       s.basic_salary + s.hra + s.da + s.special_allowance AS fixed_gross
FROM salary_structure s
JOIN employee e ON e.employee_id = s.employee_id
ORDER BY fixed_gross DESC;

-- ---------------------------------------------------------------------
-- 3. Aggregate functions + GROUP BY + HAVING
-- ---------------------------------------------------------------------
-- 3.1 Totals for each payroll period
SELECT payroll_period_id, COUNT(*) AS employees, SUM(gross_salary) AS total_gross,
       SUM(total_deductions) AS total_deductions, SUM(net_salary) AS total_net,
       AVG(net_salary) AS avg_net, MIN(net_salary) AS lowest_net, MAX(net_salary) AS highest_net
FROM payroll_detail
GROUP BY payroll_period_id
ORDER BY payroll_period_id;

-- 3.2 Department payroll cost for period 1; HAVING keeps only departments above 2 employees
SELECT d.department_name, COUNT(*) AS employees, SUM(p.gross_salary) AS total_gross
FROM payroll_detail p
JOIN employee e   ON e.employee_id = p.employee_id
JOIN department d ON d.department_id = e.department_id
WHERE p.payroll_period_id = 1
GROUP BY d.department_id, d.department_name
HAVING COUNT(*) > 2
ORDER BY total_gross DESC;

-- 3.3 Statutory deductions by type (period 2)
SELECT deduction_type, COUNT(*) AS employees, SUM(amount) AS total
FROM deductions
WHERE payroll_period_id = 2 AND is_statutory = 1
GROUP BY deduction_type;

-- 3.4 Total loss-of-pay days per department (derived LOP = working - present - paid leave)
SELECT d.department_name, SUM(a.working_days - a.days_present - a.paid_leave_days) AS lop_days
FROM attendance_summary a
JOIN employee e   ON e.employee_id = a.employee_id
JOIN department d ON d.department_id = e.department_id
GROUP BY d.department_id, d.department_name
ORDER BY lop_days DESC;

-- ---------------------------------------------------------------------
-- 4. Subqueries
-- ---------------------------------------------------------------------
-- 4.1 Scalar subquery: employees paid more than the company average net (period 2)
SELECT e.emp_code, e.first_name, p.net_salary
FROM payroll_detail p JOIN employee e ON e.employee_id = p.employee_id
WHERE p.payroll_period_id = 2
  AND p.net_salary > (SELECT AVG(net_salary) FROM payroll_detail WHERE payroll_period_id = 2)
ORDER BY p.net_salary DESC;

-- 4.2 IN subquery: employees who currently have an active loan
SELECT emp_code, first_name, last_name FROM employee
WHERE employee_id IN (SELECT employee_id FROM loan WHERE status = 'ACTIVE');

-- 4.3 NOT EXISTS: active employees with no payroll yet for period 3 (October 2026)
SELECT e.emp_code, e.first_name FROM employee e
WHERE e.status = 'ACTIVE'
  AND NOT EXISTS (SELECT 1 FROM payroll_detail p WHERE p.employee_id = e.employee_id AND p.payroll_period_id = 3);

-- 4.4 Correlated subquery: each employee's gross vs their department average (period 2)
SELECT e.emp_code, e.first_name, p.gross_salary,
       (SELECT AVG(p2.gross_salary) FROM payroll_detail p2 JOIN employee e2 ON e2.employee_id = p2.employee_id
        WHERE p2.payroll_period_id = p.payroll_period_id AND e2.department_id = e.department_id) AS dept_avg
FROM payroll_detail p JOIN employee e ON e.employee_id = p.employee_id
WHERE p.payroll_period_id = 2
ORDER BY e.emp_code;

-- 4.5 Subquery in FROM (derived table): highest-paid department
SELECT t.department_name, t.total_net
FROM (SELECT d.department_name, SUM(p.net_salary) AS total_net
      FROM payroll_detail p JOIN employee e ON e.employee_id = p.employee_id
      JOIN department d ON d.department_id = e.department_id
      WHERE p.payroll_period_id = 2 GROUP BY d.department_id, d.department_name) t
ORDER BY t.total_net DESC
LIMIT 1;

-- ---------------------------------------------------------------------
-- 5. Payroll calculation expressed in SQL (cross-check of the app's engine)
--    net = gross - total_deductions must hold for every payroll row
-- ---------------------------------------------------------------------
SELECT COUNT(*) AS rows_checked,
       SUM(CASE WHEN ABS(gross_salary - total_deductions - net_salary) < 0.01 THEN 1 ELSE 0 END) AS rows_consistent
FROM payroll_detail;

-- total_deductions must equal statutory + loan + other
SELECT COUNT(*) AS rows_checked,
       SUM(CASE WHEN ABS(statutory_deductions + loan_deductions + other_deductions - total_deductions) < 0.01 THEN 1 ELSE 0 END) AS rows_consistent
FROM payroll_detail;

-- itemised AUTO + MANUAL deduction rows must add up to payroll_detail.total_deductions
SELECT COUNT(*) AS rows_checked,
       SUM(CASE WHEN ABS(x.item_total - p.total_deductions) < 0.01 THEN 1 ELSE 0 END) AS rows_consistent
FROM payroll_detail p
JOIN (SELECT employee_id, payroll_period_id, SUM(amount) AS item_total FROM deductions
      GROUP BY employee_id, payroll_period_id) x
  ON x.employee_id = p.employee_id AND x.payroll_period_id = p.payroll_period_id;

-- ---------------------------------------------------------------------
-- 6. Reports
-- ---------------------------------------------------------------------
-- 6.1 Payroll register for one period
SELECT e.emp_code, e.first_name, e.last_name, d.department_name,
       p.gross_salary, p.statutory_deductions, p.loan_deductions, p.other_deductions, p.net_salary
FROM payroll_detail p
JOIN employee e   ON e.employee_id = p.employee_id
JOIN department d ON d.department_id = e.department_id
WHERE p.payroll_period_id = 2
ORDER BY e.emp_code;

-- 6.2 Bank transfer status summary
SELECT status, COUNT(*) AS transfers, SUM(amount) AS total_amount FROM bank_transfer GROUP BY status;

-- 6.3 Loan ledger: repayments per loan
SELECT l.loan_id, e.emp_code, l.loan_amount, l.outstanding_balance,
       COUNT(r.repayment_id) AS emis_paid, COALESCE(SUM(r.amount), 0) AS repaid
FROM loan l
JOIN employee e ON e.employee_id = l.employee_id
LEFT JOIN loan_repayment r ON r.loan_id = l.loan_id
GROUP BY l.loan_id, e.emp_code, l.loan_amount, l.outstanding_balance
ORDER BY l.loan_id;

-- 6.4 Views (defined in database/views.sql): reuse packaged queries like tables
SELECT * FROM v_payroll_summary WHERE period_name = 'September 2026' ORDER BY net_salary DESC LIMIT 5;
SELECT * FROM v_department_cost WHERE period_name = 'September 2026' ORDER BY total_gross DESC;
SELECT * FROM v_loan_ledger WHERE status = 'ACTIVE';

-- ---------------------------------------------------------------------
-- 7. Integrity demonstrations (each statement below is EXPECTED TO FAIL).
--    They are kept commented out so the file runs cleanly; uncomment one at
--    a time during the viva to show the constraint rejecting bad data.
-- ---------------------------------------------------------------------
-- Foreign key: employee in a non-existent department
--   INSERT INTO employee (emp_code, first_name, last_name, email, date_of_joining, department_id, designation_id) VALUES ('X1','A','B','x1@example.com','2026-01-01',99,1);
-- Foreign key RESTRICT: delete an employee that already has payroll
--   DELETE FROM employee WHERE employee_id = 1;
-- CHECK: negative basic salary
--   UPDATE salary_structure SET basic_salary = -5 WHERE employee_id = 1;
-- CHECK: present + paid leave cannot exceed working days
--   UPDATE attendance_summary SET days_present = 40 WHERE attendance_id = 1;
-- UNIQUE: a second salary structure for the same employee (1:1 relationship)
--   INSERT INTO salary_structure (employee_id, basic_salary, effective_from) VALUES (1, 1000, '2026-01-01');
-- Trigger: payroll history of a PROCESSED/PAID period cannot be changed or deleted
--   UPDATE payroll_detail SET net_salary = 1 WHERE payroll_id = 1;   -> "Payroll history is locked ..."
--   DELETE FROM payroll_detail WHERE payroll_id = 1;                 -> "Payroll history is locked ..."

-- ---------------------------------------------------------------------
-- 8. Triggers and the audit trail (self-cleaning demo)
--    database/*/triggers.sql writes audit_log rows when salary, employee status or a rate changes.
-- ---------------------------------------------------------------------
UPDATE salary_structure SET basic_salary = basic_salary + 1000 WHERE employee_id = 2;
UPDATE salary_structure SET basic_salary = basic_salary - 1000 WHERE employee_id = 2;
SELECT table_name, record_ref, action, old_value, new_value FROM audit_log WHERE table_name = 'salary_structure';
DELETE FROM audit_log WHERE table_name = 'salary_structure';
