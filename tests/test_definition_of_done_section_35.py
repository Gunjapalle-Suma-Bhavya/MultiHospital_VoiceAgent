"""
Unit and Integration Tests for Section 35: Definition of Done (DoD).

Validates:
1. Canonical 27-Stage Platform Journey:
   Hospital Registration -> Admin Approval -> Hospital Configuration ->
   Doctor Creation -> Calendar Configuration -> EHR Configuration ->
   Patient Registration -> AI Voice Conversation -> Intent Understanding ->
   Context Resolution -> Doctor Discovery -> Availability Check ->
   Patient Selection -> Appointment Booking -> EHR Integration ->
   External Verification -> State Synchronization -> Follow-Up Workflow ->
   Pre-Visit Questionnaire -> Structured Responses -> Doctor Review ->
   Notification -> Analytics -> Audit Trail -> Operational Monitoring ->
   Multi-Role Perspectives -> Definition of Done Verification.

2. Failure Scenario 1: Transient EHR Failure & Self-Healing Recovery:
   Booking Attempt -> EHR Integration Failure -> Classify Failure ->
   Retry -> External State Verification -> Recovery -> Verification ->
   Successful Completion.

3. Failure Scenario 2: Persistent EHR Failure, Reconciliation & Human Escalation:
   Booking Attempt -> EHR Integration Failure -> Retry Limit Reached ->
   External State Verification -> Reconciliation Required ->
   Human Escalation -> Operational Issue Record Created.

4. REST API endpoints for Section 35.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.models import (
    Base, Hospital, HospitalStatus, Doctor, PatientProfile, Appointment,
    AppointmentStatus, IntegrationVerificationRecord, PatientIntakeRecord,
    WorkflowInstance, NotificationRecord, AuditLog, OperationTrace,
    ReconciliationRecord, HumanEscalationRecord
)
from app.database.config import get_db
from app.workflows.definition_of_done_service import DefinitionOfDoneService

from sqlalchemy.pool import StaticPool

# In-memory test SQLite database with StaticPool
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# =============================================================================
# Test 1: Canonical 27-Stage DoD Journey
# =============================================================================

def test_canonical_27_stage_journey_execution(setup_db):
    result = DefinitionOfDoneService.execute_canonical_journey(
        db=setup_db,
        hospital_name="St. Jude Memorial Hospital",
        doctor_name="Dr. Sharma",
        patient_name="Patient A",
        patient_phone="+1-555-0199"
    )

    assert result["status"] == "SUCCESS"
    assert result["definition_of_done"] == "COMPLETE"
    assert result["total_stages"] == 27
    assert len(result["stages"]) == 27

    # Verify each stage sequentially
    expected_stage_names = [
        "Hospital Registration",
        "Admin Approval",
        "Hospital Configuration",
        "Doctor Creation",
        "Calendar Configuration",
        "EHR / Healthcare-System Configuration",
        "Patient Registration",
        "AI Voice Conversation",
        "Intent Understanding",
        "Context Resolution",
        "Doctor Discovery",
        "Availability Check",
        "Patient Selection",
        "Appointment Booking",
        "EHR Integration",
        "External Verification",
        "State Synchronization",
        "Follow-Up Workflow",
        "Pre-Visit Questionnaire",
        "Structured Responses",
        "Doctor Review",
        "Notification",
        "Analytics",
        "Audit Trail",
        "Operational Monitoring",
        "Multi-Role Perspectives",
        "Definition of Done Verification"
    ]

    for idx, expected_name in enumerate(expected_stage_names, start=1):
        stage = result["stages"][idx - 1]
        assert stage["stage_number"] == idx
        assert stage["stage_name"] == expected_name
        assert stage["status"] == "COMPLETED"

    # Verify database persistence of key entities
    hospital = setup_db.query(Hospital).filter(Hospital.name == "St. Jude Memorial Hospital").first()
    assert hospital is not None
    assert hospital.hospital_status == HospitalStatus.APPROVED
    assert hospital.is_active is True

    doctor = setup_db.query(Doctor).filter(Doctor.hospital_id == hospital.id).first()
    assert doctor is not None
    assert doctor.name == "Dr. Sharma"
    assert doctor.specialty == "Orthopedics"

    patient = setup_db.query(PatientProfile).filter(PatientProfile.phone_number == "+1-555-0199").first()
    assert patient is not None
    assert patient.full_name == "Patient A"

    appt = setup_db.query(Appointment).filter(Appointment.hospital_id == hospital.id).first()
    assert appt is not None
    assert appt.status == AppointmentStatus.CONFIRMED
    assert appt.is_ehr_verified is True

    verif = setup_db.query(IntegrationVerificationRecord).filter(IntegrationVerificationRecord.appointment_id == appt.id).first()
    assert verif is not None
    assert verif.is_verified is True

    intake = setup_db.query(PatientIntakeRecord).filter(PatientIntakeRecord.appointment_id == appt.id).first()
    assert intake is not None
    assert intake.is_patient_reported_only is True
    assert "shoulder" in intake.patient_reported_summary.lower()

    notifs = setup_db.query(NotificationRecord).all()
    assert len(notifs) >= 2
    roles = {n.recipient_role for n in notifs}
    assert "DOCTOR" in roles
    assert "PATIENT" in roles

    audit = setup_db.query(AuditLog).filter(AuditLog.event_type == "DOD_CANONICAL_JOURNEY_COMPLETED").first()
    assert audit is not None
    assert audit.status == "SUCCESS"
    assert audit.category == "OPERATIONAL_MONITORING"

    trace = setup_db.query(OperationTrace).filter(OperationTrace.operation_name == "DOD_27_STAGE_CANONICAL_JOURNEY").first()
    assert trace is not None
    assert trace.status == "COMPLETED"

    # Multi-Role Perspectives
    perspectives = result["perspectives"]
    assert "doctor" in perspectives
    assert "hospital_admin" in perspectives
    assert "platform_admin" in perspectives
    assert perspectives["hospital_admin"]["ehr_sync_status"] == "SYNCHRONIZED"


# =============================================================================
# Test 2: Failure Scenario 1 - Transient EHR Failure & Recovery
# =============================================================================

def test_failure_scenario_transient_recovery(setup_db):
    result = DefinitionOfDoneService.execute_failure_scenario_transient_recovery(db=setup_db)

    assert result["scenario_type"] == "TRANSIENT_FAILURE_SELF_HEALING_RECOVERY"
    assert result["outcome"] == "RECOVERED_AND_COMPLETED"
    assert result["total_steps"] == 8

    step_names = [s["name"] for s in result["steps"]]
    assert step_names == [
        "Booking Attempt",
        "EHR Integration Failure",
        "Classify Failure",
        "Retry",
        "External State Verification",
        "Recovery",
        "Verification",
        "Successful Completion"
    ]

    # Verify step classifications
    classify_step = result["steps"][2]
    assert classify_step["classification"]["category"] == "TRANSIENT_NETWORK_ERROR"
    assert classify_step["classification"]["is_retryable"] is True

    # Verify retry and verification
    retry_step = result["steps"][3]
    assert retry_step["status"] == "SUCCESS"

    verif_step = result["steps"][6]
    assert verif_step["result"] == "VERIFIED"

    complete_step = result["steps"][7]
    assert complete_step["internal_appointment_status"] == "CONFIRMED"
    assert complete_step["ehr_sync_status"] == "RECOVERED_AFTER_RETRY"

    # Verify audit persistence
    audit = setup_db.query(AuditLog).filter(AuditLog.event_type == "EHR_TRANSIENT_FAILURE_RECOVERED").first()
    assert audit is not None
    assert audit.category == "RELIABILITY"


# =============================================================================
# Test 3: Failure Scenario 2 - Persistent EHR Failure & Human Escalation
# =============================================================================

def test_failure_scenario_reconciliation_and_escalation(setup_db):
    result = DefinitionOfDoneService.execute_failure_scenario_reconciliation_escalation(db=setup_db)

    assert result["scenario_type"] == "PERSISTENT_FAILURE_RECONCILIATION_AND_ESCALATION"
    assert result["outcome"] == "ESCALATED_WITH_OPERATIONAL_RECORD"
    assert result["total_steps"] == 7

    step_names = [s["name"] for s in result["steps"]]
    assert step_names == [
        "Booking Attempt",
        "EHR Integration Failure",
        "Retry Limit Reached",
        "External State Verification",
        "Reconciliation Required",
        "Human Escalation",
        "Operational Issue Record Created"
    ]

    # Verify reconciliation and escalation entities created
    reconcil = setup_db.query(ReconciliationRecord).first()
    assert reconcil is not None
    assert reconcil.resolution_status == "PENDING_OPERATOR_ACTION"

    escal = setup_db.query(HumanEscalationRecord).first()
    assert escal is not None
    assert escal.trigger_reason == "EHR_INTEGRATION_FAILURE"
    assert escal.failure_count == 3
    assert escal.resolution_status == "ESCALATED"

    trace = setup_db.query(OperationTrace).filter(OperationTrace.operation_name == "EHR_PERSISTENT_FAILURE_ESCALATION").first()
    assert trace is not None
    assert trace.status == "ESCALATED"
    assert trace.reconciliation_occurred is True
    assert trace.escalated_to_human is True


# =============================================================================
# Test 4: REST API Endpoints for Section 35 Definition of Done
# =============================================================================

def test_dod_checklist_api(client):
    response = client.get("/api/v1/definition-of-done/checklist")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PROTOTYPE_COMPLETE"
    assert data["total_canonical_stages"] == 27
    assert len(data["canonical_stages"]) == 27
    assert len(data["failure_recovery_scenarios"]) == 2


def test_dod_execute_journey_api(client):
    payload = {
        "hospital_name": "City General Hospital",
        "doctor_name": "Dr. Sharma",
        "patient_name": "Patient A",
        "patient_phone": "+1-555-4422"
    }
    response = client.post("/api/v1/definition-of-done/execute-journey", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["definition_of_done"] == "COMPLETE"
    assert data["total_stages"] == 27


def test_dod_simulate_transient_failure_api(client):
    payload = {"mode": "TRANSIENT_RECOVERY"}
    response = client.post("/api/v1/definition-of-done/simulate-failure-recovery", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_type"] == "TRANSIENT_FAILURE_SELF_HEALING_RECOVERY"
    assert data["outcome"] == "RECOVERED_AND_COMPLETED"
    assert data["total_steps"] == 8


def test_dod_simulate_escalation_failure_api(client):
    payload = {"mode": "RECONCILIATION_ESCALATION"}
    response = client.post("/api/v1/definition-of-done/simulate-failure-recovery", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_type"] == "PERSISTENT_FAILURE_RECONCILIATION_AND_ESCALATION"
    assert data["outcome"] == "ESCALATED_WITH_OPERATIONAL_RECORD"
    assert data["total_steps"] == 7
