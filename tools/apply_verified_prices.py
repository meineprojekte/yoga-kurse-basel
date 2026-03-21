#!/usr/bin/env python3
"""
Apply verified prices from price files to studio data files.
- Studios with verified prices get their pricing updated.
- Studios without verified prices have their pricing field removed entirely.
"""

import json
import os
import re
import glob

BASE_DIR = "/Users/andrea/ClaudeWork/JogaKurseBasel"
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Price fields we care about
PRICE_FIELDS = ["single", "card_10", "monthly", "trial"]


def parse_price(value):
    """Convert a price value to a numeric value, or None if not usable."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if value == 0:
            return 0  # Free trial is valid
        return value
    if isinstance(value, str):
        # Handle ranges like "25-35" -> take lower number
        match = re.match(r"(\d+(?:\.\d+)?)", value)
        if match:
            num = float(match.group(1))
            return int(num) if num == int(num) else num
        return None
    return None


def has_any_real_price(price_data):
    """Check if the price data has at least one actual numeric price."""
    for field in PRICE_FIELDS:
        val = price_data.get(field)
        parsed = parse_price(val)
        if parsed is not None and parsed >= 0:
            return True
    return False


def build_pricing_object(price_data):
    """Build a clean pricing object from verified price data."""
    pricing = {}
    for field in PRICE_FIELDS:
        val = parse_price(price_data.get(field))
        if val is not None:
            pricing[field] = val
    pricing["currency"] = "CHF"
    pricing["verified"] = True
    if price_data.get("source"):
        pricing["source"] = price_data["source"]
    return pricing


def load_all_prices():
    """
    Load all price files and return a flat dict: studio_id -> price_data.
    Also return a canton-keyed version for prices_remaining.json.
    """
    all_prices = {}  # studio_id -> price_data

    # Flat price files: studio_id is a top-level key
    flat_files = {
        "prices_zurich.json": "zurich",
        "prices_basel.json": "basel",
        "prices_geneve.json": "geneve",
        "prices_vaud.json": "vaud",
        "prices_luzern.json": "luzern",
        "prices_aargau.json": "aargau",
        "prices_st-gallen.json": "st-gallen",
    }

    metadata_keys = {"last_updated", "last_scraped", "notes", "_metadata"}

    for filename, canton in flat_files.items():
        filepath = os.path.join(TOOLS_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  WARNING: {filename} not found, skipping")
            continue
        with open(filepath, "r") as f:
            data = json.load(f)

        # Check if it has a "studios" wrapper (like prices_bern.json)
        if "studios" in data and isinstance(data["studios"], dict):
            studios_data = data["studios"]
        else:
            studios_data = {k: v for k, v in data.items() if k not in metadata_keys}

        for studio_id, price_data in studios_data.items():
            if isinstance(price_data, dict):
                all_prices[studio_id] = price_data

    # prices_bern.json has "studios" key
    bern_path = os.path.join(TOOLS_DIR, "prices_bern.json")
    if os.path.exists(bern_path):
        with open(bern_path, "r") as f:
            data = json.load(f)
        studios_data = data.get("studios", {})
        for studio_id, price_data in studios_data.items():
            if isinstance(price_data, dict):
                all_prices[studio_id] = price_data

    # prices_remaining.json: nested by canton
    remaining_path = os.path.join(TOOLS_DIR, "prices_remaining.json")
    if os.path.exists(remaining_path):
        with open(remaining_path, "r") as f:
            data = json.load(f)
        for key, value in data.items():
            if key == "_metadata":
                continue
            if isinstance(value, dict):
                # value is a dict of studio_id -> price_data
                for studio_id, price_data in value.items():
                    if isinstance(price_data, dict):
                        all_prices[studio_id] = price_data

    return all_prices


def process_studio_files(all_prices):
    """Process all studio files, applying verified prices or removing pricing."""
    studio_files = sorted(glob.glob(os.path.join(DATA_DIR, "studios_*.json")))
    # Filter out .enc.json files
    studio_files = [f for f in studio_files if not f.endswith(".enc.json")]

    total_verified = 0
    total_removed = 0
    total_unchanged = 0
    total_studios = 0

    for filepath in studio_files:
        filename = os.path.basename(filepath)
        with open(filepath, "r") as f:
            data = json.load(f)

        studios = data.get("studios", [])
        file_verified = 0
        file_removed = 0

        for studio in studios:
            total_studios += 1
            studio_id = studio.get("id", "")
            price_data = all_prices.get(studio_id)

            if price_data and price_data.get("verified") is True and has_any_real_price(price_data):
                # Apply verified prices
                studio["pricing"] = build_pricing_object(price_data)
                file_verified += 1
                total_verified += 1
            else:
                # Remove pricing if it exists
                if "pricing" in studio:
                    del studio["pricing"]
                    file_removed += 1
                    total_removed += 1
                else:
                    total_unchanged += 1

        # Save updated file
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

        if file_verified > 0 or file_removed > 0:
            print(f"  {filename}: {file_verified} verified, {file_removed} removed")

    return total_studios, total_verified, total_removed, total_unchanged


def main():
    print("=" * 60)
    print("APPLYING VERIFIED PRICES TO STUDIO FILES")
    print("=" * 60)

    print("\n1. Loading price files...")
    all_prices = load_all_prices()
    verified_count = sum(1 for p in all_prices.values() if p.get("verified") is True and has_any_real_price(p))
    print(f"   Loaded {len(all_prices)} studio prices ({verified_count} verified with real prices)")

    print("\n2. Processing studio files...")
    total, verified, removed, unchanged = process_studio_files(all_prices)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total studios processed: {total}")
    print(f"  Verified prices applied: {verified}")
    print(f"  Pricing removed (unverified/missing): {removed}")
    print(f"  No pricing field (unchanged): {unchanged}")
    print("=" * 60)


if __name__ == "__main__":
    main()
