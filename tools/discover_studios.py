#!/usr/bin/env python3
"""Scopre studi di yoga non ancora presenti nel dataset e ne prepara la scheda.

**Non gira nella CI, e volutamente.** Aggiungere studi a un comparatore e' una
decisione editoriale: un bot che ogni lunedi' si inventa nuove schede senza che
nessuno le guardi e' esattamente il modo di riempire il sito di doppioni, palestre
che fanno "anche yoga" e insegnanti privati senza sede. Questo strumento fa il
lavoro pesante e produce una **coda da rivedere**; l'inserimento e' un secondo
passo esplicito (tools/merge_discovered.py).

Cosa fa per ogni candidato:
  - verifica che il sito risponda ed estrae nome, descrizione, stili;
  - trova la pagina degli orari e quella dei prezzi;
  - raccoglie indirizzo, telefono, email (anche dalla pagina contatti);
  - geocodifica l'indirizzo con **api3.geo.admin.ch**, il servizio ufficiale
    di Swisstopo, per ottenere lat/lng come gli altri record;
  - riconosce la piattaforma di prenotazione (Eversports, Wix, Momoyoga...),
    che e' cio' che poi permette allo scraper di prendere gli orari.

Uso:
    python3 tools/discover_studios.py --input tools/candidates.json
    python3 tools/discover_studios.py --url https://studio.ch --canton ticino
"""
import argparse
import glob
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'data')
OUT = os.path.join(ROOT, 'tools', 'discovered_studios.json')

# webfetch, se disponibile, da' cascata + cortesia + robots; altrimenti requests.
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), 'accesso a pagine online'))
try:
    from webfetch import FetchConfig, Fetcher, extract, structured
    HAVE_WEBFETCH = True
except Exception:
    HAVE_WEBFETCH = False

GEOADMIN = 'https://api3.geo.admin.ch/rest/services/ech/SearchServer'

STYLE_VOCAB = [
    'Vinyasa', 'Hatha', 'Yin', 'Ashtanga', 'Kundalini', 'Power Yoga', 'Bikram',
    'Hot Yoga', 'Restorative', 'Prenatal', 'Schwangerschaftsyoga', 'Aerial',
    'Jivamukti', 'Flow', 'Meditation', 'Pilates', 'Iyengar', 'Yoga Nidra',
    'Faszien', 'Rückenyoga', 'Kinderyoga',
]
PLATFORM_SIGNS = [
    ('eversports', ['eversports']), ('momoyoga', ['momoyoga']),
    ('mindbody', ['mindbody', 'healcode']), ('bsport', ['bsport']),
    ('sportsnow', ['sportsnow']), ('fitogram', ['fitogram']),
    ('acuity', ['acuityscheduling']), ('wix', ['wix-bookings', 'parastorage']),
    ('squarespace', ['squarespace']), ('woocommerce', ['woocommerce']),
    ('wordpress', ['wp-content', 'wp-json']),
]
SCHED_WORDS = re.compile(
    r'stundenplan|kursplan|horaire|orari|schedule|planning|agenda|kurse|cours|classes|lezioni', re.I)
PRICE_WORDS = re.compile(r'preis|tarif|prezz|prix|pricing|abo|mitglied|karte|abbonament|angebot', re.I)
CONTACT_WORDS = re.compile(r'kontakt|contact|contatt|impressum|ueber-uns|about', re.I)

EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
PHONE = re.compile(r'(?:\+41|0041|\b0)\s?(?:\(0\))?\s?\d{2}[\s./-]?\d{3}[\s./-]?\d{2}[\s./-]?\d{2}')
SWISS_ADDR = re.compile(
    r'([A-ZÀ-Ü][\wÀ-ÿ.\-]*(?:\s+[A-ZÀ-Ü\d][\wÀ-ÿ.\-]*){0,3}\s+\d+[a-z]?)\s*,?\s*'
    r'(\d{4})\s+([A-ZÀ-Ü][A-Za-zÀ-ÿ\-\' ]{2,25})')


