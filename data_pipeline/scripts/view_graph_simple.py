import torch

print("\n" + "="*60)
print("📊 LOADING HETEROGENEOUS GRAPH")
print("="*60)

# Load the graph (weights_only=False since you created it)
graph = torch.load('data/graph_data/emission_graph.pt', weights_only=False)

print(f"\n✅ Graph loaded successfully!\n")

# Basic info
print("📌 NODE TYPES:")
for node_type in graph.node_types:
    num_nodes = graph[node_type].num_nodes if hasattr(graph[node_type], 'num_nodes') else "N/A"
    print(f"   • {node_type}: {num_nodes} nodes")

print("\n🔗 EDGE TYPES:")
for edge_type in graph.edge_types:
    edge_index = graph[edge_type].edge_index
    num_edges = edge_index.shape[1]
    print(f"   • {edge_type}: {num_edges} edges")

# Check for features
print("\n🎯 FEATURES:")
for node_type in graph.node_types:
    if hasattr(graph[node_type], 'x'):
        print(f"   • {node_type}: features shape {graph[node_type].x.shape}")
    else:
        print(f"   • {node_type}: no features (using node IDs)")

print("\n✅ Done!")