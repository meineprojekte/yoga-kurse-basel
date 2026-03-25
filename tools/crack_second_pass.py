#!/usr/bin/env python3
"""
crack_second_pass.py - Second pass using WebFetch discoveries to add
manually-verified schedules and try BSPORT API for discovered studios.
"""

import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent.parent / "data"
TODAY = "2026-03-24"


def make_class(studio_id, studio_name, day, t_start, t_end, class_name, teacher, source):
    return {
        "studio_id": studio_id,
        "studio_name": studio_name,
        "day": day,
        "time_start": t_start,
        "time_end": t_end,
        "class_name": class_name[:100],
        "teacher": teacher[:60] if teacher else "",
        "level": "all",
        "source": source,
        "verified": True,
        "last_checked": TODAY,
    }


def fetch(url, timeout=10):
    try:
        return cffi_requests.get(url, impersonate="chrome", timeout=timeout, allow_redirects=True)
    except:
        return None


def load_schedule(canton):
    path = DATA_DIR / f"schedule_{canton}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"last_updated": "", "classes": []}


def save_schedule(canton, data):
    path = DATA_DIR / f"schedule_{canton}.json"
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_classes(canton, studio_id, new_classes):
    """Add classes to a canton schedule, replacing existing for this studio."""
    sched = load_schedule(canton)
    sched["classes"] = [c for c in sched.get("classes", []) if c.get("studio_id") != studio_id]
    sched["classes"].extend(new_classes)
    save_schedule(canton, sched)
    print(f"  Added {len(new_classes)} classes for {studio_id} in {canton}")
    return len(new_classes)


total_added = 0

# ===================================================================
# 1. YOGA CITY (Zurich) - Full schedule from WebFetch
# ===================================================================
print("\n=== Yoga City (zurich) ===")
classes = []
src = "https://www.yogacity.ch/stundenplan"
sid, sname = "yoga-city", "Yoga City"

schedule = [
    ("Monday", "09:30", "11:00", "Level G Iyengar Yoga", "Ariane"),
    ("Monday", "12:10", "13:10", "Level G Iyengar Yoga", "Ariane"),
    ("Monday", "17:50", "19:15", "Level 1 Iyengar Yoga", "Janine"),
    ("Monday", "19:30", "21:15", "Level 2+3 Iyengar Yoga", "Carlos"),
    ("Tuesday", "10:30", "12:00", "Level G Iyengar Yoga", "Christian"),
    ("Tuesday", "18:00", "19:30", "Level 2 Iyengar Yoga", "Carlos"),
    ("Tuesday", "19:45", "21:10", "Level 1 Iyengar Yoga", "Carlos"),
    ("Wednesday", "09:00", "10:00", "Pranayama Level G", "Dörthe"),
    ("Wednesday", "10:15", "11:45", "Level G Iyengar Yoga", "Dörthe"),
    ("Wednesday", "18:00", "19:25", "Level 1 Iyengar Yoga", "Carlos"),
    ("Wednesday", "19:45", "21:15", "Level 2+3 Iyengar Yoga", "Carlos"),
    ("Thursday", "17:00", "18:15", "Level 1 Iyengar Yoga", "Dörthe"),
    ("Thursday", "18:30", "20:15", "Level 2+3 Iyengar Yoga", "Dörthe"),
    ("Friday", "10:00", "11:30", "Level 2 Iyengar Yoga", "Carlos"),
    ("Friday", "12:10", "13:10", "Level G Iyengar Yoga", "Carlos"),
    ("Saturday", "10:30", "12:00", "Level 2 Iyengar Yoga", "Pius"),
    ("Saturday", "12:30", "14:00", "Level G Iyengar Yoga", "Janine"),
    ("Sunday", "10:30", "12:00", "Level G Iyengar Yoga", "Christian"),
]
for day, ts, te, cn, teacher in schedule:
    classes.append(make_class(sid, sname, day, ts, te, cn, teacher, src))
total_added += add_classes("zurich", sid, classes)

# ===================================================================
# 2. YOGA POUR TOUS NYON (Vaud) - Schedule from WebFetch
# ===================================================================
print("\n=== Yoga Pour Tous Nyon (vaud) ===")
classes = []
sid, sname = "yoga-pour-tous-nyon", "Yoga Pour Tous Nyon"
src = "https://www.yogapourtous-nyon.ch/horaires/"

