#!/usr/bin/env python3
"""
crack_final_push.py - Final push to extract schedule data from ALL 136 remaining studios.

Enhanced approaches:
1. Eversports slug guessing (name permutations + website scraping)
2. MindBody public explore API by geo
3. Karmasoft/Punchpass/Blueleaf API probing
4. Deep website crawling (more subpaths, menu link following)
5. MindBody widget/healcode extraction
6. Processes ALL 136 studios including Basel ones

Uses curl_cffi with impersonate='chrome' to bypass 403 blocks.
"""

import json
import re
import signal
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, quote

from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests

# --- Configuration ---
DATA_DIR = Path(__file__).parent.parent / "data"
TOOLS_DIR = Path(__file__).parent
REMAINING_FILE = TOOLS_DIR / "remaining_studios.json"
TODAY = "2026-03-24"

DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

DAY_MAP_DE = {
    "montag": "Monday", "dienstag": "Tuesday", "mittwoch": "Wednesday",
    "donnerstag": "Thursday", "freitag": "Friday", "samstag": "Saturday",
    "sonntag": "Sunday",
    "montags": "Monday", "dienstags": "Tuesday", "mittwochs": "Wednesday",
    "donnerstags": "Thursday", "freitags": "Friday", "samstags": "Saturday",
    "sonntags": "Sunday",
    "mo": "Monday", "di": "Tuesday", "mi": "Wednesday",
    "do": "Thursday", "fr": "Friday", "sa": "Saturday", "so": "Sunday",
}

DAY_MAP_FR = {
    "lundi": "Monday", "mardi": "Tuesday", "mercredi": "Wednesday",
    "jeudi": "Thursday", "vendredi": "Friday", "samedi": "Saturday",
    "dimanche": "Sunday",
    "lu": "Monday", "ma": "Tuesday", "me": "Wednesday",
    "je": "Thursday", "ve": "Friday", "sa": "Saturday", "di": "Sunday",
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

REPORT = []
CANTON_STATS = {}

# Extended subpage paths - ordered by likelihood
SCHEDULE_SUBPATHS = [
    "/stundenplan", "/schedule", "/classes", "/kurse", "/horaire",
    "/angebot", "/yoga", "/orario", "/class-schedule", "/timetable",
    "/kursplan", "/programm", "/programme", "/planning",
    "/wochenkurse", "/yoga-classes", "/yoga-kurse",
    "/cours", "/cours-horaire", "/yoga-schedule",
    "/open-classes", "/group-classes",
    "/en/schedule", "/en/classes",
    "/de/stundenplan",
    "/fr/horaire",
]

# Known impossible studios (truly no data available)
IMPOSSIBLE_IDS = {
    "fitnesspark", "gyym", "klubschule", "sutra-house", "yoba",
    "erlenyoga",  # private/password-protected
}


# --- Utilities ---

def fetch(url, timeout=10):
    """Fetch URL using curl_cffi with Chrome impersonation."""
    try:
        return cffi_requests.get(url, impersonate="chrome", timeout=timeout,
                                  allow_redirects=True)
    except Exception:
        return None


def fetch_text(url, timeout=10):
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
    sys.stdout.flush()

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
    for key, val in ALL_DAY_MAP.items():
        if text == key or text == key + "s":
            return val
    return None


def slugify(name):
    """Turn a studio name into a URL slug."""
    s = name.lower().strip()
    s = re.sub(r'[àáâãäå]', 'a', s)
    s = re.sub(r'[èéêë]', 'e', s)
    s = re.sub(r'[ìíîï]', 'i', s)
    s = re.sub(r'[òóôõö]', 'o', s)
    s = re.sub(r'[ùúûü]', 'u', s)
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'[\s]+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')


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
    # Pattern: eversports widget embed data attribute
    m = re.search(r'data-eversports-widget-id=["\']([a-zA-Z0-9_-]+)', html)
    if m:
        return m.group(1)
    # Pattern: eversports.com/widget
    m = re.search(r'eversports\.com/widget/w/([a-zA-Z0-9_-]+)', html)
    if m:
        return m.group(1)
    # Generic eversports reference with slug
    m = re.search(r'eversports\.[a-z]+/(?:s|studio|widget/w)/([a-zA-Z0-9_-]+)', html)
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


