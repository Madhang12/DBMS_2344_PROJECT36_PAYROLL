"""Automated tests for Project 36.   Run from the project root:

    python -m unittest discover -s tests -v

Every test builds a fresh temporary SQLite database (schema + seed + demo
payroll), so nothing here touches instance/payroll.db.
"""
import re
import shutil
import sqlite3
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from app import auth, config, create_app, db as dbmod, dbinfo, payroll  # noqa: E402
import init_db  # noqa: E402

CFG = {"pf_rate": Decimal("0.12"), "pf_wage_ceiling": Decimal("15000"), "esi_rate": Decimal("0.0075"),
       "esi_gross_limit": Decimal("21000"), "pt_amount": Decimal("200"), "pt_gross_limit": Decimal("15000"),
       "tds_rate": Decimal("0.05"), "tds_monthly_threshold": Decimal("50000")}


class CalcTests(unittest.TestCase):
    """Pure calculation checks with hand-computed expected values."""

    def test_high_salary_with_lop_loan_and_manual_deduction(self):
        r = payroll.calculate(
            dict(basic_salary=30000, hra=12000, da=3000, special_allowance=6000),
            dict(working_days=20, days_present=19, paid_leave_days=0), 5000, 800,
            [dict(loan_id=1, emi_amount=5000, outstanding_balance=60000)], CFG)
        self.assertEqual(r["lop_amount"], Decimal("2550.00"))      # 51000/20 * 1 day
        self.assertEqual(r["gross_salary"], Decimal("53450.00"))   # 51000 - 2550 + 5000
        self.assertEqual(r["pf"], Decimal("1800.00"))              # 12% of min(30000, 15000)
        self.assertEqual(r["esi"], Decimal("0.00"))                # gross > 21000
        self.assertEqual(r["pt"], Decimal("200.00"))
        self.assertEqual(r["tds"], Decimal("172.50"))              # 5% of (53450 - 50000)
        self.assertEqual(r["total_deductions"], Decimal("7972.50"))
        self.assertEqual(r["net_salary"], Decimal("45477.50"))

    def test_low_salary_gets_esi_but_no_tds(self):
        r = payroll.calculate(
            dict(basic_salary=10000, hra=4000, da=1000, special_allowance=2000),
            dict(working_days=22, days_present=22, paid_leave_days=0), 0, 0, [], CFG)
        self.assertEqual(r["gross_salary"], Decimal("17000.00"))
        self.assertEqual(r["pf"], Decimal("1200.00"))
        self.assertEqual(r["esi"], Decimal("127.50"))
        self.assertEqual(r["tds"], Decimal("0.00"))
        self.assertEqual(r["net_salary"], Decimal("15472.50"))

    def test_loan_emi_never_exceeds_outstanding_balance(self):
        r = payroll.calculate(
            dict(basic_salary=20000, hra=8000, da=2000, special_allowance=4000),
            dict(working_days=20, days_present=20, paid_leave_days=0), 0, 0,
            [dict(loan_id=1, emi_amount=5000, outstanding_balance=1200)], CFG)
        self.assertEqual(r["loan_deductions"], Decimal("1200.00"))

    def test_paid_leave_is_not_loss_of_pay(self):
        r = payroll.calculate(
            dict(basic_salary=20000, hra=0, da=0, special_allowance=0),
            dict(working_days=20, days_present=18, paid_leave_days=2), 0, 0, [], CFG)
        self.assertEqual(r["lop_amount"], Decimal("0.00"))

    def test_changing_config_changes_result(self):
        cfg = dict(CFG, pf_rate=Decimal("0"))
        r = payroll.calculate(dict(basic_salary=30000, hra=0, da=0, special_allowance=0),
                              dict(working_days=20, days_present=20, paid_leave_days=0), 0, 0, [], cfg)
        self.assertEqual(r["pf"], Decimal("0.00"))


class AppTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.path = str(self.tmp / "test.db")
        config.SQLITE_PATH = self.path
        config.DB_BACKEND = "sqlite"
        auth.ITERATIONS = 1000                      # fast password hashing for tests
        init_db.init("sqlite", self.path, quiet=True)
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["CSRF_ENABLED"] = False     # the CSRF test switches it back on
        self.client = self.app.test_client()

    def login(self, username="admin", password=None, client=None):
        client = client or self.client
        return client.post("/login", data={"username": username, "password": password or auth.DEMO_PASSWORD})

    def tearDown(self):
        for c in getattr(self, "_conns", []):
            c.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def db(self):
        conn = dbmod.connect("sqlite", self.path)
        self._conns = getattr(self, "_conns", []) + [conn]
        return conn


