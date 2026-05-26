import pandas as pd
import ast
import re
import os

os.makedirs("data/normalized", exist_ok=True)

# ── TARGET SCHEMA ──────────────────────────────────────────────
# job_title, role, company, location, city, country,
# salary_year_avg, salary_hour_avg, salary_rate,
# remote, schedule_type, posted_date, skills_raw, source

# ── HELPER FUNCTIONS ──────────────────────────────────────────

def extract_city(location_str):
    """Extract city from location string."""
    if pd.isna(location_str):
        return None
    return str(location_str).split(',')[0].strip()

def parse_skills_str(val):
    """Parse skills from various formats into a clean Python list."""
    if pd.isna(val) or val == '' or val == '[]':
        return []
    try:
        result = ast.literal_eval(str(val))
        if isinstance(result, list):
            return [str(s).strip().lower() for s in result if s]
    except:
        pass
    # fallback: split by comma/semicolon
    return [s.strip().lower() for s in re.split(r'[,;|]', str(val)) if s.strip()]

def parse_euro_salary(val):
    """Convert Euro salary string to USD-equivalent float (approx 1 EUR = 1.47 CAD)."""
    if pd.isna(val):
        return None
    val = str(val).replace('€', '').replace(',', '').strip()
    # Handle range like "100472 - 200938" → take average
    if '-' in val:
        parts = val.split('-')
        try:
            nums = [float(p.strip()) for p in parts if p.strip()]
            eur_avg = sum(nums) / len(nums)
            return round(eur_avg * 1.47, 0)  # EUR → CAD approx
        except:
            return None
    try:
        return round(float(val) * 1.47, 0)
    except:
        return None

def standardize_role(title):
    """Map varied job titles to standard role buckets."""
    if pd.isna(title):
        return 'Other'
    title_lower = str(title).lower()
    if any(x in title_lower for x in ['bi developer', 'bi analyst', 'business intelligence']):
        return 'BI Developer'
    if any(x in title_lower for x in ['data analyst', 'data analysis']):
        return 'Data Analyst'
    if any(x in title_lower for x in ['data scientist', 'data science']):
        return 'Data Scientist'
    if any(x in title_lower for x in ['data engineer', 'data engineering']):
        return 'Data Engineer'
    if any(x in title_lower for x in ['machine learning', 'ml engineer']):
        return 'ML Engineer'
    if any(x in title_lower for x in ['business analyst']):
        return 'Business Analyst'
    if any(x in title_lower for x in ['software engineer', 'software developer']):
        return 'Software Engineer'
    return 'Other'

# ── NORMALIZE COLUMNS TO TARGET ───────────────────────────────
TARGET_COLS = [
    'job_title', 'role', 'company', 'location', 'city', 'country',
    'salary_year_avg', 'salary_hour_avg', 'salary_rate',
    'remote', 'schedule_type', 'posted_date',
    'skills_raw', 'source'
]

# ══════════════════════════════════════════════════════════════
# DATASET 1 — lukebarousse
# ══════════════════════════════════════════════════════════════
print("\nNormalizing lukebarousse...")
df1 = pd.read_csv("data/raw/lukebarousse_raw.csv", low_memory=False)
df1 = df1[df1['job_country'] == 'Canada'].copy()

df1_norm = pd.DataFrame()
df1_norm['job_title']       = df1['job_title']
df1_norm['role']            = df1['job_title_short'].apply(standardize_role)
df1_norm['company']         = df1['company_name']
df1_norm['location']        = df1['job_location']
df1_norm['city']            = df1['job_location'].apply(extract_city)
df1_norm['country']         = 'Canada'
df1_norm['salary_year_avg'] = pd.to_numeric(df1['salary_year_avg'], errors='coerce')
df1_norm['salary_hour_avg'] = pd.to_numeric(df1['salary_hour_avg'], errors='coerce')
df1_norm['salary_rate']     = df1['salary_rate']
df1_norm['remote']          = df1['job_work_from_home'].astype(bool)
df1_norm['schedule_type']   = df1['job_schedule_type']
df1_norm['posted_date']     = pd.to_datetime(df1['job_posted_date'], errors='coerce')
df1_norm['skills_raw']      = df1['job_skills'].apply(parse_skills_str)
df1_norm['source']          = 'lukebarousse'

df1_norm.to_csv("data/normalized/lukebarousse_norm.csv", index=False)
print(f"  ✅ lukebarousse: {len(df1_norm):,} rows")

# ══════════════════════════════════════════════════════════════
# DATASET 2 — techsalerator
# ══════════════════════════════════════════════════════════════
print("\nNormalizing techsalerator...")
df2 = pd.read_csv("data/raw/techsalerator/Job Posting.csv", encoding='latin-1')

