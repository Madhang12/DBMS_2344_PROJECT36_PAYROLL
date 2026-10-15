# Submission Document - Project 36

**Title:** Employee Payroll and Statutory Deduction Management System
**Student:** G MADHAN (25WU0102344), AI ML RHINOS  *(name and ID taken from the Review 1 PDF; edit if needed)*
**Course:** Database Management Systems - Project-Based Learning

## Links (fill in before submitting)
- GitHub repository: [PASTE GITHUB REPOSITORY URL HERE]
- Demo video (Google Drive, 5 minutes): [PASTE GOOGLE DRIVE VIDEO URL HERE]

## Contents of the submission folder
| Item | Location |
|---|---|
| Review 1 presentation (original) | `review1/Project36_Employee_Payroll_DBMS_Review1.pdf` |
| Review 2 presentation | `presentations/Project36_DBMS_Review2.pptx` (script: `docs/Review2_Presentation_Script.md`) |
| Review 3 presentation | `presentations/Project36_DBMS_Review3.pptx` (script: `docs/Review3_Presentation_Script.md`) |
| Source code | `app/`, `run.py`, `scripts/` |
| Database scripts | `database/mysql/schema.sql`, `database/sqlite/schema.sql`, `database/seed.sql`, `database/views.sql`, `database/*/triggers.sql`, `database/queries.sql` |
| Final project report | `docs/Project_Report.md` |
| Setup, testing, assumptions, ER diagram, GitHub guide | `docs/SETUP.md`, `docs/TESTING.md`, `docs/ASSUMPTIONS.md`, `docs/ER_DIAGRAM.md`, `docs/GITHUB_UPLOAD.md` |
| Test results | `tests/test_results.txt` (74 / 74 SQLite), `tests/test_results_mysql.txt` (11 / 11 MySQL 8.0.46) |
| Screenshots | `screenshots/` (35 real screenshots; `review2_stage/` has the 27 from Review 2) |
| Demo video script | `docs/Demo_Video_Script.md` |

## Declarations
- All data is synthetic; no real personal information is included.
- No passwords or secrets are stored in the repository (`.env` is git-ignored; `.env.example` has placeholders).
- Deduction rates are illustrative, not official statutory rates.
- Demo login accounts are synthetic and local; the demo password comes from `DEMO_PASSWORD` in `.env` (default shown in the README).
- Limitations: simulated bank transfers, demo-grade security (no HTTPS), MySQL tested on 8.0.46 only, GitHub Actions workflow not yet run.
