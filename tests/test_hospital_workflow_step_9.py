"""
Tests for Step 9 — Complete Hospital Workflow.

Verifies the full 23-stage hospital lifecycle:
1. Hospital Registers
2. Submits Details
3. Platform Admin Reviews
4. Hospital Approved
5. Hospital Admin Login
6. Configure Hospital
7. Create Doctors
8. Doctors Configure Calendars
9. Configure Availability
10. Configure Blocked Periods
11. Create Questionnaires
12. Configure EHR / Healthcare-System Integration
13. Configure Workflows
14. Publish Availability
15. Patients Discover Hospital
16. AI Books Appointments
17. EHR / External System Synchronization
18. Verification
19. Workflow Executes
20. Notifications
21. Doctors Receive Appointments
22. Doctors Review Pre-Visit Information
23. Hospital Monitors Analytics
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
    Base, Hospital, Doctor, HospitalStaff, HospitalDepartment, HospitalSpecialty,
    DoctorCalendar, DoctorWorkingHour, BlockedSlot, HospitalQuestionnaire,
    EHRIntegrationConfig, Appointment, IntegrationVerificationRecord,
    NotificationRecord, PatientQuestionnaireResponse
)
from app.hospital_workflow import (
    HospitalWorkflowExecutionRequest,
    HOSPITAL_WORKFLOW_PRESETS,
    HOSPITAL_WORKFLOW_STEP_TITLES,
)
from app.hospital_workflow.service import CompleteHospitalWorkflowService


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
# 1. 23-Stage Complete Hospital Service Tests
# ---------------------------------------------------------------------------
def test_complete_23_stage_hospital_workflow_service(setup_db):
    """Verifies all 23 stages execute in sequence with database persistence."""
    svc = CompleteHospitalWorkflowService(setup_db)

    req = HospitalWorkflowExecutionRequest(
        hospital_name="St. Jude Health System",
        hospital_code="STJUDE",
        contact_email="contact@stjude-health.org",
        admin_name="Dr. Marcus Vance",
        admin_email="marcus.vance@stjude-health.org",
        department_name="Cardiovascular Sciences",
        specialty_name="Cardiology",
        doctor_name="Dr. Olivia Chen",
        doctor_email="olivia.chen@stjude-health.org",
        ehr_adapter_type="MOCK_EHR",
    )

    result = svc.execute_23_step_workflow(req)

    assert result["success"] is True
    assert result["stages_completed"] == 23
    assert len(result["execution_trace"]) == 23
    assert result["hospital_status"] == "APPROVED"
    assert result["doctor_name"] == "Dr. Olivia Chen"
    assert "appointment_id" in result
    assert "external_appointment_id" in result

    trace = result["execution_trace"]

    # Stage 1: Hospital Registers
    assert trace[0]["step"] == 1
    assert trace[0]["details"]["lifecycle_state"] == "DRAFT"

    # Stage 2: Submits Details
    assert trace[1]["step"] == 2
    assert trace[1]["details"]["lifecycle_state"] == "SUBMITTED"
    assert trace[1]["details"]["tax_id"].startswith("TAX-ID-")

    # Stage 3: Platform Admin Reviews
    assert trace[2]["step"] == 3
    assert trace[2]["details"]["lifecycle_state"] == "UNDER_REVIEW"

    # Stage 4: Hospital Approved
    assert trace[3]["step"] == 4
    assert trace[3]["details"]["lifecycle_state"] == "APPROVED"
    assert trace[3]["details"]["is_active"] is True

    # Stage 5: Hospital Admin Login
    assert trace[4]["step"] == 5
    assert trace[4]["details"]["admin_role"] == "ADMIN"

    # Stage 6: Configure Hospital
    assert trace[5]["step"] == 6
    assert trace[5]["details"]["department"] == "Cardiovascular Sciences"

    # Stage 7: Create Doctors
    assert trace[6]["step"] == 7
    assert trace[6]["details"]["name"] == "Dr. Olivia Chen"

    # Stage 8: Doctors Configure Calendars
    assert trace[7]["step"] == 8
    assert "Primary Clinic" in trace[7]["details"]["calendar_name"] or "Outpatient Clinic" in trace[7]["details"]["calendar_name"]

    # Stage 9: Configure Availability
    assert trace[8]["step"] == 9
    assert trace[8]["details"]["working_hours"] == "09:00 - 17:00"

    # Stage 10: Configure Blocked Periods
    assert trace[9]["step"] == 10
    assert trace[9]["details"]["duration_minutes"] == 60

    # Stage 11: Create Questionnaires
    assert trace[10]["step"] == 11
    assert trace[10]["details"]["questions_count"] == 3

    # Stage 12: Configure EHR Integration
    assert trace[11]["step"] == 12
    assert trace[11]["details"]["adapter_type"] == "MOCK_EHR"

    # Stage 13: Configure Workflows
    assert trace[12]["step"] == 13
    assert "APPOINTMENT_REMINDER_WORKFLOW" in trace[12]["details"]["enabled_workflows"]

    # Stage 14: Publish Availability
    assert trace[13]["step"] == 14
    assert trace[13]["details"]["status"] == "PUBLISHED_LIVE"

    # Stage 15: Patients Discover Hospital
    assert trace[14]["step"] == 15
    assert trace[14]["details"]["hospital_name"] == "St. Jude Health System"

    # Stage 16: AI Books Appointments
    assert trace[15]["step"] == 16
    assert trace[15]["details"]["booking_channel"] == "AI_VOICE_AGENT"

    # Stage 17: EHR / External System Synchronization
    assert trace[16]["step"] == 17
    assert trace[16]["details"]["status"] == "SYNCED_TO_EXTERNAL_EHR"

    # Stage 18: Verification
    assert trace[17]["step"] == 18
    assert trace[17]["details"]["is_verified"] is True
    assert trace[17]["details"]["authoritative_match"]["match_patient"] is True

    # Stage 19: Workflow Executes
    assert trace[18]["step"] == 19
    assert trace[18]["details"]["workflow_name"] == "APPOINTMENT_REMINDER_WORKFLOW"

    # Stage 20: Notifications
    assert trace[19]["step"] == 20
    assert trace[19]["details"]["notification_status"] == "DELIVERED"

    # Stage 21: Doctors Receive Appointments
    assert trace[20]["step"] == 21
    assert trace[20]["details"]["calendar_synced"] is True

    # Stage 22: Doctors Review Pre-Visit Information
    assert trace[21]["step"] == 22
    assert trace[21]["details"]["clinician_review_status"] == "AUTHORIZED_AND_READY"

    # Stage 23: Hospital Monitors Analytics
    assert trace[22]["step"] == 23
    assert trace[22]["details"]["total_doctors"] >= 1
    assert trace[22]["details"]["total_appointments"] >= 1
    assert trace[22]["details"]["ehr_sync_rate_pct"] == 100.0


def test_hospital_workflow_fhir_r4_adapter(setup_db):
    """Verifies workflow with FHIR_R4 adapter configuration."""
    svc = CompleteHospitalWorkflowService(setup_db)

    req = HospitalWorkflowExecutionRequest(
        hospital_name="Metro General Hospital",
        hospital_code="METROGEN",
        contact_email="admin@metrogen.org",
        admin_name="Sarah Jenkins",
        admin_email="s.jenkins@metrogen.org",
        department_name="Orthopedic Surgery",
        specialty_name="Orthopedics",
        doctor_name="Dr. Vikram Patel",
        doctor_email="v.patel@metrogen.org",
        ehr_adapter_type="FHIR_R4",
    )

    result = svc.execute_23_step_workflow(req)
    assert result["success"] is True
    assert result["hospital_name"] == "Metro General Hospital"
    ehr_stage = result["execution_trace"][11]
    assert ehr_stage["details"]["adapter_type"] == "FHIR_R4"


# ---------------------------------------------------------------------------
# 2. REST API Endpoint Tests
# ---------------------------------------------------------------------------
def test_api_get_hospital_workflow_steps(client):
    """GET /api/v1/hospital-workflow/steps returns all 23 stage titles."""
    res = client.get("/api/v1/hospital-workflow/steps")
    assert res.status_code == 200
    data = res.json()
    assert data["total_steps"] == 23
    assert len(data["steps"]) == 23
    assert data["steps"][0]["title"] == "Hospital Registers"
    assert data["steps"][22]["title"] == "Hospital Monitors Analytics"


def test_api_get_hospital_workflow_presets(client):
    """GET /api/v1/hospital-workflow/presets returns standard hospital presets."""
    res = client.get("/api/v1/hospital-workflow/presets")
    assert res.status_code == 200
    data = res.json()
    assert len(data["presets"]) >= 3
    preset_codes = [p["hospital_code"] for p in data["presets"]]
    assert "STJUDE" in preset_codes
    assert "METROGEN" in preset_codes


def test_api_execute_hospital_workflow(client):
    """POST /api/v1/hospital-workflow/execute executes complete 23 stages."""
    payload = {
        "hospital_name": "St. Jude Health System",
        "hospital_code": "STJUDE",
        "contact_email": "contact@stjude-health.org",
        "admin_name": "Dr. Marcus Vance",
        "admin_email": "marcus.vance@stjude-health.org",
        "department_name": "Cardiovascular Sciences",
        "specialty_name": "Cardiology",
        "doctor_name": "Dr. Olivia Chen",
        "doctor_email": "olivia.chen@stjude-health.org",
        "ehr_adapter_type": "MOCK_EHR",
    }
    res = client.post("/api/v1/hospital-workflow/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["stages_completed"] == 23
    assert data["hospital_name"] == "St. Jude Health System"
    assert len(data["execution_trace"]) == 23
