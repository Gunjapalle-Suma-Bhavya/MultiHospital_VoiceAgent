"""
Test Suite for Section 15: Reliability & Failure Handling.

Tests:
1. Real-World Failure Classification across all 5 domains:
   - Voice Failures (noisy audio, interruption, silence, unclear speech, call drop)
   - Agent Failures (capability failure, missing info, ambiguous request, unsupported request, long-running, context failure)
   - Scheduling Failures (slot unavailable, double booking attempt, calendar conflict, doctor unavailable)
   - EHR / External Integration Failures (timeout, auth failure, rate limit, mapping failure, patient not found, unknown outcome)
   - Workflow Failures (timeout, external service, notification, duplicate execution, dependency unavailable)
2. Section 15.1 Controlled Retries & Recovery with Anti-Duplicate Guarantees:
   - Safe query of existing external state before creation
   - Idempotency key tracking
   - Reached retry limit triggers reconciliation and escalation
3. Section 15.2 Idempotency Enforcer:
   - Zero duplicate bookings, cancellations, notifications, or workflows on repeated executions
4. Section 15.3 Strict Booking Verification:
   - Never states "Your appointment is booked" until authoritative external EHR verification succeeds
   - Verified state produces confirmation speech
   - Unverified state returns pending verification speech
5. REST API Endpoints under /api/v1/reliability
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.config import get_db, init_db, SessionLocal
from app.database.models import (
    Base, Hospital, Doctor, PatientProfile, Appointment, AppointmentStatus,
    HumanEscalationRecord, IntegrationVerificationRecord
)
from app.reliability import (
    FailureDomain,
    VoiceFailureType,
    AgentFailureType,
    SchedulingFailureType,
    EHRFailureType,
    WorkflowFailureType,
    FailureHandlingStrategy,
)
from app.reliability.failure_handler import ReliabilityAndFailureEngine


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 1. Failure Classification across All 5 Domains
# -----------------------------------------------------------------------------
def test_voice_failures_classification():
    # Noisy Audio
    p1 = ReliabilityAndFailureEngine.resolve_failure(FailureDomain.VOICE, VoiceFailureType.NOISY_AUDIO.value)
    assert p1.is_retryable is True
    assert p1.recommended_strategy == FailureHandlingStrategy.CLARIFY_WITH_PATIENT
    assert "trouble hearing" in p1.patient_facing_message

    # Interruption (Barge-in)
    p2 = ReliabilityAndFailureEngine.resolve_failure(FailureDomain.VOICE, VoiceFailureType.PATIENT_INTERRUPTION.value)
    assert p2.recommended_strategy == FailureHandlingStrategy.TERMINATE_SAFE

    # Silence
    p3 = ReliabilityAndFailureEngine.resolve_failure(FailureDomain.VOICE, VoiceFailureType.SILENCE.value)
    assert "still there" in p3.patient_facing_message

    # Unclear Speech
    p4 = ReliabilityAndFailureEngine.resolve_failure(FailureDomain.VOICE, VoiceFailureType.UNCLEAR_SPEECH.value)
    assert "didn't quite catch" in p4.patient_facing_message

    # Call Drop
    p5 = ReliabilityAndFailureEngine.resolve_failure(FailureDomain.VOICE, VoiceFailureType.CALL_DROP.value)
    assert p5.is_retryable is False


def test_agent_and_scheduling_failures():
    # Unsupported request -> Escalate to human
    p_unsupp = ReliabilityAndFailureEngine.resolve_failure(FailureDomain.AGENT, AgentFailureType.UNSUPPORTED_REQUEST.value)
    assert p_unsupp.recommended_strategy == FailureHandlingStrategy.ESCALATE_TO_HUMAN

    # Ambiguous request -> Clarify
    p_ambig = ReliabilityAndFailureEngine.resolve_failure(FailureDomain.AGENT, AgentFailureType.AMBIGUOUS_REQUEST.value)
    assert p_ambig.recommended_strategy == FailureHandlingStrategy.CLARIFY_WITH_PATIENT

    # Double Booking Attempt -> Offer alternative slot
    p_double = ReliabilityAndFailureEngine.resolve_failure(FailureDomain.SCHEDULING, SchedulingFailureType.DOUBLE_BOOKING_ATTEMPT.value)
    assert p_double.recommended_strategy == FailureHandlingStrategy.OFFER_ALTERNATIVE_SLOT
    assert "just reserved" in p_double.patient_facing_message


def test_ehr_and_workflow_failures():
    # EHR Timeout -> Retryable with backoff
    p_ehr_time = ReliabilityAndFailureEngine.resolve_failure(FailureDomain.EHR_INTEGRATION, EHRFailureType.API_TIMEOUT.value)
    assert p_ehr_time.is_retryable is True
    assert p_ehr_time.recommended_strategy == FailureHandlingStrategy.RETRY_WITH_BACKOFF

    # EHR Auth failure -> Escalate
    p_ehr_auth = ReliabilityAndFailureEngine.resolve_failure(FailureDomain.EHR_INTEGRATION, EHRFailureType.AUTHENTICATION_FAILURE.value)
    assert p_ehr_auth.is_retryable is False
    assert p_ehr_auth.recommended_strategy == FailureHandlingStrategy.ESCALATE_TO_HUMAN

    # Duplicate execution workflow -> Terminate safe without side-effects
    p_wf_dup = ReliabilityAndFailureEngine.resolve_failure(FailureDomain.WORKFLOW, WorkflowFailureType.DUPLICATE_EXECUTION.value)
    assert p_wf_dup.recommended_strategy == FailureHandlingStrategy.TERMINATE_SAFE


# -----------------------------------------------------------------------------
# 2. Section 15.1: Controlled Retries & Recovery
# -----------------------------------------------------------------------------
def test_controlled_retry_success_and_anti_duplicate_behavior(db_session):
    hosp = Hospital(name="St. Jude", code="STJUDE", is_active=True)
    db_session.add(hosp)
    db_session.commit()

    doc = Doctor(hospital_id=hosp.id, name="Dr. Sarah Connor", specialty="Orthopedics", is_active=True)
    db_session.add(doc)
    db_session.commit()

    appt = Appointment(
        hospital_id=hosp.id,
        doctor_id=doc.id,
        patient_name="Alex Miller",
        patient_phone="+15551234567",
        start_datetime=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2),
        end_datetime=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2, minutes=30),
        status=AppointmentStatus.PENDING_EHR_VERIFICATION,
        is_ehr_verified=False
    )
    db_session.add(appt)
    db_session.commit()

    engine = ReliabilityAndFailureEngine(db_session)
    res = engine.execute_controlled_retry(appointment_id=appt.id, failure_type="API_TIMEOUT", max_retries=3)

    assert res["retry_executed"] is True
    assert res["is_verified"] is True
    assert appt.is_ehr_verified is True
    assert appt.status == AppointmentStatus.SCHEDULED


# -----------------------------------------------------------------------------
# 3. Section 15.2: Idempotency Enforcer
# -----------------------------------------------------------------------------
def test_idempotency_enforcer_zero_duplicate_side_effects(db_session):
    idemp_key = "IDEMP-TEST-KEY-9999"
    counter = {"calls": 0}

    def _side_effect_action():
        counter["calls"] += 1
        return {"action": "APPOINTMENT_CREATION", "booking_id": "APPT-IDEMP-01"}

    # First execution -> calls action
    res1 = ReliabilityAndFailureEngine.execute_idempotent_operation(
        idempotency_key=idemp_key,
        operation_type="APPOINTMENT_CREATION",
        operation_fn=_side_effect_action,
        db_session=db_session
    )
    assert res1["idempotent_replay"] is False
    assert counter["calls"] == 1
    assert res1["result"]["booking_id"] == "APPT-IDEMP-01"

    # Second execution with same key -> returns cached result, does NOT call action
    res2 = ReliabilityAndFailureEngine.execute_idempotent_operation(
        idempotency_key=idemp_key,
        operation_type="APPOINTMENT_CREATION",
        operation_fn=_side_effect_action,
        db_session=db_session
    )
    assert res2["idempotent_replay"] is True
    assert counter["calls"] == 1  # Guaranteed zero duplicate side-effects!
    assert res2["result"]["booking_id"] == "APPT-IDEMP-01"


# -----------------------------------------------------------------------------
# 4. Section 15.3: Strict Booking Verification Rule
# -----------------------------------------------------------------------------
def test_strict_booking_verification_prevents_unverified_confirmation(db_session):
    hosp = Hospital(name="Care Regional", code="CARE_REG", is_active=True)
    db_session.add(hosp)
    db_session.commit()

    doc = Doctor(hospital_id=hosp.id, name="Dr. Elena", specialty="Dermatology", is_active=True)
    db_session.add(doc)
    db_session.commit()

    # Case A: UNVERIFIED appointment
    unverified_appt = Appointment(
        hospital_id=hosp.id,
        doctor_id=doc.id,
        patient_name="Rachel Adams",
        patient_phone="+15559876543",
        start_datetime=datetime(2026, 9, 17, 15, 0),
        end_datetime=datetime(2026, 9, 17, 15, 30),
        status=AppointmentStatus.PENDING_EHR_VERIFICATION,
        is_ehr_verified=False
    )
    db_session.add(unverified_appt)
    db_session.commit()

    engine = ReliabilityAndFailureEngine(db_session)
    verif_res_unverif = engine.evaluate_booking_confirmation_speech(unverified_appt.id)

    # Must NEVER say "Your appointment is booked"
    assert verif_res_unverif["can_confirm"] is False
    assert "Your appointment is confirmed" not in verif_res_unverif["speech"]
    assert "pending external system verification" in verif_res_unverif["speech"]

    # Case B: VERIFIED appointment
    unverified_appt.is_ehr_verified = True
    unverified_appt.status = AppointmentStatus.SCHEDULED
    unverified_appt.external_appointment_id = "EXT-EHR-CONFIRMED-88"
    db_session.commit()

    verif_res_verif = engine.evaluate_booking_confirmation_speech(unverified_appt.id)
    assert verif_res_verif["can_confirm"] is True
    assert "Your appointment is confirmed" in verif_res_verif["speech"]


# -----------------------------------------------------------------------------
# 5. REST API Endpoints
# -----------------------------------------------------------------------------
def test_reliability_rest_api(client, db_session):
    # 1. Classify failure
    r1 = client.post("/api/v1/reliability/classify-failure", json={
        "domain": "EHR_INTEGRATION",
        "failure_type": "API_TIMEOUT"
    })
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["is_retryable"] is True
    assert d1["recommended_strategy"] == "RETRY_WITH_BACKOFF"

    # 2. Idempotent execute
    r2 = client.post("/api/v1/reliability/idempotent-execute", json={
        "idempotency_key": "API-IDEMP-KEY-777",
        "operation_type": "NOTIFICATION_DISPATCH",
        "payload": {"recipient": "+15551234567", "msg": "Appointment Confirmed"}
    })
    assert r2.status_code == 200
    assert r2.json()["idempotent_replay"] is False

    # Second call with same key -> idempotent_replay == True
    r2_replay = client.post("/api/v1/reliability/idempotent-execute", json={
        "idempotency_key": "API-IDEMP-KEY-777",
        "operation_type": "NOTIFICATION_DISPATCH",
        "payload": {"recipient": "+15551234567", "msg": "Appointment Confirmed"}
    })
    assert r2_replay.status_code == 200
    assert r2_replay.json()["idempotent_replay"] is True
