"""
Doctor Calendar Management Service (Section 5.5).

Doctors can configure and view multiple calendar-based scheduling interfaces:
- Hospital consultation
- Online consultation
- Follow-up consultation
- Specialty-specific consultation

Aggregated calendar view displays:
- Working hours
- Lunch & break periods
- Blocked periods & Leave
- Booked appointments
- Available slots
"""

from datetime import datetime, date, time, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.database.models import (
    Doctor, DoctorCalendar, CalendarType, DoctorWorkingHour, BlockedSlot, Appointment, AppointmentStatus
)


class DoctorCalendarService:
    """
    Service managing multi-calendar configurations and aggregated calendar views for doctors.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def create_doctor_calendar(
        self,
        doctor_id: str,
        calendar_name: str,
        calendar_type: CalendarType = CalendarType.HOSPITAL_CONSULTATION
    ) -> DoctorCalendar:
        doc = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise ValueError("Doctor not found")

        cal = DoctorCalendar(
            doctor_id=doctor_id,
            calendar_name=calendar_name,
            calendar_type=calendar_type,
            is_active=True
        )
        self.db.add(cal)
        self.db.commit()
        return cal

    def list_doctor_calendars(self, doctor_id: str) -> List[Dict[str, Any]]:
        doc = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise ValueError("Doctor not found")

        cals = self.db.query(DoctorCalendar).filter(DoctorCalendar.doctor_id == doctor_id).all()
        if not cals:
            # Create default hospital consultation calendar if none exists
            default_cal = self.create_doctor_calendar(doctor_id, "Default Hospital Calendar", CalendarType.HOSPITAL_CONSULTATION)
            cals = [default_cal]

        return [
            {
                "calendar_id": c.id,
                "doctor_id": c.doctor_id,
                "calendar_name": c.calendar_name,
                "calendar_type": c.calendar_type.value if c.calendar_type else None,
                "is_active": c.is_active
            }
            for c in cals
        ]

    def get_calendar_aggregated_view(
        self,
        doctor_id: str,
        target_date: date,
        calendar_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Returns aggregated calendar view displaying working hours, lunch, blocked periods, leave, booked appointments.
        """
        doc = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise ValueError("Doctor not found")

        day_of_week = target_date.weekday()
        wh = self.db.query(DoctorWorkingHour).filter(
            DoctorWorkingHour.doctor_id == doctor_id,
            DoctorWorkingHour.day_of_week == day_of_week
        ).first()

        working_hours_info = None
        lunch_info = None
        if wh:
            working_hours_info = {"start_time": wh.start_time.strftime("%H:%M"), "end_time": wh.end_time.strftime("%H:%M")}
            if wh.break_start and wh.break_end:
                lunch_info = {"break_start": wh.break_start.strftime("%H:%M"), "break_end": wh.break_end.strftime("%H:%M")}

        day_start = datetime.combine(target_date, time.min)
        day_end = datetime.combine(target_date, time.max)

        # Blocked slots & Leave
        blocked_query = self.db.query(BlockedSlot).filter(
            BlockedSlot.doctor_id == doctor_id,
            BlockedSlot.start_datetime <= day_end,
            BlockedSlot.end_datetime >= day_start
        ).all()

        blocked_periods = []
        for b in blocked_query:
            blocked_periods.append({
                "id": b.id,
                "start_datetime": b.start_datetime.isoformat(),
                "end_datetime": b.end_datetime.isoformat(),
                "reason": b.reason or "Unavailable"
            })

        # Booked appointments
        appts_query = self.db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.start_datetime <= day_end,
            Appointment.end_datetime >= day_start,
            Appointment.status.in_([
                AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED,
                AppointmentStatus.REQUESTED, AppointmentStatus.PENDING,
                AppointmentStatus.PENDING_EHR_VERIFICATION
            ])
        )
        if calendar_id:
            appts_query = appts_query.filter(Appointment.calendar_id == calendar_id)

        booked_appts = []
        for a in appts_query.all():
            booked_appts.append({
                "appointment_id": a.id,
                "patient_name": a.patient_name,
                "start_datetime": a.start_datetime.isoformat(),
                "end_datetime": a.end_datetime.isoformat(),
                "status": a.status.value if a.status else None
            })

        return {
            "doctor_id": doctor_id,
            "doctor_name": doc.name,
            "target_date": target_date.isoformat(),
            "calendar_id": calendar_id,
            "working_hours": working_hours_info,
            "lunch_break": lunch_info,
            "blocked_periods": blocked_periods,
            "booked_appointments": booked_appts
        }
