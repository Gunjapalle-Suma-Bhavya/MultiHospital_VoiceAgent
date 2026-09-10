"""
Test Suite for Section 5.2 Platform Admin Approval & Strict Rules Enforcement.
"""

from datetime import datetime, time, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import (
    Base, Hospital, HospitalStatus, Doctor, Appointment, EHRIntegrationConfig, EHRAdapterType
)
from app.onboarding.hospital_onboarding import HospitalSelfServiceOnboardingService
from app.admin.admin_approval import PlatformAdminApprovalService
from app.journeys.doctor_journey import DoctorJourneyEngine
from app.agent.actions import ActionExecutor
from app.schemas.actions import CreateAppointmentInput


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_platform_admin_lifecycle_and_actions(db_session):
    """
    Tests complete admin lifecycle: Review, Approve, Reject, Request Corrections, Suspend, Reactivate.
    """
    onboarding = HospitalSelfServiceOnboardingService(db_session)
    admin_service = PlatformAdminApprovalService(db_session)

    # 1. Create Draft & Submit
    hosp = onboarding.create_draft_hospital(
        name="Metro Health Center",
        code="METRO-001",
        contact_email="contact@metrohealth.org",
        admin_name="Dr. Jane Smith",
        admin_email="jane@metrohealth.org"
    )
    onboarding.update_hospital_draft_metadata(
        hospital_id=hosp.id,
        organization_info="Regional Health System",
        address="100 Metro Way, Cityville",
        departments=["Cardiology", "Neurology"],
        specialties=["Cardiology"],
        services=["Intensive Care", "Outpatient Consultation"],
        tax_id="TAX-998877",
        license_id="LIC-112233"
    )
    onboarding.submit_application(hosp.id)

    # 2. Review Hospital Info
    review_info = admin_service.review_hospital_info(hosp.id)
    assert review_info["name"] == "Metro Health Center"
    assert review_info["hospital_status"] == HospitalStatus.SUBMITTED.value
    assert review_info["is_active"] is False
    assert review_info["verification_info"]["tax_id"] == "TAX-998877"

    # 3. Request Corrections
    hosp_corr = admin_service.request_corrections(hosp.id, "Please upload valid medical license documentation.")
    assert hosp_corr.hospital_status == HospitalStatus.CORRECTION_REQUESTED
    assert hosp_corr.is_active is False
    assert hosp_corr.correction_notes == "Please upload valid medical license documentation."

    # 4. Approve Hospital
    hosp_app = admin_service.approve_hospital(hosp.id)
    assert hosp_app.hospital_status == HospitalStatus.APPROVED
    assert hosp_app.is_active is True

    # 5. Review EHR Integration Config & Activate
    ehr_config = admin_service.review_ehr_integration_config(hosp.id)
    assert ehr_config["configured"] is True
    assert ehr_config["can_activate"] is True

    activated_config = admin_service.activate_ehr_integration(hosp.id)
    assert activated_config.is_active is True

    # 6. View Hospital Activity
    activity = admin_service.view_hospital_activity(hosp.id)
    assert activity["hospital_name"] == "Metro Health Center"
    assert activity["is_active"] is True

    # 7. Suspend Hospital
    hosp_susp = admin_service.suspend_hospital(hosp.id, "Pending safety compliance audit.")
    assert hosp_susp.hospital_status == HospitalStatus.SUSPENDED
    assert hosp_susp.is_active is False
    assert hosp_susp.suspension_reason == "Pending safety compliance audit."

    # 8. Reactivate Hospital
    hosp_react = admin_service.reactivate_hospital(hosp.id)
    assert hosp_react.hospital_status == HospitalStatus.APPROVED
    assert hosp_react.is_active is True


