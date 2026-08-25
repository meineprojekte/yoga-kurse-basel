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


# --- plausibilita' -----------------------------------------------------------
# `verified: True` nello scraper NON significa "controllato da qualcuno": viene
# messo ogni volta che una regex trova un importo CHF vicino a una parola-chiave.
# Caso reale trovato: "Wasser CHF 5.- Für eine Erfrischung" finito come prezzo
# d'ingresso di uno studio che in realta' chiede CHF 38. In una tabella di
# confronto un numero sbagliato e' peggio di un numero assente: ordina male,
# mette lo studio in cima e induce in errore chi legge.
#
# Questi limiti non "correggono" nulla: tengono fuori dal confronto cio' che non
# puo' essere un prezzo di lezione, e lo mandano in revisione.
SINGLE_MIN = 12.0      # sotto: in CH non e' un drop-in (e' acqua, tè, un buono...)
SINGLE_MAX = 120.0     # sopra: e' un workshop o un abbonamento, non una lezione


def implausibile(p):
    """Perche' questo prezzo non entra nel confronto (stringa), o None se va bene."""
    single = p.get('single')
    if single is None:
        return 'nessun prezzo d\'ingresso'
    if single < SINGLE_MIN:
        return f'ingresso CHF {single}: sotto il minimo plausibile ({SINGLE_MIN:g})'
    if single > SINGLE_MAX:
        return f'ingresso CHF {single}: sopra il massimo plausibile ({SINGLE_MAX:g})'
    card = p.get('card_10')
    if card and card < single * 2:
        return f'10er CHF {card} < 2x l\'ingresso (CHF {single}): categorie scambiate'
    if card and card > single * 12:
        return f'10er CHF {card} > 12x l\'ingresso (CHF {single}): categorie scambiate'
    monthly = p.get('monthly')
    if monthly and monthly < single:
        return f'abo mensile CHF {monthly} < ingresso CHF {single}: incoerente'
    return None


def _num(value):
    """Prezzo utilizzabile: numero positivo. Scarta stringhe, None, 0 e negativi."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if value > 0 else None


def collect():
    labels = canton_labels()
    rows, respinti = [], []
    skipped = {'inattivi': 0, 'senza_prezzo': 0, 'non_verificati': 0,
               'senza_single': 0, 'implausibili': 0}

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
            candidato = {
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
            }
            motivo = implausibile(candidato)
            if motivo:
                skipped['implausibili'] += 1
                respinti.append({'name': candidato['name'], 'canton': slug,
                                 'motivo': motivo, 'url': candidato['url'],
                                 'pricing': {k: candidato.get(k) for k in
                                             ('single', 'card_10', 'monthly', 'trial')}})
                continue
            rows.append(candidato)

    rows.sort(key=lambda r: (r['single'], r['name'].lower()))
    return rows, skipped, respinti


def main():
    rows, skipped, respinti = collect()
    # I respinti non spariscono: finiscono in una lista da controllare a mano.
    with open(os.path.join(ROOT, 'tools', 'prices_da_verificare.json'), 'w',
              encoding='utf-8') as fh:
        json.dump({'count': len(respinti),
                   'note': 'Prezzi esclusi dal confronto perche' + chr(39) +
                           ' implausibili. Da controllare sul sito dello studio.',
                   'studios': sorted(respinti, key=lambda r: r['name'])},
                  fh, ensure_ascii=False, indent=1)
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
    if respinti:
        print(f'  {len(respinti)} esclusi come implausibili -> tools/prices_da_verificare.json')
    print(f'prices_all.json: {len(rows)} studi con prezzo verificato, '
          f'{len(per_canton)} cantoni, {len(text)} byte')
    print('  esclusi: ' + ', '.join(f'{k}={v}' for k, v in skipped.items() if v))
    if rows:
        print(f'  fascia: CHF {rows[0]["single"]} ({rows[0]["name"]}) '
              f'-> CHF {rows[-1]["single"]} ({rows[-1]["name"]})')


if __name__ == '__main__':
    main()
