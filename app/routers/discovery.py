"""
Discovery Engine & Capability Tool Layer Router.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.discovery.discovery_engine import HospitalDoctorDiscoveryEngine, DiscoveryRequest
from app.agent.capability_registry import CapabilityRegistry, CapabilityExecutionRequest
from app.agent.capability_discovery import CapabilityDiscoveryService, CapabilityCategory

router = APIRouter(prefix="/api/v1", tags=["Discovery Engine & Capability Tools"])


@router.post("/discovery/search")
def execute_discovery_search(payload: DiscoveryRequest, db: Session = Depends(get_db)):
    engine = HospitalDoctorDiscoveryEngine(db)
    return engine.execute_discovery(payload)

@router.get("/capabilities/list")
def list_capabilities(db: Session = Depends(get_db)):
    registry = CapabilityRegistry(db)
    return {"registered_capabilities": registry.get_registered_capabilities()}

@router.post("/capabilities/execute")
def execute_capability(payload: CapabilityExecutionRequest, db: Session = Depends(get_db)):
    registry = CapabilityRegistry(db)
    return registry.execute(payload)

@router.get("/capabilities/discover")
def discover_capabilities_catalog(category: Optional[str] = None, caller_role: str = "PATIENT_AGENT", db: Session = Depends(get_db)):
    svc = CapabilityDiscoveryService(db)
    cat_enum = CapabilityCategory(category) if category else None
    descriptors = svc.discover_capabilities(category=cat_enum, caller_role=caller_role)
    return {"count": len(descriptors), "capabilities": descriptors}