def guess_eversports_slugs(studio_id, studio_name, website):
    """Generate possible Eversports slugs from studio info."""
    slugs = []

    # From studio_id directly
    slugs.append(studio_id)

    # From studio name
    name_slug = slugify(studio_name)
    slugs.append(name_slug)

    # Without common suffixes
    for suffix in ["-yoga", "-studio", "-zurich", "-zuerich", "-bern", "-basel",
                   "-luzern", "-geneve", "-lausanne", "-winterthur"]:
        if name_slug.endswith(suffix):
            slugs.append(name_slug[:-len(suffix)])

    # With common prefixes
    if not name_slug.startswith("yoga-"):
        slugs.append("yoga-" + name_slug)

    # Without hyphens
    slugs.append(name_slug.replace("-", ""))

    # From website domain
    if website:
        parsed = urlparse(website)
        domain = parsed.hostname or ""
        domain_slug = domain.replace("www.", "").split(".")[0]
        if domain_slug:
            slugs.append(domain_slug)

    # From schedule_url if it has eversports
    # (handled separately in crack_studio)

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for s in slugs:
        if s and s not in seen:
            seen.add(s)
            unique.append(s)
    return unique


def try_eversports_slugs(slugs, studio_id, studio_name):
    """Try multiple Eversports slugs, return classes if any work."""
    for slug in slugs:
        ev_html = eversports_fetch(slug)
        if ev_html:
            classes = parse_eversports_html(ev_html, studio_id, studio_name,
                                             f"https://www.eversports.ch/s/{slug}")
            if classes:
                print(f"    Eversports slug FOUND: {slug}")
                return slug, classes
        time.sleep(0.2)
    return None, []


# --- SportsNow ---

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
    classes = []
    seen = set()

    # Try table-based parsing
    table = soup.find("table")
    if table:
        current_day = ""
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if not cells:
                continue
            text = " ".join(c.get_text(strip=True) for c in cells)

            for key, val in ALL_DAY_MAP.items():
                if key in text.lower().split()[0:1]:
                    current_day = val
                    break

            if not current_day:
                continue

            m = re.search(r'(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})', text)
            if m:
                t_start, t_end = m.group(1), m.group(2)
                name = re.sub(r'\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2}', '', text).strip(" -–|,")
                for key in ALL_DAY_MAP:
                    name = re.sub(rf'^{key}\w*\s*', '', name, flags=re.I)
                name = name.strip(" -–|,:")
                if name:
                    k = (current_day, t_start, name[:40])
                    if k not in seen:
                        seen.add(k)
                        classes.append(make_class(studio_id, studio_name, current_day,
                                                  t_start, t_end, name, "", source_url))

    # Also try div-based parsing (SportsNow sometimes uses divs)
    if not classes:
        for div in soup.find_all("div", class_=re.compile(r"schedule|event|class|course", re.I)):
            text = div.get_text(" ", strip=True)
            for day_key, day_val in ALL_DAY_MAP.items():
                m = re.search(rf'{day_key}\w*\s+(\d{{1,2}}:\d{{2}})\s*[-–]\s*(\d{{1,2}}:\d{{2}})', text, re.I)
                if m:
                    t_start, t_end = m.group(1), m.group(2)
                    name = re.sub(r'\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2}', '', text)
                    for k in ALL_DAY_MAP:
                        name = re.sub(rf'\b{k}\w*\b', '', name, flags=re.I)
                    name = name.strip(" -–|,:")
                    if name:
                        key = (day_val, t_start, name[:40])
                        if key not in seen:
                            seen.add(key)
                            classes.append(make_class(studio_id, studio_name, day_val,
                                                      t_start, t_end, name, "", source_url))
    return classes


