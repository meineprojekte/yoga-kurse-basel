#!/usr/bin/env python3
"""Sanitize scraped data before it is published.

Scraping from many sources produces a small amount of garbage that hurts trust
and breaks the schedule UI / Event schema. This removes the clearly-broken
entries (verified high-precision rules — no legit class names are affected) and
nulls impossible prices. Idempotent. Run after scrape_all.py and before
encryption / page generation (wired into .github/workflows/scrape.yml).

Rules:
  Schedule classes are dropped if ANY of:
    - end time <= start time (both valid HH:MM)  -> impossible duration
    - class_name has a clock time glued to a letter, e.g. "10:00RachelVinyasa"
    - class_name is long (>40) camelCase concatenation, e.g. "22./23.26MitAlex..."
  Pricing: a monthly price < CHF 40 is impossible (it's a mislabeled drop-in/
    trial) -> set to null. High/ambiguous values are left untouched.
"""
import json, glob, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'data')

CLOCK_GLUE = re.compile(r'\d{1,2}:\d{2}[A-Za-zÄÖÜ]')
CAMEL = re.compile(r'[a-zäöü][A-ZÄÖÜ][a-zäöü]')
TIME_RE = re.compile(r'^(\d{1,2}):(\d{2})$')


def minutes(t):
    if not isinstance(t, str):
        return None
    m = TIME_RE.match(t.strip())
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def is_garbage_class(c):
    name = c.get('class_name', '') or ''
    s, e = minutes(c.get('time_start', '')), minutes(c.get('time_end', ''))
    if s is not None and e is not None and e <= s:
        return True
    if CLOCK_GLUE.search(name):
        return True
    if len(name) > 40 and CAMEL.search(name):
        return True
    return False


def clean_schedules():
    dropped = 0
    for sf in sorted(glob.glob(os.path.join(DATA_DIR, 'schedule_*.json'))):
        if '.enc.' in sf:
            continue
        d = json.load(open(sf, encoding='utf-8'))
        classes = d.get('classes', [])
        kept = [c for c in classes if not is_garbage_class(c)]
        if len(kept) != len(classes):
            dropped += len(classes) - len(kept)
            d['classes'] = kept
            json.dump(d, open(sf, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    return dropped


# A price outside these bounds is impossible for that field (mislabeled scrape),
# so it is nulled rather than shown. Bounds are deliberately wide — they only
# catch true impossibilities (e.g. a CHF 1100 single, a CHF 5 ten-class card),
# not merely unusual values, which are left in place.
IMPOSSIBLE = {
    "single":  (3, 100),
    "card_10": (60, 700),
    "monthly": (40, 600),
    "trial":   (0, 120),
}


def clean_prices():
    nulled = 0
    for sf in sorted(glob.glob(os.path.join(DATA_DIR, 'studios_*.json'))):
        if '.enc.' in sf:
            continue
        d = json.load(open(sf, encoding='utf-8'))
        changed = False
        for s in d.get('studios', []):
            p = s.get('pricing') or {}
            for field, (lo, hi) in IMPOSSIBLE.items():
                v = p.get(field)
                if isinstance(v, (int, float)) and not (lo <= v <= hi):
                    p[field] = None
                    nulled += 1
                    changed = True
        if changed:
            json.dump(d, open(sf, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    return nulled


def main():
    d = clean_schedules()
    p = clean_prices()
    print(f'clean_data: dropped {d} garbage classes, nulled {p} impossible prices')


if __name__ == '__main__':
    main()
