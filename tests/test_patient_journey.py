"""
Unit tests for Section 4.3: Patient Journey Lifecycle Engine.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, Doctor, EHRIntegrationConfig, EHRAdapterType
from app.journeys.patient_journey import PatientJourneyEngine


def test_full_19_step_patient_journey():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Seed hospital & doctor
    hosp = Hospital(id="h-pat-j", name="Johns Hopkins Hospital", code="JHH")
    doc = Doctor(id="d-pat-j", hospital_id="h-pat-j", name="Dr. Ben Carson", specialty="Neurosurgery")
    config = EHRIntegrationConfig(hospital_id="h-pat-j", adapter_type=EHRAdapterType.MOCK_EHR)
    db.add_all([hosp, doc, config])
    db.commit()

    patient_journey = PatientJourneyEngine(db)

    res = patient_journey.execute_full_patient_journey(
        phone_number="+1-555-6677",
        patient_name="Clark Kent",
        utterance="I need a neurosurgeon for consultation",
        intake_symptoms="Mild tension headaches after long work shifts."
    )

    assert res["success"] is True
    assert res["doctor_name"] == "Dr. Ben Carson"
    assert res["hospital_name"] == "Johns Hopkins Hospital"
    assert len(res["19_step_patient_journey_trace"]) == 19

    step_actions = [s["action"] for s in res["19_step_patient_journey_trace"]]
    expected_actions = [
        "Register / Login", "Start AI Conversation", "Describe Requirement",
        "AI Understands Intent", "Resolve Context", "Search Doctors & Hospitals",
        "Check Real Availability", "Present Options", "Patient Chooses", "Confirm",
        "Book Appointment", "EHR / External System Integration", "Verify Booking",
        "Synchronize State", "Pre-Visit Workflow", "Patient Responds",
        "Notifications / Follow-Up", "Doctor Reviews", "Analytics Updated"
    ]
    assert step_actions == expected_actions
