# Final ER diagram (16 tables)

GitHub renders the diagram below directly. Crow's-foot notation: `||--o{` = one-to-many, `||--||` = one-to-one.

```mermaid
erDiagram
    DEPARTMENT ||--o{ EMPLOYEE : "has"
    DESIGNATION ||--o{ EMPLOYEE : "has"
    EMPLOYEE ||--|| SALARY_STRUCTURE : "has one"
    EMPLOYEE ||--o{ ATTENDANCE_SUMMARY : "monthly"
    EMPLOYEE ||--o{ EARNINGS : "monthly"
    EMPLOYEE ||--o{ DEDUCTIONS : "monthly"
    EMPLOYEE ||--o{ LOAN : "takes"
    EMPLOYEE ||--o{ PAYROLL_DETAIL : "paid by"
    EMPLOYEE |o--o{ APP_USER : "login (EMPLOYEE role)"
    PAYROLL_PERIOD ||--o{ PAYROLL_DETAIL : "contains"
    PAYROLL_PERIOD ||--o{ ATTENDANCE_SUMMARY : "for"
    PAYROLL_PERIOD ||--o{ EARNINGS : "for"
    PAYROLL_PERIOD ||--o{ DEDUCTIONS : "for"
    PAYROLL_DETAIL ||--|| PAYSLIP : "produces"
    PAYROLL_DETAIL ||--|| BANK_TRANSFER : "produces"
    LOAN ||--o{ LOAN_REPAYMENT : "repaid by"
    PAYROLL_DETAIL |o--o{ LOAN_REPAYMENT : "deducted in"

    PAYROLL_CONFIG { string config_key PK }
    AUDIT_LOG { int audit_id PK }
    APP_USER { int user_id PK }
```

`PAYROLL_CONFIG` (editable illustrative rates) and `AUDIT_LOG` (written only by database triggers) have no foreign keys by design.
Views: `v_payroll_summary`, `v_department_cost`, `v_loan_ledger`. Triggers: see `database/sqlite/triggers.sql` and `database/mysql/triggers.sql`.
