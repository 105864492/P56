import pandas as pd
from src.config import DATA_RAW, MIN_YEAR, MAX_YEAR
from src.utils import logger

def load_raw_data(filename="global_emissions.csv"):
    """Load and initial clean of raw CSV"""
    filepath = DATA_RAW / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"Raw data not found: {filepath}")
    
    logger.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)
    
    # Standardize columns
    df.columns = df.columns.str.lower()
    
    # Keep only needed columns
    essential_cols = [
        'country', 'year', 'iso_code', 'population', 'gdp',
        'co2', 'co2_per_capita', 'consumption_co2', 'trade_co2',
        'coal_co2', 'gas_co2', 'oil_co2', 'land_use_change_co2',
        'total_ghg', 'temperature_change_from_ghg'
    ]
    
    available_cols = [col for col in essential_cols if col in df.columns]
    df = df[available_cols].copy()
    
    # Filter by year
    df = df[(df['year'] >= MIN_YEAR) & (df['year'] <= MAX_YEAR)]
    
    # Drop rows with missing critical data
    df = df.dropna(subset=['country', 'year', 'iso_code'])
    
    logger.info(f"Loaded {len(df)} rows")
    return df