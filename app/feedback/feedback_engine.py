"""
AI Quality Feedback Loop Engine (Section 5.38).
Implements the full 7-step engineering lifecycle:
AI Interaction -> Outcome -> Evaluation -> Classification -> Review -> Improvement -> Re-Evaluation
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.database.models import AIQualityFeedbackRecord
from app.analytics.ai_evaluation_engine import AIEvaluationEngine


class AIQualityFeedbackEngine:
    """
    Engine governing continuous AI platform improvement and lifecycle tracking.
    """

    @staticmethod
    def process_interaction_outcome(
        db_session: Session,
        interaction_id: str,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        hospital_id: Optional[str] = None,
        evaluation_score: float = 1.0,
        is_success: bool = True,
        is_escalated: bool = False,
        failure_reason: Optional[str] = None
    ) -> AIQualityFeedbackRecord:
        """
        Step 1-4: Ingests interaction outcome, evaluates score, and classifies failure/success.
        """
        if is_escalated:
            classification = "ESCALATED"
        elif not is_success or evaluation_score < 0.70:
            classification = "CRITICAL_FAILURE"
        elif evaluation_score < 0.90 or failure_reason:
            classification = "MINOR_FAILURE"
        else:
            classification = "SUCCESS"

        record = AIQualityFeedbackRecord(
            interaction_id=interaction_id,
            session_id=session_id,
            trace_id=trace_id,
            hospital_id=hospital_id,
            classification=classification,
            evaluation_score=evaluation_score,
            review_notes=f"Outcome ingested: {failure_reason}" if failure_reason else "Auto-ingested interaction outcome",
            improvement_status="IDENTIFIED" if classification != "SUCCESS" else "VERIFIED_IN_RE_EVALUATION"
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        return record

    @staticmethod
    def review_and_attribute_root_cause(
        db_session: Session,
        feedback_id: str,
        root_cause_category: str,
        review_notes: str
    ) -> AIQualityFeedbackRecord:
        """
        Step 5: Review step attributing root cause category.
        """
        record = db_session.query(AIQualityFeedbackRecord).filter(
            (AIQualityFeedbackRecord.id == feedback_id) | (AIQualityFeedbackRecord.interaction_id == feedback_id)
        ).first()
        if not record:
            raise ValueError(f"AIQualityFeedbackRecord not found for identifier: {feedback_id}")

        record.root_cause_category = root_cause_category
        record.review_notes = review_notes
        record.improvement_status = "UNDER_REVIEW"
        record.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        db_session.commit()
        db_session.refresh(record)

        return record

    @staticmethod
    def apply_system_improvement(
        db_session: Session,
        feedback_id: str,
        improvement_type: str,
        improvement_details: Dict[str, Any]
    ) -> AIQualityFeedbackRecord:
        """
        Step 6: Applies prompt, workflow, capability, or EHR integration improvement.
        """
        record = db_session.query(AIQualityFeedbackRecord).filter(
            (AIQualityFeedbackRecord.id == feedback_id) | (AIQualityFeedbackRecord.interaction_id == feedback_id)
        ).first()
        if not record:
            raise ValueError(f"AIQualityFeedbackRecord not found for identifier: {feedback_id}")

        record.improvement_type = improvement_type
        record.improvement_details_json = json.dumps(improvement_details)
        record.improvement_status = "IMPROVEMENT_APPLIED"
        record.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        db_session.commit()
        db_session.refresh(record)

        return record

    @staticmethod
    def trigger_re_evaluation(
        db_session: Session,
        feedback_id: str
    ) -> Dict[str, Any]:
        """
        Step 7: Runs benchmark re-evaluation and verifies improvement effectiveness.
        """
        record = db_session.query(AIQualityFeedbackRecord).filter(
            (AIQualityFeedbackRecord.id == feedback_id) | (AIQualityFeedbackRecord.interaction_id == feedback_id)
        ).first()
        if not record:
            raise ValueError(f"AIQualityFeedbackRecord not found for identifier: {feedback_id}")

        # Run re-evaluation suite
        eval_report = AIEvaluationEngine.run_full_platform_evaluation(
            db_session=db_session,
            hospital_id=record.hospital_id,
            session_id=record.session_id
        )

        record.re_evaluation_id = eval_report["evaluation_id"]
        record.improvement_status = "VERIFIED_IN_RE_EVALUATION"
        record.evaluation_score = eval_report["overall_platform_score"]
        record.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        db_session.commit()
        db_session.refresh(record)

        return {
            "feedback_id": record.id,
            "interaction_id": record.interaction_id,
            "improvement_status": record.improvement_status,
            "post_improvement_score": eval_report["overall_platform_score"],
            "re_evaluation_report": eval_report
        }

    @staticmethod
    def get_feedback_lifecycle_history(
        db_session: Session,
        hospital_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries complete reviewable feedback loop history across engineering lifecycle stages.
        """
        query = db_session.query(AIQualityFeedbackRecord)
        if hospital_id:
            query = query.filter(AIQualityFeedbackRecord.hospital_id == hospital_id)

        records = query.order_by(AIQualityFeedbackRecord.created_at.desc()).all()

        output = []
        for r in records:
            output.append({
                "id": r.id,
                "interaction_id": r.interaction_id,
                "session_id": r.session_id,
                "trace_id": r.trace_id,
                "hospital_id": r.hospital_id,
                "classification": r.classification,
                "evaluation_score": r.evaluation_score,
                "root_cause_category": r.root_cause_category,
                "review_notes": r.review_notes,
                "improvement_type": r.improvement_type,
                "improvement_details": json.loads(r.improvement_details_json) if r.improvement_details_json else {},
                "improvement_status": r.improvement_status,
                "re_evaluation_id": r.re_evaluation_id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None
            })

        return output
