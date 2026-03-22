#!/usr/bin/env python3
"""
Yoga Kurse Basel — Studio Schedule & Price Scraper
Scrapes schedule and pricing data from yoga studio websites across all Swiss cantons.
Processes all canton-specific data files (data/studios_*.json).
Designed to run via GitHub Actions 4 times daily.
"""

import json
import os
import sys
import logging
import re
import glob
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('yoga-scraper')

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
TOOLS_DIR = PROJECT_ROOT / 'tools'
PRICE_CHANGELOG_FILE = TOOLS_DIR / 'price_changelog.json'
VERIFICATION_FILE = TOOLS_DIR / 'schedule_verification.json'

HEADERS = {
    'User-Agent': 'YogaKurseBasel/1.0 (https://yogakursebasel.ch; info aggregator)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'de-CH,de;q=0.9,en;q=0.8',
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def fetch_page(url, timeout=15):
    """Fetch a page, respecting robots.txt conventions."""
    try:
        resp = SESSION.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def check_robots_txt(base_url):
    """Check if scraping is allowed by robots.txt."""
    try:
        robots_url = base_url.rstrip('/') + '/robots.txt'
        resp = SESSION.get(robots_url, timeout=5)
        if resp.status_code == 200:
            content = resp.text.lower()
            if 'disallow: /' in content and 'user-agent: *' in content:
                lines = content.split('\n')
                user_agent_star = False
                for line in lines:
                    line = line.strip()
                    if line == 'user-agent: *':
                        user_agent_star = True
                    elif user_agent_star and line == 'disallow: /':
                        logger.info(f"Robots.txt disallows scraping: {base_url}")
                        return False
                    elif line.startswith('user-agent:'):
                        user_agent_star = False
        return True
    except requests.RequestException:
        return True


def scrape_eversports_widget(url):
    """Attempt to extract schedule info from pages using Eversports widgets."""
    html = fetch_page(url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'lxml')
    classes = []

    iframes = soup.find_all('iframe', src=re.compile(r'eversports', re.I))
    if iframes:
        logger.info(f"Found Eversports widget at {url}")
        for iframe in iframes:
            logger.info(f"  Eversports iframe: {iframe.get('src', '')}")

    return classes


def scrape_generic_schedule(studio):
    """Generic scraper that looks for schedule information on studio websites."""
    url = studio.get('schedule_url') or studio.get('website')
    if not url:
        return None

    base_url = '/'.join(url.split('/')[:3])
    if not check_robots_txt(base_url):
        return {'status': 'blocked', 'source_url': url, 'booking_links': []}

    html = fetch_page(url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'lxml')

    schedule_data = {
        'last_scraped': datetime.now(timezone.utc).isoformat(),
        'source_url': url,
        'status': 'scraped'
    }

    # Look for common schedule patterns — tables
    tables = soup.find_all('table')
    for table in tables:
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        schedule_keywords = ['montag', 'dienstag', 'mittwoch', 'donnerstag', 'freitag',
                           'samstag', 'sonntag', 'monday', 'tuesday', 'wednesday',
                           'thursday', 'friday', 'saturday', 'sunday',
                           'zeit', 'time', 'kurs', 'class', 'lehrer', 'teacher']
        if any(kw in ' '.join(headers).lower() for kw in schedule_keywords):
            schedule_data['has_schedule_table'] = True
            logger.info(f"  Found schedule table at {url}")

    # Check for booking platform links
    for platform in ['eversports', 'mindbody', 'momoyoga', 'fitogram', 'classpass']:
        links = soup.find_all('a', href=re.compile(platform, re.I))
        if links:
            schedule_data['booking_links'] = schedule_data.get('booking_links', [])
            for link in links:
                href = link.get('href', '')
                if href:
                    schedule_data['booking_links'].append({
                        'platform': platform,
                        'url': href
                    })

    return schedule_data


PRICE_PAGE_PATHS = ['/preise', '/prices', '/pricing', '/tarife', '/prix', '/angebot']

# Regex to find CHF amounts
CHF_PATTERN = re.compile(r'CHF\s*(\d+[\.,]?\d*)', re.IGNORECASE)

# Keywords that help classify a price (German, French, English)
PRICE_KEYWORDS = {
    'single': ['einzeleintritt', 'einzellektion', 'drop-in', 'drop in', 'single class',
               'cours unique', 'einzelstunde', 'einzelkurs'],
    'card_10': ['10er', '10-er', '10 er', '10 lektionen', '10 classes', '10 cours',
                '10er-abo', '10er abo', '10er-karte'],
    'monthly': ['monats', 'monatlich', 'monthly', 'mensuel', 'monatsabo', 'month'],
    'trial': ['probestunde', 'probelektion', 'schnuppern', 'trial', 'cours d\'essai',
              'probetraining', 'first class', 'erste stunde'],
    'abo': ['abo', 'abonnement', 'subscription', 'mitgliedschaft', 'membership'],
}


def scrape_prices(studio):
    """
    Attempt to scrape pricing information from a studio's website.

    Tries the main website and common price page paths. Looks for CHF amounts
    near pricing keywords and returns a structured pricing dict.
    """
    website = studio.get('website', '')
    if not website:
        return None

    base_url = website.rstrip('/')

    domain_url = '/'.join(base_url.split('/')[:3])
    if not check_robots_txt(domain_url):
        logger.info(f"  Price scraping blocked by robots.txt: {domain_url}")
        return None

    urls_to_try = [base_url]
    for path in PRICE_PAGE_PATHS:
        urls_to_try.append(base_url + path)

    all_prices = {}
    source_url = None

    for url in urls_to_try:
        html = fetch_page(url, timeout=10)
        if not html:
            continue

        soup = BeautifulSoup(html, 'lxml')
        text_content = soup.get_text(separator=' ', strip=True).lower()

        chf_matches = CHF_PATTERN.findall(text_content)
        if not chf_matches:
            continue

        page_prices = _extract_prices_from_soup(soup)
        if page_prices:
            all_prices.update(page_prices)
            source_url = url
            logger.info(f"  Found {len(page_prices)} price(s) at {url}")
            if any(path in url for path in PRICE_PAGE_PATHS):
                break

    if not all_prices:
        return None

    pricing = {
        'currency': 'CHF',
        'verified': True,
        'source': source_url,
        'last_checked': datetime.now(timezone.utc).isoformat(),
    }
    pricing.update(all_prices)
    return pricing


def _extract_prices_from_soup(soup):
    """
    Extract categorized prices from a BeautifulSoup document.

    Looks at text blocks containing CHF amounts and checks surrounding text
    for pricing keywords to classify each price.
    """
    prices = {}

    body = soup.find('body')
    if not body:
        return prices

    for element in body.find_all(string=CHF_PATTERN):
        parent = element.parent
        if not parent:
            continue

        grandparent = parent.parent if parent.parent else parent
        context_text = grandparent.get_text(separator=' ', strip=True).lower()
        context = context_text

        amounts = CHF_PATTERN.findall(element)

        for amount_str in amounts:
            try:
                amount = float(amount_str.replace(',', '.'))
            except ValueError:
                continue

            if amount < 5 or amount > 500:
                continue

            for category, keywords in PRICE_KEYWORDS.items():
                if any(kw in context for kw in keywords):
                    if category == 'abo' and any(k in prices for k in ['monthly', 'card_10']):
                        continue
                    prices[category] = amount
                    break

    return prices


# ---------------------------------------------------------------------------
# Canton-aware file handling
# ---------------------------------------------------------------------------

def load_all_canton_files():
    """
    Load all canton-specific studio files (data/studios_*.json, excluding .enc.json).

    Returns a list of tuples: (file_path, canton_name, data_dict).
    """
    pattern = str(DATA_DIR / 'studios_*.json')
    all_files = sorted(glob.glob(pattern))
    canton_files = []

    for fpath in all_files:
        if fpath.endswith('.enc.json'):
            continue
        canton_name = Path(fpath).stem.replace('studios_', '')
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            canton_files.append((fpath, canton_name, data))
            studio_count = len(data.get('studios', []))
            logger.info(f"Loaded {fpath} ({studio_count} studios)")
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load {fpath}: {e}")

    return canton_files


def save_canton_file(file_path, data):
    """Save a canton data dict back to its JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')
    logger.info(f"Saved {file_path}")


# ---------------------------------------------------------------------------
# Schedule file handling (canton-specific)
# ---------------------------------------------------------------------------

# Day name mapping for schedule parsing (DE/FR/EN -> English canonical)
DAY_MAP = {
    'montag': 'Monday', 'dienstag': 'Tuesday', 'mittwoch': 'Wednesday',
    'donnerstag': 'Thursday', 'freitag': 'Friday', 'samstag': 'Saturday',
    'sonntag': 'Sunday',
    'lundi': 'Monday', 'mardi': 'Tuesday', 'mercredi': 'Wednesday',
    'jeudi': 'Thursday', 'vendredi': 'Friday', 'samedi': 'Saturday',
    'dimanche': 'Sunday',
    'monday': 'Monday', 'tuesday': 'Tuesday', 'wednesday': 'Wednesday',
    'thursday': 'Thursday', 'friday': 'Friday', 'saturday': 'Saturday',
    'sunday': 'Sunday',
    'mon': 'Monday', 'tue': 'Tuesday', 'wed': 'Wednesday',
    'thu': 'Thursday', 'fri': 'Friday', 'sat': 'Saturday', 'sun': 'Sunday',
    'mo': 'Monday', 'di': 'Tuesday', 'mi': 'Wednesday',
    'do': 'Thursday', 'fr': 'Friday', 'sa': 'Saturday', 'so': 'Sunday',
}

# Time pattern: matches HH:MM or H:MM
TIME_PATTERN = re.compile(r'\b(\d{1,2}:\d{2})\b')


def load_verification_data():
    """Load schedule verification data to know which studios are scrapable."""
    if VERIFICATION_FILE.exists():
        try:
            with open(VERIFICATION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            logger.warning("Could not load schedule_verification.json")
    return {}


def load_all_schedule_files():
    """
    Load all canton-specific schedule files (data/schedule_*.json, excluding .enc.json).

    Returns a dict: canton_name -> (file_path, data_dict).
    """
    pattern = str(DATA_DIR / 'schedule_*.json')
    all_files = sorted(glob.glob(pattern))
    schedule_files = {}

    for fpath in all_files:
        if fpath.endswith('.enc.json'):
            continue
        canton_name = Path(fpath).stem.replace('schedule_', '')
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            schedule_files[canton_name] = (fpath, data)
            class_count = len(data.get('classes', []))
            logger.info(f"Loaded schedule {fpath} ({class_count} classes)")
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load schedule {fpath}: {e}")

    return schedule_files


def save_schedule_file(file_path, data):
    """Save a schedule data dict back to its JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')
    logger.info(f"Saved schedule {file_path}")


def _normalize_day(text):
    """Try to extract a canonical English day name from text."""
    text_lower = text.strip().lower()
    for key, value in DAY_MAP.items():
        if key in text_lower:
            return value
    return None


def scrape_schedule_classes(studio, schedule_url):
    """
    Attempt to scrape actual class entries from a studio's schedule page.

    Looks for schedule tables and structured content to extract:
    - day, time_start, time_end, class_name, teacher

    Returns a list of class entry dicts, or an empty list if nothing found.
    """
    html = fetch_page(schedule_url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'lxml')
    classes = []
    studio_id = studio.get('id', '')
    studio_name = studio.get('name', '')

    # Strategy 1: Look for schedule tables
    tables = soup.find_all('table')
    for table in tables:
        headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
        schedule_keywords = ['montag', 'dienstag', 'mittwoch', 'donnerstag', 'freitag',
                             'samstag', 'sonntag', 'monday', 'tuesday', 'wednesday',
                             'thursday', 'friday', 'saturday', 'sunday',
                             'zeit', 'time', 'kurs', 'class', 'tag', 'day']
        if not any(kw in ' '.join(headers) for kw in schedule_keywords):
            continue

        rows = table.find_all('tr')
        for row in rows:
            cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
            if len(cells) < 2:
                continue

            day = None
            times = []
            class_name = None
            teacher = None

            for cell in cells:
                if not day:
                    day = _normalize_day(cell)
                    if day:
                        continue

                found_times = TIME_PATTERN.findall(cell)
                if found_times and not times:
                    times = found_times[:2]
                    continue

                if not class_name and cell and not TIME_PATTERN.match(cell):
                    class_name = cell

            if day and times and class_name:
                entry = {
                    'studio_id': studio_id,
                    'studio_name': studio_name,
                    'day': day,
                    'time_start': times[0],
                    'time_end': times[1] if len(times) > 1 else '',
                    'class_name': class_name,
                    'teacher': teacher,
                    'level': 'all',
                }
                classes.append(entry)

    # Strategy 2: Look for day headings followed by class listings
    if not classes:
        for heading in soup.find_all(['h2', 'h3', 'h4', 'strong', 'b']):
            heading_text = heading.get_text(strip=True)
            day = _normalize_day(heading_text)
            if not day:
                continue

            # Look at siblings/next elements for class info
            sibling = heading.find_next_sibling()
            while sibling and sibling.name not in ['h2', 'h3', 'h4']:
                text = sibling.get_text(strip=True)
                found_times = TIME_PATTERN.findall(text)
                if found_times:
                    # Try to extract class name: text minus times
                    class_text = TIME_PATTERN.sub('', text).strip(' -–|/')
                    if class_text:
                        entry = {
                            'studio_id': studio_id,
                            'studio_name': studio_name,
                            'day': day,
                            'time_start': found_times[0],
                            'time_end': found_times[1] if len(found_times) > 1 else '',
                            'class_name': class_text.split('  ')[0].strip(),
                            'teacher': None,
                            'level': 'all',
                        }
                        classes.append(entry)
                sibling = sibling.find_next_sibling()

    if classes:
        logger.info(f"  Scraped {len(classes)} class(es) from {schedule_url}")
    return classes


def update_schedule_for_studio(schedule_data, studio, new_classes, schedule_url, verified):
    """
    Update schedule entries for a specific studio within a canton's schedule data.

    If verified=True (freshly scraped), replaces all entries for this studio.
    Otherwise, just updates the tracking fields on existing entries.
    """
    studio_id = studio.get('id', '')
    now_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    existing_classes = schedule_data.get('classes', [])

    if verified and new_classes:
        # Remove old entries for this studio and add new ones
        existing_classes = [c for c in existing_classes if c.get('studio_id') != studio_id]
        for entry in new_classes:
            entry['source'] = schedule_url
            entry['verified'] = True
            entry['last_checked'] = now_date
        existing_classes.extend(new_classes)
        logger.info(f"  Replaced schedule entries for {studio_id} ({len(new_classes)} classes)")
    else:
        # Mark existing entries as unverified but update last_checked
        for entry in existing_classes:
            if entry.get('studio_id') == studio_id:
                entry['verified'] = False
                entry['last_checked'] = now_date
                if schedule_url:
                    entry['source'] = schedule_url

    schedule_data['classes'] = existing_classes


# ---------------------------------------------------------------------------
# Price change logging
# ---------------------------------------------------------------------------

def load_price_changelog():
    """Load the existing price changelog or return an empty list."""
    if PRICE_CHANGELOG_FILE.exists():
        try:
            with open(PRICE_CHANGELOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_price_changelog(changelog):
    """Persist the price changelog to disk."""
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    with open(PRICE_CHANGELOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(changelog, f, ensure_ascii=False, indent=2)
        f.write('\n')
    logger.info(f"Price changelog saved ({len(changelog)} entries)")


def log_price_change(changelog, studio_id, canton, field, old_value, new_value, source_url):
    """Append a price change entry to the changelog list (in memory)."""
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'studio_id': studio_id,
        'canton': canton,
        'field': field,
        'old_value': old_value,
        'new_value': new_value,
        'source': source_url or '',
    }
    changelog.append(entry)
    logger.info(f"  PRICE CHANGE [{canton}/{studio_id}] {field}: {old_value} -> {new_value}")


def detect_price_changes(existing_pricing, new_pricing, studio_id, canton, changelog):
    """Compare existing and new pricing dicts; log any changes."""
    price_fields = ['single', 'card_10', 'monthly', 'trial', 'abo']
    source_url = new_pricing.get('source', '')

    for field in price_fields:
        old_val = existing_pricing.get(field)
        new_val = new_pricing.get(field)
        if new_val is not None and old_val is not None and old_val != new_val:
            log_price_change(changelog, studio_id, canton, f'pricing.{field}',
                             old_val, new_val, source_url)


# ---------------------------------------------------------------------------
# _meta field management
# ---------------------------------------------------------------------------

def build_meta(studio, scrape_result, pricing_result):
    """
    Build a _meta dict for a studio based on scrape/price results.
    Merges with any existing _meta to preserve historical data.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    existing_meta = studio.get('_meta', {})

    # Determine scrape status
    if scrape_result:
        scrape_status = scrape_result.get('status', 'success')
    else:
        scrape_status = existing_meta.get('scrape_status', 'no_data')

    # Build source_urls from studio fields
    source_urls = existing_meta.get('source_urls', {})
    if studio.get('website'):
        source_urls['website'] = studio['website']
    if studio.get('schedule_url'):
        source_urls['schedule'] = studio['schedule_url']
    if pricing_result and pricing_result.get('source'):
        source_urls['pricing'] = pricing_result['source']

    # Booking links from scrape result
    booking_links = existing_meta.get('booking_links', [])
    if scrape_result and scrape_result.get('booking_links'):
        booking_links = scrape_result['booking_links']

    meta = {
        'last_scraped': now_iso,
        'last_price_check': now_iso if pricing_result else existing_meta.get('last_price_check'),
        'scrape_status': scrape_status,
        'booking_links': booking_links,
        'source_urls': source_urls,
    }
    return meta


# ---------------------------------------------------------------------------
# Main scraping logic
# ---------------------------------------------------------------------------

def update_studio_data(canton_files, changelog, schedule_files, verification_data):
    """Run scrapers for all active studios across all canton files.

    Also scrapes fresh schedule data for studios marked as scrapable in the
    verification data, and updates the corresponding schedule_*.json files.
    """
    total_updated = 0
    total_errors = 0
    total_prices_found = 0
    total_schedule_scraped = 0

    for file_path, canton_name, data in canton_files:
        logger.info(f"--- Canton: {canton_name} ({file_path}) ---")
        updated_count = 0
        error_count = 0
        prices_found = 0
        schedule_scraped = 0

        # Get or create the schedule data for this canton
        if canton_name in schedule_files:
            sched_path, sched_data = schedule_files[canton_name]
        else:
            sched_path = str(DATA_DIR / f'schedule_{canton_name}.json')
            sched_data = {'classes': []}
            schedule_files[canton_name] = (sched_path, sched_data)

        for studio in data.get('studios', []):
            if not studio.get('active', True):
                continue

            studio_name = studio.get('name', 'Unknown')
            studio_id = studio.get('id', studio_name)
            logger.info(f"Processing: {studio_name} [{canton_name}]")

            scrape_result = None
            pricing_result = None

            # --- Schedule scraping (studio metadata) ---
            try:
                scrape_result = scrape_generic_schedule(studio)
                if scrape_result:
                    updated_count += 1
                    # Keep legacy fields for backward compat (but _meta is canonical)
                    studio['scrape_status'] = scrape_result.get('status', 'unknown')
                    studio['last_scraped'] = scrape_result.get('last_scraped')
                    if scrape_result.get('booking_links'):
                        studio['detected_booking_links'] = scrape_result['booking_links']
                else:
                    studio['scrape_status'] = 'no_data'
            except Exception as e:
                logger.error(f"Error scraping {studio_name}: {e}")
                studio['scrape_status'] = 'error'
                scrape_result = {'status': 'error'}
                error_count += 1

            # --- Schedule class scraping (actual class data) ---
            schedule_url = studio.get('schedule_url', '')
            vinfo = verification_data.get(studio_id, {})
            vstatus = vinfo.get('status', '')

            if vstatus == 'scrapable' and schedule_url:
                # Studio has a scrapable static schedule
                try:
                    new_classes = scrape_schedule_classes(studio, schedule_url)
                    if new_classes:
                        update_schedule_for_studio(sched_data, studio, new_classes,
                                                   schedule_url, verified=True)
                        schedule_scraped += 1
                    else:
                        # No classes extracted but studio is scrapable; keep existing, mark unverified
                        update_schedule_for_studio(sched_data, studio, [],
                                                   schedule_url, verified=False)
                except Exception as e:
                    logger.error(f"Error scraping schedule classes for {studio_name}: {e}")
                    update_schedule_for_studio(sched_data, studio, [],
                                               schedule_url, verified=False)
            elif vstatus in ('blocked', 'dynamic', 'error', 'no_url', ''):
                # Cannot scrape; keep existing entries but mark as unverified
                update_schedule_for_studio(sched_data, studio, [],
                                           schedule_url, verified=False)

            # --- Price scraping ---
            try:
                new_pricing = scrape_prices(studio)
                existing_pricing = studio.get('pricing', {})

                if new_pricing and new_pricing.get('verified'):
                    # Detect and log price changes before merging
                    detect_price_changes(existing_pricing, new_pricing,
                                         studio_id, canton_name, changelog)
                    # Merge: keep existing fields not in new data, update the rest
                    merged = dict(existing_pricing)
                    merged.update(new_pricing)
                    studio['pricing'] = merged
                    pricing_result = new_pricing
                    prices_found += 1
                    logger.info(f"  Updated pricing for {studio_name}: {new_pricing}")
                elif not new_pricing:
                    if existing_pricing:
                        existing_pricing['last_checked'] = datetime.now(timezone.utc).isoformat()
                    logger.debug(f"  No pricing found for {studio_name}")
            except Exception as e:
                logger.error(f"Error scraping prices for {studio_name}: {e}")

            # --- Persist _meta ---
            studio['_meta'] = build_meta(studio, scrape_result, pricing_result)

        # Update file-level timestamps
        data['last_updated'] = datetime.now(timezone.utc).isoformat()
        now_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        sched_data['_meta'] = {
            'last_updated': now_date,
            'note': 'Stundenplan-Daten aus öffentlichen Quellen. Für aktuelle Zeiten siehe Studio-Website.',
        }

        logger.info(f"Canton {canton_name}: {updated_count} updated, "
                     f"{error_count} errors, {prices_found} prices found, "
                     f"{schedule_scraped} schedules scraped")
        total_updated += updated_count
        total_errors += error_count
        total_prices_found += prices_found
        total_schedule_scraped += schedule_scraped

    logger.info(f"Total price scraping summary: {total_prices_found} studios with new/updated prices")
    logger.info(f"Total schedule scraping summary: {total_schedule_scraped} studios with fresh schedule data")
    return total_updated, total_errors


def run_validation():
    """Run the data validation script after scraping."""
    validate_script = TOOLS_DIR / 'validate_data.py'
    if not validate_script.exists():
        logger.warning(f"Validation script not found: {validate_script}")
        return None

    logger.info("Running data validation...")
    try:
        result = subprocess.run(
            ['python3', str(validate_script)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            logger.info("Validation passed.")
        else:
            logger.warning(f"Validation exited with code {result.returncode}")
        if result.stdout:
            logger.info(f"Validation output:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"Validation stderr:\n{result.stderr}")
        return result
    except FileNotFoundError:
        logger.warning("python3 not found; skipping validation")
        return None
    except subprocess.TimeoutExpired:
        logger.error("Validation script timed out after 120s")
        return None


def main():
    logger.info("=" * 60)
    logger.info("Yoga Kurse Schweiz — Starting scrape run (all cantons)")
    logger.info("=" * 60)

    # Load all canton-specific studio files
    canton_files = load_all_canton_files()
    if not canton_files:
        logger.error("No canton studio files found in data/ directory")
        sys.exit(1)

    logger.info(f"Found {len(canton_files)} canton file(s) to process")

    # Load schedule verification data (which studios are scrapable)
    verification_data = load_verification_data()
    logger.info(f"Loaded verification data for {len(verification_data)} studio(s)")

    # Load all canton-specific schedule files
    schedule_files = load_all_schedule_files()
    logger.info(f"Loaded {len(schedule_files)} schedule file(s)")

    # Load existing price changelog
    changelog = load_price_changelog()

    # Run scrapers across all cantons (studios + schedules + prices)
    updated, errors = update_studio_data(canton_files, changelog,
                                         schedule_files, verification_data)

    # Save all canton studio files back
    for file_path, canton_name, data in canton_files:
        save_canton_file(file_path, data)

    # Save all canton schedule files back
    for canton_name, (sched_path, sched_data) in schedule_files.items():
        save_schedule_file(sched_path, sched_data)

    # Save price changelog if there were changes
    save_price_changelog(changelog)

    # Run validation
    run_validation()

    logger.info("=" * 60)
    logger.info(f"Scrape complete: {updated} updated, {errors} errors "
                f"across {len(canton_files)} cantons")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
