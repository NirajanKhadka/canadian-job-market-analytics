import pandas as pd
import ast
import re
import os
import warnings
warnings.filterwarnings('ignore')

os.makedirs("data/processed", exist_ok=True)

print("Loading master_jobs.csv...")
df = pd.read_csv("data/processed/master_jobs.csv", low_memory=False)
print(f"Starting shape: {df.shape}")

# ══════════════════════════════════════════════════════════════
# 1. ROLE STANDARDIZATION
# ══════════════════════════════════════════════════════════════
def standardize_role(title):
    if pd.isna(title):
        return 'Other'
    t = str(title).lower()
    if any(x in t for x in ['bi developer', 'bi analyst', 'business intelligence',
                              'power bi', 'tableau developer', 'reporting analyst',
                              'bi report', 'bi specialist']):
        return 'BI Developer'
    if any(x in t for x in ['data analyst', 'data analysis', 'analytics analyst',
                              'insights analyst', 'research analyst', 'analyst ii',
                              'analyst iii', 'senior analyst', 'junior analyst']):
        return 'Data Analyst'
    if any(x in t for x in ['data scientist', 'data science', 'applied scientist',
                              'quantitative analyst', 'statistical analyst',
                              'statistician', 'actuary', 'econometri']):
        return 'Data Scientist'
    if any(x in t for x in ['data engineer', 'data engineering', 'etl developer',
                              'etl engineer', 'pipeline engineer', 'databricks',
                              'spark engineer', 'analytics engineer',
                              'cloud architect', 'solution architect', 'data architect',
                              'database administrator', 'dba', 'data modeler']):
        return 'Data Engineer'
    if any(x in t for x in ['machine learning', 'ml engineer', 'ai engineer',
                              'deep learning', 'nlp engineer', 'computer vision',
                              'mlops', 'ai developer']):
        return 'ML Engineer'
    if any(x in t for x in ['business analyst', 'systems analyst', 'functional analyst',
                              'product analyst', 'process analyst', 'operations analyst']):
        return 'Business Analyst'
    if any(x in t for x in ['software engineer', 'software developer', 'backend',
                              'frontend', 'fullstack', 'full stack', 'devops',
                              'cloud engineer', 'platform engineer']):
        return 'Software Engineer'
    # Broad data-related consultant/specialist → Data Analyst
    if any(x in t for x in ['consultant', 'advisor', 'specialist',
                              'associate', 'coordinator']):
        if any(x in t for x in ['data', 'analytics', 'insight', 'report']):
            return 'Data Analyst'
    return 'Other'

df['role'] = df['job_title'].apply(standardize_role)

# ══════════════════════════════════════════════════════════════
# 2. PARSE DATES
# ══════════════════════════════════════════════════════════════
df['posted_date'] = pd.to_datetime(df['posted_date'], errors='coerce')
df['year']  = df['posted_date'].dt.year
df['month'] = df['posted_date'].dt.month
print(f"Date range: {df['posted_date'].min()} → {df['posted_date'].max()}")

# ══════════════════════════════════════════════════════════════
# 3. CLEAN SALARY
# ══════════════════════════════════════════════════════════════
df['salary_year_avg'] = pd.to_numeric(df['salary_year_avg'], errors='coerce')
df['salary_hour_avg'] = pd.to_numeric(df['salary_hour_avg'], errors='coerce')

salary_before = df['salary_year_avg'].notna().sum()
df.loc[~df['salary_year_avg'].between(25000, 400000), 'salary_year_avg'] = None
salary_after = df['salary_year_avg'].notna().sum()
print(f"Salary outliers removed : {salary_before - salary_after}")
print(f"Rows with salary        : {salary_after:,} ({salary_after/len(df)*100:.1f}%)")

# ══════════════════════════════════════════════════════════════
# 4. CLEAN CITY
# ══════════════════════════════════════════════════════════════
df['city'] = df['city'].astype(str).str.strip().str.lower()

