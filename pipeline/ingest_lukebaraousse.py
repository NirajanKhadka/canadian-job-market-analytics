from datasets import load_dataset
import pandas as pd
import os

os.makedirs("data/raw", exist_ok=True)

print("Downloading lukebarousse/data_jobs from HuggingFace...")
ds = load_dataset("lukebarousse/data_jobs", split="train")
df = ds.to_pandas()

print(f"Total rows (global): {len(df):,}")
print(f"Columns: {df.columns.tolist()}")
print(f"Sample countries: {df['job_country'].value_counts().head(10)}")

df.to_csv("data/raw/lukebarousse_raw.csv", index=False)
print(f"Saved → data/raw/lukebarousse_raw.csv")