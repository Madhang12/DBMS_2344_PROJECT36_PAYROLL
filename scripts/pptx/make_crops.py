"""Crop the sidebar off table-heavy screenshots so they stay legible on a slide."""
from pathlib import Path
from PIL import Image
root = Path(__file__).resolve().parent.parent.parent
import sys
src = root / "screenshots" / (sys.argv[1] if len(sys.argv) > 1 else "")
out = root / "presentations" / "assets" / (sys.argv[2] if len(sys.argv) > 2 else "crops")
out.mkdir(parents=True, exist_ok=True)
for f in ["02_employees_list", "04_employee_add_form", "10_salary_structures", "11_attendance_october", "14_loans",
          "15_loan_repayments", "18_periods_october_open", "19_payroll_processed", "20_transfers_generated",
          "21_payroll_register", "23_bank_transfers_pending", "24_bank_transfers_paid", "25_reports_top",
          "07_constraint_duplicate_code", "16_period_locked_error", "13_deductions_auto_and_manual", "12_earnings", "22_payslip", "26_report_sql_subquery", "17_rates_settings", "29_users_and_roles", "30_employee_self_service", "31_access_denied_for_employee", "32_database_explorer", "33_sql_console_view_query", "34_sql_console_blocks_writes"]:
    im = Image.open(src / f"{f}.png")
    # 2160x1215 source; sidebar is ~366px wide (244px at 1.5x). Keep 1794x1009 (16:9) of the main area.
    im.crop((366, 0, 366 + 1794, 1009)).save(out / f"{f}.png")
print("crops written to", out)
