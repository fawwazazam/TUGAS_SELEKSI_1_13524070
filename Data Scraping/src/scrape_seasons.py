"""
Scraper data season MPL Indonesia, dari tabel "Events" di hub page
https://liquipedia.net/mobilelegends/MPL_Indonesia.

Tabel Events isinya semua season sekaligus (bukan per-page kayak
scrape_teams.py dkk), jadi SEASON_RANGE difilter manual di sini biar
scope-nya konsisten (S12-S17).

Output: data/seasons.json
"""

import re

import config
import utils


def _find_events_table(soup):
    # cari lewat heading, bukan class - class Liquipedia sering berubah
    heading = soup.find(id="Events")
    if heading is None:
        raise RuntimeError("Section 'Events' tidak ditemukan, cek struktur halaman manual")

    # id section kadang langsung di <h2>, kadang di <span> nested (skin lama)
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
    # Winner/Runner-up/Tournament kadang isinya cuma logo, teks-nya kosong -
    # coba ambil dari alt gambar kalau begitu
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

        # baris data punya cell lebih banyak dari header (ada logo tim di
        # depan) - hitung selisihnya, jangan asumsikan selalu sama
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

        seasons.append({
            "season_number": season_number,
            "name": name,
            "date_range": _cell_text(col_cell("Date")),
            "prize_pool": _cell_text(col_cell("Prize Pool")),
            "location": _cell_text(col_cell("Location")),
            "participant_count": _cell_text(col_cell("P#")),
            "winner": _cell_text(col_cell("Winner")) or None,
            "runner_up": _cell_text(col_cell("Runner-up")) or None,
        })

    seasons.sort(key=lambda s: s["season_number"])
    return seasons


if __name__ == "__main__":
    data = scrape_seasons()
    utils.save_json(data, "seasons.json")