"""
Unit tests for Section 1.6: Workflow-Driven Operations, Traceability, and Observability.
"""

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import (
    Base, Hospital, Doctor, Appointment, WorkflowInstance, WorkflowStepLog, WorkflowStatus, EHRIntegrationConfig, EHRAdapterType
)
from app.workflows.engine import WorkflowEngine
from app.agent.actions import ActionExecutor
from app.schemas.actions import CreateAppointmentInput


def test_appointment_reminder_workflow_lifecycle():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Seed hospital & doctor
    hosp = Hospital(id="hosp-w1", name="Mercy Hospital", code="MH")
    doc = Doctor(id="doc-w1", hospital_id="hosp-w1", name="Dr. Bob", specialty="Neurology")
    config = EHRIntegrationConfig(hospital_id="hosp-w1", adapter_type=EHRAdapterType.MOCK_EHR)
    db.add_all([hosp, doc, config])
    db.commit()

    executor = ActionExecutor(db)
    now = datetime.utcnow() + timedelta(hours=2)  # Booking in 2 hours

    # Create Appointment (triggers reminder workflow automatically)
    res = executor.create_appointment(CreateAppointmentInput(
        session_id="sess-wf",
        patient_id="pat-wf",
        hospital_id="hosp-w1",
        doctor_id="doc-w1",
        start_datetime=now,
        patient_name="Bruce Wayne",
        patient_phone="+1-555-0900"
    ))

    assert res.success is True

    # Verify WorkflowInstance created
    wf = db.query(WorkflowInstance).filter(WorkflowInstance.appointment_id == res.appointment_id).first()
    assert wf is not None
    assert wf.workflow_name == "APPOINTMENT_REMINDER_WORKFLOW"
    assert wf.trigger_event == "APPOINTMENT_CONFIRMED"
    assert wf.status == WorkflowStatus.WAITING

    # Force scheduled_for to past to simulate time arrival
    wf.scheduled_for = datetime.utcnow() - timedelta(minutes=1)
    db.commit()

    # Execute due reminder workflows
    executed_count = executor.workflow_engine.execute_due_reminder_workflows()
    assert executed_count == 1

    # Verify updated workflow status
    db.refresh(wf)
    assert wf.status == WorkflowStatus.COMPLETED

    # Verify step logs (Observability & Traceability)
    step_logs = db.query(WorkflowStepLog).filter(WorkflowStepLog.workflow_id == wf.id).all()
    step_names = [log.step_name for log in step_logs]
    assert "CREATE_REMINDER_WORKFLOW" in step_names
    assert "WAIT_UNTIL_REMINDER_WINDOW" in step_names
    assert "SEND_REMINDER" in step_names
    assert "RECORD_DELIVERY" in step_names
    assert "UPDATE_APPOINTMENT_ACTIVITY" in step_names


def test_ehr_failure_reconciliation_workflow():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    hosp = Hospital(id="hosp-w2", name="Metro Health", code="MTH")
    doc = Doctor(id="doc-w2", hospital_id="hosp-w2", name="Dr. Clara", specialty="Pediatrics")
    db.add_all([hosp, doc])
    db.commit()

    wf_engine = WorkflowEngine(db)
    wf = wf_engine.handle_ehr_failure_workflow("appt-999", "EHR SYSTEM TIMEOUT ERROR")

    assert wf.workflow_name == "EHR_FAILURE_RECONCILIATION_WORKFLOW"
    assert wf.trigger_event == "EHR_INTEGRATION_FAILED"
    
    # Check step logs
    step_logs = db.query(WorkflowStepLog).filter(WorkflowStepLog.workflow_id == wf.id).all()
    step_names = [log.step_name for log in step_logs]
    assert "CLASSIFY_FAILURE" in step_names
    assert "RETRY_IF_SAFE" in step_names
