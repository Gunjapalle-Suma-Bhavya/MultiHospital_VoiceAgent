"""
Doctor Dashboard REST API Router (Section 5.31).
"""

from datetime import date
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dashboard.dashboard_service import DoctorDashboardService


router = APIRouter(prefix="/api/v1/doctor-dashboard", tags=["Doctor Dashboard"])


class CreateLeaveInput(BaseModel):
    start_date: date
    end_date: date
    leave_type: str = "ANNUAL_LEAVE"
    reason: Optional[str] = None


@router.get("/{doctor_id}/home")
def get_doctor_home_summary(doctor_id: str, db: Session = Depends(get_db)):
    """
    Returns Doctor Home Overview telemetry: today's appointments, upcoming appointments, pending questionnaires, and completed questionnaires.
    """
    service = DoctorDashboardService(db)
    try:
        return service.get_home_summary(doctor_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{doctor_id}/calendar")
def get_doctor_calendar_view(
    doctor_id: str,
    view_type: str = Query("DAY", pattern="^(DAY|WEEK|MONTH)$"),
    target_date: Optional[str] = Query(None),
    calendar_ids: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns Doctor Calendar Inspector across Day, Week, and Month views, multiple calendars, booked slots, available slots, blocked slots, and leave records.
    """
    service = DoctorDashboardService(db)
    try:
        return service.get_calendar_view(
            doctor_id=doctor_id,
            view_type=view_type,
            target_date_str=target_date,
            calendar_ids=calendar_ids
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{doctor_id}/appointments/{appointment_id}")
def get_appointment_details(doctor_id: str, appointment_id: str, db: Session = Depends(get_db)):
    """
    Returns 360-Degree Appointment Details: patient, appointment, hospital, pre-visit questionnaire, relevant authorized context, and external EHR reference.
    """
    service = DoctorDashboardService(db)
    try:
        return service.get_appointment_details(doctor_id, appointment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{doctor_id}/appointments")
def get_doctor_all_appointments(doctor_id: str, db: Session = Depends(get_db)):
    """
    Returns all scheduled, confirmed, and active appointments for this doctor across all dates.
    """
    from app.database.models import Appointment, AppointmentStatus, Doctor
    doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Doctor '{doctor_id}' not found.")

    appts = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status != AppointmentStatus.CANCELLED
    ).order_by(Appointment.start_datetime.desc()).all()

    formatted = []
    for a in appts:
        t_str = a.start_datetime.strftime("%I:%M %p") if a.start_datetime else "10:00 AM"
        d_str = a.start_datetime.strftime("%Y-%m-%d") if a.start_datetime else ""
        formatted.append({
            "id": a.id,
            "appointment_id": a.id,
            "doctor_id": a.doctor_id,
            "doctor_name": doc.name,
            "patient_name": a.patient_name,
            "patient_phone": a.patient_phone,
            "patient_email": a.patient_email,
            "start_datetime": a.start_datetime.isoformat() if a.start_datetime else None,
            "end_datetime": a.end_datetime.isoformat() if a.end_datetime else None,
            "time": t_str,
            "date": d_str,
            "slot_time": t_str,
            "complaint": getattr(a, 'reason_for_visit', None) or f"{doc.specialty} Consultation & Clinical Intake",
            "status": a.status.value if hasattr(a.status, 'value') else str(a.status),
            "is_ehr_verified": bool(a.is_ehr_verified)
        })

    return {
        "status": "success",
        "doctor_id": doctor_id,
        "doctor_name": doc.name,
        "total_appointments": len(formatted),
        "appointments": formatted
    }


@router.post("/{doctor_id}/leaves")
def create_doctor_leave(doctor_id: str, payload: CreateLeaveInput, db: Session = Depends(get_db)):
    """
    Submits a doctor leave request and updates calendar slot availability.
    """
    service = DoctorDashboardService(db)
    try:
        leave = service.create_doctor_leave(
            doctor_id=doctor_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            leave_type=payload.leave_type,
            reason=payload.reason
        )
        leave_data = {
            "leave_id": leave.id,
            "doctor_id": leave.doctor_id,
            "start_date": leave.start_date.isoformat(),
            "end_date": leave.end_date.isoformat(),
            "leave_type": leave.leave_type,
            "reason": leave.reason,
            "status": leave.status
        }
        try:
            from app.database.mongodb import persist_to_mongodb
            persist_to_mongodb("leaves", leave_data, key_field="leave_id")
        except Exception:
            pass

        return {
            "success": True,
            "leave_id": leave.id,
            "doctor_id": leave.doctor_id,
            "start_date": leave.start_date.isoformat(),
            "end_date": leave.end_date.isoformat(),
            "leave_type": leave.leave_type,
            "status": leave.status
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{doctor_id}/leaves")
def get_doctor_leaves(doctor_id: str, db: Session = Depends(get_db)):
    """
    Queries recorded leaves for a doctor.
    """
    service = DoctorDashboardService(db)
    leaves = service.get_doctor_leaves(doctor_id)
    return {
        "doctor_id": doctor_id,
        "leaves_count": len(leaves),
        "leaves": [
            {
                "id": l.id,
                "start_date": l.start_date.isoformat(),
                "end_date": l.end_date.isoformat(),
                "leave_type": l.leave_type,
                "reason": l.reason,
                "status": l.status
            }
            for l in leaves
        ]
    }
