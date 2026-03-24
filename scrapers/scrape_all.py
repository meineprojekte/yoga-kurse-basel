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
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# curl_cffi bypasses Cloudflare/bot protection (needed for Eversports & Wix)
try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False
    try:
        import cloudscraper
        HAS_CLOUDSCRAPER = True
    except ImportError:
        HAS_CLOUDSCRAPER = False

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

# Rate limiting between studios (seconds)
RATE_LIMIT_DELAY = 2


def cffi_get(url, timeout=15):
    """
    Fetch a URL using curl_cffi (impersonates Chrome to bypass 403 blocks).
    Falls back to cloudscraper, then regular requests.
    """
    if HAS_CURL_CFFI:
        try:
            resp = cffi_requests.get(url, timeout=timeout, impersonate="chrome")
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            logger.warning(f"curl_cffi failed for {url}: {e}")
            return None
    elif HAS_CLOUDSCRAPER:
        try:
            scraper = cloudscraper.create_scraper()
            resp = scraper.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            logger.warning(f"cloudscraper failed for {url}: {e}")
            return None
    else:
        logger.warning("Neither curl_cffi nor cloudscraper available; using requests")
        return fetch_page(url, timeout=timeout)


def cffi_post_json(url, headers=None, json_body=None, timeout=15):
    """
    POST JSON using curl_cffi (impersonates Chrome to bypass 403 blocks).
    Returns parsed JSON response or None.
    """
    if HAS_CURL_CFFI:
        try:
            resp = cffi_requests.post(
                url, headers=headers, json=json_body,
                timeout=timeout, impersonate="chrome"
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"curl_cffi POST failed for {url}: {e}")
            return None
    elif HAS_CLOUDSCRAPER:
        try:
            scraper = cloudscraper.create_scraper()
            resp = scraper.post(url, headers=headers, json=json_body, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"cloudscraper POST failed for {url}: {e}")
            return None
    else:
        try:
            resp = requests.post(url, headers=headers, json=json_body, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"requests POST failed for {url}: {e}")
            return None


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


# ---------------------------------------------------------------------------
# Platform-specific scrapers
# ---------------------------------------------------------------------------

# Eversports day name mapping (German day headers in calendar HTML)
EVERSPORTS_DAY_MAP = {
    'montag': 'Monday', 'dienstag': 'Tuesday', 'mittwoch': 'Wednesday',
    'donnerstag': 'Thursday', 'freitag': 'Friday', 'samstag': 'Saturday',
    'sonntag': 'Sunday',
    'monday': 'Monday', 'tuesday': 'Tuesday', 'wednesday': 'Wednesday',
    'thursday': 'Thursday', 'friday': 'Friday', 'saturday': 'Saturday',
    'sunday': 'Sunday',
    'mo': 'Monday', 'di': 'Tuesday', 'mi': 'Wednesday',
    'do': 'Thursday', 'fr': 'Friday', 'sa': 'Saturday', 'so': 'Sunday',
}


def _extract_eversports_slug(studio):
    """Extract the Eversports slug from studio schedule_url or detected booking links."""
    schedule_url = studio.get('schedule_url', '')
    # Pattern: eversports.ch/s/{slug}
    m = re.search(r'eversports\.ch/s/([a-zA-Z0-9_-]+)', schedule_url)
    if m:
        return m.group(1)

    # Check detected_booking_links and _meta.booking_links
    for links_key in ('detected_booking_links', ):
        for link in studio.get(links_key, []):
            url = link.get('url', '')
            m = re.search(r'eversports\.ch/s/([a-zA-Z0-9_-]+)', url)
            if m:
                return m.group(1)

    meta_links = studio.get('_meta', {}).get('booking_links', [])
    for link in meta_links:
        url = link.get('url', '')
        m = re.search(r'eversports\.ch/s/([a-zA-Z0-9_-]+)', url)
        if m:
            return m.group(1)

    return None


def _extract_eversports_widget_slug(studio):
    """Extract widget slug (short hash) from detected Eversports widget URLs."""
    for links_key in ('detected_booking_links', ):
        for link in studio.get(links_key, []):
            url = link.get('url', '')
            m = re.search(r'eversports\.ch/widget/w/([a-zA-Z0-9]+)', url)
            if m:
                return m.group(1)

    meta_links = studio.get('_meta', {}).get('booking_links', [])
    for link in meta_links:
        url = link.get('url', '')
        m = re.search(r'eversports\.ch/widget/w/([a-zA-Z0-9]+)', url)
        if m:
            return m.group(1)

    return None


