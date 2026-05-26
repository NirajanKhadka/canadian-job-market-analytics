import kagglehub
import pandas as pd
import os
import shutil

os.makedirs("data/raw/techsalerator", exist_ok=True)
os.makedirs("data/raw/asaniczka", exist_ok=True)
os.makedirs("data/raw/elahehgolrokh", exist_ok=True)

# ── 1. techsalerator ──────────────────────────────────────────
print("Downloading techsalerator...")
path1 = kagglehub.dataset_download("techsalerator/job-posting-data-in-canada")
print(f"Cache path: {path1}")
print(f"Files: {os.listdir(path1)}")

# Copy files to your project's data/raw folder
for f in os.listdir(path1):
    shutil.copy(os.path.join(path1, f), f"data/raw/techsalerator/{f}")

# ── 2. asaniczka ──────────────────────────────────────────────
print("\nDownloading asaniczka...")
path2 = kagglehub.dataset_download("asaniczka/data-science-job-postings-and-skills")
print(f"Cache path: {path2}")
print(f"Files: {os.listdir(path2)}")

for f in os.listdir(path2):
    shutil.copy(os.path.join(path2, f), f"data/raw/asaniczka/{f}")

# ── 3. elahehgolrokh ──────────────────────────────────────────
print("\nDownloading elahehgolrokh...")
path3 = kagglehub.dataset_download("elahehgolrokh/data-science-job-postings-with-salaries-2025")
print(f"Cache path: {path3}")
print(f"Files: {os.listdir(path3)}")

for f in os.listdir(path3):
    shutil.copy(os.path.join(path3, f), f"data/raw/elahehgolrokh/{f}")

print("\n✅ All 3 Kaggle datasets downloaded and copied to data/raw/")

# ── Preview all 3 datasets ────────────────────────────────────

print("\n========== DATASET PREVIEWS ==========")

def safe_read(filepath, nrows=None):
    """Read CSV with automatic encoding fallback."""
    try:
        return pd.read_csv(filepath, nrows=nrows, encoding='utf-8')
    except UnicodeDecodeError:
        print(f"  ⚠️  UTF-8 failed, retrying with latin-1: {filepath}")
        return pd.read_csv(filepath, nrows=nrows, encoding='latin-1')


# techsalerator
t_files = os.listdir("data/raw/techsalerator")
print(f"\n[techsalerator] Files: {t_files}")
df_tech = safe_read(f"data/raw/techsalerator/{t_files[0]}")
print(f"Shape: {df_tech.shape}")
print(f"Columns: {df_tech.columns.tolist()}")
print(df_tech.head(2))

# asaniczka
a_files = os.listdir("data/raw/asaniczka")
print(f"\n[asaniczka] Files: {a_files}")
for f in a_files:
    df_a = safe_read(f"data/raw/asaniczka/{f}")
    print(f"  {f} → Shape: {df_a.shape} | Columns: {df_a.columns.tolist()}")

# elahehgolrokh
e_files = os.listdir("data/raw/elahehgolrokh")
print(f"\n[elahehgolrokh] Files: {e_files}")
df_ela = safe_read(f"data/raw/elahehgolrokh/{e_files[0]}")
print(f"Shape: {df_ela.shape}")
print(f"Columns: {df_ela.columns.tolist()}")
print(df_ela.head(2))