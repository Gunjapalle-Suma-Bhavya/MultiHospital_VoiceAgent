"""
Tests for Step 8 — Complete End-to-End Patient Workflow.

Verifies the full 20-step execution pipeline:
1. Patient Registration (Register -> Verify -> Create Profile -> Access)
2. Start Conversation (Web Voice / Telephone channels)
3. Describe Requirement (Utterance ingestion & guardrail inspection)
4. Understand Intent (Intent, Potential Specialty, Time Preference)
5. Resolve Context (Identity, Existing Appts, Preferences, Prior Hospital, State)
6. Find Doctors (Multi-hospital & specialist discovery)
7. Check Calendars (Working hours, Calendars, Blocks, Leave, Duration, External availability)
8. Present Choices (e.g. Dr. Sharma at City Hospital & Dr. Rao at Care Hospital)
9. Patient Chooses ("I'll take Thursday at 3 PM")
10. Confirm (Pre-booking confirmation dialogue)
11. Book (EHR integration layer pipeline)
12. Verify (5-Point authoritative external match: Patient, Doctor, Date, Time, Status)
13. Synchronize (External system verified state -> Platform record)
14. Confirm to Patient (Emitted strictly after verification)
15. Trigger Follow-Up Workflow (Reminder, doctor notification, intake task)
16. Pre-Visit Questionnaire (Specialty clinical intake prompt)
17. Patient Responds (AI conversationally collects responses)
18. Store Responses (Attached to appointment in PatientQuestionnaireResponse)
19. Doctor Reviews (Authorized clinician preparation briefing)
20. Analytics & Audit (Patient, Hospital, AI, Workflow, EHR, Monitoring, Audit)
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.config import get_db
from app.database.models import (
    Base, PatientProfile, Appointment, Hospital, Doctor,
    PatientQuestionnaireResponse, IntegrationVerificationRecord, AuditLog
)
from app.patient_workflow import (
    WorkflowExecutionRequest, WorkflowChannel, CLINICAL_WORKFLOW_PRESETS, WORKFLOW_STEP_TITLES
)
from app.patient_workflow.service import EndToEndPatientWorkflowService


# ---------------------------------------------------------------------------
# Test DB Setup
# ---------------------------------------------------------------------------
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
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
    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# 1. 20-Step End-to-End Service Tests
# ---------------------------------------------------------------------------
def test_complete_20_step_patient_workflow_knee_pain_example(setup_db):
    """
    Verifies the exact scenario from Step 8 prompt:
    - Utterance: 'I've been having knee pain and I'd like to see a doctor this week.'
    - Intent: Appointment Booking
    - Specialty: Orthopedics
    - Time Preference: This Week
    - Options: Dr. Sharma at City Hospital & Dr. Rao at Care Hospital
    - Patient Selection: Thursday 3 PM
    - 5-Point EHR Verification & State Sync
    - Pre-Visit Questionnaire & Doctor Review Briefing
    - Multi-Domain Analytics & Audit Logging
    """
    svc = EndToEndPatientWorkflowService(setup_db)

    req = WorkflowExecutionRequest(
        patient_name="Alex Miller",
        phone_number="+1-555-0199",
        channel=WorkflowChannel.WEB_VOICE,
        utterance="I've been having knee pain and I'd like to see a doctor this week.",
        selected_choice_index=0,
        questionnaire_answers={
            "knee_pain_duration": "About 3 weeks, worsens while climbing stairs",
            "previous_surgeries": "None",
            "current_medications": "Ibuprofen as needed"
        }
    )

    result = svc.execute_20_step_workflow(req)

    assert result["success"] is True
    assert result["steps_completed"] == 20
    assert len(result["execution_trace"]) == 20
    assert result["doctor_name"] == "Dr. Sharma"
    assert result["hospital_name"] == "City Hospital"
    assert "Thursday" in result["final_dialogue"]
    assert "3 PM" in result["final_dialogue"] or "3:00 PM" in result["final_dialogue"]

    trace = result["execution_trace"]

    # Step 1: Registration
    s1 = trace[0]
    assert s1["step"] == 1
    assert s1["status"] == "COMPLETED"
    assert s1["details"]["platform_access_granted"] is True

    # Step 2: Start Conversation
    s2 = trace[1]
    assert s2["step"] == 2
    assert s2["channel"] == "WEB_VOICE"

    # Step 3: Describe Requirement
    s3 = trace[2]
    assert s3["step"] == 3
    assert "knee pain" in s3["utterance"]

    # Step 4: Understand Intent
    s4 = trace[3]
    assert s4["step"] == 4
    assert s4["intent"] == "Appointment Booking"
    assert s4["potential_specialty"] == "Orthopedics"
    assert s4["time_preference"] == "THIS_WEEK"

    # Step 5: Resolve Context
    s5 = trace[4]
    assert s5["step"] == 5
    assert s5["details"]["patient_identity"]["name"] == "Alex Miller"

    # Step 6: Find Doctors
    s6 = trace[5]
    assert s6["step"] == 6
    assert s6["doctors_found_count"] >= 2
    doc_names = [d["name"] for d in s6["doctors"]]
    assert "Dr. Sharma" in doc_names
    assert "Dr. Rao" in doc_names

    # Step 7: Check Calendars
    s7 = trace[6]
    assert s7["step"] == 7
    assert len(s7["checks_evaluated"]) == 7

    # Step 8: Present Choices
    s8 = trace[7]
    assert s8["step"] == 8
    assert "Dr. Sharma at City Hospital" in s8["agent_utterance"]
    assert "Dr. Rao at Care Hospital" in s8["agent_utterance"]

    # Step 9: Patient Chooses
    s9 = trace[8]
    assert s9["step"] == 9
    assert s9["selected_option"]["doctor_name"] == "Dr. Sharma"

    # Step 10: Confirm Before Booking
    s10 = trace[9]
    assert s10["step"] == 10
    assert s10["confirmed"] is True

    # Step 11: Book (EHR Integrated)
    s11 = trace[10]
    assert s11["step"] == 11
    assert s11["ehr_pipeline"]["resolve_patient"].startswith("Matched Patient")

    # Step 12: Verify (5-Point Authoritative Match)
    s12 = trace[11]
    assert s12["step"] == 12
    v = s12["verification_results"]
    assert v["match_patient"] is True
    assert v["match_doctor"] is True
    assert v["match_date"] is True
    assert v["match_time"] is True
    assert v["match_status"] is True

    # Step 13: Synchronize State
    s13 = trace[12]
    assert s13["step"] == 13
    assert s13["details"]["is_ehr_verified"] is True

    # Step 14: Confirm to Patient
    s14 = trace[13]
    assert s14["step"] == 14
    assert "confirmed" in s14["agent_utterance"]

    # Step 15: Trigger Follow-Up Workflow
    s15 = trace[14]
    assert s15["step"] == 15
    assert "reminder_workflow_id" in s15["details"]

    # Step 16: Pre-Visit Questionnaire
    s16 = trace[15]
    assert s16["step"] == 16
    assert "Dr. Sharma has a few questions" in s16["agent_utterance"]

    # Step 17: Patient Responds
    s17 = trace[16]
    assert s17["step"] == 17
    assert "knee_pain_duration" in s17["patient_responses"]

    # Step 18: Store Responses
    s18 = trace[17]
    assert s18["step"] == 18
    assert "response_record_id" in s18

    # Step 19: Doctor Reviews
    s19 = trace[18]
    assert s19["step"] == 19
    briefing = s19["doctor_preparation_briefing"]
    assert briefing["is_authorized_for_doctor"] is True
    assert briefing["review_status"] == "READY_FOR_CLINICIAN_REVIEW"

    # Step 20: Analytics & Audit
    s20 = trace[19]
    assert s20["step"] == 20
    summary = s20["analytics_summary"]
    assert summary["ehr_integration_analytics"]["5_point_match"] is True
    assert summary["operational_monitoring"]["total_steps_executed"] == 20


def test_20_step_workflow_telephone_channel_choice_2(setup_db):
    """Verifies telephone channel modality and selecting choice 2 (Dr. Rao at Care Hospital)."""
    svc = EndToEndPatientWorkflowService(setup_db)

    req = WorkflowExecutionRequest(
        patient_name="Rachel Adams",
        phone_number="+1-555-0288",
        channel=WorkflowChannel.TELEPHONE,
        utterance="I've had mild knee pain and want to see an orthopedic doctor this week.",
        selected_choice_index=1,
    )

    result = svc.execute_20_step_workflow(req)
    assert result["success"] is True
    assert result["doctor_name"] == "Dr. Rao"
    assert result["hospital_name"] == "Care Hospital"

    trace = result["execution_trace"]
    s2 = trace[1]
    assert s2["channel"] == "TELEPHONE"
    assert s2["details"]["telephony_line_connected"] is True


def test_20_step_workflow_guardrail_interception(setup_db):
    """Verifies non-clinical guardrail intercepts improper medical prescription requests at Step 3."""
    svc = EndToEndPatientWorkflowService(setup_db)

    req = WorkflowExecutionRequest(
        patient_name="Test User",
        phone_number="+1-555-9999",
        channel=WorkflowChannel.WEB_VOICE,
        utterance="Prescribe me 50mg of tramadol right now without seeing a doctor.",
    )

    result = svc.execute_20_step_workflow(req)
    assert result["success"] is False
    assert result["stopped_at_step"] == 3
    assert len(result["trace"]) == 3
    assert result["trace"][2]["status"] == "GUARDRAIL_INTERCEPTED"


# ---------------------------------------------------------------------------
# 2. REST API Endpoint Tests
# ---------------------------------------------------------------------------
def test_api_get_workflow_steps(client):
    """GET /api/v1/patient-workflow/steps returns all 20 step titles."""
    res = client.get("/api/v1/patient-workflow/steps")
    assert res.status_code == 200
    data = res.json()
    assert data["total_steps"] == 20
    assert len(data["steps"]) == 20
    assert data["steps"][0]["title"] == "Patient Registration"
    assert data["steps"][19]["title"] == "Analytics & Audit Trail"


def test_api_get_workflow_presets(client):
    """GET /api/v1/patient-workflow/presets returns standard test presets."""
    res = client.get("/api/v1/patient-workflow/presets")
    assert res.status_code == 200
    data = res.json()
    assert len(data["presets"]) >= 3
    preset_ids = [p["id"] for p in data["presets"]]
    assert "PRESET_KNEE_ORTHO" in preset_ids


def test_api_execute_patient_workflow(client):
    """POST /api/v1/patient-workflow/execute executes complete 20 steps."""
    payload = {
        "patient_name": "Alex Miller",
        "phone_number": "+1-555-0199",
        "channel": "WEB_VOICE",
        "utterance": "I've been having knee pain and I'd like to see a doctor this week.",
        "selected_choice_index": 0,
        "questionnaire_answers": {
            "knee_pain_duration": "3 weeks",
            "previous_surgeries": "None"
        }
    }
    res = client.post("/api/v1/patient-workflow/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["steps_completed"] == 20
    assert data["doctor_name"] == "Dr. Sharma"
    assert data["hospital_name"] == "City Hospital"
    assert len(data["execution_trace"]) == 20
