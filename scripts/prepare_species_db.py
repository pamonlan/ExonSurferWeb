#!/usr/bin/env python3
"""
prepare_species_db.py
─────────────────────
Downloads RNA + DNA FASTAs from Ensembl/EnsemblGenomes, builds BLAST databases,
generates the transcript→gene table.txt, downloads per-chromosome sequences, and
zips everything ready for Zenodo upload.

Two zip files are produced per species:
  • {prefix}.zip       – BLAST DBs (rna + dna) + table.txt  → BLAST_DB_LINKS
  • {prefix}_seqs.zip  – per-chromosome .txt files           → CHROM_LINKS

Chromosome files are AUTO-DISCOVERED by scraping the Ensembl FTP HTML index,
so no hardcoded chromosome lists are needed and 404s are avoided even when
organelles or scaffold files follow non-standard naming conventions.

Usage:
    python prepare_species_db.py homo_sapiens
    python prepare_species_db.py --list               # show all species
    python prepare_species_db.py --all                # build all species
    python prepare_species_db.py tomato --no-blast    # only seqs zip
    python prepare_species_db.py tomato --no-seqs     # only blast zip
    python prepare_species_db.py --print-constants    # print ExonSurfer dicts

Requirements:
    pip install pyensembl
    makeblastdb must be in PATH  (NCBI BLAST+)
"""

import argparse
import gzip
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


# ── FTP base paths ────────────────────────────────────────────────────────────
_E108  = "https://ftp.ensembl.org/pub/release-108/fasta"
_EG55M = "https://ftp.ensemblgenomes.ebi.ac.uk/pub/metazoa/release-55/fasta"
_EG55F = "https://ftp.ensemblgenomes.ebi.ac.uk/pub/fungi/release-55/fasta"
_EP57  = "https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-57/fasta"


# ── Species configuration ─────────────────────────────────────────────────────
#
# Required for every species:
#   prefix            – short name used in output filenames  (e.g. "human")
#   ensembl_release   – Ensembl/EnsemblGenomes release number (None for wormbase)
#   db_type           – "ensembl" | "ensemblgenomes" | "wormbase"
#   assembly          – assembly string appearing in FTP filenames
#   cdna_url          – cDNA .fa.gz  → BLAST RNA DB + table.txt
#   dna_url           – genome .fa.gz → BLAST DNA DB
#   pyensembl_species – pyensembl species name, or None → parse FASTA headers
#
# Per-chromosome seqs zip (auto-discovery):
#   chr_ftp_dir    – URL of the Ensembl FTP dna/ directory to scrape.
#                    Set to None for scaffold-only genomes.
#   chr_mask_token – token(s) that a filename must contain to be collected.
#                    String or list of strings, e.g.:
#                      "dna_rm.chromosome"               most vertebrates / plants
#                      "dna_rm.primary_assembly"         Xenopus, some fish
#                      ["dna_rm.chromosome",
#                       "dna_rm.nonchromosomal"]         when organelles are separate
#   chr_file_pattern – output .txt filename template.  "{}" is replaced with the
#                      chromosome id extracted from the .fa.gz filename.
#
# Optional:
#   division       – (ensemblgenomes only) "plants" | "metazoa" | "fungi"
#   chr_extra_urls – list of (url, output_filename) for scaffold genomes or
#                    files outside the standard FTP directory.

