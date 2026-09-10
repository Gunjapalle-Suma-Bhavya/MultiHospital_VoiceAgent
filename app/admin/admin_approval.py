"""
Platform Admin Approval Service (Section 5.2).

Provides administrative capabilities for platform administrators:
- Review hospital information
- Approve hospitals
- Reject hospitals
- Request corrections
- Suspend hospitals
- Reactivate hospitals
- View hospital activity
- Review healthcare-system integration configuration
- Activate EHR integrations (with strict enforcement that only APPROVED active hospitals can activate integrations)
"""

import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models import (
    Hospital, HospitalStatus, Doctor, Appointment, EHRIntegrationConfig,
    AITelemetryLog, EHRSyncLog, WorkflowInstance, PatientIntakeRecord
)


class PlatformAdminApprovalService:
    """
    Service executing Platform Admin Approval actions and enforcing hospital activation rules.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def review_hospital_info(self, hospital_id: str) -> Dict[str, Any]:
        """
        Retrieves complete hospital registration & metadata for administrative review.
        """
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found")

        departments = json.loads(hosp.departments_json) if hosp.departments_json else []
        specialties = json.loads(hosp.specialties_json) if hosp.specialties_json else []
        services = json.loads(hosp.services_json) if hosp.services_json else []
        supported_systems = json.loads(hosp.supported_systems_json) if hosp.supported_systems_json else []

        ehr_config = self.db.query(EHRIntegrationConfig).filter(EHRIntegrationConfig.hospital_id == hospital_id).first()

        return {
            "hospital_id": hosp.id,
            "name": hosp.name,
            "code": hosp.code,
            "organization_info": hosp.organization_info,
            "address": hosp.address,
            "phone": hosp.phone,
            "contact_email": hosp.contact_email,
            "website": hosp.website,
            "timezone": hosp.timezone,
            "hospital_status": hosp.hospital_status.value if hosp.hospital_status else None,
            "is_active": hosp.is_active,
            "rejection_reason": hosp.rejection_reason,
            "correction_notes": hosp.correction_notes,
            "suspension_reason": hosp.suspension_reason,
            "admin_contact": {
                "name": hosp.admin_name,
                "email": hosp.admin_email,
                "phone": hosp.admin_phone
            },
            "verification_info": {
                "tax_id": hosp.verification_tax_id,
                "license_id": hosp.verification_license_id,
                "accreditation_details": hosp.accreditation_details
            },
            "departments": departments,
            "specialties": specialties,
            "services": services,
            "supported_systems": supported_systems,
            "ehr_config_summary": {
                "adapter_type": ehr_config.adapter_type.value if ehr_config and ehr_config.adapter_type else None,
                "is_active": ehr_config.is_active if ehr_config else False,
                "endpoint_url": ehr_config.endpoint_url if ehr_config else None
            }
        }

    def approve_hospital(self, hospital_id: str) -> Hospital:
        """
        Approves hospital application.
        Sets status = APPROVED and is_active = True.
        """
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found")

        hosp.hospital_status = HospitalStatus.APPROVED
        hosp.is_active = True
        self.db.commit()
        return hosp

    def reject_hospital(self, hospital_id: str, reason: str) -> Hospital:
        """
        Rejects hospital application.
        Sets status = REJECTED, is_active = False, and records rejection_reason.
        """
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found")
        if not reason:
            raise ValueError("Rejection reason is required")

        hosp.hospital_status = HospitalStatus.REJECTED
        hosp.rejection_reason = reason
        hosp.is_active = False
        self.db.commit()
        return hosp

    def request_corrections(self, hospital_id: str, notes: str) -> Hospital:
        """
        Requests corrections from hospital organization.
        Sets status = CORRECTION_REQUESTED, is_active = False, and records correction_notes.
        """
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found")
        if not notes:
            raise ValueError("Correction notes are required")

        hosp.hospital_status = HospitalStatus.CORRECTION_REQUESTED
        hosp.correction_notes = notes
        hosp.is_active = False
        self.db.commit()
        return hosp

    def suspend_hospital(self, hospital_id: str, reason: str) -> Hospital:
        """
        Suspends an approved hospital.
        Sets status = SUSPENDED, is_active = False, and records suspension_reason.
        """
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found")
        if not reason:
            raise ValueError("Suspension reason is required")

        hosp.hospital_status = HospitalStatus.SUSPENDED
        hosp.suspension_reason = reason
        hosp.is_active = False
        self.db.commit()
        return hosp

    def reactivate_hospital(self, hospital_id: str) -> Hospital:
        """
        Reactivates a suspended hospital.
        Sets status = APPROVED and is_active = True.
        """
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found")
        if hosp.hospital_status != HospitalStatus.SUSPENDED:
            raise ValueError(f"Cannot reactivate hospital from status {hosp.hospital_status.value}. Only SUSPENDED hospitals can be reactivated.")

        hosp.hospital_status = HospitalStatus.APPROVED
        hosp.is_active = True
        self.db.commit()
        return hosp

    def view_hospital_activity(self, hospital_id: str) -> Dict[str, Any]:
        """
        Returns real-time activity metrics and operational logs for a specific hospital.
        """
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found")

        total_doctors = self.db.query(func.count(Doctor.id)).filter(Doctor.hospital_id == hospital_id).scalar() or 0
        active_doctors = self.db.query(func.count(Doctor.id)).filter(Doctor.hospital_id == hospital_id, Doctor.is_active == True).scalar() or 0
        total_appointments = self.db.query(func.count(Appointment.id)).filter(Appointment.hospital_id == hospital_id).scalar() or 0
        intake_records = self.db.query(func.count(PatientIntakeRecord.id)).join(Appointment).filter(Appointment.hospital_id == hospital_id).scalar() or 0
        
        # Telemetry and EHR sync counts
        telemetry_logs = self.db.query(func.count(AITelemetryLog.id)).filter(AITelemetryLog.hospital_id == hospital_id).scalar() or 0
        ehr_syncs = self.db.query(func.count(EHRSyncLog.id)).filter(EHRSyncLog.hospital_id == hospital_id).scalar() or 0

        return {
            "hospital_id": hospital_id,
            "hospital_name": hosp.name,
            "hospital_status": hosp.hospital_status.value if hosp.hospital_status else None,
            "is_active": hosp.is_active,
            "metrics": {
                "total_doctors": total_doctors,
                "active_doctors": active_doctors,
                "total_appointments": total_appointments,
                "intake_records_count": intake_records,
                "telemetry_logs_count": telemetry_logs,
                "ehr_sync_logs_count": ehr_syncs
            }
        }

    def review_ehr_integration_config(self, hospital_id: str) -> Dict[str, Any]:
        """
        Reviews healthcare-system EHR integration configuration for a hospital.
        """
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found")

        config = self.db.query(EHRIntegrationConfig).filter(EHRIntegrationConfig.hospital_id == hospital_id).first()
        if not config:
            return {
                "hospital_id": hospital_id,
                "configured": False,
                "hospital_status": hosp.hospital_status.value if hosp.hospital_status else None,
                "can_activate": hosp.hospital_status == HospitalStatus.APPROVED and hosp.is_active
            }

        return {
            "hospital_id": hospital_id,
            "configured": True,
            "config_id": config.id,
            "adapter_type": config.adapter_type.value if config.adapter_type else None,
            "endpoint_url": config.endpoint_url,
            "is_active": config.is_active,
            "last_sync_at": config.last_sync_at.isoformat() if config.last_sync_at else None,
            "hospital_status": hosp.hospital_status.value if hosp.hospital_status else None,
            "can_activate": hosp.hospital_status == HospitalStatus.APPROVED and hosp.is_active
        }

    def activate_ehr_integration(self, hospital_id: str) -> EHRIntegrationConfig:
        """
        Activates EHR Integration for a hospital.
        ENFORCEMENT: Only APPROVED and active hospitals can activate supported EHR integrations.
        """
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found")

        if hosp.hospital_status != HospitalStatus.APPROVED or not hosp.is_active:
            raise ValueError(f"Cannot activate EHR integration for hospital in status {hosp.hospital_status.value}. Only APPROVED and active hospitals can activate EHR integrations.")

        config = self.db.query(EHRIntegrationConfig).filter(EHRIntegrationConfig.hospital_id == hospital_id).first()
        if not config:
            raise ValueError("EHR integration configuration not found for this hospital")

        config.is_active = True
        self.db.commit()
        return config
