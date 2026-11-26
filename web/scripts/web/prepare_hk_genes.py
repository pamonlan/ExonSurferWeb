#!/usr/bin/env python3
"""
prepare_hk_genes.py
────────────────────
Reads all downloaded housekeeping gene files from the Data/HK/ directory,
normalises them into a single unified format, deduplicates, prioritises
the top N most stable genes per species, and writes two CSVs:
  - combined_hk_genes.csv        full dataset
  - combined_hk_genes_top50.csv  top-50 per species (recommended for UI)

Stability ranking logic:
  PaGenBase : sort by DPM ascending  (lower = more stable across conditions)
  HRT Atlas : sort by context priority: most_stable > multi-tissue > human_mouse_common
  RED (rice): sort by CV ascending if available, else by AVG descending

Output columns:
    species, gene_name, source, source_url, context, dpm, avg_expression, rank

Usage:
    python prepare_hk_genes.py
    python prepare_hk_genes.py --hk-dir /path/to/HK --out combined_hk_genes.csv --top-n 50
"""

import argparse
import pandas as pd
from pathlib import Path

COLS = ["species", "gene_name", "source", "source_url", "context",
        "dpm", "avg_expression"]

HRT_SOURCE  = "HRT Atlas"
HRT_URL     = "https://housekeeping.unicamp.br"

PG_SOURCE   = "PaGenBase"
PG_URL      = "https://bioinf.xmu.edu.cn/PaGenBase/download.jsp"

RED_SOURCE  = "Rice Expression Database"
RED_URL     = "https://ngdc.cncb.ac.cn/red/hkts"

PAGENBASE_SPECIES_MAP = {
    "arabidopsisthaliana":      "arabidopsis_thaliana",
    "arabidopsis thaliana":     "arabidopsis_thaliana",
    "caenorhabditis elegans":   "caenorhabditis_elegans",
    "danio rerio":              "danio_rerio",
    "drosophila melanogaster":  "drosophila_melanogaster",
    "glycine max":              "glycine_max",
    "saccharomyces cerevisiae": "saccharomyces_cerevisiae",
}

# ── HRT Atlas ─────────────────────────────────────────────────────────────────

def parse_hrt_atlas(hk_dir: Path) -> pd.DataFrame:
    atlas_dir = hk_dir / "Housekeeping Transcript Atlas"
    rows = []

    human_file = atlas_dir / "Housekeeping_GenesHuman.csv"
    if human_file.exists():
        df = pd.read_csv(human_file, sep=";", usecols=["Ensembl", "Gene.name"])
        df = df.rename(columns={"Gene.name": "gene_name"})
        df["species"] = "homo_sapiens"; df["source"] = HRT_SOURCE
        df["source_url"] = HRT_URL;     df["context"] = "multi-tissue"
        df["dpm"] = None;               df["avg_expression"] = None
        rows.append(df[COLS])
        print(f"  HRT Atlas human:         {len(df):>6} entries")

    mouse_stable = atlas_dir / "MostStable_Mouse.csv"
    if mouse_stable.exists():
        df = pd.read_csv(mouse_stable, sep=";", usecols=["transcript_id", "Gene.name"])
        df = df.rename(columns={"Gene.name": "gene_name"})
        df["species"] = "mus_musculus"; df["source"] = HRT_SOURCE
        df["source_url"] = HRT_URL;     df["context"] = "most_stable"
        df["dpm"] = None;               df["avg_expression"] = None
        rows.append(df[COLS])
        print(f"  HRT Atlas mouse stable:  {len(df):>6} entries")

    common_file = atlas_dir / "Human_Mouse_Common.csv"
    if common_file.exists():
        df = pd.read_csv(common_file, sep=";")
        for col, species in [("Mouse", "mus_musculus"), ("Human", "homo_sapiens")]:
            if col in df.columns:
                sub = pd.DataFrame({
                    "gene_name": df[col], "species": species,
                    "source": HRT_SOURCE, "source_url": HRT_URL,
                    "context": "human_mouse_common",
                    "dpm": None, "avg_expression": None,
                })
                rows.append(sub[COLS])
        print(f"  HRT Atlas common:        {len(df):>6} entries (x2 species)")

    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=COLS)


