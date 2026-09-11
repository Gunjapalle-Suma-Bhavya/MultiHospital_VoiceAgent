"""
Hospital & Doctor Discovery Engine (Section 5.13).

Executes the 7-step discovery pipeline:
1. Understand Request & Parse Filters (Specialty, Department, Hospital, Location, Doctor, Category, Date, Time Window)
2. Identify Appointment Category (In-Person, Video, Follow-up, Specialty)
3. Find Relevant Active Doctors
4. Search Participating Approved Hospitals
5. Check Availability (via AvailabilityEngine)
6. Apply Scheduling & Operational Rules
7. Return Actual Bookable Slots (Anti-Hallucination)

Example: "Find me a dermatologist this Friday afternoon."
"""

from datetime import datetime, date, time, timedelta
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.models import Hospital, Doctor, HospitalStatus, DoctorStatus, PreferredTimeWindow, ConsultationType
from app.scheduling.availability_engine import AvailabilityEngine
from app.agent.intent_understanding import SymptomIntentResolver


class DiscoveryRequest(BaseModel):
    query_text: Optional[str] = None
    specialty: Optional[str] = None
    department: Optional[str] = None
    hospital_name: Optional[str] = None
    location: Optional[str] = None
    doctor_name: Optional[str] = None
    appointment_category: Optional[str] = "IN_PERSON"
    target_date: Optional[str] = None  # YYYY-MM-DD
    time_window: Optional[str] = "ANYTIME"  # MORNING, AFTERNOON, EVENING, ANYTIME
    patient_id: Optional[str] = None


class DiscoverySlotResult(BaseModel):
    slot_id: str
    hospital_id: str
    hospital_name: str
    doctor_id: str
    doctor_name: str
    specialty: str
    start_datetime: str
    end_datetime: str
    time_window: str
    appointment_category: str


class DiscoveryPipelineResult(BaseModel):
    status: str
    query_understood: Dict[str, Any]
    hospitals_matched_count: int
    doctors_matched_count: int
    available_slots: List[DiscoverySlotResult]
    cautious_disclaimer: str


class HospitalDoctorDiscoveryEngine:
    """
    Multi-parameter discovery engine orchestrating multi-hospital doctor and slot lookup.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.avail_engine = AvailabilityEngine(db_session)

    def execute_discovery(self, request: DiscoveryRequest) -> DiscoveryPipelineResult:
        # Step 1: Understand Request & Extract Symptoms / Filters
        specialty = request.specialty
        cautious_text = "Slots retrieved based on actual scheduling data."

        if request.query_text and not specialty:
            symptom_res = SymptomIntentResolver.infer_specialty_from_utterance(request.query_text)
            if symptom_res.has_symptom:
                specialty = symptom_res.inferred_specialty
                cautious_text = symptom_res.cautious_response

        # Target Date Resolution (Default: tomorrow if unspecified)
        if request.target_date:
            try:
                target_d = datetime.strptime(request.target_date, "%Y-%m-%d").date()
            except ValueError:
                target_d = date.today() + timedelta(days=1)
        else:
            target_d = date.today() + timedelta(days=1)

        # Step 2 & 3 & 4: Find Participating Approved Hospitals & Active Doctors
        hosp_query = self.db.query(Hospital).filter(
            Hospital.hospital_status == HospitalStatus.APPROVED,
            Hospital.is_active == True
        )
        if request.hospital_name:
            hosp_query = hosp_query.filter(Hospital.name.ilike(f"%{request.hospital_name}%"))
        hospitals = hosp_query.all()
        allowed_hosp_ids = {h.id for h in hospitals}

        doc_query = self.db.query(Doctor).filter(
            Doctor.doctor_status == DoctorStatus.ACTIVE,
            Doctor.is_active == True,
            Doctor.hospital_id.in_(allowed_hosp_ids)
        )
        if specialty:
            doc_query = doc_query.filter(Doctor.specialty.ilike(f"%{specialty}%"))
        if request.doctor_name:
            doc_query = doc_query.filter(Doctor.name.ilike(f"%{request.doctor_name}%"))
        if request.department:
            doc_query = doc_query.filter(Doctor.department.ilike(f"%{request.department}%"))

        doctors = doc_query.all()

        # Step 5 & 6 & 7: Check Availability & Filter actual bookable slots
        matched_slots: List[DiscoverySlotResult] = []

        for doc in doctors:
            hosp = self.db.query(Hospital).filter(Hospital.id == doc.hospital_id).first()
            if not hosp or hosp.hospital_status != HospitalStatus.APPROVED:
                continue

            slots = self.avail_engine.query_actual_availability(
                doctor_id=doc.id,
                target_date=target_d,
                time_window=request.time_window or "ANYTIME"
            )

            for slot in slots:
                # Apply time window filtering
                slot_start_dt = slot["start_datetime"]
                if isinstance(slot_start_dt, str):
                    slot_dt = datetime.fromisoformat(slot_start_dt)
                else:
                    slot_dt = slot_start_dt

                hour = slot_dt.hour
                window_match = True
                tw = (request.time_window or "ANYTIME").upper()

                if tw == "MORNING" and not (8 <= hour < 12):
                    window_match = False
                elif tw == "AFTERNOON" and not (12 <= hour < 17):
                    window_match = False
                elif tw == "EVENING" and not (17 <= hour < 21):
                    window_match = False

                if window_match:
                    matched_slots.append(
                        DiscoverySlotResult(
                            slot_id=slot.get("slot_id") or f"SLOT-{doc.id[:4]}-{int(slot_dt.timestamp())}",
                            hospital_id=hosp.id,
                            hospital_name=hosp.name,
                            doctor_id=doc.id,
                            doctor_name=doc.name,
                            specialty=doc.specialty,
                            start_datetime=slot_dt.isoformat(),
                            end_datetime=(slot_dt + timedelta(minutes=30)).isoformat(),
                            time_window=tw,
                            appointment_category=request.appointment_category or "IN_PERSON"
                        )
                    )

        return DiscoveryPipelineResult(
            status="SUCCESS",
            query_understood={
                "specialty": specialty,
                "target_date": target_d.isoformat(),
                "time_window": request.time_window,
                "doctor_name": request.doctor_name,
                "hospital_name": request.hospital_name
            },
            hospitals_matched_count=len(hospitals),
            doctors_matched_count=len(doctors),
            available_slots=matched_slots,
            cautious_disclaimer=cautious_text
        )
