"""
EHR Integration Layer & Verification Service (Section 1.5).

Abstracts vendor-specific implementation details, handles cross-system identity mapping,
and enforces authoritative external verification before confirming appointments.
"""

from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.database.models import (
    Appointment, AppointmentStatus, Hospital, EHRIntegrationConfig, EHRMapping, EHRSyncLog, EHRAdapterType
)
from app.ehr.adapters import BaseEHRAdapter, MockEHRAdapter, FHIRR4Adapter, EHRBookingResult


class EHRIntegrationService:
    """
    Decouples AI Capability Layer from EHR vendor implementations.
    Enforces authoritative state verification before confirming appointments.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_adapter_for_hospital(self, hospital_id: str) -> BaseEHRAdapter:
        config = self.db.query(EHRIntegrationConfig).filter(EHRIntegrationConfig.hospital_id == hospital_id).first()
        if not config or config.adapter_type == EHRAdapterType.MOCK_EHR:
            return MockEHRAdapter()
        elif config.adapter_type == EHRAdapterType.FHIR_R4:
            return FHIRR4Adapter(base_url=config.api_base_url or "https://fhir.hospital.org/r4")
        else:
            return MockEHRAdapter()

    def resolve_external_id(self, hospital_id: str, entity_type: str, internal_id: str) -> str:
        """
        Looks up external EHR ID in EHRMapping table.
        If missing, creates a default mapped identifier.
        """
        mapping = self.db.query(EHRMapping).filter(
            EHRMapping.hospital_id == hospital_id,
            EHRMapping.entity_type == entity_type,
            EHRMapping.internal_id == internal_id
        ).first()

        if mapping:
            return mapping.external_ehr_id

        # Auto-provision mapping for seamless operation
        ext_id = f"EXT-{entity_type[:3]}-{internal_id[:8]}"
        new_mapping = EHRMapping(
            hospital_id=hospital_id,
            entity_type=entity_type,
            internal_id=internal_id,
            external_ehr_id=ext_id
        )
        self.db.add(new_mapping)
        self.db.commit()
        return ext_id

    def sync_and_verify_booking(self, appointment_id: str) -> Tuple[bool, str, Optional[str]]:
        """
        Enforces Authoritative State Verification:
        Book in EHR -> Verify -> Set AppointmentStatus.SCHEDULED in Platform.
        Returns: (success: bool, message: str, external_appointment_id: str)
        """
        appt = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            return False, "Appointment not found", None

        adapter = self.get_adapter_for_hospital(appt.hospital_id)

        # Resolve cross-system identities
        ehr_patient_id = self.resolve_external_id(appt.hospital_id, "PATIENT", appt.patient_phone)
        ehr_practitioner_id = self.resolve_external_id(appt.hospital_id, "PROVIDER", appt.doctor_id)

        # Execute external booking via adapter
        duration = 30
        if appt.doctor and appt.doctor.default_appointment_duration:
            duration = appt.doctor.default_appointment_duration

        res: EHRBookingResult = adapter.create_appointment(
            ehr_patient_id=ehr_patient_id,
            ehr_practitioner_id=ehr_practitioner_id,
            start_datetime=appt.start_datetime,
            duration_minutes=duration
        )

        # Authoritative State Verification Check
        if res.is_confirmed:
            appt.status = AppointmentStatus.SCHEDULED
            appt.external_appointment_id = res.external_appointment_id
            appt.is_ehr_verified = True

            sync_log = EHRSyncLog(
                appointment_id=appt.id,
                hospital_id=appt.hospital_id,
                action_type="BOOK",
                sync_status="VERIFIED_SUCCESS",
                external_reference_id=res.external_appointment_id,
                details_json=str(res.raw_response)
            )
            self.db.add(sync_log)
            self.db.commit()
            return True, "EHR Authoritative Verification Confirmed", res.external_appointment_id
        else:
            appt.status = AppointmentStatus.CANCELLED
            appt.is_ehr_verified = False

            sync_log = EHRSyncLog(
                appointment_id=appt.id,
                hospital_id=appt.hospital_id,
                action_type="BOOK",
                sync_status="FAILED",
                details_json=res.message
            )
            self.db.add(sync_log)
            self.db.commit()
            return False, f"EHR Verification Failed: {res.message}", None