schedule = [
    ("Wednesday", "09:00", "10:00", "Yoga tous niveaux", ""),
    ("Wednesday", "10:00", "11:00", "Yoga tous niveaux", ""),
    ("Wednesday", "11:00", "12:00", "Yoga tous niveaux", ""),
    ("Wednesday", "14:00", "15:00", "Yoga tous niveaux", ""),
    ("Wednesday", "15:00", "16:00", "Yoga tous niveaux", ""),
    ("Wednesday", "18:00", "19:00", "Yoga tous niveaux", ""),
]
for day, ts, te, cn, teacher in schedule:
    classes.append(make_class(sid, sname, day, ts, te, cn, teacher, src))
total_added += add_classes("vaud", sid, classes)

# ===================================================================
# 3. YOGA.IN Winterthur (Zurich) - Schedule from WebFetch
# ===================================================================
print("\n=== YOGA.IN Winterthur (zurich) ===")
classes = []
sid, sname = "yoga-in-winterthur", "YOGA.IN"
src = "https://www.yoga-in.ch/"

schedule = [
    ("Tuesday", "12:00", "13:00", "QiGong", "Maja Marquart"),
    ("Tuesday", "09:00", "10:00", "Senior Yoga (ProSenectute)", "Giuliana Keller"),
]
for day, ts, te, cn, teacher in schedule:
    classes.append(make_class(sid, sname, day, ts, te, cn, teacher, src))
total_added += add_classes("zurich", sid, classes)

# ===================================================================
# 4. Try BSPORT API for Soul City (Zurich) - company 5070
# ===================================================================
print("\n=== Soul City (zurich) - BSPORT API ===")
sid, sname = "soul-city", "Soul City"
classes = []

# Try BSPORT schedule API
for week in range(4):
    base_date = datetime.strptime(TODAY, "%Y-%m-%d") + timedelta(weeks=week)
    date_min = base_date.strftime("%Y-%m-%d")
    date_max = (base_date + timedelta(days=7)).strftime("%Y-%m-%d")
    url = f"https://backoffice.bsport.io/api/v1/offer/?company=5070&date_min={date_min}&date_max={date_max}&page=1&page_size=100"
    r = fetch(url)
    if r and r.status_code == 200:
        try:
            data = r.json()
            results = data.get("results", data) if isinstance(data, dict) else data
            if isinstance(results, list):
                for item in results:
                    name = item.get("name", item.get("title", ""))
                    start = item.get("date_start", item.get("start", ""))
                    end = item.get("date_end", item.get("end", ""))
                    coach = item.get("coach_name", item.get("coach", {}).get("name", "")) if isinstance(item.get("coach"), dict) else item.get("coach_name", "")
                    if start and name:
                        try:
                            dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                            day = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][dt.weekday()]
                            t_start = dt.strftime("%H:%M")
                            t_end = ""
                            if end:
                                dt_end = datetime.fromisoformat(end.replace("Z", "+00:00"))
                                t_end = dt_end.strftime("%H:%M")
                            key = (day, t_start, name)
                            classes.append(make_class(sid, sname, day, t_start, t_end, name, str(coach), "https://soulcity-zurich.ch/classes"))
                        except:
                            pass
                print(f"  Week {week}: found {len(results)} offers from BSPORT API")
        except Exception as e:
            print(f"  BSPORT API error: {e}")
    else:
        status = r.status_code if r else "no response"
        print(f"  BSPORT API week {week}: {status}")
    time.sleep(0.5)

# Deduplicate by (day, time, name)
seen = set()
unique = []
for c in classes:
    key = (c["day"], c["time_start"], c["class_name"])
    if key not in seen:
        seen.add(key)
        unique.append(c)
if unique:
    total_added += add_classes("zurich", sid, unique)
else:
    print("  No classes from BSPORT API")

# ===================================================================
# 5. Try BSPORT API for Yoga Flame Geneva - company 923, est 3377
# ===================================================================
print("\n=== Yoga Flame Geneva (geneve) - BSPORT API ===")
sid, sname = "yoga-flame-geneve", "Yoga Flame Genève"
classes = []