# Step 1 — known variant → canonical name
city_map = {
    'greater toronto area'      : 'toronto',
    'toronto, on'               : 'toronto',
    'toronto ontario'           : 'toronto',
    'north york'                : 'toronto',
    'scarborough'               : 'toronto',
    'etobicoke'                 : 'toronto',
    'east york'                 : 'toronto',
    'city of toronto'           : 'toronto',
    'downtown toronto'          : 'toronto',
    'mississauga'               : 'mississauga',
    'brampton'                  : 'brampton',
    'oakville'                  : 'oakville',
    'markham'                   : 'markham',
    'richmond hill'             : 'richmond hill',
    'vaughan'                   : 'vaughan',
    'burlington'                : 'burlington',
    'hamilton'                  : 'hamilton',
    'kitchener'                 : 'kitchener',
    'waterloo'                  : 'waterloo',
    'remote'                    : 'Remote',
    'work from home'            : 'Remote',
    'anywhere'                  : 'Remote',
    'home office'               : 'Remote',
    # nullify
    'canada'                    : 'Unspecified',
    'nan'                       : 'Unspecified',
    'nat'                       : 'Unspecified',
    'n/a'                       : 'Unspecified',
    'none'                      : 'Unspecified',
    ''                          : 'Unspecified',
}
df['city'] = df['city'].replace(city_map)

# Step 2 — province names → Unspecified
province_names = {
    'ontario', 'british columbia', 'alberta', 'quebec', 'manitoba',
    'saskatchewan', 'nova scotia', 'new brunswick', 'newfoundland',
    'prince edward island', 'bc', 'on', 'ab', 'qc', 'mb', 'sk', 'ns',
}
df.loc[df['city'].isin(province_names), 'city'] = 'Unspecified'

# Step 3 — explicit non-Canadian city/country list → Unspecified
non_canada = {
    # India
    'bangalore', 'bengaluru', 'chennai', 'mumbai', 'hyderabad', 'pune',
    'delhi', 'new delhi', 'india', 'kolkata', 'ahmedabad', 'noida',
    'gurgaon', 'gurugram', 'jaipur', 'chandigarh',
    # Europe
    'hanau', 'berlin', 'munich', 'frankfurt', 'hamburg', 'germany',
    'paris', 'lyon', 'france', 'amsterdam', 'netherlands',
    'budapest', 'hungary', 'cz_stochowa', 'warsaw', 'poland',
    'rome', 'milan', 'italy', 'madrid', 'spain', 'barcelona',
    'zurich', 'switzerland', 'vienna', 'austria', 'brussels', 'belgium',
    'stockholm', 'sweden', 'oslo', 'norway', 'copenhagen', 'denmark',
    'helsinki', 'finland', 'lisbon', 'portugal', 'bucharest', 'romania',
    'prague', 'czech republic', 'sofia', 'bulgaria',
    # US states/cities
    'new york', 'chicago', 'austin', 'seattle', 'boston',
    'san francisco', 'los angeles', 'denver', 'atlanta',
    'indiana', 'ohio', 'texas', 'california', 'florida',
    'washington', 'virginia', 'georgia', 'michigan', 'illinois',
    'pennsylvania', 'new jersey', 'arizona', 'nevada',
    # Asia-Pacific
    'campinas', 'sao paulo', 'brazil', 'singapore', 'sydney',
    'melbourne', 'australia', 'dubai', 'abu dhabi', 'riyadh',
    'jakarta', 'indonesia', 'manila', 'philippines', 'bangkok',
    'thailand', 'kuala lumpur', 'malaysia', 'tokyo', 'japan',
    'beijing', 'shanghai', 'china', 'hong kong', 'seoul', 'korea',
    # Other
    'united kingdom', 'uk', 'london uk', 'cape town', 'johannesburg',
    'south africa', 'nigeria', 'lagos', 'nairobi', 'kenya',
}
df.loc[df['city'].isin(non_canada), 'city'] = 'Unspecified'

# Step 4 — catch remaining Nan variants explicitly
df.loc[df['city'].str.lower().isin(['nan', 'nat', 'none', 'n/a', '', 'null']),
       'city'] = 'Unspecified'

# Step 5 — title case real cities only
df['city'] = df['city'].apply(
    lambda x: x if x in ('Remote', 'Unspecified') else str(x).title()
)

print(f"\nTop 15 cities:\n{df['city'].value_counts().head(15).to_string()}")

# ══════════════════════════════════════════════════════════════
# 5. CLEAN SKILLS
# ══════════════════════════════════════════════════════════════
NOISE_SKILLS = {
    '', 'nan', 'none', 'n/a', 'other', '1', '0',
    'yes', 'no', 'true', 'false', 'null', 'na', 'not specified'
}

