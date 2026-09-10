"""
Unit Test Suite for Section 5.20 EHR / Healthcare System Integration.

Tests:
1. 12 Controlled Operations (patient_lookup, provider_lookup, facility_lookup, calendar_lookup, availability_retrieval, etc.)
2. Core 12-Step Integration Sequence (Validate Patient -> Resolve External -> Map -> Create/Update -> Verify -> Sync)
3. Bi-directional cross-system identifier mappings (Internal ↔ External)
4. Dynamic connector factory instantiation (Mock, FHIR_R4, Epic, Cerner)
5. Platform state synchronization and authoritative verification
"""

import pytest
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, Doctor, PatientProfile, Appointment, AppointmentStatus, EHRMapping
from app.ehr.adapters import EHRConnectorFactory, BaseEHRAdapter, MockEHRAdapter, FHIRR4Adapter, EpicConnectorAdapter, CernerConnectorAdapter
from app.ehr.integration_layer import EHRIntegrationService, CoreIntegrationSequenceResult


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def setup_ehr_test_data(db_session):
    hosp = Hospital(name="St. Jude Medical Center", code="STJUDE", is_active=True)
    db_session.add(hosp)
    db_session.commit()

    doc = Doctor(hospital_id=hosp.id, name="Dr. Gregory House", specialty="Diagnostics", is_active=True)
    db_session.add(doc)
    db_session.commit()

    patient = PatientProfile(phone_number="+15559876543", full_name="John Doe")
    db_session.add(patient)
    db_session.commit()

    appt = Appointment(
        hospital_id=hosp.id,
        doctor_id=doc.id,
        patient_id=patient.id,
        patient_name="John Doe",
        patient_phone="+15559876543",
        start_datetime=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=3, hours=10),
        end_datetime=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=3, hours=11),
        status=AppointmentStatus.PENDING_EHR_VERIFICATION
    )
    db_session.add(appt)
    db_session.commit()

    return hosp, doc, patient, appt


def test_12_controlled_ehr_operations():
    connector = EHRConnectorFactory.get_connector("MOCK")

    # 1. Patient Lookup
    pat_res = connector.patient_lookup("+15559876543", "John Doe")
    assert pat_res["found"] is True

    # 2. Patient Identity Resolution
    pat_id_res = connector.patient_identity_resolution("P-101")
    assert pat_id_res["resolved"] is True

    # 3. Provider Lookup
    prov_res = connector.provider_lookup("Diagnostics")
    assert prov_res["found"] is True

    # 4. Facility Lookup
    fac_res = connector.facility_lookup("STJUDE")
    assert fac_res["found"] is True

    # 5. Calendar Lookup
    cal_res = connector.calendar_lookup("EXT-DOC-MOCK-1")
    assert cal_res["found"] is True

    # 6. Availability Retrieval
    avail_res = connector.availability_retrieval("EXT-DOC-MOCK-1", "2026-09-15")
    assert len(avail_res["available_slots"]) == 3

    # 7. Appointment Creation
    now_dt = datetime.now(timezone.utc).replace(tzinfo=None)
    create_res = connector.create_appointment("PAT-1", "DOC-1", now_dt, 30)
    assert create_res.is_confirmed is True

    # 8. Appointment Update
    upd_res = connector.update_appointment(create_res.external_appointment_id, {"note": "Follow up"})
    assert upd_res.is_confirmed is True

    # 9. Appointment Rescheduling
    resched_res = connector.reschedule_appointment(create_res.external_appointment_id, now_dt + timedelta(days=1))
    assert resched_res.is_confirmed is True

    # 10. Appointment Cancellation
    cancel_res = connector.cancel_appointment(create_res.external_appointment_id, "Patient request")
    assert cancel_res.is_confirmed is True

    # 11. Appointment Retrieval
    get_res = connector.get_appointment(create_res.external_appointment_id)
    assert get_res["status"] == "booked"

    # 12. Appointment Status Verification
    ver_res = connector.verify_appointment_status(create_res.external_appointment_id)
    assert ver_res.is_confirmed is True


def test_ehr_connector_factory():
    epic = EHRConnectorFactory.get_connector("EPIC")
    assert isinstance(epic, EpicConnectorAdapter)

    cerner = EHRConnectorFactory.get_connector("CERNER")
    assert isinstance(cerner, CernerConnectorAdapter)

    fhir = EHRConnectorFactory.get_connector("FHIR_R4")
    assert isinstance(fhir, FHIRR4Adapter)

    mock = EHRConnectorFactory.get_connector("UNKNOWN")
    assert isinstance(mock, MockEHRAdapter)


def test_bi_directional_id_mapping(db_session, setup_ehr_test_data):
    hosp, doc, patient, appt = setup_ehr_test_data
    svc = EHRIntegrationService(db_session)

    # Resolve / Provision External Patient ID
    ext_pat_id = svc.resolve_external_id(hosp.id, "PATIENT", patient.id)
    assert ext_pat_id.startswith("EXT-PAT-")

    # Reverse Lookup Internal ID from External ID
    int_id = svc.resolve_internal_id(hosp.id, "PATIENT", ext_pat_id)
    assert int_id == patient.id


def test_core_12_step_integration_sequence_execution(db_session, setup_ehr_test_data):
    hosp, doc, patient, appt = setup_ehr_test_data
    svc = EHRIntegrationService(db_session)

    # Execute 12-Step Integration Sequence
    res: CoreIntegrationSequenceResult = svc.execute_core_integration_sequence(appt.id)
    
    assert res.is_successful is True
    assert len(res.steps) == 12
    assert res.steps[0].step_name == "Validate Patient"
    assert res.steps[1].step_name == "Resolve External Patient"
    assert res.steps[11].step_name == "Synchronize Platform State"

    # Verify Platform State Synchronization
    db_session.refresh(appt)
    assert appt.status == AppointmentStatus.SCHEDULED
    assert appt.is_ehr_verified is True
    assert appt.external_appointment_id is not None
