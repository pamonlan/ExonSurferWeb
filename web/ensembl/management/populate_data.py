from .connect_pyensembl import connect_pyensembl_db, get_table, connect_local_db, create_engine
from ensembl.models import Gene, Transcript
from django.db import IntegrityError
from django.core.management import call_command
from django.db import connection
import io
import psycopg2.extras
import psycopg2
import pandas as pd

from ensembl.management.species_config import SPECIES_LIST, get_db_path
import os


def update_pk(table):
    """
    Reset the primary key sequence of a table in the local database.
    Args:
        table [in] (str): Table name (e.g. "ensembl_gene")
    """
    app_name = list(table.split("_"))[0]
    output = io.StringIO()
    call_command('sqlsequencereset', app_name, stdout=output, no_color=True)
    sql = output.getvalue()
    with connection.cursor() as cursor:
        cursor.execute(sql)
    output.close()


def populate_gene_table(specie):
    """
    Populate the ensembl_gene table from the pyensembl SQLite DB for a species.

    Handles species that lack gene_name (plants, non-vertebrates) by falling
    back to gene_id as the display name so the web dropdown is never empty.

    Args:
        specie [in] (str): Species key (lowercase, e.g. "solanum_lycopersicum")
    """
    conn_pyensembl = connect_pyensembl_db(specie)

    # Discover which columns actually exist in this species' SQLite gene table
    cursor = conn_pyensembl.cursor()
    cursor.execute("PRAGMA table_info(gene)")
    available_cols = {row[1] for row in cursor.fetchall()}

    wanted_cols = ["gene_id", "strand", "source", "end", "start", "seqname",
                   "gene_biotype", "gene_name", "feature"]
    select_cols = [c for c in wanted_cols if c in available_cols]

    df = get_table("gene", select_cols, conn_pyensembl)

    # Ensure all expected columns exist (fill missing ones with None)
    for col in wanted_cols:
        if col not in df.columns:
            df[col] = None

    df = df[wanted_cols]

    # ── Normalise gene_name ───────────────────────────────────────────────────
    # Plants and non-vertebrates often have no gene symbol — use gene_id instead
    # so the web dropdown is never empty for these species.
    df["gene_name"] = (
        df["gene_name"]
        .replace("", pd.NA)
        .fillna(df["gene_id"])
    )

    df["species"] = specie.lower()

    table_name_local = "ensembl_gene"

    if pd.read_sql(
        f"SELECT * FROM {table_name_local} WHERE species='{specie.lower()}' LIMIT 1",
        con=create_engine()
    ).shape[0] > 0:
        print(f"[+] Warning: The data for {specie} already exists in the gene database", flush=True)
        print("[+] The data was not inserted in the database", flush=True)
    else:
        try:
            df.to_sql(name=table_name_local, if_exists="append",
                      con=create_engine(), index=False)
        except IntegrityError:
            print("[+] Warning: The data already exists in the database", flush=True)
        else:
            print(f"[+] Gene data inserted for {specie}", flush=True)
            update_pk(table_name_local)