class DatabaseTests(AppTestBase):
    def test_all_tables_exist(self):
        d = self.db()
        names = {r["name"] for r in d.all("SELECT name FROM sqlite_master WHERE type='table'")}
        for t in ["department", "designation", "employee", "salary_structure", "attendance_summary", "earnings",
                  "deductions", "loan", "loan_repayment", "payroll_period", "payroll_detail", "payslip",
                  "bank_transfer", "payroll_config", "app_user", "audit_log"]:
            self.assertIn(t, names)

    def test_seed_counts(self):
        d = self.db()
        self.assertEqual(d.scalar("SELECT COUNT(*) FROM employee"), 30)
        self.assertEqual(d.scalar("SELECT COUNT(*) FROM department"), 6)
        self.assertEqual(d.scalar("SELECT COUNT(*) FROM payroll_period"), 3)

    def test_foreign_key_rejects_bad_department(self):
        d = self.db()
        with self.assertRaises(sqlite3.IntegrityError):
            d.run("INSERT INTO employee (emp_code, first_name, last_name, email, date_of_joining, department_id, designation_id) "
                  "VALUES ('X1','A','B','x1@example.com','2026-01-01',99,1)")

    def test_unique_emp_code(self):
        d = self.db()
        with self.assertRaises(sqlite3.IntegrityError):
            d.run("INSERT INTO employee (emp_code, first_name, last_name, email, date_of_joining, department_id, designation_id) "
                  "VALUES ('EMP001','A','B','dup@example.com','2026-01-01',1,1)")

    def test_check_negative_salary(self):
        d = self.db()
        with self.assertRaises(sqlite3.IntegrityError):
            d.run("UPDATE salary_structure SET basic_salary = -5 WHERE employee_id = 1")

    def test_check_attendance_total(self):
        d = self.db()
        with self.assertRaises(sqlite3.IntegrityError):
            d.run("UPDATE attendance_summary SET days_present = 40 WHERE attendance_id = 1")

    def test_one_salary_structure_per_employee(self):
        d = self.db()
        with self.assertRaises(sqlite3.IntegrityError):
            d.run("INSERT INTO salary_structure (employee_id, basic_salary, effective_from) VALUES (1, 1000, '2026-01-01')")

    def test_restrict_delete_employee_with_payroll(self):
        d = self.db()
        with self.assertRaises(sqlite3.IntegrityError):
            d.run("DELETE FROM employee WHERE employee_id = 1")

    def test_queries_sql_runs_completely(self):
        """Every statement in database/queries.sql executes without error."""
        copy = self.tmp / "copy.db"
        shutil.copy(self.path, copy)
        conn = sqlite3.connect(copy)
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript((ROOT / "database" / "queries.sql").read_text())
        conn.close()


