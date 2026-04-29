import pandas as pd
import torch
from pathlib import Path

# Allow PyG HeteroData to be loaded safely
torch.serialization.add_safe_globals([torch.load, 'torch_geometric.data.hetero_data.HeteroData'])

print("\n" + "="*70)
print("📊 ALL GENERATED FILES")
print("="*70)

# Find all parquet and pt files
all_files = list(Path('data').rglob('*.parquet')) + list(Path('data').rglob('*.pt'))

for filepath in sorted(all_files):
    print(f"\n{'─'*70}")
    print(f"📄 {filepath}")
    print(f"{'─'*70}")
    
    if filepath.suffix == '.parquet':
        df = pd.read_parquet(filepath)
        print(f"📏 Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"📋 Columns: {', '.join(df.columns)}")
        print(f"\n🔍 First 3 rows:")
        print(df.head(3).to_string())
        
        # Special info for edge files
        if 'edge_type' in df.columns:
            print(f"\n🔗 Edge types: {df['edge_type'].unique()}")
        if 'node_type' in df.columns:
            print(f"\n🏷️ Node type: {df['node_type'].unique()[0]}")
            
    elif filepath.suffix == '.pt':
        # Load with weights_only=False (safe since you created the file)
        graph = torch.load(filepath, weights_only=False)
        print(f"📏 Graph info:")
        print(f"   Node types: {graph.node_types}")
        print(f"   Edge types: {graph.edge_types}")
        for node_type in graph.node_types:
            if hasattr(graph[node_type], 'num_nodes'):
                print(f"   {node_type}: {graph[node_type].num_nodes} nodes")

print("\n" + "="*70)
print("✅ Done viewing all files")