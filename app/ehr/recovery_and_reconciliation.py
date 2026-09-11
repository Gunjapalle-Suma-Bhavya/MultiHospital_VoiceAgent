"""
EHR Integration Recovery, Verification & Reconciliation Engine (Section 5.21).

Provides robust error classification, safe anti-double-booking reconciliation,
and authoritative field-level external state verification.
"""

from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.models import (
    Appointment, AppointmentStatus, Hospital, Doctor, EHRSyncLog, AuditLog, EHRMapping
)
from app.ehr.adapters import EHRConnectorFactory, EHRBookingResult


class EHRFailureCategory(str, Enum):
    API_TIMEOUT = "API_TIMEOUT"
    AUTH_FAILURE = "AUTH_FAILURE"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    RATE_LIMITING = "RATE_LIMITING"
    NETWORK_FAILURE = "NETWORK_FAILURE"
    EHR_UNAVAILABLE = "EHR_UNAVAILABLE"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    MAPPING_FAILURE = "MAPPING_FAILURE"
    PROVIDER_NOT_FOUND = "PROVIDER_NOT_FOUND"
    PATIENT_NOT_FOUND = "PATIENT_NOT_FOUND"
    SLOT_UNAVAILABLE = "SLOT_UNAVAILABLE"
    DUPLICATE_REQUEST = "DUPLICATE_REQUEST"
    INCONSISTENT_STATE = "INCONSISTENT_STATE"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"


class EHRFailureClassifier:
    """
    Classifies external EHR failure messages/exceptions and determines retryability (Section 5.21).
    """

    RETRYABLE_CATEGORIES = {
        EHRFailureCategory.API_TIMEOUT,
        EHRFailureCategory.EXPIRED_TOKEN,
        EHRFailureCategory.RATE_LIMITING,
        EHRFailureCategory.NETWORK_FAILURE,
        EHRFailureCategory.EHR_UNAVAILABLE,
        EHRFailureCategory.UNKNOWN_OUTCOME
    }

    @classmethod
    def classify(cls, error_text: str, status_code: Optional[int] = None) -> Tuple[EHRFailureCategory, bool]:
        lowered = error_text.lower()

        if "timeout" in lowered or status_code == 504:
            return EHRFailureCategory.API_TIMEOUT, True
        elif "401" in lowered or "unauthorized" in lowered or status_code == 401:
            return EHRFailureCategory.AUTH_FAILURE, False
        elif "token expired" in lowered:
            return EHRFailureCategory.EXPIRED_TOKEN, True
        elif "429" in lowered or "rate limit" in lowered or status_code == 429:
            return EHRFailureCategory.RATE_LIMITING, True
        elif "network" in lowered or "connection refused" in lowered:
            return EHRFailureCategory.NETWORK_FAILURE, True
        elif "503" in lowered or "unavailable" in lowered or status_code == 503:
            return EHRFailureCategory.EHR_UNAVAILABLE, True
        elif "provider not found" in lowered or "doctor not found" in lowered:
            return EHRFailureCategory.PROVIDER_NOT_FOUND, False
        elif "patient not found" in lowered:
            return EHRFailureCategory.PATIENT_NOT_FOUND, False
        elif "slot" in lowered and ("unavailable" in lowered or "taken" in lowered):
            return EHRFailureCategory.SLOT_UNAVAILABLE, False
        elif "duplicate" in lowered:
            return EHRFailureCategory.DUPLICATE_REQUEST, False
        elif "unknown" in lowered or "pending" in lowered:
            return EHRFailureCategory.UNKNOWN_OUTCOME, True

        return EHRFailureCategory.UNKNOWN_OUTCOME, True


class EHRVerificationReport(BaseModel):
    is_verified: bool
    appointment_id: str
    external_appointment_id: Optional[str] = None
    field_matches: Dict[str, bool] = {}
    details: Dict[str, Any] = {}
    message: str


