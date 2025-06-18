# EQDataScraper

This script retrieves spell data for each EverQuest class from the Clumsy's World Allakhazam clone. It generates one HTML file per class showing the spell table with a simple colour theme.

By default the script fetches spell tables directly from the Clumsy's World site. If the
site is unreachable you can provide a directory of HTML files using `--local-dir`.
Each file should be named `<class>.html` (e.g. `bard.html`). A generic
`sample_table.html` is provided for testing and will be used for any missing class file.

## Usage

Install dependencies:

```bash
pip install -r requirements.txt
```

Run once:

```bash
python3 scrape_spells.py
```

Run continually every hour:

```bash
python3 scrape_spells.py --loop --interval 3600
```

Use local HTML files instead of fetching:

```bash
python3 scrape_spells.py --local-dir samples
```

Specify an alternate base URL:

```bash
python3 scrape_spells.py --base-url https://my-mirror.example.com/
```

Generated HTML files will appear in the project directory.
