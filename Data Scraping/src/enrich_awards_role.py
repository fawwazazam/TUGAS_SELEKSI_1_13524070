"""
Isi field role yang None di awards.json (award MVP/Most Improved/Rising
Star/Rookie/Dream Team - tabel sumbernya emang ga punya info role) dengan
lookup ke rosters.json berdasarkan (player_name, season_number).

First_Team/Second_Team tidak disentuh - udah punya role asli dari icon
lane di tabelnya sendiri, lebih akurat daripada roster (roster cuma role
default sepanjang season, bukan role spesifik pas menang award).

Kalau player ga ketemu di rosters.json, role tetap None - keterbatasan,
bukan ditebak.

Jalanin ini SETELAH scrape_rosters.py dan scrape_awards.py.
Cara pakai: python enrich_awards_role.py
"""

import utils


def build_role_lookup(rosters):
    """(player_name, season_number) -> role. Kalau ada duplikat, ambil yang pertama ketemu."""
    lookup = {}
    for r in rosters:
        key = (r.get("player_name"), r.get("season_number"))
        role = r.get("role")
        if key not in lookup and role:
            lookup[key] = role
    return lookup


def enrich_awards_role():
    rosters = utils.load_json("rosters.json")
    awards = utils.load_json("awards.json")
    role_lookup = build_role_lookup(rosters)

    filled = 0
    still_missing = 0
    for a in awards:
        if a.get("role") is not None:
            continue
        role = role_lookup.get((a.get("player_name"), a.get("season_number")))
        if role:
            a["role"] = role
            filled += 1
        else:
            still_missing += 1

    print(f"[INFO] role terisi dari roster: {filled}")
    print(f"[INFO] role masih kosong: {still_missing}")
    return awards


if __name__ == "__main__":
    utils.save_json(enrich_awards_role(), "awards.json")