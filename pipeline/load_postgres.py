import pandas as pd
import ast
import os
from sqlalchemy import create_engine, text

# ── CONFIG ────────────────────────────────────────────────────
DB_USER     = "postgres"
DB_PASSWORD = "root"   # ← change this
DB_HOST     = "localhost"
DB_PORT     = "5432"
DB_NAME     = "canadian_jobs_db"

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL)

print("Connecting to PostgreSQL...")
with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
print("✅ Connected successfully\n")

# ── LOAD DATA ─────────────────────────────────────────────────
print("Loading master_jobs_clean.csv...")
df = pd.read_csv("data/processed/master_jobs_clean.csv", low_memory=False)
print(f"Shape: {df.shape}")

# ── FINAL CLEANUP BEFORE DB LOAD ──────────────────────────────
# Kill any remaining 'Nan' string city values
df['city'] = df['city'].replace({'Nan': 'Unspecified', 'nan': 'Unspecified',
                                  'None': 'Unspecified', 'none': 'Unspecified'})

# Parse posted_date safely
df['posted_date'] = pd.to_datetime(df['posted_date'], errors='coerce').dt.date

# Ensure numeric types

df['salary_year_avg'] = pd.to_numeric(df['salary_year_avg'], errors='coerce')
df['salary_hour_avg'] = pd.to_numeric(df['salary_hour_avg'], errors='coerce')
df['skills_count']    = pd.to_numeric(df['skills_count'],    errors='coerce').fillna(0).astype(int)
df['remote']          = df['remote'].astype(str).str.lower().isin(['true', '1', 'yes'])
df['year']            = pd.to_numeric(df['year'],  errors='coerce').fillna(0).astype(int)
df['month']           = pd.to_numeric(df['month'], errors='coerce').fillna(0).astype(int)

# ══════════════════════════════════════════════════════════════
# STEP 1 — CREATE SCHEMA
# ══════════════════════════════════════════════════════════════
print("Creating schema...")

schema_sql = """
DROP TABLE IF EXISTS job_skills CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;

CREATE TABLE jobs (
    job_id          SERIAL PRIMARY KEY,
    job_title       TEXT,
    role            TEXT,
    company         TEXT,
    city            TEXT,
    location        TEXT,
    country         TEXT,
    salary_year_avg NUMERIC,
    salary_hour_avg NUMERIC,
    salary_rate     TEXT,
    remote          BOOLEAN,
    schedule_type   TEXT,
    posted_date     DATE,
    year            INT,
    month           INT,
    skills_count    INT,
    source          TEXT
);

CREATE TABLE job_skills (
    id      SERIAL PRIMARY KEY,
    job_id  INT REFERENCES jobs(job_id) ON DELETE CASCADE,
    skill   TEXT
);

CREATE INDEX idx_jobs_role       ON jobs(role);
CREATE INDEX idx_jobs_city       ON jobs(city);
CREATE INDEX idx_jobs_source     ON jobs(source);
CREATE INDEX idx_jobs_posted     ON jobs(posted_date);
CREATE INDEX idx_skills_job_id   ON job_skills(job_id);
CREATE INDEX idx_skills_skill    ON job_skills(skill);
"""

with engine.connect() as conn:
    conn.execute(text(schema_sql))
    conn.commit()
print("✅ Schema created\n")

# ══════════════════════════════════════════════════════════════
# STEP 2 — LOAD JOBS TABLE
# ══════════════════════════════════════════════════════════════
print("Loading jobs table...")

jobs_cols = [
    'job_title', 'role', 'company', 'city', 'location', 'country',
    'salary_year_avg', 'salary_hour_avg', 'salary_rate',
    'remote', 'schedule_type', 'posted_date',
    'year', 'month', 'skills_count', 'source'
]

df_jobs = df[jobs_cols].copy()
df_jobs.to_sql('jobs', engine, if_exists='append', index=False, method='multi', chunksize=500)

with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM jobs"))
    print(f"✅ Jobs loaded: {result.fetchone()[0]:,} rows\n")

# ══════════════════════════════════════════════════════════════
# STEP 3 — LOAD JOB_SKILLS TABLE
# ══════════════════════════════════════════════════════════════
print("Building job_skills table...")

# Get job_ids from DB (they were auto-assigned by SERIAL)
with engine.connect() as conn:
    db_jobs = pd.read_sql("SELECT job_id, job_title, company, posted_date FROM jobs", conn)

# Merge to get job_id per row
df['posted_date_str'] = df['posted_date'].astype(str)
db_jobs['posted_date_str'] = db_jobs['posted_date'].astype(str)

df_merged = df.merge(
    db_jobs[['job_id', 'job_title', 'company', 'posted_date_str']],
    on=['job_title', 'company', 'posted_date_str'],
    how='left'
)

# Explode skills into one row per skill
skills_rows = []
for _, row in df_merged.iterrows():
    job_id = row.get('job_id')
    if pd.isna(job_id):
        continue
    try:
        skills = ast.literal_eval(str(row['skills'])) if isinstance(row['skills'], str) else row['skills']
    except:
        continue
    for skill in skills:
        skill = str(skill).strip().lower()
        if skill and len(skill) > 1:
            skills_rows.append({'job_id': int(job_id), 'skill': skill})

df_skills = pd.DataFrame(skills_rows)
print(f"Total skill rows to insert: {len(df_skills):,}")

df_skills.to_sql('job_skills', engine, if_exists='append', index=False, method='multi', chunksize=1000)

with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM job_skills"))
    print(f"✅ Job skills loaded: {result.fetchone()[0]:,} rows\n")

# ══════════════════════════════════════════════════════════════
# STEP 4 — VALIDATION QUERIES
# ══════════════════════════════════════════════════════════════
print("Running validation queries...\n")

validation_queries = {
    "Total jobs"           : "SELECT COUNT(*) FROM jobs",
    "Total skill rows"     : "SELECT COUNT(*) FROM job_skills",
    "Unique skills"        : "SELECT COUNT(DISTINCT skill) FROM job_skills",
    "Jobs with salary"     : "SELECT COUNT(*) FROM jobs WHERE salary_year_avg IS NOT NULL",
    "Top role"             : "SELECT role, COUNT(*) as n FROM jobs GROUP BY role ORDER BY n DESC LIMIT 1",
    "Top city"             : "SELECT city, COUNT(*) as n FROM jobs GROUP BY city ORDER BY n DESC LIMIT 1",
    "Top skill"            : "SELECT skill, COUNT(*) as n FROM job_skills GROUP BY skill ORDER BY n DESC LIMIT 1",
}

with engine.connect() as conn:
    for label, query in validation_queries.items():
        result = conn.execute(text(query))
        row = result.fetchone()
        print(f"  {label:<25}: {row[0] if len(row) == 1 else f'{row[0]} ({row[1]:,})'}")

print("\n✅ PostgreSQL load complete — canadian_jobs_db is ready!")
print("   Tables: jobs, job_skills")
