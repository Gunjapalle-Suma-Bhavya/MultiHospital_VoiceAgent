"""
Unit Test Suite for Section 5.28 Background Workflow Engine.

Tests:
1. Appointment Reminder Workflow
2. Questionnaire Reminder Workflow
3. Failed Booking Recovery Workflow
4. Post-Booking 7-Step Sequence Workflow
5. Trigger-based, scheduled, delayed, retry, and history logging
"""

import pytest
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, Doctor, PatientProfile, Appointment, AppointmentStatus, WorkflowInstance, WorkflowStatus, WorkflowStepLog
from app.workflows.engine import BackgroundWorkflowEngine


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def setup_workflow_test_data(db_session):
    hosp = Hospital(name="Mercy Health", code="MERCY", is_active=True)
    db_session.add(hosp)
    db_session.commit()

    doc = Doctor(hospital_id=hosp.id, name="Dr. Gregory House", specialty="Diagnostics", is_active=True)
    db_session.add(doc)
    db_session.commit()

    patient = PatientProfile(phone_number="+15556667777", full_name="Sarah Connor")
    db_session.add(patient)
    db_session.commit()

    appt = Appointment(
        hospital_id=hosp.id,
        doctor_id=doc.id,
        patient_id=patient.id,
        patient_name="Sarah Connor",
        patient_phone="+15556667777",
        start_datetime=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2, hours=10),
        end_datetime=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2, hours=11),
        status=AppointmentStatus.CONFIRMED
    )
    db_session.add(appt)
    db_session.commit()

    return hosp, doc, patient, appt


def test_appointment_reminder_workflow_lifecycle(db_session, setup_workflow_test_data):
    hosp, doc, patient, appt = setup_workflow_test_data
    engine = BackgroundWorkflowEngine(db_session)

    # 1. Start Appointment Reminder Workflow (Delayed 5 mins)
    wf = engine.start_appointment_reminder_workflow(appt.id, delay_minutes=5)
    assert wf.workflow_name == "APPOINTMENT_REMINDER_WORKFLOW"
    assert wf.status == WorkflowStatus.WAITING

    # 2. Simulate Scheduled Time Window Reached
    wf.scheduled_for = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
    db_session.commit()

    executed_count = engine.execute_due_scheduled_workflows()
    assert executed_count >= 1

    db_session.refresh(wf)
    assert wf.status == WorkflowStatus.COMPLETED

    logs = db_session.query(WorkflowStepLog).filter(WorkflowStepLog.workflow_id == wf.id).all()
    assert any(l.step_name == "SEND_NOTIFICATION" for l in logs)


def test_questionnaire_reminder_workflow(db_session, setup_workflow_test_data):
    hosp, doc, patient, appt = setup_workflow_test_data
    engine = BackgroundWorkflowEngine(db_session)

    wf = engine.start_questionnaire_reminder_workflow(appt.id, questionnaire_id="Q-CARD-101")
    assert wf.workflow_name == "QUESTIONNAIRE_REMINDER_WORKFLOW"
    assert wf.status == WorkflowStatus.WAITING

    wf.scheduled_for = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
    db_session.commit()

    executed_count = engine.execute_due_scheduled_workflows()
    assert executed_count >= 1

    db_session.refresh(wf)
    assert wf.status == WorkflowStatus.COMPLETED


def test_failed_booking_recovery_workflow(db_session, setup_workflow_test_data):
    hosp, doc, patient, appt = setup_workflow_test_data
    engine = BackgroundWorkflowEngine(db_session)

    wf = engine.start_failed_booking_recovery_workflow(appt.id, error_reason="Gateway Timeout")
    assert wf.workflow_name == "FAILED_BOOKING_RECOVERY_WORKFLOW"
    assert wf.status in [WorkflowStatus.COMPLETED, WorkflowStatus.ESCALATED]


def test_post_booking_multi_step_workflow(db_session, setup_workflow_test_data):
    hosp, doc, patient, appt = setup_workflow_test_data
    engine = BackgroundWorkflowEngine(db_session)

    wf = engine.start_post_booking_workflow(appt.id)
    assert wf.workflow_name == "POST_BOOKING_WORKFLOW"
    assert wf.status == WorkflowStatus.COMPLETED

    logs = db_session.query(WorkflowStepLog).filter(WorkflowStepLog.workflow_id == wf.id).all()
    step_names = [l.step_name for l in logs]
    
    assert "UPDATE_PATIENT" in step_names
    assert "SYNCHRONIZE_EHR" in step_names
    assert "NOTIFY_DOCTOR" in step_names
    assert "CREATE_QUESTIONNAIRE_TASK" in step_names
    assert "SCHEDULE_REMINDER" in step_names
    assert "UPDATE_ANALYTICS" in step_names
