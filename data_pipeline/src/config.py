import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
GRAPH_DATA = PROJECT_ROOT / "data" / "graph_data"

# Create directories
for dir_path in [DATA_RAW, DATA_PROCESSED, GRAPH_DATA]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Node types
NODE_TYPES = {
    'country': 'c_',
    'year': 'y_',
    'metric': 'm_',
    'country_year': 'cy_'
}

# Edge types
EDGE_TYPES = [
    'emits_in_year',
    'has_metric_value',
    'trade_flow',
    'year_follows'
]

# Metrics to include
METRICS = [
    'co2', 'co2_per_capita', 'consumption_co2', 'trade_co2',
    'coal_co2', 'gas_co2', 'oil_co2', 'land_use_change_co2',
    'total_ghg', 'temperature_change_from_ghg'
]

# Data filtering
MIN_YEAR = 1950
MAX_YEAR = 2023