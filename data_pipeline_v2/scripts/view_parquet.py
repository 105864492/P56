# scripts/view_parquet.py
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
from src.config import AUTHORS_PATH, PAPERS_PATH, VENUES_PATH, YEARS_PATH, AUTHOR_WROTE_PATH, PAPER_VENUE_PATH, PAPER_YEAR_PATH


def show(label, path, n=5):
    print(f"\n{'=' * 40}")
    print(f"  {label}")
    print(f"{'=' * 40}")
    if not path.exists():
        print("  File not found, run the pipeline first.")
        return
    df = pd.read_parquet(path)
    print(f"  Rows: {len(df):,}  |  Columns: {list(df.columns)}")
    print()
    print(df.head(n).to_string(index=False))


def main():
    show("Authors",              AUTHORS_PATH)
    show("Papers",               PAPERS_PATH)
    show("Venues",               VENUES_PATH)
    show("Years",                YEARS_PATH)
    show("Author -> Paper",      AUTHOR_WROTE_PATH)
    show("Paper  -> Venue",      PAPER_VENUE_PATH)
    show("Paper  -> Year",       PAPER_YEAR_PATH)


if __name__ == "__main__":
    main()