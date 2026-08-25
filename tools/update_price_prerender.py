#!/usr/bin/env python3
"""Rigenera il fallback pre-renderizzato della tabella prezzi in index.html.

Il <tbody id="comparisonBody"> contiene HTML statico che JavaScript sostituisce
appena l'indice nazionale e' caricato. Serve a due cose: i motori di ricerca e
chi ha JS disattivato. Finora conteneva 10 studi **solo di Basilea**, scritti a
mano e mai piu' aggiornati: un fallback che rappresentava male il sito.

Ora si rigenera dai dati veri (data/prices_all.json), su base **nazionale**.

Perche' non tutti e 165: questo blocco pesa su OGNI visita alla homepage, e viene
sostituito dal JS dopo poche centinaia di millisecondi. Metterceli tutti
aggiungerebbe ~60 KB a ogni caricamento per un contenuto che quasi nessuno vede.
TOP_N e' un compromesso esplicito e regolabile — la tabella completa resta quella
costruita dal JS, che mostra tutti i 165.

Idempotente. Gira nel workflow dopo build_price_index.py.
"""
import json
import os
import re
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, 'index.html')
PRICES = os.path.join(ROOT, 'data', 'prices_all.json')

TOP_N = 30
START = '<!-- Pre-rendered pricing for SEO — replaced by JS -->'
TBODY_OPEN = '<tbody id="comparisonBody">'
TBODY_CLOSE = '</tbody>'
IND = ' ' * 28


def chf(value):
    if value is None:
        return '&mdash;'
    if value == 0:
        return 'Gratis'
    text = f'{value:.2f}'.rstrip('0').rstrip('.') if isinstance(value, float) else str(value)
    return 'CHF ' + text


def link_rel(url):
    """Stessa regola di app.js: i link di prenotazione sono 'sponsored'."""
    for token in ('eversports.', 'classpass.', 'mindbody', 'momoyoga.', 'fitogram.'):
        if token in (url or ''):
            return 'sponsored noopener noreferrer'
    return 'nofollow noopener noreferrer'


def build_rows(studios):
    out = []
    for i, s in enumerate(studios[:TOP_N]):
        styles = ', '.join(s.get('styles') or [])
        if s.get('styles_more'):
            styles += f" +{s['styles_more']}"
        cls = 'comp-row-even' if i % 2 == 0 else 'comp-row-odd'
        city = f' <span class="comp-city">({escape(s["city"])})</span>' if s.get('city') else ''
        url = s.get('url') or ''
        link = (f'<a href="{escape(url)}" target="_blank" rel="{link_rel(url)}">&#8599;</a>'
                if url else '')
        out.append(
            f'{IND}<tr class="{cls}">'
            f'<td class="comp-studio" data-label="#">{i + 1}</td>'
            f'<td class="comp-name" data-label="Studio"><strong>{escape(s["name"])}</strong>{city}</td>'
            f'<td class="comp-price" data-label="Einzeleintritt"><strong>{chf(s.get("single"))}</strong></td>'
            f'<td class="comp-price" data-label="10er-Karte">{chf(s.get("card_10"))}</td>'
            f'<td class="comp-price" data-label="Monatsabo">{chf(s.get("monthly"))}</td>'
            f'<td class="comp-price" data-label="Probestunde">{chf(s.get("trial"))}</td>'
            f'<td class="comp-styles" data-label="Stile"><small>{escape(styles)}</small></td>'
            f'<td class="comp-link" data-label="Link">{link}</td>'
            f'</tr>'
        )
    return out


def main():
    # Questo script gira nella stessa pipeline che aggiorna orari e prezzi. Se
    # qualcosa qui non torna si esce SENZA errore: il fallback resta quello di
    # prima (vecchio ma valido) e soprattutto il commit dei dati va avanti.
    # Fallire qui vorrebbe dire bloccare l'aggiornamento dell'intero sito per un
    # blocco di HTML che il JavaScript sostituisce comunque dopo mezzo secondo.
    if not os.path.exists(PRICES):
        print('data/prices_all.json mancante: salto il fallback (lancia build_price_index.py)')
        return
    try:
        data = json.load(open(PRICES, encoding='utf-8'))
    except Exception as e:
        print(f'indice prezzi illeggibile ({e}): salto il fallback')
        return
    studios = data.get('studios', [])
    if not studios:
        print('indice prezzi vuoto: non tocco index.html')
        return

    html = open(INDEX, encoding='utf-8').read()
    open_at = html.find(TBODY_OPEN)
    if open_at < 0:
        print('<tbody id="comparisonBody"> non trovato in index.html: salto')
        return
    body_start = open_at + len(TBODY_OPEN)
    close_at = html.find(TBODY_CLOSE, body_start)
    if close_at < 0:
        print('</tbody> di chiusura non trovato: salto')
        return

    cantons = len({s['canton'] for s in studios[:TOP_N]})
    block = ('\n' + IND + START + '\n' +
             IND + f'<!-- {TOP_N} studi piu\' economici su {len(studios)} '
                   f'({cantons} cantoni). Tabella completa via JS. -->\n' +
             '\n'.join(build_rows(studios)) + '\n' + ' ' * 24)

    updated = html[:body_start] + block + html[close_at:]
    if updated == html:
        print('fallback prezzi gia\' aggiornato — nessuna modifica')
        return
    open(INDEX, 'w', encoding='utf-8').write(updated)
    print(f'index.html: fallback prezzi rigenerato — {min(TOP_N, len(studios))} righe '
          f'da {cantons} cantoni (su {len(studios)} studi totali)')


if __name__ == '__main__':
    main()
