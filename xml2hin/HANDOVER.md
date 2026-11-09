# xml2hin 1.0: handover guide

Team P56 (COS40005/COS40006, Swinburne University of Technology), November 2026.

This guide is for the people who will use and maintain xml2hin after the student team
leaves. `README.md` has the short version and the full-DBLP download steps.

---

## 1. What it does

xml2hin turns an XML file into a **Heterogeneous Information Network (HIN)**: a graph with
several node types and several edge (relation) types.

- The code is generic. It knows nothing about any dataset.
- Each dataset gets a small **schema file** (YAML) that says which XML elements are nodes,
  where their IDs are, and which fields refer to other IDs (these become edges).
- New dataset = new schema file. No code change.

Two real datasets run with the same code: **MONDIAL** (geography: countries, cities,
rivers, ...; included) and **DBLP** (bibliography: publications and persons; the full dump
is several GB, so it is downloaded separately, see README).

Out of scope for this version: working out the schema automatically from the XML. The
schema is written by hand (see section 5). Automatic schema inference is future work.

## 2. Quick start

```
pip install -r requirements.txt          # Python 3.9 or newer, 64-bit
python run.py mondial                     # builds MONDIAL into out/mondial (under a second)
python run.py dblp                        # full DBLP, after downloading it (~7-18 min, ~17 GB RAM)
python run.py                             # list all datasets
python explore.py out/mondial country D   # look at Germany and its neighbours
python -m pytest -q                       # tests (pip install pytest first)
```

Your own data:

```
python xml2hin.py <file.xml> <schema.yaml> <out_dir>
```

## 3. How the HIN is stored

### 3.1 In memory (RAM): typed adjacency lists

A simple graph is normally stored as adjacency lists: each node has one list of its
neighbours. In an HIN the *type* of each link matters (a paper's authors are not the same
as the papers it cites), so xml2hin keeps a **separate adjacency list for every relation
type**, in both directions:

```
publication conf/x/P1
    authored_by -> [Alice, Bob]          (person)
    part_of     -> [conf/x/2020]         (publication)
    cites       -> [P7, P9]              (publication)
person Alice
    authored_by <- [conf/x/P1, P4]       (reverse direction)
```

In code this is the `HIN` class in `hin.py`:

| Part | Content |
|---|---|
| `hin.node_ids[type]` | array of node IDs; the position in the array is the node's integer index |
| `hin.node_index[type]` | dictionary ID -> index |
| `hin.attributes[type]` | table of node attributes (strings, copied from the XML unchanged) |
| `hin.relations[(src_type, name, dst_type)]` | one `Relation` = one typed adjacency list |

Each `Relation` holds its adjacency lists in **CSR form** (compressed sparse row), which is
the standard compact way to store adjacency lists:

```
out_indptr[i] .. out_indptr[i+1]  ->  slice of out_indices = neighbours of node i
in_indptr / in_indices            ->  the same for the reverse direction
```

Getting a node's neighbours is one array slice. Memory is about 8 bytes per edge per
direction, instead of one Python object per edge.

If one edge in the schema can point to several node types (e.g. MONDIAL
`flows_into: river -> river/lake/sea`), it becomes one relation per target type, so every
adjacency list stays typed.

Main calls:

```python
from xml2hin import build
from hin import HIN

hin = build("data/mondial/mondial.xml", "schemas/mondial.yaml")   # XML -> HIN in RAM
hin.neighbors("country", "D", "borders")                          # list of IDs
hin.neighbors("city", "cty-Germany-Berlin", "capital", direction="in")
hin.neighbors("country", "D")              # all relations: {(src, name, dst): [IDs]}
hin.degree("person", "Bob Brown", "authored_by", direction="in")
hin.node("country", "D")                   # attributes
print(hin)                                 # summary: node/relation counts and RAM used
hin.memory_usage()                         # RAM in MB: adjacency lists, IDs, attributes, total
```

