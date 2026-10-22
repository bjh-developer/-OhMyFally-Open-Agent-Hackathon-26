#!/usr/bin/env python
"""GeBIZ awards: download raw CSV, run the quotation check / agency shortlist, write data/sample/awards.csv.

  python scripts/fetch_gebiz.py check      # ETT vs ETQ counts + agency shortlist stats
  python scripts/fetch_gebiz.py            # download (cached) + write data/sample/awards.csv

Source: data.gov.sg dataset d_acde1106003906a75c3fa052592f2fcb (Singapore Open Data Licence).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import RAW, SAMPLE, download_dataset  # noqa: E402

DATASET_ID = "d_acde1106003906a75c3fa052592f2fcb"
RAW_CSV = RAW / "gebiz_awards.csv"
AGENCIES = [
    "Housing and Development Board",
    "People's Association",
    "National Parks Board",
]
COLUMNS = ["tender_no", "tender_description", "agency", "award_date", "tender_detail_status",
           "supplier_name", "awarded_amt"]


def load_raw(force: bool = False) -> pd.DataFrame:
    download_dataset(DATASET_ID, RAW_CSV, force=force)
    return pd.read_csv(RAW_CSV, dtype=str, keep_default_na=False)


def parse(df: pd.DataFrame) -> pd.DataFrame:
    out = df[COLUMNS].copy()
    d = pd.to_datetime(out["award_date"], format="%d/%m/%Y", errors="coerce")
    if d.isna().any():
        raise ValueError(f"{int(d.isna().sum())} unparseable award_date values")
    out["award_date"] = d.dt.strftime("%Y-%m-%d")  # ISO, loads straight into a Postgres date column
    out["awarded_amt"] = pd.to_numeric(out["awarded_amt"], errors="raise")
    return out


def quotation_check(df: pd.DataFrame) -> None:
    kind = df["tender_no"].str[6:9]
    amt = pd.to_numeric(df["awarded_amt"], errors="coerce")
    print("tender_no type (chars 7-9) counts:")
    for k, n in kind.value_counts().items():
        print(f"  {k}: {n}")
    print(f"ETT={int((kind == 'ETT').sum())}  ETQ={int((kind == 'ETQ').sum())}")
    ett = amt[kind == "ETT"]
    print(f"ETT awards < S$90k: {int((ett < 90000).sum())}  < S$6k: {int((ett < 6000).sum())}")


def shortlist_stats(df: pd.DataFrame, top: int = 25) -> None:
    p = parse(df)
    p["d"] = pd.to_datetime(p["award_date"])
    rows = []
    for ag, g in p.groupby("agency"):
        sub = g[(g.awarded_amt > 0) & (g.awarded_amt < 90000)]
        cand = 0
        for _, y in sub.sort_values("d").groupby("supplier_name"):
            y = y.reset_index(drop=True)
            for i in range(len(y)):
                w = y[(y.d >= y.d[i]) & (y.d <= y.d[i] + pd.Timedelta(days=90))]
                if len(w) >= 2 and w.awarded_amt.sum() > 90000:
                    cand += 1
                    break
        rows.append((ag, len(g), g.supplier_name.nunique(), len(sub), g.awarded_amt.median(), cand))
    res = pd.DataFrame(rows, columns=["agency", "awards", "suppliers", "sub90k", "median", "r4_candidates"])
    print(res.sort_values("awards", ascending=False).head(top).to_string(index=False))


def build_sample() -> pd.DataFrame:
    df = parse(load_raw())
    s = df[df["agency"].isin(AGENCIES)].sort_values(["agency", "award_date", "tender_no", "supplier_name"])
    missing = set(AGENCIES) - set(s["agency"].unique())
    if missing:
        raise SystemExit(f"agencies not found in GeBIZ data: {missing}")
    SAMPLE.mkdir(parents=True, exist_ok=True)
    s.to_csv(SAMPLE / "awards.csv", index=False)
    return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="build", choices=["build", "check"])
    ap.add_argument("--force", action="store_true", help="re-download raw CSV")
    a = ap.parse_args()
    if a.cmd == "check":
        raw = load_raw(a.force)
        quotation_check(raw)
        shortlist_stats(raw)
        return
    if a.force:
        load_raw(True)
    s = build_sample()
    print(f"wrote {SAMPLE / 'awards.csv'}: {len(s)} rows")
    print(s.groupby("agency").size().to_string())
    print("suppliers:", s["supplier_name"].nunique(), "dates:", s["award_date"].min(), "..", s["award_date"].max())


if __name__ == "__main__":
    main()