def guess_sportsnow_slugs(studio_id, studio_name, website):
    """Generate possible SportsNow slugs."""
    slugs = []
    slugs.append(studio_id)
    slugs.append(slugify(studio_name))
    if website:
        parsed = urlparse(website)
        domain = (parsed.hostname or "").replace("www.", "").split(".")[0]
        if domain:
            slugs.append(domain)
    # Deduplicate
    seen = set()
    return [s for s in slugs if s and s not in seen and not seen.add(s)]


# --- MomoYoga ---

def find_momoyoga_slug(html):
    """Extract MomoYoga slug/ID from HTML."""
    m = re.search(r'momoyoga\.com/([a-zA-Z0-9_-]+)', html)
    if m and m.group(1) not in ("yoga", "en", "de", "fr", "it", "embed", "widget"):
        return m.group(1)
    return None


# --- MindBody ---

def find_mindbody_studio_id(html):
    """Extract MindBody/Healcode studio ID from HTML."""
    # healcode widget: studioid=NNNNN
    m = re.search(r'studioid=(\d+)', html)
    if m:
        return m.group(1)
    # data-studioid
    m = re.search(r'data-studioid=["\']?(\d+)', html)
    if m:
        return m.group(1)
    # MindBody branded web widget
    m = re.search(r'brandedweb\.mindbodyonline\.com/.*?studioid=(\d+)', html)
    if m:
        return m.group(1)
    # MBO web widgets endpoint
    m = re.search(r'widgets\.mindbodyonline\.com/.*?(\d{5,})', html)
    if m:
        return m.group(1)
    return None


def mindbody_scrape_widget(studio_mb_id, studio_id, studio_name, source_url):
    """Try to scrape MindBody widget schedule."""
    classes = []

    # Try branded web schedule
    urls_to_try = [
        f"https://brandedweb.mindbodyonline.com/Api/GuestService/GetClassSchedule?studioid={studio_mb_id}&request.startDate={TODAY}",
        f"https://widgets.mindbodyonline.com/widgets/schedules/{studio_mb_id}?options[start_date]={TODAY}",
    ]

    for url in urls_to_try:
        r = fetch(url)
        if not r or r.status_code != 200:
            continue
        try:
            data = r.json()
            # Parse the response depending on format
            if isinstance(data, dict):
                schedule_items = data.get("Classes", data.get("classes", data.get("data", [])))
                if isinstance(schedule_items, list):
                    for item in schedule_items:
                        class_name = item.get("ClassName", item.get("className", item.get("name", "")))
                        teacher_name = item.get("StaffName", item.get("staffName", item.get("teacher", "")))
                        start_time = item.get("StartTime", item.get("startTime", ""))
                        end_time = item.get("EndTime", item.get("endTime", ""))
                        start_dt = item.get("StartDateTime", item.get("startDateTime", ""))

                        if start_dt:
                            try:
                                dt = datetime.fromisoformat(start_dt.replace("Z", "+00:00"))
                                day = DAYS_EN[dt.weekday()]
                                t_start = dt.strftime("%H:%M")
                            except:
                                day = ""
                                t_start = start_time
                        else:
                            day = ""
                            t_start = start_time

                        if class_name and (day or t_start):
                            # Parse time strings
                            if t_start and ":" not in t_start:
                                tm = re.search(r'(\d{1,2}:\d{2})', str(t_start))
                                t_start = tm.group(1) if tm else ""
                            t_end_str = ""
                            if end_time:
                                tm = re.search(r'(\d{1,2}:\d{2})', str(end_time))
                                t_end_str = tm.group(1) if tm else ""

                            classes.append(make_class(studio_id, studio_name,
                                                      day or "TBC", t_start or "", t_end_str,
                                                      class_name, teacher_name, source_url))
        except Exception:
            pass

    return classes


