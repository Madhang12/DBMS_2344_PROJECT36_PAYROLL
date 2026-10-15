-- =====================================================================
-- Project 36 : Employee Payroll and Statutory Deduction Management System
-- MySQL 8.0+ schema  (the SQLite schema is generated from this file by
-- scripts/build_sqlite_schema.py so both stay identical)
--
-- Review 1 had 12 entities. Final design = 12 Review-1 entities
-- + loan_repayment (needed for "loans and repayments")
-- + payroll_config (configurable illustrative deduction rates)
-- Normalisation: every table is in 3NF. LOP days, gross, net are derived
-- from stored facts; payroll_detail stores the *result* of a processing run
-- as an audit snapshot (so past payslips never change if rates change).
-- =====================================================================

CREATE DATABASE IF NOT EXISTS payroll_db CHARACTER SET utf8mb4;
USE payroll_db;

-- ---------- Master tables ----------
CREATE TABLE department (
    department_id    INT AUTO_INCREMENT PRIMARY KEY,
    department_name  VARCHAR(80) NOT NULL,
    location         VARCHAR(80),
    CONSTRAINT uq_department_name UNIQUE (department_name)
) ENGINE=InnoDB;

CREATE TABLE designation (
    designation_id   INT AUTO_INCREMENT PRIMARY KEY,
    title            VARCHAR(80) NOT NULL,
    grade_level      INT NOT NULL,
    CONSTRAINT uq_designation_title UNIQUE (title),
    CONSTRAINT chk_grade CHECK (grade_level BETWEEN 1 AND 10)
) ENGINE=InnoDB;

