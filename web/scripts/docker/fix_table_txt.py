#!/usr/bin/env python3
"""
Regenerate table.txt (transcript_id -> gene_symbol) for species whose
Zenodo-bundled table.txt was built with a gene_symbol/gene tag-priority bug
in prepare_species_db.py's build_table(): it stopped at whichever of
"gene_symbol:"/"gene:" appeared first in FASTA header order, and Ensembl
headers always list "gene:" (stable ID) before "gene_symbol:" (real symbol)
- so it always grabbed the stable ID instead of the symbol.

Uses the cDNA FASTA pyensembl already downloaded via `pyensembl install`
earlier in entrypoint.sh - no extra download needed.
"""
import gzip
import os
import sys

PYENSEMBL_CACHE = "/home/app/web/Data/pyensembl"
BLASTDB_DIR = "/home/app/web/Data/db"

# species_key -> (assembly, release) - must match species_config.py
SPECIES_PATHS = {
    "caenorhabditis_elegans": ("WBcel235", 108),
    "drosophila_melanogaster": ("BDGP6.32", 108),
    "saccharomyces_cerevisiae": ("R64-1-1", 108),
    "xenopus_tropicalis": ("UCB_Xtro_10.0", 108),
    "oryza_sativa": ("IRGSP-1.0", 57),
    "solanum_lycopersicum": ("SL3.0", 57),
    "glycine_max": ("Glycine_max_v2.1", 57),
    "zea_mays": ("Zm-B73-REFERENCE-NAM-5.0", 57),
}


def build_table_fixed(cdna_gz, table_out):
    with gzip.open(cdna_gz, "rt") as f_in, open(table_out, "w") as f_out:
        for line in f_in:
            if not line.startswith(">"):
                continue
            parts = line[1:].split()
            t_id = parts[0]
            gene_symbol = gene_id = None
            for p in parts:
                if p.startswith("gene_symbol:"):
                    gene_symbol = p.split(":", 1)[1]
                elif p.startswith("gene:"):
                    gene_id = p.split(":", 1)[1]
            symbol = gene_symbol or gene_id or t_id
            f_out.write(f"{t_id}\t{symbol}\n")


if __name__ == "__main__":
    for species in sys.argv[1:]:
        if species not in SPECIES_PATHS:
            print(f"[!] {species}: unknown species, skipping")
            continue
        assembly, release = SPECIES_PATHS[species]
        pdir = os.path.join(PYENSEMBL_CACHE, assembly, f"ensembl{release}")
        if not os.path.isdir(pdir):
            print(f"[!] {species}: pyensembl cache dir not found ({pdir}), skipping")
            continue
        cdna = next(
            (os.path.join(pdir, f) for f in os.listdir(pdir) if f.endswith("cdna.all.fa.gz")),
            None,
        )
        if cdna is None:
            print(f"[!] {species}: no cdna.all.fa.gz found in {pdir}, skipping")
            continue
        out_dir = os.path.join(BLASTDB_DIR, species)
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, "table.txt")
        build_table_fixed(cdna, out)
        print(f"[+] {species}: table.txt regenerated from {cdna}")
