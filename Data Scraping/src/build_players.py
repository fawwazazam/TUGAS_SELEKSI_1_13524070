"""
Assembly players.json dari rosters.json. Bukan scraper baru, cuma
post-processing dari data yang udah di-scrape. Jalanin SETELAH scrape_rosters.py.

Dedup pakai player_name (canonical, dari title attribute link Liquipedia),
bukan player_name_raw (nickname bisa beda tiap season).

Cara pakai: python build_players.py
"""

import config
import utils


def build_players():
    rosters = utils.load_json("rosters.json")

    players = {}
    for r in rosters:
        name = r.get("player_name")
        if not name:
            continue
        if name not in players:
            players[name] = {"player_name": name, "nationality": r.get("nationality")}
        elif players[name]["nationality"] is None and r.get("nationality"):
            players[name]["nationality"] = r["nationality"]

    return sorted(players.values(), key=lambda p: p["player_name"].lower())


if __name__ == "__main__":
    utils.save_json(build_players(), "players.json")