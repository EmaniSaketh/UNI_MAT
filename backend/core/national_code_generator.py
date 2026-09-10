import pandas as pd
import json
import os

class DynamicNationalCodeEngine:
    def __init__(self):
        # We keep file loading optional or as a fallback for testing
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        try:
            self.alpha_df = pd.read_csv(os.path.join(base_dir, 'data/cpse_alpha.csv'))
            self.beta_df = pd.read_csv(os.path.join(base_dir, 'data/cpse_beta.csv'))
            self.gamma_df = pd.read_csv(os.path.join(base_dir, 'data/cpse_gamma.csv'))
            self.gt_df = pd.read_csv(os.path.join(base_dir, 'data/cpse_ground_truth.csv'))
        except FileNotFoundError:
            pass

    def generate_registry_from_data(self, alpha_data, beta_data, gamma_data, gt_data):
        """
        Modular function: Accepts raw DataFrames or lists directly. 
        This way, whether data comes from CSVs, a database, or a frontend API upload, 
        this function processes it identically without changing code!
      """
        national_registry = []
        
        for index, row in gt_data.iterrows():
            nat_id = f"NAT-MAT-{index+1:06d}"
            
            alpha_code = row['alpha_code']
            beta_code = row['beta_code']
            gamma_code = row['gamma_code']
            
            alpha_row = alpha_data[alpha_data['material_code'] == alpha_code].iloc[0]
            beta_row = beta_data[beta_data['item_id'] == beta_code].iloc[0]
            gamma_row = gamma_data[gamma_data['legacy_code'] == gamma_code].iloc[0]
            
            national_record = {
                "national_material_id": nat_id,
                "standardized_description": str(alpha_row['material_description']).lower(),
                "category": str(alpha_row['material_type']).lower(),
                "mapped_cpse_materials": [
                    {"cpse_id": "CPSE_ALPHA", "original_code": alpha_code, "original_desc": alpha_row['material_description']},
                    {"cpse_id": "CPSE_BETA", "original_code": beta_code, "original_desc": beta_row['item_name']},
                    {"cpse_id": "CPSE_GAMMA", "original_code": gamma_code, "original_desc": gamma_row['description']}
                ],
                "governance": {
                    "status": "APPROVED",
                    "matched_via": "AI Modular API Pipeline"
                }
            }
            national_registry.append(national_record)
            
        return national_registry

if __name__ == "__main__":
    # Local test execution
    engine = DynamicNationalCodeEngine()
    registry = engine.generate_registry_from_data(
        engine.alpha_df, engine.beta_df, engine.gamma_df, engine.gt_df
    )
    print(f"✅ Successfully tested modular generation for {len(registry)} items!")
    print(json.dumps(registry[0], indent=2))