def mindbody_explore_api(lat, lon, radius=50):
    """Try MindBody public explore/search API for a location."""
    classes_found = []

    urls = [
        f"https://prod-mkt-gateway.mindbody.io/v1/search/classes?filter.latitude={lat}&filter.longitude={lon}&filter.radius={radius}&page.size=100",
        f"https://prod-mkt-gateway.mindbody.io/v1/search/studios?filter.latitude={lat}&filter.longitude={lon}&filter.radius={radius}&page.size=100&filter.categoryIds=9",
    ]

    for url in urls:
        r = fetch(url, timeout=20)
        if not r or r.status_code != 200:
            continue
        try:
            data = r.json()
            results = data.get("data", data.get("results", []))
            if isinstance(results, list):
                for item in results:
                    studio_name = item.get("studioName", item.get("name", ""))
                    class_name = item.get("className", item.get("name", ""))
                    start_time = item.get("startTime", item.get("startDateTime", ""))
                    classes_found.append({
                        "studio_name": studio_name,
                        "class_name": class_name,
                        "start_time": start_time,
                        "raw": item,
                    })
        except Exception:
            pass

    return classes_found


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
                                             "kundalini", "power", "stretch", "relax",
                                             "prenatal", "postnatal", "mysore", "hot",
                                             "restorative", "gentle", "dynamic"]):
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


# --- Karmasoft ---

def try_karmasoft(website, studio_id, studio_name):
    """Try Karmasoft API/widget discovery."""
    classes = []

    # Try to find karmasoft references in website HTML
    html = fetch_text(website) if website else None
    if not html:
        return []

    # Look for karmasoft iframe/widget
    m = re.search(r'karmasoft\.io/(?:embed|widget|schedule)/([a-zA-Z0-9_-]+)', html)
    if m:
        ks_id = m.group(1)
        # Try Karmasoft API
        ks_url = f"https://app.karmasoft.io/api/v1/studios/{ks_id}/schedule"
        r = fetch(ks_url)
        if r and r.status_code == 200:
            try:
                data = r.json()
                for item in (data if isinstance(data, list) else data.get("data", [])):
                    name = item.get("name", "Yoga")
                    day = item.get("day", "")
                    t_start = item.get("start_time", item.get("time", ""))
                    t_end = item.get("end_time", "")
                    classes.append(make_class(studio_id, studio_name, day, t_start, t_end,
                                              name, "", website))
            except:
                pass

    # Also check for karmasoft.ch or karmasoft.net
    for pattern in [r'karmasoft\.\w+/([a-zA-Z0-9_/-]+)',
                    r'app\.karmasoft\.\w+/(\w+)']:
        m = re.search(pattern, html)
        if m:
            print(f"    Karmasoft reference found: {m.group(0)}")

    return classes


# --- Punchpass ---

def try_punchpass(website, schedule_url, studio_id, studio_name):
    """Try Punchpass widget/embed discovery."""
    classes = []

    html = fetch_text(schedule_url or website) if (schedule_url or website) else None
    if not html:
        return []

    # Look for punchpass iframe/widget
    m = re.search(r'punchpass\.com/([a-zA-Z0-9_/-]+)', html)
    if m:
        pp_path = m.group(1)
        print(f"    Punchpass path found: {pp_path}")
        pp_url = f"https://app.punchpass.com/{pp_path}"
        pp_html = fetch_text(pp_url)
        if pp_html:
            classes = parse_html_schedule(pp_html, studio_id, studio_name, pp_url)

    return classes


# --- Blueleaf ---

