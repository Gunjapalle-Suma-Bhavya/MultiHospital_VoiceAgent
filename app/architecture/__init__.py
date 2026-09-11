"""
Complete Platform Architecture domain definitions.
Implements the 9-layer architectural model:
1. Patient Entry Layer (Web Voice, Telephony)
2. Real-Time Voice Layer
3. Conversational AI Layer (Context Layer, Capability Layer, Safety / Guardrails)
4. EHR Integration Layer (Connectors A/B/C, Verification, State Synchronization)
5. Workflow / Event Layer (Background Workflows, Scheduled Tasks, Notifications)
6. Core Platform Layer (Hospitals, Doctors, Calendars, Patients, Appointments)
7. Data Layer (Operational Data, User Context Data, Analytics Data)
8. Observability / Audit Layer (Metrics, Traces, Events)
9. Admin / Operations Dashboard Layer
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ArchitectureLayerEnum(str, Enum):
    PATIENT_ENTRY = "patient_entry"
    REALTIME_VOICE = "realtime_voice"
    CONVERSATIONAL_AI = "conversational_ai"
    EHR_INTEGRATION = "ehr_integration"
    WORKFLOW_EVENT = "workflow_event"
    CORE_PLATFORM = "core_platform"
    DATA_LAYER = "data_layer"
    OBSERVABILITY_AUDIT = "observability_audit"
    ADMIN_OPERATIONS_DASHBOARD = "admin_operations_dashboard"


class LayerComponent(BaseModel):
    name: str
    display_title: str
    description: str
    sub_category: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    status: str = "ACTIVE"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ArchitectureLayerDefinition(BaseModel):
    layer_id: ArchitectureLayerEnum
    layer_number: int
    name: str
    display_title: str
    description: str
    components: List[LayerComponent]
    inbound_protocols: List[str] = Field(default_factory=list)
    outbound_protocols: List[str] = Field(default_factory=list)
    downstream_layers: List[ArchitectureLayerEnum] = Field(default_factory=list)


class ArchitectureTopologyResponse(BaseModel):
    version: str = "1.0.0"
    platform_name: str = "Autonomous Multi-Hospital Voice Agent Platform"
    total_layers: int = 9
    layers: List[ArchitectureLayerDefinition]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ComponentHealth(BaseModel):
    component_name: str
    status: str = "HEALTHY"  # HEALTHY, DEGRADED, UNHEALTHY
    latency_ms: float = 0.0
    details: Optional[str] = None


class LayerHealthStatus(BaseModel):
    layer_id: ArchitectureLayerEnum
    layer_number: int
    name: str
    status: str = "HEALTHY"
    healthy_components: int
    total_components: int
    average_latency_ms: float
    components: List[ComponentHealth] = Field(default_factory=list)


class ArchitectureHealthResponse(BaseModel):
    overall_status: str = "HEALTHY"
    timestamp: str
    active_layers: int = 9
    total_components_monitored: int
    healthy_components_count: int
    layer_health: List[LayerHealthStatus]
    summary_notes: List[str] = Field(default_factory=list)


class DistributedTraceSpan(BaseModel):
    span_id: str
    parent_span_id: Optional[str] = None
    layer_id: ArchitectureLayerEnum
    layer_number: int
    component: str
    operation: str
    started_at: str
    ended_at: str
    duration_ms: float
    status: str = "SUCCESS"  # SUCCESS, WARN, ERROR
    input_snapshot: Dict[str, Any] = Field(default_factory=dict)
    output_snapshot: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SyntheticTraceRequest(BaseModel):
    patient_channel: str = "WEB_VOICE"  # WEB_VOICE, TELEPHONY
    patient_name: str = "Priya Sharma"
    patient_phone: str = "+14155552671"
    patient_symptom: str = "Persistent lower back pain requiring orthopedic evaluation"
    preferred_hospital_name: Optional[str] = "St. Jude Memorial Hospital"
    preferred_specialty: str = "Orthopedics"
    ehr_connector: str = "CONNECTOR_A"  # CONNECTOR_A (FHIR), CONNECTOR_B (Epic), CONNECTOR_C (Cerner)
    simulate_guardrail_pass: bool = True
    simulate_ehr_verification: bool = True


class SyntheticTraceResponse(BaseModel):
    trace_id: str
    execution_status: str = "COMPLETED"
    started_at: str
    completed_at: str
    total_duration_ms: float
    channel: str
    ehr_connector_used: str
    spans: List[DistributedTraceSpan]
    layer_timing_breakdown: Dict[str, float] = Field(default_factory=dict)
    final_result: Dict[str, Any] = Field(default_factory=dict)
