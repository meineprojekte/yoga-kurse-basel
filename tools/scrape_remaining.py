#!/usr/bin/env python3
"""
Scrape schedule data for studios that currently have 0 schedule entries.
Uses curl_cffi to bypass 403 blocks, discovers platform embeds, and tries
alternative URL patterns.
"""

import json
import glob
import os
import re
import sys
import time
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('remaining-scraper')

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
TOOLS_DIR = PROJECT_ROOT / 'tools'

RATE_LIMIT = 2  # seconds between requests
TIMEOUT = 15

# Day name mapping (multi-language)
DAY_MAP = {
    'montag': 'Monday', 'dienstag': 'Tuesday', 'mittwoch': 'Wednesday',
    'donnerstag': 'Thursday', 'freitag': 'Friday', 'samstag': 'Saturday',
    'sonntag': 'Sunday',
    'lundi': 'Monday', 'mardi': 'Tuesday', 'mercredi': 'Wednesday',
    'jeudi': 'Thursday', 'vendredi': 'Friday', 'samedi': 'Saturday',
    'dimanche': 'Sunday',
    'lunedì': 'Monday', 'martedì': 'Tuesday', 'mercoledì': 'Wednesday',
    'giovedì': 'Thursday', 'venerdì': 'Friday', 'sabato': 'Saturday',
    'domenica': 'Sunday',
    'monday': 'Monday', 'tuesday': 'Tuesday', 'wednesday': 'Wednesday',
    'thursday': 'Thursday', 'friday': 'Friday', 'saturday': 'Saturday',
    'sunday': 'Sunday',
    'mo': 'Monday', 'di': 'Tuesday', 'mi': 'Wednesday',
    'do': 'Thursday', 'fr': 'Friday', 'sa': 'Saturday', 'so': 'Sunday',
}

WEEKDAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

TIME_PATTERN = re.compile(r'\b(\d{1,2}:\d{2})\b')


def normalize_day(text):
    """Extract canonical English day name from text."""
    text_lower = text.strip().lower()
    for key, value in DAY_MAP.items():
        if key in text_lower:
            return value
    return None


