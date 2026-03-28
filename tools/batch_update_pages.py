#!/usr/bin/env python3
"""
Batch SEO & Accessibility update for all sub-pages.
Updates canton pages (26), yoga style pages (58), blog pages (5), and sitemap.xml.
"""

import os
import re
import json
import glob
import shutil
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = "https://meineprojekte.github.io/yoga-kurse-basel"
TODAY = date.today().isoformat()

OG_IMAGE_URL = f"{BASE_URL}/img/og-image.png"

# Counters
stats = {
    'canton_updated': 0,
    'yoga_updated': 0,
    'blog_updated': 0,
    'sitemap_updated': False,
    'errors': []
}


def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def backup_file(path):
    backup_path = path + '.bak'
    if not os.path.exists(backup_path):
        shutil.copy2(path, backup_path)


# ============================================================
# CANTON PAGE UPDATES (26 files)
# ============================================================

def update_canton_page(filepath):
    """Apply all SEO/accessibility updates to a canton page."""
    content = read_file(filepath)
    original = content

    # 1. Add twitter:image meta tag if missing
    if 'twitter:image' not in content:
        content = content.replace(
            '<meta name="twitter:description"',
            f'<meta name="twitter:image" content="{OG_IMAGE_URL}">\n    <meta name="twitter:description"'
        )
        # If that didn't work (different ordering), try after twitter:card block
        if 'twitter:image' not in content:
            content = re.sub(
                r'(<!-- Twitter Card -->.*?<meta name="twitter:description"[^>]*>)',
                r'\1\n    <meta name="twitter:image" content="' + OG_IMAGE_URL + '">',
                content,
                flags=re.DOTALL
            )

    # 2. Add theme-color meta tag if missing
    if 'theme-color' not in content:
        content = content.replace(
            '<meta name="viewport"',
            '<meta name="viewport"'
        )
        # Add after viewport meta
        content = re.sub(
            r'(<meta name="viewport"[^>]*>)',
            r'\1\n    <meta name="theme-color" content="#6B5B95">',
            content
        )

    # 3. Add manifest.json link if missing
    if 'manifest' not in content:
        content = re.sub(
            r'(<meta name="theme-color"[^>]*>)',
            r'\1\n    <link rel="manifest" href="../../manifest.json">',
            content
        )

    # 4. Enhance robots meta tag
    content = re.sub(
        r'<meta name="robots" content="index, follow">',
        '<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">',
        content
    )

    # 5. Add og:image:alt if missing
    if 'og:image:alt' not in content:
        content = re.sub(
            r'(<meta property="og:image:height"[^>]*>)',
            r'\1\n    <meta property="og:image:alt" content="Yoga Schweiz — Studios und Kurse">',
            content
        )

    # 6. Change LocalBusiness to SportsActivityLocation in JSON-LD
    content = content.replace('"@type": "LocalBusiness"', '"@type": "SportsActivityLocation"')

    # 7. Add skip-link CSS (inline) if not present
    skip_link_css = """.skip-link { position: absolute; top: -100%; left: 50%; transform: translateX(-50%); background: #6B5B95; color: #fff; padding: 8px 16px; border-radius: 0 0 8px 8px; z-index: 9999; font-size: 0.9rem; text-decoration: none; transition: top 0.2s; }
        .skip-link:focus { top: 0; }"""

    if 'skip-link' not in content:
        # Add skip-link CSS before closing </style>
        content = content.replace(
            '</style>\n</head>',
            f'        {skip_link_css}\n    </style>\n</head>'
        )

    # 8. Add skip-link anchor after <body> tag
    if 'skip-link' not in content.split('</style>')[0] or 'class="skip-link"' not in content:
        # Only add if not already present in body
        if 'class="skip-link"' not in content:
            content = re.sub(
                r'(<body>)',
                r'\1\n    <a href="#main-content" class="skip-link">Zum Inhalt springen</a>',
                content
            )

    # 9. Add <main id="main-content"> wrapping content between </header> and <footer>
    if '<main' not in content:
        # Find the end of header and start of footer
        # Canton pages use </header> and <footer class="canton-footer">
        content = re.sub(
            r'(</header>\s*\n)',
            r'\1\n    <main id="main-content">\n',
            content,
            count=1
        )
        # Add closing </main> before <footer
        content = re.sub(
            r'(\n\s*<!-- Footer -->\s*\n\s*<footer)',
            r'\n    </main>\n\1',
            content,
            count=1
        )
        # If the above didn't work (no <!-- Footer --> comment), try directly before <footer
        if '</main>' not in content:
            content = re.sub(
                r'(\n\s*<footer)',
                r'\n    </main>\1',
                content,
                count=1
            )

    # Make sure <main> has id="main-content"
    if '<main' in content and 'id="main-content"' not in content:
        content = re.sub(r'<main\b', '<main id="main-content"', content, count=1)

    if content != original:
        write_file(filepath, content)
        return True
    return False


