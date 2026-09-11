"""
Complete Hospital Workflow REST API Router (Step 9).

Exposes:
- POST /api/v1/hospital-workflow/execute: Executes full 23-stage hospital workflow.
- GET /api/v1/hospital-workflow/presets: Standard simulation presets.
- GET /api/v1/hospital-workflow/steps: Definitions and titles for all 23 stages.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.hospital_workflow import (
    HospitalWorkflowExecutionRequest,
    HOSPITAL_WORKFLOW_PRESETS,
    HOSPITAL_WORKFLOW_STEP_TITLES,
)
from app.hospital_workflow.service import CompleteHospitalWorkflowService

router = APIRouter(prefix="/api/v1/hospital-workflow", tags=["Complete Hospital Workflow (Step 9)"])


@router.post("/execute", status_code=status.HTTP_200_OK)
def execute_hospital_workflow(req: HospitalWorkflowExecutionRequest, db: Session = Depends(get_db)):
    """
    Executes the complete 23-stage hospital workflow from registration to analytics.
    """
    svc = CompleteHospitalWorkflowService(db)
    result = svc.execute_23_step_workflow(req)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
    return result


@router.get("/presets")
def get_hospital_workflow_presets():
    """
    Returns standard hospital workflow presets for demonstration.
    """
    return {
        "presets": HOSPITAL_WORKFLOW_PRESETS
    }


@router.get("/steps")
def get_hospital_workflow_steps():
    """
    Returns all 23 stages of the canonical hospital workflow.
    """
    return {
        "total_steps": len(HOSPITAL_WORKFLOW_STEP_TITLES),
        "steps": [
            {"step": k, "title": v} for k, v in HOSPITAL_WORKFLOW_STEP_TITLES.items()
        ]
    }
