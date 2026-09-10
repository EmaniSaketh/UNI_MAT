import pandas as pd
import sys
import os

# Ensure Python can find the backend module when running this script directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.core.canonical_schema import CanonicalMaterial, SourceDetails, RawData

def process_alpha_data(file_path: str):
    """Reads CPSE Alpha's CSV and maps it to the Canonical Schema."""
    df = pd.read_csv(file_path)
    canonical_records = []

    for _, row in df.iterrows():
        # Map CPSE Alpha's specific columns to our Source tracking
        source = SourceDetails(
            cpse_id="CPSE_ALPHA",
            original_material_code=str(row['material_code']),
            erp_system="CSV_Mock"
        )

        # Map CPSE Alpha's specific columns to our RawData model
        raw_data = RawData(
            description=str(row['material_description']),
            uom=str(row['uom']),
            category=str(row['material_type']) if pd.notna(row['material_type']) else None,
            manufacturer=str(row['manufacturer']) if pd.notna(row['manufacturer']) else None,
            specification=str(row['specification']) if pd.notna(row['specification']) else None
        )

        # Create the unified material record
        material = CanonicalMaterial(
            source=source,
            raw_data=raw_data
        )
        canonical_records.append(material)

    return canonical_records

if __name__ == "__main__":
    # Test the adapter locally
    file_path = "data/cpse_alpha.csv"
    
    try:
        records = process_alpha_data(file_path)
        print(f"✅ Successfully processed {len(records)} records from CPSE Alpha.")
        print("\nHere is a sample Canonical JSON record:")
        print(records[0].model_dump_json(indent=2))
    except Exception as e:
        print(f"❌ Error processing file: {e}")