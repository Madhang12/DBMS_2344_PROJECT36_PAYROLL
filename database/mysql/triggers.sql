-- MySQL 8 triggers. Loaded after schema, seed and views.
-- Blocks are separated by the line "-- @@" because trigger bodies contain semicolons
-- (scripts/init_db.py splits on it; in the mysql client use DELIMITER // instead).
-- Two jobs: (1) lock payroll history once a period is no longer OPEN, (2) write an audit trail.
-- NOTE: creating triggers with binary logging on needs the SUPER privilege or
-- log_bin_trust_function_creators=1 (see docs/SETUP.md).
-- @@
CREATE TRIGGER trg_payroll_detail_lock_insert BEFORE INSERT ON payroll_detail
FOR EACH ROW
BEGIN
  IF (SELECT status FROM payroll_period WHERE payroll_period_id = NEW.payroll_period_id) <> 'OPEN' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Payroll history is locked: the period is no longer OPEN';
  END IF;
END
-- @@
CREATE TRIGGER trg_payroll_detail_lock_update BEFORE UPDATE ON payroll_detail
FOR EACH ROW
BEGIN
  IF (SELECT status FROM payroll_period WHERE payroll_period_id = OLD.payroll_period_id) <> 'OPEN' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Payroll history is locked: the period is no longer OPEN';
  END IF;
END
-- @@
CREATE TRIGGER trg_payroll_detail_lock_delete BEFORE DELETE ON payroll_detail
FOR EACH ROW
BEGIN
  IF (SELECT status FROM payroll_period WHERE payroll_period_id = OLD.payroll_period_id) <> 'OPEN' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Payroll history is locked: the period is no longer OPEN';
  END IF;
END
-- @@
CREATE TRIGGER trg_salary_update_audit AFTER UPDATE ON salary_structure
FOR EACH ROW
BEGIN
  IF NOT (OLD.basic_salary <=> NEW.basic_salary AND OLD.hra <=> NEW.hra AND OLD.da <=> NEW.da
          AND OLD.special_allowance <=> NEW.special_allowance) THEN
    INSERT INTO audit_log (table_name, record_ref, action, old_value, new_value)
    VALUES ('salary_structure', NEW.employee_id, 'UPDATE',
            CONCAT('basic=', OLD.basic_salary, ', hra=', OLD.hra, ', da=', OLD.da, ', special=', OLD.special_allowance),
            CONCAT('basic=', NEW.basic_salary, ', hra=', NEW.hra, ', da=', NEW.da, ', special=', NEW.special_allowance));
  END IF;
END
-- @@
CREATE TRIGGER trg_employee_status_audit AFTER UPDATE ON employee
FOR EACH ROW
BEGIN
  IF OLD.status <> NEW.status THEN
    INSERT INTO audit_log (table_name, record_ref, action, old_value, new_value)
    VALUES ('employee', NEW.emp_code, 'UPDATE', CONCAT('status=', OLD.status), CONCAT('status=', NEW.status));
  END IF;
END
-- @@
CREATE TRIGGER trg_config_audit AFTER UPDATE ON payroll_config
FOR EACH ROW
BEGIN
  IF OLD.config_value <> NEW.config_value THEN
    INSERT INTO audit_log (table_name, record_ref, action, old_value, new_value)
    VALUES ('payroll_config', NEW.config_key, 'UPDATE', OLD.config_value, NEW.config_value);
  END IF;
END