def cffi_get(url, timeout=TIMEOUT):
    """Fetch URL using curl_cffi with Chrome impersonation."""
    try:
        resp = cffi_requests.get(url, timeout=timeout, impersonate="chrome",
                                  allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.debug(f"  cffi_get failed for {url}: {e}")
        return None


def cffi_post_json(url, headers=None, json_body=None, timeout=TIMEOUT):
    """POST JSON using curl_cffi with Chrome impersonation."""
    try:
        resp = cffi_requests.post(
            url, headers=headers, json=json_body,
            timeout=timeout, impersonate="chrome"
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.debug(f"  cffi_post failed for {url}: {e}")
        return None


# =========================================================================
# Step 1: Identify remaining studios
# =========================================================================

def load_all_data():
    """Load all studios and schedules, return remaining studios grouped by canton."""
    studios_by_canton = {}
    schedules_by_canton = {}

    for fpath in sorted(glob.glob(str(DATA_DIR / 'studios_*.json'))):
        if '.enc.' in fpath:
            continue
        canton = Path(fpath).stem.replace('studios_', '')
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        studios_by_canton[canton] = data

    for fpath in sorted(glob.glob(str(DATA_DIR / 'schedule_*.json'))):
        if '.enc.' in fpath:
            continue
        canton = Path(fpath).stem.replace('schedule_', '')
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        schedules_by_canton[canton] = data

    # Find studio IDs that have schedule entries
    ids_with_schedule = set()
    for canton, sched_data in schedules_by_canton.items():
        for c in sched_data.get('classes', []):
            if c.get('time_start'):
                ids_with_schedule.add(c['studio_id'])

    # Find remaining active studios
    remaining = []
    for canton, studio_data in studios_by_canton.items():
        studios_list = studio_data.get('studios', studio_data)
        if isinstance(studios_list, dict):
            studios_list = list(studios_list.values())
        for s in studios_list:
            if s.get('active', True) and s.get('id') not in ids_with_schedule:
                s['_canton'] = canton
                remaining.append(s)

    return remaining, studios_by_canton, schedules_by_canton


# =========================================================================
# Platform detection from HTML
# =========================================================================

def detect_eversports_slug(html, studio):
    """Look for Eversports embeds in HTML and return slug if found."""
    # Direct eversports.ch/s/{slug} links
    m = re.search(r'eversports\.ch/s/([a-zA-Z0-9_-]+)', html)
    if m:
        return m.group(1)
    # Widget embeds: widget.eversports.com/w/{slug}
    m = re.search(r'eversports\.ch/widget/w/([a-zA-Z0-9]+)', html)
    if m:
        return m.group(1)
    # data-eversports attribute
    m = re.search(r'data-eversports["\s:=]+["\']?([a-zA-Z0-9_-]+)', html)
    if m:
        return m.group(1)
    # Check studio's own data
    schedule_url = studio.get('schedule_url', '')
    m = re.search(r'eversports\.ch/s/([a-zA-Z0-9_-]+)', schedule_url)
    if m:
        return m.group(1)
    return None


def detect_sportsnow_slug(html):
    """Look for SportsNow embeds in HTML and return slug if found."""
    slugs = re.findall(r'sportsnow\.ch/(?:go|providers)/([a-zA-Z0-9_-]+)', html)
    if slugs:
        return slugs[0]
    return None


def detect_momoyoga_slug(html):
    """Look for Momoyoga embeds in HTML and return slug/URL if found."""
    # momoyoga.com/yoga-studio-name
    m = re.search(r'momoyoga\.com/([a-zA-Z0-9_-]+)', html)
    if m and m.group(1) not in ('assets', 'css', 'js', 'images', 'favicon', 'api', 'embed'):
        return m.group(1)
    return None


def detect_mindbody_widget(html):
    """Look for MindBody/Healcode widget ID in HTML."""
    # healcode widget
    m = re.search(r'data-widget-id["\s:=]+["\']?([a-f0-9]{10,})', html)
    if m:
        return m.group(1)
    m = re.search(r'healcode.*?data-widget-id["\s:=]+["\']?([a-f0-9]+)', html, re.DOTALL)
    if m:
        return m.group(1)
    return None


def detect_wix(html):
    """Check if page is a Wix site."""
    wix_indicators = ['wix.com', '_wixCIDX', 'wixsite', 'X-Wix-', 'wix-warmup-data']
    for indicator in wix_indicators:
        if indicator in html:
            return True
    return False


# =========================================================================
# Scraper functions
# =========================================================================

def scrape_eversports(studio, slug):
    """Scrape Eversports via calendar API."""
    today = datetime.now().strftime('%Y-%m-%d')
    calendar_url = (
        f'https://www.eversports.ch/widget/api/eventsession/calendar'
        f'?facilityShortId={slug}&startDate={today}'
    )
    raw = cffi_get(calendar_url)
    if not raw:
        return None

    try:
        data = json.loads(raw)
        if data.get('status') != 'success':
            return None
        calendar_html = data.get('data', {}).get('html', '')
    except (json.JSONDecodeError, AttributeError):
        return None

    if not calendar_html:
        return None

    soup = BeautifulSoup(calendar_html, 'html.parser')
    classes = []
    studio_id = studio.get('id', '')
    studio_name = studio.get('name', '')
    schedule_url = studio.get('schedule_url', '') or f'https://www.eversports.ch/s/{slug}'

    for slot in soup.find_all('li', class_=re.compile(r'calendar__slot')):
        day_name = None
        sr_only = slot.find('div', class_='sr-only')
        if sr_only:
            sr_text = sr_only.get_text(strip=True)
            for en_day in WEEKDAY_NAMES:
                if en_day.lower() in sr_text.lower():
                    day_name = en_day
                    break
            if not day_name:
                for de_day, en_day in DAY_MAP.items():
                    if de_day in sr_text.lower():
                        day_name = en_day
                        break
            if not day_name:
                date_match = re.search(r'(\d{2})/(\d{2})/(\d{4})', sr_text)
                if date_match:
                    try:
                        dt = datetime(int(date_match.group(3)), int(date_match.group(2)),
                                      int(date_match.group(1)))
                        day_name = WEEKDAY_NAMES[dt.weekday()]
                    except (ValueError, IndexError):
                        pass

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

        time_el = slot.find('div', class_='session-time')
        time_text = time_el.get_text(strip=True) if time_el else ''
        time_start = ''
        time_end = ''

        time_match = re.search(r'(\d{1,2}:\d{2})', time_text)
        if time_match:
            time_start = time_match.group(1)
            dur_match = re.search(r'(\d+)\s*[Mm]in', time_text)
            if dur_match:
                duration_min = int(dur_match.group(1))
                try:
                    start_h, start_m = map(int, time_start.split(':'))
                    end_total = start_h * 60 + start_m + duration_min
                    time_end = f'{end_total // 60:02d}:{end_total % 60:02d}'
                except ValueError:
                    pass

        name_el = slot.find('div', class_='session-name')
        class_name = name_el.get_text(strip=True) if name_el else ''

        ellipsis_divs = slot.find_all('div', class_='ellipsis')
        teacher = ''
        if len(ellipsis_divs) >= 2:
            teacher = ellipsis_divs[1].get_text(strip=True)

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
                'last_checked': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            })

    return classes if classes else None


