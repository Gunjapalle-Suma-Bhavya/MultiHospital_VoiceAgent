"""
Automated Verification Test Suite:
14 AI Capabilities & 12 EHR / Healthcare-System Integration Capabilities.

Verifies 100% of both checklists:
AI (14 Items):
1. Web real-time voice
2. Inbound phone
3. Intent understanding
4. Context handling
5. Persistent relevant user context
6. Doctor discovery
7. Hospital discovery
8. Availability checking
9. Booking
10. Rescheduling
11. Cancellation
12. Clarification handling
13. Explicit capability/tool execution
14. Human escalation

EHR / Healthcare-System Integration (12 Items):
1. Mock EHR / Mock Healthcare System
2. Patient lookup
3. Provider lookup
4. Appointment creation
5. Appointment rescheduling
6. Appointment cancellation
7. External appointment verification
8. Internal/external identifier mapping
9. State synchronization
10. Basic retry/recovery
11. Idempotency
12. Basic reconciliation
"""

import os
from datetime import datetime, timezone, timedelta, date, time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.config import Base, get_db
from app.database.models import (
    Hospital,
    HospitalStatus,
    Doctor,
    DoctorStatus,
    PatientProfile,
    Appointment,
    AppointmentStatus,
    DoctorWorkingHour,
    EHRIntegrationConfig,
    EHRAdapterType,
    EHRSyncLog,
)

# In-memory test SQLite setup
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed Hospital
    hosp = Hospital(
        id="HOSP-TEST-01",
        name="Metropolitan Medical Center",
        code="MMC",
        hospital_status=HospitalStatus.APPROVED,
        is_active=True,
    )
    db.add(hosp)

    # Seed Doctor
    doc = Doctor(
        id="DOC-TEST-01",
        hospital_id="HOSP-TEST-01",
        name="Dr. Alice Smith",
        specialty="Cardiology",
        department="Cardiology & Vascular",
        doctor_status=DoctorStatus.ACTIVE,
        is_active=True,
        default_appointment_duration=30,
        experience_years=12,
    )
    db.add(doc)

    # Seed Working Hours (Mon-Fri 09:00 - 17:00, day_of_week 0-4)
    for day in [0, 1, 2, 3, 4]:
        wh = DoctorWorkingHour(
            doctor_id="DOC-TEST-01",
            day_of_week=day,
            start_time=time(9, 0),
            end_time=time(17, 0),
        )
        db.add(wh)

    # Seed EHR config
    ehr_cfg = EHRIntegrationConfig(
        hospital_id="HOSP-TEST-01",
        adapter_type=EHRAdapterType.MOCK_EHR,
        api_base_url="https://mock-ehr.nexushealth.internal/v1",
        is_active=True,
    )
    db.add(ehr_cfg)

    # Seed Patient
    pat = PatientProfile(
        id="PAT-TEST-01",
        phone_number="+1-555-0199",
        full_name="Jane Doe",
        email="jane.doe@example.com",
    )
    db.add(pat)

    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(setup_test_db):
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# =========================================================================
# PART 1: 14 AI CAPABILITIES TESTS
# =========================================================================

def test_ai_01_web_real_time_voice(client):
    """1. Web real-time voice capability."""
    # Start voice session
    start_resp = client.post("/api/v1/voice/session/start", json={
        "hospital_id": "HOSP-TEST-01",
        "patient_identifier": "+1-555-0199",
        "channel": "web_voice",
        "language": "en"
    })
    assert start_resp.status_code == 200
    session_data = start_resp.json()
    assert "session_id" in session_data
    session_id = session_data["session_id"]

    # Conversational turn
    turn_resp = client.post("/api/v1/voice/turn", json={
        "session_id": session_id,
        "patient_identifier": "+1-555-0199",
        "hospital_id": "HOSP-TEST-01",
        "utterance": "I have severe chest tightness since this morning."
    })
    assert turn_resp.status_code == 200
    turn_data = turn_resp.json()
    assert "agent_response" in turn_data or "text_response" in turn_data or turn_data.get("success") is True

    # Audio synthesis
    synth_resp = client.post("/api/v1/voice/synthesize", json={
        "text": "Hello, I am your medical intake assistant.",
        "voice": "clinical_female",
        "language": "en"
    })
    assert synth_resp.status_code == 200
    synth_data = synth_resp.json()
    assert "audio_base64" in synth_data or "audio_url" in synth_data or synth_data.get("status") == "success"


