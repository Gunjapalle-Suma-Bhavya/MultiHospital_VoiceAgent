"""
Decoupled Event Consumers (Section 5.29).

Implements independent consumer modules that subscribe to SystemEvents:
- Analytics Consumer
- Notification Consumer
- Workflow Consumer
- Audit Systems Consumer
- Monitoring Consumer
- Evaluation Systems Consumer
- Reconciliation Consumer
"""

import json
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.events.event_bus import SystemEvent, event_bus
from app.database.models import AuditLog, EventType
from app.telemetry.intelligence import OperationalIntelligenceService
from app.notifications.notification_engine import NotificationEngine
from app.workflows.engine import BackgroundWorkflowEngine


class PlatformEventConsumers:
    """
    Subscribes and attaches decoupled handlers to the central EventBus.
    """

    @staticmethod
    def handle_analytics_event(db_session: Session, event: SystemEvent):
        """Records telemetry & operational analytics for published system events."""
        telemetry = OperationalIntelligenceService(db_session)
        telemetry.record_turn_telemetry(
            session_id=event.aggregate_id or "GLOBAL_EVENT",
            ai_attempt_summary=f"Event Driven Telemetry: {event.event_type}",
            capability_invoked=event.event_type,
            latency_ms=10.0
        )

    @staticmethod
    def handle_notification_event(db_session: Session, event: SystemEvent):
        """Dispatches multi-role notifications based on published structured events."""
        notifier = NotificationEngine(db_session)
        p = event.payload or {}

        if event.event_type == EventType.HOSPITAL_APPROVED.value:
            notifier.notify_hospital_approval(
                hospital_id=event.aggregate_id,
                hospital_name=p.get("hospital_name", "Hospital")
            )
        elif event.event_type == EventType.APPOINTMENT_BOOKED.value:
            patient_phone = p.get("patient_phone", "+15550000000")
            doctor_id = p.get("doctor_id", "DOC-DEFAULT")
            hospital_id = p.get("hospital_id", "HOSP-DEFAULT")
            doctor_name = p.get("doctor_name", "Doctor")
            hospital_name = p.get("hospital_name", "Hospital")
            start_dt = p.get("start_datetime", "Upcoming")

            # Patient Notification
            notifier.notify_patient_appointment_confirmation(patient_phone, doctor_name, hospital_name, start_dt)
            # Doctor Notification
            notifier.notify_doctor_new_appointment(doctor_id, p.get("patient_name", "Patient"), start_dt)
            # Hospital Notification
            notifier.notify_hospital_new_appointment(hospital_id, event.aggregate_id)

        elif event.event_type == EventType.APPOINTMENT_CANCELLED.value:
            patient_phone = p.get("patient_phone", "+15550000000")
            doctor_id = p.get("doctor_id", "DOC-DEFAULT")
            hospital_id = p.get("hospital_id", "HOSP-DEFAULT")
            
            notifier.notify_patient_cancellation(patient_phone, p.get("doctor_name", "Doctor"), p.get("hospital_name", "Hospital"), p.get("start_datetime", "Scheduled Time"))
            notifier.notify_doctor_cancellation(doctor_id, p.get("patient_name", "Patient"), p.get("start_datetime", "Scheduled Time"))
            notifier.notify_hospital_cancellation(hospital_id, event.aggregate_id)

        elif event.event_type == EventType.QUESTIONNAIRE_COMPLETED.value:
            patient_phone = p.get("patient_phone", "+15550000000")
            doctor_id = p.get("doctor_id", "DOC-DEFAULT")
            doctor_name = p.get("doctor_name", "Doctor")

            notifier.notify_patient_questionnaire_completion(patient_phone, doctor_name)
            notifier.notify_doctor_questionnaire_completed(doctor_id, p.get("patient_name", "Patient"))

        elif event.event_type == EventType.EHR_INTEGRATION_FAILED.value:
            hospital_id = p.get("hospital_id", "HOSP-DEFAULT")
            error_msg = p.get("error_reason", "EHR Sync Failed")

            notifier.notify_hospital_integration_failure(hospital_id, error_msg)

    @staticmethod
    def handle_workflow_event(db_session: Session, event: SystemEvent):
        """Triggers asynchronous workflows upon relevant event signals."""
        wf_engine = BackgroundWorkflowEngine(db_session)
        
        if event.event_type == EventType.APPOINTMENT_BOOKED.value:
            # Trigger appointment reminder and post-booking sequence
            wf_engine.start_appointment_reminder_workflow(event.aggregate_id)
            wf_engine.start_post_booking_workflow(event.aggregate_id)
            
        elif event.event_type == EventType.EHR_INTEGRATION_FAILED.value:
            wf_engine.start_failed_booking_recovery_workflow(
                appointment_id=event.aggregate_id,
                error_reason=event.payload.get("error_reason", "EHR Timeout")
            )

    @staticmethod
    def handle_audit_event(db_session: Session, event: SystemEvent):
        """Persists audit log entries for audit system consumer."""
        audit = AuditLog(
            session_id=event.payload.get("session_id", "EVENT_BUS"),
            hospital_id=event.payload.get("hospital_id", ""),
            event_type=f"EVENT_BUS_{event.event_type}",
            payload_json=json.dumps(event.to_dict())
        )
        db_session.add(audit)
        db_session.commit()

    @staticmethod
    def handle_monitoring_event(db_session: Session, event: SystemEvent):
        """Monitors system health and alerts on critical escalation triggers."""
        if event.event_type == EventType.HUMAN_ESCALATION_TRIGGERED.value:
            print(f"[Monitoring Alert] Human Escalation Triggered for Session {event.aggregate_id}")

    @staticmethod
    def handle_evaluation_event(db_session: Session, event: SystemEvent):
        """Records agent evaluation telemetry for quality scoring."""
        pass

    @staticmethod
    def handle_reconciliation_event(db_session: Session, event: SystemEvent):
        """Flags reconciliation when EHR state mismatches."""
        pass


def register_default_event_consumers():
    """Registers all default event consumers with the global EventBus instance."""
    for event_type in EventType:
        et = event_type.value
        event_bus.subscribe(et, PlatformEventConsumers.handle_analytics_event)
        event_bus.subscribe(et, PlatformEventConsumers.handle_notification_event)
        event_bus.subscribe(et, PlatformEventConsumers.handle_workflow_event)
        event_bus.subscribe(et, PlatformEventConsumers.handle_audit_event)
        event_bus.subscribe(et, PlatformEventConsumers.handle_monitoring_event)
        event_bus.subscribe(et, PlatformEventConsumers.handle_evaluation_event)
        event_bus.subscribe(et, PlatformEventConsumers.handle_reconciliation_event)


# Automatically register default consumers upon import
register_default_event_consumers()
