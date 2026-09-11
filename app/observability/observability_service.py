"""
Observability Service (Sections 5.34 & 5.35).
Provides operational trace lookup, 16-step timeline reconstruction, failure diagnostics,
and cross-component correlation aggregation across all 10 system layers.
"""

import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.database.models import (
    OperationTrace, OperationTraceStep, AuditLog, PlatformEventRecord,
    NotificationRecord, AITelemetryLog, EHRSyncLog, WorkflowInstance, Appointment
)
from app.observability import CANONICAL_LIFECYCLE_STEPS, COMPONENT_TYPES


class ObservabilityService:
    """
    Query & Telemetry Analysis Engine for Operational Observability & Correlation Traceability.
    """

    @staticmethod
    def get_trace_details(db_session: Session, trace_id: str) -> Dict[str, Any]:
        """
        Retrieves complete operational trace summary, latency breakdown, and ordered 16-step timeline.
        """
        trace = db_session.query(OperationTrace).filter(OperationTrace.trace_id == trace_id).first()
        if not trace:
            trace = db_session.query(OperationTrace).filter(OperationTrace.id == trace_id).first()
        if not trace:
            return {"error": f"Operation trace not found for identifier: {trace_id}"}

        steps = db_session.query(OperationTraceStep).filter(
            OperationTraceStep.trace_id == trace.id
        ).order_by(OperationTraceStep.step_number).all()

        step_records = []
        for s in steps:
            step_records.append({
                "step_number": s.step_number,
                "step_name": s.step_name,
                "component_type": s.component_type,
                "status": s.status,
                "latency_ms": s.latency_ms,
                "error_message": s.error_message,
                "external_system_name": s.external_system_name,
                "retry_count": s.retry_count,
                "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                "details": json.loads(s.details_json) if s.details_json else {}
            })

        return {
            "trace_id": trace.trace_id,
            "correlation_id": trace.correlation_id,
            "session_id": trace.session_id,
            "hospital_id": trace.hospital_id,
            "patient_id": trace.patient_id,
            "appointment_id": trace.appointment_id,
            "operation_name": trace.operation_name,
            "status": trace.status,
            "started_at": trace.started_at.isoformat() if trace.started_at else None,
            "completed_at": trace.completed_at.isoformat() if trace.completed_at else None,
            "total_latency_ms": trace.total_latency_ms,
            "diagnostics": {
                "failure_location": trace.failure_location,
                "failed_action": trace.failed_action,
                "failed_external_system": trace.failed_external_system,
                "retries_triggered": trace.retries_triggered,
                "recovery_succeeded": trace.recovery_succeeded,
                "reconciliation_occurred": trace.reconciliation_occurred,
                "escalated_to_human": trace.escalated_to_human
            },
            "step_count": len(step_records),
            "steps": step_records
        }

    @staticmethod
    def get_correlation_timeline(db_session: Session, correlation_id: str) -> Dict[str, Any]:
        """
        Aggregates and correlates events across all 10 system layers connected by correlation_id (Section 5.35).
        """
        # 1. Operation Trace & Steps
        traces = db_session.query(OperationTrace).filter(
            OperationTrace.correlation_id == correlation_id
        ).all()
        trace_data = []
        session_ids = set()
        appointment_ids = set()

        for t in traces:
            if t.session_id:
                session_ids.add(t.session_id)
            if t.appointment_id:
                appointment_ids.add(t.appointment_id)
            trace_data.append(ObservabilityService.get_trace_details(db_session, t.trace_id))

        # 2. AI Decision Telemetry Logs
        ai_logs = []
        if session_ids:
            telemetry_records = db_session.query(AITelemetryLog).filter(
                AITelemetryLog.session_id.in_(list(session_ids))
            ).all()
            for rec in telemetry_records:
                ai_logs.append({
                    "id": rec.id,
                    "session_id": rec.session_id,
                    "attempt_summary": rec.ai_attempt_summary,
                    "capability_invoked": rec.capability_invoked,
                    "latency_ms": rec.latency_ms,
                    "tokens": rec.total_tokens,
                    "timestamp": rec.timestamp.isoformat() if rec.timestamp else None
                })

        # 3. EHR Integration Operations
        ehr_logs = []
        if appointment_ids:
            sync_records = db_session.query(EHRSyncLog).filter(
                EHRSyncLog.appointment_id.in_(list(appointment_ids))
            ).all()
            for s in sync_records:
                ehr_logs.append({
                    "id": s.id,
                    "appointment_id": s.appointment_id,
                    "action_type": s.action_type,
                    "sync_status": s.sync_status,
                    "external_reference_id": s.external_reference_id,
                    "timestamp": s.timestamp.isoformat() if s.timestamp else None
                })

        # 4. Workflows
        workflows = []
        if appointment_ids:
            wf_records = db_session.query(WorkflowInstance).filter(
                WorkflowInstance.appointment_id.in_(list(appointment_ids))
            ).all()
            for wf in wf_records:
                workflows.append({
                    "id": wf.id,
                    "workflow_name": wf.workflow_name,
                    "trigger_event": wf.trigger_event,
                    "status": wf.status,
                    "created_at": wf.created_at.isoformat() if wf.created_at else None
                })

        # 5. Audit Events
        audit_events = db_session.query(AuditLog).filter(
            AuditLog.correlation_id == correlation_id
        ).all()
        audit_list = [{
            "id": a.id,
            "event_type": a.event_type,
            "payload": json.loads(a.payload_json) if a.payload_json else {},
            "timestamp": a.timestamp.isoformat() if a.timestamp else None
        } for a in audit_events]

        # 6. Notifications
        notifications = db_session.query(NotificationRecord).all()
        # Filter notifications correlated by session/appointment or metadata
        matched_notifications = []
        for n in notifications:
            meta = json.loads(n.metadata_json) if n.metadata_json else {}
            if meta.get("correlation_id") == correlation_id or meta.get("session_id") in session_ids:
                matched_notifications.append({
                    "id": n.id,
                    "recipient_role": n.recipient_role,
                    "recipient_id": n.recipient_id,
                    "notification_type": n.notification_type,
                    "status": n.status,
                    "sent_at": n.sent_at.isoformat() if n.sent_at else None
                })

        # 7. System Events
        events = db_session.query(PlatformEventRecord).filter(
            PlatformEventRecord.aggregate_id.in_(list(session_ids) + list(appointment_ids) + [correlation_id])
        ).all()
        system_events = [{
            "id": e.id,
            "event_type": e.event_type,
            "source": e.source,
            "published_at": e.published_at.isoformat() if e.published_at else None
        } for e in events]

        return {
            "correlation_id": correlation_id,
            "component_layers": {
                "conversation": list(session_ids),
                "ai_decision": ai_logs,
                "capability_call": [t for tr in trace_data for t in tr.get("steps", []) if t.get("component_type") == "CAPABILITY_CALL"],
                "scheduling_operation": list(appointment_ids),
                "ehr_integration_operation": ehr_logs,
                "verification": [t for tr in trace_data for t in tr.get("steps", []) if t.get("component_type") == "VERIFICATION"],
                "synchronization": [t for tr in trace_data for t in tr.get("steps", []) if t.get("component_type") == "SYNCHRONIZATION"],
                "workflow": workflows,
                "notification": matched_notifications,
                "audit_event": audit_list
            },
            "system_events": system_events,
            "operation_traces": trace_data
        }

    @staticmethod
    def get_observability_analytics(db_session: Session) -> Dict[str, Any]:
        """
        Computes platform operational metrics, latency profiling per step, and failure diagnostics.
        """
        total_traces = db_session.query(OperationTrace).count()
        completed_traces = db_session.query(OperationTrace).filter(OperationTrace.status == "COMPLETED").count()
        failed_traces = db_session.query(OperationTrace).filter(OperationTrace.status == "FAILED").count()
        escalated_traces = db_session.query(OperationTrace).filter(OperationTrace.escalated_to_human == True).count()

        traces = db_session.query(OperationTrace).all()
        total_latency = sum(t.total_latency_ms for t in traces if t.total_latency_ms)
        avg_latency_ms = round(total_latency / total_traces, 2) if total_traces > 0 else 0.0

        # Step-level latency breakdown
        steps = db_session.query(OperationTraceStep).all()
        step_latency_map: Dict[str, List[float]] = {}
        failed_action_map: Dict[str, int] = {}
        failed_system_map: Dict[str, int] = {}

        for s in steps:
            if s.step_name not in step_latency_map:
                step_latency_map[s.step_name] = []
            if s.latency_ms:
                step_latency_map[s.step_name].append(s.latency_ms)

            if s.status == "FAILED":
                failed_action_map[s.step_name] = failed_action_map.get(s.step_name, 0) + 1
                if s.external_system_name:
                    failed_system_map[s.external_system_name] = failed_system_map.get(s.external_system_name, 0) + 1

        step_avg_latencies = {
            step: round(sum(lats) / len(lats), 2) for step, lats in step_latency_map.items() if lats
        }

        total_retries = sum(t.retries_triggered for t in traces if t.retries_triggered)
        successful_recoveries = sum(1 for t in traces if t.recovery_succeeded)
        reconciliations_count = sum(1 for t in traces if t.reconciliation_occurred)

        return {
            "total_traces": total_traces,
            "completed_traces": completed_traces,
            "failed_traces": failed_traces,
            "escalated_traces": escalated_traces,
            "success_rate_percent": round((completed_traces / total_traces * 100), 2) if total_traces > 0 else 100.0,
            "avg_latency_ms": avg_latency_ms,
            "step_latency_breakdown_ms": step_avg_latencies,
            "failed_action_distribution": failed_action_map,
            "failed_external_system_distribution": failed_system_map,
            "total_retries_triggered": total_retries,
            "successful_recoveries": successful_recoveries,
            "reconciliations_occurred": reconciliations_count,
            "human_escalation_rate_percent": round((escalated_traces / total_traces * 100), 2) if total_traces > 0 else 0.0
        }