def scrape_sportsnow(studio, slug):
    """Scrape SportsNow schedule page."""
    url = f'https://www.sportsnow.ch/providers/{slug}/schedule?locale=de'
    html = cffi_get(url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    if not table:
        return None

    classes = []
    current_day = None
    studio_id = studio.get('id', '')
    studio_name = studio.get('name', '')

    sn_day_map = {
        'montag': 'Monday', 'dienstag': 'Tuesday', 'mittwoch': 'Wednesday',
        'donnerstag': 'Thursday', 'freitag': 'Friday', 'samstag': 'Saturday',
        'sonntag': 'Sunday',
    }

    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if not tds:
            continue

        if len(tds) == 1 and tds[0].get('colspan'):
            day_text = tds[0].get_text(strip=True).lower()
            for de_day, en_day in sn_day_map.items():
                if de_day in day_text:
                    current_day = en_day
                    break
            continue

        if len(tds) >= 3 and current_day:
            time_text = tds[0].get_text(strip=True)
            class_name = tds[1].get_text(strip=True) if len(tds) > 1 else ''
            teacher = tds[2].get_text(strip=True) if len(tds) > 2 else ''

            time_match = re.search(r'(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})', time_text)
            if time_match and class_name:
                class_name = re.sub(
                    r'\s*/?\s*\d{2}\.\d{2}\.\d{4}\s*[-–]\s*\d{2}\.\d{2}\.\d{4}',
                    '', class_name).strip()
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
                    'last_checked': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                })

    return classes if classes else None


