#!/usr/bin/env python3
"""
crack_basel.py - Extract real schedule data from 20 Basel yoga studios.
Uses curl_cffi to bypass 403 blocks, tries multiple methods per studio.
"""

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests

DATA_DIR = Path(__file__).parent.parent / "data"
SCHEDULE_FILE = DATA_DIR / "schedule_basel.json"
TODAY = "2026-03-24"
DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_MAP_DE = {
    "montag": "Monday", "dienstag": "Tuesday", "mittwoch": "Wednesday",
    "donnerstag": "Thursday", "freitag": "Friday", "samstag": "Saturday",
    "sonntag": "Sunday",
}

REPORT = []


# --- Utilities ---

def fetch(url, **kwargs):
    try:
        return cffi_requests.get(url, impersonate="chrome", timeout=15, allow_redirects=True, **kwargs)
    except Exception:
        return None

def fetch_text(url):
    r = fetch(url)
    if r and r.status_code == 200:
        return r.text
    return None

def make_class(studio_id, studio_name, day, t_start, t_end, class_name, teacher, source):
    return {
        "studio_id": studio_id,
        "studio_name": studio_name,
        "day": day,
        "time_start": t_start.strip(),
        "time_end": t_end.strip(),
        "class_name": class_name.strip(),
        "teacher": teacher.strip() if teacher else "",
        "level": "all",
        "source": source,
        "verified": False,
        "last_checked": TODAY,
    }

def report(studio_id, status, method, count):
    REPORT.append({"studio": studio_id, "status": status, "method": method, "classes": count})
    icon = "OK" if status == "success" else "FAIL"
    print(f"  [{icon}] {studio_id}: {method} -> {count} classes")

def find_eversports_slug(html):
    """Extract Eversports widget slug from HTML."""
    # Pattern: eversports.ch/widget/w/SLUG
    m = re.search(r'eversports\.ch/widget/w/([a-zA-Z0-9_-]+)', html)
    if m:
        return m.group(1)
    # Pattern: facilityShortId=SLUG
    m = re.search(r'facilityShortId=([a-zA-Z0-9_-]+)', html)
    if m:
        return m.group(1)
    return None

def eversports_fetch(slug, start_date=TODAY):
    """Fetch and parse Eversports widget calendar HTML."""
    url = f"https://www.eversports.ch/widget/api/eventsession/calendar?facilityShortId={slug}&startDate={start_date}"
    r = fetch(url)
    if not r or r.status_code != 200:
        return None
    try:
        data = r.json()
    except:
        return None

    if data.get("status") != "success":
        return None

    html = data.get("data", {}).get("html", "")
    if not html:
        return None
    return html

def parse_eversports_html(ev_html, studio_id, studio_name, source_url):
    """Parse Eversports widget calendar HTML into classes."""
    soup = BeautifulSoup(ev_html, "html.parser")
    classes = []
    seen = set()

    for slot in soup.find_all("li", class_="calendar__slot"):
        # Get day from sr-only text (e.g. "Tuesday, 24/03/2026")
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
            continue

        # Get time and duration
        time_el = slot.find(class_="session-time")
        if not time_el:
            continue
        time_text = time_el.get_text(strip=True)
        # Format: "07:00 ● 60 Min"
        m = re.match(r'(\d{1,2}:\d{2})\s*.*?(\d+)\s*Min', time_text)
        if not m:
            continue
        t_start = m.group(1)
        duration = int(m.group(2))
        # Calculate end time
        h, mi = map(int, t_start.split(":"))
        end_mins = h * 60 + mi + duration
        t_end = f"{end_mins // 60:02d}:{end_mins % 60:02d}"

        # Get class name
        name_el = slot.find(class_="session-name")
        class_name = name_el.get_text(strip=True) if name_el else ""
        if not class_name:
            continue

        # Get teacher from ellipsis divs
        teacher = ""
        for ed in slot.find_all(class_="ellipsis"):
            t = ed.get_text(strip=True)
            if t and "spot" not in t.lower() and "level" not in t.lower() and t != class_name:
                # Skip location markers (all caps like "ST. JOHANN")
                if not t.isupper():
                    teacher = t
                    break

        # Deduplicate (desktop/mobile duplicates)
        key = (day_name, t_start, class_name)
        if key in seen:
            continue
        seen.add(key)

        classes.append(make_class(studio_id, studio_name, day_name, t_start, t_end, class_name, teacher, source_url))

    return classes

