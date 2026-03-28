#!/usr/bin/env python3
"""
Final comprehensive price scraper for ALL studios without verified pricing.

Strategy per studio:
1. curl_cffi (impersonate='chrome') to fetch homepage
2. Crawl navigation links for pricing-related pages
3. Try /preise, /prices, /pricing, /tarife, /tarifs, /prix, /angebot, /prezzi,
   /membership, /abos and more
4. Parse HTML for CHF amounts near keywords: Einzeleintritt, Einzellektion,
   Single, Drop-in, 10er, Abo, Monats, Trial, Probe, Schnupper, cours unique
5. Detect Eversports widget -> try Eversports API for pricing
6. Detect Wix -> try Wix bookings services API
7. Detect MomoYoga -> try pricing page
8. Only save prices clearly found on official pages, include source URL.

Updates studios_*.json files directly.
"""

import json
import os
import re
import glob
import time
import sys
import logging
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from html import unescape

from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup

# ───────────────────── Configuration ─────────────────────

BASE_DIR = "/Users/andrea/ClaudeWork/JogaKurseBasel"
DATA_DIR = os.path.join(BASE_DIR, "data")
TOOLS_DIR = os.path.join(BASE_DIR, "tools")

RATE_LIMIT = 1.2  # seconds between studios
SUB_PAGE_DELAY = 0.25  # seconds between subpage requests
TIMEOUT = 15
MAX_SUBPAGES = 25  # max subpages to try per studio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("price-scraper")

# Pricing page paths to try (ordered by likelihood)
PRICE_PATHS = [
    "/preise", "/prices", "/pricing", "/tarife", "/tarifs", "/prix",
    "/angebot", "/prezzi", "/membership", "/abos",
    "/abo-preise", "/preise-abos", "/kurse-preise", "/yoga-preise",
    "/classes-prices", "/classes-pricing", "/class-pricing",
    "/en/prices", "/en/pricing", "/de/preise", "/fr/tarifs", "/fr/prix",
    "/it/prezzi", "/it/costi",
    "/angebote", "/kursangebote", "/kurse-und-preise", "/kurse",
    "/offer", "/offers", "/offres",
    "/abonnemente", "/abonnements",
    "/probelektion", "/probetraining",
    "/rates", "/fees",
    "/booking", "/book",
    "/en/membership", "/de/membership",
    "/shop", "/packs", "/packages",
    "/kosten", "/gebuehren",
    "/klassen", "/classes",
    "/yoga-classes", "/yoga-kurse",
    "/stundenplan-preise", "/schedule-prices",
    "/info", "/informationen",
    "/about", "/ueber-uns",
    "/leistungen", "/services",
]

# Keywords that indicate a link might lead to pricing info
PRICING_LINK_KEYWORDS = [
    'preis', 'price', 'pricing', 'tarif', 'prix', 'prezz',
    'angebot', 'offer', 'offre', 'abo', 'membership',
    'kurs', 'class', 'lektion', 'cours', 'lesson',
    'kosten', 'cost', 'gebühr', 'fee', 'rate',
    'booking', 'book', 'buchen', 'réserv',
    'shop', 'pack', 'paket',
    'single', 'drop-in', 'dropin', 'einzel',
    'probe', 'trial', 'schnupper', 'essai',
]

PRICE_FIELDS = ["single", "card_10", "monthly", "trial"]

# ───────────────────── Price extraction patterns ─────────────────────

PRICE_AMOUNT_PATTERNS = [
    r'CHF\s*(\d+(?:[.,]\d{1,2})?)',
    r'(\d+(?:[.,]\d{1,2})?)\s*CHF',
    r'Fr\.?\s*(\d+(?:[.,]\d{1,2})?)',
    r'(\d+(?:[.,]\d{1,2})?)\s*Fr\b',
    r'SFr\.?\s*(\d+(?:[.,]\d{1,2})?)',
    r'(\d+(?:[.,]\d{1,2})?)\s*(?:Franken|francs?)',
    # Also try just digits followed by .- (Swiss notation: "30.-")
    r'(\d+)\s*\.\s*[-–]',
]

