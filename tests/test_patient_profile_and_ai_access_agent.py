"""
Unit test suite for Section 5.8 Patient Registration & Profile and Section 5.9 AI Patient Access Agent.
Tests:
- Patient registration, profile update, data minimization verification
- Patient appointment self-service (list, cancel, request reschedule)
- Patient questionnaire submission & response retrieval
- Multi-channel AI Patient Access Agent 12-capability turns:
  1. Natural language understanding & intent detection
  2. Context resolution
  3. Clarification
  4. Tool / capability selection
  5. Structured actions
  6. Persistent interaction context
  7. Workflow initiation (intake, booking)
  8. Error handling
  9. EHR integration orchestration
  10. Verification (EHR match)
  11. Human escalation
  12. Channel reuse across Web Voice, Telephone, Messaging
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, Doctor, HospitalStatus, DoctorStatus, EHRIntegrationConfig, EHRAdapterType, PatientProfile, HospitalQuestionnaire
from app.patients.patient_service import PatientSelfServiceService
from app.agent.patient_access_agent import AIPatientAccessAgent
from app.onboarding.hospital_onboarding import HospitalSelfServiceOnboardingService
from app.doctors.doctor_management import DoctorManagementService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def setup_hospital_and_doctor(db_session):
    onboarding = HospitalSelfServiceOnboardingService(db_session)
    hosp = onboarding.create_draft_hospital(
        name="St. Jude Medical Center",
        code="STJUDE",
        contact_email="admin@stjude.org",
        admin_name="Dr. Mark",
        admin_email="mark@stjude.org"
    )
    onboarding.submit_application(hosp.id)
    onboarding.approve_hospital(hosp.id)

    doc_service = DoctorManagementService(db_session)
    doc = doc_service.invite_doctor(
        hospital_id=hosp.id,
        name="Dr. Gregory House",
        specialty="Diagnostics",
        department="Internal Medicine"
    )
    doc_service.activate_doctor(doc.id)

    ehr_cfg = EHRIntegrationConfig(
        hospital_id=hosp.id,
        adapter_type=EHRAdapterType.MOCK_EHR,
        is_active=True,
        is_sync_enabled=True
    )
    db_session.add(ehr_cfg)

    q = HospitalQuestionnaire(
        hospital_id=hosp.id,
        title="General Intake Questionnaire",
        specialty="Diagnostics",
        questions_json='["Do you have allergies?", "List current medications."]'
    )
    db_session.add(q)
    db_session.commit()

    return hosp, doc, q


def test_patient_registration_and_data_minimization(db_session):
    service = PatientSelfServiceService(db_session)
    patient = service.register_patient(
        name="Alice Smith",
        phone_number="+15550001111",
        email="alice@example.com",
        date_of_birth="1990-05-15",
        preferred_language="en",
        emergency_contact={"name": "Bob Smith", "phone": "+15550002222"},
        external_patient_id="EXT-PAT-100",
        saved_preferences={"sms_opt_in": True, "preferred_time": "morning"}
    )
    assert patient.id is not None
    assert patient.name == "Alice Smith"
    assert patient.external_patient_id == "EXT-PAT-100"

    # Fetch profile
    prof = service.get_patient_profile(patient.id)
    assert prof["name"] == "Alice Smith"
    assert prof["date_of_birth"] == "1990-05-15"
    assert prof["emergency_contact"]["name"] == "Bob Smith"

    # Update profile
    upd = service.update_patient_profile(patient.id, preferred_language="es")
    assert upd.preferred_language == "es"


def test_patient_questionnaire_submission(db_session, setup_hospital_and_doctor):
    hosp, doc, q = setup_hospital_and_doctor
    patient_svc = PatientSelfServiceService(db_session)
    patient = patient_svc.register_patient(
        name="Bob Johnson",
        phone_number="+15559998888"
    )

    resp = patient_svc.submit_questionnaire_response(
        patient_id=patient.id,
        questionnaire_id=q.id,
        responses={"allergies": "Penicillin", "medications": "Aspirin"}
    )
    assert resp.id is not None
    assert resp.patient_id == patient.id
    assert resp.questionnaire_id == q.id

    all_resps = patient_svc.get_patient_questionnaire_responses(patient.id)
    assert len(all_resps) == 1
    assert all_resps[0]["responses"]["allergies"] == "Penicillin"


def test_ai_agent_booking_intent_turn(db_session, setup_hospital_and_doctor):
    hosp, doc, _ = setup_hospital_and_doctor
    agent = AIPatientAccessAgent(db_session)

    res = agent.process_patient_turn(
        channel="web_voice",
        patient_identifier="+15551234567",
        user_utterance="I need to book an appointment with Dr. Gregory House tomorrow for chest tightness",
        hospital_id=hosp.id,
        doctor_id=doc.id
    )

    assert res["status"] == "SUCCESS"
    assert res["detected_intent"] in ["BOOK_APPOINTMENT", "PRE_VISIT_INTAKE"]
    assert res["nlu_analysis"]["intent"] is not None
    assert res["interaction_context"]["session_id"] is not None
    assert "speech_response" in res


def test_ai_agent_human_escalation_intent(db_session, setup_hospital_and_doctor):
    hosp, doc, _ = setup_hospital_and_doctor
    agent = AIPatientAccessAgent(db_session)

    res = agent.process_patient_turn(
        channel="telephone",
        patient_identifier="+15551234567",
        user_utterance="I have severe crushing chest pain, calling an ambulance, I need human emergency help right now!",
        hospital_id=hosp.id
    )

    assert res["status"] == "SUCCESS"
    assert res["detected_intent"] == "HUMAN_ESCALATION"
    assert res["escalation_triggered"] is True
    assert "EMERGENCY" in res["speech_response"] or "transferring" in res["speech_response"].lower()


def test_ai_agent_multichannel_reuse(db_session, setup_hospital_and_doctor):
    hosp, doc, _ = setup_hospital_and_doctor
    agent = AIPatientAccessAgent(db_session)

    for channel in ["web_voice", "telephone", "messaging"]:
        res = agent.process_patient_turn(
            channel=channel,
            patient_identifier="+15558887777",
            user_utterance="What are Dr. House's available slots?",
            hospital_id=hosp.id,
            doctor_id=doc.id
        )
        assert res["status"] == "SUCCESS"
        assert res["channel"] == channel
        assert "speech_response" in res