SPECIES_CONFIG = {

    # ── VERTEBRATES (Ensembl 108) ─────────────────────────────────────────────

    # pyensembl_species notes
    # ─────────────────────
    # pyensembl only knows a fixed list of species hardcoded in its source.
    # When a species IS in that list, pyensembl gives us clean gene symbols
    # directly from its cached SQLite DB (faster and more reliable than parsing
    # FASTA headers).  When a species is NOT in the list we fall back to parsing
    # the "gene_symbol:XXX" field from each cDNA FASTA header – that information
    # is always present in Ensembl/EnsemblGenomes FASTA files so it works fine,
    # just with slightly less metadata resolution.
    #
    # Species NOT supported by pyensembl (verified at runtime):
    #   xenopus_tropicalis  – not in pyensembl species registry
    #   zea_mays            – not in pyensembl species registry
    #   solanum_lycopersicum– not in pyensembl species registry
    #   glycine_max         – not in pyensembl species registry
    #   litomosoides_sigmodontis – WormBase, not Ensembl

    "homo_sapiens": {
        "prefix": "human",
        "ensembl_release": 108, "db_type": "ensembl", "assembly": "GRCh38",
        "cdna_url": f"{_E108}/homo_sapiens/cdna/Homo_sapiens.GRCh38.cdna.all.fa.gz",
        "dna_url":  f"{_E108}/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz",
        "pyensembl_species": "homo_sapiens",       # ✓ pyensembl supported
        "chr_ftp_dir":    f"{_E108}/homo_sapiens/dna/",
        "chr_mask_token": "dna_rm.chromosome",
        "chr_file_pattern": "human{}.txt",
    },

    "homo_sapiens_masked": {
        # Soft-masked (dna_sm) seqs for off-target specificity checks
        "prefix": "human_masked",
        "ensembl_release": 108, "db_type": "ensembl", "assembly": "GRCh38",
        "cdna_url": f"{_E108}/homo_sapiens/cdna/Homo_sapiens.GRCh38.cdna.all.fa.gz",
        "dna_url":  f"{_E108}/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz",
        "pyensembl_species": "homo_sapiens",       # ✓ pyensembl supported
        "chr_ftp_dir":    f"{_E108}/homo_sapiens/dna/",
        "chr_mask_token": "dna_sm.chromosome",
        "chr_file_pattern": "human{}_masked.txt",
    },

    "mus_musculus": {
        "prefix": "mouse",
        "ensembl_release": 108, "db_type": "ensembl", "assembly": "GRCm39",
        "cdna_url": f"{_E108}/mus_musculus/cdna/Mus_musculus.GRCm39.cdna.all.fa.gz",
        "dna_url":  f"{_E108}/mus_musculus/dna/Mus_musculus.GRCm39.dna.primary_assembly.fa.gz",
        "pyensembl_species": "mus_musculus",       # ✓ pyensembl supported
        "chr_ftp_dir":    f"{_E108}/mus_musculus/dna/",
        "chr_mask_token": "dna_rm.chromosome",
        "chr_file_pattern": "mouse{}.txt",
    },

    "rattus_norvegicus": {
        "prefix": "rat",
        "ensembl_release": 108, "db_type": "ensembl", "assembly": "mRatBN7.2",
        "cdna_url": f"{_E108}/rattus_norvegicus/cdna/Rattus_norvegicus.mRatBN7.2.cdna.all.fa.gz",
        "dna_url":  f"{_E108}/rattus_norvegicus/dna/Rattus_norvegicus.mRatBN7.2.dna.toplevel.fa.gz",
        "pyensembl_species": "rattus_norvegicus",  # ✓ pyensembl supported
        "chr_ftp_dir":    f"{_E108}/rattus_norvegicus/dna/",
        "chr_mask_token": "dna_rm.chromosome",
        "chr_file_pattern": "rat{}.txt",
    },

    "danio_rerio": {
        "prefix": "zebrafish",
        "ensembl_release": 108, "db_type": "ensembl", "assembly": "GRCz11",
        "cdna_url": f"{_E108}/danio_rerio/cdna/Danio_rerio.GRCz11.cdna.all.fa.gz",
        "dna_url":  f"{_E108}/danio_rerio/dna/Danio_rerio.GRCz11.dna.primary_assembly.fa.gz",
        "pyensembl_species": "None",        # ✓ pyensembl supported
        "chr_ftp_dir":    f"{_E108}/danio_rerio/dna/",
        "chr_mask_token": "dna_rm.chromosome",
        "chr_file_pattern": "daniorerio_{}.txt",
    },

    "xenopus_tropicalis": {
        "prefix": "frog",
        "ensembl_release": 108, "db_type": "ensembl", "assembly": "UCB_Xtro_10.0",
        "cdna_url": f"{_E108}/xenopus_tropicalis/cdna/Xenopus_tropicalis.UCB_Xtro_10.0.cdna.all.fa.gz",
        "dna_url":  f"{_E108}/xenopus_tropicalis/dna/Xenopus_tropicalis.UCB_Xtro_10.0.dna.toplevel.fa.gz",
        "pyensembl_species": None,                 # ✗ not in pyensembl → FASTA header fallback
        # Xenopus uses "primary_assembly" instead of "chromosome" in filenames
        "chr_ftp_dir":    f"{_E108}/xenopus_tropicalis/dna/",
        "chr_mask_token": "dna_rm.primary_assembly",
        "chr_file_pattern": "xenopus_tropicalis_{}.txt",
    },

    "gallus_gallus": {
        "prefix": "chicken",
        "ensembl_release": 108, "db_type": "ensembl",
        "assembly": "bGalGal1.mat.broiler.GRCg7b",
        "cdna_url": f"{_E108}/gallus_gallus/cdna/Gallus_gallus.bGalGal1.mat.broiler.GRCg7b.cdna.all.fa.gz",
        "dna_url":  f"{_E108}/gallus_gallus/dna/Gallus_gallus.bGalGal1.mat.broiler.GRCg7b.dna.toplevel.fa.gz",
        "pyensembl_species": None,      # ✓ pyensembl supported
        "chr_ftp_dir":    f"{_E108}/gallus_gallus/dna/",
        "chr_mask_token": "dna_rm.chromosome",
        "chr_file_pattern": "gallus_gallus_{}.txt",
    },

    "sus_scrofa": {
        "prefix": "pig",
        "ensembl_release": 108, "db_type": "ensembl", "assembly": "Sscrofa11.1",
        "cdna_url": f"{_E108}/sus_scrofa/cdna/Sus_scrofa.Sscrofa11.1.cdna.all.fa.gz",
        "dna_url":  f"{_E108}/sus_scrofa/dna/Sus_scrofa.Sscrofa11.1.dna.toplevel.fa.gz",
        "pyensembl_species": None,         # ✓ pyensembl supported
        "chr_ftp_dir":    f"{_E108}/sus_scrofa/dna/",
        "chr_mask_token": "dna_rm.chromosome",
        "chr_file_pattern": "sus_scrofa_{}.txt",
    },

    "macaca_mulatta": {
        "prefix": "macaque",
        "ensembl_release": 108, "db_type": "ensembl", "assembly": "Mmul_10",
        "cdna_url": f"{_E108}/macaca_mulatta/cdna/Macaca_mulatta.Mmul_10.cdna.all.fa.gz",
        "dna_url":  f"{_E108}/macaca_mulatta/dna/Macaca_mulatta.Mmul_10.dna.toplevel.fa.gz",
        "pyensembl_species": None,     # ✓ pyensembl supported
        "chr_ftp_dir":    f"{_E108}/macaca_mulatta/dna/",
        "chr_mask_token": "dna_rm.chromosome",
        "chr_file_pattern": "macaca_mulatta_{}.txt",
    },

    # ── METAZOA / FUNGI (EnsemblGenomes 55) ──────────────────────────────────

    "drosophila_melanogaster": {
        "prefix": "fruitfly",
        "ensembl_release": 108, "db_type": "ensemblgenomes",
        "division": "metazoa", "assembly": "BDGP6.32",
        "cdna_url": f"{_EG55M}/drosophila_melanogaster/cdna/Drosophila_melanogaster.BDGP6.32.cdna.all.fa.gz",
        "dna_url":  f"{_EG55M}/drosophila_melanogaster/dna/Drosophila_melanogaster.BDGP6.32.dna.toplevel.fa.gz",
        "pyensembl_species": None,  # ✓ pyensembl supported
        # chromosome arms (2L/2R/3L/3R/4/X/Y) + nonchromosomal = mitochondrion
        "chr_ftp_dir":    f"{_EG55M}/drosophila_melanogaster/dna/",
        "chr_mask_token": ["dna_rm.chromosome", "dna_rm.nonchromosomal"],
        "chr_file_pattern": "drosophila_melanogaster_{}.txt",
    },

    "caenorhabditis_elegans": {
        "prefix": "celegans",
        "ensembl_release": 108, "db_type": "ensemblgenomes",
        "division": "metazoa", "assembly": "WBcel235",
        "cdna_url": f"{_EG55M}/caenorhabditis_elegans/cdna/Caenorhabditis_elegans.WBcel235.cdna.all.fa.gz",
        "dna_url":  f"{_EG55M}/caenorhabditis_elegans/dna/Caenorhabditis_elegans.WBcel235.dna.toplevel.fa.gz",
        "pyensembl_species": None,   # ✓ pyensembl supported
        "chr_ftp_dir":    f"{_EG55M}/caenorhabditis_elegans/dna/",
        "chr_mask_token": "dna_rm.chromosome",
        "chr_file_pattern": "caenorhabditis_elegans_{}.txt",
    },

    "saccharomyces_cerevisiae": {
        "prefix": "yeast",
        "ensembl_release": 108, "db_type": "ensemblgenomes",
        "division": "fungi", "assembly": "R64-1-1",
        "cdna_url": f"{_EG55F}/saccharomyces_cerevisiae/cdna/Saccharomyces_cerevisiae.R64-1-1.cdna.all.fa.gz",
        "dna_url":  f"{_EG55F}/saccharomyces_cerevisiae/dna/Saccharomyces_cerevisiae.R64-1-1.dna.toplevel.fa.gz",
        "pyensembl_species": None,  # ✓ pyensembl supported
        "chr_ftp_dir":    f"{_EG55F}/saccharomyces_cerevisiae/dna/",
        "chr_mask_token": "dna_rm.chromosome",
        "chr_file_pattern": "saccharomyces_cerevisiae_{}.txt",
    },

    # ── PLANTS (EnsemblGenomes Plants 57) ─────────────────────────────────────

    "arabidopsis_thaliana": {
        "prefix": "arabidopsis",
        "ensembl_release": 57, "db_type": "ensemblgenomes",
        "division": "plants", "assembly": "TAIR10",
        "cdna_url": f"{_EP57}/arabidopsis_thaliana/cdna/Arabidopsis_thaliana.TAIR10.cdna.all.fa.gz",
        "dna_url":  f"{_EP57}/arabidopsis_thaliana/dna/Arabidopsis_thaliana.TAIR10.dna.toplevel.fa.gz",
        "pyensembl_species": None,     # ✓ pyensembl supported
        # Chromosomes 1-5 + Mt + Pt are all dna_rm.chromosome files
        "chr_ftp_dir":    f"{_EP57}/arabidopsis_thaliana/dna/",
        "chr_mask_token": "dna_rm.chromosome",
        "chr_file_pattern": "arabidopsis_thaliana_{}.txt",
    },

    "oryza_sativa": {
        "prefix": "rice",
        "ensembl_release": 57, "db_type": "ensemblgenomes",
        "division": "plants", "assembly": "IRGSP-1.0",
        "cdna_url": f"{_EP57}/oryza_sativa/cdna/Oryza_sativa.IRGSP-1.0.cdna.all.fa.gz",
        "dna_url":  f"{_EP57}/oryza_sativa/dna/Oryza_sativa.IRGSP-1.0.dna.toplevel.fa.gz",
        "pyensembl_species": None,             # ✓ pyensembl supported
        "chr_ftp_dir":    f"{_EP57}/oryza_sativa/dna/",
        "chr_mask_token": "dna_rm.chromosome",
        "chr_file_pattern": "oryza_sativa_{}.txt",
    },

    "zea_mays": {
        "prefix": "maize",
        "ensembl_release": 57, "db_type": "ensemblgenomes",
        "division": "plants", "assembly": "Zm-B73-REFERENCE-NAM-5.0",
        "cdna_url": f"{_EP57}/zea_mays/cdna/Zea_mays.Zm-B73-REFERENCE-NAM-5.0.cdna.all.fa.gz",
        "dna_url":  f"{_EP57}/zea_mays/dna/Zea_mays.Zm-B73-REFERENCE-NAM-5.0.dna.toplevel.fa.gz",
        "pyensembl_species": None,                       # ✗ not in pyensembl → FASTA header fallback
        "chr_ftp_dir":    f"{_EP57}/zea_mays/dna/",
        "chr_mask_token": "dna_rm.chromosome",
        "chr_file_pattern": "zea_mays_{}.txt",
    },

    "solanum_lycopersicum": {
        "prefix": "tomato",
        "ensembl_release": 57, "db_type": "ensemblgenomes",
        "division": "plants",
        # SL3.0 used – SL4.0 not on Ensembl Plants rel-57
        "assembly": "SL3.0",
        "cdna_url": f"{_EP57}/solanum_lycopersicum/cdna/Solanum_lycopersicum.SL3.0.cdna.all.fa.gz",
        "dna_url":  f"{_EP57}/solanum_lycopersicum/dna/Solanum_lycopersicum.SL3.0.dna.toplevel.fa.gz",
        "pyensembl_species": None,                       # ✗ not in pyensembl → FASTA header fallback
        # Tomato has no separate Mt/Pt chromosome files;
        # organelles are inside nonchromosomal.fa.gz
        "chr_ftp_dir":    f"{_EP57}/solanum_lycopersicum/dna/",
        "chr_mask_token": ["dna_rm.chromosome", "dna_rm.nonchromosomal"],
        "chr_file_pattern": "solanum_lycopersicum_{}.txt",
    },

    "glycine_max": {
        "prefix": "soybean",
        "ensembl_release": 57, "db_type": "ensemblgenomes",
        "division": "plants", "assembly": "Glycine_max_v2.1",
        "cdna_url": f"{_EP57}/glycine_max/cdna/Glycine_max.Glycine_max_v2.1.cdna.all.fa.gz",
        "dna_url":  f"{_EP57}/glycine_max/dna/Glycine_max.Glycine_max_v2.1.dna.toplevel.fa.gz",
        "pyensembl_species": None,                       # ✗ not in pyensembl → FASTA header fallback
        "chr_ftp_dir":    f"{_EP57}/glycine_max/dna/",
        "chr_mask_token": ["dna_rm.chromosome", "dna_rm.nonchromosomal"],
        "chr_file_pattern": "glycine_max_{}.txt",
    },

    # ── NEMATODE PARASITES (WormBase ParaSite) ────────────────────────────────

    "litomosoides_sigmodontis": {
        "prefix": "l_sigmodontis",
        "ensembl_release": None, "db_type": "wormbase", "assembly": "nLs.2.1",
        "cdna_url": "https://ftp.ebi.ac.uk/pub/databases/wormbase/parasite/releases/WBPS19/species/litomosoides_sigmodontis/PRJEB3075/litomosoides_sigmodontis.PRJEB3075.WBPS19.mRNA_transcripts.fa.gz",
        "dna_url":  "https://ftp.ebi.ac.uk/pub/databases/wormbase/parasite/releases/WBPS19/species/litomosoides_sigmodontis/PRJEB3075/litomosoides_sigmodontis.PRJEB3075.WBPS19.genomic.fa.gz",
        "pyensembl_species": None,
        # Scaffold-based: no FTP chromosome directory to scrape
        "chr_ftp_dir":    None,
        "chr_mask_token": None,
        "chr_file_pattern": "L_sigmodontis_nLs.2.1.{}.txt",
        "chr_extra_urls": [
            (
                "https://ftp.ebi.ac.uk/pub/databases/wormbase/parasite/releases/WBPS19/species/litomosoides_sigmodontis/PRJEB3075/litomosoides_sigmodontis.PRJEB3075.WBPS19.genomic.fa.gz",
                "L_sigmodontis_nLs.2.1.scaf00001.txt",
            )
        ],
    },
}


