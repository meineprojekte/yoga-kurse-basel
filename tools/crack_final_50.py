#!/usr/bin/env python3
"""
crack_final_50.py - Crack schedule data for the final 50 studios.
Uses curl_cffi with impersonate='chrome' for ALL requests.
"""

import json
import re
import signal
import sys
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
TODAY = datetime.now().strftime("%Y-%m-%d")

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
    "je": "Thursday", "ve": "Friday", "sa": "Saturday",
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

SCHEDULE_SUBPATHS = [
    "/stundenplan", "/schedule", "/classes", "/kurse", "/horaire",
    "/angebot", "/yoga", "/orario", "/class-schedule", "/timetable",
    "/kursplan", "/programm", "/programme", "/planning",
    "/wochenkurse", "/yoga-classes", "/yoga-kurse",
    "/cours", "/cours-horaire", "/yoga-schedule",
    "/open-classes", "/group-classes",
    "/en/schedule", "/en/classes",
    "/de/stundenplan", "/fr/horaire",
    "/kurse-preise", "/angebote", "/kursangebot",
    "/weekly-schedule", "/wochenplan",
]

# The 50 studios organized by canton
STUDIOS = [
    # BASEL-LANDSCHAFT (3)
    {"id": "yoga-werkstatt-liestal", "name": "Yoga Werkstatt Liestal", "canton": "basel-landschaft",
     "website": "https://yoga-werkstatt.ch/"},
    {"id": "yoga-shanti-oberwil", "name": "Yoga Shanti Oberwil", "canton": "basel-landschaft",
     "website": "https://www.yogashanti.ch/"},
    {"id": "hathayoga-arlesheim", "name": "Hatha Yoga Arlesheim", "canton": "basel-landschaft",
     "website": "https://www.hathayoga-basel.ch/"},

    # BASEL (11)
    {"id": "meyo-house", "name": "Meyo House", "canton": "basel",
     "website": "https://www.meyohouse.com/"},
    {"id": "erlenyoga", "name": "Erlenyoga", "canton": "basel",
     "website": "https://erlenyoga.ch/"},
    {"id": "iyengar-kreis", "name": "Iyengar Yoga Kreis", "canton": "basel",
     "website": "https://www.i-yoga-basel.ch/"},
    {"id": "mysore-club", "name": "Mysore Club Basel", "canton": "basel",
     "website": "https://www.mysorebasel.ch/"},
    {"id": "fitnesspark", "name": "Fitnesspark Basel Heuwaage", "canton": "basel",
     "website": "https://www.fitnesspark.ch/en/fitnessparks/basel-heuwaage/"},
    {"id": "gyym", "name": "GYYM", "canton": "basel",
     "website": "https://gyym.ch/en/"},
    {"id": "klubschule", "name": "Klubschule Migros", "canton": "basel",
     "website": "https://www.klubschule.ch/"},
    {"id": "sutra-house", "name": "Sutra House", "canton": "basel",
     "website": "https://www.sutra-house.com/"},
    {"id": "yoba", "name": "Yoba", "canton": "basel",
     "website": ""},

    # BERN (5)
    {"id": "hothaus-bern", "name": "Hothaus Yoga Bern", "canton": "bern",
     "website": "https://www.hothausyoga.com/"},
    {"id": "origin8-bern", "name": "Origin8 Bern", "canton": "bern",
     "website": "https://origin8.ch/", "booking_platform": "sportsnow"},
    {"id": "grey-rebel-bern", "name": "Grey Rebel Bern", "canton": "bern",
     "website": "https://www.grey-rebel.com/"},
    {"id": "yogakaleidoskop-bern", "name": "Inner Light Academy", "canton": "bern",
     "website": "https://www.innerlightacademy.ch/"},
    {"id": "energie-yoga-bern", "name": "Energie Yoga Bern", "canton": "bern",
     "website": "https://energieyoga.ch/"},

    # FRIBOURG (2)
    {"id": "sakinayoga-fribourg", "name": "Sakina Yoga Fribourg", "canton": "fribourg",
     "website": "https://www.sakinayoga.com/"},
    {"id": "yoga-nicole-fribourg", "name": "Yoga Nicole Fribourg", "canton": "fribourg",
     "website": "https://www.yoga-nicole.ch/"},

    # GENEVE (8)
    {"id": "yoga7-geneve", "name": "Yoga 7 Geneve", "canton": "geneve",
     "website": "https://yoga7.com/"},
    {"id": "fancy-yoga-geneve", "name": "Fancy Yoga Geneve", "canton": "geneve",
     "website": "https://www.fancy.yoga/"},
    {"id": "colife-geneve", "name": "Colife Geneve", "canton": "geneve",
     "website": "https://colife.ch/"},
    {"id": "sol-studio-geneve", "name": "Sol Studio Geneve", "canton": "geneve",
     "website": "https://solstudio.ch/"},
    {"id": "swiss-pilates-yoga-geneve", "name": "Swiss Pilates & Yoga Geneve", "canton": "geneve",
     "website": "https://swisspilatesandyoga.com/"},
    {"id": "yoga-shambala-carouge", "name": "Yoga Shambala Carouge", "canton": "geneve",
     "website": "https://www.yoga-shambala.ch/"},
    {"id": "ka-studio-geneve", "name": "KA Studio Geneve", "canton": "geneve",
     "website": "https://www.kastudio.ch/"},
    {"id": "yoga-sha-geneve", "name": "Yoga Sha Geneve", "canton": "geneve",
     "website": "https://yogasha.ch/"},

    # GRAUBUENDEN (2)
    {"id": "belude-yoga-chur", "name": "Belude Yoga Chur", "canton": "graubuenden",
     "website": "https://belude.ch/"},
    {"id": "yogaplaza-davos", "name": "Yoga Plaza Davos", "canton": "graubuenden",
     "website": "https://www.yogaplazadavos.ch/", "booking_platform": "eversports"},

    # JURA (1)
    {"id": "pilatesyogajura", "name": "Pilates Yoga Jura", "canton": "jura",
     "website": "https://www.pilatesyogajura.com/"},

    # LUZERN (3)
    {"id": "ashtanga-luzern", "name": "Ashtanga Yoga Luzern", "canton": "luzern",
     "website": "https://ashtanga-luzern.ch/"},
    {"id": "studio-fayo", "name": "Studio Fayo", "canton": "luzern",
     "website": "https://studiofayo.com/"},
    {"id": "pure-you-yoga-horw", "name": "Pure You Yoga Horw", "canton": "luzern",
     "website": "https://www.pureyouyoga.ch/"},

    # NEUCHATEL (2)
    {"id": "yoga-shashin-neuchatel", "name": "Yoga Shashin Neuchatel", "canton": "neuchatel",
     "website": "https://www.yogashashin.ch/"},
    {"id": "banyann-yoga", "name": "Banyann Yoga", "canton": "neuchatel",
     "website": "https://www.banyann.ch/"},

    # ST-GALLEN (1)
    {"id": "power-yoga-st-gallen", "name": "Power Yoga St. Gallen", "canton": "st-gallen",
     "website": "https://www.poweryogastgallen.com/"},

    # VAUD (9)
    {"id": "nueva-luna-yoga", "name": "Nueva Luna Yoga", "canton": "vaud",
     "website": "https://www.nuevalunayoga.ch/"},
    {"id": "the-yogarden", "name": "The Yogarden", "canton": "vaud",
     "website": "https://www.theyogarden.ch/"},
    {"id": "yoga-flame-lausanne", "name": "Yoga Flame Lausanne", "canton": "vaud",
     "website": "https://yogaflame.ch/"},
    {"id": "yogavaud", "name": "Yoga Vaud", "canton": "vaud",
     "website": "https://www.yogavaud.ch/"},
    {"id": "myoga-studio-lausanne", "name": "Myoga Studio Lausanne", "canton": "vaud",
     "website": "https://myogastudio.ch/"},
    {"id": "ashtanga-yoga-lausanne", "name": "Ashtanga Yoga Lausanne", "canton": "vaud",
     "website": "https://www.ashtanga-yoga-lausanne.com/"},
    {"id": "yoga-sadhana-lausanne", "name": "Yoga Sadhana Lausanne", "canton": "vaud",
     "website": "https://vivre-le-yoga.ch/"},
    {"id": "yogacenter-montreux", "name": "Yogacenter Montreux", "canton": "vaud",
     "website": "https://yogacenter.ch/"},
    {"id": "terre-du-yoga-vevey", "name": "Terre du Yoga Vevey", "canton": "vaud",
     "website": "https://www.caroledalmas.com/"},

    # ZURICH (5)
    {"id": "soul-city", "name": "Soul City Zurich", "canton": "zurich",
     "website": "https://soulcity-zurich.ch/", "booking_platform": "eversports"},
    {"id": "studio-y3", "name": "Studio Y3", "canton": "zurich",
     "website": "https://www.studioy3.ch/", "booking_platform": "classpass"},
    {"id": "templeshape", "name": "Templeshape", "canton": "zurich",
     "website": "https://templeshape.com/"},
    {"id": "project-peace", "name": "Project Peace", "canton": "zurich",
     "website": "https://projectpeace.ch/"},
    {"id": "flowfabrik-winterthur", "name": "Flowfabrik Winterthur", "canton": "zurich",
     "website": "https://www.flowfabrik.ch/"},
]


