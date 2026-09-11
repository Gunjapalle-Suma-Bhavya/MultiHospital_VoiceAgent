"""
Platform Architecture REST API Router.
Exposes endpoints for inspecting architectural topology, auditing multi-layer health,
and executing synthetic distributed transaction traces across all 9 layers.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.architecture import (
    ArchitectureTopologyResponse,
    ArchitectureHealthResponse,
    SyntheticTraceRequest,
    SyntheticTraceResponse,
)
from app.architecture.service import PlatformArchitectureService

router = APIRouter(prefix="/architecture", tags=["Platform Architecture"])


@router.get("/topology", response_model=ArchitectureTopologyResponse)
def get_architecture_topology():
    """Returns the complete 9-layer architectural topology and component hierarchy."""
    return PlatformArchitectureService.get_complete_topology()


@router.get("/health", response_model=ArchitectureHealthResponse)
def get_architecture_health(db: Session = Depends(get_db)):
    """Audits live health, connectivity, and latency across all 9 architectural layers."""
    return PlatformArchitectureService.check_architecture_health(db=db)


@router.post("/synthesize-trace", response_model=SyntheticTraceResponse)
def synthesize_distributed_trace(
    request: SyntheticTraceRequest = SyntheticTraceRequest(),
    db: Session = Depends(get_db),
):
    """
    Executes a real synthetic transaction traversing all 9 architectural layers sequentially,
    capturing distributed trace spans, per-layer latencies, and payload snapshots.
    """
    return PlatformArchitectureService.synthesize_distributed_trace(request=request, db=db)