# ── FTP auto-discovery ────────────────────────────────────────────────────────

def _scrape_ftp_dir(dir_url: str) -> list:
    """
    Fetch an Ensembl HTTP/FTP index page and return all .fa.gz filenames listed.
    """
    try:
        with urllib.request.urlopen(dir_url, timeout=30) as resp:
            html_text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cannot reach FTP index {dir_url}: {e}")
    # Ensembl index pages use:  href="Filename.fa.gz"
    return re.findall(r'href="([^"/]+\.fa\.gz)"', html_text)


def discover_chr_files(cfg: dict) -> list:
    """
    Return a list of (remote_url, local_txt_name) for all chromosome files.

    Files are found by scraping chr_ftp_dir and keeping those whose filename
    contains one of the chr_mask_token strings.  The chromosome id is extracted
    as the suffix after the token in the filename stem.

    chr_extra_urls entries are appended unconditionally.
    """
    results = []
    ftp_dir      = cfg.get("chr_ftp_dir")
    mask_tokens  = cfg.get("chr_mask_token")
    file_pattern = cfg.get("chr_file_pattern", "{}.txt")

    if ftp_dir and mask_tokens:
        tokens = [mask_tokens] if isinstance(mask_tokens, str) else mask_tokens
        all_fa_gz = _scrape_ftp_dir(ftp_dir)

        for token in tokens:
            for fname in all_fa_gz:
                if token not in fname:
                    continue
                remote_url = ftp_dir.rstrip("/") + "/" + fname
                # Extract chromosome id from filename
                # e.g. "Solanum_lycopersicum.SL3.0.dna_rm.chromosome.1.fa.gz"
                #   token = "dna_rm.chromosome"  → after = ".1" → id = "1"
                # e.g. "Solanum_lycopersicum.SL3.0.dna_rm.nonchromosomal.fa.gz"
                #   token = "dna_rm.nonchromosomal" → after = "" → id = "nonchromosomal"
                stem      = fname[: -len(".fa.gz")]
                after     = stem.split(token, 1)[1].lstrip(".")
                chrom_id  = after if after else token.split(".")[-1]
                local_name = file_pattern.replace("{}", chrom_id)
                results.append((remote_url, local_name))

    for url, local_name in cfg.get("chr_extra_urls", []):
        results.append((url, local_name))

    return results


