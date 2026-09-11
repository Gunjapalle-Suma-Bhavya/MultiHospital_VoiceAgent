"""
AI Quality Feedback Loop & Continuous Improvement Package (Section 5.38).
"""

ROOT_CAUSE_CATEGORIES = [
    "PROMPT_AMBIGUITY",
    "WORKFLOW_TIMEOUT",
    "CAPABILITY_MISCONFIG",
    "EHR_SCHEMA_MISMATCH",
    "GUARDRAIL_TRIGGER",
    "UNSUPPORTED_INTENT"
]

IMPROVEMENT_TYPES = [
    "PROMPT_REFINEMENT",
    "WORKFLOW_SCHEDULE_ADJUSTMENT",
    "CAPABILITY_REGISTRATION",
    "EHR_ADAPTER_MAPPING",
    "GUARDRAIL_RULE"
]

CLASSIFICATIONS = [
    "SUCCESS",
    "MINOR_FAILURE",
    "CRITICAL_FAILURE",
    "ESCALATED"
]

from app.feedback.feedback_engine import AIQualityFeedbackEngine

__all__ = [
    "ROOT_CAUSE_CATEGORIES",
    "IMPROVEMENT_TYPES",
    "CLASSIFICATIONS",
    "AIQualityFeedbackEngine"
]
