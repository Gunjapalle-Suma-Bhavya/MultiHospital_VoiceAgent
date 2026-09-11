"""
Doctor & Specialty Questionnaires, Conversational Intake & Safety Router (Sections 5.23 - 5.27).
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.questionnaires.questionnaire_engine import (
    QuestionnaireEngine, QuestionItem, QuestionResponseType, QuestionnaireStatus, StructuredQuestionnaire, ApplicabilityRules
)
from app.database.models import DoctorApprovedQuestion, HospitalQuestionnaire

router = APIRouter(prefix="/api/v1/questionnaires", tags=["Doctor & Specialty Questionnaires"])


class ConfigureApprovedQuestionInput(BaseModel):
    doctor_id: str
    question_text: str
    question_type: str = "SHORT_TEXT"

class ParseAnswerInput(BaseModel):
    question_id: str
    question_text: str
    response_type: str = "SHORT_TEXT"
    user_utterance: str

class SafetyCheckInput(BaseModel):
    user_utterance: str


@router.post("/configure-doctor-question")
def configure_doctor_approved_question(payload: ConfigureApprovedQuestionInput, db: Session = Depends(get_db)):
    daq = DoctorApprovedQuestion(
        doctor_id=payload.doctor_id,
        question_text=payload.question_text,
        question_type=payload.question_type
    )
    db.add(daq)
    db.commit()
    db.refresh(daq)
    return {"question_id": daq.id, "doctor_id": daq.doctor_id, "question_text": daq.question_text, "question_type": daq.question_type}

@router.get("/applicable")
def get_applicable_questionnaire(
    specialty: Optional[str] = None,
    appointment_type: Optional[str] = None,
    condition_category: Optional[str] = None,
    doctor_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    engine = QuestionnaireEngine(db)
    q = engine.resolve_applicable_questionnaire(
        specialty=specialty,
        appointment_type=appointment_type,
        condition_category=condition_category,
        doctor_id=doctor_id
    )
    intro = engine.generate_conversational_intro(q)
    return {
        "questionnaire": q.model_dump(),
        "conversational_intro": intro
    }

@router.post("/parse-response")
def parse_conversational_response(payload: ParseAnswerInput, db: Session = Depends(get_db)):
    engine = QuestionnaireEngine(db)
    qitem = QuestionItem(
        question_id=payload.question_id,
        question_text=payload.question_text,
        response_type=QuestionResponseType(payload.response_type if payload.response_type in QuestionResponseType.__members__ else "SHORT_TEXT")
    )
    parsed = engine.parse_conversational_answer(qitem, payload.user_utterance)
    return parsed

@router.post("/safety-check")
def evaluate_intake_safety(payload: SafetyCheckInput, db: Session = Depends(get_db)):
    engine = QuestionnaireEngine(db)
    safety_res = engine.evaluate_safety_and_urgency(payload.user_utterance)
    return safety_res.model_dump()


class QuestionnaireSubmitPayload(BaseModel):
    specialty: Optional[str] = "General"
    patient_name: Optional[str] = "Anonymous Patient"
    patient_phone: Optional[str] = "+1-555-0199"
    answers: Dict[str, Any] = {}


@router.post("/submit")
def submit_questionnaire_intake(payload: QuestionnaireSubmitPayload, db: Session = Depends(get_db)):
    import uuid
    from datetime import datetime, timezone
    from app.database.mongodb import persist_to_mongodb
    from app.events.event_bus import event_bus, SystemEvent

    submission_id = f"SUB-{uuid.uuid4().hex[:8].upper()}"
    doc = {
        "submission_id": submission_id,
        "specialty": payload.specialty,
        "patient_name": payload.patient_name,
        "patient_phone": payload.patient_phone,
        "answers": payload.answers,
        "status": "COMPLETED",
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }
    # 1. Persist directly to MongoDB Atlas
    persist_to_mongodb("questionnaires", doc, key_field="submission_id")

    # 2. Publish cross-portal event
    event = SystemEvent(
        event_type="PATIENT_INTAKE_COMPLETED",
        aggregate_id=submission_id,
        source="QUESTIONNAIRE_UI",
        payload=doc
    )
    event_bus.publish(db, event)

    return {
        "success": True,
        "submission_id": submission_id,
        "status": "COMPLETED",
        "persisted_to_mongodb": True
    }