class PayrollProcessingTests(AppTestBase):
    def test_demo_periods_processed_and_paid(self):
        d = self.db()
        st = {r["payroll_period_id"]: r["status"] for r in d.all("SELECT * FROM payroll_period")}
        self.assertEqual(st, {1: "PAID", 2: "PAID", 3: "OPEN"})
        self.assertEqual(d.scalar("SELECT COUNT(*) FROM employee WHERE status='ACTIVE'"), 29)
        self.assertEqual(d.scalar("SELECT COUNT(*) FROM payroll_detail WHERE payroll_period_id=1"), 29)

    def test_net_equals_gross_minus_deductions_for_every_row(self):
        d = self.db()
        bad = d.scalar("SELECT COUNT(*) FROM payroll_detail WHERE ABS(gross_salary - total_deductions - net_salary) >= 0.01")
        self.assertEqual(bad, 0)

    def test_itemised_deductions_match_totals(self):
        d = self.db()
        bad = d.scalar("SELECT COUNT(*) FROM payroll_detail p WHERE ABS(p.total_deductions - "
                       "(SELECT COALESCE(SUM(amount),0) FROM deductions x WHERE x.employee_id=p.employee_id "
                       "AND x.payroll_period_id=p.payroll_period_id)) >= 0.01")
        self.assertEqual(bad, 0)

    def test_process_october_end_to_end(self):
        d = self.db()
        before = d.scalar("SELECT outstanding_balance FROM loan WHERE loan_id=6")     # starts in October
        self.assertEqual(before, 90000)
        res = payroll.process_period(d, 3)
        self.assertEqual(res["processed"], 29)
        self.assertEqual(d.scalar("SELECT status FROM payroll_period WHERE payroll_period_id=3"), "PROCESSED")
        self.assertEqual(d.scalar("SELECT COUNT(*) FROM payslip ps JOIN payroll_detail p ON p.payroll_id=ps.payroll_id "
                                  "WHERE p.payroll_period_id=3"), 29)
        self.assertEqual(d.scalar("SELECT outstanding_balance FROM loan WHERE loan_id=6"), 82500)   # 90000 - 7500 EMI
        self.assertEqual(d.scalar("SELECT COUNT(*) FROM loan_repayment WHERE loan_id=6"), 1)

    def test_cannot_process_twice(self):
        d = self.db()
        payroll.process_period(d, 3)
        with self.assertRaises(ValueError):
            payroll.process_period(d, 3)

    def test_inactive_employee_is_skipped(self):
        d = self.db()
        payroll.process_period(d, 3)
        self.assertEqual(d.scalar("SELECT COUNT(*) FROM payroll_detail p JOIN employee e ON e.employee_id=p.employee_id "
                                  "WHERE e.status='INACTIVE'"), 0)

    def test_missing_attendance_is_skipped_and_reported(self):
        d = self.db()
        d.run("DELETE FROM attendance_summary WHERE employee_id=5 AND payroll_period_id=3")
        d.commit()
        res = payroll.process_period(d, 3)
        self.assertEqual(res["processed"], 28)
        self.assertEqual(res["skipped"][0][0], "EMP005")

    def test_bank_transfer_flow(self):
        d = self.db()
        payroll.process_period(d, 3)
        with self.assertRaises(ValueError):                       # cannot pay before records exist
            payroll.mark_transfers_paid(d, 3)
        self.assertEqual(payroll.create_bank_transfers(d, 3), 29)
        self.assertEqual(payroll.create_bank_transfers(d, 3), 0)  # idempotent
        self.assertEqual(payroll.mark_transfers_paid(d, 3), 29)
        self.assertEqual(d.scalar("SELECT status FROM payroll_period WHERE payroll_period_id=3"), "PAID")
        self.assertEqual(d.scalar("SELECT COUNT(*) FROM bank_transfer WHERE status='SUCCESS'"), 87)
        self.assertEqual(d.scalar("SELECT COUNT(*) FROM bank_transfer b JOIN payroll_detail p ON p.payroll_id=b.payroll_id "
                                  "WHERE ABS(b.amount - p.net_salary) >= 0.01"), 0)

    def test_failed_processing_rolls_back(self):
        d = self.db()
        # make one employee's deductions exceed gross -> whole run must roll back
        d.run("UPDATE loan SET emi_amount=10000000, loan_amount=20000000, outstanding_balance=20000000 WHERE loan_id=6")
        d.commit()
        with self.assertRaises(ValueError):
            payroll.process_period(d, 3)
        self.assertEqual(d.scalar("SELECT COUNT(*) FROM payroll_detail WHERE payroll_period_id=3"), 0)
        self.assertEqual(d.scalar("SELECT status FROM payroll_period WHERE payroll_period_id=3"), "OPEN")


