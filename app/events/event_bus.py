"""
Event Bus & Structured Event Engine (Section 5.29).

Implements event-driven architecture to decouple platform features.
Events are published to the central EventBus, which persists event records to the DB
and dispatches them to registered consumers (Analytics, Notifications, Workflows, Audit, Monitoring, Evaluation, Reconciliation).
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Callable, Optional
from sqlalchemy.orm import Session

from app.database.models import PlatformEventRecord, EventType


@dataclass
class SystemEvent:
    event_type: str
    aggregate_id: str
    source: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "source": self.source,
            "payload": self.payload,
            "timestamp": self.timestamp
        }


class EventBus:
    """
    Central Event Bus Dispatcher supporting decoupled event publication & subscription.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Session, SystemEvent], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[Session, SystemEvent], None]):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    def publish(self, db_session: Session, event: SystemEvent) -> PlatformEventRecord:
        """
        Publishes a structured SystemEvent:
        1. Persists event record to DB (PlatformEventRecord)
        2. Dispatches to all registered event consumer handlers
        """
        # 1. Persist Event Record
        record = PlatformEventRecord(
            event_type=event.event_type,
            source=event.source,
            aggregate_id=event.aggregate_id,
            payload_json=json.dumps(event.payload)
        )
        db_session.add(record)
        db_session.commit()

        # 2. Dispatch to Subscribed Consumers
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(db_session, event)
            except Exception as e:
                # Isolate consumer errors so publishing never fails
                print(f"[EventBus Error] Consumer failed for event {event.event_type}: {str(e)}")

        # 3. Non-blocking Dual-Write Sync to MongoDB Atlas Cloud Store
        try:
            from app.database.mongodb import sync_event_to_mongodb
            sync_event_to_mongodb(event.to_dict())
        except Exception:
            pass

        return record

    def get_subscribers(self) -> Dict[str, int]:
        """Returns subscriber count per event type."""
        return {k: len(v) for k, v in self._subscribers.items()}

    def clear(self):
        """Clears subscribers for testing."""
        self._subscribers.clear()


# Global Singleton Event Bus Instance
event_bus = EventBus()
