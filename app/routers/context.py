"""
Context State, Anaphora Reference Resolution & Ambiguity Router.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.agent.multi_tier_context import MultiTierContextEngine
from app.agent.anaphora_and_ambiguity import AnaphoraContextResolver, AmbiguityClarificationEngine

router = APIRouter(prefix="/api/v1/context", tags=["Context State & Ambiguity Resolution"])


class ContextResolveInput(BaseModel):
    session_id: str
    patient_id: Optional[str] = None
    phone_number: Optional[str] = None
    user_utterance: str


@router.get("/state")
def get_context_state(session_id: str, patient_id: Optional[str] = None, phone_number: Optional[str] = None, db: Session = Depends(get_db)):
    engine = MultiTierContextEngine(db)
    bundle = engine.get_hierarchical_context(session_id=session_id, patient_id=patient_id, phone_number=phone_number)
    return {
        "bundle": bundle.model_dump(),
        "natural_hint": bundle.generate_natural_prompt_hint()
    }

@router.get("/patient/{phone_number}")
def get_patient_persistent_context(phone_number: str, db: Session = Depends(get_db)):
    engine = MultiTierContextEngine(db)
    bundle = engine.get_hierarchical_context(session_id="persistent-lookup", phone_number=phone_number)
    return {
        "phone_number": phone_number,
        "patient_id": bundle.patient_id,
        "bundle": bundle.model_dump(),
        "tier3_long_term": bundle.tier3_long_term.model_dump(),
        "preferred_hospitals": bundle.tier3_long_term.preferred_hospitals,
        "preferred_doctors": bundle.tier3_long_term.preferred_doctors,
        "previous_conversation_summaries": bundle.tier3_long_term.previous_conversation_summaries,
        "natural_hint": bundle.generate_natural_prompt_hint()
    }

@router.get("/{session_id}")
def get_session_context(session_id: str, db: Session = Depends(get_db)):
    engine = MultiTierContextEngine(db)
    bundle = engine.get_hierarchical_context(session_id=session_id)
    return {
        "session_id": session_id,
        "bundle": bundle.model_dump(),
        "tier1_turn": bundle.tier1_conversation_state.model_dump(),
        "tier2_session": bundle.tier2_short_term.model_dump(),
        "natural_hint": bundle.generate_natural_prompt_hint()
    }

@router.post("/resolve")
def resolve_context_reference(payload: ContextResolveInput, db: Session = Depends(get_db)):
    context_engine = MultiTierContextEngine(db)
    bundle = context_engine.get_hierarchical_context(
        session_id=payload.session_id,
        patient_id=payload.patient_id,
        phone_number=payload.phone_number
    )
    result = AnaphoraContextResolver.resolve_reference(
        user_utterance=payload.user_utterance,
        context_bundle=bundle
    )
    return result.model_dump()
