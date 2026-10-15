-- SQLite triggers. Loaded after schema, seed and views.
-- Two jobs: (1) lock payroll history once a period is no longer OPEN, (2) write an audit trail.

CREATE TRIGGER trg_payroll_detail_lock_insert BEFORE INSERT ON payroll_detail
FOR EACH ROW
WHEN (SELECT status FROM payroll_period WHERE payroll_period_id = NEW.payroll_period_id) <> 'OPEN'
BEGIN
  SELECT RAISE(ABORT, 'Payroll history is locked: the period is no longer OPEN');
END;

CREATE TRIGGER trg_payroll_detail_lock_update BEFORE UPDATE ON payroll_detail
FOR EACH ROW
WHEN (SELECT status FROM payroll_period WHERE payroll_period_id = OLD.payroll_period_id) <> 'OPEN'
BEGIN
  SELECT RAISE(ABORT, 'Payroll history is locked: the period is no longer OPEN');
END;

CREATE TRIGGER trg_payroll_detail_lock_delete BEFORE DELETE ON payroll_detail
FOR EACH ROW
WHEN (SELECT status FROM payroll_period WHERE payroll_period_id = OLD.payroll_period_id) <> 'OPEN'
BEGIN
  SELECT RAISE(ABORT, 'Payroll history is locked: the period is no longer OPEN');
END;

CREATE TRIGGER trg_salary_update_audit AFTER UPDATE ON salary_structure
FOR EACH ROW
WHEN OLD.basic_salary <> NEW.basic_salary OR OLD.hra <> NEW.hra OR OLD.da <> NEW.da
     OR OLD.special_allowance <> NEW.special_allowance
BEGIN
  INSERT INTO audit_log (table_name, record_ref, action, old_value, new_value)
  VALUES ('salary_structure', NEW.employee_id, 'UPDATE',
          'basic=' || OLD.basic_salary || ', hra=' || OLD.hra || ', da=' || OLD.da || ', special=' || OLD.special_allowance,
          'basic=' || NEW.basic_salary || ', hra=' || NEW.hra || ', da=' || NEW.da || ', special=' || NEW.special_allowance);
END;

CREATE TRIGGER trg_employee_status_audit AFTER UPDATE ON employee
FOR EACH ROW
WHEN OLD.status <> NEW.status
BEGIN
  INSERT INTO audit_log (table_name, record_ref, action, old_value, new_value)
  VALUES ('employee', NEW.emp_code, 'UPDATE', 'status=' || OLD.status, 'status=' || NEW.status);
END;

CREATE TRIGGER trg_config_audit AFTER UPDATE ON payroll_config
FOR EACH ROW
WHEN OLD.config_value <> NEW.config_value
BEGIN
  INSERT INTO audit_log (table_name, record_ref, action, old_value, new_value)
  VALUES ('payroll_config', NEW.config_key, 'UPDATE', OLD.config_value, NEW.config_value);
END;
