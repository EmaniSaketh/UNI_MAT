from pathlib import Path
import pandas as pd


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Data folder
DATA_DIR = PROJECT_ROOT / "data"

print("=" * 70)
print("UNI_MAT DATASET INSPECTION")
print("=" * 70)

print(f"Data folder: {DATA_DIR}")
print(f"Exists: {DATA_DIR.exists()}")

if not DATA_DIR.exists():
    raise FileNotFoundError(f"Data folder not found: {DATA_DIR}")


csv_files = sorted(DATA_DIR.glob("*.csv"))

print(f"\nCSV files found: {len(csv_files)}")

for file_path in csv_files:

    print("\n" + "=" * 70)
    print(f"FILE: {file_path.name}")
    print("=" * 70)

    df = pd.read_csv(file_path)

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    print("\nColumns:")
    for column in df.columns:
        print(f"  - {column}")

    print("\nFirst 3 rows:")
    print(df.head(3).to_string(index=False))