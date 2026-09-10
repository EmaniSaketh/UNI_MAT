from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid

class SourceDetails(BaseModel):
    """Tracks exactly where the data came from."""
    cpse_id: str
    original_material_code: str
    erp_system: str = "CSV_Mock"

class RawData(BaseModel):
    """The untouched data exactly as the CPSE provided it."""
    description: str
    uom: str
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    specification: Optional[str] = None

class NormalizedData(BaseModel):
    """Cleaned data (lowercase, standard units, no weird spacing)."""
    description: str
    uom: str
    category: Optional[str] = None

class TechnicalAttributes(BaseModel):
    """Extracted parameters for exact technical matching."""
    material_type: Optional[str] = None
    dimensions: Dict[str, Any] = Field(default_factory=dict)
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)

class CanonicalMaterial(BaseModel):
    """The master JSON structure for UniMat AI."""
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: SourceDetails
    raw_data: RawData
    normalized_data: Optional[NormalizedData] = None
    technical_attributes: Optional[TechnicalAttributes] = None