#Conect to sqlite database
import sqlite3
import os
import pandas as pd
from exonsurfer.settings import BASE_DIR
import psycopg2
import sys
import sqlalchemy

params_dic = {
        "host"      : os.environ.get("SQL_HOST", "localhost"),
        "database"  : os.environ.get("SQL_DATABASE", os.path.join(BASE_DIR, "db.sqlite3")),
        "user"      : os.environ.get("SQL_USER", "user"),
        "password"  : os.environ.get("SQL_PASSWORD", "password"),
        'port': os.environ.get("SQL_PORT", "5432")
    }

def build_specie_path_db(specie):
    #Build the path to the specie database
    species_db = {
        "Rattus_norvegicus": "/home/app/web/Data/pyensembl/mRatBN7.2/ensembl108/Rattus_norvegicus.mRatBN7.2.108.gtf.db",
        "Homo_sapiens": "/home/app/web/Data/pyensembl/GRCh38/ensembl108/Homo_sapiens.GRCh38.108.gtf.db",
        "Mus_musculus": "/home/app/web/Data/pyensembl/GRCm39/ensembl108/Mus_musculus.GRCm39.108.gtf.db"
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
    #Connect to the postgres local database
    conn = None
    try:
        if "SQL_HOST" in os.environ:
            # connect to the PostgreSQL server
            print('Connecting to the PostgreSQL database...')
            conn = psycopg2.connect(**params_dic)
        else:            
            # connect to the SQLite server
            print('Connecting to the SQLite database...')
            conn = sqlite3.connect(params_dic["database"])

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        sys.exit(1) 
    print("Connection successful")
    return conn

def create_engine():
    #Create the engine to connect to the local database
    if "SQL_HOST" in os.environ:
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        engine = sqlalchemy.create_engine(f'postgresql://{params_dic["user"]}:{params_dic["password"]}@{params_dic["host"]}:{params_dic["port"]}/{params_dic["database"]}')
    else:            
        # connect to the SQLite server
        print('Connecting to the SQLite database...')
        engine = sqlalchemy.create_engine(f'sqlite:///{params_dic["database"]}')
    return engine