def scrape_wix(studio):
    """Scrape Wix Bookings API."""
    website = studio.get('website', '') or studio.get('schedule_url', '')
    if not website:
        return None

    base_url = website.rstrip('/')
    parts = base_url.split('/')
    domain_url = '/'.join(parts[:3]) if len(parts) >= 3 else base_url

    dm_text = cffi_get(f'{domain_url}/_api/v2/dynamicmodel')
    if not dm_text:
        return None

    try:
        dm = json.loads(dm_text)
    except (json.JSONDecodeError, TypeError):
        return None

    WIX_BOOKINGS_APP_ID = '13d21c63-b5ec-5912-8397-c3a5ddb27a97'
    apps = dm.get('apps', {})
    bookings_app = apps.get(WIX_BOOKINGS_APP_ID, {})
    instance_token = bookings_app.get('instance', '') if isinstance(bookings_app, dict) else ''

    if not instance_token:
        return None

    logger.info(f"  Wix: found Bookings instance for {studio.get('name', '')}")

    now = datetime.now(timezone.utc)
    from_date = now.strftime('%Y-%m-%dT00:00:00Z')
    to_date = (now + timedelta(days=7)).strftime('%Y-%m-%dT23:59:59Z')

    result = cffi_post_json(
        'https://www.wixapis.com/bookings/v2/calendar/sessions/query',
        headers={'Authorization': instance_token, 'Content-Type': 'application/json'},
        json_body={'fromDate': from_date, 'toDate': to_date}
    )
    if not result:
        return None

    sessions = result.get('sessions', []) or result.get('data', {}).get('sessions', [])
    if not sessions:
        return None

    classes = []
    studio_id = studio.get('id', '')
    studio_name = studio.get('name', '')
    schedule_url = studio.get('schedule_url', '') or website

    for session in sessions:
        try:
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
                    day_name = WEEKDAY_NAMES[datetime(year, month, day).weekday()]
                except (ValueError, IndexError):
                    day_name = 'Unknown'
            else:
                start_str = start_info.get('timestamp', '')
                if not start_str:
                    continue
                start_dt = None
                for fmt in ('%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ'):
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
                time_end = f'{local_end.get("hourOfDay", 0):02d}:{local_end.get("minutesOfHour", 0):02d}'
            else:
                end_str = end_info.get('timestamp', '')
                time_end = ''
                if end_str:
                    for fmt in ('%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ'):
                        try:
                            time_end = datetime.strptime(end_str, fmt).strftime('%H:%M')
                            break
                        except ValueError:
                            continue

            class_name = session.get('title', '') or 'Yoga Class'
            teacher = ''
            for aff in session.get('affectedSchedules', []):
                owner_name = aff.get('scheduleOwnerName', '')
                if owner_name:
                    teacher = owner_name
                    break
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
                'last_checked': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            })
        except Exception:
            continue

    return classes if classes else None


