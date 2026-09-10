"""
Doctor Journey Engine (Section 4.2).

Executes the 10-step Doctor Lifecycle:
Doctor Created -> Complete Profile -> Configure Calendar -> Set Working Hours -> Set Availability ->
Block Lunch / Leave / Other Periods -> Create Approved Questions -> View Appointments ->
Review Pre-Visit Responses -> Review Relevant Patient Context
"""

from datetime import datetime, time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.database.models import (
    Doctor, DoctorWorkingHour, BlockedSlot, DoctorApprovedQuestion,
    Appointment, PatientIntakeRecord, PatientProfile
)
from app.vision.executive_summary import ProductVisionEngine


class DoctorJourneyEngine:
    """
    Executes and manages the complete Doctor Journey lifecycle.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.vision = ProductVisionEngine(db_session)

    def execute_full_doctor_journey(
        self,
        hospital_id: str,
        doctor_name: str,
        specialty: str,
        bio: str,
        special_instructions: str,
        approved_questions: List[str],
        blocked_leave_start: Optional[datetime] = None,
        blocked_leave_end: Optional[datetime] = None
    ) -> Dict[str, Any]:

        trace = []

        # 1. Doctor Created
        doc = Doctor(hospital_id=hospital_id, name=doctor_name, specialty=specialty)
        self.db.add(doc)
        self.db.flush()
        trace.append({"step": 1, "action": "Doctor Created", "doctor_id": doc.id})

        # 2. Complete Profile
        doc.bio = bio
        doc.special_instructions = special_instructions
        doc.profile_completed = True
        self.db.commit()
        trace.append({"step": 2, "action": "Complete Profile", "status": "PROFILE_COMPLETED"})

        # 3. Configure Calendar & 4. Set Working Hours & 5. Set Availability
        for day in [0, 1, 2, 3, 4]:
            wh = DoctorWorkingHour(
                doctor_id=doc.id,
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(17, 0),
                break_start=time(12, 30),
                break_end=time(13, 30)
            )
            self.db.add(wh)
        trace.append({"step": 3, "action": "Configure Calendar", "status": "CALENDAR_CONFIGURED"})
        trace.append({"step": 4, "action": "Set Working Hours", "schedule": "Mon-Fri 09:00-17:00"})
        trace.append({"step": 5, "action": "Set Availability", "lunch_break": "12:30-13:30"})

        # 6. Block Lunch / Leave / Other Periods
        if blocked_leave_start and blocked_leave_end:
            bs = BlockedSlot(
                doctor_id=doc.id,
                start_datetime=blocked_leave_start,
                end_datetime=blocked_leave_end,
                reason="Doctor Scheduled Leave"
            )
            self.db.add(bs)
            trace.append({"step": 6, "action": "Block Lunch / Leave", "leave": f"{blocked_leave_start} to {blocked_leave_end}"})
        else:
            trace.append({"step": 6, "action": "Block Lunch / Leave", "status": "LUNCH_BREAK_LOCKED"})

        # 7. Create Approved Questions
        for q_text in approved_questions:
            q = DoctorApprovedQuestion(doctor_id=doc.id, question_text=q_text)
            self.db.add(q)
        self.db.commit()
        trace.append({"step": 7, "action": "Create Approved Questions", "count": len(approved_questions)})

        # 8. View Appointments & 9. Review Pre-Visit Responses & 10. Review Relevant Patient Context
        dashboard = self.get_doctor_dashboard(doc.id)
        trace.append({"step": 8, "action": "View Appointments", "total_appointments": len(dashboard["appointments"])})
        trace.append({"step": 9, "action": "Review Pre-Visit Responses", "status": "INTAKE_RESPONSES_ACCESSIBLE"})
        trace.append({"step": 10, "action": "Review Relevant Patient Context", "status": "PATIENT_CONTEXT_BOUND"})

        return {
            "success": True,
            "doctor_id": doc.id,
            "doctor_name": doc.name,
            "10_step_journey_trace": trace,
            "dashboard": dashboard
        }

    def get_doctor_dashboard(self, doctor_id: str) -> Dict[str, Any]:
        doc = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            return {"error": "Doctor not found"}

        appts = self.db.query(Appointment).filter(Appointment.doctor_id == doctor_id).all()
        
        appt_briefings = []
        for a in appts:
            briefing = self.vision.generate_doctor_preparation_briefing(a.id)
            appt_briefings.append(briefing)

        return {
            "doctor_id": doctor_id,
            "doctor_name": doc.name,
            "specialty": doc.specialty,
            "profile_completed": doc.profile_completed,
            "appointments_count": len(appts),
            "appointments": appt_briefings
        }