# ── Low-level helpers ─────────────────────────────────────────────────────────

def log(msg: str):
    print(f"  {msg}", flush=True)


def run(cmd: list, cwd: Path = None):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(f"Command failed: {' '.join(str(c) for c in cmd)}")
    return result.stdout


def download(url: str, dest: Path):
    if dest.exists():
        log(f"already downloaded: {dest.name}")
        return
    log(f"downloading {Path(url).name} ...")
    urllib.request.urlretrieve(url, dest)


def decompress_gz(gz_path: Path, out_path: Path):
    if out_path.exists():
        log(f"already decompressed: {out_path.name}")
        return
    log(f"decompressing {gz_path.name} ...")
    with gzip.open(gz_path, "rb") as f_in, open(out_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)


def fasta_gz_to_txt(gz_path: Path, txt_path: Path):
    """Decompress a chromosome .fa.gz → plain .txt (FASTA)."""
    if txt_path.exists():
        log(f"already converted: {txt_path.name}")
        return
    log(f"converting {gz_path.name} → {txt_path.name} ...")
    with gzip.open(gz_path, "rt") as f_in, open(txt_path, "w") as f_out:
        shutil.copyfileobj(f_in, f_out)


def build_blast_db(fasta: Path, db_name: Path, db_type: str = "nucl"):
    if db_name.with_suffix(".nhr").exists():
        log(f"BLAST DB already built: {db_name.name}")
        return
    log(f"building BLAST DB: {db_name.name} ...")
    run(["makeblastdb", "-dbtype", db_type, "-in", str(fasta), "-out", str(db_name)])


