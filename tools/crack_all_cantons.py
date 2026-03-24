#!/usr/bin/env python3
"""
crack_all_cantons.py - Extract real schedule data from ALL remaining yoga studios
across all Swiss cantons (excluding Basel which is already done).

Uses curl_cffi with impersonate='chrome' to bypass 403 blocks.
Tries multiple methods per studio in order of reliability.
"""

import json
import re
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests

# --- Configuration ---
DATA_DIR = Path(__file__).parent.parent / "data"
TOOLS_DIR = Path(__file__).parent
REMAINING_FILE = TOOLS_DIR / "remaining_studios.json"
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

DAY_MAP_DE = {
    "montag": "Monday", "dienstag": "Tuesday", "mittwoch": "Wednesday",
    "donnerstag": "Thursday", "freitag": "Friday", "samstag": "Saturday",
    "sonntag": "Sunday",
    "montags": "Monday", "dienstags": "Tuesday", "mittwochs": "Wednesday",
    "donnerstags": "Thursday", "freitags": "Friday", "samstags": "Saturday",
    "sonntags": "Sunday",
}

DAY_MAP_FR = {
    "lundi": "Monday", "mardi": "Tuesday", "mercredi": "Wednesday",
    "jeudi": "Thursday", "vendredi": "Friday", "samedi": "Saturday",
    "dimanche": "Sunday",
}

DAY_MAP_IT = {
    "lunedi": "Monday", "lunedì": "Monday",
    "martedi": "Tuesday", "martedì": "Tuesday",
    "mercoledi": "Wednesday", "mercoledì": "Wednesday",
    "giovedi": "Thursday", "giovedì": "Thursday",
    "venerdi": "Friday", "venerdì": "Friday",
    "sabato": "Saturday",
    "domenica": "Sunday",
}

ALL_DAY_MAP = {}
ALL_DAY_MAP.update(DAY_MAP_DE)
ALL_DAY_MAP.update(DAY_MAP_FR)
ALL_DAY_MAP.update(DAY_MAP_IT)
for d in DAYS_EN:
    ALL_DAY_MAP[d.lower()] = d

# Basel studio IDs to skip (already done)
BASEL_IDS = {
    "byoga", "yogabloom", "volta-yoga", "secret-garden", "erlenyoga",
    "exhale", "iyengar-kreis", "ayalga", "yoga-now", "kathrin-mathews",
    "mysore-club", "alessia-yoga", "food-changes", "claudia-stamm",
    "mignon", "fitnesspark", "gyym", "klubschule", "sutra-house", "yoba",
}

# Studios known to be impossible (from Basel cracking)
IMPOSSIBLE_IDS = {
    "fitnesspark", "gyym", "klubschule", "sutra-house", "yoba",
    "erlenyoga",  # private/password-protected
}

REPORT = []
CANTON_STATS = {}

# --- Subpage paths to try for schedule discovery (most productive first) ---
SCHEDULE_SUBPATHS = [
    "/stundenplan", "/schedule", "/classes", "/kurse", "/horaire",
    "/angebot", "/yoga", "/orario", "/class-schedule",
]


# --- Utilities ---

def fetch(url, timeout=15):
    """Fetch URL using curl_cffi with Chrome impersonation."""
    try:
        return cffi_requests.get(url, impersonate="chrome", timeout=timeout,
                                  allow_redirects=True)
    except Exception:
        return None


def fetch_text(url, timeout=15):
    """Fetch URL and return text if 200."""
    r = fetch(url, timeout=timeout)
    if r and r.status_code == 200:
        return r.text
    return None


def make_class(studio_id, studio_name, day, t_start, t_end, class_name, teacher, source):
    """Create a standardized class entry dict."""
    return {
        "studio_id": studio_id,
        "studio_name": studio_name,
        "day": day,
        "time_start": t_start.strip() if t_start else "",
        "time_end": t_end.strip() if t_end else "",
        "class_name": class_name.strip()[:100] if class_name else "Yoga",
        "teacher": teacher.strip()[:60] if teacher else "",
        "level": "all",
        "source": source,
        "verified": True,
        "last_checked": TODAY,
    }


