# src/node_builder.py
import pandas as pd
from src.config import AUTHORS_PATH, PAPERS_PATH, VENUES_PATH, YEARS_PATH, NODES_DIR
from src.parser import parse_dblp


def build_nodes():
    NODES_DIR.mkdir(parents=True, exist_ok=True)

    authors = {}    # name -> author_id
    papers = []
    venues = {}     # name -> venue_id
    years = {}      # year -> year_id

    def process(record):
        # --- papers ---
        paper_id = len(papers)
        papers.append({
            "paper_id": paper_id,
            "key": record.get("key"),
            "title": record.get("title"),
            "type": record.get("type"),
            "ee": record.get("ee"),
            "pages": record.get("pages"),
        })

        # --- authors ---
        for name in record.get("authors", []):
            if name not in authors:
                authors[name] = len(authors)

        # --- venues ---
        venue = record.get("venue")
        if venue and venue not in venues:
            venues[venue] = len(venues)

        # --- years ---
        year = record.get("year")
        if year and year not in years:
            years[year] = len(years)

    parse_dblp(process)

    # --- save ---
    df_papers = pd.DataFrame(papers)
    df_authors = pd.DataFrame([
        {"author_id": aid, "name": name}
        for name, aid in authors.items()
    ])
    df_venues = pd.DataFrame([
        {"venue_id": vid, "name": name}
        for name, vid in venues.items()
    ])
    df_years = pd.DataFrame([
        {"year_id": yid, "year": year}
        for year, yid in years.items()
    ]).sort_values("year")

    df_papers.to_parquet(PAPERS_PATH, index=False)
    df_authors.to_parquet(AUTHORS_PATH, index=False)
    df_venues.to_parquet(VENUES_PATH, index=False)
    df_years.to_parquet(YEARS_PATH, index=False)

    print(f"  Papers:  {len(df_papers):,}")
    print(f"  Authors: {len(df_authors):,}")
    print(f"  Venues:  {len(df_venues):,}")
    print(f"  Years:   {len(df_years):,}")

    return authors, venues, years


if __name__ == "__main__":
    build_nodes()