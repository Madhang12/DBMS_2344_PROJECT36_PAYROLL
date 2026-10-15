"""Authentication helpers: password hashing and the demo accounts.

Passwords are never stored - only salted PBKDF2 hashes (werkzeug). Roles:
  ADMIN     everything, including rates, users and the database explorer
  HR        manage data and run payroll (no rates / users / database explorer)
  EMPLOYEE  sees only their own profile and payslips
"""
import hashlib
import hmac
import os

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

ITERATIONS = 200_000          # tests lower this for speed
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "Payroll@2026")   # demo-only, local accounts; change in .env
ROLES = ("ADMIN", "HR", "EMPLOYEE")
MIN_PASSWORD_LENGTH = 8


def hash_password(password):
    return generate_password_hash(password, method=f"pbkdf2:sha256:{ITERATIONS}")


def verify_password(stored_hash, password):
    return check_password_hash(stored_hash, password)


def password_problem(password):
    """Return a message if the password is unacceptable, else None."""
    if len(password or "") < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    return None


def create_demo_users(db):
    """admin, hr and five employee accounts (emp001..emp005). Synthetic, local demo accounts."""
    db.run("INSERT INTO app_user (username, password_hash, role) VALUES (?,?,?)", ("admin", hash_password(DEMO_PASSWORD), "ADMIN"))
    db.run("INSERT INTO app_user (username, password_hash, role) VALUES (?,?,?)", ("hr", hash_password(DEMO_PASSWORD), "HR"))
    for emp in db.all("SELECT employee_id, emp_code FROM employee WHERE status='ACTIVE' ORDER BY employee_id LIMIT 5"):
        db.run("INSERT INTO app_user (username, password_hash, role, employee_id) VALUES (?,?,?,?)",
               (emp["emp_code"].lower(), hash_password(DEMO_PASSWORD), "EMPLOYEE", emp["employee_id"]))
    db.commit()


# ---- password reset links --------------------------------------------------------------------------------------
# A link carries the user id plus a fingerprint of the CURRENT password hash and is signed with SECRET_KEY.
# So it expires by itself, and stops working the moment the password changes (one use only). Nothing is stored.
def _fingerprint(password_hash):
    return hashlib.sha256(password_hash.encode()).hexdigest()[:20]


def make_reset_token(secret_key, user):
    return URLSafeTimedSerializer(secret_key, salt="password-reset").dumps(
        {"u": user["user_id"], "f": _fingerprint(user["password_hash"])})


def read_reset_token(secret_key, token, max_age_seconds):
    """Return (user_id, fingerprint) or (None, reason) where reason is 'expired' or 'invalid'."""
    try:
        data = URLSafeTimedSerializer(secret_key, salt="password-reset").loads(token, max_age=max_age_seconds)
        return data["u"], data["f"]
    except SignatureExpired:
        return None, "expired"
    except (BadSignature, KeyError, TypeError):
        return None, "invalid"


def fingerprint_matches(user, fingerprint):
    return hmac.compare_digest(_fingerprint(user["password_hash"]), fingerprint)
