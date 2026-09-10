"""
Unit tests for Section 4.2: Doctor Journey Lifecycle Engine.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital
from app.journeys.doctor_journey import DoctorJourneyEngine


def test_full_10_step_doctor_journey():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    hosp = Hospital(id="h-doc-j", name="Mayo Clinic", code="MC")
    db.add(hosp)
    db.commit()

    doctor_journey = DoctorJourneyEngine(db)

    approved_questions = [
        "What triggered your symptoms?",
        "Are you taking blood thinners?"
    ]

    res = doctor_journey.execute_full_doctor_journey(
        hospital_id="h-doc-j",
        doctor_name="Dr. William Mayo",
        specialty="Surgery",
        bio="Lead Chief Surgeon with 20 years experience.",
        special_instructions="Verify blood pressure prior to consultation.",
        approved_questions=approved_questions,
        blocked_leave_start=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=10),
        blocked_leave_end=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=15)
    )

    assert res["success"] is True
    assert res["doctor_name"] == "Dr. William Mayo"
    assert len(res["10_step_journey_trace"]) == 10

    step_actions = [s["action"] for s in res["10_step_journey_trace"]]
    expected_actions = [
        "Doctor Created", "Complete Profile", "Configure Calendar", "Set Working Hours",
        "Set Availability", "Block Lunch / Leave", "Create Approved Questions",
        "View Appointments", "Review Pre-Visit Responses", "Review Relevant Patient Context"
    ]
    assert step_actions == expected_actions

    dashboard = res["dashboard"]
    assert dashboard["doctor_name"] == "Dr. William Mayo"
    assert dashboard["profile_completed"] is True
