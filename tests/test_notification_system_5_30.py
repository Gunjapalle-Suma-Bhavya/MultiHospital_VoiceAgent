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

    n9 = notifier.notify_hospital_workflow_failure(hosp_id, "PATIENT_INTAKE_ROUTING", "Execution timed out")
    assert "Workflow Failure Alert" in n9.body
    assert n9.notification_type == "WORKFLOW_FAILURE"

    history = notifier.get_recipient_notifications("HOSPITAL", hosp_id)
    assert len(history) == 9


def test_section_14_notifications_complete_coverage(db_session):
    """
    Verifies all notification types explicitly itemized in Section 14:
    Hospital:
    - Hospital approved, Hospital rejected, New appointment, Cancellation, Rescheduling,
      Doctor status change, Workflow failure, Operational alert, Healthcare-system integration failure
    Doctor:
    - New appointment, Appointment cancelled, Appointment rescheduled, Questionnaire completed,
      Upcoming appointment, Workflow notification
    Patient:
    - Appointment confirmation, Appointment reminder, Rescheduling confirmation,
      Cancellation confirmation, Questionnaire reminder, Questionnaire completion,
      Important appointment updates
    """
    notifier = NotificationEngine(db_session)

    # 1. Hospital (9 notification types)
    hosp_id = "HOSP-SEC-14"
    r_h1 = notifier.notify_hospital_approval(hosp_id, "Metro Health")
    assert r_h1.notification_type == "HOSPITAL_APPROVAL"
    r_h2 = notifier.notify_hospital_rejection(hosp_id, "Invalid tax ID")
    assert r_h2.notification_type == "HOSPITAL_REJECTION"
    r_h3 = notifier.notify_hospital_new_appointment(hosp_id, "APPT-1401")
    assert r_h3.notification_type == "NEW_APPOINTMENT"
    r_h4 = notifier.notify_hospital_cancellation(hosp_id, "APPT-1401")
    assert r_h4.notification_type == "CANCELLATION"
    r_h5 = notifier.notify_hospital_rescheduling(hosp_id, "APPT-1401")
    assert r_h5.notification_type == "RESCHEDULING"
    r_h6 = notifier.notify_hospital_doctor_status_change(hosp_id, "Dr. Rao", "ON_LEAVE")
    assert r_h6.notification_type == "DOCTOR_STATUS_CHANGE"
    r_h7 = notifier.notify_hospital_workflow_failure(hosp_id, "APPOINTMENT_REMINDER", "Timeout")
    assert r_h7.notification_type == "WORKFLOW_FAILURE"
    r_h8 = notifier.notify_hospital_operational_alert(hosp_id, "High booking volume")
    assert r_h8.notification_type == "OPERATIONAL_ALERT"
    r_h9 = notifier.notify_hospital_integration_failure(hosp_id, "Epic FHIR 503")
    assert r_h9.notification_type == "INTEGRATION_FAILURE"

    # 2. Doctor (6 notification types)
    doc_id = "DOC-SEC-14"
    r_d1 = notifier.notify_doctor_new_appointment(doc_id, "Alex Miller", "Thursday 3:00 PM")
    assert r_d1.notification_type == "NEW_APPOINTMENT"
    r_d2 = notifier.notify_doctor_cancellation(doc_id, "Alex Miller", "Thursday 3:00 PM")
    assert r_d2.notification_type == "APPOINTMENT_CANCELLATION"
    r_d3 = notifier.notify_doctor_rescheduled(doc_id, "Alex Miller", "Friday 11:00 AM")
    assert r_d3.notification_type == "APPOINTMENT_RESCHEDULED"
    r_d4 = notifier.notify_doctor_questionnaire_completed(doc_id, "Alex Miller")
    assert r_d4.notification_type == "QUESTIONNAIRE_COMPLETED"
    r_d5 = notifier.notify_doctor_upcoming_appointment(doc_id, 4)
    assert r_d5.notification_type == "UPCOMING_APPOINTMENT"
    r_d6 = notifier.notify_doctor_workflow_notification(doc_id, "INTAKE_ROUTING", "Briefing prepared")
    assert r_d6.notification_type == "WORKFLOW_NOTIFICATION"

    # 3. Patient (7 notification types)
    pat_phone = "+1555998877"
    r_p1 = notifier.notify_patient_appointment_confirmation(pat_phone, "Dr. Sharma", "City Hospital", "Thursday 3:00 PM")
    assert r_p1.notification_type == "APPOINTMENT_CONFIRMATION"
    r_p2 = notifier.notify_patient_appointment_reminder(pat_phone, "Dr. Sharma", "City Hospital", "Thursday 3:00 PM")
    assert r_p2.notification_type == "APPOINTMENT_REMINDER"
    r_p3 = notifier.notify_patient_reschedule(pat_phone, "Dr. Sharma", "City Hospital", "Friday 11:00 AM")
    assert r_p3.notification_type == "RESCHEDULING_CONFIRMATION"
    r_p4 = notifier.notify_patient_cancellation(pat_phone, "Dr. Sharma", "City Hospital", "Thursday 3:00 PM")
    assert r_p4.notification_type == "CANCELLATION_CONFIRMATION"
    r_p5 = notifier.notify_patient_questionnaire_reminder(pat_phone, "Dr. Sharma")
    assert r_p5.notification_type == "QUESTIONNAIRE_REMINDER"
    r_p6 = notifier.notify_patient_questionnaire_completion(pat_phone, "Dr. Sharma")
    assert r_p6.notification_type == "QUESTIONNAIRE_COMPLETED"
    r_p7 = notifier.notify_patient_important_appointment_update(pat_phone, "Dr. Sharma", "Clinic room moved to Suite 402.")
    assert r_p7.notification_type == "IMPORTANT_APPOINTMENT_UPDATE"
    assert "Suite 402" in r_p7.body
