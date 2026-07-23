"""Config scraping MPL Indonesia - Seleksi Tahap 2 Asisten Lab Basdat 2026, 13524070."""

import os

# Identitas asli di User-Agent, sesuai etika pada panduan scraping.
NAMA = "A. Fawwaz Azam Wicaksono"
NIM = "13524070"
EMAIL = f"{NIM}@std.stei.itb.ac.id"
USER_AGENT = f"MPLIndonesiaScraper/1.0 ({NAMA} - {NIM} - ITB, tugas seleksi asisten lab basdat; {EMAIL})"
HEADERS = {"User-Agent": USER_AGENT}

BASE_URL = "https://liquipedia.net"
WIKI_PATH = "/mobilelegends"
HUB_PAGE = BASE_URL + WIKI_PATH + "/MPL_Indonesia"

# Cakupan final S12-S17; alasan lengkap ditulis di README.
SEASON_RANGE = range(12, 18)


def season_urls(season_number):
    base = f"{WIKI_PATH}/MPL/Indonesia/Season_{season_number}"
    return {
        "overview": BASE_URL + base,
        "regular_season": BASE_URL + base + "/Regular_Season",
        "playoffs": BASE_URL + base + "/Playoffs",
        "statistics": BASE_URL + base + "/Statistics",
    }


# Rate limit ke server Liquipedia.
REQUEST_DELAY_SECONDS = 2.0
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5.0

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CACHE_DIR = os.path.join(PROJECT_ROOT, "src", ".html_cache")
TEAM_ALIASES_PATH = os.path.join(PROJECT_ROOT, "src", "team_aliases.json")
ROLE_ALIASES_PATH = os.path.join(PROJECT_ROOT, "src", "role_aliases.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
