"""
Test Suite for Sections 5.34 Operational Observability & 5.35 Correlation & Traceability.
Verifies 16-step canonical operation lifecycle tracing, latency profiling, failure diagnostics,
retry & recovery tracking, cross-component correlation aggregation, and REST API endpoints.
"""

import json
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import (
    Base, OperationTrace, OperationTraceStep, AITelemetryLog,
    EHRSyncLog, WorkflowInstance, AuditLog, NotificationRecord, PlatformEventRecord, Hospital, Doctor, PatientProfile, Appointment
)
from app.observability import TraceManager, ObservabilityService, CANONICAL_LIFECYCLE_STEPS
from app.main import app
from sqlalchemy.pool import StaticPool
from app.database.config import get_db

# In-Memory SQLite Setup with StaticPool for Shared In-Memory Connection
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_complete_16_step_operation_trace(setup_db):
    """
    Tests end-to-end recording of all 16 canonical operation lifecycle steps (Section 5.34).
    """
    db = setup_db

    # 1. Start Trace
    trace = TraceManager.start_trace(
        db_session=db,
        session_id="SESS-16-STEP-TEST",
        hospital_id="HOSP-101",
        operation_name="FULL_PATIENT_INTAKE_CYCLE"
    )
    assert trace.trace_id.startswith("TRC-")
    assert trace.correlation_id.startswith("CORR-")
    assert trace.status == "IN_PROGRESS"

    # Step #1 is auto-added: CALL_STARTED
    # Add remaining 15 steps
    remaining_steps = CANONICAL_LIFECYCLE_STEPS[1:]
    component_mapping = {
        "PATIENT_IDENTIFIED": "CONVERSATION",
        "INTENT_DETECTED": "AI_DECISION",
        "CONTEXT_RETRIEVED": "AI_DECISION",
        "SEARCH_DOCTORS": "CAPABILITY_CALL",
        "CHECK_AVAILABILITY": "CAPABILITY_CALL",
        "PATIENT_SELECTED_SLOT": "CONVERSATION",
        "BOOKING_STARTED": "SCHEDULING",
        "EHR_INTEGRATION_STARTED": "EHR_INTEGRATION",
        "EXTERNAL_RECORD_CREATED": "EHR_INTEGRATION",
        "EHR_SYNC_VERIFIED": "VERIFICATION",
        "BOOKING_VERIFIED": "VERIFICATION",
        "QUESTIONNAIRE_STARTED": "WORKFLOW",
        "QUESTIONNAIRE_COMPLETED": "WORKFLOW",
        "NOTIFICATION_SENT": "NOTIFICATION",
        "CALL_COMPLETED": "CONVERSATION"
    }

    for step_name in remaining_steps:
        comp = component_mapping.get(step_name, "CAPABILITY_CALL")
        TraceManager.record_step(
            db_session=db,
            trace_id=trace.trace_id,
            step_name=step_name,
            component_type=comp,
            latency_ms=25.0,
            status="SUCCESS"
        )

    # Finalize Trace
    final_trace = TraceManager.finalize_trace(db_session=db, trace_id=trace.trace_id, status="COMPLETED")
    assert final_trace.status == "COMPLETED"
    assert final_trace.total_latency_ms >= 385.0  # 10ms initial + 15 * 25ms

    # Query details
    details = ObservabilityService.get_trace_details(db, trace.trace_id)
    assert details["step_count"] == 16
    recorded_names = [s["step_name"] for s in details["steps"]]
    assert recorded_names == CANONICAL_LIFECYCLE_STEPS


def test_latency_and_failure_diagnostics(setup_db):
    """
    Tests failure location identification, external system attribution, retry tracking,
    recovery, and reconciliation verification (Section 5.34).
    """
    db = setup_db

    trace = TraceManager.start_trace(
        db_session=db,
        session_id="SESS-FAILURE-TEST",
        hospital_id="HOSP-DIAG-01"
    )

    # Record normal step
    TraceManager.record_step(
        db_session=db,
        trace_id=trace.trace_id,
        step_name="PATIENT_IDENTIFIED",
        component_type="CONVERSATION",
        latency_ms=12.0
    )

    # Record failed EHR step with retries
    TraceManager.record_step(
        db_session=db,
        trace_id=trace.trace_id,
        step_name="EHR_INTEGRATION_STARTED",
        component_type="EHR_INTEGRATION",
        latency_ms=1500.0,
        status="FAILED",
        error_message="FHIR Endpoint Connection Timeout (504)",
        external_system_name="EPIC_MYCHART",
        retry_count=3
    )

    # Finalize with recovery & reconciliation
    final_trace = TraceManager.finalize_trace(
        db_session=db,
        trace_id=trace.trace_id,
        status="COMPLETED",
        recovery_succeeded=True,
        reconciliation_occurred=True,
        escalated_to_human=False
    )

    details = ObservabilityService.get_trace_details(db, trace.trace_id)
    assert details["diagnostics"]["failed_action"] == "EHR_INTEGRATION_STARTED"
    assert details["diagnostics"]["failure_location"] == "EHR_INTEGRATION"
    assert details["diagnostics"]["failed_external_system"] == "EPIC_MYCHART"
    assert details["diagnostics"]["retries_triggered"] == 3
    assert details["diagnostics"]["recovery_succeeded"] is True
    assert details["diagnostics"]["reconciliation_occurred"] is True


