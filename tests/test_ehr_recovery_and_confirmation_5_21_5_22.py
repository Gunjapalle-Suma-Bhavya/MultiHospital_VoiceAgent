"""
Unit Test Suite for Sections 5.21 & 5.22:
- 5.21 EHR Recovery, Verification & Anti-Double-Booking Reconciliation
- 5.22 Authoritative Appointment Confirmation & Verification Enforcement
"""

import pytest
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, Doctor, PatientProfile, Appointment, AppointmentStatus
from app.ehr.recovery_and_reconciliation import (
    EHRFailureClassifier, EHRFailureCategory, EHRRecoveryAndReconciliationService
)
from app.appointments.confirmation_service import AppointmentConfirmationService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def setup_recovery_test_data(db_session):
    hosp = Hospital(name="City Hospital", code="CITYHOSP", is_active=True)
    db_session.add(hosp)
    db_session.commit()

    doc = Doctor(hospital_id=hosp.id, name="Dr. Rao", specialty="Cardiology", is_active=True)
    db_session.add(doc)
    db_session.commit()

    patient = PatientProfile(phone_number="+15554443333", full_name="Bob Miller")
    db_session.add(patient)
    db_session.commit()

    target_dt = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2, hours=16, minutes=30)
    appt = Appointment(
        hospital_id=hosp.id,
        doctor_id=doc.id,
        patient_id=patient.id,
        patient_name="Bob Miller",
        patient_phone="+15554443333",
        start_datetime=target_dt,
        end_datetime=target_dt + timedelta(minutes=30),
        status=AppointmentStatus.PENDING_EHR_VERIFICATION,
        is_ehr_verified=False
    )
    db_session.add(appt)
    db_session.commit()

    return hosp, doc, patient, appt


def test_section_5_21_ehr_failure_classification_and_retryability():
    # Timeout -> Retryable
    cat, retry = EHRFailureClassifier.classify("Gateway Timeout during FHIR POST", status_code=504)
    assert cat == EHRFailureCategory.API_TIMEOUT
    assert retry is True

    # Auth Failure -> Non-retryable
    cat2, retry2 = EHRFailureClassifier.classify("401 Unauthorized token invalid", status_code=401)
    assert cat2 == EHRFailureCategory.AUTH_FAILURE
    assert retry2 is False

    # Provider Not Found -> Non-retryable
    cat3, retry3 = EHRFailureClassifier.classify("Provider not found in EHR registry")
    assert cat3 == EHRFailureCategory.PROVIDER_NOT_FOUND
    assert retry3 is False


def test_section_5_21_anti_double_booking_reconciliation(db_session, setup_recovery_test_data):
    hosp, doc, patient, appt = setup_recovery_test_data
    svc = EHRRecoveryAndReconciliationService(db_session)

    # 1. Execute Reconciliation
    res = svc.reconcile_unknown_outcome(appt.id)
    assert res["reconciled"] is True
    assert appt.status == AppointmentStatus.SCHEDULED
    assert appt.is_ehr_verified is True


def test_section_5_21_authoritative_field_level_verification(db_session, setup_recovery_test_data):
    hosp, doc, patient, appt = setup_recovery_test_data
    svc = EHRRecoveryAndReconciliationService(db_session)

    report = svc.verify_field_level_external_state(appt.id)
    assert report.is_verified is True
    assert report.field_matches["external_appointment_id"] is True
    assert report.field_matches["status_match"] is True


def test_section_5_22_verified_appointment_confirmation_rule(db_session, setup_recovery_test_data):
    hosp, doc, patient, appt = setup_recovery_test_data
    confirm_svc = AppointmentConfirmationService(db_session)

    # 1. Unverified State -> Returns Pending Text
    unver_details = confirm_svc.get_appointment_confirmation(appt.id)
    assert unver_details.is_verified is False
    assert "pending verification with the hospital system" in unver_details.spoken_confirmation_text
    assert "is confirmed for" not in unver_details.spoken_confirmation_text

    # 2. Authoritatively Verified State -> Returns Confirmed Spoken Text
    appt.status = AppointmentStatus.SCHEDULED
    appt.is_ehr_verified = True
    appt.external_appointment_id = "EHR-APPT-VERIFIED-101"
    db_session.commit()

    ver_details = confirm_svc.get_appointment_confirmation(appt.id)
    assert ver_details.is_verified is True
    assert "Your appointment with Dr. Rao at City Hospital is confirmed for" in ver_details.spoken_confirmation_text
    assert ver_details.external_appointment_id == "EHR-APPT-VERIFIED-101"