class WebTests(AppTestBase):
    def setUp(self):
        super().setUp()
        self.login("admin")

    PAGES = ["/", "/manage/employees/", "/manage/departments/", "/manage/designations/", "/manage/salary-structures/",
             "/manage/attendance/", "/manage/earnings/", "/manage/deductions/", "/manage/loans/", "/periods",
             "/payroll", "/payroll/export.csv", "/transfers", "/reports", "/settings", "/employees/1", "/loans/1",
             "/payslips/1", "/manage/employees/new", "/manage/employees/1/edit", "/database", "/admin/users",
             "/account/password"]

    def test_all_pages_load(self):
        for u in self.PAGES:
            with self.subTest(page=u):
                self.assertEqual(self.client.get(u).status_code, 200)

    def test_unknown_page_404(self):
        self.assertEqual(self.client.get("/manage/nothing/").status_code, 404)

    def test_employee_crud(self):
        form = dict(emp_code="EMP777", first_name="Test", last_name="Person", email="emp777@example.com", phone="9000077777",
                    date_of_joining="2026-10-01", department_id="1", designation_id="3", status="ACTIVE")
        r = self.client.post("/manage/employees/new", data=form, follow_redirects=True)
        self.assertIn(b"Employee added", r.data)
        d = self.db()
        eid = d.scalar("SELECT employee_id FROM employee WHERE emp_code='EMP777'")
        self.assertIsNotNone(eid)
        form["first_name"] = "Changed"
        r = self.client.post(f"/manage/employees/{eid}/edit", data=form, follow_redirects=True)
        self.assertIn(b"Employee updated", r.data)
        self.assertEqual(d.scalar("SELECT first_name FROM employee WHERE employee_id=?", (eid,)), "Changed")
        r = self.client.post(f"/manage/employees/{eid}/delete", follow_redirects=True)
        self.assertIn(b"Employee deleted", r.data)
        self.assertIsNone(d.scalar("SELECT employee_id FROM employee WHERE emp_code='EMP777'"))

    def test_duplicate_employee_code_shows_friendly_error(self):
        form = dict(emp_code="EMP001", first_name="Dup", last_name="X", email="dupx@example.com",
                    date_of_joining="2026-10-01", department_id="1", designation_id="3", status="ACTIVE")
        r = self.client.post("/manage/employees/new", data=form, follow_redirects=True)
        self.assertIn(b"database rule was violated", r.data)

    def test_required_field_validation(self):
        r = self.client.post("/manage/employees/new", data=dict(emp_code=""), follow_redirects=True)
        self.assertIn(b"is required", r.data)

    def test_delete_employee_with_payroll_is_blocked(self):
        r = self.client.post("/manage/employees/1/delete", follow_redirects=True)
        self.assertIn(b"Cannot delete", r.data)
        self.assertEqual(self.db().scalar("SELECT COUNT(*) FROM employee WHERE employee_id=1"), 1)

    def test_delete_department_with_employees_is_blocked(self):
        r = self.client.post("/manage/departments/1/delete", follow_redirects=True)
        self.assertIn(b"Cannot delete", r.data)

    def test_department_and_designation_crud(self):
        r = self.client.post("/manage/departments/new", data=dict(department_name="Legal", location="Delhi"), follow_redirects=True)
        self.assertIn(b"Department added", r.data)
        r = self.client.post("/manage/designations/new", data=dict(title="Principal", grade_level="9"), follow_redirects=True)
        self.assertIn(b"Designation added", r.data)
        r = self.client.post("/manage/designations/new", data=dict(title="Bad", grade_level="99"), follow_redirects=True)
        self.assertIn(b"database rule was violated", r.data)

    def test_locked_period_rejects_new_earning(self):
        r = self.client.post("/manage/earnings/new", data=dict(employee_id="1", payroll_period_id="1", earning_type="Bonus",
                                                               amount="100"), follow_redirects=True)
        self.assertIn(b"already processed", r.data)

    def test_open_period_accepts_earning_and_it_reaches_payslip(self):
        r = self.client.post("/manage/earnings/new", data=dict(employee_id="2", payroll_period_id="3", earning_type="Bonus",
                                                               amount="1234", remarks="test"), follow_redirects=True)
        self.assertIn(b"Earning added", r.data)
        self.client.post("/periods/3/process", follow_redirects=True)
        slip = self.db().scalar("SELECT ps.payslip_id FROM payslip ps JOIN payroll_detail p ON p.payroll_id=ps.payroll_id "
                                "WHERE p.employee_id=2 AND p.payroll_period_id=3")
        page = self.client.get(f"/payslips/{slip}").data
        self.assertIn(b"1,234.00", page)

    def test_auto_deduction_rows_are_read_only(self):
        auto_id = self.db().scalar("SELECT deduction_id FROM deductions WHERE source='AUTO' LIMIT 1")
        r = self.client.post(f"/manage/deductions/{auto_id}/delete", follow_redirects=True)
        self.assertIn(b"cannot be deleted", r.data)

    def test_process_via_web_then_double_process_is_refused(self):
        r = self.client.post("/periods/3/process", follow_redirects=True)
        self.assertIn(b"Payroll processed for 29 employees", r.data)
        r = self.client.post("/periods/3/process", follow_redirects=True)
        self.assertIn(b"cannot be processed again", r.data)

    def test_period_creation_and_duplicate(self):
        r = self.client.post("/periods", data=dict(period_month="11", period_year="2026"), follow_redirects=True)
        self.assertIn(b"November 2026 created", r.data)
        r = self.client.post("/periods", data=dict(period_month="11", period_year="2026"), follow_redirects=True)
        self.assertIn(b"already exists", r.data)

    def test_manual_loan_repayment(self):
        r = self.client.post("/loans/6", data=dict(amount="10000"), follow_redirects=True)
        self.assertIn(b"Manual repayment recorded", r.data)
        self.assertEqual(self.db().scalar("SELECT outstanding_balance FROM loan WHERE loan_id=6"), 80000)
        r = self.client.post("/loans/6", data=dict(amount="999999"), follow_redirects=True)
        self.assertIn(b"not exceed", r.data)

    def test_settings_change_applies_to_next_processing(self):
        d = self.db()
        self.client.post("/settings", data={r["config_key"]: ("0" if r["config_key"] == "pf_rate" else str(r["config_value"]))
                                            for r in d.all("SELECT * FROM payroll_config")}, follow_redirects=True)
        self.client.post("/periods/3/process", follow_redirects=True)
        pf = d.scalar("SELECT COUNT(*) FROM deductions WHERE payroll_period_id=3 AND deduction_type LIKE 'Provident%'")
        self.assertEqual(pf, 0)

    def test_csv_export(self):
        r = self.client.get("/payroll/export.csv?period=1")
        self.assertEqual(r.mimetype, "text/csv")
        self.assertEqual(len(r.data.decode().strip().splitlines()), 30)   # header + 29 rows

    def test_reports_page_has_all_seven_reports_with_data(self):
        page = self.client.get("/reports?period=2").data.decode()
        self.assertEqual(len(re.findall(r'class="sql"', page)), 7)
        self.assertIn("Department-wise payroll cost", page)


