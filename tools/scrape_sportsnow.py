#!/usr/bin/env python3
"""
SportsNow Schedule Scraper
Scrapes yoga class schedules from studios using the SportsNow booking platform.

Uses the public endpoint: https://www.sportsnow.ch/providers/{slug}/schedule?locale=de
which returns a clean HTML table with day headers, times, class names, and teachers.

Usage:
    python3 tools/scrape_sportsnow.py          # scrape all SportsNow studios
    python3 tools/scrape_sportsnow.py --dry-run # preview without saving
"""

import json
import glob
import re
import sys
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('sportsnow-scraper')

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'

HEADERS = {
    'User-Agent': 'YogaKurseBasel/1.0 (https://yogakursebasel.ch; info aggregator)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'de-CH,de;q=0.9,en;q=0.8',
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# Known SportsNow slug overrides (studio_id -> sportsnow_slug)
SPORTSNOW_SLUGS = {
    'ayana-yoga-schaffhausen': 'ayana-yoga',
    'yogaflowzug': 'yogaflowzug',
    'hot-yoga-christoph-herren': 'hot-yoga-christoph-herren',
    'goyoga-sarnen': 'goyoga-sarnen',
    'mii-ruum': 'mii-ruum-yoga-und-pilates-luzern',
    'yoga-carmen-bern': 'yoga-carmen',
    'openyoga-bern': 'openyoga',
    'studio-8-st-gallen': 'studio-8',
}

# Day name mapping (German -> English)
DAY_MAP = {
    'montag': 'Monday', 'dienstag': 'Tuesday', 'mittwoch': 'Wednesday',
    'donnerstag': 'Thursday', 'freitag': 'Friday', 'samstag': 'Saturday',
    'sonntag': 'Sunday',
}


def fetch_page(url, timeout=15):
    """Fetch a page with error handling."""
    try:
        resp = SESSION.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def discover_sportsnow_slug(studio):
    """
    Try to discover the SportsNow slug by:
    1. Checking known slug overrides
    2. Fetching the studio's website/schedule page for embedded SportsNow URLs
    3. Trying common slug patterns based on the studio name
    """
    studio_id = studio.get('id', '')

    # Check known overrides first
    if studio_id in SPORTSNOW_SLUGS:
        return SPORTSNOW_SLUGS[studio_id]

    # Check studio data for an explicit slug
    if studio.get('sportsnow_slug'):
        return studio['sportsnow_slug']

    # Fetch studio pages and look for sportsnow URLs
    website = studio.get('website', '') or ''
    schedule_url = studio.get('schedule_url', '') or ''

    urls_to_check = []
    if schedule_url:
        urls_to_check.append(schedule_url)
    if website and website != schedule_url:
        urls_to_check.append(website)

    for url in urls_to_check:
        html = fetch_page(url, timeout=10)
        if not html:
            continue

        slugs = re.findall(
            r'sportsnow\.ch/(?:go|providers)/([a-zA-Z0-9_-]+)', html)
        if slugs:
            return slugs[0]

        # Check subpages for schedule links
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=re.compile(
                r'(?:stundenplan|schedule|kurse|classes)', re.I)):
            href = link.get('href', '')
            if href.startswith('/'):
                base = '/'.join(url.split('/')[:3])
                sub_url = base + href
            elif href.startswith('http'):
                sub_url = href
            else:
                continue

            sub_html = fetch_page(sub_url, timeout=10)
            if sub_html:
                sub_slugs = re.findall(
                    r'sportsnow\.ch/(?:go|providers)/([a-zA-Z0-9_-]+)',
                    sub_html)
                if sub_slugs:
                    return sub_slugs[0]

    # Try common slug patterns
    name = studio.get('name', '')
    name_slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    id_slug = studio_id

    for guess in [name_slug, id_slug]:
        if not guess:
            continue
        url = f'https://www.sportsnow.ch/providers/{guess}/schedule?locale=de'
        try:
            resp = SESSION.get(url, timeout=8, allow_redirects=False)
            if resp.status_code == 200:
                logger.info(f"  Discovered slug by guessing: {guess}")
                return guess
        except requests.RequestException:
            pass

    return None