# ── PaGenBase ─────────────────────────────────────────────────────────────────

def _pg_species(fname: str):
    stem = Path(fname).stem.lower().split("|")[0].strip()
    for key, val in PAGENBASE_SPECIES_MAP.items():
        if stem == key or stem.startswith(key.replace(" ", "")):
            return val
    for key, val in PAGENBASE_SPECIES_MAP.items():
        if key in stem:
            return val
    return None

def _pg_context(fname: str):
    stem = Path(fname).stem
    return stem.split("|")[1].strip().lower() if "|" in stem else "unknown"

def parse_pagenbase(hk_dir: Path) -> pd.DataFrame:
    pg_dir = hk_dir / "PaGenBase"
    if not pg_dir.exists():
        print("  PaGenBase directory not found — skipping"); return pd.DataFrame(columns=COLS)
    rows = []
    for fpath in sorted(pg_dir.glob("*.txt")):
        species_key = _pg_species(fpath.name)
        if not species_key:
            print(f"  PaGenBase: cannot map {fpath.name} — skipping"); continue
        context = _pg_context(fpath.name)

        # Skip comment lines (^  !)
        with open(fpath, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        data_lines = [l for l in lines if not l.startswith("^") and not l.startswith("!")]
        from io import StringIO
        try:
            df = pd.read_csv(StringIO("".join(data_lines)), sep="\t")
        except Exception as e:
            print(f"  PaGenBase: error reading {fpath.name}: {e}"); continue
        if "Gene Symbol" not in df.columns:
            print(f"  PaGenBase: no 'Gene Symbol' in {fpath.name} — skipping"); continue

        df = df.rename(columns={"Gene Symbol": "gene_name", "DPM": "dpm"})
        df["gene_name"] = df["gene_name"].astype(str).str.strip()
        df = df[df["gene_name"] != ""].copy()

        # Mean DPM per gene across datasets in this file
        agg = df.groupby("gene_name", as_index=False)["dpm"].mean()
        agg["species"] = species_key; agg["source"] = PG_SOURCE
        agg["source_url"] = PG_URL;   agg["context"] = context
        agg["avg_expression"] = None
        rows.append(agg[COLS])
        print(f"  PaGenBase {species_key:<35} context={context:<15} {len(agg):>5} genes")

    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=COLS)


# ── Rice Expression Database ──────────────────────────────────────────────────

def parse_red(hk_dir: Path) -> pd.DataFrame:
    red_dir = hk_dir / "Rice Expression Database"
    if not red_dir.exists():
        print("  RED directory not found — skipping"); return pd.DataFrame(columns=COLS)
    rows = []
    file_map = {
        "most_robust_rice_hk_genes.csv": "most_stable",
        "hk-ts.csv":                     "multi-tissue",
    }
    for fname, context in file_map.items():
        fpath = red_dir / fname
        if not fpath.exists():
            print(f"  RED: {fname} not found — skipping"); continue
        df = pd.read_csv(fpath)
        if "OS Gene ID" in df.columns:
            df["gene_name"] = df["OS Gene ID"].replace("-", pd.NA).fillna(df["LOC Gene ID"])
        else:
            df["gene_name"] = df["LOC Gene ID"]
        avg_col = "AVG" if "AVG" in df.columns else None
        cv_col  = "CV"  if "CV"  in df.columns else None
        sub = pd.DataFrame({
            "gene_name": df["gene_name"].astype(str).str.strip(),
            "species": "oryza_sativa", "source": RED_SOURCE,
            "source_url": RED_URL, "context": context,
            "dpm": df[cv_col] if cv_col else None,   # use CV as stability proxy
            "avg_expression": df[avg_col] if avg_col else None,
        })
        sub = sub[sub["gene_name"].notna() & (sub["gene_name"] != "")].copy()
        rows.append(sub[COLS])
        print(f"  RED oryza_sativa context={context:<15} {len(sub):>5} genes")
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=COLS)


# ── Prioritisation ────────────────────────────────────────────────────────────