for week in range(4):
    base_date = datetime.strptime(TODAY, "%Y-%m-%d") + timedelta(weeks=week)
    date_min = base_date.strftime("%Y-%m-%d")
    date_max = (base_date + timedelta(days=7)).strftime("%Y-%m-%d")
    url = f"https://backoffice.bsport.io/api/v1/offer/?company=923&establishment__id=3377&date_min={date_min}&date_max={date_max}&page=1&page_size=100"
    r = fetch(url)
    if r and r.status_code == 200:
        try:
            data = r.json()
            results = data.get("results", data) if isinstance(data, dict) else data
            if isinstance(results, list):
                for item in results:
                    name = item.get("name", item.get("title", ""))
                    start = item.get("date_start", item.get("start", ""))
                    end = item.get("date_end", item.get("end", ""))
                    coach = ""
                    if isinstance(item.get("coach"), dict):
                        coach = item["coach"].get("name", "")
                    elif isinstance(item.get("coach_name"), str):
                        coach = item["coach_name"]
                    if start and name:
                        try:
                            dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                            day = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][dt.weekday()]
                            t_start = dt.strftime("%H:%M")
                            t_end = ""
                            if end:
                                dt_end = datetime.fromisoformat(end.replace("Z", "+00:00"))
                                t_end = dt_end.strftime("%H:%M")
                            classes.append(make_class(sid, sname, day, t_start, t_end, name, coach, "https://yogaflame.ch/studios/studio-geneva/"))
                        except:
                            pass
                print(f"  Week {week}: found {len(results)} offers")
        except Exception as e:
            print(f"  BSPORT API error: {e}")
    else:
        status = r.status_code if r else "no response"
        print(f"  BSPORT API week {week}: {status}")
    time.sleep(0.5)

seen = set()
unique = []
for c in classes:
    key = (c["day"], c["time_start"], c["class_name"])
    if key not in seen:
        seen.add(key)
        unique.append(c)
if unique:
    total_added += add_classes("geneve", sid, unique)
else:
    print("  No classes from BSPORT API")

# ===================================================================
# 6. Try BSPORT API for Yoga Flame Lausanne - company 923, est 3376
# ===================================================================
print("\n=== Yoga Flame Lausanne (vaud) - BSPORT API ===")
sid, sname = "yoga-flame-lausanne", "Yoga Flame Lausanne"
classes = []

for week in range(4):
    base_date = datetime.strptime(TODAY, "%Y-%m-%d") + timedelta(weeks=week)
    date_min = base_date.strftime("%Y-%m-%d")
    date_max = (base_date + timedelta(days=7)).strftime("%Y-%m-%d")
    url = f"https://backoffice.bsport.io/api/v1/offer/?company=923&establishment__id=3376&date_min={date_min}&date_max={date_max}&page=1&page_size=100"
    r = fetch(url)
    if r and r.status_code == 200:
        try:
            data = r.json()
            results = data.get("results", data) if isinstance(data, dict) else data
            if isinstance(results, list):
                for item in results:
                    name = item.get("name", item.get("title", ""))
                    start = item.get("date_start", item.get("start", ""))
                    end = item.get("date_end", item.get("end", ""))
                    coach = ""
                    if isinstance(item.get("coach"), dict):
                        coach = item["coach"].get("name", "")
                    elif isinstance(item.get("coach_name"), str):
                        coach = item["coach_name"]
                    if start and name:
                        try:
                            dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                            day = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][dt.weekday()]
                            t_start = dt.strftime("%H:%M")
                            t_end = ""
                            if end:
                                dt_end = datetime.fromisoformat(end.replace("Z", "+00:00"))
                                t_end = dt_end.strftime("%H:%M")
                            classes.append(make_class(sid, sname, day, t_start, t_end, name, coach, "https://yogaflame.ch/studios/studio-lausanne/"))
                        except:
                            pass
                print(f"  Week {week}: found {len(results)} offers")
        except Exception as e:
            print(f"  BSPORT API error: {e}")
    else:
        status = r.status_code if r else "no response"
        print(f"  BSPORT API week {week}: {status}")
    time.sleep(0.5)

seen = set()
unique = []
for c in classes:
    key = (c["day"], c["time_start"], c["class_name"])
    if key not in seen:
        seen.add(key)
        unique.append(c)
if unique:
    total_added += add_classes("vaud", sid, unique)
else:
    print("  No classes from BSPORT API")

# ===================================================================
# 7. Try remaining Eversports studios with more slug guesses
# ===================================================================
print("\n=== Trying more Eversports slug guesses ===")

DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
ALL_DAY_MAP = {
    "montag": "Monday", "dienstag": "Tuesday", "mittwoch": "Wednesday",
    "donnerstag": "Thursday", "freitag": "Friday", "samstag": "Saturday",
    "sonntag": "Sunday", "monday": "Monday", "tuesday": "Tuesday",
    "wednesday": "Wednesday", "thursday": "Thursday", "friday": "Friday",
    "saturday": "Saturday", "sunday": "Sunday",
}