**Lifetime.** The HIN lives in the RAM of the Python process that built or loaded it.
It is not a background service. When the script ends (or you close Python), the memory is
released. Inside a long-running session (Jupyter, Python shell) free it with:

```python
del hin
import gc; gc.collect()
```

The Parquet files on disk stay, so `HIN.load(...)` brings it back at any time.

### 3.2 On disk: parse the XML once

`xml2hin.py` writes the HIN to `<out_dir>/hin/` as Parquet tables. Loading them back
rebuilds the same in-memory HIN without reading the XML again:

```python
hin = HIN.load("out/dblp")                       # everything
hin = HIN.load("out/dblp", attributes=False)     # IDs + adjacency lists only (less RAM)
hin.save_adjacency("out/dblp/adjacency")         # optional: raw CSR arrays as .npy
```

Files:

| File | Columns / content |
|---|---|
| `hin/nodes_<type>.parquet` | `idx`, `node_id`, then one column per attribute |
| `hin/edges_<name>.parquet` | `src_type`, `src_idx`, `dst_type`, `dst_idx`, `src_id`, `dst_id` |
| `hin/meta.json` | dataset name, xml2hin version, edge definitions |
| `dangling_refs.csv` | references to IDs that are not in the file (`edge`, `src_id`, `missing_id`) |
| `summary.txt` | node and edge counts (same as the console output) |

Parquet can be read by pandas, Spark, DuckDB, R and most other tools.

## 4. How the pipeline works

```
XML file --(1) stream records--> node table + raw edge list --(2) index--> HIN
                                                                  |-> Parquet files on disk
                                                                  |-> HIN object in RAM
```

1. **Extract (streaming).** `lxml.iterparse` reads one record at a time. For each element
   listed as a node in the schema, it reads the ID, the attributes and the reference
   fields. When a top-level record is finished, it is deleted from memory, so the XML tree
   is never fully loaded. The DTD is loaded so entities like `&uuml;` become real characters.
2. **Index.** Every ID gets an integer index per node type. Every reference becomes an
   (source index, target index) pair. A reference to an ID that does not exist is **not
   kept as an edge**. It is written to `dangling_refs.csv` so nothing is lost silently.
   Duplicate edges are removed.

## 5. Adding a new dataset

1. Look at the XML (and its DTD). Find the elements that are "things" (nodes) and how
   they refer to each other: ID/IDREF attributes, key strings in child elements, or nesting.
2. Copy `schemas/mondial.yaml` or `schemas/dblp.yaml` and edit it:

```yaml
dataset: MyData
xml: data/mydata/mydata.xml          # where run.py finds the XML
note: "shown by run.py"              # optional
example: <node_type> <node_id>       # optional: explore.py example shown after the run
nodes:
  <node_type>:
    tags: [element names that are this node type]
    id: "@attr" | "child"            # where the node's ID is
    attributes: all | [fields]       # copied as-is (default: all)
    keep_tag_as: <column>            # optional: merge several tags into one type, keep the tag
  <node_type>:
    from_values: true                # nodes that only appear as values (e.g. author names)
edges:
  - {name: x, from: A, to: B, ref: "@attr"}          # IDREF / IDREFS attribute
  - {name: x, from: A, to: B, ref: "child"}          # ID as child element text
  - {name: x, from: A, to: B, ref: "child/@attr"}    # ID on a child element
  - {name: x, from: A, to: [B, C], nested_in: true}  # A sits inside B (or C) in the tree
  # optional on ref edges:  ignore: ["..."]          # placeholder values to skip
```

3. Save it as `schemas/my.yaml` and run `python run.py my` (output in `out/my/`), then
   check `summary.txt`. Many
   dangling references usually means a wrong `id` or `ref` path.
4. Look at a few nodes with `python explore.py out/my <type> <id>`.
   No code change is needed: `run.py`, `xml2hin.py` and `hin.py` are the same for every dataset.

