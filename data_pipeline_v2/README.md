# DBLP Heterogeneous Graph Pipeline

Transform the DBLP academic bibliography XML dump into a heterogeneous graph for network analysis and graph machine learning.

## What This Pipeline Does

Converts the raw DBLP XML into a graph with four node types and three edge types:

**Nodes**
- Author (for example: E. W. Dijkstra)
- Paper (for example: Go To Statement Considered Harmful)
- Venue (for example: Communications of the ACM)
- Year (for example: 1968)

**Edges**
- Author wrote Paper
- Paper published_in Venue
- Paper published_in Year

## Quick Start

### 1) Setup

```bash
git clone <your-repo-url>
cd data_pipeline_v2
python -m venv venv
```

Activate the environment:

**Windows**
```bash
venv\Scripts\activate
```

**macOS / Linux**
```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2) Download the Data

```bash
python scripts/download_data.py
```

Downloads `dblp.xml.gz` (~1GB) from dblp.org into `data/raw/`. This is gitignored and must be downloaded before running the pipeline.

### 3) (Optional) Limit Records for Testing

In `src/config.py`, set:

```python
MAX_RECORDS = 100_000
```

This lets you run the full pipeline quickly on a small slice. Set back to `None` for the full dataset.

### 4) Run the Pipeline

```bash
python scripts/run_pipeline.py
```

Pipeline steps:

- Streams and parses `dblp.xml.gz` using a SAX parser
- Extracts and deduplicates Author, Paper, Venue, and Year nodes
- Builds edges between node types
- Saves node and edge tables as Parquet files
- Builds a PyTorch Geometric `HeteroData` graph and saves it as `.pt`

## Output Files

```text
data/processed/nodes/
  authors.parquet
  papers.parquet
  venues.parquet
  years.parquet

data/processed/edges/
  author_wrote_paper.parquet
  paper_published_in_venue.parquet
  paper_published_in_year.parquet

data/graph_data/
  dblp_graph.pt
```

## View Results

### View Parquet Tables

```bash
python scripts/view_parquet.py
```

### View Graph Structure

```bash
python scripts/view_graph.py
```

## View Interactive Visualised Data (Web)

```bash
streamlit run scripts/dashboard.py
```

## Project Structure

```text
dblp_pipeline/
├── data/
│   ├── raw/                        ← gitignored
│   ├── processed/
│   │   ├── nodes/
│   │   └── edges/
│   └── graph_data/
├── scripts/
│   ├── download_data.py
│   ├── run_pipeline.py
│   ├── view_parquet.py
│   └── view_graph.py
├── src/
│   ├── config.py
│   ├── parser.py
│   ├── node_builder.py
│   ├── edge_builder.py
│   └── graph_builder.py
├── .gitignore
├── requirements.txt
└── README.md
```