def scrape_momoyoga(studio, slug):
    """Scrape Momoyoga schedule page."""
    url = f'https://www.momoyoga.com/{slug}'
    html = cffi_get(url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    classes = []
    studio_id = studio.get('id', '')
    studio_name = studio.get('name', '')

    # Momoyoga uses schedule-day divs with day headers and class rows
    current_day = None
    for el in soup.find_all(['h2', 'h3', 'h4', 'div', 'span', 'strong']):
        text = el.get_text(strip=True)
        day = normalize_day(text)
        if day:
            current_day = day
            continue

        if current_day and el.name == 'div':
            times = TIME_PATTERN.findall(text)
            if times:
                class_text = TIME_PATTERN.sub('', text).strip(' -–|/\n\t')
                parts = [p.strip() for p in class_text.split('\n') if p.strip()]
                class_name = parts[0] if parts else ''
                teacher = parts[1] if len(parts) > 1 else ''
                if class_name:
                    classes.append({
                        'studio_id': studio_id,
                        'studio_name': studio_name,
                        'day': current_day,
                        'time_start': times[0],
                        'time_end': times[1] if len(times) > 1 else '',
                        'class_name': class_name,
                        'teacher': teacher,
                        'level': 'all',
                        'source': url,
                        'verified': True,
                        'last_checked': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                    })

    # Also try looking for schedule-entry class or similar
    for entry in soup.find_all(class_=re.compile(r'schedule.*entry|class.*item|lesson', re.I)):
        text = entry.get_text(separator='\n', strip=True)
        times = TIME_PATTERN.findall(text)
        if not times:
            continue
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        class_name = ''
        teacher = ''
        day_name = None
        for line in lines:
            d = normalize_day(line)
            if d:
                day_name = d
                continue
            if TIME_PATTERN.search(line):
                continue
            if not class_name:
                class_name = line
            elif not teacher:
                teacher = line

        if class_name and times:
            classes.append({
                'studio_id': studio_id,
                'studio_name': studio_name,
                'day': day_name or current_day or 'Unknown',
                'time_start': times[0],
                'time_end': times[1] if len(times) > 1 else '',
                'class_name': class_name,
                'teacher': teacher,
                'level': 'all',
                'source': url,
                'verified': True,
                'last_checked': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            })

    return classes if classes else None


def scrape_html_schedule(studio, url, html):
    """Generic HTML scraper: look for schedule tables and day-heading patterns."""
    soup = BeautifulSoup(html, 'html.parser')
    classes = []
    studio_id = studio.get('id', '')
    studio_name = studio.get('name', '')

    # Strategy 1: Schedule tables
    for table in soup.find_all('table'):
        headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
        schedule_keywords = ['montag', 'dienstag', 'mittwoch', 'donnerstag', 'freitag',
                             'samstag', 'sonntag', 'monday', 'tuesday', 'wednesday',
                             'thursday', 'friday', 'saturday', 'sunday',
                             'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi',
                             'zeit', 'time', 'kurs', 'class', 'tag', 'day',
                             'heure', 'cours', 'orario', 'ora']
        header_text = ' '.join(headers)
        if not any(kw in header_text for kw in schedule_keywords):
            # Also check if table contains time patterns
            table_text = table.get_text()
            if not TIME_PATTERN.search(table_text):
                continue

        current_day = None
        for row in table.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            cell_texts = [c.get_text(strip=True) for c in cells]

            # Day header row
            if len(cells) == 1 and cells[0].get('colspan'):
                d = normalize_day(cell_texts[0])
                if d:
                    current_day = d
                continue

            if len(cell_texts) < 2:
                continue

            day = None
            times = []
            class_name = None
            teacher = None

            for cell in cell_texts:
                if not day:
                    day = normalize_day(cell)
                    if day:
                        continue
                found_times = TIME_PATTERN.findall(cell)
                if found_times and not times:
                    times = found_times[:2]
                    continue
                if not class_name and cell and not TIME_PATTERN.match(cell):
                    class_name = cell

            use_day = day or current_day
            if use_day and times and class_name:
                classes.append({
                    'studio_id': studio_id,
                    'studio_name': studio_name,
                    'day': use_day,
                    'time_start': times[0],
                    'time_end': times[1] if len(times) > 1 else '',
                    'class_name': class_name,
                    'teacher': teacher or '',
                    'level': 'all',
                    'source': url,
                    'verified': True,
                    'last_checked': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                })

    # Strategy 2: Day headings followed by class listings
    if not classes:
        for heading in soup.find_all(['h2', 'h3', 'h4', 'strong', 'b']):
            heading_text = heading.get_text(strip=True)
            day = normalize_day(heading_text)
            if not day:
                continue

            sibling = heading.find_next_sibling()
            while sibling and sibling.name not in ['h2', 'h3', 'h4']:
                text = sibling.get_text(strip=True)
                found_times = TIME_PATTERN.findall(text)
                if found_times:
                    class_text = TIME_PATTERN.sub('', text).strip(' -–|/')
                    if class_text:
                        classes.append({
                            'studio_id': studio_id,
                            'studio_name': studio_name,
                            'day': day,
                            'time_start': found_times[0],
                            'time_end': found_times[1] if len(found_times) > 1 else '',
                            'class_name': class_text.split('  ')[0].strip(),
                            'teacher': '',
                            'level': 'all',
                            'source': url,
                            'verified': True,
                            'last_checked': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                        })
                sibling = sibling.find_next_sibling()

    # Strategy 3: divs/sections with day names and time patterns
    if not classes:
        for section in soup.find_all(['div', 'section', 'article']):
            # Only process direct containers with schedule-like class names
            section_class = ' '.join(section.get('class', []))
            section_id = section.get('id', '')
            if not re.search(r'schedule|stundenplan|kurse|classes|horaire|timetable|calendar',
                            section_class + ' ' + section_id, re.I):
                continue

            text = section.get_text(separator='\n', strip=True)
            lines = text.split('\n')
            current_day = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                d = normalize_day(line)
                if d and len(line) < 30:
                    current_day = d
                    continue
                if current_day:
                    times = TIME_PATTERN.findall(line)
                    if times:
                        class_text = TIME_PATTERN.sub('', line).strip(' -–|/,')
                        if class_text and len(class_text) > 2:
                            classes.append({
                                'studio_id': studio_id,
                                'studio_name': studio_name,
                                'day': current_day,
                                'time_start': times[0],
                                'time_end': times[1] if len(times) > 1 else '',
                                'class_name': class_text.split('  ')[0].strip(),
                                'teacher': '',
                                'level': 'all',
                                'source': url,
                                'verified': True,
                                'last_checked': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                            })

    return classes if classes else None


# =========================================================================
# Main scraping logic
# =========================================================================

def try_scrape_studio(studio):
    """
    Try all methods to scrape schedule data for a studio.
    Returns (classes_list, method_used) or (None, None).
    """
    studio_id = studio.get('id', '')
    studio_name = studio.get('name', '')
    website = studio.get('website', '') or ''
    schedule_url = studio.get('schedule_url', '') or ''
    platform = (studio.get('booking_platform', '') or '').lower()

    logger.info(f"--- {studio_name} ({studio_id}) [platform={platform}]")

    # Step A: If platform is known, try it directly first
    if 'eversports' in platform:
        slug = detect_eversports_slug(schedule_url + ' ' + website, studio)
        if slug:
            logger.info(f"  Trying Eversports slug: {slug}")
            result = scrape_eversports(studio, slug)
            if result:
                return result, f'eversports:{slug}'
            time.sleep(RATE_LIMIT)

    if 'sportsnow' in platform:
        # Try known slug or guess from name
        name = studio.get('name', '')
        name_slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        for guess in [studio_id, name_slug]:
            logger.info(f"  Trying SportsNow slug: {guess}")
            result = scrape_sportsnow(studio, guess)
            if result:
                return result, f'sportsnow:{guess}'
            time.sleep(RATE_LIMIT)

    if 'wix' in platform:
        logger.info(f"  Trying Wix Bookings API")
        result = scrape_wix(studio)
        if result:
            return result, 'wix'
        time.sleep(RATE_LIMIT)

    # Step B: Fetch the schedule URL (or website) and detect platform
    urls_to_try = []
    if schedule_url:
        urls_to_try.append(schedule_url)
    if website and website != schedule_url:
        urls_to_try.append(website)

    visited = set()  # Track all visited URLs (normalized)

    def _norm_url(u):
        return u.rstrip('/').lower()

    for url in urls_to_try:
        if _norm_url(url) in visited:
            continue
        visited.add(_norm_url(url))
        html = cffi_get(url)
        if not html:
            time.sleep(RATE_LIMIT)
            continue

        # Detect Eversports
        ev_slug = detect_eversports_slug(html, studio)
        if ev_slug:
            logger.info(f"  Detected Eversports embed: {ev_slug}")
            time.sleep(RATE_LIMIT)
            result = scrape_eversports(studio, ev_slug)
            if result:
                return result, f'eversports:{ev_slug}'

        # Detect SportsNow
        sn_slug = detect_sportsnow_slug(html)
        if sn_slug:
            logger.info(f"  Detected SportsNow embed: {sn_slug}")
            time.sleep(RATE_LIMIT)
            result = scrape_sportsnow(studio, sn_slug)
            if result:
                return result, f'sportsnow:{sn_slug}'

        # Detect Momoyoga
        momo_slug = detect_momoyoga_slug(html)
        if momo_slug:
            logger.info(f"  Detected Momoyoga embed: {momo_slug}")
            time.sleep(RATE_LIMIT)
            result = scrape_momoyoga(studio, momo_slug)
            if result:
                return result, f'momoyoga:{momo_slug}'

        # Detect Wix
        if detect_wix(html) and 'eversports' not in platform:
            logger.info(f"  Detected Wix site")
            time.sleep(RATE_LIMIT)
            result = scrape_wix(studio)
            if result:
                return result, 'wix'

        # Try generic HTML scraping on this page
        result = scrape_html_schedule(studio, url, html)
        if result:
            return result, f'html:{url}'

        # Check for schedule subpage links in the HTML
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=re.compile(
                r'(?:stundenplan|schedule|kurse|classes|horaire|orario|angebot)', re.I)):
            href = link.get('href', '')
            if not href or href.startswith('#') or href.startswith('mailto:'):
                continue
            if href.startswith('/'):
                base = '/'.join(url.split('/')[:3])
                sub_url = base + href
            elif href.startswith('http'):
                sub_url = href
            else:
                base = '/'.join(url.split('/')[:3])
                sub_url = base + '/' + href

            if _norm_url(sub_url) in visited:
                continue
            visited.add(_norm_url(sub_url))

            logger.info(f"  Following subpage link: {sub_url}")
            time.sleep(RATE_LIMIT)
            sub_html = cffi_get(sub_url)
            if not sub_html:
                continue

            # Check for platform embeds on subpage
            ev_slug2 = detect_eversports_slug(sub_html, studio)
            if ev_slug2:
                time.sleep(RATE_LIMIT)
                result = scrape_eversports(studio, ev_slug2)
                if result:
                    return result, f'eversports:{ev_slug2}'

            sn_slug2 = detect_sportsnow_slug(sub_html)
            if sn_slug2:
                time.sleep(RATE_LIMIT)
                result = scrape_sportsnow(studio, sn_slug2)
                if result:
                    return result, f'sportsnow:{sn_slug2}'

            momo_slug2 = detect_momoyoga_slug(sub_html)
            if momo_slug2:
                time.sleep(RATE_LIMIT)
                result = scrape_momoyoga(studio, momo_slug2)
                if result:
                    return result, f'momoyoga:{momo_slug2}'

            # Try HTML scraping on subpage
            result = scrape_html_schedule(studio, sub_url, sub_html)
            if result:
                return result, f'html:{sub_url}'

        time.sleep(RATE_LIMIT)

    # Step C: Try alternative schedule URL patterns
    if website:
        base = website.rstrip('/')
        alt_paths = ['/stundenplan', '/schedule', '/kurse', '/classes',
                     '/horaire', '/orario', '/angebot', '/timetable',
                     '/programm', '/cours', '/kalender', '/calendar']
        for path in alt_paths:
            alt_url = base + path
            if _norm_url(alt_url) in visited:
                continue
            visited.add(_norm_url(alt_url))
            html = cffi_get(alt_url)
            if not html:
                time.sleep(1)  # shorter delay for 404s
                continue
            logger.info(f"  Found alt page: {alt_url}")

            # Check for embeds
            ev_slug = detect_eversports_slug(html, studio)
            if ev_slug:
                time.sleep(RATE_LIMIT)
                result = scrape_eversports(studio, ev_slug)
                if result:
                    return result, f'eversports:{ev_slug}'

            sn_slug = detect_sportsnow_slug(html)
            if sn_slug:
                time.sleep(RATE_LIMIT)
                result = scrape_sportsnow(studio, sn_slug)
                if result:
                    return result, f'sportsnow:{sn_slug}'

            momo_slug = detect_momoyoga_slug(html)
            if momo_slug:
                time.sleep(RATE_LIMIT)
                result = scrape_momoyoga(studio, momo_slug)
                if result:
                    return result, f'momoyoga:{momo_slug}'

            if detect_wix(html):
                time.sleep(RATE_LIMIT)
                result = scrape_wix(studio)
                if result:
                    return result, 'wix'

            result = scrape_html_schedule(studio, alt_url, html)
            if result:
                return result, f'html:{alt_url}'

            time.sleep(RATE_LIMIT)

    # Step D: Try Squarespace JSON endpoint
    for url in urls_to_try:
        json_url = url.rstrip('/') + '?format=json'
        html = cffi_get(json_url)
        if html:
            try:
                data = json.loads(html)
                # Check for mindbody widget
                widget_ids = re.findall(r'data-widget-id["\s:=]+["\']?([a-f0-9]{10,})', str(data))
                if widget_ids:
                    logger.info(f"  Found MindBody widget via Squarespace: {widget_ids[0]}")
                    # MindBody requires browser rendering - can't scrape via HTTP
            except (json.JSONDecodeError, ValueError):
                pass
        time.sleep(1)

    logger.info(f"  No schedule data found for {studio_name}")
    return None, None