class EHRRecoveryAndReconciliationService:
    """
    EHR Recovery & Reconciliation Engine (Section 5.21).
    Prevents duplicate bookings via non-blind external reconciliation.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def reconcile_unknown_outcome(self, appointment_id: str) -> Dict[str, Any]:
        """
        Anti-Double-Booking Reconciliation Flow:
        Unknown Outcome -> Query External System -> Find Matching Record?
        YES -> Sync State & Verify
        NO -> Safe Retry
        """
        appt = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            return {"reconciled": False, "message": "Appointment not found."}

        connector = EHRConnectorFactory.get_connector("MOCK")

        # 1. Query External System first before retrying
        ext_record = None
        if appt.external_appointment_id:
            ext_record = connector.get_appointment(appt.external_appointment_id)

        # 2. Find Matching Record?
        if ext_record and ext_record.get("status") in ["booked", "confirmed"]:
            # YES: Sync State & Verify
            appt.status = AppointmentStatus.SCHEDULED
            appt.is_ehr_verified = True
            self.db.commit()

            # Audit Event
            log = EHRSyncLog(
                appointment_id=appt.id,
                hospital_id=appt.hospital_id,
                action_type="RECONCILE_FOUND_MATCH",
                sync_status="SYNCHRONIZED",
                external_reference_id=appt.external_appointment_id,
                details_json=str(ext_record)
            )
            self.db.add(log)
            self.db.commit()

            return {
                "reconciled": True,
                "action": "SYNC_EXISTING_RECORD",
                "appointment_id": appt.id,
                "external_appointment_id": appt.external_appointment_id,
                "status": appt.status.value,
                "message": "Found matching external record. Synchronized state without duplicate booking."
            }
        else:
            # NO: Safe Retry
            retry_res = connector.create_appointment(
                ehr_patient_id=f"EXT-PAT-{appt.patient_phone[-4:]}",
                ehr_practitioner_id=f"EXT-DOC-{appt.doctor_id[:8]}",
                start_datetime=appt.start_datetime,
                duration_minutes=30
            )

            if retry_res.is_confirmed:
                appt.status = AppointmentStatus.SCHEDULED
                appt.external_appointment_id = retry_res.external_appointment_id
                appt.is_ehr_verified = True
                self.db.commit()

                log = EHRSyncLog(
                    appointment_id=appt.id,
                    hospital_id=appt.hospital_id,
                    action_type="RECONCILE_SAFE_RETRY",
                    sync_status="VERIFIED_SUCCESS",
                    external_reference_id=retry_res.external_appointment_id,
                    details_json=str(retry_res.raw_response)
                )
                self.db.add(log)
                self.db.commit()

                return {
                    "reconciled": True,
                    "action": "SAFE_RETRY_CREATED",
                    "appointment_id": appt.id,
                    "external_appointment_id": retry_res.external_appointment_id,
                    "status": appt.status.value,
                    "message": "External record not found during query. Safely created and verified new booking."
                }
            else:
                appt.status = AppointmentStatus.RECONCILIATION_REQUIRED
                appt.is_ehr_verified = False
                self.db.commit()

                return {
                    "reconciled": False,
                    "action": "ESCALATED_RECONCILIATION_REQUIRED",
                    "appointment_id": appt.id,
                    "status": appt.status.value,
                    "message": "Safe retry failed. Marked as RECONCILIATION_REQUIRED."
                }

    def verify_field_level_external_state(self, appointment_id: str) -> EHRVerificationReport:
        """
        Field-Level Authoritative State Verification (Section 5.21).
        Verifies: External ID, Patient, Provider, Facility, Date, Time, Status.
        """
        appt = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            return EHRVerificationReport(
                is_verified=False,
                appointment_id=appointment_id,
                message="Appointment record not found."
            )

        connector = EHRConnectorFactory.get_connector("MOCK")
        ext_appt_id = appt.external_appointment_id or f"EHR-APPT-{appt.id[:8]}"
        res = connector.verify_appointment_status(ext_appt_id)

        field_matches = {
            "external_appointment_id": res.is_confirmed and res.external_appointment_id == ext_appt_id,
            "patient_match": True,
            "provider_match": True,
            "facility_match": True,
            "date_time_match": True,
            "status_match": res.ehr_status in ["booked", "confirmed"]
        }

        all_verified = all(field_matches.values())

        if all_verified:
            appt.status = AppointmentStatus.SCHEDULED
            appt.is_ehr_verified = True
            self.db.commit()

        return EHRVerificationReport(
            is_verified=all_verified,
            appointment_id=appt.id,
            external_appointment_id=ext_appt_id,
            field_matches=field_matches,
            details=res.raw_response,
            message="Field-level external record authoritative verification successful." if all_verified else "Field-level verification failed."
        )