def scrape_eversports_widget_api(studio):
    """
    Scrape schedule from Eversports using the widget calendar API.

    The calendar API accepts the studio slug directly as facilityShortId.
    URL: /widget/api/eventsession/calendar?facilityShortId={slug}&startDate={date}
    Response: JSON with data.html containing calendar HTML.

    Calendar HTML structure per slot (li.calendar__slot):
      - div.sr-only: day name (e.g. "Monday, 23/03/2026")
      - div.session-time: time + duration (e.g. "09:30 . 90 Min")
      - div.session-name: class name
      - div.ellipsis (2nd): teacher name

    Returns list of class entry dicts, or None if approach fails.
    """
    studio_id = studio.get('id', '')
    studio_name = studio.get('name', '')

    # Get the Eversports slug
    slug = _extract_eversports_slug(studio)
    if not slug:
        # Try widget slug as fallback for calendar API
        slug = _extract_eversports_widget_slug(studio)
    if not slug:
        logger.debug(f"  Eversports: no slug found for {studio_name}")
        return None

    # Call calendar API (slug works directly as facilityShortId)
    today = datetime.now().strftime('%Y-%m-%d')
    calendar_url = (
        f'https://www.eversports.ch/widget/api/eventsession/calendar'
        f'?facilityShortId={slug}&startDate={today}'
    )
    logger.info(f"  Eversports: fetching calendar API for {studio_name} (slug={slug})")
    raw_response = cffi_get(calendar_url, timeout=15)
    if not raw_response:
        logger.warning(f"  Eversports: calendar API returned no data for {studio_name}")
        return None

    # Parse JSON response to get HTML content
    try:
        calendar_json = json.loads(raw_response)
        if calendar_json.get('status') != 'success':
            logger.warning(f"  Eversports: API status={calendar_json.get('status')} for {studio_name}")
            return None
        calendar_html = calendar_json.get('data', {}).get('html', '')
    except (json.JSONDecodeError, AttributeError):
        logger.warning(f"  Eversports: failed to parse API JSON for {studio_name}")
        return None

    if not calendar_html:
        logger.warning(f"  Eversports: no calendar HTML for {studio_name}")
        return None

    # Parse the calendar HTML
    soup = BeautifulSoup(calendar_html, 'html.parser')
    classes = []
    schedule_url = studio.get('schedule_url', f'https://www.eversports.ch/s/{slug}')

    # Day name mapping from date to weekday
    WEEKDAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    # Iterate over all calendar slots
    for slot in soup.find_all('li', class_=re.compile(r'calendar__slot')):
        # Extract day from .sr-only div (e.g., "Monday, 23/03/2026")
        sr_only = slot.find('div', class_='sr-only')
        day_name = None
        if sr_only:
            sr_text = sr_only.get_text(strip=True)
            # Parse day from text like "Monday, 23/03/2026"
            for en_day in WEEKDAY_NAMES:
                if en_day.lower() in sr_text.lower():
                    day_name = en_day
                    break
            if not day_name:
                # Try German day names
                for de_day, en_day in EVERSPORTS_DAY_MAP.items():
                    if de_day in sr_text.lower():
                        day_name = en_day
                        break
            if not day_name:
                # Try to parse the date from sr_text
                date_match = re.search(r'(\d{2})/(\d{2})/(\d{4})', sr_text)
                if date_match:
                    try:
                        dt = datetime(int(date_match.group(3)), int(date_match.group(2)),
                                      int(date_match.group(1)))
                        day_name = WEEKDAY_NAMES[dt.weekday()]
                    except (ValueError, IndexError):
                        pass

        # If no sr-only, find closest preceding day header
        if not day_name:
            prev = slot.find_previous('h3', class_='calendar__day-header')
            if prev:
                data_day = prev.get('data-day', '')
                if data_day:
                    try:
                        dt = datetime.strptime(data_day, '%Y-%m-%d')
                        day_name = WEEKDAY_NAMES[dt.weekday()]
                    except ValueError:
                        pass

        # Extract time from .session-time div (e.g., "09:30 . 90 Min")
        time_el = slot.find('div', class_='session-time')
        time_text = time_el.get_text(strip=True) if time_el else ''
        time_start = ''
        time_end = ''
        duration_min = 0

        time_match = re.search(r'(\d{1,2}:\d{2})', time_text)
        if time_match:
            time_start = time_match.group(1)
            # Extract duration to calculate end time
            dur_match = re.search(r'(\d+)\s*[Mm]in', time_text)
            if dur_match:
                duration_min = int(dur_match.group(1))
                try:
                    start_h, start_m = map(int, time_start.split(':'))
                    end_total = start_h * 60 + start_m + duration_min
                    time_end = f'{end_total // 60:02d}:{end_total % 60:02d}'
                except ValueError:
                    pass

        # Extract class name from .session-name div
        name_el = slot.find('div', class_='session-name')
        class_name = name_el.get_text(strip=True) if name_el else ''

        # Extract teacher from the second .ellipsis div
        # Structure: 1st ellipsis = level/spots, 2nd = teacher, 3rd = room
        ellipsis_divs = slot.find_all('div', class_='ellipsis')
        teacher = ''
        if len(ellipsis_divs) >= 2:
            teacher = ellipsis_divs[1].get_text(strip=True)
        elif len(ellipsis_divs) == 1:
            teacher = ellipsis_divs[0].get_text(strip=True)

        if class_name and time_start:
            classes.append({
                'studio_id': studio_id,
                'studio_name': studio_name,
                'day': day_name or 'Unknown',
                'time_start': time_start,
                'time_end': time_end,
                'class_name': class_name,
                'teacher': teacher,
                'level': 'all',
                'source': schedule_url,
                'verified': True,
            })

    if classes:
        logger.info(f"  Eversports: extracted {len(classes)} classes for {studio_name}")
    else:
        logger.info(f"  Eversports: no classes parsed from calendar for {studio_name}")

    return classes if classes else None


