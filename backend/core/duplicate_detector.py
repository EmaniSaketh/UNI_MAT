import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.core.matching_engine import HybridMatchingEngine


class DuplicateDetector:

    def __init__(self):
        self.engine = HybridMatchingEngine()

    def detect(self, records, threshold=70.0):
        """
        Group records that represent the same material.

        records:
        [
            {
                "source": "CPSE_ALPHA",
                "material_code": "ALP-001",
                "description": "...",
                "specification": "..."
            }
        ]
        """

        groups = []
        assigned = set()

        for i, record in enumerate(records):

            if i in assigned:
                continue

            group = [record]
            assigned.add(i)

            for j in range(i + 1, len(records)):

                if j in assigned:
                    continue

                candidate = records[j]

                result = self.engine.compare(
                    record.get("description", ""),
                    candidate.get("description", ""),
                    record.get("specification", ""),
                    candidate.get("specification", ""),
                )

                confidence = result["confidence"]
                decision = result["recommendation"]

                if decision == "APPROVE" and confidence >= threshold:
                    group.append(candidate)
                    assigned.add(j)

            groups.append(group)

        return groups

# -------------------------------------------------------------
# TEST
# -------------------------------------------------------------

if __name__ == "__main__":
    records = [
        {
            "source": "CPSE_ALPHA",
            "material_code": "ALP-001",
            "description": "SS HEX BOLT M10 X 8 MM",
            "specification": "M10 x 50 mm",
        },
        {
            "source": "CPSE_BETA",
            "material_code": "BET-4501",
            "description": "Stainless Steel Hexagonal Bolt 10x50mm",
            "specification": "Diameter 10 mm, Length 50 mm",
        },
        {
            "source": "CPSE_GAMMA",
            "material_code": "GAM-882",
            "description": "HEX BOLT SS M10X50",
            "specification": "M10 x 50 mm",
        },
    ]

    detector = DuplicateDetector()
    groups = detector.detect(records)

    print("\n" + "=" * 60)
    print("UNI_MAT DUPLICATE DETECTION")
    print("=" * 60)

    for index, group in enumerate(groups, 1):

        print(f"\nGROUP {index}")

        for item in group:
            print(
                f"{item['source']:12} "
                f"{item['material_code']:10} "
                f"{item['description']}"
            )