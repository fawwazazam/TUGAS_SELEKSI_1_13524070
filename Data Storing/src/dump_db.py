"""
Export the populated MariaDB database into Data Storing/export/mpl_indonesia.sql.

Run after load_db.py:
    python "Data Storing/src/dump_db.py" --user root --password
"""

import argparse
import getpass
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_FILE = ROOT / "Data Storing" / "export" / "mpl_indonesia.sql"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump-client", default="mariadb-dump")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--user", default="root")
    parser.add_argument("--password", action="store_true", help="Prompt for password")
    parser.add_argument("--disable-ssl", action="store_true", help="Pass --ssl=0 to the dump client")
    args = parser.parse_args()

    env = os.environ.copy()
    if args.password:
        env["MYSQL_PWD"] = getpass.getpass("MariaDB password: ")

    command = [
        args.dump_client,
        "--host", args.host,
        "--port", str(args.port),
        "--user", args.user,
        "--protocol=TCP",
        "--default-character-set=utf8mb4",
        "--databases", "mpl_indonesia",
    ]
    if args.disable_ssl:
        command.append("--ssl=0")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUT_FILE.open("w", encoding="utf-8", newline="\n") as f:
        result = subprocess.run(command, stdout=f, text=True, env=env)
    if result.returncode != 0:
        raise SystemExit(result.returncode)

    print(f"Exported {OUT_FILE}")


if __name__ == "__main__":
    main()
