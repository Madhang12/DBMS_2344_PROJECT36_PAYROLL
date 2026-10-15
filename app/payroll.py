"""Payroll calculation and processing.

HOW THE NUMBERS ARE CALCULATED  (all rates are illustrative and editable in the
payroll_config table / Settings page - they are NOT official statutory rates)

    fixed_gross   = basic + HRA + DA + special allowance
    per_day       = fixed_gross / working_days
    lop_days      = working_days - days_present - paid_leave_days
    lop_amount    = per_day * lop_days                      (loss-of-pay cut)
    gross_salary  = fixed_gross - lop_amount + other_earnings (bonus, overtime ...)

    PF   = pf_rate  * min(basic, pf_wage_ceiling)
    ESI  = esi_rate * gross            only if gross <= esi_gross_limit
    PT   = pt_amount                   only if gross >  pt_gross_limit
    TDS  = tds_rate * (gross - tds_monthly_threshold)   only if gross > threshold
    Loan EMI = sum of EMIs of ACTIVE loans started on/before the period end
               (never more than the outstanding balance)
    Other deductions = manual deductions entered for the period

    total_deductions = PF + ESI + PT + TDS + Loan EMI + other deductions
    net_salary       = gross_salary - total_deductions
"""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

TWO = Decimal("0.01")


def D(x):
    return Decimal(str(x if x is not None else 0))


def money(x):
    return D(x).quantize(TWO, rounding=ROUND_HALF_UP)


def get_config(db):
    return {r["config_key"]: D(r["config_value"]) for r in db.all("SELECT config_key, config_value FROM payroll_config")}


def calculate(salary, attendance, other_earnings, manual_deductions, loans, cfg):
    """Pure function: inputs are plain numbers/dicts, output is a dict of results.

    salary            : dict(basic_salary, hra, da, special_allowance)
    attendance        : dict(working_days, days_present, paid_leave_days)
    other_earnings    : total of extra earnings for the period
    manual_deductions : total of manual (non-statutory) deductions
    loans             : list of dict(loan_id, emi_amount, outstanding_balance)
    """
    basic, hra, da, special = (money(salary[k]) for k in ("basic_salary", "hra", "da", "special_allowance"))
    fixed_gross = basic + hra + da + special
    working = int(attendance["working_days"])
    lop_days = D(working) - D(attendance["days_present"]) - D(attendance["paid_leave_days"])
    lop_amount = money(fixed_gross / D(working) * lop_days)
    other_earn = money(other_earnings)
    gross = money(fixed_gross - lop_amount + other_earn)

    pf = money(cfg["pf_rate"] * min(basic, cfg["pf_wage_ceiling"]))
    esi = money(cfg["esi_rate"] * gross) if gross <= cfg["esi_gross_limit"] else Decimal("0.00")
    pt = money(cfg["pt_amount"]) if gross > cfg["pt_gross_limit"] else Decimal("0.00")
    tds = money(cfg["tds_rate"] * (gross - cfg["tds_monthly_threshold"])) if gross > cfg["tds_monthly_threshold"] else Decimal("0.00")

    loan_parts = []
    for ln in loans:
        emi = min(money(ln["emi_amount"]), money(ln["outstanding_balance"]))
        if emi > 0:
            loan_parts.append((ln["loan_id"], emi))
    loan_total = sum((e for _, e in loan_parts), Decimal("0.00"))

    statutory = pf + esi + pt + tds
    other_ded = money(manual_deductions)
    total_ded = statutory + loan_total + other_ded
    net = gross - total_ded
    return {
        "basic_salary": basic, "hra": hra, "da": da, "special_allowance": special,
        "fixed_gross": fixed_gross, "working_days": working, "lop_days": lop_days,
        "lop_amount": lop_amount, "other_earnings": other_earn, "gross_salary": gross,
        "pf": pf, "esi": esi, "pt": pt, "tds": tds,
        "statutory_deductions": statutory, "loan_deductions": loan_total, "loan_parts": loan_parts,
        "other_deductions": other_ded, "total_deductions": total_ded, "net_salary": net,
    }


