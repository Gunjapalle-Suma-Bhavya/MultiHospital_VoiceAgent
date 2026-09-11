"""
REST API Router for Section 25: Product Principles.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.vision import ProductPrinciplesService

router = APIRouter(prefix="/api/v1/principles", tags=["Product Principles"])


@router.get("", summary="Get Canonical 16 Product Principles (Section 25)")
def get_product_principles():
    """
    Returns the authoritative 16 Product Principles that govern platform architecture,
    clinical safety boundaries, data isolation, and operational reliability.
    """
    return {
        "count": len(ProductPrinciplesService.get_principles_registry()),
        "principles": ProductPrinciplesService.get_principles_registry()
    }


@router.post("/audit", summary="Execute System-Wide Principles Compliance Audit (Section 25)")
def run_principles_audit(db: Session = Depends(get_db)):
    """
    Executes a real-time compliance audit across all 16 Product Principles against live platform subsystems.
    """
    return ProductPrinciplesService.evaluate_all_principles(db=db)
