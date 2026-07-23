"""
Scraper final standings tiap season MPL Indonesia, dari tabel di bagian
"Regular_Season" pada halaman /Season_N/Regular_Season.

Menghasilkan:
- data/teams.json        -> daftar master tim (nama unik, sudah dinormalisasi)
- data/team_seasons.json -> rank, win/loss match, dan win/loss game per team-season

Catatan: status partisipasi (FRA/INV/Q/NQ) tidak diambil karena tabel
"Team participation" dimuat melalui JavaScript dan tidak tersedia pada
request statis.

Tes 1 season: python scrape_teams.py 17
Jalankan penuh: python scrape_teams.py
"""

import json
import re
import sys

import config
import utils


def _load_team_alias_map():
    with open(config.TEAM_ALIASES_PATH, encoding="utf-8") as f:
        raw = json.load(f)

    mapping = {}
    for group in raw["groups"]:
        for alias in group["aliases"]:
            mapping[alias] = group["canonical_name"]
    return mapping


TEAM_ALIAS_MAP = _load_team_alias_map()


def normalize_team_name(name):
    return TEAM_ALIAS_MAP.get(name, name)


def _is_rank_cell(text):
    return bool(re.match(r"^\d+\.$", text))


def _parse_record(text):
    wins, losses = text.split("-", 1)
    return int(wins), int(losses)


def _parse_game_record(game_record, diff):
    # S12 memakai game_record sebagai win rate dan diff sebagai "game wins-losses".
    # S13+ memakai game_record sebagai "game wins-losses" dan diff sebagai delta.
    return _parse_record(diff if game_record.endswith("%") else game_record)


def _final_standings_block(table):
    """
    Tabel memiliki satu header dan beberapa blok standings mingguan. Blok baru
    dimulai saat rank kembali ke "1."; blok terakhir adalah standings final.
    """
    data_rows = []
    for row in table.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) < 5:
            continue
        if _is_rank_cell(utils.clean_text(cells[0].get_text())):
            data_rows.append(cells)

    blocks = []
    current = None
    for cells in data_rows:
        if utils.clean_text(cells[0].get_text()) == "1.":
            current = []
            blocks.append(current)
        if current is not None:
            current.append(cells)

    if not blocks:
        raise RuntimeError("Blok standings tidak ditemukan")
    return blocks[-1]


def _team_name(cell):
    # Alt/title gambar lebih bersih karena tidak membawa simbol perubahan rank.
    img = cell.find("img")
    if img and img.get("alt"):
        return utils.clean_text(img["alt"])

    link = cell.find("a")
    if link and link.get("title"):
        return utils.clean_text(link["title"])

    text = utils.clean_text(cell.get_text())
    return re.sub(r"[\u25b2\u25bc]\d+$", "", text).strip()


# Nama bagian standings berbeda antar season.
STANDINGS_SECTION_CANDIDATES = ["Regular_Season", "Results", "Detailed_Results", "Group_Stage"]


def _find_standings_table(soup, season_number):
    last_error = None
    for section_id in STANDINGS_SECTION_CANDIDATES:
        try:
            tables = utils.find_tables_in_section(soup, section_id)
            if tables:
                return tables[0]
        except RuntimeError as e:
            last_error = e
            continue
    raise RuntimeError(
        f"Season {season_number}: bagian standings tidak ditemukan dari kandidat "
        f"{STANDINGS_SECTION_CANDIDATES} (error terakhir: {last_error})"
    )


def scrape_season_standings(season_number):
    url = config.season_urls(season_number)["regular_season"]
    soup = utils.get_soup(url)

    table = _find_standings_table(soup, season_number)
    standings_rows = _final_standings_block(table)

    result = []
    for cells in standings_rows:
        raw_name = _team_name(cells[1])
        match_wins, match_losses = _parse_record(utils.clean_text(cells[2].get_text()))
        game_wins, game_losses = _parse_game_record(
            utils.clean_text(cells[3].get_text()),
            utils.clean_text(cells[4].get_text()),
        )
        result.append({
            "season_number": season_number,
            "final_rank": int(utils.clean_text(cells[0].get_text()).rstrip(".")),
            "team_name": normalize_team_name(raw_name),
            "team_name_raw": raw_name,
            "match_wins": match_wins,
            "match_losses": match_losses,
            "game_wins": game_wins,
            "game_losses": game_losses,
        })
    return result


def scrape_all_teams_and_standings():
    team_seasons = []
    team_names = set()

    for season_number in config.SEASON_RANGE:
        try:
            rows = scrape_season_standings(season_number)
        except Exception as e:
            print(f"[SKIP] Season {season_number}: {e}")
            continue

        team_names.update(r["team_name"] for r in rows)
        team_seasons.extend(rows)

    teams = [{"team_name": name} for name in sorted(team_names) if name]
    return teams, team_seasons


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for r in scrape_season_standings(int(sys.argv[1])):
            print(r)
    else:
        teams, team_seasons = scrape_all_teams_and_standings()
        utils.save_json(teams, "teams.json")
        utils.save_json(team_seasons, "team_seasons.json")