def build_table(cdna_fasta: Path, table_out: Path, pyensembl_species, release):
    """Build transcript_id → gene_symbol table.txt."""
    if table_out.exists():
        log("table.txt already built")
        return
    log("building table.txt ...")
    data = None
    if pyensembl_species:
        try:
            from pyensembl import EnsemblRelease
            data = EnsemblRelease(species=pyensembl_species, release=release)
            log(f"using pyensembl ({pyensembl_species}, release {release})")
        except Exception as e:
            log(f"pyensembl unavailable ({e}), falling back to FASTA header parsing")

    with open(cdna_fasta, "r") as f_in, open(table_out, "w") as f_out:
        for line in f_in:
            if not line.startswith(">"):
                continue
            parts  = line[1:].split()
            t_id   = parts[0]
            symbol = None
            if data:
                try:
                    symbol = data.transcript_by_id(t_id.split(".")[0]).gene_name
                except Exception:
                    pass
            if symbol is None:
                gene_symbol = None
                gene_id = None
                for p in parts:
                    if p.startswith("gene_symbol:"):
                        gene_symbol = p.split(":", 1)[1]
                    elif p.startswith("gene:"):
                        gene_id = p.split(":", 1)[1]
                symbol = gene_symbol if gene_symbol is not None else gene_id

            if symbol is None:
                symbol = t_id
            f_out.write(f"{t_id}\t{symbol}\n")


