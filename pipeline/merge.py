import pandas as pd
import ast
import os

os.makedirs("data/processed", exist_ok=True)

# ── LOAD ALL 4 NORMALIZED FILES ───────────────────────────────
print("Loading normalized datasets...")
df1 = pd.read_csv("data/normalized/lukebarousse_norm.csv")
df2 = pd.read_csv("data/normalized/techsalerator_norm.csv")
df3 = pd.read_csv("data/normalized/asaniczka_norm.csv")
df4 = pd.read_csv("data/normalized/elahehgolrokh_norm.csv")

print(f"  lukebarousse : {len(df1):,}")
print(f"  techsalerator: {len(df2):,}")
print(f"  asaniczka    : {len(df3):,}")
print(f"  elahehgolrokh: {len(df4):,}")

# ── CONCAT ────────────────────────────────────────────────────
df_all = pd.concat([df1, df2, df3, df4], ignore_index=True)
print(f"\nTotal after concat : {len(df_all):,}")

# ── DEDUPLICATE ───────────────────────────────────────────────
# Normalize keys before comparison
df_all['_title_key']   = df_all['job_title'].str.lower().str.strip()
df_all['_company_key'] = df_all['company'].str.lower().str.strip()
df_all['_date_key']    = pd.to_datetime(df_all['posted_date'], errors='coerce').dt.date

before = len(df_all)
df_all.drop_duplicates(
    subset=['_title_key', '_company_key', '_date_key'],
    keep='first',
    inplace=True
)
after = len(df_all)
print(f"Duplicates removed : {before - after:,}")
print(f"Total after dedup  : {after:,}")

# Drop helper columns
df_all.drop(columns=['_title_key', '_company_key', '_date_key'], inplace=True)

# ── SOURCE DISTRIBUTION ───────────────────────────────────────
print("\nRows per source after dedup:")
print(df_all['source'].value_counts().to_string())

# ── SAVE ──────────────────────────────────────────────────────
df_all.to_csv("data/processed/master_jobs.csv", index=False)
print(f"\n✅ Saved → data/processed/master_jobs.csv")
print(f"   Shape : {df_all.shape}")
print(f"   Columns: {df_all.columns.tolist()}")