# src/data_loader.py
import pandas as pd
import json
from src.config import DATA_RAW, MIN_YEAR, MAX_YEAR

def load_raw_data(filename="global_emissions.json"):  # Changed to .json
    """Load raw data from JSON file"""
    filepath = DATA_RAW / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"Raw data not found: {filepath}")
    
    # Load JSON instead of CSV
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    # Rest of the function stays exactly the same
    df.columns = df.columns.str.lower()
    
    essential_cols = [
        'country', 'year', 'iso_code', 'population', 'gdp',
        'co2', 'co2_per_capita', 'consumption_co2', 'trade_co2',
        'coal_co2', 'gas_co2', 'oil_co2', 'land_use_change_co2',
        'total_ghg', 'temperature_change_from_ghg'
    ]
    
    available_cols = [col for col in essential_cols if col in df.columns]
    df = df[available_cols].copy()
    df = df[(df['year'] >= MIN_YEAR) & (df['year'] <= MAX_YEAR)]
    df = df.dropna(subset=['country', 'year', 'iso_code'])
    
    return df