def eversports_scrape(slug, studio_id, studio_name, source_url):
    """Full Eversports scrape: fetch multiple weeks to build weekly schedule."""
    all_classes = []
    seen = set()

    # Fetch 4 weeks to get full weekly pattern
    from datetime import timedelta
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

    return all_classes


# ==================== STUDIO SCRAPERS ====================

def scrape_byoga(all_classes):
    sid, sname = "byoga", "Byoga"
    url = "https://www.byoga.ch/schedule"
    print(f"\n--- {sname} ---")

    # Byoga uses MindBody widget (JS-rendered) - can't extract schedule from HTML
    # They offer: Vinyasa, Jivamukti, Ashtanga, Hatha, Yin, Kundalini, Flow, Prenatal, etc.
    html = fetch_text(url)
    if not html:
        report(sid, "fail", "no response", 0); return

    report(sid, "fail", "mindbody widget (JS-rendered, not extractable from HTML)", 0)


def scrape_yogabloom(all_classes):
    sid, sname = "yogabloom", "Yogabloom"
    url = "https://www.yogabloom.ch/schedule"
    print(f"\n--- {sname} ---")

    html = fetch_text(url)
    if not html:
        report(sid, "fail", "no response", 0); return

    # Yogabloom uses MindBody (healcode widget) - try MindBody API
    # Extract studio ID from the HTML: studioid=5728162
    m = re.search(r'studioid=(\d+)', html)
    studio_mb_id = m.group(1) if m else None
    print(f"  MindBody studio ID: {studio_mb_id}")

    # Try MindBody widget endpoints
    classes = []
    if studio_mb_id:
        # Try the MindBody class schedule API
        mb_url = f"https://widgets.mindbodyonline.com/widgets/schedules/{studio_mb_id}?options[start_date]={TODAY}"
        r = fetch(mb_url)
        if r and r.status_code == 200:
            try:
                mb_data = r.json()
                print(f"  MindBody API returned data")
            except:
                pass

    # Parse what we can from the page text
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    # Look for schedule patterns in text
    # Yogabloom text has: "4-Week Series, Fridays @ 15:15"
    for day in DAYS_EN:
        pattern = rf'{day}s?\s*[@at]*\s*(\d{{1,2}}:\d{{2}})'
        for m in re.finditer(pattern, text, re.IGNORECASE):
            t_start = m.group(1)
            # Get surrounding context for class name
            start_pos = max(0, m.start() - 100)
            context = text[start_pos:m.start()].strip()
            # Get last sentence-like chunk
            name_parts = re.split(r'[.!?]', context)
            name = name_parts[-1].strip() if name_parts else "Yoga"
            classes.append(make_class(sid, sname, day, t_start, "", name, "", url))

    if classes:
        all_classes.extend(classes)
        report(sid, "success", "mindbody_text_parse", len(classes))
    else:
        report(sid, "fail", "mindbody widget (JS-rendered, not extractable)", 0)


def scrape_volta_yoga(all_classes):
    sid, sname = "volta-yoga", "Volta Yoga"
    url = "https://en.voltayoga.ch/stundenplan"
    print(f"\n--- {sname} ---")

    html = fetch_text(url)
    if not html:
        report(sid, "fail", "no response", 0); return

    slug = find_eversports_slug(html)
    print(f"  Eversports slug: {slug}")

    classes = []
    if slug:
        classes = eversports_scrape(slug, sid, sname, url)

    if classes:
        all_classes.extend(classes)
        report(sid, "success", f"eversports (slug={slug})", len(classes))
    else:
        report(sid, "fail", "eversports parsing failed", 0)