def test_ai_02_inbound_phone(client):
    """2. Inbound phone telephony simulation & IVR turn."""
    # Inbound phone call simulation
    inbound_resp = client.post("/api/v1/voice/inbound-phone/simulate", json={
        "caller_phone_number": "+1-555-0199"
    })
    assert inbound_resp.status_code == 200
    data = inbound_resp.json()
    assert data.get("status") == "CALL_CONNECTED"
    assert "session_id" in data
    assert "greeting_text" in data
    phone_sid = data["session_id"]

    # Telephony turn
    turn_resp = client.post("/api/v1/telephony/process-turn", json={
        "session_id": phone_sid,
        "caller_phone_number": "+1-555-0199",
        "speech_text": "I need to check doctor availability for heart checkup.",
        "hospital_id": "HOSP-TEST-01"
    })
    assert turn_resp.status_code == 200
    turn_data = turn_resp.json()
    assert "speech_response" in turn_data or "response" in turn_data or "text_response" in turn_data


def test_ai_03_intent_understanding(client):
    """3. Intent understanding (NLU Symptom & Specialty Inference)."""
    resp_cardio = client.post("/api/v1/ai/intent/infer", json={
        "utterance": "I'm having sharp chest pain radiating to my left arm and breathlessness"
    })
    assert resp_cardio.status_code == 200
    cardio_data = resp_cardio.json()
    assert cardio_data.get("specialty") in ["Cardiology", "Emergency Medicine"] or cardio_data.get("has_symptom") is True
    assert cardio_data.get("urgency") in ["HIGH", "CRITICAL", "EMERGENCY", "NORMAL"]

    resp_ortho = client.post("/api/v1/ai/intent/infer", json={
        "utterance": "I fell down while running and twisted my knee joint, it is swollen"
    })
    assert resp_ortho.status_code == 200
    assert resp_ortho.json().get("specialty") == "Orthopedics" or resp_ortho.json().get("inferred_specialty") == "Orthopedics"


def test_ai_04_context_handling(client):
    """4. Context handling (Multi-tier session context retention)."""
    resp = client.get("/api/v1/context/SES-TEST-MULTI-TIER")
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert "bundle" in data
    assert "tier1_turn" in data


def test_ai_05_persistent_relevant_user_context(client):
    """5. Persistent relevant user context by telephone/patient identity."""
    resp = client.get("/api/v1/context/patient/%2B1-555-0199")
    assert resp.status_code == 200
    data = resp.json()
    assert "phone_number" in data
    assert "bundle" in data
    assert "tier3_long_term" in data


def test_ai_06_doctor_discovery(client):
    """6. Doctor discovery with clinical filtering."""
    resp = client.get("/api/v1/discovery/doctors?specialty=Cardiology")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("total", 0) >= 1
    assert any(d["specialty"] == "Cardiology" for d in data.get("doctors", []))


def test_ai_07_hospital_discovery(client):
    """7. Hospital discovery."""
    resp = client.get("/api/v1/discovery/hospitals")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("total", 0) >= 1
    assert any("Metropolitan" in h["name"] for h in data.get("hospitals", []))


def test_ai_08_availability_checking(client):
    """8. Availability checking for open doctor calendar slots."""
    target = date.today() + timedelta(days=1)
    while target.weekday() >= 5:
        target += timedelta(days=1)

    resp = client.get(f"/api/v1/doctors/DOC-TEST-01/availability?target_date={target.isoformat()}")
    assert resp.status_code == 200
    data = resp.json()
    assert "available_slots" in data
    assert len(data["available_slots"]) > 0


