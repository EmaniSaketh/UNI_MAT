import re
import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..")
    )
)

from backend.core.canonical_schema import CanonicalMaterial, NormalizedData


class MaterialCleaner:

    def __init__(self):

        # -----------------------------
        # Units of Measurement
        # -----------------------------
        self.uom_mapping = {
            "pcs": "pieces",
            "pc": "pieces",
            "nos": "pieces",
            "no": "pieces",
            "numbers": "pieces",

            "mtr": "meter",
            "mtrs": "meter",
            "m": "meter",

            "mm": "millimeter",
            "millimetre": "millimeter",
            "millimetres": "millimeter",

            "cm": "centimeter",
            "centimetre": "centimeter",

            "m": "meter",

            "kg": "kilogram",
            "kgs": "kilogram",

            "g": "gram",
            "gm": "gram",
            "gms": "gram",

            "l": "liter",
            "ltr": "liter",
            "litre": "liter",
            "litres": "liter"
        }

        # -----------------------------
        # Industrial Abbreviations
        # -----------------------------
        self.term_mapping = {

            # Materials
            "ss": "stainless steel",
            "s.s": "stainless steel",

            "ms": "mild steel",
            "m.s": "mild steel",

            "cs": "carbon steel",
            "c.s": "carbon steel",

            "gi": "galvanized iron",
            "g.i": "galvanized iron",

            "ci": "cast iron",
            "c.i": "cast iron",

            "al": "aluminium",
            "alu": "aluminium",

            # Product terms
            "hex": "hexagonal",
            "hexg": "hexagonal",

            "dia": "diameter",
            "diam": "diameter",

            "assy": "assembly",

            "brg": "bearing",

            "bkt": "bracket",

            "gsk": "gasket",

            "thk": "thickness",

            # Common technical abbreviations
            "od": "outer diameter",
            "id": "inner diameter",

            "lg": "length",

            "wt": "weight"
        }

    # ==========================================================
    # TEXT CLEANING
    # ==========================================================

    def clean_text(self, text: str) -> str:

        if not text:
            return ""

        text = str(text).lower().strip()

        # Normalize multiplication signs
        text = text.replace("×", " x ")
        text = text.replace("*", " x ")

        # Normalize common separators
        text = text.replace("-", " ")
        text = text.replace("/", " ")

        # Remove punctuation but preserve decimal points
        text = re.sub(r'[^a-z0-9.\s]', ' ', text)

        # Remove dots only when they are abbreviation-style dots,
        # not decimal points.
        text = re.sub(r'(?<=[a-z])\.(?=[a-z])', '', text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    # ==========================================================
    # STANDARDIZE INDUSTRIAL TERMS
    # ==========================================================

    def standardize_terms(self, text: str) -> str:

        if not text:
            return ""

        words = text.split()

        standardized_words = []

        for word in words:

            replacement = self.term_mapping.get(word, word)

            standardized_words.append(replacement)

        return " ".join(standardized_words)

    # ==========================================================
    # NORMALIZE UNITS
    # ==========================================================

    def normalize_uom(self, uom: str) -> str:

        if not uom:
            return "unknown"

        clean_uom = str(uom).lower().strip()

        return self.uom_mapping.get(
            clean_uom,
            clean_uom
        )

    # ==========================================================
    # NORMALIZE DIMENSIONS
    # ==========================================================

    def normalize_dimensions(self, text: str) -> str:

        if not text:
            return ""

        # Normalize X between dimensions
        text = re.sub(
            r"(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)",
            r"\1 x \2",
            text
        )

        # Normalize number + MM
        text = re.sub(
            r"(\d+(?:\.\d+)?)\s*mm\b",
            r"\1 mm",
            text
        )

        # Normalize number + CM
        text = re.sub(
            r"(\d+(?:\.\d+)?)\s*cm\b",
            r"\1 cm",
            text
        )

        return text

    # ==========================================================
    # COMPLETE DESCRIPTION STANDARDIZATION
    # ==========================================================

    def standardize_description(self, text: str) -> str:

        if not text:
            return ""

        # Step 1: clean
        text = self.clean_text(text)

        # Step 2: standardize industrial terminology
        text = self.standardize_terms(text)

        # Step 3: normalize dimensions
        text = self.normalize_dimensions(text)

        # Step 4: clean spaces again
        text = re.sub(r"\s+", " ", text).strip()

        return text

    # ==========================================================
    # NORMALIZE COMPLETE MATERIAL
    # ==========================================================

    def normalize_material(
        self,
        material: CanonicalMaterial
    ) -> CanonicalMaterial:

        clean_desc = self.standardize_description(
            material.raw_data.description
        )

        clean_uom = self.normalize_uom(
            material.raw_data.uom
        )

        clean_cat = (
            self.standardize_description(
                material.raw_data.category
            )
            if material.raw_data.category
            else None
        )

        material.normalized_data = NormalizedData(
            description=clean_desc,
            uom=clean_uom,
            category=clean_cat
        )

        return material


# ==============================================================
# TEST
# ==============================================================

if __name__ == "__main__":

    cleaner = MaterialCleaner()

    test_descriptions = [

        "SS HEX BOLT M10 X 50 MM",

        "Stainless Steel Hexagonal Bolt 10x50mm",

        "HEX BOLT SS M10X50",

        "SS HEX BOLT M10 X 8 MM",

        "SS Circle BOLT M10 X 8 MM",

        "GI BRG ASSY 10 MM"
    ]

    print("\n--- MATERIAL STANDARDIZATION TEST ---")

    for description in test_descriptions:

        result = cleaner.standardize_description(
            description
        )

        print(f"\nRAW    : {description}")
        print(f"OUTPUT : {result}")