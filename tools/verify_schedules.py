#!/usr/bin/env python3
"""
Verify schedule URLs for yoga studios across Swiss cantons.
Checks if schedule pages have static HTML with scrapable schedule data.
Prioritizes biggest cantons, caps at 100 studios.
"""

import json
import glob
import re
import os
import sys
import time
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests

DATA_DIR = "/Users/andrea/ClaudeWork/JogaKurseBasel/data"
TOOLS_DIR = "/Users/andrea/ClaudeWork/JogaKurseBasel/tools"
MAX_STUDIOS = 100

# Prioritize biggest cantons
PRIORITY_CANTONS = ["zurich", "basel", "bern", "geneve", "vaud", "luzern",
                    "basel-landschaft", "st-gallen", "aargau", "solothurn",
                    "thurgau", "fribourg", "valais", "ticino", "graubuenden",
                    "neuchatel", "schwyz", "zug"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-CH,de;q=0.9,en;q=0.8,fr;q=0.7",
}

# Patterns for detecting schedule content
TIME_PATTERN = re.compile(r'\b\d{1,2}[:.]\d{2}\b')
DAY_PATTERNS = re.compile(
    r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|'
    r'Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag|'
    r'Lundi|Mardi|Mercredi|Jeudi|Vendredi|Samedi|Dimanche|'
    r'Lunedì|Martedì|Mercoledì|Giovedì|Venerdì|Sabato|Domenica|'
    r'Mo|Di|Mi|Do|Fr|Sa|So)\b', re.IGNORECASE
)
YOGA_KEYWORDS = re.compile(
    r'\b(Vinyasa|Hatha|Yin|Ashtanga|Bikram|Hot Yoga|Power Yoga|'
    r'Kundalini|Restorative|Prenatal|Flow|Pilates|Meditation|'
    r'Yoga Nidra|Jivamukti|Iyengar|Aerial|Dynamic|Slow Flow|'
    r'Mysore|Pranayama|Stretch|Relax|Gentle|Basic|Open Level|'
    r'Beginners?|Anfänger|Morning|Evening|Lunch|Core|Balance)\b', re.IGNORECASE
)

# Platform detection
PLATFORM_PATTERNS = {
    "Eversports": re.compile(r'eversports', re.IGNORECASE),
    "Momoyoga": re.compile(r'momoyoga', re.IGNORECASE),
    "MindBody": re.compile(r'mindbody|healcode', re.IGNORECASE),
    "Kursifant": re.compile(r'kursifant', re.IGNORECASE),
    "FitogramPro": re.compile(r'fitogram', re.IGNORECASE),
    "TeamUp": re.compile(r'teamup|goteamup', re.IGNORECASE),
    "Glofox": re.compile(r'glofox', re.IGNORECASE),
    "Supersaas": re.compile(r'supersaas', re.IGNORECASE),
    "Bookeo": re.compile(r'bookeo', re.IGNORECASE),
}


def load_studios():
    """Load all studios from prioritized cantons, up to MAX_STUDIOS."""
    studios = {}
    canton_files_loaded = []

    for canton in PRIORITY_CANTONS:
        if len(studios) >= MAX_STUDIOS:
            break
        path = os.path.join(DATA_DIR, f"studios_{canton}.json")
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for s in data.get("studios", []):
            if len(studios) >= MAX_STUDIOS:
                break
            sid = s.get("id", "")
            studios[sid] = {
                "name": s.get("name", ""),
                "schedule_url": s.get("schedule_url", ""),
                "website": s.get("website", ""),
                "booking_platform": s.get("booking_platform", ""),
                "canton": canton,
            }
        canton_files_loaded.append(canton)

    # Fill remaining slots from other cantons
    if len(studios) < MAX_STUDIOS:
        all_files = glob.glob(os.path.join(DATA_DIR, "studios_*.json"))
        for path in sorted(all_files):
            if len(studios) >= MAX_STUDIOS:
                break
            if ".enc.json" in path:
                continue
            canton = os.path.basename(path).replace("studios_", "").replace(".json", "")
            if canton in canton_files_loaded:
                continue
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for s in data.get("studios", []):
                if len(studios) >= MAX_STUDIOS:
                    break
                sid = s.get("id", "")
                if sid not in studios:
                    studios[sid] = {
                        "name": s.get("name", ""),
                        "schedule_url": s.get("schedule_url", ""),
                        "website": s.get("website", ""),
                        "booking_platform": s.get("booking_platform", ""),
                        "canton": canton,
                    }

    return studios


