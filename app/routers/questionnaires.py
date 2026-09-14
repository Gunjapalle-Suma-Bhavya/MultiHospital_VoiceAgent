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
    try:
        from app.database.mongodb import persist_to_mongodb
        persist_to_mongodb("doctor_questions", {
            "question_id": daq.id,
            "doctor_id": daq.doctor_id,
            "question_text": daq.question_text,
            "question_type": daq.question_type,
            "created_at": daq.created_at.isoformat() if daq.created_at else None
        }, key_field="question_id")
    except Exception:
        pass
    return {"question_id": daq.id, "doctor_id": daq.doctor_id, "question_text": daq.question_text, "question_type": daq.question_type}

@router.get("/doctor/{doctor_id}")
def get_doctor_configured_questions(doctor_id: str, db: Session = Depends(get_db)):
    """
    Returns live dynamic doctor-configured approved questions from the database.
    """
    questions = db.query(DoctorApprovedQuestion).filter(
        DoctorApprovedQuestion.doctor_id == doctor_id
    ).order_by(DoctorApprovedQuestion.created_at.asc()).all()
    return [
        {
            "id": q.id,
            "doctor_id": q.doctor_id,
            "prompt": q.question_text,
            "type": q.question_type or "TEXT",
            "required": True
        }
        for q in questions
    ]

@router.delete("/doctor-question/{question_id}")
def delete_doctor_approved_question(question_id: str, db: Session = Depends(get_db)):
    """
    Deletes a doctor-approved question by ID.
    """
    q = db.query(DoctorApprovedQuestion).filter(DoctorApprovedQuestion.id == question_id).first()
    if q:
        db.delete(q)
        db.commit()
        try:
            from app.database.mongodb import get_collection
            col = get_collection("doctor_questions")
            if col is not None:
                col.delete_one({"question_id": question_id})
        except Exception:
            pass
        return {"success": True, "question_id": question_id}
    return {"success": False, "error": "Question not found"}

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
    from app.database.mongodb import persist_questionnaire_response, persist_to_mongodb
    from app.events.event_bus import event_bus, SystemEvent

    submission_id = f"SUB-{uuid.uuid4().hex[:8].upper()}"
    doc = {
        "submission_id": submission_id,
        "questionnaire_id": submission_id,
        "specialty": payload.specialty,
        "patient_name": payload.patient_name,
        "patient_phone": payload.patient_phone,
        "answers": payload.answers,
        "status": "COMPLETED",
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }
    # 1. Persist directly to MongoDB Atlas and link into patient_history
    try:
        persist_questionnaire_response(doc)
    except Exception:
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


@router.get("/appointments/{appointment_id}/responses")
def get_appointment_questionnaire_responses(appointment_id: str, db: Session = Depends(get_db)):
    """
    Returns submitted patient intake questionnaire responses associated with an appointment.
    Checks SQLite transactional records and MongoDB Atlas.
    """
    import json
    from app.database.models import PatientQuestionnaireResponse, PatientIntakeRecord

    answers: Dict[str, Any] = {}
    response_id: Optional[str] = None
    questionnaire_id: Optional[str] = None
    submitted_at: Optional[str] = None

    q_resp = db.query(PatientQuestionnaireResponse).filter(
        PatientQuestionnaireResponse.appointment_id == appointment_id
    ).order_by(PatientQuestionnaireResponse.submitted_at.desc()).first()

    if q_resp:
        response_id = q_resp.id
        questionnaire_id = q_resp.questionnaire_id
        submitted_at = q_resp.submitted_at.isoformat() if q_resp.submitted_at else None
        if q_resp.answers_json:
            try:
                answers.update(json.loads(q_resp.answers_json))
            except Exception:
                pass

    intake = db.query(PatientIntakeRecord).filter(
        PatientIntakeRecord.appointment_id == appointment_id
    ).first()

    if intake:
        if not response_id:
            response_id = intake.id
        if not questionnaire_id:
            questionnaire_id = intake.questionnaire_id or "INTAKE-STANDARD"
        if not submitted_at and hasattr(intake, "created_at") and intake.created_at:
            submitted_at = intake.created_at.isoformat()
        if intake.intake_answers_json:
            try:
                answers.update(json.loads(intake.intake_answers_json))
            except Exception:
                pass
        elif not answers and intake.patient_reported_summary:
            answers["symptoms"] = intake.patient_reported_summary

    # Also check MongoDB Atlas if answers still empty or for enrichment
    try:
        from app.database.mongodb import get_collection
        col = get_collection("patient_questionnaire_responses")
        if col is not None:
            m_doc = col.find_one({"appointment_id": appointment_id})
            if not m_doc:
                m_doc = col.find_one({"response_id": appointment_id})
            if m_doc:
                if not response_id:
                    response_id = m_doc.get("response_id") or str(m_doc.get("_id"))
                if not questionnaire_id:
                    questionnaire_id = m_doc.get("questionnaire_id") or "INTAKE-DYNAMIC"
                if not submitted_at:
                    submitted_at = m_doc.get("submitted_at")
                m_answers = m_doc.get("answers")
                if isinstance(m_answers, dict):
                    for k, v in m_answers.items():
                        if k not in answers:
                            answers[k] = v
    except Exception:
        pass

    if answers:
        return {
            "has_responses": True,
            "response_id": response_id or f"RESP-{appointment_id}",
            "questionnaire_id": questionnaire_id or "INTAKE-STANDARD",
            "submitted_at": submitted_at,
            "answers": answers
        }

    return {"has_responses": False, "answers": {}}


