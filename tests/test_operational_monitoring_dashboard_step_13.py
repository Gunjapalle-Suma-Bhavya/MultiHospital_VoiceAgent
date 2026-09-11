"""
Test Suite for Step 13: Operational Monitoring Dashboard.

Validates the complete 4-pillar operational view:
1. AI Health (active conversations, response latency, failed capability calls, escalation rate, AI error rate, evaluation results)
2. Workflow Health (running, completed, failed, retried, average duration, stuck executions)
3. EHR / External Integration Health (requests, operations, success/failure rate, duration, verification rate, recovery rate, reconciliations, unknown outcome, connector health)
4. Platform Health (API errors, background task failures, queue backlogs, notification failures, database errors, service availability)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.config import init_db, SessionLocal
from app.monitoring import (
    AIHealthMetrics,
    WorkflowHealthMetrics,
    EHRIntegrationHealthMetrics,
    PlatformHealthMetrics,
    OperationalMonitoringDashboardResponse,
)
from app.monitoring.operational_monitoring_service import OperationalMonitoringService


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


def test_complete_operational_monitoring_dashboard_service(db_session):
    """Validates the complete 4-pillar dashboard snapshot computed by the service."""
    res = OperationalMonitoringService.get_operational_dashboard(db=db_session)
    assert isinstance(res, OperationalMonitoringDashboardResponse)
    assert res.dashboard_name == "Operational Monitoring Dashboard"
    assert res.overall_health_grade in ["OPTIMAL", "STABLE", "DEGRADED", "ATTENTION_REQUIRED"]
    assert res.timestamp is not None


def test_ai_health_pillar_metrics(db_session):
    """Validates Pillar 1: AI Health metrics."""
    ai = OperationalMonitoringService.get_ai_health(db=db_session)
    assert isinstance(ai, AIHealthMetrics)
    assert isinstance(ai.active_conversations, int) and ai.active_conversations >= 0
    assert isinstance(ai.average_response_latency_ms, float) and ai.average_response_latency_ms >= 0.0
    assert isinstance(ai.failed_capability_calls, int) and ai.failed_capability_calls >= 0
    assert isinstance(ai.escalation_rate_pct, float) and 0.0 <= ai.escalation_rate_pct <= 100.0
    assert isinstance(ai.ai_error_rate_pct, float) and 0.0 <= ai.ai_error_rate_pct <= 100.0
    assert isinstance(ai.evaluation_results, dict)
    assert "overall_score" in ai.evaluation_results
    assert "pass_rate_pct" in ai.evaluation_results


def test_workflow_health_pillar_metrics(db_session):
    """Validates Pillar 2: Workflow Health metrics."""
    wf = OperationalMonitoringService.get_workflow_health(db=db_session)
    assert isinstance(wf, WorkflowHealthMetrics)
    assert isinstance(wf.running_workflows, int) and wf.running_workflows >= 0
    assert isinstance(wf.completed_workflows, int) and wf.completed_workflows >= 0
    assert isinstance(wf.failed_workflows, int) and wf.failed_workflows >= 0
    assert isinstance(wf.retried_workflows, int) and wf.retried_workflows >= 0
    assert isinstance(wf.average_workflow_duration_sec, float) and wf.average_workflow_duration_sec >= 0.0
    assert isinstance(wf.stuck_executions, int) and wf.stuck_executions >= 0


def test_ehr_integration_health_pillar_metrics(db_session):
    """Validates Pillar 3: EHR / External Integration Health metrics."""
    ehr = OperationalMonitoringService.get_ehr_health(db=db_session)
    assert isinstance(ehr, EHRIntegrationHealthMetrics)
    assert isinstance(ehr.integration_requests, int) and ehr.integration_requests >= 0
    assert isinstance(ehr.integration_operations, int) and ehr.integration_operations >= 0
    assert isinstance(ehr.success_rate_pct, float) and 0.0 <= ehr.success_rate_pct <= 100.0
    assert isinstance(ehr.failure_rate_pct, float) and 0.0 <= ehr.failure_rate_pct <= 100.0
    assert isinstance(ehr.average_duration_ms, float) and ehr.average_duration_ms >= 0.0
    assert isinstance(ehr.verification_rate_pct, float) and 0.0 <= ehr.verification_rate_pct <= 100.0
    assert isinstance(ehr.recovery_rate_pct, float) and 0.0 <= ehr.recovery_rate_pct <= 100.0
    assert isinstance(ehr.reconciliation_count, int) and ehr.reconciliation_count >= 0
    assert isinstance(ehr.unknown_outcome_operations, int) and ehr.unknown_outcome_operations >= 0
    assert isinstance(ehr.connector_health, dict)
    assert "MOCK_EHR" in ehr.connector_health


def test_platform_health_pillar_metrics(db_session):
    """Validates Pillar 4: Platform Health metrics."""
    plat = OperationalMonitoringService.get_platform_health(db=db_session)
    assert isinstance(plat, PlatformHealthMetrics)
    assert isinstance(plat.api_errors, int) and plat.api_errors >= 0
    assert isinstance(plat.background_task_failures, int) and plat.background_task_failures >= 0
    assert isinstance(plat.queue_backlog_indicators, dict)
    assert "workflow_queue" in plat.queue_backlog_indicators
    assert "outbound_notification_queue" in plat.queue_backlog_indicators
    assert isinstance(plat.notification_failures, int) and plat.notification_failures >= 0
    assert isinstance(plat.database_errors, int) and plat.database_errors >= 0
    assert isinstance(plat.service_availability_pct, float) and 0.0 <= plat.service_availability_pct <= 100.0
    assert plat.overall_status in ["HEALTHY", "DEGRADED", "CRITICAL"]


def test_operational_monitoring_api_endpoints(client):
    """Validates all REST API endpoints for operational monitoring."""
    # 1. Full Dashboard
    r_full = client.get("/api/v1/monitoring/operational")
    assert r_full.status_code == 200
    data_full = r_full.json()
    assert "ai_health" in data_full
    assert "workflow_health" in data_full
    assert "ehr_integration_health" in data_full
    assert "platform_health" in data_full

    # 2. AI Health
    r_ai = client.get("/api/v1/monitoring/operational/ai-health")
    assert r_ai.status_code == 200
    data_ai = r_ai.json()
    assert "active_conversations" in data_ai
    assert "average_response_latency_ms" in data_ai
    assert "evaluation_results" in data_ai

    # 3. Workflow Health
    r_wf = client.get("/api/v1/monitoring/operational/workflow-health")
    assert r_wf.status_code == 200
    data_wf = r_wf.json()
    assert "running_workflows" in data_wf
    assert "completed_workflows" in data_wf
    assert "stuck_executions" in data_wf

    # 4. EHR Health
    r_ehr = client.get("/api/v1/monitoring/operational/ehr-health")
    assert r_ehr.status_code == 200
    data_ehr = r_ehr.json()
    assert "verification_rate_pct" in data_ehr
    assert "connector_health" in data_ehr

    # 5. Platform Health
    r_plat = client.get("/api/v1/monitoring/operational/platform-health")
    assert r_plat.status_code == 200
    data_plat = r_plat.json()
    assert "service_availability_pct" in data_plat
    assert "queue_backlog_indicators" in data_plat
    assert "overall_status" in data_plat
