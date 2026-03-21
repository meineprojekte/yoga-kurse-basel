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


PRICE_PAGE_PATHS = ['/preise', '/prices', '/pricing', '/tarife', '/prix', '/angebot']

# Regex to find CHF amounts
CHF_PATTERN = re.compile(r'CHF\s*(\d+[\.,]?\d*)', re.IGNORECASE)

# Keywords that help classify a price (German, French, English)
PRICE_KEYWORDS = {
    'single': ['einzeleintritt', 'einzellektion', 'drop-in', 'drop in', 'single class',
               'cours unique', 'einzelstunde', 'einzelkurs'],
    'card_10': ['10er', '10-er', '10 er', '10 lektionen', '10 classes', '10 cours',
                '10er-abo', '10er abo', '10er-karte'],
    'monthly': ['monats', 'monatlich', 'monthly', 'mensuel', 'monatsabo', 'month'],
    'trial': ['probestunde', 'probelektion', 'schnuppern', 'trial', 'cours d\'essai',
              'probetraining', 'first class', 'erste stunde'],
    'abo': ['abo', 'abonnement', 'subscription', 'mitgliedschaft', 'membership'],
}


def scrape_prices(studio):
    """
    Attempt to scrape pricing information from a studio's website.

    Tries the main website and common price page paths. Looks for CHF amounts
    near pricing keywords and returns a structured pricing dict.

    Args:
        studio: dict with 'website' and optionally 'schedule_url' fields.

    Returns:
        A pricing dict with verified=True if prices found, None otherwise.
    """
    website = studio.get('website', '')
    if not website:
        return None

    base_url = website.rstrip('/')

    # Check robots.txt once for the domain
    domain_url = '/'.join(base_url.split('/')[:3])
    if not check_robots_txt(domain_url):
        logger.info(f"  Price scraping blocked by robots.txt: {domain_url}")
        return None

    # Build list of URLs to try: main site + common price page paths
    urls_to_try = [base_url]
    for path in PRICE_PAGE_PATHS:
        urls_to_try.append(base_url + path)

    all_prices = {}
    source_url = None

    for url in urls_to_try:
        html = fetch_page(url, timeout=10)
        if not html:
            continue

        soup = BeautifulSoup(html, 'lxml')
        text_content = soup.get_text(separator=' ', strip=True).lower()

        # Find all CHF amounts on the page
        chf_matches = CHF_PATTERN.findall(text_content)
        if not chf_matches:
            continue

        # For each price keyword category, search for nearby CHF values
        page_prices = _extract_prices_from_soup(soup)
        if page_prices:
            all_prices.update(page_prices)
            source_url = url
            logger.info(f"  Found {len(page_prices)} price(s) at {url}")
            # If we found prices on a dedicated price page, prefer that and stop
            if any(path in url for path in PRICE_PAGE_PATHS):
                break

    if not all_prices:
        return None

    pricing = {
        'currency': 'CHF',
        'verified': True,
        'source': source_url,
        'last_checked': datetime.now(timezone.utc).isoformat(),
    }
    pricing.update(all_prices)
    return pricing


def _extract_prices_from_soup(soup):
    """
    Extract categorized prices from a BeautifulSoup document.

    Looks at text blocks containing CHF amounts and checks surrounding text
    for pricing keywords to classify each price.

    Returns:
        dict with keys like 'single', 'card_10', 'monthly', 'trial' mapped to float values.
    """
    prices = {}

    # Get all text nodes that contain CHF
    body = soup.find('body')
    if not body:
        return prices

    # Walk through elements looking for CHF patterns in context
    for element in body.find_all(string=CHF_PATTERN):
        # Get surrounding context: parent and siblings text
        parent = element.parent
        if not parent:
            continue

        # Build context from the parent element and its parent
        context_parts = []
        grandparent = parent.parent if parent.parent else parent
        context_text = grandparent.get_text(separator=' ', strip=True).lower()
        context_parts.append(context_text)
        context = ' '.join(context_parts)

        # Find CHF amounts in this element
        amounts = CHF_PATTERN.findall(element)

        for amount_str in amounts:
            try:
                amount = float(amount_str.replace(',', '.'))
            except ValueError:
                continue

            # Skip unreasonable prices (< 5 or > 500 CHF)
            if amount < 5 or amount > 500:
                continue

            # Classify this price based on nearby keywords
            for category, keywords in PRICE_KEYWORDS.items():
                if any(kw in context for kw in keywords):
                    # For 'abo' category, only store if we don't have more specific ones
                    if category == 'abo' and any(k in prices for k in ['monthly', 'card_10']):
                        continue
                    prices[category] = amount
                    break

    return prices


def update_studio_data(studios_data):
    """Run scrapers for all active studios and update the data."""
    updated_count = 0
    error_count = 0
    prices_found = 0

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

        # --- Price scraping ---
        try:
            new_pricing = scrape_prices(studio)
            existing_pricing = studio.get('pricing', {})

            if new_pricing and new_pricing.get('verified'):
                # Merge: keep existing fields not in new data, update the rest
                merged = dict(existing_pricing)
                merged.update(new_pricing)
                studio['pricing'] = merged
                prices_found += 1
                logger.info(f"  Updated pricing for {studio_name}: {new_pricing}")
            elif not new_pricing:
                # No prices found; update last_checked but don't clear existing data
                if existing_pricing:
                    existing_pricing['last_checked'] = datetime.now(timezone.utc).isoformat()
                logger.debug(f"  No pricing found for {studio_name}")
        except Exception as e:
            logger.error(f"Error scraping prices for {studio_name}: {e}")

    logger.info(f"Price scraping summary: {prices_found} studios with new/updated prices")
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
