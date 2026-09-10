"""
Patient Profile, Self-Service, Appointments & Questionnaire Router.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.patients.patient_service import PatientSelfServiceService, PatientRegistrationInput, QuestionnaireSubmissionInput

router = APIRouter(prefix="/api/v1/patients", tags=["Patient Self-Service & Appointments"])


class PatientRescheduleInput(BaseModel):
    new_start_datetime: str

class PatientPreferenceInput(BaseModel):
    last_hospital_id: Optional[str] = None
    last_doctor_id: Optional[str] = None
    preferred_time_window: Optional[str] = None
    communication_preference: Optional[str] = None


@router.post("/register")
def register_patient(payload: PatientRegistrationInput, db: Session = Depends(get_db)):
    service = PatientSelfServiceService(db)
    patient = service.register_or_update_patient(
        phone_number=payload.phone_number,
        full_name=payload.name,
        email=payload.email,
        date_of_birth=payload.date_of_birth,
        preferred_language=payload.preferred_language,
        external_patient_id=payload.external_patient_id
    )
    return {"patient_id": patient.id, "phone_number": patient.phone_number, "name": patient.full_name}

@router.get("/{patient_id}")
def get_patient_profile(patient_id: str, db: Session = Depends(get_db)):
    service = PatientSelfServiceService(db)
    prof = service.get_patient_profile(patient_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return prof

@router.get("/{patient_id}/appointments")
def view_patient_appointments(patient_id: str, db: Session = Depends(get_db)):
    service = PatientSelfServiceService(db)
    return service.view_appointments(patient_id)

@router.post("/{patient_id}/appointments/{appointment_id}/cancel")
def cancel_patient_appointment(patient_id: str, appointment_id: str, db: Session = Depends(get_db)):
    service = PatientSelfServiceService(db)
    try:
        return service.cancel_appointment_self_service(patient_id, appointment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{patient_id}/appointments/{appointment_id}/reschedule")
def reschedule_patient_appointment(patient_id: str, appointment_id: str, payload: PatientRescheduleInput, db: Session = Depends(get_db)):
    service = PatientSelfServiceService(db)
    try:
        new_dt = datetime.fromisoformat(payload.new_start_datetime)
        return service.request_reschedule_self_service(patient_id, appointment_id, new_dt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{patient_id}/questionnaires/submit")
def submit_questionnaire(patient_id: str, payload: QuestionnaireSubmissionInput, db: Session = Depends(get_db)):
    service = PatientSelfServiceService(db)
    try:
        resp = service.submit_questionnaire(
            patient_id=patient_id,
            questionnaire_id=payload.questionnaire_id,
            answers=payload.answers,
            appointment_id=payload.appointment_id
        )
        return {"response_id": resp.id, "patient_id": resp.patient_id, "submitted_at": resp.submitted_at.isoformat()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{patient_id}/preferences")
def update_patient_preferences(patient_id: str, payload: PatientPreferenceInput, db: Session = Depends(get_db)):
    service = PatientSelfServiceService(db)
    try:
        return service.manage_communication_preferences(
            patient_id=patient_id,
            communication_preference=payload.communication_preference,
            preferred_time_window=payload.preferred_time_window
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
