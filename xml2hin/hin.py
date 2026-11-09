"""In-memory Heterogeneous Information Network (HIN) stored as typed adjacency lists.

A plain graph keeps one adjacency list per node: "P1 -> Alice, Bob, P7".
An HIN has many node types and many edge (relation) types, so the neighbours are
kept separately for every relation:

    publication P1
        authored_by -> [Alice, Bob]
        part_of     -> [conf/x/2020]
        cites       -> [P7, P9]
    person Alice
        authored_by <- [P1, P4]           (reverse direction)

Storage: every relation (src_type, name, dst_type) has two compact adjacency
lists, one per direction, in CSR form (two numpy arrays):

    indptr[i] .. indptr[i+1]   = slice of `indices` holding node i's neighbours
    indices                    = neighbour indexes (into the destination node type)

so a neighbour lookup is one array slice, and memory is about 8 bytes per edge per
direction instead of a Python object per edge.

    from hin import HIN
    hin = HIN.load("out/dblp")                   # no XML needed
    hin.neighbors("publication", "conf/x/P1", "cites")
    hin.neighbors("person", "Alice", "authored_by", direction="in")

The HIN can be built straight from an XML file (xml2hin.build) or loaded from a
folder written by xml2hin.py / HIN.save (no need to parse the XML again).
"""
import glob
import json
import os

import numpy as np
import pandas as pd


class Relation:
    """One typed adjacency list: src_type -[name]-> dst_type, both directions."""

    def __init__(self, src_type, name, dst_type, src_idx, dst_idx, n_src, n_dst):
        self.src_type, self.name, self.dst_type = src_type, name, dst_type
        src_idx = np.asarray(src_idx, dtype=np.int64)
        dst_idx = np.asarray(dst_idx, dtype=np.int64)
        self.out_indptr, self.out_indices = _csr(src_idx, dst_idx, n_src)
        self.in_indptr, self.in_indices = _csr(dst_idx, src_idx, n_dst)

    @property
    def key(self):
        return (self.src_type, self.name, self.dst_type)

    @property
    def num_edges(self):
        return int(len(self.out_indices))

    def out(self, i):
        return self.out_indices[self.out_indptr[i]:self.out_indptr[i + 1]]

    def inc(self, i):
        return self.in_indices[self.in_indptr[i]:self.in_indptr[i + 1]]

    def __repr__(self):
        return f"{self.src_type} -[{self.name}]-> {self.dst_type}: {self.num_edges:,} edges"


def _csr(rows, cols, n_rows):
    order = np.argsort(rows, kind="stable")
    indices = cols[order]
    counts = np.bincount(rows, minlength=n_rows)
    indptr = np.zeros(n_rows + 1, dtype=np.int64)
    np.cumsum(counts, out=indptr[1:])
    return indptr, indices


