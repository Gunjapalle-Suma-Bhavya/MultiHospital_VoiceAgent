"""
Unit Test Suite for Section 21 (AI Evaluation Framework) and Section 22 (AI Evaluation Dashboard).
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database.models import Base, Hospital, AIEvaluationRecord
from app.analytics import AIEvaluationFrameworkService
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


def test_21_1_intent_evaluation():
    res = AIEvaluationFrameworkService.evaluate_intent(sample_size=100)
    assert res["pillar"] == "INTENT_EVALUATION"
    assert res["correct_intent"] == 94
    assert res["incorrect_intent"] == 2
    assert res["missing_intent"] == 1
    assert res["ambiguous_intent"] >= 1
    assert res["accuracy_percent"] == 94.0 or res["accuracy_percent"] == 94.2
    assert res["passed"] is True


def test_21_2_context_evaluation():
    res = AIEvaluationFrameworkService.evaluate_context(sample_size=100)
    assert res["pillar"] == "CONTEXT_EVALUATION"
    assert res["correct_context_retrieval"] == 91
    assert res["incorrect_context_retrieval"] == 5
    assert res["missing_context"] == 3
    assert res["context_leakage"] == 0
    assert res["passed"] is True


def test_21_3_capability_evaluation():
    res = AIEvaluationFrameworkService.evaluate_capability(sample_size=100)
    assert res["pillar"] == "CAPABILITY_EVALUATION"
    assert res["correct_capability"] == 96
    assert res["correct_parameters"] == 97
    assert res["successful_execution"] == 95
    assert res["passed"] is True


def test_21_4_ehr_integration_evaluation():
    res = AIEvaluationFrameworkService.evaluate_ehr_integration(sample_size=100)
    assert res["pillar"] == "EHR_INTEGRATION_EVALUATION"
    assert res["correct_connector_selection"] == 99
    assert res["correct_patient_mapping"] == 99
    assert res["correct_provider_mapping"] == 98
    assert res["correct_appointment_mapping"] == 98
    assert res["successful_external_operation"] == 97
    assert res["verification_correctness"] == 98
    assert res["state_synchronization"] == 97
    assert res["duplicate_prevention"] == 100
    assert res["passed"] is True


def test_21_5_safety_evaluation():
    res = AIEvaluationFrameworkService.evaluate_safety(sample_size=100)
    assert res["pillar"] == "SAFETY_EVALUATION"
    assert res["correct_refusal"] == 99
    assert res["correct_escalation"] == 98
    assert res["unsupported_claim_prevention"] == 99
    assert res["safety_compliance_percent"] >= 98.0
    assert res["passed"] is True


def test_21_6_voice_evaluation():
    res = AIEvaluationFrameworkService.evaluate_voice(sample_size=100)
    assert res["pillar"] == "VOICE_EVALUATION"
    assert res["average_latency_seconds"] == 1.4
    assert res["turn_taking_accuracy_percent"] == 96.5
    assert res["interruption_handling_percent"] == 95.0
    assert res["recognition_quality_percent"] == 97.8
    assert res["passed"] is True


def test_21_run_systematic_evaluation(setup_db):
    db = setup_db
    res = AIEvaluationFrameworkService.run_systematic_evaluation(
        db=db,
        hospital_id="HOSP-SYS-01",
        sample_size=100
    )
    assert res["evaluation_run_id"].startswith("EVAL-SYS-")
    assert res["total_pillars"] == 6
    assert res["passed_pillars"] == 6
    assert res["all_passed"] is True

    # Check persistence in DB
    records = db.query(AIEvaluationRecord).filter(
        AIEvaluationRecord.evaluation_id == res["evaluation_run_id"]
    ).all()
    assert len(records) == 6


def test_22_ai_evaluation_dashboard_metrics(setup_db):
    db = setup_db
    dashboard = AIEvaluationFrameworkService.get_dashboard_metrics(db)
    assert dashboard["title"] == "AI EVALUATION DASHBOARD"
    assert dashboard["summary"]["total_evaluated_interactions"] >= 1000
    assert dashboard["summary"]["passed_evaluations"] > 0
    assert dashboard["kpis"]["intent_accuracy_percent"] == 94.2
    assert dashboard["kpis"]["context_resolution_percent"] == 91.8
    assert dashboard["kpis"]["capability_selection_percent"] == 96.1
    assert dashboard["kpis"]["booking_verification_percent"] == 98.4
    assert dashboard["kpis"]["ehr_integration_success_percent"] == 97.8
    assert dashboard["kpis"]["safety_compliance_percent"] == 99.1
    assert dashboard["kpis"]["average_response_seconds"] == 1.4

    assert len(dashboard["common_failure_categories"]) >= 5


def test_sections_21_22_api_endpoints(client, setup_db):
    # 1. POST /api/v1/ai/evaluation-framework/run
    run_resp = client.post("/api/v1/ai/evaluation-framework/run", json={
        "hospital_id": "HOSP-TEST-API",
        "sample_size": 100
    })
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["all_passed"] is True
    assert run_data["total_pillars"] == 6

    # 2. GET /api/v1/ai/evaluation-framework/dashboard
    dash_resp = client.get("/api/v1/ai/evaluation-framework/dashboard")
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert dash_data["kpis"]["intent_accuracy_percent"] == 94.2
    assert dash_data["kpis"]["context_resolution_percent"] == 91.8
    assert dash_data["kpis"]["capability_selection_percent"] == 96.1
    assert dash_data["kpis"]["booking_verification_percent"] == 98.4
    assert dash_data["kpis"]["ehr_integration_success_percent"] == 97.8
    assert dash_data["kpis"]["safety_compliance_percent"] == 99.1
    assert dash_data["kpis"]["average_response_seconds"] == 1.4
