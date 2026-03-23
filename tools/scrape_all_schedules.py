#!/usr/bin/env python3
"""
Full schedule scrape for ALL studios across ALL cantons.
Reads studio files, scrapes using the appropriate method per platform,
and updates schedule files with verified data.
"""

import json
import sys
import os
import time
import glob
import re
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scrapers.scrape_all import (
    scrape_eversports_widget_api,
    scrape_wix_bookings,
    scrape_sportsnow_schedule,
    scrape_schedule_classes,
    update_schedule_for_studio,
    logger,
)

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

DATA_DIR = PROJECT_ROOT / 'data'
RATE_LIMIT = 2  # seconds between studios


def load_studios_and_schedules():
    """Load all studio and schedule files."""
    studios_by_canton = {}
    schedules_by_canton = {}

    # Load studio files
    for fpath in sorted(glob.glob(str(DATA_DIR / 'studios_*.json'))):
        if fpath.endswith('.enc.json'):
            continue
        canton = Path(fpath).stem.replace('studios_', '')
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        studios_by_canton[canton] = (fpath, data)

    # Load schedule files
    for fpath in sorted(glob.glob(str(DATA_DIR / 'schedule_*.json'))):
        if fpath.endswith('.enc.json'):
            continue
        canton = Path(fpath).stem.replace('schedule_', '')
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        schedules_by_canton[canton] = (fpath, data)

    return studios_by_canton, schedules_by_canton


def determine_scraper(studio):
    """Determine which scraper to use based on booking_platform and URLs."""
    platform = (studio.get('booking_platform', '') or '').lower()
    schedule_url = studio.get('schedule_url', '')

    if platform == 'eversports' or 'eversports.ch/s/' in schedule_url:
        return 'eversports'
    if platform == 'sportsnow':
        return 'sportsnow'

    # Check if it's a Wix site (will be tested dynamically)
    return 'auto'


def scrape_studio(studio, method):
    """Scrape a single studio using the specified method."""
    if method == 'eversports':
        return scrape_eversports_widget_api(studio)
    elif method == 'sportsnow':
        return scrape_sportsnow_schedule(studio)
    elif method == 'wix':
        return scrape_wix_bookings(studio)
    elif method == 'auto':
        # Try Wix first (quick check via dynamic model), then generic HTML
        result = scrape_wix_bookings(studio)
        if result:
            return result
        # Fall back to generic HTML scraping
        schedule_url = studio.get('schedule_url', '')
        if schedule_url:
            return scrape_schedule_classes(studio, schedule_url) or None
    elif method == 'html':
        schedule_url = studio.get('schedule_url', '')
        if schedule_url:
            return scrape_schedule_classes(studio, schedule_url) or None
    return None


def main():
    print("=" * 60)
    print("FULL SCHEDULE SCRAPE - ALL CANTONS")
    print("=" * 60)

    studios_by_canton, schedules_by_canton = load_studios_and_schedules()
    print(f"Loaded {len(studios_by_canton)} canton studio files")
    print(f"Loaded {len(schedules_by_canton)} canton schedule files")

    # Statistics
    total_studios = 0
    total_active = 0
    total_scraped = 0
    total_classes = 0
    total_errors = 0
    platform_stats = {}
    canton_stats = {}

    for canton, (studio_path, studio_data) in sorted(studios_by_canton.items()):
        studios = studio_data.get('studios', [])
        active_studios = [s for s in studios if s.get('active', True)]

        if canton in schedules_by_canton:
            sched_path, sched_data = schedules_by_canton[canton]
        else:
            sched_path = str(DATA_DIR / f'schedule_{canton}.json')
            sched_data = {'classes': []}
            schedules_by_canton[canton] = (sched_path, sched_data)

        canton_classes = 0
        canton_scraped = 0

        for studio in active_studios:
            total_studios += 1
            total_active += 1
            studio_name = studio.get('name', 'Unknown')
            studio_id = studio.get('id', studio_name)

            method = determine_scraper(studio)

            try:
                classes = scrape_studio(studio, method)

                if classes:
                    # Track which method actually worked
                    actual_method = method
                    platform_stats[actual_method] = platform_stats.get(actual_method, 0) + 1

                    schedule_url = studio.get('schedule_url', '') or studio.get('website', '')
                    source = classes[0].get('source', schedule_url) if classes else schedule_url
                    update_schedule_for_studio(sched_data, studio, classes, source, verified=True)

                    total_scraped += 1
                    total_classes += len(classes)
                    canton_classes += len(classes)
                    canton_scraped += 1
                    print(f"  {studio_name} [{method}]: {len(classes)} classes")
                else:
                    update_schedule_for_studio(sched_data, studio, [],
                                               studio.get('schedule_url', ''), verified=False)

            except Exception as e:
                total_errors += 1
                logger.error(f"Error scraping {studio_name}: {e}")

            time.sleep(RATE_LIMIT)

        canton_stats[canton] = {'scraped': canton_scraped, 'classes': canton_classes, 'total': len(active_studios)}

        # Update schedule file metadata
        sched_data['last_updated'] = datetime.now(timezone.utc).isoformat()
        sched_data['_meta'] = {
            'last_updated': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            'note': 'Stundenplan-Daten aus oeffentlichen Quellen. Fuer aktuelle Zeiten siehe Studio-Website.',
        }

    # Save all schedule files
    print("\n" + "=" * 60)
    print("SAVING SCHEDULE FILES")
    print("=" * 60)

    for canton, (sched_path, sched_data) in schedules_by_canton.items():
        class_count = len(sched_data.get('classes', []))
        verified_count = len([c for c in sched_data.get('classes', []) if c.get('verified')])
        with open(sched_path, 'w', encoding='utf-8') as f:
            json.dump(sched_data, f, ensure_ascii=False, indent=2)
            f.write('\n')
        print(f"  {canton}: {class_count} classes ({verified_count} verified)")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total studios processed: {total_active}")
    print(f"Studios with scraped schedules: {total_scraped}")
    print(f"Total classes found: {total_classes}")
    print(f"Errors: {total_errors}")

    print("\nBy platform:")
    for platform, count in sorted(platform_stats.items()):
        print(f"  {platform}: {count} studios")

    print("\nBy canton (top results):")
    for canton, stats in sorted(canton_stats.items(), key=lambda x: x[1]['classes'], reverse=True):
        if stats['classes'] > 0:
            print(f"  {canton}: {stats['scraped']}/{stats['total']} studios, {stats['classes']} classes")

    return 0


if __name__ == '__main__':
    sys.exit(main())
