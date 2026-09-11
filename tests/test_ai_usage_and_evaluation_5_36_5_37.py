"""
Unit Test Suite for Section 5.36 AI Usage & Cost Tracking and Section 5.37 AI Evaluation.
Verifies token tracking, voice duration, latency, cost aggregations by hospital/feature/session/workflow,
and internal evaluation benchmarks across Conversational AI, Scheduling, EHR Integration, and Questionnaire domains.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database.models import Base, Hospital, AIUsageRecord, AIEvaluationRecord
from app.analytics import AIUsageCostTracker, AIEvaluationEngine
from app.main import app
from app.database.config import get_db

# In-Memory SQLite Setup with StaticPool
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


def test_ai_usage_cost_tracking(setup_db):
    """
    Tests AI usage logging, token counts, voice duration, latency, and 4 cost breakdown dimensions (Section 5.36).
    """
    db = setup_db

    # Seed Hospital
    hosp = Hospital(id="HOSP-USAGE-01", name="St. Jude Hospital", code="STJ")
    db.add(hosp)
    db.commit()

    # 1. Record Usage
    rec1 = AIUsageCostTracker.record_ai_usage(
        db_session=db,
        session_id="SESS-USAGE-101",
        hospital_id="HOSP-USAGE-01",
        workflow_id="WF-USAGE-201",
        feature_name="VOICE_PATIENT_INTAKE",
        input_tokens=1000,
        output_tokens=200,
        voice_duration_seconds=30.0,
        processing_duration_ms=850.0
    )
    assert rec1.id is not None
    assert rec1.estimated_cost_usd > 0.0

    rec2 = AIUsageCostTracker.record_ai_usage(
        db_session=db,
        session_id="SESS-USAGE-101",
        hospital_id="HOSP-USAGE-01",
        feature_name="DOCTOR_DISCOVERY",
        input_tokens=500,
        output_tokens=100,
        voice_duration_seconds=10.0,
        processing_duration_ms=400.0
    )

    # 2. Summary
    summary = AIUsageCostTracker.get_overall_ai_usage_summary(db)
    assert summary["total_ai_requests"] == 2
    assert summary["total_input_tokens"] == 1500
    assert summary["total_output_tokens"] == 300
    assert summary["total_tokens"] == 1800
    assert summary["total_voice_duration_seconds"] == 40.0

    # 3. Cost by Hospital
    by_hosp = AIUsageCostTracker.get_cost_by_hospital(db)
    assert len(by_hosp) == 1
    assert by_hosp[0]["hospital_id"] == "HOSP-USAGE-01"
    assert by_hosp[0]["ai_requests"] == 2

    # 4. Cost by Feature
    by_feat = AIUsageCostTracker.get_cost_by_feature(db)
    assert "VOICE_PATIENT_INTAKE" in by_feat
    assert "DOCTOR_DISCOVERY" in by_feat
    assert by_feat["VOICE_PATIENT_INTAKE"]["ai_requests"] == 1

    # 5. Cost by Conversation
    by_conv = AIUsageCostTracker.get_cost_by_conversation(db, session_id="SESS-USAGE-101")
    assert len(by_conv) == 1
    assert by_conv[0]["session_id"] == "SESS-USAGE-101"
    assert by_conv[0]["ai_requests"] == 2

    # 6. Cost by Workflow
    by_wf = AIUsageCostTracker.get_cost_by_workflow(db, workflow_id="WF-USAGE-201")
    assert len(by_wf) == 1
    assert by_wf[0]["workflow_id"] == "WF-USAGE-201"


def test_ai_evaluation_engine_4_domains(setup_db):
    """
    Tests internal evaluation benchmark execution across Conversational AI, Scheduling, EHR Integration,
    and Questionnaire domains (Section 5.37).
    """
    db = setup_db

    # Run full platform evaluation
    report = AIEvaluationEngine.run_full_platform_evaluation(
        db_session=db,
        hospital_id="HOSP-EVAL-01",
        session_id="SESS-EVAL-01"
    )

    assert report["evaluation_id"].startswith("EVAL-")
    assert report["all_domains_passed"] is True
    assert report["evaluated_domains_count"] == 4
    assert report["overall_platform_score"] >= 0.90

    # Verify domain sub-metrics
    domain_names = [d["domain"] for d in report["domain_results"]]
    assert "CONVERSATIONAL_AI" in domain_names
    assert "SCHEDULING" in domain_names
    assert "EHR_INTEGRATION" in domain_names
    assert "QUESTIONNAIRE" in domain_names

    # Check persistence & history lookup
    history = AIEvaluationEngine.get_evaluation_history(db, evaluation_id=report["evaluation_id"])
    assert len(history) == 4
    for record in history:
        assert record["overall_score"] >= 0.90
        assert "metrics" in record


def test_ai_analytics_api_endpoints(client, setup_db):
    """
    Tests REST API endpoints for AI usage tracking and evaluation suite (Sections 5.36 & 5.37).
    """
    # 1. Record Usage Endpoint
    res_rec = client.post("/api/v1/ai/usage/record", json={
        "session_id": "SESS-API-99",
        "hospital_id": "HOSP-API-101",
        "feature_name": "VOICE_PATIENT_INTAKE",
        "input_tokens": 1200,
        "output_tokens": 300,
        "voice_duration_seconds": 25.0,
        "processing_duration_ms": 950.0
    })
    assert res_rec.status_code == 200
    assert res_rec.json()["status"] == "RECORDED"

    # 2. Get Summary Endpoint
    res_sum = client.get("/api/v1/ai/usage/summary")
    assert res_sum.status_code == 200
    assert res_sum.json()["total_ai_requests"] >= 1

    # 3. Get Cost by Hospital
    res_hosp = client.get("/api/v1/ai/usage/by-hospital")
    assert res_hosp.status_code == 200
    assert len(res_hosp.json()) >= 1

    # 4. Get Cost by Feature
    res_feat = client.get("/api/v1/ai/usage/by-feature")
    assert res_feat.status_code == 200
    assert "VOICE_PATIENT_INTAKE" in res_feat.json()

    # 5. Get Cost by Conversation
    res_conv = client.get("/api/v1/ai/usage/by-conversation/SESS-API-99")
    assert res_conv.status_code == 200
    assert res_conv.json()["session_id"] == "SESS-API-99"

    # 6. Run Evaluation Suite
    res_eval = client.post("/api/v1/ai/evaluations/run", json={
        "hospital_id": "HOSP-API-101"
    })
    assert res_eval.status_code == 200
    eval_data = res_eval.json()
    assert eval_data["all_domains_passed"] is True

    # 7. Get Evaluation History
    res_hist = client.get("/api/v1/ai/evaluations/results")
    assert res_hist.status_code == 200
    assert len(res_hist.json()) >= 4