def scrape_wix_bookings(studio):
    """
    Scrape schedule from Wix-based studio websites using the Wix Bookings V2 API.

    Steps:
    1. Fetch /_api/v2/dynamicmodel to get app instance tokens
    2. Extract instance token for Wix Bookings app (13d21c63-b5ec-5912-8397-c3a5ddb27a97)
    3. POST to Wix Bookings V2 calendar sessions query API
    4. Parse JSON response for class sessions (uses localDateTime for correct timezone)

    Returns list of class entry dicts, or None if approach fails.
    """
    studio_id = studio.get('id', '')
    studio_name = studio.get('name', '')
    website = studio.get('website', '') or studio.get('schedule_url', '')

    if not website:
        return None

    # Normalize base URL
    base_url = website.rstrip('/')
    # Extract domain (e.g., https://www.yamabern.ch)
    parts = base_url.split('/')
    if len(parts) >= 3:
        domain_url = '/'.join(parts[:3])
    else:
        domain_url = base_url

    # Step 1: Fetch dynamic model to get app instance tokens
    dynamic_model_url = f'{domain_url}/_api/v2/dynamicmodel'
    logger.info(f"  Wix: fetching dynamic model from {domain_url}")
    dm_text = cffi_get(dynamic_model_url, timeout=15)
    if not dm_text:
        return None

    try:
        dm = json.loads(dm_text)
    except (json.JSONDecodeError, TypeError):
        logger.debug(f"  Wix: dynamic model not valid JSON for {studio_name}")
        return None

    # Step 2: Extract Wix Bookings instance token
    WIX_BOOKINGS_APP_ID = '13d21c63-b5ec-5912-8397-c3a5ddb27a97'
    apps = dm.get('apps', {})
    bookings_app = apps.get(WIX_BOOKINGS_APP_ID, {})
    instance_token = bookings_app.get('instance', '') if isinstance(bookings_app, dict) else ''

    if not instance_token:
        logger.debug(f"  Wix: no Bookings app instance found for {studio_name}")
        return None

    logger.info(f"  Wix: found Bookings instance token for {studio_name}")

    # Step 3: Query the Wix Bookings V2 API for sessions over the next 7 days
    now = datetime.now(timezone.utc)
    from_date = now.strftime('%Y-%m-%dT00:00:00Z')
    to_date = (now + timedelta(days=7)).strftime('%Y-%m-%dT23:59:59Z')

    api_url = 'https://www.wixapis.com/bookings/v2/calendar/sessions/query'
    api_headers = {
        'Authorization': instance_token,
        'Content-Type': 'application/json',
    }
    api_body = {
        'fromDate': from_date,
        'toDate': to_date,
    }

    logger.info(f"  Wix: querying bookings API for {studio_name}")
    result = cffi_post_json(api_url, headers=api_headers, json_body=api_body, timeout=15)
    if not result:
        return None

    # Step 4: Parse sessions from the response
    sessions = result.get('sessions', [])
    if not sessions:
        sessions = result.get('data', {}).get('sessions', [])

    if not sessions:
        logger.info(f"  Wix: no sessions returned for {studio_name}")
        return None

    classes = []
    schedule_url = studio.get('schedule_url', '') or website

    WEEKDAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    for session in sessions:
        try:
            # Use localDateTime for correct timezone display
            start_info = session.get('start', {})
            end_info = session.get('end', {})

            local_start = start_info.get('localDateTime', {})
            local_end = end_info.get('localDateTime', {})

            if local_start:
                hour = local_start.get('hourOfDay', 0)
                minute = local_start.get('minutesOfHour', 0)
                year = local_start.get('year', 0)
                month = local_start.get('monthOfYear', 0)
                day = local_start.get('dayOfMonth', 0)
                time_start = f'{hour:02d}:{minute:02d}'
                try:
                    start_dt = datetime(year, month, day)
                    day_name = WEEKDAY_NAMES[start_dt.weekday()]
                except (ValueError, IndexError):
                    day_name = 'Unknown'
            else:
                # Fallback to timestamp
                start_str = start_info.get('timestamp', '')
                if not start_str:
                    continue
                start_dt = None
                for fmt in ('%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S'):
                    try:
                        start_dt = datetime.strptime(start_str, fmt)
                        break
                    except ValueError:
                        continue
                if not start_dt:
                    continue
                day_name = WEEKDAY_NAMES[start_dt.weekday()]
                time_start = start_dt.strftime('%H:%M')

            if local_end:
                end_hour = local_end.get('hourOfDay', 0)
                end_minute = local_end.get('minutesOfHour', 0)
                time_end = f'{end_hour:02d}:{end_minute:02d}'
            else:
                end_str = end_info.get('timestamp', '')
                if end_str:
                    for fmt in ('%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S'):
                        try:
                            end_dt = datetime.strptime(end_str, fmt)
                            time_end = end_dt.strftime('%H:%M')
                            break
                        except ValueError:
                            continue
                    else:
                        time_end = ''
                else:
                    time_end = ''

            # Extract class name
            class_name = session.get('title', '') or 'Yoga Class'

            # Extract teacher from affectedSchedules
            teacher = ''
            affected = session.get('affectedSchedules', [])
            for aff in affected:
                owner_name = aff.get('scheduleOwnerName', '')
                if owner_name:
                    teacher = owner_name
                    break

            # Also check staffMembers
            if not teacher:
                staff = session.get('staffMembers', []) or session.get('staff', [])
                if staff:
                    teacher = staff[0].get('name', '') or staff[0].get('fullName', '')

            classes.append({
                'studio_id': studio_id,
                'studio_name': studio_name,
                'day': day_name,
                'time_start': time_start,
                'time_end': time_end,
                'class_name': class_name,
                'teacher': teacher,
                'level': 'all',
                'source': schedule_url,
                'verified': True,
            })
        except Exception as e:
            logger.debug(f"  Wix: error parsing session for {studio_name}: {e}")
            continue

    if classes:
        logger.info(f"  Wix: extracted {len(classes)} classes for {studio_name}")
    else:
        logger.info(f"  Wix: no classes parsed from API for {studio_name}")

    return classes if classes else None