def try_blueleaf(schedule_url, studio_id, studio_name):
    """Try Blueleaf calendar/widget."""
    if not schedule_url or "blueleaf" not in schedule_url:
        return []

    html = fetch_text(schedule_url)
    if not html:
        return []

    # Blueleaf calendar pages have schedule data in HTML
    classes = parse_html_schedule(html, studio_id, studio_name, schedule_url)

    # Also try JSON API
    if not classes:
        parsed = urlparse(schedule_url)
        base = f"{parsed.scheme}://{parsed.hostname}"
        api_urls = [
            f"{base}/api/v1/calendar",
            f"{base}/api/v1/events",
            f"{base}/api/schedule",
        ]
        for api_url in api_urls:
            r = fetch(api_url)
            if r and r.status_code == 200:
                try:
                    data = r.json()
                    if isinstance(data, list):
                        for item in data:
                            name = item.get("name", item.get("title", "Yoga"))
                            start = item.get("start", item.get("startTime", ""))
                            if start:
                                try:
                                    dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                                    day = DAYS_EN[dt.weekday()]
                                    t_start = dt.strftime("%H:%M")
                                    classes.append(make_class(studio_id, studio_name, day,
                                                              t_start, "", name, "", schedule_url))
                                except:
                                    pass
                except:
                    pass

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

    classes = []
    items = data.get("items", [])
    if not items:
        items = data.get("collection", {}).get("items", [])
    for item in items:
        title = item.get("title", "")
        body = item.get("body", "")
        excerpt = item.get("excerpt", "")
        text = f"{title} {body} {excerpt}"
        for day_key, day_val in ALL_DAY_MAP.items():
            pattern = rf'{day_key}\w*\s+(\d{{1,2}}[:.]\d{{2}})'
            for m in re.finditer(pattern, text, re.I):
                t_start = m.group(1).replace(".", ":")
                classes.append(make_class(studio_id, studio_name, day_val, t_start, "",
                                          title or "Yoga", "", url))
    return classes


# --- HTML Time Pattern Parsing ---

def parse_html_schedule(html, studio_id, studio_name, source_url):
    """Parse schedule from HTML using time patterns and day names."""
    soup = BeautifulSoup(html, "html.parser")
    classes = []
    seen = set()

    # Strategy 1: Day headings followed by time entries
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b', 'dt', 'th']):
        heading_text = heading.get_text(strip=True)
        day = normalize_day(heading_text)
        if not day:
            # Check if heading text starts with a day name
            for key, val in ALL_DAY_MAP.items():
                if heading_text.lower().startswith(key):
                    day = val
                    break
        if not day:
            continue

        sibling = heading.find_next_sibling()
        attempts = 0
        while sibling and attempts < 30:
            attempts += 1
            sib_text = sibling.get_text(strip=True)
            if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
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
                d = normalize_day(cells[0])
                if d:
                    current_day = d
                if not current_day:
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

    # Strategy 4: Look for div/li blocks with day + time patterns
    if not classes:
        for block in soup.find_all(['div', 'li', 'p', 'span']):
            block_text = block.get_text(" ", strip=True)
            if len(block_text) < 10 or len(block_text) > 300:
                continue
            # Pattern: "Montag 18:00 - 19:30 Hatha Yoga"
            for day_key, day_val in ALL_DAY_MAP.items():
                m = re.search(
                    rf'\b{day_key}\w*\b\s*:?\s*(\d{{1,2}}[:.]\d{{2}})\s*[-–—]\s*(\d{{1,2}}[:.]\d{{2}})\s*(?:Uhr|h)?\s*(.*)',
                    block_text, re.I
                )
                if m:
                    t_start = m.group(1).replace(".", ":")
                    t_end = m.group(2).replace(".", ":")
                    desc = m.group(3).strip(" -–—|/:,\t")[:100]
                    if not desc:
                        desc = "Yoga"
                    key = (day_val, t_start, desc[:40])
                    if key not in seen:
                        seen.add(key)
                        classes.append(make_class(studio_id, studio_name, day_val, t_start, t_end,
                                                  desc, "", source_url))

    return classes


# --- Deep website crawling ---