def load_existing_schedules():
    """Load all schedule data from schedule_*.json files."""
    schedules = {}
    for path in glob.glob(os.path.join(DATA_DIR, "schedule_*.json")):
        if ".enc.json" in path:
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for cls in data.get("classes", []):
            sid = cls.get("studio_id", "")
            if sid not in schedules:
                schedules[sid] = []
            schedules[sid].append(cls)
    return schedules


def detect_platform(html, url):
    """Detect which booking platform is used."""
    for name, pattern in PLATFORM_PATTERNS.items():
        if pattern.search(html) or pattern.search(url):
            return name
    return "website"


def check_schedule_url(studio_id, info):
    """Check a single studio's schedule URL."""
    url = info.get("schedule_url", "").strip()
    result = {
        "schedule_url": url,
        "studio_name": info.get("name", ""),
        "canton": info.get("canton", ""),
        "status": "no_url",
        "has_static_schedule": False,
        "platform": info.get("booking_platform", "unknown"),
        "classes_found": 0,
        "times_found": 0,
        "days_found": 0,
        "yoga_keywords_found": 0,
        "http_status": None,
        "scraped_times": [],
        "scraped_days": [],
        "scraped_classes": [],
    }

    if not url:
        return studio_id, result

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        result["http_status"] = resp.status_code

        if resp.status_code == 403:
            result["status"] = "blocked"
            return studio_id, result
        elif resp.status_code >= 400:
            result["status"] = "error"
            return studio_id, result

        html = resp.text
        result["platform"] = detect_platform(html, url)

        # Find schedule indicators
        times = TIME_PATTERN.findall(html)
        days = DAY_PATTERNS.findall(html)
        yoga_kw = YOGA_KEYWORDS.findall(html)

        # Filter out times that are clearly not schedule times (e.g., in CSS/JS)
        # Only count unique times
        unique_times = list(set(times))
        unique_days = list(set(d.lower() for d in days))
        unique_yoga = list(set(k.lower() for k in yoga_kw))

        result["times_found"] = len(unique_times)
        result["days_found"] = len(unique_days)
        result["yoga_keywords_found"] = len(unique_yoga)
        result["scraped_times"] = sorted(unique_times)[:20]
        result["scraped_days"] = sorted(unique_days)
        result["scraped_classes"] = sorted(unique_yoga)[:20]

        # Determine if scrapable: need times AND (days OR yoga keywords)
        has_times = len(unique_times) >= 3
        has_days = len(unique_days) >= 2
        has_yoga = len(unique_yoga) >= 2

        if has_times and (has_days or has_yoga):
            result["status"] = "scrapable"
            result["has_static_schedule"] = True
            result["classes_found"] = min(len(unique_times), 30)
        else:
            result["status"] = "dynamic"
            result["has_static_schedule"] = False

    except requests.exceptions.Timeout:
        result["status"] = "error"
        result["http_status"] = "timeout"
    except requests.exceptions.ConnectionError:
        result["status"] = "error"
        result["http_status"] = "connection_error"
    except Exception as e:
        result["status"] = "error"
        result["http_status"] = str(e)[:100]

    return studio_id, result


