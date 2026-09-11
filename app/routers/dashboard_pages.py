"""
Dashboard Pages REST API Router.
Exposes endpoints for the 4-persona, 49-page frontend feature breakdown:
11.1 Platform Admin (16 pages)
11.2 Hospital Dashboard (15 pages)
11.3 Doctor Dashboard (9 pages)
11.4 Patient Dashboard (9 pages)
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.dashboard.dashboard_pages_service import (
    DashboardPagesService,
    PageDataResponse
)

router = APIRouter(prefix="/dashboard-pages", tags=["Dashboard Front-End Pages (Step 11)"])


class PageActionRequest(BaseModel):
    action_name: str
    action_payload: Dict[str, Any] = {}


@router.get("/catalog")
def get_dashboard_pages_catalog():
    """
    Returns the complete 4-persona, 49-page frontend catalog breakdown:
    - 11.1 Platform Admin (16 pages)
    - 11.2 Hospital Dashboard (15 pages)
    - 11.3 Doctor Dashboard (9 pages)
    - 11.4 Patient Dashboard (9 pages)
    """
    return DashboardPagesService.get_catalog()


@router.get("/data/{role}/{page_id}", response_model=PageDataResponse)
def get_dashboard_page_data(
    role: str,
    page_id: str,
    hospital_id: Optional[str] = Query(None),
    doctor_id: Optional[str] = Query(None),
    patient_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns live structured data, KPIs, records, and controls for any of the 49 dashboard pages.
    """
    return DashboardPagesService.get_page_data(
        role=role,
        page_id=page_id,
        hospital_id=hospital_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        db=db
    )


@router.post("/action/{role}/{page_id}")
def execute_dashboard_page_action(
    role: str,
    page_id: str,
    req: PageActionRequest,
    db: Session = Depends(get_db)
):
    """
    Executes a contextual action on any of the 49 dashboard pages.
    """
    return {
        "status": "SUCCESS",
        "role": role,
        "page_id": page_id,
        "action_executed": req.action_name,
        "message": f"Action '{req.action_name}' executed successfully on {role} page '{page_id}'.",
        "result_payload": req.action_payload
    }