class AuthTests(AppTestBase):
    """Login, roles, CSRF and password handling."""

    def payslip_id(self, employee_id):
        return self.db().scalar("SELECT ps.payslip_id FROM payslip ps JOIN payroll_detail p ON p.payroll_id = ps.payroll_id "
                                "WHERE p.employee_id = ? ORDER BY ps.payslip_id LIMIT 1", (employee_id,))

    def test_anonymous_is_redirected_to_login(self):
        for url in ["/", "/manage/employees/", "/payroll", "/database", "/payslips/1"]:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302, url)
            self.assertIn("/login", r.headers["Location"])
        self.assertEqual(self.client.get("/login").status_code, 200)

    def test_wrong_password_and_unknown_user_are_rejected(self):
        self.assertEqual(self.login("admin", "not-the-password").status_code, 200)
        self.assertEqual(self.client.get("/").status_code, 302)       # still anonymous
        self.assertEqual(self.login("nobody").status_code, 200)

    def test_passwords_are_stored_hashed(self):
        for r in self.db().all("SELECT password_hash FROM app_user"):
            self.assertTrue(r["password_hash"].startswith("pbkdf2:sha256:"))
            self.assertNotIn(auth.DEMO_PASSWORD, r["password_hash"])

    def test_login_throttle_after_repeated_failures(self):
        for _ in range(5):
            self.login("hr", "wrong-password")
        self.assertEqual(self.login("hr").status_code, 429)           # even the right password is refused for a while

    def test_admin_can_open_everything(self):
        self.login("admin")
        for url in ["/", "/settings", "/database", "/admin/users", "/periods", "/reports"]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_hr_cannot_open_admin_pages(self):
        self.login("hr")
        for url in ["/settings", "/database", "/admin/users"]:
            self.assertEqual(self.client.get(url).status_code, 403, url)
        for url in ["/", "/manage/employees/", "/periods", "/payroll", "/reports"]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_employee_sees_only_own_payslips(self):
        r = self.login("emp003")
        self.assertTrue(r.headers["Location"].endswith("/me"))
        self.assertEqual(self.client.get("/me").status_code, 200)
        self.assertEqual(self.client.get("/payslips/%d" % self.payslip_id(3)).status_code, 200)
        self.assertEqual(self.client.get("/payslips/%d" % self.payslip_id(4)).status_code, 403)
        for url in ["/manage/employees/", "/payroll", "/employees/3", "/reports", "/periods", "/settings", "/database"]:
            self.assertEqual(self.client.get(url).status_code, 403, url)
        self.assertEqual(self.client.get("/").status_code, 302)       # dashboard sends employees to /me

    def test_employee_cannot_post_to_management_endpoints(self):
        self.login("emp003")
        self.assertEqual(self.client.post("/periods/3/process").status_code, 403)
        self.assertEqual(self.client.post("/manage/employees/1/delete").status_code, 403)

    def test_csrf_token_is_required_for_posts(self):
        self.app.config["CSRF_ENABLED"] = True
        c = self.app.test_client()
        self.assertEqual(c.post("/login", data={"username": "admin", "password": auth.DEMO_PASSWORD}).status_code, 400)
        token = re.search(rb'name="csrf_token" value="(\w+)"', c.get("/login").data).group(1).decode()
        r = c.post("/login", data={"username": "admin", "password": auth.DEMO_PASSWORD, "csrf_token": token})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(c.post("/periods/3/process").status_code, 400)   # logged in, but no token

    def test_change_password(self):
        self.login("hr")
        bad = self.client.post("/account/password", data={"current_password": "wrong", "new_password": "NewPass#123", "confirm_password": "NewPass#123"})
        self.assertEqual(bad.status_code, 200)
        short = self.client.post("/account/password", data={"current_password": auth.DEMO_PASSWORD, "new_password": "abc", "confirm_password": "abc"})
        self.assertEqual(short.status_code, 200)
        ok = self.client.post("/account/password", data={"current_password": auth.DEMO_PASSWORD, "new_password": "NewPass#123", "confirm_password": "NewPass#123"})
        self.assertEqual(ok.status_code, 302)
        other = self.app.test_client()
        self.assertEqual(self.login("hr", auth.DEMO_PASSWORD, other).status_code, 200)    # old password no longer works
        self.assertEqual(self.login("hr", "NewPass#123", other).status_code, 302)

    def test_admin_creates_user_and_duplicates_are_refused(self):
        self.login("admin")
        r = self.client.post("/admin/users/new", data={"username": "auditor", "role": "HR", "password": "LongEnough1"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.db().scalar("SELECT role FROM app_user WHERE username='auditor'"), "HR")
        self.client.post("/admin/users/new", data={"username": "auditor", "role": "HR", "password": "LongEnough1"})
        self.assertEqual(self.db().scalar("SELECT COUNT(*) FROM app_user WHERE username='auditor'"), 1)
        self.client.post("/admin/users/new", data={"username": "ghost", "role": "EMPLOYEE", "password": "LongEnough1"})   # no employee linked
        self.assertEqual(self.db().scalar("SELECT COUNT(*) FROM app_user WHERE username='ghost'"), 0)

    def test_deactivated_user_cannot_sign_in_and_last_admin_is_protected(self):
        self.login("admin")
        hr_id = self.db().scalar("SELECT user_id FROM app_user WHERE username='hr'")
        self.client.post("/admin/users/%d/toggle" % hr_id)
        self.assertEqual(self.login("hr", client=self.app.test_client()).status_code, 200)    # login page again, not a redirect
        admin_id = self.db().scalar("SELECT user_id FROM app_user WHERE username='admin'")
        self.client.post("/admin/users/%d/toggle" % admin_id)
        self.assertEqual(self.db().scalar("SELECT is_active FROM app_user WHERE username='admin'"), 1)

    def test_user_table_constraints(self):
        d = self.db()
        with self.assertRaises(sqlite3.IntegrityError):                # EMPLOYEE role needs an employee
            d.run("INSERT INTO app_user (username, password_hash, role) VALUES ('x1', 'h', 'EMPLOYEE')")
        with self.assertRaises(sqlite3.IntegrityError):                # role must be one of the three
            d.run("INSERT INTO app_user (username, password_hash, role) VALUES ('x2', 'h', 'BOSS')")


class PasswordResetTests(AppTestBase):
    def request_link(self, username="emp001", client=None):
        c = client or self.client
        r = c.post("/forgot-password", data={"username": username})
        self.assertEqual(r.status_code, 200)
        m = re.search(rb'href="(http://[^"]+/reset-password/[^"]+)"', r.data)
        return (m.group(1).decode().split("localhost")[-1] if m else None), r

    def test_forgot_page_is_public_and_known_user_gets_a_link(self):
        self.assertEqual(self.client.get("/forgot-password").status_code, 200)
        link, r = self.request_link("emp001")
        self.assertIsNotNone(link)
        self.assertIn(b"If that username exists", r.data)

    def test_unknown_and_inactive_users_get_the_same_message_but_no_link(self):
        link, r = self.request_link("nobody")
        self.assertIsNone(link)
        self.assertIn(b"If that username exists", r.data)
        d = self.db(); d.run("UPDATE app_user SET is_active=0 WHERE username='emp002'"); d.commit()
        link, r = self.request_link("emp002")
        self.assertIsNone(link)
        self.assertIn(b"If that username exists", r.data)

    def test_reset_link_changes_the_password_and_works_only_once(self):
        link, _ = self.request_link("emp001")
        self.assertEqual(self.client.get(link).status_code, 200)
        r = self.client.post(link, data={"new_password": "Brand-new-pass1", "confirm_password": "Brand-new-pass1"})
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.headers["Location"])
        self.assertEqual(self.login("emp001", "Brand-new-pass1").status_code, 302)       # new password works
        self.client.post("/logout")
        self.assertEqual(self.login("emp001").status_code, 200)                          # old one is refused
        self.assertEqual(self.client.get(link).status_code, 400)                         # link is now dead
        self.assertIn(b"already have been used", self.client.get(link).data)

    def test_reset_rejects_weak_or_mismatched_passwords(self):
        link, _ = self.request_link("emp001")
        r = self.client.post(link, data={"new_password": "short", "confirm_password": "short"})
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"at least 8", r.data)
        r = self.client.post(link, data={"new_password": "Longenough1", "confirm_password": "Different12"})
        self.assertIn(b"do not match", r.data)
        self.assertEqual(self.login("emp001").status_code, 302)                          # still the old password

    def test_tampered_and_expired_links_are_refused(self):
        link, _ = self.request_link("emp001")
        self.assertEqual(self.client.get(link[:-3] + "abc").status_code, 400)
        self.assertEqual(self.client.get("/reset-password/not-a-token").status_code, 400)
        old = config.RESET_TOKEN_MINUTES
        try:
            config.RESET_TOKEN_MINUTES = -1                                              # everything is expired
            r = self.client.get(link)
            self.assertEqual(r.status_code, 400)
            self.assertIn(b"has expired", r.data)
        finally:
            config.RESET_TOKEN_MINUTES = old

    def test_link_is_not_shown_when_demo_mode_is_off(self):
        self.app.config["SHOW_RESET_LINK"] = False
        link, r = self.request_link("emp001")
        self.assertIsNone(link)
        self.assertIn(b"If that username exists", r.data)

    def test_reset_requests_are_throttled(self):
        for _ in range(5):
            self.client.post("/forgot-password", data={"username": "emp001"})
        r = self.client.post("/forgot-password", data={"username": "emp001"})
        self.assertEqual(r.status_code, 429)


