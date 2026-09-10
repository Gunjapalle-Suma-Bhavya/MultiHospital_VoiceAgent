"""
Test Suite for Section 5.5 Doctor Calendar Management, Section 5.6 Availability Engine & Section 5.7 Appointment Management.
"""

from datetime import datetime, date, time, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import (
    Base, Hospital, HospitalStatus, Doctor, DoctorStatus, CalendarType, DoctorWorkingHour, BlockedSlot, AppointmentStatus
)
from app.calendars.doctor_calendar import DoctorCalendarService
from app.scheduling.availability_engine import AvailabilityEngine
from app.appointments.appointment_management import AppointmentService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_doctor_calendar_management_and_aggregated_view(db_session):
    """
    Tests Section 5.5: Multi-calendar creation and aggregated calendar view.
    """
    cal_service = DoctorCalendarService(db_session)

    hosp = Hospital(name="Mercy Hospital", code="MERCY-001", hospital_status=HospitalStatus.APPROVED, is_active=True)
    db_session.add(hosp)
    db_session.commit()

    doc = Doctor(hospital_id=hosp.id, name="Dr. Frank", specialty="Dermatology", doctor_status=DoctorStatus.ACTIVE, is_active=True)
    db_session.add(doc)
    db_session.commit()

    # Create working hours
    wh = DoctorWorkingHour(doctor_id=doc.id, day_of_week=0, start_time=time(9, 0), end_time=time(17, 0), break_start=time(12, 0), break_end=time(13, 0))
    db_session.add(wh)
    db_session.commit()

    # 1. Create multiple calendars
    cal_hosp = cal_service.create_doctor_calendar(doc.id, "Hospital Consultations", CalendarType.HOSPITAL_CONSULTATION)
    cal_tele = cal_service.create_doctor_calendar(doc.id, "Telehealth Consultations", CalendarType.ONLINE_CONSULTATION)

    cals = cal_service.list_doctor_calendars(doc.id)
    assert len(cals) == 2

    # 2. Aggregated calendar view
    target_date = date(2026, 9, 14)  # Monday
    view = cal_service.get_calendar_aggregated_view(doc.id, target_date, calendar_id=cal_hosp.id)
    assert view["working_hours"]["start_time"] == "09:00"
    assert view["lunch_break"]["break_start"] == "12:00"


def test_availability_engine_10_step_pipeline_and_anti_hallucination(db_session):
    """
    Tests Section 5.6: 10-step availability decision pipeline and anti-hallucination slot query.
    """
    avail_engine = AvailabilityEngine(db_session)

    hosp = Hospital(name="St. Paul", code="STPAUL-001", hospital_status=HospitalStatus.APPROVED, is_active=True)
    db_session.add(hosp)
    db_session.commit()

    doc = Doctor(hospital_id=hosp.id, name="Dr. Grace", specialty="Pediatrics", doctor_status=DoctorStatus.ACTIVE, is_active=True, default_appointment_duration=30)
    db_session.add(doc)
    db_session.commit()

    target_date = date(2026, 9, 14)  # Monday (day_of_week = 0)
    wh = DoctorWorkingHour(doctor_id=doc.id, day_of_week=0, start_time=time(9, 0), end_time=time(12, 0), break_start=time(12, 0), break_end=time(13, 0))
    db_session.add(wh)
    db_session.commit()

    # 1. Query anti-hallucinated slots
    slots = avail_engine.query_actual_availability(doc.id, target_date)
    assert len(slots) > 0

    # 2. Block 09:30 slot with Leave
    block_start = datetime.combine(target_date, time(9, 30))
    block_end = datetime.combine(target_date, time(10, 0))
    bs = BlockedSlot(doctor_id=doc.id, start_datetime=block_start, end_datetime=block_end, reason="Medical Leave")
    db_session.add(bs)
    db_session.commit()

    # 3. Evaluate blocked slot pipeline
    eval_blocked = avail_engine.evaluate_slot_pipeline(doc.id, block_start, block_end)
    assert eval_blocked["is_bookable"] is False
    assert eval_blocked["failure_step"] in [4, 5]

    # 4. Evaluate valid slot 09:00 - 09:30
    eval_valid = avail_engine.evaluate_slot_pipeline(doc.id, datetime.combine(target_date, time(9, 0)), block_start)
    assert eval_valid["is_bookable"] is True
    assert len(eval_valid["10_step_pipeline_trace"]) == 10


def test_appointment_management_lifecycle_and_history(db_session):
    """
    Tests Section 5.7: Appointment 10-state lifecycle, dual-state tracking, and change history audit logs.
    """
    appt_service = AppointmentService(db_session)

    hosp = Hospital(name="City Care", code="CARE-001", hospital_status=HospitalStatus.APPROVED, is_active=True)
    db_session.add(hosp)
    db_session.commit()

    doc = Doctor(hospital_id=hosp.id, name="Dr. Henry", specialty="Cardiology", doctor_status=DoctorStatus.ACTIVE, is_active=True, default_appointment_duration=30)
    db_session.add(doc)
    db_session.commit()

    wh = DoctorWorkingHour(doctor_id=doc.id, day_of_week=0, start_time=time(9, 0), end_time=time(17, 0))
    db_session.add(wh)
    db_session.commit()

    start_dt = datetime(2026, 9, 14, 10, 0)

    # 1. Create Appointment Request (State = PENDING)
    appt = appt_service.create_appointment_request(
        hospital_id=hosp.id,
        doctor_id=doc.id,
        patient_name="Michael Jordan",
        patient_phone="+15559999",
        start_datetime=start_dt
    )
    assert appt.status == AppointmentStatus.PENDING
    assert appt.external_status == "PENDING_SYNC"

    # 2. Confirm Appointment (State = CONFIRMED)
    appt_confirmed = appt_service.confirm_appointment(appt.id)
    assert appt_confirmed.status in [AppointmentStatus.CONFIRMED, AppointmentStatus.RECONCILIATION_REQUIRED]

    # 3. Reschedule Appointment
    new_dt = datetime(2026, 9, 14, 14, 0)
    appt_rescheduled = appt_service.reschedule_appointment(appt.id, new_dt, reason="Patient requested afternoon slot")
    assert appt_rescheduled.status == AppointmentStatus.RESCHEDULED
    assert appt_rescheduled.start_datetime == new_dt

    # 4. Complete Appointment
    appt_completed = appt_service.complete_appointment(appt.id)
    assert appt_completed.status == AppointmentStatus.COMPLETED

    # 5. Check Change History Audit Log Trail
    history = appt_service.get_appointment_history(appt.id)
    assert len(history) >= 4
    assert history[0]["new_status"] == AppointmentStatus.PENDING.value
    assert history[-1]["new_status"] == AppointmentStatus.COMPLETED.value
