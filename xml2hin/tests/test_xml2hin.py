"""Run from the project folder:   python -m pytest -q"""
import os
import subprocess
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from hin import HIN          # noqa: E402
from xml2hin import build    # noqa: E402

MINI = os.path.join(ROOT, "tests", "data", "mini_dblp.xml")
DBLP_SCHEMA = os.path.join(ROOT, "schemas", "dblp.yaml")
MONDIAL = os.path.join(ROOT, "data", "mondial", "mondial.xml")
MONDIAL_SCHEMA = os.path.join(ROOT, "schemas", "mondial.yaml")


@pytest.fixture(scope="module")
def mini():
    return build(MINI, DBLP_SCHEMA)


def test_nodes(mini):
    assert mini.num_nodes("publication") == 4          # <www> and the record without key are not publications
    assert set(mini.node_ids["person"]) == {"Jürgen Müller", "Bob Brown", "Carol Chen", "Eva Editor"}


def test_entities_resolved_by_dtd(mini):
    assert "Jürgen Müller" in mini.neighbors("publication", "conf/test/A20", "authored_by")


def test_all_four_edge_types(mini):
    assert mini.neighbors("publication", "conf/test/A20", "part_of") == ["conf/test/2020"]
    assert mini.neighbors("publication", "conf/test/A20", "cites") == ["conf/test/B20"]   # "..." ignored, missing key dropped
    assert mini.neighbors("publication", "conf/test/2020", "edited_by") == ["Eva Editor"]
    assert sorted(mini.neighbors("publication", "conf/test/2020", "part_of", direction="in")) == \
        ["conf/test/A20", "conf/test/B20"]


def test_reverse_direction(mini):
    assert sorted(mini.neighbors("person", "Bob Brown", "authored_by", direction="in")) == \
        ["conf/test/A20", "conf/test/B20"]
    assert mini.neighbors("publication", "conf/test/A20", "cites", direction="in") == ["journals/tj/C21"]


def test_attributes_kept_as_is(mini):
    a = mini.node("publication", "conf/test/A20")
    assert a["title"] == "Paper A" and a["year"] == "2020" and a["pub_type"] == "inproceedings"


def test_unknown_node_raises(mini):
    with pytest.raises(KeyError):
        mini.neighbors("publication", "does/not/exist", "cites")


def test_cli_files_dangling_and_reload(tmp_path):
    out = tmp_path / "out"
    subprocess.run([sys.executable, os.path.join(ROOT, "xml2hin.py"), MINI, DBLP_SCHEMA, str(out)],
                   check=True, capture_output=True)
    d = pd.read_csv(out / "dangling_refs.csv")
    assert d.to_dict("records") == [{"edge": "cites", "src_id": "conf/test/A20", "missing_id": "journals/missing/X99"}]
    e = pd.read_parquet(out / "hin" / "edges_cites.parquet")
    assert list(e.columns) == ["src_type", "src_idx", "dst_type", "dst_idx", "src_id", "dst_id"]
    loaded = HIN.load(str(out))                          # load from disk, no XML
    assert loaded.num_edges() == build(MINI, DBLP_SCHEMA).num_edges() == 9
    assert loaded.dataset == "DBLP"


def test_save_adjacency(mini, tmp_path):
    mini.save_adjacency(str(tmp_path))
    assert (tmp_path / "relations.json").exists()
    assert (tmp_path / "publication__cites__publication.out_indptr.npy").exists()


def test_mondial_nesting_and_multi_target():
    h = build(MONDIAL, MONDIAL_SCHEMA)
    assert h.neighbors("country", "D", "capital") == ["cty-Germany-Berlin"]
    parents = h.neighbors("city", "cty-Germany-Berlin", "city_in")           # nested_in edge, 2 target types
    assert sum(len(v) for v in parents.values()) == 1
    flows = h.neighbors("river", "river-Rhein", "flows_into")                # river -> river/lake/sea
    assert sum(len(v) for v in flows.values()) == 1
    assert h.neighbors("country", "D", "on_continent") == ["europe"]


def test_memory_usage(mini):
    m = mini.memory_usage()
    assert m["total"] >= 0 and set(m) == {"adjacency_lists", "node_ids", "id_index", "attributes", "total"}