df2_norm = pd.DataFrame()
df2_norm['job_title']       = df2['Job Opening Title']
df2_norm['role']            = df2['Job Opening Title'].apply(standardize_role)
df2_norm['company']         = df2['Website Domain']
df2_norm['location']        = df2['Location']
df2_norm['city']            = df2['Location'].apply(extract_city)
df2_norm['country']         = 'Canada'   # dataset is Canada-only
df2_norm['salary_year_avg'] = pd.to_numeric(
    df2['Salary'].astype(str).str.replace(r'[^\d.]', '', regex=True),
    errors='coerce'
)
df2_norm['salary_hour_avg'] = None
df2_norm['salary_rate']     = None
df2_norm['remote']          = df2['Location'].str.contains('Remote', case=False, na=False)
df2_norm['schedule_type']   = df2['Contract Types']
df2_norm['posted_date']     = pd.to_datetime(df2['First Seen At'], errors='coerce')
df2_norm['skills_raw']      = df2['Keywords'].apply(parse_skills_str)
df2_norm['source']          = 'techsalerator'

df2_norm.to_csv("data/normalized/techsalerator_norm.csv", index=False)
print(f"  ✅ techsalerator: {len(df2_norm):,} rows")

# ══════════════════════════════════════════════════════════════
# DATASET 3 — asaniczka (join 3 files on job_link)
# ══════════════════════════════════════════════════════════════
print("\nNormalizing asaniczka...")
df3_posts  = pd.read_csv("data/raw/asaniczka/job_postings.csv")
df3_skills = pd.read_csv("data/raw/asaniczka/job_skills.csv")
df3_summ   = pd.read_csv("data/raw/asaniczka/job_summary.csv")

# Join all 3 on job_link
df3 = df3_posts.merge(df3_skills, on='job_link', how='left') \
               .merge(df3_summ,   on='job_link', how='left')

# Filter Canada
df3 = df3[df3['search_country'].str.lower() == 'canada'].copy() \
    if 'search_country' in df3.columns else df3.copy()

df3_norm = pd.DataFrame()
df3_norm['job_title']       = df3['job_title']
df3_norm['role']            = df3['job_title'].apply(standardize_role)
df3_norm['company']         = df3['company']
df3_norm['location']        = df3['job_location']
df3_norm['city']            = df3['job_location'].apply(extract_city)
df3_norm['country']         = 'Canada'
df3_norm['salary_year_avg'] = None   # asaniczka has no salary column
df3_norm['salary_hour_avg'] = None
df3_norm['salary_rate']     = None
df3_norm['remote']          = df3['job_location'].str.contains('Remote', case=False, na=False)
df3_norm['schedule_type']   = df3['job_type']
df3_norm['posted_date']     = pd.to_datetime(df3['first_seen'], errors='coerce')
df3_norm['skills_raw']      = df3['job_skills'].apply(parse_skills_str)
df3_norm['source']          = 'asaniczka'

df3_norm.to_csv("data/normalized/asaniczka_norm.csv", index=False)
print(f"  ✅ asaniczka: {len(df3_norm):,} rows")

# ══════════════════════════════════════════════════════════════
# DATASET 4 — elahehgolrokh
# ══════════════════════════════════════════════════════════════
print("\nNormalizing elahehgolrokh...")
df4 = pd.read_csv("data/raw/elahehgolrokh/data_science_job_posts_2025.csv")

df4_norm = pd.DataFrame()
df4_norm['job_title']       = df4['job_title']
df4_norm['role']            = df4['job_title'].apply(standardize_role)
df4_norm['company']         = df4['company']
df4_norm['location']        = df4['location']
df4_norm['city']            = df4['location'].apply(extract_city)
df4_norm['country']         = 'Canada'   # treat all as Canada (global DS jobs, enriches salary data)
df4_norm['salary_year_avg'] = df4['salary'].apply(parse_euro_salary)
df4_norm['salary_hour_avg'] = None
df4_norm['salary_rate']     = 'year'
df4_norm['remote']          = df4['status'].str.contains('remote', case=False, na=False)
df4_norm['schedule_type']   = df4['status']
df4_norm['posted_date']     = pd.to_datetime(df4['post_date'], errors='coerce')
df4_norm['skills_raw']      = df4['skills'].apply(parse_skills_str)
df4_norm['source']          = 'elahehgolrokh'

df4_norm.to_csv("data/normalized/elahehgolrokh_norm.csv", index=False)
print(f"  ✅ elahehgolrokh: {len(df4_norm):,} rows")

# ══════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════════
print("\n========== NORMALIZATION SUMMARY ==========")
for name, df in [("lukebarousse", df1_norm), ("techsalerator", df2_norm),
                 ("asaniczka", df3_norm), ("elahehgolrokh", df4_norm)]:
    print(f"  {name:<20} {len(df):>6,} rows | "
          f"salary_null: {df['salary_year_avg'].isna().mean()*100:.0f}% | "
          f"skills_empty: {df['skills_raw'].apply(lambda x: len(x)==0).mean()*100:.0f}%")
print("============================================")
print("✅ All normalized files saved to data/normalized/")