# --- Utilities ---

def fetch(url, timeout=12):
    """Fetch URL using curl_cffi with Chrome impersonation."""
    try:
        return cffi_requests.get(url, impersonate="chrome", timeout=timeout,
                                  allow_redirects=True)
    except Exception:
        return None


def fetch_text(url, timeout=12):
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
    # Direct match
    if text in ALL_DAY_MAP:
        return ALL_DAY_MAP[text]
    # Try with trailing 's'
    if text + "s" in ALL_DAY_MAP:
        return ALL_DAY_MAP[text + "s"]
    # Check startswith for longer strings
    for key, val in ALL_DAY_MAP.items():
        if len(key) >= 3 and text.startswith(key):
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
    patterns = [
        r'eversports\.ch/widget/w/([a-zA-Z0-9_-]+)',
        r'facilityShortId=([a-zA-Z0-9_-]+)',
        r'eversports\.ch/s/([a-zA-Z0-9_-]+)',
        r'data-eversports-widget-id=["\']([a-zA-Z0-9_-]+)',
        r'eversports\.com/widget/w/([a-zA-Z0-9_-]+)',
        r'eversports\.[a-z]+/(?:s|studio|widget/w)/([a-zA-Z0-9_-]+)',
    ]
    for pat in patterns:
        m = re.search(pat, html)
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
    slugs = set()
    slugs.add(studio_id)

    name_slug = slugify(studio_name)
    slugs.add(name_slug)

    # Without common suffixes
    for suffix in ["-yoga", "-studio", "-zurich", "-zuerich", "-bern", "-basel",
                   "-luzern", "-geneve", "-lausanne", "-winterthur", "-chur",
                   "-davos", "-fribourg", "-carouge", "-oberwil", "-liestal",
                   "-arlesheim", "-horw", "-montreux", "-vevey", "-st-gallen"]:
        if name_slug.endswith(suffix):
            slugs.add(name_slug[:-len(suffix)])

    # With common prefixes
    if not name_slug.startswith("yoga-"):
        slugs.add("yoga-" + name_slug)

    # Without hyphens
    slugs.add(name_slug.replace("-", ""))

    # From website domain
    if website:
        parsed = urlparse(website)
        domain = (parsed.hostname or "").replace("www.", "").split(".")[0]
        if domain:
            slugs.add(domain)

    return [s for s in slugs if s]


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

    # div-based
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