def test_strict_enforcement_doctor_creation(db_session):
    """
    ENFORCEMENT RULE 1: Only approved hospitals can create active doctors.
    """
    onboarding = HospitalSelfServiceOnboardingService(db_session)
    doctor_engine = DoctorJourneyEngine(db_session)

    # Unapproved Draft Hospital
    draft_hosp = onboarding.create_draft_hospital(
        name="Draft Clinic", code="DRAFT-001", contact_email="draft@clinic.org",
        admin_name="Admin", admin_email="admin@clinic.org"
    )

    with pytest.raises(ValueError, match="Only APPROVED and active hospitals can create active doctors"):
        doctor_engine.create_active_doctor(draft_hosp.id, "Dr. Alice", "Neurology")

    # Full journey attempt on unapproved hospital should fail
    with pytest.raises(ValueError, match="Hospital is not approved or is inactive"):
        doctor_engine.execute_full_doctor_journey(
            hospital_id=draft_hosp.id, doctor_name="Dr. Bob", specialty="Cardiology",
            bio="Bio", special_instructions="Instructions", approved_questions=[]
        )


def test_strict_enforcement_availability_publishing(db_session):
    """
    ENFORCEMENT RULE 2: Only approved hospitals can publish availability.
    """
    admin_service = PlatformAdminApprovalService(db_session)
    doctor_engine = DoctorJourneyEngine(db_session)

    # Approved Hospital created with active status initially
    hosp = Hospital(name="City Hospital", code="CITY-001", hospital_status=HospitalStatus.APPROVED, is_active=True)
    db_session.add(hosp)
    db_session.commit()

    doc = doctor_engine.create_active_doctor(hosp.id, "Dr. Charlie", "Pediatrics")
    wh = doctor_engine.publish_doctor_availability(doc.id, 0, time(9, 0), time(17, 0))
    assert wh.id is not None

    # Now suspend hospital and attempt to publish availability
    admin_service.suspend_hospital(hosp.id, "Audit pending")
    with pytest.raises(ValueError, match="Only APPROVED and active hospitals can publish availability"):
        doctor_engine.publish_doctor_availability(doc.id, 1, time(9, 0), time(17, 0))


def test_strict_enforcement_receive_bookings(db_session):
    """
    ENFORCEMENT RULE 3: Only approved hospitals can receive bookings.
    """
    admin_service = PlatformAdminApprovalService(db_session)
    executor = ActionExecutor(db_session)

    hosp = Hospital(name="St. Mary", code="STMARY-001", hospital_status=HospitalStatus.APPROVED, is_active=True)
    db_session.add(hosp)
    db_session.commit()

    doc = Doctor(hospital_id=hosp.id, name="Dr. David", specialty="Orthopedics", is_active=True)
    db_session.add(doc)
    db_session.commit()

    start_dt = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2, hours=10)
    input_data = CreateAppointmentInput(
        session_id="sess-101", patient_id="pat-101", hospital_id=hosp.id, doctor_id=doc.id,
        patient_name="John Doe", patient_phone="+15550001", start_datetime=start_dt
    )

    # Valid booking on APPROVED hospital
    res = executor.create_appointment(input_data)
    assert res.success is True

    # Suspend hospital and attempt booking
    admin_service.suspend_hospital(hosp.id, "Administrative suspension")
    res_suspended = executor.create_appointment(input_data)
    assert res_suspended.success is False
    assert res_suspended.error_code == "HOSPITAL_NOT_APPROVED"


def test_strict_enforcement_ehr_activation(db_session):
    """
    ENFORCEMENT RULE 4: Only approved hospitals can activate supported EHR integrations.
    """
    onboarding = HospitalSelfServiceOnboardingService(db_session)
    admin_service = PlatformAdminApprovalService(db_session)

    hosp = onboarding.create_draft_hospital(
        name="St. Jude", code="STJUDE-001", contact_email="jude@health.org",
        admin_name="Admin", admin_email="admin@health.org"
    )
    onboarding.update_hospital_draft_metadata(hosp.id, ehr_adapter_type=EHRAdapterType.FHIR_R4)

    # Unapproved activation attempt
    with pytest.raises(ValueError, match="Only APPROVED and active hospitals can activate EHR integrations"):
        admin_service.activate_ehr_integration(hosp.id)

    # Approve hospital then activate
    admin_service.approve_hospital(hosp.id)
    config = admin_service.activate_ehr_integration(hosp.id)
    assert config.is_active is True
