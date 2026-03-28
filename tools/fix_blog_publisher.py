#!/usr/bin/env python3
"""Fix blog publisher logo - add ImageObject logo to publisher Organization in JSON-LD."""

import os
import re
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OG_IMAGE_URL = "https://meineprojekte.github.io/yoga-kurse-basel/img/og-image.png"

LOGO_BLOCK = ''',
        "logo": {
          "@type": "ImageObject",
          "url": "''' + OG_IMAGE_URL + '''"
        }'''


def fix_publisher_logo(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if '"ImageObject"' in content:
        print(f"  Already has logo: {filepath}")
        return False

    original = content

    # Pattern: match publisher block ending with url line followed by },
    # The publisher object looks like:
    #   "publisher": {
    #     "@type": "Organization",
    #     "name": "YogaSchweiz",
    #     "url": "https://..."
    #   },
    # OR
    #   "publisher": {
    #     "@type": "Organization",
    #     "name": "YogaSchweiz",
    #     "url": "https://..."
    #   }

    # Replace: add logo before the closing brace of publisher object
    content = re.sub(
        r'("publisher":\s*\{\s*"@type":\s*"Organization",\s*"name":\s*"[^"]*",\s*"url":\s*"[^"]*")\s*\}',
        lambda m: m.group(1) + LOGO_BLOCK + '\n      }',
        content
    )

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    print("Fixing blog publisher logos...")

    blog_files = sorted(glob.glob(os.path.join(BASE_DIR, 'blog', '*', 'index.html')))
    blog_index = os.path.join(BASE_DIR, 'blog', 'index.html')
    if os.path.exists(blog_index):
        blog_files.append(blog_index)

    fixed = 0
    for filepath in blog_files:
        name = os.path.basename(os.path.dirname(filepath))
        if filepath == blog_index:
            name = "index"
        if fix_publisher_logo(filepath):
            fixed += 1
            print(f"  Fixed: {name}")
        else:
            print(f"  No change: {name}")

    print(f"\nFixed {fixed}/{len(blog_files)} files")


if __name__ == '__main__':
    main()