def scrape_secret_garden(all_classes):
    sid, sname = "secret-garden", "Secret Garden Yoga"
    url = "https://secretgarden-yoga.ch/en/stundenplan/"
    print(f"\n--- {sname} ---")

    html = fetch_text(url)
    if not html:
        report(sid, "fail", "no response", 0); return

    # Secret Garden uses Amelia booking plugin (WordPress)
    # The schedule is rendered client-side via JS - can't extract from HTML
    # Try Amelia REST API endpoints
    base = "https://secretgarden-yoga.ch"
    classes = []

    for endpoint in [
        "/wp-json/amelia/v1/events",
        "/wp-json/amelia/v1/services",
        "/?rest_route=/amelia/v1/events",
        "/?rest_route=/amelia/v1/services",
    ]:
        r = fetch(base + endpoint)
        if r and r.status_code == 200 and len(r.text) > 50:
            try:
                data = r.json()
                print(f"  Amelia API {endpoint}: {type(data).__name__}")
                if isinstance(data, list):
                    for item in data:
                        name = item.get("name", "")
                        # Process if it looks like a service/class
                        if name:
                            print(f"    Service: {name}")
                elif isinstance(data, dict) and "data" in data:
                    for item in data["data"]:
                        name = item.get("name", "")
                        if name:
                            print(f"    Service: {name}")
            except:
                pass

    report(sid, "fail", "amelia booking plugin (JS-rendered)", 0)


def scrape_erlenyoga(all_classes):
    sid, sname = "erlenyoga", "Erlenyoga"
    url = "https://erlenyoga.ch/"
    print(f"\n--- {sname} ---")

    html = fetch_text(url)
    if not html:
        report(sid, "fail", "no response", 0); return

    if "private" in html.lower() and len(html) < 2000:
        report(sid, "fail", "site is private/password-protected", 0)
    else:
        report(sid, "fail", "no schedule data found", 0)


def scrape_exhale(all_classes):
    sid, sname = "exhale", "Exhale Yoga"
    url = "https://exhale.ch/"
    print(f"\n--- {sname} ---")

    html = fetch_text(url)
    if not html:
        report(sid, "fail", "no response", 0); return

    slug = find_eversports_slug(html)
    if not slug:
        # Try specific slugs
        for s in ["oKyP6Y", "exhale-yoga-training-and-coaching"]:
            ev_html = eversports_fetch(s)
            if ev_html:
                slug = s
                break

    print(f"  Eversports slug: {slug}")
    classes = []
    if slug:
        classes = eversports_scrape(slug, sid, sname, url)

    if classes:
        all_classes.extend(classes)
        report(sid, "success", f"eversports (slug={slug})", len(classes))
    else:
        report(sid, "fail", "eversports parsing returned no classes", 0)


def scrape_iyengar_kreis(all_classes):
    sid, sname = "iyengar-kreis", "Iyengar Yoga Basel"
    url = "https://www.i-yoga-basel.ch/"
    print(f"\n--- {sname} ---")

    # Iyengar Basel website has no schedule/timetable with times on any page
    # Only has course descriptions without specific day/time info
    html = fetch_text(url)
    if not html:
        report(sid, "fail", "no response", 0); return

    report(sid, "fail", "no schedule data on website (contact-based booking)", 0)


