import os
import sys
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(__file__)
        )
    )
)

from backend.core.dataset_loader import DatasetLoader
from backend.core.matching_engine import HybridMatchingEngine
from backend.core.attribute_extractor import AttributeExtractor


class DatasetEvaluator:

    def __init__(self):
        self.engine = HybridMatchingEngine()
        self.extractor = AttributeExtractor()

    def get_record(self, df, code):
        result = df[df["material_code"] == code]

        if result.empty:
            return None

        return result.iloc[0]

    def get_pairwise_ground_truth(
    self,
    relationship,
    alpha_row,
    beta_row,
    gamma_row,
):
        """
    Convert the three-way ground truth into pairwise labels.

    same_material:
        Alpha-Beta  = MATCH
        Alpha-Gamma = MATCH
        Beta-Gamma  = MATCH

    different_*:
        The dataset contains one variant in Alpha and the
        corresponding variant in Beta + Gamma.

        Therefore:
        Alpha-Beta  = NON-MATCH
        Alpha-Gamma = NON-MATCH
        Beta-Gamma  = MATCH

    Returns:
        Dictionary containing pairwise ground-truth labels.
    """

        if relationship == "same_material":
            return {
                "AB": 1,
                "AG": 1,
                "BG": 1,
            }

        if relationship.startswith("different_"):
            return {
                "AB": 0,
                "AG": 0,
                "BG": 1,
            }

        raise ValueError(
            f"Unknown ground-truth relationship: {relationship}"
        )

    def extract_attribute_pair(
        self,
        attribute,
        relationship,
        alpha_row,
        beta_row,
        gamma_row,
    ):
        """Return the pair sharing a known extracted attribute."""

        def extract_value(row):
            attributes = self.extractor.extract(
                row["description"],
                row["specification"],
            )
            return attributes.get(attribute)

        values = {
            "A": extract_value(alpha_row),
            "B": extract_value(beta_row),
            "G": extract_value(gamma_row),
        }

        pairs = {
            "AB": (values["A"], values["B"]),
            "AG": (values["A"], values["G"]),
            "BG": (values["B"], values["G"]),
        }

        positive_pair = next(
            (
                pair_name
                for pair_name, (value1, value2) in pairs.items()
                if value1 is not None and value2 is not None and value1 == value2
            ),
            None,
        )

        if positive_pair is None:
            raise ValueError(
                f"Could not determine pairwise ground truth for "
                f"{relationship}: {values}"
            )

        return {
            pair: 1 if pair == positive_pair else 0
            for pair in pairs
        }

    def compare_pair(
        self,
        pair_name,
        row1,
        row2,
    ):
        result = self.engine.compare(
            row1["description"],
            row2["description"],
            row1["specification"],
            row2["specification"],
        )

        return {
            "pair": pair_name,
            "code1": row1["material_code"],
            "code2": row2["material_code"],
            "prediction": result["recommendation"],
            "confidence": result["confidence"],
            "semantic_similarity": result["semantic_similarity"],
            "hard_mismatch": result["hard_mismatch"],
            "mismatch_reasons": result["mismatch_reasons"],
        }

    def evaluate(self):

        print("\n" + "=" * 70)
        print("UNI_MAT DATASET EVALUATION")
        print("=" * 70)

        loader = DatasetLoader()
        alpha, beta, gamma, ground_truth = loader.load_all()

        results = []

        for _, gt_row in ground_truth.iterrows():

            alpha_row = self.get_record(
                alpha,
                gt_row["alpha_code"],
            )

            beta_row = self.get_record(
                beta,
                gt_row["beta_code"],
            )

            gamma_row = self.get_record(
                gamma,
                gt_row["gamma_code"],
            )

            if (
                alpha_row is None
                or beta_row is None
                or gamma_row is None
            ):
                print(
                    f"Skipping missing record: "
                    f"{gt_row['alpha_code']}, "
                    f"{gt_row['beta_code']}, "
                    f"{gt_row['gamma_code']}"
                )
                continue

            relationship = gt_row["relationship"]

            pairwise_truth = self.get_pairwise_ground_truth(
                relationship,
                alpha_row,
                beta_row,
                gamma_row,
            )

            comparisons = [
                (
                    "AB",
                    alpha_row,
                    beta_row,
                ),
                (
                    "AG",
                    alpha_row,
                    gamma_row,
                ),
                (
                    "BG",
                    beta_row,
                    gamma_row,
                ),
            ]

            for pair_name, row1, row2 in comparisons:

                prediction = self.compare_pair(
                    pair_name,
                    row1,
                    row2,
                )

                prediction["ground_truth"] = pairwise_truth[pair_name]

                # APPROVE = positive prediction
                # REVIEW / DECLINE = negative prediction
                prediction["predicted_match"] = (
                    1
                    if prediction["prediction"] == "APPROVE"
                    else 0
                )

                results.append(prediction)

        results_df = pd.DataFrame(results)

        self.print_report(results_df)

        # Save detailed results
        output_path = os.path.join(
            os.path.dirname(__file__),
            "evaluation_results.csv",
        )

        results_df.to_csv(
            output_path,
            index=False,
        )

        print(
            f"\nDetailed results saved to:\n"
            f"{output_path}"
        )

        return results_df

    def print_report(self, df):

        y_true = df["ground_truth"]
        y_pred = df["predicted_match"]

        precision = precision_score(
            y_true,
            y_pred,
            zero_division=0,
        )

        recall = recall_score(
            y_true,
            y_pred,
            zero_division=0,
        )

        f1 = f1_score(
            y_true,
            y_pred,
            zero_division=0,
        )

        total = len(df)

        actual_matches = int(
            (df["ground_truth"] == 1).sum()
        )

        actual_non_matches = int(
            (df["ground_truth"] == 0).sum()
        )

        approvals = int(
            (df["prediction"] == "APPROVE").sum()
        )

        reviews = int(
            (df["prediction"] == "REVIEW").sum()
        )

        declines = int(
            (df["prediction"] == "DECLINE").sum()
        )

        false_approvals = int(
            (
                (df["ground_truth"] == 0)
                & (df["prediction"] == "APPROVE")
            ).sum()
        )

        false_declines = int(
            (
                (df["ground_truth"] == 1)
                & (df["prediction"] == "DECLINE")
            ).sum()
        )

        unresolved_matches = int(
            (
                (df["ground_truth"] == 1)
                & (df["prediction"] == "REVIEW")
            ).sum()
        )

        review_rate = reviews / total * 100

        print("\n" + "-" * 70)
        print("DATASET SUMMARY")
        print("-" * 70)

        print(f"Total pairwise comparisons : {total}")
        print(f"Actual matches              : {actual_matches}")
        print(f"Actual non-matches          : {actual_non_matches}")

        print("\n" + "-" * 70)
        print("MODEL DECISIONS")
        print("-" * 70)

        print(f"APPROVE                     : {approvals}")
        print(f"REVIEW                      : {reviews}")
        print(f"DECLINE                     : {declines}")
        print(f"Review rate                 : {review_rate:.2f}%")

        print("\n" + "-" * 70)
        print("ML METRICS")
        print("-" * 70)

        print(f"Precision                   : {precision * 100:.2f}%")
        print(f"Recall                      : {recall * 100:.2f}%")
        print(f"F1 Score                    : {f1 * 100:.2f}%")

        print("\n" + "-" * 70)
        print("ERROR ANALYSIS")
        print("-" * 70)

        print(f"False approvals             : {false_approvals}")
        print(f"False declines              : {false_declines}")
        print(
            f"Matching pairs sent to review : "
            f"{unresolved_matches}"
        )

        print("\n" + "=" * 70)
        print("IMPORTANT")
        print("=" * 70)

        print(
            "APPROVE is treated as an automatic positive prediction."
        )

        print(
            "REVIEW is treated as unresolved rather than automatically "
            "counted as a wrong prediction."
        )

        print(
            "Confidence score is NOT model accuracy."
        )

        print("=" * 70)


if __name__ == "__main__":
    evaluator = DatasetEvaluator()
    evaluator.evaluate()