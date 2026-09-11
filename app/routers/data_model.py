"""
Core Data Model REST API Router (Step 7).

Exposes:
- Full hierarchical entity tree with live database counts
- Entity schema catalog and relationship inspection
- Database record statistics
- Relational integrity verification
- Baseline demonstration graph seeding
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.core_models.data_model_service import DataModelService

router = APIRouter(prefix="/api/v1/core-data-model", tags=["Core Data Model (Step 7)"])


@router.get("/tree")
def get_hierarchical_data_model_tree(db: Session = Depends(get_db)):
    """
    Returns the complete 22-entity hierarchical tree structure annotated with live database counts.
    """
    svc = DataModelService(db)
    return svc.get_hierarchical_tree()


@router.get("/entities")
def get_entity_catalog(db: Session = Depends(get_db)):
    """
    Returns metadata and column definitions for all core entities in the platform.
    """
    svc = DataModelService(db)
    catalog = svc.get_entity_catalog()
    return {
        "count": len(catalog),
        "entities": catalog,
    }


@router.get("/stats")
def get_database_statistics(db: Session = Depends(get_db)):
    """
    Returns flat row counts across all tables and entity nodes.
    """
    svc = DataModelService(db)
    return svc.get_database_stats()


@router.post("/validate")
def validate_relational_integrity(db: Session = Depends(get_db)):
    """
    Runs relational integrity and foreign-key consistency diagnostics across the data model.
    """
    svc = DataModelService(db)
    return svc.validate_relational_integrity()


@router.post("/seed-demo", status_code=status.HTTP_201_CREATED)
def seed_demo_hierarchy(db: Session = Depends(get_db)):
    """
    Seeds a fully interconnected baseline demonstration dataset spanning all 22 entities.
    """
    svc = DataModelService(db)
    return svc.seed_demo_hierarchy()