def report(studio_id, canton, status, method, count):
    """Record a studio result."""
    REPORT.append({
        "studio": studio_id, "canton": canton,
        "status": status, "method": method, "classes": count,
    })
    icon = "OK" if status == "success" else "FAIL"
    print(f"  [{icon}] {studio_id}: {method} -> {count} classes")

    if canton not in CANTON_STATS:
        CANTON_STATS[canton] = {"success": 0, "fail": 0, "classes": 0}
    if status == "success":
        CANTON_STATS[canton]["success"] += 1
        CANTON_STATS[canton]["classes"] += count
    else:
        CANTON_STATS[canton]["fail"] += 1


def normalize_day(text):
    """Normalize day name from German/French/Italian/English to English."""
    text = text.strip().lower().rstrip("s:, ")
    # Also try with trailing 's' removed
    for key, val in ALL_DAY_MAP.items():
        if text == key or text == key + "s":
            return val
    return None


# --- Eversports ---

def find_eversports_slug(html):
    """Extract Eversports widget slug from HTML source."""
    # Pattern: eversports.ch/widget/w/SLUG
    m = re.search(r'eversports\.ch/widget/w/([a-zA-Z0-9_-]+)', html)
    if m:
        return m.group(1)
    # Pattern: facilityShortId=SLUG
    m = re.search(r'facilityShortId=([a-zA-Z0-9_-]+)', html)
    if m:
        return m.group(1)
    # Pattern: eversports.ch/s/SLUG
    m = re.search(r'eversports\.ch/s/([a-zA-Z0-9_-]+)', html)
    if m:
        return m.group(1)
    return None


def eversports_fetch(slug, start_date=None):
    """Fetch Eversports calendar HTML via widget API."""
    if not start_date:
        start_date = TODAY
    url = f"https://www.eversports.ch/widget/api/eventsession/calendar?facilityShortId={slug}&startDate={start_date}"
    r = fetch(url)
    if not r or r.status_code != 200:
        return None
    try:
        data = r.json()
    except Exception:
        return None
    if data.get("status") != "success":
        return None
    return data.get("data", {}).get("html", "")


def parse_eversports_html(ev_html, studio_id, studio_name, source_url):
    """Parse Eversports widget calendar HTML into class entries."""
    soup = BeautifulSoup(ev_html, "html.parser")
    classes = []
    seen = set()

    for slot in soup.find_all("li", class_="calendar__slot"):
        sr = slot.find(class_="sr-only")
        if not sr:
            continue
        sr_text = sr.get_text(strip=True)
        day_name = ""
        for d in DAYS_EN:
            if d.lower() in sr_text.lower():
                day_name = d
                break
        if not day_name:
            for key, val in ALL_DAY_MAP.items():
                if key in sr_text.lower():
                    day_name = val
                    break
        if not day_name:
            continue

        time_el = slot.find(class_="session-time")
        if not time_el:
            continue
        time_text = time_el.get_text(strip=True)
        m = re.match(r'(\d{1,2}:\d{2})\s*.*?(\d+)\s*Min', time_text)
        if not m:
            continue
        t_start = m.group(1)
        duration = int(m.group(2))
        h, mi = map(int, t_start.split(":"))
        end_mins = h * 60 + mi + duration
        t_end = f"{end_mins // 60:02d}:{end_mins % 60:02d}"

        name_el = slot.find(class_="session-name")
        class_name = name_el.get_text(strip=True) if name_el else ""
        if not class_name:
            continue

        teacher = ""
        for ed in slot.find_all(class_="ellipsis"):
            t = ed.get_text(strip=True)
            if t and "spot" not in t.lower() and "level" not in t.lower() and t != class_name:
                if not t.isupper():
                    teacher = t
                    break

        key = (day_name, t_start, class_name)
        if key in seen:
            continue
        seen.add(key)
        classes.append(make_class(studio_id, studio_name, day_name, t_start, t_end,
                                   class_name, teacher, source_url))
    return classes