class AmountInWordsTests(unittest.TestCase):
    def test_indian_system(self):
        from app.numwords import rupees_in_words as w
        self.assertEqual(w(0), "Rupees Zero Only")
        self.assertEqual(w(100000), "Rupees One Lakh Only")
        self.assertEqual(w(100130), "Rupees One Lakh One Hundred Thirty Only")
        self.assertEqual(w(90623.5), "Rupees Ninety Thousand Six Hundred Twenty Three and Fifty Paise Only")
        self.assertEqual(w(12345678.9),
                         "Rupees One Crore Twenty Three Lakh Forty Five Thousand Six Hundred Seventy Eight and Ninety Paise Only")
        self.assertEqual(w("abc"), "")

    def test_payslip_shows_amount_in_words(self):
        # covered end-to-end in WebTests; here just check the Jinja filter is registered
        from app import create_app
        self.assertIn("inr_words", create_app().jinja_env.filters)


class TriggerAndViewTests(AppTestBase):
    """Database-level protection (triggers), audit trail and reporting views."""

    def test_triggers_and_views_exist(self):
        d = self.db()
        trig = {r["name"] for r in d.all("SELECT name FROM sqlite_master WHERE type='trigger'")}
        self.assertEqual(len(trig), 6)
        views = {r["name"] for r in d.all("SELECT name FROM sqlite_master WHERE type='view'")}
        self.assertEqual(views, {"v_payroll_summary", "v_department_cost", "v_loan_ledger"})

    def test_paid_payroll_cannot_be_updated_or_deleted(self):
        d = self.db()
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            d.run("UPDATE payroll_detail SET net_salary = 1 WHERE payroll_id = 1")
        self.assertIn("locked", str(cm.exception))
        with self.assertRaises(sqlite3.IntegrityError):
            d.run("DELETE FROM payroll_detail WHERE payroll_id = 1")

    def test_cannot_insert_payroll_into_a_closed_period(self):
        d = self.db()
        with self.assertRaises(sqlite3.IntegrityError):
            d.run("INSERT INTO payroll_detail (employee_id, payroll_period_id, basic_salary, hra, da, special_allowance, working_days, "
                  "lop_days, lop_amount, other_earnings, gross_salary, statutory_deductions, loan_deductions, other_deductions, "
                  "total_deductions, net_salary, processed_on) VALUES (30, 1, 1,1,1,1, 20,0,0,0, 4,0,0,0, 0,4, '2026-01-01')")

    def test_salary_change_is_audited(self):
        d = self.db()
        d.run("UPDATE salary_structure SET basic_salary = basic_salary + 500 WHERE employee_id = 2")
        d.commit()
        row = d.one("SELECT * FROM audit_log WHERE table_name='salary_structure'")
        self.assertEqual(row["record_ref"], "2")
        self.assertIn("basic=", row["old_value"])
        self.assertNotEqual(row["old_value"], row["new_value"])

    def test_status_and_rate_changes_are_audited_but_unchanged_values_are_not(self):
        d = self.db()
        d.run("UPDATE employee SET status='INACTIVE' WHERE emp_code='EMP002'")
        d.run("UPDATE payroll_config SET config_value = 0.10 WHERE config_key='pf_rate'")
        d.run("UPDATE employee SET phone='9000099999' WHERE emp_code='EMP002'")         # not an audited column
        d.commit()
        rows = d.all("SELECT table_name, record_ref FROM audit_log ORDER BY audit_id")
        self.assertEqual([(r["table_name"], r["record_ref"]) for r in rows], [("employee", "EMP002"), ("payroll_config", "pf_rate")])

    def test_views_agree_with_base_tables(self):
        d = self.db()
        self.assertEqual(d.scalar("SELECT SUM(total_net) FROM v_department_cost WHERE payroll_period_id = 1"),
                         d.scalar("SELECT SUM(net_salary) FROM payroll_detail WHERE payroll_period_id = 1"))
        self.assertEqual(d.scalar("SELECT COUNT(*) FROM v_payroll_summary"), d.scalar("SELECT COUNT(*) FROM payroll_detail"))
        ledger = d.one("SELECT * FROM v_loan_ledger WHERE loan_id = 1")
        self.assertEqual(round(ledger["loan_amount"] - ledger["repaid_through_payroll"], 2), round(ledger["outstanding_balance"], 2))


