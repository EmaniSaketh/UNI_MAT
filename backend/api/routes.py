from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
import io
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.core.national_code_generator import DynamicNationalCodeEngine

router = APIRouter()
engine = DynamicNationalCodeEngine()

@router.get("/api/national-registry")
def get_registry(limit: int = 40):
    registry_data = engine.generate_registry_from_data(
        engine.alpha_df, engine.beta_df, engine.gamma_df, engine.gt_df
    )
    return {
        "status": "success",
        "total_records": len(registry_data[:limit]),
        "data": registry_data[:limit]
    }

@router.get("/api/accuracy")
def get_accuracy_metrics():
    if engine.gt_df is None or engine.gt_df.empty:
        return {
            "status": "success",
            "total_evaluated": len(engine.alpha_df) if engine.alpha_df is not None else 0,
            "correct_matches": 0,
            "false_positives": 0,
            "accuracy_percentage": 0,
            "precision_percentage": 0
        }
        
    gt_df = engine.gt_df
    total = len(gt_df)
    registry = engine.generate_registry_from_data(
        engine.alpha_df, engine.beta_df, engine.gamma_df, engine.gt_df
    )
    
    correct = 0
    false_positives = 0
    
    for index, gt_row in gt_df.iterrows():
        alpha_code = gt_row['alpha_code']
        expected_beta = gt_row['beta_code']
        expected_gamma = gt_row['gamma_code']
        
        ai_record = next((item for item in registry if any(m['original_code'] == alpha_code for m in item['mapped_cpse_materials'])), None)
        
        if ai_record:
            ai_codes = [m['original_code'] for m in ai_record['mapped_cpse_materials']]
            if expected_beta in ai_codes and expected_gamma in ai_codes:
                correct += 1
            else:
                false_positives += 1
        else:
            false_positives += 1
            
    accuracy = (correct / total) * 100 if total > 0 else 0
    precision = (correct / (correct + false_positives)) * 100 if (correct + false_positives) > 0 else 0
    
    return {
        "status": "success",
        "total_evaluated": total,
        "correct_matches": correct,
        "false_positives": false_positives,
        "accuracy_percentage": round(accuracy, 2),
        "precision_percentage": round(precision, 2)
    }

@router.post("/api/upload-datasets")
async def upload_datasets(
    alpha_file: UploadFile = File(...),
    beta_file: UploadFile = File(...),
    gamma_file: UploadFile = File(...)
):
    try:
        engine.alpha_df = pd.read_csv(io.StringIO(str(await alpha_file.read(), 'utf-8')))
        engine.beta_df = pd.read_csv(io.StringIO(str(await beta_file.read(), 'utf-8')))
        engine.gamma_df = pd.read_csv(io.StringIO(str(await gamma_file.read(), 'utf-8')))
        engine.gt_df = pd.DataFrame() 
        return {"status": "success", "message": "Datasets loaded."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading files: {str(e)}")