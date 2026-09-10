"""
Unit tests for Section 4.4: Platform Admin Journey Lifecycle Engine.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, HospitalStatus
from app.journeys.admin_journey import PlatformAdminJourneyEngine


def test_full_13_step_admin_journey():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Seed pending hospital application
    pending_hosp = Hospital(name="Cleveland Clinic", code="CC", hospital_status=HospitalStatus.SUBMITTED)
    db.add(pending_hosp)
    db.commit()

    admin_journey = PlatformAdminJourneyEngine(db)
    res = admin_journey.execute_full_admin_journey(admin_email="admin@platform-network.com")

    assert res["success"] is True
    assert res["admin_email"] == "admin@platform-network.com"
    assert len(res["13_step_admin_journey_trace"]) == 13

    # Check hospital was approved
    db.refresh(pending_hosp)
    assert pending_hosp.hospital_status == HospitalStatus.APPROVED

    step_actions = [s["action"] for s in res["13_step_admin_journey_trace"]]
    expected_actions = [
        "Admin Login", "Review Hospital Applications", "Approve / Reject",
        "Monitor Platform", "View Appointments", "Monitor AI Activity",
        "Monitor EHR Integration Activity", "Monitor Workflows", "Monitor Failures",
        "Review Audit Trail", "Review AI Quality", "Review Platform Analytics",
        "Manage Configuration"
    ]
    assert step_actions == expected_actions
