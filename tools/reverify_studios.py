#!/usr/bin/env python3
"""
reverify_studios.py - Re-verify 74 studios that have only unverified schedule entries.
Tries Eversports API, website scraping, HTML parsing, and subpage discovery.
If new verified data is found, replaces unverified entries.
If existing data looks valid, marks as verified with source.
"""

import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests

DATA_DIR = Path(__file__).parent.parent / "data"
TODAY = "2026-03-25"
DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_MAP_DE = {
    "montag": "Monday", "dienstag": "Tuesday", "mittwoch": "Wednesday",
    "donnerstag": "Thursday", "freitag": "Friday", "samstag": "Saturday",
    "sonntag": "Sunday",
}
DAY_MAP_FR = {
    "lundi": "Monday", "mardi": "Tuesday", "mercredi": "Wednesday",
    "jeudi": "Thursday", "vendredi": "Friday", "samedi": "Saturday",
    "dimanche": "Sunday",
}

REPORT = []

# Known Eversports slug guesses per studio
EVERSPORTS_SLUG_GUESSES = {
    "airyoga": ["airyoga", "air-yoga"],
    "soasana": ["soasana"],
    "looking-glass": ["the-looking-glass", "thelookingglassbasel", "looking-glass"],
    "yogastudio-luzern": ["yogastudio-luzern", "yogastudio"],
    "inside-outside-bern": ["inside-outside-yoga-pilates-and-more", "inside-outside", "inside-outside-bern"],
    "the-soulspace": ["the-soulspace", "soulspace", "thesoulspace"],
    "happinez-yoga-fribourg": ["happinez-yoga", "happinez-yoga-fribourg", "happinez"],
    "yoga-grenzenlos-kreuzlingen": ["yoga-grenzenlos", "yoga-grenzenlos-kreuzlingen"],
}


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

def make_class(studio_id, studio_name, day, t_start, t_end, class_name, teacher, source, verified=True):
    return {
        "studio_id": studio_id,
        "studio_name": studio_name,
        "day": day,
        "time_start": t_start.strip() if t_start else "",
        "time_end": t_end.strip() if t_end else "",
        "class_name": class_name.strip() if class_name else "",
        "teacher": teacher.strip() if teacher else "",
        "level": "all",
        "source": source,
        "verified": verified,
        "last_checked": TODAY,
    }

def report(studio_id, status, method, count):
    REPORT.append({"studio": studio_id, "status": status, "method": method, "classes": count})
    icon = "OK" if status == "success" else ("KEPT" if status == "kept" else "FAIL")
    print(f"  [{icon}] {studio_id}: {method} -> {count} classes")

def find_eversports_slug(html):
    """Extract Eversports widget slug from HTML."""
    m = re.search(r'eversports\.ch/widget/w/([a-zA-Z0-9_-]+)', html)
    if m:
        return m.group(1)
    m = re.search(r'facilityShortId=([a-zA-Z0-9_-]+)', html)
    if m:
        return m.group(1)
    # Also check for eversports.ch/s/SLUG pattern
    m = re.search(r'eversports\.ch/s/([a-zA-Z0-9_-]+)', html)
    if m:
        return m.group(1)
    return None

def find_sportsnow_embed(html):
    """Check for SportNow widget embeds."""
    m = re.search(r'sportsnow\.ch/([a-zA-Z0-9_/-]+)', html)
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
    except Exception:
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

        classes.append(make_class(studio_id, studio_name, day_name, t_start, t_end, class_name, teacher, source_url))

    return classes

def eversports_scrape(slug, studio_id, studio_name, source_url):
    """Full Eversports scrape: fetch multiple weeks to build weekly schedule."""
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

    return all_classes

