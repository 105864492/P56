# Heterogeneous Emission Network Pipeline

Transform emission data from CSV format into a heterogeneous graph for network analysis and graph machine learning.

## What This Pipeline Does

This project converts a flat table (countries, years, emissions) into a graph with multiple connected node types:

- Country nodes (for example: Afghanistan, USA)
- Year nodes (for example: 1950, 2023)
- Metric nodes (for example: CO2, methane, temperature)
- Country-Year nodes (composite identifiers)

Each edge stores relationships and measurement values, enabling graph-based analytics and ML workflows.

## Quick Start

### 1) Setup

Clone the repository, create a virtual environment, and install dependencies.

```bash
git clone <your-repo-url>
cd data_pipeline
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

Install required packages:

```bash
pip install -r requirements.txt
```

### 2) Add Input Data

The CSV data is already placed at:

```text
data/raw/global_emissions.csv
```

Expected columns include:
`country`, `year`, `iso_code`, `co2`, `co2_per_capita`, `methane`, `temperature_change`, etc.

### 3) (Optional) Clean Previous Outputs

Remove generated files if you want a fresh rebuild.

Simply delete `data/graph_data` and `data/processed`

### 4) Run the Pipeline

```bash
python scripts/run_pipeline.py
```

Pipeline actions:

- Loads and cleans the raw CSV
- Creates node tables (countries, years, metrics, country-years)
- Creates edge tables (emits edges, metric value edges)
- Builds a PyTorch Geometric heterogeneous graph
- Saves outputs to `data/processed/` and `data/graph_data/`

## Output Files

Expected generated files:

```text
data/processed/nodes/
  - countries.parquet
  - years.parquet
  - metrics.parquet
  - country_years.parquet

data/processed/edges/
  - emits_edges.parquet
  - metric_edges.parquet

data/graph_data/
  - emission_graph.pt
```

## View Results

### Option A: Web Dashboard

```bash
streamlit run scripts/gui_dashboard.py
```

Opens an interactive dashboard with charts, filters, and exploration tools.

### Option B: View Parquet Tables

```bash
python scripts/view_parquet.py
```

Displays node and edge tables as formatted text.

### Option C: View Graph Structure

```bash
python scripts/view_graph_simple.py
```

Shows graph node types, edge types, and summary statistics.

## Project Structure

```text
data_pipeline/
├── data/
│   ├── raw/
│   │   └── global_emissions.csv
│   ├── processed/
│   │   ├── nodes/
│   │   │   ├── countries.parquet
│   │   │   ├── years.parquet
│   │   │   ├── metrics.parquet
│   │   │   └── country_years.parquet
│   │   └── edges/
│   │       ├── emits_edges.parquet
│   │       └── metric_edges.parquet
│   └── graph_data/
│       └── emission_graph.pt
├── scripts/
│   ├── run_pipeline.py
│   ├── gui_dashboard.py
│   ├── view_parquet.py
│   └── view_graph_simple.py
├── src/
│   ├── config.py
│   ├── data_loader.py
│   ├── node_builder.py
│   ├── edge_builder.py
│   ├── graph_builder.py
│   └── utils.py
├── requirements.txt
└── README.md
```