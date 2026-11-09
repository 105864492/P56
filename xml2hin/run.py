"""Build the HIN for any dataset by name. Works for every dataset; no code change needed.

    python run.py                    list the datasets (one per file in schemas/)
    python run.py <name>             build schemas/<name>.yaml -> out/<name>/
    python run.py <name> <file.xml>  same, but use this XML instead of the one in the schema

Examples:
    python run.py mondial            MONDIAL (included), under a second
    python run.py dblp               full DBLP (download first, see README), ~7-18 min, ~17 GB RAM

New dataset: put the XML (+ DTD) under data/, write schemas/<name>.yaml with an
`xml:` line pointing to it, then run  python run.py <name>
"""
import glob
import os
import subprocess
import sys

import yaml

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def read_schema(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def list_datasets():
    print(__doc__)
    print("Datasets found in schemas/:")
    for path in sorted(glob.glob("schemas/*.yaml")):
        name = os.path.splitext(os.path.basename(path))[0]
        s = read_schema(path)
        xml = s.get("xml", "")
        status = "ready" if xml and os.path.exists(xml) else (f"missing {xml}" if xml else "no xml: line")
        print(f"  python run.py {name:<12} {s.get('note', '')}  [{status}]")
    sys.exit(1)


if len(sys.argv) not in (2, 3):
    list_datasets()
name = sys.argv[1]
schema = f"schemas/{name}.yaml"
if not os.path.exists(schema):
    print(f"No schema {schema}\n")
    list_datasets()
s = read_schema(schema)
xml = sys.argv[2] if len(sys.argv) == 3 else s.get("xml")
if not xml:
    sys.exit(f"{schema} has no 'xml:' line. Add one, or run:  python run.py {name} <file.xml>")
if not os.path.exists(xml):
    sys.exit(f"{xml} not found. {s.get('note', '')}")
out = f"out/{name}"
if s.get("note"):
    print(s["note"])
print(f"python xml2hin.py {xml} {schema} {out}\n")
subprocess.run([sys.executable, "xml2hin.py", xml, schema, out], check=True)
print(f"\nLook at one node:  python explore.py {out} <node_type> <node_id>")
if s.get("example"):
    print(f"   e.g.            python explore.py {out} {s['example']}")
