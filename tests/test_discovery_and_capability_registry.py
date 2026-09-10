"""
Unit test suite for Section 5.13 Hospital & Doctor Discovery Engine and Section 5.14 Capability Tool Layer.
Tests:
- 7-step Discovery Pipeline ("Find me a dermatologist this Friday afternoon")
- Time window filtering (MORNING, AFTERNOON, EVENING, ANYTIME)
- 19-Capability Tool Registry execution
- Authorization & validation enforcement
- Idempotency caching & audit logging
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, Doctor, PatientProfile, HospitalQuestionnaire, AuditLog
from app.discovery.discovery_engine import HospitalDoctorDiscoveryEngine, DiscoveryRequest
from app.agent.capability_registry import CapabilityRegistry, CapabilityExecutionRequest
from app.onboarding.hospital_onboarding import HospitalSelfServiceOnboardingService
from app.doctors.doctor_management import DoctorManagementService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def setup_hospital_and_doctors(db_session):
    onboarding = HospitalSelfServiceOnboardingService(db_session)
    hosp = onboarding.create_draft_hospital(
        name="St. Jude General Hospital",
        code="STJUDEGEN",
        contact_email="admin@stjudegen.org",
        admin_name="Dr. Sarah",
        admin_email="sarah@stjudegen.org"
    )
    onboarding.submit_application(hosp.id)
    onboarding.approve_hospital(hosp.id)

    doc_svc = DoctorManagementService(db_session)
    doc1 = doc_svc.invite_doctor(
        hospital_id=hosp.id,
        name="Dr. Gregory House",
        specialty="Dermatology",
        department="Dermatology Department"
    )
    doc_svc.activate_doctor(doc1.id)

    doc2 = doc_svc.invite_doctor(
        hospital_id=hosp.id,
        name="Dr. James Wilson",
        specialty="Orthopedics",
        department="Surgery"
    )
    doc_svc.activate_doctor(doc2.id)

    from datetime import time
    from app.calendars.doctor_calendar import DoctorCalendarService
    from app.database.models import DoctorWorkingHour, CalendarType
    cal_svc = DoctorCalendarService(db_session)
    cal_svc.create_doctor_calendar(doc1.id, "Hospital Consultations", CalendarType.HOSPITAL_CONSULTATION)
    cal_svc.create_doctor_calendar(doc2.id, "Hospital Consultations", CalendarType.HOSPITAL_CONSULTATION)

    for day in range(7):
        wh1 = DoctorWorkingHour(doctor_id=doc1.id, day_of_week=day, start_time=time(8, 0), end_time=time(18, 0))
        wh2 = DoctorWorkingHour(doctor_id=doc2.id, day_of_week=day, start_time=time(8, 0), end_time=time(18, 0))
        db_session.add(wh1)
        db_session.add(wh2)


    patient = PatientProfile(
        phone_number="+15559990000",
        full_name="Alice Smith"
    )
    db_session.add(patient)

    q = HospitalQuestionnaire(
        hospital_id=hosp.id,
        title="Dermatology Pre-Visit Form",
        specialty="Dermatology",
        questions_json='["Any skin allergies?"]'
    )
    db_session.add(q)
    db_session.commit()

    return hosp, doc1, doc2, patient, q



def test_section_5_13_discovery_engine_pipeline(db_session, setup_hospital_and_doctors):
    hosp, doc1, doc2, patient, _ = setup_hospital_and_doctors
    discovery = HospitalDoctorDiscoveryEngine(db_session)

    # Execute natural query: "Find me a dermatologist tomorrow afternoon"
    target_d = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    req = DiscoveryRequest(
        query_text="Find me a dermatologist tomorrow afternoon",
        time_window="AFTERNOON",
        target_date=target_d
    )

    res = discovery.execute_discovery(req)

    assert res.status == "SUCCESS"
    assert res.query_understood["specialty"] == "Dermatology"
    assert res.doctors_matched_count >= 1
    assert res.hospitals_matched_count >= 1
    assert "scheduling" in res.cautious_disclaimer or "diagnosis" in res.cautious_disclaimer


def test_section_5_14_capability_registry_19_capabilities(db_session, setup_hospital_and_doctors):
    hosp, doc1, doc2, patient, q = setup_hospital_and_doctors
    registry = CapabilityRegistry(db_session)

    # 1. Registered Capabilities Check
    caps = registry.get_registered_capabilities()
    assert len(caps) == 19
    assert "search_hospitals" in caps
    assert "create_appointment" in caps
    assert "transfer_to_human" in caps

    # 2. Test search_doctors capability
    exec_req = CapabilityExecutionRequest(
        capability_name="search_doctors",
        arguments={"specialty": "Dermatology"},
        caller_role="PATIENT_AGENT"
    )
    res = registry.execute(exec_req)
    assert res.success is True
    assert len(res.data["doctors"]) >= 1

    # 3. Test check_availability capability
    avail_req = CapabilityExecutionRequest(
        capability_name="check_availability",
        arguments={"doctor_id": doc1.id},
        caller_role="PATIENT_AGENT"
    )
    avail_res = registry.execute(avail_req)
    assert avail_res.success is True

    # 4. Test Idempotency Behavior for mutation capability
    idem_key = f"IDEM-{uuid.uuid4()}"
    create_req = CapabilityExecutionRequest(
        capability_name="create_appointment",
        arguments={
            "hospital_id": hosp.id,
            "doctor_id": doc1.id,
            "patient_name": "Alice Smith",
            "patient_phone": "+15559990000"
        },
        caller_role="PATIENT_AGENT",
        idempotency_key=idem_key
    )

    res1 = registry.execute(create_req)
    assert res1.success is True
    assert res1.idempotent_replay is False

    # Second execution with same idempotency_key returns cached response
    res2 = registry.execute(create_req)
    assert res2.success is True
    assert res2.idempotent_replay is True

    # 5. Test Authorization Check Failure
    unauth_req = CapabilityExecutionRequest(
        capability_name="create_appointment",
        arguments={},
        caller_role="UNAUTHORIZED_ROLE"
    )
    unauth_res = registry.execute(unauth_req)
    assert unauth_res.success is False
    assert "Unauthorized" in unauth_res.message

    # 6. Test Audit Logging
    logs = db_session.query(AuditLog).all()
    assert len(logs) > 0
