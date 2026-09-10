import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.core.canonical_schema import CanonicalMaterial, SourceDetails, RawData

def process_beta_data(file_path: str):
    df = pd.read_csv(file_path)
    canonical_records = []

    for _, row in df.iterrows():
        source = SourceDetails(
            cpse_id="CPSE_BETA",
            original_material_code=str(row['item_id']),
            erp_system="CSV_Mock"
        )

        raw_data = RawData(
            description=str(row['item_name']),
            uom=str(row['unit']),
            category=str(row['category']) if pd.notna(row['category']) else None,
            manufacturer=str(row['make']) if pd.notna(row['make']) else None,
            specification=str(row['technical_spec']) if pd.notna(row['technical_spec']) else None
        )

        material = CanonicalMaterial(source=source, raw_data=raw_data)
        canonical_records.append(material)

    return canonical_records

if __name__ == "__main__":
    records = process_beta_data("data/cpse_beta.csv")
    print(f"✅ Processed {len(records)} records from CPSE Beta.")