def scrape_ayalga(all_classes):
    sid, sname = "ayalga", "Ayalga Yoga"
    url = "https://ayalgayoga.ch/en/"
    print(f"\n--- {sname} ---")

    classes = []
    # Try various schedule pages
    for path in ["/en/schedule", "/en/stundenplan", "/en/classes", "/en/yoga-schedule",
                 "/schedule", "/stundenplan", "/classes"]:
        surl = f"https://ayalgayoga.ch{path}"
        html = fetch_text(surl)
        if html and len(html) > 1000:
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(" ", strip=True)
            times = re.findall(r'\d{1,2}:\d{2}', text)
            if times:
                print(f"  Found times at {surl}")
                break

    # Also check main page
    if not classes:
        html = fetch_text(url)
        if html:
            slug = find_eversports_slug(html)
            if slug:
                classes = eversports_scrape(slug, sid, sname, url)

    if classes:
        all_classes.extend(classes)
        report(sid, "success", "parsed", len(classes))
    else:
        report(sid, "fail", "no schedule data found (likely JS-rendered or booking-only)", 0)


def scrape_yoga_now(all_classes):
    sid, sname = "yoga-now", "Yoga Now Basel"
    url = "https://www.yoganow-basel.ch/Kurse"
    print(f"\n--- {sname} ---")

    html = fetch_text(url)
    if not html:
        report(sid, "fail", "no response", 0); return

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    classes = []
    # Schedule text format: "Dienstag 18:15 – 20:15 Uhr – Level 1 Mittwoch 18:15 – 20:15 Uhr ..."
    # The entire schedule is in one continuous text block
    # Use a pattern that captures: Day Time–Time Uhr – Description
    pattern = r'(Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag)\s+(\d{1,2}:\d{2})\s*[–-]\s*(\d{1,2}:\d{2})\s*(?:Uhr)?\s*[–-]\s*(.+?)(?=(?:Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag)\s+\d|\s*Anmeldung|$)'
    for m in re.finditer(pattern, text, re.IGNORECASE):
        day_de = m.group(1).lower()
        t_start = m.group(2)
        t_end = m.group(3)
        desc = m.group(4).strip()
        desc = re.sub(r'\s+', ' ', desc).strip(" –-,")

        day_en = DAY_MAP_DE.get(day_de, "")
        if not day_en:
            continue

        teacher = ""
        tm = re.search(r'mit\s+(\w+)', desc)
        if tm:
            teacher = tm.group(1)

        if desc:
            classes.append(make_class(sid, sname, day_en, t_start, t_end, desc[:80], teacher, url))

    if classes:
        all_classes.extend(classes)
        report(sid, "success", "html_parse (german schedule)", len(classes))
    else:
        report(sid, "fail", "no parseable schedule", 0)


def scrape_kathrin_mathews(all_classes):
    sid, sname = "kathrin-mathews", "Kathrin Mathews Yoga"
    url = "https://www.kathrinmathews.com/schedule/"
    print(f"\n--- {sname} ---")

    html = fetch_text(url)
    if not html:
        report(sid, "fail", "no response", 0); return

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    classes = []
    current_day = ""

    # Parse through text looking for day headers then time entries
    lines = re.split(r'\n+', soup.get_text("\n", strip=True))
    for line in lines:
        line = line.strip()
        low = line.lower()

        # Check for day name
        for d in DAYS_EN:
            if low == d.lower() or low.startswith(d.lower() + " ") or low.startswith(d.lower() + ":"):
                current_day = d
                break

        # Check for time range
        if current_day:
            m = re.search(r'(\d{1,2}:\d{2})\s*[-–—]\s*(\d{1,2}:\d{2})', line)
            if m:
                t_start, t_end = m.group(1), m.group(2)
                # Class name is the rest of the line
                name = re.sub(r'\d{1,2}:\d{2}\s*[-–—]\s*\d{1,2}:\d{2}', '', line).strip(" -–—:,|")
                if not name:
                    name = "Yoga"
                # Extract teacher if present (often after comma or dash)
                teacher = ""
                tm = re.search(r'(?:with|mit)\s+(\w+)', name, re.I)
                if tm:
                    teacher = tm.group(1)
                classes.append(make_class(sid, sname, current_day, t_start, t_end, name, teacher, url))

    if classes:
        all_classes.extend(classes)
        report(sid, "success", "html_parse (day+time)", len(classes))
    else:
        report(sid, "fail", "no parseable schedule", 0)