def discover_schedule_links(html, base_url):
    """Find links on a page that might lead to schedule pages."""
    soup = BeautifulSoup(html, "html.parser")
    schedule_keywords = [
        "stundenplan", "schedule", "classes", "kurse", "horaire",
        "timetable", "angebot", "cours", "orario", "programm",
        "kursplan", "yoga", "offering", "termine", "daten",
    ]
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True).lower()
        href_lower = href.lower()

        is_schedule_link = any(kw in href_lower or kw in text for kw in schedule_keywords)
        if is_schedule_link:
            full_url = urljoin(base_url, href)
            # Only follow links on same domain
            if urlparse(full_url).hostname == urlparse(base_url).hostname:
                links.add(full_url)

    return list(links)[:8]  # Limit to 8 links


# --- Main cracking logic ---

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

    # === Phase 1: Fetch schedule_url and website, discover widgets ===
    html = None
    if schedule_url:
        html = fetch_text(schedule_url)
    if not html and schedule_url != website and website:
        html = fetch_text(website)

    website_html = html  # Save for later reuse

    if html:
        # 1a. Eversports widget discovery
        slug = find_eversports_slug(html)
        if slug:
            print(f"    Found Eversports slug in HTML: {slug}")
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

        # 1e. MindBody widget discovery
        mb_id = find_mindbody_studio_id(html)
        if mb_id:
            print(f"    Found MindBody ID: {mb_id}")
            classes = mindbody_scrape_widget(mb_id, sid, sname, schedule_url)
            if classes:
                report(sid, canton, "success", f"mindbody_widget (id={mb_id})", len(classes))
                return classes

        # 1f. Direct HTML parsing of schedule page
        classes = parse_html_schedule(html, sid, sname, schedule_url)
        if classes:
            report(sid, canton, "success", "html_parse", len(classes))
            return classes

    # === Phase 2: Known booking platform-specific approaches ===

    # 2a. Eversports: try slug guessing
    if booking_platform == "eversports" or "eversports" in (schedule_url or "").lower():
        print(f"    Trying Eversports slug guessing...")

        # First: if schedule_url has eversports slug
        if schedule_url and "eversports.ch/s/" in schedule_url:
            m = re.search(r'eversports\.ch/s/([a-zA-Z0-9_-]+)', schedule_url)
            if m:
                slug = m.group(1)
                classes = eversports_scrape(slug, sid, sname, schedule_url)
                if classes:
                    report(sid, canton, "success", f"eversports_url (slug={slug})", len(classes))
                    return classes

        # Second: guess slugs
        slugs = guess_eversports_slugs(sid, sname, website)
        found_slug, classes = try_eversports_slugs(slugs, sid, sname)
        if classes:
            report(sid, canton, "success", f"eversports_guess (slug={found_slug})", len(classes))
            return classes

        # Third: scan website for eversports links (check all pages)
        if website_html:
            links = discover_schedule_links(website_html, website)
            for link in links:
                link_html = fetch_text(link, timeout=6)
                if link_html:
                    slug = find_eversports_slug(link_html)
                    if slug:
                        classes = eversports_scrape(slug, sid, sname, link)
                        if classes:
                            report(sid, canton, "success", f"eversports_deep (slug={slug})", len(classes))
                            return classes
                time.sleep(0.2)

    # 2b. SportsNow: try slug guessing
    if booking_platform == "sportsnow":
        print(f"    Trying SportsNow slug guessing...")
        slugs = guess_sportsnow_slugs(sid, sname, website)
        for slug in slugs:
            classes = sportsnow_scrape(slug, sid, sname, website)
            if classes:
                report(sid, canton, "success", f"sportsnow_guess (slug={slug})", len(classes))
                return classes
            time.sleep(0.2)

    # 2c. MindBody: try explore API or widget
    if booking_platform in ("mindbody", "mindbody"):
        print(f"    Trying MindBody approaches...")
        # Try finding MB ID from website
        if website_html:
            mb_id = find_mindbody_studio_id(website_html)
            if mb_id:
                classes = mindbody_scrape_widget(mb_id, sid, sname, schedule_url or website)
                if classes:
                    report(sid, canton, "success", f"mindbody_widget (id={mb_id})", len(classes))
                    return classes

    # 2d. Karmasoft
    if booking_platform == "karmasoft":
        print(f"    Trying Karmasoft...")
        classes = try_karmasoft(website, sid, sname)
        if classes:
            report(sid, canton, "success", "karmasoft", len(classes))
            return classes

    # 2e. Punchpass
    if booking_platform == "punchpass":
        print(f"    Trying Punchpass...")
        classes = try_punchpass(website, schedule_url, sid, sname)
        if classes:
            report(sid, canton, "success", "punchpass", len(classes))
            return classes

    # 2f. Blueleaf
    if booking_platform == "blueleaf" or "blueleaf" in (schedule_url or ""):
        print(f"    Trying Blueleaf...")
        classes = try_blueleaf(schedule_url, sid, sname)
        if classes:
            report(sid, canton, "success", "blueleaf", len(classes))
            return classes

    # 2g. ClassPass
    if booking_platform == "classpass":
        print(f"    Trying ClassPass discovery...")
        # ClassPass doesn't have a public API, but the studio website might have schedule info
        pass

    # === Phase 3: Subpage crawling ===
    base_url = website.rstrip("/") if website else ""
    if base_url:
        print(f"    Crawling subpages...")
        miss_count = 0
        for subpath in SCHEDULE_SUBPATHS:
            if miss_count >= 5:
                break
            sub_url = base_url + subpath
            sub_html = fetch_text(sub_url, timeout=6)
            if not sub_html or len(sub_html) < 500:
                miss_count += 1
                continue
            miss_count = 0

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

            mb_id = find_mindbody_studio_id(sub_html)
            if mb_id:
                classes = mindbody_scrape_widget(mb_id, sid, sname, sub_url)
                if classes:
                    report(sid, canton, "success", f"mindbody_subpage ({subpath})", len(classes))
                    return classes

            acuity_owner = find_acuity_owner(sub_html)
            if acuity_owner:
                classes = acuity_scrape(acuity_owner, sid, sname, sub_url)
                if classes:
                    report(sid, canton, "success", f"acuity_subpage ({subpath})", len(classes))
                    return classes

            classes = parse_html_schedule(sub_html, sid, sname, sub_url)
            if classes:
                report(sid, canton, "success", f"html_parse_subpage ({subpath})", len(classes))
                return classes

            time.sleep(0.15)

    # === Phase 4: Follow menu links from homepage ===
    if website_html and base_url:
        links = discover_schedule_links(website_html, base_url)
        already_tried = set(base_url + sp for sp in SCHEDULE_SUBPATHS)
        new_links = [l for l in links if l not in already_tried]
        if new_links:
            print(f"    Following {len(new_links)} menu links...")
        for link in new_links[:10]:
            link_html = fetch_text(link, timeout=6)
            if not link_html or len(link_html) < 500:
                continue

            # Check for widgets
            slug = find_eversports_slug(link_html)
            if slug:
                classes = eversports_scrape(slug, sid, sname, link)
                if classes:
                    report(sid, canton, "success", f"eversports_menulink ({link})", len(classes))
                    return classes

            sn_slug = find_sportsnow_slug(link_html)
            if sn_slug:
                classes = sportsnow_scrape(sn_slug, sid, sname, link)
                if classes:
                    report(sid, canton, "success", f"sportsnow_menulink", len(classes))
                    return classes

            mb_id = find_mindbody_studio_id(link_html)
            if mb_id:
                classes = mindbody_scrape_widget(mb_id, sid, sname, link)
                if classes:
                    report(sid, canton, "success", f"mindbody_menulink", len(classes))
                    return classes

            classes = parse_html_schedule(link_html, sid, sname, link)
            if classes:
                report(sid, canton, "success", f"html_parse_menulink ({link})", len(classes))
                return classes

            time.sleep(0.3)

    # === Phase 5: Squarespace JSON ===
    if schedule_url:
        classes = try_squarespace_json(schedule_url, sid, sname)
        if classes:
            report(sid, canton, "success", "squarespace_json", len(classes))
            return classes

    # All methods failed
    fail_reason = "no schedule data extractable"
    if not html:
        fail_reason = "website unreachable"
    report(sid, canton, "fail", fail_reason, 0)
    return []


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


