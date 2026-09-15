from pathlib import Path
import json

import pandas as pd
import torch
from torch_geometric.data import HeteroData

import os

def load_schema(schema_path):
    with open(schema_path, "r", encoding="utf-8") as file:
        return json.load(file)


def read_table(file_path):
    file_path = Path(file_path)

    if file_path.suffix == ".parquet":
        return pd.read_parquet(file_path)

    if file_path.suffix == ".csv":
        return pd.read_csv(file_path)

    raise ValueError(f"Unsupported file type: {file_path.suffix}")


def build_graph(schema_path, base_dir):
    schema = load_schema(schema_path)
    base_dir = Path(base_dir)
    data = HeteroData()

    for node in schema["nodes"]:
        node_type = node["type"]
        file_path = base_dir / node["file"]

        node_table = read_table(file_path)

        data[node_type].num_nodes = len(node_table)

    for edge in schema["edges"]:
        source_type = edge["source_type"]
        relation = edge["relation"]
        target_type = edge["target_type"]

        file_path = base_dir / edge["file"]
        edge_table = read_table(file_path)
        source_column = edge["source_column"]
        target_column = edge["target_column"]

        source_ids = torch.tensor(
            edge_table[source_column].values,
            dtype=torch.long
        )

        target_ids = torch.tensor(
            edge_table[target_column].values,
            dtype=torch.long
        )

        edge_index = torch.stack([source_ids, target_ids])

        data[source_type, relation, target_type].edge_index = edge_index
    return data

def export_tables(schema_path, base_dir, output_dir):
    with open(schema_path, "r") as f:
        schema = json.load(f)

    os.makedirs(output_dir, exist_ok=True)

    for node in schema["nodes"]:
        node_type = node["type"]
        file_path = os.path.join(base_dir, node["file"])
        node_table = read_table(file_path)

        output_path = os.path.join(output_dir, f"{node_type}_nodes.csv")
        node_table.to_csv(output_path, index=False)

    for edge in schema["edges"]:
        source_type = edge["source_type"]
        relation = edge["relation"]
        target_type = edge["target_type"]

        file_path = os.path.join(base_dir, edge["file"])
        edge_table = read_table(file_path)

        output_path = os.path.join(
            output_dir,
            f"{source_type}_{relation}_{target_type}_edges.csv"
        )
        edge_table.to_csv(output_path, index=False)

graph = build_graph(
    "universal_hin/schema_example.json",
    "."
)

print("Node types:", graph.node_types)
print("Edge types:", graph.edge_types)

torch.save(graph, "universal_hin/generated_hin.pt")
print("Graph saved to universal_hin/generated_hin.pt")

export_tables(
    "universal_hin/schema_example.json",
    ".",
    "universal_hin/output"
)

print("Tables saved to universal_hin/output")