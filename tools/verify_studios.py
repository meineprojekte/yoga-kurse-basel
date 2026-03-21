#!/usr/bin/env python3
"""
Verify that all studio websites in the database are reachable.
Reads studios_*.json files, checks each active studio's website via HEAD request,
and reports problematic entries (404s, connection errors, suspicious redirects).

Does NOT modify any data files.
"""

import json
import glob
import os
import sys
import time
from urllib.parse import urlparse
from datetime import datetime

try:
    import requests
except ImportError:
    print("Installing requests...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests


DATA_DIR = "/Users/andrea/ClaudeWork/JogaKurseBasel/data"
REPORT_PATH = "/Users/andrea/ClaudeWork/JogaKurseBasel/tools/studio_verification_report.txt"
TIMEOUT = 10  # seconds
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) YogaBaselBot/1.0"


def get_base_domain(url):
    """Extract the base domain (e.g. 'byoga.ch') from a URL."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    # Strip www. prefix for comparison
    if host.startswith("www."):
        host = host[4:]
    return host


def check_url(url):
    """
    Check a URL via HEAD request. Returns a dict with:
      status, final_url, error, redirect_domain_changed
    """
    result = {
        "status": None,
        "final_url": None,
        "error": None,
        "redirect_domain_changed": False,
    }
    try:
        resp = requests.head(
            url,
            timeout=TIMEOUT,
            allow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )
        result["status"] = resp.status_code
        result["final_url"] = resp.url

        # Check if redirected to a completely different domain
        original_domain = get_base_domain(url)
        final_domain = get_base_domain(resp.url)
        if original_domain and final_domain and original_domain != final_domain:
            result["redirect_domain_changed"] = True

    except requests.exceptions.SSLError as e:
        result["error"] = f"SSL error: {e}"
    except requests.exceptions.ConnectionError as e:
        result["error"] = f"Connection error: {e}"
    except requests.exceptions.Timeout:
        result["error"] = "Timeout (>10s)"
    except requests.exceptions.TooManyRedirects:
        result["error"] = "Too many redirects"
    except requests.exceptions.RequestException as e:
        result["error"] = f"Request error: {e}"

    return result


def main():
    # Find all non-encrypted studio JSON files
    pattern = os.path.join(DATA_DIR, "studios_*.json")
    all_files = sorted(glob.glob(pattern))
    json_files = [f for f in all_files if not f.endswith(".enc.json")]

    print(f"Found {len(json_files)} studio data files to check.\n")

    problems = []       # list of dicts describing issues
    ok_count = 0
    skipped_count = 0
    total_studios = 0

    for filepath in json_files:
        canton = os.path.basename(filepath).replace("studios_", "").replace(".json", "")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        studios = data.get("studios", [])
        for studio in studios:
            total_studios += 1
            name = studio.get("name", "(unknown)")
            active = studio.get("active", True)
            website = studio.get("website", "")

            if not active:
                skipped_count += 1
                continue

            if not website:
                skipped_count += 1
                continue

            print(f"  Checking: {name} ({canton}) -> {website} ... ", end="", flush=True)
            result = check_url(website)

            if result["error"]:
                tag = "CONNECTION_ERROR"
                print(f"ERROR")
                problems.append({
                    "canton": canton,
                    "name": name,
                    "website": website,
                    "issue": tag,
                    "detail": result["error"],
                })
            elif result["status"] == 404:
                tag = "404_NOT_FOUND"
                print(f"404")
                problems.append({
                    "canton": canton,
                    "name": name,
                    "website": website,
                    "issue": tag,
                    "detail": f"HTTP 404 - page not found",
                })
            elif result["status"] and result["status"] >= 400:
                tag = f"HTTP_{result['status']}"
                print(f"{result['status']}")
                problems.append({
                    "canton": canton,
                    "name": name,
                    "website": website,
                    "issue": tag,
                    "detail": f"HTTP {result['status']}",
                })
            elif result["redirect_domain_changed"]:
                tag = "DOMAIN_REDIRECT"
                print(f"REDIRECT -> {get_base_domain(result['final_url'])}")
                problems.append({
                    "canton": canton,
                    "name": name,
                    "website": website,
                    "issue": tag,
                    "detail": f"Redirects to different domain: {result['final_url']}",
                })
            else:
                ok_count += 1
                print(f"OK ({result['status']})")

    # Build report
    report_lines = []
    report_lines.append("=" * 72)
    report_lines.append("STUDIO WEBSITE VERIFICATION REPORT")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 72)
    report_lines.append("")
    report_lines.append(f"Total studios in database:  {total_studios}")
    report_lines.append(f"Checked (active + has URL): {ok_count + len(problems)}")
    report_lines.append(f"Skipped (inactive/no URL):  {skipped_count}")
    report_lines.append(f"OK:                         {ok_count}")
    report_lines.append(f"Problems found:             {len(problems)}")
    report_lines.append("")

    if problems:
        report_lines.append("-" * 72)
        report_lines.append("PROBLEMATIC STUDIOS")
        report_lines.append("-" * 72)

        # Group by issue type
        by_type = {}
        for p in problems:
            by_type.setdefault(p["issue"], []).append(p)

        for issue_type, entries in sorted(by_type.items()):
            report_lines.append("")
            report_lines.append(f"### {issue_type} ({len(entries)} studios)")
            report_lines.append("")
            for e in entries:
                report_lines.append(f"  Canton:  {e['canton']}")
                report_lines.append(f"  Studio:  {e['name']}")
                report_lines.append(f"  URL:     {e['website']}")
                report_lines.append(f"  Detail:  {e['detail']}")
                report_lines.append("")
    else:
        report_lines.append("All studio websites are reachable. No issues found.")

    report_lines.append("=" * 72)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 72)

    report_text = "\n".join(report_lines)

    # Print report
    print("\n")
    print(report_text)

    # Save report
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text + "\n")
    print(f"\nReport saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
