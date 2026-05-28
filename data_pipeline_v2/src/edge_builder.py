# src/edge_builder.py
import pandas as pd
from src.config import (
    AUTHOR_WROTE_PATH,
    PAPER_VENUE_PATH,
    PAPER_YEAR_PATH,
    EDGES_DIR,
)
from src.parser import parse_dblp


def build_edges(authors, venues, years):
    """
    authors, venues, years are the lookup dicts returned by build_nodes()
    so we don't parse the file twice.
    """
    EDGES_DIR.mkdir(parents=True, exist_ok=True)

    author_wrote = []       # (author_id, paper_id)
    paper_venue = []        # (paper_id, venue_id)
    paper_year = []         # (paper_id, year_id)

    paper_id = 0

    def process(record):
        nonlocal paper_id

        # author -> paper
        for name in record.get("authors", []):
            aid = authors.get(name)
            if aid is not None:
                author_wrote.append({
                    "author_id": aid,
                    "paper_id": paper_id,
                })

        # paper -> venue
        venue = record.get("venue")
        if venue:
            vid = venues.get(venue)
            if vid is not None:
                paper_venue.append({
                    "paper_id": paper_id,
                    "venue_id": vid,
                })

        # paper -> year
        year = record.get("year")
        if year:
            yid = years.get(year)
            if yid is not None:
                paper_year.append({
                    "paper_id": paper_id,
                    "year_id": yid,
                })

        paper_id += 1

    parse_dblp(process)

    df_author_wrote = pd.DataFrame(author_wrote)
    df_paper_venue = pd.DataFrame(paper_venue)
    df_paper_year = pd.DataFrame(paper_year)

    df_author_wrote.to_parquet(AUTHOR_WROTE_PATH, index=False)
    df_paper_venue.to_parquet(PAPER_VENUE_PATH, index=False)
    df_paper_year.to_parquet(PAPER_YEAR_PATH, index=False)

    print(f"  Author->Paper edges: {len(df_author_wrote):,}")
    print(f"  Paper->Venue edges:  {len(df_paper_venue):,}")
    print(f"  Paper->Year edges:   {len(df_paper_year):,}")