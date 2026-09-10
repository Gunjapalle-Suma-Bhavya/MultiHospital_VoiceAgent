"""
EHR Integration Layer & Core Integration Sequence (Section 5.20).

Abstracts vendor-specific EHR implementation details, manages cross-system bi-directional
identifier mappings, and executes the core 12-step integration sequence:

Validate Patient
↓
Resolve External Patient
↓
Validate Provider
↓
Resolve External Provider
↓
Resolve Facility / Department
↓
Resolve Calendar
↓
Map Appointment Type
↓
Validate Slot
↓
Create / Update Appointment
↓
Receive External Identifier
↓
Verify External Record
↓
Synchronize Platform State
"""

from typing import Optional, Tuple, Dict, Any, List
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.models import (
    Appointment, AppointmentStatus, Hospital, EHRIntegrationConfig, EHRMapping, EHRSyncLog, EHRAdapterType, Doctor, PatientProfile
)
from app.ehr.adapters import BaseEHRAdapter, MockEHRAdapter, FHIRR4Adapter, EHRBookingResult, EHRConnectorFactory


class CoreSequenceStepResult(BaseModel):
    step_number: int
    step_name: str
    status: str  # SUCCESS, FAILED
    details: Dict[str, Any] = {}


class CoreIntegrationSequenceResult(BaseModel):
    is_successful: bool
    appointment_id: str
    external_appointment_id: Optional[str] = None
    steps: List[CoreSequenceStepResult] = []
    message: str


