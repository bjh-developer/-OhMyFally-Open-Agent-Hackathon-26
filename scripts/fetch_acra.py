#!/usr/bin/env python
"""ACRA entities: download the 27 collection CSVs, keep only candidate matches for our suppliers.

  python scripts/fetch_acra.py download   # raw CSVs -> data/raw/acra/ (rate limited, cached)
  python scripts/fetch_acra.py            # build data/sample/acra_entities.{parquet,csv}

Candidate rule: an ACRA entity is kept when ANY of its names (current or former_entity_name1..15)
shares the first two significant tokens with a supplier in data/sample/awards.csv, or shares the first
token when that token is rare in ACRA (<= RARE_MAX entities). Source: data.gov.sg collection 2
(Singapore Open Data Licence).
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import RAW, ROOT, SAMPLE, download_dataset  # noqa: E402
from app.resolver.normalize import blocking_keys, normalize  # noqa: E402

COLLECTION_META = "https://api-production.data.gov.sg/v2/public/api/collections/2/metadata"
ACRA_RAW = RAW / "acra"
RARE_MAX = 50
FORMER_COLS = [f"former_entity_name{i}" for i in range(1, 16)]
KEEP_COLS = ["uen", "entity_name", "entity_type_description", "entity_status_description",
             "registration_incorporation_date", "block", "street_name", "level_no", "unit_no",
             "building_name", "postal_code", "primary_ssic_code", "primary_ssic_description",
             "no_of_officers"] + FORMER_COLS


def dataset_ids() -> list[str]:
    r = requests.get(COLLECTION_META, timeout=60)
    r.raise_for_status()
    return r.json()["data"]["collectionMetadata"]["childDatasets"]


def download_all(pause: float = 14.0) -> list[Path]:
    ids = dataset_ids()
    paths = []
    for i, ds in enumerate(ids, 1):
        dest = ACRA_RAW / f"{ds}.csv"
        cached = dest.exists() and dest.stat().st_size > 0
        download_dataset(ds, dest)
        print(f"[{i}/{len(ids)}] {ds} {dest.stat().st_size // 1024} KiB", flush=True)
        paths.append(dest)
        if not cached:
            time.sleep(pause)  # unauthenticated limit: 5 requests/min
    return paths


def raw_files() -> list[Path]:
    files = sorted(ACRA_RAW.glob("*.csv"))
    if not files:
        raise SystemExit("no raw ACRA files; run: python scripts/fetch_acra.py download")
    return files


def read_file(f: Path) -> pd.DataFrame:
    df = pd.read_csv(f, dtype=str, keep_default_na=False)
    for c in KEEP_COLS:
        if c not in df.columns:
            df[c] = ""
    return df[KEEP_COLS]


def entity_keys(row) -> list[tuple[str, str]]:
    ks = []
    for n in row:
        if n:
            f, t = blocking_keys(n)
            if f:
                ks.append((f, t))
    return ks


def supplier_keys() -> tuple[set[str], set[str]]:
    aw = pd.read_csv(SAMPLE / "awards.csv", dtype=str, keep_default_na=False)
    first, two = set(), set()
    for n in aw["supplier_name"].unique():
        f, t = blocking_keys(n)
        if f:
            first.add(f)
            two.add(t)
    return first, two


def build() -> pd.DataFrame:
    """Two streaming passes over the raw files (a full concat is ~2M rows x 30 string columns: OOM)."""
    first_s, two_s = supplier_keys()
    files = raw_files()
    first_counts: Counter[str] = Counter()
    total = 0
    for f in files:  # pass 1: how common is each first token across ACRA?
        df = read_file(f)
        total += len(df)
        for row in df[["entity_name"] + FORMER_COLS].to_numpy():
            for tok in {k[0] for k in entity_keys(row)}:
                first_counts[tok] += 1
    kept = []
    for f in files:  # pass 2: keep candidates
        df = read_file(f)
        mask = [any(t in two_s or (ft in first_s and first_counts[ft] <= RARE_MAX) for ft, t in entity_keys(row))
                for row in df[["entity_name"] + FORMER_COLS].to_numpy()]
        kept.append(df[pd.Series(mask, index=df.index)])
    out = pd.concat(kept, ignore_index=True).drop_duplicates("uen").reset_index(drop=True)
    out["registration_incorporation_date"] = pd.to_datetime(
        out["registration_incorporation_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    SAMPLE.mkdir(parents=True, exist_ok=True)
    out.to_parquet(SAMPLE / "acra_entities.parquet", index=False)
    out.to_csv(SAMPLE / "acra_entities.csv", index=False)  # fallback if Zetaris can't read Parquet
    print(f"ACRA total rows: {total}  candidates kept: {len(out)}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="build", choices=["build", "download"])
    a = ap.parse_args()
    if a.cmd == "download":
        download_all()
    else:
        build()


if __name__ == "__main__":
    main()
