import os
import pandas as pd
import psycopg2
import streamlit as st
import urllib.parse as urlparse

try:
    DATABASE_URL = st.secrets["DATABASE_URL"]
except:
    DATABASE_URL = os.environ.get("DATABASE_URL", None)

if DATABASE_URL:
    url = urlparse.urlparse(DATABASE_URL)
    DB_CONFIG = {
        "host":     url.hostname,
        "port":     url.port or 5432,
        "dbname":   url.path[1:],
        "user":     url.username,
        "password": url.password,
        "sslmode":  "require"
    }
else:
    DB_CONFIG = {
        "host":     "localhost",
        "port":     5432,
        "dbname":   "canadian_jobs_db",
        "user":     "postgres",
        "password": "root"
    }

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def run_query(query, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            clean = {
                k: list(v) if isinstance(v, (list, tuple)) else v
                for k, v in params.items()
            } if params else None
            cur.execute(query, clean)
            columns = [desc[0] for desc in cur.description]
            return pd.DataFrame(cur.fetchall(), columns=columns)
    finally:
        conn.close()