class ExplorerTests(AppTestBase):
    """Database Explorer introspection and the read-only SQL console."""

    def test_introspection_lists_schema_objects(self):
        info = dbinfo.introspect(self.db())
        self.assertEqual(len(info["tables"]), 16)
        emp = next(t for t in info["tables"] if t["name"] == "employee")
        self.assertEqual(emp["rows"], 30)
        self.assertEqual({f["ref_table"] for f in emp["fks"]}, {"department", "designation"})
        self.assertEqual(len(info["triggers"]), 6)

    def test_console_runs_select(self):
        cols, rows, truncated = dbinfo.run_console("SELECT COUNT(*) AS n FROM employee")
        self.assertEqual((cols, rows, truncated), (["n"], [[30]], False))

    def test_console_refuses_writes_and_secrets(self):
        for q in ["DELETE FROM employee", "UPDATE employee SET status='X'", "DROP TABLE employee", "SELECT 1; DELETE FROM employee",
                  "PRAGMA foreign_keys", "SELECT * FROM app_user", "INSERT INTO department (department_name) VALUES ('x')"]:
            with self.assertRaises(dbinfo.ConsoleError, msg=q):
                dbinfo.run_console(q)
        self.assertEqual(self.db().scalar("SELECT COUNT(*) FROM employee"), 30)

    def test_console_connection_is_really_read_only(self):
        """The console opens the database with mode=ro, so even a write that slipped past the text filter would fail."""
        conn = sqlite3.connect(Path(self.path).resolve().as_uri() + "?mode=ro", uri=True)
        try:
            with self.assertRaises(sqlite3.OperationalError):
                conn.execute("DELETE FROM employee")
        finally:
            conn.close()
        with self.assertRaises(dbinfo.ConsoleError):
            dbinfo.run_console("SELECT * FROM no_such_table")             # SQL errors become friendly messages
        self.assertEqual(self.db().scalar("SELECT COUNT(*) FROM employee"), 30)

    def test_console_row_limit(self):
        cols, rows, truncated = dbinfo.run_console("SELECT * FROM deductions")        # 171 rows < 200
        self.assertFalse(truncated)
        cols, rows, truncated = dbinfo.run_console("WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i+1 FROM n WHERE i < 500) SELECT i FROM n")
        self.assertTrue(truncated)
        self.assertEqual(len(rows), 200)

    def test_explorer_page_via_web(self):
        self.login("admin")
        r = self.client.post("/database", data={"sql": "SELECT emp_code FROM employee ORDER BY emp_code LIMIT 3"})
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"EMP001", r.data)
        r = self.client.post("/database", data={"sql": "DELETE FROM employee"})
        self.assertIn(b"read-only", r.data)
        self.assertEqual(self.db().scalar("SELECT COUNT(*) FROM employee"), 30)


if __name__ == "__main__":
    unittest.main(verbosity=2)