def scrape_sportsnow_schedule(studio):
    """
    Scrape schedule from SportsNow using the /providers/{slug}/schedule endpoint.

    The endpoint returns a clean HTML table with:
    - Day headers as <tr><td colspan="6">Montag</td></tr>
    - Class rows with columns: Zeit, Stunde, Leitung, Ort/Raum, Bemerkung, Aktion

    Returns a list of class entry dicts, or None if scraping fails.
    """
    studio_id = studio.get('id', '')
    studio_name = studio.get('name', '')

    slug = discover_sportsnow_slug(studio)
    if not slug:
        logger.warning(f"  No SportsNow slug found for {studio_name}")
        return None

    url = f'https://www.sportsnow.ch/providers/{slug}/schedule?locale=de'
    logger.info(f"  Fetching: {url}")

    html = fetch_page(url, timeout=15)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')

    table = soup.find('table')
    if not table:
        logger.warning(f"  No schedule table found for {studio_name} ({slug})")
        return None

    classes = []
    current_day = None

    for tr in table.find_all('tr'):
        tds = tr.find_all('td')

        if not tds:
            continue

        # Day header row: single td with colspan
        if len(tds) == 1 and tds[0].get('colspan'):
            day_text = tds[0].get_text(strip=True).lower()
            for de_day, en_day in DAY_MAP.items():
                if de_day in day_text:
                    current_day = en_day
                    break
            continue

        # Class row: 6 columns (Zeit, Stunde, Leitung, Ort/Raum, Bemerkung, Aktion)
        if len(tds) >= 3 and current_day:
            time_text = tds[0].get_text(strip=True)
            class_name = tds[1].get_text(strip=True) if len(tds) > 1 else ''
            teacher = tds[2].get_text(strip=True) if len(tds) > 2 else ''

            # Parse time range (e.g., "09:00 - 10:15")
            time_match = re.search(
                r'(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})', time_text)

            if time_match and class_name:
                # Clean class name: strip date ranges like "/ 15.09.2025 - 23.03.2026"
                class_name = re.sub(
                    r'\s*/?\s*\d{2}\.\d{2}\.\d{4}\s*[-–]\s*\d{2}\.\d{2}\.\d{4}',
                    '', class_name).strip()
                # Clean teacher name
                teacher = re.sub(r'^\d+\)\s*', '', teacher).strip()

                classes.append({
                    'studio_id': studio_id,
                    'studio_name': studio_name,
                    'day': current_day,
                    'time_start': time_match.group(1),
                    'time_end': time_match.group(2),
                    'class_name': class_name,
                    'teacher': teacher,
                    'level': 'all',
                    'source': url,
                    'verified': True,
                })

    if classes:
        logger.info(f"  Extracted {len(classes)} classes for {studio_name}")
    else:
        logger.warning(f"  No classes parsed from table for {studio_name} ({slug})")

    return classes if classes else None


def find_sportsnow_studios():
    """
    Read all studios_*.json files and find studios using SportsNow.

    Returns a list of tuples: (canton_name, studio_dict)
    """
    pattern = str(DATA_DIR / 'studios_*.json')
    studios = []

    for fpath in sorted(glob.glob(pattern)):
        if fpath.endswith('.enc.json'):
            continue

        canton = Path(fpath).stem.replace('studios_', '')

        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for s in data.get('studios', []):
            if not s.get('active', True):
                continue
            bp = (s.get('booking_platform', '') or '').lower()
            su = (s.get('schedule_url', '') or '').lower()
            ws = (s.get('website', '') or '').lower()

            if bp == 'sportsnow' or 'sportsnow' in su or 'sportsnow' in ws:
                studios.append((canton, s))

    return studios


def load_schedule_file(canton):
    """Load a canton's schedule file."""
    fpath = DATA_DIR / f'schedule_{canton}.json'
    if fpath.exists():
        with open(fpath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'last_updated': None, 'classes': []}


def save_schedule_file(canton, data):
    """Save a canton's schedule file."""
    fpath = DATA_DIR / f'schedule_{canton}.json'
    with open(fpath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')
    logger.info(f"Saved {fpath}")


def update_schedule_for_studio(schedule_data, studio_id, new_classes):
    """Replace all entries for a studio in the schedule data with new classes."""
    now_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    existing = schedule_data.get('classes', [])

    # Remove old entries for this studio
    existing = [c for c in existing if c.get('studio_id') != studio_id]

    # Add new entries with timestamp
    for entry in new_classes:
        entry['last_checked'] = now_date

    existing.extend(new_classes)
    schedule_data['classes'] = existing
    schedule_data['last_updated'] = datetime.now(timezone.utc).isoformat()


def main():
    dry_run = '--dry-run' in sys.argv

    logger.info("=== SportsNow Schedule Scraper ===")
    if dry_run:
        logger.info("DRY RUN: no files will be modified")

    # Find all SportsNow studios
    sportsnow_studios = find_sportsnow_studios()
    logger.info(f"Found {len(sportsnow_studios)} SportsNow studios across all cantons")

    total_classes = 0
    success_count = 0
    fail_count = 0
    results_by_canton = {}  # canton -> list of new classes

    for canton, studio in sportsnow_studios:
        studio_name = studio.get('name', 'Unknown')
        studio_id = studio.get('id', '')
        logger.info(f"\n--- {studio_name} [{canton}] ---")

        classes = scrape_sportsnow_schedule(studio)

        if classes:
            success_count += 1
            total_classes += len(classes)

            if canton not in results_by_canton:
                results_by_canton[canton] = []
            results_by_canton[canton].append((studio_id, classes))

            for c in classes:
                logger.info(f"  {c['day']:10s} {c['time_start']}-{c['time_end']}  "
                           f"{c['class_name']:<30s}  {c['teacher']}")
        else:
            fail_count += 1
            logger.warning(f"  FAILED to scrape {studio_name}")

        # Be polite: wait between requests
        time.sleep(1)

    # Update schedule files
    if not dry_run:
        for canton, studio_classes_list in results_by_canton.items():
            sched_data = load_schedule_file(canton)

            for studio_id, new_classes in studio_classes_list:
                update_schedule_for_studio(sched_data, studio_id, new_classes)

            # Update metadata
            sched_data['_meta'] = {
                'last_updated': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                'note': 'Stundenplan-Daten aus öffentlichen Quellen. Für aktuelle Zeiten siehe Studio-Website.',
            }

            save_schedule_file(canton, sched_data)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info(f"RESULTS: {success_count} studios scraped, {fail_count} failed")
    logger.info(f"TOTAL:   {total_classes} classes extracted")
    logger.info(f"CANTONS: {len(results_by_canton)} schedule files updated")
    if dry_run:
        logger.info("(DRY RUN - no files were modified)")
    logger.info("=" * 60)

    return success_count, fail_count, total_classes


if __name__ == '__main__':
    main()
