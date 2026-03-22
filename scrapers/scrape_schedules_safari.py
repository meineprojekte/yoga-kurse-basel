#!/usr/bin/env python3
"""
Safari-based Schedule Scraper for Yoga Kurse Basel/Schweiz

Uses Safari via AppleScript to access studio websites that block regular
HTTP scrapers (e.g., Eversports 403s, dynamic JS-rendered schedules).

This script is for LOCAL use on Andrea's Mac — NOT for GitHub Actions.
Run manually to collect schedule data the automated scraper cannot get.

Usage:
    python3 scrapers/scrape_schedules_safari.py                    # all blocked/dynamic/error studios
    python3 scrapers/scrape_schedules_safari.py --canton zurich    # only zurich
    python3 scrapers/scrape_schedules_safari.py --max 20           # max 20 studios
    python3 scrapers/scrape_schedules_safari.py --status blocked   # only blocked status
    python3 scrapers/scrape_schedules_safari.py --dry-run          # show what would be scraped
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TOOLS_DIR = PROJECT_ROOT / "tools"
VERIFICATION_FILE = TOOLS_DIR / "schedule_verification.json"

# Temp files for AppleScript/JS communication
TMP_DIR = Path(tempfile.gettempdir())
JS_FILE = TMP_DIR / "_safari_yoga_extract.js"
APPLESCRIPT_FILE = TMP_DIR / "_safari_yoga.scpt"
RESULT_FILE = TMP_DIR / "_safari_yoga_result.json"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("safari-scraper")

# ---------------------------------------------------------------------------
# Target statuses — studios whose schedules we want to scrape via Safari
# ---------------------------------------------------------------------------
TARGET_STATUSES = {"blocked", "dynamic", "error"}

# ---------------------------------------------------------------------------
# JavaScript extraction code
# ---------------------------------------------------------------------------
EXTRACTION_JS = r"""
(function() {
    var results = {classes: [], platform: 'unknown', error: null};

    // Day name mapping: DE, EN, FR, IT -> English canonical
    var dayMap = {
        'montag':'Monday','dienstag':'Tuesday','mittwoch':'Wednesday',
        'donnerstag':'Thursday','freitag':'Friday','samstag':'Saturday','sonntag':'Sunday',
        'mo':'Monday','di':'Tuesday','mi':'Wednesday','do':'Thursday',
        'fr':'Friday','sa':'Saturday','so':'Sunday',
        'monday':'Monday','tuesday':'Tuesday','wednesday':'Wednesday',
        'thursday':'Thursday','friday':'Friday','saturday':'Saturday','sunday':'Sunday',
        'mon':'Monday','tue':'Tuesday','wed':'Wednesday','thu':'Thursday',
        'fri':'Friday','sat':'Saturday','sun':'Sunday',
        'lundi':'Monday','mardi':'Tuesday','mercredi':'Wednesday',
        'jeudi':'Thursday','vendredi':'Friday','samedi':'Saturday','dimanche':'Sunday',
        'lunedi':'Monday','lunedì':'Monday','martedi':'Tuesday','martedì':'Tuesday',
        'mercoledi':'Wednesday','mercoledì':'Wednesday','giovedi':'Thursday','giovedì':'Thursday',
        'venerdi':'Friday','venerdì':'Friday','sabato':'Saturday','domenica':'Sunday',
        'lu':'Monday','ma':'Tuesday','me':'Wednesday','gi':'Thursday',
        've':'Friday','lun':'Monday','mar':'Tuesday','mer':'Wednesday',
        'gio':'Thursday','ven':'Friday','sab':'Saturday','dom':'Sunday'
    };

    // Yoga-related keywords to validate class names
    var yogaKeywords = /yoga|vinyasa|hatha|yin|ashtanga|kundalini|flow|pilates|meditation|stretch|power|hot|bikram|restorative|prenatal|postnatal|nidra|pranayama|mysore|jivamukti|aerial|acro|iyengar|sivananda|anusara|forrest|rocket|slow|gentle|sanft|dynamic|dynamisch|kurs|class|lektion|stunde|session/i;

    // Noise words to skip
    var noiseWords = /^(buchen|book|anmelden|register|sign up|mehr|more|details|info|plätze|spots|frei|available|abbrechen|cancel|jetzt|now|login|warenkorb|cart|CHF|EUR|\d+\s*(min|€|CHF)|cookie|akzeptieren|accept|impressum|datenschutz|agb)$/i;

    var timeRangeRe = /(\d{1,2})[.:h](\d{2})\s*[-–—]\s*(\d{1,2})[.:h](\d{2})/;
    var singleTimeRe = /(\d{1,2})[.:h](\d{2})/;
    var dayRe = /\b(Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Lundi|Mardi|Mercredi|Jeudi|Vendredi|Samedi|Dimanche|Luned[iì]|Marted[iì]|Mercoled[iì]|Gioved[iì]|Venerd[iì]|Sabato|Domenica|Mo|Di|Mi|Do|Fr|Sa|So)\b/gi;

    function normTime(h, m) {
        return (h.length === 1 ? '0' : '') + h + ':' + m;
    }

    function lookupDay(text) {
        var t = text.trim().toLowerCase().replace(/[,.\s\d]/g, '');
        return dayMap[t] || null;
    }

    try {
        // =====================================================================
        // STRATEGY 1: TEXT-BASED extraction from document.body.innerText
        // Works regardless of CSS class names (Eversports obfuscated DOM, etc.)
        // =====================================================================
        var bodyText = document.body.innerText || '';
        var allLines = bodyText.split('\n').map(function(l){return l.trim()}).filter(function(l){return l.length > 0});

        // Detect platform from URL or page content
        var pageUrl = window.location.href || '';
        if (pageUrl.indexOf('eversports') >= 0) results.platform = 'Eversports';
        else if (pageUrl.indexOf('mindbody') >= 0 || bodyText.indexOf('MINDBODY') >= 0) results.platform = 'MindBody';
        else if (pageUrl.indexOf('sportsnow') >= 0) results.platform = 'SportsNow';

        var currentDay = '';
        var pendingClass = null;

        for (var li = 0; li < allLines.length; li++) {
            var line = allLines[li];

            // Skip noise
            if (noiseWords.test(line)) continue;
            if (line.length > 200) continue;

            // Check if this line is a day header
            var dayMatch = line.match(dayRe);
            if (dayMatch) {
                var candidateDay = lookupDay(dayMatch[0]);
                if (candidateDay) {
                    // Only treat as day header if line is short (just the day name, maybe a date)
                    var stripped = line.replace(dayRe, '').replace(/[\d\s.,\/\-]/g, '');
                    if (stripped.length < 15) {
                        currentDay = candidateDay;
                        continue;
                    }
                }
            }

            // Check for time range in this line
            var trMatch = line.match(timeRangeRe);
            if (trMatch) {
                var timeStart = normTime(trMatch[1], trMatch[2]);
                var timeEnd = normTime(trMatch[3], trMatch[4]);

                // Extract class name: text before or after the time, excluding noise
                var beforeTime = line.substring(0, line.indexOf(trMatch[0])).trim();
                var afterTime = line.substring(line.indexOf(trMatch[0]) + trMatch[0].length).trim();

                // Remove trailing/leading separators
                beforeTime = beforeTime.replace(/^[\s\-–—|:]+|[\s\-–—|:]+$/g, '');
                afterTime = afterTime.replace(/^[\s\-–—|:]+|[\s\-–—|:]+$/g, '');

                var className = '';
                var teacher = '';

                // If there's text before the time, that's often the class name
                if (beforeTime.length > 2 && !noiseWords.test(beforeTime)) {
                    className = beforeTime;
                    if (afterTime.length > 2 && !noiseWords.test(afterTime)) {
                        teacher = afterTime;
                    }
                } else if (afterTime.length > 2 && !noiseWords.test(afterTime)) {
                    className = afterTime;
                }

                // If no class name found inline, look at adjacent lines
                if (!className) {
                    // Check previous line
                    if (li > 0 && !allLines[li-1].match(timeRangeRe) && !noiseWords.test(allLines[li-1])) {
                        var prevLine = allLines[li-1];
                        var prevDay = lookupDay(prevLine);
                        if (!prevDay && prevLine.length > 2 && prevLine.length < 100) {
                            className = prevLine;
                        }
                    }
                    // Check next line
                    if (!className && li + 1 < allLines.length && !allLines[li+1].match(timeRangeRe)) {
                        var nextLine = allLines[li+1];
                        if (!noiseWords.test(nextLine) && nextLine.length > 2 && nextLine.length < 100) {
                            className = nextLine;
                        }
                    }
                }

                // If still no class name, check next line for teacher
                if (className && !teacher && li + 1 < allLines.length) {
                    var nextL = allLines[li+1];
                    if (!nextL.match(timeRangeRe) && !noiseWords.test(nextL) && nextL.length > 2 && nextL.length < 60) {
                        var nextDay = lookupDay(nextL);
                        if (!nextDay && nextL !== className) {
                            teacher = nextL;
                        }
                    }
                }

                if (className || timeStart) {
                    results.classes.push({
                        class_name: className,
                        time_start: timeStart,
                        time_end: timeEnd,
                        teacher: teacher,
                        day: currentDay,
                        level: 'all',
                        raw: line.substring(0, 200)
                    });
                }
                continue;
            }

            // Check for single time (no range) — less reliable, only use if line has yoga keywords
            var stMatch = line.match(singleTimeRe);
            if (stMatch && yogaKeywords.test(line)) {
                var tStart = normTime(stMatch[1], stMatch[2]);
                var cName = line.replace(singleTimeRe, '').replace(/^[\s\-–—|:]+|[\s\-–—|:]+$/g, '').trim();
                if (cName.length > 2 && !noiseWords.test(cName)) {
                    results.classes.push({
                        class_name: cName,
                        time_start: tStart,
                        time_end: '',
                        teacher: '',
                        day: currentDay,
                        level: 'all',
                        raw: line.substring(0, 200)
                    });
                }
            }
        }

        // =====================================================================
        // STRATEGY 2: DOM-BASED extraction (try specific selectors as fallback)
        // =====================================================================
        if (results.classes.length === 0) {
            // --- SportsNow cal-entry divs ---
            var snEntries = document.querySelectorAll('.cal-entry, .calendar-entry');
            if (snEntries.length > 0) {
                results.platform = 'SportsNow';
                snEntries.forEach(function(entry) {
                    var name = entry.getAttribute('data-service-session-name') || '';
                    var teacher = entry.getAttribute('data-team') || '';
                    var text = entry.innerText || '';
                    var tm = text.match(timeRangeRe);
                    if (name || tm) {
                        results.classes.push({
                            class_name: name,
                            time_start: tm ? normTime(tm[1], tm[2]) : '',
                            time_end: tm ? normTime(tm[3], tm[4]) : '',
                            teacher: teacher,
                            day: currentDay,
                            level: 'all',
                            raw: text.substring(0, 200)
                        });
                    }
                });
            }

            // --- Generic table rows with times ---
            if (results.classes.length === 0) {
                results.platform = 'generic';
                var rows = document.querySelectorAll('table tr');
                rows.forEach(function(row) {
                    var text = row.innerText || '';
                    var tm = text.match(timeRangeRe);
                    if (tm) {
                        var dm = text.match(dayRe);
                        var cells = Array.from(row.querySelectorAll('td, th')).map(function(c){return c.innerText.trim()});
                        var cn = '';
                        for (var i=0;i<cells.length;i++) {
                            if (cells[i].length > 3 && !cells[i].match(/^\d{1,2}[.:]\d{2}/) && !cells[i].match(dayRe) && !noiseWords.test(cells[i])) {
                                cn = cells[i]; break;
                            }
                        }
                        results.classes.push({
                            class_name: cn,
                            time_start: normTime(tm[1], tm[2]),
                            time_end: normTime(tm[3], tm[4]),
                            teacher: '',
                            day: dm ? (dayMap[dm[0].toLowerCase()] || dm[0]) : '',
                            level: 'all',
                            raw: text.substring(0, 200)
                        });
                    }
                });
            }
        }

        // Deduplicate by class_name + time_start + day
        var unique = {};
        results.classes = results.classes.filter(function(c) {
            var key = (c.class_name + '|' + c.time_start + '|' + c.day).toLowerCase();
            if (unique[key]) return false;
            unique[key] = true;
            return true;
        });

    } catch(e) {
        results.error = e.toString();
    }
    return JSON.stringify(results);
})();
"""


# ---------------------------------------------------------------------------
# AppleScript helpers
# ---------------------------------------------------------------------------

def verify_safari_available():
    """Check that Safari is available via AppleScript."""
    script = 'tell application "Safari" to return name of window 1'
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            log.warning("Safari not open, trying to launch...")
            subprocess.run(["open", "-a", "Safari"], timeout=10)
            import time; time.sleep(3)
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=15
            )
        log.info("Safari OK — AppleScript is working.")
        return True
    except subprocess.TimeoutExpired:
        log.error("AppleScript timed out. Is macOS responsive?")
        return False
    except FileNotFoundError:
        log.error("osascript not found — this script requires macOS.")
        return False


def safari_open_url(url):
    """Open a URL in Safari and return the tab index."""
    script = f'''
    tell application "Safari"
        activate
        if (count of windows) = 0 then
            make new document with properties {{URL:"{url}"}}
        else
            tell window 1
                set newTab to make new tab with properties {{URL:"{url}"}}
            end tell
        end if
    end tell
    '''
    subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)


def safari_wait_for_load(timeout_seconds=15):
    """Wait for the current Safari tab to finish loading."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        check = '''
        tell application "Safari"
            tell window 1
                set currentTab to current tab
                return (do JavaScript "document.readyState" in currentTab)
            end tell
        end tell
        '''
        try:
            r = subprocess.run(
                ["osascript", "-e", check],
                capture_output=True, text=True, timeout=5
            )
            state = r.stdout.strip()
            if state == "complete":
                return True
        except (subprocess.TimeoutExpired, Exception):
            pass
        time.sleep(0.5)
    return False


def safari_execute_js(js_code, timeout=15):
    """Execute JavaScript in the current Safari tab and return the result."""
    # Write JS to a temp file to avoid AppleScript quoting issues
    JS_FILE.write_text(js_code, encoding="utf-8")

    applescript = f'''
    set jsFile to POSIX file "{JS_FILE}" as alias
    set jsCode to read jsFile as «class utf8»
    tell application "Safari"
        tell window 1
            set currentTab to current tab
            set jsResult to (do JavaScript jsCode in currentTab)
            return jsResult
        end tell
    end tell
    '''
    APPLESCRIPT_FILE.write_text(applescript, encoding="utf-8")

    try:
        r = subprocess.run(
            ["osascript", str(APPLESCRIPT_FILE)],
            capture_output=True, text=True, timeout=timeout
        )
        if r.returncode == 0:
            return r.stdout.strip()
        else:
            log.warning(f"JS execution error: {r.stderr.strip()[:200]}")
            return None
    except subprocess.TimeoutExpired:
        log.warning("JS execution timed out")
        return None


def safari_close_tab():
    """Close the current tab in Safari."""
    script = '''
    tell application "Safari"
        tell window 1
            close current tab
        end tell
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=5)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_verification():
    """Load schedule_verification.json."""
    if not VERIFICATION_FILE.exists():
        log.warning(f"Verification file not found: {VERIFICATION_FILE}")
        return {}
    with open(VERIFICATION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_studios_for_canton(canton):
    """Load studios_*.json for a given canton, return list of studio dicts."""
    fname = DATA_DIR / f"studios_{canton}.json"
    if not fname.exists():
        return []
    with open(fname, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("studios", [])
    return data


def load_schedule_for_canton(canton):
    """Load schedule_*.json for a given canton."""
    fname = DATA_DIR / f"schedule_{canton}.json"
    if not fname.exists():
        return {"last_updated": "", "classes": [], "_meta": {}}
    with open(fname, "r", encoding="utf-8") as f:
        return json.load(f)


def save_schedule_for_canton(canton, schedule_data):
    """Save schedule_*.json for a given canton."""
    fname = DATA_DIR / f"schedule_{canton}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(schedule_data, f, indent=2, ensure_ascii=False)
    log.info(f"Saved {fname.name}")


def get_all_cantons():
    """Get list of all cantons that have studios files."""
    cantons = []
    for f in sorted(DATA_DIR.glob("studios_*.json")):
        if ".enc." in f.name:
            continue
        canton = f.stem.replace("studios_", "")
        cantons.append(canton)
    return cantons


# ---------------------------------------------------------------------------
# Build target list
# ---------------------------------------------------------------------------

def build_targets(verification, cantons_filter=None, statuses=None, max_studios=50):
    """
    Build list of studios to scrape via Safari.
    Returns list of dicts with keys: studio_id, studio_name, canton, schedule_url, platform, status
    """
    if statuses is None:
        statuses = TARGET_STATUSES

    targets = []
    for studio_id, info in verification.items():
        if info.get("status") not in statuses:
            continue
        if not info.get("schedule_url"):
            continue
        canton = info.get("canton", "")
        if cantons_filter and canton not in cantons_filter:
            continue
        targets.append({
            "studio_id": studio_id,
            "studio_name": info.get("studio_name", studio_id),
            "canton": canton,
            "schedule_url": info["schedule_url"],
            "platform": info.get("platform", "unknown"),
            "status": info["status"],
        })

    # Sort: blocked first, then dynamic, then error
    order = {"blocked": 0, "dynamic": 1, "error": 2}
    targets.sort(key=lambda t: (order.get(t["status"], 9), t["canton"], t["studio_name"]))

    if len(targets) > max_studios:
        targets = targets[:max_studios]

    return targets


# ---------------------------------------------------------------------------
# Scrape a single studio
# ---------------------------------------------------------------------------

def get_eversports_schedule_url(url):
    """
    For Eversports studio URLs, try the /classes path variant.
    E.g. https://www.eversports.ch/s/yoga-am-zuerichberg -> .../classes
    """
    if "eversports.ch/s/" in url:
        base = url.rstrip("/")
        if not base.endswith("/classes"):
            return base + "/classes"
    return url


def get_mindbody_widget_url(url, studio):
    """
    For studios with MindBody widget IDs, construct the direct widget URL
    which renders the schedule in an iframe-like page.
    """
    widget_id = studio.get("mindbody_widget_id", "")
    if widget_id:
        return f"https://go.mindbodyonline.com/book/widgets/schedules/view/{widget_id}/schedule"
    return url


def scrape_studio(target):
    """
    Scrape a single studio's schedule via Safari.
    Returns dict with keys: success, classes, platform, error
    """
    url = target["schedule_url"]
    platform = target.get("platform", "").lower()
    is_eversports = "eversports" in url.lower() or platform == "eversports"
    is_mindbody = platform == "mindbody"
    log.info(f"  Opening: {url}")

    # For Eversports, try /classes path first
    if is_eversports:
        url = get_eversports_schedule_url(url)
        log.info(f"  Eversports: using URL {url}")

    try:
        safari_open_url(url)

        # Wait for initial page load
        loaded = safari_wait_for_load(timeout_seconds=20)
        if not loaded:
            log.warning(f"  Page did not finish loading within 20s")

        # Extra wait for JS-heavy pages
        if is_eversports:
            wait_time = 15
        elif is_mindbody:
            wait_time = 12
        else:
            wait_time = 5
        log.info(f"  Waiting {wait_time}s for JS rendering...")
        time.sleep(wait_time)

        # Execute extraction JavaScript
        raw_result = safari_execute_js(EXTRACTION_JS, timeout=20)

        if not raw_result:
            # For Eversports, try the base URL if /classes didn't work
            if is_eversports and url.endswith("/classes"):
                base_url = url.replace("/classes", "")
                log.info(f"  /classes failed, trying base URL: {base_url}")
                safari_close_tab()
                safari_open_url(base_url)
                safari_wait_for_load(timeout_seconds=20)
                time.sleep(15)
                raw_result = safari_execute_js(EXTRACTION_JS, timeout=20)

            if not raw_result:
                return {"success": False, "classes": [], "platform": "unknown",
                        "error": "No result from JS extraction"}

        # Parse JSON result
        try:
            result = json.loads(raw_result)
        except json.JSONDecodeError as e:
            # Sometimes the result has extra wrapping
            log.warning(f"  JSON parse failed, trying cleanup: {e}")
            # Try to find JSON in the output
            match = re.search(r'\{.*\}', raw_result, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                return {"success": False, "classes": [], "platform": "unknown",
                        "error": f"Invalid JSON: {raw_result[:100]}"}

        classes = result.get("classes", [])
        platform_detected = result.get("platform", "unknown")
        error = result.get("error")

        if error:
            log.warning(f"  JS error: {error}")

        return {
            "success": len(classes) > 0,
            "classes": classes,
            "platform": platform_detected,
            "error": error,
        }

    except Exception as e:
        return {"success": False, "classes": [], "platform": "unknown",
                "error": str(e)}

    finally:
        try:
            safari_close_tab()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Update schedule data
# ---------------------------------------------------------------------------

def update_schedule_with_results(canton, studio_id, studio_name, classes, source_url):
    """
    Merge scraped classes into the canton's schedule file.
    Replaces all existing classes for the studio_id, marks as verified.
    """
    schedule = load_schedule_for_canton(canton)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Remove old entries for this studio
    existing = schedule.get("classes", [])
    filtered = [c for c in existing if c.get("studio_id") != studio_id]

    # Add new entries
    for cls in classes:
        filtered.append({
            "studio_id": studio_id,
            "studio_name": studio_name,
            "day": cls.get("day", ""),
            "time_start": cls.get("time_start", ""),
            "time_end": cls.get("time_end", ""),
            "class_name": cls.get("class_name", ""),
            "teacher": cls.get("teacher", ""),
            "level": cls.get("level", "all"),
            "source": source_url,
            "verified": True,
            "last_checked": today,
        })

    schedule["classes"] = filtered
    schedule["last_updated"] = datetime.now(timezone.utc).isoformat()

    if "_meta" not in schedule:
        schedule["_meta"] = {}
    schedule["_meta"]["last_updated"] = today
    schedule["_meta"]["note"] = ("Stundenplan-Daten aus öffentlichen Quellen. "
                                  "Für aktuelle Zeiten siehe Studio-Website.")

    save_schedule_for_canton(canton, schedule)
    return len(classes)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Scrape yoga schedules via Safari (for blocked/dynamic sites)")
    parser.add_argument("--canton", type=str, default=None,
                        help="Only scrape studios in this canton (e.g. zurich)")
    parser.add_argument("--max", type=int, default=50,
                        help="Maximum number of studios to scrape (default: 50)")
    parser.add_argument("--status", type=str, default=None,
                        help="Comma-separated statuses to target (default: blocked,dynamic,error)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be scraped without actually scraping")
    parser.add_argument("--delay", type=float, default=2.0,
                        help="Seconds to wait between studios (default: 2)")
    args = parser.parse_args()

    print("=" * 60)
    print("  Safari Schedule Scraper — Yoga Kurse Schweiz")
    print("=" * 60)
    print()

    # 1. Verify Safari/AppleScript is working
    if not args.dry_run:
        if not verify_safari_available():
            print("\nERROR: Safari/AppleScript not available. Exiting.")
            sys.exit(1)
        print()

    # 2. Load verification data
    verification = load_verification()
    if not verification:
        print("ERROR: No verification data found. Run verify_schedules.py first.")
        sys.exit(1)

    # 3. Determine cantons and statuses to target
    cantons_filter = None
    if args.canton:
        cantons_filter = [c.strip() for c in args.canton.split(",")]
        log.info(f"Filtering cantons: {cantons_filter}")

    statuses = TARGET_STATUSES
    if args.status:
        statuses = set(s.strip() for s in args.status.split(","))
        log.info(f"Targeting statuses: {statuses}")

    # 4. Build target list
    targets = build_targets(verification, cantons_filter, statuses, args.max)

    if not targets:
        print("No studios match the filter criteria.")
        print(f"  Cantons: {cantons_filter or 'all'}")
        print(f"  Statuses: {statuses}")
        sys.exit(0)

    print(f"Found {len(targets)} studios to scrape:")
    print()
    for i, t in enumerate(targets, 1):
        print(f"  {i:3d}. [{t['status']:8s}] {t['studio_name']:<40s} ({t['canton']})")
        print(f"       {t['schedule_url']}")
    print()

    if args.dry_run:
        print("DRY RUN — no scraping performed.")
        sys.exit(0)

    # 5. Scrape each studio
    results = {"success": 0, "failed": 0, "skipped": 0, "total_classes": 0}
    details = []

    for i, target in enumerate(targets, 1):
        print(f"\n[{i}/{len(targets)}] {target['studio_name']} ({target['canton']})")
        print(f"  Status: {target['status']} | Platform: {target['platform']}")

        result = scrape_studio(target)

        if result["success"]:
            n_classes = len(result["classes"])
            results["success"] += 1
            results["total_classes"] += n_classes
            print(f"  SUCCESS: {n_classes} classes found (platform: {result['platform']})")

            # Update schedule file
            update_schedule_with_results(
                target["canton"],
                target["studio_id"],
                target["studio_name"],
                result["classes"],
                target["schedule_url"],
            )
            details.append({
                "studio": target["studio_name"],
                "canton": target["canton"],
                "status": "OK",
                "classes": n_classes,
                "platform": result["platform"],
            })
        else:
            results["failed"] += 1
            error_msg = result.get("error", "unknown error")
            print(f"  FAILED: {error_msg}")
            details.append({
                "studio": target["studio_name"],
                "canton": target["canton"],
                "status": "FAILED",
                "classes": 0,
                "error": error_msg,
            })

        # Rate limiting
        if i < len(targets):
            log.info(f"  Waiting {args.delay}s before next studio...")
            time.sleep(args.delay)

    # 6. Print summary
    print()
    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Total studios attempted:  {len(targets)}")
    print(f"  Successful:               {results['success']}")
    print(f"  Failed:                    {results['failed']}")
    print(f"  Total classes extracted:   {results['total_classes']}")
    print()

    if details:
        print("  Details:")
        for d in details:
            status_icon = "OK" if d["status"] == "OK" else "FAIL"
            classes_info = f"{d['classes']} classes" if d["status"] == "OK" else (d.get("error") or "unknown error")[:50]
            print(f"    [{status_icon:4s}] {d['studio']:<40s} {classes_info}")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
