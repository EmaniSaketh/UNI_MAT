import re
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.core.canonical_schema import CanonicalMaterial, NormalizedData

class MaterialCleaner:
    def __init__(self):
        # Dictionary to standardize units of measure (UOM)
        self.uom_mapping = {
            'pcs': 'pieces',
            'nos': 'pieces',
            'numbers': 'pieces',
            'mtr': 'meter',
            'm': 'meter',
            'mm': 'millimeter',
            'kg': 'kilogram',
            'kgs': 'kilogram'
        }

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Convert to lowercase
        text = text.lower()
        # Remove special characters but keep spaces and alphanumeric
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def normalize_uom(self, uom: str) -> str:
        if not uom:
            return "unknown"
        clean_uom = uom.lower().strip()
        return self.uom_mapping.get(clean_uom, clean_uom)
    
    # Add explicit confidence or accuracy scores inside the mapped item payload
def compute_match_confidence(desc1, desc2):
    # Basic token overlap or vector similarity metric
    tokens1 = set(desc1.lower().split())
    tokens2 = set(desc2.lower().split())
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    similarity = len(intersection) / len(union) if union else 0.0
    return round(similarity * 100, 1)

    def normalize_material(self, material: CanonicalMaterial) -> CanonicalMaterial:
        """Takes a raw canonical record and fills in the normalized_data section."""
        clean_desc = self.clean_text(material.raw_data.description)
        clean_uom = self.normalize_uom(material.raw_data.uom)
        clean_cat = self.clean_text(material.raw_data.category) if material.raw_data.category else None

        material.normalized_data = NormalizedData(
            description=clean_desc,
            uom=clean_uom,
            category=clean_cat
        )
        return material

if __name__ == "__main__":
    from backend.adapters.alpha_adapter import process_alpha_data
    from backend.adapters.beta_adapter import process_beta_data
    
    cleaner = MaterialCleaner()
    
    # Load one record from Alpha and one from Beta using correct filenames and absolute path relative to project root
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    alpha_records = process_alpha_data(os.path.join(base_dir, "data", "cpse_alpha_100.csv"))
    beta_records = process_beta_data(os.path.join(base_dir, "data", "cpse_beta_100.csv"))
    
    test_records = [alpha_records[0], beta_records[0]]
    
    print("\n--- NORMALIZATION TEST ---")
    for rec in test_records:
        normalized_rec = cleaner.normalize_material(rec)
        print(f"\nCPSE Source: {normalized_rec.source.cpse_id}")
        print(f"RAW Description : {normalized_rec.raw_data.description}")
        print(f"CLEANED         : {normalized_rec.normalized_data.description}")
        print(f"RAW UOM         : {normalized_rec.raw_data.uom}  -->  CLEANED UOM: {normalized_rec.normalized_data.uom}")