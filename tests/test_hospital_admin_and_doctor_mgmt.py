"""
Test Suite for Section 5.3 Hospital Administration & Section 5.4 Doctor Management.
"""

from datetime import datetime, time, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import (
    Base, Hospital, HospitalStatus, Doctor, DoctorStatus, ConsultationType,
    EHRAdapterType, Appointment
)
from app.admin.hospital_admin import HospitalAdminService
from app.doctors.doctor_management import DoctorManagementService
from app.agent.actions import ActionExecutor
from app.schemas.actions import CreateAppointmentInput, SearchDoctorsInput


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_hospital_administration_and_isolation(db_session):
    """
    Tests 13 hospital administration operations and multi-tenant data isolation.
    """
    admin_service = HospitalAdminService(db_session)

    # Create Hospital A & Hospital B
    hosp_a = Hospital(name="Hospital Alpha", code="ALPHA-001", hospital_status=HospitalStatus.APPROVED, is_active=True)
    hosp_b = Hospital(name="Hospital Beta", code="BETA-001", hospital_status=HospitalStatus.APPROVED, is_active=True)
    db_session.add_all([hosp_a, hosp_b])
    db_session.commit()

    # 1. Update Profile for Hosp A
    admin_service.update_hospital_profile(hosp_a.id, address="123 Alpha St", phone="+15551111")
    prof_a = admin_service.get_hospital_profile(hosp_a.id)
    assert prof_a["address"] == "123 Alpha St"

    # 2. Departments & Specialties
    admin_service.update_departments_and_specialties(
        hosp_a.id, departments=["Cardiology", "Oncology"], specialties=["Cardiology"]
    )
    prof_a_updated = admin_service.get_hospital_profile(hosp_a.id)
    assert "Cardiology" in prof_a_updated["departments"]

    # 3. Appointment Settings
    pref_a = admin_service.update_appointment_settings(hosp_a.id, max_advance_booking_days=45)
    assert pref_a.max_advance_booking_days == 45

    # 4. Staff Management & Multi-Tenant Isolation
    staff_a = admin_service.add_staff_member(hosp_a.id, "Alice Admin", "alice@alpha.org", role="CLINIC_MANAGER")
    staff_b = admin_service.add_staff_member(hosp_b.id, "Bob Admin", "bob@beta.org", role="RECEPTIONIST")

    staff_list_a = admin_service.list_staff_members(hosp_a.id)
    staff_list_b = admin_service.list_staff_members(hosp_b.id)

    # ISOLATION ASSERTIONS: Hosp A cannot see Hosp B's staff!
    assert len(staff_list_a) == 1
    assert staff_list_a[0]["email"] == "alice@alpha.org"
    assert len(staff_list_b) == 1
    assert staff_list_b[0]["email"] == "bob@beta.org"

    # 5. Communication Preferences
    comm_pref = admin_service.update_communication_preferences(hosp_a.id, communication_preference="VOICE_ONLY", sms_enabled=False)
    assert comm_pref.communication_preference == "VOICE_ONLY"

    # 6. Questionnaires
    q = admin_service.create_questionnaire(hosp_a.id, "Chest Pain Screening", "Cardiology", ["Have you felt pressure in your chest?"])
    qs_a = admin_service.list_questionnaires(hosp_a.id)
    qs_b = admin_service.list_questionnaires(hosp_b.id)
    assert len(qs_a) == 1
    assert len(qs_b) == 0  # ISOLATION ASSERTION

    # 7. EHR Integration Configuration
    config = admin_service.configure_ehr_integration(hosp_a.id, adapter_type=EHRAdapterType.FHIR_R4, endpoint_url="https://fhir.alpha.org/r4")
    assert config.adapter_type == EHRAdapterType.FHIR_R4

    # 8. Isolated Analytics
    analytics_a = admin_service.get_isolated_hospital_analytics(hosp_a.id)
    assert analytics_a["hospital_name"] == "Hospital Alpha"


def test_doctor_management_lifecycle_and_enforcement(db_session):
    """
    Tests Doctor Management lifecycle states (INVITED -> ACTIVE -> INACTIVE -> SUSPENDED)
    and strict booking enforcement rules.
    """
    doc_service = DoctorManagementService(db_session)
    executor = ActionExecutor(db_session)

    hosp = Hospital(name="General Hospital", code="GEN-001", hospital_status=HospitalStatus.APPROVED, is_active=True)
    db_session.add(hosp)
    db_session.commit()

    # 1. Invite Doctor (State = INVITED, is_active = False)
    doc = doc_service.invite_doctor(
        hospital_id=hosp.id,
        name="Dr. Elena Vance",
        specialty="Neurology",
        qualifications="MD, PhD",
        experience_years=12,
        languages=["English", "French"],
        consultation_type=ConsultationType.HYBRID,
        external_provider_id="NPI-998877"
    )
    assert doc.doctor_status == DoctorStatus.INVITED
    assert doc.is_active is False

    # SEARCH ENFORCEMENT: INVITED doctor must not appear in search
    search_res = executor.search_doctors(SearchDoctorsInput(session_id="s1", patient_id="p1", hospital_id=hosp.id))
    assert len(search_res.doctors) == 0

    # BOOKING ENFORCEMENT: Booking attempt for INVITED doctor must fail
    start_dt = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2, hours=9)
    input_data = CreateAppointmentInput(
        session_id="s1", patient_id="p1", hospital_id=hosp.id, doctor_id=doc.id,
        patient_name="Mark Smith", patient_phone="+15552222", start_datetime=start_dt
    )
    res_invited = executor.create_appointment(input_data)
    assert res_invited.success is False
    assert res_invited.error_code == "DOCTOR_NOT_ACTIVE"

    # 2. Activate Doctor (State = ACTIVE, is_active = True)
    doc_service.activate_doctor(doc.id)
    doc_profile = doc_service.get_doctor_profile(doc.id)
    assert doc_profile["doctor_status"] == DoctorStatus.ACTIVE.value
    assert doc_profile["is_active"] is True

    # Search and Booking should now succeed for ACTIVE doctor
    search_res_active = executor.search_doctors(SearchDoctorsInput(session_id="s1", patient_id="p1", hospital_id=hosp.id))
    assert len(search_res_active.doctors) == 1

    res_active = executor.create_appointment(input_data)
    assert res_active.success is True

    # 3. Deactivate Doctor (State = INACTIVE)
    doc_service.deactivate_doctor(doc.id)
    input_data_2 = CreateAppointmentInput(
        session_id="s2", patient_id="p2", hospital_id=hosp.id, doctor_id=doc.id,
        patient_name="Sarah Connor", patient_phone="+15553333", start_datetime=start_dt + timedelta(hours=1)
    )
    res_inactive = executor.create_appointment(input_data_2)
    assert res_inactive.success is False
    assert res_inactive.error_code == "DOCTOR_NOT_ACTIVE"

    # 4. Suspend Doctor (State = SUSPENDED)
    doc_service.suspend_doctor(doc.id, reason="Medical board review")
    doc_suspended_profile = doc_service.get_doctor_profile(doc.id)
    assert doc_suspended_profile["doctor_status"] == DoctorStatus.SUSPENDED.value
    assert "SUSPENDED" in doc_suspended_profile["special_instructions"]

    res_suspended = executor.create_appointment(input_data_2)
    assert res_suspended.success is False
    assert res_suspended.error_code == "DOCTOR_NOT_ACTIVE"
