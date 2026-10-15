"""Collect real numbers from the implemented project into scripts/pptx/facts.json
(used by the presentation builders so slides never contain invented figures)."""
import json, re, sys, tempfile, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from app import config, db as dbmod, payroll
import init_db

tmp = Path(tempfile.mkdtemp()) / "facts.db"
config.SQLITE_PATH = str(tmp)
init_db.init("sqlite", str(tmp), quiet=True)
d = dbmod.connect("sqlite", str(tmp))
f0 = {r["name"]: d.scalar(f"SELECT COUNT(*) FROM {r['name']}") for r in
      d.all("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")}
res3 = payroll.process_period(d, 3)           # October, exactly like the live demo

f = {"tables_init": f0}
f["tables"] = {r["name"]: d.scalar(f"SELECT COUNT(*) FROM {r['name']}") for r in
               d.all("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")}
f["periods"] = d.all("SELECT pp.period_name, COUNT(*) n, ROUND(SUM(gross_salary),2) gross, ROUND(SUM(total_deductions),2) ded, "
                     "ROUND(SUM(net_salary),2) net FROM payroll_detail p JOIN payroll_period pp ON pp.payroll_period_id=p.payroll_period_id "
                     "GROUP BY pp.payroll_period_id, pp.period_name ORDER BY pp.payroll_period_id")
f["sample_payslip"] = d.one("SELECT p.* FROM payroll_detail p WHERE employee_id=3 AND payroll_period_id=3")
f["sample_deductions"] = d.all("SELECT deduction_type, amount FROM deductions WHERE employee_id=3 AND payroll_period_id=3 ORDER BY deduction_id")
f["dept_cost_oct"] = d.all("SELECT d.department_name, COUNT(*) n, ROUND(SUM(p.gross_salary),2) gross FROM payroll_detail p "
                           "JOIN employee e ON e.employee_id=p.employee_id JOIN department d ON d.department_id=e.department_id "
                           "WHERE p.payroll_period_id=3 GROUP BY d.department_id, d.department_name ORDER BY gross DESC")
sch = (ROOT / "database/mysql/schema.sql").read_text()
f["constraints"] = {"tables": len(re.findall(r"^CREATE TABLE", sch, re.M)),
                    "primary_keys": len(re.findall(r"PRIMARY KEY", sch)),
                    "foreign_keys": len(re.findall(r"FOREIGN KEY", sch)),
                    "unique": len(re.findall(r"\bUNIQUE \(", sch)),
                    "check": len(re.findall(r"\bCHECK \(", sch)),
                    "indexes": len(re.findall(r"^CREATE INDEX", sch, re.M))}
f["oct_result"] = {k: str(v) for k, v in res3.items() if k != "skipped"}
out = subprocess.run([sys.executable, "-W", "ignore", "-m", "unittest", "discover", "-s", "tests"], cwd=ROOT, capture_output=True, text=True)
m = re.search(r"Ran (\d+) tests", out.stderr)
f["tests_run"] = int(m.group(1)); f["tests_ok"] = "OK" in out.stderr.splitlines()[-1]
txt = (ROOT / "tests/test_results.txt").read_text()
suites = {}
for line in txt.splitlines():
    mm = re.search(r"\(test_app\.(\w+)\.", line)
    if mm:
        suites[mm.group(1)] = suites.get(mm.group(1), 0) + 1
f["test_suites"] = suites
f["loc"] = {"python": sum(len(p.read_text().splitlines()) for p in (ROOT/"app").rglob("*.py")) + sum(len(p.read_text().splitlines()) for p in (ROOT/"scripts").glob("*.py")),
            "html": sum(len(p.read_text().splitlines()) for p in (ROOT/"app/templates").glob("*.html")),
            "sql": sum(len(p.read_text().splitlines()) for p in (ROOT/"database").rglob("*.sql") if "sqlite" not in str(p))}
(ROOT / "scripts/pptx/facts.json").write_text(json.dumps(f, indent=1, default=str))
print(json.dumps({k: f[k] for k in ("constraints","oct_result","tests_run","tests_ok","test_suites","loc")}, indent=1, default=str))
print(f["periods"]); print(f["tables"])
