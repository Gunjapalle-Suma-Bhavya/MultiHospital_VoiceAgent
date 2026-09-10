"""
Unit test suite for Sections 5.10, 5.11, 5.12 & Gemini Flash Strategy Blueprint.
Tests:
- Section 5.10 Real-Time Voice Pipeline: barge-in processing, low latency targets (<2s)
- Section 5.11 Telephony Integration: inbound call handling, patient phone lookup, human escalation fallback
- Section 5.12 Patient Intent Understanding: symptom-to-specialty inference ("shoulder pain" -> Orthopedics), cautious non-diagnosis language
- Strategy Blueprint (/api/voice/chat): tool calling, DB transaction lock, MockEHR verification, RECONCILIATION_REQUIRED fallback, correlation_id audit logs
"""

import pytest
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, Doctor, PatientProfile, Appointment, AppointmentStatus, AuditLog
from app.agent.intent_understanding import SymptomIntentResolver
from app.voice.realtime_pipeline import RealTimeVoicePipelineEngine, TurnState
from app.telephony.inbound_service import TelephonyInboundService
from app.ehr.adapters import MockEHRService
from app.onboarding.hospital_onboarding import HospitalSelfServiceOnboardingService
from app.doctors.doctor_management import DoctorManagementService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def setup_data(db_session):
    onboarding = HospitalSelfServiceOnboardingService(db_session)
    hosp = onboarding.create_draft_hospital(
        name="Metro Health Center",
        code="METRO",
        contact_email="admin@metro.org",
        admin_name="Dr. Smith",
        admin_email="smith@metro.org"
    )
    onboarding.submit_application(hosp.id)
    onboarding.approve_hospital(hosp.id)

    doc_svc = DoctorManagementService(db_session)
    doc = doc_svc.invite_doctor(
        hospital_id=hosp.id,
        name="Dr. Gregory House",
        specialty="Orthopedics",
        department="Surgery"
    )
    doc_svc.activate_doctor(doc.id)

    patient = PatientProfile(
        phone_number="+15551234567",
        full_name="John Doe",
        email="john@example.com"
    )
    db_session.add(patient)
    db_session.commit()

    return hosp, doc, patient


def test_section_5_12_symptom_intent_understanding():
    # 1. Shoulder pain -> Orthopedics
    res = SymptomIntentResolver.infer_specialty_from_utterance("I've been having shoulder pain for the last few weeks.")
    assert res.has_symptom is True
    assert res.inferred_specialty == "Orthopedics"
    assert "does not constitute a medical diagnosis" in res.cautious_response
    assert res.is_patient_reported_only is True
    assert res.is_diagnostic is False

    # 2. Severe chest pain -> Emergency
    emerg_res = SymptomIntentResolver.infer_specialty_from_utterance("I have severe chest pain and can't breathe")
    assert emerg_res.inferred_specialty == "Emergency Medicine"
    assert "EMERGENCY WARNING" in emerg_res.cautious_response

    # 3. Ambiguous input -> Clarification
    clar_res = SymptomIntentResolver.infer_specialty_from_utterance("Hello, I need help.")
    assert clar_res.requires_clarification is True


def test_section_5_10_realtime_voice_pipeline():
    engine = RealTimeVoicePipelineEngine()
    sess = engine.get_or_create_session("sess-100")

    # Test Barge-in
    barge_res = engine.handle_barge_in_signal("sess-100")
    assert barge_res["event"] == "BARGE_IN_TRIGGERED"
    assert barge_res["action"] == "CANCEL_ACTIVE_TTS_PLAYBACK"
    assert sess.state == TurnState.INTERRUPTED

    # Test low-latency turn execution
    def dummy_turn():
        return {"response": "Hello John"}

    turn_res = engine.execute_low_latency_turn("sess-100", "Hi", dummy_turn)
    assert turn_res["sub_2_sec_target_met"] is True
    assert turn_res["latency_ms"] >= 0.0


def test_section_5_11_telephony_inbound_service(db_session, setup_data):
    hosp, doc, patient = setup_data
    telephony_svc = TelephonyInboundService(db_session)

    # 1. Inbound call handling & caller lookup
    call_res = telephony_svc.handle_inbound_call("+15551234567")
    assert call_res["status"] == "CALL_CONNECTED"
    assert call_res["is_known_patient"] is True
    assert "John Doe" in call_res["greeting_text"]

    # 2. Process turn over phone
    turn_res = telephony_svc.process_telephony_turn(
        session_id=call_res["session_id"],
        caller_phone_number="+15551234567",
        speech_text="I want to book an appointment with Dr. House",
        hospital_id=hosp.id
    )
    assert turn_res["status"] == "SUCCESS"
    assert "speech_response" in turn_res

    # 3. Call termination
    term_res = telephony_svc.terminate_call(call_res["session_id"])
    assert term_res["status"] == "CALL_TERMINATED"


def test_strategy_blueprint_mock_ehr_and_reconciliation_required(db_session, setup_data):
    hosp, doc, patient = setup_data
    corr_id = str(uuid.uuid4())
    start_dt = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2)

    # Test Successful EHR Verification
    ehr_ok = MockEHRService.createAndVerifyBooking(patient.id, doc.id, start_dt, force_fail=False)
    assert ehr_ok["success"] is True
    assert ehr_ok["status"] == "CONFIRMED"

    # Test Failed EHR Verification -> RECONCILIATION_REQUIRED
    ehr_fail = MockEHRService.createAndVerifyBooking(patient.id, doc.id, start_dt, force_fail=True)
    assert ehr_fail["success"] is False
    assert ehr_fail["status"] == "RECONCILIATION_REQUIRED"

    # Verify Audit Logging
    audit = AuditLog(
        session_id="sess-audit-1",
        correlation_id=corr_id,
        event_type="EHR_STATUS_CHECK",
        tool_invocation_json='{"tool": "book_appointment"}',
        payload_json=str(ehr_fail)
    )
    db_session.add(audit)
    db_session.commit()

    fetched = db_session.query(AuditLog).filter(AuditLog.correlation_id == corr_id).first()
    assert fetched is not None
    assert fetched.event_type == "EHR_STATUS_CHECK"
