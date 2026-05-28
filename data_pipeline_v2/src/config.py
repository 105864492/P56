# src/config.py
from pathlib import Path

# Root
BASE_DIR = Path(__file__).resolve().parent.parent

# Data paths
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
GRAPH_DIR = BASE_DIR / "data" / "graph_data"

NODES_DIR = PROCESSED_DIR / "nodes"
EDGES_DIR = PROCESSED_DIR / "edges"

# Raw file
DBLP_GZ = RAW_DIR / "dblp.xml.gz"
DBLP_XML = RAW_DIR / "dblp.xml"

# Node outputs
AUTHORS_PATH = NODES_DIR / "authors.parquet"
PAPERS_PATH = NODES_DIR / "papers.parquet"
VENUES_PATH = NODES_DIR / "venues.parquet"
YEARS_PATH = NODES_DIR / "years.parquet"

# Edge outputs
AUTHOR_WROTE_PATH = EDGES_DIR / "author_wrote_paper.parquet"
PAPER_VENUE_PATH = EDGES_DIR / "paper_published_in_venue.parquet"
PAPER_YEAR_PATH = EDGES_DIR / "paper_published_in_year.parquet"

# Graph output
GRAPH_PATH = GRAPH_DIR / "dblp_graph.pt"

# Parser settings
PUBLICATION_TYPES = {"article", "inproceedings", "incollection", "book", "phdthesis", "mastersthesis"}
MAX_RECORDS = None  # set to e.g. 100_000 for a quick test run