class HIN:
    def __init__(self):
        self.node_ids = {}      # node type -> numpy array of ID strings (position = idx)
        self.node_index = {}    # node type -> {ID string: idx}
        self.attributes = {}    # node type -> DataFrame (row idx = node idx); may be empty
        self.relations = {}     # (src_type, name, dst_type) -> Relation
        self.dataset = ""

    # ---------- building ----------

    def add_node_type(self, ntype, ids, attributes=None):
        ids = np.asarray(list(ids), dtype=object)
        self.node_ids[ntype] = ids
        self.node_index[ntype] = {v: i for i, v in enumerate(ids)}
        self.attributes[ntype] = attributes if attributes is not None else pd.DataFrame(index=range(len(ids)))

    def add_relation(self, src_type, name, dst_type, src_idx, dst_idx):
        rel = Relation(src_type, name, dst_type, src_idx, dst_idx,
                       len(self.node_ids[src_type]), len(self.node_ids[dst_type]))
        self.relations[rel.key] = rel
        return rel

    @classmethod
    def from_tables(cls, node_tables, edge_tables, dataset=""):
        """node_tables: {type: DataFrame with idx, node_id, attrs...}
           edge_tables: {name: DataFrame with src_type, src_idx, dst_type, dst_idx}"""
        hin = cls()
        hin.dataset = dataset
        for ntype, df in node_tables.items():
            df = df.sort_values("idx")
            hin.add_node_type(ntype, df["node_id"], df.drop(columns=["idx", "node_id"]).reset_index(drop=True))
        for name, df in edge_tables.items():
            if df.empty:
                continue
            for (st, dt), g in df.groupby(["src_type", "dst_type"], sort=False):
                hin.add_relation(st, name, dt, g["src_idx"].to_numpy(), g["dst_idx"].to_numpy())
        return hin

    @classmethod
    def load(cls, folder, attributes=True):
        """Load from an xml2hin output folder (the one holding hin/). No XML needed.
        attributes=False loads only IDs and adjacency lists (much less RAM on big data)."""
        hin_dir = os.path.join(folder, "hin") if os.path.isdir(os.path.join(folder, "hin")) else folder
        nodes = {os.path.basename(p)[6:-8]: pd.read_parquet(p, columns=None if attributes else ["idx", "node_id"])
                 for p in sorted(glob.glob(os.path.join(hin_dir, "nodes_*.parquet")))}
        if not nodes:
            raise FileNotFoundError(f"No nodes_*.parquet in {hin_dir}")
        edges = {os.path.basename(p)[6:-8]: pd.read_parquet(p, columns=["src_type", "src_idx", "dst_type", "dst_idx"])
                 for p in sorted(glob.glob(os.path.join(hin_dir, "edges_*.parquet")))}
        meta_path = os.path.join(hin_dir, "meta.json")
        dataset = json.load(open(meta_path, encoding="utf-8")).get("dataset", "") if os.path.exists(meta_path) else ""
        return cls.from_tables(nodes, edges, dataset)

    # ---------- queries ----------

    def idx(self, ntype, node_id):
        try:
            return self.node_index[ntype][node_id]
        except KeyError:
            raise KeyError(f"No {ntype} node with id {node_id!r}") from None

    def find_relations(self, ntype, name=None, direction="out"):
        side = 0 if direction == "out" else 2
        return [r for k, r in self.relations.items() if k[side] == ntype and (name is None or k[1] == name)]

    def neighbors(self, ntype, node_id, relation=None, direction="out"):
        """IDs of the neighbours of one node.
        relation: edge name (e.g. 'cites'); None = all relations.
        direction: 'out' (node is the source) or 'in' (node is the target).
        Returns a list when one relation matches, else {relation key: list}."""
        i = self.idx(ntype, node_id)
        result = {}
        for r in self.find_relations(ntype, relation, direction):
            if direction == "out":
                result[r.key] = self.node_ids[r.dst_type][r.out(i)].tolist()
            else:
                result[r.key] = self.node_ids[r.src_type][r.inc(i)].tolist()
        if relation is not None and len(result) == 1:
            return next(iter(result.values()))
        return result

    def degree(self, ntype, node_id, relation, direction="out"):
        n = self.neighbors(ntype, node_id, relation, direction)
        return len(n) if isinstance(n, list) else sum(len(v) for v in n.values())

    def node(self, ntype, node_id):
        """Attributes of one node as a dict."""
        return {k: v for k, v in self.attributes[ntype].iloc[self.idx(ntype, node_id)].items() if v != ""}

    def num_nodes(self, ntype=None):
        if ntype:
            return len(self.node_ids[ntype])
        return sum(len(v) for v in self.node_ids.values())

    def num_edges(self):
        return sum(r.num_edges for r in self.relations.values())

    def memory_usage(self):
        """Approximate RAM used by this HIN, in MB, split into parts."""
        mb = 1024 ** 2
        adj = sum(getattr(r, p).nbytes for r in self.relations.values()
                  for p in ("out_indptr", "out_indices", "in_indptr", "in_indices"))
        ids = sum(int(pd.Series(v, dtype=object).memory_usage(deep=True)) for v in self.node_ids.values())
        index = sum(len(d) * 100 for d in self.node_index.values())     # dict entry overhead, rough
        attrs = sum(int(df.memory_usage(deep=True).sum()) for df in self.attributes.values())
        parts = {"adjacency_lists": adj, "node_ids": ids, "id_index": index, "attributes": attrs}
        out = {k: round(v / mb, 1) for k, v in parts.items()}
        out["total"] = round(sum(parts.values()) / mb, 1)
        return out

    def summary(self):
        lines = [f"HIN {self.dataset}: {self.num_nodes():,} nodes, {self.num_edges():,} edges, "
                 f"~{self.memory_usage()['total']:,} MB in RAM"]
        for t, ids in self.node_ids.items():
            lines.append(f"  node type {t:<14} {len(ids):>10,}")
        for r in self.relations.values():
            lines.append(f"  relation  {repr(r)}")
        return "\n".join(lines)

    def __repr__(self):
        return self.summary()

    # ---------- saving the adjacency lists themselves (optional) ----------

    def save_adjacency(self, folder):
        """Write the CSR arrays as .npy files (useful for other tools, e.g. numpy/PyTorch)."""
        os.makedirs(folder, exist_ok=True)
        index = []
        for (st, name, dt), r in self.relations.items():
            base = f"{st}__{name}__{dt}"
            for part in ("out_indptr", "out_indices", "in_indptr", "in_indices"):
                np.save(os.path.join(folder, f"{base}.{part}.npy"), getattr(r, part))
            index.append({"src_type": st, "relation": name, "dst_type": dt, "file_prefix": base,
                          "edges": r.num_edges})
        with open(os.path.join(folder, "relations.json"), "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)
