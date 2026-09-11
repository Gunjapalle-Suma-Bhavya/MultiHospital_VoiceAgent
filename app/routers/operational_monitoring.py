"""
Operational Monitoring Dashboard REST API Router (Step 13).

Exposes endpoints for the four core operational monitoring pillars:
1. Complete Operational Monitoring Dashboard: GET /api/v1/monitoring/operational
2. AI Health: GET /api/v1/monitoring/operational/ai-health
3. Workflow Health: GET /api/v1/monitoring/operational/workflow-health
4. EHR / External Integration Health: GET /api/v1/monitoring/operational/ehr-health
5. Platform Health: GET /api/v1/monitoring/operational/platform-health
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.monitoring import (
    AIHealthMetrics,
    WorkflowHealthMetrics,
    EHRIntegrationHealthMetrics,
    PlatformHealthMetrics,
    OperationalMonitoringDashboardResponse,
)
from app.monitoring.operational_monitoring_service import OperationalMonitoringService

router = APIRouter(prefix="/api/v1/monitoring/operational", tags=["Operational Monitoring Dashboard (Step 13)"])


@router.get("", response_model=OperationalMonitoringDashboardResponse)
@router.get("/", response_model=OperationalMonitoringDashboardResponse)
def get_operational_monitoring_dashboard(db: Session = Depends(get_db)):
    """
    Returns the complete Operational Monitoring Dashboard across all four pillars:
    - AI Health (active conversations, response latency, failed capability calls, escalation rate, AI error rate, evaluation results)
    - Workflow Health (running, completed, failed, retried, average duration, stuck executions)
    - EHR / External Integration Health (requests, operations, success rate, failure rate, duration, verification rate, recovery rate, reconciliations, connector health)
    - Platform Health (API errors, background task failures, queue backlogs, notification failures, database errors, service availability)
    """
    return OperationalMonitoringService.get_operational_dashboard(db=db)


@router.get("/ai-health", response_model=AIHealthMetrics)
def get_ai_health_metrics(db: Session = Depends(get_db)):
    """Returns AI Health metrics."""
    return OperationalMonitoringService.get_ai_health(db=db)


@router.get("/workflow-health", response_model=WorkflowHealthMetrics)
def get_workflow_health_metrics(db: Session = Depends(get_db)):
    """Returns Workflow Health metrics."""
    return OperationalMonitoringService.get_workflow_health(db=db)


@router.get("/ehr-health", response_model=EHRIntegrationHealthMetrics)
def get_ehr_integration_health_metrics(db: Session = Depends(get_db)):
    """Returns EHR / External Integration Health metrics."""
    return OperationalMonitoringService.get_ehr_health(db=db)


@router.get("/platform-health", response_model=PlatformHealthMetrics)
def get_platform_health_metrics(db: Session = Depends(get_db)):
    """Returns Platform Health, queue backlogs, error counters, and availability metrics."""
    return OperationalMonitoringService.get_platform_health(db=db)
