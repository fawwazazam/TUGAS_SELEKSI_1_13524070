"""
Jalankan seluruh scraping dan enrichment sesuai urutan dependensinya.

Cara pakai:
    python main.py
"""

import subprocess
import sys
import time

STEPS = [
    ("scrape_seasons.py", "Musim (seasons.json)"),
    ("scrape_teams.py", "Tim + TeamSeason (teams.json, team_seasons.json)"),
    ("scrape_awards.py", "Penghargaan (awards.json)"),
    ("scrape_rosters.py", "Roster (rosters.json)"),
    ("enrich_awards_role.py", "Pengayaan role award dari roster"),
    ("build_players.py", "Pemain (players.json)"),
    ("scrape_matches.py", "Pertandingan (matches.json)"),
]


def run_step(script_name, description):
    """Jalankan satu script sebagai subprocess dan kembalikan statusnya."""
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
        print("Periksa error di atas, lalu jalankan ulang step yang gagal.")
        sys.exit(1)
    else:
        print("\nSemua step berhasil.")


if __name__ == "__main__":
    main()
