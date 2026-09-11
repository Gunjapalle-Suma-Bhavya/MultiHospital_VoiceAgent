"""
Operational Monitoring Package (Step 13).

Defines typed response models and schemas for the dedicated operational view across 4 pillars:
1. AI Health
2. Workflow Health
3. EHR / External Integration Health
4. Platform Health
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class AIHealthMetrics(BaseModel):
    """Pillar 1: AI Health Metrics."""
    active_conversations: int = Field(..., description="Currently active conversational sessions")
    average_response_latency_ms: float = Field(..., description="Average AI response latency in milliseconds")
    failed_capability_calls: int = Field(..., description="Number of failed tool/capability invocations")
    escalation_rate_pct: float = Field(..., description="Percentage of interactions escalated to human support (%)")
    ai_error_rate_pct: float = Field(..., description="Percentage of turns resulting in an AI failure or timeout (%)")
    evaluation_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Aggregate internal evaluation benchmarks, pass rates, and domain quality scores"
    )


class WorkflowHealthMetrics(BaseModel):
    """Pillar 2: Workflow Health Metrics."""
    running_workflows: int = Field(..., description="Workflows currently executing")
    completed_workflows: int = Field(..., description="Successfully finished workflows")
    failed_workflows: int = Field(..., description="Workflows that terminated with failure")
    retried_workflows: int = Field(..., description="Workflows that triggered one or more retries")
    average_workflow_duration_sec: float = Field(..., description="Average end-to-end execution duration in seconds")
    stuck_executions: int = Field(..., description="Workflows in running/pending state beyond SLA threshold")


class EHRIntegrationHealthMetrics(BaseModel):
    """Pillar 3: EHR / External Integration Health Metrics."""
    integration_requests: int = Field(..., description="Total inbound and outbound EHR integration requests")
    integration_operations: int = Field(..., description="Count of distinct synchronization and mapping operations")
    success_rate_pct: float = Field(..., description="Percentage of integration actions completed successfully (%)")
    failure_rate_pct: float = Field(..., description="Percentage of integration calls that failed (%)")
    average_duration_ms: float = Field(..., description="Average roundtrip latency for external EHR operations in ms")
    verification_rate_pct: float = Field(..., description="Authoritative 5-point external state verification success rate (%)")
    recovery_rate_pct: float = Field(..., description="Percentage of failed external operations recovered via retry/fallback (%)")
    reconciliation_count: int = Field(..., description="Total discrepancies recorded in reconciliation ledger")
    unknown_outcome_operations: int = Field(..., description="Operations with indeterminate external state requiring audit")
    connector_health: Dict[str, str] = Field(
        default_factory=dict,
        description="Health status per external connector (MOCK_EHR, FHIR_R4, EPIC, CERNER)"
    )


class PlatformHealthMetrics(BaseModel):
    """Pillar 4: Platform Health Metrics."""
    api_errors: int = Field(..., description="Total 5xx and 4xx API level errors recorded")
    background_task_failures: int = Field(..., description="Background worker or scheduler failed executions")
    queue_backlog_indicators: Dict[str, int] = Field(
        default_factory=dict,
        description="Queue depths and backlog counts across async channels"
    )
    notification_failures: int = Field(..., description="Failed SMS, Email, or Voice notification deliveries")
    database_errors: int = Field(..., description="Database transaction or pool errors")
    service_availability_pct: float = Field(..., description="Estimated platform uptime / availability (%)")
    overall_status: str = Field(default="HEALTHY", description="Overall operational health status: HEALTHY, DEGRADED, CRITICAL")


class OperationalMonitoringDashboardResponse(BaseModel):
    """Comprehensive Operational Monitoring Dashboard Snapshot (Step 13)."""
    dashboard_name: str = Field(default="Operational Monitoring Dashboard", description="Dashboard title")
    overall_health_grade: str = Field(default="OPTIMAL", description="OPTIMAL, STABLE, DEGRADED, ATTENTION_REQUIRED")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ai_health: AIHealthMetrics
    workflow_health: WorkflowHealthMetrics
    ehr_integration_health: EHRIntegrationHealthMetrics
    platform_health: PlatformHealthMetrics
