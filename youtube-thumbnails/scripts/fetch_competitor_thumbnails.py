#!/usr/bin/env python3
"""
Fetch competitor thumbnail images from URLs for visual analysis.

Usage:
  python3 fetch_competitor_thumbnails.py --urls url1,url2,url3 --output /tmp/competitor_thumbs/
  python3 fetch_competitor_thumbnails.py --urls-file urls.txt --output /tmp/competitor_thumbs/

Each thumbnail is saved as 01_title-slug.jpg, 02_title-slug.jpg, etc.
Prints the list of downloaded local paths so Claude can analyze them with Read tool.
"""

import argparse
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path


def slugify(text: str, max_len: int = 40) -> str:
    """Convert text to a safe filename slug."""
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[\s_-]+', '-', text).strip('-')
    return text[:max_len]


def fetch_thumbnail(url: str, output_path: str) -> bool:
    """Download a single thumbnail URL to output_path. Returns True on success."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; thumbnail-fetcher/1.0)'
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        with open(output_path, 'wb') as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"  WARN: Could not fetch {url[:80]}... — {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Fetch competitor thumbnails for visual analysis")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--urls', help='Comma-separated list of thumbnail URLs')
    group.add_argument('--urls-file', help='File with one URL per line (optionally: url<TAB>title)')
    parser.add_argument('--output', required=True, help='Output directory for downloaded thumbnails')
    parser.add_argument('--limit', type=int, default=20, help='Max thumbnails to fetch (default: 20)')

    args = parser.parse_args()

    # Collect (url, title) pairs
    entries = []
    if args.urls:
        for url in args.urls.split(','):
            url = url.strip()
            if url:
                entries.append((url, ''))
    else:
        with open(args.urls_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('\t', 1)
                url = parts[0].strip()
                title = parts[1].strip() if len(parts) > 1 else ''
                entries.append((url, title))

    entries = entries[:args.limit]

    # Create output directory
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching {len(entries)} competitor thumbnails to {out_dir}/")
    downloaded = []

    for idx, (url, title) in enumerate(entries, 1):
        slug = slugify(title) if title else f'thumb-{idx:02d}'
        # Guess extension from URL
        ext = 'jpg'
        for candidate in ['.jpg', '.jpeg', '.png', '.webp']:
            if candidate in url.lower():
                ext = candidate.lstrip('.')
                break
        filename = f'{idx:02d}_{slug}.{ext}'
        output_path = str(out_dir / filename)

        print(f"  [{idx:02d}/{len(entries)}] {filename} ...")
        if fetch_thumbnail(url, output_path):
            downloaded.append(output_path)
            print(f"         -> {output_path}")

    print(f"\nDownloaded: {len(downloaded)}/{len(entries)} thumbnails")
    print(f"Output dir: {out_dir}")
    print("\nLOCAL_PATHS:")
    for p in downloaded:
        print(f"  {p}")

    return 0 if downloaded else 1


if __name__ == '__main__':
    sys.exit(main())
