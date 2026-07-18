"""
Normalisasi nama role PLAYER (bukan role staff/kelas hero), supaya
konsisten lintas sumber:
- roster (scrape_rosters.py) pakai label kayak "Jungler"/"Middle"
- First_Team/Second_Team (scrape_awards.py) pakai "Jungle"/"Mid Lane"
Beda template Liquipedia, tapi maksudnya sama - dinormalisasi ke 1 istilah
canonical lewat role_aliases.json.

CATATAN: role kelas hero dari Dream_Team (Fighter/Assassin/Mage/Marksman/
Tank) dan role staff (Head Coach/Analyst/dst) TIDAK lewat sini. Itu bukan
role player (lane position), jadi jangan dipaksa dinormalisasi pakai
mapping ini - biarin field terpisah / None sesuai konteksnya masing-masing.
"""

import json

import config


def _load_role_alias_map():
    with open(config.ROLE_ALIASES_PATH, encoding="utf-8") as f:
        raw = json.load(f)

    mapping = {}
    for group in raw["groups"]:
        canonical = group["canonical_name"]
        for alias in group["aliases"]:
            mapping[alias] = canonical
    return mapping


ROLE_ALIAS_MAP = _load_role_alias_map()


def normalize_role(raw_role):
    """Role yang ga ada di role_aliases.json dipakai apa adanya (biar ketauan kalau ada label baru yang belum di-cover)."""
    if raw_role is None:
        return None
    return ROLE_ALIAS_MAP.get(raw_role, raw_role)