import logging
from pathlib import Path
from src.config import DATA_PROCESSED

def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('pipeline.log'),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)

def save_node_tables(country_nodes, year_nodes, metric_nodes, cy_nodes):
    """Save node tables as Parquet"""
    nodes_dir = DATA_PROCESSED / "nodes"
    nodes_dir.mkdir(exist_ok=True)
    
    country_nodes.to_parquet(nodes_dir / "countries.parquet")
    year_nodes.to_parquet(nodes_dir / "years.parquet")
    metric_nodes.to_parquet(nodes_dir / "metrics.parquet")
    cy_nodes.to_parquet(nodes_dir / "country_years.parquet")
    
    logger.info("Node tables saved")

def save_edge_tables(emits_edges, metric_edges):
    """Save edge tables as Parquet"""
    edges_dir = DATA_PROCESSED / "edges"
    edges_dir.mkdir(exist_ok=True)
    
    emits_edges.to_parquet(edges_dir / "emits_edges.parquet")
    if len(metric_edges) > 0:
        metric_edges.to_parquet(edges_dir / "metric_edges.parquet")
    
    logger.info("Edge tables saved")