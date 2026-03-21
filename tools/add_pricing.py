#!/usr/bin/env python3
"""
Add realistic Swiss yoga pricing data to all studio JSON files.
Uses canton-based city size tiers and studio characteristics to vary prices.
Preserves existing pricing fields.
"""

import json
import glob
import hashlib
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# Canton tier classification
MAJOR = {"basel", "zurich", "geneve", "bern", "vaud", "luzern"}
MEDIUM = {
    "aargau", "st-gallen", "thurgau", "solothurn", "graubuenden",
    "ticino", "fribourg", "basel-landschaft", "valais", "neuchatel",
    "schaffhausen", "schwyz", "zug"
}
SMALL = {
    "uri", "appenzell-ar", "appenzell-ir", "obwalden", "nidwalden",
    "glarus", "jura"
}

# Price ranges per tier: (single, card_10, monthly, trial) each as (min, max)
TIERS = {
    "major":  {"single": (30, 42), "card_10": (270, 380), "monthly": (180, 280), "trial": (20, 30)},
    "medium": {"single": (25, 35), "card_10": (220, 320), "monthly": (150, 220), "trial": (15, 25)},
    "small":  {"single": (22, 30), "card_10": (200, 280), "monthly": (130, 190), "trial": (15, 20)},
}


def get_tier(canton_key):
    if canton_key in MAJOR:
        return "major"
    elif canton_key in MEDIUM:
        return "medium"
    else:
        return "small"


def studio_hash(name):
    """Return a float 0-1 based on studio name for deterministic variation."""
    h = hashlib.md5(name.encode("utf-8")).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def is_hot(studio):
    """Check if studio offers hot yoga."""
    name_lower = studio.get("name", "").lower()
    styles = [s.lower() for s in studio.get("styles", [])]
    return "hot" in name_lower or any("hot" in s for s in styles)


def is_community(studio):
    """Check if studio is community-oriented or small."""
    name_lower = studio.get("name", "").lower()
    num_styles = len(studio.get("styles", []))
    return "community" in name_lower or "verein" in name_lower or num_styles <= 2


def pick_price(lo, hi, fraction):
    """Pick a price in range based on fraction 0-1, rounded to nearest int."""
    return round(lo + (hi - lo) * fraction)


def generate_pricing(studio, canton_key):
    tier = get_tier(canton_key)
    ranges = TIERS[tier]
    frac = studio_hash(studio.get("name", studio.get("id", "")))

    pricing = {}
    for key in ("single", "card_10", "monthly", "trial"):
        lo, hi = ranges[key]
        pricing[key] = pick_price(lo, hi, frac)

    # Adjust for hot yoga (+15%)
    if is_hot(studio):
        for key in ("single", "card_10", "monthly", "trial"):
            pricing[key] = round(pricing[key] * 1.15)

    # Adjust for community/small studios (-10%)
    if is_community(studio):
        for key in ("single", "card_10", "monthly", "trial"):
            pricing[key] = round(pricing[key] * 0.90)

    # Larger studios with many styles: nudge up slightly
    num_styles = len(studio.get("styles", []))
    if num_styles >= 8:
        bump = 1 + 0.02 * min(num_styles - 7, 5)  # up to +10%
        for key in ("single", "card_10", "monthly", "trial"):
            pricing[key] = round(pricing[key] * bump)

    pricing["currency"] = "CHF"
    pricing["note"] = "Richtpreise"
    return pricing


def main():
    pattern = os.path.join(DATA_DIR, "studios_*.json")
    files = sorted(f for f in glob.glob(pattern) if not f.endswith(".enc.json"))
    print(f"Found {len(files)} studio files to process.\n")

    total_added = 0
    total_skipped = 0

    for filepath in files:
        filename = os.path.basename(filepath)
        # Extract canton key from filename: studios_<canton>.json
        canton_key = filename.replace("studios_", "").replace(".json", "")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        added = 0
        skipped = 0
        for studio in data.get("studios", []):
            if "pricing" in studio:
                skipped += 1
                continue
            studio["pricing"] = generate_pricing(studio, canton_key)
            added += 1

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

        print(f"  {filename}: {added} added, {skipped} kept existing")
        total_added += added
        total_skipped += skipped

    print(f"\nDone! Added pricing to {total_added} studios, kept {total_skipped} existing.")


if __name__ == "__main__":
    main()
