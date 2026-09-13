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


from sqlalchemy.pool import StaticPool


@pytest.fixture
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(test_engine):
    Session = sessionmaker(bind=test_engine)
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


def test_list_hospital_applications_and_filtering(db_session):
    """
    Test listing hospital applications with pending, approved, and rejected filters.
    """
    admin_service = PlatformAdminApprovalService(db_session)

    # Seed diverse hospital states
    h1 = Hospital(name="Pending Clinic", code="PEND-01", hospital_status=HospitalStatus.SUBMITTED, is_active=False)
    h2 = Hospital(name="Under Review Pavilion", code="REV-01", hospital_status=HospitalStatus.UNDER_REVIEW, is_active=False)
    h3 = Hospital(name="Active General", code="ACT-01", hospital_status=HospitalStatus.APPROVED, is_active=True)
    h4 = Hospital(name="Rejected Infirmary", code="REJ-01", hospital_status=HospitalStatus.REJECTED, is_active=False, rejection_reason="Missing accreditation")
    db_session.add_all([h1, h2, h3, h4])
    db_session.commit()

    # 1. Filter PENDING
    pending = admin_service.list_hospital_applications(status_filter="PENDING")
    assert len(pending["hospitals"]) == 2
    assert pending["counts"]["pending"] == 2
    assert pending["counts"]["approved"] == 1
    assert pending["counts"]["rejected"] == 1
    assert pending["counts"]["total"] == 4

    # 2. Filter APPROVED
    approved = admin_service.list_hospital_applications(status_filter="APPROVED")
    assert len(approved["hospitals"]) == 1
    assert approved["hospitals"][0]["code"] == "ACT-01"

    # 3. Filter REJECTED
    rejected = admin_service.list_hospital_applications(status_filter="REJECTED")
    assert len(rejected["hospitals"]) == 1
    assert rejected["hospitals"][0]["rejection_reason"] == "Missing accreditation"

    # 4. Filter ALL
    all_hosp = admin_service.list_hospital_applications(status_filter="ALL")
    assert len(all_hosp["hospitals"]) == 4


def test_approval_and_rejection_synchronizes_user_accounts(db_session):
    """
    Test that approving/rejecting a hospital automatically activates/deactivates
    the hospital administrator's UserAccount credentials.
    """
    from app.database.models import UserAccount

    admin_service = PlatformAdminApprovalService(db_session)

    # Create submitted hospital
    hosp = Hospital(
        name="Oakland Specialty Hospital",
        code="OAK-01",
        hospital_status=HospitalStatus.SUBMITTED,
        is_active=False,
        contact_email="admin@oakland.org"
    )
    db_session.add(hosp)
    db_session.commit()

    # Associated hospital admin account (inactive while hospital is pending)
    user = UserAccount(
        email="admin@oakland.org",
        full_name="Admin Oakland",
        password_hash="hashed_dummy_password",
        role="HOSPITAL_ADMIN",
        hospital_id=hosp.id,
        is_active=False
    )
    db_session.add(user)
    db_session.commit()

    # 1. Approve hospital
    approved_hosp = admin_service.approve_hospital(hosp.id)
    assert approved_hosp.is_active is True
    assert approved_hosp.hospital_status == HospitalStatus.APPROVED
    db_session.refresh(user)
    assert user.is_active is True

    # 2. Reject hospital
    rejected_hosp = admin_service.reject_hospital(hosp.id, "Failed physical site inspection")
    assert rejected_hosp.is_active is False
    assert rejected_hosp.hospital_status == HospitalStatus.REJECTED
    assert rejected_hosp.rejection_reason == "Failed physical site inspection"
    db_session.refresh(user)
    assert user.is_active is False


def test_admin_hospital_api_endpoints(test_engine):
    """
    Test onboarding and admin approval endpoints via FastAPI TestClient.
    """
    import uuid
    from fastapi.testclient import TestClient
    from app.database.config import get_db
    from app.main import app

    TestingSession = sessionmaker(bind=test_engine)

    def _override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as client:
            uid = uuid.uuid4().hex[:6].upper()

            # 1. Self-service hospital registration
            reg_payload = {
                "name": f"Test Hospital {uid}",
                "code": f"TH-{uid}",
                "contact_email": f"admin-{uid}@test-hospital.org",
                "admin_name": f"Dr. Admin {uid}",
                "admin_email": f"admin-{uid}@test-hospital.org",
                "admin_password": "secure_password_123",
                "departments": ["Pediatrics", "Emergency"]
            }
            resp_reg = client.post("/api/v1/onboarding/register", json=reg_payload)
            assert resp_reg.status_code == 200
            res_json = resp_reg.json()
            assert res_json["status"] == "success"
            hosp_data = res_json["hospital"]
            hosp_id = hosp_data["hospital_id"]
            assert hosp_data["status"] == "SUBMITTED"
            assert hosp_data["is_active"] is False

            # 2. List hospital requests (filter PENDING)
            resp_list = client.get("/api/v1/admin/hospitals?status=PENDING")
            assert resp_list.status_code == 200
            list_data = resp_list.json()
            assert list_data["counts"]["pending"] >= 1
            found = any(h["id"] == hosp_id for h in list_data["hospitals"])
            assert found is True

            # 3. Approve the hospital
            resp_app = client.post(f"/api/v1/admin/hospitals/{hosp_id}/approve")
            assert resp_app.status_code == 200
            app_data = resp_app.json()
            assert app_data["hospital_status"] == "APPROVED"
            assert app_data["is_active"] is True

            # 4. Reject the hospital with rationale
            resp_rej = client.post(
                f"/api/v1/admin/hospitals/{hosp_id}/reject",
                json={"rejection_reason": "Auditing flagged regulatory discrepancy"}
            )
            assert resp_rej.status_code == 200
            rej_data = resp_rej.json()
            assert rej_data["hospital_status"] == "REJECTED"
            assert rej_data["is_active"] is False
            assert rej_data["rejection_reason"] == "Auditing flagged regulatory discrepancy"
    finally:
        app.dependency_overrides.clear()