def populate_transcript_table(specie):
    """
    Populate the ensembl_transcript table from the pyensembl SQLite DB.

    Handles species that lack transcript_name or gene_name (plants,
    non-vertebrates) by falling back to transcript_id / gene_id respectively.

    Args:
        specie [in] (str): Species key (lowercase, e.g. "solanum_lycopersicum")
    """
    conn_pyensembl = connect_pyensembl_db(specie)

    # Discover available columns
    cursor = conn_pyensembl.cursor()
    cursor.execute("PRAGMA table_info(transcript)")
    available_cols = {row[1] for row in cursor.fetchall()}

    wanted_cols = [
        "transcript_id",
        "transcript_name",
        "transcript_biotype",
        "gene_id",
        "gene_name",
    ]
    select_cols = [c for c in wanted_cols if c in available_cols]

    df = get_table("transcript", select_cols, conn_pyensembl)

    # Ensure all expected columns exist
    for col in wanted_cols:
        if col not in df.columns:
            df[col] = None

    df = df[wanted_cols]

    # ── Normalise transcript_name ─────────────────────────────────────────────
    # EnsemblGenomes plant/fungal/nematode GTFs often omit transcript_name.
    # Fall back to transcript_id so the NOT NULL constraint is never violated.
    df["transcript_name"] = (
        df["transcript_name"]
        .replace("", pd.NA)
        .fillna(df["transcript_id"])
    )

    # ── Normalise gene_name ───────────────────────────────────────────────────
    # Same issue: plants use only gene_id as identifier, no gene symbol.
    df["gene_name"] = (
        df["gene_name"]
        .replace("", pd.NA)
        .fillna(df["gene_id"])
    )

    df["species"] = specie.lower()

    table_name_local = "ensembl_transcript"

    if pd.read_sql(
        f"SELECT * FROM {table_name_local} WHERE species='{specie.lower()}' LIMIT 1",
        con=create_engine()
    ).shape[0] > 0:
        print(f"[+] Warning: The data for {specie} already exists in the transcript database", flush=True)
    else:
        try:
            df.to_sql(
                name=table_name_local,
                if_exists="append",
                con=create_engine(),
                index=False,
            )
        except IntegrityError:
            print("[+] Warning: The data already exists in the database", flush=True)
        else:
            print(f"[+] Transcript data inserted for {specie}", flush=True)
            update_pk(table_name_local)


def populate_housekeeping_genes():
    """
    Populate the ensembl_housekeepinggene table from the versioned curated CSV
    at web/ensembl/data/top50_housekeeping_exonsurfer.csv (14 species x 50 genes,
    100% verified against ExonSurfer GTF databases).
    """
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "top50_housekeeping_exonsurfer.csv",
    )
    df = pd.read_csv(csv_path)
    for col in ("biotype", "sources", "stability_metric", "citation"):
        if col in df.columns:
            df[col] = df[col].fillna("")

    table_name_local = "ensembl_housekeepinggene"

    # Self-heal legacy empty table schema (e.g. apps-01 upgrade from 2.0-rc1 -> 2.0-rc2)
    from django.db import connection
    from ensembl.models import HousekeepingGene
    with connection.cursor() as cur:
        existing_cols = {
            c.name for c in connection.introspection.get_table_description(cur, table_name_local)
        } if table_name_local in connection.introspection.table_names(cur) else set()
        if "evidence_tier" not in existing_cols:
            cur.execute(f"DROP TABLE IF EXISTS {table_name_local} CASCADE;")
    if "evidence_tier" not in existing_cols:
        with connection.schema_editor() as se:
            se.create_model(HousekeepingGene)
        print("[+] Recreated ensembl_housekeepinggene table with updated 2.0-rc2 schema", flush=True)

    try:
        df.to_sql(name=table_name_local, if_exists="append", con=create_engine(), index=False)
    except IntegrityError:
        print("[+] Warning: The housekeeping gene data already exists in the database", flush=True)
    else:
        print(f"[+] Housekeeping gene data inserted ({len(df)} rows across {df['species'].nunique()} species)", flush=True)
        update_pk(table_name_local)


def main():
    """
    Populate gene and transcript tables for all species in SPECIES_LIST.
    Skips species whose GTF DB file has not been built yet (safe to re-run).
    """
    for specie in SPECIES_LIST:
        # Skip species whose GTF DB doesn't exist yet in the container
        try:
            db_path = get_db_path(specie)
        except KeyError:
            print(f"[!] Skipping {specie} — not in species_config", flush=True)
            continue

        if not os.path.exists(db_path):
            print(f"[!] Skipping {specie} — GTF DB not found: {db_path}", flush=True)
            continue

        print(f"\n[+] Processing {specie}", flush=True)
        populate_gene_table(specie)
        populate_transcript_table(specie)

    print("\n[+] All species processed.", flush=True)

    try:
        populate_housekeeping_genes()
    except FileNotFoundError as exc:
        print(f"[!] Housekeeping gene CSV not found ({exc}). Skipping.", flush=True)
        