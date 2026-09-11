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