# ============================================================
# YOGA STYLE PAGE UPDATES (58 files)
# ============================================================

def update_yoga_page(filepath):
    """Apply all SEO/accessibility updates to a yoga style page."""
    content = read_file(filepath)
    original = content

    # 1. Add skip-link CSS if not present
    skip_link_css = """.skip-link { position: absolute; top: -100%; left: 50%; transform: translateX(-50%); background: #6B5B95; color: #fff; padding: 8px 16px; border-radius: 0 0 8px 8px; z-index: 9999; font-size: 0.9rem; text-decoration: none; transition: top 0.2s; }
        .skip-link:focus { top: 0; }"""

    if 'skip-link' not in content:
        content = content.replace(
            '    </style>\n</head>',
            f'        {skip_link_css}\n    </style>\n</head>'
        )

    # 2. Add skip-link anchor after <body> tag
    if 'class="skip-link"' not in content:
        content = re.sub(
            r'(<body>)',
            r'\1\n    <a href="#main-content" class="skip-link">Zum Inhalt springen</a>',
            content
        )

    # 3. Add id="main-content" to existing <main> tag
    if '<main' in content and 'id="main-content"' not in content:
        content = re.sub(r'<main\b([^>]*?)>', r'<main id="main-content"\1>', content, count=1)

    # If no <main> tag exists, wrap content between </header> and <footer>
    if '<main' not in content:
        content = re.sub(
            r'(</header>\s*\n)',
            r'\1\n    <main id="main-content">\n',
            content,
            count=1
        )
        content = re.sub(
            r'(\n\s*<!-- Footer -->\s*\n\s*<footer)',
            r'\n    </main>\n\1',
            content,
            count=1
        )
        if '</main>' not in content:
            content = re.sub(
                r'(\n\s*<footer)',
                r'\n    </main>\1',
                content,
                count=1
            )

    # 4. Change @type "Article" to "WebPage" in JSON-LD (for directory pages, not blog articles)
    # Be careful: only change in the first schema block, not BreadcrumbList
    # Target the specific Article schema block
    content = re.sub(
        r'(<!-- Schema\.org Article -->\s*<script type="application/ld\+json">\s*\{[^}]*?"@type":\s*)"Article"',
        r'\1"WebPage"',
        content,
        flags=re.DOTALL
    )
    # Also handle cases without comment
    # Use a more targeted regex: find JSON-LD blocks with @type Article that have headline/description
    def replace_article_type(match):
        block = match.group(0)
        # Only replace if this looks like a yoga page schema (has "headline" or "about")
        if '"headline"' in block or '"about"' in block:
            block = block.replace('"@type": "Article"', '"@type": "WebPage"', 1)
        return block

    content = re.sub(
        r'<script type="application/ld\+json">\s*\{[^<]*?"@type":\s*"Article"[^<]*?</script>',
        replace_article_type,
        content,
        flags=re.DOTALL
    )

    # 5. Add og:image:alt if missing
    if 'og:image:alt' not in content:
        content = re.sub(
            r'(<meta property="og:image:height"[^>]*>)',
            r'\1\n    <meta property="og:image:alt" content="Yoga Schweiz — Studios und Kurse">',
            content
        )

    if content != original:
        write_file(filepath, content)
        return True
    return False