def build_blast_zip(db_dir: Path, out_zip: Path):
    if out_zip.exists():
        log(f"blast zip already exists: {out_zip.name}"); return
    files = sorted(db_dir.iterdir())
    if not files:
        log("WARNING: BLAST db directory empty – skipping zip"); return
    log(f"zipping BLAST DB ({len(files)} files) → {out_zip.name} ...")
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, arcname=f.name)   # flat – no subfolder
    log(f"done → {out_zip}")


def build_seqs_zip(seqs_dir: Path, out_zip: Path):
    txt_files = sorted(seqs_dir.glob("*.txt"))
    if not txt_files:
        log("WARNING: no .txt files in seqs dir – skipping zip"); return
    if out_zip.exists():
        log(f"seqs zip already exists: {out_zip.name}"); return
    log(f"zipping {len(txt_files)} chromosome files → {out_zip.name} ...")
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in txt_files:
            zf.write(f, arcname=f.name)   # flat – no subfolder
    log(f"done → {out_zip}")


# ── Main pipeline ─────────────────────────────────────────────────────────────

def prepare_species(
    species_key: str,
    base_dir: Path,
    skip_blast: bool = False,
    skip_seqs:  bool = False,
    skip_zip:   bool = False,
):
    cfg     = SPECIES_CONFIG[species_key]
    prefix  = cfg["prefix"]
    release = cfg.get("ensembl_release")

    raw_dir  = base_dir / "raw"  / species_key
    db_dir   = base_dir / "db"   / species_key
    seqs_dir = base_dir / "seqs" / species_key
    for d in (raw_dir, db_dir, seqs_dir):
        d.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Species  : {species_key}")
    print(f"  Prefix   : {prefix}")
    print(f"  Assembly : {cfg['assembly']}")
    if release:
        print(f"  Release  : {release}")
    print(f"{'='*60}")

    # ── A. BLAST pipeline ────────────────────────────────────────────────────
    if not skip_blast:
        print("\n[A1] Download cDNA + genomic FASTAs")
        cdna_gz = raw_dir / Path(cfg["cdna_url"]).name
        dna_gz  = raw_dir / Path(cfg["dna_url"]).name
        download(cfg["cdna_url"], cdna_gz)
        download(cfg["dna_url"],  dna_gz)

        print("\n[A2] Decompress FASTAs")
        cdna_fa = raw_dir / cdna_gz.stem
        dna_fa  = raw_dir / dna_gz.stem
        decompress_gz(cdna_gz, cdna_fa)
        decompress_gz(dna_gz,  dna_fa)

        print("\n[A3] Build BLAST databases")
        build_blast_db(cdna_fa, db_dir / f"{prefix}.rna.fna")
        build_blast_db(dna_fa,  db_dir / f"{prefix}.dna.fna")

        print("\n[A4] Build table.txt")
        build_table(cdna_fa, db_dir / "table.txt",
                    cfg.get("pyensembl_species"), release)

        if not skip_zip:
            print(f"\n[A5] Package BLAST zip")
            build_blast_zip(db_dir, base_dir / f"{prefix}.zip")

    # ── B. Per-chromosome sequences pipeline ─────────────────────────────────
    if not skip_seqs:
        print(f"\n[B1] Discover chromosome files from FTP index")
        chr_pairs = discover_chr_files(cfg)
        if not chr_pairs:
            print("  WARNING: no chromosome files found – seqs zip will be empty")
        else:
            print(f"  found {len(chr_pairs)} file(s):")
            for url, name in chr_pairs:
                print(f"    {name:<45}  ←  .../{url.split('/')[-1]}")

        print(f"\n[B2] Download chromosome FASTAs")
        for url, _name in chr_pairs:
            download(url, raw_dir / Path(url).name)

        print(f"\n[B3] Convert to .txt")
        for url, txt_name in chr_pairs:
            fasta_gz_to_txt(raw_dir / Path(url).name, seqs_dir / txt_name)

        if not skip_zip:
            print(f"\n[B4] Package seqs zip")
            build_seqs_zip(seqs_dir, base_dir / f"{prefix}_seqs.zip")

    print(f"\n✓  {species_key} done")
    if not skip_zip:
        print(f"   → Upload these to Zenodo:")
        if not skip_blast:
            print(f"       {base_dir / (prefix + '.zip')}")
        if not skip_seqs:
            print(f"       {base_dir / (prefix + '_seqs.zip')}")
    print()


