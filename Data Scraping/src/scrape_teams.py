"""
Scraper final standings tiap season MPL Indonesia, dari tabel di section
"Regular_Season" pada halaman /Season_N/Regular_Season.

Menghasilkan:
- data/teams.json        -> daftar master tim (nama unik, sudah dinormalisasi)
- data/team_seasons.json -> final_rank, match_record, game_record, diff per tim per season

Catatan: status partisipasi (FRA/INV/Q/NQ) sengaja tidak diambil - sumbernya
(tabel "Team participation" di hub page) dimuat lewat JavaScript jadi ga
kebaca lewat static request. Ini keterbatasan yang ditulis di README.

Test 1 season: python scrape_teams.py 17
Full run:      python scrape_teams.py
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


def _final_standings_block(table):
    """
    Tabel cuma punya satu header di awal, standings tiap minggu (Week 1-9)
    ditumpuk berurutan tanpa header ulang. Split-nya pakai patokan rank
    balik ke "1." (nandain minggu baru mulai), blok terakhir = final.
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
        raise RuntimeError("Blok standings tidak ketemu")
    return blocks[-1]


def _team_name(cell):
    # img alt / title link lebih bersih daripada text (ga kebawa simbol naik-turun peringkat)
    img = cell.find("img")
    if img and img.get("alt"):
        return utils.clean_text(img["alt"])

    link = cell.find("a")
    if link and link.get("title"):
        return utils.clean_text(link["title"])

    text = utils.clean_text(cell.get_text())
    return re.sub(r"[▲▼]\d+$", "", text).strip()


# nama section standings beda-beda antar season, dicoba berurutan
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
        f"Season {season_number}: section standings ga ketemu dari kandidat "
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
        result.append({
            "season_number": season_number,
            "final_rank": utils.clean_text(cells[0].get_text()),
            "team_name": normalize_team_name(raw_name),
            "team_name_raw": raw_name,
            "match_record": utils.clean_text(cells[2].get_text()),
            "game_record": utils.clean_text(cells[3].get_text()),
            "diff": utils.clean_text(cells[4].get_text()),
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