"""
Isi role award yang masih kosong dari rosters.json berdasarkan
(player_name, season_number).

First Team dan Second Team sudah membawa role lane ternormalisasi dari scraper.
Dream Team dan award format panjang tidak, sehingga role diambil dari roster
yang sesuai.
"""

import utils


def build_role_lookup(rosters):
    """Buat pemetaan (player_name, season_number) -> role dari baris roster."""
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
