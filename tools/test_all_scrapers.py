#!/usr/bin/env python3
"""
Test script for all scraper methods: Eversports, Wix, SportsNow.
Tests a few representative studios per platform.
"""

import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scrapers.scrape_all import (
    scrape_eversports_widget_api,
    scrape_wix_bookings,
    scrape_sportsnow_schedule,
    logger,
)

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


def test_eversports():
    """Test Eversports scraping on 3 studios."""
    print("\n" + "=" * 60)
    print("TESTING EVERSPORTS WIDGET API")
    print("=" * 60)

    test_studios = [
        {
            'id': 'planet-yoga',
            'name': 'Planet Yoga',
            'schedule_url': 'https://www.eversports.ch/s/planet-yoga',
            'booking_platform': 'Eversports',
        },
        {
            'id': 'yoga-am-zuerichberg',
            'name': 'Yoga am Zuerichberg',
            'schedule_url': 'https://www.eversports.ch/s/yoga-am-zuerichberg',
            'booking_platform': 'Eversports',
        },
        {
            'id': 'aloha-yoga',
            'name': 'Aloha Yoga',
            'schedule_url': 'https://www.eversports.ch/s/aloha-yoga',
            'booking_platform': 'Eversports',
        },
    ]

    results = {}
    for studio in test_studios:
        print(f"\n--- Testing: {studio['name']} ---")
        try:
            classes = scrape_eversports_widget_api(studio)
            count = len(classes) if classes else 0
            results[studio['id']] = count
            print(f"  Result: {count} classes found")
            if classes:
                for c in classes[:3]:
                    print(f"    {c['day']} {c['time_start']}-{c['time_end']} "
                          f"{c['class_name']} ({c.get('teacher', 'N/A')})")
                if count > 3:
                    print(f"    ... and {count - 3} more")
        except Exception as e:
            results[studio['id']] = f"ERROR: {e}"
            print(f"  ERROR: {e}")

    return results


def test_wix():
    """Test Wix Bookings API on 2 studios."""
    print("\n" + "=" * 60)
    print("TESTING WIX BOOKINGS API")
    print("=" * 60)

    test_studios = [
        {
            'id': 'yamabern',
            'name': 'Yama Bern',
            'website': 'https://www.yamabern.ch',
            'schedule_url': 'https://www.yamabern.ch/stundenplan',
            'booking_platform': 'Wix',
        },
        {
            'id': 'yogart-bern',
            'name': 'YogArt Bern',
            'website': 'https://www.yogart.ch',
            'schedule_url': 'https://www.yogart.ch/stundenplan',
            'booking_platform': 'Wix',
        },
    ]

    results = {}
    for studio in test_studios:
        print(f"\n--- Testing: {studio['name']} ---")
        try:
            classes = scrape_wix_bookings(studio)
            count = len(classes) if classes else 0
            results[studio['id']] = count
            print(f"  Result: {count} classes found")
            if classes:
                for c in classes[:3]:
                    print(f"    {c['day']} {c['time_start']}-{c['time_end']} "
                          f"{c['class_name']} ({c.get('teacher', 'N/A')})")
                if count > 3:
                    print(f"    ... and {count - 3} more")
        except Exception as e:
            results[studio['id']] = f"ERROR: {e}"
            print(f"  ERROR: {e}")

    return results


def test_sportsnow():
    """Test SportsNow scraping on 1 studio."""
    print("\n" + "=" * 60)
    print("TESTING SPORTSNOW")
    print("=" * 60)

    test_studios = [
        {
            'id': 'ayana-yoga-schaffhausen',
            'name': 'Ayana Yoga Schaffhausen',
            'website': 'https://www.ayana-yoga.ch',
            'schedule_url': 'https://www.ayana-yoga.ch/stundenplan',
            'booking_platform': 'SportsNow',
            'sportsnow_slug': 'ayana-yoga',
        },
    ]

    results = {}
    for studio in test_studios:
        print(f"\n--- Testing: {studio['name']} ---")
        try:
            classes = scrape_sportsnow_schedule(studio)
            count = len(classes) if classes else 0
            results[studio['id']] = count
            print(f"  Result: {count} classes found")
            if classes:
                for c in classes[:3]:
                    print(f"    {c['day']} {c['time_start']}-{c['time_end']} "
                          f"{c['class_name']} ({c.get('teacher', 'N/A')})")
                if count > 3:
                    print(f"    ... and {count - 3} more")
        except Exception as e:
            results[studio['id']] = f"ERROR: {e}"
            print(f"  ERROR: {e}")

    return results


def main():
    print("=" * 60)
    print("COMPREHENSIVE SCRAPER TEST")
    print("=" * 60)

    all_results = {}

    ev_results = test_eversports()
    all_results['eversports'] = ev_results

    wix_results = test_wix()
    all_results['wix'] = wix_results

    sn_results = test_sportsnow()
    all_results['sportsnow'] = sn_results

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total_classes = 0
    total_success = 0
    total_fail = 0

    for platform, results in all_results.items():
        print(f"\n{platform.upper()}:")
        for studio_id, count in results.items():
            if isinstance(count, int):
                status = f"{count} classes" if count > 0 else "0 classes (no data)"
                total_classes += count
                if count > 0:
                    total_success += 1
                else:
                    total_fail += 1
            else:
                status = str(count)
                total_fail += 1
            print(f"  {studio_id}: {status}")

    print(f"\nTotal: {total_success} succeeded, {total_fail} failed, {total_classes} classes found")
    return 0 if total_success > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