def process_period(db, period_id):
    """Process payroll for one OPEN period. All-or-nothing (single transaction).

    Returns dict(processed=n, skipped=[(emp_code, reason)], gross, deductions, net).
    Raises ValueError if the period is not OPEN or nothing could be processed.
    """
    period = db.one("SELECT * FROM payroll_period WHERE payroll_period_id = ?", (period_id,))
    if not period:
        raise ValueError("Payroll period not found.")
    if period["status"] != "OPEN":
        raise ValueError(f"{period['period_name']} is already {period['status']} - it cannot be processed again.")

    cfg = get_config(db)
    today = date.today().isoformat()
    employees = db.all(
        "SELECT e.employee_id, e.emp_code FROM employee e WHERE e.status = 'ACTIVE' ORDER BY e.employee_id")
    processed, skipped = 0, []
    tot_g = tot_d = tot_n = Decimal("0.00")
    try:
        for emp in employees:
            eid = emp["employee_id"]
            sal = db.one("SELECT * FROM salary_structure WHERE employee_id = ?", (eid,))
            att = db.one("SELECT * FROM attendance_summary WHERE employee_id = ? AND payroll_period_id = ?", (eid, period_id))
            if not sal:
                skipped.append((emp["emp_code"], "no salary structure"))
                continue
            if not att:
                skipped.append((emp["emp_code"], "no attendance for this period"))
                continue
            extra = db.scalar("SELECT COALESCE(SUM(amount),0) FROM earnings WHERE employee_id=? AND payroll_period_id=?", (eid, period_id))
            manual = db.scalar("SELECT COALESCE(SUM(amount),0) FROM deductions WHERE employee_id=? AND payroll_period_id=? AND source='MANUAL'", (eid, period_id))
            loans = db.all("SELECT loan_id, emi_amount, outstanding_balance FROM loan "
                           "WHERE employee_id=? AND status='ACTIVE' AND start_date <= ?", (eid, str(period["end_date"])))
            r = calculate(sal, att, extra, manual, loans, cfg)
            if r["net_salary"] < 0:
                raise ValueError(f"{emp['emp_code']}: deductions exceed gross salary - check loans/deductions.")

            pid = db.run(
                "INSERT INTO payroll_detail (employee_id, payroll_period_id, basic_salary, hra, da, special_allowance, "
                "working_days, lop_days, lop_amount, other_earnings, gross_salary, statutory_deductions, loan_deductions, "
                "other_deductions, total_deductions, net_salary, processed_on) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (eid, period_id, r["basic_salary"], r["hra"], r["da"], r["special_allowance"], r["working_days"],
                 r["lop_days"], r["lop_amount"], r["other_earnings"], r["gross_salary"], r["statutory_deductions"],
                 r["loan_deductions"], r["other_deductions"], r["total_deductions"], r["net_salary"], today))

            # statutory + loan deductions are recorded as AUTO rows (itemised on the payslip)
            for name, amt in (("Provident Fund (PF)", r["pf"]), ("ESI", r["esi"]),
                              ("Professional Tax (PT)", r["pt"]), ("Income Tax (TDS)", r["tds"])):
                if amt > 0:
                    db.run("INSERT INTO deductions (employee_id, payroll_period_id, deduction_type, amount, is_statutory, source) "
                           "VALUES (?,?,?,?,1,'AUTO')", (eid, period_id, name, amt))
            if r["loan_deductions"] > 0:
                db.run("INSERT INTO deductions (employee_id, payroll_period_id, deduction_type, amount, is_statutory, source) "
                       "VALUES (?,?,?,?,0,'AUTO')", (eid, period_id, "Loan EMI", r["loan_deductions"]))
            for loan_id, emi in r["loan_parts"]:
                bal = db.one("SELECT outstanding_balance FROM loan WHERE loan_id=?", (loan_id,))["outstanding_balance"]
                new_bal = money(bal) - emi
                db.run("INSERT INTO loan_repayment (loan_id, payroll_id, amount, repayment_date, balance_after) VALUES (?,?,?,?,?)",
                       (loan_id, pid, emi, today, new_bal))
                db.run("UPDATE loan SET outstanding_balance=?, status=? WHERE loan_id=?",
                       (new_bal, "CLOSED" if new_bal <= 0 else "ACTIVE", loan_id))

            db.run("INSERT INTO payslip (payroll_id, payslip_no, generated_on) VALUES (?,?,?)",
                   (pid, f"PS-{period['period_year']}{int(period['period_month']):02d}-{emp['emp_code']}", today))
            processed += 1
            tot_g += r["gross_salary"]; tot_d += r["total_deductions"]; tot_n += r["net_salary"]

        if processed == 0:
            raise ValueError("No employee could be processed - add salary structures and attendance first.")
        db.run("UPDATE payroll_period SET status='PROCESSED' WHERE payroll_period_id=?", (period_id,))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"processed": processed, "skipped": skipped, "gross": tot_g, "deductions": tot_d, "net": tot_n}


def create_bank_transfers(db, period_id):
    """One PENDING transfer record per payslip of a PROCESSED period."""
    period = db.one("SELECT * FROM payroll_period WHERE payroll_period_id=?", (period_id,))
    if not period or period["status"] != "PROCESSED":
        raise ValueError("Bank transfers can only be generated for a PROCESSED period.")
    rows = db.all("SELECT p.payroll_id, p.net_salary, e.bank_name, e.bank_account_no, e.ifsc_code "
                  "FROM payroll_detail p JOIN employee e ON e.employee_id = p.employee_id "
                  "WHERE p.payroll_period_id = ? AND NOT EXISTS (SELECT 1 FROM bank_transfer b WHERE b.payroll_id = p.payroll_id)",
                  (period_id,))
    for r in rows:
        db.run("INSERT INTO bank_transfer (payroll_id, bank_name, account_no, ifsc_code, amount, reference_no, status) "
               "VALUES (?,?,?,?,?,?, 'PENDING')",
               (r["payroll_id"], r["bank_name"], r["bank_account_no"], r["ifsc_code"], r["net_salary"],
                f"TXN{period_id:03d}{r['payroll_id']:05d}"))
    db.commit()
    return len(rows)


def mark_transfers_paid(db, period_id):
    """Mark all PENDING transfers SUCCESS (simulated) and close the period as PAID."""
    period = db.one("SELECT * FROM payroll_period WHERE payroll_period_id=?", (period_id,))
    if not period or period["status"] != "PROCESSED":
        raise ValueError("Only a PROCESSED period can be marked as paid.")
    pending = db.scalar("SELECT COUNT(*) FROM bank_transfer b JOIN payroll_detail p ON p.payroll_id=b.payroll_id "
                        "WHERE p.payroll_period_id=? AND b.status='PENDING'", (period_id,))
    if not pending:
        raise ValueError("Generate the bank transfer records first.")
    db.run("UPDATE bank_transfer SET status='SUCCESS', transfer_date=? WHERE status='PENDING' AND payroll_id IN "
           "(SELECT payroll_id FROM payroll_detail WHERE payroll_period_id=?)", (date.today().isoformat(), period_id))
    db.run("UPDATE payroll_period SET status='PAID' WHERE payroll_period_id=?", (period_id,))
    db.commit()
    return pending