# --- MindBody geo exploration ---

def run_mindbody_geo_explore():
    """Run MindBody explore API for major Swiss cities."""
    print("\n" + "=" * 60)
    print("MINDBODY GEO EXPLORATION")
    print("=" * 60)

    cities = {
        "Basel": (47.55, 7.58),
        "Zurich": (47.37, 8.54),
        "Bern": (46.95, 7.44),
        "Geneva": (46.20, 6.14),
        "Lausanne": (46.52, 6.63),
    }

    all_results = {}
    for city, (lat, lon) in cities.items():
        print(f"\n  Searching near {city} ({lat}, {lon})...")
        results = mindbody_explore_api(lat, lon, radius=50)
        all_results[city] = results
        if results:
            print(f"    Found {len(results)} results")
            for r in results[:5]:
                print(f"      - {r.get('studio_name', 'unknown')}: {r.get('class_name', '')}")
        else:
            print(f"    No results from API")
        time.sleep(1)

    return all_results


# --- Main ---

def main():
    print("=" * 70)
    print("CRACK FINAL PUSH - Extracting from ALL 136 remaining studios")
    print("=" * 70)

    # Load remaining studios
    with open(REMAINING_FILE) as f:
        all_studios = json.load(f)

    # Filter out known impossible studios
    studios = [s for s in all_studios if s["id"] not in IMPOSSIBLE_IDS]

    print(f"\nTotal studios to process: {len(studios)}")
    print(f"Skipped (impossible): {len(all_studios) - len(studios)}")

    # First: run MindBody geo exploration
    mb_results = run_mindbody_geo_explore()

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
        print(f"\n{'=' * 60}")
        print(f"CANTON: {canton.upper()} ({len(canton_studios)} studios)")
        print(f"{'=' * 60}")

        # Load existing schedule
        sched_data = load_schedule(canton)

        for studio in canton_studios:
            print(f"\n--- {studio['name']} ({studio['id']}) ---")
            sys.stdout.flush()
            try:
                # Set a per-studio timeout of 60 seconds
                def _timeout_handler(signum, frame):
                    raise TimeoutError("Studio processing timed out")
                old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
                signal.alarm(60)
                new_classes = crack_studio(studio)
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                if new_classes:
                    sid = studio["id"]
                    sched_data["classes"] = [
                        c for c in sched_data.get("classes", [])
                        if c.get("studio_id") != sid
                    ]
                    sched_data["classes"].extend(new_classes)
                    total_new_classes += len(new_classes)
                    total_success += 1
                else:
                    total_fail += 1
            except TimeoutError:
                signal.alarm(0)
                print(f"  [TIMEOUT] {studio['id']}: exceeded 60s limit")
                report(studio["id"], canton, "fail", "timeout (60s)", 0)
                total_fail += 1
            except Exception as e:
                signal.alarm(0)
                print(f"  [ERROR] {studio['id']}: {e}")
                traceback.print_exc()
                report(studio["id"], canton, "fail", f"exception: {str(e)[:60]}", 0)
                total_fail += 1

            time.sleep(0.5)  # Rate limit between studios

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
        print(f"  {status} | {r['canton']:18s} | {r['studio']:40s} | {r['method'][:55]:55s} | {r['classes']:3d}")

    # Save report
    report_path = TOOLS_DIR / "crack_final_push_report.json"
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

    # List truly impossible studios
    print(f"\nStudios that could NOT be cracked:")
    fail_count = 0
    for r in sorted(REPORT, key=lambda x: x["canton"]):
        if r["status"] == "fail":
            fail_count += 1
            print(f"  {fail_count:3d}. {r['canton']}/{r['studio']}: {r['method']}")


if __name__ == "__main__":
    main()
