# scripts/view_graph.py
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import torch
from src.config import GRAPH_PATH


def main():
    if not GRAPH_PATH.exists():
        print("Graph not found. Run the pipeline first.")
        sys.exit(1)

    data = torch.load(GRAPH_PATH, weights_only=False)

    print("\n" + "=" * 40)
    print("  Node Types")
    print("=" * 40)
    for nt in data.node_types:
        print(f"  {nt:15s}  {data[nt].num_nodes:>10,} nodes")

    print("\n" + "=" * 40)
    print("  Edge Types")
    print("=" * 40)
    for et in data.edge_types:
        num_edges = data[et].edge_index.shape[1]
        src, rel, dst = et
        print(f"  ({src}) --[{rel}]--> ({dst})  {num_edges:>10,} edges")

    print("\n" + "=" * 40)
    print("  Graph Summary")
    print("=" * 40)
    print(data)


if __name__ == "__main__":
    main()