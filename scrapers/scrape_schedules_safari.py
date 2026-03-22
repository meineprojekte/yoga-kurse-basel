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
    try {
        // --- Eversports ---
        var evCells = document.querySelectorAll(
            '.ev-event-cell, .ev-session, [class*="EventCell"], [class*="event-cell"], '
            + '[class*="SessionCard"], [class*="session-card"], [data-testid*="event"], '
            + '[class*="schedule-event"], [class*="timetable"] [class*="event"]'
        );
        if (evCells.length > 0) {
            results.platform = 'Eversports';
            evCells.forEach(function(cell) {
                var text = cell.innerText || cell.textContent || '';
                var lines = text.split('\n').map(function(l){return l.trim()}).filter(Boolean);
                var timeMatch = text.match(/(\d{1,2}[:.]\d{2})\s*[-–]\s*(\d{1,2}[:.]\d{2})/);
                var timeStart = timeMatch ? timeMatch[1].replace('.', ':') : '';
                var timeEnd = timeMatch ? timeMatch[2].replace('.', ':') : '';
                // Try single time if no range found
                if (!timeStart) {
                    var singleTime = text.match(/(\d{1,2}[:.]\d{2})/);
                    if (singleTime) timeStart = singleTime[1].replace('.', ':');
                }
                var className = '';
                var teacher = '';
                // First non-time, non-empty line is usually the class name
                for (var i = 0; i < lines.length; i++) {
                    if (!lines[i].match(/^\d{1,2}[:.]\d{2}/) && lines[i].length > 2) {
                        if (!className) className = lines[i];
                        else if (!teacher && lines[i] !== className) {
                            teacher = lines[i];
                            break;
                        }
                    }
                }
                if (className || timeStart) {
                    results.classes.push({
                        class_name: className,
                        time_start: timeStart,
                        time_end: timeEnd,
                        teacher: teacher,
                        day: '',
                        level: 'all',
                        raw: text.substring(0, 200)
                    });
                }
            });
        }

        // --- Eversports table/grid view (day columns) ---
        if (results.classes.length === 0) {
            var dayHeaders = document.querySelectorAll(
                '[class*="DayHeader"], [class*="day-header"], '
                + '[class*="weekday"], th[class*="day"]'
            );
            if (dayHeaders.length > 0) {
                results.platform = 'Eversports';
                var dayNames = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
                var deDays = {'Mo':'Monday','Di':'Tuesday','Mi':'Wednesday','Do':'Thursday',
                              'Fr':'Friday','Sa':'Saturday','So':'Sunday',
                              'Montag':'Monday','Dienstag':'Tuesday','Mittwoch':'Wednesday',
                              'Donnerstag':'Thursday','Freitag':'Friday','Samstag':'Saturday',
                              'Sonntag':'Sunday'};
                dayHeaders.forEach(function(header, idx) {
                    var dayText = (header.innerText || '').trim();
                    var day = deDays[dayText] || dayText;
                    // Find events in the same column
                    var col = header.closest('[class*="column"], [class*="col"]');
                    if (col) {
                        var events = col.querySelectorAll('[class*="event"], [class*="session"]');
                        events.forEach(function(ev) {
                            var t = ev.innerText || '';
                            var tm = t.match(/(\d{1,2}[:.]\d{2})\s*[-–]?\s*(\d{1,2}[:.]\d{2})?/);
                            var lines = t.split('\n').map(function(l){return l.trim()}).filter(Boolean);
                            var cn = '';
                            for (var i=0;i<lines.length;i++) {
                                if (!lines[i].match(/^\d/) && lines[i].length > 2) { cn = lines[i]; break; }
                            }
                            results.classes.push({
                                class_name: cn,
                                time_start: tm ? tm[1].replace('.',':') : '',
                                time_end: tm && tm[2] ? tm[2].replace('.',':') : '',
                                teacher: '',
                                day: day,
                                level: 'all',
                                raw: t.substring(0,200)
                            });
                        });
                    }
                });
            }
        }

        // --- MindBody ---
        if (results.classes.length === 0) {
            var mbSessions = document.querySelectorAll(
                '.bw-session, .bw-widget__class, [class*="mindbody"] [class*="session"], '
                + '[class*="healcode"] [class*="session"]'
            );
            if (mbSessions.length > 0) {
                results.platform = 'MindBody';
                mbSessions.forEach(function(s) {
                    var text = s.innerText || '';
                    var tm = text.match(/(\d{1,2}[:.]\d{2}\s*(?:AM|PM)?)\s*[-–]\s*(\d{1,2}[:.]\d{2}\s*(?:AM|PM)?)/i);
                    var lines = text.split('\n').map(function(l){return l.trim()}).filter(Boolean);
                    results.classes.push({
                        class_name: lines[0] || '',
                        time_start: tm ? tm[1] : '',
                        time_end: tm ? tm[2] : '',
                        teacher: lines.length > 1 ? lines[1] : '',
                        day: '',
                        level: 'all',
                        raw: text.substring(0,200)
                    });
                });
            }
        }

        // --- SportsNow ---
        if (results.classes.length === 0) {
            var snSessions = document.querySelectorAll(
                '.sn-schedule, .sn-session, [class*="sportsnow"] [class*="event"]'
            );
            if (snSessions.length > 0) {
                results.platform = 'SportsNow';
                snSessions.forEach(function(s) {
                    var text = s.innerText || '';
                    var tm = text.match(/(\d{1,2}[:.]\d{2})\s*[-–]\s*(\d{1,2}[:.]\d{2})/);
                    var lines = text.split('\n').map(function(l){return l.trim()}).filter(Boolean);
                    results.classes.push({
                        class_name: lines[0] || '',
                        time_start: tm ? tm[1].replace('.',':') : '',
                        time_end: tm ? tm[2].replace('.',':') : '',
                        teacher: '',
                        day: '',
                        level: 'all',
                        raw: text.substring(0,200)
                    });
                });
            }
        }

        // --- Generic: tables with time patterns ---
        if (results.classes.length === 0) {
            results.platform = 'generic';
            var deDays = {'Montag':'Monday','Dienstag':'Tuesday','Mittwoch':'Wednesday',
                          'Donnerstag':'Thursday','Freitag':'Friday','Samstag':'Saturday',
                          'Sonntag':'Sunday','Mo':'Monday','Di':'Tuesday','Mi':'Wednesday',
                          'Do':'Thursday','Fr':'Friday','Sa':'Saturday','So':'Sunday'};
            var dayPattern = /\b(Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b/gi;

            // Try table rows
            var rows = document.querySelectorAll('table tr, .schedule-row, [class*="schedule"] tr');
            rows.forEach(function(row) {
                var text = row.innerText || '';
                var tm = text.match(/(\d{1,2}[:.]\d{2})\s*[-–]?\s*(\d{1,2}[:.]\d{2})?/);
                if (tm) {
                    var dayMatch = text.match(dayPattern);
                    var cells = row.querySelectorAll('td, th');
                    var cellTexts = Array.from(cells).map(function(c){return c.innerText.trim()});
                    var cn = '';
                    for (var i=0;i<cellTexts.length;i++) {
                        if (cellTexts[i].length > 3 && !cellTexts[i].match(/^\d{1,2}[:.]\d{2}/) &&
                            !cellTexts[i].match(dayPattern)) {
                            cn = cellTexts[i]; break;
                        }
                    }
                    results.classes.push({
                        class_name: cn,
                        time_start: tm[1].replace('.',':'),
                        time_end: tm[2] ? tm[2].replace('.',':') : '',
                        teacher: '',
                        day: dayMatch ? (deDays[dayMatch[0]] || dayMatch[0]) : '',
                        level: 'all',
                        raw: text.substring(0,200)
                    });
                }
            });

            // Try lists / divs with times
            if (results.classes.length === 0) {
                var allElements = document.querySelectorAll('li, div, p, span');
                var seen = new Set();
                allElements.forEach(function(el) {
                    if (el.children.length > 3) return; // skip containers
                    var text = (el.innerText || '').trim();
                    if (text.length < 8 || text.length > 300) return;
                    if (seen.has(text)) return;
                    var tm = text.match(/(\d{1,2}[:.]\d{2})\s*[-–]?\s*(\d{1,2}[:.]\d{2})?/);
                    if (tm) {
                        seen.add(text);
                        var dayMatch = text.match(dayPattern);
                        var parts = text.split(/\s{2,}|\t|\n|[|·•]/).map(function(p){return p.trim()}).filter(Boolean);
                        var cn = '';
                        for (var i=0;i<parts.length;i++) {
                            if (parts[i].length > 3 && !parts[i].match(/^\d{1,2}[:.]\d{2}/) &&
                                !parts[i].match(dayPattern)) {
                                cn = parts[i]; break;
                            }
                        }
                        if (cn) {
                            results.classes.push({
                                class_name: cn,
                                time_start: tm[1].replace('.',':'),
                                time_end: tm[2] ? tm[2].replace('.',':') : '',
                                teacher: '',
                                day: dayMatch ? (deDays[dayMatch[0]] || dayMatch[0]) : '',
                                level: 'all',
                                raw: text.substring(0,200)
                            });
                        }
                    }
                });
            }
        }

        // Deduplicate by class_name + time_start + day
        var unique = {};
        results.classes = results.classes.filter(function(c) {
            var key = c.class_name + '|' + c.time_start + '|' + c.day;
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

def scrape_studio(target):
    """
    Scrape a single studio's schedule via Safari.
    Returns dict with keys: success, classes, platform, error
    """
    url = target["schedule_url"]
    is_eversports = "eversports" in url.lower()
    log.info(f"  Opening: {url}")

    try:
        safari_open_url(url)

        # Wait for initial page load
        loaded = safari_wait_for_load(timeout_seconds=15)
        if not loaded:
            log.warning(f"  Page did not finish loading within 15s")

        # Accept cookies / dismiss consent banners
        cookie_js = r"""
        (function() {
            // Common cookie consent button selectors
            var selectors = [
                '[id*="accept" i]', '[id*="cookie" i] button', '[id*="consent" i] button',
                '[class*="accept" i]', '[class*="cookie-accept" i]', '[class*="consent-accept" i]',
                'button[class*="agree" i]', 'a[class*="agree" i]',
                '[data-testid*="accept" i]', '[data-action*="accept" i]',
                '.cc-accept', '.cc-allow', '.cc-dismiss',
                '#onetrust-accept-btn-handler', '.onetrust-accept-btn-handler',
                '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
                '#cookie-accept', '#accept-cookies', '#acceptAllCookies',
                '.cookie-consent-accept', '.js-cookie-accept',
                '[aria-label*="accept" i]', '[aria-label*="akzeptieren" i]',
                '[aria-label*="accepter" i]', '[aria-label*="accetta" i]',
                'button[title*="accept" i]', 'button[title*="akzeptieren" i]',
                '.gdpr-accept', '#gdpr-accept',
                // German-specific
                'button:not([disabled])', 'a.btn'
            ];
            var clicked = false;
            for (var i = 0; i < selectors.length - 2; i++) {
                var btns = document.querySelectorAll(selectors[i]);
                for (var j = 0; j < btns.length; j++) {
                    var txt = (btns[j].textContent || '').toLowerCase().trim();
                    if (txt.match(/^(accept|akzeptieren|accepter|accetta|ok|alle akzeptieren|accept all|tout accepter|accetta tutti|einverstanden|zustimmen|allow|erlauben|got it|verstanden|alles klar)$/i)) {
                        btns[j].click();
                        clicked = true;
                        break;
                    }
                }
                if (clicked) break;
            }
            // Also try removing overlay/modal blockers
            var overlays = document.querySelectorAll('[class*="cookie-overlay"], [class*="consent-overlay"], [id*="cookie-banner"], [class*="cookie-banner"], .cc-banner, #onetrust-banner-sdk');
            overlays.forEach(function(el) { el.style.display = 'none'; });
            var body = document.body;
            if (body) { body.style.overflow = 'auto'; body.classList.remove('no-scroll', 'modal-open'); }
            return clicked ? 'clicked' : 'no-banner';
        })();
        """
        cookie_result = safari_execute_js(cookie_js, timeout=5)
        if cookie_result and 'clicked' in cookie_result:
            log.info("  Cookie banner accepted automatically")
            time.sleep(1)  # Wait for banner to dismiss

        # Extra wait for JS-heavy pages (Eversports, etc.)
        wait_time = 10 if is_eversports else 5
        log.info(f"  Waiting {wait_time}s for JS rendering...")
        time.sleep(wait_time)

        # Execute extraction JavaScript
        raw_result = safari_execute_js(EXTRACTION_JS, timeout=15)

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
        platform = result.get("platform", "unknown")
        error = result.get("error")

        if error:
            log.warning(f"  JS error: {error}")

        return {
            "success": len(classes) > 0,
            "classes": classes,
            "platform": platform,
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
