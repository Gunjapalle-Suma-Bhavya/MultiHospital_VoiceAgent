"""
Patient Profile, Self-Service, Appointments & Questionnaire Router.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.database.models import Appointment
from app.patients.patient_service import PatientSelfServiceService, PatientRegistrationInput, QuestionnaireSubmissionInput

router = APIRouter(prefix="/api/v1/patients", tags=["Patient Self-Service & Appointments"])


class PatientRescheduleInput(BaseModel):
    new_start_datetime: str

class PatientPreferenceInput(BaseModel):
    last_hospital_id: Optional[str] = None
    last_doctor_id: Optional[str] = None
    preferred_time_window: Optional[str] = None
    communication_preference: Optional[str] = None

class PatientLoginInput(BaseModel):
    phone_number: str
    full_name: Optional[str] = None
    email: Optional[str] = None

class BookAppointmentRequest(BaseModel):
    hospital_id: Optional[str] = None
    doctor_id: str
    patient_id: Optional[str] = None
    patient_name: str
    patient_phone: str
    patient_email: Optional[str] = None
    start_datetime: str
    notes: Optional[str] = None

appointments_router = APIRouter(prefix="/api/v1/appointments", tags=["Appointments Booking"])

def _execute_direct_booking(payload: BookAppointmentRequest, db: Session):
    from app.agent.actions import ActionExecutor, CreateAppointmentInput
    from app.database.models import Doctor, Hospital
    doc = db.query(Doctor).filter(Doctor.id == payload.doctor_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")
    hosp_id = payload.hospital_id or doc.hospital_id
    try:
        dt = datetime.fromisoformat(payload.start_datetime)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid start_datetime format (ISO expected)")

    executor = ActionExecutor(db)
    input_data = CreateAppointmentInput(
        hospital_id=hosp_id,
        doctor_id=payload.doctor_id,
        patient_id=payload.patient_id or f"PAT-{payload.patient_phone[-6:]}",
        patient_name=payload.patient_name,
        patient_phone=payload.patient_phone,
        patient_email=payload.patient_email,
        start_datetime=dt,
        session_id=f"BOOK-DIRECT-{payload.patient_phone}"
    )
    result = executor.create_appointment(input_data)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return {
        "status": "success",
        "message": result.message,
        "appointment_id": result.appointment_id,
        "audit_id": result.audit_id
    }

@appointments_router.post("/book")
def direct_book_appointment(payload: BookAppointmentRequest, db: Session = Depends(get_db)):
    return _execute_direct_booking(payload, db)

@router.post("/appointments/book")
def patient_book_appointment(payload: BookAppointmentRequest, db: Session = Depends(get_db)):
    return _execute_direct_booking(payload, db)


class DirectRescheduleInput(BaseModel):
    appointment_id: str
    new_start_datetime: str

class DirectCancelInput(BaseModel):
    appointment_id: str
    reason: Optional[str] = None

@appointments_router.post("/reschedule")
def direct_reschedule_appointment(payload: DirectRescheduleInput, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == payload.appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    service = PatientSelfServiceService(db)
    try:
        new_dt = datetime.fromisoformat(payload.new_start_datetime)
        return service.request_reschedule_self_service(appt.patient_id, appt.id, new_dt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@appointments_router.post("/cancel")
def direct_cancel_appointment(payload: DirectCancelInput, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == payload.appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    service = PatientSelfServiceService(db)
    try:
        return service.cancel_appointment_self_service(appt.patient_id, appt.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@appointments_router.get("")
@appointments_router.get("/")
def list_appointments(
    patient_id: Optional[str] = None,
    doctor_id: Optional[str] = None,
    hospital_id: Optional[str] = None,
    patient_phone: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns non-cancelled appointments across the network or filtered by patient, doctor, or hospital.
    Authoritatively synchronizes with doctor calendars and patient appointment views.
    """
    from app.database.models import Appointment, AppointmentStatus, Doctor, Hospital
    query = db.query(Appointment).filter(Appointment.status != AppointmentStatus.CANCELLED)

    if patient_id:
        cleaned_pid = patient_id.strip()
        possible_pids = {cleaned_pid}
        if cleaned_pid.startswith(" "):
            possible_pids.add("+" + cleaned_pid.lstrip())
        elif cleaned_pid.startswith("+"):
            possible_pids.add(cleaned_pid[1:])
        else:
            possible_pids.add("+" + cleaned_pid)
        query = query.filter(
            (Appointment.patient_id.in_(possible_pids)) |
            (Appointment.patient_phone.in_(possible_pids)) |
            (Appointment.patient_email.in_(possible_pids))
        )
    if patient_phone:
        cleaned_phone = patient_phone.strip()
        possible_phones = {cleaned_phone}
        if cleaned_phone.startswith(" "):
            possible_phones.add("+" + cleaned_phone.lstrip())
        elif cleaned_phone.startswith("+"):
            possible_phones.add(cleaned_phone[1:])
        else:
            possible_phones.add("+" + cleaned_phone)
        query = query.filter(Appointment.patient_phone.in_(possible_phones))
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if hospital_id:
        query = query.filter(Appointment.hospital_id == hospital_id)

    appts = query.order_by(Appointment.start_datetime.desc()).all()
    results = []
    for a in appts:
        doc = db.query(Doctor).filter(Doctor.id == a.doctor_id).first() if a.doctor_id else None
        hosp = db.query(Hospital).filter(Hospital.id == a.hospital_id).first() if a.hospital_id else None

        t_str = a.start_datetime.strftime("%I:%M %p") if a.start_datetime else "10:00 AM"
        d_str = a.start_datetime.strftime("%Y-%m-%d") if a.start_datetime else ""
        sched_str = a.start_datetime.strftime("%b %d, %Y at %I:%M %p") if a.start_datetime else "Today"

        from app.database.models import PatientIntakeRecord, PatientQuestionnaireResponse
        intake = db.query(PatientIntakeRecord).filter(PatientIntakeRecord.appointment_id == a.id).first()
        q_resp = db.query(PatientQuestionnaireResponse).filter(
            PatientQuestionnaireResponse.appointment_id == a.id
        ).order_by(PatientQuestionnaireResponse.submitted_at.desc()).first()

        intake_ans = {}
        if q_resp and q_resp.answers_json:
            try:
                intake_ans.update(json.loads(q_resp.answers_json))
            except Exception:
                pass
        if intake and intake.intake_answers_json:
            try:
                intake_ans.update(json.loads(intake.intake_answers_json))
            except Exception:
                pass

        results.append({
            "id": a.id,
            "appointment_id": a.id,
            "doctor_id": a.doctor_id,
            "doctor_name": doc.name if doc else "Specialist Doctor",
            "specialty": doc.specialty if doc else "General Medicine",
            "hospital_id": a.hospital_id,
            "hospital_name": hosp.name if hosp else "Affiliated Hospital",
            "patient_id": a.patient_id,
            "patient_name": a.patient_name or "Registered Patient",
            "patient_phone": a.patient_phone or "N/A",
            "start_datetime": a.start_datetime.isoformat() if a.start_datetime else None,
            "end_datetime": a.end_datetime.isoformat() if a.end_datetime else None,
            "time": t_str,
            "date": d_str,
            "slot_time": t_str,
            "scheduled_time": sched_str,
            "status": a.status.value if hasattr(a.status, "value") else str(a.status),
            "is_ehr_verified": bool(a.is_ehr_verified),
            "external_ehr_id": getattr(a, "external_ehr_id", None) or f"EHR-{a.id[:8] if a.id else 'SYNC'}",
            "is_booked": True,
            "complaint": getattr(a, "reason_for_visit", None) or (intake.patient_reported_summary if intake else (f"{doc.specialty} Consultation" if doc else "Medical Consultation")),
            "intake_answers": intake_ans,
            "intake_summary": intake.patient_reported_summary if intake else None
        })

    return {
        "status": "success",
        "total": len(results),
        "appointments": results
    }

