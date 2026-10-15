"""Integration tests against a REAL MySQL 8 server. Skipped unless enabled:

    export PAYROLL_MYSQL_TESTS=1 MYSQL_HOST=localhost MYSQL_USER=... MYSQL_PASSWORD=... MYSQL_DATABASE=payroll_test
    python -m unittest tests.test_mysql -v

WARNING: scripts/init_db.py DROPS every table in MYSQL_DATABASE - use a throw-away database.
The server needs log_bin_trust_function_creators=1 (or a SUPER user) so triggers can be created.
"""
import os
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

ENABLED = os.getenv("PAYROLL_MYSQL_TESTS") == "1"


@unittest.skipUnless(ENABLED, "set PAYROLL_MYSQL_TESTS=1 (and MYSQL_* variables) to run the MySQL tests")
class MySQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DB_BACKEND"] = "mysql"
        from app import auth, config, create_app, db as dbmod, dbinfo
        import init_db
        config.DB_BACKEND = "mysql"
        auth.ITERATIONS = 1000
        cls.auth, cls.dbmod, cls.dbinfo, cls.config = auth, dbmod, dbinfo, config
        init_db.init("mysql", quiet=True)
        cls.app = create_app()
        cls.app.config["CSRF_ENABLED"] = False
        cls.db = dbmod.connect("mysql")

    def setUp(self):
        self.db.commit()                       # start each test on a fresh snapshot (REPEATABLE READ)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_row_counts_and_periods(self):
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM employee"), 30)
        st = {r["payroll_period_id"]: r["status"] for r in self.db.all("SELECT * FROM payroll_period")}
        self.assertEqual(st, {1: "PAID", 2: "PAID", 3: "OPEN"})
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM payroll_detail"), 58)

    def test_payroll_totals_match_sqlite_results(self):
        self.assertEqual(str(self.db.scalar("SELECT SUM(net_salary) FROM payroll_detail WHERE payroll_period_id = 1")), "1836259.13")
        self.assertEqual(str(self.db.scalar("SELECT SUM(net_salary) FROM payroll_detail WHERE payroll_period_id = 2")), "1806179.32")

    def test_net_equals_gross_minus_deductions(self):
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM payroll_detail WHERE ROUND(gross_salary - total_deductions, 2) <> net_salary"), 0)

    def test_constraints_reject_bad_data(self):
        err = self.dbmod.integrity_errors()
        with self.assertRaises(err):
            self.db.run("INSERT INTO employee (emp_code, first_name, last_name, email, date_of_joining, department_id, designation_id) "
                        "VALUES ('EMP001','A','B','dup@example.com','2026-01-01',1,1)")
        self.db.rollback()
        with self.assertRaises(err):
            self.db.run("INSERT INTO employee (emp_code, first_name, last_name, email, date_of_joining, department_id, designation_id) "
                        "VALUES ('X1','A','B','x1@example.com','2026-01-01',99,1)")
        self.db.rollback()
        with self.assertRaises(err):
            self.db.run("UPDATE salary_structure SET basic_salary = -5 WHERE employee_id = 1")
        self.db.rollback()
        with self.assertRaises(err):
            self.db.run("DELETE FROM employee WHERE employee_id = 1")          # RESTRICT: has payroll history
        self.db.rollback()

    def test_trigger_locks_paid_payroll(self):
        err = self.dbmod.integrity_errors()
        with self.assertRaises(err) as cm:
            self.db.run("UPDATE payroll_detail SET net_salary = 1 WHERE payroll_id = 1")
        self.assertIn("locked", str(cm.exception))
        self.db.rollback()
        with self.assertRaises(err):
            self.db.run("DELETE FROM payroll_detail WHERE payroll_id = 1")
        self.db.rollback()

    def test_audit_trigger_and_views(self):
        self.db.run("UPDATE salary_structure SET basic_salary = basic_salary + 500 WHERE employee_id = 2")
        self.db.run("UPDATE salary_structure SET basic_salary = basic_salary - 500 WHERE employee_id = 2")
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM audit_log WHERE table_name='salary_structure' AND record_ref='2'"), 2)
        self.db.run("DELETE FROM audit_log WHERE table_name='salary_structure'")
        self.db.commit()
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM v_payroll_summary"), 58)
        self.assertEqual(len(self.db.all("SELECT * FROM v_department_cost WHERE payroll_period_id = 1")), 5)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM v_loan_ledger"), 6)

    def test_queries_sql_runs_completely(self):
        self.db.script((ROOT / "database" / "queries.sql").read_text())
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM employee"), 30)    # the file cleans up after itself

    def test_introspection_and_console(self):
        info = self.dbinfo.introspect(self.db)
        self.assertEqual(len(info["tables"]), 16)
        self.assertEqual(len(info["views"]), 3)
        self.assertEqual(len(info["triggers"]), 6)
        cols, rows, truncated = self.dbinfo.run_console("SELECT COUNT(*) AS n FROM employee")
        self.assertEqual(rows, [[30]])
        with self.assertRaises(self.dbinfo.ConsoleError):
            self.dbinfo.run_console("DELETE FROM employee")

    def test_web_login_and_pages(self):
        c = self.app.test_client()
        self.assertEqual(c.get("/").status_code, 302)
        r = c.post("/login", data={"username": "admin", "password": self.auth.DEMO_PASSWORD})
        self.assertEqual(r.status_code, 302)
        for url in ["/", "/manage/employees/", "/periods", "/payroll", "/transfers", "/reports", "/settings", "/database",
                    "/admin/users", "/payslips/1", "/loans/1", "/employees/1"]:
            self.assertEqual(c.get(url).status_code, 200, url)

    def test_web_rule_violations_show_friendly_messages(self):
        c = self.app.test_client()
        c.post("/login", data={"username": "admin", "password": self.auth.DEMO_PASSWORD})
        dup = dict(emp_code="EMP001", first_name="Dup", last_name="Test", email="dup@example.com", date_of_joining="2026-10-05",
                   department_id="1", designation_id="1", status="ACTIVE")
        r = c.post("/manage/employees/new", data=dup, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"database rule was violated", r.data)                     # UNIQUE
        neg = dict(employee_id="1", basic_salary="-5", hra="0", da="0", special_allowance="0", effective_from="2026-10-01")
        r = c.post("/manage/salary-structures/1/edit", data=neg, follow_redirects=True)
        self.assertEqual(r.status_code, 200)                                      # CHECK (MySQL error 3819) handled, no 500
        self.assertIn(b"database rule was violated", r.data)
        r = c.post("/manage/employees/1/delete", follow_redirects=True)
        self.assertIn(b"Cannot delete", r.data)                                   # RESTRICT

    def test_zz_process_october_through_the_app(self):  # runs last: it changes the data
        c = self.app.test_client()
        c.post("/login", data={"username": "hr", "password": self.auth.DEMO_PASSWORD})
        c.post("/periods/3/process")
        self.assertEqual(self.db.scalar("SELECT status FROM payroll_period WHERE payroll_period_id = 3"), "PROCESSED")
        self.db.commit()                                                    # refresh this connection's snapshot
        self.assertEqual(str(self.db.scalar("SELECT net_salary FROM payroll_detail p JOIN employee e ON e.employee_id = p.employee_id "
                                            "WHERE p.payroll_period_id = 3 AND e.emp_code = 'EMP003'")), "90623.50")


if __name__ == "__main__":
    unittest.main()
