# Assumptions and Payroll Rules

All rates are **illustrative** and stored in the `payroll_config` table (editable under *Settings*).
They are not official statutory rates and must not be used for real payroll.

| Key | Value | Meaning |
|---|---|---|
| pf_rate | 0.12 | Employee PF on basic salary |
| pf_wage_ceiling | 15000 | Basic salary used for PF is capped at this |
| esi_rate | 0.0075 | ESI on gross |
| esi_gross_limit | 21000 | ESI applies only when gross <= this |
| pt_amount | 200 | Flat professional tax per month |
| pt_gross_limit | 15000 | PT applies when gross > this |
| tds_rate | 0.05 | Simple TDS rate |
| tds_monthly_threshold | 50000 | TDS applies on gross above this |

## Formulas
- fixed gross = basic + HRA + DA + special allowance (salary_structure)
- LOP days = working days - days present - paid leave days (derived, not stored)
- LOP amount = fixed gross / working days x LOP days
- gross = fixed gross - LOP amount + extra earnings (bonus, overtime, incentive)
- PF = pf_rate x min(basic, pf_wage_ceiling); ESI = esi_rate x gross if gross <= esi_gross_limit
- PT = pt_amount if gross > pt_gross_limit; TDS = tds_rate x (gross - tds_monthly_threshold) if positive
- Loan EMI = min(EMI, outstanding balance) for ACTIVE loans that started on or before the period end
- net = gross - (statutory + loan + other deductions); amounts rounded to 2 decimals

## Other assumptions
- One payroll_detail row per employee per period; INACTIVE employees are skipped; employees missing salary or attendance are reported and skipped.
- A period is processed once (OPEN -> PROCESSED -> PAID); inputs for processed periods are locked.
- payroll_detail is a deliberate results snapshot (denormalised) so payslips never change after processing.
- Bank transfers are simulated records. Reference format `TXN{period:03d}{payroll_id:05d}`; payslip number `PS-{year}{month:02d}-{emp_code}`.
- Access: ADMIN (everything), HR (no rates / users / explorer), EMPLOYEE (own payslips only). Demo accounts share the password in DEMO_PASSWORD.
- Security scope: salted PBKDF2-SHA256 hashes, CSRF tokens, per-username in-memory login throttle, read-only SQL console. Not hardened for internet exposure (no HTTPS, no e-mail password reset).
- Triggers: payroll_detail rows of a period that is not OPEN cannot be inserted, updated or deleted; salary, employee-status and rate changes are written to audit_log (no user name is stored because triggers cannot see the web user).
- Data is synthetic: random.seed(36) in `scripts/generate_seed.py`.