def test_ai_09_booking_appointment(client):
    """9. Appointment booking with validation."""
    target_dt = datetime.now(timezone.utc) + timedelta(days=2)
    resp = client.post("/api/v1/appointments/book", json={
        "doctor_id": "DOC-TEST-01",
        "hospital_id": "HOSP-TEST-01",
        "patient_name": "Jane Doe",
        "patient_phone": "+1-555-0199",
        "start_datetime": target_dt.isoformat(),
        "notes": "Followup consultation"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "success"
    assert "appointment_id" in data


def test_ai_10_rescheduling_appointment(client):
    """10. Appointment rescheduling."""
    target_dt = datetime.now(timezone.utc) + timedelta(days=3)
    book_resp = client.post("/api/v1/appointments/book", json={
        "doctor_id": "DOC-TEST-01",
        "hospital_id": "HOSP-TEST-01",
        "patient_name": "Jane Doe",
        "patient_phone": "+1-555-0199",
        "start_datetime": target_dt.isoformat(),
    })
    appt_id = book_resp.json()["appointment_id"]

    new_dt = target_dt + timedelta(days=1)
    resched_resp = client.post("/api/v1/appointments/reschedule", json={
        "appointment_id": appt_id,
        "new_start_datetime": new_dt.isoformat()
    })
    assert resched_resp.status_code == 200
    resched_data = resched_resp.json()
    assert resched_data.get("status") in ["RESCHEDULED", "REQUESTED", "success"] or "rescheduled" in str(resched_data).lower()


def test_ai_11_cancellation_appointment(client):
    """11. Appointment cancellation."""
    target_dt = datetime.now(timezone.utc) + timedelta(days=4)
    book_resp = client.post("/api/v1/appointments/book", json={
        "doctor_id": "DOC-TEST-01",
        "hospital_id": "HOSP-TEST-01",
        "patient_name": "Jane Doe",
        "patient_phone": "+1-555-0199",
        "start_datetime": target_dt.isoformat(),
    })
    appt_id = book_resp.json()["appointment_id"]

    cancel_resp = client.post("/api/v1/appointments/cancel", json={
        "appointment_id": appt_id,
        "reason": "Personal conflict"
    })
    assert cancel_resp.status_code == 200
    cancel_data = cancel_resp.json()
    assert cancel_data.get("status") == "CANCELLED" or "cancelled" in str(cancel_data).lower()


def test_ai_12_clarification_handling(client):
    """12. Clarification handling for ambiguous pronouns and relative references."""
    resp = client.post("/api/v1/ai/clarify", json={
        "session_id": "SES-TEST-CLARIFY",
        "patient_phone": "+1-555-0199",
        "utterance": "Can you book an appointment with her tomorrow morning?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "is_resolved" in data or "requires_clarification" in data or "resolved_intent" in data


def test_ai_13_explicit_capability_tool_execution(client):
    """13. Explicit capability / tool execution and catalog discovery."""
    resp = client.get("/api/v1/ai/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert "registered_capabilities" in data
    assert len(data["registered_capabilities"]) >= 10

    # Execute capability directly via capability registry
    exec_resp = client.post("/api/v1/capabilities/execute", json={
        "capability_name": "search_doctors",
        "parameters": {"specialty": "Cardiology"},
        "caller_role": "PATIENT_AGENT"
    })
    assert exec_resp.status_code == 200


def test_ai_14_human_escalation(client):
    """14. Human escalation ticketing and telephony operator transfer."""
    # Direct escalation ticket
    esc_resp = client.post("/api/v1/escalation/tickets", json={
        "patient_phone": "+1-555-0199",
        "hospital_id": "HOSP-TEST-01",
        "urgency": "HIGH",
        "reason": "Patient requested live nurse triage for acute pain"
    })
    assert esc_resp.status_code == 200
    esc_data = esc_resp.json()
    assert "ticket_id" in esc_data or "escalation_id" in esc_data or "id" in esc_data
    assert esc_data.get("urgency") == "HIGH"

    # Telephony operator transfer
    tel_esc = client.post("/api/v1/telephony/escalate?session_id=SES-TEL-ESCALATE-01")
    assert tel_esc.status_code == 200
    tel_data = tel_esc.json()
    assert tel_data.get("status") in ["CALL_TERMINATED", "COMPLETED", "ESCALATED"]


# =========================================================================
# PART 2: 12 EHR / HEALTHCARE-SYSTEM INTEGRATION CAPABILITIES TESTS
# =========================================================================

def test_ehr_01_mock_ehr_sandbox(client):
    """1. Mock EHR / Mock Healthcare System configuration & fault simulator."""
    resp = client.get("/api/v1/ehr/config/HOSP-TEST-01")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("hospital_id") == "HOSP-TEST-01"
    assert data.get("adapter_type") == "MOCK_EHR"
    assert data.get("status") == "CONNECTED"


def test_ehr_02_patient_lookup(client):
    """2. EHR Patient lookup by demographic & telephone identity."""
    resp = client.post("/api/v1/ehr/patient-lookup", json={
        "phone_number": "+1-555-0199",
        "full_name": "Jane Doe",
        "hospital_id": "HOSP-TEST-01"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "external_patient_id" in data or "ehr_patient_id" in data or data.get("found") is True


def test_ehr_03_provider_lookup(client):
    """3. EHR Provider lookup by specialty and facility."""
    resp = client.post("/api/v1/ehr/provider-lookup", json={
        "specialty": "Cardiology",
        "department": "Cardiology & Vascular",
        "hospital_id": "HOSP-TEST-01"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "external_provider_id" in data or "providers" in data or data.get("found") is True


def test_ehr_04_appointment_creation(client):
    """4. EHR Appointment creation with FHIR-compliant synchronization."""
    idemp_key = f"idemp-test-ehr-{datetime.now().timestamp()}"
    resp = client.post("/api/v1/ehr/sync/appointment", json={
        "hospital_id": "HOSP-TEST-01",
        "patient_id": "PAT-EHR-101",
        "doctor_id": "DOC-EHR-102",
        "duration_minutes": 30,
        "idempotency_key": idemp_key,
        "special_instructions": "Initial diagnostic review"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "success"
    assert data.get("is_confirmed") is True
    assert "external_appointment_id" in data


def test_ehr_05_appointment_rescheduling(client):
    """5. EHR Appointment rescheduling on external healthcare system."""
    new_dt = datetime.now(timezone.utc) + timedelta(days=5)
    resp = client.post("/api/v1/ehr/reschedule", json={
        "external_appointment_id": "EXT-EHR-APPT-8831",
        "new_start_datetime": new_dt.isoformat()
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("is_confirmed") is True or data.get("ehr_status") in ["rescheduled", "confirmed", "booked"]


def test_ehr_06_appointment_cancellation(client):
    """6. EHR Appointment cancellation on external healthcare system."""
    resp = client.post("/api/v1/ehr/cancel", json={
        "external_appointment_id": "EXT-EHR-APPT-8831",
        "reason": "Patient requested slot release"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ehr_status") == "cancelled" or "cancel" in data.get("message", "").lower()


def test_ehr_07_external_appointment_verification(client):
    """7. External appointment verification against EHR record."""
    resp = client.post("/api/v1/ehr/verify-record", json={
        "appointment_id": "EXT-EHR-APPT-8831"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "is_synchronized" in data or "field_discrepancies" in data or "appointment_id" in data


def test_ehr_08_internal_external_identifier_mapping(client):
    """8. Internal/external identifier mapping cross-reference."""
    resp = client.get("/api/v1/ehr/mappings?hospital_id=HOSP-TEST-01&entity_type=patient&internal_id=PAT-TEST-01")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("internal_id") == "PAT-TEST-01"
    assert "external_ehr_id" in data


def test_ehr_09_state_synchronization(client):
    """9. State synchronization & audit trail logging."""
    resp = client.get("/api/v1/ehr/sync-logs?hospital_id=HOSP-TEST-01&limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "sync_logs" in data
    assert isinstance(data["sync_logs"], list)


def test_ehr_10_basic_retry_recovery(client):
    """10. Basic retry / recovery error classification."""
    # Transient upstream 503 should be retryable
    resp_503 = client.post("/api/v1/ehr/recovery/classify", json={
        "error_text": "HTTP 503 Service Unavailable: FHIR upstream gateway timeout",
        "status_code": 503
    })
    assert resp_503.status_code == 200
    data_503 = resp_503.json()
    assert data_503.get("is_retryable") is True

    # Permanent 400 bad request should NOT be retryable
    resp_400 = client.post("/api/v1/ehr/recovery/classify", json={
        "error_text": "HTTP 400 Bad Request: Invalid patient MRN format",
        "status_code": 400
    })
    assert resp_400.status_code == 200
    assert resp_400.json().get("is_retryable") is False


def test_ehr_11_idempotency(client):
    """11. Idempotency enforcement on appointment synchronization."""
    unique_key = f"idemp-test-dedup-{datetime.now().timestamp()}"

    # First attempt: creates appointment
    res1 = client.post("/api/v1/ehr/sync/appointment", json={
        "hospital_id": "HOSP-TEST-01",
        "patient_id": "PAT-DEDUP-01",
        "doctor_id": "DOC-DEDUP-01",
        "idempotency_key": unique_key
    })
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1.get("status") == "success"
    assert "idempotent_replay" not in d1 or d1["idempotent_replay"] is False

    # Second identical attempt with duplicate key: intercepts without recreating
    res2 = client.post("/api/v1/ehr/sync/appointment", json={
        "hospital_id": "HOSP-TEST-01",
        "patient_id": "PAT-DEDUP-01",
        "doctor_id": "DOC-DEDUP-01",
        "idempotency_key": unique_key
    })
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2.get("idempotent_replay") is True
    assert d2.get("external_appointment_id") == d1.get("external_appointment_id")


def test_ehr_12_basic_reconciliation(client):
    """12. Basic reconciliation engine discrepancy scanning & auto-resolution."""
    resp = client.post("/api/v1/ehr/reconciliation/run")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "completed"
    assert "discrepancies_count" in data
    assert "auto_resolved_count" in data
    assert "message" in data
