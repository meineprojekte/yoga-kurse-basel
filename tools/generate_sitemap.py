#!/usr/bin/env python3
"""Generate sitemap.xml from the pages that actually exist on disk.

Replaces the old hand-maintained sitemap that had a uniform, stale <lastmod>
and listed deleted pages. lastmod per URL = the file's last git commit date,
or today if the file has uncommitted changes (i.e. it changed in this run).
Wired into .github/workflows/scrape.yml so it stays correct automatically.
"""
import os, glob, subprocess, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://meineprojekte.github.io/yoga-kurse-basel"
TODAY = datetime.date.today().isoformat()

# (glob pattern relative to ROOT, priority, changefreq)
GROUPS = [
    ("index.html", "1.0", "daily"),
    ("kanton/index.html", "0.8", "weekly"),
    ("kanton/*/index.html", "0.8", "weekly"),
    ("yoga/index.html", "0.7", "weekly"),
    ("yoga/*/index.html", "0.6", "weekly"),
    ("blog/index.html", "0.6", "monthly"),
    ("blog/*/index.html", "0.6", "monthly"),
    ("about/index.html", "0.5", "yearly"),
    ("datenschutz/index.html", "0.4", "yearly"),
]


def run(args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)


def has_uncommitted_change(rel):
    # untracked file -> changed
    if run(["git", "ls-files", "--error-unmatch", rel]).returncode != 0:
        return True
    # tracked but differs from HEAD -> changed
    return run(["git", "diff", "--quiet", "HEAD", "--", rel]).returncode != 0


def git_date(rel):
    out = run(["git", "log", "-1", "--format=%cs", "--", rel]).stdout.strip()
    return out or TODAY


def lastmod(rel):
    return TODAY if has_uncommitted_change(rel) else git_date(rel)


def url_for(rel):
    d = os.path.dirname(rel)
    return BASE + "/" if d == "" else f"{BASE}/{d}/"


def main():
    seen = set()
    entries = []
    for pattern, prio, freq in GROUPS:
        for rel in sorted(glob.glob(os.path.join(ROOT, pattern))):
            rel = os.path.relpath(rel, ROOT)
            if rel in seen:
                continue
            seen.add(rel)
            entries.append((url_for(rel), lastmod(rel), prio, freq))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lm, prio, freq in entries:
        lines += ["  <url>",
                  f"    <loc>{loc}</loc>",
                  f"    <lastmod>{lm}</lastmod>",
                  f"    <changefreq>{freq}</changefreq>",
                  f"    <priority>{prio}</priority>",
                  "  </url>"]
    lines.append("</urlset>")
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"sitemap.xml: {len(entries)} URLs")


if __name__ == "__main__":
    main()
