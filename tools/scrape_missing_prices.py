#!/usr/bin/env python3
"""
Scrape missing prices for studios that have verified schedules but no verified pricing.

1. Reads all studios_*.json to find studios without verified pricing
2. Checks existing price files for previously scraped data
3. Scrapes remaining studios with curl_cffi
4. Updates studios_*.json with verified pricing
5. Rate limits 2 seconds between requests
"""

import json
import os
import re
import glob
import time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

BASE_DIR = "/Users/andrea/ClaudeWork/JogaKurseBasel"
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Price page URL suffixes to try (most common first, no duplicate with/without slash)
PRICE_PATHS = [
    "/preise", "/prices", "/pricing", "/tarife", "/tarifs", "/prix",
    "/angebot", "/prezzi", "/costi",
    "/en/prices", "/en/pricing", "/de/preise", "/fr/tarifs",
    "/abo-preise", "/preise-abos", "/kurse-preise",
    "/classes-prices", "/yoga-preise",
]

PRICE_FILES = [
    "prices_zurich.json",
    "prices_basel.json",
    "prices_bern.json",
    "prices_geneve.json",
    "prices_vaud.json",
    "prices_luzern.json",
    "prices_aargau.json",
    "prices_st-gallen.json",
    "prices_remaining.json",
]

PRICE_FIELDS = ["single", "card_10", "monthly", "trial"]


def load_existing_prices():
    """Load all existing price data from price files."""
    all_prices = {}

    for fname in PRICE_FILES:
        fpath = os.path.join(TOOLS_DIR, fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath) as f:
            data = json.load(f)

        # prices_remaining.json has canton-level nesting
        if fname == "prices_remaining.json":
            for key, val in data.items():
                if key == "_metadata":
                    continue
                if isinstance(val, dict):
                    # Check if it's a canton dict (contains studio dicts)
                    first_val = next(iter(val.values()), None)
                    if isinstance(first_val, dict) and "currency" in first_val:
                        # It's a canton -> studios mapping
                        for studio_id, price_data in val.items():
                            all_prices[studio_id] = price_data
                    elif "currency" in val:
                        # Direct studio entry
                        all_prices[key] = val
        # prices_bern.json has a "studios" wrapper
        elif "studios" in data and isinstance(data["studios"], dict):
            for studio_id, price_data in data["studios"].items():
                all_prices[studio_id] = price_data
        else:
            # Direct studio_id -> price_data mapping (prices_zurich, prices_geneve, etc.)
            for key, val in data.items():
                if isinstance(val, dict) and "currency" in val:
                    all_prices[key] = val

    return all_prices


def find_studios_without_prices():
    """Find studios with verified schedules but no verified pricing."""
    studios = []
    for fpath in sorted(glob.glob(os.path.join(DATA_DIR, "studios_*.json"))):
        if ".enc." in fpath:
            continue
        canton = os.path.basename(fpath).replace("studios_", "").replace(".json", "")
        with open(fpath) as f:
            data = json.load(f)
        studios_list = data.get("studios", [])
        for s in studios_list:
            has_schedule = s.get("scrape_status") == "scraped" or bool(s.get("classes"))
            pricing = s.get("pricing", {})
            has_verified_pricing = pricing.get("verified", False) if pricing else False
            if has_schedule and not has_verified_pricing:
                studios.append({
                    "id": s["id"],
                    "name": s["name"],
                    "canton": canton,
                    "website": s.get("website", ""),
                    "file": fpath,
                })
    return studios


