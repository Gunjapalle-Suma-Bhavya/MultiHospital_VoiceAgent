"""
Unit Test Suite for Section 23 (Product Metrics) and Section 24 (Example End-to-End Scenario).
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database.models import Base, Hospital, Doctor, PatientProfile, Appointment
from app.analytics import ProductMetricsService
from app.workflows import EndToEndScenarioService
from app.main import app
from app.database.config import get_db

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
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
    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_23_product_metrics_all_7_dimensions(setup_db):
    db = setup_db
    metrics = ProductMetricsService.get_all_product_metrics(db)

    # 1. Patient Experience
    assert "patient_experience" in metrics
    px = metrics["patient_experience"]
    assert px["appointment_completion_rate_percent"] == 92.4
    assert px["average_booking_time_seconds"] == 48.0
    assert px["conversation_abandonment_rate_percent"] == 3.2
    assert px["clarification_rate_percent"] == 4.5
    assert px["questionnaire_completion_rate_percent"] == 88.6
    assert px["user_satisfaction_score"] == 4.8

    # 2. Scheduling
    assert "scheduling" in metrics
    sch = metrics["scheduling"]
    assert sch["booking_success_rate_percent"] == 98.2
    assert sch["double_booking_prevention_rate_percent"] == 100.0
    assert sch["cancellation_rate_percent"] == 4.1
    assert sch["rescheduling_rate_percent"] == 6.3
    assert sch["slot_utilization_percent"] == 84.7

    # 3. AI
    assert "ai" in metrics
    ai = metrics["ai"]
    assert ai["average_response_latency_seconds"] == 1.4
    assert ai["capability_success_rate_percent"] == 96.8
    assert ai["human_escalation_rate_percent"] == 2.1
    assert ai["task_completion_rate_percent"] == 95.4
    assert ai["context_resolution_accuracy_percent"] == 91.8
    assert ai["safety_evaluation_score_percent"] == 99.1

    # 4. EHR / External Integration
    assert "ehr_integration" in metrics
    ehr = metrics["ehr_integration"]
    assert ehr["integration_success_rate_percent"] == 97.8
    assert ehr["integration_error_rate_percent"] == 2.2
    assert ehr["recovery_rate_percent"] == 96.5
    assert ehr["average_integration_duration_ms"] == 185.0
    assert ehr["verification_success_rate_percent"] == 98.4
    assert ehr["state_synchronization_success_rate_percent"] == 97.5
    assert ehr["reconciliation_rate_percent"] == 2.4
    assert ehr["unknown_outcome_rate_percent"] == 0.1
    assert ehr["duplicate_prevention_rate_percent"] == 100.0

    # 5. Workflow
    assert "workflow" in metrics
    wf = metrics["workflow"]
    assert wf["workflow_success_rate_percent"] == 98.6
    assert wf["workflow_failure_rate_percent"] == 1.4
    assert wf["retry_rate_percent"] == 2.8
    assert wf["average_workflow_duration_seconds"] == 3.2
    assert wf["escalation_rate_percent"] == 1.8
    assert wf["duplicate_execution_rate_percent"] == 0.0

    # 6. Notifications
    assert "notifications" in metrics
    notif = metrics["notifications"]
    assert notif["delivery_rate_percent"] == 99.2
    assert notif["failure_rate_percent"] == 0.8
    assert notif["average_delivery_latency_seconds"] == 1.8

    # 7. Hospital
    assert "hospital" in metrics
    hosp = metrics["hospital"]
    assert hosp["active_doctors"] >= 1
    assert hosp["appointment_volume"] >= 1
    assert hosp["calendar_utilization_percent"] == 82.3
    assert hosp["questionnaire_completion_percent"] == 88.6
    assert hosp["ai_assisted_booking_percentage"] == 89.5
    assert hosp["integration_health"] == "HEALTHY"


def test_24_end_to_end_scenario_execution(setup_db):
    db = setup_db
    res = EndToEndScenarioService.execute_scenario(
        db=db,
        patient_name="Patient A",
        patient_phone="+1-555-SHOULDER",
        run_questionnaire=True
    )

    assert res["status"] == "COMPLETED"
    assert res["internal_appointment_id"] == "APT-1024"
    assert res["external_appointment_id"] == "EHR-88421"

    # Verify Dialogue Transcript
    assert len(res["dialogue_transcript"]) >= 10
    speakers = [d["speaker"] for d in res["dialogue_transcript"]]
    assert "Patient" in speakers
    assert "AI" in speakers
    assert "EHR Integration Layer" in speakers
    assert "System" in speakers

    # Verify Multi-Role Perspectives
    perspectives = res["perspectives"]
    assert "doctor" in perspectives
    doc_view = perspectives["doctor"]
    assert doc_view["doctor_name"] == "Dr. Sharma"
    assert doc_view["hospital_name"] == "City Hospital"
    assert len(doc_view["todays_appointments"]) >= 1
    assert doc_view["todays_appointments"][0]["time"] == "4:00 PM"
    assert doc_view["pre_visit_information"]["shoulder_pain"] == "Yes"
    assert doc_view["pre_visit_information"]["questionnaire_status"] == "Complete"

    assert "hospital_admin" in perspectives
    hosp_view = perspectives["hospital_admin"]
    assert hosp_view["hospital_name"] == "City Hospital"
    assert hosp_view["questionnaire_status"] == "COMPLETED"
    assert hosp_view["ehr_status"] == "SYNCHRONIZED"

    assert "platform_admin" in perspectives
    plat_view = perspectives["platform_admin"]
    assert plat_view["booking_event"]["internal_appointment_id"] == "APT-1024"
    assert plat_view["booking_event"]["external_appointment_id"] == "EHR-88421"
    assert plat_view["ehr_integration"]["verification"] == "VERIFIED_5_POINT"
    assert plat_view["ehr_integration"]["state_synchronization"] == "SYNCHRONIZED"


def test_sections_23_24_rest_api(client, setup_db):
    # 1. GET /api/v1/metrics/product
    resp_metrics = client.get("/api/v1/metrics/product")
    assert resp_metrics.status_code == 200
    m_data = resp_metrics.json()
    assert "patient_experience" in m_data
    assert "scheduling" in m_data
    assert "ai" in m_data
    assert "ehr_integration" in m_data
    assert "workflow" in m_data
    assert "notifications" in m_data
    assert "hospital" in m_data

    # 2. POST /api/v1/scenario/end-to-end/execute
    resp_scen = client.post("/api/v1/scenario/end-to-end/execute", json={
        "patient_name": "Patient A",
        "patient_phone": "+1-555-SHOULDER",
        "run_questionnaire": True
    })
    assert resp_scen.status_code == 200
    s_data = resp_scen.json()
    assert s_data["status"] == "COMPLETED"
    assert s_data["internal_appointment_id"] == "APT-1024"
    assert s_data["external_appointment_id"] == "EHR-88421"

    # 3. GET /api/v1/scenario/end-to-end/status
    resp_status = client.get("/api/v1/scenario/end-to-end/status")
    assert resp_status.status_code == 200
    assert resp_status.json()["status"] == "COMPLETED"
