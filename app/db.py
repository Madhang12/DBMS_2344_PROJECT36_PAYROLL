"""Tiny database layer that hides the SQLite / MySQL differences.

All SQL in the project is written with '?' placeholders and standard syntax
that works on both engines; this module converts '?' to '%s' for MySQL.
"""
import re
import sqlite3
from decimal import Decimal
from pathlib import Path

from flask import g

from . import config


def integrity_errors():
    """Tuple of exception classes meaning 'a constraint was violated'."""
    errs = [sqlite3.IntegrityError]
    if config.DB_BACKEND == "mysql":
        import pymysql
        errs.append(pymysql.err.IntegrityError)
    return tuple(errs)


class DB:
    def __init__(self, conn, backend):
        self.conn = conn
        self.backend = backend

    def _sql(self, sql):
        return sql.replace("?", "%s") if self.backend == "mysql" else sql

    def _params(self, params):
        """SQLite cannot bind Decimal; convert to float. MySQL driver handles Decimal."""
        if self.backend == "sqlite":
            return tuple(float(p) if isinstance(p, Decimal) else p for p in params)
        return tuple(params)

    def _cursor(self):
        if self.backend == "mysql":
            import pymysql.cursors
            return self.conn.cursor(pymysql.cursors.DictCursor)
        return self.conn.cursor()

    def all(self, sql, params=()):
        cur = self._cursor()
        cur.execute(self._sql(sql), self._params(params))
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]

    def one(self, sql, params=()):
        rows = self.all(sql, params)
        return rows[0] if rows else None

    def scalar(self, sql, params=()):
        row = self.one(sql, params)
        return next(iter(row.values())) if row else None

    def run(self, sql, params=()):
        """Execute INSERT/UPDATE/DELETE. Returns lastrowid. Caller commits."""
        cur = self._cursor()
        try:
            cur.execute(self._sql(sql), self._params(params))
        except Exception as e:
            raise self._as_integrity_error(e)
        rid = cur.lastrowid
        cur.close()
        return rid

    @staticmethod
    def _as_integrity_error(e):
        """MySQL reports a violated CHECK constraint (3819) and a trigger SIGNAL (1644) as OperationalError.
        Re-raise them as IntegrityError so the app treats every rule violation the same way on both engines."""
        if config.DB_BACKEND == "mysql":
            import pymysql
            if (isinstance(e, pymysql.err.OperationalError) and e.args and e.args[0] in (3819, 1644)):
                return pymysql.err.IntegrityError(*e.args)
        return e

    def script(self, sql_text):
        """Run a multi-statement SQL script (used by init_db.py)."""
        if self.backend == "sqlite":
            self.conn.executescript(sql_text)
            return
        cur = self._cursor()
        buf = []
        for line in sql_text.splitlines():
            if line.strip().startswith("--") or not line.strip():
                continue
            buf.append(line)
            if line.rstrip().endswith(";"):
                cur.execute("\n".join(buf))
                buf = []
        cur.close()
        self.conn.commit()

    def script_blocks(self, sql_text):
        """Run a script made of blocks separated by '-- @@' lines (used for triggers, whose bodies
        contain semicolons). SQLite can run the whole text; MySQL needs one statement at a time."""
        if self.backend == "sqlite":
            self.conn.executescript(sql_text)
            return
        cur = self._cursor()
        for block in re.split(r"^-- @@\s*$", sql_text, flags=re.M):
            lines = [ln for ln in block.splitlines() if not ln.strip().startswith("--")]
            stmt = "\n".join(lines).strip()
            if stmt:
                cur.execute(stmt)
        cur.close()
        self.conn.commit()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def connect(backend=None, sqlite_path=None):
    backend = backend or config.DB_BACKEND
    if backend == "mysql":
        import pymysql
        conn = pymysql.connect(**config.MYSQL, autocommit=False, charset="utf8mb4")
        return DB(conn, "mysql")
    path = sqlite_path or config.SQLITE_PATH
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")      # SQLite needs this per connection
    return DB(conn, "sqlite")


def get_db():
    if "db" not in g:
        g.db = connect()
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
