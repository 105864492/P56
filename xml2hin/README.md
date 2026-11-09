# xml2hin: any XML file -> Heterogeneous Information Network (HIN)

Version 1.0.0. One generic pipeline. Each XML dataset only needs a small schema file (YAML).
New dataset = new schema file, no code change.

The result is an HIN held in RAM as **typed adjacency lists** (`hin.py`), and it can be
saved to disk (Parquet) so the XML only has to be parsed once. See `HANDOVER.md` for the
full user and maintainer guide.

| File | What it is |
|---|---|
| `xml2hin.py` | the pipeline: XML + schema -> HIN, saved to `<out_dir>/hin/` |
| `hin.py` | the in-memory HIN (typed adjacency lists), load/save, neighbour queries |
| `run.py` | build any dataset by name: `python run.py <name>` uses `schemas/<name>.yaml` |
| `explore.py` | print one node and its neighbours from a saved HIN |
| `schemas/` | one YAML schema per dataset (DBLP, MONDIAL) |
| `tests/` | automated tests (`python -m pytest -q`) |

## Install
    pip install -r requirements.txt        (Python 3.9+)

## Run
Pick the dataset by name:

    python run.py                 # list datasets (one per schema) and whether their XML is present
    python run.py mondial         # MONDIAL (included), under a second
    python run.py dblp            # full DBLP (download first, see below), ~7-18 min, ~17 GB RAM
    python explore.py out/mondial country D

`run.py` is the same for every dataset: `python run.py <name>` reads `schemas/<name>.yaml`,
takes the XML path from its `xml:` line and writes to `out/<name>/`. A new dataset only needs
a new schema file. `python run.py <name> <file.xml>` uses another XML with that schema.

## Use the HIN in Python
```python
from xml2hin import build
from hin import HIN

hin = build("data/mondial/mondial.xml", "schemas/mondial.yaml")   # parse XML -> HIN in RAM
hin = HIN.load("out/mondial")                                     # or load a saved HIN, no XML
print(hin)                                                        # node and relation counts
hin.neighbors("country", "D", "borders")                          # ['F', 'A', 'CZ', ...]
hin.neighbors("city", "cty-Germany-Berlin", "capital", direction="in")   # ['D']
hin.node("country", "D")                                          # attributes as a dict
```
For big data use `HIN.load(folder, attributes=False)` to load only IDs and adjacency lists.

## Tests
    pip install pytest
    python -m pytest -q

## Run on your own XML
    python xml2hin.py <file.xml> <schema.yaml> <out_dir>
Keep the DTD next to the XML if the file has one (DBLP needs it for characters like &uuml;).

## Run on the full DBLP dump

DBLP is not included because it is several GB. Download it once as below.

### 1. Download (both files from https://dblp.org/xml/)
- `dblp.xml.gz`: the whole bibliography, about 1 GB compressed, several GB unzipped
- `dblp.dtd`: needed to read characters such as `&uuml;`. Download it on the same day as the
  XML, because the DTD changes between releases.

Windows PowerShell (use `curl.exe`, not `curl`, which is an alias in PowerShell 5):

    mkdir data\dblp_full
    cd data\dblp_full
    curl.exe -L -O https://dblp.org/xml/dblp.xml.gz
    curl.exe -L -O https://dblp.org/xml/dblp.dtd
    curl.exe -L -O https://dblp.org/xml/dblp.xml.gz.md5
    certutil -hashfile dblp.xml.gz MD5      # should match the number in dblp.xml.gz.md5
    cd ..\..

Linux / macOS:

    mkdir -p data/dblp_full && cd data/dblp_full
    wget https://dblp.org/xml/dblp.xml.gz https://dblp.org/xml/dblp.dtd https://dblp.org/xml/dblp.xml.gz.md5
    md5sum -c dblp.xml.gz.md5
    cd ../..

### 2. Unzip
`dblp.xml` only appears after you unzip `dblp.xml.gz`. Windows has no built-in gunzip, so
use Python (works on every system). From the project folder:

