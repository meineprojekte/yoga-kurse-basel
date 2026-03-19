#!/usr/bin/env python3
"""
Yoga Kurse Basel — Studio Schedule Scraper
Scrapes schedule data from Basel yoga studio websites and updates studios.json.
Designed to run via GitHub Actions 4 times daily.
"""

import json
import os
import sys
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('yoga-scraper')

DATA_DIR = Path(__file__).parent.parent / 'data'
STUDIOS_FILE = DATA_DIR / 'studios.json'

HEADERS = {
    'User-Agent': 'YogaKurseBasel/1.0 (https://yogakursebasel.ch; info aggregator)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'de-CH,de;q=0.9,en;q=0.8',
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def fetch_page(url, timeout=15):
    """Fetch a page, respecting robots.txt conventions."""
    try:
        resp = SESSION.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def check_robots_txt(base_url):
    """Check if scraping is allowed by robots.txt."""
    try:
        robots_url = base_url.rstrip('/') + '/robots.txt'
        resp = SESSION.get(robots_url, timeout=5)
        if resp.status_code == 200:
            content = resp.text.lower()
            # Basic check: if there's a blanket disallow for all user agents
            if 'disallow: /' in content and 'user-agent: *' in content:
                # Check if it's truly a blanket disallow
                lines = content.split('\n')
                user_agent_star = False
                for line in lines:
                    line = line.strip()
                    if line == 'user-agent: *':
                        user_agent_star = True
                    elif user_agent_star and line == 'disallow: /':
                        logger.info(f"Robots.txt disallows scraping: {base_url}")
                        return False
                    elif line.startswith('user-agent:'):
                        user_agent_star = False
        return True
    except requests.RequestException:
        return True  # If we can't fetch robots.txt, proceed cautiously


def scrape_eversports_widget(url):
    """Attempt to extract schedule info from pages using Eversports widgets."""
    html = fetch_page(url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'lxml')
    classes = []

    # Look for Eversports iframes or embedded schedules
    iframes = soup.find_all('iframe', src=re.compile(r'eversports', re.I))
    if iframes:
        logger.info(f"Found Eversports widget at {url}")
        # Note: Eversports content is loaded dynamically, we log it for reference
        for iframe in iframes:
            logger.info(f"  Eversports iframe: {iframe.get('src', '')}")

    return classes


def scrape_generic_schedule(studio):
    """Generic scraper that looks for schedule information on studio websites."""
    url = studio.get('schedule_url') or studio.get('website')
    if not url:
        return None

    # Check robots.txt
    base_url = '/'.join(url.split('/')[:3])
    if not check_robots_txt(base_url):
        return None

    html = fetch_page(url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'lxml')

    # Extract any visible class/schedule information
    schedule_data = {
        'last_scraped': datetime.now(timezone.utc).isoformat(),
        'source_url': url,
        'status': 'scraped'
    }

    # Look for common schedule patterns
    # Tables
    tables = soup.find_all('table')
    for table in tables:
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        schedule_keywords = ['montag', 'dienstag', 'mittwoch', 'donnerstag', 'freitag',
                           'samstag', 'sonntag', 'monday', 'tuesday', 'wednesday',
                           'thursday', 'friday', 'saturday', 'sunday',
                           'zeit', 'time', 'kurs', 'class', 'lehrer', 'teacher']
        if any(kw in ' '.join(headers).lower() for kw in schedule_keywords):
            schedule_data['has_schedule_table'] = True
            logger.info(f"  Found schedule table at {url}")

    # Check for booking platform links
    for platform in ['eversports', 'mindbody', 'momoyoga', 'fitogram', 'classpass']:
        links = soup.find_all('a', href=re.compile(platform, re.I))
        if links:
            schedule_data['booking_links'] = schedule_data.get('booking_links', [])
            for link in links:
                href = link.get('href', '')
                if href:
                    schedule_data['booking_links'].append({
                        'platform': platform,
                        'url': href
                    })

    return schedule_data


def update_studio_data(studios_data):
    """Run scrapers for all active studios and update the data."""
    updated_count = 0
    error_count = 0

    for studio in studios_data.get('studios', []):
        if not studio.get('active', True):
            continue

        studio_name = studio.get('name', 'Unknown')
        logger.info(f"Processing: {studio_name}")

        try:
            result = scrape_generic_schedule(studio)
            if result:
                studio['scrape_status'] = result.get('status', 'unknown')
                studio['last_scraped'] = result.get('last_scraped')
                if result.get('booking_links'):
                    studio['detected_booking_links'] = result['booking_links']
                updated_count += 1
            else:
                studio['scrape_status'] = 'no_data'
        except Exception as e:
            logger.error(f"Error scraping {studio_name}: {e}")
            studio['scrape_status'] = 'error'
            error_count += 1

    return updated_count, error_count


def main():
    logger.info("=" * 60)
    logger.info("Yoga Kurse Basel — Starting scrape run")
    logger.info("=" * 60)

    # Load existing data
    if not STUDIOS_FILE.exists():
        logger.error(f"Studios file not found: {STUDIOS_FILE}")
        sys.exit(1)

    with open(STUDIOS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Run scrapers
    updated, errors = update_studio_data(data)

    # Update timestamp
    data['last_updated'] = datetime.now(timezone.utc).isoformat()

    # Save updated data
    with open(STUDIOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("=" * 60)
    logger.info(f"Scrape complete: {updated} updated, {errors} errors")
    logger.info(f"Data saved to {STUDIOS_FILE}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