def clean_skills(val):
    if pd.isna(val) or str(val).strip() in ('', '[]', 'nan'):
        return []
    try:
        skills = ast.literal_eval(str(val))
    except:
        skills = re.split(r'[,;|]', str(val))
    cleaned = []
    for s in skills:
        s = str(s).strip().lower()
        s = re.sub(r'[^a-z0-9\s\+\#\.]', '', s).strip()
        if s and s not in NOISE_SKILLS and len(s) > 1:
            cleaned.append(s)
    return cleaned

df['skills'] = df['skills_raw'].apply(clean_skills)
df['skills_count'] = df['skills'].apply(len)

print(f"\nSkill stats:")
print(f"  Avg skills per posting : {df['skills_count'].mean():.1f}")
print(f"  Postings with 0 skills : {(df['skills_count'] == 0).sum():,}")
print(f"  Postings with 5+ skills: {(df['skills_count'] >= 5).sum():,}")

# Top 20 skills preview
from collections import Counter
all_skills = [s for sublist in df['skills'] for s in sublist]
top_skills = Counter(all_skills).most_common(20)
print(f"\nTop 20 skills preview:")
for skill, count in top_skills:
    print(f"  {skill:<25} {count:,}")

# ══════════════════════════════════════════════════════════════
# 6. CLEAN REMOTE FLAG
# ══════════════════════════════════════════════════════════════
df['remote'] = df['remote'].fillna(False)
df['remote'] = df['remote'].astype(str).str.lower().isin(['true', '1', 'yes'])
df.loc[df['city'] == 'Remote', 'remote'] = True

# ══════════════════════════════════════════════════════════════
# 7. CLEAN SCHEDULE TYPE
# ══════════════════════════════════════════════════════════════
schedule_map = {
    'full-time'  : 'Full-time',
    'fulltime'   : 'Full-time',
    'full time'  : 'Full-time',
    'part-time'  : 'Part-time',
    'parttime'   : 'Part-time',
    'part time'  : 'Part-time',
    'contract'   : 'Contract',
    'contractor' : 'Contract',
    'temporary'  : 'Contract',
    'temp'       : 'Contract',
    'internship' : 'Internship',
    'intern'     : 'Internship',
    'hybrid'     : 'Full-time',
    'on-site'    : 'Full-time',
    'onsite'     : 'Full-time',
}
df['schedule_type'] = (
    df['schedule_type']
    .astype(str).str.lower().str.strip()
    .map(schedule_map)
    .fillna('Unspecified')
)

# ══════════════════════════════════════════════════════════════
# 8. DROP ROWS WITH NO USEFUL DATA
# ══════════════════════════════════════════════════════════════
before = len(df)
df = df[df['job_title'].notna()]
df = df[~((df['skills_count'] == 0) & (df['salary_year_avg'].isna()))]
after = len(df)
print(f"\nRows dropped (no title + no skills/salary): {before - after:,}")

# ══════════════════════════════════════════════════════════════
# 9. FINAL COLUMN ORDER + SAVE
# ══════════════════════════════════════════════════════════════
final_cols = [
    'job_title', 'role', 'company', 'city', 'location', 'country',
    'salary_year_avg', 'salary_hour_avg', 'salary_rate',
    'remote', 'schedule_type',
    'posted_date', 'year', 'month',
    'skills', 'skills_count', 'source'
]
df = df[final_cols].reset_index(drop=True)

df.to_csv("data/processed/master_jobs_clean.csv", index=False)

print(f"\n========== FINAL CLEAN SUMMARY ==========")
print(f"  Final rows      : {len(df):,}")
print(f"  Final columns   : {len(df.columns)}")
print(f"  Salary coverage : {df['salary_year_avg'].notna().mean()*100:.1f}%")
print(f"  Remote %        : {df['remote'].mean()*100:.1f}%")
print(f"  Date range      : {df['posted_date'].min().date()} → "
      f"{df['posted_date'].max().date()}")
print(f"\n  Role distribution:")
print(df['role'].value_counts().to_string())
print(f"\n  Top 10 cities:")
print(df['city'].value_counts().head(10).to_string())
print(f"\n  Schedule type:")
print(df['schedule_type'].value_counts().to_string())
print(f"\n  Source distribution:")
print(df['source'].value_counts().to_string())
print(f"==========================================")
print("✅ Saved → data/processed/master_jobs_clean.csv")