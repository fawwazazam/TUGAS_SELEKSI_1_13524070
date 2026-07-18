"""
Scraper match results, dari 2 sumber beda per stage:
- Regular Season: widget "brkts-matchlist" di /Season_N/Regular_Season
- Playoffs: tabel biasa (table2__table) di /Season_N/Playoffs

Scope: cuma skor akhir per matchup (mis. "2-1"), bukan detail tiap game
individual di dalam best-of-N (hero pick, durasi, dll - ada di popup match,
effort-nya jauh lebih besar, dievaluasi terpisah). Dicatat di README.
"""

import re
import sys

import config
import utils
from scrape_teams import normalize_team_name


def _find_week_headings(soup):
    """
    Cari heading yang id-nya match pola minggu pertandingan. Konvensi id
    beda antar era (RS:_Week_N vs Week_N polos), jumlah minggu juga beda
    tiap season - jangan hardcode.
    """
    headings = []
    for h in soup.find_all(["h2", "h3", "h4"]):
        hid = h.get("id")
        if hid is None:
            nested = h.find(id=True)
            hid = nested.get("id") if nested else None
        if hid and re.search(r"Week_\d+$", hid):
            headings.append((hid, h))
    return headings


def _matchlist_div_for_heading(heading_tag):
    """MediaWiki bungkus heading dalam div.mw-heading - isi section ada di
    sibling div itu, bukan sibling <h3> langsung."""
    header_tag = heading_tag if heading_tag.name in ("h2", "h3", "h4") else heading_tag.find_parent(["h2", "h3", "h4"])
    wrapper = header_tag.find_parent("div", class_="mw-heading")
    anchor = wrapper if wrapper is not None else header_tag
    return anchor.find_next_sibling("div", class_="brkts-matchlist")


def _parse_single_match(match_div):
    opponents = match_div.find_all("div", class_="brkts-matchlist-opponent")
    scores = match_div.find_all("div", class_="brkts-matchlist-score")
    if len(opponents) < 2 or len(scores) < 2:
        return None

    team_a_div, team_b_div = opponents[0], opponents[1]

    def _team_name(div):
        name_div = div.find("div", class_="team-name-dynamic")
        return name_div.get("data-team-name") if name_div else None

    team_a_raw = _team_name(team_a_div)
    team_b_raw = _team_name(team_b_div)
    if not team_a_raw or not team_b_raw:
        return None

    score_a = utils.clean_text(scores[0].get_text())
    score_b = utils.clean_text(scores[1].get_text())

    a_classes = team_a_div.get("class") or []
    b_classes = team_b_div.get("class") or []
    if "brkts-matchlist-slot-winner" in a_classes:
        winner_raw = team_a_raw
    elif "brkts-matchlist-slot-winner" in b_classes:
        winner_raw = team_b_raw
    else:
        winner_raw = None  # belum dimainkan / belum ke-detect

    return {
        "team_a": normalize_team_name(team_a_raw),
        "team_a_raw": team_a_raw,
        "team_b": normalize_team_name(team_b_raw),
        "team_b_raw": team_b_raw,
        "score_a": score_a,
        "score_b": score_b,
        "winner": normalize_team_name(winner_raw) if winner_raw else None,
    }


def _parse_week(matchlist_div, week_number, season_number):
    results = []
    collapse_area = matchlist_div.find("div", class_="brkts-matchlist-collapse-area")
    if collapse_area is None:
        return results

    current_day = None
    for child in collapse_area.find_all(recursive=False):
        classes = child.get("class") or []
        if "brkts-matchlist-header" in classes:
            current_day = utils.clean_text(child.get_text())
            continue
        if "brkts-matchlist-match" in classes:
            match = _parse_single_match(child)
            if match is None:
                continue
            match.update({
                "season_number": season_number,
                "stage": "Regular Season",
                "week": week_number,
                "day": current_day,
            })
            results.append(match)
    return results


def _parse_playoffs_score_cell(cell):
    """Format "0:<b>3</b>" -> get_text() gabung jadi "0:3". Winner ditentuin
    dari angka mana yang lebih besar, bukan posisi <b> (lebih robust)."""
    div = cell.find("div")
    text = utils.clean_text(div.get_text()) if div else utils.clean_text(cell.get_text())
    parts = text.split(":")
    if len(parts) != 2:
        return None, None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None, None


def _parse_playoffs_team_cell(cell):
    block = cell.find("div", class_="block-team")
    if block is None:
        return None
    return utils.link_title(block.find("a"))


def scrape_season_playoffs(season_number):
    url = config.season_urls(season_number)["playoffs"]
    soup = utils.get_soup(url)

    table = soup.find("table", class_="table2__table")
    if table is None:
        raise RuntimeError(f"Season {season_number}: tabel playoffs tidak ketemu")

    results = []
    for row in table.find_all("tr", class_="table2__row--body"):
        cells = row.find_all("td")
        if len(cells) < 5:
            continue

        round_name = utils.clean_text(cells[1].get_text())
        team_a_raw = _parse_playoffs_team_cell(cells[2])
        team_b_raw = _parse_playoffs_team_cell(cells[4])
        score_a, score_b = _parse_playoffs_score_cell(cells[3])

        if not team_a_raw or not team_b_raw or score_a is None:
            continue

        if score_a > score_b:
            winner_raw = team_a_raw
        elif score_b > score_a:
            winner_raw = team_b_raw
        else:
            winner_raw = None

        results.append({
            "team_a": normalize_team_name(team_a_raw),
            "team_a_raw": team_a_raw,
            "team_b": normalize_team_name(team_b_raw),
            "team_b_raw": team_b_raw,
            "score_a": str(score_a),
            "score_b": str(score_b),
            "winner": normalize_team_name(winner_raw) if winner_raw else None,
            "season_number": season_number,
            "stage": "Playoffs",
            "week": None,
            "day": round_name,  # field "day" dipake biar skema konsisten sama Regular Season
        })
    return results


def _scrape_regular_season(season_number):
    url = config.season_urls(season_number)["regular_season"]
    soup = utils.get_soup(url)

    week_headings = _find_week_headings(soup)
    if not week_headings:
        raise RuntimeError(f"Season {season_number}: heading 'RS:_Week_N' tidak ketemu")

    results = []
    for hid, heading in week_headings:
        m = re.search(r"Week_(\d+)", hid)
        week_number = int(m.group(1)) if m else None

        matchlist = _matchlist_div_for_heading(heading)
        if matchlist is None:
            print(f"[SKIP] Season {season_number} Week {week_number}: div.brkts-matchlist tidak ketemu")
            continue

        results.extend(_parse_week(matchlist, week_number, season_number))

    return results


def scrape_season_matches(season_number):
    """Gabungan Regular Season + Playoffs. Kalau salah satu gagal, yang lain tetap jalan."""
    results = []

    try:
        results.extend(_scrape_regular_season(season_number))
    except Exception as e:
        print(f"[SKIP] Season {season_number} Regular Season: {e}")

    try:
        results.extend(scrape_season_playoffs(season_number))
    except Exception as e:
        print(f"[SKIP] Season {season_number} Playoffs: {e}")

    return results


def scrape_all_matches():
    all_results = []
    for season_number in config.SEASON_RANGE:
        try:
            rows = scrape_season_matches(season_number)
        except Exception as e:
            print(f"[SKIP] Season {season_number}: {e}")
            continue
        all_results.extend(rows)
    return all_results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        season = int(sys.argv[1])
        rows = scrape_season_matches(season)
        for r in rows:
            print(r)
        print(f"\nTotal: {len(rows)} match")
    else:
        utils.save_json(scrape_all_matches(), "matches.json")