# Known SportsNow slug overrides (studio_id -> sportsnow_slug)
# Discovered by scraping studio websites for embedded SportsNow widget URLs
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


def scrape_sportsnow_schedule(studio):
    """
    Scrape schedule from SportsNow using the /providers/{slug}/schedule endpoint.

    This endpoint returns a clean HTML table with:
    - Day headers as <tr><td colspan="6">Montag</td></tr>
    - Class rows with columns: Zeit, Stunde, Leitung, Ort/Raum, Bemerkung, Aktion

    URL pattern: https://www.sportsnow.ch/providers/{slug}/schedule?locale=de

    Returns a list of class entry dicts, or None if the approach fails.
    """
    studio_id = studio.get('id', '')
    studio_name = studio.get('name', '')

    # Determine the SportsNow slug
    sn_slug = studio.get('sportsnow_slug', '') or SPORTSNOW_SLUGS.get(studio_id, '')

    # If no slug known, try to find it from the studio website
    if not sn_slug:
        sn_slug = _discover_sportsnow_slug(studio)
        if sn_slug:
            logger.info(f"  Discovered SportsNow slug: {sn_slug}")

    if not sn_slug:
        logger.debug(f"  No SportsNow slug found for {studio_name}")
        return None

    url = f'https://www.sportsnow.ch/providers/{sn_slug}/schedule?locale=de'
    logger.info(f"  SportsNow: fetching {url}")

    html = fetch_page(url, timeout=15)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')

    table = soup.find('table')
    if not table:
        logger.warning(f"  SportsNow: no schedule table found for {sn_slug}")
        return None

    classes = []
    current_day = None

    # Day name mapping
    sn_day_map = {
        'montag': 'Monday', 'dienstag': 'Tuesday', 'mittwoch': 'Wednesday',
        'donnerstag': 'Thursday', 'freitag': 'Friday', 'samstag': 'Saturday',
        'sonntag': 'Sunday',
    }

    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if not tds:
            continue

        # Day header row: single td with colspan
        if len(tds) == 1 and tds[0].get('colspan'):
            day_text = tds[0].get_text(strip=True).lower()
            for de_day, en_day in sn_day_map.items():
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
                # Clean teacher name: SportsNow sometimes prefixes with "N) "
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
        logger.info(f"  SportsNow: extracted {len(classes)} classes for {studio_name}")
    return classes if classes else None


