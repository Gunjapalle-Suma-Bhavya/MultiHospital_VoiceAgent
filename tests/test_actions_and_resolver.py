"""
Unit tests for Context-Aware Reference Resolver (1.3) and Action-Oriented AI capabilities (1.4).
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, Doctor, AppointmentStatus
from app.agent.resolver import ContextResolver
from app.agent.actions import ActionExecutor
from app.schemas.actions import (
    SearchHospitalsInput, SearchDoctorsInput, CreateAppointmentInput, CancelAppointmentInput
)


def test_resolver_same_doctor_reference():
    res = ContextResolver.resolve_doctor_reference(
        "Book me with the same doctor as last time",
        last_doctor_name="Dr. Sharma",
        last_doctor_id="doc-123"
    )
    assert res.is_resolved is True
    assert res.resolved_data["doctor_name"] == "Dr. Sharma"


def test_resolver_ambiguous_cancellation_triggers_clarification():
    appointments = [
        {"id": "a-1", "doctor_name": "Dr. Sharma", "start_datetime": "2026-09-12 10:00"},
        {"id": "a-2", "doctor_name": "Dr. Gupta", "start_datetime": "2026-09-15 14:00"}
    ]
    res = ContextResolver.resolve_appointment_cancellation("Cancel my upcoming appointment", appointments)
    assert res.is_resolved is False
    assert res.requires_clarification is True
    assert "multiple upcoming appointments" in res.clarification_question


def test_action_executor_flow():
    # Setup in-memory sqlite DB for test
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Seed data
    hosp = Hospital(id="hosp-1", name="City General Hospital", code="CGH", timezone="UTC")
    doc = Doctor(id="doc-1", hospital_id="hosp-1", name="Dr. Sharma", specialty="Dermatology")
    db.add_all([hosp, doc])
    db.commit()

    executor = ActionExecutor(db)

    # 1. Search Hospitals
    hosp_res = executor.search_hospitals(SearchHospitalsInput(session_id="s-1", patient_id="p-1", query="City"))
    assert hosp_res.success is True
    assert len(hosp_res.hospitals) == 1
    assert hosp_res.hospitals[0].name == "City General Hospital"

    # 2. Search Doctors
    doc_res = executor.search_doctors(SearchDoctorsInput(session_id="s-1", patient_id="p-1", specialty="Dermatology"))
    assert doc_res.success is True
    assert len(doc_res.doctors) == 1

    # 3. Create Appointment
    now = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)
    create_res = executor.create_appointment(CreateAppointmentInput(
        session_id="s-1",
        patient_id="p-1",
        hospital_id="hosp-1",
        doctor_id="doc-1",
        start_datetime=now,
        patient_name="John Doe",
        patient_phone="+1234567890"
    ))
    assert create_res.success is True
    assert create_res.appointment_id is not None

    # 4. Cancel Appointment
    cancel_res = executor.cancel_appointment(CancelAppointmentInput(
        session_id="s-1",
        patient_id="p-1",
        appointment_id=create_res.appointment_id
    ))
    assert cancel_res.success is True
    assert cancel_res.action_type == "CANCEL_APPOINTMENT"