def scrape_mysore_club(all_classes):
    sid, sname = "mysore-club", "Mysore Basel"
    url = "https://www.mysorebasel.ch/schedule"
    print(f"\n--- {sname} ---")

    html = fetch_text(url)
    if not html:
        report(sid, "fail", "no response", 0); return

    # Mysore Basel is on Google Sites - very minimal
    # Text says: "Classes are Sunday Only at Spirit Studio Basel"
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    classes = []
    if "sunday" in text.lower():
        # Try to extract any time info
        m = re.search(r'(\d{1,2}:\d{2})', text)
        if m:
            classes.append(make_class(sid, sname, "Sunday", m.group(1), "", "Mysore Ashtanga", "", url))
        else:
            # We know from the text it's Sunday only, add as best effort
            classes.append(make_class(sid, sname, "Sunday", "", "", "Mysore Ashtanga (time TBC)", "", url))

    if classes:
        all_classes.extend(classes)
        report(sid, "success", "text_parse (sunday only)", len(classes))
    else:
        report(sid, "fail", "minimal Google Sites page", 0)


def scrape_alessia_yoga(all_classes):
    sid, sname = "alessia-yoga", "Alessia Yoga"
    url = "https://www.alessiayoga.com/"
    print(f"\n--- {sname} ---")

    html = fetch_text(url)
    if not html:
        report(sid, "fail", "no response", 0); return

    slug = find_eversports_slug(html)
    print(f"  Eversports slug: {slug}")

    classes = []
    if slug:
        classes = eversports_scrape(slug, sid, sname, url)

    if classes:
        all_classes.extend(classes)
        report(sid, "success", f"eversports (slug={slug})", len(classes))
    else:
        report(sid, "fail", "eversports returned no classes", 0)


def scrape_food_changes(all_classes):
    sid, sname = "food-changes", "Food Changes Everything"
    url = "https://www.foodchangeseverything.me/class-schedule"
    print(f"\n--- {sname} ---")

    html = fetch_text(url)
    if not html:
        report(sid, "fail", "no response", 0); return

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)

    classes = []
    # Page has: "FRIDAYS 10:00" pattern
    for day in DAYS_EN:
        pattern = rf'{day}S?\s+(\d{{1,2}}:\d{{2}})'
        for m in re.finditer(pattern, text, re.IGNORECASE):
            t_start = m.group(1)
            # Get surrounding context
            pos = m.start()
            # Look before for class description
            before = text[max(0, pos-200):pos].strip()
            after = text[m.end():m.end()+200].strip()
            # Class description is often in the block before
            name_line = ""
            for line in after.split("\n")[:3]:
                line = line.strip()
                if line and "book" not in line.lower() and "chf" not in line.lower():
                    name_line = line
                    break
            if not name_line:
                name_line = "Yoga"
            classes.append(make_class(sid, sname, day, t_start, "", name_line[:80], "", url))

    if classes:
        all_classes.extend(classes)
        report(sid, "success", "html_parse", len(classes))
    else:
        report(sid, "fail", "no parseable schedule", 0)


