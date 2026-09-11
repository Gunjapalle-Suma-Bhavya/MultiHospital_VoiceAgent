"""
AI Usage & Cost Tracker (Section 5.36).
Tracks request counts, token consumption, voice duration, processing latency, and estimated costs,
demonstrating that model usage is monitored as measurable infrastructure.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models import AIUsageRecord, Hospital


class AIUsageCostTracker:
    """
    Service for recording and aggregating AI economics metrics across hospitals, features,
    conversations, and workflows.
    """

    DEFAULT_INPUT_TOKEN_COST = 0.0000005   # $0.50 per 1M input tokens
    DEFAULT_OUTPUT_TOKEN_COST = 0.0000015  # $1.50 per 1M output tokens
    DEFAULT_VOICE_SEC_COST = 0.0001        # $0.0001 per voice second

    @staticmethod
    def record_ai_usage(
        db_session: Session,
        session_id: Optional[str] = None,
        hospital_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        feature_name: str = "VOICE_PATIENT_INTAKE",
        input_tokens: int = 0,
        output_tokens: int = 0,
        voice_duration_seconds: float = 0.0,
        processing_duration_ms: float = 0.0,
        estimated_cost_usd: Optional[float] = None,
        model_name: str = "gemini-3.6-flash"
    ) -> AIUsageRecord:
        """
        Logs an AI usage transaction and calculates estimated cost if not provided.
        """
        if estimated_cost_usd is None:
            calculated_cost = (
                (input_tokens * AIUsageCostTracker.DEFAULT_INPUT_TOKEN_COST) +
                (output_tokens * AIUsageCostTracker.DEFAULT_OUTPUT_TOKEN_COST) +
                (voice_duration_seconds * AIUsageCostTracker.DEFAULT_VOICE_SEC_COST)
            )
            estimated_cost_usd = round(calculated_cost, 6)

        record = AIUsageRecord(
            session_id=session_id,
            hospital_id=hospital_id,
            workflow_id=workflow_id,
            feature_name=feature_name,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            voice_duration_seconds=voice_duration_seconds,
            processing_duration_ms=processing_duration_ms,
            estimated_cost_usd=estimated_cost_usd
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        return record

    @staticmethod
    def get_overall_ai_usage_summary(db_session: Session) -> Dict[str, Any]:
        """
        Returns platform-wide AI economics summary.
        """
        total_requests = db_session.query(AIUsageRecord).count()
        if total_requests == 0:
            return {
                "total_ai_requests": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "total_voice_duration_seconds": 0.0,
                "avg_processing_duration_ms": 0.0,
                "total_estimated_cost_usd": 0.0
            }

        input_tokens = db_session.query(func.sum(AIUsageRecord.input_tokens)).scalar() or 0
        output_tokens = db_session.query(func.sum(AIUsageRecord.output_tokens)).scalar() or 0
        voice_seconds = db_session.query(func.sum(AIUsageRecord.voice_duration_seconds)).scalar() or 0.0
        avg_processing_ms = db_session.query(func.avg(AIUsageRecord.processing_duration_ms)).scalar() or 0.0
        total_cost = db_session.query(func.sum(AIUsageRecord.estimated_cost_usd)).scalar() or 0.0

        return {
            "total_ai_requests": total_requests,
            "total_input_tokens": input_tokens,
            "total_output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "total_voice_duration_seconds": round(voice_seconds, 2),
            "avg_processing_duration_ms": round(avg_processing_ms, 2),
            "total_estimated_cost_usd": round(total_cost, 4)
        }

    @staticmethod
    def get_cost_by_hospital(db_session: Session) -> List[Dict[str, Any]]:
        """
        Aggregates AI usage request counts, token usage, and costs per hospital.
        """
        results = db_session.query(
            AIUsageRecord.hospital_id,
            func.count(AIUsageRecord.id).label("request_count"),
            func.sum(AIUsageRecord.input_tokens).label("input_tokens"),
            func.sum(AIUsageRecord.output_tokens).label("output_tokens"),
            func.sum(AIUsageRecord.voice_duration_seconds).label("voice_seconds"),
            func.sum(AIUsageRecord.estimated_cost_usd).label("total_cost")
        ).group_by(AIUsageRecord.hospital_id).all()

        output = []
        for r in results:
            hosp_id = r.hospital_id or "UNASSIGNED_PLATFORM"
            hosp_name = "Global Platform / Unassigned"
            if r.hospital_id:
                hosp = db_session.query(Hospital).filter(Hospital.id == r.hospital_id).first()
                if hosp:
                    hosp_name = hosp.name

            in_tok = r.input_tokens or 0
            out_tok = r.output_tokens or 0
            output.append({
                "hospital_id": hosp_id,
                "hospital_name": hosp_name,
                "ai_requests": r.request_count,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "total_tokens": in_tok + out_tok,
                "voice_duration_seconds": round(r.voice_seconds or 0.0, 2),
                "estimated_cost_usd": round(r.total_cost or 0.0, 4)
            })

        return output

    @staticmethod
    def get_cost_by_feature(db_session: Session) -> Dict[str, Any]:
        """
        Aggregates usage and costs by feature area.
        """
        results = db_session.query(
            AIUsageRecord.feature_name,
            func.count(AIUsageRecord.id).label("request_count"),
            func.sum(AIUsageRecord.input_tokens).label("input_tokens"),
            func.sum(AIUsageRecord.output_tokens).label("output_tokens"),
            func.sum(AIUsageRecord.voice_duration_seconds).label("voice_seconds"),
            func.sum(AIUsageRecord.estimated_cost_usd).label("total_cost")
        ).group_by(AIUsageRecord.feature_name).all()

        feature_map = {}
        for r in results:
            in_tok = r.input_tokens or 0
            out_tok = r.output_tokens or 0
            feature_map[r.feature_name] = {
                "ai_requests": r.request_count,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "total_tokens": in_tok + out_tok,
                "voice_duration_seconds": round(r.voice_seconds or 0.0, 2),
                "estimated_cost_usd": round(r.total_cost or 0.0, 4)
            }

        return feature_map

    @staticmethod
    def get_cost_by_conversation(db_session: Session, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Aggregates AI costs per conversation session.
        """
        query = db_session.query(
            AIUsageRecord.session_id,
            func.count(AIUsageRecord.id).label("request_count"),
            func.sum(AIUsageRecord.input_tokens).label("input_tokens"),
            func.sum(AIUsageRecord.output_tokens).label("output_tokens"),
            func.sum(AIUsageRecord.voice_duration_seconds).label("voice_seconds"),
            func.sum(AIUsageRecord.estimated_cost_usd).label("total_cost")
        ).filter(AIUsageRecord.session_id != None)

        if session_id:
            query = query.filter(AIUsageRecord.session_id == session_id)

        results = query.group_by(AIUsageRecord.session_id).all()

        output = []
        for r in results:
            in_tok = r.input_tokens or 0
            out_tok = r.output_tokens or 0
            output.append({
                "session_id": r.session_id,
                "ai_requests": r.request_count,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "total_tokens": in_tok + out_tok,
                "voice_duration_seconds": round(r.voice_seconds or 0.0, 2),
                "estimated_cost_usd": round(r.total_cost or 0.0, 4)
            })

        return output

    @staticmethod
    def get_cost_by_workflow(db_session: Session, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Aggregates AI costs per background workflow instance.
        """
        query = db_session.query(
            AIUsageRecord.workflow_id,
            func.count(AIUsageRecord.id).label("request_count"),
            func.sum(AIUsageRecord.input_tokens).label("input_tokens"),
            func.sum(AIUsageRecord.output_tokens).label("output_tokens"),
            func.sum(AIUsageRecord.estimated_cost_usd).label("total_cost")
        ).filter(AIUsageRecord.workflow_id != None)

        if workflow_id:
            query = query.filter(AIUsageRecord.workflow_id == workflow_id)

        results = query.group_by(AIUsageRecord.workflow_id).all()

        output = []
        for r in results:
            in_tok = r.input_tokens or 0
            out_tok = r.output_tokens or 0
            output.append({
                "workflow_id": r.workflow_id,
                "ai_requests": r.request_count,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "total_tokens": in_tok + out_tok,
                "estimated_cost_usd": round(r.total_cost or 0.0, 4)
            })

        return output
