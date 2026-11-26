#!/usr/bin/env python3
"""
enrich_hk_with_ensembl_ids.py
──────────────────────────────
Adds Ensembl gene_id to the combined housekeeping gene CSV by looking up
gene symbols against the pyensembl SQLite databases already present in
Data/pyensembl/.

Match strategy per species:
  - Most species    : gene_name → DB gene_name  (case-insensitive)
  - oryza_sativa    : gene_name → DB gene_id
                      (RED uses RAP-DB IDs like Os03g0708600 = Ensembl gene_id)
  - glycine_max     : LOC<id> → NCBI gene2ensembl crosswalk → Ensembl gene_id
                      (PaGenBase uses NCBI LOC IDs, no gene_name in DB)

Usage:
    python enrich_hk_with_ensembl_ids.py \\
        --input         ../../Data/HK/combined_hk_genes_top50.csv \\
        --output        ../../Data/HK/combined_hk_genes_top50_ensembl.csv \\
        --pyensembl-dir ../../Data/pyensembl \\
        --ncbi-cache    ../../Data/HK/gene2ensembl.gz
"""

import argparse
import gzip
import re
import sqlite3
import urllib.request
import pandas as pd
from pathlib import Path

# ── Species → DB path ─────────────────────────────────────────────────────────
SPECIES_DB = {
    "homo_sapiens":            "GRCh38/ensembl108/Homo_sapiens.GRCh38.108.gtf.db",
    "mus_musculus":            "GRCm39/ensembl108/Mus_musculus.GRCm39.108.gtf.db",
    "rattus_norvegicus":       "mRatBN7.2/ensembl108/Rattus_norvegicus.mRatBN7.2.108.gtf.db",
    "danio_rerio":             "GRCz11/ensembl108/Danio_rerio.GRCz11.108.gtf.db",
    "drosophila_melanogaster": "BDGP6.32/ensembl108/Drosophila_melanogaster.BDGP6.32.108.gtf.db",
    "arabidopsis_thaliana":    "TAIR10/ensembl57/Arabidopsis_thaliana.TAIR10.57.gtf.db",
    "oryza_sativa":            "IRGSP-1.0/ensembl57/Oryza_sativa.IRGSP-1.0.57.gtf.db",
    "caenorhabditis_elegans":  "WBcel235/ensembl108/Caenorhabditis_elegans.WBcel235.108.gtf.db",
    "saccharomyces_cerevisiae":"R64-1-1/ensembl108/Saccharomyces_cerevisiae.R64-1-1.108.gtf.db",
    "xenopus_tropicalis":      "UCB_Xtro_10.0/ensembl108/Xenopus_tropicalis.UCB_Xtro_10.0.108.gtf.db",
    # glycine_max handled separately via NCBI gene2ensembl crosswalk
}

# Species where HK gene_name IS the Ensembl gene_id (match against gene_id col)
MATCH_BY_GENE_ID = {"oryza_sativa"}

# Species handled by NCBI crosswalk (not in SPECIES_DB above)
MATCH_BY_NCBI = {"glycine_max"}
NCBI_TAXON = {"glycine_max": "3847"}
NCBI_URL   = "https://ftp.ncbi.nih.gov/gene/DATA/gene2ensembl.gz"


# ── Lookup builders ───────────────────────────────────────────────────────────

def build_name_lookup(db_path: Path) -> dict:
    """gene_name_lower → first gene_id"""
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql("SELECT gene_id, gene_name FROM gene", conn)
    except Exception as e:
        print(f"    Warning: {db_path.name}: {e}"); return {}
    finally:
        conn.close()
    lookup = {}
    for _, row in df.iterrows():
        name = str(row["gene_name"]).strip()
        if name:
            lookup.setdefault(name.lower(), str(row["gene_id"]).strip())
    return lookup


def build_id_lookup(db_path: Path) -> set:
    """Set of valid gene_ids"""
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql("SELECT gene_id FROM gene", conn)
    except Exception as e:
        print(f"    Warning: {db_path.name}: {e}"); return set()
    finally:
        conn.close()
    return set(df["gene_id"].astype(str).str.strip())


def fetch_ncbi_crosswalk(cache_path: Path, taxon: str) -> dict:
    """
    Download NCBI gene2ensembl.gz (cached) and return
    {ncbi_gene_id: ensembl_gene_id} for the given taxon.
    """
    if not cache_path.exists():
        print(f"  NCBI: downloading gene2ensembl.gz (this may take a minute)...")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(NCBI_URL, cache_path)
        print(f"  NCBI: downloaded ({cache_path.stat().st_size // 1_000_000} MB)")
    else:
        print(f"  NCBI: using cached {cache_path.name}")

    mapping = {}
    with gzip.open(cache_path, "rt") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            if parts[0] == taxon and parts[2] != "-":
                mapping[parts[1]] = parts[2]   # ncbi_id → ensembl_id
    print(f"  NCBI: {len(mapping)} mappings loaded for taxon {taxon}")
    return mapping


# ── Per-gene mapping helpers ──────────────────────────────────────────────────