# ============================================================
# BLOG PAGE UPDATES (4 posts + index)
# ============================================================

def update_blog_page(filepath):
    """Apply all SEO/accessibility updates to a blog page."""
    content = read_file(filepath)
    original = content

    # 1. Add skip-link CSS if not present
    skip_link_css = """.skip-link { position: absolute; top: -100%; left: 50%; transform: translateX(-50%); background: #6B5B95; color: #fff; padding: 8px 16px; border-radius: 0 0 8px 8px; z-index: 9999; font-size: 0.9rem; text-decoration: none; transition: top 0.2s; }
        .skip-link:focus { top: 0; }"""

    if 'skip-link' not in content:
        content = content.replace(
            '    </style>\n</head>',
            f'        {skip_link_css}\n    </style>\n</head>'
        )

    # 2. Add skip-link anchor after <body> tag
    if 'class="skip-link"' not in content:
        content = re.sub(
            r'(<body>)',
            r'\1\n    <a href="#main-content" class="skip-link">Zum Inhalt springen</a>',
            content
        )

    # 3. Add id="main-content" to existing <main> tag
    if '<main' in content and 'id="main-content"' not in content:
        content = re.sub(r'<main\b([^>]*?)>', r'<main id="main-content"\1>', content, count=1)

    # If no <main> tag, wrap content
    if '<main' not in content:
        content = re.sub(
            r'(</header>\s*\n)',
            r'\1\n    <main id="main-content">\n',
            content,
            count=1
        )
        content = re.sub(
            r'(\n\s*<!-- Footer -->\s*\n\s*<footer)',
            r'\n    </main>\n\1',
            content,
            count=1
        )
        if '</main>' not in content:
            content = re.sub(
                r'(\n\s*<footer)',
                r'\n    </main>\1',
                content,
                count=1
            )

    # 4. Add logo to publisher Organization in Article JSON-LD
    # Match the publisher block and add logo if missing
    if '"publisher"' in content and '"logo"' not in content:
        # Add logo object after publisher url
        content = re.sub(
            r'("publisher":\s*\{\s*"@type":\s*"Organization",\s*"name":\s*"[^"]*",\s*"url":\s*"[^"]*")\s*\}',
            r'''\1,
        "logo": {
          "@type": "ImageObject",
          "url": "''' + OG_IMAGE_URL + r'''"
        }
      }''',
            content
        )

    # Also handle blog index publisher (might have different structure)
    # For the blog index, the publisher is inside the Blog schema
    if '"publisher"' in content and '"logo"' not in content:
        # Try a more lenient pattern
        def add_logo_to_publisher(match):
            pub_block = match.group(0)
            if '"logo"' not in pub_block:
                pub_block = re.sub(
                    r'("url":\s*"[^"]*")\s*\}',
                    r'\1,\n        "logo": {\n          "@type": "ImageObject",\n          "url": "' + OG_IMAGE_URL + '"\n        }\n      }',
                    pub_block,
                    count=1
                )
            return pub_block

        content = re.sub(
            r'"publisher":\s*\{[^}]*\}',
            add_logo_to_publisher,
            content
        )

    if content != original:
        write_file(filepath, content)
        return True
    return False


# ============================================================
# SITEMAP UPDATE
# ============================================================