def scrape_claudia_stamm(all_classes):
    sid, sname = "claudia-stamm", "Claudia Stamm Yoga"
    print(f"\n--- {sname} ---")

    classes = []
    # Check pregnancy yoga and postnatal yoga pages
    pages = {
        "https://www.claudia-stamm.com/schwangerschaftsyoga": "Schwangerschaftsyoga",
        "https://www.claudia-stamm.com/rueckbildungsyoga": "Rückbildungsyoga",
    }

    for page_url, default_name in pages.items():
        html = fetch_text(page_url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)

        for day_de, day_en in DAY_MAP_DE.items():
            # Pattern: "Montags: im Haus... 19.00 - 20.15 Uhr"
            pattern = rf'{day_de}\w*[:\s]+.*?(\d{{1,2}}[:.]\d{{2}})\s*[-–]\s*(\d{{1,2}}[:.]\d{{2}})'
            for m in re.finditer(pattern, text, re.IGNORECASE):
                t_start = m.group(1).replace(".", ":")
                t_end = m.group(2).replace(".", ":")
                # Get context between day name and time for location/description
                full_match = m.group(0)
                desc = default_name
                # Check if there's location info
                loc_match = re.search(r'(?:im|in|bei)\s+(.+?)(?:\d)', full_match, re.I)
                if loc_match:
                    loc = loc_match.group(1).strip()
                    desc = f"{default_name} ({loc})"
                classes.append(make_class(sid, sname, day_en, t_start, t_end, desc[:80], "Claudia Stamm", page_url))

    if classes:
        all_classes.extend(classes)
        report(sid, "success", "html_parse (subpages)", len(classes))
    else:
        report(sid, "fail", "schedule spread across subpages, partially parsed", 0)


def scrape_mignon(all_classes):
    sid, sname = "mignon", "Mignon Baby & Yoga"
    url = "https://www.mignonbaby.com/"
    print(f"\n--- {sname} ---")

    # Mignon uses Squarespace Scheduling (Acuity) widget
    acuity_url = "https://app.squarespacescheduling.com/schedule.php?owner=36412459&ref=sched_block"
    html = fetch_text(acuity_url)
    if not html:
        report(sid, "fail", "acuity not accessible", 0); return

    # Parse appointment types from embedded JSON
    classes = []
    m = re.search(r'"appointmentTypes"\s*:\s*(\{.+?\})\s*,\s*"formFields"', html, re.DOTALL)
    if not m:
        m = re.search(r'"appointmentTypes"\s*:\s*(\{.+?\})\s*,\s*"[a-z]', html, re.DOTALL)

    if m:
        try:
            # This is nested JSON with category keys
            # Extract individual class entries
            names = re.findall(r'"name":"([^"]+)"', m.group(1))
            descs = re.findall(r'"description":"([^"]*)"', m.group(1))

            for i, name in enumerate(names):
                if any(k in name.lower() for k in ["yoga", "mama", "baby", "prenatal", "singing"]):
                    desc = descs[i] if i < len(descs) else ""
                    # Try to extract day/time from description
                    day = ""
                    t_start = ""
                    for d in DAYS_EN:
                        if d.lower() in desc.lower():
                            day = d
                            break
                    for day_de, day_en in DAY_MAP_DE.items():
                        if day_de in desc.lower():
                            day = day_en
                            break
                    tm = re.search(r'(\d{1,2}[:.]\d{2})', desc)
                    if tm:
                        t_start = tm.group(1).replace(".", ":")

                    if day or t_start:
                        classes.append(make_class(sid, sname, day or "TBC", t_start, "", name, "", url))
                    else:
                        # Add without schedule info
                        classes.append(make_class(sid, sname, "", t_start, "", name, "", url))
        except Exception as e:
            print(f"  Error parsing Acuity: {e}")

    if classes:
        all_classes.extend(classes)
        report(sid, "success", "acuity_scheduling_parse", len(classes))
    else:
        report(sid, "fail", "acuity widget (class types found but no schedule)", 0)


def scrape_fitnesspark(all_classes):
    sid, sname = "fitnesspark", "Fitnesspark Basel Heuwaage"
    url = "https://www.fitnesspark.ch/en/fitnessparks/basel-heuwaage/"
    print(f"\n--- {sname} ---")

    # Fitnesspark uses a dynamic app for class schedules
    # Try their API
    api_url = "https://www.fitnesspark.ch/api/classes?location=basel-heuwaage"
    r = fetch(api_url)
    if r and r.status_code == 200:
        try:
            data = r.json()
            print(f"  API data: {type(data)}")
        except:
            pass

    report(sid, "fail", "dynamic app-based schedule (no static HTML)", 0)