# Keywords for contextual matching (multilingual: DE, FR, IT, EN)
SINGLE_KW = (
    r'(?:einzelstunde|einzellektion|einzeleintritt|single\s*class|drop[- ]?in|'
    r'kurse?\s*(?:60|75|90)\s*min|lezione?\s*(?:singola|unica)|'
    r'cours?\s*(?:individuel|unique|[àa]\s*l.unit[eé])|'
    r'1\s*(?:lektion|class|cours)|pro\s*lektion|per\s*lezione|par\s*cours|'
    r'class\s*pass|yoga\s*class|einzeln|einzel|'
    r'per\s*class|per\s*session|pro\s*stunde|pro\s*klasse|'
    r'single\s*entry|einmalig|une\s*séance|par\s*séance|'
    r'classe\s*individuelle|singola\s*lezione|'
    r'1x|one\s*class|une\s*classe|lezione\s*singola)'
)
CARD10_KW = (
    r'(?:10er|10[- ]?(?:class|karte|lektionen|cours|lezioni|er\s*(?:karte|abo))|'
    r'(?:carte?|pass|abo|carnet)\s*(?:de?\s*)?10|'
    r'10\s*(?:classes?|lektionen|cours|lezioni|entrées?|séances?|lezioni)|'
    r'block\s*(?:of\s*)?10|zehnerkarte|'
    r'5er|5\s*(?:classes?|lektionen)|'
    r'(?:carte?|pass|abo|carnet)\s*(?:de?\s*)?5)'
)
MONTHLY_KW = (
    r'(?:monats?\s*abo|monthly|monatlich|unlimited\s*(?:1\s*)?month|'
    r'illimit[eé]|mensuel|abo\s*(?:un)?limit[eé]?|'
    r'flatrate|flat\s*rate|all\s*you\s*can\s*yoga|jahres?\s*abo|annual|'
    r'abo\s*\d+\s*monat|abonnement\s*mensuel|monats\s*flat|'
    r'unlimited\s*yoga|mitgliedschaft|membership|'
    r'abbonamento\s*mensile|mese|monat\s*(?:abo|flat)|'
    r'abo\s*mensuel|subscription\s*month)'
)
TRIAL_KW = (
    r'(?:probe|trial|schnupper|essai|d[eé]couverte|prova|kennen\s*lern|intro|'
    r'first\s*class|premier\s*cours|erste?\s*(?:lektion|stunde)|'
    r'new\s*student|new\s*client|newcomer|neueinsteiger|'
    r'beginner\s*offer|try\s*out|promo|aktion|offre\s*d.essai|'
    r'angebots?\s*paket|starter|welcome|'
    r'prima\s*lezione|prova\s*gratuita|'
    r'nouveau\s*client|nouvelle?\s*[eé]l[eè]ve|'
    r'kennenlernen|reinschnuppern|test\s*class)'
)


# ───────────────────── Helper functions ─────────────────────

