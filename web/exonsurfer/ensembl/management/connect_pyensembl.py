#Conect to sqlite database
import sqlite3
import os
import pandas as pd
from exonsurfer.settings import BASE_DIR

def build_specie_path_db(specie):
    #Build the path to the specie database
    species_db = {
        "Rattus_norvegicus": "/home/q053pm//.cache/pyensembl/mRatBN7.2/ensembl108/Rattus_norvegicus.mRatBN7.2.108.gtf.db",
        "Homo_sapiens": "/home/q053pm//.cache/pyensembl/GRCh38/ensembl76/Homo_sapiens.GRCh38.76.gtf.db",
        "Mus_musculus": "/home/q053pm/.cache/pyensembl/GRCm39/ensembl108/Mus_musculus.GRCm39.108.gtf.db"
    }
    return species_db[specie]

def connect_pyensembl_db(specie):
    #Connect to the specie database
    db_path = build_specie_path_db(specie)
    conn = sqlite3.connect(db_path)
    return conn

def get_table(table_name, col_names, conn):
    #Get the table from the database
    query = "SELECT {} FROM {}".format(",".join(col_names), table_name)
    df = pd.read_sql_query(query, conn)
    return df

def connect_local_db():
    #Connect to the local database
    path_db = os.path.join(BASE_DIR, "db.sqlite3")
    conn = sqlite3.connect(path_db)
    return conn