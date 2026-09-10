"""
Unit tests for Section 5.1: Self-Service Hospital Registration & Onboarding Feature.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, HospitalStatus, Doctor
from app.onboarding.hospital_onboarding import HospitalSelfServiceOnboardingService
from app.agent.actions import ActionExecutor
from app.schemas.actions import SearchHospitalsInput, SearchDoctorsInput


def test_hospital_onboarding_state_machine_and_active_rule():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    onboarding = HospitalSelfServiceOnboardingService(db)
    executor = ActionExecutor(db)

    # 1. Create Draft
    hosp = onboarding.create_draft_hospital(
        name="Mass General Hospital",
        code="MGH",
        contact_email="contact@mgh.org",
        admin_name="Dr. Mark",
        admin_email="mark@mgh.org"
    )
    assert hosp.hospital_status == HospitalStatus.DRAFT
    assert hosp.is_active is False

    # Verify search excludes draft hospital
    search1 = executor.search_hospitals(SearchHospitalsInput(session_id="s1", patient_id="p1", query="Mass"))
    assert len(search1.hospitals) == 0

    # 2. Update Draft Metadata & Submit
    onboarding.update_hospital_draft_metadata(
        hospital_id=hosp.id,
        address="55 Fruit St, Boston, MA",
        phone="+1-617-726-2000",
        departments=["Cardiology", "Neurology"],
        specialties=["Cardiology", "Neurology"]
    )
    onboarding.submit_application(hosp.id)
    assert hosp.hospital_status == HospitalStatus.SUBMITTED
    assert hosp.is_active is False

    # 3. Move to Under Review
    onboarding.move_to_under_review(hosp.id)
    assert hosp.hospital_status == HospitalStatus.UNDER_REVIEW
    assert hosp.is_active is False

    # 4. Approve Hospital
    onboarding.approve_hospital(hosp.id)
    assert hosp.hospital_status == HospitalStatus.APPROVED
    assert hosp.is_active is True

    # Seed a doctor in approved hospital
    doc = Doctor(hospital_id=hosp.id, name="Dr. Paul", specialty="Cardiology", is_active=True)
    db.add(doc)
    db.commit()

    # Verify search NOW finds approved hospital and doctor
    search2 = executor.search_hospitals(SearchHospitalsInput(session_id="s2", patient_id="p2", query="Mass"))
    assert len(search2.hospitals) == 1
    assert search2.hospitals[0].name == "Mass General Hospital"

    doc_search = executor.search_doctors(SearchDoctorsInput(session_id="s2", patient_id="p2", specialty="Cardiology"))
    assert len(doc_search.doctors) == 1


def test_hospital_rejection_deactivates():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    onboarding = HospitalSelfServiceOnboardingService(db)
    hosp = onboarding.create_draft_hospital("Fake Clinic", "FC", "a@fc.org", "Admin", "a@fc.org")
    onboarding.submit_application(hosp.id)
    onboarding.reject_hospital(hosp.id, "Incomplete medical license verification.")

    assert hosp.hospital_status == HospitalStatus.REJECTED
    assert hosp.is_active is False
    assert hosp.rejection_reason == "Incomplete medical license verification."
