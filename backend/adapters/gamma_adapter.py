import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.core.canonical_schema import CanonicalMaterial, SourceDetails, RawData

def process_gamma_data(file_path: str):
    df = pd.read_csv(file_path)
    canonical_records = []

    for _, row in df.iterrows():
        source = SourceDetails(
            cpse_id="CPSE_GAMMA",
            original_material_code=str(row['legacy_code']),
            erp_system="CSV_Mock"
        )

        raw_data = RawData(
            description=str(row['description']),
            uom=str(row['unit_of_measure']),
            category=str(row['material_group']) if pd.notna(row['material_group']) else None,
            manufacturer=str(row['vendor_name']) if pd.notna(row['vendor_name']) else None,
            specification=str(row['dimensions']) if pd.notna(row['dimensions']) else None
        )

        material = CanonicalMaterial(source=source, raw_data=raw_data)
        canonical_records.append(material)

    return canonical_records

if __name__ == "__main__":
    records = process_gamma_data("data/cpse_gamma.csv")
    print(f"✅ Processed {len(records)} records from CPSE Gamma.")