# ── Print ExonSurfer constants ────────────────────────────────────────────────

def print_exonsurfer_constants():
    keys = list(SPECIES_CONFIG.keys())

    print("BLAST_DB_LINKS = {")
    for k in keys:
        p = SPECIES_CONFIG[k]["prefix"]
        print(f'    "{k}": "",  # upload {p}.zip to Zenodo then paste URL')
    print("}\n")

    print("BLAST_DB_NAMES = {")
    for k in keys:
        p = SPECIES_CONFIG[k]["prefix"]
        print(f'    "{k}": "{p}.rna.fna",')
    print("}\n")

    print("BLAST_GENOMIC_DB_NAMES = {")
    for k in keys:
        p = SPECIES_CONFIG[k]["prefix"]
        print(f'    "{k}": "{p}.dna.fna",')
    print("}\n")

    print("CHROM_LINKS = {")
    for k in keys:
        p = SPECIES_CONFIG[k]["prefix"]
        print(f'    "{k}": "",  # upload {p}_seqs.zip to Zenodo then paste URL')
    print("}\n")

    # FIRST_CHR hint – for scaffold genomes use the known extra filename
    print("FIRST_CHR = {")
    for k in keys:
        cfg    = SPECIES_CONFIG[k]
        extras = cfg.get("chr_extra_urls", [])
        if extras:
            first = extras[0][1]
        else:
            first = cfg.get("chr_file_pattern", "{}.txt")
        print(f'    "{k}": "{first}",  # first file in {cfg["prefix"]}_seqs.zip')
    print("}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Prepare ExonSurfer BLAST databases and chromosome sequences",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python prepare_species_db.py arabidopsis_thaliana
  python prepare_species_db.py solanum_lycopersicum --no-blast
  python prepare_species_db.py --all --outdir /data/exonsurfer_dbs
  python prepare_species_db.py --print-constants
""",
    )
    parser.add_argument("species", nargs="?",
                        help="Species key or prefix shorthand (see --list)")
    parser.add_argument("--list",   action="store_true", help="List all configured species")
    parser.add_argument("--all",    action="store_true", help="Build all species")
    parser.add_argument("--outdir", default=".", metavar="DIR",
                        help="Base output directory (default: current dir)")
    parser.add_argument("--no-blast", action="store_true",
                        help="Skip BLAST DB build and blast zip")
    parser.add_argument("--no-seqs",  action="store_true",
                        help="Skip chromosome seqs download and seqs zip")
    parser.add_argument("--no-zip",   action="store_true",
                        help="Build DBs/seqs but skip zip creation")
    parser.add_argument("--print-constants", action="store_true",
                        help="Print ExonSurfer constant dicts ready to paste")
    args = parser.parse_args()

    if args.print_constants:
        print_exonsurfer_constants(); return

    if args.list:
        print("\nConfigured species:\n")
        for k, v in SPECIES_CONFIG.items():
            print(f"  {k:<35} prefix={v['prefix']:<15} assembly={v['assembly']}")
        print(); return

    base_dir = Path(args.outdir).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    if args.all:
        species_list = list(SPECIES_CONFIG.keys())
    else:
        if not args.species:
            parser.print_help(); sys.exit(1)
        key = args.species
        if key not in SPECIES_CONFIG:
            # accept prefix shorthand  e.g. "tomato" → "solanum_lycopersicum"
            matches = [k for k, v in SPECIES_CONFIG.items() if v["prefix"] == key]
            if len(matches) == 1:
                key = matches[0]
            else:
                print(f"\nUnknown species or prefix: '{args.species}'")
                print("Run with --list to see available options.\n")
                sys.exit(1)
        species_list = [key]

    for sp in species_list:
        prepare_species(sp, base_dir,
                        skip_blast=args.no_blast,
                        skip_seqs=args.no_seqs,
                        skip_zip=args.no_zip)


if __name__ == "__main__":
    main()