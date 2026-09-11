"""
Hospital Administrator Dashboard REST API Router (Section 5.32).
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dashboard.hospital_dashboard import HospitalDashboardService


router = APIRouter(prefix="/api/v1/hospital-dashboard", tags=["Hospital Dashboard"])


@router.get("/{hospital_id}/kpis")
def get_hospital_kpis(hospital_id: str, db: Session = Depends(get_db)):
    """
    Returns 13 organization-specific KPIs for hospital administrators.
    """
    service = HospitalDashboardService(db)
    try:
        return service.get_hospital_kpis(hospital_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{hospital_id}/management")
def get_hospital_management_overview(hospital_id: str, db: Session = Depends(get_db)):
    """
    Returns management overview across 10 hospital domains: departments, specialties, doctors, calendars, availability, questionnaires, staff, workflows, communication settings, and healthcare-system integrations.
    """
    service = HospitalDashboardService(db)
    try:
        return service.get_management_overview(hospital_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
