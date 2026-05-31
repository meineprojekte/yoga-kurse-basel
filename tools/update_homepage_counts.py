#!/usr/bin/env python3
"""Keep index.html counts and dates in sync with the live data.

The homepage is hand-maintained, so its counts used to drift out of date.
This recomputes them from data/ and rewrites:
  - in <head> only: total studios ("... Studios"), total classes ("... Kurse"),
    JSON-LD numberOfItems and dateModified;
  - anywhere: the per-canton counts shown in canton links, e.g.
    <a href="./kanton/zurich/">Yoga Kurse Zürich (44)</a>  -> active count.
Contextual body numbers (e.g. "Zürich mit über 40 Studios") are never touched.
Idempotent. Wired into .github/workflows/scrape.yml.
"""
import json, glob, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'data')
INDEX = os.path.join(ROOT, 'index.html')


def slug_to_key(slug):
    # canton URL slug -> studios_*.json file key (only basel-stadt differs)
    return 'basel' if slug == 'basel-stadt' else slug


def compute():
    studios = classes = 0
    latest = '2026-01-01'
    per_canton = {}  # file key -> active studio count
    for sf in sorted(glob.glob(os.path.join(DATA_DIR, 'studios_*.json'))):
        if '.enc.' in sf:
            continue
        key = os.path.basename(sf)[len('studios_'):-len('.json')]
        d = json.load(open(sf, encoding='utf-8'))
        active = [s for s in d.get('studios', []) if s.get('active', True)]
        active_ids = {s.get('id') for s in active}
        per_canton[key] = len(active)
        studios += len(active)
        lu = (d.get('last_updated') or '')[:10]
        if lu and lu > latest:
            latest = lu
        schf = os.path.join(DATA_DIR, f'schedule_{key}.json')
        if os.path.exists(schf):
            sd = json.load(open(schf, encoding='utf-8'))
            classes += len([c for c in sd.get('classes', []) if c.get('studio_id') in active_ids])
            mlu = (sd.get('_meta', {}).get('last_updated') or '')[:10]
            if mlu and mlu > latest:
                latest = mlu
    return studios, classes, latest, per_canton


def main():
    studios, classes, latest, per_canton = compute()
    html = open(INDEX, encoding='utf-8').read()
    head, sep, body = html.partition('</head>')

    # Totals + date: only inside <head> (title + meta + JSON-LD all live there)
    head = re.sub(r'\d+(\s*(?:Yoga-)?Studios)', lambda m: f'{studios}{m.group(1)}', head)
    head = re.sub(r'\d+(\s+Kurse)', lambda m: f'{classes}{m.group(1)}', head)
    head = re.sub(r'("numberOfItems":\s*)\d+', lambda m: f'{m.group(1)}{studios}', head)
    head = re.sub(r'("dateModified":\s*")\d{4}-\d{2}-\d{2}(")',
                  lambda m: f'{m.group(1)}{latest}{m.group(2)}', head)

    new_html = head + sep + body

    # Per-canton counts in canton links, matched by slug -> never touches prose.
    def fix_canton(m):
        key = slug_to_key(m.group(2))
        n = per_canton.get(key)
        return f'{m.group(1)}{n}{m.group(3)}' if n is not None else m.group(0)
    new_html = re.sub(r'(kanton/([a-z-]+)/">[^<()]*\()\d+(\))', fix_canton, new_html)

    if new_html != html:
        open(INDEX, 'w', encoding='utf-8').write(new_html)
        print(f'index.html updated: {studios} studios, {classes} classes, dateModified {latest}')
    else:
        print(f'index.html already in sync: {studios} studios, {classes} classes, {latest}')


if __name__ == '__main__':
    main()
