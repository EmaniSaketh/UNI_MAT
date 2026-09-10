from fastapi import FastAPI, APIRouter
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.core.national_code_generator import DynamicNationalCodeEngine

router = APIRouter()
engine = DynamicNationalCodeEngine()

@router.get("/api/national-registry")
def get_registry(limit: int = 40):
    """API endpoint that feeds the generated National Codes directly to a frontend or client."""
    registry_data = engine.generate_registry_from_data(
        engine.alpha_df, engine.beta_df, engine.gamma_df, engine.gt_df
    )
    return {
        "status": "success",
        "total_records": len(registry_data[:limit]),
        "data": registry_data[:limit]
    }