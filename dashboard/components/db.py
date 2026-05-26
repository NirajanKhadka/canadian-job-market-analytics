import os
import psycopg2
import pandas as pd
import streamlit as st


def get_conn():
    # Streamlit Cloud → reads from st.secrets
    # Local → reads from environment variable or falls back to local config
    try:
        database_url = st.secrets["DATABASE_URL"]
    except Exception:
        database_url = os.getenv("DATABASE_URL", None)

    if database_url:
        return psycopg2.connect(database_url, sslmode="require")

    # Local PostgreSQL fallback
    return psycopg2.connect(
        dbname   = os.getenv("LOCAL_DB_NAME",     "canadian_jobs_db"),
        user     = os.getenv("LOCAL_DB_USER",     "postgres"),
        password = os.getenv("LOCAL_DB_PASSWORD", ""),
        host     = os.getenv("LOCAL_DB_HOST",     "localhost"),
        port     = int(os.getenv("LOCAL_DB_PORT", "5432")),
    )


def run_query(sql: str, params=None) -> pd.DataFrame:
    conn = get_conn()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()