def _discover_sportsnow_slug(studio):
    """
    Try to discover the SportsNow slug by checking the studio's website
    for embedded SportsNow widget URLs.
    """
    website = studio.get('website', '')
    schedule_url = studio.get('schedule_url', '')

    urls_to_check = []
    if schedule_url:
        urls_to_check.append(schedule_url)
    if website and website != schedule_url:
        urls_to_check.append(website)

    for url in urls_to_check:
        html = fetch_page(url, timeout=10)
        if not html:
            continue

        # Look for sportsnow.ch slug patterns in HTML
        slugs = re.findall(
            r'sportsnow\.ch/(?:go|providers)/([a-zA-Z0-9_-]+)', html)
        if slugs:
            return slugs[0]

        # Check subpages for schedule links
        soup = BeautifulSoup(html, 'lxml')
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
                    r'sportsnow\.ch/(?:go|providers)/([a-zA-Z0-9_-]+)', sub_html)
                if sub_slugs:
                    return sub_slugs[0]

    return None


def scrape_eversports_schedule(studio):
    """
    Scrape Eversports schedule via the widget calendar API.
    Uses curl_cffi to bypass Cloudflare 403 blocks.

    Returns a list of class entry dicts, or None.
    """
    return scrape_eversports_widget_api(studio)


def discover_eversports_from_html(studio):
    """
    Discover Eversports widget slug by fetching the studio's website with curl_cffi
    and searching for embedded widget URLs or facilityShortId parameters.
    If found, calls the Eversports calendar API to extract classes.

    Returns a list of class entry dicts, or None.
    """
    website = studio.get('website', '')
    schedule_url = studio.get('schedule_url', '')
    urls_to_try = [u for u in [schedule_url, website] if u]

    for url in urls_to_try:
        html = cffi_get(url)
        if not html:
            continue

        slug = None
        # Pattern: eversports.ch/widget/w/SLUG
        m = re.search(r'eversports\.ch/widget/w/([a-zA-Z0-9_-]+)', html)
        if m:
            slug = m.group(1)
        # Pattern: facilityShortId=SLUG
        if not slug:
            m = re.search(r'facilityShortId=([a-zA-Z0-9_-]+)', html)
            if m:
                slug = m.group(1)
        # Pattern: eversports.ch/s/SLUG
        if not slug:
            m = re.search(r'eversports\.ch/s/([a-zA-Z0-9_-]+)', html)
            if m:
                slug = m.group(1)

        if slug:
            logger.info(f"  Discovered Eversports slug from HTML: {slug}")
            # Inject discovered slug so the standard Eversports scraper can use it
            studio.setdefault('_meta', {}).setdefault('booking_links', []).append({
                'platform': 'eversports',
                'url': f'https://www.eversports.ch/s/{slug}'
            })
            return scrape_eversports_widget_api(studio)

    return None


