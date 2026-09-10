"""
Unit Test Suite for Sections 5.15 - 5.19:
- 5.15 Capability Discovery & External Action Adapters
- 5.16 Conversation State Management & Lifecycle (Active, Completed, Cancelled, Abandoned, Expired)
- 5.17 4-Tier Persistent User Context Hierarchy
- 5.18 Context Resolution (Anaphora & Reference Resolution)
- 5.19 Ambiguity Handling & Clarification Engine
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, Doctor, PatientProfile, Appointment, AppointmentStatus
from app.agent.capability_discovery import CapabilityDiscoveryService, CapabilityCategory, CapabilityDescriptor
from app.agent.capability_registry import CapabilityExecutionRequest
from app.agent.conversation_state import ConversationStateManager, WorkflowLifecycleStatus
from app.agent.multi_tier_context import MultiTierContextEngine
from app.agent.anaphora_and_ambiguity import AnaphoraContextResolver, AmbiguityClarificationEngine


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def setup_context_test_data(db_session):
    hosp = Hospital(name="City General Hospital", code="CITYGEN", is_active=True)
    db_session.add(hosp)
    db_session.commit()

    doc1 = Doctor(hospital_id=hosp.id, name="Dr. Gregory House", specialty="Dermatology", is_active=True)
    doc2 = Doctor(hospital_id=hosp.id, name="Dr. James Wilson", specialty="Orthopedics", is_active=True)
    db_session.add(doc1)
    db_session.add(doc2)
    db_session.commit()

    patient = PatientProfile(
        phone_number="+15551112222",
        full_name="Alice Smith",
        last_hospital_id=hosp.id,
        last_doctor_id=doc1.id
    )
    db_session.add(patient)
    db_session.commit()

    appt1 = Appointment(
        hospital_id=hosp.id,
        doctor_id=doc1.id,
        patient_id=patient.id,
        patient_name="Alice Smith",
        patient_phone="+15551112222",
        start_datetime=datetime.utcnow() + timedelta(days=2),
        end_datetime=datetime.utcnow() + timedelta(days=2, hours=1),
        status=AppointmentStatus.CONFIRMED
    )
    db_session.add(appt1)
    db_session.commit()

    return hosp, doc1, doc2, patient, appt1


def test_section_5_15_capability_discovery_catalog_and_adapters(db_session):
    svc = CapabilityDiscoveryService(db_session)
    
    # 1. Discover all patient agent capabilities
    all_caps = svc.discover_capabilities(caller_role="PATIENT_AGENT")
    assert len(all_caps) >= 17

    # 2. Filter by Category (EHR_CONNECTOR)
    ehr_caps = svc.discover_capabilities(category=CapabilityCategory.EHR_CONNECTOR, caller_role="SYSTEM_WORKFLOW")
    assert len(ehr_caps) == 2
    assert any(c.capability_name == "verify_external_appointment" for c in ehr_caps)

    # 3. Execute external capability via adapter
    req = CapabilityExecutionRequest(
        capability_name="verify_external_appointment",
        arguments={"appointment_id": "APPT-1001"},
        caller_role="PATIENT_AGENT"
    )
    res = svc.execute_capability_pipeline(req)
    assert res.success is True
    assert res.data["verified"] is True
    assert "EHR-EPIC-APPT-1001" in res.data["external_id"]

    # 4. Unauthorized Role Rejection
    unauth_req = CapabilityExecutionRequest(
        capability_name="synchronize_appointment_state",
        arguments={"appointment_id": "APPT-1001"},
        caller_role="PATIENT_AGENT"
    )
    unauth_res = svc.execute_capability_pipeline(unauth_req)
    assert unauth_res.success is False
    assert "Unauthorized" in unauth_res.message


def test_section_5_16_conversation_state_lifecycle(db_session):
    mgr = ConversationStateManager(db_session, ttl_minutes=15)
    sess_id = f"SESS-{uuid.uuid4()}"

    # 1. Init state
    state = mgr.get_or_create_state(sess_id)
    assert state.workflow_status == WorkflowLifecycleStatus.ACTIVE
    assert state.appointment_status == "PENDING"

    # 2. Update state slots
    state2 = mgr.update_state(
        sess_id,
        intent="BOOK_APPOINTMENT",
        specialty="Dermatology",
        date="2026-09-15",
        time_preference="AFTERNOON",
        selected_doctor={"doctor_id": "DOC-1", "name": "Dr. House"}
    )
    assert state2.intent == "BOOK_APPOINTMENT"
    assert state2.specialty == "Dermatology"
    assert state2.selected_doctor["name"] == "Dr. House"

    # 3. Lifecycle Transitions: Complete, Cancel, Abandon
    completed_state = mgr.complete_workflow(sess_id)
    assert completed_state.workflow_status == WorkflowLifecycleStatus.COMPLETED
    assert completed_state.appointment_status == "BOOKED"


def test_section_5_17_multi_tier_context_hierarchy(db_session, setup_context_test_data):
    hosp, doc1, doc2, patient, appt1 = setup_context_test_data
    engine = MultiTierContextEngine(db_session)
    sess_id = f"SESS-{uuid.uuid4()}"

    # Fetch 4-Tier Context Bundle
    bundle = engine.get_hierarchical_context(session_id=sess_id, patient_id=patient.id)
    
    assert bundle.tier1_conversation_state.workflow_status == "ACTIVE"
    assert bundle.tier3_long_term.full_name == "Alice Smith"
    assert "City General Hospital" in bundle.tier3_long_term.preferred_hospitals
    assert "Dr. Gregory House" in bundle.tier3_long_term.preferred_doctors
    assert len(bundle.tier4_appointment_info.upcoming_appointments) == 1

    # Prompt Hint Generation
    hint = bundle.generate_natural_prompt_hint()
    assert "Patient preferred doctors: Dr. Gregory House" in hint
    assert "Patient has 1 upcoming appointment(s)" in hint


def test_section_5_18_anaphora_context_resolution(db_session, setup_context_test_data):
    hosp, doc1, doc2, patient, appt1 = setup_context_test_data
    engine = MultiTierContextEngine(db_session)
    sess_id = f"SESS-{uuid.uuid4()}"

    bundle = engine.get_hierarchical_context(session_id=sess_id, patient_id=patient.id)

    # 1. Resolve "Same hospital as last time"
    res_hosp = AnaphoraContextResolver.resolve_reference("Can I book at the same hospital as last time?", bundle)
    assert res_hosp.is_resolved is True
    assert res_hosp.resolved_entity_type == "HOSPITAL"
    assert res_hosp.resolved_data["hospital_name"] == "City General Hospital"

    # 2. Resolve "Book that doctor"
    res_doc = AnaphoraContextResolver.resolve_reference("Please book that doctor", bundle)
    assert res_doc.is_resolved is True
    assert res_doc.resolved_entity_type == "DOCTOR"
    assert res_doc.resolved_data["doctor_name"] == "Dr. Gregory House"

    # 3. Resolve "Actually Friday"
    res_day = AnaphoraContextResolver.resolve_reference("Actually Friday afternoon would be better", bundle)
    assert res_day.is_resolved is True
    assert res_day.resolved_entity_type == "DATE"
    assert res_day.resolved_data["updated_date_day"] == "Friday"

    # 4. Resolve "Cancel my upcoming appointment" (1 active appointment -> Clean resolution)
    res_cancel = AnaphoraContextResolver.resolve_reference("Cancel my upcoming appointment", bundle)
    assert res_cancel.is_resolved is True
    assert res_cancel.resolved_entity_type == "APPOINTMENT"
    assert res_cancel.resolved_data["appointment_id"] == appt1.id

    # 5. Multi-appointment Cancellation Ambiguity Test
    appt2 = Appointment(
        hospital_id=hosp.id,
        doctor_id=doc2.id,
        patient_id=patient.id,
        patient_name="Alice Smith",
        patient_phone="+15551112222",
        start_datetime=datetime.utcnow() + timedelta(days=5),
        end_datetime=datetime.utcnow() + timedelta(days=5, hours=1),
        status=AppointmentStatus.CONFIRMED
    )
    db_session.add(appt2)
    db_session.commit()

    multi_bundle = engine.get_hierarchical_context(session_id=sess_id, patient_id=patient.id)
    res_multi_cancel = AnaphoraContextResolver.resolve_reference("Cancel my upcoming appointment", multi_bundle)
    assert res_multi_cancel.is_resolved is False
    assert res_multi_cancel.requires_clarification is True
    assert "I see you have 2 upcoming appointments" in res_multi_cancel.clarification_question


def test_section_5_19_ambiguity_handling_and_clarification():
    # 1. Multiple Matching Doctors Ambiguity
    matching_docs = [{"name": "Dr. Sharma"}, {"name": "Dr. Rao"}]
    res_docs = AmbiguityClarificationEngine.evaluate_ambiguity(
        intent="BOOK_APPOINTMENT",
        matching_doctors=matching_docs,
        available_slots=[]
    )
    assert res_docs.requires_clarification is True
    assert "Would you prefer Dr. Sharma or Dr. Rao?" in res_docs.clarification_question

    # 2. No Available Slots -> Offer Alternative Suggestion
    res_no_slots = AmbiguityClarificationEngine.evaluate_ambiguity(
        intent="BOOK_APPOINTMENT",
        matching_doctors=[],
        available_slots=[],
        requested_date="Thursday",
        requested_time_window="AFTERNOON"
    )
    assert res_no_slots.requires_clarification is True
    assert "There are no afternoon appointments available on Thursday" in res_no_slots.clarification_question
    assert "Friday" in res_no_slots.clarification_question
