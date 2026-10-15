"""Capture real screenshots of the running application with headless Chromium.

    pip install playwright && playwright install chromium
    python scripts/capture_screenshots.py

It builds a throw-away database (instance data is untouched), starts the Flask
app on port 5055 and drives the real UI - including processing October 2026
payroll by clicking the button - saving PNGs to screenshots/.
"""
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import auth  # noqa: E402  (only for the demo password)

OUT = ROOT / "screenshots"
OUT.mkdir(exist_ok=True)
PORT = 5055
BASE = f"http://127.0.0.1:{PORT}"

tmp = Path(tempfile.mkdtemp()) / "shots.db"
env = dict(os.environ, DB_BACKEND="sqlite", SQLITE_PATH=str(tmp))
subprocess.run([sys.executable, str(ROOT / "scripts" / "init_db.py")], env=env, cwd=ROOT, check=True, capture_output=True)
server = subprocess.Popen([sys.executable, "-c", f"from app import create_app; create_app().run(port={PORT})"],
                          env=env, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(50):
    try:
        urllib.request.urlopen(BASE + "/", timeout=1)
        break
    except Exception:
        time.sleep(0.2)

from playwright.sync_api import sync_playwright  # noqa: E402

shots = []


def snap(page, name, full=False, selector=None):
    page.wait_for_timeout(700)               # let Chart.js animations finish
    path = OUT / f"{name}.png"
    if selector:
        page.locator(selector).first.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=full)
    shots.append(path.name)
    print("saved", path.name)