def slugify(name):
    s = name.lower()
    for a, b in (('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('à', 'a'), ('è', 'e'),
                 ('é', 'e'), ('ç', 'c'), ('ß', 'ss')):
        s = s.replace(a, b)
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return re.sub(r'-+', '-', s)[:40]


def existing_index():
    """Domini e id gia' presenti, per non proporre doppioni."""
    domains, ids, names = set(), set(), set()
    for path in glob.glob(os.path.join(DATA_DIR, 'studios_*.json')):
        if '.enc.' in path:
            continue
        for s in json.load(open(path, encoding='utf-8')).get('studios', []):
            ids.add(s.get('id', ''))
            names.add((s.get('name') or '').lower().strip())
            m = re.search(r'https?://(?:www\.)?([^/]+)', s.get('website') or '')
            if m:
                domains.add(m.group(1).lower())
    return domains, ids, names


class Client:
    def __init__(self, contact=None):
        if HAVE_WEBFETCH:
            cfg = FetchConfig.for_locale('de-CH', 'Europe/Zurich')
            cfg.contact = contact
            cfg.min_delay_per_host = 1.5      # discovery non ha fretta
            self.f = Fetcher(cfg)
        else:
            self.f = None

    def get(self, url, render=False):
        """(html, url_finale) oppure (None, motivo)."""
        if self.f is not None:
            r = self.f.fetch(url, render=True if render else None)
            if not r.ok:
                return None, (r.block_reason or r.error or f'status {r.status}')
            return r.full_html, r.url
        import requests
        try:
            r = requests.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0 (webfetch discovery)'})
            return (r.text, r.url) if r.status_code < 400 else (None, f'status {r.status_code}')
        except Exception as e:
            return None, f'{type(e).__name__}'

    def text(self, html, url):
        if HAVE_WEBFETCH:
            return extract.to_text(html, url)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        for t in soup(['script', 'style', 'noscript']):
            t.decompose()
        return re.sub(r'\n{3,}', '\n\n', soup.get_text('\n'))

    def links(self, html, url):
        if HAVE_WEBFETCH:
            return extract.links(html, url)
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin
        soup = BeautifulSoup(html, 'lxml')
        return [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]

    def meta(self, html):
        if HAVE_WEBFETCH:
            return extract.meta(html)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        out = {}
        if soup.title:
            out['title'] = soup.title.get_text(strip=True)
        for m in soup.find_all('meta'):
            k = (m.get('name') or m.get('property') or '').lower()
            if k in ('description', 'og:description') and m.get('content'):
                out[k] = m['content'].strip()
        return out


def geocode(address):
    """Indirizzo -> (lat, lng) dal servizio ufficiale Swisstopo. None se non trovato."""
    if not address:
        return None, None
    params = urllib.parse.urlencode(
        {'searchText': address, 'type': 'locations', 'sr': '4326', 'limit': 1})
    try:
        req = urllib.request.Request(f'{GEOADMIN}?{params}',
                                     headers={'User-Agent': 'yogakurse-discovery'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        results = data.get('results') or []
        if not results:
            return None, None
        attrs = results[0].get('attrs', {})
        return attrs.get('lat'), attrs.get('lon')
    except Exception:
        return None, None


def detect_platform(html, links):
    hay = (html or '').lower() + ' ' + ' '.join(links).lower()
    for name, signs in PLATFORM_SIGNS:
        if any(s in hay for s in signs):
            return name
    return 'website'


def pick(links, pattern, base_host, limit=1):
    out = []
    for l in links:
        if base_host in l and pattern.search(l) and l not in out:
            out.append(l)
        if len(out) >= limit:
            break
    return out


def profile(client, name, url, canton, render=False):
    html, final = client.get(url, render=render)
    if html is None:
        return {'name': name, 'canton': canton, 'website': url, 'error': final}

    host = urllib.parse.urlparse(final).netloc.replace('www.', '')
    text = client.text(html, final)
    links = client.links(html, final)
    meta = client.meta(html)

    # la pagina contatti spesso ha indirizzo/telefono che la home non mostra
    # La pagina contatti spesso ha indirizzo/telefono che la home non mostra. Non
    # sempre e' linkata nella navigazione (o il link e' generato via JS), quindi
    # oltre ai link trovati si sondano i percorsi convenzionali dei quattro idiomi.
    contact_text = ''
    tried = []
    for cu in pick(links, CONTACT_WORDS, host, limit=2):
        tried.append(cu)
    origin = f"{urllib.parse.urlparse(final).scheme}://{urllib.parse.urlparse(final).netloc}"
    for path in ('/kontakt', '/contact', '/contatti', '/impressum', '/kontakt/',
                 '/contact/', '/ueber-uns', '/about', '/chi-siamo', '/a-propos'):
        if len(tried) >= 5:
            break
        candidate = origin + path
        if candidate not in tried:
            tried.append(candidate)
    for cu in tried:
        chtml, curl = client.get(cu, render=render)
        if not chtml:
            continue
        chunk = client.text(chtml, curl)
        contact_text += '\n' + chunk
        # basta il primo che porta davvero un indirizzo svizzero
        if SWISS_ADDR.search(chunk):
            break

    blob = text + '\n' + contact_text
    addr_m = SWISS_ADDR.search(blob)
    street, zipc, city = (addr_m.group(1).strip(), addr_m.group(2), addr_m.group(3).strip()) \
        if addr_m else ('', '', '')
    # scarta i falsi positivi tipo "2026 Consultez" (un anno seguito da parole)
    if zipc and zipc.startswith('20') and not street:
        street = zipc = city = ''

    emails = [e for e in EMAIL.findall(blob)
              if not e.lower().endswith(('.png', '.jpg', '.webp'))
              and 'sentry' not in e.lower()]
    phones = PHONE.findall(blob)

    lat = lng = None
    if street and city:
        lat, lng = geocode(f'{street}, {zipc} {city}')
    elif city:
        lat, lng = geocode(f'{zipc} {city}')

    styles = [s for s in STYLE_VOCAB if re.search(r'\b' + re.escape(s), blob, re.I)]
    sched = pick(links, SCHED_WORDS, host)
    prices = pick(links, PRICE_WORDS, host)

    return {
        'id': slugify(name),
        'name': name,
        'canton': canton,
        'website': final,
        'schedule_url': sched[0] if sched else final,
        'price_url': prices[0] if prices else '',
        'addresses': ([{'street': street, 'zip': zipc, 'city': city, 'label': ''}]
                      if street or city else []),
        'phone': phones[0].strip() if phones else '',
        'email': emails[0] if emails else '',
        'styles': styles[:10],
        'description': (meta.get('og:description') or meta.get('description') or '')[:280],
        'booking_platform': detect_platform(html, links),
        'lat': lat, 'lng': lng,
        'active': True,
        'teachers': [], 'classes': [], 'languages': [], 'special_features': [],
        'drop_in': None, 'hours': '',
        'scrape_status': 'discovered',
        'discovered_at': time.strftime('%Y-%m-%d'),
        'needs_review': True,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--input', help='JSON con [{name, url, canton}, ...]')
    ap.add_argument('--url'), ap.add_argument('--name'), ap.add_argument('--canton')
    ap.add_argument('--contact', default=None, help='email da mettere nello User-Agent')
    args = ap.parse_args()

    if args.input:
        cands = json.load(open(args.input, encoding='utf-8'))
    elif args.url:
        cands = [{'url': args.url, 'name': args.name or args.url, 'canton': args.canton or ''}]
    else:
        raise SystemExit('serve --input oppure --url')

    domains, ids, names = existing_index()
    client = Client(args.contact)
    out, skipped = [], 0

    for c in cands:
        url = c['url']
        host = re.sub(r'^www\.', '', urllib.parse.urlparse(url).netloc).lower()
        if host in domains or (c.get('name') or '').lower().strip() in names:
            skipped += 1
            continue
        rec = profile(client, c.get('name') or host, url, c.get('canton', ''))
        # Wix/Squarespace & co. rendono indirizzo e recapiti via JavaScript: se la
        # scheda e' rimasta vuota, vale la pena riprovare con un browser vero.
        if not rec.get('error') and not rec.get('addresses'):
            retry = profile(client, c.get('name') or host, url, c.get('canton', ''), render=True)
            if not retry.get('error') and (retry.get('addresses') or retry.get('phone')
                                           or len(retry.get('styles') or []) > len(rec.get('styles') or [])):
                retry['id'] = rec['id']
                retry['rendered'] = True
                rec = retry
        base = rec.get('id', '')
        n = 2
        while rec.get('id') in ids:            # id unico anche fra i nuovi
            rec['id'] = f'{base}-{n}'; n += 1
        ids.add(rec.get('id', ''))
        out.append(rec)
        status = rec.get('error') or f"{rec['booking_platform']}, {len(rec['styles'])} stili"
        print(f"  {rec['name'][:34]:<36}{status}")

    json.dump({'generated': time.strftime('%Y-%m-%dT%H:%M:%SZ'), 'count': len(out),
               'note': 'Coda da rivedere. Inserimento: tools/merge_discovered.py',
               'studios': out}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    ok = [r for r in out if not r.get('error')]
    print(f"\n{len(ok)} schede pronte, {len(out) - len(ok)} con errore, "
          f"{skipped} gia' presenti -> {OUT}")


if __name__ == '__main__':
    main()