def map_by_name(gene_name: str, lookup: dict):
    gid = lookup.get(str(gene_name).strip().lower())
    return (gid, "iexact") if gid else (None, "unmapped")


def map_by_id(gene_name: str, valid_ids: set):
    gid = str(gene_name).strip()
    return (gid, "direct") if gid in valid_ids else (None, "unmapped")


def map_by_ncbi(gene_name: str, crosswalk: dict):
    name = str(gene_name).strip()
    # LOC100306580 → "100306580"
    m = re.fullmatch(r"LOC(\d+)", name, re.IGNORECASE)
    ncbi_id = m.group(1) if m else (name if name.isdigit() else None)
    if ncbi_id:
        gid = crosswalk.get(ncbi_id)
        if gid:
            return gid, "ncbi_crosswalk"
    return None, "unmapped"


# ── Main enrichment ───────────────────────────────────────────────────────────

def enrich(input_csv: Path, output_csv: Path,
           pyensembl_dir: Path, ncbi_cache: Path):

    df = pd.read_csv(input_csv)
    print(f"  Loaded {len(df)} rows from {input_csv.name}\n")

    df["gene_id"]    = None
    df["match_type"] = "unmapped"

    total_mapped = total_rows = 0

    # ── Pyensembl-based species ───────────────────────────────────────────────
    for species in sorted(df["species"].unique()):
        if species in MATCH_BY_NCBI:
            continue   # handled separately below

        rel_path = SPECIES_DB.get(species)
        if not rel_path:
            n = (df["species"] == species).sum()
            print(f"  {species:<40} → no DB configured [{n} genes]")
            continue

        db_path = pyensembl_dir / rel_path
        if not db_path.exists():
            print(f"  {species:<40} → DB not found: {db_path}")
            continue

        mask = df["species"] == species
        n    = mask.sum()
        total_rows += n
        mapped = 0

        if species in MATCH_BY_GENE_ID:
            valid_ids = build_id_lookup(db_path)
            fn = lambda name: map_by_id(name, valid_ids)
        else:
            lookup = build_name_lookup(db_path)
            fn = lambda name: map_by_name(name, lookup)

        for idx in df[mask].index:
            gid, mtype = fn(df.at[idx, "gene_name"])
            df.at[idx, "gene_id"]    = gid
            df.at[idx, "match_type"] = mtype
            if gid:
                mapped += 1

        total_mapped += mapped
        pct = 100 * mapped / n if n else 0
        print(f"  {species:<40} {mapped:>4}/{n:<4} mapped  ({pct:.0f}%)")

    # ── NCBI crosswalk species ────────────────────────────────────────────────
    for species in sorted(MATCH_BY_NCBI):
        if species not in df["species"].values:
            continue
        taxon     = NCBI_TAXON[species]
        crosswalk = fetch_ncbi_crosswalk(ncbi_cache, taxon)
        mask = df["species"] == species
        n    = mask.sum()
        total_rows  += n
        mapped = 0
        for idx in df[mask].index:
            gid, mtype = map_by_ncbi(df.at[idx, "gene_name"], crosswalk)
            df.at[idx, "gene_id"]    = gid
            df.at[idx, "match_type"] = mtype
            if gid:
                mapped += 1
        total_mapped += mapped
        pct = 100 * mapped / n if n else 0
        print(f"  {species:<40} {mapped:>4}/{n:<4} mapped  ({pct:.0f}%)  [NCBI crosswalk]")

    # ── Summary ───────────────────────────────────────────────────────────────
    if total_rows:
        print(f"\n  Overall: {total_mapped}/{total_rows} "
              f"({100*total_mapped/total_rows:.1f}%)")

    unmapped = df[df["match_type"] == "unmapped"][["species", "gene_name"]]
    if len(unmapped):
        print(f"\n  Unmapped ({len(unmapped)}) — kept with gene_id=None:")
        print(unmapped.groupby("species").size().to_string())

    # Reorder columns
    front = ["species", "gene_name", "gene_id", "match_type",
             "source", "source_url", "context", "rank", "dpm", "avg_expression"]
    existing = [c for c in front if c in df.columns]
    rest     = [c for c in df.columns if c not in existing]
    df = df[existing + rest]

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"\n✓ Written to {output_csv}")
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Add Ensembl gene_id to housekeeping gene CSV"
    )
    parser.add_argument("--input",          default="../../Data/HK/combined_hk_genes_top50.csv")
    parser.add_argument("--output",         default="../../Data/HK/combined_hk_genes_top50_ensembl.csv")
    parser.add_argument("--pyensembl-dir",  default="../../Data/pyensembl")
    parser.add_argument("--ncbi-cache",     default="../../Data/HK/gene2ensembl.gz",
                        help="Local cache path for NCBI gene2ensembl.gz (downloaded once)")
    args = parser.parse_args()

    print("\n── Enriching HK genes with Ensembl IDs ──────────────────────────────")
    enrich(
        input_csv     = Path(args.input),
        output_csv    = Path(args.output),
        pyensembl_dir = Path(args.pyensembl_dir),
        ncbi_cache    = Path(args.ncbi_cache),
    )


if __name__ == "__main__":
    main()
