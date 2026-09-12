import re
import pandas as pd

from backend.core.attribute_extractor import AttributeExtractor
from backend.core.matching_engine import HybridMatchingEngine


class NationalCodeGenerator:

    def __init__(self):
        self.prefix = "NMC"

    @staticmethod
    def _format_number(value):
        value = float(value)

        if value.is_integer():
            return str(int(value))

        return str(value).replace(".", "P")

    def generate(self, attributes):
        product = attributes.get("product")
        material = attributes.get("material")
        shape = attributes.get("shape")
        diameter = attributes.get("diameter")
        length = attributes.get("length")
        nominal_size = attributes.get("nominal_size")
        thickness = attributes.get("thickness")
        steel_grade = attributes.get("steel_grade")
        cable_size = attributes.get("cable_size")
        voltage = attributes.get("voltage")
        bearing_number = attributes.get("bearing_number")
        valve_type = attributes.get("valve_type")

        parts = [self.prefix]

        material_map = {
            "stainless steel": "SS",
            "mild steel": "MS",
            "carbon steel": "CS",
            "cast iron": "CI",
            "galvanized iron": "GI",
            "aluminium": "AL",
            "copper": "CU",
            "brass": "BR",
            "plastic": "PL",
            "rubber": "RB",
        }

        shape_map = {
            "hexagonal": "HEX",
            "circular": "CIRC",
            "square": "SQ",
            "flat": "FLAT",
            "oval": "OVAL",
        }

        if material:
            parts.append(material_map.get(material, material.upper()))

        if product:
            parts.append(product.upper())

        if shape:
            parts.append(shape_map.get(shape, shape.upper()))

        if steel_grade:
            parts.append(f"G{steel_grade}")

        if bearing_number:
            parts.append(str(bearing_number))

        if cable_size is not None:
            parts.append(f"{self._format_number(cable_size)}SQMM")

        if voltage is not None:
            parts.append(f"{self._format_number(voltage)}V")

        if diameter is not None:
            parts.append(f"M{self._format_number(diameter)}")
        elif nominal_size is not None:
            parts.append(f"N{self._format_number(nominal_size)}")

        if length is not None:
            parts.append(self._format_number(length))

        if thickness is not None:
            parts.append(f"T{self._format_number(thickness)}")

        if valve_type:
            parts.append(valve_type.upper())

        return "-".join(parts)


class DynamicNationalCodeEngine:

    def __init__(self):
        self.generator = NationalCodeGenerator()
        self.extractor = AttributeExtractor()
        self.matcher = HybridMatchingEngine()

    def _standardized_attributes(self, description, specification=None):
        description = description or ""
        specification = specification or ""

        return self.extractor.extract(
            description,
            specification
        )

    def generate_registry_from_data(
        self,
        alpha_data: pd.DataFrame,
        beta_data: pd.DataFrame,
        gamma_data: pd.DataFrame,
        ground_truth: pd.DataFrame,
    ):
        """
        Build the national material registry from the supplied CPSE data.

        For the prototype dataset, ground_truth defines which Alpha,
        Beta and Gamma records belong to the same material.
        """

        def lookup(data, *keys):
            key = next((candidate for candidate in keys if candidate in data.columns), None)
            if key is None:
                raise ValueError(
                    f"Dataset is missing one of the required columns: {keys}"
                )
            return {
                str(row[key]): row
                for _, row in data.iterrows()
            }

        def value(row, *keys):
            for key in keys:
                if key in row.index:
                    return row.get(key, "")
            return ""

        # Create lookup dictionaries. Both raw adapter frames and the
        # normalized DatasetLoader frames are supported.
        alpha_lookup = {
            str(row["material_code"]): row
            for _, row in alpha_data.iterrows()
        }
        beta_lookup = lookup(beta_data, "item_id", "material_code")
        gamma_lookup = lookup(gamma_data, "legacy_code", "material_code")

        registry = []

        for _, gt in ground_truth.iterrows():

            alpha_code = str(gt["alpha_code"])
            beta_code = str(gt["beta_code"])
            gamma_code = str(gt["gamma_code"])

            alpha = alpha_lookup.get(alpha_code)
            beta = beta_lookup.get(beta_code)
            gamma = gamma_lookup.get(gamma_code)

            if alpha is None:
                continue

            # Alpha becomes the canonical base record
            description = str(value(alpha, "material_description", "description"))
            specification = str(value(alpha, "specification"))

            attributes = self._standardized_attributes(
                description,
                specification,
            )

            national_code = self.generator.generate(attributes)

            mapped_materials = []

            # Alpha
            mapped_materials.append({
                "source": "CPSE_ALPHA",
                "original_code": alpha_code,
                "description": description,
                "specification": specification,
                "manufacturer": str(value(alpha, "manufacturer")),
                "uom": str(value(alpha, "uom")),
            })

            # Beta
            if beta is not None:
                mapped_materials.append({
                    "source": "CPSE_BETA",
                    "original_code": beta_code,
                    "description": str(value(beta, "item_name", "description")),
                    "specification": str(value(beta, "technical_spec", "specification")),
                    "manufacturer": str(value(beta, "make", "manufacturer")),
                    "uom": str(value(beta, "unit", "uom")),
                })

            # Gamma
            if gamma is not None:
                mapped_materials.append({
                    "source": "CPSE_GAMMA",
                    "original_code": gamma_code,
                    "description": str(value(gamma, "description")),
                    "specification": str(value(gamma, "dimensions", "specification")),
                    "manufacturer": str(value(gamma, "vendor_name", "manufacturer")),
                    "uom": str(value(gamma, "unit_of_measure", "uom")),
                })

            registry.append({
                "national_material_id": national_code,
                "national_code": national_code,
                "description": description,
                "specification": specification,
                "attributes": attributes,
                "mapped_cpse_materials": mapped_materials,
                "governance": {
                    "status": "PENDING",
                    "remarks": "",
                },
            })

        return registry


if __name__ == "__main__":

    generator = NationalCodeGenerator()

    attributes = {
        "product": "bolt",
        "material": "stainless steel",
        "shape": "hexagonal",
        "diameter": 10,
        "length": 50,
    }

    print("\n" + "=" * 60)
    print("UNI_MAT NATIONAL MATERIAL CODE")
    print("=" * 60)
    print(
        "Generated Code :",
        generator.generate(attributes)
    )