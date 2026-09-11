"""
Platform Administrator Dashboard REST API Router (Section 5.33).
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dashboard.platform_admin_dashboard import PlatformAdminDashboardService


router = APIRouter(prefix="/api/v1/platform-admin", tags=["Platform Admin Dashboard"])


@router.get("/kpis")
def get_global_platform_kpis(db: Session = Depends(get_db)):
    """
    Returns global operational KPIs: Hospitals, Doctors, Patients, Appointments Today, AI Calls Today, Booking Success %, Questionnaire Complete %, Human Escalation %, Avg AI Latency (sec), and EHR Integration Success %.
    """
    service = PlatformAdminDashboardService(db)
    return service.get_global_kpis()


@router.get("/explorer/{category}")
def get_platform_explorer_data(
    category: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Queries authorized platform records across 12 domains: hospitals, doctors, patients, appointments, ai_interactions, workflows, system_failures, ehr_operations, external_events, audit_events, analytics, and ai_evaluations.
    """
    service = PlatformAdminDashboardService(db)
    try:
        return service.get_explorer_data(category=category, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
