"""
Unit tests for Section 1.7: Operational Intelligence, AI Telemetry, Token Usage, and Cost Calculation.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, Doctor, EHRIntegrationConfig, EHRAdapterType, AITelemetryLog
from app.telemetry.intelligence import OperationalIntelligenceService
from app.agent.actions import ActionExecutor
from app.schemas.actions import SearchHospitalsInput, CreateAppointmentInput, EscalateToHumanInput


def test_cost_calculation():
    # Gemini 3.6 Flash pricing: $0.00015 / 1k prompt, $0.00060 / 1k completion
    cost = OperationalIntelligenceService.calculate_cost("gemini-3.6-flash", 1000, 1000)
    assert cost == 0.00075


def test_telemetry_logging_and_report_generation():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    telemetry = OperationalIntelligenceService(db)

    # Record normal turn
    telemetry.record_turn_telemetry(
        session_id="sess-t1",
        ai_attempt_summary="Search dermatologist",
        capability_invoked="SEARCH_DOCTORS",
        latency_ms=120.5,
        prompt_tokens=300,
        completion_tokens=50
    )

    # Record escalated turn
    telemetry.record_turn_telemetry(
        session_id="sess-t2",
        ai_attempt_summary="Escalate patient to agent",
        capability_invoked="ESCALATE_TO_HUMAN",
        latency_ms=45.0,
        escalated_to_human=True,
        prompt_tokens=200,
        completion_tokens=40
    )

    report = telemetry.get_system_health_report()
    assert report["total_ai_invocations"] == 2
    assert report["total_tokens_used"] == 590
    assert report["human_escalations_count"] == 1
    assert report["workflow_health_breakdown"]["CRITICAL"] == 1
    assert report["workflow_health_breakdown"]["HEALTHY"] == 1


def test_end_to_end_action_telemetry():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    hosp = Hospital(id="h-tele", name="City Health", code="CH")
    doc = Doctor(id="d-tele", hospital_id="h-tele", name="Dr. Sam", specialty="General")
    config = EHRIntegrationConfig(hospital_id="h-tele", adapter_type=EHRAdapterType.MOCK_EHR)
    db.add_all([hosp, doc, config])
    db.commit()

    executor = ActionExecutor(db)

    # Execute Search
    executor.search_hospitals(SearchHospitalsInput(session_id="s-tele", patient_id="p-tele", query="City"))

    # Execute Booking
    executor.create_appointment(CreateAppointmentInput(
        session_id="s-tele",
        patient_id="p-tele",
        hospital_id="h-tele",
        doctor_id="d-tele",
        start_datetime=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1),
        patient_name="Alice Vance",
        patient_phone="+1-555-9988"
    ))

    # Verify Telemetry logs written
    logs = db.query(AITelemetryLog).all()
    assert len(logs) == 2
    capabilities = [l.capability_invoked for l in logs]
    assert "SEARCH_HOSPITALS" in capabilities
    assert "CREATE_APPOINTMENT" in capabilities
    assert logs[1].estimated_cost_usd > 0