def parse_price_value(value):
    """Convert a price value to a numeric value, or None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        match = re.match(r"(\d+(?:\.\d+)?)", value)
        if match:
            num = float(match.group(1))
            return int(num) if num == int(num) else num
    return None


def has_any_real_price(price_data):
    """Check if price data has at least one real numeric price."""
    for field in PRICE_FIELDS:
        val = parse_price_value(price_data.get(field))
        if val is not None and val >= 0:
            return True
    return False


def strip_tags(html_snippet):
    """Remove HTML tags and normalize whitespace."""
    text = re.sub(r'<[^>]+>', ' ', html_snippet)
    return re.sub(r'\s+', ' ', text).strip()


def extract_prices_from_html(html, url):
    """Extract CHF prices from HTML content."""
    if not html:
        return None

    # Strip HTML tags for easier text matching
    text = strip_tags(html)

    # Patterns for finding CHF amounts (both "CHF 30" and "30 CHF")
    price_patterns = [
        r'CHF\s*(\d+(?:[.,]\d{1,2})?)',
        r'(\d+(?:[.,]\d{1,2})?)\s*CHF',
        r'Fr\.?\s*(\d+(?:[.,]\d{1,2})?)',
        r'(\d+(?:[.,]\d{1,2})?)\s*Fr\.',
        r'SFr\.?\s*(\d+(?:[.,]\d{1,2})?)',
    ]

    found_amounts = []
    for pattern in price_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                val = match.group(1).replace(",", ".")
                amount = float(val)
                if 5 <= amount <= 10000:  # Reasonable price range
                    found_amounts.append(amount)
            except (ValueError, IndexError):
                continue

    if not found_amounts:
        return None

    result = {
        "currency": "CHF",
        "source": url,
        "verified": True,
    }

    single_price = None
    card_10_price = None
    monthly_price = None
    trial_price = None

    # ---- Context-based extraction (search in stripped text) ----
    # Each group: (price_type, keyword_regex, proximity_chars)
    # We search for keyword near a CHF amount
    single_keywords = r'(?:einzelstunde|einzellektion|single\s*class|drop[- ]?in|kurse?\s*(?:60|75|90)\s*min|lezione?\s*(?:singola|unica)|cours?\s*(?:individuel|unique|à\s*l.unit[eé])|1\s*(?:lektion|class|cours))'
    card_10_keywords = r'(?:10er|10[- ]?(?:class|karte|lektionen|cours|lezioni)|(?:carte?|pass|abo)\s*(?:de?\s*)?10)'
    monthly_keywords = r'(?:monats?\s*abo|monthly|monatlich|unlimited\s*(?:1\s*)?month|illimit[eé]|mensuel|abo\s*(?:un)?limit[eé]?)'
    trial_keywords = r'(?:probe|trial|schnupper|essai|d[eé]couverte|prova|kennen\s*lern|intro)'

    # Generic pattern: keyword within 80 chars of a CHF amount in either direction
    def find_price_near_keyword(keyword_pat, text_to_search, max_dist=100):
        """Find a CHF amount near a keyword."""
        for kw_match in re.finditer(keyword_pat, text_to_search, re.IGNORECASE):
            kw_start = kw_match.start()
            kw_end = kw_match.end()
            # Search for CHF amounts in a window around the keyword
            window_start = max(0, kw_start - max_dist)
            window_end = min(len(text_to_search), kw_end + max_dist)
            window = text_to_search[window_start:window_end]
            for pp in price_patterns:
                for pm in re.finditer(pp, window, re.IGNORECASE):
                    try:
                        val = float(pm.group(1).replace(",", "."))
                        if 5 <= val <= 5000:
                            return val
                    except (ValueError, IndexError):
                        continue
        return None

    single_price = find_price_near_keyword(single_keywords, text)
    card_10_price = find_price_near_keyword(card_10_keywords, text)
    monthly_price = find_price_near_keyword(monthly_keywords, text)
    trial_price = find_price_near_keyword(trial_keywords, text)

    # Check for free trial (but NOT Wix platform config strings like supportFreeTrialType)
    # First, strip out Wix/platform JSON config to avoid false positives
    text_for_trial = re.sub(r'(?:specs|config|settings)\.\w+\.(?:support)?free\w*', '', text, flags=re.IGNORECASE)
    free_trial_patterns = [
        r'(?:probe|trial|schnupper|essai)[^.]{0,40}?(?:gratis|free|kostenlos|gratuit)',
        r'(?:gratis|free|kostenlos|gratuit)[^.]{0,40}?(?:probe|trial|schnupper|essai)',
        r'erste?\s*(?:stunde|lektion|class)[^.]{0,30}?(?:gratis|free|kostenlos|gratuit)',
        r'(?:gratis|free|kostenlos|gratuit)[^.]{0,30}?erste?\s*(?:stunde|lektion|class)',
    ]
    for pat in free_trial_patterns:
        m = re.search(pat, text_for_trial, re.IGNORECASE)
        if m:
            # Extra check: make sure the context is not from JS/config code
            start = max(0, m.start() - 50)
            end = min(len(text_for_trial), m.end() + 50)
            context = text_for_trial[start:end].lower()
            if not any(x in context for x in ['specs.', 'config.', '"true"', '"false"', 'wix']):
                if trial_price is None:
                    trial_price = 0
                break

    # ---- Heuristic classification fallback ----
    # If we found CHF amounts on a /preise or /pricing page but context matching failed,
    # try to classify by amount ranges typical for Swiss yoga studios.
    # Single: 15-50, Card_10: 150-400, Monthly: 100-350, Trial: 0-100
    if single_price is None and card_10_price is None and monthly_price is None:
        unique_amounts = sorted(set(found_amounts))
        # Only use heuristics if we're on a pricing-related page
        pricing_page = bool(re.search(
            r'(?:preis|price|pricing|tarif|prix|angebot|prezz|cost|abo)',
            url.lower() + ' ' + text[:500].lower()
        ))
        if pricing_page and len(unique_amounts) >= 2:
            # Filter to yoga-relevant range (15-500)
            yoga_prices = [a for a in unique_amounts if 15 <= a <= 500]
            if yoga_prices:
                # Smallest amount in 15-50 range is likely single class
                singles = [a for a in yoga_prices if 15 <= a <= 50]
                tens = [a for a in yoga_prices if 150 <= a <= 400]
                monthlies = [a for a in yoga_prices if 100 <= a <= 350]

                if singles and single_price is None:
                    single_price = singles[0]  # Lowest single-class price
                if tens and card_10_price is None:
                    # Pick a 10er that's roughly 7-12x the single price
                    if single_price:
                        reasonable_10 = [t for t in tens if 6 * single_price <= t <= 13 * single_price]
                        if reasonable_10:
                            card_10_price = reasonable_10[0]
                    else:
                        card_10_price = tens[0]

    # Assign to result
    if single_price is not None:
        result["single"] = int(single_price) if single_price == int(single_price) else single_price
    if card_10_price is not None:
        result["card_10"] = int(card_10_price) if card_10_price == int(card_10_price) else card_10_price
    if monthly_price is not None:
        result["monthly"] = int(monthly_price) if monthly_price == int(monthly_price) else monthly_price
    if trial_price is not None:
        result["trial"] = int(trial_price) if trial_price == int(trial_price) else trial_price

    if not has_any_real_price(result):
        return None

    # Build notes
    unique_amounts = sorted(set(found_amounts))
    amounts_str = ', '.join(str(int(a) if a == int(a) else a) for a in unique_amounts[:15])
    result["notes"] = f"CHF amounts found on page: {amounts_str}"

    return result


def fetch_url(session, url, timeout=15):
    """Fetch a URL with curl_cffi, return (html, final_url) or (None, None)."""
    try:
        resp = session.get(url, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            return resp.text, str(resp.url)
        return None, None
    except Exception:
        return None, None


def scrape_studio_prices(session, website):
    """Try to scrape prices from a studio website."""
    if not website:
        return None

    # Normalize base URL
    parsed = urlparse(website)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # First try the homepage
    html, final_url = fetch_url(session, website)
    if html:
        result = extract_prices_from_html(html, final_url)
        if result and has_any_real_price(result):
            return result

    # Try common pricing page paths
    tried_urls = {website, website.rstrip("/"), website.rstrip("/") + "/"}
    for path in PRICE_PATHS:
        # Try both with and without trailing slash
        for suffix in [path, path + "/"]:
            url = base_url + suffix
            if url in tried_urls:
                continue
            tried_urls.add(url)

            time.sleep(0.3)  # Brief delay between subpage requests
            html, final_url = fetch_url(session, url, timeout=10)
            if html:
                result = extract_prices_from_html(html, final_url or url)
                if result and has_any_real_price(result):
                    return result

    return None


def build_pricing_object(price_data):
    """Build a clean pricing object for studios_*.json."""
    pricing = {}
    for field in PRICE_FIELDS:
        val = parse_price_value(price_data.get(field))
        if val is not None:
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
            # Also update _meta
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


def main():
    print("=" * 70)
    print("SCRAPE MISSING PRICES")
    print("=" * 70)

    # Step 1: Find studios without verified pricing
    studios_needed = find_studios_without_prices()
    print(f"\nStudios with schedule but no verified pricing: {len(studios_needed)}")

    # Step 2: Load existing price data
    existing_prices = load_existing_prices()
    print(f"Existing price entries in price files: {len(existing_prices)}")

    # Step 3: Check existing prices first
    recovered_from_existing = 0
    still_needed = []

    for studio in studios_needed:
        sid = studio["id"]
        if sid in existing_prices:
            price_data = existing_prices[sid]
            if price_data.get("verified") and has_any_real_price(price_data):
                pricing_obj = build_pricing_object(price_data)
                if update_studio_in_file(studio["file"], sid, pricing_obj):
                    recovered_from_existing += 1
                    print(f"  [EXISTING] {sid}: single={pricing_obj.get('single')}, "
                          f"card_10={pricing_obj.get('card_10')}, "
                          f"monthly={pricing_obj.get('monthly')}, "
                          f"trial={pricing_obj.get('trial')}")
                continue
        still_needed.append(studio)

    print(f"\nRecovered from existing price files: {recovered_from_existing}")
    print(f"Studios still needing scraping: {len(still_needed)}")

    # Step 4: Scrape remaining studios with curl_cffi
    scraped_count = 0
    failed_count = 0

    if still_needed:
        from curl_cffi import requests as cffi_requests

        session = cffi_requests.Session(impersonate="chrome")

        print(f"\nScraping {len(still_needed)} studios...")
        print("-" * 70)

        for i, studio in enumerate(still_needed):
            sid = studio["id"]
            website = studio["website"]
            canton = studio["canton"]

            if not website:
                print(f"  [{i+1}/{len(still_needed)}] {sid}: NO WEBSITE - skipped")
                failed_count += 1
                continue

            print(f"  [{i+1}/{len(still_needed)}] {sid} ({canton}): {website}")

            result = scrape_studio_prices(session, website)

            if result and has_any_real_price(result):
                pricing_obj = build_pricing_object(result)
                if update_studio_in_file(studio["file"], sid, pricing_obj):
                    scraped_count += 1
                    print(f"    -> FOUND: single={pricing_obj.get('single')}, "
                          f"card_10={pricing_obj.get('card_10')}, "
                          f"monthly={pricing_obj.get('monthly')}, "
                          f"trial={pricing_obj.get('trial')}")
                else:
                    failed_count += 1
                    print(f"    -> PRICES FOUND but could not update file")
            else:
                failed_count += 1
                print(f"    -> NO PRICES found")

            # Rate limit: 2 seconds between studios
            if i < len(still_needed) - 1:
                time.sleep(2)

        session.close()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total studios needing prices:       {len(studios_needed)}")
    print(f"Recovered from existing files:       {recovered_from_existing}")
    print(f"Newly scraped:                       {scraped_count}")
    print(f"Failed/no prices found:              {failed_count}")
    print(f"Total now with verified pricing:     {recovered_from_existing + scraped_count}")
    print(f"Still missing:                       {len(studios_needed) - recovered_from_existing - scraped_count}")


if __name__ == "__main__":
    main()
