#!/bin/bash
# Script per aggiornare tutti gli URL dal dominio GitHub Pages al dominio personalizzato
# Uso: bash tools/switch_domain.sh
#
# ATTENZIONE: Esegui SOLO dopo aver configurato il DNS e verificato che yoga-schweiz.ch funziona!

OLD_DOMAIN="https://meineprojekte.github.io/yoga-kurse-basel"
NEW_DOMAIN="https://yoga-schweiz.ch"

echo "=== Aggiornamento URL da GitHub Pages a dominio personalizzato ==="
echo "Da: $OLD_DOMAIN"
echo "A:  $NEW_DOMAIN"
echo ""

# Trova tutti i file HTML, XML, JSON, JS, TXT che contengono il vecchio dominio
FILES=$(grep -rl "$OLD_DOMAIN" --include="*.html" --include="*.xml" --include="*.json" --include="*.js" --include="*.txt" .)

COUNT=$(echo "$FILES" | wc -l)
echo "File da aggiornare: $COUNT"
echo ""

for file in $FILES; do
    sed -i '' "s|$OLD_DOMAIN|$NEW_DOMAIN|g" "$file"
    echo "  Aggiornato: $file"
done

echo ""
echo "=== Fatto! Tutti gli URL sono stati aggiornati. ==="
echo "Ricorda di fare commit e push:"
echo "  git add -A && git commit -m 'chore: switch to custom domain yoga-schweiz.ch' && git push"
