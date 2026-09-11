"""
Event-Driven Architecture REST API Router (Section 5.29).
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.models import PlatformEventRecord
from app.database.connection import get_db
from app.events.event_bus import event_bus, SystemEvent


router = APIRouter(prefix="/api/v1/events", tags=["Event-Driven Architecture"])


class PublishEventInput(BaseModel):
    event_type: str
    aggregate_id: str
    source: str = "REST_API"
    payload: Dict[str, Any] = {}


@router.post("/publish")
def publish_event(payload: PublishEventInput, db: Session = Depends(get_db)):
    """
    Publishes a structured system event to the central EventBus.
    """
    event = SystemEvent(
        event_type=payload.event_type,
        aggregate_id=payload.aggregate_id,
        source=payload.source,
        payload=payload.payload
    )
    record = event_bus.publish(db, event)
    return {
        "success": True,
        "event_id": record.id,
        "event_type": record.event_type,
        "aggregate_id": record.aggregate_id,
        "published_at": record.published_at.isoformat() if record.published_at else None
    }


@router.get("/history")
def get_event_history(
    event_type: Optional[str] = Query(None),
    aggregate_id: Optional[str] = Query(None),
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Queries published platform event records.
    """
    query = db.query(PlatformEventRecord)
    if event_type:
        query = query.filter(PlatformEventRecord.event_type == event_type)
    if aggregate_id:
        query = query.filter(PlatformEventRecord.aggregate_id == aggregate_id)

    records = query.order_by(PlatformEventRecord.published_at.desc()).limit(limit).all()
    return {
        "total_count": len(records),
        "events": [
            {
                "id": r.id,
                "event_type": r.event_type,
                "source": r.source,
                "aggregate_id": r.aggregate_id,
                "payload_json": r.payload_json,
                "published_at": r.published_at.isoformat() if r.published_at else None
            }
            for r in records
        ]
    }


@router.get("/subscribers")
def get_event_subscribers():
    """
    Returns active event subscriber map.
    """
    return {
        "active_subscribers": event_bus.get_subscribers()
    }
