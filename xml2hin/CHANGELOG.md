# Changelog

## 1.0.0 (November 2026): handover release
- New `hin.py`: the HIN in RAM as typed adjacency lists (CSR per relation, both
  directions), with `neighbors`, `degree`, `node`, `summary` and `memory_usage`.
- `HIN.load(out_dir)` rebuilds the HIN from the saved Parquet files, so the XML is parsed
  only once. `attributes=False` loads just the graph structure for large datasets.
- `xml2hin.build(xml, schema)` returns the HIN directly from Python.
- `hin/meta.json` written with each output. `--version` flag added.
- Progress line every 500,000 records for long runs (full DBLP).
- `explore.py` now uses the in-memory HIN.
- The DBLP random sample was removed (its crossref/cite targets were missing, so part_of
  and cites were 0). DBLP is now run on the full dump.
- `run_demo.py` replaced by the generic `run.py <name>`: it reads `schemas/<name>.yaml`
  (new optional `xml:`, `note:`, `example:` keys) and writes to `out/<name>/`.
- Tests added (`tests/`, pytest).
- README: how to download, unzip and run the full DBLP dump, plus memory notes.
- New `HANDOVER.md` user and maintainer guide.
- `requirements.txt` lists minimum versions and adds numpy.

## 0.6 (October 2026): Sprint 6 beta
- Generic schema-driven XML -> HIN pipeline, streaming parser, Parquet output.
- Demo on the DBLP sample and MONDIAL with the same code.
