"""
Ambil data season MPL Indonesia dari tabel "Events" pada halaman hub:
https://liquipedia.net/mobilelegends/MPL_Indonesia.

Tabel Events berisi semua season, jadi SEASON_RANGE diterapkan manual agar
output tetap terbatas pada S12-S17.

File keluaran: data/seasons.json
"""

import re
from datetime import datetime

import config
import utils
from scrape_teams import normalize_team_name

KNOWN_LOCATIONS = ("Jakarta", "Bandung", "Tangerang")


def _find_events_table(soup):
    # Cari lewat heading karena class CSS Liquipedia cukup sering berubah.
    heading = soup.find(id="Events")
    if heading is None:
        raise RuntimeError("Bagian 'Events' tidak ditemukan, cek struktur halaman manual")

    # Beberapa skin menaruh id pada heading, lainnya pada span di dalam heading.
    if heading.name in ("h2", "h3"):
        section = heading
    else:
        section = heading.find_parent(["h2", "h3"])

    table = section.find_next("table")
    if table is None:
        raise RuntimeError("Tabel setelah heading 'Events' tidak ditemukan")
    return table


def _column_index(header_cells):
    headers = [utils.clean_text(c.get_text()) for c in header_cells]
    return {name: i for i, name in enumerate(headers) if name}


def _cell_text(cell):
    # Sel Winner/Runner-up/Tournament kadang hanya berisi logo.
    text = utils.clean_text(cell.get_text())
    if text:
        return text

    img = cell.find("img")
    if img and img.get("alt"):
        return utils.clean_text(img["alt"])

    link = cell.find("a")
    if link and link.get("title"):
        return utils.clean_text(link["title"])

    return ""


def _team_text(cell):
    text = _cell_text(cell)
    return normalize_team_name(text) if text else None


def _parse_date_range(text):
    text = re.sub(r"\s+(?:-|\u2013|\u2014)\s+", " - ", text)
    start_text, end_text = text.split(" - ", 1)
    end_date = datetime.strptime(end_text, "%b %d, %Y").date()

    start_month = datetime.strptime(start_text.split()[0], "%b").month
    start_year = end_date.year - (1 if start_month > end_date.month else 0)
    start_date = datetime.strptime(f"{start_text}, {start_year}", "%b %d, %Y").date()
    return start_date.isoformat(), end_date.isoformat()


def _parse_prize_pool(text):
    return float(re.sub(r"[^\d.]", "", text))


def _parse_locations(text):
    return [location for location in KNOWN_LOCATIONS if location in text]


def scrape_seasons():
    allowed_seasons = set(config.SEASON_RANGE)

    soup = utils.get_soup(config.HUB_PAGE)
    table = _find_events_table(soup)

    rows = table.find_all("tr")
    header_cells = rows[0].find_all(["th", "td"])
    col = _column_index(header_cells)
    header_len = len(header_cells)

    seasons = []
    for row in rows[1:]:
        cells = row.find_all("td")
        if not cells:
            continue

        # Baris data bisa punya sel logo tambahan dibanding header.
        offset = max(0, len(cells) - header_len)

        def col_cell(name, cells=cells, offset=offset):
            return cells[col[name] + offset]

        name = _cell_text(col_cell("Tournament"))
        match = re.search(r"Season\s+(\d+)", name)
        if not match:
            continue

        season_number = int(match.group(1))
        if season_number not in allowed_seasons:
            continue

        start_date, end_date = _parse_date_range(_cell_text(col_cell("Date")))

        seasons.append({
            "season_number": season_number,
            "name": name,
            "start_date": start_date,
            "end_date": end_date,
            "prize_pool_usd": _parse_prize_pool(_cell_text(col_cell("Prize Pool"))),
            "locations": _parse_locations(_cell_text(col_cell("Location"))),
            "participant_count": _cell_text(col_cell("P#")),
            "winner": _team_text(col_cell("Winner")),
            "runner_up": _team_text(col_cell("Runner-up")),
        })

    seasons.sort(key=lambda s: s["season_number"])
    return seasons


if __name__ == "__main__":
    data = scrape_seasons()
    utils.save_json(data, "seasons.json")