def scrape_acuity_schedule(studio):
    """
    Discover and scrape Acuity Scheduling / Squarespace Scheduling widgets.
    Fetches the studio's website, looks for owner IDs in embedded iframe URLs,
    then retrieves appointment types from the Acuity widget page.

    Returns a list of class entry dicts, or None.
    """
    studio_id = studio.get('id', '')
    studio_name = studio.get('name', '')
    website = studio.get('website', '')
    schedule_url = studio.get('schedule_url', '')

    urls_to_try = [u for u in [schedule_url, website] if u]
    owner_id = None

    for url in urls_to_try:
        html = cffi_get(url)
        if not html:
            continue
        m = re.search(r'squarespacescheduling\.com/schedule\.php\?owner=(\d+)', html)
        if not m:
            m = re.search(r'acuityscheduling\.com/schedule\.php\?owner=(\d+)', html)
        if m:
            owner_id = m.group(1)
            break

    if not owner_id:
        return None

    logger.info(f"  Acuity: found owner={owner_id} for {studio_name}")
    acuity_url = f"https://app.squarespacescheduling.com/schedule.php?owner={owner_id}"
    acuity_html = cffi_get(acuity_url)
    if not acuity_html:
        return None

    classes = []
    m = re.search(r'"appointmentTypes"\s*:\s*(\{.+?\})\s*,\s*"[a-z]', acuity_html, re.DOTALL)
    if not m:
        return None

    names = re.findall(r'"name":"([^"]+)"', m.group(1))
    descs = re.findall(r'"description":"([^"]*)"', m.group(1))
    yoga_keywords = ['yoga', 'pilates', 'meditation', 'breathwork', 'vinyasa',
                     'hatha', 'yin', 'flow', 'ashtanga', 'kundalini', 'stretch']

    for i, name in enumerate(names):
        if any(k in name.lower() for k in yoga_keywords):
            desc = descs[i] if i < len(descs) else ''
            day = ''
            t_start = ''
            for de_day, en_day in EVERSPORTS_DAY_MAP.items():
                if de_day in desc.lower():
                    day = en_day
                    break
            tm = re.search(r'(\d{1,2}[:.]\d{2})', desc)
            if tm:
                t_start = tm.group(1).replace('.', ':')
            if day or t_start:
                classes.append({
                    'studio_id': studio_id,
                    'studio_name': studio_name,
                    'day': day or 'TBC',
                    'time_start': t_start,
                    'time_end': '',
                    'class_name': name.strip()[:100],
                    'teacher': '',
                    'level': 'all',
                })

    if classes:
        logger.info(f"  Acuity: extracted {len(classes)} classes for {studio_name}")
    return classes if classes else None


# Subpage paths used for schedule discovery crawling
_SCHEDULE_SUBPATHS = [
    '/stundenplan', '/schedule', '/classes', '/kurse', '/horaire',
    '/angebot', '/yoga', '/orario', '/class-schedule',
]


