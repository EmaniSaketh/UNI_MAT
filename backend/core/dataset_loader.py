from pathlib import Path
import pandas as pd


class DatasetLoader:

    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.data_dir = self.project_root / "data"

    def load_alpha(self):
        path = self.data_dir / "cpse_alpha_100.csv"

        df = pd.read_csv(path)

        return pd.DataFrame({
            "source": "CPSE_ALPHA",
            "material_code": df["material_code"],
            "description": df["material_description"],
            "material_type": df["material_type"],
            "manufacturer": df["manufacturer"],
            "specification": df["specification"],
            "uom": df["uom"],
        })

    def load_beta(self):
        path = self.data_dir / "cpse_beta_100.csv"

        df = pd.read_csv(path)

        return pd.DataFrame({
            "source": "CPSE_BETA",
            "material_code": df["item_id"],
            "description": df["item_name"],
            "material_type": df["category"],
            "manufacturer": df["make"],
            "specification": df["technical_spec"],
            "uom": df["unit"],
        })

    def load_gamma(self):
        path = self.data_dir / "cpse_gamma_100.csv"

        df = pd.read_csv(path)

        return pd.DataFrame({
            "source": "CPSE_GAMMA",
            "material_code": df["legacy_code"],
            "description": df["description"],
            "material_type": df["material_group"],
            "manufacturer": df["vendor_name"],
            "specification": df["dimensions"],
            "uom": df["unit_of_measure"],
        })

    def load_ground_truth(self):
        path = self.data_dir / "cpse_ground_truth_100.csv"

        return pd.read_csv(path)

    def load_all(self):
        alpha = self.load_alpha()
        beta = self.load_beta()
        gamma = self.load_gamma()
        ground_truth = self.load_ground_truth()

        return alpha, beta, gamma, ground_truth


if __name__ == "__main__":

    loader = DatasetLoader()

    alpha = loader.load_alpha()
    beta = loader.load_beta()
    gamma = loader.load_gamma()
    ground_truth = loader.load_ground_truth()

    print("=" * 70)
    print("UNI_MAT DATASET LOADER")
    print("=" * 70)

    print(f"\nCPSE_ALPHA: {len(alpha)} records")
    print(f"CPSE_BETA : {len(beta)} records")
    print(f"CPSE_GAMMA: {len(gamma)} records")

    datasets = loader.load_all()

    print(f"\nTotal material records: {sum(len(dataset) for dataset in datasets[:3])}")
    print(f"Ground truth records: {len(ground_truth)}")

    print("\nUnified format:")
    print(datasets[0].head(5).to_string(index=False))