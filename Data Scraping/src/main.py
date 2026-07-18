"""
Orchestrator: jalanin semua scraper + enrichment script secara berurutan,
biar ga perlu manual jalanin satu-satu.

URUTAN INI PENTING (ada dependency antar step):
    1. scrape_seasons.py    - independen
    2. scrape_teams.py      - independen (tapi logically duluan, teams.json
                               dipakai buat referensi tim di step lain)
    3. scrape_awards.py     - independen
    4. scrape_rosters.py    - independen
    5. enrich_awards_role.py - BUTUH rosters.json + awards.json (step 3 & 4)
    6. build_players.py     - BUTUH rosters.json + awards.json (step 3 & 4)
    7. scrape_matches.py    - independen

Tiap step dijalanin sebagai subprocess terpisah (bukan import function),
biar konsisten sama cara masing-masing script dites manual satu-satu
sebelumnya (python scrape_X.py), dan biar 1 script gagal ga bikin crash
seluruh proses import module lain.

Cara pakai:
    python main.py
"""

import subprocess
import sys
import time

STEPS = [
    ("scrape_seasons.py", "Season (seasons.json)"),
    ("scrape_teams.py", "Team + TeamSeason (teams.json, team_seasons.json)"),
    ("scrape_awards.py", "Award (awards.json)"),
    ("scrape_rosters.py", "Roster (rosters.json)"),
    ("enrich_awards_role.py", "Enrichment: isi role award dari roster"),
    ("build_players.py", "Player (players.json)"),
    ("scrape_matches.py", "Match (matches.json)"),
]


def run_step(script_name, description):
    print(f"\n{'=' * 60}")
    print(f"[RUN] {script_name} - {description}")
    print("=" * 60)

    start = time.time()
    result = subprocess.run([sys.executable, script_name])
    elapsed = time.time() - start

    ok = result.returncode == 0
    status = "OK" if ok else "GAGAL"
    print(f"[{status}] {script_name} selesai dalam {elapsed:.1f}s")
    return ok


def main():
    results = []
    total_start = time.time()

    for script_name, description in STEPS:
        ok = run_step(script_name, description)
        results.append((script_name, ok))

    total_elapsed = time.time() - total_start

    print(f"\n{'=' * 60}")
    print("RINGKASAN")
    print("=" * 60)
    for script_name, ok in results:
        print(f"  [{'OK' if ok else 'GAGAL'}] {script_name}")
    print(f"\nTotal waktu: {total_elapsed:.1f}s")

    failed = [name for name, ok in results if not ok]
    if failed:
        print(f"\n{len(failed)} step gagal: {', '.join(failed)}")
        print("Cek error di atas, benerin, lalu jalanin ulang step yang gagal secara manual.")
        sys.exit(1)
    else:
        print("\nSemua step berhasil.")


if __name__ == "__main__":
    main()