Windows PowerShell:

    cd data\dblp_full
    python -c "import gzip,shutil; shutil.copyfileobj(gzip.open('dblp.xml.gz','rb'), open('dblp.xml','wb'))"
    cd ..\..

Linux / macOS:

    cd data/dblp_full && gunzip -k dblp.xml.gz && cd ../..

It takes a minute or two and prints nothing while it runs. Afterwards `data/dblp_full/`
holds `dblp.xml` (several GB) next to `dblp.dtd`. They must stay in the **same folder**,
because the XML points to `dblp.dtd` by a relative path. (7-Zip "Extract Here" also works.)

### 3. Run (from the project folder)

    python run.py dblp
    (same as: python xml2hin.py data/dblp_full/dblp.xml schemas/dblp.yaml out/dblp)

No schema change is needed. Expect `part_of` and `cites` to be non-zero now; a small number
of references can still be dangling (DBLP itself has some broken keys), and these are listed
in `out/dblp/dangling_refs.csv`.

### Memory, disk and time
- **Reading is streaming**: the XML is read one record at a time with `lxml.iterparse`
  and every finished record is freed, so the several-GB file is never loaded as a whole tree.
- **The graph is kept in memory** until it is written: every node, its attributes and every
  edge. On the full dump the team measured about **17 GB peak RAM and 7 to 18 minutes**
  depending on the machine (8.8M publications, 4.3M persons, 34.8M edges, 50 dangling refs).
- So use a machine with **at least 24 GB RAM** (32 GB is comfortable) and **64-bit Python**.
  With less RAM, Windows will swap heavily or the run ends with `MemoryError`.
- Disk: keep about 10 GB free (the .gz, the unzipped XML, and the Parquet output).
  You can delete `dblp.xml.gz` after unzipping.
- Ways to lower memory if needed: close other programs; keep only the attributes you need
  in `schemas/dblp.yaml` (e.g. `attributes: [title, year]`); or drop the `cites` edge if you
  do not need it.
- A progress line is printed every 500,000 records, so you can see it is still running.
- To use the result later without the XML: `HIN.load("out/dblp", attributes=False)`
  loads only IDs and adjacency lists (far less RAM than a fresh run).
- Do not open `dblp.xml` in a normal text editor; it is too big. Use
  `python explore.py out/dblp publication <key>` to look at results instead.

## Writing a schema
```yaml
dataset: MyData
xml: data/mydata/mydata.xml          # optional: where run.py finds the XML
note: "shown by run.py"              # optional
example: <node_type> <node_id>       # optional: explore.py example shown after the run
nodes:
  <node_type>:
    tags: [element names that are this node type]
    id: "@attr" | "child"            # where the node's ID is
    attributes: all | [fields]       # copied as-is, never interpreted (default: all)
    keep_tag_as: <column>            # optional: merge several tags into one type, keep the tag
  <node_type>:
    from_values: true                # nodes that only appear as values (e.g. author names)
edges:
  - {name: x, from: A, to: B, ref: "@attr"}          # ID reference in an attribute (IDREF/IDREFS)
  - {name: x, from: A, to: B, ref: "child"}          # ID reference as child element text
  - {name: x, from: A, to: B, ref: "child/@attr"}    # ID reference on a child element
  - {name: x, from: A, to: [B, C], nested_in: true}  # A sits inside B (or C) in the XML tree
```

## Output (`<out_dir>/`)
- `hin/nodes_<type>.parquet`: idx, node_id, attributes
- `hin/edges_<name>.parquet`: src_idx, dst_type, dst_idx, src_id, dst_id
- `dangling_refs.csv`: references pointing to IDs that are not in the file
- `summary.txt`: node and edge counts by type

## Data
- `data/mondial/mondial.xml`: the full MONDIAL geography database (Univ. Göttingen; copy from github.com/ullenboom/mondial-database), with `mondial.dtd`.
- DBLP: not included (several GB); download the full dump from https://dblp.org/xml/ as described above.
- `tests/data/mini_dblp.xml` is a hand-made file in DBLP format used only by the tests.

Data licences: see `HANDOVER.md`.
