"""
Operational Intelligence & Telemetry Service (Section 1.7).

Provides full visibility into:
- What the AI attempted
- Capabilities invoked
- EHR systems contacted and connector used
- Latency (ms)
- Failures, retries, verification status, reconciliation, and human escalations
- AI model configuration, token usage, and approximate USD cost
- Overall workflow health metrics
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models import AITelemetryLog, WorkflowInstance, WorkflowStatus


# Model pricing rates (USD per 1,000 tokens)
MODEL_PRICING = {
    "gemini-3.6-flash": {"prompt": 0.00015, "completion": 0.00060},
    "gemini-3.6-pro": {"prompt": 0.00125, "completion": 0.00500},
    "gpt-4o": {"prompt": 0.00250, "completion": 0.01000}
}


class OperationalIntelligenceService:
    """
    Service for logging and querying AI & EHR operational telemetry.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    @staticmethod
    def calculate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        rates = MODEL_PRICING.get(model_name, MODEL_PRICING["gemini-3.6-flash"])
        cost = (prompt_tokens / 1000.0 * rates["prompt"]) + (completion_tokens / 1000.0 * rates["completion"])
        return round(cost, 6)

    def record_turn_telemetry(
        self,
        session_id: str,
        ai_attempt_summary: str,
        capability_invoked: Optional[str] = None,
        hospital_id: Optional[str] = None,
        ehr_system_contacted: Optional[str] = None,
        ehr_connector_used: Optional[str] = None,
        latency_ms: float = 0.0,
        failure_location: Optional[str] = None,
        retries_triggered: int = 0,
        verification_succeeded: bool = True,
        reconciliation_required: bool = False,
        recovery_succeeded: bool = True,
        escalated_to_human: bool = False,
        model_name: str = "gemini-3.6-flash",
        prompt_tokens: int = 0,
        completion_tokens: int = 0
    ) -> AITelemetryLog:
        
        total_tokens = prompt_tokens + completion_tokens
        cost = self.calculate_cost(model_name, prompt_tokens, completion_tokens)
        
        health = "HEALTHY"
        if escalated_to_human or not recovery_succeeded:
            health = "CRITICAL"
        elif retries_triggered > 0 or reconciliation_required:
            health = "DEGRADED"

        log = AITelemetryLog(
            session_id=session_id,
            hospital_id=hospital_id,
            ai_attempt_summary=ai_attempt_summary,
            capability_invoked=capability_invoked,
            model_name=model_name,
            ehr_system_contacted=ehr_system_contacted,
            ehr_connector_used=ehr_connector_used,
            latency_ms=latency_ms,
            failure_location=failure_location,
            retries_triggered=retries_triggered,
            verification_succeeded=verification_succeeded,
            reconciliation_required=reconciliation_required,
            recovery_succeeded=recovery_succeeded,
            escalated_to_human=escalated_to_human,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=cost,
            workflow_health_status=health
        )
        self.db.add(log)
        self.db.commit()
        return log

    def get_system_health_report(self) -> Dict[str, Any]:
        """
        Generates an aggregated operational intelligence summary for administrators.
        """
        total_invocations = self.db.query(func.count(AITelemetryLog.id)).scalar() or 0
        total_cost = self.db.query(func.sum(AITelemetryLog.estimated_cost_usd)).scalar() or 0.0
        total_tokens = self.db.query(func.sum(AITelemetryLog.total_tokens)).scalar() or 0
        avg_latency = self.db.query(func.avg(AITelemetryLog.latency_ms)).scalar() or 0.0
        escalations = self.db.query(func.count(AITelemetryLog.id)).filter(AITelemetryLog.escalated_to_human == True).scalar() or 0
        
        degraded_workflows = self.db.query(func.count(AITelemetryLog.id)).filter(AITelemetryLog.workflow_health_status == "DEGRADED").scalar() or 0
        critical_workflows = self.db.query(func.count(AITelemetryLog.id)).filter(AITelemetryLog.workflow_health_status == "CRITICAL").scalar() or 0

        return {
            "total_ai_invocations": total_invocations,
            "total_tokens_used": total_tokens,
            "total_estimated_cost_usd": round(total_cost, 4),
            "average_latency_ms": round(avg_latency, 2),
            "human_escalations_count": escalations,
            "workflow_health_breakdown": {
                "HEALTHY": total_invocations - degraded_workflows - critical_workflows,
                "DEGRADED": degraded_workflows,
                "CRITICAL": critical_workflows
            }
        }