def extract_schedule_from_html(url, html):
    """Try to extract structured schedule data from HTML."""
    entries = []

    # Simple extraction: find lines with time patterns near day/class names
    lines = html.split('\n')
    for i, line in enumerate(lines):
        times_in_line = TIME_PATTERN.findall(line)
        if not times_in_line:
            continue

        # Look at surrounding context (this line and neighbors)
        context = ' '.join(lines[max(0, i-2):min(len(lines), i+3)])
        days_in_ctx = DAY_PATTERNS.findall(context)
        classes_in_ctx = YOGA_KEYWORDS.findall(context)

        if days_in_ctx or classes_in_ctx:
            entries.append({
                "times": times_in_line,
                "days": list(set(days_in_ctx)),
                "classes": list(set(classes_in_ctx)),
                "raw_line": line.strip()[:200],
            })

    return entries


def main():
    print("=" * 70)
    print("YOGA STUDIO SCHEDULE URL VERIFICATION")
    print("=" * 70)

    # Load data
    print("\nLoading studios...")
    studios = load_studios()
    print(f"  Loaded {len(studios)} studios from priority cantons")

    print("Loading existing schedules...")
    existing_schedules = load_existing_schedules()
    print(f"  Found schedules for {len(existing_schedules)} studios")

    # Count studios with URLs
    with_url = {sid: s for sid, s in studios.items() if s.get("schedule_url", "").strip()}
    without_url = {sid: s for sid, s in studios.items() if not s.get("schedule_url", "").strip()}
    print(f"\n  Studios with schedule_url: {len(with_url)}")
    print(f"  Studios without schedule_url: {len(without_url)}")

    # Check URLs concurrently
    print(f"\nChecking {len(with_url)} schedule URLs (10s timeout each)...")
    results = {}
    scrapable = []
    dynamic = []
    blocked = []
    errors = []

    # Add no_url entries first
    for sid, info in without_url.items():
        results[sid] = {
            "schedule_url": "",
            "studio_name": info.get("name", ""),
            "canton": info.get("canton", ""),
            "status": "no_url",
            "has_static_schedule": False,
            "platform": info.get("booking_platform", "unknown"),
            "classes_found": 0,
        }

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(check_schedule_url, sid, info): sid
            for sid, info in with_url.items()
        }
        done_count = 0
        for future in as_completed(futures):
            done_count += 1
            sid, result = future.result()
            results[sid] = result

            status = result["status"]
            name = result.get("studio_name", sid)
            if status == "scrapable":
                scrapable.append((sid, result))
                marker = "[OK]"
            elif status == "dynamic":
                dynamic.append((sid, result))
                marker = "[JS]"
            elif status == "blocked":
                blocked.append((sid, result))
                marker = "[403]"
            else:
                errors.append((sid, result))
                marker = "[ERR]"

            if done_count % 10 == 0 or done_count == len(with_url):
                print(f"  Progress: {done_count}/{len(with_url)}")

    # Report results
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print(f"\n  Total studios checked: {len(with_url)}")
    print(f"  Scrapable (static HTML schedules): {len(scrapable)}")
    print(f"  Dynamic (JS-rendered): {len(dynamic)}")
    print(f"  Blocked (403): {len(blocked)}")
    print(f"  Errors: {len(errors)}")
    print(f"  No URL: {len(without_url)}")

    if scrapable:
        print(f"\n{'=' * 70}")
        print("SCRAPABLE STUDIOS (have static schedule data in HTML)")
        print("=" * 70)
        for sid, r in sorted(scrapable, key=lambda x: x[1].get("canton", "")):
            print(f"\n  [{r['canton'].upper()}] {r['studio_name']} ({sid})")
            print(f"    URL: {r['schedule_url']}")
            print(f"    Platform: {r['platform']}")
            print(f"    Times found: {r['times_found']}, Days: {r['days_found']}, Keywords: {r['yoga_keywords_found']}")
            if r.get("scraped_classes"):
                print(f"    Classes: {', '.join(r['scraped_classes'][:8])}")

    if blocked:
        print(f"\n{'=' * 70}")
        print("BLOCKED STUDIOS (403 Forbidden)")
        print("=" * 70)
        for sid, r in blocked:
            print(f"  [{r['canton'].upper()}] {r['studio_name']}: {r['schedule_url']}")

    if errors:
        print(f"\n{'=' * 70}")
        print("ERROR STUDIOS")
        print("=" * 70)
        for sid, r in errors:
            print(f"  [{r['canton'].upper()}] {r['studio_name']}: {r.get('http_status', 'unknown')}")

    # Count existing schedule classes for each studio
    print(f"\n{'=' * 70}")
    print("EXISTING SCHEDULE DATA vs VERIFICATION")
    print("=" * 70)
    studios_with_classes = sum(1 for sid in studios if sid in existing_schedules and len(existing_schedules[sid]) > 0)
    total_classes = sum(len(v) for v in existing_schedules.values())
    print(f"  Studios with existing schedule data: {studios_with_classes}")
    print(f"  Total classes in schedule files: {total_classes}")

    # Save verification results (clean version without scraped data)
    verification = {}
    for sid, r in results.items():
        verification[sid] = {
            "schedule_url": r.get("schedule_url", ""),
            "studio_name": r.get("studio_name", ""),
            "canton": r.get("canton", ""),
            "status": r["status"],
            "has_static_schedule": r.get("has_static_schedule", False),
            "platform": r.get("platform", "unknown"),
            "classes_found": r.get("classes_found", 0),
            "http_status": r.get("http_status"),
        }

    verification_path = os.path.join(TOOLS_DIR, "schedule_verification.json")
    with open(verification_path, "w", encoding="utf-8") as f:
        json.dump(verification, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved verification to: {verification_path}")

    # Save verified/scraped schedules for scrapable studios
    verified_schedules = {}
    for sid, r in scrapable:
        verified_schedules[sid] = {
            "studio_name": r["studio_name"],
            "canton": r["canton"],
            "schedule_url": r["schedule_url"],
            "platform": r["platform"],
            "scraped_times": r.get("scraped_times", []),
            "scraped_days": r.get("scraped_days", []),
            "scraped_classes": r.get("scraped_classes", []),
            "existing_classes": len(existing_schedules.get(sid, [])),
        }

    verified_path = os.path.join(TOOLS_DIR, "verified_schedules.json")
    with open(verified_path, "w", encoding="utf-8") as f:
        json.dump(verified_schedules, f, indent=2, ensure_ascii=False)
    print(f"  Saved verified schedules to: {verified_path}")

    # Summary
    print(f"\n{'=' * 70}")
    print("RECOMMENDATION SUMMARY")
    print("=" * 70)
    print(f"\n  SCRAPABLE ({len(scrapable)} studios):")
    print("    These studios have schedule data in static HTML.")
    print("    Their schedules can potentially be auto-updated via scraping.")
    print()
    print(f"  LINK-TO-OFFICIAL ({len(dynamic) + len(blocked)} studios):")
    print("    These studios use JS-rendered widgets or block scraping.")
    print("    Best approach: link to their official schedule page.")
    print()
    print(f"  NO URL ({len(without_url)} studios):")
    print("    These studios have no schedule_url.")
    print("    Schedule data comes from manual research only.")

    # Canton breakdown
    print(f"\n{'=' * 70}")
    print("CANTON BREAKDOWN")
    print("=" * 70)
    canton_stats = {}
    for sid, r in results.items():
        c = r.get("canton", "unknown")
        if c not in canton_stats:
            canton_stats[c] = {"scrapable": 0, "dynamic": 0, "blocked": 0, "error": 0, "no_url": 0}
        canton_stats[c][r["status"]] = canton_stats[c].get(r["status"], 0) + 1

    for canton in sorted(canton_stats.keys()):
        stats = canton_stats[canton]
        total = sum(stats.values())
        print(f"  {canton:20s}: {total:3d} total | "
              f"scrapable: {stats.get('scrapable',0):2d} | "
              f"dynamic: {stats.get('dynamic',0):2d} | "
              f"blocked: {stats.get('blocked',0):2d} | "
              f"error: {stats.get('error',0):2d} | "
              f"no_url: {stats.get('no_url',0):2d}")


if __name__ == "__main__":
    main()
