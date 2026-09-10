"""
Unit tests for Section 1.5: EHR Integration Layer, Identity Mappings, and Authoritative Verification.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import (
    Base, Hospital, Doctor, Appointment, AppointmentStatus, EHRIntegrationConfig, EHRAdapterType, EHRSyncLog, EHRMapping
)
from app.ehr.adapters import MockEHRAdapter, FHIRR4Adapter
from app.ehr.integration_layer import EHRIntegrationService
from app.agent.actions import ActionExecutor
from app.schemas.actions import CreateAppointmentInput


def test_fhir_r4_adapter_payload():
    adapter = FHIRR4Adapter(base_url="https://fhir.hospital.org/r4")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    res = adapter.create_appointment(
        ehr_patient_id="pat-100",
        ehr_practitioner_id="prac-200",
        start_datetime=now,
        duration_minutes=30
    )
    assert res.is_confirmed is True
    assert "FHIR-APPT-" in res.external_appointment_id
    assert res.raw_response["resourceType"] == "Appointment"


def test_authoritative_ehr_verification_flow():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Seed data
    hosp = Hospital(id="hosp-1", name="St. Jude Hospital", code="SJH")
    doc = Doctor(id="doc-1", hospital_id="hosp-1", name="Dr. Alice", specialty="Cardiology")
    config = EHRIntegrationConfig(hospital_id="hosp-1", adapter_type=EHRAdapterType.MOCK_EHR)
    db.add_all([hosp, doc, config])
    db.commit()

    executor = ActionExecutor(db)
    now = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2)

    # Execute booking
    create_res = executor.create_appointment(CreateAppointmentInput(
        session_id="s-999",
        patient_id="p-888",
        hospital_id="hosp-1",
        doctor_id="doc-1",
        start_datetime=now,
        patient_name="Sarah Connor",
        patient_phone="+1-555-0199"
    ))

    assert create_res.success is True
    assert "verified with EHR" in create_res.message
    assert create_res.appointment_id is not None

    # Verify Database state
    appt = db.query(Appointment).filter(Appointment.id == create_res.appointment_id).first()
    assert appt.status == AppointmentStatus.SCHEDULED
    assert appt.is_ehr_verified is True
    assert appt.external_appointment_id.startswith("EHR-APPT-")

    # Verify EHRSyncLog creation
    sync_log = db.query(EHRSyncLog).filter(EHRSyncLog.appointment_id == create_res.appointment_id).first()
    assert sync_log is not None
    assert sync_log.sync_status == "VERIFIED_SUCCESS"

    # Verify EHRMapping creation
    patient_map = db.query(EHRMapping).filter(EHRMapping.internal_id == "+1-555-0199").first()
    assert patient_map is not None
    assert patient_map.entity_type == "PATIENT"
