"""
Unit Test Suite for Section 5.30 Notification System.

Tests:
1. Patient Notification Triggers (Appointment confirmation, reminder, reschedule, cancel, questionnaire reminder/completion, workflow/integration updates).
2. Doctor Notification Triggers (New appointment, cancellation, rescheduled, questionnaire completed, upcoming appointment, operational notifications).
3. Hospital Notification Triggers (Approval, rejection, new appointment, cancellation, rescheduling, doctor status changes, operational alerts, integration failures).
4. Notification log retrieval and preference configuration.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, NotificationRecord, NotificationRecipientRole
from app.notifications.notification_engine import NotificationEngine


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_patient_notifications(db_session):
    notifier = NotificationEngine(db_session)
    phone = "+15551234567"

    n1 = notifier.notify_patient_appointment_confirmation(phone, "Dr. House", "Mercy Hospital", "2026-09-15 10:00")
    assert n1.recipient_role == "PATIENT"
    assert "Confirmed" in n1.body

    n2 = notifier.notify_patient_appointment_reminder(phone, "Dr. House", "Mercy Hospital", "2026-09-15 10:00")
    assert "Reminder" in n2.body

    n3 = notifier.notify_patient_reschedule(phone, "Dr. House", "Mercy Hospital", "2026-09-16 11:00")
    assert "Rescheduled" in n3.body

    n4 = notifier.notify_patient_cancellation(phone, "Dr. House", "Mercy Hospital", "2026-09-15 10:00")
    assert "Cancelled" in n4.body

    n5 = notifier.notify_patient_questionnaire_reminder(phone, "Dr. House")
    assert "Questionnaire Pending" in n5.body

    n6 = notifier.notify_patient_questionnaire_completion(phone, "Dr. House")
    assert "received and verified" in n6.body

    n7 = notifier.notify_patient_workflow_update(phone, "APPOINTMENT_REMINDER", "COMPLETED")
    assert "Workflow Update" in n7.body

    n8 = notifier.notify_patient_integration_update(phone, "Dr. House", "VERIFIED")
    assert "EHR Integration Update" in n8.body

    history = notifier.get_recipient_notifications("PATIENT", phone)
    assert len(history) == 8


def test_doctor_notifications(db_session):
    notifier = NotificationEngine(db_session)
    doc_id = "DOC-CARDIOLOGY-1"

    n1 = notifier.notify_doctor_new_appointment(doc_id, "Sarah Connor", "2026-09-15 10:00")
    assert n1.recipient_role == "DOCTOR"
    assert "Sarah Connor" in n1.body

    n2 = notifier.notify_doctor_cancellation(doc_id, "Sarah Connor", "2026-09-15 10:00")
    assert "Cancelled" in n2.body

    n3 = notifier.notify_doctor_rescheduled(doc_id, "Sarah Connor", "2026-09-16 11:00")
    assert "Rescheduled" in n3.body

    n4 = notifier.notify_doctor_questionnaire_completed(doc_id, "Sarah Connor")
    assert "Intake Complete" in n4.body

    n5 = notifier.notify_doctor_upcoming_appointment(doc_id, count=5)
    assert "5 appointments" in n5.body

    n6 = notifier.notify_doctor_operational_notice(doc_id, "Clinic open until 6 PM")
    assert "Clinic open" in n6.body

    history = notifier.get_recipient_notifications("DOCTOR", doc_id)
    assert len(history) == 6


def test_hospital_notifications(db_session):
    notifier = NotificationEngine(db_session)
    hosp_id = "HOSP-CITY-GEN"

    n1 = notifier.notify_hospital_approval(hosp_id, "City General Hospital")
    assert n1.recipient_role == "HOSPITAL"
    assert "Approved" in n1.body

    n2 = notifier.notify_hospital_rejection(hosp_id, "Missing license document")
    assert "rejected" in n2.body

    n3 = notifier.notify_hospital_new_appointment(hosp_id, "APPT-909")
    assert "APPT-909" in n3.body

    n4 = notifier.notify_hospital_cancellation(hosp_id, "APPT-909")
    assert "cancelled" in n4.body

    n5 = notifier.notify_hospital_rescheduling(hosp_id, "APPT-909")
    assert "rescheduled" in n5.body

    n6 = notifier.notify_hospital_doctor_status_change(hosp_id, "House", "ACTIVE")
    assert "ACTIVE" in n6.body

    n7 = notifier.notify_hospital_operational_alert(hosp_id, "High server load detected")
    assert "High server load" in n7.body

    n8 = notifier.notify_hospital_integration_failure(hosp_id, "FHIR API Endpoint Timeout")
    assert "Integration Failure" in n8.body

    history = notifier.get_recipient_notifications("HOSPITAL", hosp_id)
    assert len(history) == 8
