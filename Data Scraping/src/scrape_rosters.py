"""
Scraper roster dari section "Participating Teams" di tiap halaman /Season_N
(bukan hub page, section ini per-season).

Scope (keputusan sadar, ditulis di README):
- Season dibatasi S12-S17 (config.SEASON_RANGE), bukan full S1-S17 - era
  franchise formatnya paling stabil, waktu pengerjaan terbatas.
- Cuma tab Main/Subs/Staff yang diproses, tab "Former" di-skip.
- Captaincy/Vice-Captaincy tidak diambil, bukan prioritas.

Struktur section ini widget div (bukan <table>):
    div.team-participant
      > div.team-participant__grid
        > div.team-participant-card   (1 per tim)
          > switch-pill-option (label tab Main/Subs/Former/Staff - urutan
            & jumlah tab beda per tim, jangan hardcode index)
          > div[data-toggle-area-content=N]  (isi tiap tab)
            > div.team-participant-card__member  (1 per player/staff)

Role player pakai label icon (mis. "Jungler") yang beda penamaan dari role
di scrape_awards.py (mis. "Jungle") - dinormalisasi lewat role_utils.py.
Role staff (Head Coach dst) dibiarkan apa adanya, bukan lane position.

Test 1 season: python scrape_rosters.py 17
Full run:      python scrape_rosters.py
"""

import sys

import config
import utils
from role_utils import normalize_role
from scrape_teams import normalize_team_name


def _season_base_url(season_number):
    # halaman utama season (ada section Participating Teams) itu base dari regular_season url
    urls = config.season_urls(season_number)
    if "overview" in urls:
        return urls["overview"]
    return urls["regular_season"].rsplit("/Regular_Season", 1)[0]


ALLOWED_STATUS = {"main", "subs", "staff"}


def _parse_status_map(card):
    """Baca label tab & value toggle-nya per tim - urutan/jumlah tab beda-beda, jangan hardcode."""
    status_map = {}
    for pill in card.find_all("div", class_="switch-pill-option"):
        value = pill.get("data-switch-value")
        label = utils.clean_text(pill.get_text()).lower()
        if value and label in ALLOWED_STATUS:
            status_map[value] = label
    return status_map


def _parse_team_name(card):
    opp = card.find("div", class_="team-participant-card__opponent-full")
    if opp is None:
        opp = card.find("div", class_="team-participant-card__opponent-compact")
    if opp is None:
        return None
    link = opp.find("a")
    return utils.clean_text(link["title"]) if link and link.get("title") else None


def _parse_member(member_div):
    name_block = member_div.find("div", class_="block-player")
    if name_block is None:
        return None

    link = name_block.find("a")
    player_raw = utils.clean_text(link.get_text()) if link else None
    player_name = utils.link_title(link) or player_raw
    if not player_name:
        return None

    flag_img = name_block.find("img")
    nationality = utils.clean_text(flag_img["alt"]) if flag_img and flag_img.get("alt") else None

    role_left = member_div.find("div", class_="team-participant-card__member-role-left")
    role_left_text = None
    if role_left:
        img = role_left.find("img")
        raw_role = utils.clean_text(img["alt"]) if img and img.get("alt") else None
        role_left_text = normalize_role(raw_role)

    role_right = member_div.find("div", class_="team-participant-card__member-role-right")
    role_right_text = utils.clean_text(role_right.get_text()) if role_right else None

    return {
        "player_name": player_name,
        "player_name_raw": player_raw,
        "nationality": nationality,
        "role": role_left_text or role_right_text,
    }


def scrape_team_roster(card, season_number):
    team_raw = _parse_team_name(card)
    status_map = _parse_status_map(card)

    results = []
    for value, status_label in status_map.items():
        content = card.find(attrs={"data-toggle-area-content": value})
        if content is None:
            continue

        for m in content.find_all("div", class_="team-participant-card__member"):
            parsed = _parse_member(m)
            if parsed is None:
                continue
            results.append({
                "season_number": season_number,
                "team_name": normalize_team_name(team_raw) if team_raw else None,
                "team_name_raw": team_raw,
                "status": status_label,
                **parsed,
            })
    return results


def scrape_season_rosters(season_number):
    url = _season_base_url(season_number)
    soup = utils.get_soup(url)

    container = soup.find("div", class_="team-participant")
    if container is None:
        raise RuntimeError(f"Season {season_number}: div.team-participant tidak ketemu")

    cards = container.find_all("div", class_="team-participant-card")
    if not cards:
        raise RuntimeError(f"Season {season_number}: team-participant-card tidak ketemu")

    results = []
    for card in cards:
        results.extend(scrape_team_roster(card, season_number))
    return results


def scrape_all_rosters():
    all_results = []
    for season_number in config.SEASON_RANGE:
        try:
            rows = scrape_season_rosters(season_number)
        except Exception as e:
            print(f"[SKIP] Season {season_number}: {e}")
            continue
        all_results.extend(rows)
    return all_results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        season = int(sys.argv[1])
        rows = scrape_season_rosters(season)
        for r in rows:
            print(r)
        print(f"\nTotal: {len(rows)} baris")
    else:
        utils.save_json(scrape_all_rosters(), "rosters.json")