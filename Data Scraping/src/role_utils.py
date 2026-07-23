"""
Normalisasi label lane role Mobile Legends pada tabel roster dan award.

Role staff disimpan langsung dari data roster. Role Dream Team diisi dari
roster, bukan dari icon kelas hero yang muncul di tabel sumber.
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
    """Kembalikan role kanonik jika ada alias; selain itu pakai label sumber."""
    if raw_role is None:
        return None
    return ROLE_ALIAS_MAP.get(raw_role, raw_role)
