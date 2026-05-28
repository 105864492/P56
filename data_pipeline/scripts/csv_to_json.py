# scripts/csv_to_json.py
import pandas as pd
import json
from pathlib import Path

# Get the project root (two levels up from scripts folder)
project_root = Path(__file__).parent.parent

# Build correct paths
csv_path = project_root / 'data' / 'raw' / 'global_emissions.csv'
json_path = project_root / 'data' / 'raw' / 'global_emissions.json'

# Load CSV
df = pd.read_csv(csv_path)

# Convert to JSON
df.to_json(json_path, orient='records', indent=2)

print(f"Converted {len(df)} rows to JSON")
print(f"Saved to: {json_path}")