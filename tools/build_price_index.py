#!/usr/bin/env python3
"""Costruisce l'indice NAZIONALE dei prezzi: data/prices_all.json

Perche' esiste. La tabella "Preisvergleich" della homepage promette *"Alle Studios
mit verifizierten Preisen im Überblick"*, ma il front-end tiene in memoria un
cantone per volta (`state.studios`, default Basilea). Risultato: la tabella
mostrava ~22 studi su 165 — l'87% dei prezzi raccolti restava invisibile.

Caricare i 26 file cantonali per costruirla sarebbe assurdo (26 richieste per una
tabella). Qui si pre-calcola **un solo file compatto** con i soli campi che la
tabella usa davvero, gia' ordinato per prezzo d'ingresso crescente.

Gira nel workflow PRIMA di encrypt_data.py, cosi' viene cifrato come gli altri.
Idempotente: a dati invariati riscrive un file identico e git non vede nulla.
"""
import json
import glob
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'data')
OUT = os.path.join(DATA_DIR, 'prices_all.json')

# I file cantonali usano 'basel', gli URL del sito 'basel-stadt'.
FILEKEY_TO_SLUG = {'basel': 'basel-stadt'}


def canton_labels():
    """id cantone -> nome tedesco, da data/cantons.json."""
    path = os.path.join(DATA_DIR, 'cantons.json')
    if not os.path.exists(path):
        return {}
    out = {}
    for c in json.load(open(path, encoding='utf-8')).get('cantons', []):
        name = c.get('name')
        out[c.get('id')] = name.get('de') if isinstance(name, dict) else (name or c.get('id'))
    return out


def _num(value):
    """Prezzo utilizzabile: numero positivo. Scarta stringhe, None, 0 e negativi."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if value > 0 else None


def collect():
    labels = canton_labels()
    rows, skipped = [], {'inattivi': 0, 'senza_prezzo': 0, 'non_verificati': 0, 'senza_single': 0}

    for path in sorted(glob.glob(os.path.join(DATA_DIR, 'studios_*.json'))):
        if '.enc.' in path:
            continue
        key = os.path.basename(path)[len('studios_'):-len('.json')]
        slug = FILEKEY_TO_SLUG.get(key, key)
        data = json.load(open(path, encoding='utf-8'))

        for s in data.get('studios', []):
            if s.get('active') is False:
                skipped['inattivi'] += 1
                continue
            p = s.get('pricing') or {}
            if not p:
                skipped['senza_prezzo'] += 1
                continue
            # La tabella confronta prezzi: mostrare un dato non verificato come se
            # lo fosse sarebbe peggio che non mostrarlo.
            if not p.get('verified'):
                skipped['non_verificati'] += 1
                continue
            single = _num(p.get('single'))
            if single is None:
                skipped['senza_single'] += 1
                continue

            addresses = s.get('addresses') or []
            city = (addresses[0].get('city') if addresses else '') or ''
            styles = [x for x in (s.get('styles') or []) if x]
            rows.append({
                'id': s.get('id', ''),
                'name': s.get('name', ''),
                'city': city,
                'canton': slug,
                'canton_label': labels.get(slug, slug),
                'single': single,
                'card_10': _num(p.get('card_10')),
                'monthly': _num(p.get('monthly')),
                # trial 0 = "prima lezione gratis": e' un'informazione, non un buco
                'trial': p.get('trial') if isinstance(p.get('trial'), (int, float))
                         and not isinstance(p.get('trial'), bool) and p.get('trial') >= 0 else None,
                'styles': styles[:3],
                'styles_more': max(0, len(styles) - 3),
                'url': p.get('source') or s.get('website') or '',
                'last_checked': (p.get('last_checked') or '')[:10],
            })

    rows.sort(key=lambda r: (r['single'], r['name'].lower()))
    return rows, skipped


def main():
    rows, skipped = collect()
    payload = {
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'count': len(rows),
        'note': 'Indice nazionale dei prezzi verificati. Generato da tools/build_price_index.py.',
        'studios': rows,
    }
    # separators compatti: il file viaggia verso il browser a ogni visita
    text = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))

    previous = None
    if os.path.exists(OUT):
        try:
            previous = json.load(open(OUT, encoding='utf-8'))
        except Exception:
            previous = None
    # Idempotenza: se cambia solo il timestamp, non riscrivere (eviti commit vuoti)
    if previous and previous.get('studios') == rows:
        print(f'prices_all.json invariato ({len(rows)} studi) — non riscritto')
        return

    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write(text)

    per_canton = {}
    for r in rows:
        per_canton[r['canton']] = per_canton.get(r['canton'], 0) + 1
    print(f'prices_all.json: {len(rows)} studi con prezzo verificato, '
          f'{len(per_canton)} cantoni, {len(text)} byte')
    print('  esclusi: ' + ', '.join(f'{k}={v}' for k, v in skipped.items() if v))
    if rows:
        print(f'  fascia: CHF {rows[0]["single"]} ({rows[0]["name"]}) '
              f'-> CHF {rows[-1]["single"]} ({rows[-1]["name"]})')


if __name__ == '__main__':
    main()