# --- MomoYoga ---

def find_momoyoga_slug(html):
    """Extract MomoYoga slug/ID from HTML."""
    m = re.search(r'momoyoga\.com/([a-zA-Z0-9_-]+)', html)
    if m and m.group(1) not in ("yoga", "en", "de", "fr", "it", "embed", "widget", "css", "js"):
        return m.group(1)
    return None


def momoyoga_scrape(slug, studio_id, studio_name):
    """Scrape MomoYoga schedule page."""
    momo_url = f"https://www.momoyoga.com/{slug}/schedule"
    html = fetch_text(momo_url)
    if not html:
        return []
    return parse_html_schedule(html, studio_id, studio_name, momo_url)


# --- bsport ---

def find_bsport_slug(html):
    """Extract bsport slug from HTML."""
    # Pattern: bfrnd.com/SLUG or bsport.io/SLUG
    patterns = [
        r'(?:bfrnd\.com|bsport\.io)/([a-zA-Z0-9_-]+)',
        r'backoffice\.bsport\.io/m/([a-zA-Z0-9_-]+)',
    ]
    for pat in patterns:
        m = re.search(pat, html)
        if m and m.group(1) not in ("en", "fr", "de", "it", "js", "css", "widget"):
            return m.group(1)
    return None


def bsport_scrape(slug, studio_id, studio_name, source_url):
    """Try to scrape bsport schedule."""
    # bsport has an API
    api_url = f"https://api.bsport.io/api/v1/offer/?company__slug={slug}&page=1&page_size=100"
    r = fetch(api_url, timeout=15)
    if not r or r.status_code != 200:
        # Try direct page
        page_url = f"https://{slug}.bfrnd.com/"
        html = fetch_text(page_url)
        if html:
            return parse_html_schedule(html, studio_id, studio_name, page_url)
        return []

    try:
        data = r.json()
        results = data.get("results", [])
        classes = []
        seen = set()
        for item in results:
            name = item.get("name", "")
            # Get schedule from offer's sessions
            offer_id = item.get("id")
            if offer_id:
                sess_url = f"https://api.bsport.io/api/v1/session/?offer={offer_id}&date_gte={TODAY}&page=1&page_size=50"
                sr = fetch(sess_url, timeout=10)
                if sr and sr.status_code == 200:
                    try:
                        sdata = sr.json()
                        for sess in sdata.get("results", []):
                            start_str = sess.get("date_start", "")
                            if start_str:
                                try:
                                    dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                                    day = DAYS_EN[dt.weekday()]
                                    t_start = dt.strftime("%H:%M")
                                    dur = sess.get("duration", 60)
                                    end_mins = dt.hour * 60 + dt.minute + dur
                                    t_end = f"{end_mins // 60:02d}:{end_mins % 60:02d}"
                                    teacher_data = sess.get("coach", {})
                                    teacher = ""
                                    if isinstance(teacher_data, dict):
                                        teacher = f"{teacher_data.get('first_name', '')} {teacher_data.get('last_name', '')}".strip()
                                    key = (day, t_start, name)
                                    if key not in seen:
                                        seen.add(key)
                                        classes.append(make_class(studio_id, studio_name, day,
                                                                  t_start, t_end, name, teacher, source_url))
                                except:
                                    pass
                    except:
                        pass
                time.sleep(0.2)
        return classes
    except:
        return []