The schema is checked on start. Unknown node types in edges, or missing `tags`/`id`/`ref`,
stop the run with a clear message.

## 6. Performance

Full DBLP dump (`dblp.xml`, 5.4 GB unzipped), version 1.0 run of 10 Nov 2026:

| | |
|---|---|
| Publications | 8,822,888 |
| Persons | 4,335,758 |
| Edges | 34,796,175 (authored_by 30.4M, part_of 4.07M, edited_by 172k, cites 112k) |
| Dangling references | 50 (all `cites` to web pages such as W3C notes, which are `<www>` records, not publications) |
| Time | ~7 to 18 min depending on the machine (442 s and 1,096 s measured on two team PCs) |
| Peak RAM | ~17 GB (measured in an earlier run) |

Reading is streaming, but the whole graph is held in RAM until it is written, so RAM grows
with the size of the graph, not the size of the file. Use a machine with at least 24 GB RAM
for full DBLP. MONDIAL runs in under a second on any laptop.

## 7. Known limitations

- **Everything is in RAM during a run.** Graphs much bigger than DBLP need a machine with
  more memory, or a future version that writes edges to disk in chunks.
- **DBLP persons are identified by their name string.** dblp already separates people
  with the same name by adding a number (e.g. `Wei Wang 0001`), and xml2hin keeps that.
  Two spellings of one person stay two nodes.
- **Attributes are opaque strings.** Nothing is converted or interpreted. Repeated fields
  are joined with `|` (e.g. several `<ee>` links).
- **One ID per node.** If the ID field has several values, the first is used. If two
  records have the same ID, the later one replaces the earlier one.
- **`nested_in` links to the nearest enclosing node** of the listed types only.
- **The schema is written by hand.** Inferring it from the XML is future work.
- `<www>` records (DBLP person home pages) are not in the DBLP schema. Add them as a node
  type if needed.

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| `Undeclared entity` / parse error on DBLP | put `dblp.dtd` in the same folder as the XML; use the DTD from the same release |
| `MemoryError` or the PC freezes on full DBLP | use a machine with 24 GB+ RAM and 64-bit Python; close other programs; reduce `attributes:` in the schema |
| `dblp.xml` not found after download | unzip `dblp.xml.gz` first (README, step 2) |
| Many dangling references on a new dataset | check the `id` and `ref` paths in the schema |
| `ImportError: pyarrow` | `pip install -r requirements.txt` |
| `curl` fails in PowerShell | use `curl.exe` |

## 9. Maintenance

- Tests: `python -m pytest -q` (10 tests: all DBLP edge types, the reverse direction,
  dangling references, save/load, the MONDIAL nesting and multi-target edges).
  `tests/data/mini_dblp.xml` is a hand-made file in DBLP format used only by the tests.
- Code layout: `xml2hin.py` (`load_schema`, `extract`, `make_tables`, `write_tables`,
  `build`), `hin.py` (`HIN`, `Relation`).
- The version is in `xml2hin.__version__` and `python xml2hin.py --version`; changes are
  listed in `CHANGELOG.md`.
- Ideas for future work: automatic schema inference from the XML/DTD; writing edges to
  disk in chunks for graphs bigger than RAM; export to graph libraries (PyTorch Geometric
  `HeteroData`, DGL, NetworkX); meta-path queries on top of `HIN.neighbors`.

## 10. Data and licences

| Data | Source | Licence |
|---|---|---|
| DBLP (full dump, not bundled) | https://dblp.org/xml/ | dblp states its data is released under CC0 1.0; please confirm on dblp.org before redistributing |
| MONDIAL (`mondial.xml`) | Univ. Göttingen (Wolfgang May); copy from github.com/ullenboom/mondial-database | check the terms on the MONDIAL web page before redistributing |

Python packages used: lxml, PyYAML, pandas, pyarrow, numpy (all open source).

## 11. Contacts

Project team P56. Contact details are in the Deployment and Handover Report.