CREATE TABLE employee (
    employee_id      INT AUTO_INCREMENT PRIMARY KEY,
    emp_code         VARCHAR(12) NOT NULL,
    first_name       VARCHAR(50) NOT NULL,
    last_name        VARCHAR(50) NOT NULL,
    email            VARCHAR(100) NOT NULL,
    phone            VARCHAR(15),
    date_of_joining  DATE NOT NULL,
    department_id    INT NOT NULL,
    designation_id   INT NOT NULL,
    bank_name        VARCHAR(60),
    bank_account_no  VARCHAR(20),
    ifsc_code        VARCHAR(11),
    status           VARCHAR(10) NOT NULL DEFAULT 'ACTIVE',
    CONSTRAINT uq_emp_code  UNIQUE (emp_code),
    CONSTRAINT uq_emp_email UNIQUE (email),
    CONSTRAINT chk_emp_status CHECK (status IN ('ACTIVE','INACTIVE')),
    CONSTRAINT fk_emp_dept  FOREIGN KEY (department_id)  REFERENCES department(department_id)  ON DELETE RESTRICT,
    CONSTRAINT fk_emp_desig FOREIGN KEY (designation_id) REFERENCES designation(designation_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 1:1 with employee (UNIQUE foreign key)
CREATE TABLE salary_structure (
    salary_structure_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id         INT NOT NULL,
    basic_salary        DECIMAL(12,2) NOT NULL,
    hra                 DECIMAL(12,2) NOT NULL DEFAULT 0,
    da                  DECIMAL(12,2) NOT NULL DEFAULT 0,
    special_allowance   DECIMAL(12,2) NOT NULL DEFAULT 0,
    effective_from      DATE NOT NULL,
    CONSTRAINT uq_salary_employee UNIQUE (employee_id),
    CONSTRAINT chk_salary_basic CHECK (basic_salary > 0),
    CONSTRAINT chk_salary_allow CHECK (hra >= 0 AND da >= 0 AND special_allowance >= 0),
    CONSTRAINT fk_salary_emp FOREIGN KEY (employee_id) REFERENCES employee(employee_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE payroll_period (
    payroll_period_id INT AUTO_INCREMENT PRIMARY KEY,
    period_name       VARCHAR(30) NOT NULL,
    period_month      INT NOT NULL,
    period_year       INT NOT NULL,
    start_date        DATE NOT NULL,
    end_date          DATE NOT NULL,
    status            VARCHAR(10) NOT NULL DEFAULT 'OPEN',
    CONSTRAINT uq_period_name  UNIQUE (period_name),
    CONSTRAINT uq_period_my    UNIQUE (period_month, period_year),
    CONSTRAINT chk_period_month  CHECK (period_month BETWEEN 1 AND 12),
    CONSTRAINT chk_period_dates  CHECK (end_date >= start_date),
    CONSTRAINT chk_period_status CHECK (status IN ('OPEN','PROCESSED','PAID'))
) ENGINE=InnoDB;

-- ---------- Monthly input tables ----------
CREATE TABLE attendance_summary (
    attendance_id     INT AUTO_INCREMENT PRIMARY KEY,
    employee_id       INT NOT NULL,
    payroll_period_id INT NOT NULL,
    working_days      INT NOT NULL,
    days_present      DECIMAL(4,1) NOT NULL,
    paid_leave_days   DECIMAL(4,1) NOT NULL DEFAULT 0,
    CONSTRAINT uq_att_emp_period UNIQUE (employee_id, payroll_period_id),
    CONSTRAINT chk_att_days CHECK (working_days BETWEEN 1 AND 31 AND days_present >= 0 AND paid_leave_days >= 0),
    CONSTRAINT chk_att_total CHECK (days_present + paid_leave_days <= working_days),
    CONSTRAINT fk_att_emp    FOREIGN KEY (employee_id)       REFERENCES employee(employee_id) ON DELETE CASCADE,
    CONSTRAINT fk_att_period FOREIGN KEY (payroll_period_id) REFERENCES payroll_period(payroll_period_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Extra (variable) earnings: bonus, overtime, ...
CREATE TABLE earnings (
    earning_id        INT AUTO_INCREMENT PRIMARY KEY,
    employee_id       INT NOT NULL,
    payroll_period_id INT NOT NULL,
    earning_type      VARCHAR(20) NOT NULL,
    amount            DECIMAL(12,2) NOT NULL,
    remarks           VARCHAR(120),
    CONSTRAINT chk_earn_type   CHECK (earning_type IN ('Bonus','Overtime','Incentive','Arrears','Other')),
    CONSTRAINT chk_earn_amount CHECK (amount > 0),
    CONSTRAINT fk_earn_emp    FOREIGN KEY (employee_id)       REFERENCES employee(employee_id) ON DELETE CASCADE,
    CONSTRAINT fk_earn_period FOREIGN KEY (payroll_period_id) REFERENCES payroll_period(payroll_period_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Statutory (PF/ESI/PT/TDS, written by payroll processing: source='AUTO')
-- and other deductions (entered by the payroll officer: source='MANUAL')
CREATE TABLE deductions (
    deduction_id      INT AUTO_INCREMENT PRIMARY KEY,
    employee_id       INT NOT NULL,
    payroll_period_id INT NOT NULL,
    deduction_type    VARCHAR(40) NOT NULL,
    amount            DECIMAL(12,2) NOT NULL,
    is_statutory      TINYINT(1) NOT NULL DEFAULT 0,
    source            VARCHAR(6) NOT NULL DEFAULT 'MANUAL',
    CONSTRAINT chk_ded_amount CHECK (amount > 0),
    CONSTRAINT chk_ded_stat   CHECK (is_statutory IN (0,1)),
    CONSTRAINT chk_ded_source CHECK (source IN ('MANUAL','AUTO')),
    CONSTRAINT fk_ded_emp    FOREIGN KEY (employee_id)       REFERENCES employee(employee_id) ON DELETE CASCADE,
    CONSTRAINT fk_ded_period FOREIGN KEY (payroll_period_id) REFERENCES payroll_period(payroll_period_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE loan (
    loan_id             INT AUTO_INCREMENT PRIMARY KEY,
    employee_id         INT NOT NULL,
    loan_amount         DECIMAL(12,2) NOT NULL,
    emi_amount          DECIMAL(12,2) NOT NULL,
    outstanding_balance DECIMAL(12,2) NOT NULL,
    start_date          DATE NOT NULL,
    purpose             VARCHAR(80),
    status              VARCHAR(10) NOT NULL DEFAULT 'ACTIVE',
    CONSTRAINT chk_loan_amount CHECK (loan_amount > 0 AND emi_amount > 0),
    CONSTRAINT chk_loan_bal    CHECK (outstanding_balance >= 0 AND outstanding_balance <= loan_amount),
    CONSTRAINT chk_loan_status CHECK (status IN ('ACTIVE','CLOSED')),
    CONSTRAINT fk_loan_emp FOREIGN KEY (employee_id) REFERENCES employee(employee_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------- Payroll output tables ----------
CREATE TABLE payroll_detail (
    payroll_id           INT AUTO_INCREMENT PRIMARY KEY,
    employee_id          INT NOT NULL,
    payroll_period_id    INT NOT NULL,
    basic_salary         DECIMAL(12,2) NOT NULL,
    hra                  DECIMAL(12,2) NOT NULL,
    da                   DECIMAL(12,2) NOT NULL,
    special_allowance    DECIMAL(12,2) NOT NULL,
    working_days         INT NOT NULL,
    lop_days             DECIMAL(4,1) NOT NULL,
    lop_amount           DECIMAL(12,2) NOT NULL,
    other_earnings       DECIMAL(12,2) NOT NULL,
    gross_salary         DECIMAL(12,2) NOT NULL,
    statutory_deductions DECIMAL(12,2) NOT NULL,
    loan_deductions      DECIMAL(12,2) NOT NULL,
    other_deductions     DECIMAL(12,2) NOT NULL,
    total_deductions     DECIMAL(12,2) NOT NULL,
    net_salary           DECIMAL(12,2) NOT NULL,
    processed_on         DATE NOT NULL,
    CONSTRAINT uq_payroll_emp_period UNIQUE (employee_id, payroll_period_id),
    CONSTRAINT chk_payroll_net CHECK (net_salary >= 0 AND gross_salary >= 0 AND total_deductions >= 0),
    CONSTRAINT fk_pay_emp    FOREIGN KEY (employee_id)       REFERENCES employee(employee_id) ON DELETE RESTRICT,
    CONSTRAINT fk_pay_period FOREIGN KEY (payroll_period_id) REFERENCES payroll_period(payroll_period_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE loan_repayment (
    repayment_id   INT AUTO_INCREMENT PRIMARY KEY,
    loan_id        INT NOT NULL,
    payroll_id     INT NULL,              -- NULL = manual / cash repayment
    amount         DECIMAL(12,2) NOT NULL,
    repayment_date DATE NOT NULL,
    balance_after  DECIMAL(12,2) NOT NULL,
    CONSTRAINT chk_repay_amount CHECK (amount > 0 AND balance_after >= 0),
    CONSTRAINT fk_repay_loan    FOREIGN KEY (loan_id)    REFERENCES loan(loan_id) ON DELETE CASCADE,
    CONSTRAINT fk_repay_payroll FOREIGN KEY (payroll_id) REFERENCES payroll_detail(payroll_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 1:1 with payroll_detail
CREATE TABLE payslip (
    payslip_id   INT AUTO_INCREMENT PRIMARY KEY,
    payroll_id   INT NOT NULL,
    payslip_no   VARCHAR(30) NOT NULL,
    generated_on DATE NOT NULL,
    CONSTRAINT uq_payslip_payroll UNIQUE (payroll_id),
    CONSTRAINT uq_payslip_no      UNIQUE (payslip_no),
    CONSTRAINT fk_payslip_payroll FOREIGN KEY (payroll_id) REFERENCES payroll_detail(payroll_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 1:1 with payroll_detail (simulated transfer record - no real bank API)
CREATE TABLE bank_transfer (
    transfer_id   INT AUTO_INCREMENT PRIMARY KEY,
    payroll_id    INT NOT NULL,
    bank_name     VARCHAR(60),
    account_no    VARCHAR(20),
    ifsc_code     VARCHAR(11),
    amount        DECIMAL(12,2) NOT NULL,
    transfer_date DATE NULL,
    reference_no  VARCHAR(30) NOT NULL,
    status        VARCHAR(10) NOT NULL DEFAULT 'PENDING',
    CONSTRAINT uq_transfer_payroll UNIQUE (payroll_id),
    CONSTRAINT uq_transfer_ref     UNIQUE (reference_no),
    CONSTRAINT chk_transfer_amount CHECK (amount >= 0),
    CONSTRAINT chk_transfer_status CHECK (status IN ('PENDING','SUCCESS','FAILED')),
    CONSTRAINT fk_transfer_payroll FOREIGN KEY (payroll_id) REFERENCES payroll_detail(payroll_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Configurable illustrative rates (edited from the Settings page)
CREATE TABLE payroll_config (
    config_key   VARCHAR(40) PRIMARY KEY,
    config_value DECIMAL(12,4) NOT NULL,
    description  VARCHAR(160)
) ENGINE=InnoDB;

-- Helpful indexes on foreign keys / frequent filters
CREATE INDEX idx_emp_dept      ON employee(department_id);
CREATE INDEX idx_emp_desig     ON employee(designation_id);
CREATE INDEX idx_att_period    ON attendance_summary(payroll_period_id);
CREATE INDEX idx_earn_emp_per  ON earnings(employee_id, payroll_period_id);
CREATE INDEX idx_ded_emp_per   ON deductions(employee_id, payroll_period_id);
CREATE INDEX idx_loan_emp      ON loan(employee_id);
CREATE INDEX idx_pay_period    ON payroll_detail(payroll_period_id);

-- Application login accounts (passwords are stored only as salted hashes)
CREATE TABLE app_user (
    user_id        INT AUTO_INCREMENT PRIMARY KEY,
    username       VARCHAR(30)  NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    role           VARCHAR(10)  NOT NULL,
    employee_id    INT NULL,
    is_active      TINYINT(1)   NOT NULL DEFAULT 1,
    CONSTRAINT uq_user_name     UNIQUE (username),
    CONSTRAINT chk_user_role    CHECK (role IN ('ADMIN','HR','EMPLOYEE')),
    CONSTRAINT chk_user_emp     CHECK (role <> 'EMPLOYEE' OR employee_id IS NOT NULL),
    CONSTRAINT fk_user_employee FOREIGN KEY (employee_id) REFERENCES employee(employee_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Written by database triggers (see database/*/triggers.sql): who/what changed salary, status and rates
CREATE TABLE audit_log (
    audit_id    INT AUTO_INCREMENT PRIMARY KEY,
    table_name  VARCHAR(40)  NOT NULL,
    record_ref  VARCHAR(40)  NOT NULL,
    action      VARCHAR(10)  NOT NULL,
    old_value   VARCHAR(255),
    new_value   VARCHAR(255),
    changed_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
CREATE INDEX idx_audit_table ON audit_log(table_name, changed_at);
