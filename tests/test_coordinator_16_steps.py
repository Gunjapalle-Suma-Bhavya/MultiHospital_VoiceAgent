"""
Unit tests for Step 4: 16-Step Coordinated Product Vision Engine.
"""

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, Doctor, EHRIntegrationConfig, EHRAdapterType
from app.agent.coordinator import ProductVision16StepCoordinator, PRODUCT_PRINCIPLE


def test_16_step_coordination_full_pipeline():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Seed hospital & doctor
    hosp = Hospital(id="h-16", name="Mount Sinai Hospital", code="MSH")
    doc = Doctor(id="d-16", hospital_id="h-16", name="Dr. Jean Grey", specialty="Endocrinology")
    config = EHRIntegrationConfig(hospital_id="h-16", adapter_type=EHRAdapterType.MOCK_EHR)
    db.add_all([hosp, doc, config])
    db.commit()

    coordinator = ProductVision16StepCoordinator(db)
    res = coordinator.execute_16_step_coordination(
        phone_number="+1-555-4433",
        patient_name="Peter Parker",
        utterance="I need an endocrinologist for thyroid evaluation",
        pre_visit_symptoms="Mild fatigue for past month."
    )

    assert res["success"] is True
    assert res["product_principle"] == PRODUCT_PRINCIPLE
    assert res["doctor_name"] == "Dr. Jean Grey"
    assert len(res["16_step_execution_trace"]) == 16

    step_names = [s["name"] for s in res["16_step_execution_trace"]]
    expected_steps = [
        "Understanding", "Context resolution", "Hospital discovery", "Doctor discovery",
        "Availability verification", "Clarification", "Appointment selection", "Booking",
        "EHR / healthcare-system integration", "External verification", "State synchronization",
        "Pre-visit information collection", "Notifications", "Follow-up workflows",
        "Analytics", "Auditability"
    ]
    for step in expected_steps:
        assert step in step_names


def test_16_step_coordination_guardrail_interception():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    coordinator = ProductVision16StepCoordinator(db)
    res = coordinator.execute_16_step_coordination(
        phone_number="+1-555-4433",
        patient_name="Peter Parker",
        utterance="Can you diagnose me and tell me what medication should I take?"
    )

    assert res["success"] is False
    assert res["step_failed"] == 1
    assert "cannot provide medical diagnoses" in res["message"]
