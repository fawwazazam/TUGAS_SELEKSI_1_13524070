"""
Build the MPL Indonesia data warehouse from the populated OLTP database.

Prerequisite:
    python "Data Storing/src/load_db.py" --user root --password --disable-ssl

Run from the repository root:
    python "Data Warehouse/src/load_dw.py" --user root --password --disable-ssl
"""

import argparse
import getpass
import os
import subprocess
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent
SCHEMA_SQL = SRC_DIR / "schema_dw.sql"
LOAD_SQL = SRC_DIR / "load_dw.sql"


def run_sql_file(sql_file, args, password):
    """Run one SQL file through the MariaDB client using UTF-8 input."""
    env = os.environ.copy()
    if password:
        env["MYSQL_PWD"] = password

    command = [
        args.client,
        "--host", args.host,
        "--port", str(args.port),
        "--user", args.user,
        "--protocol=TCP",
        "--default-character-set=utf8mb4",
    ]
    if args.disable_ssl:
        command.append("--ssl=0")

    result = subprocess.run(command, input=sql_file.read_bytes(), env=env)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", default="mariadb", help="MariaDB client executable")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--user", default="root")
    parser.add_argument("--password", action="store_true", help="Prompt for password")
    parser.add_argument("--disable-ssl", action="store_true", help="Pass --ssl=0 to the client")
    args = parser.parse_args()

    password = getpass.getpass("MariaDB password: ") if args.password else ""
    run_sql_file(SCHEMA_SQL, args, password)
    run_sql_file(LOAD_SQL, args, password)
    print("Data warehouse mpl_indonesia_dw created and populated.")


if __name__ == "__main__":
    main()
