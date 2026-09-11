"""
Unit Test Suite for Sections 5.23 - 5.27:
- 5.23 Doctor-Configured Pre-Visit Questionnaire (Dr. Rao Cardiology example)
- 5.24 Specialty & Condition-Specific Questionnaires (Non-Invention Guardrail)
- 5.25 Questionnaire Engine (8 Response Types & Conversational Parser)
- 5.26 Questionnaire Conversation (Natural Conversational Intro & Transitions)
- 5.27 Questionnaire Safety Principle (Non-diagnostic Guardrail & Emergency Policy)
"""

import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, Doctor, DoctorApprovedQuestion, HospitalQuestionnaire
from app.questionnaires.questionnaire_engine import (
    QuestionnaireEngine, QuestionItem, QuestionResponseType, QuestionnaireStatus, StructuredQuestionnaire
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def setup_dr_rao_cardiology_data(db_session):
    hosp = Hospital(name="St. Jude General", code="STJUDE", is_active=True)
    db_session.add(hosp)
    db_session.commit()

    doc = Doctor(hospital_id=hosp.id, name="Dr. Rao", specialty="Cardiology", is_active=True)
    db_session.add(doc)
    db_session.commit()

    # Section 5.23 Dr. Rao Cardiology Approved Questions
    q1 = DoctorApprovedQuestion(doctor_id=doc.id, question_text="Have you experienced chest discomfort recently?", question_type="YES_NO")
    q2 = DoctorApprovedQuestion(doctor_id=doc.id, question_text="When did it begin?", question_type="SHORT_TEXT")
    q3 = DoctorApprovedQuestion(doctor_id=doc.id, question_text="Does it occur during physical activity?", question_type="YES_NO")
    q4 = DoctorApprovedQuestion(doctor_id=doc.id, question_text="Are you currently taking any prescribed medication?", question_type="YES_NO")
    db_session.add_all([q1, q2, q3, q4])
    db_session.commit()

    return hosp, doc


def test_section_5_23_doctor_configured_questionnaire(db_session, setup_dr_rao_cardiology_data):
    hosp, doc = setup_dr_rao_cardiology_data
    engine = QuestionnaireEngine(db_session)

    # Resolve Dr. Rao's Doctor-Configured Questionnaire
    q = engine.resolve_applicable_questionnaire(doctor_id=doc.id)
    assert q.doctor_name == "Dr. Rao"
    assert q.specialty == "Cardiology"
    assert len(q.questions) == 4
    assert q.questions[0].question_text == "Have you experienced chest discomfort recently?"
    assert q.questions[0].response_type == QuestionResponseType.YES_NO


def test_section_5_24_specialty_questionnaire_and_non_invention_guardrail(db_session, setup_dr_rao_cardiology_data):
    hosp, doc = setup_dr_rao_cardiology_data
    engine = QuestionnaireEngine(db_session)

    # 1. Resolve Specialty Questionnaire
    hq = HospitalQuestionnaire(
        hospital_id=hosp.id,
        title="Dermatology Pre-Visit Intake",
        specialty="Dermatology",
        questions_json='["Any skin allergies?", "How long has the rash been present?"]'
    )
    db_session.add(hq)
    db_session.commit()

    q_derm = engine.resolve_applicable_questionnaire(specialty="Dermatology")
    assert q_derm.title == "Dermatology Pre-Visit Intake"
    assert len(q_derm.questions) == 2

    # 2. Non-Invention Rule: Strictly uses approved database questionnaire
    assert q_derm.questions[0].question_text == "Any skin allergies?"


def test_section_5_25_response_types_and_conversational_parser(db_session):
    engine = QuestionnaireEngine(db_session)

    # YES_NO parsing
    q_yesno = QuestionItem(question_id="Q1", question_text="Chest pain?", response_type=QuestionResponseType.YES_NO)
    p1 = engine.parse_conversational_answer(q_yesno, "Yes, a few times")
    assert p1["parsed_value"] is True

    p2 = engine.parse_conversational_answer(q_yesno, "No, not really")
    assert p2["parsed_value"] is False

    # NUMERIC parsing
    q_num = QuestionItem(question_id="Q2", question_text="How many days?", response_type=QuestionResponseType.NUMERIC)
    p3 = engine.parse_conversational_answer(q_num, "It has been about 14 days")
    assert p3["parsed_value"] == 14

    # SHORT_TEXT parsing
    q_text = QuestionItem(question_id="Q3", question_text="When did it start?", response_type=QuestionResponseType.SHORT_TEXT)
    p4 = engine.parse_conversational_answer(q_text, "About two weeks ago")
    assert p4["parsed_value"] == "About two weeks ago"


def test_section_5_26_conversational_intro(db_session, setup_dr_rao_cardiology_data):
    hosp, doc = setup_dr_rao_cardiology_data
    engine = QuestionnaireEngine(db_session)

    q = engine.resolve_applicable_questionnaire(doctor_id=doc.id)
    intro = engine.generate_conversational_intro(q)
    assert "Dr. Rao has asked a few quick questions to help prepare for your visit. Is that okay?" in intro


def test_section_5_27_safety_principle_and_emergency_escalation(db_session):
    engine = QuestionnaireEngine(db_session)

    # 1. Non-diagnostic disclaimer
    safe_res = engine.evaluate_safety_and_urgency("I have a mild cough")
    assert safe_res.is_safe is True
    assert safe_res.is_urgent is False
    assert "Not a medical diagnosis" in safe_res.warning_disclaimer

    # 2. Emergency Escalation Policy
    urgent_res = engine.evaluate_safety_and_urgency("I am having severe chest pain and can't breathe")
    assert urgent_res.is_safe is False
    assert urgent_res.is_urgent is True
    assert urgent_res.requires_escalation is True
    assert "call 911" in urgent_res.warning_disclaimer