# --- MindBody ---

def find_mindbody_studio_id(html):
    """Extract MindBody/Healcode studio ID from HTML."""
    patterns = [
        r'studioid=(\d+)',
        r'data-studioid=["\']?(\d+)',
        r'brandedweb\.mindbodyonline\.com/.*?studioid=(\d+)',
        r'widgets\.mindbodyonline\.com/.*?(\d{5,})',
    ]
    for pat in patterns:
        m = re.search(pat, html)
        if m:
            return m.group(1)
    return None


# --- Acuity ---

def find_acuity_owner(html):
    """Find Acuity Scheduling owner ID from HTML."""
    patterns = [
        r'squarespacescheduling\.com/schedule\.php\?owner=(\d+)',
        r'acuityscheduling\.com/schedule\.php\?owner=(\d+)',
    ]
    for pat in patterns:
        m = re.search(pat, html)
        if m:
            return m.group(1)
    return None


# --- Fitogram ---

def find_fitogram_slug(html):
    """Find Fitogram widget slug."""
    m = re.search(r'widget\.fitogram\.pro/([a-zA-Z0-9_-]+)', html)
    if m:
        return m.group(1)
    m = re.search(r'fitogram\.pro/([a-zA-Z0-9_-]+)', html)
    if m and m.group(1) not in ("en", "de", "fr", "widget", "js", "css"):
        return m.group(1)
    return None


