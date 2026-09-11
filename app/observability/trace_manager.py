"""
Trace Manager (Section 5.34 Operational Observability).
Manages lifecycle tracing, step accumulation, latency recording, failure location attribution,
retry counts, and final trace resolution.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.database.models import OperationTrace, OperationTraceStep


class TraceManager:
    """
    Core engine responsible for starting, recording, and resolving end-to-end operation traces.
    """

    @staticmethod
    def start_trace(
        db_session: Session,
        session_id: str,
        hospital_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        appointment_id: Optional[str] = None,
        operation_name: str = "PATIENT_ACCESS_BOOKING_LIFECYCLE",
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> OperationTrace:
        """
        Starts a new operation trace and assigns a unified correlation identifier.
        """
        generated_trace_id = f"TRC-{uuid.uuid4().hex[:12].upper()}"
        active_correlation_id = correlation_id or f"CORR-{uuid.uuid4().hex[:12].upper()}"

        trace = OperationTrace(
            trace_id=generated_trace_id,
            correlation_id=active_correlation_id,
            session_id=session_id,
            hospital_id=hospital_id,
            patient_id=patient_id,
            appointment_id=appointment_id,
            operation_name=operation_name,
            status="IN_PROGRESS",
            started_at=datetime.now(timezone.utc).replace(tzinfo=None),
            total_latency_ms=0.0,
            retries_triggered=0,
            metadata_json=json.dumps(metadata) if metadata else None
        )
        db_session.add(trace)
        db_session.commit()
        db_session.refresh(trace)

        # Record initial step 1: CALL_STARTED
        step1 = OperationTraceStep(
            trace_id=trace.id,
            step_number=1,
            step_name="CALL_STARTED",
            component_type="CONVERSATION",
            status="SUCCESS",
            latency_ms=10.0,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
            details_json=json.dumps({"session_id": session_id, "operation": operation_name})
        )
        db_session.add(step1)
        db_session.commit()

        return trace

    @staticmethod
    def record_step(
        db_session: Session,
        trace_id: str,
        step_name: str,
        component_type: str,
        latency_ms: float = 0.0,
        status: str = "SUCCESS",
        error_message: Optional[str] = None,
        external_system_name: Optional[str] = None,
        retry_count: int = 0,
        details: Optional[Dict[str, Any]] = None
    ) -> OperationTraceStep:
        """
        Appends a step to an existing operation trace and updates diagnostic state.
        """
        trace = db_session.query(OperationTrace).filter(OperationTrace.trace_id == trace_id).first()
        if not trace:
            # Fallback lookup by primary key ID
            trace = db_session.query(OperationTrace).filter(OperationTrace.id == trace_id).first()
        if not trace:
            raise ValueError(f"OperationTrace not found for identifier: {trace_id}")

        existing_steps_count = db_session.query(OperationTraceStep).filter(OperationTraceStep.trace_id == trace.id).count()
        next_step_number = existing_steps_count + 1

        # Accumulate metrics
        if retry_count > 0:
            trace.retries_triggered = (trace.retries_triggered or 0) + retry_count

        if status == "FAILED" or error_message:
            trace.status = "FAILED"
            trace.failed_action = step_name
            trace.failure_location = component_type
            if external_system_name:
                trace.failed_external_system = external_system_name

        step_record = OperationTraceStep(
            trace_id=trace.id,
            step_number=next_step_number,
            step_name=step_name,
            component_type=component_type,
            status=status,
            latency_ms=latency_ms,
            error_message=error_message,
            external_system_name=external_system_name,
            retry_count=retry_count,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
            details_json=json.dumps(details) if details else None
        )
        db_session.add(step_record)
        db_session.commit()
        db_session.refresh(step_record)

        return step_record

    @staticmethod
    def finalize_trace(
        db_session: Session,
        trace_id: str,
        status: str = "COMPLETED",
        recovery_succeeded: bool = False,
        reconciliation_occurred: bool = False,
        escalated_to_human: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> OperationTrace:
        """
        Finalizes an operation trace, calculates total latency, appends CALL_COMPLETED step if missing,
        and records final recovery/reconciliation/escalation outcomes.
        """
        trace = db_session.query(OperationTrace).filter(OperationTrace.trace_id == trace_id).first()
        if not trace:
            trace = db_session.query(OperationTrace).filter(OperationTrace.id == trace_id).first()
        if not trace:
            raise ValueError(f"OperationTrace not found for identifier: {trace_id}")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        trace.completed_at = now
        trace.status = status
        trace.recovery_succeeded = recovery_succeeded
        trace.reconciliation_occurred = reconciliation_occurred
        trace.escalated_to_human = escalated_to_human

        # Calculate sum of latencies across steps
        steps = db_session.query(OperationTraceStep).filter(OperationTraceStep.trace_id == trace.id).all()
        has_call_completed = any(s.step_name == "CALL_COMPLETED" for s in steps)

        if not has_call_completed:
            final_step_number = len(steps) + 1
            final_step = OperationTraceStep(
                trace_id=trace.id,
                step_number=final_step_number,
                step_name="CALL_COMPLETED",
                component_type="CONVERSATION",
                status="SUCCESS" if status == "COMPLETED" else "FAILED",
                latency_ms=15.0,
                timestamp=now,
                details_json=json.dumps({"final_status": status})
            )
            db_session.add(final_step)
            db_session.commit()
            steps.append(final_step)

        trace.total_latency_ms = sum(s.latency_ms for s in steps if s.latency_ms)

        if metadata:
            existing_meta = json.loads(trace.metadata_json) if trace.metadata_json else {}
            existing_meta.update(metadata)
            trace.metadata_json = json.dumps(existing_meta)

        db_session.commit()
        db_session.refresh(trace)

        return trace
