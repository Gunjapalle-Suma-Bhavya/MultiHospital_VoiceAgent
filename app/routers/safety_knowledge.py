"""
REST API Router for Section 18 (AI Safety Principles) and
Section 19 (Approved Knowledge & Information Retrieval).
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.safety.ai_safety import ai_safety_engine
from app.knowledge.approved_knowledge import approved_knowledge_engine

router = APIRouter(prefix="/api/v1/safety-knowledge", tags=["AI Safety & Knowledge (18 & 19)"])


class EvaluateCapabilityRequest(BaseModel):
    capability_name: str


class InspectQueryRequest(BaseModel):
    query_text: str


class FramingCheckRequest(BaseModel):
    statement_text: str


class KnowledgeQueryRequest(BaseModel):
    query: str
    hospital_id: Optional[str] = None


# =========================================================================
# SECTION 18: AI SAFETY PRINCIPLES ENDPOINTS
# =========================================================================

@router.post("/evaluate-capability")
def evaluate_capability_endpoint(req: EvaluateCapabilityRequest):
    """
    Evaluates whether a capability is allowed as an administrative assistant
    or strictly blocked as non-autonomous clinician behavior (e.g. diagnosis, prescriptions).
    """
    return ai_safety_engine.evaluate_capability(req.capability_name)


@router.post("/inspect-query")
def inspect_query_endpoint(req: InspectQueryRequest):
    """
    Scans patient utterances for clinical diagnosis, treatment decisions, or medication changes.
    """
    return ai_safety_engine.inspect_patient_query(req.query_text)


@router.post("/check-patient-framing")
def check_patient_framing_endpoint(req: FramingCheckRequest):
    """
    Enforces Section 18 Framing Rule:
    Distinguishes 'You reported [symptom]' from prohibited diagnostic 'You have [disease]'.
    """
    return ai_safety_engine.enforce_patient_reported_framing(req.statement_text)


# =========================================================================
# SECTION 19: APPROVED KNOWLEDGE & INFORMATION RETRIEVAL ENDPOINTS
# =========================================================================

@router.post("/query-knowledge")
def query_knowledge_endpoint(req: KnowledgeQueryRequest):
    """
    Retrieves grounded administrative information with citations.
    Distinguishes administrative info from medical advice and avoids unsupported claims.
    """
    return approved_knowledge_engine.query_approved_knowledge(
        query=req.query,
        hospital_id=req.hospital_id
    )