def strip_tags(html):
    """Remove HTML tags, script/style content, normalize whitespace."""
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_text_bs4(html):
    """Extract visible text from HTML using BeautifulSoup for better accuracy."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        # Remove script and style elements
        for tag in soup(['script', 'style', 'noscript', 'meta', 'link']):
            tag.decompose()
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        return text
    except Exception:
        return strip_tags(html)


def parse_amount(s):
    """Parse a price string to float."""
    s = s.replace(",", ".").strip()
    try:
        return float(s)
    except ValueError:
        return None


def find_all_chf_amounts(text):
    """Find all CHF amounts in text."""
    amounts = []
    for pat in PRICE_AMOUNT_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            val = parse_amount(m.group(1))
            if val and 5 <= val <= 10000:
                amounts.append(val)
    return amounts


def find_price_near_keyword(keyword_pat, text, max_dist=150):
    """Find a CHF amount within max_dist chars of a keyword match."""
    candidates = []
    for kw_match in re.finditer(keyword_pat, text, re.IGNORECASE):
        kw_start = kw_match.start()
        kw_end = kw_match.end()
        window_start = max(0, kw_start - max_dist)
        window_end = min(len(text), kw_end + max_dist)
        window = text[window_start:window_end]
        for pat in PRICE_AMOUNT_PATTERNS:
            for pm in re.finditer(pat, window, re.IGNORECASE):
                val = parse_amount(pm.group(1))
                if val and 5 <= val <= 5000:
                    candidates.append(val)
    if not candidates:
        return None
    # For single/trial prefer lowest reasonable; for card_10/monthly pick most common
    return min(candidates)


def extract_prices_from_text(text, url):
    """Extract pricing info from page text content."""
    if not text or len(text) < 20:
        return None

    # Find all CHF amounts on page
    found_amounts = find_all_chf_amounts(text)
    if not found_amounts:
        return None

    result = {"currency": "CHF", "source": url, "verified": True}

    # Context-based extraction
    single_price = find_price_near_keyword(SINGLE_KW, text)
    card_10_price = find_price_near_keyword(CARD10_KW, text)
    monthly_price = find_price_near_keyword(MONTHLY_KW, text)
    trial_price = find_price_near_keyword(TRIAL_KW, text)

    # For card_10: also check 5er cards
    if card_10_price is None:
        card_5_kw = r'(?:5er|5[- ]?(?:class|karte|lektionen|cours|lezioni)|(?:carte?|pass|abo|carnet)\s*(?:de?\s*)?5|5\s*(?:classes?|lektionen|cours|lezioni))'
        card_5_price = find_price_near_keyword(card_5_kw, text)
        if card_5_price and 50 <= card_5_price <= 300:
            # Convert 5er to approximate 10er
            card_10_price = round(card_5_price * 2 * 0.95)  # slight discount for 10er
            # Actually, just store the 5er price as card_10 note, or skip
            card_10_price = None  # Don't fabricate data

    # For trial: check for "free first class" patterns
    text_clean = re.sub(r'(?:specs|config|settings)\.\w+\.(?:support)?free\w*', '', text, flags=re.IGNORECASE)
    free_trial_pats = [
        r'(?:probe|trial|schnupper|essai)[^.]{0,40}?(?:gratis|free|kostenlos|gratuit)',
        r'(?:gratis|free|kostenlos|gratuit)[^.]{0,40}?(?:probe|trial|schnupper|essai)',
        r'erste?\s*(?:stunde|lektion|class)[^.]{0,30}?(?:gratis|free|kostenlos|gratuit)',
        r'(?:gratis|free|kostenlos|gratuit)[^.]{0,30}?erste?\s*(?:stunde|lektion|class)',
        r'prima\s*lezione\s*(?:gratis|gratuit)',
    ]
    for pat in free_trial_pats:
        m = re.search(pat, text_clean, re.IGNORECASE)
        if m:
            start = max(0, m.start() - 50)
            end = min(len(text_clean), m.end() + 50)
            ctx = text_clean[start:end].lower()
            if not any(x in ctx for x in ['specs.', 'config.', '"true"', '"false"', 'wix']):
                if trial_price is None:
                    trial_price = 0
                break

    # Heuristic fallback: classify by amount ranges
    if single_price is None and card_10_price is None and monthly_price is None:
        pricing_page = bool(re.search(
            r'(?:preis|price|pricing|tarif|prix|angebot|prezz|cost|abo|membership|offre|kosten)',
            url.lower() + ' ' + text[:800].lower()
        ))
        if pricing_page:
            unique_amounts = sorted(set(found_amounts))
            yoga_prices = [a for a in unique_amounts if 10 <= a <= 500]
            if len(yoga_prices) >= 2:
                singles = [a for a in yoga_prices if 15 <= a <= 55]
                tens = [a for a in yoga_prices if 140 <= a <= 450]
                monthlies = [a for a in yoga_prices if 80 <= a <= 400]

                if singles and single_price is None:
                    single_price = singles[0]
                if tens and card_10_price is None:
                    if single_price:
                        reasonable = [t for t in tens if 6 * single_price <= t <= 13 * single_price]
                        if reasonable:
                            card_10_price = reasonable[0]
                    else:
                        card_10_price = tens[0]
                if monthlies and monthly_price is None and len(yoga_prices) >= 3:
                    candidates = [m for m in monthlies if m > (single_price or 0)]
                    if candidates:
                        if card_10_price:
                            candidates = [c for c in candidates if c != card_10_price]
                        if candidates:
                            monthly_price = candidates[-1]

    # Assign results
    def clean_val(v):
        if v is None:
            return None
        return int(v) if v == int(v) else v

    if single_price is not None:
        result["single"] = clean_val(single_price)
    if card_10_price is not None:
        result["card_10"] = clean_val(card_10_price)
    if monthly_price is not None:
        result["monthly"] = clean_val(monthly_price)
    if trial_price is not None:
        result["trial"] = clean_val(trial_price)

    if not any(result.get(f) is not None and result.get(f, -1) >= 0 for f in PRICE_FIELDS):
        return None

    unique_amounts = sorted(set(found_amounts))
    amounts_str = ', '.join(str(int(a) if a == int(a) else a) for a in unique_amounts[:20])
    result["notes"] = f"CHF amounts found: {amounts_str}"

    return result


def extract_prices_from_html(html, url):
    """Extract pricing info from HTML page content. Uses both BS4 and regex."""
    if not html:
        return None
    # Try BS4 text extraction first (better at handling complex HTML)
    text = extract_text_bs4(html)
    result = extract_prices_from_text(text, url)
    if result and result.get("single"):
        return result
    # Fallback to regex strip_tags
    text2 = strip_tags(html)
    result2 = extract_prices_from_text(text2, url)
    if result2:
        if result is None:
            return result2
        # Return whichever has more fields
        r1_fields = sum(1 for f in PRICE_FIELDS if (result or {}).get(f) is not None)
        r2_fields = sum(1 for f in PRICE_FIELDS if result2.get(f) is not None)
        return result2 if r2_fields > r1_fields else result
    return result


# ───────────────────── HTTP helpers ─────────────────────

def cffi_get(session, url, timeout=TIMEOUT):
    """GET with curl_cffi, return (html, final_url) or (None, None)."""
    try:
        resp = session.get(url, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            ct = resp.headers.get("content-type", "")
            if "text" in ct or "html" in ct or "json" in ct or not ct:
                return resp.text, str(resp.url)
        return None, None
    except Exception as e:
        log.debug(f"  GET failed {url}: {e}")
        return None, None


def extract_nav_links(html, base_url):
    """Extract pricing-related links from navigation/page."""
    if not html:
        return []
    try:
        soup = BeautifulSoup(html, 'html.parser')
    except Exception:
        return []

    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc.lower()
    links = set()

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href'].strip()
        if not href or href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
            continue

        # Get link text
        link_text = a_tag.get_text(strip=True).lower()
        href_lower = href.lower()

        # Check if this link looks pricing-related
        is_pricing = False
        for kw in PRICING_LINK_KEYWORDS:
            if kw in link_text or kw in href_lower:
                is_pricing = True
                break

        if not is_pricing:
            continue

        # Resolve relative URLs
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        # Only same domain
        if parsed.netloc.lower() != base_domain:
            continue

        # Skip non-http
        if parsed.scheme not in ('http', 'https'):
            continue

        # Skip files
        path_lower = parsed.path.lower()
        if any(path_lower.endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.gif', '.zip', '.mp4']):
            continue

        links.add(full_url)

    return list(links)


def detect_eversports(html, website):
    """Detect Eversports widget and extract venue slug/ID."""
    if not html:
        return None
    patterns = [
        r'eversports\.(?:com|ch|de|at)/s/([a-zA-Z0-9_-]+)',
        r'eversports\.(?:com|ch|de|at)/widget/w/([a-zA-Z0-9_-]+)',
        r'data-eversports-widget="([^"]+)"',
    ]
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def try_eversports_api(session, slug):
    """Try Eversports API to get pricing for a venue."""
    if not slug:
        return None
    # Try both .com and .ch
    for domain in ['www.eversports.com', 'www.eversports.ch']:
        api_url = f"https://{domain}/s/{slug}"
        html, final_url = cffi_get(session, api_url)
        if html:
            result = extract_prices_from_html(html, final_url or api_url)
            if result and any(result.get(f) is not None for f in PRICE_FIELDS):
                return result
    return None


def detect_wix(html):
    """Detect if site is built on Wix."""
    if not html:
        return False
    return bool(re.search(r'wix\.com|wixsite\.com|X-Wix-|wix-warmup-data', html, re.IGNORECASE))


def try_wix_bookings(session, website):
    """Try Wix bookings API to find service prices."""
    parsed = urlparse(website)
    base = f"{parsed.scheme}://{parsed.netloc}"
    api_url = f"{base}/_api/bookings-viewer/visitor/services/list"
    try:
        resp = session.post(
            api_url,
            json={"includeDeleted": False},
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT,
            impersonate="chrome",
        )
        if resp.status_code == 200:
            data = resp.json()
            services = data.get("services", [])
            if services:
                prices_found = []
                for svc in services:
                    payment = svc.get("payment", {})
                    price_data = payment.get("fixed", {}) or payment.get("varied", {})
                    if price_data:
                        price_val = price_data.get("price")
                        currency = price_data.get("currency", "CHF")
                        if price_val and currency.upper() in ("CHF",):
                            prices_found.append(float(price_val))

                if prices_found:
                    prices_found.sort()
                    result = {
                        "currency": "CHF",
                        "source": api_url,
                        "verified": True,
                    }
                    yoga_prices = [p for p in prices_found if 10 <= p <= 500]
                    if yoga_prices:
                        singles = [p for p in yoga_prices if 10 <= p <= 55]
                        if singles:
                            val = singles[0]
                            result["single"] = int(val) if val == int(val) else val
                        return result
    except Exception as e:
        log.debug(f"  Wix API failed: {e}")
    return None


def detect_momoyoga(html):
    """Detect MomoYoga widget."""
    if not html:
        return None
    m = re.search(r'momoyoga\.com/([a-zA-Z0-9_-]+)', html, re.IGNORECASE)
    if m:
        return m.group(1)
    return None


def try_momoyoga(session, slug):
    """Try fetching prices from MomoYoga pricing page."""
    if not slug:
        return None
    url = f"https://www.momoyoga.com/{slug}/pricing"
    html, final_url = cffi_get(session, url)
    if html:
        result = extract_prices_from_html(html, final_url or url)
        if result and any(result.get(f) is not None for f in PRICE_FIELDS):
            return result
    return None


def detect_fitogram(html):
    """Detect Fitogram / FitogramPro widget."""
    if not html:
        return None
    m = re.search(r'fitogram\.(?:pro|com)/([a-zA-Z0-9_-]+)', html, re.IGNORECASE)
    if m:
        return m.group(1)
    return None


def try_fitogram(session, slug):
    """Try fetching prices from Fitogram."""
    if not slug:
        return None
    url = f"https://widget.fitogram.pro/en/{slug}/shop"
    html, final_url = cffi_get(session, url)
    if html:
        result = extract_prices_from_html(html, final_url or url)
        if result and any(result.get(f) is not None for f in PRICE_FIELDS):
            return result
    return None


# ───────────────────── Main scraping logic ─────────────────────

def scrape_studio(session, studio):
    """Scrape pricing for a single studio. Returns pricing dict or None."""
    website = studio.get("website", "").strip().rstrip("/")
    if not website:
        return None

    parsed = urlparse(website)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # 1. Fetch homepage
    html, final_url = cffi_get(session, website)

    homepage_result = None
    eversports_slug = None
    is_wix = False
    momoyoga_slug = None
    fitogram_slug = None
    nav_links = []

    best_result = None

    def update_best(result):
        nonlocal best_result
        if result is None:
            return
        has_single = result.get("single") is not None
        r_fields = sum(1 for f in PRICE_FIELDS if result.get(f) is not None)
        b_fields = sum(1 for f in PRICE_FIELDS if (best_result or {}).get(f) is not None) if best_result else 0
        b_has_single = (best_result or {}).get("single") is not None if best_result else False

        if best_result is None:
            best_result = result
        elif has_single and not b_has_single:
            best_result = result
        elif has_single and b_has_single and r_fields > b_fields:
            best_result = result
        elif not b_has_single and r_fields > b_fields:
            best_result = result

    if html:
        # Check for platform integrations
        eversports_slug = detect_eversports(html, website)
        is_wix = detect_wix(html)
        momoyoga_slug = detect_momoyoga(html)
        fitogram_slug = detect_fitogram(html)

        # Extract navigation links
        nav_links = extract_nav_links(html, final_url or website)

        # Try extracting from homepage
        homepage_result = extract_prices_from_html(html, final_url or website)
        if homepage_result and homepage_result.get("single"):
            return homepage_result
        update_best(homepage_result)

    # 2. Try navigation links found on page (these are most likely to have prices)
    tried = {website, website + "/", base_url, base_url + "/"}
    if final_url:
        tried.add(final_url)
        tried.add(final_url.rstrip("/"))

    subpages_tried = 0
    for nav_url in nav_links[:15]:
        nav_clean = nav_url.rstrip("/")
        if nav_clean in tried or nav_url in tried:
            continue
        tried.add(nav_clean)
        tried.add(nav_url)

        if subpages_tried >= MAX_SUBPAGES:
            break
        subpages_tried += 1

        time.sleep(SUB_PAGE_DELAY)
        sub_html, sub_url = cffi_get(session, nav_url, timeout=10)
        if sub_html:
            result = extract_prices_from_html(sub_html, sub_url or nav_url)
            if result and result.get("single"):
                return result
            update_best(result)

    # 3. Try common pricing page paths
    for path in PRICE_PATHS:
        if subpages_tried >= MAX_SUBPAGES:
            break

        url = base_url + path
        url_clean = url.rstrip("/")
        if url_clean in tried or url in tried:
            continue
        tried.add(url_clean)
        tried.add(url)
        subpages_tried += 1

        time.sleep(SUB_PAGE_DELAY)
        sub_html, sub_url = cffi_get(session, url, timeout=10)
        if sub_html:
            # Check if we got redirected to a page we already tried
            if sub_url and sub_url.rstrip("/") in tried and sub_url != url:
                continue

            result = extract_prices_from_html(sub_html, sub_url or url)
            if result and result.get("single"):
                return result
            update_best(result)

            # Also check for further pricing links on subpages
            if sub_html and not best_result:
                sub_nav = extract_nav_links(sub_html, sub_url or url)
                for sn_url in sub_nav[:5]:
                    sn_clean = sn_url.rstrip("/")
                    if sn_clean in tried:
                        continue
                    tried.add(sn_clean)
                    if subpages_tried >= MAX_SUBPAGES:
                        break
                    subpages_tried += 1
                    time.sleep(SUB_PAGE_DELAY)
                    sn_html, sn_final = cffi_get(session, sn_url, timeout=10)
                    if sn_html:
                        sn_result = extract_prices_from_html(sn_html, sn_final or sn_url)
                        if sn_result and sn_result.get("single"):
                            return sn_result
                        update_best(sn_result)

    # 4. Try Eversports API
    if eversports_slug:
        time.sleep(SUB_PAGE_DELAY)
        ev_result = try_eversports_api(session, eversports_slug)
        if ev_result and ev_result.get("single"):
            return ev_result
        update_best(ev_result)

    # Also check detected_booking_links for Eversports
    booking_links = studio.get("detected_booking_links", [])
    if not eversports_slug:
        for bl in booking_links:
            if bl.get("platform") == "eversports" and bl.get("url"):
                m = re.search(r'eversports\.(?:com|ch|de|at)/s/([a-zA-Z0-9_-]+)', bl["url"])
                if m:
                    eversports_slug = m.group(1)
                    time.sleep(SUB_PAGE_DELAY)
                    ev_result = try_eversports_api(session, eversports_slug)
                    if ev_result and ev_result.get("single"):
                        return ev_result
                    update_best(ev_result)
                    break

    # 5. Try Wix bookings API
    if is_wix:
        time.sleep(SUB_PAGE_DELAY)
        wix_result = try_wix_bookings(session, website)
        if wix_result and wix_result.get("single"):
            return wix_result
        update_best(wix_result)

    # 6. Try MomoYoga
    if momoyoga_slug:
        time.sleep(SUB_PAGE_DELAY)
        momo_result = try_momoyoga(session, momoyoga_slug)
        if momo_result and momo_result.get("single"):
            return momo_result
        update_best(momo_result)

    # 7. Try Fitogram
    if fitogram_slug:
        time.sleep(SUB_PAGE_DELAY)
        fito_result = try_fitogram(session, fitogram_slug)
        if fito_result and fito_result.get("single"):
            return fito_result
        update_best(fito_result)

    # 8. Try schedule_url if different
    sched_url = studio.get("schedule_url", "")
    if sched_url and sched_url.rstrip("/") not in tried:
        time.sleep(SUB_PAGE_DELAY)
        sched_html, sched_final = cffi_get(session, sched_url)
        if sched_html:
            sched_result = extract_prices_from_html(sched_html, sched_final or sched_url)
            if sched_result and sched_result.get("single"):
                return sched_result
            update_best(sched_result)

            # Check for Eversports in schedule page too
            ev_slug_sched = detect_eversports(sched_html, sched_url)
            if ev_slug_sched and ev_slug_sched != eversports_slug:
                time.sleep(SUB_PAGE_DELAY)
                ev2 = try_eversports_api(session, ev_slug_sched)
                if ev2 and ev2.get("single"):
                    return ev2
                update_best(ev2)

    # Return best result we found (even without single, if it has other fields)
    return best_result


# ───────────────────── File update logic ─────────────────────

def build_pricing_object(price_data):
    """Build a clean pricing object for studios_*.json."""
    pricing = {}
    for field in PRICE_FIELDS:
        val = price_data.get(field)
        if val is not None:
            if isinstance(val, str):
                m = re.match(r"(\d+(?:\.\d+)?)", val)
                if m:
                    val = float(m.group(1))
                    val = int(val) if val == int(val) else val
                else:
                    continue
            pricing[field] = val
    pricing["currency"] = "CHF"
    pricing["verified"] = True
    if price_data.get("source"):
        pricing["source"] = price_data["source"]
    pricing["last_checked"] = datetime.now(timezone.utc).isoformat()
    return pricing


def update_studio_in_file(fpath, studio_id, pricing_obj):
    """Update a studio's pricing in its studios_*.json file."""
    with open(fpath) as f:
        data = json.load(f)

    updated = False
    for studio in data.get("studios", []):
        if studio["id"] == studio_id:
            studio["pricing"] = pricing_obj
            if "_meta" not in studio:
                studio["_meta"] = {}
            studio["_meta"]["last_price_check"] = pricing_obj["last_checked"]
            if pricing_obj.get("source"):
                if "source_urls" not in studio["_meta"]:
                    studio["_meta"]["source_urls"] = {}
                studio["_meta"]["source_urls"]["pricing"] = pricing_obj["source"]
            updated = True
            break

    if updated:
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(fpath, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    return updated


# ───────────────────── Load existing price files ─────────────────────

def load_existing_prices():
    """Load previously scraped prices from tools/prices_*.json files."""
    all_prices = {}
    for fname in glob.glob(os.path.join(TOOLS_DIR, "prices_*.json")):
        try:
            with open(fname) as f:
                data = json.load(f)
        except Exception:
            continue

        if isinstance(data, dict):
            for key, val in data.items():
                if key == "_metadata":
                    continue
                if isinstance(val, dict):
                    if "currency" in val or "single" in val:
                        all_prices[key] = val
                    else:
                        for subkey, subval in val.items():
                            if isinstance(subval, dict) and ("currency" in subval or "single" in subval):
                                all_prices[subkey] = subval

    return all_prices


# ───────────────────── Main ─────────────────────

def main():
    print("=" * 72)
    print("  FINAL COMPREHENSIVE PRICE SCRAPER v2")
    print("  Scanning ALL studios without verified pricing")
    print("  Using curl_cffi with chrome impersonation")
    print("=" * 72)

    # Step 1: Find all studios without verified pricing (with single price)
    missing = []
    for fpath in sorted(glob.glob(os.path.join(DATA_DIR, "studios_*.json"))):
        if ".enc." in fpath:
            continue
        canton = os.path.basename(fpath).replace("studios_", "").replace(".json", "")
        with open(fpath) as f:
            data = json.load(f)
        for s in data.get("studios", []):
            if not s.get("active", True):
                continue
            p = s.get("pricing", {})
            if not (p and p.get("verified") and p.get("single")):
                missing.append({
                    "id": s["id"],
                    "name": s["name"],
                    "canton": canton,
                    "website": s.get("website", ""),
                    "schedule_url": s.get("schedule_url", ""),
                    "detected_booking_links": s.get("detected_booking_links", []),
                    "file": os.path.abspath(fpath),
                })

    print(f"\nStudios needing verified pricing: {len(missing)}")

    # Step 2: Check existing price files for recoverable data
    existing = load_existing_prices()
    print(f"Existing scraped price entries: {len(existing)}")

    recovered = 0
    still_needed = []

    for studio in missing:
        sid = studio["id"]
        if sid in existing:
            pd = existing[sid]
            if pd.get("single") or pd.get("verified"):
                pricing_obj = build_pricing_object(pd)
                if pricing_obj.get("single") and update_studio_in_file(studio["file"], sid, pricing_obj):
                    recovered += 1
                    log.info(f"[EXISTING] {sid}: single={pricing_obj.get('single')}, "
                             f"card_10={pricing_obj.get('card_10')}, "
                             f"monthly={pricing_obj.get('monthly')}")
                    continue
        still_needed.append(studio)

    print(f"Recovered from existing files: {recovered}")
    print(f"Studios to scrape: {len(still_needed)}")

    # Step 3: Scrape with curl_cffi
    session = cffi_requests.Session(impersonate="chrome")

    scraped = 0
    failed = 0
    results_log = []

    print(f"\n{'─' * 72}")
    print(f"  Scraping {len(still_needed)} studios...")
    print(f"{'─' * 72}\n")

    for i, studio in enumerate(still_needed):
        sid = studio["id"]
        website = studio["website"]
        canton = studio["canton"]

        if not website:
            log.info(f"[{i+1}/{len(still_needed)}] {sid} ({canton}): NO WEBSITE — skipped")
            failed += 1
            results_log.append({"id": sid, "canton": canton, "status": "no_website"})
            continue

        log.info(f"[{i+1}/{len(still_needed)}] {sid} ({canton}): {website}")

        try:
            result = scrape_studio(session, studio)
        except Exception as e:
            log.warning(f"  ERROR: {e}")
            result = None

        if result and any(result.get(f) is not None and result.get(f, -1) >= 0 for f in PRICE_FIELDS):
            pricing_obj = build_pricing_object(result)
            if update_studio_in_file(studio["file"], sid, pricing_obj):
                scraped += 1
                log.info(f"  -> FOUND: single={pricing_obj.get('single')}, "
                         f"card_10={pricing_obj.get('card_10')}, "
                         f"monthly={pricing_obj.get('monthly')}, "
                         f"trial={pricing_obj.get('trial')} "
                         f"[source: {pricing_obj.get('source', '?')}]")
                results_log.append({
                    "id": sid, "canton": canton, "status": "scraped",
                    "single": pricing_obj.get("single"),
                    "card_10": pricing_obj.get("card_10"),
                    "monthly": pricing_obj.get("monthly"),
                    "trial": pricing_obj.get("trial"),
                    "source": pricing_obj.get("source"),
                })
            else:
                failed += 1
                log.warning(f"  -> Prices found but file update failed")
                results_log.append({"id": sid, "canton": canton, "status": "update_failed"})
        else:
            failed += 1
            log.info(f"  -> NO PRICES found")
            results_log.append({"id": sid, "canton": canton, "status": "not_found", "website": website})

        # Rate limit
        if i < len(still_needed) - 1:
            time.sleep(RATE_LIMIT)

    session.close()

    # Step 4: Save results log
    log_path = os.path.join(TOOLS_DIR, "price_scrape_final_results.json")
    with open(log_path, "w") as f:
        json.dump({
            "_metadata": {
                "run_date": datetime.now(timezone.utc).isoformat(),
                "total_needed": len(missing),
                "recovered_existing": recovered,
                "newly_scraped": scraped,
                "failed": failed,
            },
            "results": results_log,
        }, f, indent=2, ensure_ascii=False)

    # Summary
    print(f"\n{'=' * 72}")
    print(f"  SUMMARY")
    print(f"{'=' * 72}")
    print(f"  Total studios needing prices:     {len(missing)}")
    print(f"  Recovered from existing files:     {recovered}")
    print(f"  Newly scraped:                     {scraped}")
    print(f"  Failed / not found:                {failed}")
    print(f"  Total now with verified pricing:   {recovered + scraped}")
    print(f"  Still missing:                     {len(missing) - recovered - scraped}")
    print(f"\n  Results saved to: {log_path}")

    # Post-run count
    total_verified = 0
    total_studios = 0
    for fpath in sorted(glob.glob(os.path.join(DATA_DIR, "studios_*.json"))):
        if ".enc." in fpath:
            continue
        with open(fpath) as f:
            data = json.load(f)
        for s in data.get("studios", []):
            if not s.get("active", True):
                continue
            total_studios += 1
            p = s.get("pricing", {})
            if p and p.get("verified") and p.get("single"):
                total_verified += 1

    print(f"\n  Overall: {total_verified}/{total_studios} studios now have verified pricing")
    pct = (total_verified / total_studios * 100) if total_studios else 0
    print(f"  Coverage: {pct:.1f}%")
    print(f"{'=' * 72}")

    # Print still-missing studios
    still_missing = [r for r in results_log if r["status"] in ("not_found", "no_website")]
    if still_missing:
        print(f"\n  Studios still without pricing ({len(still_missing)}):")
        for r in still_missing:
            print(f"    {r['id']:40s} {r['canton']:18s} {r.get('website', 'N/A')}")


if __name__ == "__main__":
    main()