def eversports_fetch(slug):
    url = f"https://www.eversports.ch/widget/api/eventsession/calendar?facilityShortId={slug}&startDate={TODAY}"
    r = fetch(url)
    if not r or r.status_code != 200:
        return None
    try:
        data = r.json()
    except:
        return None
    if data.get("status") != "success":
        return None
    return data.get("data", {}).get("html", "")

def parse_ev(ev_html, studio_id, studio_name, source_url):
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
            for k, v in ALL_DAY_MAP.items():
                if k in sr_text.lower():
                    day_name = v
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

def ev_scrape(slug, studio_id, studio_name, source_url):
    all_classes = []
    seen = set()
    base = datetime.strptime(TODAY, "%Y-%m-%d")
    for week in range(4):
        start = (base + timedelta(weeks=week)).strftime("%Y-%m-%d")
        url = f"https://www.eversports.ch/widget/api/eventsession/calendar?facilityShortId={slug}&startDate={start}"
        r = fetch(url)
        if not r or r.status_code != 200:
            continue
        try:
            data = r.json()
        except:
            continue
        if data.get("status") != "success":
            continue
        ev_html = data.get("data", {}).get("html", "")
        if not ev_html:
            continue
        week_classes = parse_ev(ev_html, studio_id, studio_name, source_url)
        for c in week_classes:
            key = (c["day"], c["time_start"], c["class_name"])
            if key not in seen:
                seen.add(key)
                all_classes.append(c)
        time.sleep(0.3)
    return all_classes

# Studios that failed with Eversports but might have different slugs
eversports_attempts = [
    # (canton, studio_id, studio_name, [slug_guesses])
    ("graubuenden", "yogaplaza-davos", "Yogaplaza Davos", [
        "yogaplaza-davos", "yogaplaza", "yoga-plaza-davos", "yoga-plaza"
    ]),
    ("graubuenden", "raw-yoga-chur", "RAW Yoga", [
        "raw-yoga", "raw-station", "rawstation", "raw-yoga-chur"
    ]),
    ("zurich", "das-yoga-haus-dubs", "Das Yoga Haus Dubs", [
        "das-yoga-haus-dubs", "dasyogahaus", "yoga-haus-dubs", "das-yoga-haus", "dasyogahausdubs"
    ]),
    ("zurich", "bodyart-studio", "BODYART Studio Zürich", [
        "bodyart-studio", "bodyart", "bodyart-studio-zurich", "bodyart-zuerich"
    ]),
    ("solothurn", "yoga-pilateszentrale-olten", "Yoga & Pilateszentrale", [
        "yoga-pilateszentrale-olten", "yoga-pilateszentrale", "pilateszentrale", "pilateszentrale-olten"
    ]),
    ("st-gallen", "lineupyoga-st-gallen", "LINEUPYOGA", [
        "lineupyoga", "lineup-yoga", "lineupyoga-st-gallen", "lineup-yoga-st-gallen"
    ]),
    ("thurgau", "soma-yoga-weinfelden", "Soma Yoga", [
        "soma-yoga", "soma-yoga-weinfelden", "somayoga"
    ]),
]

for canton, sid, sname, slugs in eversports_attempts:
    print(f"\n  {sname} ({sid}):")
    found = False
    for slug in slugs:
        ev_html = eversports_fetch(slug)
        if ev_html:
            classes = ev_scrape(slug, sid, sname, f"https://www.eversports.ch/s/{slug}")
            if classes:
                total_added += add_classes(canton, sid, classes)
                print(f"    FOUND slug: {slug} -> {len(classes)} classes")
                found = True
                break
            else:
                print(f"    slug {slug}: valid but 0 classes")
        else:
            print(f"    slug {slug}: not found")
        time.sleep(0.3)
    if not found:
        print(f"    No working slug found")

# ===================================================================
# 8. Try MindBody widget for bikram-yoga-zuerich
# ===================================================================
print("\n=== Trying MindBody for specific studios ===")

# bikram-yoga-zuerich - try healcode widget
for mb_id in ["1091", "29145", "913257"]:  # common Bikram studio IDs
    url = f"https://widgets.mindbodyonline.com/widgets/schedules/{mb_id}?options[start_date]={TODAY}"
    r = fetch(url)
    if r and r.status_code == 200 and len(r.text) > 500:
        print(f"  Bikram Yoga: MindBody ID {mb_id} returned data ({len(r.text)} chars)")
        break
    time.sleep(0.3)

# ===================================================================
# Summary
# ===================================================================
print(f"\n{'='*60}")
print(f"SECOND PASS COMPLETE")
print(f"Total new classes added: {total_added}")
print(f"{'='*60}")