def scrape_subpage_crawl(studio):
    """
    Try to discover schedule data by crawling common subpages of the studio website.
    For each subpage, check for embedded booking widgets (Eversports, SportsNow, Acuity)
    and attempt HTML schedule parsing.

    Returns a list of class entry dicts, or None.
    """
    website = studio.get('website', '')
    if not website:
        return None

    studio_id = studio.get('id', '')
    studio_name = studio.get('name', '')
    base_url = website.rstrip('/')

    for subpath in _SCHEDULE_SUBPATHS:
        sub_url = base_url + subpath
        html = cffi_get(sub_url, timeout=8)
        if not html or len(html) < 500:
            continue

        # Check for Eversports widget
        slug = None
        m = re.search(r'eversports\.ch/widget/w/([a-zA-Z0-9_-]+)', html)
        if m:
            slug = m.group(1)
        if not slug:
            m = re.search(r'facilityShortId=([a-zA-Z0-9_-]+)', html)
            if m:
                slug = m.group(1)
        if not slug:
            m = re.search(r'eversports\.ch/s/([a-zA-Z0-9_-]+)', html)
            if m:
                slug = m.group(1)
        if slug:
            studio.setdefault('_meta', {}).setdefault('booking_links', []).append({
                'platform': 'eversports',
                'url': f'https://www.eversports.ch/s/{slug}'
            })
            result = scrape_eversports_widget_api(studio)
            if result:
                logger.info(f"  Subpage crawl: found Eversports on {subpath}")
                return result

        # Check for SportsNow
        sn_m = re.search(r'sportsnow\.ch/(?:go|providers)/([a-zA-Z0-9_-]+)', html)
        if sn_m:
            sn_slug = sn_m.group(1)
            studio['sportsnow_slug'] = sn_slug
            result = scrape_sportsnow_schedule(studio)
            if result:
                logger.info(f"  Subpage crawl: found SportsNow on {subpath}")
                return result

        # Check for Acuity
        ac_m = re.search(r'(?:squarespacescheduling|acuityscheduling)\.com/schedule\.php\?owner=(\d+)', html)
        if ac_m:
            studio['_acuity_owner'] = ac_m.group(1)
            result = scrape_acuity_schedule(studio)
            if result:
                logger.info(f"  Subpage crawl: found Acuity on {subpath}")
                return result

        # Try HTML schedule parsing on subpage
        soup = BeautifulSoup(html, 'html.parser')
        classes = _parse_subpage_schedule(soup, studio_id, studio_name, sub_url)
        if classes:
            logger.info(f"  Subpage crawl: parsed {len(classes)} classes from {subpath}")
            return classes

    return None


def _parse_subpage_schedule(soup, studio_id, studio_name, source_url):
    """Parse schedule from a subpage's HTML using day headings + time patterns."""
    classes = []
    seen = set()

    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b']):
        heading_text = heading.get_text(strip=True)
        day = _normalize_day(heading_text)
        if not day:
            continue

        sibling = heading.find_next_sibling()
        attempts = 0
        while sibling and attempts < 30:
            attempts += 1
            sib_text = sibling.get_text(strip=True)
            if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                break
            if _normalize_day(sib_text):
                break

            m = re.search(r'(\d{1,2}[:.]\d{2})\s*[-\u2013\u2014]\s*(\d{1,2}[:.]\d{2})', sib_text)
            if m:
                t_start = m.group(1).replace('.', ':')
                t_end = m.group(2).replace('.', ':')
                name = re.sub(r'\d{1,2}[:.]\d{2}\s*[-\u2013\u2014]\s*\d{1,2}[:.]\d{2}', '', sib_text)
                name = name.strip(' -\u2013\u2014|/:,\t\n')
                name = re.sub(r'\s*(Uhr|h)\s*', ' ', name).strip()
                if not name:
                    name = 'Yoga'
                key = (day, t_start, name[:40])
                if key not in seen:
                    seen.add(key)
                    classes.append({
                        'studio_id': studio_id,
                        'studio_name': studio_name,
                        'day': day,
                        'time_start': t_start,
                        'time_end': t_end,
                        'class_name': name.strip()[:100],
                        'teacher': '',
                        'level': 'all',
                        'source': source_url,
                    })
            sibling = sibling.find_next_sibling()

    return classes if classes else None


def scrape_squarespace_schedule(studio):
    """
    Extract schedule data from Squarespace sites using ?format=json.

    Squarespace sites expose page data as JSON. This can reveal embedded
    MindBody widget IDs which we store for the Safari scraper to use.

    Returns a list of class entry dicts, or None.
    """
    schedule_url = studio.get('schedule_url', '') or studio.get('website', '')
    if not schedule_url:
        return None

    studio_id = studio.get('id', '')
    studio_name = studio.get('name', '')

    # Try ?format=json on the schedule page
    json_url = schedule_url.rstrip('/') + '?format=json'
    try:
        resp = SESSION.get(json_url, timeout=10)
        if resp.status_code != 200:
            return None

        # Check if it's actually JSON
        content_type = resp.headers.get('content-type', '')
        if 'json' not in content_type and 'javascript' not in content_type:
            return None

        text = resp.text

        # Look for MindBody widget IDs
        widget_ids = re.findall(
            r'data-widget-id["\s:=]+["\']?([a-f0-9]{10,})', text)
        if widget_ids:
            logger.info(f"  Squarespace: found MindBody widget ID {widget_ids[0]} for {studio_name}")
            # Store it on the studio for future Safari scraper use
            studio['mindbody_widget_id'] = widget_ids[0]
            # We can't fetch the MindBody schedule via HTTP (it's a React SPA),
            # but having the widget ID is valuable for the Safari scraper

        # Look for any schedule-like JSON content
        # (Squarespace page JSON rarely has schedule data directly)

    except Exception as e:
        logger.debug(f"  Squarespace JSON failed for {studio_name}: {e}")

    return None


