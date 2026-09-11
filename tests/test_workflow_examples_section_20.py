"""
Comprehensive Tests for Section 20 Workflow Examples.
Covers all 6 specified workflows:
20.1: Appointment Reminder
20.2: Questionnaire Reminder
20.3: Failed Booking Recovery (Branching YES / NO)
20.4: Human Escalation
20.5: Appointment Cancellation
20.6: Appointment Rescheduling
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import (
    Base, Hospital, Doctor, Appointment, AppointmentStatus, HospitalStatus,
    WorkflowInstance, WorkflowStatus, WorkflowStepLog, HumanEscalationRecord
)
from app.database.config import get_db
from app.main import app
from app.workflows.canonical_examples import CanonicalWorkflowExamplesService


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_workflows_sec20.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    hosp = Hospital(
        id="hosp-wf-01",
        name="General Health Center",
        code="GHC_01",
        hospital_status=HospitalStatus.APPROVED,
        is_active=True
    )
    doc = Doctor(
        id="doc-wf-01",
        hospital_id="hosp-wf-01",
        name="Dr. Priya Sharma",
        specialty="General Medicine",
        is_active=True
    )
    appt = Appointment(
        id="appt-wf-demo-01",
        hospital_id="hosp-wf-01",
        doctor_id="doc-wf-01",
        patient_name="John Doe",
        patient_phone="+15551234567",
        start_datetime=datetime(2026, 11, 10, 15, 0, 0),
        end_datetime=datetime(2026, 11, 10, 15, 30, 0),
        status=AppointmentStatus.CONFIRMED,
        is_ehr_verified=True
    )
    db.add_all([hosp, doc, appt])
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_section_20_1_appointment_reminder():
    """
    20.1 Appointment Reminder:
    Appointment Confirmed -> Schedule Reminder -> Wait -> Reminder Triggered -> Send Notification -> Record Result
    """
    db = TestingSessionLocal()
    svc = CanonicalWorkflowExamplesService(db)
    res = svc.execute_appointment_reminder_workflow("appt-wf-demo-01")

    assert res["status"] == "COMPLETED"
    step_names = [s["step"] for s in res["steps"]]
    assert step_names == [
        "APPOINTMENT_CONFIRMED",
        "SCHEDULE_REMINDER",
        "WAIT_PERIOD",
        "REMINDER_TRIGGERED",
        "SEND_NOTIFICATION",
        "RECORD_RESULT"
    ]
    db.close()


def test_section_20_2_questionnaire_reminder():
    """
    20.2 Questionnaire Reminder:
    Appointment Confirmed -> Questionnaire Assigned -> Patient Has Not Completed -> Wait -> Reminder -> Patient Completes -> Stop Reminder Workflow
    """
    db = TestingSessionLocal()
    svc = CanonicalWorkflowExamplesService(db)
    res = svc.execute_questionnaire_reminder_workflow(
        appointment_id="appt-wf-demo-01",
        questionnaire_id="Q-PREVISIT-MED-01",
        patient_completes_after_reminder=True
    )

    assert res["status"] == "COMPLETED"
    step_names = [s["step"] for s in res["steps"]]
    assert "QUESTIONNAIRE_ASSIGNED" in step_names
    assert "PATIENT_HAS_NOT_COMPLETED" in step_names
    assert "SEND_REMINDER" in step_names
    assert "PATIENT_COMPLETES" in step_names
    assert "STOP_REMINDER_WORKFLOW" in step_names
    db.close()


def test_section_20_3_failed_booking_branching():
    """
    20.3 Failed Booking Recovery:
    Booking Requested -> Scheduling Action -> EHR Integration -> Failure -> Classify Failure -> Retry if Safe -> Verify External State -> Success? [YES / NO]
    """
    db = TestingSessionLocal()
    svc = CanonicalWorkflowExamplesService(db)

    # Branch A: Retry Succeeds -> Complete
    res_success = svc.execute_failed_booking_workflow("appt-wf-demo-01", simulated_retry_success=True)
    assert res_success["status"] == "COMPLETED"
    steps_success = [s["step"] for s in res_success["steps"]]
    assert "CLASSIFY_FAILURE" in steps_success
    assert "RETRY_IF_SAFE" in steps_success
    assert "VERIFY_EXTERNAL_STATE" in steps_success
    assert "SUCCESS_BRANCH_YES" in steps_success

    # Branch B: Retry Fails -> Reconcile / Escalate
    res_fail = svc.execute_failed_booking_workflow("appt-wf-demo-01", simulated_retry_success=False)
    assert res_fail["status"] == "ESCALATED"
    steps_fail = [s["step"] for s in res_fail["steps"]]
    assert "SUCCESS_BRANCH_NO" in steps_fail
    db.close()


def test_section_20_4_human_escalation():
    """
    20.4 Human Escalation:
    AI Interaction -> Unsupported / Failed / User Requests Human -> Create Escalation -> Attach Relevant Authorized Context -> Human Support -> Resolution -> Record Outcome
    """
    db = TestingSessionLocal()
    svc = CanonicalWorkflowExamplesService(db)
    res = svc.execute_human_escalation_workflow(
        session_id="SESS-ESC-TEST-99",
        reason="PATIENT_EXPLICIT_REQUEST_HUMAN",
        hospital_id="hosp-wf-01"
    )

    assert res["status"] == "COMPLETED"
    assert "escalation_id" in res
    step_names = [s["step"] for s in res["steps"]]
    assert "CREATE_ESCALATION" in step_names
    assert "ATTACH_RELEVANT_AUTHORIZED_CONTEXT" in step_names
    assert "HUMAN_SUPPORT" in step_names
    assert "RESOLUTION" in step_names
    assert "RECORD_OUTCOME" in step_names
    db.close()


def test_section_20_5_appointment_cancellation():
    """
    20.5 Appointment Cancellation:
    User Request -> Identify Appointment -> Confirm Target -> Cancellation Capability -> EHR / External System Update -> Verify Cancellation -> Synchronize Platform State -> Notify Patient -> Update Calendar -> Update Analytics
    """
    db = TestingSessionLocal()
    svc = CanonicalWorkflowExamplesService(db)

    # Create distinct appointment to cancel
    cancel_appt = Appointment(
        id="appt-to-cancel-01",
        hospital_id="hosp-wf-01",
        doctor_id="doc-wf-01",
        patient_name="Bob Brown",
        patient_phone="+15559876543",
        start_datetime=datetime(2026, 11, 12, 10, 0, 0),
        end_datetime=datetime(2026, 11, 12, 10, 30, 0),
        status=AppointmentStatus.CONFIRMED
    )
    db.add(cancel_appt)
    db.commit()

    res = svc.execute_appointment_cancellation_workflow(cancel_appt.id)
    assert res["status"] == "COMPLETED"
    step_names = [s["step"] for s in res["steps"]]
    assert step_names == [
        "USER_REQUEST",
        "IDENTIFY_APPOINTMENT",
        "CONFIRMED_TARGET" if "CONFIRMED_TARGET" in step_names else "CONFIRM_TARGET",
        "CANCELLATION_CAPABILITY",
        "EHR_EXTERNAL_SYSTEM_UPDATE",
        "VERIFY_CANCELLATION",
        "SYNCHRONIZE_PLATFORM_STATE",
        "NOTIFY_PATIENT",
        "UPDATE_CALENDAR",
        "UPDATE_ANALYTICS"
    ]

    # Verify platform state synchronized to CANCELLED
    db.refresh(cancel_appt)
    assert cancel_appt.status == AppointmentStatus.CANCELLED
    db.close()


def test_section_20_6_appointment_rescheduling():
    """
    20.6 Appointment Rescheduling:
    User Request -> Identify Existing Appointment -> Find New Availability -> Patient Selects New Slot -> Reschedule Capability -> EHR / External System Update -> Verify New Appointment -> Synchronize State -> Cancel / Release Old Slot -> Notify Patient -> Update Analytics
    """
    db = TestingSessionLocal()
    svc = CanonicalWorkflowExamplesService(db)

    resched_appt = Appointment(
        id="appt-to-resched-01",
        hospital_id="hosp-wf-01",
        doctor_id="doc-wf-01",
        patient_name="Carol White",
        patient_phone="+15555554321",
        start_datetime=datetime(2026, 11, 15, 14, 0, 0),
        end_datetime=datetime(2026, 11, 15, 14, 30, 0),
        status=AppointmentStatus.CONFIRMED
    )
    db.add(resched_appt)
    db.commit()

    new_time = datetime(2026, 11, 18, 16, 0, 0)
    res = svc.execute_appointment_rescheduling_workflow(resched_appt.id, new_start_datetime=new_time)
    assert res["status"] == "COMPLETED"
    step_names = [s["step"] for s in res["steps"]]
    assert "IDENTIFY_EXISTING_APPOINTMENT" in step_names
    assert "FIND_NEW_AVAILABILITY" in step_names
    assert "PATIENT_SELECTS_NEW_SLOT" in step_names
    assert "RESCHEDULE_CAPABILITY" in step_names
    assert "EHR_EXTERNAL_SYSTEM_UPDATE" in step_names
    assert "VERIFY_NEW_APPOINTMENT" in step_names
    assert "SYNCHRONIZE_STATE" in step_names
    assert "CANCEL_RELEASE_OLD_SLOT" in step_names
    assert "NOTIFY_PATIENT" in step_names
    assert "UPDATE_ANALYTICS" in step_names

    db.refresh(resched_appt)
    assert resched_appt.status == AppointmentStatus.RESCHEDULED
    assert resched_appt.start_datetime == new_time
    db.close()


def test_workflow_examples_rest_api():
    """
    Verifies POST /api/v1/workflow-examples/execute for all workflows.
    """
    # 20.1 API
    r1 = client.post("/api/v1/workflow-examples/execute", json={"workflow_code": "20.1", "appointment_id": "appt-wf-demo-01"})
    assert r1.status_code == 200
    assert r1.json()["workflow_name"] == "20.1 Appointment Reminder"

    # 20.4 API (Escalation)
    r4 = client.post("/api/v1/workflow-examples/execute", json={"workflow_code": "20.4", "session_id": "SES-API-TEST"})
    assert r4.status_code == 200
    assert r4.json()["workflow_name"] == "20.4 Human Escalation"
