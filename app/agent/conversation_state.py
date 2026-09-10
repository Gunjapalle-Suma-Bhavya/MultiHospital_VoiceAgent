"""
Active Conversation State & Context Engine (Section 5.16).

Tracks active turn state:
- intent = BOOK_APPOINTMENT / RESCHEDULE / CANCEL / DISCOVERY
- specialty = Cardiology
- date = Friday
- time_preference = Afternoon
- selected_doctor = Dr. Gregory House
- selected_hospital = St. Jude General Hospital
- selected_slot = 14:00
- appointment_status = PENDING / BOOKED / RECONCILIATION_REQUIRED
- workflow_status = ACTIVE / COMPLETED / CANCELLED / ABANDONED / EXPIRED

Persists in database until workflow completes, cancels, abandons, or expires (TTL).
"""

import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.models import PatientSessionState, PatientProfile


class WorkflowLifecycleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ABANDONED = "ABANDONED"
    EXPIRED = "EXPIRED"


class ConversationStateModel(BaseModel):
    session_id: str
    patient_id: Optional[str] = None
    intent: Optional[str] = None  # e.g., BOOK_APPOINTMENT, CANCEL_APPOINTMENT, DISCOVERY
    specialty: Optional[str] = None
    date: Optional[str] = None
    time_preference: Optional[str] = None  # MORNING, AFTERNOON, EVENING, ANYTIME
    selected_doctor: Optional[Dict[str, Any]] = None
    selected_hospital: Optional[Dict[str, Any]] = None
    selected_slot: Optional[Dict[str, Any]] = None
    appointment_status: str = "PENDING"
    workflow_status: WorkflowLifecycleStatus = WorkflowLifecycleStatus.ACTIVE
    collected_slots: Dict[str, Any] = {}
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: str = Field(default_factory=lambda: (datetime.utcnow() + timedelta(minutes=15)).isoformat())

    def is_expired(self) -> bool:
        exp_dt = datetime.fromisoformat(self.expires_at)
        return datetime.utcnow() > exp_dt


class ConversationStateManager:
    """
    Manages active session conversation state with DB persistence and lifecycle transitions.
    """

    def __init__(self, db_session: Session, ttl_minutes: int = 15):
        self.db = db_session
        self.ttl_minutes = ttl_minutes

    def get_or_create_state(self, session_id: str, patient_id: Optional[str] = None) -> ConversationStateModel:
        row = self.db.query(PatientSessionState).filter(PatientSessionState.session_id == session_id).first()
        if not row:
            now = datetime.utcnow()
            expires = now + timedelta(minutes=self.ttl_minutes)
            init_draft = {
                "intent": None,
                "specialty": None,
                "date": None,
                "time_preference": None,
                "selected_doctor": None,
                "selected_hospital": None,
                "selected_slot": None,
                "appointment_status": "PENDING",
                "workflow_status": WorkflowLifecycleStatus.ACTIVE.value,
                "collected_slots": {},
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "expires_at": expires.isoformat()
            }
            row = PatientSessionState(
                session_id=session_id,
                patient_id=patient_id or str(uuid.uuid4()),
                current_intent="GENERAL_INQUIRY",
                workflow_step="INITIAL",
                active_draft_booking_json=json.dumps(init_draft),
                is_active=True
            )
            self.db.add(row)
            self.db.commit()
            self.db.refresh(row)

        draft = json.loads(row.active_draft_booking_json) if row.active_draft_booking_json else {}
        
        # Expiration Check
        exp_dt = datetime.fromisoformat(draft.get("expires_at", datetime.utcnow().isoformat()))
        if datetime.utcnow() > exp_dt and draft.get("workflow_status") == WorkflowLifecycleStatus.ACTIVE.value:
            draft["workflow_status"] = WorkflowLifecycleStatus.EXPIRED.value
            row.active_draft_booking_json = json.dumps(draft)
            row.is_active = False
            self.db.commit()

        return ConversationStateModel(
            session_id=row.session_id,
            patient_id=row.patient_id,
            intent=draft.get("intent") or row.current_intent,
            specialty=draft.get("specialty"),
            date=draft.get("date"),
            time_preference=draft.get("time_preference"),
            selected_doctor=draft.get("selected_doctor"),
            selected_hospital=draft.get("selected_hospital"),
            selected_slot=draft.get("selected_slot"),
            appointment_status=draft.get("appointment_status", "PENDING"),
            workflow_status=WorkflowLifecycleStatus(draft.get("workflow_status", WorkflowLifecycleStatus.ACTIVE.value)),
            collected_slots=draft.get("collected_slots", {}),
            created_at=draft.get("created_at", datetime.utcnow().isoformat()),
            updated_at=draft.get("updated_at", datetime.utcnow().isoformat()),
            expires_at=draft.get("expires_at", (datetime.utcnow() + timedelta(minutes=self.ttl_minutes)).isoformat())
        )

    def update_state(
        self,
        session_id: str,
        intent: Optional[str] = None,
        specialty: Optional[str] = None,
        date: Optional[str] = None,
        time_preference: Optional[str] = None,
        selected_doctor: Optional[Dict[str, Any]] = None,
        selected_hospital: Optional[Dict[str, Any]] = None,
        selected_slot: Optional[Dict[str, Any]] = None,
        appointment_status: Optional[str] = None,
        workflow_status: Optional[WorkflowLifecycleStatus] = None,
        additional_slots: Optional[Dict[str, Any]] = None
    ) -> ConversationStateModel:
        state = self.get_or_create_state(session_id)
        
        if intent: state.intent = intent
        if specialty: state.specialty = specialty
        if date: state.date = date
        if time_preference: state.time_preference = time_preference
        if selected_doctor: state.selected_doctor = selected_doctor
        if selected_hospital: state.selected_hospital = selected_hospital
        if selected_slot: state.selected_slot = selected_slot
        if appointment_status: state.appointment_status = appointment_status
        if workflow_status: state.workflow_status = workflow_status
        if additional_slots: state.collected_slots.update(additional_slots)

        now = datetime.utcnow()
        state.updated_at = now.isoformat()
        state.expires_at = (now + timedelta(minutes=self.ttl_minutes)).isoformat()

        row = self.db.query(PatientSessionState).filter(PatientSessionState.session_id == session_id).first()
        if row:
            row.current_intent = state.intent
            row.is_active = (state.workflow_status == WorkflowLifecycleStatus.ACTIVE)
            row.active_draft_booking_json = json.dumps(state.model_dump())
            self.db.commit()

        return state

    def complete_workflow(self, session_id: str) -> ConversationStateModel:
        return self.update_state(session_id, workflow_status=WorkflowLifecycleStatus.COMPLETED, appointment_status="BOOKED")

    def cancel_workflow(self, session_id: str) -> ConversationStateModel:
        return self.update_state(session_id, workflow_status=WorkflowLifecycleStatus.CANCELLED, appointment_status="CANCELLED")

    def abandon_workflow(self, session_id: str) -> ConversationStateModel:
        return self.update_state(session_id, workflow_status=WorkflowLifecycleStatus.ABANDONED, appointment_status="ABANDONED")
