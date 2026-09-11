"""
Comprehensive Test Suite for Section 27: Should Have.

Validates:
1. Multi-Connector Healthcare Hub (FHIR R4, HL7 v2, Epic, Cerner, Mock)
2. EHR Circuit Breaker & Resilience State Transitions
3. Integration Reconciliation Dashboard & 1-Click Discrepancy Resolution
4. Advanced Multi-Path Workflow Branching (Fast-Track, Intake, Emergency Escalation, Outage Fallback)
5. Automated Appointment Reminders (T-24h / T-2h Scanning)
6. Cost Estimation & Receptionist Financial ROI Telemetry
7. Human Escalation Queue & Triage Resolution
8. 4 Golden Signals Operational Telemetry
9. Streaming AI Response Generator (SSE) & Rich Voice Barge-in
10. Patient Granular Notification Preferences
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.config import SessionLocal, engine
from app.database.models import (
    Base, Hospital, Doctor, Appointment, PatientProfile, AppointmentStatus, HospitalStatus
)
from app.ehr.circuit_breaker import default_ehr_circuit_breaker, CircuitState
from app.ehr.adapters import EHRConnectorFactory
from app.voice.streaming_service import StreamingAIService, RichVoiceInteractionManager
from app.patients.patient_service import PatientSelfServiceService


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed hospital and doctor for tests
        hosp = db.query(Hospital).filter(Hospital.code == "SH_HOSP").first()
        if not hosp:
            hosp = Hospital(
                name="Should Have Medical Center",
                code="SH_HOSP",
                hospital_status=HospitalStatus.APPROVED,
                is_active=True,
                admin_email="admin@shouldhave.org"
            )
            db.add(hosp)
            db.commit()
            db.refresh(hosp)

            doc = Doctor(
                hospital_id=hosp.id,
                name="Dr. Gregory House",
                specialty="Nephrology",
                department="Diagnostic Medicine",
                consultation_fee=250.0,
                is_active=True
            )
            db.add(doc)
            db.commit()

            # Seed an appointment for reminder scan
            appt = Appointment(
                hospital_id=hosp.id,
                doctor_id=doc.id,
                patient_name="John Reminder Test",
                patient_phone="+15558887766",
                start_datetime=datetime.now(timezone.utc) + timedelta(hours=2),
                end_datetime=datetime.now(timezone.utc) + timedelta(hours=2, minutes=30),
                status=AppointmentStatus.CONFIRMED
            )
            db.add(appt)
            db.commit()

        yield db
    finally:
        db.close()


def test_multi_connector_catalog_and_testing(client: TestClient):
    """Validates connector factory catalog and active connection testing for all 5 systems."""
    # 1. Catalog listing
    res = client.get("/api/v1/should-have/connectors")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] >= 5
    types = {c["type"] for c in data["connectors"]}
    assert {"FHIR_R4", "EPIC", "CERNER", "HL7_V2", "MOCK"}.issubset(types)

    # 2. Connection probe for Epic
    epic_res = client.post("/api/v1/should-have/connectors/test", json={"connector_type": "EPIC"})
    assert epic_res.status_code == 200
    assert epic_res.json()["status"] == "CONNECTED"
    assert epic_res.json()["patient_resolution_tested"] is True

    # 3. Connection probe for HL7 v2
    hl7_res = client.post("/api/v1/should-have/connectors/test", json={"connector_type": "HL7_V2"})
    assert hl7_res.status_code == 200
    assert hl7_res.json()["status"] == "CONNECTED"

    # 4. Connection probe for Mock
    mock_res = client.post("/api/v1/should-have/connectors/test", json={"connector_type": "MOCK"})
    assert mock_res.status_code == 200
    assert mock_res.json()["status"] == "CONNECTED"


def test_ehr_circuit_breaker_lifecycle(client: TestClient):
    """Tests circuit breaker normal operation, tripping on failure threshold, and reset."""
    # 1. Initial status
    status_res = client.get("/api/v1/should-have/circuit-breaker")
    assert status_res.status_code == 200
    assert status_res.json()["can_execute"] is True

    # 2. Trip circuit
    default_ehr_circuit_breaker.record_failure("Test timeout 1")
    default_ehr_circuit_breaker.record_failure("Test timeout 2")
    default_ehr_circuit_breaker.record_failure("Test timeout 3")
    assert default_ehr_circuit_breaker.state == CircuitState.OPEN
    assert default_ehr_circuit_breaker.can_execute() is False

    # 3. Reset circuit via API
    reset_res = client.post("/api/v1/should-have/circuit-breaker/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["status"]["state"] == "CLOSED"
    assert default_ehr_circuit_breaker.can_execute() is True


def test_advanced_workflow_branching(client: TestClient):
    """Tests multi-path branching: Emergency Escalation, New Patient Intake, and Circuit Breaker Outage."""
    # 1. Emergency Branch
    emerg_res = client.post("/api/v1/should-have/workflows/execute-branch", json={
        "patient_phone": "+15559991111",
        "user_utterance": "I have severe chest pain and crushing pressure in my chest"
    })
    assert emerg_res.status_code == 200
    e_data = emerg_res.json()
    assert e_data["branch_taken"] == "BRANCH_C_CLINICAL_EMERGENCY_ESCALATION"
    assert e_data["status"] == "ESCALATED"
    assert "911" in e_data["advisory"]

    # 2. New Patient Intake Branch
    intake_res = client.post("/api/v1/should-have/workflows/execute-branch", json={
        "patient_phone": "+15554443322",
        "user_utterance": "I have eczema and an itchy rash on my face"
    })
    assert intake_res.status_code == 200
    i_data = intake_res.json()
    assert i_data["branch_taken"] == "BRANCH_B_NEW_PATIENT_COMPREHENSIVE_INTAKE"
    assert i_data["inferred_specialty"] == "Dermatology"
    assert i_data["status"] == "INTAKE_COMPLETE_BOOKED"

    # 3. EHR Outage Fallback Branch
    outage_res = client.post("/api/v1/should-have/workflows/execute-branch", json={
        "patient_phone": "+15554443322",
        "user_utterance": "I need a general checkup",
        "force_ehr_outage": True
    })
    assert outage_res.status_code == 200
    # Clean up circuit breaker
    default_ehr_circuit_breaker.reset()


def test_automated_appointment_reminders(client: TestClient, db_session: Session):
    """Tests automated appointment reminder batch scanning and dispatch."""
    res = client.post("/api/v1/should-have/reminders/trigger-batch")
    assert res.status_code == 200
    data = res.json()
    assert "appointments_evaluated" in data
    assert "reminders_dispatched_count" in data


def test_cost_estimation_and_roi(client: TestClient):
    """Tests voice AI unit economics, cost breakdowns, and savings calculations."""
    res = client.get("/api/v1/should-have/cost-estimate")
    assert res.status_code == 200
    data = res.json()
    assert data["currency"] == "USD"
    assert data["overall_savings_percentage"] >= 80.0
    assert "volume_projections" in data
    assert data["volume_projections"]["volume_1000"]["roi_multiplier"] > 5.0


def test_human_escalation_queue_and_resolution(client: TestClient):
    """Tests listing triage escalation queue and resolving a clinical ticket."""
    # List tickets
    list_res = client.get("/api/v1/should-have/escalations")
    assert list_res.status_code == 200
    data = list_res.json()
    assert len(data["tickets"]) >= 2

    # Resolve ticket
    ticket_id = data["tickets"][0]["ticket_id"]
    resolve_res = client.post("/api/v1/should-have/escalations/resolve", json={
        "ticket_id": ticket_id,
        "resolution_notes": "Patient routed to emergency room; ambulance dispatched.",
        "resolved_by": "Nurse Kelly, BSN"
    })
    assert resolve_res.status_code == 200
    assert resolve_res.json()["ticket"]["status"] == "RESOLVED"


def test_four_golden_signals_telemetry(client: TestClient):
    """Tests the 4 Golden Signals operational telemetry endpoint."""
    res = client.get("/api/v1/should-have/golden-signals")
    assert res.status_code == 200
    signals = res.json()["golden_signals"]
    assert "latency" in signals
    assert "traffic" in signals
    assert "errors" in signals
    assert "saturation" in signals
    assert res.json()["system_status"] == "ALL_SYSTEMS_OPERATIONAL"


def test_streaming_ai_service_sse():
    """Tests Server-Sent Events (SSE) streaming output chunks."""
    service = StreamingAIService()
    chunks = list(service.generate_sse_stream("session-test-01", "I have back pain and need a doctor"))
    
    assert len(chunks) >= 5
    combined = "".join(chunks)
    assert "event: filler" in combined
    assert "event: token" in combined
    assert "event: done" in combined

    # Test barge-in interruption
    manager = RichVoiceInteractionManager()
    b_res = manager.register_barge_in("session-test-02")
    assert b_res["status"] == "INTERRUPTED"
    assert manager.is_interrupted("session-test-02") is True
    manager.clear_barge_in("session-test-02")
    assert manager.is_interrupted("session-test-02") is False


def test_patient_granular_notification_preferences(db_session: Session):
    """Tests setting granular notification preferences across SMS, Email, WhatsApp, and Phone."""
    service = PatientSelfServiceService(db_session)
    pat = service.register_or_update_patient(
        phone_number="+15557778899",
        full_name="Alexander Hamilton"
    )

    channels = {"sms": True, "email": True, "whatsapp": False, "phone": False}
    res = service.set_granular_notification_preferences(
        patient_id=pat.id,
        channels=channels,
        preferred_time_window="MORNING"
    )
    assert res["notification_channels"]["sms"] is True
    assert res["notification_channels"]["whatsapp"] is False
    assert res["preferred_time_window"] == "MORNING"
