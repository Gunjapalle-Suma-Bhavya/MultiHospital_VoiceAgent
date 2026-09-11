"""
Test Suite for Section 32: State Management Expectations.

Validates the explicit architectural separation of the 6 distinct platform states:
1. Transactional State (e.g. Appointment = Confirmed, Doctor = Active, Hospital = Approved)
2. Conversational State (e.g. Current Intent = Booking, Selected Doctor = Dr. Sharma, Selected Date = Friday)
3. User Context (e.g. Preferred Time Window = Afternoon, Preferred Hospital = Hospital A, Language = English)
4. Workflow State (e.g. Reminder Workflow = Scheduled, Intake Questionnaire = In Progress)
5. Integration State (e.g. EHR Integration = Verified, External Sync Status = Confirmed)
6. Operational State (e.g. EHR Operation = Reconciliation Required, Circuit Breaker = Closed)

These states must never be blended into a single unstructured data object.
"""

import pytest
import json
import uuid
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import (
    Base, Hospital, Doctor, PatientProfile, Appointment, AppointmentStatus,
    PatientSessionState, WorkflowInstance, WorkflowStatus, EHRSyncLog,
    PreferredTimeWindow, OperationTrace
)
from app.ehr.circuit_breaker import default_ehr_circuit_breaker
from app.agent.patient_access_agent import PatientAccessAgentService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def setup_state_environment(db_session):
    hosp = Hospital(name="Apollo Healthcare Center", code="APOLLO", is_active=True)
    db_session.add(hosp)
    db_session.commit()

    doc = Doctor(
        hospital_id=hosp.id,
        name="Dr. Sharma",
        specialty="Cardiology",
        is_active=True
    )
    db_session.add(doc)
    db_session.commit()

    patient = PatientProfile(
        phone_number="+15558889999",
        full_name="Vikram Patel",
        preferred_time_window=PreferredTimeWindow.AFTERNOON,
        last_hospital_id=hosp.id,
        last_doctor_id=doc.id
    )
    db_session.add(patient)
    db_session.commit()

    return {"hospital": hosp, "doctor": doc, "patient": patient}


def test_section_32_distinct_state_separation(db_session, setup_state_environment):
    """
    Validates that each of the 6 states has its own discrete schema, lifecycle, and store.
    """
    env = setup_state_environment
    session_id = f"SESS-{uuid.uuid4().hex[:8]}"

    # 1. CONVERSATIONAL STATE (stored in PatientSessionState, ephemeral & turn-scoped)
    conv_state = PatientSessionState(
        session_id=session_id,
        patient_id=env["patient"].id,
        current_intent="BOOK_APPOINTMENT",
        workflow_step="DOCTOR_SELECTED",
        active_draft_booking_json=json.dumps({
            "selected_doctor": "Dr. Sharma",
            "selected_date": "Friday",
            "specialty": "Cardiology"
        })
    )
    db_session.add(conv_state)
    db_session.commit()

    assert conv_state.current_intent == "BOOK_APPOINTMENT"
    draft = json.loads(conv_state.active_draft_booking_json)
    assert draft["selected_doctor"] == "Dr. Sharma"
    assert draft["selected_date"] == "Friday"

    # 2. USER CONTEXT (stored in PatientProfile, persistent across visits)
    user_context = db_session.query(PatientProfile).filter(PatientProfile.id == env["patient"].id).first()
    assert user_context.preferred_time_window == PreferredTimeWindow.AFTERNOON
    assert user_context.last_hospital_id == env["hospital"].id
    # Ensure user context is not contaminated with ephemeral turn data
    assert not hasattr(user_context, "current_intent")

    # 3. TRANSACTIONAL STATE (stored in Appointment, canonical business truth)
    target_dt = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=3)
    appt = Appointment(
        hospital_id=env["hospital"].id,
        doctor_id=env["doctor"].id,
        patient_id=env["patient"].id,
        patient_name=env["patient"].full_name,
        patient_phone=env["patient"].phone_number,
        start_datetime=target_dt,
        end_datetime=target_dt + timedelta(minutes=30),
        status=AppointmentStatus.CONFIRMED,
        is_ehr_verified=True
    )
    db_session.add(appt)
    db_session.commit()

    assert appt.status == AppointmentStatus.CONFIRMED
    assert appt.is_ehr_verified is True

    # 4. WORKFLOW STATE (stored in WorkflowInstance, background & scheduled jobs)
    wf = WorkflowInstance(
        appointment_id=appt.id,
        workflow_name="APPOINTMENT_REMINDER",
        trigger_event="APPOINTMENT_CONFIRMED",
        status=WorkflowStatus.WAITING,
        scheduled_for=target_dt - timedelta(hours=24)
    )
    db_session.add(wf)
    db_session.commit()

    assert wf.status == WorkflowStatus.WAITING
    assert wf.workflow_name == "APPOINTMENT_REMINDER"

    # 5. INTEGRATION STATE (stored in EHRSyncLog, external system boundary)
    sync_log = EHRSyncLog(
        appointment_id=appt.id,
        hospital_id=env["hospital"].id,
        action_type="CREATE_APPOINTMENT",
        sync_status="VERIFIED",
        external_reference_id="EPIC-APPT-889900"
    )
    db_session.add(sync_log)
    db_session.commit()

    assert sync_log.sync_status == "VERIFIED"
    assert sync_log.external_reference_id == "EPIC-APPT-889900"

    # 6. OPERATIONAL STATE (stored in OperationTrace and EHRCircuitBreaker)
    op_trace = OperationTrace(
        trace_id=f"TRC-{uuid.uuid4().hex[:8]}",
        correlation_id=f"CORR-{uuid.uuid4().hex[:8]}",
        session_id=session_id,
        appointment_id=appt.id,
        status="RECONCILIATION_REQUIRED",
        reconciliation_occurred=True
    )
    db_session.add(op_trace)
    db_session.commit()

    assert op_trace.status == "RECONCILIATION_REQUIRED"
    assert op_trace.reconciliation_occurred is True
    assert default_ehr_circuit_breaker.can_execute() is True


def test_section_32_no_unstructured_state_leakage(db_session, setup_state_environment):
    """
    Validates that turn execution does not pollute persistent user context with ephemeral slot state.
    """
    env = setup_state_environment
    agent_svc = PatientAccessAgentService(db_session)

    res = agent_svc.process_patient_turn(
        patient_phone=env["patient"].phone_number,
        user_utterance="I want to book an appointment with Dr. Sharma next Friday",
        hospital_id=env["hospital"].id,
        doctor_id=env["doctor"].id
    )

    # Verify structured response separation
    assert "detected_intent" in res
    assert "interaction_context" in res
    assert "capabilities_invoked" in res

    # Verify patient profile retains only long-term profile data
    patient_fresh = db_session.query(PatientProfile).filter(PatientProfile.id == env["patient"].id).first()
    assert patient_fresh.preferred_time_window == PreferredTimeWindow.AFTERNOON
    assert not hasattr(patient_fresh, "active_draft_booking")
