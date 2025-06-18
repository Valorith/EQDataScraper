#!/usr/bin/env python3
import os, time, requests, pandas as pd
from bs4 import BeautifulSoup
from jinja2 import Template

# 🎯 Full list of classes with their type IDs
CLASSES = {
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

BASE_URL = 'https://alla.clumsysworld.com/'
HTML_TEMPLATE = """
<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{{ cls }} Spells</title>
<style>
  body { font-family: sans-serif; background: #f0f0f0; padding: 20px; }
  h1 { color: #333; }
  table { width:100%; border-collapse: collapse; }
  th, td { padding: 6px; border: 1px solid #888; text-align: left; }
  tr:nth-child(even) { background: #eee; }
</style></head>
<body><h1>{{ cls }} Spells</h1>
{{ table|safe }}</body></html>
"""

def fetch_spell_html(class_type: int) -> str:
    resp = requests.get(BASE_URL, params={'a':'spells','name':'','type':class_type,'level':1,'opt':2})
    resp.raise_for_status()
    return resp.text

def parse_spell_table(html: str) -> pd.DataFrame:
    from io import StringIO
    soup = BeautifulSoup(html, 'html.parser')
    tbl = soup.find('table')
    if not tbl:
        raise ValueError("No table found")
    return pd.read_html(StringIO(str(tbl)))[0]

def render_html(df: pd.DataFrame, cls: str) -> str:
    return Template(HTML_TEMPLATE).render(cls=cls, table=df.to_html(index=False))

def process_all_classes():
    for cls, ctype in CLASSES.items():
        try:
            html = fetch_spell_html(ctype)
            df = parse_spell_table(html)
            out = render_html(df, cls)
            fname = os.path.join(os.path.dirname(__file__), f"{cls.lower()}_spells.html")
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(out)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ {fname}")
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ {cls}: {e}")

def main():
    process_all_classes()

if __name__ == "__main__":
    main()