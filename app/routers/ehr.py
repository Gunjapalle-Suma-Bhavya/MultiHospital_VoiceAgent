"""
EHR Integration, 12-Step Core Sequence & Identifier Mapping Router.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.ehr.integration_layer import EHRIntegrationService
from app.ehr.adapters import EHRConnectorFactory

router = APIRouter(prefix="/api/v1/ehr", tags=["EHR Integration & 12-Step Sequence"])


class EHRSequenceInput(BaseModel):
    appointment_id: str

class EHROperationInput(BaseModel):
    hospital_id: str
    connector_type: str = "MOCK"  # MOCK, FHIR_R4, EPIC, CERNER
    operation_name: str  # patient_lookup, provider_lookup, facility_lookup, etc.
    arguments: Dict[str, Any] = {}


@router.post("/sequence/execute")
def execute_ehr_core_sequence(payload: EHRSequenceInput, db: Session = Depends(get_db)):
    svc = EHRIntegrationService(db)
    res = svc.execute_core_integration_sequence(payload.appointment_id)
    return res.model_dump()

@router.get("/mappings")
def get_ehr_mappings(hospital_id: str, entity_type: str, internal_id: str, db: Session = Depends(get_db)):
    svc = EHRIntegrationService(db)
    ext_id = svc.resolve_external_id(hospital_id=hospital_id, entity_type=entity_type, internal_id=internal_id)
    return {
        "hospital_id": hospital_id,
        "entity_type": entity_type,
        "internal_id": internal_id,
        "external_ehr_id": ext_id
    }

@router.post("/operations/execute")
def execute_ehr_operation(payload: EHROperationInput, db: Session = Depends(get_db)):
    connector = EHRConnectorFactory.get_connector(payload.connector_type)
    op = payload.operation_name.lower().strip()
    
    if hasattr(connector, op):
        method = getattr(connector, op)
        result = method(**payload.arguments)
        if hasattr(result, "model_dump"):
            return result.model_dump()
        return result
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported EHR operation '{op}' on connector '{payload.connector_type}'")
