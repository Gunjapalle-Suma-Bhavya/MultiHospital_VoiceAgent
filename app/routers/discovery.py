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

@router.get("/discovery/doctors")
def discover_doctors(
    query: Optional[str] = "",
    specialty: Optional[str] = None,
    hospital_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    from app.database.models import Doctor, Hospital
    q = db.query(Doctor).filter(Doctor.is_active == True)
    if hospital_id:
        q = q.filter(Doctor.hospital_id == hospital_id)
    if specialty:
        q = q.filter(Doctor.specialty.ilike(f"%{specialty}%"))
    if query:
        q = q.filter(Doctor.name.ilike(f"%{query}%") | Doctor.specialty.ilike(f"%{query}%"))
    doctors = q.all()
    res = []
    for d in doctors:
        hosp = db.query(Hospital).filter(Hospital.id == d.hospital_id).first()
        res.append({
            "doctor_id": d.id,
            "id": d.id,
            "name": d.name,
            "specialty": d.specialty,
            "department": d.department,
            "hospital_id": d.hospital_id,
            "hospital_name": hosp.name if hosp else "Hospital",
            "experience_years": d.experience_years,
            "default_appointment_duration": d.default_appointment_duration,
            "is_active": d.is_active
        })
    return {"total": len(res), "doctors": res}

@router.get("/discovery/hospitals")
def discover_hospitals(
    query: Optional[str] = "",
    db: Session = Depends(get_db)
):
    from app.database.models import Hospital
    q = db.query(Hospital).filter(Hospital.is_active == True)
    if query:
        q = q.filter(Hospital.name.ilike(f"%{query}%"))
    hospitals = q.all()
    res = []
    for h in hospitals:
        res.append({
            "hospital_id": h.id,
            "id": h.id,
            "name": h.name,
            "code": h.code,
            "is_active": h.is_active
        })
    return {"total": len(res), "hospitals": res}

@router.get("/capabilities/list")
def list_capabilities(db: Session = Depends(get_db)):
    registry = CapabilityRegistry(db)
    return {"registered_capabilities": registry.get_registered_capabilities()}

@router.get("/ai/capabilities")
def list_ai_capabilities(db: Session = Depends(get_db)):
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
