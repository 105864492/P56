#!/usr/bin/env python
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_loader import load_raw_data
from src.node_builder import (
    build_country_nodes, build_year_nodes, 
    build_metric_nodes, build_country_year_nodes
)
from src.edge_builder import build_emits_edges, build_metric_edges
from src.graph_builder import build_hetero_graph, save_graph
from src.utils import setup_logging, save_node_tables, save_edge_tables

def main():
    # Setup
    setup_logging()
    
    # 1. Load data
    print("Loading raw data...")
    df = load_raw_data()
    
    # 2. Build nodes
    print("Building nodes...")
    country_nodes = build_country_nodes(df)
    year_nodes = build_year_nodes(df)
    metric_nodes = build_metric_nodes()
    cy_nodes = build_country_year_nodes(df)
    
    # 3. Build edges
    print("Building edges...")
    emits_edges = build_emits_edges(df)
    metric_edges = build_metric_edges(df)
    
    # 4. Save intermediate files (optional)
    print("Saving node/edge tables...")
    save_node_tables(country_nodes, year_nodes, metric_nodes, cy_nodes)
    save_edge_tables(emits_edges, metric_edges)
    
    # 5. Build graph
    print("Building heterogeneous graph...")
    graph = build_hetero_graph(
        country_nodes, year_nodes, metric_nodes,
        emits_edges, metric_edges
    )
    
    # 6. Save final graph
    print("Saving graph...")
    save_graph(graph)
    
    print("Pipeline completed successfully!")

if __name__ == "__main__":
    main()