"""
Scraper untuk section "Player awards" di hub page MPL Indonesia.

Ada 2 pola tabel:
1. Long format (Regular_Season_MVP, Finals_MVP, Most_Improved, Rising_Star,
   Rookie_of_The_Season): tiap baris = Season | Player | Team.
2. Wide format (Dream_Team, First_Team, Second_Team): kolom dikelompokkan
   per beberapa season, ditandai header "Role" yang berulang tiap awal
   grup. Tiap baris = satu role, isinya player+team per season dalam grup itu.

Role di Dream_Team pakai taksonomi kelas hero (Fighter/Assassin/Mage/
Marksman/Tank), beda dari First_Team/Second_Team yang pakai taksonomi lane
(EXP Lane/Jungle/Mid Lane/Gold Lane/Roamer) - bukan bug, sumber datanya
emang beda. Role disimpan apa adanya per sumber, tidak dipaksa diseragamkan.

Role diekstrak dari nama file icon di href (alt/title-nya kosong), contoh:
    /mobilelegends/File:Mobile_Legends_Fighter_icon.png -> "Fighter"
    /mobilelegends/File:Mobile_Legends_EXP_Lane.png     -> "EXP Lane"

Test 1 section: python scrape_awards.py Regular_Season_MVP
Full run:       python scrape_awards.py
"""

import re
import sys

import config
import utils
from role_utils import normalize_role
from scrape_teams import normalize_team_name

LONG_FORMAT_SECTIONS = {
    "Regular_Season_MVP": "Regular Season MVP",
    "Finals_MVP": "Finals MVP",
    "Most_Improved": "Most Improved",
    "Rising_Star": "Rising Star",
    "Rookie_of_The_Season": "Rookie of The Season",
}

WIDE_FORMAT_SECTIONS = {
    # Dream_Team icon-nya kelas hero (Fighter/Assassin/dst), bukan lane
    # player, jadi extract_role=False - role dibiarin None kayak award lain
    "Dream_Team": {"award_type": "Dream Team", "extract_role": False},
    "First_Team": {"award_type": "First Team", "extract_role": True},
    "Second_Team": {"award_type": "Second Team", "extract_role": True},
}


def _parse_role_from_icon_cell(cell):
    """Ambil nama role dari filename icon di href, karena alt/title-nya kosong."""
    a = cell.find("a", class_="image")
    if not a or not a.get("href"):
        return None
    m = re.search(r"File:Mobile_Legends_(.+?)\.png", a["href"])
    if not m:
        return None
    raw = re.sub(r"_icon$", "", m.group(1))
    return raw.replace("_", " ").strip()


def _parse_player_team_cell(cell):
    """Player = <a> paling luar cell (bukan yang nested di team-template-team-part,
    itu link tim). Team = alt img tim."""
    team_container = cell.find(class_="team-template-team-part")

    player_link = None
    for a in cell.find_all("a"):
        if team_container is not None and a in team_container.find_all("a"):
            continue
        player_link = a
        break

    if player_link is not None:
        player_raw = utils.clean_text(player_link.get_text())
        player_name = utils.link_title(player_link) or player_raw
    else:
        player_raw = utils.clean_text(cell.get_text())
        player_name = player_raw

    img = cell.find("img")
    team_raw = utils.clean_text(img["alt"]) if img and img.get("alt") else None

    return player_name, player_raw, team_raw


def _parse_season_number(text):
    m = re.search(r"(\d+)", text)
    return int(m.group(1)) if m else None


def _parse_wide_header(header_row):
    """Scan header row: tiap cell "Role" mulai grup baru, cell sesudahnya
    sampai "Role" berikutnya adalah kolom season di grup itu."""
    cells = header_row.find_all(["th", "td"])
    groups = []
    current = None
    for idx, c in enumerate(cells):
        label = utils.clean_text(c.get_text())
        if label == "Role":
            current = {"role_col": idx, "seasons": []}
            groups.append(current)
            continue
        if current is None:
            continue
        link = c.find("a")
        season_text = utils.clean_text(link["title"]) if link and link.get("title") else label
        current["seasons"].append({
            "col": idx,
            "season_number": _parse_season_number(season_text),
        })
    return groups