def scrape_mindbody_schedule(studio, widget_id=None):
    """
    Attempt to scrape MindBody schedule via HTTP.

    MindBody widgets are React SPAs that require a browser to render.
    This function stores the widget URL for the Safari scraper.

    Returns None (MindBody requires browser rendering).
    """
    wid = widget_id or studio.get('mindbody_widget_id', '')
    if wid:
        # Store the direct widget URL for Safari scraper to use
        studio['_mindbody_widget_url'] = (
            f'https://go.mindbodyonline.com/book/widgets/schedules/view/{wid}/schedule'
        )
        logger.debug(f"  MindBody widget URL stored for {studio.get('name', '')}")

    # MindBody schedule data cannot be extracted via HTTP
    return None


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
            booking_platform = (studio.get('booking_platform', '') or '').lower()

            new_classes = None

            # --- Platform-specific scrapers (ordered by reliability) ---

            # 1. Eversports: use widget calendar API via curl_cffi
            if new_classes is None and booking_platform == 'eversports':
                try:
                    new_classes = scrape_eversports_widget_api(studio)
                except Exception as e:
                    logger.error(f"Error in Eversports scraper for {studio_name}: {e}")

            # Also try Eversports if schedule_url points to eversports.ch
            if new_classes is None and 'eversports.ch' in schedule_url:
                try:
                    new_classes = scrape_eversports_widget_api(studio)
                except Exception as e:
                    logger.error(f"Error in Eversports scraper for {studio_name}: {e}")

            # 2. SportsNow
            if new_classes is None and booking_platform == 'sportsnow':
                try:
                    new_classes = scrape_sportsnow_schedule(studio)
                except Exception as e:
                    logger.error(f"Error in SportsNow scraper for {studio_name}: {e}")

            # 3. Wix: try if website is on Wix platform
            if new_classes is None and schedule_url:
                try:
                    new_classes = scrape_wix_bookings(studio)
                except Exception as e:
                    logger.debug(f"Wix check failed for {studio_name}: {e}")

            # 4. For Squarespace sites, try to extract MindBody widget IDs
            if new_classes is None and schedule_url:
                try:
                    scrape_squarespace_schedule(studio)
                except Exception as e:
                    logger.debug(f"Squarespace check failed for {studio_name}: {e}")

            # 5. For MindBody, store widget URL for Safari scraper
            if new_classes is None and booking_platform in ('mindbody', 'mind body'):
                try:
                    scrape_mindbody_schedule(studio)
                except Exception as e:
                    logger.debug(f"MindBody check failed for {studio_name}: {e}")

            # 6. Discover Eversports widget from HTML (curl_cffi scan)
            if new_classes is None:
                try:
                    new_classes = discover_eversports_from_html(studio)
                except Exception as e:
                    logger.debug(f"Eversports HTML discovery failed for {studio_name}: {e}")

            # 7. Acuity Scheduling discovery
            if new_classes is None:
                try:
                    new_classes = scrape_acuity_schedule(studio)
                except Exception as e:
                    logger.debug(f"Acuity check failed for {studio_name}: {e}")

            # 8. Fall back to generic static HTML scraping
            if new_classes is None and schedule_url:
                try:
                    new_classes = scrape_schedule_classes(studio, schedule_url)
                except Exception as e:
                    logger.error(f"Error scraping schedule classes for {studio_name}: {e}")

            # 9. Subpage crawling as last resort
            if new_classes is None:
                try:
                    new_classes = scrape_subpage_crawl(studio)
                except Exception as e:
                    logger.debug(f"Subpage crawl failed for {studio_name}: {e}")

            # Rate limit between studios
            time.sleep(RATE_LIMIT_DELAY)

            # Update schedule data
            if new_classes:
                source = new_classes[0].get('source', schedule_url) if new_classes else schedule_url
                update_schedule_for_studio(sched_data, studio, new_classes,
                                           source, verified=True)
                schedule_scraped += 1
            elif vstatus in ('scrapable', 'blocked', 'dynamic', 'error', 'no_url', ''):
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
