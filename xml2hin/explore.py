"""Look at one node of a built HIN and its neighbours, using the in-memory HIN
(typed adjacency lists, see hin.py). The XML is not read again.

    python explore.py <out_dir> <node_type> <node_id>
    e.g. python explore.py out/mondial country D
"""
import os
import sys

import pandas as pd

from hin import HIN

if len(sys.argv) != 4:
    sys.exit(__doc__)
out_dir, ntype, nid = sys.argv[1:4]
hin = HIN.load(out_dir, attributes=False)          # graph only; attributes read below for one node
if ntype not in hin.node_ids:
    sys.exit(f"No node type {ntype!r}. Types: {', '.join(hin.node_ids)}")
if nid not in hin.node_index[ntype]:
    sys.exit(f"No {ntype} with id {nid}")

print(f"{ntype} {nid}")
row = pd.read_parquet(os.path.join(out_dir, "hin", f"nodes_{ntype}.parquet"), filters=[("node_id", "==", nid)])
for k, v in row.iloc[0].items():
    if v and k not in ("idx", "node_id"):
        print(f"   {k}: {str(v)[:80]}")


def show(arrow, ids):
    if ids:
        more = " ..." if len(ids) > 8 else ""
        print(f"  {arrow} {len(ids)}: {', '.join(ids[:8])}{more}")


for (st, name, dt), ids in hin.neighbors(ntype, nid, direction="out").items():
    show(f"-[{name}]-> {dt}", ids)
for (st, name, dt), ids in hin.neighbors(ntype, nid, direction="in").items():
    show(f"<-[{name}]- {st}", ids)
