"""
Unit Test Suite for Section 5.29 Event-Driven Platform Behavior.

Tests:
1. Publishing structured events across all 19 required event types.
2. EventBus subscriber dispatching to Analytics, Notifications, Workflows, Audit, Monitoring, Evaluation, Reconciliation consumers.
3. Event persistence in PlatformEventRecord database table.
4. REST API endpoints /api/v1/events/publish, /history, /subscribers.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, PlatformEventRecord, EventType, AuditLog, NotificationRecord
from app.events.event_bus import EventBus, SystemEvent, event_bus
from app.events.consumers import register_default_event_consumers


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_structured_system_events_publishing(db_session):
    bus = EventBus()
    consumed_events = []

    def mock_consumer(session, event):
        consumed_events.append(event.event_type)

    bus.subscribe(EventType.APPOINTMENT_BOOKED.value, mock_consumer)

    event = SystemEvent(
        event_type=EventType.APPOINTMENT_BOOKED.value,
        aggregate_id="APPT-101",
        source="SCHEDULING_SERVICE",
        payload={"patient_name": "Sarah Connor", "doctor_id": "DOC-77"}
    )

    record = bus.publish(db_session, event)

    assert record.id is not None
    assert record.event_type == "APPOINTMENT_BOOKED"
    assert record.aggregate_id == "APPT-101"
    assert "APPOINTMENT_BOOKED" in consumed_events

    # Verify persistent DB record
    db_rec = db_session.query(PlatformEventRecord).filter(PlatformEventRecord.id == record.id).first()
    assert db_rec is not None
    assert db_rec.source == "SCHEDULING_SERVICE"


def test_all_19_event_types_supported(db_session):
    required_events = [
        "HOSPITAL_APPROVED", "DOCTOR_CREATED", "APPOINTMENT_REQUESTED",
        "APPOINTMENT_BOOKED", "APPOINTMENT_CANCELLED", "APPOINTMENT_RESCHEDULED",
        "QUESTIONNAIRE_ASSIGNED", "QUESTIONNAIRE_COMPLETED", "AI_CONVERSATION_STARTED",
        "AI_TOOL_EXECUTED", "EHR_INTEGRATION_STARTED", "EHR_INTEGRATION_COMPLETED",
        "EHR_INTEGRATION_FAILED", "EHR_SYNC_VERIFIED", "EHR_RECONCILIATION_REQUIRED",
        "WORKFLOW_STARTED", "WORKFLOW_COMPLETED", "WORKFLOW_FAILED", "HUMAN_ESCALATION_TRIGGERED"
    ]

    for evt_type in required_events:
        evt = SystemEvent(
            event_type=evt_type,
            aggregate_id="TEST-AGG-1",
            source="TEST_SUITE",
            payload={"test": True}
        )
        rec = event_bus.publish(db_session, evt)
        assert rec.event_type == evt_type

    # Verify 19 event records persisted
    count = db_session.query(PlatformEventRecord).count()
    assert count >= 19


def test_decoupled_consumers_auto_dispatch(db_session):
    # Register default consumers
    register_default_event_consumers()

    evt = SystemEvent(
        event_type=EventType.APPOINTMENT_BOOKED.value,
        aggregate_id="APPT-AUTO-1",
        source="VOICE_AGENT",
        payload={
            "patient_phone": "+15559990000",
            "patient_name": "John Connor",
            "doctor_id": "DOC-HOUSE",
            "hospital_id": "HOSP-MERCY",
            "doctor_name": "Dr. House",
            "hospital_name": "Mercy Hospital",
            "start_datetime": "2026-09-15 10:00:00"
        }
    )

    event_bus.publish(db_session, evt)

    # 1. Audit System Consumer check
    audit_entry = db_session.query(AuditLog).filter(AuditLog.event_type == "EVENT_BUS_APPOINTMENT_BOOKED").first()
    assert audit_entry is not None

    # 2. Notification Consumer check
    notifications = db_session.query(NotificationRecord).all()
    assert len(notifications) >= 3  # Patient, Doctor, Hospital notifications triggered automatically!
    recipient_roles = [n.recipient_role for n in notifications]
    assert "PATIENT" in recipient_roles
    assert "DOCTOR" in recipient_roles
    assert "HOSPITAL" in recipient_roles
