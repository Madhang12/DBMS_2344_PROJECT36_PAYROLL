"""Database introspection and a safe read-only SQL console (used by the Database Explorer page)."""
import re
import sqlite3
import time
from pathlib import Path

from . import config
from .db import connect

CONSOLE_ROW_LIMIT = 200
CONSOLE_TIMEOUT_SECONDS = 5
BLOCKED_TABLES = ("app_user",)          # password hashes are never shown, even to admins


def introspect(db):
    """Tables (with columns, keys, row counts), views and triggers of the connected database."""
    return _sqlite(db) if db.backend == "sqlite" else _mysql(db)


def _sqlite(db):
    names = [r["name"] for r in db.all("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    tables = []
    for t in names:                                   # names come from sqlite_master, not user input
        cols = [dict(name=c["name"], type=c["type"] or "", pk=bool(c["pk"]), notnull=bool(c["notnull"]))
                for c in db.all(f"PRAGMA table_info({t})")]
        fks = [dict(col=f["from"], ref_table=f["table"], ref_col=f["to"], on_delete=f["on_delete"])
               for f in db.all(f"PRAGMA foreign_key_list({t})")]
        tables.append(dict(name=t, rows=db.scalar(f"SELECT COUNT(*) FROM {t}"), columns=cols, fks=fks))
    views = [r["name"] for r in db.all("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")]
    triggers = []
    for r in db.all("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger' ORDER BY name"):
        m = re.search(r"\b(BEFORE|AFTER)\s+(INSERT|UPDATE|DELETE)", r["sql"], re.I)
        triggers.append(dict(name=r["name"], table=r["tbl_name"], timing=m.group(1).upper() if m else "", event=m.group(2).upper() if m else ""))
    return dict(tables=tables, views=views, triggers=triggers)


def _mysql(db):
    names = [r["TABLE_NAME"] for r in db.all(
        "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME")]
    tables = []
    for t in names:
        cols = [dict(name=c["COLUMN_NAME"], type=c["COLUMN_TYPE"], pk=c["COLUMN_KEY"] == "PRI", notnull=c["IS_NULLABLE"] == "NO")
                for c in db.all("SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_KEY, IS_NULLABLE FROM information_schema.COLUMNS "
                                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ? ORDER BY ORDINAL_POSITION", (t,))]
        fks = [dict(col=f["COLUMN_NAME"], ref_table=f["REFERENCED_TABLE_NAME"], ref_col=f["REFERENCED_COLUMN_NAME"], on_delete=f["DELETE_RULE"])
               for f in db.all("SELECT k.COLUMN_NAME, k.REFERENCED_TABLE_NAME, k.REFERENCED_COLUMN_NAME, r.DELETE_RULE "
                               "FROM information_schema.KEY_COLUMN_USAGE k JOIN information_schema.REFERENTIAL_CONSTRAINTS r "
                               "ON r.CONSTRAINT_NAME = k.CONSTRAINT_NAME AND r.CONSTRAINT_SCHEMA = k.TABLE_SCHEMA "
                               "WHERE k.TABLE_SCHEMA = DATABASE() AND k.TABLE_NAME = ? AND k.REFERENCED_TABLE_NAME IS NOT NULL", (t,))]
        tables.append(dict(name=t, rows=db.scalar(f"SELECT COUNT(*) FROM `{t}`"), columns=cols, fks=fks))
    views = [r["TABLE_NAME"] for r in db.all("SELECT TABLE_NAME FROM information_schema.VIEWS WHERE TABLE_SCHEMA = DATABASE() ORDER BY TABLE_NAME")]
    triggers = [dict(name=r["TRIGGER_NAME"], table=r["EVENT_OBJECT_TABLE"], timing=r["ACTION_TIMING"], event=r["EVENT_MANIPULATION"])
                for r in db.all("SELECT TRIGGER_NAME, EVENT_OBJECT_TABLE, ACTION_TIMING, EVENT_MANIPULATION FROM information_schema.TRIGGERS "
                                "WHERE TRIGGER_SCHEMA = DATABASE() ORDER BY TRIGGER_NAME")]
    return dict(tables=tables, views=views, triggers=triggers)


class ConsoleError(ValueError):
    """The query was refused or failed; the message is safe to show."""


def check_console_sql(sql):
    s = (sql or "").strip().rstrip(";").strip()
    if not s:
        raise ConsoleError("Type a SELECT query first.")
    if ";" in s:
        raise ConsoleError("Only one statement at a time.")
    if not re.match(r"(?is)^(select|with)\b", s):
        raise ConsoleError("Only SELECT queries are allowed in this console (it is read-only).")
    for t in BLOCKED_TABLES:
        if re.search(rf"\b{t}\b", s, re.I):
            raise ConsoleError(f"The table {t} holds password hashes and is not available in the console.")
    return s


def run_console(sql):
    """Run a SELECT on a separate read-only connection. Returns (columns, rows, truncated)."""
    s = check_console_sql(sql)
    if config.DB_BACKEND == "sqlite":
        uri = Path(config.SQLITE_PATH).resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.execute("PRAGMA query_only = ON")
        deadline = time.time() + CONSOLE_TIMEOUT_SECONDS
        conn.set_progress_handler(lambda: 1 if time.time() > deadline else 0, 100000)
        try:
            cur = conn.execute(s)
            cols = [d[0] for d in cur.description or []]
            rows = cur.fetchmany(CONSOLE_ROW_LIMIT + 1)
        except sqlite3.Error as e:
            raise ConsoleError(f"SQL error: {e}")
        finally:
            conn.close()
    else:
        import pymysql
        d = connect("mysql")
        try:
            cur = d.conn.cursor()
            cur.execute("SET SESSION TRANSACTION READ ONLY")
            cur.execute(f"SET SESSION MAX_EXECUTION_TIME = {CONSOLE_TIMEOUT_SECONDS * 1000}")
            cur.execute(s)
            cols = [c[0] for c in cur.description or []]
            rows = cur.fetchmany(CONSOLE_ROW_LIMIT + 1)
        except pymysql.MySQLError as e:
            raise ConsoleError(f"SQL error: {e}")
        finally:
            d.close()
    truncated = len(rows) > CONSOLE_ROW_LIMIT
    return cols, [list(r) for r in rows[:CONSOLE_ROW_LIMIT]], truncated
