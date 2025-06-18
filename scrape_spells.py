#!/usr/bin/env python3
import os
import time
import argparse
from typing import Dict, Optional

import requests
import pandas as pd
from bs4 import BeautifulSoup
from jinja2 import Template

# 🎯 Full list of classes with their type IDs
CLASSES: Dict[str, int] = {
    'Warrior': 1,
    'Cleric': 2,
    'Paladin': 3,
    'Ranger': 4,
    'ShadowKnight': 5,
    'Druid': 6,
    'Monk': 7,
    'Bard': 8,
    'Rogue': 9,
    'Shaman': 10,
    'Necromancer': 11,
    'Wizard': 12,
    'Magician': 13,
    'Enchanter': 14,
    'Beastlord': 15,
    'Berserker': 16,
}

# Basic colour theme for each class used in the generated HTML. This is far from
# accurate to the game's palette but provides a quick way to differentiate the
# pages when rendered.
CLASS_COLORS: Dict[str, str] = {
    'Warrior': '#8e2d2d',
    'Cleric': '#ccccff',
    'Paladin': '#ffd700',
    'Ranger': '#228b22',
    'ShadowKnight': '#551a8b',
    'Druid': '#a0522d',
    'Monk': '#556b2f',
    'Bard': '#ff69b4',
    'Rogue': '#708090',
    'Shaman': '#20b2aa',
    'Necromancer': '#4b0082',
    'Wizard': '#1e90ff',
    'Magician': '#ff8c00',
    'Enchanter': '#9370db',
    'Beastlord': '#a52a2a',
    'Berserker': '#b22222',
}

BASE_URL = 'https://alla.clumsysworld.com/'
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8'>
    <title>{{ cls }} Spells</title>
    <style>
        body { font-family: sans-serif; background: #f0f0f0; padding: 20px; }
        h1 { color: {{ color }}; }
        table { width: 100%%; border-collapse: collapse; }
        th, td { padding: 6px; border: 1px solid #888; text-align: left; }
        tr:nth-child(even) { background: #eee; }
    </style>
</head>
<body>
    <h1>{{ cls }} Spells</h1>
    {{ table|safe }}
</body>
</html>
"""

def fetch_spell_html(class_type: int, base_url: str = BASE_URL) -> str:
    """Fetch HTML for a class's spells from the remote site."""

    resp = requests.get(
        base_url,
        params={"a": "spells", "name": "", "type": class_type, "level": 1, "opt": 2},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.text

def read_local_spell_html(cls: str, local_dir: str) -> Optional[str]:
    """Return HTML from a local file if present."""

    path = os.path.join(local_dir, f"{cls.lower()}.html")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    # Fallback to a generic sample if available
    sample = os.path.join(local_dir, "sample_table.html")
    if os.path.exists(sample):
        with open(sample, "r", encoding="utf-8") as f:
            return f.read()
    return None

def parse_spell_table(html: str) -> pd.DataFrame:
    from io import StringIO
    soup = BeautifulSoup(html, 'html.parser')
    tbl = soup.find('table')
    if not tbl:
        raise ValueError("No table found")
    return pd.read_html(StringIO(str(tbl)))[0]

def render_html(df: pd.DataFrame, cls: str) -> str:
    color = CLASS_COLORS.get(cls, "#333")
    return Template(HTML_TEMPLATE).render(cls=cls, table=df.to_html(index=False), color=color)

def process_all_classes(base_url: str = BASE_URL, local_dir: Optional[str] = None) -> None:
    """Fetch and render spell tables for every class."""
    for cls, ctype in CLASSES.items():
        try:
            html = None
            if local_dir:
                html = read_local_spell_html(cls, local_dir)
            if html is None:
                html = fetch_spell_html(ctype, base_url)
            df = parse_spell_table(html)
            out = render_html(df, cls)
            fname = os.path.join(os.path.dirname(__file__), f"{cls.lower()}_spells.html")
            with open(fname, "w", encoding="utf-8") as f:
                f.write(out)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ {fname}")
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ {cls}: {e}")

def run(loop: bool = False, interval: int = 3600, base_url: str = BASE_URL, local_dir: Optional[str] = None) -> None:
    """Run the scraping process once or continually."""
    while True:
        process_all_classes(base_url=base_url, local_dir=local_dir)
        if not loop:
            break
        time.sleep(interval)

def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Clumsy's World spell tables")
    parser.add_argument("--loop", action="store_true", help="continually scrape on an interval")
    parser.add_argument("--interval", type=int, default=3600, help="seconds between scrapes when looping")
    parser.add_argument("--base-url", default=BASE_URL, help="alternate base URL for fetching spell tables")
    parser.add_argument("--local-dir", help="read HTML files from this directory instead of fetching")
    args = parser.parse_args()

    run(loop=args.loop, interval=args.interval, base_url=args.base_url, local_dir=args.local_dir)


if __name__ == "__main__":
    main()