# scripts/run_pipeline.py
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.node_builder import build_nodes
from src.edge_builder import build_edges
from src.graph_builder import build_graph
from src.config import DBLP_XML


def main():
    if not DBLP_XML.exists():
        print("dblp.xml not found. Place it in data/raw/ or run scripts/download_data.py first.")
        sys.exit(1)

    print("=" * 40)
    print("Step 1: Building nodes")
    print("=" * 40)
    authors, venues, years = build_nodes()

    print()
    print("=" * 40)
    print("Step 2: Building edges")
    print("=" * 40)
    build_edges(authors, venues, years)

    print()
    print("=" * 40)
    print("Step 3: Building graph")
    print("=" * 40)
    build_graph()

    print()
    print("Pipeline complete.")


if __name__ == "__main__":
    main()