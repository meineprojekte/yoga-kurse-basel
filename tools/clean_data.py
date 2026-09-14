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


# --- German umlaut restoration -------------------------------------------
# Part of the seed data was typed with umlauts folded to ASCII. Bern is the
# extreme case (3 real umlauts against 144 folded sequences, where Zurich has
# 138 and Basel 80). Its page therefore read "fuer", "Koeniz" and "Muenstergasse"
# where every other canton read "für", "Köniz" and "Münstergasse" — one template,
# but a visibly worse-looking page. The divergence is in the data, so it is
# repaired here, before encryption and page generation.
#
# A blanket ae/oe/ue -> ä/ö/ü rule is NOT possible: the data legitimately holds
# "Tuesday" (495x), "Aerial Yoga" (58x), "Rue"/"Avenue"/"Boutique"/"Dominique",
# "aktuelle", "neue", "individuelle", "Frauenfeld", "Neuenburg" — and Zurich's
# "Oerlikon" plus Basel's "Aeschenvorstadt"/"Aeschengraben", whose official
# spelling really is ASCII. So this is an allowlist, verified word by word;
# anything not listed is left exactly as it is.
#
# Deliberately NOT included: surnames (Baer, Schaer, Schluep, Oehler, Voegeli,
# Koechlin, Kraehenbuehl, Aemisegger, Naepflin, Boesch). Both spellings are real
# Swiss surnames and guessing would misname a person — clean_data reports them
# instead, so they can be decided case by case.
UMLAUT_FIX = {
    # everyday German
    'fuer': 'für', 'ueber': 'über', 'moeglich': 'möglich', 'noetig': 'nötig',
    'schoenen': 'schönen', 'persoenlichen': 'persönlichen',
    'taeglich': 'täglich', 'taegliche': 'tägliche', 'taeglichen': 'täglichen',
    'woechentlich': 'wöchentlich', 'woechentliche': 'wöchentliche',
    'gegruendet': 'gegründet', 'geschuetzt': 'geschützt',
    'geschuetzten': 'geschützten', 'gefuehrt': 'geführt',
    'anfaenger': 'Anfänger', 'anfaengerfreundlich': 'Anfängerfreundlich',
    'aelteste': 'Älteste', 'spiritualitaet': 'Spiritualität',
    'waerme': 'Wärme', 'vielfaeltigem': 'vielfältigem', 'baeumen': 'Bäumen',
    'wirbelsaeule': 'Wirbelsäule', 'buero': 'Büro',
    'rueckbildung': 'Rückbildung', 'ernaehrungsberatung': 'Ernährungsberatung',
    # place and street names (official spelling carries the umlaut)
    'koeniz': 'Köniz', 'muenstergasse': 'Münstergasse',
    'muensterplatz': 'Münsterplatz', 'muenzgraben': 'Münzgraben',
    'laenggasse': 'Länggasse', 'schaenzlihalde': 'Schänzlihalde',
    'schloesslistrasse': 'Schlösslistrasse',
    'schulhausgaessli': 'Schulhausgässli',
    'gerbergaesslein': 'Gerbergässlein',
}

# Identifiers and links must keep their ASCII form or they stop resolving:
# studio_id is the schedule -> studio join key, and the rest are URLs/emails.
UMLAUT_SKIP_KEYS = {
    'id', 'studio_id', 'canton', 'slug', 'source', 'url', 'website', 'email',
    'schedule', 'schedule_url', 'booking_url', 'pricing', 'instagram',
    'facebook', 'image', 'logo',
}
# Second guard: a link can appear under an unexpected key too.
URLISH = re.compile(r'https?://|www\.|\S+@\S+|\.(?:ch|com|net|org|io|de|fr)\b')
UMLAUT_RE = re.compile(
    r'\b(' + '|'.join(sorted(UMLAUT_FIX, key=len, reverse=True)) + r')\b',
    re.IGNORECASE)
# Folded-looking words that are NOT in the allowlist: reported, never changed.
FOLDED_RE = re.compile(r'\b[A-Za-zÄÖÜäöüß]*(?:ae|oe|ue)[A-Za-zÄÖÜäöüß]*\b')


def _restore_word(m):
    word = m.group(0)
    fixed = UMLAUT_FIX[word.lower()]
    # Follow the casing of the source word, not of the table entry, so that both
    # "Gefuehrt" -> "Geführt" and "gefuehrt" -> "geführt" come out right.
    head = fixed[0].upper() if word[0].isupper() else fixed[0].lower()
    return head + fixed[1:]


def _restore_in(value, key, unknown):
    if key in UMLAUT_SKIP_KEYS or URLISH.search(value):
        return value
    fixed = UMLAUT_RE.sub(_restore_word, value)
    for w in FOLDED_RE.findall(fixed):
        if w.lower() not in UMLAUT_FIX:
            unknown.add(w)
    return fixed


def _walk(node, key, unknown):
    """Rewrite every string in the tree, remembering the key it sits under."""
    if isinstance(node, dict):
        return {k: _walk(v, k, unknown) for k, v in node.items()}
    if isinstance(node, list):
        return [_walk(v, key, unknown) for v in node]
    if isinstance(node, str):
        return _restore_in(node, key, unknown)
    return node


def restore_umlauts():
    """Undo ASCII-folded umlauts so every canton reads the same. Idempotent."""
    changed_files = 0
    unknown = set()
    for sf in sorted(glob.glob(os.path.join(DATA_DIR, 'studios_*.json'))
                     + glob.glob(os.path.join(DATA_DIR, 'schedule_*.json'))):
        if '.enc.' in sf:
            continue
        before = open(sf, encoding='utf-8').read()
        fixed = _walk(json.loads(before), '', unknown)
        after = json.dumps(fixed, ensure_ascii=False, indent=2)
        if after != before.rstrip('\n'):
            open(sf, 'w', encoding='utf-8').write(after)
            changed_files += 1
    return changed_files, unknown


def main():
    d = clean_schedules()
    p = clean_prices()
    u, unknown = restore_umlauts()
    print(f'clean_data: dropped {d} garbage classes, nulled {p} impossible prices, '
          f'restored umlauts in {u} files')
    if unknown:
        # Not a failure: these are words holding ae/oe/ue that the allowlist does
        # not cover (English/French/Spanish, surnames, officially-ASCII places).
        # Listed so a new genuinely-folded German word gets noticed and added.
        print(f'  {len(unknown)} unlisted ae/oe/ue words left untouched (review if German): '
              + ', '.join(sorted(unknown)[:25]) + (' ...' if len(unknown) > 25 else ''))


if __name__ == '__main__':
    main()
