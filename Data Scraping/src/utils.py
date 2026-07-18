"""Fungsi bantu scraping MPL Indonesia: fetch+cache, cleaning teks, simpan/baca JSON."""

import os
import re
import json
import time
import hashlib
import logging
import requests
from bs4 import BeautifulSoup

import config

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("mpl_scraper")

_last_request_time = 0.0


def _wait_for_rate_limit():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    remaining = config.REQUEST_DELAY_SECONDS - elapsed
    if remaining > 0:
        time.sleep(remaining)
    _last_request_time = time.time()


def _cache_path(url):
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return os.path.join(config.CACHE_DIR, key + ".html")


def fetch_html(url, use_cache=True):
    """Ambil HTML dari url, baca dari cache kalau sudah pernah di-fetch."""
    cache_file = _cache_path(url)
    if use_cache and os.path.exists(cache_file):
        logger.info(f"[cache] {url}")
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()

    last_error = None
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            _wait_for_rate_limit()
            logger.info(f"[fetch] {url} (percobaan {attempt}/{config.MAX_RETRIES})")
            resp = requests.get(url, headers=config.HEADERS, timeout=15)
            resp.raise_for_status()

            if use_cache:
                with open(cache_file, "w", encoding="utf-8") as f:
                    f.write(resp.text)
            return resp.text

        except requests.RequestException as e:
            last_error = e
            logger.warning(f"Gagal fetch {url}: {e}, retry {config.RETRY_BACKOFF_SECONDS}s lagi")
            time.sleep(config.RETRY_BACKOFF_SECONDS)

    raise RuntimeError(f"Gagal fetch {url} setelah {config.MAX_RETRIES}x coba: {last_error}")


def get_soup(url, use_cache=True):
    """fetch_html + parse ke BeautifulSoup."""
    return BeautifulSoup(fetch_html(url, use_cache=use_cache), "html.parser")


def find_heading(soup, section_id):
    """Cari heading h2/h3/h4 lewat id-nya. Handle id di span nested (skin MediaWiki lama)."""
    el = soup.find(id=section_id)
    if el is None:
        raise RuntimeError(f"Section '{section_id}' tidak ditemukan di halaman")
    if el.name in ("h2", "h3", "h4"):
        return el
    return el.find_parent(["h2", "h3", "h4"])


def find_tables_in_section(soup, section_id, max_tables=5):
    """
    Ambil semua <table> di antara heading section_id sampai heading
    level sama/lebih tinggi berikutnya. Return list karena satu section
    kadang punya beberapa tabel (misal tabel legend sebelum tabel data asli).
    """
    heading = find_heading(soup, section_id)
    level = int(heading.name[1])

    tables = []
    for el in heading.find_all_next():
        if el.name and el.name[0] == "h" and el.name[1:].isdigit() and int(el.name[1]) <= level:
            break
        if el.name == "table":
            tables.append(el)
        if len(tables) >= max_tables:
            break
    return tables


def clean_text(text):
    """Buang tanda referensi kayak [1], rapikan whitespace, trim."""
    if not text:
        return ""
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def link_title(link):
    """title attribute <a>, dibuang suffix redlink MediaWiki ' (page does not exist)'."""
    if link is None:
        return None
    title = clean_text(link.get("title"))
    if not title:
        return None
    return re.sub(r"\s*\(page does not exist\)\s*$", "", title).strip()


def save_json(data, filename):
    filepath = os.path.join(config.DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Tersimpan: {filepath} ({len(data)} entri)")


def load_json(filename):
    filepath = os.path.join(config.DATA_DIR, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)