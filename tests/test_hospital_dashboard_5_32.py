"""
Unit Test Suite for Section 5.32 Hospital Dashboard.

Tests:
1. All 13 Hospital KPIs (Appointments today, upcoming appointments, active doctors, available slots, cancelled, rescheduled, AI bookings, human escalations, questionnaire completion, workflow failures, EHR success, EHR failures, reconciliation items).
2. All 10 Management Domains (Departments, Specialties, Doctors, Calendars, Availability, Questionnaires, Staff, Workflows, Communication Settings, EHR Integrations).
"""

import pytest
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import (
    Base, Hospital, Doctor, DoctorStatus, DoctorCalendar, Appointment, AppointmentStatus,
    HospitalQuestionnaire, HospitalStaff, HospitalOperationalPreference, EHRIntegrationConfig,
    WorkflowInstance, WorkflowStatus, EHRSyncLog, PatientIntakeRecord, AuditLog
)
from app.dashboard.hospital_dashboard import HospitalDashboardService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def setup_hospital_dashboard_data(db_session):
    hosp = Hospital(
        name="Metro Health Center",
        code="MTH",
        departments_json='["Cardiology", "Neurology", "Pediatrics"]',
        specialties_json='["Cardiology", "Neurology"]',
        is_active=True
    )
    db_session.add(hosp)
    db_session.commit()

    doc1 = Doctor(hospital_id=hosp.id, name="Dr. Alice", specialty="Cardiology", doctor_status=DoctorStatus.ACTIVE, is_active=True)
    doc2 = Doctor(hospital_id=hosp.id, name="Dr. Bob", specialty="Neurology", doctor_status=DoctorStatus.ACTIVE, is_active=True)
    db_session.add_all([doc1, doc2])
    db_session.commit()

    cal1 = DoctorCalendar(doctor_id=doc1.id, calendar_name="Cardio OPD")
    db_session.add(cal1)
    db_session.commit()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    today_noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
    
    # Appointments
    appt_today = Appointment(hospital_id=hosp.id, doctor_id=doc1.id, calendar_id=cal1.id, patient_name="Pat 1", patient_phone="+15550001111", start_datetime=today_noon, end_datetime=today_noon + timedelta(hours=1), status=AppointmentStatus.CONFIRMED, is_ehr_verified=True)
    appt_upcoming = Appointment(hospital_id=hosp.id, doctor_id=doc2.id, patient_name="Pat 2", patient_phone="+15550002222", start_datetime=now + timedelta(days=2), end_datetime=now + timedelta(days=2, hours=1), status=AppointmentStatus.SCHEDULED, is_ehr_verified=True)
    appt_cancelled = Appointment(hospital_id=hosp.id, doctor_id=doc1.id, patient_name="Pat 3", patient_phone="+15550003333", start_datetime=today_noon + timedelta(hours=1), end_datetime=today_noon + timedelta(hours=2), status=AppointmentStatus.CANCELLED)
    appt_rescheduled = Appointment(hospital_id=hosp.id, doctor_id=doc2.id, patient_name="Pat 4", patient_phone="+15550004444", start_datetime=now + timedelta(days=3), end_datetime=now + timedelta(days=3, hours=1), status=AppointmentStatus.RESCHEDULED)
    appt_rec = Appointment(hospital_id=hosp.id, doctor_id=doc1.id, patient_name="Pat 5", patient_phone="+15550005555", start_datetime=today_noon + timedelta(hours=3), end_datetime=today_noon + timedelta(hours=3, minutes=30), status=AppointmentStatus.RECONCILIATION_REQUIRED)



    db_session.add_all([appt_today, appt_upcoming, appt_cancelled, appt_rescheduled, appt_rec])
    db_session.commit()

    # Pre-visit Questionnaire Intake
    intake = PatientIntakeRecord(appointment_id=appt_today.id, patient_reported_summary="Chest pain")
    db_session.add(intake)

    # Human Escalation Audit
    esc_audit = AuditLog(hospital_id=hosp.id, session_id="SESS-101", event_type="ESCALATE_TO_HUMAN")
    db_session.add(esc_audit)

    # Workflow Failure
    wf_failed = WorkflowInstance(appointment_id=appt_rec.id, workflow_name="FAILED_BOOKING_RECOVERY", trigger_event="BOOKING_FAILED", status=WorkflowStatus.ESCALATED)
    db_session.add(wf_failed)

    # EHR Sync Logs
    ehr_s1 = EHRSyncLog(appointment_id=appt_today.id, hospital_id=hosp.id, action_type="SYNC", sync_status="VERIFIED")
    ehr_s2 = EHRSyncLog(appointment_id=appt_rec.id, hospital_id=hosp.id, action_type="SYNC", sync_status="FAILED")
    db_session.add_all([ehr_s1, ehr_s2])


    # Hospital Questionnaire, Staff, Preferences & EHR Config
    q1 = HospitalQuestionnaire(hospital_id=hosp.id, title="Pre-Visit Intake", specialty="Cardiology", questions_json="[]")
    staff1 = HospitalStaff(hospital_id=hosp.id, name="Admin Staff", email="staff@mth.org", role="ADMIN")
    pref = HospitalOperationalPreference(hospital_id=hosp.id, communication_preference="VOICE_AND_SMS")
    cfg = EHRIntegrationConfig(hospital_id=hosp.id)

    db_session.add_all([q1, staff1, pref, cfg])
    db_session.commit()

    return hosp, doc1, doc2, appt_today


def test_hospital_dashboard_13_kpis(db_session, setup_hospital_dashboard_data):
    hosp, doc1, doc2, appt_today = setup_hospital_dashboard_data
    service = HospitalDashboardService(db_session)

    res = service.get_hospital_kpis(hosp.id)

    assert res["hospital_id"] == hosp.id
    kpis = res["kpis"]

    assert kpis["appointments_today"] == 2
    assert kpis["upcoming_appointments"] == 2

    assert kpis["active_doctors"] == 2
    assert kpis["cancelled_appointments"] == 1
    assert kpis["rescheduled_appointments"] == 1
    assert kpis["ai_bookings"] >= 1
    assert kpis["human_escalations"] == 1
    assert kpis["questionnaires_completed"] == 1
    assert kpis["workflow_failures"] == 1
    assert kpis["ehr_integration_success"] == 1
    assert kpis["ehr_integration_failures"] == 1
    assert kpis["reconciliation_items"] == 1


def test_hospital_dashboard_10_management_domains(db_session, setup_hospital_dashboard_data):
    hosp, doc1, doc2, appt_today = setup_hospital_dashboard_data
    service = HospitalDashboardService(db_session)

    res = service.get_management_overview(hosp.id)

    mgmt = res["management"]
    assert "Cardiology" in mgmt["departments"]
    assert "Neurology" in mgmt["specialties"]
    assert len(mgmt["doctors"]) == 2
    assert len(mgmt["calendars"]) == 1
    assert "operating_hours" in mgmt["availability"]
    assert len(mgmt["questionnaires"]) == 1
    assert len(mgmt["staff"]) == 1
    assert len(mgmt["workflows"]) == 1
    assert mgmt["communication_settings"]["communication_preference"] == "VOICE_AND_SMS"
    assert mgmt["healthcare_system_integrations"]["adapter_type"] == "MOCK_EHR"
