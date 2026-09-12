import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.core.attribute_extractor import AttributeExtractor
from backend.core.embedding_engine import EmbeddingEngine
from backend.core.nlp_cleaner import MaterialCleaner


class HybridMatchingEngine:

    def __init__(self):
        print("Initializing Hybrid Matching Engine...")

        self.cleaner = MaterialCleaner()
        self.extractor = AttributeExtractor()
        self.embedding_engine = EmbeddingEngine()

    # ---------------------------------------------------------
    # GENERIC ATTRIBUTE COMPARISON
    # ---------------------------------------------------------

    def compare_attribute(self, value1, value2):
        if value1 is None or value2 is None:
            return 0.5

        return 1.0 if value1 == value2 else 0.0

    # ---------------------------------------------------------
    # TECHNICAL ATTRIBUTE COMPARISON
    # ---------------------------------------------------------

    def compare_technical_attributes(self, attributes1, attributes2):
        """
        Compare technical attributes.

        Specification-derived values have already been selected
        by AttributeExtractor.

        Returns:
            scores
            hard_mismatches
            mismatch_reasons
        """

        technical_fields = [
            ("diameter", "Diameter"),
            ("length", "Length"),
            ("nominal_size", "Nominal size"),
            ("thickness", "Thickness"),
            ("bearing_number", "Bearing number"),
            ("steel_grade", "Steel grade"),
            ("cable_size", "Cable size"),
            ("voltage", "Voltage"),
            ("valve_type", "Valve type"),
        ]

        scores = {}
        hard_mismatch = False
        mismatch_reasons = []

        for key, label in technical_fields:

            value1 = attributes1.get(key)
            value2 = attributes2.get(key)

            score = self.compare_attribute(value1, value2)

            scores[key] = score

            # Only call it a mismatch when BOTH values exist
            # and explicitly disagree.
            if (
                value1 is not None
                and value2 is not None
                and value1 != value2
            ):
                hard_mismatch = True

                mismatch_reasons.append(
                    f"{label} mismatch: {value1} vs {value2}"
                )

        return scores, hard_mismatch, mismatch_reasons

    # ---------------------------------------------------------
    # DIMENSION COMPARISON
    # ---------------------------------------------------------

    def compare_dimensions(self, attributes1, attributes2):
        """
        Compare the main physical dimensions.

        Uses authoritative dimensions selected by the
        AttributeExtractor.

        Returns:
            1.0 -> dimensions match
            0.0 -> dimensions mismatch
            None -> dimensions unavailable
        """

        dimension_fields = [
            "diameter",
            "length",
            "nominal_size",
            "thickness",
        ]

        scores = []

        for field in dimension_fields:

            value1 = attributes1.get(field)
            value2 = attributes2.get(field)

            if value1 is not None and value2 is not None:

                scores.append(
                    1.0 if value1 == value2 else 0.0
                )

        if not scores:
            return None

        return 0.0 if 0.0 in scores else 1.0

    # ---------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------

    @staticmethod
    def status(score):

        if score is None or score == 0.5:
            return "UNKNOWN"

        if score == 1.0:
            return "MATCH"

        return "MISMATCH"

    # ---------------------------------------------------------
    # CONFLICT INFORMATION
    # ---------------------------------------------------------

    def collect_conflicts(self, attributes, source_name):
        """
        Collect conflicts detected inside one material record.

        Example:

            description: M10 x 8
            specification: M10 x 50

        """

        conflicts = attributes.get("conflicts", [])

        formatted = []

        for conflict in conflicts:

            formatted.append(
                {
                    "source": source_name,
                    "attribute": conflict["attribute"],
                    "description_value": conflict["description_value"],
                    "specification_value": conflict["specification_value"],
                    "selected_value": conflict["selected_value"],
                }
            )

        return formatted

    # ---------------------------------------------------------
    # MAIN COMPARISON
    # ---------------------------------------------------------

    def compare(
        self,
        description1,
        description2,
        specification1=None,
        specification2=None,
    ):
        """
        Compare two material records.

        IMPORTANT:

        description and specification are kept separate.

        Specification has higher authority for technical
        attributes.
        """

        # -----------------------------------------------------
        # CLEAN TEXT
        # -----------------------------------------------------

        standardized_description1 = self.cleaner.clean_text(
            description1
        )

        standardized_description2 = self.cleaner.clean_text(
            description2
        )

        standardized_specification1 = (
            self.cleaner.clean_text(specification1)
            if specification1
            else None
        )

        standardized_specification2 = (
            self.cleaner.clean_text(specification2)
            if specification2
            else None
        )

        # -----------------------------------------------------
        # EXTRACT ATTRIBUTES
        # -----------------------------------------------------

        attributes1 = self.extractor.extract(
            standardized_description1,
            standardized_specification1,
        )

        attributes2 = self.extractor.extract(
            standardized_description2,
            standardized_specification2,
        )

        # -----------------------------------------------------
        # SEMANTIC SIMILARITY
        # -----------------------------------------------------

        # For semantic matching, combine the two sources.
        # Technical matching is NOT based on this combined text.
        semantic_text1 = standardized_description1

        if standardized_specification1:
            semantic_text1 += " " + standardized_specification1

        semantic_text2 = standardized_description2

        if standardized_specification2:
            semantic_text2 += " " + standardized_specification2

        embeddings = self.embedding_engine.generate_embeddings(
            [
                semantic_text1,
                semantic_text2,
            ]
        )

        semantic_score = self.embedding_engine.similarity(
            embeddings[0],
            embeddings[1],
        )

        semantic_score = max(
            0.0,
            min(1.0, semantic_score),
        )

        # -----------------------------------------------------
        # GENERAL ATTRIBUTES
        # -----------------------------------------------------

        product_score = self.compare_attribute(
            attributes1.get("product"),
            attributes2.get("product"),
        )

        material_score = self.compare_attribute(
            attributes1.get("material"),
            attributes2.get("material"),
        )

        shape_score = self.compare_attribute(
            attributes1.get("shape"),
            attributes2.get("shape"),
        )

        # -----------------------------------------------------
        # DIMENSIONS
        # -----------------------------------------------------

        dimension_score = self.compare_dimensions(
            attributes1,
            attributes2,
        )

        effective_dimension_score = (
            0.5
            if dimension_score is None
            else dimension_score
        )

        # -----------------------------------------------------
        # TECHNICAL ATTRIBUTES
        # -----------------------------------------------------

        technical_scores, technical_hard_mismatch, technical_reasons = (
            self.compare_technical_attributes(
                attributes1,
                attributes2,
            )
        )

        # -----------------------------------------------------
        # HYBRID SCORE
        # -----------------------------------------------------

        hybrid_score = (
            semantic_score * 0.30
            + product_score * 0.20
            + material_score * 0.15
            + effective_dimension_score * 0.20
            + shape_score * 0.10
            + 0.05
        )

        # -----------------------------------------------------
        # HARD MISMATCH DETECTION
        # -----------------------------------------------------

        hard_mismatch = technical_hard_mismatch
        mismatch_reasons = list(technical_reasons)

        # Product mismatch
        if (
            attributes1.get("product") is not None
            and attributes2.get("product") is not None
            and attributes1["product"] != attributes2["product"]
        ):
            hard_mismatch = True

            mismatch_reasons.append(
                f"Product type mismatch: "
                f"{attributes1['product']} vs "
                f"{attributes2['product']}"
            )

        # Material mismatch
        if (
            attributes1.get("material") is not None
            and attributes2.get("material") is not None
            and attributes1["material"] != attributes2["material"]
        ):
            hard_mismatch = True

            mismatch_reasons.append(
                f"Material mismatch: "
                f"{attributes1['material']} vs "
                f"{attributes2['material']}"
            )

        # Shape mismatch
        if (
            attributes1.get("shape") is not None
            and attributes2.get("shape") is not None
            and attributes1["shape"] != attributes2["shape"]
        ):
            hard_mismatch = True

            mismatch_reasons.append(
                f"Shape mismatch: "
                f"{attributes1['shape']} vs "
                f"{attributes2['shape']}"
            )

        # -----------------------------------------------------
        # HARD MISMATCH PENALTY
        # -----------------------------------------------------

        if hard_mismatch:
            hybrid_score *= 0.45

        # -----------------------------------------------------
        # CONFIDENCE
        # -----------------------------------------------------

        confidence = round(
            hybrid_score * 100,
            1,
        )

        # -----------------------------------------------------
        # RECOMMENDATION
        # -----------------------------------------------------

        if hard_mismatch:

            recommendation = (
                "REVIEW"
                if confidence >= 70
                else "DECLINE"
            )

        elif confidence >= 90:

            recommendation = "APPROVE"

        elif confidence >= 70:

            recommendation = "REVIEW"

        else:

            recommendation = "DECLINE"

        # -----------------------------------------------------
        # CONFLICTS
        # -----------------------------------------------------

        conflicts1 = self.collect_conflicts(
            attributes1,
            "material_1",
        )

        conflicts2 = self.collect_conflicts(
            attributes2,
            "material_2",
        )

        all_conflicts = conflicts1 + conflicts2

        # -----------------------------------------------------
        # RESULT
        # -----------------------------------------------------

        return {

            "confidence": confidence,

            "recommendation": recommendation,

            "semantic_similarity": round(
                semantic_score * 100,
                1,
            ),

            "attribute_scores": {

                "product": round(
                    product_score * 100,
                    1,
                ),

                "material": round(
                    material_score * 100,
                    1,
                ),

                "shape": round(
                    shape_score * 100,
                    1,
                ),

                "dimensions": round(
                    effective_dimension_score * 100,
                    1,
                ),

                "bearing_number": round(
                    technical_scores["bearing_number"] * 100,
                    1,
                ),

                "steel_grade": round(
                    technical_scores["steel_grade"] * 100,
                    1,
                ),

                "cable_size": round(
                    technical_scores["cable_size"] * 100,
                    1,
                ),

                "voltage": round(
                    technical_scores["voltage"] * 100,
                    1,
                ),

                "valve_type": round(
                    technical_scores["valve_type"] * 100,
                    1,
                ),
            },

            "verification": {

                "product": self.status(
                    product_score
                ),

                "material": self.status(
                    material_score
                ),

                "shape": self.status(
                    shape_score
                ),

                "dimensions": self.status(
                    dimension_score
                ),

                "bearing_number": self.status(
                    technical_scores["bearing_number"]
                ),

                "steel_grade": self.status(
                    technical_scores["steel_grade"]
                ),

                "cable_size": self.status(
                    technical_scores["cable_size"]
                ),

                "voltage": self.status(
                    technical_scores["voltage"]
                ),

                "valve_type": self.status(
                    technical_scores["valve_type"]
                ),
            },

            "attributes": {

                "material_1": attributes1.get(
                    "material"
                ),

                "material_2": attributes2.get(
                    "material"
                ),

                "product_1": attributes1.get(
                    "product"
                ),

                "product_2": attributes2.get(
                    "product"
                ),

                "shape_1": attributes1.get(
                    "shape"
                ),

                "shape_2": attributes2.get(
                    "shape"
                ),

                "diameter_1": attributes1.get(
                    "diameter"
                ),

                "diameter_2": attributes2.get(
                    "diameter"
                ),

                "length_1": attributes1.get(
                    "length"
                ),

                "length_2": attributes2.get(
                    "length"
                ),

                "nominal_size_1": attributes1.get(
                    "nominal_size"
                ),

                "nominal_size_2": attributes2.get(
                    "nominal_size"
                ),

                "thickness_1": attributes1.get(
                    "thickness"
                ),

                "thickness_2": attributes2.get(
                    "thickness"
                ),

                "bearing_number_1": attributes1.get(
                    "bearing_number"
                ),

                "bearing_number_2": attributes2.get(
                    "bearing_number"
                ),

                "steel_grade_1": attributes1.get(
                    "steel_grade"
                ),

                "steel_grade_2": attributes2.get(
                    "steel_grade"
                ),

                "cable_size_1": attributes1.get(
                    "cable_size"
                ),

                "cable_size_2": attributes2.get(
                    "cable_size"
                ),

                "voltage_1": attributes1.get(
                    "voltage"
                ),

                "voltage_2": attributes2.get(
                    "voltage"
                ),

                "valve_type_1": attributes1.get(
                    "valve_type"
                ),

                "valve_type_2": attributes2.get(
                    "valve_type"
                ),

                # Keep the original source-specific data
                "description_attributes_1": attributes1.get(
                    "description_attributes"
                ),

                "description_attributes_2": attributes2.get(
                    "description_attributes"
                ),

                "specification_attributes_1": attributes1.get(
                    "specification_attributes"
                ),

                "specification_attributes_2": attributes2.get(
                    "specification_attributes"
                ),
            },

            "conflicts": all_conflicts,

            "hard_mismatch": hard_mismatch,

            "mismatch_reasons": mismatch_reasons,
        }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    engine = HybridMatchingEngine()

    print("\nTEST 1 - SAME MATERIAL")

    result = engine.compare(
        "SS HEX BOLT M10 X 8 MM",
        "Stainless Steel Hexagonal Bolt 10x50mm",
        "M10 x 50 mm",
        "Diameter 10 mm, Length 50 mm",
    )

    print(
        f"Confidence: {result['confidence']}%"
    )

    print(
        f"Recommendation: {result['recommendation']}"
    )

    print(
        "Dimensions:",
        result["verification"]["dimensions"]
    )

    print(
        "Conflicts:",
        result["conflicts"]
    )

    print(
        "Mismatch reasons:",
        result["mismatch_reasons"]
    )

    print("\nTEST 2 - DIFFERENT LENGTH")

    result = engine.compare(
        "SS HEX BOLT M10 X 8 MM",
        "Stainless Steel Hexagonal Bolt 10x50mm",
        "M10 x 8 mm",
        "M10 x 50 mm",
    )

    print(
        f"Confidence: {result['confidence']}%"
    )

    print(
        f"Recommendation: {result['recommendation']}"
    )

    print(
        "Dimensions:",
        result["verification"]["dimensions"]
    )

    print(
        "Mismatch reasons:",
        result["mismatch_reasons"]
    )

    print("\nTEST 3 - DIFFERENT SHAPE")

    result = engine.compare(
        "SS Circle BOLT M10 X 8 MM",
        "Stainless Steel Hexagonal Bolt 10x50mm",
        "M10 x 50 mm",
        "M10 x 50 mm",
    )

    print(
        f"Confidence: {result['confidence']}%"
    )

    print(
        f"Recommendation: {result['recommendation']}"
    )

    print(
        "Mismatch reasons:",
        result["mismatch_reasons"]
    )