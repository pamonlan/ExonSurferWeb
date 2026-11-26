"""
species_config.py
─────────────────
Single source of truth for all species metadata in ExonSurferWeb.
Import from here everywhere instead of maintaining parallel dicts/lists.

Usage:
    from species_config import SPECIES, get_db_path, canonical_chr

Add a new species by adding one entry to SPECIES — nothing else needs changing.
"""

# ── Master species registry ───────────────────────────────────────────────────
# Keys are the lowercase Ensembl/internal species identifiers used throughout
# ExonSurfer and the database.  Every other structure below is derived from this.

SPECIES = {
    "homo_sapiens": {
        "display_name":   "Homo sapiens",
        "assembly":       "GRCh38",
        "release":        108,
        "db_type":        "ensembl",
        "gtf_db":         "/home/app/web/Data/pyensembl/GRCh38/ensembl108/Homo_sapiens.GRCh38.108.gtf.db",
        "chromosomes":    [str(i) for i in range(1, 23)] + ["X", "Y", "MT"],
        "api_url":        "homo_sapiens",
        "field_name":     "human_gene_field",
        "scaffold_only":  False,
    },
    "homo_sapiens_masked": {
        # Shares GTF/genome with homo_sapiens — only the seq files differ
        "display_name":   "Homo sapiens (masked)",
        "assembly":       "GRCh38",
        "release":        108,
        "db_type":        "ensembl",
        "gtf_db":         "/home/app/web/Data/pyensembl/GRCh38/ensembl108/Homo_sapiens.GRCh38.108.gtf.db",
        "chromosomes":    [str(i) for i in range(1, 23)] + ["X", "Y", "MT"],
        "api_url":        None,   # shares homo_sapiens endpoint
        "field_name":     None,
        "scaffold_only":  False,
    },
    "mus_musculus": {
        "display_name":   "Mus musculus",
        "assembly":       "GRCm39",
        "release":        108,
        "db_type":        "ensembl",
        "gtf_db":         "/home/app/web/Data/pyensembl/GRCm39/ensembl108/Mus_musculus.GRCm39.108.gtf.db",
        "chromosomes":    [str(i) for i in range(1, 20)] + ["X", "Y", "MT"],
        "api_url":        "mus_musculus",
        "field_name":     "mouse_gene_field",
        "scaffold_only":  False,
    },
    "rattus_norvegicus": {
        "display_name":   "Rattus norvegicus",
        "assembly":       "mRatBN7.2",
        "release":        108,
        "db_type":        "ensembl",
        "gtf_db":         "/home/app/web/Data/pyensembl/mRatBN7.2/ensembl108/Rattus_norvegicus.mRatBN7.2.108.gtf.db",
        "chromosomes":    [str(i) for i in range(1, 21)] + ["X", "Y", "MT"],
        "api_url":        "rattus_norvegicus",
        "field_name":     "rat_gene_field",
        "scaffold_only":  False,
    },
    "danio_rerio": {
        "display_name":   "Danio rerio",
        "assembly":       "GRCz11",
        "release":        108,
        "db_type":        "ensembl",
        "gtf_db":         "/home/app/web/Data/pyensembl/GRCz11/ensembl108/Danio_rerio.GRCz11.108.gtf.db",
        "chromosomes":    [str(i) for i in range(1, 26)] + ["MT"],
        "api_url":        "danio_rerio",
        "field_name":     "zebrafish_gene_field",
        "scaffold_only":  False,
    },
    "drosophila_melanogaster": {
        "display_name":   "Drosophila melanogaster",
        "assembly":       "BDGP6.32",
        "release":        108,
        "db_type":        "ensembl",
        "gtf_db":         "/home/app/web/Data/pyensembl/BDGP6.32/ensembl108/Drosophila_melanogaster.BDGP6.32.108.gtf.db",
        "chromosomes":    ["2L", "2R", "3L", "3R", "4", "X", "Y", "mitochondrion_genome"],
        "api_url":        "drosophila_melanogaster",
        "field_name":     "fly_gene_field",
        "scaffold_only":  False,
    },
    "arabidopsis_thaliana": {
        "display_name":   "Arabidopsis thaliana",
        "assembly":       "TAIR10",
        "release":        57,
        "db_type":        "ensemblgenomes",
        "gtf_db":         "/home/app/web/Data/pyensembl/TAIR10/ensembl57/Arabidopsis_thaliana.TAIR10.57.gtf.db",
        "chromosomes":    [str(i) for i in range(1, 6)] + ["Mt", "Pt"],
        "api_url":        "arabidopsis_thaliana",
        "field_name":     "arabidopsis_gene_field",
        "scaffold_only":  False,
    },
    "oryza_sativa": {
        "display_name":   "Oryza sativa",
        "assembly":       "IRGSP-1.0",
        "release":        57,
        "db_type":        "ensemblgenomes",
        "gtf_db":         "/home/app/web/Data/pyensembl/IRGSP-1.0/ensembl57/Oryza_sativa.IRGSP-1.0.57.gtf.db",
        "chromosomes":    [str(i) for i in range(1, 13)] + ["Mt", "Pt"],
        "api_url":        "oryza_sativa",
        "field_name":     "rice_gene_field",
        "scaffold_only":  False,
    },
    "litomosoides_sigmodontis": {
        "display_name":   "Litomosoides sigmodontis",
        "assembly":       "nLs.2.1",
        "release":        None,   # WormBase, not Ensembl
        "db_type":        "wormbase",
        "gtf_db":         "/home/app/web/Data/pyensembl/Litomosoides_sigmodontis_nLs.2.1/WormBase_ParaSite_WBPS19/litomosoides_sigmodontis.PRJEB3075.WBPS19.canonical_geneset.gtf.db",
        "chromosomes":    [],     # scaffold-based, no canonical chromosomes
        "api_url":        "litomosoides_sigmodontis",
        "field_name":     "mouse_worm_gene_field",
        "scaffold_only":  True,
    },

    # ── New species (v1.4) ────────────────────────────────────────────────────
    "xenopus_tropicalis": {
        "display_name":   "Xenopus tropicalis",
        "assembly":       "UCB_Xtro_10.0",
        "release":        108,
        "db_type":        "ensembl",
        "gtf_db":         "/home/app/web/Data/pyensembl/UCB_Xtro_10.0/ensembl108/Xenopus_tropicalis.UCB_Xtro_10.0.108.gtf.db",
        "chromosomes":    [str(i) for i in range(1, 11)] + ["MT"],
        "api_url":        "xenopus_tropicalis",
        "field_name":     "xenopus_gene_field",
        "scaffold_only":  False,
    },
    "caenorhabditis_elegans": {
        "display_name":   "Caenorhabditis elegans",
        "assembly":       "WBcel235",
        "release":        108,
        "db_type":        "ensembl",
        "gtf_db":         "/home/app/web/Data/pyensembl/WBcel235/ensembl108/Caenorhabditis_elegans.WBcel235.108.gtf.db",
        "chromosomes":    ["I", "II", "III", "IV", "V", "X", "MtDNA"],
        "api_url":        "caenorhabditis_elegans",
        "field_name":     "celegans_gene_field",
        "scaffold_only":  False,
    },
    "saccharomyces_cerevisiae": {
        "display_name":   "Saccharomyces cerevisiae",
        "assembly":       "R64-1-1",
        "release":        108,
        "db_type":        "ensemblgenomes",
        "gtf_db":         "/home/app/web/Data/pyensembl/R64-1-1/ensembl108/Saccharomyces_cerevisiae.R64-1-1.108.gtf.db",
        "chromosomes":    ["I","II","III","IV","V","VI","VII","VIII",
                           "IX","X","XI","XII","XIII","XIV","XV","XVI","Mito"],
        "api_url":        "saccharomyces_cerevisiae",
        "field_name":     "yeast_gene_field",
        "scaffold_only":  False,
    },
    "solanum_lycopersicum": {
        "display_name":   "Solanum lycopersicum",
        "assembly":       "SL3.0",
        "release":        57,
        "db_type":        "ensemblgenomes",
        "gtf_db":         "/home/app/web/Data/pyensembl/SL3.0/ensembl57/Solanum_lycopersicum.SL3.0.57.gtf.db",
        "chromosomes":    [str(i) for i in range(1, 13)],
        "api_url":        "solanum_lycopersicum",
        "field_name":     "tomato_gene_field",
        "scaffold_only":  False,
    },
    "zea_mays": {
        "display_name":   "Zea mays",
        "assembly":       "Zm-B73-REFERENCE-NAM-5.0",
        "release":        57,
        "db_type":        "ensemblgenomes",
        "gtf_db":         "/home/app/web/Data/pyensembl/Zm-B73-REFERENCE-NAM-5.0/ensembl57/Zea_mays.Zm-B73-REFERENCE-NAM-5.0.57.gtf.db",
        "chromosomes":    [str(i) for i in range(1, 11)],
        "api_url":        "zea_mays",
        "field_name":     "maize_gene_field",
        "scaffold_only":  False,
    },
    "glycine_max": {
        "display_name":   "Glycine max",
        "assembly":       "Glycine_max_v2.1",
        "release":        57,
        "db_type":        "ensemblgenomes",
        "gtf_db":         "/home/app/web/Data/pyensembl/Glycine_max_v2.1/ensembl57/Glycine_max.Glycine_max_v2.1.57.gtf.db",
        "chromosomes":    [str(i) for i in range(1, 21)],
        "api_url":        "glycine_max",
        "field_name":     "soybean_gene_field",
        "scaffold_only":  False,
    },
}


