# src/graph_builder.py
import torch
import numpy as np
import pandas as pd
from torch_geometric.data import HeteroData
from src.config import (
    AUTHORS_PATH, PAPERS_PATH, VENUES_PATH, YEARS_PATH,
    AUTHOR_WROTE_PATH, PAPER_VENUE_PATH, PAPER_YEAR_PATH,
    GRAPH_DIR, GRAPH_PATH,
)


def build_graph():
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)

    # --- load nodes ---
    authors = pd.read_parquet(AUTHORS_PATH)
    papers  = pd.read_parquet(PAPERS_PATH)
    venues  = pd.read_parquet(VENUES_PATH)
    years   = pd.read_parquet(YEARS_PATH)

    # --- load edges ---
    author_wrote = pd.read_parquet(AUTHOR_WROTE_PATH)
    paper_venue  = pd.read_parquet(PAPER_VENUE_PATH)
    paper_year   = pd.read_parquet(PAPER_YEAR_PATH)

    # --- build hetero graph ---
    data = HeteroData()

    # node counts (features can be added later)
    data["author"].num_nodes = len(authors)
    data["paper"].num_nodes  = len(papers)
    data["venue"].num_nodes  = len(venues)
    data["year"].num_nodes   = len(years)

    # edges
    data["author", "wrote", "paper"].edge_index = torch.tensor(
        np.array([author_wrote["author_id"].values, author_wrote["paper_id"].values]),
        dtype=torch.long,
    )

    data["paper", "published_in", "venue"].edge_index = torch.tensor(
        np.array([paper_venue["paper_id"].values, paper_venue["venue_id"].values]),
        dtype=torch.long,
    )

    data["paper", "published_in", "year"].edge_index = torch.tensor(
        np.array([paper_year["paper_id"].values, paper_year["year_id"].values]),
        dtype=torch.long,
    )

    data["paper", "written_by", "author"].edge_index = torch.tensor(
        np.array([author_wrote["paper_id"].values, author_wrote["author_id"].values]),
        dtype=torch.long,
    )

    torch.save(data, GRAPH_PATH)
    print(f"  Node types:  {data.node_types}")
    print(f"  Edge types:  {data.edge_types}")
    print(f"  Saved to:    {GRAPH_PATH}")

    return data


if __name__ == "__main__":
    build_graph()