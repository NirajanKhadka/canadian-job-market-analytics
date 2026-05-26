# db_connection.py
import os
import psycopg2
import pandas as pd

DB_CONFIG = {
    "dbname"  : os.getenv("LOCAL_DB_NAME",     "canadian_jobs_db"),
    "user"    : os.getenv("LOCAL_DB_USER",     "postgres"),
    "password": os.getenv("LOCAL_DB_PASSWORD", "root"),
    "host"    : os.getenv("LOCAL_DB_HOST",     "localhost"),
    "port"    : int(os.getenv("LOCAL_DB_PORT", "5432")),
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def run_query(sql: str, params=None) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)