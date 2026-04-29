import pandas as pd
from src.config import NODE_TYPES, METRICS
from src.utils import logger

def build_emits_edges(df):
    """Build Country -> Year edges"""
    edges = df[['iso_code', 'year']].drop_duplicates()
    edges['src'] = NODE_TYPES['country'] + edges['iso_code']
    edges['dst'] = NODE_TYPES['year'] + edges['year'].astype(str)
    edges['edge_type'] = 'emits_in_year'
    edges['weight'] = 1.0
    
    logger.info(f"Created {len(edges)} emits_in_year edges")
    return edges

def build_metric_edges(df):
    """Build CountryYear -> Metric edges with values"""
    df['cy_id'] = NODE_TYPES['country_year'] + df['iso_code'] + '_' + df['year'].astype(str)
    
    all_edges = []
    
    for metric in METRICS:
        if metric in df.columns:
            temp = df[['cy_id', metric]].dropna()
            temp['dst'] = NODE_TYPES['metric'] + metric.replace('_', '')
            temp['src'] = temp['cy_id']
            temp['value'] = temp[metric]
            temp['edge_type'] = 'has_metric_value'
            all_edges.append(temp[['src', 'dst', 'value', 'edge_type']])
    
    if all_edges:
        edges = pd.concat(all_edges, ignore_index=True)
        logger.info(f"Created {len(edges)} metric value edges")
        return edges
    else:
        return pd.DataFrame()