# =========================================================================
# Update schedule files
# =========================================================================

def save_results(new_data_by_canton, schedules_by_canton):
    """Save updated schedule data back to files."""
    for canton, new_classes in new_data_by_canton.items():
        if not new_classes:
            continue

        sched_file = DATA_DIR / f'schedule_{canton}.json'
        if canton in schedules_by_canton:
            sched_data = schedules_by_canton[canton]
        else:
            sched_data = {
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'classes': [],
            }

        existing_ids = set()
        for c in sched_data.get('classes', []):
            existing_ids.add(c.get('studio_id'))

        for studio_id, classes in new_classes.items():
            # Remove any old entries for this studio
            sched_data['classes'] = [
                c for c in sched_data.get('classes', [])
                if c.get('studio_id') != studio_id
            ]
            sched_data['classes'].extend(classes)

        sched_data['last_updated'] = datetime.now(timezone.utc).isoformat()

        with open(sched_file, 'w', encoding='utf-8') as f:
            json.dump(sched_data, f, ensure_ascii=False, indent=2)
            f.write('\n')
        logger.info(f"Saved schedule_{canton}.json")


def main():
    remaining, studios_by_canton, schedules_by_canton = load_all_data()
    logger.info(f"Found {len(remaining)} studios without schedule data")

    # Save remaining list
    remaining_info = []
    for s in remaining:
        remaining_info.append({
            'id': s.get('id'),
            'name': s.get('name'),
            'canton': s.get('_canton'),
            'website': s.get('website', ''),
            'schedule_url': s.get('schedule_url', ''),
            'booking_platform': s.get('booking_platform', ''),
        })

    os.makedirs(TOOLS_DIR, exist_ok=True)
    with open(TOOLS_DIR / 'remaining_studios.json', 'w', encoding='utf-8') as f:
        json.dump(remaining_info, f, ensure_ascii=False, indent=2)
        f.write('\n')
    logger.info(f"Saved remaining_studios.json ({len(remaining_info)} studios)")

    # Scrape each studio
    results = {}  # canton -> {studio_id -> [classes]}
    successes = []
    failures = []
    method_stats = {}

    for i, studio in enumerate(remaining):
        canton = studio['_canton']
        studio_id = studio['id']
        logger.info(f"\n[{i+1}/{len(remaining)}] Processing {studio.get('name', '')} ({canton})")

        classes, method = try_scrape_studio(studio)

        if classes:
            if canton not in results:
                results[canton] = {}
            results[canton][studio_id] = classes
            successes.append({
                'id': studio_id,
                'name': studio.get('name', ''),
                'canton': canton,
                'classes_found': len(classes),
                'method': method,
            })
            method_name = method.split(':')[0] if method else 'unknown'
            method_stats[method_name] = method_stats.get(method_name, 0) + 1
            logger.info(f"  SUCCESS: {len(classes)} classes via {method}")
        else:
            failures.append({
                'id': studio_id,
                'name': studio.get('name', ''),
                'canton': canton,
                'website': studio.get('website', ''),
                'schedule_url': studio.get('schedule_url', ''),
                'booking_platform': studio.get('booking_platform', ''),
            })

    # Save results to schedule files
    save_results(results, schedules_by_canton)

    # Print summary
    total_classes = sum(s['classes_found'] for s in successes)
    print("\n" + "=" * 70)
    print("SCRAPING RESULTS SUMMARY")
    print("=" * 70)
    print(f"Total studios attempted: {len(remaining)}")
    print(f"Studios recovered: {len(successes)}")
    print(f"Studios failed: {len(failures)}")
    print(f"Total new classes: {total_classes}")
    print()

    print("Methods used:")
    for method, count in sorted(method_stats.items(), key=lambda x: -x[1]):
        print(f"  {method}: {count} studios")
    print()

    if successes:
        print("Successful studios:")
        for s in sorted(successes, key=lambda x: -x['classes_found']):
            print(f"  {s['name']} ({s['canton']}): {s['classes_found']} classes via {s['method']}")
    print()

    if failures:
        print(f"Failed studios ({len(failures)}):")
        for f in sorted(failures, key=lambda x: x['canton']):
            platform = f.get('booking_platform', 'unknown')
            print(f"  {f['name']} ({f['canton']}) [{platform}] - {f.get('website', 'no website')}")

    # Save summary
    summary = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'total_attempted': len(remaining),
        'total_recovered': len(successes),
        'total_failed': len(failures),
        'total_new_classes': total_classes,
        'method_stats': method_stats,
        'successes': successes,
        'failures': failures,
    }
    with open(TOOLS_DIR / 'scrape_remaining_results.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        f.write('\n')


if __name__ == '__main__':
    main()
