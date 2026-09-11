from io import BytesIO
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.adapters.sap_adapter import fetch_sap_materials, normalize_sap_materials
from backend.core.national_code_generator import DynamicNationalCodeEngine


router = APIRouter(prefix="/api")
_base_dir = Path(__file__).resolve().parents[2]
_engine = DynamicNationalCodeEngine()
_erp_registry: list[dict] = []


def _load_default_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return tuple(
        pd.read_csv(_base_dir / "data" / filename)
        for filename in (
            "cpse_alpha_100.csv",
            "cpse_beta_100.csv",
            "cpse_gamma_100.csv",
            "cpse_ground_truth_100.csv",
        )
    )


def _build_registry(
    alpha_data: pd.DataFrame,
    beta_data: pd.DataFrame,
    gamma_data: pd.DataFrame,
    ground_truth: pd.DataFrame,
) -> list[dict]:
    try:
        return _engine.generate_registry_from_data(
            alpha_data, beta_data, gamma_data, ground_truth
        )
    except (KeyError, IndexError) as exc:
        raise HTTPException(
            status_code=422,
            detail="The uploaded CSV files do not contain compatible material records.",
        ) from exc


_alpha_data, _beta_data, _gamma_data, _ground_truth = _load_default_data()
_registry = _build_registry(_alpha_data, _beta_data, _gamma_data, _ground_truth)


@router.get("/accuracy")
def get_accuracy() -> dict:
    correct_matches = 0
    for ground_truth_row in _ground_truth.itertuples(index=False):
        record = next(
            (
                item
                for item in _registry
                if any(
                    material["original_code"] == ground_truth_row.alpha_code
                    for material in item["mapped_cpse_materials"]
                )
            ),
            None,
        )
        if record and {
            ground_truth_row.beta_code,
            ground_truth_row.gamma_code,
        }.issubset(
            {material["original_code"] for material in record["mapped_cpse_materials"]}
        ):
            correct_matches += 1

    total_evaluated = len(_ground_truth)
    false_positives = total_evaluated - correct_matches
    accuracy = (correct_matches / total_evaluated * 100) if total_evaluated else 0.0
    precision_denominator = correct_matches + false_positives
    return {
        "status": "success",
        "total_evaluated": total_evaluated,
        "correct_matches": correct_matches,
        "false_positives": false_positives,
        "accuracy_percentage": round(accuracy, 2),
        "precision_percentage": round(
            correct_matches / precision_denominator * 100
            if precision_denominator
            else 0.0,
            2,
        ),
        "accuracy": round(accuracy, 2),
        "total_records": len(_registry),
    }

@router.patch("/national-registry/{national_id}/status")
def update_registry_status(national_id: str, status: str):
    global _registry
    status = status.upper()
    if status not in ["APPROVED", "DECLINED"]:
        raise HTTPException(status_code=400, detail="Invalid status.")

    found = False
    for item in _registry:
        if item.get("national_material_id") == national_id:
            if "governance" not in item:
                item["governance"] = {}
            item["governance"]["status"] = status
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="ID not found.")
    return {"status": "success", "national_material_id": national_id, "new_status": status}


@router.get("/erp/sap-materials")
def get_sap_materials() -> dict:
    """Return materials from SAP_ERP_URL, or the local demo ERP when unset."""
    try:
        materials = fetch_sap_materials()
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"status": "success", "source": "sap_odata", "data": materials}


@router.post("/erp/sync-sap")
def sync_sap_materials() -> dict:
    global _erp_registry
    try:
        _erp_registry = normalize_sap_materials(fetch_sap_materials())
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "status": "success",
        "message": f"Synchronized {len(_erp_registry)} SAP/ERP material records.",
        "records_processed": len(_erp_registry),
        "source": "sap_odata",
    }


@router.get("/national-registry")
def get_national_registry(limit: int = 100):
    limit = max(0, limit)
    combined_registry = _registry + _erp_registry
    return {
        "status": "success",
        "total_records": len(combined_registry[:limit]),
        "data": combined_registry[:limit],
    }


@router.post("/upload-datasets")
async def upload_datasets(
    alpha_file: Annotated[UploadFile, File(...)],
    beta_file: Annotated[UploadFile, File(...)],
    gamma_file: Annotated[UploadFile, File(...)],
) -> dict:
    """Process a matching set of CPSE CSV files and replace the registry."""
    global _alpha_data, _beta_data, _gamma_data, _ground_truth, _registry

    try:
        alpha_data = pd.read_csv(BytesIO(await alpha_file.read()))
        beta_data = pd.read_csv(BytesIO(await beta_file.read()))
        gamma_data = pd.read_csv(BytesIO(await gamma_file.read()))
        registry = _build_registry(
            alpha_data, beta_data, gamma_data, _ground_truth
        )
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        raise HTTPException(status_code=422, detail="Each upload must be a valid CSV file.") from exc

    _alpha_data = alpha_data
    _beta_data = beta_data
    _gamma_data = gamma_data
    _registry = registry
    return {"status": "success", "records_processed": len(registry)}