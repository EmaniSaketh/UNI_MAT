"""Small SAP/ERP material adapter for the prototype.

The adapter accepts SAP OData-style payloads and normalizes them to the
shape used by the frontend. Without SAP_ERP_URL it uses local demo data.
"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEMO_SAP_MATERIALS = [
    {
        "Product": "SAP-MAT-8001",
        "ProductDescription": "Industrial Carbon Steel Gate Valve 2-inch",
        "ProductGroup": "VALV",
        "BaseUnit": "PC",
        "Plant": "1000",
    },
    {
        "Product": "SAP-MAT-8002",
        "ProductDescription": "Seamless High-Pressure Stainless Steel Pipe 4-meter",
        "ProductGroup": "PIPE",
        "BaseUnit": "M",
        "Plant": "1000",
    },
]


def _extract_materials(payload: dict) -> list[dict]:
    """Read both classic OData v2 (d.results) and OData v4 (value) responses."""
    if isinstance(payload.get("value"), list):
        return payload["value"]
    data = payload.get("d", {})
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        return data["results"]
    if isinstance(payload.get("results"), list):
        return payload["results"]
    raise ValueError("SAP response must contain an OData 'value' or 'd.results' list")


def _read_remote_payload(url: str, token: str | None) -> dict:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to read SAP ERP endpoint: {exc}") from exc


def fetch_sap_materials() -> list[dict]:
    """Fetch SAP materials from SAP_ERP_URL, or return local demo records."""
    url = os.getenv("SAP_ERP_URL")
    if not url:
        return DEMO_SAP_MATERIALS.copy()
    payload = _read_remote_payload(url, os.getenv("SAP_ERP_TOKEN"))
    return _extract_materials(payload)


def normalize_sap_materials(materials: list[dict]) -> list[dict]:
    """Map common SAP material fields to the app's ERP registry shape."""
    normalized = []
    for material in materials:
        product = material.get("Product") or material.get("Material") or material.get("product")
        description = (
            material.get("ProductDescription")
            or material.get("MaterialDescription")
            or material.get("description")
        )
        if not product or not description:
            raise ValueError("Each SAP material needs Product and ProductDescription fields")
        normalized.append(
            {
                "national_material_id": f"ERP-{product}",
                "standardized_description": str(description).lower(),
                "category": str(material.get("ProductGroup") or material.get("category") or "ERP"),
                "mapped_cpse_materials": [
                    {
                        "cpse_id": "SAP_ERP",
                        "original_code": str(product),
                        "original_desc": str(description),
                    }
                ],
                "governance": {
                    "status": "IMPORTED",
                    "matched_via": "SAP/ERP adapter",
                    "plant": material.get("Plant") or material.get("plant"),
                    "uom": material.get("BaseUnit") or material.get("unit"),
                },
            }
        )
    return normalized
