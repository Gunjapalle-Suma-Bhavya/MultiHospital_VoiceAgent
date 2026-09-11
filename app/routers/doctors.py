"""
Doctor Management, Calendars, Availability Engine & Questionnaire Router.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date, time
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.doctors.doctor_management import DoctorManagementService, DoctorInviteInput, DoctorProfileUpdateInput
from app.admin.hospital_admin import HospitalAdminService, QuestionnaireCreateInput, QuestionnaireUpdateInput
from app.calendars.doctor_calendar import DoctorCalendarService, WorkingHourInput, BlockedSlotInput
from app.scheduling.availability_engine import AvailabilityEngine

router = APIRouter(prefix="/api/v1", tags=["Doctor Management & Calendars"])


@router.post("/hospitals/{hospital_id}/doctors/invite")
def invite_doctor(hospital_id: str, payload: DoctorInviteInput, db: Session = Depends(get_db)):
    doc_service = DoctorManagementService(db)
    try:
        doc = doc_service.invite_doctor(
            hospital_id=hospital_id,
            name=payload.name,
            specialty=payload.specialty,
            department=payload.department,
            qualifications=payload.qualifications,
            experience_years=payload.experience_years,
            languages=payload.languages,
            consultation_type=payload.consultation_type,
            default_appointment_duration=payload.default_appointment_duration,
            bio=payload.bio
        )
        try:
            from app.database.mongodb import persist_to_mongodb
            persist_to_mongodb("doctors", {
                "doctor_id": doc.id,
                "name": doc.name,
                "specialty": payload.specialty,
                "department": payload.department,
                "hospital_id": hospital_id,
                "status": doc.doctor_status.value,
                "bio": payload.bio,
                "experience_years": payload.experience_years
            }, key_field="doctor_id")
        except Exception:
            pass
        return {"doctor_id": doc.id, "name": doc.name, "status": doc.doctor_status.value}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/doctors/{doctor_id}/activate")
def activate_doctor(doctor_id: str, db: Session = Depends(get_db)):
    doc_service = DoctorManagementService(db)
    try:
        doc = doc_service.activate_doctor(doctor_id)
        try:
            from app.database.mongodb import persist_to_mongodb
            persist_to_mongodb("doctors", {
                "doctor_id": doc.id,
                "status": doc.doctor_status.value,
                "is_active": doc.is_active
            }, key_field="doctor_id")
        except Exception:
            pass
        return {"doctor_id": doc.id, "status": doc.doctor_status.value, "is_active": doc.is_active}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/doctors/{doctor_id}/deactivate")
def deactivate_doctor(doctor_id: str, db: Session = Depends(get_db)):
    doc_service = DoctorManagementService(db)
    try:
        doc = doc_service.deactivate_doctor(doctor_id)
        return {"doctor_id": doc.id, "status": doc.doctor_status.value, "is_active": doc.is_active}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/doctors/{doctor_id}/profile")
def update_doctor_profile(doctor_id: str, payload: DoctorProfileUpdateInput, db: Session = Depends(get_db)):
    doc_service = DoctorManagementService(db)
    try:
        doc = doc_service.update_doctor_profile(
            doctor_id=doctor_id,
            name=payload.name,
            specialty=payload.specialty,
            department=payload.department,
            qualifications=payload.qualifications,
            experience_years=payload.experience_years,
            languages=payload.languages,
            bio=payload.bio,
            special_instructions=payload.special_instructions
        )
        return {"doctor_id": doc.id, "profile_completed": doc.profile_completed}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/doctors/{doctor_id}")
def get_doctor_profile(doctor_id: str, db: Session = Depends(get_db)):
    doc_service = DoctorManagementService(db)
    prof = doc_service.get_doctor_profile(doctor_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return prof

@router.get("/hospitals/{hospital_id}/doctors")
def list_doctors_by_hospital(hospital_id: str, active_only: bool = True, db: Session = Depends(get_db)):
    doc_service = DoctorManagementService(db)
    return doc_service.list_doctors_by_hospital(hospital_id, active_only)

@router.post("/hospitals/{hospital_id}/questionnaires")
def create_hospital_questionnaire(hospital_id: str, payload: QuestionnaireCreateInput, db: Session = Depends(get_db)):
    admin_service = HospitalAdminService(db)
    q = admin_service.create_questionnaire(
        hospital_id=hospital_id,
        title=payload.title,
        specialty=payload.specialty,
        questions_json=payload.questions_json
    )
    return {"questionnaire_id": q.id, "hospital_id": q.hospital_id, "title": q.title}

@router.get("/doctors/{doctor_id}/availability")
def get_doctor_availability(doctor_id: str, target_date: str, db: Session = Depends(get_db)):
    avail_engine = AvailabilityEngine(db)
    try:
        target_d = date.fromisoformat(target_date)
        slots = avail_engine.get_available_slots(doctor_id, target_d)
        return {"doctor_id": doctor_id, "target_date": target_date, "available_slots": [s.model_dump() for s in slots]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
