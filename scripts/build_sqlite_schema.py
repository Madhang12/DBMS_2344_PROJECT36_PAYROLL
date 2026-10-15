"""Generate database/sqlite/schema.sql from database/mysql/schema.sql.

Only three syntax differences exist between the two dialects for this schema:
  * INT AUTO_INCREMENT PRIMARY KEY  ->  INTEGER PRIMARY KEY AUTOINCREMENT
  * CREATE DATABASE / USE            ->  removed (SQLite is one file per DB)
  * ENGINE=InnoDB                    ->  removed
"""
import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
src = (root / "database" / "mysql" / "schema.sql").read_text()

out = re.sub(r"^CREATE DATABASE.*\n", "", src, flags=re.M)
out = re.sub(r"^USE .*\n", "", out, flags=re.M)
out = out.replace("INT AUTO_INCREMENT PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
out = out.replace(") ENGINE=InnoDB;", ");")
out = out.replace("MySQL 8.0+ schema", "SQLite schema (generated - do not edit by hand)")
out = "PRAGMA foreign_keys = ON;\n" + out

(root / "database" / "sqlite" / "schema.sql").write_text(out)
print("wrote database/sqlite/schema.sql")