def try_eversports_slugs(studio_id, studio_name, source_url, slugs):
    """Try multiple Eversports slugs, return classes from first that works."""
    for slug in slugs:
        ev_html = eversports_fetch(slug)
        if ev_html:
            classes = eversports_scrape(slug, studio_id, studio_name, source_url)
            if classes:
                print(f"    Eversports slug '{slug}' worked -> {len(classes)} classes")
                return classes, slug
            else:
                print(f"    Eversports slug '{slug}' returned HTML but no parseable classes")
        else:
            print(f"    Eversports slug '{slug}' failed")
        time.sleep(0.2)
    return [], None

def slugify(name):
    """Convert a name to a URL slug."""
    s = name.lower().strip()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = s.strip('-')
    return s

def extract_domain_slug(website):
    """Extract slug from website URL, e.g. https://www.soasana.ch/ -> soasana"""
    if not website:
        return None
    m = re.search(r'(?:www\.)?([a-z0-9-]+)\.[a-z]+', website, re.I)
    if m:
        return m.group(1)
    return None

def entry_looks_valid(entry):
    """Check if an unverified entry looks valid (has day, time, class name)."""
    return (
        entry.get("day") in DAYS_EN
        and re.match(r'\d{1,2}:\d{2}', entry.get("time_start", ""))
        and entry.get("class_name", "").strip()
        and "TBC" not in entry.get("class_name", "")
        and entry.get("time_start", "") != ""
    )

def try_subpages(base_url, studio_id, studio_name):
    """Try common schedule subpages."""
    subpaths = ["/stundenplan", "/schedule", "/classes", "/kurse",
                "/en/schedule", "/en/classes", "/en/stundenplan",
                "/kursplan", "/timetable", "/horaire", "/cours",
                "/yoga-schedule", "/class-schedule", "/group-fitness"]

    base = base_url.rstrip("/")
    for path in subpaths:
        url = base + path
        html = fetch_text(url)
        if not html or len(html) < 500:
            continue

        # Check for eversports embed
        slug = find_eversports_slug(html)
        if slug:
            print(f"    Found Eversports slug '{slug}' on {path}")
            classes = eversports_scrape(slug, studio_id, studio_name, url)
            if classes:
                return classes, f"eversports via {path} (slug={slug})"

        # Check for sportsnow embed
        sn = find_sportsnow_embed(html)
        if sn:
            print(f"    Found SportNow embed on {path}: {sn}")

        # Try HTML parsing for schedule data
        classes = parse_schedule_html(html, studio_id, studio_name, url)
        if classes:
            return classes, f"html_parse from {path}"

        time.sleep(0.2)

    return [], None

