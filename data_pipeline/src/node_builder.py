import pandas as pd
from src.config import NODE_TYPES, METRICS
from src.utils import logger

def build_country_nodes(df):
    """Create country nodes"""
    countries = df[['iso_code', 'country']].drop_duplicates('iso_code')
    countries['node_id'] = NODE_TYPES['country'] + countries['iso_code']
    countries['node_type'] = 'Country'
    
    logger.info(f"Created {len(countries)} country nodes")
    return countries

def build_year_nodes(df):
    """Create year nodes"""
    years = pd.DataFrame({'year': sorted(df['year'].unique())})
    years['node_id'] = NODE_TYPES['year'] + years['year'].astype(str)
    years['node_type'] = 'Year'
    
    logger.info(f"Created {len(years)} year nodes")
    return years

def build_metric_nodes():
    """Create metric nodes"""
    metrics_df = pd.DataFrame({
        'metric_name': METRICS,
        'node_id': [NODE_TYPES['metric'] + m.replace('_', '') for m in METRICS],
        'node_type': 'Metric'
    })
    
    logger.info(f"Created {len(metrics_df)} metric nodes")
    return metrics_df

def build_country_year_nodes(df):
    """Create composite Country-Year nodes"""
    df['cy_id'] = NODE_TYPES['country_year'] + df['iso_code'] + '_' + df['year'].astype(str)
    
    cy_nodes = df[['cy_id', 'iso_code', 'year', 'country']].drop_duplicates('cy_id')
    cy_nodes['node_type'] = 'CountryYear'
    
    logger.info(f"Created {len(cy_nodes)} Country-Year nodes")
    return cy_nodes