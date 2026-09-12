from backend.core.dataset_loader import DatasetLoader
from backend.core.matching_engine import HybridMatchingEngine


def main():

    print("=" * 70)
    print("UNI_MAT DATASET MATCHING")
    print("=" * 70)

    # ---------------------------------------------------------
    # LOAD DATASETS
    # ---------------------------------------------------------

    loader = DatasetLoader()

    alpha = loader.load_alpha()
    beta = loader.load_beta()
    gamma = loader.load_gamma()
    ground_truth = loader.load_ground_truth()

    # ---------------------------------------------------------
    # INITIALIZE MATCHER
    # ---------------------------------------------------------

    engine = HybridMatchingEngine()

    print("\nDatasets loaded:")
    print(f"  Alpha: {len(alpha)}")
    print(f"  Beta : {len(beta)}")
    print(f"  Gamma: {len(gamma)}")
    print(f"  Ground truth: {len(ground_truth)}")

    print("\n" + "=" * 70)
    print("MATCHING GROUND-TRUTH MATERIALS")
    print("=" * 70)

    results = []

    # ---------------------------------------------------------
    # PROCESS EVERY GROUND-TRUTH RECORD
    # ---------------------------------------------------------

    for _, row in ground_truth.iterrows():

        alpha_code = row["alpha_code"]
        beta_code = row["beta_code"]
        gamma_code = row["gamma_code"]
        relationship = row["relationship"]

        # -----------------------------------------------------
        # FIND MATERIAL RECORDS
        # -----------------------------------------------------

        alpha_matches = alpha[
            alpha["material_code"] == alpha_code
        ]

        beta_matches = beta[
            beta["material_code"] == beta_code
        ]

        gamma_matches = gamma[
            gamma["material_code"] == gamma_code
        ]

        # -----------------------------------------------------
        # VALIDATE RECORD EXISTENCE
        # -----------------------------------------------------

        if (
            alpha_matches.empty
            or beta_matches.empty
            or gamma_matches.empty
        ):
            print(
                f"\nSKIPPED: "
                f"{alpha_code} <-> {beta_code} <-> {gamma_code}"
            )

            if alpha_matches.empty:
                print(f"  Missing Alpha record: {alpha_code}")

            if beta_matches.empty:
                print(f"  Missing Beta record: {beta_code}")

            if gamma_matches.empty:
                print(f"  Missing Gamma record: {gamma_code}")

            continue

        # -----------------------------------------------------
        # GET RECORDS
        # -----------------------------------------------------

        alpha_row = alpha_matches.iloc[0]
        beta_row = beta_matches.iloc[0]
        gamma_row = gamma_matches.iloc[0]

        # -----------------------------------------------------
        # IMPORTANT:
        #
        # DO NOT COMBINE DESCRIPTION + SPECIFICATION.
        #
        # They are passed separately so that the matching
        # engine can give technical authority to specification.
        # -----------------------------------------------------

        ab = engine.compare(
            alpha_row["description"],
            beta_row["description"],
            alpha_row["specification"],
            beta_row["specification"],
        )

        ag = engine.compare(
            alpha_row["description"],
            gamma_row["description"],
            alpha_row["specification"],
            gamma_row["specification"],
        )

        bg = engine.compare(
            beta_row["description"],
            gamma_row["description"],
            beta_row["specification"],
            gamma_row["specification"],
        )

        # -----------------------------------------------------
        # STORE RESULTS
        # -----------------------------------------------------

        results.append({
            "alpha_code": alpha_code,
            "beta_code": beta_code,
            "gamma_code": gamma_code,
            "relationship": relationship,

            "alpha_beta_confidence": ab["confidence"],
            "alpha_beta_recommendation": ab["recommendation"],

            "alpha_gamma_confidence": ag["confidence"],
            "alpha_gamma_recommendation": ag["recommendation"],

            "beta_gamma_confidence": bg["confidence"],
            "beta_gamma_recommendation": bg["recommendation"],
        })

        # -----------------------------------------------------
        # DISPLAY RESULTS
        # -----------------------------------------------------

        print(
            f"\n{alpha_code} <-> {beta_code} <-> {gamma_code}"
        )

        print(
            f"  Relationship   : {relationship}"
        )

        print(
            f"  Alpha <-> Beta   : "
            f"{ab['confidence']:.1f}% "
            f"({ab['recommendation']})"
        )

        print(
            f"  Alpha <-> Gamma  : "
            f"{ag['confidence']:.1f}% "
            f"({ag['recommendation']})"
        )

        print(
            f"  Beta <-> Gamma   : "
            f"{bg['confidence']:.1f}% "
            f"({bg['recommendation']})"
        )

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("DATASET MATCHING COMPLETE")
    print("=" * 70)

    print(
        f"\nProcessed records: {len(results)}"
    )

    print(
        f"Ground-truth records: {len(ground_truth)}"
    )

    if len(results) != len(ground_truth):
        print(
            "\nWARNING:"
            "\nNot all ground-truth records were processed."
        )
    else:
        print(
            "\nAll ground-truth records processed successfully."
        )


if __name__ == "__main__":
    main()