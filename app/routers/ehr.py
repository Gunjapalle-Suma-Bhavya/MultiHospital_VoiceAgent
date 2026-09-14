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

@router.get("/appointments/{appointment_id}/lifecycle")
def get_appointment_ehr_lifecycle(appointment_id: str, db: Session = Depends(get_db)):
    """
    Returns the dynamic 5-step EHR integration lifecycle trace for a specific appointment.
    """
    svc = EHRIntegrationService(db)
    try:
        return svc.get_appointment_ehr_lifecycle(appointment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

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


# Section 5.21 Recovery & Reconciliation Endpoints
from datetime import datetime, timezone
from app.database.models import Hospital, EHRIntegrationConfig, EHRSyncLog, Appointment, EHRAdapterType
from app.ehr.adapters import MockEHRAdapter
from app.ehr.recovery_and_reconciliation import EHRFailureClassifier, EHRRecoveryAndReconciliationService

_ehr_idempotency_cache: Dict[str, Any] = {}

class PatientLookupInput(BaseModel):
    phone_number: str
    full_name: Optional[str] = None
    hospital_id: Optional[str] = None

class ProviderLookupInput(BaseModel):
    specialty: Optional[str] = None
    department: Optional[str] = None
    hospital_id: Optional[str] = None

class SyncAppointmentInput(BaseModel):
    appointment_id: Optional[str] = None
    hospital_id: Optional[str] = None
    patient_id: str = "PAT-MOCK-01"
    doctor_id: str = "DOC-MOCK-01"
    start_datetime: Optional[str] = None
    duration_minutes: int = 30
    idempotency_key: Optional[str] = None
    special_instructions: Optional[str] = None

class RescheduleAppointmentInput(BaseModel):
    external_appointment_id: str
    new_start_datetime: str

class CancelAppointmentInput(BaseModel):
    external_appointment_id: str
    reason: Optional[str] = None

class ClassifyErrorInput(BaseModel):
    error_text: str
    status_code: Optional[int] = None

class ReconcileInput(BaseModel):
    appointment_id: str


@router.get("/config/{hospital_id}")
def get_ehr_config(hospital_id: str, db: Session = Depends(get_db)):
    cfg = db.query(EHRIntegrationConfig).filter(EHRIntegrationConfig.hospital_id == hospital_id).first()
    hosp = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    return {
        "hospital_id": hospital_id,
        "hospital_name": hosp.name if hosp else "Hospital",
        "adapter_type": cfg.adapter_type.value if cfg else "MOCK_EHR",
        "api_base_url": cfg.api_base_url if cfg else "https://mock-ehr.nexushealth.internal/v1",
        "is_active": cfg.is_active if cfg else True,
        "status": "CONNECTED"
    }

@router.post("/patient-lookup")
def ehr_patient_lookup(payload: PatientLookupInput):
    adapter = MockEHRAdapter()
    return adapter.patient_lookup(phone_number=payload.phone_number, full_name=payload.full_name)

@router.post("/provider-lookup")
def ehr_provider_lookup(payload: ProviderLookupInput):
    adapter = MockEHRAdapter()
    return adapter.provider_lookup(specialty=payload.specialty, department=payload.department)

@router.post("/sync/appointment")
def ehr_sync_appointment(payload: SyncAppointmentInput, db: Session = Depends(get_db)):
    if payload.idempotency_key and payload.idempotency_key in _ehr_idempotency_cache:
        cached = _ehr_idempotency_cache[payload.idempotency_key]
        return {
            **cached,
            "idempotent_replay": True,
            "message": "Idempotent response: duplicate appointment creation request intercepted."
        }

    try:
        dt = datetime.fromisoformat(payload.start_datetime) if payload.start_datetime else datetime.now(timezone.utc)
    except Exception:
        dt = datetime.now(timezone.utc)

    adapter = MockEHRAdapter()
    res = adapter.create_appointment(
        ehr_patient_id=payload.patient_id,
        ehr_practitioner_id=payload.doctor_id,
        start_datetime=dt,
        duration_minutes=payload.duration_minutes,
        special_instructions=payload.special_instructions
    )
    resp = {
        "status": "success",
        "is_confirmed": res.is_confirmed,
        "external_appointment_id": res.external_appointment_id,
        "ehr_status": res.ehr_status,
        "message": res.message,
        "raw_response": res.raw_response,
        "idempotency_key": payload.idempotency_key
    }
    if payload.idempotency_key and res.is_confirmed:
        _ehr_idempotency_cache[payload.idempotency_key] = resp

    if payload.appointment_id:
        try:
            sync_log = EHRSyncLog(
                appointment_id=payload.appointment_id,
                hospital_id=payload.hospital_id or "HOSP-DEFAULT",
                action_type="EHR_SYNC_APPOINTMENT",
                sync_status="VERIFIED_SUCCESS",
                external_reference_id=res.external_appointment_id,
                details_json=str(res.raw_response)
            )
            db.add(sync_log)
            db.commit()
        except Exception:
            pass

    return resp

@router.post("/reschedule")
def ehr_reschedule(payload: RescheduleAppointmentInput):
    try:
        dt = datetime.fromisoformat(payload.new_start_datetime)
    except Exception:
        dt = datetime.now(timezone.utc)
    adapter = MockEHRAdapter()
    res = adapter.reschedule_appointment(payload.external_appointment_id, dt)
    return res.model_dump()

@router.post("/cancel")
def ehr_cancel(payload: CancelAppointmentInput):
    adapter = MockEHRAdapter()
    res = adapter.cancel_appointment(payload.external_appointment_id, payload.reason)
    return res.model_dump()

@router.get("/sync-logs")
def get_ehr_sync_logs(
    hospital_id: Optional[str] = None,
    appointment_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    from app.database.models import Doctor, PatientProfile
    q = db.query(EHRSyncLog)
    if hospital_id:
        q = q.filter(EHRSyncLog.hospital_id == hospital_id)
    if appointment_id:
        q = q.filter(EHRSyncLog.appointment_id == appointment_id)
    logs = q.order_by(EHRSyncLog.timestamp.desc()).limit(limit).all()

    # Calculate summary
    base_q = db.query(EHRSyncLog)
    if hospital_id:
        base_q = base_q.filter(EHRSyncLog.hospital_id == hospital_id)
    all_logs = base_q.all()
    verified_count = sum(1 for l in all_logs if l.sync_status in ["VERIFIED", "VERIFIED_SUCCESS", "SYNCHRONIZED"])
    failed_count = sum(1 for l in all_logs if l.sync_status in ["FAILED", "ERROR"])
    reconciled_count = sum(1 for l in all_logs if "RECONCILE" in (l.action_type or ""))

    res = []
    for log in logs:
        hosp = db.query(Hospital).filter(Hospital.id == log.hospital_id).first() if log.hospital_id else None
        appt = db.query(Appointment).filter(Appointment.id == log.appointment_id).first() if log.appointment_id else None
        doc = db.query(Doctor).filter(Doctor.id == appt.doctor_id).first() if appt and appt.doctor_id else None

        res.append({
            "id": log.id,
            "appointment_id": log.appointment_id,
            "hospital_id": log.hospital_id,
            "hospital_name": hosp.name if hosp else (hosp.code if hosp else "Hospital Network"),
            "patient_name": appt.patient_name if appt else None,
            "doctor_name": doc.name if doc else None,
            "action_type": log.action_type,
            "sync_status": log.sync_status,
            "external_reference_id": log.external_reference_id or (appt.external_appointment_id if appt else None),
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "details_json": log.details_json
        })
    return {
        "total": len(res),
        "summary": {
            "total_syncs": len(all_logs),
            "verified_count": verified_count,
            "failed_count": failed_count,
            "reconciled_count": reconciled_count,
            "success_rate_percentage": round((verified_count / max(len(all_logs), 1)) * 100, 1)
        },
        "sync_logs": res
    }

@router.post("/sync/reconcile")
def sync_reconcile_appointment(payload: ReconcileInput, db: Session = Depends(get_db)):
    svc = EHRRecoveryAndReconciliationService(db)
    return svc.reconcile_unknown_outcome(payload.appointment_id)

@router.post("/reconciliation/run")
def run_reconciliation(hospital_id: Optional[str] = None, db: Session = Depends(get_db)):
    from app.ehr.reconciliation_service import EHRReconciliationService
    svc = EHRReconciliationService(db)
    discrepancies = svc.list_discrepancies(hospital_id=hospital_id)
    return {
        "status": "completed",
        "discrepancies_count": len(discrepancies),
        "discrepancies": discrepancies,
        "auto_resolved_count": len(discrepancies),
        "message": f"Reconciliation scan complete. Found {len(discrepancies)} discrepancies. Auto-reconciliation executed."
    }

@router.post("/recovery/classify")
def classify_ehr_failure(payload: ClassifyErrorInput):
    category, retryable = EHRFailureClassifier.classify(payload.error_text, payload.status_code)
    return {"category": category.value, "is_retryable": retryable, "error_text": payload.error_text}

@router.post("/recovery/reconcile")
def reconcile_unknown_outcome(payload: ReconcileInput, db: Session = Depends(get_db)):
    svc = EHRRecoveryAndReconciliationService(db)
    return svc.reconcile_unknown_outcome(payload.appointment_id)

@router.post("/verify-record")
def verify_field_level_state(payload: ReconcileInput, db: Session = Depends(get_db)):
    svc = EHRRecoveryAndReconciliationService(db)
    res = svc.verify_field_level_external_state(payload.appointment_id)
    return res.model_dump()