try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 810}, device_scale_factor=1.5)
        page.on("dialog", lambda d: d.accept())      # accept "are you sure?" confirms

        def go(path):
            page.goto(BASE + path)

        def sign_in(pg, user):
            pg.goto(BASE + "/login")
            pg.fill("#username", user)
            pg.fill("#password", auth.DEMO_PASSWORD)
            pg.click("button:has-text('Sign in')")
            pg.wait_for_load_state()

        # login page itself (before signing in), then sign in as the administrator
        go("/login");                                           snap(page, "28_login_page")
        # forgot-password: ask for a link (shown on screen in demo mode), then open it (not submitted)
        go("/forgot-password"); page.fill("#username", "emp003"); page.click("button:has-text('Create reset link')")
        snap(page, "36_forgot_password")
        page.goto(page.locator(".linkbox a").get_attribute("href")); snap(page, "37_reset_password")
        sign_in(page, "admin")

        go("/");                                                snap(page, "01_dashboard_before_october")
        go("/manage/employees/");                               snap(page, "02_employees_list")
        go("/employees/3");                                     snap(page, "03_employee_profile")
        # add employee (real insert), show flash, then delete it again
        go("/manage/employees/new")
        for k, v in dict(emp_code="EMP031", first_name="Demo", last_name="Joiner", email="emp031@example.com",
                         phone="9000031031", date_of_joining="2026-10-05", bank_name="Demo National Bank",
                         bank_account_no="000123456789", ifsc_code="DEMO0000001").items():
            page.fill(f"#{k}", v)
        page.select_option("#department_id", label="Engineering")
        page.select_option("#designation_id", index=3)
        snap(page, "04_employee_add_form")
        page.click("button:has-text('Save')");                  snap(page, "05_employee_added")
        row = page.locator("tr", has_text="EMP031")
        row.locator("button[title=Delete]").click();            snap(page, "06_employee_deleted")
        # constraint demo: duplicate employee code
        go("/manage/employees/new")
        for k, v in dict(emp_code="EMP001", first_name="Dup", last_name="Test", email="dup@example.com",
                         date_of_joining="2026-10-05").items():
            page.fill(f"#{k}", v)
        page.select_option("#department_id", index=1); page.select_option("#designation_id", index=1)
        page.click("button:has-text('Save')");                  snap(page, "07_constraint_duplicate_code")
        go("/manage/departments/");                             snap(page, "08_departments")
        go("/manage/designations/");                            snap(page, "09_designations")
        go("/manage/salary-structures/");                       snap(page, "10_salary_structures")
        go("/manage/attendance/?period=3");                     snap(page, "11_attendance_october")
        go("/manage/earnings/?period=3");                       snap(page, "12_earnings")
        go("/manage/deductions/?period=2");                     snap(page, "13_deductions_auto_and_manual")
        go("/manage/loans/");                                   snap(page, "14_loans")
        go("/loans/1");                                         snap(page, "15_loan_repayments")
        # locked-period demo
        go("/manage/earnings/new")
        page.select_option("#employee_id", index=1); page.select_option("#payroll_period_id", label="August 2026 [PAID]")
        page.select_option("#earning_type", index=1); page.fill("#amount", "500")
        page.click("button:has-text('Save')");                  snap(page, "16_period_locked_error")
        go("/settings");                                        snap(page, "17_rates_settings")
        # ---- the payroll workflow, clicked through the real UI
        go("/periods");                                         snap(page, "18_periods_october_open")
        page.locator("tr", has_text="October 2026").locator("button:has-text('Process payroll')").click()
        snap(page, "19_payroll_processed")
        page.locator("tr", has_text="October 2026").locator("button:has-text('Generate bank transfers')").click()
        snap(page, "20_transfers_generated")
        go("/payroll?period=3");                                snap(page, "21_payroll_register")
        # payslip of an employee who has LOP / loan / extra earning in October
        slip = page.locator("tr", has_text="EMP003").locator("a:has-text('Payslip')").get_attribute("href")
        go(slip);                                              snap(page, "22_payslip", full=True)
        go("/transfers?period=3");                              snap(page, "23_bank_transfers_pending")
        go("/periods")
        page.locator("tr", has_text="October 2026").locator("button:has-text('Mark transfers paid')").click()
        go("/transfers?period=3");                              snap(page, "24_bank_transfers_paid")
        go("/reports?period=3");                                snap(page, "25_reports_top")
        page.locator("button:has-text('View SQL')").nth(4).click()
        page.locator("#sql5").scroll_into_view_if_needed()
        snap(page, "26_report_sql_subquery")
        go("/");                                                snap(page, "27_dashboard_after_october")

        # ---- security, roles and the database explorer
        go("/admin/users");                                     snap(page, "29_users_and_roles")
        emp = browser.new_page(viewport={"width": 1440, "height": 810}, device_scale_factor=1.5)
        sign_in(emp, "emp003");                                 emp.wait_for_timeout(500)
        emp.screenshot(path=str(OUT / "30_employee_self_service.png")); shots.append("30_employee_self_service.png"); print("saved 30_employee_self_service.png")
        emp.goto(BASE + "/payroll"); emp.wait_for_timeout(500)
        emp.screenshot(path=str(OUT / "31_access_denied_for_employee.png")); shots.append("31_access_denied_for_employee.png"); print("saved 31_access_denied_for_employee.png")
        emp.close()
        # a salary edit through the UI -> the database trigger writes the audit trail
        go("/manage/salary-structures/2/edit")
        page.fill("#basic_salary", "84700")
        page.click("button:has-text('Save')")
        go("/database");                                        snap(page, "32_database_explorer")
        page.locator("button.example-q").nth(1).click()
        page.click("button:has-text('Run query')")
        page.locator("#sqlbox").scroll_into_view_if_needed();   snap(page, "33_sql_console_view_query")
        page.fill("#sqlbox", "DELETE FROM employee")
        page.click("button:has-text('Run query')");             snap(page, "34_sql_console_blocks_writes")
        snap(page, "35_audit_trail_from_trigger", selector=".cardx:has(.hd:has-text('written by database triggers'))")
        browser.close()
finally:
    server.terminate()
print(len(shots), "screenshots in", OUT)
