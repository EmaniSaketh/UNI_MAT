# UNI_MAT

## Free SAP/ERP prototype integration

The backend includes a zero-cost SAP-style OData adapter. With no configuration,
it uses two local demo materials so the flow can be tested without SAP access.
Use the **Sync SAP/ERP** button in the frontend, or call:

```text
POST http://127.0.0.1:8000/api/erp/sync-sap
```

To connect a real SAP S/4HANA OData endpoint, set these environment variables
before starting FastAPI:

```powershell
$env:SAP_ERP_URL = "https://your-sap-host.example/sap/opu/odata/sap/API_PRODUCT_SRV/A_Product"
$env:SAP_ERP_TOKEN = "your-token"
python -m uvicorn main:app --reload --app-dir backend
```

The adapter accepts SAP OData v2 (`d.results`) and v4 (`value`) responses. It
expects product code and description fields, normalizes them, and adds imported
records to `/api/national-registry` with `SAP_ERP` provenance. For production,
replace the token approach with your SAP identity provider and keep credentials
in a secret store.

