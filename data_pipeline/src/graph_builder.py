import torch
import pandas as pd
from torch_geometric.data import HeteroData
from src.utils import logger

def build_hetero_graph(country_nodes, year_nodes, metric_nodes, 
                       emits_edges, metric_edges):
    """Build PyTorch Geometric HeteroData object"""
    
    data = HeteroData()
    
    # Add node features (using dummy features for now)
    data['country'].num_nodes = len(country_nodes)
    data['year'].num_nodes = len(year_nodes)
    data['metric'].num_nodes = len(metric_nodes)
    
    # Create mapping from string IDs to indices
    country_to_idx = {row['node_id']: i for i, row in country_nodes.iterrows()}
    year_to_idx = {row['node_id']: i for i, row in year_nodes.iterrows()}
    metric_to_idx = {row['node_id']: i for i, row in metric_nodes.iterrows()}
    
    # Add emits edges
    if len(emits_edges) > 0:
        src_idx = [country_to_idx[e] for e in emits_edges['src']]
        dst_idx = [year_to_idx[e] for e in emits_edges['dst']]
        data['country', 'emits_in_year', 'year'].edge_index = torch.tensor([src_idx, dst_idx])
        
        if 'weight' in emits_edges.columns:
            data['country', 'emits_in_year', 'year'].weight = torch.tensor(
                emits_edges['weight'].values, dtype=torch.float
            )
    
    # Add metric edges (need composite node type)
    if len(metric_edges) > 0:
        # For simplicity, we add metric edges as attributes to (country, year)
        # This requires country-year nodes in the graph
        pass
    
    logger.info("Heterogeneous graph built successfully")
    return data

def save_graph(data, filename="emission_graph.pt"):
    """Save graph to disk"""
    from src.config import GRAPH_DATA
    filepath = GRAPH_DATA / filename
    torch.save(data, filepath)
    logger.info(f"Graph saved to {filepath}")