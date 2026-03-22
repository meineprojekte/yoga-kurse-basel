#!/usr/bin/env python3
"""
Add source tracking fields to all schedule_*.json files.

For each class entry:
  - "source": the studio's schedule_url (from studios_*.json)
  - "verified": false
  - "last_checked": "2026-03-21"

Also adds a root-level "_meta" block to each schedule file.
"""

import json
import glob
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'
VERIFICATION_FILE = Path(__file__).parent / 'schedule_verification.json'

LAST_CHECKED = "2026-03-21"

META_BLOCK = {
    "last_updated": LAST_CHECKED,
    "note": "Stundenplan-Daten aus öffentlichen Quellen. Für aktuelle Zeiten siehe Studio-Website."
}


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def build_schedule_url_map():
    """
    Build a mapping of studio_id -> schedule_url from all studios_*.json files
    and the schedule_verification.json file.
    """
    url_map = {}

    # First, load from verification file (has studio_id as key)
    if VERIFICATION_FILE.exists():
        verification = load_json(VERIFICATION_FILE)
        for studio_id, info in verification.items():
            surl = info.get('schedule_url', '')
            if surl:
                url_map[studio_id] = surl

    # Then, load from studios_*.json files (may add more or override)
    for fpath in sorted(glob.glob(str(DATA_DIR / 'studios_*.json'))):
        if fpath.endswith('.enc.json'):
            continue
        data = load_json(fpath)
        for studio in data.get('studios', []):
            sid = studio.get('id', '')
            surl = studio.get('schedule_url', '')
            if sid and surl:
                url_map[sid] = surl

    return url_map


def update_schedule_file(fpath, url_map):
    """Add source tracking to a single schedule file."""
    data = load_json(fpath)

    # Add _meta at root level
    data['_meta'] = META_BLOCK

    classes = data.get('classes', [])
    updated = 0
    for entry in classes:
        studio_id = entry.get('studio_id', '')
        source_url = url_map.get(studio_id, '')
        entry['source'] = source_url
        entry['verified'] = False
        entry['last_checked'] = LAST_CHECKED
        updated += 1

    save_json(fpath, data)
    return updated


def main():
    url_map = build_schedule_url_map()
    print(f"Built URL map with {len(url_map)} studio(s)")

    schedule_files = sorted(glob.glob(str(DATA_DIR / 'schedule_*.json')))
    schedule_files = [f for f in schedule_files if not f.endswith('.enc.json')]

    total_classes = 0
    for fpath in schedule_files:
        canton = Path(fpath).stem.replace('schedule_', '')
        count = update_schedule_file(fpath, url_map)
        total_classes += count
        print(f"  {canton}: {count} classes updated")

    print(f"\nDone. {total_classes} class entries updated across {len(schedule_files)} files.")


if __name__ == '__main__':
    main()