def fitogram_scrape(slug, studio_id, studio_name, source_url):
    """Scrape Fitogram API."""
    api_url = f"https://api.fitogram.pro/v2/providers/{slug}/events?start={TODAY}"
    r = fetch(api_url)
    if not r or r.status_code != 200:
        return []
    try:
        data = r.json()
        events = data if isinstance(data, list) else data.get("data", [])
        classes = []
        seen = set()
        for ev in events:
            name = ev.get("name", ev.get("title", "Yoga"))
            start = ev.get("start", ev.get("startTime", ""))
            if start:
                try:
                    dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    day = DAYS_EN[dt.weekday()]
                    t_start = dt.strftime("%H:%M")
                    dur = ev.get("duration", 60)
                    end_mins = dt.hour * 60 + dt.minute + dur
                    t_end = f"{end_mins // 60:02d}:{end_mins % 60:02d}"
                    key = (day, t_start, name)
                    if key not in seen:
                        seen.add(key)
                        classes.append(make_class(studio_id, studio_name, day,
                                                  t_start, t_end, name, "", source_url))
                except:
                    pass
        return classes
    except:
        return []


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
            for key, val in ALL_DAY_MAP.items():
                if heading_text.lower().startswith(key) and len(key) >= 2:
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

    # Strategy 3: Inline text pattern
    if not classes:
        text = soup.get_text("\n", strip=True)
        day_pattern = "|".join(k for k in ALL_DAY_MAP.keys() if len(k) >= 3)
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

    # Strategy 4: div/li blocks with day + time
    if not classes:
        for block in soup.find_all(['div', 'li', 'p', 'span', 'dd']):
            block_text = block.get_text(" ", strip=True)
            if len(block_text) < 10 or len(block_text) > 300:
                continue
            for day_key, day_val in ALL_DAY_MAP.items():
                if len(day_key) < 3:
                    continue
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

    # Strategy 5: Just time+name on same line, day from context (nearby heading/strong)
    if not classes:
        text = soup.get_text("\n", strip=True)
        lines = text.split("\n")
        current_day = ""
        for line in lines:
            line = line.strip()
            d = normalize_day(line)
            if d:
                current_day = d
                continue
            if current_day:
                m = re.search(r'(\d{1,2}[:.]\d{2})\s*[-–—]\s*(\d{1,2}[:.]\d{2})', line)
                if m:
                    t_start = m.group(1).replace(".", ":")
                    t_end = m.group(2).replace(".", ":")
                    name = re.sub(r'\d{1,2}[:.]\d{2}\s*[-–—]\s*\d{1,2}[:.]\d{2}', '', line)
                    name = name.strip(" -–—|/:,\t\nUhr h")
                    if name and len(name) > 1:
                        key = (current_day, t_start, name[:40])
                        if key not in seen:
                            seen.add(key)
                            classes.append(make_class(studio_id, studio_name, current_day,
                                                      t_start, t_end, name, "", source_url))

    return classes


# --- Deep website crawling ---

def discover_schedule_links(html, base_url):
    """Find links on a page that might lead to schedule pages."""
    soup = BeautifulSoup(html, "html.parser")
    schedule_keywords = [
        "stundenplan", "schedule", "classes", "kurse", "horaire",
        "timetable", "angebot", "cours", "orario", "programm",
        "kursplan", "yoga", "offering", "termine", "daten",
        "planning", "emploi", "planning-cours",
    ]
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True).lower()
        href_lower = href.lower()

        is_schedule_link = any(kw in href_lower or kw in text for kw in schedule_keywords)
        if is_schedule_link:
            full_url = urljoin(base_url, href)
            if urlparse(full_url).hostname == urlparse(base_url).hostname:
                links.add(full_url)

    return list(links)[:10]


# --- Main cracking logic ---

