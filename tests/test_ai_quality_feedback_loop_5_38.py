"""
Unit Test Suite for Section 5.38 AI Quality Feedback Loop.
Verifies the full 7-step engineering lifecycle:
AI Interaction -> Outcome -> Evaluation -> Classification -> Review -> Improvement -> Re-Evaluation
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database.models import Base, AIQualityFeedbackRecord, Hospital
from app.feedback import AIQualityFeedbackEngine, ROOT_CAUSE_CATEGORIES, IMPROVEMENT_TYPES
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


def test_full_7_step_feedback_lifecycle(setup_db):
    """
    Tests the complete 7-step continuous improvement lifecycle (Section 5.38).
    """
    db = setup_db

    # Step 1-4: Ingest Outcome & Evaluate & Classify
    record = AIQualityFeedbackEngine.process_interaction_outcome(
        db_session=db,
        interaction_id="INT-FB-101",
        session_id="SESS-FB-101",
        hospital_id="HOSP-FB-01",
        evaluation_score=0.82,
        is_success=True,
        failure_reason="Doctor name entity misrecognized"
    )
    assert record.classification == "MINOR_FAILURE"
    assert record.improvement_status == "IDENTIFIED"

    # Step 5: Review & Attribute Root Cause
    reviewed = AIQualityFeedbackEngine.review_and_attribute_root_cause(
        db_session=db,
        feedback_id=record.id,
        root_cause_category="PROMPT_AMBIGUITY",
        review_notes="Natural language entity parser needs few-shot examples for doctor names"
    )
    assert reviewed.root_cause_category == "PROMPT_AMBIGUITY"
    assert reviewed.improvement_status == "UNDER_REVIEW"

    # Step 6: Apply Improvement
    improved = AIQualityFeedbackEngine.apply_system_improvement(
        db_session=db,
        feedback_id=record.id,
        improvement_type="PROMPT_REFINEMENT",
        improvement_details={"prompt_version": "v2.5", "added_few_shots": 5}
    )
    assert improved.improvement_type == "PROMPT_REFINEMENT"
    assert improved.improvement_status == "IMPROVEMENT_APPLIED"

    # Step 7: Trigger Re-Evaluation
    re_eval = AIQualityFeedbackEngine.trigger_re_evaluation(db_session=db, feedback_id=record.id)
    assert re_eval["improvement_status"] == "VERIFIED_IN_RE_EVALUATION"
    assert re_eval["post_improvement_score"] >= 0.90

    # History Query
    history = AIQualityFeedbackEngine.get_feedback_lifecycle_history(db, hospital_id="HOSP-FB-01")
    assert len(history) == 1
    assert history[0]["improvement_status"] == "VERIFIED_IN_RE_EVALUATION"


def test_root_cause_attribution_and_improvement_types(setup_db):
    """
    Tests various failure classifications, root cause categories, and system improvement types (Section 5.38).
    """
    db = setup_db

    # Escalated outcome
    rec_esc = AIQualityFeedbackEngine.process_interaction_outcome(
        db_session=db,
        interaction_id="INT-FB-ESC",
        is_escalated=True
    )
    assert rec_esc.classification == "ESCALATED"

    # Critical failure outcome
    rec_crit = AIQualityFeedbackEngine.process_interaction_outcome(
        db_session=db,
        interaction_id="INT-FB-CRIT",
        evaluation_score=0.55,
        is_success=False
    )
    assert rec_crit.classification == "CRITICAL_FAILURE"

    # Review with EHR schema mismatch
    reviewed = AIQualityFeedbackEngine.review_and_attribute_root_cause(
        db_session=db,
        feedback_id=rec_crit.id,
        root_cause_category="EHR_SCHEMA_MISMATCH",
        review_notes="Epic FHIR R4 date format mismatch"
    )
    assert reviewed.root_cause_category in ROOT_CAUSE_CATEGORIES

    # Apply EHR Adapter mapping improvement
    improved = AIQualityFeedbackEngine.apply_system_improvement(
        db_session=db,
        feedback_id=rec_crit.id,
        improvement_type="EHR_ADAPTER_MAPPING",
        improvement_details={"adapter": "EPIC_MYCHART", "date_format": "YYYY-MM-DDThh:mm:ssZ"}
    )
    assert improved.improvement_type in IMPROVEMENT_TYPES


def test_feedback_loop_api_endpoints(client, setup_db):
    """
    Tests REST API endpoints for feedback ingestion, review, improvement, re-evaluation, and records (Section 5.38).
    """
    # 1. Ingest Endpoint
    res_ingest = client.post("/api/v1/feedback/ingest", json={
        "interaction_id": "INT-API-55",
        "session_id": "SESS-API-55",
        "evaluation_score": 0.75,
        "is_success": True,
        "failure_reason": "Slot availability delay"
    })
    assert res_ingest.status_code == 200
    fb_id = res_ingest.json()["feedback_id"]

    # 2. Review Endpoint
    res_rev = client.post(f"/api/v1/feedback/{fb_id}/review", json={
        "root_cause_category": "WORKFLOW_TIMEOUT",
        "review_notes": "Scheduler workflow lock timeout"
    })
    assert res_rev.status_code == 200
    assert res_rev.json()["root_cause_category"] == "WORKFLOW_TIMEOUT"

    # 3. Apply Improvement Endpoint
    res_imp = client.post(f"/api/v1/feedback/{fb_id}/apply-improvement", json={
        "improvement_type": "WORKFLOW_SCHEDULE_ADJUSTMENT",
        "improvement_details": {"timeout_sec": 15}
    })
    assert res_imp.status_code == 200
    assert res_imp.json()["improvement_status"] == "IMPROVEMENT_APPLIED"

    # 4. Trigger Re-Evaluation Endpoint
    res_reeval = client.post(f"/api/v1/feedback/{fb_id}/re-evaluate")
    assert res_reeval.status_code == 200
    assert res_reeval.json()["improvement_status"] == "VERIFIED_IN_RE_EVALUATION"

    # 5. Get Records History Endpoint
    res_records = client.get("/api/v1/feedback/records")
    assert res_records.status_code == 200
    assert len(res_records.json()) >= 1
