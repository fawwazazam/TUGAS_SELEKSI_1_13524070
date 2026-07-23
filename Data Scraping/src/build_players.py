"""
Bentuk players.json dari data roster yang sudah dinormalisasi.

Pemain didedup berdasarkan player_name kanonik dari title link Liquipedia,
bukan player_name_raw karena nickname bisa berbeda antar season.
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