def _find_award_table(soup, section_id):
    tables = utils.find_tables_in_section(soup, section_id)
    if not tables:
        raise RuntimeError(f"Section '{section_id}': tabel tidak ketemu")
    return tables[0]


def scrape_long_format(soup, section_id, award_type):
    table = _find_award_table(soup, section_id)
    rows = table.find_all("tr")

    results = []
    for row in rows[1:]:
        cells = row.find_all(["th", "td"])
        if len(cells) < 3:
            continue

        season_number = _parse_season_number(utils.clean_text(cells[0].get_text()))

        player_link = cells[1].find("a")
        player_raw = utils.clean_text(cells[1].get_text())
        player = utils.link_title(player_link) or player_raw

        img = cells[2].find("img")
        team_raw = (
            utils.clean_text(img["alt"]) if img and img.get("alt")
            else utils.clean_text(cells[2].get_text())
        )

        if not player:
            continue

        results.append({
            "award_type": award_type,
            "season_number": season_number,
            "player_name": player,
            "player_name_raw": player_raw,
            "team_name": normalize_team_name(team_raw) if team_raw else None,
            "team_name_raw": team_raw,
            "role": None,
        })
    return results


def scrape_wide_format(soup, section_id, award_type, extract_role=True):
    table = _find_award_table(soup, section_id)
    rows = table.find_all("tr")
    if not rows:
        raise RuntimeError(f"Section '{section_id}': tabel kosong")

    groups = _parse_wide_header(rows[0])
    if not groups:
        raise RuntimeError(f"Section '{section_id}': header grup 'Role' tidak ketemu")

    results = []
    for row in rows[1:]:
        cells = row.find_all(["th", "td"])
        if not cells:
            continue

        for group in groups:
            role = normalize_role(_parse_role_from_icon_cell(cells[group["role_col"]])) if extract_role else None

            for s in group["seasons"]:
                player, player_raw, team_raw = _parse_player_team_cell(cells[s["col"]])
                if not player:
                    continue

                results.append({
                    "award_type": award_type,
                    "season_number": s["season_number"],
                    "player_name": player,
                    "player_name_raw": player_raw,
                    "team_name": normalize_team_name(team_raw) if team_raw else None,
                    "team_name_raw": team_raw,
                    "role": role,
                })
    return results


def scrape_all_awards():
    """Beda dari scrape_teams.py: tabel di hub page ini isinya semua season
    sekaligus, bukan loop per season page - jadi scope difilter manual di sini."""
    allowed_seasons = set(config.SEASON_RANGE)
    soup = utils.get_soup(config.HUB_PAGE)
    all_results = []

    for section_id, award_type in LONG_FORMAT_SECTIONS.items():
        try:
            all_results.extend(scrape_long_format(soup, section_id, award_type))
        except Exception as e:
            print(f"[SKIP] {section_id}: {e}")

    for section_id, cfg in WIDE_FORMAT_SECTIONS.items():
        try:
            all_results.extend(
                scrape_wide_format(soup, section_id, cfg["award_type"], extract_role=cfg["extract_role"])
            )
        except Exception as e:
            print(f"[SKIP] {section_id}: {e}")

    filtered = [r for r in all_results if r["season_number"] in allowed_seasons]
    dropped = len(all_results) - len(filtered)
    if dropped:
        print(f"[INFO] {dropped} baris award di luar scope season "
              f"({min(allowed_seasons)}-{max(allowed_seasons)}) dibuang")

    return filtered


if __name__ == "__main__":
    if len(sys.argv) > 1:
        section = sys.argv[1]
        soup = utils.get_soup(config.HUB_PAGE)

        if section in LONG_FORMAT_SECTIONS:
            rows = scrape_long_format(soup, section, LONG_FORMAT_SECTIONS[section])
        elif section in WIDE_FORMAT_SECTIONS:
            cfg = WIDE_FORMAT_SECTIONS[section]
            rows = scrape_wide_format(soup, section, cfg["award_type"], extract_role=cfg["extract_role"])
        else:
            print(f"Section '{section}' tidak dikenal. Pilihan:")
            print(list(LONG_FORMAT_SECTIONS) + list(WIDE_FORMAT_SECTIONS))
            sys.exit(1)

        for r in rows:
            print(r)
    else:
        utils.save_json(scrape_all_awards(), "awards.json")