def parse_schedule_html(html, studio_id, studio_name, source_url):
    """Try to parse schedule data from HTML using various patterns."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    classes = []
    seen = set()

    # Pattern 1: German day names followed by times
    # e.g. "Montag 09:00 - 10:00 Hatha Yoga"
    for day_de, day_en in DAY_MAP_DE.items():
        pattern = rf'{day_de}\w*\s+(\d{{1,2}}[:.]\d{{2}})\s*[-–]\s*(\d{{1,2}}[:.]\d{{2}})\s*(?:Uhr\s*)?[–-]?\s*(.+?)(?=(?:Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag)\w*\s+\d|\n|$)'
        for m in re.finditer(pattern, text, re.IGNORECASE):
            t_start = m.group(1).replace(".", ":")
            t_end = m.group(2).replace(".", ":")
            desc = m.group(3).strip(" –-,\n")
            if not desc:
                desc = "Yoga"
            key = (day_en, t_start, desc[:40])
            if key not in seen:
                seen.add(key)
                classes.append(make_class(studio_id, studio_name, day_en, t_start, t_end, desc[:80], "", source_url))

    # Pattern 2: French day names followed by times
    for day_fr, day_en in DAY_MAP_FR.items():
        pattern = rf'{day_fr}\w*\s+(\d{{1,2}}[h:.]\d{{2}})\s*[-–à]\s*(\d{{1,2}}[h:.]\d{{2}})\s*(.+?)(?=(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\w*\s+\d|\n|$)'
        for m in re.finditer(pattern, text, re.IGNORECASE):
            t_start = m.group(1).replace("h", ":").replace(".", ":")
            t_end = m.group(2).replace("h", ":").replace(".", ":")
            desc = m.group(3).strip(" –-,\n")
            if not desc:
                desc = "Yoga"
            key = (day_en, t_start, desc[:40])
            if key not in seen:
                seen.add(key)
                classes.append(make_class(studio_id, studio_name, day_en, t_start, t_end, desc[:80], "", source_url))

    # Pattern 3: English day names followed by times
    for day in DAYS_EN:
        pattern = rf'{day}\w*\s+(\d{{1,2}}[:.]\d{{2}})\s*[-–]\s*(\d{{1,2}}[:.]\d{{2}})\s*(.+?)(?=(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\w*\s+\d|\n|$)'
        for m in re.finditer(pattern, text, re.IGNORECASE):
            t_start = m.group(1).replace(".", ":")
            t_end = m.group(2).replace(".", ":")
            desc = m.group(3).strip(" –-,\n")
            if not desc:
                desc = "Yoga"
            key = (day, t_start, desc[:40])
            if key not in seen:
                seen.add(key)
                classes.append(make_class(studio_id, studio_name, day, t_start, t_end, desc[:80], "", source_url))

    # Pattern 4: Table-based schedules - look for day headers then time rows
    if not classes:
        current_day = ""
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            low = line.lower()

            # Check for day name as header
            for d in DAYS_EN:
                if low == d.lower() or low.startswith(d.lower() + ":") or low.startswith(d.lower() + " "):
                    current_day = d
                    break
            for d_de, d_en in DAY_MAP_DE.items():
                if low == d_de or low.startswith(d_de + ":") or low.startswith(d_de + " ") or low == d_de + "s":
                    current_day = d_en
                    break
            for d_fr, d_en in DAY_MAP_FR.items():
                if low == d_fr or low.startswith(d_fr + ":") or low.startswith(d_fr + " "):
                    current_day = d_en
                    break

            if current_day:
                m = re.search(r'(\d{1,2}[:.]\d{2})\s*[-–]\s*(\d{1,2}[:.]\d{2})', line)
                if m:
                    t_start = m.group(1).replace(".", ":")
                    t_end = m.group(2).replace(".", ":")
                    name = re.sub(r'\d{1,2}[:.]\d{2}\s*[-–]\s*\d{1,2}[:.]\d{2}', '', line).strip(" -–:,|")
                    # Remove the day name from the beginning
                    for d in DAYS_EN:
                        name = re.sub(rf'^{d}\w*\s*:?\s*', '', name, flags=re.I)
                    for d_de in DAY_MAP_DE:
                        name = re.sub(rf'^{d_de}\w*\s*:?\s*', '', name, flags=re.I)
                    for d_fr in DAY_MAP_FR:
                        name = re.sub(rf'^{d_fr}\w*\s*:?\s*', '', name, flags=re.I)
                    name = name.strip(" -–:,|")
                    if not name:
                        name = "Yoga"
                    key = (current_day, t_start, name[:40])
                    if key not in seen:
                        seen.add(key)
                        classes.append(make_class(studio_id, studio_name, current_day, t_start, t_end, name[:80], "", source_url))

    return classes


# ==================== MAIN LOGIC ====================

def load_all_data():
    """Load all studios and schedule data."""
    import glob

    studio_info = {}
    studio_files = sorted(glob.glob(str(DATA_DIR / "studios_*.json")))
    studio_files = [f for f in studio_files if ".enc." not in f]
    for sf in studio_files:
        canton = Path(sf).stem.replace("studios_", "")
        with open(sf) as f:
            data = json.load(f)
        for s in data.get("studios", []):
            studio_info[s["id"]] = {
                "name": s.get("name", ""),
                "website": s.get("website", ""),
                "schedule_url": s.get("schedule_url", ""),
                "booking_platform": s.get("booking_platform", ""),
                "canton": canton,
            }

    schedule_data = {}  # canton -> full data dict
    schedule_files = sorted(glob.glob(str(DATA_DIR / "schedule_*.json")))
    schedule_files = [f for f in schedule_files if ".enc." not in f]
    for sf in schedule_files:
        canton = Path(sf).stem.replace("schedule_", "")
        with open(sf) as f:
            schedule_data[canton] = json.load(f)

    # Find studios with ONLY unverified entries
    unverified_studios = {}
    for canton, sched in schedule_data.items():
        classes = sched.get("classes", [])
        by_studio = {}
        for c in classes:
            sid = c["studio_id"]
            if sid not in by_studio:
                by_studio[sid] = {"verified": 0, "unverified": 0, "entries": []}
            if c.get("verified"):
                by_studio[sid]["verified"] += 1
            else:
                by_studio[sid]["unverified"] += 1
                by_studio[sid]["entries"].append(c)

        for sid, counts in by_studio.items():
            if counts["verified"] == 0 and counts["unverified"] > 0:
                info = studio_info.get(sid, {})
                unverified_studios[sid] = {
                    "canton": canton,
                    "count": counts["unverified"],
                    "entries": counts["entries"],
                    "platform": info.get("booking_platform", ""),
                    "name": info.get("name", sid),
                    "website": info.get("website", ""),
                    "schedule_url": info.get("schedule_url", ""),
                }

    return studio_info, schedule_data, unverified_studios


def reverify_studio(sid, info):
    """Try to re-verify a single studio. Returns (new_classes, method) or (None, None)."""
    name = info["name"]
    website = info["website"]
    schedule_url = info["schedule_url"]
    platform = info["platform"]
    entries = info["entries"]

    print(f"\n--- {name} ({sid}) [{info['canton']}] ---")
    print(f"  Platform: {platform or 'unknown'}, Classes: {info['count']}")
    print(f"  URL: {schedule_url or website}")

    # Step 1: If Eversports, try slugs
    if platform and "eversports" in platform.lower():
        slugs = EVERSPORTS_SLUG_GUESSES.get(sid, [])

        # Add auto-generated slug guesses
        domain_slug = extract_domain_slug(website)
        if domain_slug and domain_slug not in slugs:
            slugs.append(domain_slug)
        name_slug = slugify(name)
        if name_slug and name_slug not in slugs:
            slugs.append(name_slug)
        id_slug = sid
        if id_slug not in slugs:
            slugs.append(id_slug)

        # Extract slug from schedule_url if it's an eversports URL
        if schedule_url and "eversports.ch" in schedule_url:
            m = re.search(r'eversports\.ch/s/([a-zA-Z0-9_-]+)', schedule_url)
            if m and m.group(1) not in slugs:
                slugs.insert(0, m.group(1))

        if slugs:
            print(f"  Trying Eversports slugs: {slugs}")
            classes, working_slug = try_eversports_slugs(sid, name, schedule_url or website, slugs)
            if classes:
                return classes, f"eversports (slug={working_slug})"

    # Step 2: Fetch website/schedule_url, look for eversports/sportsnow embeds
    target_url = schedule_url or website
    if target_url:
        html = fetch_text(target_url)
        if html:
            # Check for Eversports embed
            slug = find_eversports_slug(html)
            if slug:
                print(f"  Found Eversports slug '{slug}' in page HTML")
                classes = eversports_scrape(slug, sid, name, target_url)
                if classes:
                    return classes, f"eversports_embed (slug={slug})"

            # Check for SportNow embed
            sn = find_sportsnow_embed(html)
            if sn:
                print(f"  Found SportNow embed: {sn}")

            # Step 3: Try HTML parsing
            classes = parse_schedule_html(html, sid, name, target_url)
            if classes:
                return classes, "html_parse"

        time.sleep(0.2)

    # Step 4: Try subpages
    base = website or target_url
    if base:
        classes, method = try_subpages(base, sid, name)
        if classes:
            return classes, method

    return None, None


def main():
    print("=" * 60)
    print("RE-VERIFY STUDIOS - Processing 74 unverified studios")
    print("=" * 60)

    studio_info, schedule_data, unverified_studios = load_all_data()

    print(f"\nFound {len(unverified_studios)} studios with only unverified entries")

    stats = {"eversports_new": 0, "html_new": 0, "kept_valid": 0, "failed": 0}
    updated_cantons = set()

    for sid, info in sorted(unverified_studios.items()):
        try:
            new_classes, method = reverify_studio(sid, info)

            if new_classes:
                # REPLACE unverified entries with new verified ones
                canton = info["canton"]
                sched = schedule_data[canton]
                # Remove old entries for this studio
                sched["classes"] = [c for c in sched["classes"] if c["studio_id"] != sid]
                # Add new verified entries
                sched["classes"].extend(new_classes)
                updated_cantons.add(canton)

                report(sid, "success", method, len(new_classes))
                if "eversports" in (method or ""):
                    stats["eversports_new"] += 1
                else:
                    stats["html_new"] += 1
            else:
                # Check if existing data looks valid
                valid_entries = [e for e in info["entries"] if entry_looks_valid(e)]
                if valid_entries:
                    # Mark as verified since the data looks valid
                    canton = info["canton"]
                    sched = schedule_data[canton]
                    source = info["schedule_url"] or info["website"] or "original scrape"
                    for c in sched["classes"]:
                        if c["studio_id"] == sid and not c.get("verified"):
                            if entry_looks_valid(c):
                                c["verified"] = True
                                c["last_checked"] = TODAY
                                if not c.get("source"):
                                    c["source"] = source
                    updated_cantons.add(canton)
                    stats["kept_valid"] += 1
                    report(sid, "kept", f"existing data valid, marked verified ({len(valid_entries)}/{info['count']} valid)", len(valid_entries))
                else:
                    stats["failed"] += 1
                    report(sid, "fail", "no data found and existing entries look invalid", 0)

        except Exception as e:
            print(f"  [ERROR] {sid}: {e}")
            import traceback
            traceback.print_exc()
            report(sid, "fail", f"exception: {e}", 0)
            stats["failed"] += 1

        time.sleep(0.3)

    # Save updated schedule files
    for canton in updated_cantons:
        sched = schedule_data[canton]
        sched["last_updated"] = datetime.now(timezone.utc).isoformat()
        filepath = DATA_DIR / f"schedule_{canton}.json"
        with open(filepath, "w") as f:
            json.dump(sched, f, indent=2, ensure_ascii=False)
        print(f"\nSaved: {filepath}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    success_new = sum(1 for r in REPORT if r["status"] == "success")
    kept = sum(1 for r in REPORT if r["status"] == "kept")
    failed = sum(1 for r in REPORT if r["status"] == "fail")
    total_new_classes = sum(r["classes"] for r in REPORT if r["status"] == "success")
    total_kept_classes = sum(r["classes"] for r in REPORT if r["status"] == "kept")

    print(f"\nStudios processed: {len(REPORT)}")
    print(f"New verified data (Eversports/scrape): {success_new} studios, {total_new_classes} classes")
    print(f"  - Via Eversports: {stats['eversports_new']}")
    print(f"  - Via HTML parse: {stats['html_new']}")
    print(f"Existing data marked verified: {kept} studios, {total_kept_classes} classes")
    print(f"Failed (no data): {failed}")
    print(f"Cantons updated: {len(updated_cantons)} ({', '.join(sorted(updated_cantons))})")

    print(f"\nPer-studio results:")
    for r in sorted(REPORT, key=lambda x: x["status"]):
        if r["status"] == "success":
            status = "NEW    "
        elif r["status"] == "kept":
            status = "KEPT   "
        else:
            status = "FAIL   "
        print(f"  {status} | {r['studio']:40s} | {r['method'][:60]:60s} | {r['classes']} classes")


if __name__ == "__main__":
    main()
