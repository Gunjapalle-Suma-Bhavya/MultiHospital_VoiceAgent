"""
Structured Questionnaire & Safety Engine (Sections 5.23 - 5.27).

Manages doctor-configured & specialty questionnaires, natural conversational intake,
8 response types, non-invention guardrails, non-diagnostic safety rules, and emergency escalation policies.
"""

from enum import Enum
from datetime import datetime, timezone
import json
import re
import uuid
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.models import HospitalQuestionnaire, DoctorApprovedQuestion, Doctor, PatientProfile


class QuestionResponseType(str, Enum):
    YES_NO = "YES_NO"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    SINGLE_CHOICE = "SINGLE_CHOICE"
    NUMERIC = "NUMERIC"
    DATE = "DATE"
    SHORT_TEXT = "SHORT_TEXT"
    LONG_TEXT = "LONG_TEXT"
    STRUCTURED_RESPONSE = "STRUCTURED_RESPONSE"


class QuestionnaireStatus(str, Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class QuestionItem(BaseModel):
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    question_text: str
    response_type: QuestionResponseType = QuestionResponseType.SHORT_TEXT
    options: List[str] = []
    is_required: bool = True
    default_value: Optional[Any] = None


class ApplicabilityRules(BaseModel):
    specialty: Optional[str] = None
    appointment_type: Optional[str] = None
    condition_category: Optional[str] = None
    doctor_id: Optional[str] = None


class StructuredQuestionnaire(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    specialty: str
    version: str = "v1.0"
    status: QuestionnaireStatus = QuestionnaireStatus.ACTIVE
    questions: List[QuestionItem] = []
    applicability_rules: ApplicabilityRules = Field(default_factory=ApplicabilityRules)
    doctor_id: Optional[str] = None
    doctor_name: Optional[str] = None


class SafetyEvaluationResult(BaseModel):
    is_safe: bool
    is_urgent: bool = False
    requires_escalation: bool = False
    escalation_reason: Optional[str] = None
    warning_disclaimer: Optional[str] = None


class QuestionnaireEngine:
    """
    Core Questionnaire Engine for Doctor-Configured Pre-Visit Forms (Sections 5.23 - 5.27).
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def resolve_applicable_questionnaire(
        self,
        specialty: Optional[str] = None,
        appointment_type: Optional[str] = None,
        condition_category: Optional[str] = None,
        doctor_id: Optional[str] = None
    ) -> StructuredQuestionnaire:
        """
        Resolves applicable questionnaire.
        Non-Invention Rule: Strictly uses approved question sets from database.
        """

        # 1. Doctor-Specific Approved Questions Check (Section 5.23 - Dr. Rao Cardiology example)
        if doctor_id:
            doc = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
            if doc:
                approved_qs = self.db.query(DoctorApprovedQuestion).filter(DoctorApprovedQuestion.doctor_id == doctor_id).all()
                if approved_qs:
                    q_items = [
                        QuestionItem(
                            question_id=aq.id,
                            question_text=aq.question_text,
                            response_type=QuestionResponseType(aq.question_type if aq.question_type in QuestionResponseType.__members__ else "SHORT_TEXT")
                        ) for aq in approved_qs
                    ]
                    return StructuredQuestionnaire(
                        id=f"Q-DOC-{doctor_id[:8]}",
                        title=f"{doc.name} Pre-Visit Clinical Form",
                        specialty=doc.specialty,
                        status=QuestionnaireStatus.ACTIVE,
                        questions=q_items,
                        applicability_rules=ApplicabilityRules(specialty=doc.specialty, doctor_id=doctor_id),
                        doctor_id=doc.id,
                        doctor_name=doc.name
                    )

        # 2. Specialty & Hospital Questionnaire Check (Section 5.24)
        if specialty:
            hq = self.db.query(HospitalQuestionnaire).filter(HospitalQuestionnaire.specialty == specialty).first()
            if hq:
                raw_qs = json.loads(hq.questions_json) if hq.questions_json else []
                q_items = []
                for i, q in enumerate(raw_qs):
                    if isinstance(q, str):
                        q_items.append(QuestionItem(question_id=f"Q-{i+1}", question_text=q, response_type=QuestionResponseType.SHORT_TEXT))
                    elif isinstance(q, dict):
                        q_items.append(QuestionItem(**q))

                return StructuredQuestionnaire(
                    id=hq.id,
                    title=hq.title,
                    specialty=hq.specialty,
                    status=QuestionnaireStatus.ACTIVE,
                    questions=q_items,
                    applicability_rules=ApplicabilityRules(specialty=specialty, appointment_type=appointment_type, condition_category=condition_category)
                )

        # Default Standard Pre-Visit Intake Form
        default_qs = [
            QuestionItem(question_id="Q-DEF-1", question_text="What is your primary reason for visiting?", response_type=QuestionResponseType.SHORT_TEXT),
            QuestionItem(question_id="Q-DEF-2", question_text="Are you currently taking any prescribed medication?", response_type=QuestionResponseType.YES_NO)
        ]
        return StructuredQuestionnaire(
            id="Q-DEFAULT-GENERAL",
            title="General Pre-Visit Health Intake",
            specialty=specialty or "General",
            status=QuestionnaireStatus.ACTIVE,
            questions=default_qs,
            applicability_rules=ApplicabilityRules(specialty=specialty)
        )

    def generate_conversational_intro(self, questionnaire: StructuredQuestionnaire, doctor_name: Optional[str] = None) -> str:
        """
        Generates natural conversational intro (Section 5.26).
        Example: "Before we finish, Dr. Rao has asked a few questions to help prepare for your visit. Is that okay?"
        """
        doc = doctor_name or questionnaire.doctor_name or "your doctor"
        return f"Before we finish, {doc} has asked a few quick questions to help prepare for your visit. Is that okay?"

    def parse_conversational_answer(self, question_item: QuestionItem, user_utterance: str) -> Dict[str, Any]:
        """
        Converts natural conversational user speech/text into structured JSON matching response type (Section 5.25).
        """
        text = user_utterance.strip()
        lowered = text.lower()
        qtype = question_item.response_type

        if qtype == QuestionResponseType.YES_NO:
            if any(w in lowered for w in ["yes", "yeah", "yep", "sure", "correct", "a few times", "i have"]):
                val = True
            elif any(w in lowered for w in ["no", "nope", "never", "not really", "i haven't"]):
                val = False
            else:
                val = text
            return {"question_id": question_item.question_id, "response_type": qtype.value, "parsed_value": val, "raw_utterance": text}

        elif qtype == QuestionResponseType.NUMERIC:
            match = re.search(r'\d+', text)
            val = int(match.group(0)) if match else None
            return {"question_id": question_item.question_id, "response_type": qtype.value, "parsed_value": val, "raw_utterance": text}

        elif qtype == QuestionResponseType.DATE:
            return {"question_id": question_item.question_id, "response_type": qtype.value, "parsed_value": text, "raw_utterance": text}

        # Default SHORT_TEXT / LONG_TEXT / STRUCTURED
        return {"question_id": question_item.question_id, "response_type": qtype.value, "parsed_value": text, "raw_utterance": text}

    def evaluate_safety_and_urgency(self, user_utterance: str) -> SafetyEvaluationResult:
        """
        Questionnaire Safety Principle & Emergency Escalation Policy (Section 5.27).
        Strict Rule: Platform is NOT a diagnostic engine.
        """
        lowered = user_utterance.lower()

        # Emergency Urgent Symptoms
        urgent_keywords = ["severe chest pain", "crushing chest pain", "can't breathe", "shortness of breath", "fainted", "unconscious"]
        if any(kw in lowered for kw in urgent_keywords):
            return SafetyEvaluationResult(
                is_safe=False,
                is_urgent=True,
                requires_escalation=True,
                escalation_reason="Urgent acute symptom reported during pre-visit intake.",
                warning_disclaimer="EMERGENCY ALERT: If you are experiencing a medical emergency, please call 911 immediately or go to the nearest emergency room."
            )

        return SafetyEvaluationResult(
            is_safe=True,
            is_urgent=False,
            requires_escalation=False,
            warning_disclaimer="For pre-visit intake purposes only. Not a medical diagnosis or treatment plan."
        )