def test_cross_component_correlation_traceability(setup_db):
    """
    Tests single unified correlation_id linking across 10 platform component layers (Section 5.35).
    """
    db = setup_db
    corr_id = "CORR-UNIFIED-9999"
    sess_id = "SESS-CORR-01"
    hosp_id = "HOSP-CORR-01"
    appt_id = "APPT-CORR-01"

    # Seed Hospital & Doctor & Patient & Appointment for FK sanity
    hosp = Hospital(id=hosp_id, name="General Hospital", code="GEN-CORR")
    db.add(hosp)
    doc = Doctor(id="DOC-CORR", hospital_id=hosp_id, name="Dr. House", specialty="Internal Medicine")
    db.add(doc)
    pat = PatientProfile(id="PAT-CORR", full_name="John Doe", phone_number="+15551112222")
    db.add(pat)
    db.commit()

    appt = Appointment(
        id=appt_id,
        hospital_id=hosp_id,
        doctor_id="DOC-CORR",
        patient_id="PAT-CORR",
        patient_name="John Doe",
        patient_phone="+15551112222",
        start_datetime=datetime.now(timezone.utc).replace(tzinfo=None),
        end_datetime=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db.add(appt)
    db.commit()

    # 1. Operation Trace
    trace = TraceManager.start_trace(
        db_session=db,
        session_id=sess_id,
        hospital_id=hosp_id,
        appointment_id=appt_id,
        correlation_id=corr_id
    )

    # 2. AI Decision Telemetry
    ai_telemetry = AITelemetryLog(
        session_id=sess_id,
        hospital_id=hosp_id,
        ai_attempt_summary="Detected doctor availability search intent",
        capability_invoked="SEARCH_DOCTORS",
        latency_ms=120.0
    )
    db.add(ai_telemetry)

    # 3. EHR Integration Sync
    ehr_sync = EHRSyncLog(
        appointment_id=appt_id,
        hospital_id=hosp_id,
        action_type="CREATE_APPOINTMENT",
        sync_status="VERIFIED",
        external_reference_id="EPIC-APPT-77"
    )
    db.add(ehr_sync)

    # 4. Workflow
    wf = WorkflowInstance(
        appointment_id=appt_id,
        workflow_name="POST_BOOKING_LIFECYCLE",
        trigger_event="APPOINTMENT_BOOKED",
        status="COMPLETED"
    )
    db.add(wf)

    # 5. Audit Log
    audit = AuditLog(
        session_id=sess_id,
        hospital_id=hosp_id,
        correlation_id=corr_id,
        event_type="BOOKING_VERIFIED",
        payload_json=json.dumps({"status": "SUCCESS"})
    )
    db.add(audit)

    # 6. Notification Record
    notif = NotificationRecord(
        recipient_role="PATIENT",
        recipient_id="PAT-CORR",
        notification_type="APPOINTMENT_CONFIRMATION",
        body="Your appointment is confirmed.",
        metadata_json=json.dumps({"correlation_id": corr_id, "session_id": sess_id})
    )
    db.add(notif)

    # 7. System Event
    evt = PlatformEventRecord(
        event_type="APPOINTMENT_BOOKED",
        source="VOICE_AGENT",
        aggregate_id=corr_id
    )
    db.add(evt)
    db.commit()

    # Query Correlation Timeline
    timeline = ObservabilityService.get_correlation_timeline(db, corr_id)

    assert timeline["correlation_id"] == corr_id
    assert sess_id in timeline["component_layers"]["conversation"]
    assert appt_id in timeline["component_layers"]["scheduling_operation"]
    assert len(timeline["component_layers"]["ai_decision"]) >= 1
    assert len(timeline["component_layers"]["ehr_integration_operation"]) >= 1
    assert len(timeline["component_layers"]["workflow"]) >= 1
    assert len(timeline["component_layers"]["audit_event"]) >= 1
    assert len(timeline["component_layers"]["notification"]) >= 1
    assert len(timeline["system_events"]) >= 1


def test_observability_api_endpoints(client, setup_db):
    """
    Tests REST API endpoints for operational observability & correlation analytics.
    """
    # 1. Start Trace
    res_start = client.post("/api/v1/observability/traces/start", json={
        "session_id": "SESS-API-TEST",
        "operation_name": "API_LIFECYCLE_TEST"
    })
    assert res_start.status_code == 200
    data_start = res_start.json()
    trace_id = data_start["trace_id"]
    corr_id = data_start["correlation_id"]

    # 2. Record Step
    res_step = client.post(f"/api/v1/observability/traces/{trace_id}/step", json={
        "step_name": "CHECK_AVAILABILITY",
        "component_type": "CAPABILITY_CALL",
        "latency_ms": 34.5,
        "status": "SUCCESS"
    })
    assert res_step.status_code == 200
    assert res_step.json()["step_number"] == 2

    # 3. Finalize Trace
    res_fin = client.post(f"/api/v1/observability/traces/{trace_id}/finalize", json={
        "status": "COMPLETED",
        "recovery_succeeded": True
    })
    assert res_fin.status_code == 200
    assert res_fin.json()["final_status"] == "COMPLETED"

    # 4. Get Trace Details
    res_det = client.get(f"/api/v1/observability/traces/{trace_id}")
    assert res_det.status_code == 200
    assert res_det.json()["trace_id"] == trace_id

    # 5. Get Correlation Timeline
    res_corr = client.get(f"/api/v1/observability/correlation/{corr_id}")
    assert res_corr.status_code == 200
    assert res_corr.json()["correlation_id"] == corr_id

    # 6. Get Analytics
    res_ana = client.get("/api/v1/observability/analytics")
    assert res_ana.status_code == 200
    ana_data = res_ana.json()
    assert ana_data["total_traces"] >= 1
    assert "avg_latency_ms" in ana_data
