# Publishing to GitHub (nothing has been uploaded for you)

The folder is ready: `.gitignore` excludes `.env`, `instance/`, caches and `node_modules`; `.env.example` has placeholders only; there are no real credentials or personal data.

1. Create an **empty** repository on github.com (no README / licence - they already exist). Choose public or private.
2. In the project folder:
   ```bash
   git init -b main                   # skip if the folder already has a .git directory
   git add .
   git status                         # check: no .env, no instance/ database
   git commit -m "Project 36: payroll and statutory deduction management system"
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```
3. Open the repository's **Actions** tab - `tests.yml` runs the SQLite job and the MySQL 8 job. (It has not run yet; if a job fails, read the log - it is the first run.)
4. Put the repository URL into `README.md` and `docs/Submission_Document.md` where it says `[PASTE GITHUB REPOSITORY URL HERE]`.
5. Upload the demo video to Google Drive, set sharing as your course requires, and paste the link where it says `[PASTE GOOGLE DRIVE VIDEO URL HERE]`.

Keep `DEMO_PASSWORD` in `.env` private if you ever host the demo; the default is for local use only.
