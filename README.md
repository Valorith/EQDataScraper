# EQDataScraper

EQDataScraper is a small Python utility that retrieves spell information for every EverQuest class from the **Clumsy's World** Allakhazam clone. For each class the script builds a colour‑themed HTML page listing all spells at or above level 1.

The script pulls data directly from `https://alla.clumsysworld.com/` by default, so an internet connection is required unless you provide pre-saved HTML files. Output files are named `<class>_spells.html` and are written to the project directory.

## Requirements
- Python 3.8 or newer
- The packages listed in `requirements.txt`

Install the dependencies with:

```bash
pip install -r requirements.txt
```

## Basic usage
Execute the scraper once for all classes:

```bash
python3 scrape_spells.py
```

When finished you will find HTML files such as `bard_spells.html`, `cleric_spells.html` and so on in the repository folder. Open any of these files in your browser to view the results.

## Running continuously
The script can run in a loop to keep your local files up‑to‑date. Use `--loop` together with an optional `--interval` (seconds) to control how often it runs. The example below scrapes every hour:

```bash
python3 scrape_spells.py --loop --interval 3600
```

Press **Ctrl+C** to stop the loop.

## Command-line options
- `--loop` &ndash; run indefinitely, scraping at a set interval.
- `--interval SECONDS` &ndash; number of seconds between runs when using `--loop` (default: 3600).
- `--base-url URL` &ndash; alternate website root if you wish to scrape from a mirror.
- `--local-dir PATH` &ndash; read pre-saved HTML files from this folder instead of downloading from the web. Each file should be named `<class>.html`. A `sample_table.html` is provided for testing.

## Example: using local files
If your environment has no internet access you can still test the script by providing the supplied sample HTML table:

```bash
python3 scrape_spells.py --local-dir samples
```

The generated pages will contain the data from the files in `samples/`.

## Customisation
Colour themes for each class are defined in `scrape_spells.py` within the `CLASS_COLORS` dictionary. You can adjust the colours or add CSS in `HTML_TEMPLATE` to change the appearance of the output pages.

## Troubleshooting
- **Connection errors** &ndash; ensure the target site is reachable, or use `--local-dir` with pre‑downloaded pages.
- **No table found** &ndash; the website may have changed its structure. Verify the HTML manually and update `parse_spell_table` if necessary.

## License
This project is provided as-is for personal use and education.