def update_sitemap(filepath):
    """Add hreflang alternates to canton and yoga entries in sitemap.xml."""
    content = read_file(filepath)
    original = content

    def add_hreflang_to_url(match):
        """Add hreflang links to a <url> entry that doesn't already have them."""
        url_block = match.group(0)
        # Skip if already has hreflang
        if 'xhtml:link' in url_block:
            return url_block

        # Extract the loc URL
        loc_match = re.search(r'<loc>([^<]+)</loc>', url_block)
        if not loc_match:
            return url_block

        loc_url = loc_match.group(1)

        # Only process kanton/ and yoga/ URLs
        if '/kanton/' not in loc_url and '/yoga/' not in loc_url:
            return url_block

        hreflang_links = f'''    <xhtml:link rel="alternate" hreflang="de" href="{loc_url}"/>
    <xhtml:link rel="alternate" hreflang="en" href="{loc_url}?lang=en"/>
    <xhtml:link rel="alternate" hreflang="fr" href="{loc_url}?lang=fr"/>
    <xhtml:link rel="alternate" hreflang="it" href="{loc_url}?lang=it"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="{loc_url}"/>'''

        # Insert before </url>
        url_block = url_block.replace('  </url>', f'{hreflang_links}\n  </url>')

        return url_block

    # Process all <url>...</url> blocks
    content = re.sub(r'<url>.*?</url>', add_hreflang_to_url, content, flags=re.DOTALL)

    # Also add the kanton/index and yoga/index pages to sitemap if not present
    if '/kanton/"' not in content and '/kanton/<' not in content.replace('/kanton/zurich', '').replace('/kanton/bern', '').replace('/kanton/basel', '').replace('/kanton/geneve', '').replace('/kanton/vaud', '').replace('/kanton/luzern', '').replace('/kanton/aargau', '').replace('/kanton/st-gallen', '').replace('/kanton/thurgau', '').replace('/kanton/graubuenden', '').replace('/kanton/ticino', '').replace('/kanton/fribourg', '').replace('/kanton/zug', '').replace('/kanton/neuchatel', '').replace('/kanton/valais', '').replace('/kanton/jura', '').replace('/kanton/schaffhausen', '').replace('/kanton/schwyz', '').replace('/kanton/glarus', '').replace('/kanton/uri', '').replace('/kanton/obwalden', '').replace('/kanton/nidwalden', '').replace('/kanton/appenzell', '').replace('/kanton/solothurn', '').replace('/kanton/basel-landschaft', ''):
        pass  # Will be handled below

    # Add kanton/index.html entry if not in sitemap
    kanton_index_url = f"{BASE_URL}/kanton/"
    if kanton_index_url + '"' not in content and kanton_index_url + '<' not in content:
        # Check more carefully - the URL should end with /kanton/ exactly
        if f'<loc>{kanton_index_url}</loc>' not in content:
            kanton_entry = f'''
  <!-- Canton Index -->
  <url>
    <loc>{kanton_index_url}</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
    <xhtml:link rel="alternate" hreflang="de" href="{kanton_index_url}"/>
    <xhtml:link rel="alternate" hreflang="en" href="{kanton_index_url}?lang=en"/>
    <xhtml:link rel="alternate" hreflang="fr" href="{kanton_index_url}?lang=fr"/>
    <xhtml:link rel="alternate" hreflang="it" href="{kanton_index_url}?lang=it"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="{kanton_index_url}"/>
  </url>'''
            content = content.replace('  <!-- Canton Pages', f'{kanton_entry}\n\n  <!-- Canton Pages')

    # Add yoga/index.html entry if not in sitemap
    yoga_index_url = f"{BASE_URL}/yoga/"
    if f'<loc>{yoga_index_url}</loc>' not in content:
        yoga_entry = f'''
  <!-- Yoga Styles Index -->
  <url>
    <loc>{yoga_index_url}</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
    <xhtml:link rel="alternate" hreflang="de" href="{yoga_index_url}"/>
    <xhtml:link rel="alternate" hreflang="en" href="{yoga_index_url}?lang=en"/>
    <xhtml:link rel="alternate" hreflang="fr" href="{yoga_index_url}?lang=fr"/>
    <xhtml:link rel="alternate" hreflang="it" href="{yoga_index_url}?lang=it"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="{yoga_index_url}"/>
  </url>'''
        content = content.replace('  <!-- Yoga Style + City Pages', f'{yoga_entry}\n\n  <!-- Yoga Style + City Pages')

    if content != original:
        write_file(filepath, content)
        return True
    return False


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    print("=" * 60)
    print("Batch SEO & Accessibility Update")
    print("=" * 60)

    # --- Canton Pages ---
    print("\n[1/4] Updating canton pages...")
    canton_files = sorted(glob.glob(os.path.join(BASE_DIR, 'kanton', '*', 'index.html')))
    print(f"  Found {len(canton_files)} canton pages")

    for filepath in canton_files:
        canton_name = os.path.basename(os.path.dirname(filepath))
        try:
            backup_file(filepath)
            if update_canton_page(filepath):
                stats['canton_updated'] += 1
                print(f"    Updated: {canton_name}")
            else:
                print(f"    No changes: {canton_name}")
        except Exception as e:
            stats['errors'].append(f"Canton {canton_name}: {str(e)}")
            print(f"    ERROR: {canton_name} - {e}")

    # --- Yoga Style Pages ---
    print("\n[2/4] Updating yoga style pages...")
    yoga_files = sorted(glob.glob(os.path.join(BASE_DIR, 'yoga', '*', 'index.html')))
    print(f"  Found {len(yoga_files)} yoga pages")

    for filepath in yoga_files:
        yoga_name = os.path.basename(os.path.dirname(filepath))
        try:
            backup_file(filepath)
            if update_yoga_page(filepath):
                stats['yoga_updated'] += 1
                print(f"    Updated: {yoga_name}")
            else:
                print(f"    No changes: {yoga_name}")
        except Exception as e:
            stats['errors'].append(f"Yoga {yoga_name}: {str(e)}")
            print(f"    ERROR: {yoga_name} - {e}")

    # --- Blog Pages ---
    print("\n[3/4] Updating blog pages...")
    blog_files = sorted(glob.glob(os.path.join(BASE_DIR, 'blog', '*', 'index.html')))
    blog_index = os.path.join(BASE_DIR, 'blog', 'index.html')
    if os.path.exists(blog_index):
        blog_files.append(blog_index)
    print(f"  Found {len(blog_files)} blog pages")

    for filepath in blog_files:
        blog_name = os.path.basename(os.path.dirname(filepath))
        if filepath == blog_index:
            blog_name = "index"
        try:
            backup_file(filepath)
            if update_blog_page(filepath):
                stats['blog_updated'] += 1
                print(f"    Updated: {blog_name}")
            else:
                print(f"    No changes: {blog_name}")
        except Exception as e:
            stats['errors'].append(f"Blog {blog_name}: {str(e)}")
            print(f"    ERROR: {blog_name} - {e}")

    # --- Sitemap ---
    print("\n[4/4] Updating sitemap.xml...")
    sitemap_path = os.path.join(BASE_DIR, 'sitemap.xml')
    try:
        backup_file(sitemap_path)
        if update_sitemap(sitemap_path):
            stats['sitemap_updated'] = True
            print("    Updated: sitemap.xml")
        else:
            print("    No changes: sitemap.xml")
    except Exception as e:
        stats['errors'].append(f"Sitemap: {str(e)}")
        print(f"    ERROR: sitemap.xml - {e}")

    # --- Summary ---
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Canton pages updated:  {stats['canton_updated']}/{len(canton_files)}")
    print(f"  Yoga pages updated:    {stats['yoga_updated']}/{len(yoga_files)}")
    print(f"  Blog pages updated:    {stats['blog_updated']}/{len(blog_files)}")
    print(f"  Sitemap updated:       {'Yes' if stats['sitemap_updated'] else 'No'}")

    if stats['errors']:
        print(f"\n  ERRORS ({len(stats['errors'])}):")
        for err in stats['errors']:
            print(f"    - {err}")
    else:
        print("\n  No errors!")

    print("=" * 60)


if __name__ == '__main__':
    main()
