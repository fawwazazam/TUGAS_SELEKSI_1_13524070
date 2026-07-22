"""
Create and populate the MariaDB database from schema.sql and generated JSON data.

Run from the repository root:
    python "Data Storing/src/load_db.py" --user root --password
"""

import argparse
import getpass
import os
import subprocess
import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent
SCHEMA_SQL = SRC_DIR / "schema.sql"
LOAD_SQL = SRC_DIR / "seed.sql"
GENERATE_SQL = SRC_DIR / "make_seed.py"


def run_sql_file(sql_file, args, password):
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

    subprocess.run([sys.executable, str(GENERATE_SQL)], check=True)
    password = getpass.getpass("MariaDB password: ") if args.password else ""

    run_sql_file(SCHEMA_SQL, args, password)
    run_sql_file(LOAD_SQL, args, password)
    print("Database mpl_indonesia created and populated.")


if __name__ == "__main__":
    main()
