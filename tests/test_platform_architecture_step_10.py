"""
Test Suite for Step 10: Complete Platform Architecture.
Validates the canonical 9-layer architectural topology, multi-layer health audit,
and synthetic distributed transaction tracing engine across all 9 layers.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.config import SessionLocal, init_db
from app.architecture import (
    ArchitectureLayerEnum,
    SyntheticTraceRequest,
)
from app.architecture.service import PlatformArchitectureService


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


def test_architecture_topology_structure():
    """Validates that the architecture topology contains all 9 canonical layers and subcomponents."""
    topology = PlatformArchitectureService.get_complete_topology()

    assert topology.total_layers == 9
    assert len(topology.layers) == 9

    expected_layer_ids = [
        ArchitectureLayerEnum.PATIENT_ENTRY,
        ArchitectureLayerEnum.REALTIME_VOICE,
        ArchitectureLayerEnum.CONVERSATIONAL_AI,
        ArchitectureLayerEnum.EHR_INTEGRATION,
        ArchitectureLayerEnum.WORKFLOW_EVENT,
        ArchitectureLayerEnum.CORE_PLATFORM,
        ArchitectureLayerEnum.DATA_LAYER,
        ArchitectureLayerEnum.OBSERVABILITY_AUDIT,
        ArchitectureLayerEnum.ADMIN_OPERATIONS_DASHBOARD,
    ]

    actual_layer_ids = [l.layer_id for l in topology.layers]
    assert actual_layer_ids == expected_layer_ids

    # Verify Layer 1: Patient Entry
    l1 = topology.layers[0]
    comp_names_l1 = [c.name for c in l1.components]
    assert "web_voice" in comp_names_l1
    assert "telephony" in comp_names_l1

    # Verify Layer 2: Real-Time Voice
    l2 = topology.layers[1]
    comp_names_l2 = [c.name for c in l2.components]
    assert "speech_to_text" in comp_names_l2
    assert "text_to_speech" in comp_names_l2
    assert "voice_activity_detector" in comp_names_l2

    # Verify Layer 3: Conversational AI (Context, Capability, Guardrails)
    l3 = topology.layers[2]
    comp_names_l3 = [c.name for c in l3.components]
    assert "user_context_engine" in comp_names_l3
    assert "capability_search_engine" in comp_names_l3
    assert "capability_schedule_engine" in comp_names_l3
    assert "capability_ehr_invoker" in comp_names_l3
    assert "capability_escalation_layer" in comp_names_l3
    assert "safety_guardrails_layer" in comp_names_l3

    # Verify Layer 4: EHR Integration (Connectors A/B/C, Verification, State Sync)
    l4 = topology.layers[3]
    comp_names_l4 = [c.name for c in l4.components]
    assert "connector_a_fhir" in comp_names_l4
    assert "connector_b_epic" in comp_names_l4
    assert "connector_c_cerner" in comp_names_l4
    assert "ehr_verification_engine" in comp_names_l4
    assert "ehr_state_sync_engine" in comp_names_l4

    # Verify Layer 5: Workflow / Event
    l5 = topology.layers[4]
    comp_names_l5 = [c.name for c in l5.components]
    assert "background_workflows" in comp_names_l5
    assert "scheduled_tasks" in comp_names_l5
    assert "notifications_system" in comp_names_l5

    # Verify Layer 6: Core Platform
    l6 = topology.layers[5]
    comp_names_l6 = [c.name for c in l6.components]
    assert "hospitals_management" in comp_names_l6
    assert "doctors_management" in comp_names_l6
    assert "calendars_management" in comp_names_l6
    assert "patients_management" in comp_names_l6
    assert "appointments_management" in comp_names_l6

    # Verify Layer 7: Data Layer
    l7 = topology.layers[6]
    comp_names_l7 = [c.name for c in l7.components]
    assert "operational_data" in comp_names_l7
    assert "user_context_data" in comp_names_l7
    assert "analytics_data" in comp_names_l7

    # Verify Layer 8: Observability / Audit
    l8 = topology.layers[7]
    comp_names_l8 = [c.name for c in l8.components]
    assert "metrics_engine" in comp_names_l8
    assert "traces_engine" in comp_names_l8
    assert "events_audit_trail" in comp_names_l8

    # Verify Layer 9: Admin / Operations Dashboard
    l9 = topology.layers[8]
    comp_names_l9 = [c.name for c in l9.components]
    assert "platform_admin_dashboard" in comp_names_l9
    assert "hospital_admin_dashboard" in comp_names_l9
    assert "doctor_dashboard" in comp_names_l9
    assert "operations_dashboard" in comp_names_l9


def test_architecture_health_audit(db_session):
    """Validates that the multi-layer health audit evaluates all 9 layers."""
    health = PlatformArchitectureService.check_architecture_health(db=db_session)

    assert health.overall_status == "HEALTHY"
    assert health.active_layers == 9
    assert health.total_components_monitored >= 30
    assert health.healthy_components_count == health.total_components_monitored
    assert len(health.layer_health) == 9

    for layer_h in health.layer_health:
        assert layer_h.status == "HEALTHY"
        assert layer_h.healthy_components == layer_h.total_components
        assert layer_h.average_latency_ms >= 0.0


def test_synthetic_distributed_trace_web_voice_connector_a(db_session):
    """Executes a full synthetic transaction traversing all 9 layers via Web Voice and Connector A (FHIR R4)."""
    req = SyntheticTraceRequest(
        patient_channel="WEB_VOICE",
        patient_name="Aarav Patel",
        patient_phone="+14155551234",
        patient_symptom="Severe knee joint stiffness and mobility impairment",
        preferred_hospital_name="St. Jude Memorial Hospital",
        preferred_specialty="Orthopedics",
        ehr_connector="CONNECTOR_A",
        simulate_guardrail_pass=True,
        simulate_ehr_verification=True,
    )

    trace_resp = PlatformArchitectureService.synthesize_distributed_trace(request=req, db=db_session)

    assert trace_resp.trace_id.startswith("trace-arch-")
    assert trace_resp.execution_status == "COMPLETED"
    assert trace_resp.channel == "WEB_VOICE"
    assert "FHIR R4" in trace_resp.ehr_connector_used
    assert trace_resp.total_duration_ms > 0

    # Must contain exactly 9 spans, one for each architectural layer
    assert len(trace_resp.spans) == 9
    span_layer_nums = [s.layer_number for s in trace_resp.spans]
    assert span_layer_nums == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    # Verify span statuses
    assert all(s.status == "SUCCESS" for s in trace_resp.spans)

    # Verify timing breakdown includes all 9 layers
    assert len(trace_resp.layer_timing_breakdown) == 9

    # Verify final result contains all verification flags
    final = trace_resp.final_result
    assert final["status"] == "APPOINTMENT_CONFIRMED_AND_VERIFIED"
    assert final["is_ehr_verified"] is True
    assert final["all_9_layers_verified"] is True
    assert "EXT-CON-" in final["external_appointment_id"]


def test_synthetic_distributed_trace_telephony_connector_b(db_session):
    """Executes synthetic transaction traversing all 9 layers via Telephony and Connector B (Epic)."""
    req = SyntheticTraceRequest(
        patient_channel="TELEPHONY",
        patient_name="Meera Rao",
        patient_phone="+14155559876",
        patient_symptom="Chest tightness during morning jogs",
        preferred_hospital_name="Metro General Hospital",
        preferred_specialty="Cardiology",
        ehr_connector="CONNECTOR_B",
        simulate_guardrail_pass=True,
        simulate_ehr_verification=True,
    )

    trace_resp = PlatformArchitectureService.synthesize_distributed_trace(request=req, db=db_session)

    assert trace_resp.channel == "TELEPHONY"
    assert "Epic" in trace_resp.ehr_connector_used
    assert len(trace_resp.spans) == 9

    # Check Layer 1 metadata reflects SIP/PSTN
    l1_span = trace_resp.spans[0]
    assert l1_span.layer_id == ArchitectureLayerEnum.PATIENT_ENTRY
    assert l1_span.metadata["protocol"] == "SIP/PSTN"

    # Check Layer 4 component reflects Epic
    l4_span = trace_resp.spans[3]
    assert l4_span.layer_id == ArchitectureLayerEnum.EHR_INTEGRATION
    assert l4_span.component == "connector_b_epic"


def test_api_endpoints_architecture(client):
    """Validates FastAPI REST endpoints for platform architecture topology, health, and trace execution."""
    # 1. GET /api/v1/architecture/topology
    top_res = client.get("/api/v1/architecture/topology")
    assert top_res.status_code == 200
    top_data = top_res.json()
    assert top_data["total_layers"] == 9
    assert len(top_data["layers"]) == 9

    # 2. GET /api/v1/architecture/health
    health_res = client.get("/api/v1/architecture/health")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data["overall_status"] == "HEALTHY"
    assert health_data["active_layers"] == 9

    # 3. POST /api/v1/architecture/synthesize-trace
    trace_payload = {
        "patient_channel": "WEB_VOICE",
        "patient_name": "Kavita Reddy",
        "patient_phone": "+14155553344",
        "patient_symptom": "Acute rash on forearm",
        "preferred_hospital_name": "Regional Health Center",
        "preferred_specialty": "Dermatology",
        "ehr_connector": "CONNECTOR_C",
        "simulate_guardrail_pass": True,
        "simulate_ehr_verification": True,
    }
    trace_res = client.post("/api/v1/architecture/synthesize-trace", json=trace_payload)
    assert trace_res.status_code == 200
    trace_data = trace_res.json()
    assert trace_data["execution_status"] == "COMPLETED"
    assert len(trace_data["spans"]) == 9
    assert trace_data["final_result"]["all_9_layers_verified"] is True
