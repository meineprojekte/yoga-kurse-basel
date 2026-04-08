#!/bin/bash
# Build script: minify JS, CSS, HTML for production
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Building production assets ==="

# 1. Minify JS
echo "[1/3] Minifying app.js..."
npx terser js/app.js \
  --compress drop_console=true,passes=2 \
  --mangle \
  --output js/app.min.js
JS_ORIG=$(wc -c < js/app.js)
JS_MIN=$(wc -c < js/app.min.js)
echo "  app.js: ${JS_ORIG}B -> ${JS_MIN}B ($(( (JS_ORIG - JS_MIN) * 100 / JS_ORIG ))% smaller)"

# 2. Minify CSS
echo "[2/3] Minifying style.css..."
npx cleancss -o css/style.min.css css/style.css
CSS_ORIG=$(wc -c < css/style.css)
CSS_MIN=$(wc -c < css/style.min.css)
echo "  style.css: ${CSS_ORIG}B -> ${CSS_MIN}B ($(( (CSS_ORIG - CSS_MIN) * 100 / CSS_ORIG ))% smaller)"

# 3. Minify HTML (index.html)
echo "[3/3] Minifying index.html..."
npx html-minifier-terser \
  --collapse-whitespace \
  --remove-comments \
  --remove-redundant-attributes \
  --minify-css true \
  --minify-js true \
  -o index.min.html \
  index.html
HTML_ORIG=$(wc -c < index.html)
HTML_MIN=$(wc -c < index.min.html)
echo "  index.html: ${HTML_ORIG}B -> ${HTML_MIN}B ($(( (HTML_ORIG - HTML_MIN) * 100 / HTML_ORIG ))% smaller)"

echo ""
echo "=== Build complete ==="
echo "Production files: js/app.min.js, css/style.min.css, index.min.html"
echo ""
echo "To use minified files, update index.html references:"
echo "  ./js/app.js -> ./js/app.min.js"
echo "  ./css/style.css -> ./css/style.min.css"
