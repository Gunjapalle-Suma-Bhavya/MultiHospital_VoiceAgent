"""
Unit tests for Step 5: AI-Native Product Principle Engine (12-Stage Lifecycle).
"""

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, Doctor, EHRIntegrationConfig, EHRAdapterType
from app.agent.native_workflow import AINativeWorkflowEngine, AI_NATIVE_BENCHMARK_RULE


def test_ai_native_12_stage_lifecycle_completion():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    hosp = Hospital(id="h-native", name="St. Anthony Hospital", code="SAH")
    doc = Doctor(id="d-native", hospital_id="h-native", name="Dr. Bruce Banner", specialty="Radiology")
    config = EHRIntegrationConfig(hospital_id="h-native", adapter_type=EHRAdapterType.MOCK_EHR)
    db.add_all([hosp, doc, config])
    db.commit()

    engine_native = AINativeWorkflowEngine(db)
    res = engine_native.execute_native_ai_lifecycle(
        phone_number="+1-555-7711",
        patient_name="Natasha Romanoff",
        utterance="Need a radiologist for MRI scan"
    )

    assert res["task_completed"] is True
    assert res["benchmark_rule"] == AI_NATIVE_BENCHMARK_RULE
    assert len(res["12_stage_lifecycle"]) == 12
    assert "proactive_next_action" in res

    stages = [s["name"] for s in res["12_stage_lifecycle"]]
    expected_stages = [
        "Conversation", "Understanding", "Context", "Reasoning",
        "Capability Selection", "Action", "External Integration",
        "Verification", "Workflow", "State Update", "Analytics", "Next Action"
    ]
    assert stages == expected_stages
