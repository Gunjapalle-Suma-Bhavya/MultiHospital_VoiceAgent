"""
End-to-End Patient Workflow REST API Router (Step 8).

Exposes:
- POST /api/v1/patient-workflow/execute: Executes full 20-step patient journey.
- GET /api/v1/patient-workflow/presets: Standard test and demo presets.
- GET /api/v1/patient-workflow/steps: Definitions of all 20 steps.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.patient_workflow import (
    WorkflowExecutionRequest,
    CLINICAL_WORKFLOW_PRESETS,
    WORKFLOW_STEP_TITLES,
)
from app.patient_workflow.service import EndToEndPatientWorkflowService

router = APIRouter(prefix="/api/v1/patient-workflow", tags=["End-to-End Patient Workflow (Step 8)"])


@router.post("/execute", status_code=status.HTTP_200_OK)
def execute_patient_workflow(req: WorkflowExecutionRequest, db: Session = Depends(get_db)):
    """
    Executes the complete 20-step patient workflow end-to-end.
    """
    svc = EndToEndPatientWorkflowService(db)
    result = svc.execute_20_step_workflow(req)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
    return result


@router.get("/presets")
def get_workflow_presets():
    """
    Returns standard clinical workflow presets for testing and demonstration.
    """
    return {
        "presets": CLINICAL_WORKFLOW_PRESETS
    }


@router.get("/steps")
def get_workflow_steps():
    """
    Returns the list of all 20 canonical workflow steps.
    """
    return {
        "total_steps": len(WORKFLOW_STEP_TITLES),
        "steps": [
            {"step": k, "title": v} for k, v in WORKFLOW_STEP_TITLES.items()
        ]
    }
