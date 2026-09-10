"""
Multi-Tier Persistent User Context Engine (Section 5.17).

Enforces strict boundary separation across 4 distinct context tiers:
1. Tier 1: Current Conversation State
2. Tier 2: Short-Term Interaction Context
3. Tier 3: Longer-Term User Preferences
4. Tier 4: Appointment-Specific Information

Retrieves context dynamically when relevant, ensuring internal storage mechanisms
and database implementation details are never exposed to users.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.models import PatientProfile, Appointment, Hospital, Doctor, AppointmentStatus
from app.agent.conversation_state import ConversationStateManager, ConversationStateModel


class Tier1ConversationState(BaseModel):
    intent: Optional[str] = None
    specialty: Optional[str] = None
    date: Optional[str] = None
    time_preference: Optional[str] = None
    selected_doctor: Optional[Dict[str, Any]] = None
    selected_hospital: Optional[Dict[str, Any]] = None
    selected_slot: Optional[Dict[str, Any]] = None
    appointment_status: str = "PENDING"
    workflow_status: str = "ACTIVE"


class Tier2ShortTermContext(BaseModel):
    last_searched_specialty: Optional[str] = None
    recent_slot_options: List[Dict[str, Any]] = []
    unresolved_questions: List[str] = []


class Tier3LongTermPreferences(BaseModel):
    patient_id: str
    phone_number: str
    full_name: Optional[str] = None
    preferred_hospitals: List[str] = []
    preferred_doctors: List[str] = []
    preferred_time_window: str = "ANYTIME"
    communication_preference: str = "VOICE_AND_SMS"
    appointment_history_count: int = 0
    previous_conversation_summaries: List[str] = []


class Tier4AppointmentInformation(BaseModel):
    upcoming_appointments: List[Dict[str, Any]] = []
    pending_questionnaires_count: int = 0
    ehr_sync_status: str = "SYNCHRONIZED"


class HierarchicalContextBundle(BaseModel):
    patient_id: str
    tier1_conversation_state: Tier1ConversationState
    tier2_short_term: Tier2ShortTermContext
    tier3_long_term: Tier3LongTermPreferences
    tier4_appointment_info: Tier4AppointmentInformation

    def generate_natural_prompt_hint(self) -> str:
        """
        Synthesizes a clean, non-intrusive prompt hint for the agent.
        Hides internal database identifiers and storage mechanics.
        """
        hints = []
        # Tier 3 Long Term
        if self.tier3_long_term.preferred_doctors:
            hints.append(f"Patient preferred doctors: {', '.join(self.tier3_long_term.preferred_doctors)}.")
        if self.tier3_long_term.preferred_time_window != "ANYTIME":
            hints.append(f"Prefers {self.tier3_long_term.preferred_time_window.lower()} appointments.")
        
        # Tier 4 Appointment Info
        if self.tier4_appointment_info.upcoming_appointments:
            count = len(self.tier4_appointment_info.upcoming_appointments)
            hints.append(f"Patient has {count} upcoming appointment(s).")

        if hints:
            return "CONTEXT HINT: " + " ".join(hints)
        return ""


class MultiTierContextEngine:
    """
    Centralized 4-Tier Context Resolver & Persistent User Preference Manager.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.state_manager = ConversationStateManager(db_session)

    def get_hierarchical_context(
        self,
        session_id: str,
        patient_id: Optional[str] = None,
        phone_number: Optional[str] = None
    ) -> HierarchicalContextBundle:
        # Tier 1: Current Session State
        session_state = self.state_manager.get_or_create_state(session_id, patient_id=patient_id)
        
        # Tier 3: Resolve Patient Profile
        patient = None
        if patient_id:
            patient = self.db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
        elif phone_number:
            patient = self.db.query(PatientProfile).filter(PatientProfile.phone_number == phone_number).first()

        if not patient and session_state.patient_id:
            patient = self.db.query(PatientProfile).filter(PatientProfile.id == session_state.patient_id).first()

        pid = patient.id if patient else (patient_id or session_state.patient_id or "P-ANONYMOUS")
        phone = patient.phone_number if patient else (phone_number or "+15550000000")
        name = patient.full_name if patient else "Valued Patient"

        # Tier 3 Long Term
        pref_hospitals = []
        pref_doctors = []
        if patient and patient.last_hospital_id:
            h = self.db.query(Hospital).filter(Hospital.id == patient.last_hospital_id).first()
            if h: pref_hospitals.append(h.name)
        if patient and patient.last_doctor_id:
            d = self.db.query(Doctor).filter(Doctor.id == patient.last_doctor_id).first()
            if d: pref_doctors.append(d.name)

        t3 = Tier3LongTermPreferences(
            patient_id=pid,
            phone_number=phone,
            full_name=name,
            preferred_hospitals=pref_hospitals,
            preferred_doctors=pref_doctors,
            preferred_time_window=patient.preferred_time_window.value if (patient and patient.preferred_time_window) else "ANYTIME",
            communication_preference=patient.communication_preference if patient else "VOICE_AND_SMS",
            appointment_history_count=self.db.query(Appointment).filter(Appointment.patient_phone == phone).count() if patient else 0
        )

        # Tier 4 Appointment Info
        upcoming_appts = []
        if patient:
            appts = self.db.query(Appointment).filter(
                Appointment.patient_phone == phone,
                Appointment.status.in_([
                    AppointmentStatus.PENDING_EHR_VERIFICATION,
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.RECONCILIATION_REQUIRED
                ])
            ).all()
            for a in appts:
                doc = self.db.query(Doctor).filter(Doctor.id == a.doctor_id).first()
                hosp = self.db.query(Hospital).filter(Hospital.id == a.hospital_id).first()
                upcoming_appts.append({
                    "appointment_id": a.id,
                    "doctor_name": doc.name if doc else "Doctor",
                    "hospital_name": hosp.name if hosp else "Hospital",
                    "start_datetime": a.start_datetime.isoformat(),
                    "status": a.status.value
                })

        t4 = Tier4AppointmentInformation(
            upcoming_appointments=upcoming_appts,
            pending_questionnaires_count=0,
            ehr_sync_status="SYNCHRONIZED"
        )

        t1 = Tier1ConversationState(
            intent=session_state.intent,
            specialty=session_state.specialty,
            date=session_state.date,
            time_preference=session_state.time_preference,
            selected_doctor=session_state.selected_doctor,
            selected_hospital=session_state.selected_hospital,
            selected_slot=session_state.selected_slot,
            appointment_status=session_state.appointment_status,
            workflow_status=session_state.workflow_status.value
        )

        t2 = Tier2ShortTermContext(
            last_searched_specialty=session_state.specialty,
            recent_slot_options=[],
            unresolved_questions=[]
        )

        return HierarchicalContextBundle(
            patient_id=pid,
            tier1_conversation_state=t1,
            tier2_short_term=t2,
            tier3_long_term=t3,
            tier4_appointment_info=t4
        )

    def update_long_term_preferences(
        self,
        patient_id: str,
        preferred_doctor_id: Optional[str] = None,
        preferred_hospital_id: Optional[str] = None,
        preferred_time_window: Optional[str] = None
    ):
        patient = self.db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
        if patient:
            if preferred_doctor_id: patient.last_doctor_id = preferred_doctor_id
            if preferred_hospital_id: patient.last_hospital_id = preferred_hospital_id
            self.db.commit()