# Context priority order: higher index = preferred context
CONTEXT_PRIORITY = {
    # HRT Atlas
    "most_stable":          10,
    "multi-tissue":          8,
    "human_mouse_common":    6,
    # PaGenBase (development > tissue > strain > condition > others > cell cycle)
    "development":           7,
    "tissue":                6,
    "strain":                5,
    "condition":             4,
    "others":                3,
    "cell cycle":            2,
    "unknown":               1,
}

def prioritise(df: pd.DataFrame, top_n: int = 50) -> pd.DataFrame:
    """
    For each species, select the top_n most stable genes.

    Strategy per source:
    - PaGenBase  : lowest mean DPM (most constitutive) wins;
                   prefer higher-priority context when a gene appears in multiple
    - HRT Atlas  : prefer most_stable > multi-tissue > human_mouse_common;
                   all genes in most_stable are already the best
    - RED        : lowest CV (most stable) wins within most_stable first

    Output includes a 'rank' column (1 = most stable).
    """
    results = []

    for species, sdf in df.groupby("species"):
        # Add context priority score
        sdf = sdf.copy()
        sdf["_ctx_pri"] = sdf["context"].map(CONTEXT_PRIORITY).fillna(0)

        # For each gene keep only the row from the best context
        # (highest priority, then lowest DPM)
        sdf_best = (
            sdf.sort_values(["_ctx_pri", "dpm"],
                            ascending=[False, True],  # best context first, then lowest DPM
                            na_position="last")
               .drop_duplicates(subset=["gene_name"], keep="first")
        )

        # Sort for final ranking
        sdf_best = sdf_best.sort_values(
            ["_ctx_pri", "dpm"],
            ascending=[False, True],
            na_position="last"
        ).head(top_n).copy()

        sdf_best["rank"] = range(1, len(sdf_best) + 1)
        sdf_best = sdf_best.drop(columns=["_ctx_pri"])
        results.append(sdf_best)

        print(f"  {species:<40} top {len(sdf_best):>3}  "
              f"(from {len(sdf):>6} candidates,  "
              f"contexts: {sorted(sdf['context'].unique())})")

    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()


# ── Deduplication ─────────────────────────────────────────────────────────────

def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=["species", "gene_name", "source", "context"])
    after = len(df)
    print(f"  Deduplication: {before} → {after} rows ({before - after} removed)")
    return df


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Normalise, combine and prioritise housekeeping gene databases"
    )
    parser.add_argument("--hk-dir", default="Data/HK")
    parser.add_argument("--out",    default="Data/HK/combined_hk_genes.csv")
    parser.add_argument("--top-n",  type=int, default=50)
    args = parser.parse_args()

    hk_dir = Path(args.hk_dir)

    print("\n── HRT Atlas ────────────────────────────────────────────────────────")
    hrt = parse_hrt_atlas(hk_dir)

    print("\n── PaGenBase ────────────────────────────────────────────────────────")
    pg  = parse_pagenbase(hk_dir)

    print("\n── Rice Expression Database ─────────────────────────────────────────")
    red = parse_red(hk_dir)

    print("\n── Combining & deduplicating ────────────────────────────────────────")
    combined = pd.concat([hrt, pg, red], ignore_index=True)
    combined["gene_name"] = combined["gene_name"].str.strip()
    combined = combined[combined["gene_name"].notna() & (combined["gene_name"] != "")]
    combined = deduplicate(combined)
    combined = combined.sort_values(
        ["species", "source", "context", "gene_name"]).reset_index(drop=True)

    print(f"\n  Full total: {len(combined)} rows across {combined['species'].nunique()} species")

    print(f"\n── Prioritising top {args.top_n} per species ──────────────────────────────────")
    prioritised = prioritise(combined, top_n=args.top_n)

    print("\n── Prioritised summary ──────────────────────────────────────────────")
    print(prioritised.groupby(["species", "source", "context"])
                     .size().reset_index(name="n")
                     .to_string(index=False))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(out_path, index=False)
    print(f"\n✓ Full dataset  → {out_path}")

    out_top = out_path.with_name(out_path.stem + f"_top{args.top_n}.csv")
    prioritised.to_csv(out_top, index=False)
    print(f"✓ Top-{args.top_n} dataset → {out_top}")


if __name__ == "__main__":
    main()