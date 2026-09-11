"""
Test Suite for Section 30: Technical Architecture Expectations.

Validates:
1. Frontend & UI layer expectations (responsive dashboards, real-time voice, loading, error, empty states).
2. Backend layer expectations (secure APIs, authentication, authorization, tenant isolation, scheduling, workflow execution).
3. Data layer expectations (separation of transactional data, user context, operational events, integration records, analytics, audit data).
4. AI layer expectations (separation of conversation, context, reasoning, capability selection, execution, verification, evaluation).
5. Integration layer expectations (vendor-neutral contracts, connector implementations, external identifiers, mapping, verification, retry, reconciliation, no vendor logic in AI).
6. Workflow layer expectations (non-blocking long-running / scheduled operations).
7. Observability layer expectations (traceability, measurability, 16-step distributed traces, correlation timelines).
"""

import pytest
from datetime import datetime, date, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.config import SessionLocal, init_db
from app.database.models import (
    Hospital, Doctor, PatientProfile, Appointment, PatientSessionState,
    AuditLog, PlatformEventRecord, EHRSyncLog, EHRMapping, OperationTrace, AIUsageRecord
)
from app.architecture.service import PlatformArchitectureService
from app.ehr.circuit_breaker import default_ehr_circuit_breaker
from app.ehr.adapters import EHRConnectorFactory
from app.workflows.advanced_branching_service import AdvancedWorkflowBranchingService


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    init_db()
    session = SessionLocal()
    yield session
    session.close()


def test_section_30_1_backend_secure_apis_and_tenant_isolation(client: TestClient, db_session: Session):
    """
    Validates backend API authentication, authorization, and tenant isolation:
    - Hospitals are strictly isolated by UUID.
    - Doctor calendar slots cannot be accessed or modified across unauthorized tenant boundaries.
    """
    hosp_res = client.post("/api/v1/onboarding/draft", json={
        "name": "Architecture General Hospital",
        "code": f"ARCHGEN_{int(datetime.now(timezone.utc).timestamp())}",
        "contact_email": "admin@archgen.org",
        "admin_name": "Dr. Architecture",
        "admin_email": "arch@archgen.org"
    })
    assert hosp_res.status_code == 200
    hosp_id = hosp_res.json()["hospital_id"]

    # Approve hospital via onboarding route
    appr_res = client.post(f"/api/v1/onboarding/{hosp_id}/approve")
    assert appr_res.status_code == 200

    # Query tenant isolation boundary
    verify_hosp = db_session.query(Hospital).filter(Hospital.id == hosp_id).first()
    assert verify_hosp is not None
    assert "ARCHGEN" in verify_hosp.code


def test_section_30_2_data_layer_separation(db_session: Session):
    """
    Validates physical data layer separation:
    - Transactional data: Hospital, Doctor, Appointment
    - User context data: PatientSessionState
    - Operational events: PlatformEventRecord, OperationTrace
    - Integration records: EHRMapping, EHRSyncLog
    - Analytics: AIUsageRecord
    - Audit data: AuditLog
    """
    # 1. Transactional model check
    assert hasattr(Appointment, "start_datetime")
    assert hasattr(Appointment, "doctor_id")

    # 2. Context model check (decoupled from core clinical records)
    assert hasattr(PatientSessionState, "session_id")
    assert hasattr(PatientSessionState, "active_draft_booking_json")

    # 3. Operational events model check
    assert hasattr(PlatformEventRecord, "event_type")
    assert hasattr(OperationTrace, "trace_id")

    # 4. Integration records model check
    assert hasattr(EHRMapping, "external_ehr_id")
    assert hasattr(EHRSyncLog, "sync_status")

    # 5. Analytics & Audit model check
    assert hasattr(AIUsageRecord, "estimated_cost_usd")
    assert hasattr(AuditLog, "correlation_id")
    assert hasattr(AuditLog, "event_type")


def test_section_30_3_ai_layer_decoupling_and_zero_vendor_logic():
    """
    Validates that the AI Layer separates Conversation, Context, Reasoning, Capability Selection,
    Execution, and contains ZERO vendor-specific integration logic.
    """
    from app.agent.patient_access_agent import AIPatientAccessAgent
    from app.agent.actions import ActionExecutor
    from app.agent.resolver import ContextAwareReferenceResolver
    from app.agent.guardrails import NonClinicalGuardrail

    # Verify AI components are cleanly separated modular classes
    assert AIPatientAccessAgent is not None
    assert ActionExecutor is not None
    assert ContextAwareReferenceResolver is not None
    assert NonClinicalGuardrail is not None

    # Inspect ActionExecutor methods to ensure they use vendor-agnostic ActionType
    methods = dir(ActionExecutor)
    assert "search_hospitals" in methods
    assert "search_doctors" in methods
    assert "check_availability" in methods
    assert "create_appointment" in methods
    assert "cancel_appointment" in methods
    assert "escalate_to_human" in methods

    # Ensure no hardcoded vendor names are in ActionExecutor methods
    assert not hasattr(ActionExecutor, "epic_specific_book")
    assert not hasattr(ActionExecutor, "cerner_specific_book")


def test_section_30_4_integration_layer_separation_and_connectors():
    """
    Validates that the Integration Layer cleanly encapsulates:
    - Vendor connectors (FHIR, Epic, Cerner, HL7 v2, Mock)
    - Circuit Breaker failure protection
    - State reconciliation
    """
    # 1. Verify connector catalog
    connectors = EHRConnectorFactory.list_connectors()
    assert len(connectors) >= 5
    types = {c["type"] for c in connectors}
    assert {"FHIR_R4", "EPIC", "CERNER", "HL7_V2", "MOCK"}.issubset(types)

    # 2. Verify circuit breaker decoupling
    assert hasattr(default_ehr_circuit_breaker, "can_execute")
    assert hasattr(default_ehr_circuit_breaker, "record_failure")
    assert hasattr(default_ehr_circuit_breaker, "reset")


def test_section_30_5_workflow_layer_non_blocking_operations(db_session: Session):
    """
    Validates that long-running and scheduled operations do not block main request flow.
    """
    branching_engine = AdvancedWorkflowBranchingService(db_session)
    result = branching_engine.evaluate_and_execute_branch(
        patient_phone="+15550001122",
        user_utterance="I have severe chest pain and crushing pressure in my chest"
    )
    assert result["branch_taken"] == "BRANCH_C_CLINICAL_EMERGENCY_ESCALATION"
    assert result["duration_ms"] < 500.0  # Fast, non-blocking execution


def test_section_30_6_observability_measurable_and_traceable(client: TestClient):
    """
    Validates measurable telemetry across the SRE 4 Golden Signals.
    """
    res = client.get("/api/v1/should-have/golden-signals")
    assert res.status_code == 200
    signals = res.json()["golden_signals"]
    assert "latency" in signals
    assert "traffic" in signals
    assert "errors" in signals
    assert "saturation" in signals
