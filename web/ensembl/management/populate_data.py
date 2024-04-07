from .connect_pyensembl import connect_pyensembl_db, get_table, connect_local_db, create_engine
from ensembl.models import Gene, Transcript
from django.db import IntegrityError
from django.core.management import call_command
from django.db import connection
import io
import psycopg2.extras
import psycopg2
import pandas as pd


def update_pk(table):
    """
    This function reset the primary key of a table in the local database.
    Args:
        table [in] (str): Table name

    """
    app_name = list(table.split("_"))[0]

    # Get SQL commands from sqlsequencereset
    output = io.StringIO()
    call_command('sqlsequencereset', app_name, stdout=output, no_color=True)
    sql = output.getvalue()
        
    with connection.cursor() as cursor:
        cursor.execute(sql)
    output.close()



def populate_gene_table(specie):
    """
    This function populates the gene table in the local database. Open the
    specie database and get the gene table. Selecte the columns: gene_id,strand,
    gene_version,source,end,start,gene_biotype,gene_id,gene_name,feature.

    And create the col species with the specie name. Insert the data in the
    local database.

   
    Args:
        specie [in] (str): Specie name
    """
    # Connect to the local database
    conn_local = connect_local_db()

    # Connect to the PostgreSQL database
    conn_postgres = connect_local_db()

    # Connect to the specie database
    conn_pyensembl = connect_pyensembl_db(specie)

    # Get the gene table from the specie database
    table_name = "gene"
    col_names = ["gene_id", "strand", "source", "end", "start","seqname",
                    "gene_biotype", "gene_id", "gene_name", "feature"]
    df = get_table(table_name, col_names, conn_pyensembl)
    df.columns = ["gene_id", "strand", "source", "end", "start","seqname",
                    "gene_biotype", "gene_id", "gene_name", "feature"]
    # Add the species column
    df["species"] = specie.lower()

    # Local table name
    table_name_local = "ensembl_gene"

    # Copy the data from the local database to the PostgreSQL database
    # Check if data already exists in the database
    if pd.read_sql(f"SELECT * FROM {table_name_local} WHERE species='{specie.lower()}' LIMIT 1", con=create_engine()).shape[0] > 0:
        print(f"Error: The data for {specie} already exists in the gene database", flush=True)
        print("The data was not inserted in the database", flush=True)
    else:
        try:
            df.to_sql(name=table_name_local, if_exists="append", con=create_engine(), index=False)
        except IntegrityError:
            print("Error: The data already exists in the database", flush=True)
        else:
            print("The data was inserted in the database")
            update_pk(table_name_local)


def populate_transcript_table(specie):
    """
    This function populates the transcript table in the local database. Open the
    specie database and get the transcript table. Selecte the columns:
    transcript_version, transcript_id, transcript_name, transcript_biotype,
    gene_id, gene_name.

    Insert the data in the local database.
    Args:
        specie [in] (str): Specie name
    """

    # Connect to the local database
    conn_local = connect_local_db()

    # Connect to the PostgreSQL database
    conn_postgres = connect_local_db()

    #Connect to the specie database
    conn_pyensembl = connect_pyensembl_db(specie)
    #Get the transcript table from the specie database
    table_name = "transcript"
    col_names = ["transcript_id", "transcript_name",
                    "transcript_biotype", "gene_id", "gene_name"]
    df = get_table(table_name, col_names, conn_pyensembl)
    df["species"] = specie.lower()
    #Local_table_name
    table_name_local = "ensembl_transcript"
    #Insert the data in the local database
    # Check if data already exists in the database
    if pd.read_sql(f"SELECT * FROM {table_name_local} WHERE species='{specie.lower()}' LIMIT 1", con=create_engine()).shape[0] > 0:
        print(f"[+] Warning: The data for {specie} already exists in the transcript database", flush=True)
    else:
        try:
            df.to_sql(name=table_name_local, if_exists="append", con=create_engine(), index=False)
        except IntegrityError:
            print("[+] Warning: The data already exists in the database")
        else:
            print("[+] The data was inserted in the database")
            update_pk(table_name_local)


def main():
    """
    Function to update gene, mouse, and rat tables
    in the local database.
    """

    for specie in ["Rattus_norvegicus", "Mus_musculus","Homo_sapiens", "Drosophila_melanogaster", "Danio_rerio","Arabidopsis_thaliana", "Oryza_sativa"]:
        populate_gene_table(specie)
        populate_transcript_table(specie)