# ── Derived structures (auto-built — never edit these manually) ───────────────

# List of all species keys in display order
SPECIES_LIST = list(SPECIES.keys())

# {species_key: "Display Name"} — for forms, models.get_species()
DISPLAY_NAMES = {k: v["display_name"] for k, v in SPECIES.items()}

# {species_key: [chromosomes]} — for views.canonical_chr
CANONICAL_CHR = {
    k: v["chromosomes"]
    for k, v in SPECIES.items()
    if not v["scaffold_only"]
}

# {species_key: gtf_db_path} — for build_specie_path_db()
GTF_DB_PATHS = {
    # capitalised keys to match the existing management command convention
    k.replace("_", " ").title().replace(" ", "_"): v["gtf_db"]
    for k, v in SPECIES.items()
}

# Form choices list — for SpeciesGeneForm.SPECIES_CHOICES
SPECIES_CHOICES = [
    (k, v["display_name"])
    for k, v in SPECIES.items()
    if v["api_url"] is not None and k != "homo_sapiens_masked"
]

# {species_key: field_name} — for species_field_map in views
SPECIES_FIELD_MAP = {
    k: v["field_name"]
    for k, v in SPECIES.items()
    if v["field_name"] is not None
}

# URL patterns list — for urls.py  (use api_url, skip None entries)
API_SPECIES = {
    k: v["api_url"]
    for k, v in SPECIES.items()
    if v["api_url"] is not None
}

# get_specie() replacement — maps masked variant back to base species
def get_specie(species_key: str) -> str:
    """Return the canonical species key (strips _masked suffix)."""
    if species_key == "homo_sapiens_masked":
        return "homo_sapiens"
    return species_key


# get_db_path() replacement — for build_specie_path_db()
def get_db_path(species_key: str) -> str:
    """Return the GTF SQLite DB path for a species."""
    # Accept both capitalised (legacy) and lowercase keys
    lower = species_key.lower()
    if lower in SPECIES:
        return SPECIES[lower]["gtf_db"]
    raise KeyError(f"Unknown species: {species_key!r}")


# get_release() — for create_ensembl_data() calls
def get_release(species_key: str) -> int:
    """Return the Ensembl release number for a species."""
    return SPECIES[species_key.lower()]["release"]