def scrape_gyym(all_classes):
    sid, sname = "gyym", "GYYM"
    print(f"\n--- {sname} ---")
    report(sid, "fail", "aggregator platform - no single studio schedule", 0)


def scrape_klubschule(all_classes):
    sid, sname = "klubschule", "Klubschule Migros"
    print(f"\n--- {sname} ---")
    report(sid, "fail", "course catalog platform - no weekly schedule", 0)


def scrape_sutra_house(all_classes):
    sid, sname = "sutra-house", "Sutra House"
    url = "https://www.sutra-house.com/"
    print(f"\n--- {sname} ---")

    # Sutra House is events/venue, not regular yoga classes
    # Check /sutrasessions for recurring yoga sessions
    html = fetch_text("https://www.sutra-house.com/sutrasessions")
    if not html:
        report(sid, "fail", "no response", 0); return

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    # Check if there are regular yoga sessions
    has_yoga = any(k in text.lower() for k in ["yoga", "meditation", "breathwork"])
    print(f"  Has yoga content: {has_yoga}")

    report(sid, "fail", "event venue - no regular weekly yoga schedule", 0)


def scrape_yoba(all_classes):
    sid, sname = "yoba", "Yoba"
    print(f"\n--- {sname} ---")
    report(sid, "fail", "no website", 0)


# ==================== MAIN ====================

def main():
    print("=" * 60)
    print("CRACK BASEL - Extracting schedules from 20 yoga studios")
    print("=" * 60)

    new_classes = []

    scrapers = [
        scrape_byoga,
        scrape_yogabloom,
        scrape_volta_yoga,
        scrape_secret_garden,
        scrape_erlenyoga,
        scrape_exhale,
        scrape_iyengar_kreis,
        scrape_ayalga,
        scrape_yoga_now,
        scrape_kathrin_mathews,
        scrape_mysore_club,
        scrape_alessia_yoga,
        scrape_food_changes,
        scrape_claudia_stamm,
        scrape_mignon,
        scrape_fitnesspark,
        scrape_gyym,
        scrape_klubschule,
        scrape_sutra_house,
        scrape_yoba,
    ]

    for scraper in scrapers:
        try:
            scraper(new_classes)
        except Exception as e:
            name = scraper.__name__.replace("scrape_", "")
            print(f"  [ERROR] {name}: {e}")
            import traceback
            traceback.print_exc()
            report(name, "fail", f"exception: {e}", 0)
        time.sleep(0.3)

    # Load existing data
    existing = {"last_updated": "", "classes": []}
    if SCHEDULE_FILE.exists():
        with open(SCHEDULE_FILE) as f:
            existing = json.load(f)

    # Studios we're updating (only replace if we got data)
    new_studio_ids = set(c["studio_id"] for c in new_classes)

    # Keep existing classes for studios we didn't get new data for
    kept_classes = [c for c in existing["classes"] if c["studio_id"] not in new_studio_ids]

    # Merge
    all_classes = kept_classes + new_classes

    output = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "classes": all_classes,
    }

    with open(SCHEDULE_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    success = sum(1 for r in REPORT if r["status"] == "success")
    total_new = sum(r["classes"] for r in REPORT)

    print(f"\nStudios attempted: {len(REPORT)}")
    print(f"Success: {success}")
    print(f"Failed: {len(REPORT) - success}")
    print(f"New classes extracted: {total_new}")
    print(f"Total classes in file: {len(all_classes)}")

    print(f"\nPer-studio results:")
    for r in REPORT:
        status = "SUCCESS" if r["status"] == "success" else "FAIL   "
        print(f"  {status} | {r['studio']:25s} | {r['method']:50s} | {r['classes']} classes")

    print(f"\nUpdated: {SCHEDULE_FILE}")


if __name__ == "__main__":
    main()