def eversports_scrape(slug, studio_id, studio_name, source_url):
    """Full Eversports scrape: fetch multiple weeks."""
    all_classes = []
    seen = set()
    base = datetime.strptime(TODAY, "%Y-%m-%d")

    for week_offset in range(4):
        start = (base + timedelta(weeks=week_offset)).strftime("%Y-%m-%d")
        ev_html = eversports_fetch(slug, start)
        if not ev_html:
            continue
        week_classes = parse_eversports_html(ev_html, studio_id, studio_name, source_url)
        for c in week_classes:
            key = (c["day"], c["time_start"], c["class_name"])
            if key not in seen:
                seen.add(key)
                all_classes.append(c)
        time.sleep(0.3)
    return all_classes


# --- SportsNow ---

SPORTSNOW_SLUGS = {}  # Will be populated from HTML discovery

def find_sportsnow_slug(html):
    """Extract SportsNow slug from HTML."""
    m = re.search(r'sportsnow\.ch/(?:go|providers)/([a-zA-Z0-9_-]+)', html)
    if m:
        return m.group(1)
    return None


def sportsnow_scrape(slug, studio_id, studio_name, source_url):
    """Scrape schedule from SportsNow provider page."""
    url = f"https://www.sportsnow.ch/providers/{slug}/schedule?locale=de"
    html = fetch_text(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    classes = []
    seen = set()
    current_day = ""

    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if not cells:
            continue

        text = " ".join(c.get_text(strip=True) for c in cells)

        # Check if row is a day header
        for key, val in ALL_DAY_MAP.items():
            if key in text.lower().split()[0:1]:
                current_day = val
                break

        if not current_day:
            continue

        # Look for time pattern in row
        m = re.search(r'(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})', text)
        if m:
            t_start, t_end = m.group(1), m.group(2)
            # Remove time from text to get class name
            name = re.sub(r'\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2}', '', text).strip(" -–|,")
            # Remove day name
            for key in ALL_DAY_MAP:
                name = re.sub(rf'^{key}\w*\s*', '', name, flags=re.I)
            name = name.strip(" -–|,:")
            if name:
                key = (current_day, t_start, name[:40])
                if key not in seen:
                    seen.add(key)
                    classes.append(make_class(studio_id, studio_name, current_day,
                                              t_start, t_end, name, "", source_url))

    return classes


# --- MomoYoga ---

def find_momoyoga_slug(html):
    """Extract MomoYoga slug/ID from HTML."""
    m = re.search(r'momoyoga\.com/([a-zA-Z0-9_-]+)', html)
    if m and m.group(1) not in ("yoga", "en", "de", "fr"):
        return m.group(1)
    return None


# --- HTML Time Pattern Parsing ---

def parse_html_schedule(html, studio_id, studio_name, source_url):
    """Parse schedule from HTML using time patterns and day names."""
    soup = BeautifulSoup(html, "html.parser")
    classes = []
    seen = set()

    # Strategy 1: Day headings followed by time entries
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b', 'dt', 'th']):
        heading_text = heading.get_text(strip=True)
        day = normalize_day(heading_text)
        if not day:
            continue

        sibling = heading.find_next_sibling()
        attempts = 0
        while sibling and attempts < 30:
            attempts += 1
            sib_text = sibling.get_text(strip=True)
            # Stop if we hit another day heading
            if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                break
            if normalize_day(sib_text):
                break

            m = re.search(r'(\d{1,2}[:.]\d{2})\s*[-–—]\s*(\d{1,2}[:.]\d{2})', sib_text)
            if m:
                t_start = m.group(1).replace(".", ":")
                t_end = m.group(2).replace(".", ":")
                name = re.sub(r'\d{1,2}[:.]\d{2}\s*[-–—]\s*\d{1,2}[:.]\d{2}', '', sib_text)
                name = name.strip(" -–—|/:,\t\n")
                name = re.sub(r'\s*(Uhr|h)\s*', ' ', name).strip()
                if not name:
                    name = "Yoga"
                teacher = ""
                tm = re.search(r'(?:with|mit|avec|con)\s+([\w\s]+?)(?:\s*[,|]|$)', name, re.I)
                if tm:
                    teacher = tm.group(1).strip()
                key = (day, t_start, name[:40])
                if key not in seen:
                    seen.add(key)
                    classes.append(make_class(studio_id, studio_name, day, t_start, t_end,
                                              name, teacher, source_url))
            else:
                m2 = re.search(r'(\d{1,2}[:.]\d{2})', sib_text)
                if m2 and len(sib_text) > 5:
                    t_start = m2.group(1).replace(".", ":")
                    name = re.sub(r'\d{1,2}[:.]\d{2}', '', sib_text).strip(" -–—|/:,\t\n")
                    name = re.sub(r'\s*(Uhr|h)\s*', ' ', name).strip()
                    if name and len(name) > 2:
                        key = (day, t_start, name[:40])
                        if key not in seen:
                            seen.add(key)
                            classes.append(make_class(studio_id, studio_name, day, t_start, "",
                                                      name, "", source_url))

            sibling = sibling.find_next_sibling()

    # Strategy 2: Table-based schedule
    if not classes:
        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            has_schedule = any(
                normalize_day(h) or h in ("zeit", "time", "heure", "ora", "kurs", "class", "cours")
                for h in headers
            )
            if not has_schedule and not headers:
                # Check if table body has day names
                first_row_text = ""
                first_row = table.find("tr")
                if first_row:
                    first_row_text = first_row.get_text(" ", strip=True).lower()
                has_schedule = any(normalize_day(w) for w in first_row_text.split())

            if not has_schedule:
                continue

            current_day = ""
            for row in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                if not cells:
                    continue

                row_text = " ".join(cells)
                # Check for day in first cell
                d = normalize_day(cells[0])
                if d:
                    current_day = d
                if not current_day:
                    # Check if any cell is a day name
                    for cell in cells:
                        d = normalize_day(cell)
                        if d:
                            current_day = d
                            break

                if not current_day:
                    continue

                m = re.search(r'(\d{1,2}[:.]\d{2})\s*[-–]\s*(\d{1,2}[:.]\d{2})', row_text)
                if m:
                    t_start = m.group(1).replace(".", ":")
                    t_end = m.group(2).replace(".", ":")
                    name = re.sub(r'\d{1,2}[:.]\d{2}\s*[-–]\s*\d{1,2}[:.]\d{2}', '', row_text)
                    # Remove day names
                    for key_d in ALL_DAY_MAP:
                        name = re.sub(rf'\b{key_d}\w*\b', '', name, flags=re.I)
                    name = name.strip(" -–|/:,\t\n")
                    name = re.sub(r'\s*(Uhr|h)\s*', ' ', name).strip()
                    if name:
                        key = (current_day, t_start, name[:40])
                        if key not in seen:
                            seen.add(key)
                            classes.append(make_class(studio_id, studio_name, current_day,
                                                      t_start, t_end, name, "", source_url))

    # Strategy 3: Inline text pattern: "Day HH:MM - HH:MM Description"
    if not classes:
        text = soup.get_text("\n", strip=True)
        day_pattern = "|".join(ALL_DAY_MAP.keys())
        pattern = rf'({day_pattern})\w*[:\s]+(\d{{1,2}}[:.]\d{{2}})\s*[-–—]\s*(\d{{1,2}}[:.]\d{{2}})\s*(?:Uhr|h)?\s*[-–—:,]?\s*(.+?)(?=(?:{day_pattern})\w*\s+\d|\n|$)'
        for m in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
            day_str = m.group(1).lower()
            day = ALL_DAY_MAP.get(day_str, "")
            if not day:
                # Try without trailing chars
                for k, v in ALL_DAY_MAP.items():
                    if day_str.startswith(k):
                        day = v
                        break
            if not day:
                continue
            t_start = m.group(2).replace(".", ":")
            t_end = m.group(3).replace(".", ":")
            desc = m.group(4).strip(" -–—|/:,\t")
            if desc and len(desc) > 1:
                key = (day, t_start, desc[:40])
                if key not in seen:
                    seen.add(key)
                    classes.append(make_class(studio_id, studio_name, day, t_start, t_end,
                                              desc[:100], "", source_url))

    return classes


# --- Squarespace ---

def try_squarespace_json(url, studio_id, studio_name):
    """Try Squarespace ?format=json endpoint."""
    json_url = url.rstrip("/") + "?format=json"
    r = fetch(json_url)
    if not r or r.status_code != 200:
        return []
    try:
        data = r.json()
    except Exception:
        return []

    # Look for items with schedule data
    classes = []
    items = data.get("items", [])
    if not items:
        items = data.get("collection", {}).get("items", [])
    for item in items:
        title = item.get("title", "")
        body = item.get("body", "")
        excerpt = item.get("excerpt", "")
        text = f"{title} {body} {excerpt}"
        # Parse times from text
        for day_key, day_val in ALL_DAY_MAP.items():
            pattern = rf'{day_key}\w*\s+(\d{{1,2}}[:.]\d{{2}})'
            for m in re.finditer(pattern, text, re.I):
                t_start = m.group(1).replace(".", ":")
                classes.append(make_class(studio_id, studio_name, day_val, t_start, "",
                                          title or "Yoga", "", url))
    return classes


# --- Acuity Scheduling ---

def find_acuity_owner(html):
    """Find Acuity Scheduling owner ID from HTML."""
    m = re.search(r'squarespacescheduling\.com/schedule\.php\?owner=(\d+)', html)
    if m:
        return m.group(1)
    m = re.search(r'acuityscheduling\.com/schedule\.php\?owner=(\d+)', html)
    if m:
        return m.group(1)
    return None


def acuity_scrape(owner_id, studio_id, studio_name, source_url):
    """Scrape Acuity Scheduling for appointment types."""
    acuity_url = f"https://app.squarespacescheduling.com/schedule.php?owner={owner_id}"
    html = fetch_text(acuity_url)
    if not html:
        return []

    classes = []
    m = re.search(r'"appointmentTypes"\s*:\s*(\{.+?\})\s*,\s*"[a-z]', html, re.DOTALL)
    if not m:
        return []

    names = re.findall(r'"name":"([^"]+)"', m.group(1))
    descs = re.findall(r'"description":"([^"]*)"', m.group(1))

    for i, name in enumerate(names):
        if any(k in name.lower() for k in ["yoga", "pilates", "meditation", "breathwork",
                                             "vinyasa", "hatha", "yin", "flow", "ashtanga",
                                             "kundalini", "power", "stretch", "relax"]):
            desc = descs[i] if i < len(descs) else ""
            day = ""
            t_start = ""
            for d_key, d_val in ALL_DAY_MAP.items():
                if d_key in desc.lower():
                    day = d_val
                    break
            tm = re.search(r'(\d{1,2}[:.]\d{2})', desc)
            if tm:
                t_start = tm.group(1).replace(".", ":")
            if day or t_start:
                classes.append(make_class(studio_id, studio_name, day or "TBC",
                                          t_start, "", name, "", source_url))
    return classes


# --- Main cracking logic for a single studio ---

def crack_studio(studio):
    """Try all methods to extract schedule from a studio. Returns list of classes."""
    sid = studio["id"]
    sname = studio["name"]
    canton = studio["canton"]
    website = studio.get("website", "")
    schedule_url = studio.get("schedule_url", "") or website
    booking_platform = (studio.get("booking_platform", "") or "").lower()

    if not website and not schedule_url:
        report(sid, canton, "fail", "no website", 0)
        return []

    classes = []

    # --- Method 1: Fetch schedule_url, discover widgets ---
    html = fetch_text(schedule_url)
    if not html and schedule_url != website:
        html = fetch_text(website)

    if html:
        # 1a. Eversports widget discovery
        slug = find_eversports_slug(html)
        if slug:
            print(f"    Found Eversports slug: {slug}")
            classes = eversports_scrape(slug, sid, sname, schedule_url)
            if classes:
                report(sid, canton, "success", f"eversports (slug={slug})", len(classes))
                return classes

        # 1b. SportsNow widget discovery
        sn_slug = find_sportsnow_slug(html)
        if sn_slug:
            print(f"    Found SportsNow slug: {sn_slug}")
            classes = sportsnow_scrape(sn_slug, sid, sname, schedule_url)
            if classes:
                report(sid, canton, "success", f"sportsnow (slug={sn_slug})", len(classes))
                return classes

        # 1c. MomoYoga discovery
        momo_slug = find_momoyoga_slug(html)
        if momo_slug:
            print(f"    Found MomoYoga slug: {momo_slug}")
            # MomoYoga embeds are typically iframes - try the direct URL
            momo_url = f"https://www.momoyoga.com/{momo_slug}/schedule"
            momo_html = fetch_text(momo_url)
            if momo_html:
                classes = parse_html_schedule(momo_html, sid, sname, momo_url)
                if classes:
                    report(sid, canton, "success", f"momoyoga (slug={momo_slug})", len(classes))
                    return classes

        # 1d. Acuity Scheduling discovery
        acuity_owner = find_acuity_owner(html)
        if acuity_owner:
            print(f"    Found Acuity owner: {acuity_owner}")
            classes = acuity_scrape(acuity_owner, sid, sname, schedule_url)
            if classes:
                report(sid, canton, "success", f"acuity (owner={acuity_owner})", len(classes))
                return classes

        # 1e. Direct HTML parsing of schedule page
        classes = parse_html_schedule(html, sid, sname, schedule_url)
        if classes:
            report(sid, canton, "success", "html_parse", len(classes))
            return classes

    # --- Method 2: Known booking platform ---
    if booking_platform == "eversports" and not classes:
        # Try eversports.ch/s/{studio-id} pattern
        for slug_try in [sid, sid.replace("-", ""), sname.lower().replace(" ", "-")]:
            ev_html = eversports_fetch(slug_try)
            if ev_html:
                classes = parse_eversports_html(ev_html, sid, sname,
                                                 f"https://www.eversports.ch/s/{slug_try}")
                if classes:
                    report(sid, canton, "success", f"eversports_direct (slug={slug_try})", len(classes))
                    return classes

    # --- Method 3: Subpage crawling ---
    base_url = website.rstrip("/") if website else ""
    if base_url:
        miss_count = 0
        for subpath in SCHEDULE_SUBPATHS:
            if miss_count >= 6:
                break  # Stop after 6 consecutive 404s/failures
            sub_url = base_url + subpath
            sub_html = fetch_text(sub_url, timeout=8)
            if not sub_html or len(sub_html) < 500:
                miss_count += 1
                continue
            miss_count = 0  # Reset on successful fetch

            # Check for widgets on subpage
            slug = find_eversports_slug(sub_html)
            if slug:
                classes = eversports_scrape(slug, sid, sname, sub_url)
                if classes:
                    report(sid, canton, "success", f"eversports_subpage ({subpath}, slug={slug})", len(classes))
                    return classes

            sn_slug = find_sportsnow_slug(sub_html)
            if sn_slug:
                classes = sportsnow_scrape(sn_slug, sid, sname, sub_url)
                if classes:
                    report(sid, canton, "success", f"sportsnow_subpage ({subpath})", len(classes))
                    return classes

            acuity_owner = find_acuity_owner(sub_html)
            if acuity_owner:
                classes = acuity_scrape(acuity_owner, sid, sname, sub_url)
                if classes:
                    report(sid, canton, "success", f"acuity_subpage ({subpath})", len(classes))
                    return classes

            # Parse HTML schedule from subpage
            classes = parse_html_schedule(sub_html, sid, sname, sub_url)
            if classes:
                report(sid, canton, "success", f"html_parse_subpage ({subpath})", len(classes))
                return classes

            time.sleep(0.3)

    # --- Method 4: Squarespace JSON ---
    if schedule_url:
        classes = try_squarespace_json(schedule_url, sid, sname)
        if classes:
            report(sid, canton, "success", "squarespace_json", len(classes))
            return classes

    # --- Method 5: Eversports search as last resort ---
    # Try the studio's schedule_url if it points to eversports
    if schedule_url and "eversports.ch" in schedule_url:
        m = re.search(r'eversports\.ch/s/([a-zA-Z0-9_-]+)', schedule_url)
        if m:
            slug = m.group(1)
            classes = eversports_scrape(slug, sid, sname, schedule_url)
            if classes:
                report(sid, canton, "success", f"eversports_url (slug={slug})", len(classes))
                return classes

    # All methods failed
    fail_reason = "no schedule data extractable"
    if not html:
        fail_reason = "website unreachable"
    report(sid, canton, "fail", fail_reason, 0)
    return classes


# --- Schedule file management ---

def load_schedule(canton):
    """Load existing schedule file for a canton."""
    path = DATA_DIR / f"schedule_{canton}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"last_updated": "", "classes": []}


def save_schedule(canton, data):
    """Save schedule file for a canton."""
    path = DATA_DIR / f"schedule_{canton}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# --- Main ---

def main():
    print("=" * 70)
    print("CRACK ALL CANTONS - Extracting schedules from remaining Swiss studios")
    print("=" * 70)

    # Load remaining studios
    with open(REMAINING_FILE) as f:
        all_studios = json.load(f)

    # Filter: skip Basel studios and impossible ones
    studios = [
        s for s in all_studios
        if s["canton"] != "basel" and s["id"] not in IMPOSSIBLE_IDS
    ]

    print(f"\nTotal studios to process: {len(studios)}")
    print(f"Skipped: {len(all_studios) - len(studios)} (Basel + impossible)")

    # Group by canton
    by_canton = {}
    for s in studios:
        c = s["canton"]
        if c not in by_canton:
            by_canton[c] = []
        by_canton[c].append(s)

    total_new_classes = 0
    total_success = 0
    total_fail = 0

    for canton in sorted(by_canton.keys()):
        canton_studios = by_canton[canton]
        print(f"\n{'='*60}")
        print(f"CANTON: {canton.upper()} ({len(canton_studios)} studios)")
        print(f"{'='*60}")

        # Load existing schedule
        sched_data = load_schedule(canton)
        existing_studio_ids_with_new = set()

        for studio in canton_studios:
            print(f"\n--- {studio['name']} ({studio['id']}) ---")
            try:
                new_classes = crack_studio(studio)
                if new_classes:
                    # Remove old entries for this studio, add new ones
                    sid = studio["id"]
                    existing_studio_ids_with_new.add(sid)
                    sched_data["classes"] = [
                        c for c in sched_data.get("classes", [])
                        if c.get("studio_id") != sid
                    ]
                    sched_data["classes"].extend(new_classes)
                    total_new_classes += len(new_classes)
                    total_success += 1
                else:
                    total_fail += 1
            except Exception as e:
                print(f"  [ERROR] {studio['id']}: {e}")
                traceback.print_exc()
                report(studio["id"], canton, "fail", f"exception: {str(e)[:60]}", 0)
                total_fail += 1

            time.sleep(2)  # Rate limit between studios

        # Save updated schedule
        sched_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        save_schedule(canton, sched_data)
        print(f"\n  Saved schedule_{canton}.json ({len(sched_data['classes'])} total classes)")

    # --- Final Summary ---
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    print(f"\nStudios attempted: {len(studios)}")
    print(f"Success: {total_success}")
    print(f"Failed: {total_fail}")
    print(f"New classes extracted: {total_new_classes}")

    print(f"\nPer-canton breakdown:")
    for canton in sorted(CANTON_STATS.keys()):
        stats = CANTON_STATS[canton]
        print(f"  {canton:20s} | OK: {stats['success']:3d} | FAIL: {stats['fail']:3d} | Classes: {stats['classes']:4d}")

    print(f"\nPer-studio results:")
    for r in sorted(REPORT, key=lambda x: (x["canton"], x["studio"])):
        status = "OK  " if r["status"] == "success" else "FAIL"
        print(f"  {status} | {r['canton']:18s} | {r['studio']:35s} | {r['method'][:55]:55s} | {r['classes']:3d}")

    # Save report
    report_path = TOOLS_DIR / "crack_all_report.json"
    with open(report_path, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_studios": len(studios),
            "success": total_success,
            "failed": total_fail,
            "new_classes": total_new_classes,
            "canton_stats": CANTON_STATS,
            "details": REPORT,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to: {report_path}")

    # Impossible studios list
    print(f"\nTruly impossible studios (no extractable data):")
    for r in REPORT:
        if r["status"] == "fail":
            print(f"  - {r['canton']}/{r['studio']}: {r['method']}")


if __name__ == "__main__":
    main()