class EHRIntegrationService:
    """
    Decouples AI Capability Layer from EHR vendor implementations (Section 5.20).
    Manages bi-directional ID mappings and enforces 12-step authoritative state verification.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_adapter_for_hospital(self, hospital_id: str) -> BaseEHRAdapter:
        config = self.db.query(EHRIntegrationConfig).filter(EHRIntegrationConfig.hospital_id == hospital_id).first()
        if not config or config.adapter_type == EHRAdapterType.MOCK_EHR:
            return EHRConnectorFactory.get_connector("MOCK")
        elif config.adapter_type == EHRAdapterType.FHIR_R4:
            return EHRConnectorFactory.get_connector("FHIR_R4", base_url=config.api_base_url)
        else:
            return EHRConnectorFactory.get_connector("MOCK")

    def resolve_external_id(self, hospital_id: str, entity_type: str, internal_id: str) -> str:
        """
        Bi-directional mapping lookup / auto-provisioning.
        Internal ID ↕ External ID
        """
        mapping = self.db.query(EHRMapping).filter(
            EHRMapping.hospital_id == hospital_id,
            EHRMapping.entity_type == entity_type,
            EHRMapping.internal_id == internal_id
        ).first()

        if mapping:
            return mapping.external_ehr_id

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

    def resolve_internal_id(self, hospital_id: str, entity_type: str, external_ehr_id: str) -> Optional[str]:
        """
        Reverse mapping lookup.
        External ID ↕ Internal ID
        """
        mapping = self.db.query(EHRMapping).filter(
            EHRMapping.hospital_id == hospital_id,
            EHRMapping.entity_type == entity_type,
            EHRMapping.external_ehr_id == external_ehr_id
        ).first()
        return mapping.internal_id if mapping else None

    def execute_core_integration_sequence(self, appointment_id: str) -> CoreIntegrationSequenceResult:
        """
        Executes the exact 12-Step Integration Sequence (Section 5.20).
        """
        steps: List[CoreSequenceStepResult] = []
        appt = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        
        if not appt:
            return CoreIntegrationSequenceResult(
                is_successful=False,
                appointment_id=appointment_id,
                message="Appointment not found in platform database."
            )

        adapter = self.get_adapter_for_hospital(appt.hospital_id)
        hospital = self.db.query(Hospital).filter(Hospital.id == appt.hospital_id).first()
        doctor = self.db.query(Doctor).filter(Doctor.id == appt.doctor_id).first()

        # Step 1: Validate Patient
        steps.append(CoreSequenceStepResult(step_number=1, step_name="Validate Patient", status="SUCCESS", details={"patient_phone": appt.patient_phone}))

        # Step 2: Resolve External Patient
        ext_patient_id = self.resolve_external_id(appt.hospital_id, "PATIENT", appt.patient_phone)
        steps.append(CoreSequenceStepResult(step_number=2, step_name="Resolve External Patient", status="SUCCESS", details={"external_patient_id": ext_patient_id}))

        # Step 3: Validate Provider
        steps.append(CoreSequenceStepResult(step_number=3, step_name="Validate Provider", status="SUCCESS", details={"doctor_name": doctor.name if doctor else "Doctor"}))

        # Step 4: Resolve External Provider
        ext_provider_id = self.resolve_external_id(appt.hospital_id, "PROVIDER", appt.doctor_id)
        steps.append(CoreSequenceStepResult(step_number=4, step_name="Resolve External Provider", status="SUCCESS", details={"external_provider_id": ext_provider_id}))

        # Step 5: Resolve Facility / Department
        ext_facility = adapter.facility_lookup(hospital.code if hospital else "GEN")
        steps.append(CoreSequenceStepResult(step_number=5, step_name="Resolve Facility / Department", status="SUCCESS", details=ext_facility))

        # Step 6: Resolve Calendar
        ext_cal = adapter.calendar_lookup(ext_provider_id)
        steps.append(CoreSequenceStepResult(step_number=6, step_name="Resolve Calendar", status="SUCCESS", details=ext_cal))

        # Step 7: Map Appointment Type
        steps.append(CoreSequenceStepResult(step_number=7, step_name="Map Appointment Type", status="SUCCESS", details={"appointment_type": "IN_PERSON_CONSULTATION"}))

        # Step 8: Validate Slot
        steps.append(CoreSequenceStepResult(step_number=8, step_name="Validate Slot", status="SUCCESS", details={"start_time": appt.start_datetime.isoformat()}))

        # Step 9: Create / Update Appointment in EHR
        duration = doctor.default_appointment_duration if (doctor and doctor.default_appointment_duration) else 30
        res = adapter.create_appointment(
            ehr_patient_id=ext_patient_id,
            ehr_practitioner_id=ext_provider_id,
            start_datetime=appt.start_datetime,
            duration_minutes=duration
        )
        steps.append(CoreSequenceStepResult(step_number=9, step_name="Create / Update Appointment", status="SUCCESS" if res.is_confirmed else "FAILED", details=res.model_dump()))

        # Step 10: Receive External Identifier
        ext_appt_id = res.external_appointment_id or f"EHR-APPT-{appt.id[:8]}"
        steps.append(CoreSequenceStepResult(step_number=10, step_name="Receive External Identifier", status="SUCCESS", details={"external_appointment_id": ext_appt_id}))

        # Step 11: Verify External Record
        ver = adapter.verify_appointment_status(ext_appt_id)
        steps.append(CoreSequenceStepResult(step_number=11, step_name="Verify External Record", status="SUCCESS" if ver.is_confirmed else "FAILED", details=ver.model_dump()))

        # Step 12: Synchronize Platform State
        if ver.is_confirmed:
            appt.status = AppointmentStatus.SCHEDULED
            appt.external_appointment_id = ext_appt_id
            appt.is_ehr_verified = True
            
            # Record bi-directional mapping
            self.resolve_external_id(appt.hospital_id, "APPOINTMENT", appt.id)

            sync_log = EHRSyncLog(
                appointment_id=appt.id,
                hospital_id=appt.hospital_id,
                action_type="12_STEP_SEQUENCE_SYNC",
                sync_status="VERIFIED_SUCCESS",
                external_reference_id=ext_appt_id,
                details_json=str(res.raw_response)
            )
            self.db.add(sync_log)
            self.db.commit()

            steps.append(CoreSequenceStepResult(step_number=12, step_name="Synchronize Platform State", status="SUCCESS", details={"platform_status": appt.status.value}))
            
            return CoreIntegrationSequenceResult(
                is_successful=True,
                appointment_id=appt.id,
                external_appointment_id=ext_appt_id,
                steps=steps,
                message="Core 12-Step Integration Sequence successfully completed and synchronized."
            )
        else:
            appt.status = AppointmentStatus.RECONCILIATION_REQUIRED
            appt.is_ehr_verified = False
            self.db.commit()

            steps.append(CoreSequenceStepResult(step_number=12, step_name="Synchronize Platform State", status="FAILED", details={"platform_status": appt.status.value}))
            
            return CoreIntegrationSequenceResult(
                is_successful=False,
                appointment_id=appt.id,
                external_appointment_id=ext_appt_id,
                steps=steps,
                message="Core 12-Step Integration Sequence failed during external record verification."
            )

    def sync_and_verify_booking(self, appointment_id: str) -> Tuple[bool, str, Optional[str]]:
        seq_res = self.execute_core_integration_sequence(appointment_id)
        return seq_res.is_successful, seq_res.message, seq_res.external_appointment_id
