"""
Unit Test Suite for Section 5.31 Doctor Dashboard.

Tests:
1. Doctor Home Overview (Today's, Upcoming, Pending & Completed questionnaires).
2. Doctor Calendar Management (Day/Week/Month views, Multiple Calendars, Booked/Available/Blocked/Leave slots).
3. 360-Degree Appointment Details (Patient, Appointment, Hospital, Pre-visit questionnaire, Authorized Context, External EHR Mapping).
4. Doctor Leave Management.
"""

import pytest
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import (
    Base, Hospital, Doctor, DoctorCalendar, CalendarType, Appointment, AppointmentStatus,
    PatientProfile, PatientIntakeRecord, EHRMapping, BlockedSlot, DoctorLeave
)
from app.dashboard.dashboard_service import DoctorDashboardService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def setup_dashboard_data(db_session):
    hosp = Hospital(name="St. Mary Hospital", code="SMMC", is_active=True)
    db_session.add(hosp)
    db_session.commit()

    doc = Doctor(
        hospital_id=hosp.id,
        name="Dr. Gregory House",
        specialty="Diagnostics",
        is_active=True
    )
    db_session.add(doc)
    db_session.commit()

    cal1 = DoctorCalendar(doctor_id=doc.id, calendar_name="Main Clinic", calendar_type=CalendarType.HOSPITAL_CONSULTATION)
    cal2 = DoctorCalendar(doctor_id=doc.id, calendar_name="Telehealth", calendar_type=CalendarType.ONLINE_CONSULTATION)
    db_session.add_all([cal1, cal2])
    db_session.commit()

    patient = PatientProfile(
        phone_number="+15551112222",
        full_name="James Wilson",
        email="wilson@example.com",
        preferred_language="English",
        external_patient_id="EXT-PAT-909",
        interaction_notes="Patient has history of knee injury."
    )
    db_session.add(patient)
    db_session.commit()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Today's Appointment
    appt_today = Appointment(
        hospital_id=hosp.id,
        doctor_id=doc.id,
        calendar_id=cal1.id,
        patient_name="James Wilson",
        patient_phone="+15551112222",
        patient_email="wilson@example.com",
        start_datetime=now + timedelta(hours=1),
        end_datetime=now + timedelta(hours=1, minutes=30),
        status=AppointmentStatus.CONFIRMED,
        is_ehr_verified=True
    )
    # Upcoming Appointment
    appt_upcoming = Appointment(
        hospital_id=hosp.id,
        doctor_id=doc.id,
        calendar_id=cal2.id,
        patient_name="Sarah Connor",
        patient_phone="+15553334444",
        start_datetime=now + timedelta(days=1, hours=2),
        end_datetime=now + timedelta(days=1, hours=2, minutes=30),
        status=AppointmentStatus.SCHEDULED,
        is_ehr_verified=False
    )
    db_session.add_all([appt_today, appt_upcoming])
    db_session.commit()

    # Pre-visit Questionnaire Intake
    intake = PatientIntakeRecord(
        appointment_id=appt_today.id,
        patient_reported_summary="Leg pain and mild swelling for past 3 days.",
        intake_answers_json='{"pain_level": "6", "onset": "3 days ago"}'
    )
    db_session.add(intake)

    # EHR Mapping
    ehr_map = EHRMapping(
        hospital_id=hosp.id,
        entity_type="APPOINTMENT",
        internal_id=appt_today.id,
        external_ehr_id="EPIC-APPT-8899"
    )
    db_session.add(ehr_map)
    db_session.commit()

    return hosp, doc, patient, appt_today, appt_upcoming, cal1, cal2


def test_doctor_home_summary(db_session, setup_dashboard_data):
    hosp, doc, patient, appt_today, appt_upcoming, cal1, cal2 = setup_dashboard_data
    service = DoctorDashboardService(db_session)

    summary = service.get_home_summary(doc.id)

    assert summary["doctor_name"] == "Dr. Gregory House"
    assert summary["summary_counts"]["todays_appointments_count"] == 1
    assert summary["summary_counts"]["upcoming_appointments_count"] == 1
    assert len(summary["todays_appointments"]) == 1
    assert summary["todays_appointments"][0]["patient_name"] == "James Wilson"
    assert len(summary["recently_completed_questionnaires"]) == 1


def test_doctor_calendar_views(db_session, setup_dashboard_data):
    hosp, doc, patient, appt_today, appt_upcoming, cal1, cal2 = setup_dashboard_data
    service = DoctorDashboardService(db_session)

    # 1. Day View
    cal_day = service.get_calendar_view(doc.id, view_type="DAY")
    assert cal_day["view_type"] == "DAY"
    assert len(cal_day["calendars"]) == 2
    assert len(cal_day["booked_slots"]) == 1

    # 2. Multiple Calendars Filter (Only cal1)
    cal_filtered = service.get_calendar_view(doc.id, view_type="DAY", calendar_ids=[cal1.id])
    assert len(cal_filtered["calendars"]) == 1
    assert cal_filtered["calendars"][0]["id"] == cal1.id

    # 3. Week & Month View
    cal_week = service.get_calendar_view(doc.id, view_type="WEEK")
    assert cal_week["view_type"] == "WEEK"
    assert len(cal_week["booked_slots"]) >= 2

    cal_month = service.get_calendar_view(doc.id, view_type="MONTH")
    assert cal_month["view_type"] == "MONTH"


def test_360_degree_appointment_details(db_session, setup_dashboard_data):
    hosp, doc, patient, appt_today, appt_upcoming, cal1, cal2 = setup_dashboard_data
    service = DoctorDashboardService(db_session)

    details = service.get_appointment_details(doc.id, appt_today.id)

    assert details["appointment_id"] == appt_today.id
    assert details["patient"]["name"] == "James Wilson"
    assert details["patient"]["phone_number"] == "+15551112222"
    assert details["patient"]["external_patient_id"] == "EXT-PAT-909"

    assert details["hospital"]["name"] == "St. Mary Hospital"
    assert details["appointment"]["is_ehr_verified"] is True

    # Questionnaire responses
    assert details["pre_visit_questionnaire"]["has_submitted"] is True
    assert "Leg pain" in details["pre_visit_questionnaire"]["patient_reported_symptoms"]

    # Authorized Context & EHR reference
    assert "knee injury" in details["relevant_authorized_context"]["interaction_notes"]
    assert details["external_ehr_reference"] == "EPIC-APPT-8899"


def test_doctor_leave_management(db_session, setup_dashboard_data):
    hosp, doc, patient, appt_today, appt_upcoming, cal1, cal2 = setup_dashboard_data
    service = DoctorDashboardService(db_session)

    start_l = date.today() + timedelta(days=5)
    end_l = date.today() + timedelta(days=7)

    leave = service.create_doctor_leave(
        doctor_id=doc.id,
        start_date=start_l,
        end_date=end_l,
        leave_type="CONFERENCE",
        reason="Medical Cardiology Summit"
    )

    assert leave.id is not None
    assert leave.leave_type == "CONFERENCE"

    # Verify leave appears in doctor's leave query
    leaves = service.get_doctor_leaves(doc.id)
    assert len(leaves) == 1
    assert leaves[0].reason == "Medical Cardiology Summit"

    # Verify BlockedSlot automatically created
    blocked = db_session.query(BlockedSlot).filter(BlockedSlot.doctor_id == doc.id).first()
    assert blocked is not None
    assert "ON_LEAVE" in blocked.reason
