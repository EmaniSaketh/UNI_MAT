import re


class AttributeExtractor:
    """
    Extract structured technical attributes from material descriptions
    and specifications.

    Important design rule:
        specification > description

    We preserve both sources so conflicting values are not lost.
    """

    MATERIAL_ALIASES = {
        "ss": "stainless steel",
        "stainless steel": "stainless steel",
        "ms": "mild steel",
        "mild steel": "mild steel",
        "cs": "carbon steel",
        "carbon steel": "carbon steel",
        "gi": "galvanized iron",
        "galvanized iron": "galvanized iron",
        "ci": "cast iron",
        "cast iron": "cast iron",
        "cu": "copper",
        "copper": "copper",
        "al": "aluminium",
        "alu": "aluminium",
        "aluminium": "aluminium",
        "aluminum": "aluminium",
        "brass": "brass",
        "plastic": "plastic",
        "rubber": "rubber",
    }

    PRODUCT_TYPES = [
        "bolt",
        "nut",
        "screw",
        "washer",
        "bearing",
        "gasket",
        "valve",
        "pipe",
        "flange",
        "bracket",
        "pump",
        "motor",
        "cable",
        "wire",
        "switch",
        "fitting",
        "coupling",
        "seal",
        "plate",
    ]

    VALVE_TYPES = [
        "gate",
        "butterfly",
        "ball",
        "check",
        "globe",
        "plug",
        "needle",
    ]

    def __init__(self):
        pass

    # ---------------------------------------------------------
    # BASIC NORMALIZATION
    # ---------------------------------------------------------

    def clean_text(self, text):
        if text is None:
            return ""

        text = str(text).lower()

        replacements = {
            "stainless-steel": "stainless steel",
            "mild-steel": "mild steel",
            "carbon-steel": "carbon steel",
            "galvanized-iron": "galvanized iron",
            "sq.mm": "sqmm",
            "sq. mm": "sqmm",
            "mm2": "sqmm",
            "mm²": "sqmm",
            "kv": "kv",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # Normalize multiplication symbols
        text = text.replace("×", "x")
        text = text.replace("*", "x")

        # Normalize repeated spaces
        text = re.sub(r"\s+", " ", text).strip()

        return text

    # ---------------------------------------------------------
    # PRODUCT
    # ---------------------------------------------------------

    def extract_product(self, text):
        text = self.clean_text(text)

        for product in self.PRODUCT_TYPES:
            if re.search(rf"\b{re.escape(product)}\b", text):
                return product

        # Common industrial abbreviations
        if re.search(r"\bbrg\b", text):
            return "bearing"

        return None

    # ---------------------------------------------------------
    # MATERIAL
    # ---------------------------------------------------------

    def extract_material(self, text):
        text = self.clean_text(text)

        # Longer expressions first
        material_patterns = [
            ("stainless steel", r"\bstainless\s+steel\b"),
            ("mild steel", r"\bmild\s+steel\b"),
            ("carbon steel", r"\bcarbon\s+steel\b"),
            ("galvanized iron", r"\bgalvanized\s+iron\b"),
            ("cast iron", r"\bcast\s+iron\b"),
            ("copper", r"\bcopper\b"),
            ("aluminium", r"\baluminium\b|\baluminum\b"),
            ("brass", r"\bbrass\b"),
            ("plastic", r"\bplastic\b"),
            ("rubber", r"\brubber\b"),
        ]

        for material, pattern in material_patterns:
            if re.search(pattern, text):
                return material

        # Abbreviations
        for alias, material in self.MATERIAL_ALIASES.items():
            if re.search(rf"\b{re.escape(alias)}\b", text):
                return material

        return None

    # ---------------------------------------------------------
    # SHAPE
    # ---------------------------------------------------------

    def extract_shape(self, text):
        text = self.clean_text(text)

        if re.search(r"\bhex\b|\bhexagonal\b", text):
            return "hexagonal"

        if re.search(r"\bcircle\b|\bcircular\b|\bround\b", text):
            return "circular"

        if re.search(r"\bsquare\b", text):
            return "square"

        if re.search(r"\bflat\b", text):
            return "flat"

        if re.search(r"\boval\b", text):
            return "oval"

        return None

    # ---------------------------------------------------------
    # BOLT / NUT METRIC SIZE
    # ---------------------------------------------------------

    def extract_metric_size(self, text):
        """
        Extract M10 x 50, M12x60, etc.

        Returns:
            {
                "diameter": 10,
                "length": 50
            }
        """

        text = self.clean_text(text)

        pattern = r"\bm\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)"

        match = re.search(pattern, text)

        if match:
            return {
                "diameter": float(match.group(1)),
                "length": float(match.group(2)),
            }

        # M10 without length
        match = re.search(r"\bm\s*(\d+(?:\.\d+)?)\b", text)

        if match:
            return {
                "diameter": float(match.group(1)),
                "length": None,
            }

        return None

    # ---------------------------------------------------------
    # GENERIC X DIMENSION
    # ---------------------------------------------------------

    def extract_x_dimension(self, text):
        """
        Extract dimensions such as:

            10 x 50 mm
            10x50mm
        """

        text = self.clean_text(text)

        pattern = (
            r"\b(\d+(?:\.\d+)?)\s*x\s*"
            r"(\d+(?:\.\d+)?)\s*mm\b"
        )

        match = re.search(pattern, text)

        if match:
            return {
                "diameter": float(match.group(1)),
                "length": float(match.group(2)),
            }

        return None

    # ---------------------------------------------------------
    # SINGLE DIMENSIONS
    # ---------------------------------------------------------

    def extract_diameter(self, text):
        text = self.clean_text(text)

        patterns = [
            r"\bdia(?:meter)?\s*[:=]?\s*(\d+(?:\.\d+)?)\s*mm",
            r"\bdiameter\s*[:=]?\s*(\d+(?:\.\d+)?)\s*mm",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                return float(match.group(1))

        return None

    def extract_nominal_size(self, text):
        text = self.clean_text(text)

        patterns = [
            r"\bdn\s*[:=]?\s*(\d+(?:\.\d+)?)",
            r"\bnb\s*[:=]?\s*(\d+(?:\.\d+)?)",
            r"\bnominal\s+size\s*[:=]?\s*(\d+(?:\.\d+)?)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                return float(match.group(1))

        return None

    def extract_thickness(self, text):
        text = self.clean_text(text)

        patterns = [
            r"\bthickness\s*[:=]?\s*(\d+(?:\.\d+)?)\s*mm",
            r"\bthk\s*[:=]?\s*(\d+(?:\.\d+)?)\s*mm",
            r"\bthick\s*[:=]?\s*(\d+(?:\.\d+)?)\s*mm",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                return float(match.group(1))

        return None

    # ---------------------------------------------------------
    # BEARING NUMBER
    # ---------------------------------------------------------

    def extract_bearing_number(self, text):
        text = self.clean_text(text)

        # Typical bearing numbers: 6204, 6205, 6206, 6212 etc.
        match = re.search(r"\b(6\d{3,4})\b", text)

        if match:
            return match.group(1)

        return None

    # ---------------------------------------------------------
    # STEEL GRADE
    # ---------------------------------------------------------

    def extract_steel_grade(self, text):
        text = self.clean_text(text)

        # SS304 / SS 304 / SS-304
        match = re.search(
            r"\b(?:ss|stainless\s+steel)[\s-]*(304|316)\b",
            text,
        )

        if match:
            return f"SS{match.group(1)}"

        # Grade 304 / Grade 316
        match = re.search(
            r"\bgrade\s*[:=]?\s*(304|316)\b",
            text,
        )

        if match:
            return f"SS{match.group(1)}"

        return None

    # ---------------------------------------------------------
    # CABLE SIZE
    # ---------------------------------------------------------

    def extract_cable_size(self, text):
        text = self.clean_text(text)

        patterns = [
            r"\b(\d+(?:\.\d+)?)\s*sqmm\b",
            r"\b(\d+(?:\.\d+)?)\s*sq\s*mm\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                return float(match.group(1))

        return None

    # ---------------------------------------------------------
    # VOLTAGE
    # ---------------------------------------------------------

    def extract_voltage(self, text):
        text = self.clean_text(text)

        # 1.1 KV / 1.1KV
        match = re.search(
            r"\b(\d+(?:\.\d+)?)\s*kv\b",
            text,
        )

        if match:
            return float(match.group(1)) * 1000

        # 1100 V / 1100V
        match = re.search(
            r"\b(\d+(?:\.\d+)?)\s*v\b",
            text,
        )

        if match:
            return float(match.group(1))

        return None

    # ---------------------------------------------------------
    # VALVE TYPE
    # ---------------------------------------------------------

    def extract_valve_type(self, text):
        text = self.clean_text(text)

        # Valve type should only be extracted from valve-related text.
        if not re.search(r"\bvalve\b", text):
            return None

        for valve_type in self.VALVE_TYPES:
            if re.search(rf"\b{valve_type}\b", text):
                return valve_type

        return None

    # ---------------------------------------------------------
    # DIMENSION EXTRACTION
    # ---------------------------------------------------------

    def extract_dimensions(self, text):
        """
        Extract all relevant technical dimensions from one source.

        This method does NOT decide whether the source is authoritative.
        """

        text = self.clean_text(text)

        dimensions = {
            "diameter": None,
            "length": None,
            "nominal_size": None,
            "thickness": None,
        }

        # First: M10 x 50
        metric = self.extract_metric_size(text)

        if metric:
            dimensions["diameter"] = metric["diameter"]
            dimensions["length"] = metric["length"]

        # Then: generic 10 x 50 mm
        if dimensions["diameter"] is None:
            generic = self.extract_x_dimension(text)

            if generic:
                dimensions["diameter"] = generic["diameter"]
                dimensions["length"] = generic["length"]

        # Explicit diameter
        diameter = self.extract_diameter(text)

        if diameter is not None:
            dimensions["diameter"] = diameter

        # DN / NB
        nominal_size = self.extract_nominal_size(text)

        if nominal_size is not None:
            dimensions["nominal_size"] = nominal_size

        # Thickness
        thickness = self.extract_thickness(text)

        if thickness is not None:
            dimensions["thickness"] = thickness

        return dimensions

    # ---------------------------------------------------------
    # FULL SOURCE EXTRACTION
    # ---------------------------------------------------------

    def extract_source(self, text):
        """
        Extract attributes from ONE source only.

        Example:
            description
            OR
            specification
        """

        text = self.clean_text(text)

        dimensions = self.extract_dimensions(text)

        return {
            "product": self.extract_product(text),
            "material": self.extract_material(text),
            "shape": self.extract_shape(text),

            "diameter": dimensions["diameter"],
            "length": dimensions["length"],
            "nominal_size": dimensions["nominal_size"],
            "thickness": dimensions["thickness"],

            "bearing_number": self.extract_bearing_number(text),
            "steel_grade": self.extract_steel_grade(text),
            "cable_size": self.extract_cable_size(text),
            "voltage": self.extract_voltage(text),
            "valve_type": self.extract_valve_type(text),
        }

    # ---------------------------------------------------------
    # MERGE DESCRIPTION + SPECIFICATION
    # ---------------------------------------------------------

    def extract(self, description, specification=None):
        """
        Extract attributes from description and specification separately.

        SPECIFICATION HAS HIGHER AUTHORITY FOR TECHNICAL ATTRIBUTES.

        Both sources are preserved.
        """

        description_attributes = self.extract_source(description)

        specification_attributes = self.extract_source(
            specification if specification else ""
        )

        # Start with description
        final = description_attributes.copy()

        # Technical attributes where specification wins
        technical_attributes = [
            "diameter",
            "length",
            "nominal_size",
            "thickness",
            "bearing_number",
            "steel_grade",
            "cable_size",
            "voltage",
            "valve_type",
        ]

        for attribute in technical_attributes:
            specification_value = specification_attributes.get(attribute)

            if specification_value is not None:
                final[attribute] = specification_value

        # For general semantic attributes:
        # specification can fill missing values,
        # but description remains preferred when available.
        general_attributes = [
            "product",
            "material",
            "shape",
        ]

        for attribute in general_attributes:
            if final.get(attribute) is None:
                final[attribute] = specification_attributes.get(attribute)

        # Detect conflicts
        conflicts = []

        for attribute in technical_attributes:
            description_value = description_attributes.get(attribute)
            specification_value = specification_attributes.get(attribute)

            if (
                description_value is not None
                and specification_value is not None
                and description_value != specification_value
            ):
                conflicts.append({
                    "attribute": attribute,
                    "description_value": description_value,
                    "specification_value": specification_value,
                    "selected_value": specification_value,
                })

        final["description_attributes"] = description_attributes
        final["specification_attributes"] = specification_attributes
        final["conflicts"] = conflicts

        return final


# ---------------------------------------------------------
# TESTS
# ---------------------------------------------------------

if __name__ == "__main__":

    extractor = AttributeExtractor()

    test_cases = [
        {
            "description": "SS HEX BOLT M10 X 8 MM",
            "specification": "M10 x 50 mm",
        },
        {
            "description": "Stainless Steel Hexagonal Bolt 10x50mm",
            "specification": "Diameter 10 mm, Length 50 mm",
        },
        {
            "description": "MS PIPE 50 MM",
            "specification": "Dia 50 mm",
        },
        {
            "description": "CS GATE VALVE 50 MM",
            "specification": "DN50",
        },
        {
            "description": "BALL BEARING 6205",
            "specification": "6205",
        },
        {
            "description": "CU CABLE 4 SQMM 1.1KV",
            "specification": "4 sq mm, 1.1 kV",
        },
        {
            "description": "SS PLATE 304 5 MM",
            "specification": "SS304, 5 mm",
        },
    ]

    for case in test_cases:

        result = extractor.extract(
            case["description"],
            case["specification"],
        )

        print("\n----------------------------------------")
        print("DESCRIPTION:")
        print(case["description"])

        print("SPECIFICATION:")
        print(case["specification"])

        print("\nDESCRIPTION ATTRIBUTES:")
        print(result["description_attributes"])

        print("\nSPECIFICATION ATTRIBUTES:")
        print(result["specification_attributes"])

        print("\nFINAL AUTHORITATIVE ATTRIBUTES:")
        print({
            key: value
            for key, value in result.items()
            if key not in [
                "description_attributes",
                "specification_attributes",
                "conflicts",
            ]
        })

        print("\nCONFLICTS:")
        print(result["conflicts"])