def crack_studio(studio):
    """Try all methods to extract schedule from a studio. Returns list of classes."""
    sid = studio["id"]
    sname = studio["name"]
    canton = studio["canton"]
    website = studio.get("website", "")
    booking_platform = (studio.get("booking_platform", "") or "").lower()

    if not website:
        report(sid, canton, "fail", "no website", 0)
        return []

    classes = []

    # === Phase 1: Fetch homepage, discover widgets ===
    print(f"    Fetching homepage...")
    html = fetch_text(website)
    website_html = html

    if html:
        # 1a. Eversports widget discovery
        slug = find_eversports_slug(html)
        if slug:
            print(f"    Found Eversports slug in HTML: {slug}")
            classes = eversports_scrape(slug, sid, sname, website)
            if classes:
                report(sid, canton, "success", f"eversports (slug={slug})", len(classes))
                return classes

        # 1b. SportsNow widget discovery
        sn_slug = find_sportsnow_slug(html)
        if sn_slug:
            print(f"    Found SportsNow slug: {sn_slug}")
            classes = sportsnow_scrape(sn_slug, sid, sname, website)
            if classes:
                report(sid, canton, "success", f"sportsnow (slug={sn_slug})", len(classes))
                return classes

        # 1c. MomoYoga discovery
        momo_slug = find_momoyoga_slug(html)
        if momo_slug:
            print(f"    Found MomoYoga slug: {momo_slug}")
            classes = momoyoga_scrape(momo_slug, sid, sname)
            if classes:
                report(sid, canton, "success", f"momoyoga (slug={momo_slug})", len(classes))
                return classes

        # 1d. bsport discovery
        bs_slug = find_bsport_slug(html)
        if bs_slug:
            print(f"    Found bsport slug: {bs_slug}")
            classes = bsport_scrape(bs_slug, sid, sname, website)
            if classes:
                report(sid, canton, "success", f"bsport (slug={bs_slug})", len(classes))
                return classes

        # 1e. Fitogram discovery
        fg_slug = find_fitogram_slug(html)
        if fg_slug:
            print(f"    Found Fitogram slug: {fg_slug}")
            classes = fitogram_scrape(fg_slug, sid, sname, website)
            if classes:
                report(sid, canton, "success", f"fitogram (slug={fg_slug})", len(classes))
                return classes

        # 1f. Acuity Scheduling discovery
        acuity_owner = find_acuity_owner(html)
        if acuity_owner:
            print(f"    Found Acuity owner: {acuity_owner}")

        # 1g. MindBody widget discovery
        mb_id = find_mindbody_studio_id(html)
        if mb_id:
            print(f"    Found MindBody ID: {mb_id}")

        # 1h. Direct HTML parsing of homepage
        classes = parse_html_schedule(html, sid, sname, website)
        if classes:
            report(sid, canton, "success", "html_parse_homepage", len(classes))
            return classes

    # === Phase 2: Known booking platform-specific approaches ===

    # 2a. Eversports: try slug guessing
    if booking_platform == "eversports" or (html and "eversports" in html.lower()):
        print(f"    Trying Eversports slug guessing...")
        slugs = guess_eversports_slugs(sid, sname, website)
        # Add extra slug variations
        extra = []
        for s in list(slugs):
            extra.append(s.replace("-", ""))
            parts = s.split("-")
            if len(parts) > 1:
                extra.append(parts[0])
                extra.append("-".join(parts[:2]))
        slugs = list(set(slugs + extra))
        found_slug, classes = try_eversports_slugs(slugs, sid, sname)
        if classes:
            report(sid, canton, "success", f"eversports_guess (slug={found_slug})", len(classes))
            return classes

    # 2b. SportsNow: try slug guessing
    if booking_platform == "sportsnow" or (html and "sportsnow" in html.lower()):
        print(f"    Trying SportsNow slug guessing...")
        slugs = [sid, slugify(sname)]
        # Extra variations
        domain = urlparse(website).hostname or ""
        domain_slug = domain.replace("www.", "").split(".")[0]
        if domain_slug:
            slugs.append(domain_slug)
        # For origin8-bern, try: origin8, origin-8, origin8-bern
        extra = []
        for s in slugs:
            extra.append(s.replace("-", ""))
            parts = s.split("-")
            if len(parts) > 1:
                extra.append(parts[0])
                extra.append("-".join(parts[:2]))
        slugs = list(set(slugs + extra))
        for slug in slugs:
            classes = sportsnow_scrape(slug, sid, sname, website)
            if classes:
                report(sid, canton, "success", f"sportsnow_guess (slug={slug})", len(classes))
                return classes
            time.sleep(0.2)

    # === Phase 3: Subpage crawling ===
    base_url = website.rstrip("/")
    print(f"    Crawling subpages...")
    miss_count = 0
    for subpath in SCHEDULE_SUBPATHS:
        if miss_count >= 6:
            break
        sub_url = base_url + subpath
        sub_html = fetch_text(sub_url, timeout=8)
        if not sub_html or len(sub_html) < 300:
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

        momo_slug = find_momoyoga_slug(sub_html)
        if momo_slug:
            classes = momoyoga_scrape(momo_slug, sid, sname)
            if classes:
                report(sid, canton, "success", f"momoyoga_subpage ({subpath})", len(classes))
                return classes

        bs_slug = find_bsport_slug(sub_html)
        if bs_slug:
            classes = bsport_scrape(bs_slug, sid, sname, sub_url)
            if classes:
                report(sid, canton, "success", f"bsport_subpage ({subpath})", len(classes))
                return classes

        fg_slug = find_fitogram_slug(sub_html)
        if fg_slug:
            classes = fitogram_scrape(fg_slug, sid, sname, sub_url)
            if classes:
                report(sid, canton, "success", f"fitogram_subpage ({subpath})", len(classes))
                return classes

        mb_id = find_mindbody_studio_id(sub_html)
        if mb_id:
            print(f"    Found MindBody ID on {subpath}: {mb_id}")

        # HTML parsing
        classes = parse_html_schedule(sub_html, sid, sname, sub_url)
        if classes:
            report(sid, canton, "success", f"html_parse_subpage ({subpath})", len(classes))
            return classes

        time.sleep(0.15)

    # === Phase 4: Follow menu links from homepage ===
    if website_html:
        links = discover_schedule_links(website_html, base_url)
        already_tried = set(base_url + sp for sp in SCHEDULE_SUBPATHS)
        new_links = [l for l in links if l not in already_tried]
        if new_links:
            print(f"    Following {len(new_links)} menu links...")
        for link in new_links[:10]:
            link_html = fetch_text(link, timeout=8)
            if not link_html or len(link_html) < 300:
                continue

            # Check all widgets
            for finder, scraper, label in [
                (find_eversports_slug, lambda s: eversports_scrape(s, sid, sname, link), "eversports"),
                (find_sportsnow_slug, lambda s: sportsnow_scrape(s, sid, sname, link), "sportsnow"),
                (find_momoyoga_slug, lambda s: momoyoga_scrape(s, sid, sname), "momoyoga"),
                (find_bsport_slug, lambda s: bsport_scrape(s, sid, sname, link), "bsport"),
                (find_fitogram_slug, lambda s: fitogram_scrape(s, sid, sname, link), "fitogram"),
            ]:
                found = finder(link_html)
                if found:
                    classes = scraper(found)
                    if classes:
                        report(sid, canton, "success", f"{label}_menulink ({link})", len(classes))
                        return classes

            classes = parse_html_schedule(link_html, sid, sname, link)
            if classes:
                report(sid, canton, "success", f"html_parse_menulink ({link})", len(classes))
                return classes

            time.sleep(0.2)

    # === Phase 5: Squarespace JSON ===
    classes = try_squarespace_json(website, sid, sname)
    if classes:
        report(sid, canton, "success", "squarespace_json", len(classes))
        return classes

    # === Phase 6: Last resort - try all subpages for Squarespace JSON ===
    for subpath in ["/stundenplan", "/schedule", "/classes", "/kurse", "/horaire", "/cours"]:
        sub_url = base_url + subpath
        classes = try_squarespace_json(sub_url, sid, sname)
        if classes:
            report(sid, canton, "success", f"squarespace_json ({subpath})", len(classes))
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


