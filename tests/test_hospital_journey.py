"""
Unit tests for Section 4.1: Hospital Journey Lifecycle Engine.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, HospitalStatus, EHRAdapterType
from app.journeys.hospital_journey import HospitalJourneyEngine


def test_full_15_step_hospital_journey():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    journey_engine = HospitalJourneyEngine(db)

    questions = [
        {"id": "q1", "text": "Have you had skin rash for more than 7 days?", "type": "BOOLEAN"},
        {"id": "q2", "text": "List any current allergies.", "type": "TEXT"}
    ]

    res = journey_engine.execute_full_hospital_journey(
        name="St. Jude Children's Research Hospital",
        code="SJCRH",
        address="262 Danny Thomas Place, Memphis, TN",
        contact_email="admin@stjude.org",
        doctor_name="Dr. Jonas Salk",
        specialty="Virology",
        questionnaire_title="Pre-Visit Immunology Questionnaire",
        questions=questions,
        ehr_adapter_type=EHRAdapterType.MOCK_EHR
    )

    assert res["success"] is True
    assert res["hospital_status"] == HospitalStatus.APPROVED.value
    assert len(res["15_step_journey_trace"]) == 15

    step_actions = [s["action"] for s in res["15_step_journey_trace"]]
    expected_actions = [
        "Register Hospital", "Submit Details", "Admin Review", "Approved",
        "Configure Hospital", "Create Doctors", "Configure Calendars",
        "Define Working Hours", "Define Availability", "Create Questionnaires",
        "Configure EHR Integration", "Configure Operational Preferences",
        "Publish Availability", "Monitor Operations", "Review Analytics"
    ]
    assert step_actions == expected_actions

    # Test Analytics
    analytics = journey_engine.get_hospital_analytics(res["hospital_id"])
    assert analytics["hospital_id"] == res["hospital_id"]
    assert "total_appointments" in analytics