@appointments_router.get("/{appointment_id}/ehr-trace")
@router.get("/appointments/{appointment_id}/ehr-trace")
def get_appointment_ehr_trace(appointment_id: str, db: Session = Depends(get_db)):
    """
    Returns the dynamic 5-step EHR integration lifecycle trace for this appointment.
    """
    from app.ehr.integration_layer import EHRIntegrationService
    svc = EHRIntegrationService(db)
    try:
        return svc.get_appointment_ehr_lifecycle(appointment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))



@router.post("/login")
def login_patient(payload: PatientLoginInput, db: Session = Depends(get_db)):
    import uuid
    service = PatientSelfServiceService(db)
    patient = service.register_or_update_patient(
        phone_number=payload.phone_number,
        full_name=payload.full_name or "Valued Patient",
        email=payload.email
    )
    token = f"agy-pat-token-{uuid.uuid4().hex[:16]}"
    return {
        "access_token": token,
        "token_type": "bearer",
        "patient_id": patient.id,
        "phone_number": patient.phone_number,
        "full_name": patient.full_name,
        "preferred_language": patient.preferred_language,
        "preferences": {
            "communication_preference": patient.communication_preference,
            "preferred_time_window": patient.preferred_time_window
        },
        "headers": {
            "X-User-Role": "PATIENT",
            "X-User-Id": patient.id,
            "X-Patient-Id": patient.id
        }
    }


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
    try:
        return service.view_appointments(patient_id)
    except Exception:
        from app.database.models import Appointment, AppointmentStatus, Doctor, Hospital
        appts = db.query(Appointment).filter(
            (Appointment.patient_id == patient_id) | (Appointment.patient_phone == patient_id),
            Appointment.status != AppointmentStatus.CANCELLED
        ).order_by(Appointment.start_datetime.desc()).all()
        results = []
        for a in appts:
            doc = db.query(Doctor).filter(Doctor.id == a.doctor_id).first() if a.doctor_id else None
            hosp = db.query(Hospital).filter(Hospital.id == a.hospital_id).first() if a.hospital_id else None
            t_str = a.start_datetime.strftime("%I:%M %p") if a.start_datetime else "10:00 AM"
            d_str = a.start_datetime.strftime("%Y-%m-%d") if a.start_datetime else ""
            sched_str = a.start_datetime.strftime("%b %d, %Y at %I:%M %p") if a.start_datetime else "Today"
            results.append({
                "appointment_id": a.id,
                "id": a.id,
                "hospital_id": a.hospital_id,
                "hospital_name": hosp.name if hosp else "Affiliated Hospital",
                "doctor_id": a.doctor_id,
                "doctor_name": doc.name if doc else "Specialist Doctor",
                "specialty": doc.specialty if doc else "General Medicine",
                "start_datetime": a.start_datetime.isoformat() if a.start_datetime else None,
                "end_datetime": a.end_datetime.isoformat() if a.end_datetime else None,
                "time": t_str,
                "date": d_str,
                "slot_time": t_str,
                "scheduled_time": sched_str,
                "status": a.status.value if hasattr(a.status, "value") else str(a.status),
                "external_status": a.external_status,
                "is_ehr_verified": bool(a.is_ehr_verified),
                "is_booked": True,
                "complaint": getattr(a, "reason_for_visit", None) or "Clinical Consultation"
            })
        return results

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

@router.get("/{patient_id}/questionnaires/responses")
def get_patient_questionnaires(patient_id: str, db: Session = Depends(get_db)):
    service = PatientSelfServiceService(db)
    return service.get_patient_questionnaire_responses(patient_id)


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


# Section 5.22 Verified Appointment Confirmation Endpoint
from app.appointments.confirmation_service import AppointmentConfirmationService

@router.get("/appointments/{appointment_id}/confirmation")
def get_verified_appointment_confirmation(appointment_id: str, db: Session = Depends(get_db)):
    svc = AppointmentConfirmationService(db)
    try:
        details = svc.get_appointment_confirmation(appointment_id)
        return details.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