# --- Main ---

def main():
    print("=" * 70)
    print(f"CRACK FINAL 50 - Extracting schedule data from 50 studios")
    print(f"Date: {TODAY}")
    print("=" * 70)

    total_new_classes = 0
    total_success = 0
    total_fail = 0

    # Group by canton
    by_canton = {}
    for s in STUDIOS:
        c = s["canton"]
        if c not in by_canton:
            by_canton[c] = []
        by_canton[c].append(s)

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
                def _timeout_handler(signum, frame):
                    raise TimeoutError("Studio processing timed out")
                old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
                signal.alarm(90)
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
                print(f"  [TIMEOUT] {studio['id']}: exceeded 90s limit")
                report(studio["id"], canton, "fail", "timeout (90s)", 0)
                total_fail += 1
            except Exception as e:
                signal.alarm(0)
                print(f"  [ERROR] {studio['id']}: {e}")
                traceback.print_exc()
                report(studio["id"], canton, "fail", f"exception: {str(e)[:60]}", 0)
                total_fail += 1

            time.sleep(0.5)

        # Save updated schedule
        sched_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        save_schedule(canton, sched_data)
        print(f"\n  Saved schedule_{canton}.json ({len(sched_data['classes'])} total classes)")

    # --- Final Summary ---
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    print(f"\nStudios attempted: {len(STUDIOS)}")
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
    report_path = TOOLS_DIR / "crack_final_50_report.json"
    with open(report_path, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_studios": len(STUDIOS),
            "success": total_success,
            "failed": total_fail,
            "new_classes": total_new_classes,
            "canton_stats": CANTON_STATS,
            "details": REPORT,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to: {report_path}")

    # List failures
    print(f"\nStudios that could NOT be cracked:")
    fail_count = 0
    for r in sorted(REPORT, key=lambda x: x["canton"]):
        if r["status"] == "fail":
            fail_count += 1
            print(f"  {fail_count:3d}. {r['canton']}/{r['studio']}: {r['method']}")


if __name__ == "__main__":
    main()
