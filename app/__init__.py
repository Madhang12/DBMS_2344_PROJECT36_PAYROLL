"""Flask application factory and all routes."""
import calendar
import csv
import hmac
import io
import secrets
import time
from datetime import date

from flask import (Flask, Response, abort, flash, g, redirect, render_template, request, session, url_for)

from . import auth, config, dbinfo, payroll
from .numwords import rupees_in_words
from .crud import CRUD
from .db import close_db, get_db, integrity_errors
from .reports import REPORTS

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]


def inr(value):
    """Format a number as Indian-style currency, e.g. 123456.5 -> ₹1,23,456.50"""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "-"
    sign = "-" if v < 0 else ""
    whole, frac = f"{abs(v):.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts + [tail])
    return f"{sign}₹{whole}.{frac}"


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["CSRF_ENABLED"] = True            # tests switch this off except in the CSRF test
    app.teardown_appcontext(close_db)
    app.jinja_env.filters["inr"] = inr
    app.jinja_env.filters["inr_words"] = rupees_in_words

    # ------------------------------------------------------------------ security: login, roles, CSRF
    PUBLIC = {"login", "static", "forgot_password", "reset_password"}
    EMPLOYEE_OK = {"me", "payslip", "logout", "change_password"}
    ADMIN_ONLY = {"settings", "users", "user_create", "user_toggle", "user_reset", "database"}
    failed_logins = {}                           # username -> [timestamps]; simple in-memory throttle
    reset_requests = {}                          # throttle for reset-link requests
    MAX_FAILS, WINDOW = 5, 300

    def csrf_token():
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(16)
        return session["csrf"]

    @app.context_processor
    def inject():
        return {"crud_nav": CRUD, "backend": config.DB_BACKEND.upper(), "today": date.today(),
                "csrf_token": csrf_token, "user": getattr(g, "user", None)}

    @app.before_request
    def guard():
        ep = request.endpoint
        if ep is None:
            return None                           # unknown URL -> normal 404
        g.user = None
        if ep == "static":
            return None
        uid = session.get("uid")
        if uid:
            g.user = get_db().one("SELECT user_id, username, role, employee_id FROM app_user WHERE user_id=? AND is_active=1", (uid,))
            if g.user is None:
                session.clear()
        if request.method == "POST" and app.config["CSRF_ENABLED"]:
            sent = request.form.get("csrf_token", "")
            expected = session.get("csrf", "")
            if not expected or not hmac.compare_digest(sent, expected):
                abort(400, "Security token missing or expired - reload the page and try again.")
        if ep in PUBLIC:
            return None
        if g.user is None:
            return redirect(url_for("login", next=request.path if request.method == "GET" else None))
        role = g.user["role"]
        if role == "EMPLOYEE" and ep not in EMPLOYEE_OK:
            if ep == "dashboard":
                return redirect(url_for("me"))
            abort(403)
        if role == "HR" and ep in ADMIN_ONLY:
            abort(403)
        return None

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    def http_error(e):
        info = {400: ("Request refused", "The request could not be accepted."),
                403: ("Not allowed", "Your role does not have access to this page."),
                404: ("Page not found", "That page does not exist.")}[e.code]
        detail = e.description if e.code == 400 else info[1]
        return render_template("error.html", code=e.code, title=info[0], detail=detail), e.code

    # ------------------------------------------------------------------ helpers
    def latest_period(db, statuses=("PROCESSED", "PAID")):
        marks = ",".join("?" for _ in statuses)
        return db.one(f"SELECT * FROM payroll_period WHERE status IN ({marks}) ORDER BY payroll_period_id DESC LIMIT 1", statuses)

    def selected_period(db):
        pid = request.args.get("period", type=int)
        if pid:
            return db.one("SELECT * FROM payroll_period WHERE payroll_period_id=?", (pid,))
        return latest_period(db) or db.one("SELECT * FROM payroll_period ORDER BY payroll_period_id DESC LIMIT 1")

    def all_periods(db):
        return db.all("SELECT * FROM payroll_period ORDER BY payroll_period_id DESC")

    def db_error(e):
        flash(f"Could not save - a database rule was violated (duplicate value, out-of-range value, "
              f"missing reference or record in use). Details: {e}", "danger")

    # ------------------------------------------------------------------ dashboard
    @app.route("/")
    def dashboard():
        db = get_db()
        per = latest_period(db)
        stats = dict(
            employees=db.scalar("SELECT COUNT(*) FROM employee WHERE status='ACTIVE'"),
            departments=db.scalar("SELECT COUNT(*) FROM department"),
            open_periods=db.scalar("SELECT COUNT(*) FROM payroll_period WHERE status='OPEN'"),
            pending_transfers=db.scalar("SELECT COUNT(*) FROM bank_transfer WHERE status='PENDING'"),
            loans=db.scalar("SELECT COUNT(*) FROM loan WHERE status='ACTIVE'"),
            loan_outstanding=db.scalar("SELECT COALESCE(SUM(outstanding_balance),0) FROM loan WHERE status='ACTIVE'"),
        )
        totals = None
        top = []
        if per:
            totals = db.one("SELECT COUNT(*) AS n, SUM(gross_salary) AS gross, SUM(total_deductions) AS ded, "
                            "SUM(net_salary) AS net FROM payroll_detail WHERE payroll_period_id=?", (per["payroll_period_id"],))
            top = db.all("SELECT e.emp_code, e.first_name, e.last_name, p.net_salary, p.payslip_id FROM "
                         "(SELECT pd.employee_id, pd.net_salary, ps.payslip_id, pd.payroll_period_id FROM payroll_detail pd "
                         " JOIN payslip ps ON ps.payroll_id = pd.payroll_id) p "
                         "JOIN employee e ON e.employee_id = p.employee_id WHERE p.payroll_period_id=? "
                         "ORDER BY p.net_salary DESC LIMIT 5", (per["payroll_period_id"],))
        trend = db.all("SELECT pp.period_name, SUM(p.gross_salary) AS gross, SUM(p.total_deductions) AS ded, "
                       "SUM(p.net_salary) AS net FROM payroll_detail p JOIN payroll_period pp "
                       "ON pp.payroll_period_id = p.payroll_period_id GROUP BY pp.payroll_period_id, pp.period_name "
                       "ORDER BY pp.payroll_period_id")
        by_dept = db.all("SELECT d.department_name, COUNT(e.employee_id) AS n FROM department d "
                         "LEFT JOIN employee e ON e.department_id = d.department_id AND e.status='ACTIVE' "
                         "GROUP BY d.department_id, d.department_name ORDER BY n DESC")
        ded_mix = db.all("SELECT deduction_type, SUM(amount) AS total FROM deductions "
                         "WHERE payroll_period_id=? AND source='AUTO' GROUP BY deduction_type ORDER BY total DESC",
                         (per["payroll_period_id"] if per else 0,))
        return render_template("dashboard.html", stats=stats, per=per, totals=totals, top=top,
                               trend=trend, by_dept=by_dept, ded_mix=ded_mix, periods=all_periods(db))

    # ------------------------------------------------------------------ generic CRUD
    def get_cfg(key):
        cfg = CRUD.get(key)
        if not cfg:
            abort(404)
        return cfg

    def field_options(db, cfg):
        return {f["name"]: f["options"](db) for f in cfg["fields"] if f["type"] == "select"}

    def read_form(cfg):
        values, errors = {}, []
        for f in cfg["fields"]:
            raw = (request.form.get(f["name"]) or "").strip()
            if raw == "":
                if f["required"]:
                    errors.append(f"{f['label']} is required.")
                values[f["name"]] = None
                continue
            if f["type"] == "number" or f.get("int"):
                try:
                    values[f["name"]] = int(float(raw)) if f.get("int") else float(raw)
                except ValueError:
                    errors.append(f"{f['label']} must be a number.")
            else:
                values[f["name"]] = raw
        return values, errors

    def period_is_locked(db, period_id):
        if not period_id:
            return False
        st = db.scalar("SELECT status FROM payroll_period WHERE payroll_period_id=?", (period_id,))
        return st is not None and st != "OPEN"

    @app.route("/manage/<key>/")
    def crud_list(key):
        cfg = get_cfg(key)
        db = get_db()
        sql, params, per_sel = cfg["sql"], [], None
        if cfg.get("period_col"):
            per_sel = request.args.get("period", type=int)
            if per_sel:
                sql = f"SELECT * FROM ({sql.rsplit(' ORDER BY ', 1)[0]}) t WHERE t.{cfg['period_col']} = ?"
                params = [per_sel]
        rows = db.all(sql, params)
        hook = cfg.get("row_hook")
        if hook:
            rows = [hook(r) for r in rows]
        return render_template("crud_list.html", key=key, cfg=cfg, rows=rows,
                               periods=all_periods(db) if cfg.get("period_col") else [], per_sel=per_sel)

    @app.route("/manage/<key>/new", methods=["GET", "POST"])
    @app.route("/manage/<key>/<int:rid>/edit", methods=["GET", "POST"])
    def crud_form(key, rid=None):
        cfg = get_cfg(key)
        db = get_db()
        row = None
        if rid is not None:
            row = db.one(f"SELECT * FROM {cfg['table']} WHERE {cfg['pk']}=?", (rid,))
            if not row:
                abort(404)
            prot = cfg.get("protect")
            if prot and row.get(prot[0]) == prot[1]:
                flash("This row was generated by payroll processing and is read-only.", "warning")
                return redirect(url_for("crud_list", key=key))
            if cfg.get("lock_period") and period_is_locked(db, row["payroll_period_id"]):
                flash("This payroll period is processed - its inputs are locked.", "warning")
                return redirect(url_for("crud_list", key=key))
        values = dict(cfg.get("defaults", {}))
        if row:
            values = dict(row)
        elif request.method == "GET":
            for k in ("employee_id", "payroll_period_id"):
                if request.args.get(k):
                    values[k] = request.args.get(k, type=int)
            for f in cfg["fields"]:
                if f.get("default") is not None:
                    values.setdefault(f["name"], f["default"])
        if request.method == "POST":
            values, errors = read_form(cfg)
            if cfg.get("lock_period") and period_is_locked(db, values.get("payroll_period_id")):
                errors.append("The selected payroll period is already processed - choose an OPEN period.")
            if errors:
                for e in errors:
                    flash(e, "danger")
            else:
                try:
                    if rid is None:
                        if cfg.get("before_insert"):
                            cfg["before_insert"](values)
                        values.update(cfg.get("fixed", {}))
                        cols = list(values)
                        db.run(f"INSERT INTO {cfg['table']} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
                               [values[c] for c in cols])
                        flash(f"{cfg['singular']} added.", "success")
                    else:
                        cols = [f["name"] for f in cfg["fields"]]
                        db.run(f"UPDATE {cfg['table']} SET {', '.join(c + '=?' for c in cols)} WHERE {cfg['pk']}=?",
                               [values[c] for c in cols] + [rid])
                        flash(f"{cfg['singular']} updated.", "success")
                    db.commit()
                    return redirect(url_for("crud_list", key=key))
                except integrity_errors() as e:
                    db.rollback()
                    db_error(e)
        return render_template("crud_form.html", key=key, cfg=cfg, values=values, rid=rid,
                               options=field_options(db, cfg))

    @app.post("/manage/<key>/<int:rid>/delete")
    def crud_delete(key, rid):
        cfg = get_cfg(key)
        db = get_db()
        row = db.one(f"SELECT * FROM {cfg['table']} WHERE {cfg['pk']}=?", (rid,))
        if not row:
            abort(404)
        prot = cfg.get("protect")
        if prot and row.get(prot[0]) == prot[1]:
            flash("AUTO rows generated by payroll processing cannot be deleted.", "warning")
        elif cfg.get("lock_period") and period_is_locked(db, row["payroll_period_id"]):
            flash("This payroll period is processed - its inputs are locked.", "warning")
        else:
            try:
                db.run(f"DELETE FROM {cfg['table']} WHERE {cfg['pk']}=?", (rid,))
                db.commit()
                flash(f"{cfg['singular']} deleted.", "success")
            except integrity_errors() as e:
                db.rollback()
                flash(f"Cannot delete: this record is referenced by other data. {cfg.get('delete_hint', '')}", "danger")
        return redirect(url_for("crud_list", key=key))

    # ------------------------------------------------------------------ employee profile
    @app.route("/employees/<int:eid>")
    def employee_view(eid):
        db = get_db()
        emp = db.one("SELECT e.*, d.department_name, g.title FROM employee e "
                     "JOIN department d ON d.department_id = e.department_id "
                     "JOIN designation g ON g.designation_id = e.designation_id WHERE e.employee_id=?", (eid,))
        if not emp:
            abort(404)
        sal = db.one("SELECT * FROM salary_structure WHERE employee_id=?", (eid,))
        slips = db.all("SELECT ps.payslip_id, ps.payslip_no, pp.period_name, p.gross_salary, p.total_deductions, p.net_salary "
                       "FROM payroll_detail p JOIN payslip ps ON ps.payroll_id = p.payroll_id "
                       "JOIN payroll_period pp ON pp.payroll_period_id = p.payroll_period_id "
                       "WHERE p.employee_id=? ORDER BY pp.payroll_period_id DESC", (eid,))
        loans = db.all("SELECT * FROM loan WHERE employee_id=? ORDER BY loan_id", (eid,))
        return render_template("employee_view.html", emp=emp, sal=sal, slips=slips, loans=loans)

    # ------------------------------------------------------------------ loans + repayments
    @app.route("/loans/<int:lid>", methods=["GET", "POST"])
    def loan_view(lid):
        db = get_db()
        loan = db.one("SELECT l.*, e.emp_code, e.first_name, e.last_name FROM loan l "
                      "JOIN employee e ON e.employee_id = l.employee_id WHERE l.loan_id=?", (lid,))
        if not loan:
            abort(404)
        if request.method == "POST":
            try:
                amt = payroll.money(request.form.get("amount", "0"))
                if amt <= 0 or amt > payroll.money(loan["outstanding_balance"]):
                    raise ValueError("Repayment must be greater than 0 and not exceed the outstanding balance.")
                new_bal = payroll.money(loan["outstanding_balance"]) - amt
                db.run("INSERT INTO loan_repayment (loan_id, payroll_id, amount, repayment_date, balance_after) VALUES (?,NULL,?,?,?)",
                       (lid, amt, date.today().isoformat(), new_bal))
                db.run("UPDATE loan SET outstanding_balance=?, status=? WHERE loan_id=?",
                       (new_bal, "CLOSED" if new_bal <= 0 else "ACTIVE", lid))
                db.commit()
                flash("Manual repayment recorded.", "success")
            except Exception as e:  # ValueError / decimal.InvalidOperation / DB errors
                db.rollback()
                flash(f"Could not record repayment: {e}", "danger")
            return redirect(url_for("loan_view", lid=lid))
        reps = db.all("SELECT r.*, pp.period_name FROM loan_repayment r "
                      "LEFT JOIN payroll_detail p ON p.payroll_id = r.payroll_id "
                      "LEFT JOIN payroll_period pp ON pp.payroll_period_id = p.payroll_period_id "
                      "WHERE r.loan_id=? ORDER BY r.repayment_id", (lid,))
        return render_template("loan_view.html", loan=loan, reps=reps)

    # ------------------------------------------------------------------ payroll periods
    @app.route("/periods", methods=["GET", "POST"])
    def periods():
        db = get_db()
        if request.method == "POST":
            try:
                m, y = int(request.form["period_month"]), int(request.form["period_year"])
                if not 1 <= m <= 12 or not 2000 <= y <= 2100:
                    raise ValueError("Enter a valid month and year.")
                last = calendar.monthrange(y, m)[1]
                db.run("INSERT INTO payroll_period (period_name, period_month, period_year, start_date, end_date, status) "
                       "VALUES (?,?,?,?,?,'OPEN')",
                       (f"{MONTHS[m-1]} {y}", m, y, date(y, m, 1).isoformat(), date(y, m, last).isoformat()))
                db.commit()
                flash(f"Payroll period {MONTHS[m-1]} {y} created.", "success")
            except integrity_errors():
                db.rollback()
                flash("That month already exists as a payroll period.", "danger")
            except (ValueError, KeyError) as e:
                db.rollback()
                flash(str(e), "danger")
            return redirect(url_for("periods"))
        rows = db.all("SELECT pp.*, "
                      "(SELECT COUNT(*) FROM attendance_summary a WHERE a.payroll_period_id = pp.payroll_period_id) AS att_rows, "
                      "(SELECT COUNT(*) FROM payroll_detail p WHERE p.payroll_period_id = pp.payroll_period_id) AS payslips, "
                      "(SELECT COALESCE(SUM(p.net_salary),0) FROM payroll_detail p WHERE p.payroll_period_id = pp.payroll_period_id) AS net_total, "
                      "(SELECT COUNT(*) FROM bank_transfer b JOIN payroll_detail p ON p.payroll_id=b.payroll_id "
                      " WHERE p.payroll_period_id = pp.payroll_period_id) AS transfers "
                      "FROM payroll_period pp ORDER BY pp.period_year DESC, pp.period_month DESC")
        active = db.scalar("SELECT COUNT(*) FROM employee WHERE status='ACTIVE'")
        return render_template("periods.html", rows=rows, months=MONTHS, active=active,
                               next_year=date.today().year)

    @app.post("/periods/<int:pid>/process")
    def period_process(pid):
        db = get_db()
        try:
            res = payroll.process_period(db, pid)
            msg = (f"Payroll processed for {res['processed']} employees - gross {inr(res['gross'])}, "
                   f"deductions {inr(res['deductions'])}, net {inr(res['net'])}.")
            if res["skipped"]:
                msg += " Skipped: " + ", ".join(f"{c} ({r})" for c, r in res["skipped"])
            flash(msg, "success")
        except Exception as e:
            flash(f"Payroll not processed: {e}", "danger")
        return redirect(url_for("periods"))

    @app.post("/periods/<int:pid>/transfers")
    def period_transfers(pid):
        try:
            n = payroll.create_bank_transfers(get_db(), pid)
            flash(f"{n} bank transfer record(s) created (status PENDING).", "success")
        except Exception as e:
            flash(str(e), "danger")
        return redirect(url_for("periods"))

    @app.post("/periods/<int:pid>/paid")
    def period_paid(pid):
        try:
            n = payroll.mark_transfers_paid(get_db(), pid)
            flash(f"{n} transfer(s) marked SUCCESS (simulated) - period closed as PAID.", "success")
        except Exception as e:
            flash(str(e), "danger")
        return redirect(url_for("periods"))

    @app.post("/periods/<int:pid>/delete")
    def period_delete(pid):
        db = get_db()
        try:
            st = db.scalar("SELECT status FROM payroll_period WHERE payroll_period_id=?", (pid,))
            if st != "OPEN":
                raise ValueError("Only an OPEN period can be deleted.")
            db.run("DELETE FROM payroll_period WHERE payroll_period_id=?", (pid,))
            db.commit()
            flash("Payroll period deleted.", "success")
        except integrity_errors():
            db.rollback()
            flash("Cannot delete: attendance, earnings or deductions already exist for this period.", "danger")
        except ValueError as e:
            flash(str(e), "danger")
        return redirect(url_for("periods"))

    # ------------------------------------------------------------------ payroll register, payslips, transfers
    REGISTER_SQL = ("SELECT p.payroll_id, ps.payslip_id, ps.payslip_no, e.emp_code, e.first_name, e.last_name, d.department_name, "
                    "p.gross_salary, p.statutory_deductions, p.loan_deductions, p.other_deductions, p.total_deductions, p.net_salary "
                    "FROM payroll_detail p JOIN employee e ON e.employee_id = p.employee_id "
                    "JOIN department d ON d.department_id = e.department_id "
                    "JOIN payslip ps ON ps.payroll_id = p.payroll_id WHERE p.payroll_period_id=? ORDER BY e.emp_code")

    @app.route("/payroll")
    def payroll_register():
        db = get_db()
        per = selected_period(db)
        rows = db.all(REGISTER_SQL, (per["payroll_period_id"],)) if per else []
        tot = db.one("SELECT COALESCE(SUM(gross_salary),0) AS gross, COALESCE(SUM(total_deductions),0) AS ded, "
                     "COALESCE(SUM(net_salary),0) AS net FROM payroll_detail WHERE payroll_period_id=?",
                     (per["payroll_period_id"],)) if per else None
        return render_template("payroll.html", rows=rows, per=per, tot=tot, periods=all_periods(db))

    @app.route("/payroll/export.csv")
    def payroll_csv():
        db = get_db()
        per = selected_period(db)
        if not per:
            abort(404)
        rows = db.all(REGISTER_SQL, (per["payroll_period_id"],))
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Payslip No", "Emp Code", "First Name", "Last Name", "Department", "Gross", "Statutory",
                    "Loan EMI", "Other Deductions", "Total Deductions", "Net"])
        for r in rows:
            w.writerow([r["payslip_no"], r["emp_code"], r["first_name"], r["last_name"], r["department_name"],
                        r["gross_salary"], r["statutory_deductions"], r["loan_deductions"], r["other_deductions"],
                        r["total_deductions"], r["net_salary"]])
        return Response(buf.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": f"attachment; filename=payroll_{per['period_name'].replace(' ', '_')}.csv"})

    @app.route("/payslips/<int:slip_id>")
    def payslip(slip_id):
        db = get_db()
        ps = db.one("SELECT ps.*, p.*, e.emp_code, e.first_name, e.last_name, e.bank_name, e.bank_account_no, e.ifsc_code, "
                    "e.date_of_joining, d.department_name, g.title, pp.period_name, pp.start_date, pp.end_date "
                    "FROM payslip ps JOIN payroll_detail p ON p.payroll_id = ps.payroll_id "
                    "JOIN employee e ON e.employee_id = p.employee_id "
                    "JOIN department d ON d.department_id = e.department_id "
                    "JOIN designation g ON g.designation_id = e.designation_id "
                    "JOIN payroll_period pp ON pp.payroll_period_id = p.payroll_period_id WHERE ps.payslip_id=?", (slip_id,))
        if not ps:
            abort(404)
        if g.user["role"] == "EMPLOYEE" and ps["employee_id"] != g.user["employee_id"]:
            abort(403)                                  # employees may open only their own payslips
        extras = db.all("SELECT earning_type, amount, remarks FROM earnings WHERE employee_id=? AND payroll_period_id=?",
                        (ps["employee_id"], ps["payroll_period_id"]))
        deds = db.all("SELECT deduction_type, amount, is_statutory FROM deductions WHERE employee_id=? AND payroll_period_id=? "
                      "ORDER BY is_statutory DESC, deduction_id", (ps["employee_id"], ps["payroll_period_id"]))
        transfer = db.one("SELECT * FROM bank_transfer WHERE payroll_id=?", (ps["payroll_id"],))
        return render_template("payslip.html", ps=ps, extras=extras, deds=deds, transfer=transfer)

    @app.route("/transfers")
    def transfers():
        db = get_db()
        per = selected_period(db)
        rows = db.all("SELECT b.*, e.emp_code, e.first_name, e.last_name FROM bank_transfer b "
                      "JOIN payroll_detail p ON p.payroll_id = b.payroll_id "
                      "JOIN employee e ON e.employee_id = p.employee_id "
                      "WHERE p.payroll_period_id=? ORDER BY e.emp_code", (per["payroll_period_id"],)) if per else []
        summ = db.all("SELECT b.status, COUNT(*) AS n, SUM(b.amount) AS total FROM bank_transfer b "
                      "JOIN payroll_detail p ON p.payroll_id = b.payroll_id WHERE p.payroll_period_id=? GROUP BY b.status",
                      (per["payroll_period_id"],)) if per else []
        return render_template("transfers.html", rows=rows, per=per, summ=summ, periods=all_periods(db))

    # ------------------------------------------------------------------ reports
    @app.route("/reports")
    def reports():
        db = get_db()
        per = selected_period(db)
        results = []
        for r in REPORTS:
            n = r["sql"].count("?")
            params = (per["payroll_period_id"],) * n if (n and per) else ()
            rows = db.all(r["sql"], params) if (not n or per) else []
            results.append(dict(r, rows=rows))
        return render_template("reports.html", results=results, per=per, periods=all_periods(db))

    # ------------------------------------------------------------------ settings
    @app.route("/settings", methods=["GET", "POST"])
    def settings():
        db = get_db()
        if request.method == "POST":
            try:
                for r in db.all("SELECT config_key FROM payroll_config"):
                    val = float(request.form[r["config_key"]])
                    if val < 0:
                        raise ValueError("Rates and limits cannot be negative.")
                    db.run("UPDATE payroll_config SET config_value=? WHERE config_key=?", (val, r["config_key"]))
                db.commit()
                flash("Settings saved. They apply to payroll processed from now on.", "success")
            except (ValueError, KeyError) as e:
                db.rollback()
                flash(f"Invalid value: {e}", "danger")
            return redirect(url_for("settings"))
        return render_template("settings.html", cfg=db.all("SELECT * FROM payroll_config ORDER BY config_key"))

    # ------------------------------------------------------------------ login / logout / account
    def safe_next(target):
        return target if target and target.startswith("/") and not target.startswith("//") else None

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if g.user:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            name = request.form.get("username", "").strip().lower()
            now = time.time()
            recent = [t for t in failed_logins.get(name, []) if now - t < WINDOW]
            failed_logins[name] = recent
            if len(recent) >= MAX_FAILS:
                flash("Too many failed attempts for this username. Wait a few minutes and try again.", "danger")
                return render_template("login.html"), 429
            row = get_db().one("SELECT * FROM app_user WHERE username=?", (name,))
            if row and row["is_active"] and auth.verify_password(row["password_hash"], request.form.get("password", "")):
                failed_logins.pop(name, None)
                session.clear()                       # new session id on login (prevents fixation)
                session["uid"] = row["user_id"]
                nxt = safe_next(request.form.get("next"))
                return redirect(nxt or (url_for("me") if row["role"] == "EMPLOYEE" else url_for("dashboard")))
            failed_logins.setdefault(name, []).append(now)
            flash("Invalid username or password.", "danger")
        return render_template("login.html", next=request.args.get("next", "")), 200


    @app.route("/forgot-password", methods=["GET", "POST"])
    def forgot_password():
        if g.user:
            return redirect(url_for("change_password"))
        link = None
        if request.method == "POST":
            name = request.form.get("username", "").strip().lower()
            now = time.time()
            recent = [t for t in reset_requests.get("req:" + name, []) if now - t < WINDOW]
            reset_requests["req:" + name] = recent
            if len(recent) >= MAX_FAILS:
                flash("Too many reset requests for this username. Wait a few minutes and try again.", "danger")
                return render_template("forgot_password.html"), 429
            reset_requests["req:" + name].append(now)
            row = get_db().one("SELECT * FROM app_user WHERE username=? AND is_active=1", (name,)) if name else None
            if row:
                token = auth.make_reset_token(app.config["SECRET_KEY"], row)
                url = url_for("reset_password", token=token, _external=True)
                if not app.config.get("TESTING"):
                    print(f"[password reset] link for {row['username']} (valid {config.RESET_TOKEN_MINUTES} min): {url}")
                if app.config.get("SHOW_RESET_LINK", config.SHOW_RESET_LINK):
                    link = url
            # same message whether or not the username exists
            flash("If that username exists and is active, a reset link has been created.", "success")
        return render_template("forgot_password.html", link=link, minutes=config.RESET_TOKEN_MINUTES)

    @app.route("/reset-password/<token>", methods=["GET", "POST"])
    def reset_password(token):
        uid, info = auth.read_reset_token(app.config["SECRET_KEY"], token, config.RESET_TOKEN_MINUTES * 60)
        row = get_db().one("SELECT * FROM app_user WHERE user_id=? AND is_active=1", (uid,)) if uid else None
        if row is None or not auth.fingerprint_matches(row, info):
            why = "has expired" if info == "expired" else "is not valid any more (it may already have been used)"
            return render_template("reset_password.html", bad_link=why), 400
        if request.method == "POST":
            new = request.form.get("new_password", "")
            if new != request.form.get("confirm_password", ""):
                flash("The new passwords do not match.", "danger")
            elif auth.password_problem(new):
                flash(auth.password_problem(new), "danger")
            else:
                db = get_db()
                db.run("UPDATE app_user SET password_hash=? WHERE user_id=?", (auth.hash_password(new), row["user_id"]))
                db.commit()
                failed_logins.pop(row["username"], None)
                session.clear()
                flash("Password updated. Sign in with your new password.", "success")
                return redirect(url_for("login"))
        return render_template("reset_password.html", username=row["username"])

    @app.post("/logout")
    def logout():
        session.clear()
        flash("You have been signed out.", "success")
        return redirect(url_for("login"))

    @app.route("/account/password", methods=["GET", "POST"])
    def change_password():
        db = get_db()
        if request.method == "POST":
            row = db.one("SELECT * FROM app_user WHERE user_id=?", (g.user["user_id"],))
            new = request.form.get("new_password", "")
            if not auth.verify_password(row["password_hash"], request.form.get("current_password", "")):
                flash("Current password is incorrect.", "danger")
            elif new != request.form.get("confirm_password", ""):
                flash("The new passwords do not match.", "danger")
            elif auth.password_problem(new):
                flash(auth.password_problem(new), "danger")
            else:
                db.run("UPDATE app_user SET password_hash=? WHERE user_id=?", (auth.hash_password(new), row["user_id"]))
                db.commit()
                flash("Password changed.", "success")
                return redirect(url_for("me") if g.user["role"] == "EMPLOYEE" else url_for("dashboard"))
        return render_template("change_password.html")

    @app.route("/me")
    def me():
        db = get_db()
        eid = g.user["employee_id"]
        if eid is None:                               # ADMIN / HR have no employee record
            return redirect(url_for("dashboard"))
        emp = db.one("SELECT e.*, d.department_name, g.title FROM employee e JOIN department d ON d.department_id = e.department_id "
                     "JOIN designation g ON g.designation_id = e.designation_id WHERE e.employee_id=?", (eid,))
        slips = db.all("SELECT ps.payslip_id, ps.payslip_no, pp.period_name, p.gross_salary, p.total_deductions, p.net_salary "
                       "FROM payroll_detail p JOIN payslip ps ON ps.payroll_id = p.payroll_id "
                       "JOIN payroll_period pp ON pp.payroll_period_id = p.payroll_period_id "
                       "WHERE p.employee_id=? ORDER BY pp.payroll_period_id DESC", (eid,))
        loans = db.all("SELECT * FROM loan WHERE employee_id=? ORDER BY loan_id", (eid,))
        return render_template("me.html", emp=emp, slips=slips, loans=loans)

    # ------------------------------------------------------------------ administration: users
    @app.route("/admin/users")
    def users():
        db = get_db()
        rows = db.all("SELECT u.user_id, u.username, u.role, u.is_active, e.emp_code FROM app_user u "
                      "LEFT JOIN employee e ON e.employee_id = u.employee_id ORDER BY u.role, u.username")
        emps = db.all("SELECT employee_id, emp_code, first_name, last_name FROM employee WHERE status='ACTIVE' ORDER BY emp_code")
        return render_template("users.html", rows=rows, emps=emps, roles=auth.ROLES)

    @app.post("/admin/users/new")
    def user_create():
        db = get_db()
        name = request.form.get("username", "").strip().lower()
        role = request.form.get("role", "")
        eid = request.form.get("employee_id", type=int)
        pw = request.form.get("password", "")
        try:
            if not name or len(name) > 30 or not name.replace("_", "").replace(".", "").isalnum():
                raise ValueError("Username: 1-30 letters, digits, '.' or '_'.")
            if role not in auth.ROLES:
                raise ValueError("Choose a role.")
            if role == "EMPLOYEE" and not eid:
                raise ValueError("An EMPLOYEE account must be linked to an employee.")
            if auth.password_problem(pw):
                raise ValueError(auth.password_problem(pw))
            db.run("INSERT INTO app_user (username, password_hash, role, employee_id) VALUES (?,?,?,?)",
                   (name, auth.hash_password(pw), role, eid if role == "EMPLOYEE" else None))
            db.commit()
            flash(f"User {name} ({role}) created.", "success")
        except integrity_errors():
            db.rollback()
            flash("That username already exists.", "danger")
        except ValueError as e:
            db.rollback()
            flash(str(e), "danger")
        return redirect(url_for("users"))

    @app.post("/admin/users/<int:uid>/toggle")
    def user_toggle(uid):
        db = get_db()
        row = db.one("SELECT * FROM app_user WHERE user_id=?", (uid,))
        if not row:
            abort(404)
        if row["user_id"] == g.user["user_id"]:
            flash("You cannot deactivate your own account.", "warning")
        elif row["role"] == "ADMIN" and row["is_active"] and db.scalar("SELECT COUNT(*) FROM app_user WHERE role='ADMIN' AND is_active=1") <= 1:
            flash("The last active administrator cannot be deactivated.", "warning")
        else:
            db.run("UPDATE app_user SET is_active=? WHERE user_id=?", (0 if row["is_active"] else 1, uid))
            db.commit()
            flash(f"{row['username']} is now {'inactive' if row['is_active'] else 'active'}.", "success")
        return redirect(url_for("users"))

    @app.post("/admin/users/<int:uid>/reset")
    def user_reset(uid):
        db = get_db()
        row = db.one("SELECT username FROM app_user WHERE user_id=?", (uid,))
        if not row:
            abort(404)
        pw = request.form.get("password", "")
        if auth.password_problem(pw):
            flash(auth.password_problem(pw), "danger")
        else:
            db.run("UPDATE app_user SET password_hash=? WHERE user_id=?", (auth.hash_password(pw), uid))
            db.commit()
            flash(f"Password for {row['username']} was reset.", "success")
        return redirect(url_for("users"))

    # ------------------------------------------------------------------ database explorer + read-only console
    CONSOLE_EXAMPLES = [
        ("Payroll totals per month", "SELECT period_name, COUNT(*) AS employees, SUM(gross_salary) AS gross, SUM(net_salary) AS net\nFROM v_payroll_summary\nGROUP BY period_name"),
        ("Department cost (view)", "SELECT * FROM v_department_cost ORDER BY payroll_period_id DESC, total_gross DESC"),
        ("Loan ledger (view)", "SELECT * FROM v_loan_ledger"),
        ("Audit trail", "SELECT * FROM audit_log ORDER BY audit_id DESC"),
    ]

    @app.route("/database", methods=["GET", "POST"])
    def database():
        db = get_db()
        sql = request.form.get("sql", "") if request.method == "POST" else ""
        result = error = None
        if request.method == "POST":
            try:
                cols, rows, truncated = dbinfo.run_console(sql)
                result = dict(cols=cols, rows=rows, truncated=truncated)
            except dbinfo.ConsoleError as e:
                error = str(e)
        info = dbinfo.introspect(db)
        audit = db.all("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 15")
        return render_template("database.html", info=info, audit=audit, sql=sql, result=result, error=error,
                               examples=CONSOLE_EXAMPLES, row_limit=dbinfo.CONSOLE_ROW_LIMIT)

    return app
