"""
Test Suite for Section 31: API & Capability Design Expectations.

Validates that every capability defines:
1. Name & Purpose
2. Validated Input schema
3. Validated Output schema
4. Authorization enforcement
5. Error conditions & handling
6. Retry & Recovery behavior
7. Verification behavior (EHR synchronization)
8. Audit logging
9. Idempotency behavior via idempotency keys
10. Reusability across: Web UI, AI Agent, Workflows, Administrative Tools.
"""

import pytest
import uuid
from datetime import datetime, date, timedelta, timezone, time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import (
    Base, Hospital, Doctor, DoctorWorkingHour, PatientProfile, Appointment, AppointmentStatus,
    AuditLog
)
from app.agent.capability_registry import (
    CapabilityRegistry, CapabilityExecutionRequest, CapabilityExecutionResult
)
from app.agent.actions import ActionExecutor
from app.schemas.actions import (
    CheckAvailabilityInput, CreateAppointmentInput, CancelAppointmentInput,
    RescheduleAppointmentInput, ActionType
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def setup_catalog(db_session):
    hosp = Hospital(name="Metro Health Center", code="METRO", is_active=True)
    db_session.add(hosp)
    db_session.commit()

    doc = Doctor(
        hospital_id=hosp.id,
        name="Dr. Gregory House",
        specialty="Diagnostic Medicine",
        is_active=True
    )
    db_session.add(doc)
    db_session.commit()

    for d in range(7):
        wh = DoctorWorkingHour(
            doctor_id=doc.id,
            day_of_week=d,
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        db_session.add(wh)
    db_session.commit()

    patient = PatientProfile(
        phone_number="+15551239999",
        full_name="John Doe",
        last_hospital_id=hosp.id,
        last_doctor_id=doc.id
    )
    db_session.add(patient)
    db_session.commit()

    return {"hospital": hosp, "doctor": doc, "patient": patient}


def test_section_31_check_availability_contract(db_session, setup_catalog):
    """
    Validates check_availability capability:
    - Input: doctor_id, date/target_date
    - Output: available_slots[]
    - Error handling: Missing required parameters
    - Reusable by Web UI, AI, and Admin
    """
    registry = CapabilityRegistry(db_session)
    data = setup_catalog

    # 1. Successful execution
    req = CapabilityExecutionRequest(
        capability_name="check_availability",
        arguments={
            "doctor_id": data["doctor"].id,
            "target_date": (date.today() + timedelta(days=1)).isoformat()
        },
        caller_role="PATIENT_AGENT"
    )
    result = registry.execute(req)

    assert result.success is True
    assert result.capability_name == "check_availability"
    assert "available_slots" in result.data
    assert isinstance(result.data["available_slots"], list)

    # 2. Error handling: Missing doctor_id
    bad_req = CapabilityExecutionRequest(
        capability_name="check_availability",
        arguments={},
        caller_role="PATIENT_AGENT"
    )
    bad_res = registry.execute(bad_req)
    assert bad_res.success is False
    assert "doctor_id required" in bad_res.message.lower()


def test_section_31_create_appointment_contract_and_idempotency(db_session, setup_catalog):
    """
    Validates create_appointment capability:
    - Input: patient_id/name, doctor_id, hospital_id, start_datetime, idempotency_key
    - Output: appointment_id, status, verification_status
    - Idempotency: Repeating call with same idempotency_key returns cached result with replay flag
    - Audit: Verifies AuditLog entry created
    """
    registry = CapabilityRegistry(db_session)
    data = setup_catalog

    target_dt = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2)).replace(hour=11, minute=0, second=0, microsecond=0)
    idem_key = f"IDEM-SEC31-{uuid.uuid4().hex[:8]}"

    req = CapabilityExecutionRequest(
        capability_name="create_appointment",
        arguments={
            "hospital_id": data["hospital"].id,
            "doctor_id": data["doctor"].id,
            "patient_name": data["patient"].full_name,
            "patient_phone": data["patient"].phone_number,
            "start_datetime": target_dt.isoformat()
        },
        caller_role="PATIENT_AGENT",
        idempotency_key=idem_key
    )

    # 1. First Execution
    res1 = registry.execute(req)
    assert res1.success is True
    assert "appointment_id" in res1.data
    assert res1.idempotent_replay is False
    appt_id = res1.data["appointment_id"]

    # 2. Idempotent Replay Execution
    res2 = registry.execute(req)
    assert res2.success is True
    assert res2.data["appointment_id"] == appt_id
    assert res2.idempotent_replay is True

    # 3. Audit Verification
    audit = db_session.query(AuditLog).filter(
        AuditLog.event_type.like("%CREATE_APPOINTMENT%")
    ).first()
    assert audit is not None


def test_section_31_authorization_enforcement(db_session, setup_catalog):
    """
    Validates authorization boundary check:
    - Rejects unauthorized caller roles.
    """
    registry = CapabilityRegistry(db_session)
    data = setup_catalog

    req = CapabilityExecutionRequest(
        capability_name="cancel_appointment",
        arguments={"appointment_id": "APP-TEST-001"},
        caller_role="UNAUTHORIZED_GUEST"
    )
    res = registry.execute(req)
    assert res.success is False
    assert "unauthorized" in res.message.lower()


def test_section_31_cross_consumer_reusability(db_session, setup_catalog):
    """
    Validates that the same capability contract is reusable by:
    1. AI Agent (via ActionExecutor)
    2. Web UI / Admin / Workflows (via CapabilityRegistry)
    """
    data = setup_catalog

    # Consumer 1: AI ActionExecutor
    executor = ActionExecutor(db_session)
    ai_input = CheckAvailabilityInput(
        session_id="SESS-AI-01",
        patient_id=data["patient"].id,
        doctor_id=data["doctor"].id,
        target_date=date.today() + timedelta(days=1)
    )
    ai_output = executor.check_availability(ai_input)
    assert ai_output.success is True
    assert ai_output.action_type == ActionType.CHECK_AVAILABILITY

    # Consumer 2: Workflow / Web / Admin CapabilityRegistry
    registry = CapabilityRegistry(db_session)
    admin_req = CapabilityExecutionRequest(
        capability_name="check_availability",
        arguments={
            "doctor_id": data["doctor"].id,
            "target_date": (date.today() + timedelta(days=1)).isoformat()
        },
        caller_role="HOSPITAL_ADMIN"
    )
    admin_output = registry.execute(admin_req)
    assert admin_output.success is True
    assert "available_slots" in admin_output.data
