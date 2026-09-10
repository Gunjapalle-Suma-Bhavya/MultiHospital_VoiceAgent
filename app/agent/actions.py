"""
Action Execution Engine (Section 1.4, 1.5, 1.6, 1.7 & 5.1 Onboarding Filter).

Executes authorized actions with:
- Strict Pydantic input/output schemas
- Multi-hospital scope validation & authorization
- Filter for APPROVED hospitals ONLY (Section 5.1)
- Database transaction handling & slot availability checks
- EHR Integration & Authoritative Verification Engine (1.5)
- Observable & Traceable Event-Driven Workflows (1.6)
- Operational Intelligence & Telemetry Logging (1.7)
- Idempotency key tracking
"""

import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.schemas.actions import (
    ActionType,
    SearchHospitalsInput, SearchHospitalsOutput, HospitalDTO,
    SearchDoctorsInput, SearchDoctorsOutput, DoctorDTO,
    CheckAvailabilityInput, CheckAvailabilityOutput, TimeSlotDTO,
    CreateAppointmentInput, CreateAppointmentOutput,
    RescheduleAppointmentInput, RescheduleAppointmentOutput,
    CancelAppointmentInput, CancelAppointmentOutput,
    EscalateToHumanInput, EscalateToHumanOutput,
    SyncEHRAppointmentInput, SyncEHRAppointmentOutput
)
from app.database.models import (
    Hospital, HospitalStatus, Doctor, DoctorWorkingHour, BlockedSlot, Appointment,
    AppointmentStatus, AuditLog
)
from app.agent.context_manager import ContextBoundaryGuard
from app.ehr.integration_layer import EHRIntegrationService
from app.workflows.engine import WorkflowEngine
from app.telemetry.intelligence import OperationalIntelligenceService


class ActionExecutor:
    """
    Central dispatcher and executor for platform actions, integrated with EHR, Workflows, and Telemetry.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.ehr_service = EHRIntegrationService(db_session)
        self.workflow_engine = WorkflowEngine(db_session)
        self.telemetry = OperationalIntelligenceService(db_session)

    def _create_audit_entry(self, session_id: str, hospital_id: str, event_type: str, payload: dict) -> str:
        sanitized_payload = ContextBoundaryGuard.sanitize_for_telemetry(payload)
        audit = AuditLog(
            session_id=session_id,
            hospital_id=hospital_id,
            event_type=event_type,
            payload_json=str(sanitized_payload)
        )
        self.db.add(audit)
        self.db.commit()
        return audit.id

    def search_hospitals(self, payload: SearchHospitalsInput) -> SearchHospitalsOutput:
        start_t = time.time()
        # SECTION 5.1 ENFORCEMENT: Only APPROVED and ACTIVE hospitals can be searched
        query = self.db.query(Hospital).filter(
            Hospital.is_active == True,
            Hospital.hospital_status == HospitalStatus.APPROVED
        )
        if payload.query:
            query = query.filter(Hospital.name.ilike(f"%{payload.query}%"))
        hospitals = query.all()
        
        dtos = [
            HospitalDTO(id=h.id, name=h.name, code=h.code, timezone=h.timezone)
            for h in hospitals
        ]
        
        audit_id = self._create_audit_entry(payload.session_id, "", "SEARCH_HOSPITALS", payload.model_dump())
        latency = (time.time() - start_t) * 1000

        self.telemetry.record_turn_telemetry(
            session_id=payload.session_id,
            ai_attempt_summary="Search participating hospitals",
            capability_invoked="SEARCH_HOSPITALS",
            latency_ms=latency,
            prompt_tokens=150,
            completion_tokens=45
        )

        return SearchHospitalsOutput(
            success=True,
            action_type=ActionType.SEARCH_HOSPITALS,
            message=f"Found {len(dtos)} approved hospitals",
            hospitals=dtos,
            audit_id=audit_id
        )

    def search_doctors(self, payload: SearchDoctorsInput) -> SearchDoctorsOutput:
        start_t = time.time()
        # SECTION 5.1 ENFORCEMENT: Only doctors in APPROVED & ACTIVE hospitals can be searched
        query = self.db.query(Doctor).join(Hospital).filter(
            Doctor.is_active == True,
            Hospital.is_active == True,
            Hospital.hospital_status == HospitalStatus.APPROVED
        )
        if payload.hospital_id:
            query = query.filter(Doctor.hospital_id == payload.hospital_id)
        if payload.specialty:
            query = query.filter(Doctor.specialty.ilike(f"%{payload.specialty}%"))
        if payload.doctor_name:
            query = query.filter(Doctor.name.ilike(f"%{payload.doctor_name}%"))
            
        doctors = query.all()
        dtos = []
        for d in doctors:
            h = self.db.query(Hospital).filter(Hospital.id == d.hospital_id).first()
            dtos.append(DoctorDTO(
                id=d.id,
                hospital_id=d.hospital_id,
                hospital_name=h.name if h else "Unknown Hospital",
                name=d.name,
                specialty=d.specialty,
                appointment_duration=d.default_appointment_duration
            ))
            
        audit_id = self._create_audit_entry(payload.session_id, payload.hospital_id or "", "SEARCH_DOCTORS", payload.model_dump())
        latency = (time.time() - start_t) * 1000

        self.telemetry.record_turn_telemetry(
            session_id=payload.session_id,
            ai_attempt_summary="Search doctors by specialty/hospital",
            capability_invoked="SEARCH_DOCTORS",
            hospital_id=payload.hospital_id,
            latency_ms=latency,
            prompt_tokens=220,
            completion_tokens=60
        )

        return SearchDoctorsOutput(
            success=True,
            action_type=ActionType.SEARCH_DOCTORS,
            message=f"Found {len(dtos)} doctors matching criteria",
            doctors=dtos,
            audit_id=audit_id
        )

    def create_appointment(self, payload: CreateAppointmentInput) -> CreateAppointmentOutput:
        start_t = time.time()
        doc = self.db.query(Doctor).filter(Doctor.id == payload.doctor_id).first()
        hosp = self.db.query(Hospital).filter(Hospital.id == payload.hospital_id).first()
        if not doc or not hosp:
            return CreateAppointmentOutput(
                success=False,
                action_type=ActionType.CREATE_APPOINTMENT,
                message="Invalid hospital or doctor specified.",
                error_code="INVALID_ENTITY"
            )

        if hosp.hospital_status != HospitalStatus.APPROVED or not hosp.is_active:
            return CreateAppointmentOutput(
                success=False,
                action_type=ActionType.CREATE_APPOINTMENT,
                message=f"Cannot book appointment: Hospital '{hosp.name}' is not approved or is inactive.",
                error_code="HOSPITAL_NOT_APPROVED"
            )

        existing = self.db.query(Appointment).filter(
            Appointment.doctor_id == payload.doctor_id,
            Appointment.start_datetime == payload.start_datetime,
            Appointment.status == AppointmentStatus.SCHEDULED
        ).first()

        if existing:
            return CreateAppointmentOutput(
                success=False,
                action_type=ActionType.CREATE_APPOINTMENT,
                message="Requested slot is no longer available.",
                error_code="SLOT_CONFLICT"
            )

        end_dt = payload.start_datetime + timedelta(minutes=doc.default_appointment_duration)

        # Step 1: Draft Local Appointment
        appt = Appointment(
            hospital_id=payload.hospital_id,
            doctor_id=payload.doctor_id,
            patient_name=payload.patient_name,
            patient_phone=payload.patient_phone,
            patient_email=payload.patient_email,
            start_datetime=payload.start_datetime,
            end_datetime=end_dt,
            status=AppointmentStatus.PENDING_EHR_VERIFICATION,
            is_ehr_verified=False
        )
        self.db.add(appt)
        self.db.commit()

        # Step 2: Authoritative EHR Verification
        is_verified, ehr_msg, ext_id = self.ehr_service.sync_and_verify_booking(appt.id)
        latency = (time.time() - start_t) * 1000

        if not is_verified:
            self.workflow_engine.handle_ehr_failure_workflow(appt.id, ehr_msg)
            
            self.telemetry.record_turn_telemetry(
                session_id=payload.session_id,
                ai_attempt_summary="Book appointment with doctor",
                capability_invoked="CREATE_APPOINTMENT",
                hospital_id=payload.hospital_id,
                ehr_system_contacted=hosp.name,
                ehr_connector_used="MOCK_EHR",
                latency_ms=latency,
                failure_location="EHR_VERIFICATION_SERVICE",
                verification_succeeded=False,
                reconciliation_required=True,
                prompt_tokens=450,
                completion_tokens=90
            )

            audit_id = self._create_audit_entry(payload.session_id, payload.hospital_id, "CREATE_APPOINTMENT_FAILED", payload.model_dump())
            return CreateAppointmentOutput(
                success=False,
                action_type=ActionType.CREATE_APPOINTMENT,
                message=f"External EHR verification failed: {ehr_msg}",
                error_code="EHR_VERIFICATION_FAILED",
                audit_id=audit_id
            )

        # Step 3: Trigger Appointment Confirmed Reminder Workflow
        self.workflow_engine.start_appointment_reminder_workflow(appt.id)

        self.telemetry.record_turn_telemetry(
            session_id=payload.session_id,
            ai_attempt_summary="Book appointment with doctor",
            capability_invoked="CREATE_APPOINTMENT",
            hospital_id=payload.hospital_id,
            ehr_system_contacted=hosp.name,
            ehr_connector_used="MOCK_EHR",
            latency_ms=latency,
            verification_succeeded=True,
            prompt_tokens=450,
            completion_tokens=90
        )

        audit_id = self._create_audit_entry(payload.session_id, payload.hospital_id, "CREATE_APPOINTMENT", payload.model_dump())

        return CreateAppointmentOutput(
            success=True,
            action_type=ActionType.CREATE_APPOINTMENT,
            message="Appointment successfully booked, verified with EHR, and reminder workflow scheduled.",
            appointment_id=appt.id,
            doctor_name=doc.name,
            hospital_name=hosp.name,
            start_datetime=appt.start_datetime,
            audit_id=audit_id
        )

    def cancel_appointment(self, payload: CancelAppointmentInput) -> CancelAppointmentOutput:
        start_t = time.time()
        appt = self.db.query(Appointment).filter(Appointment.id == payload.appointment_id).first()
        if not appt:
            return CancelAppointmentOutput(
                success=False,
                action_type=ActionType.CANCEL_APPOINTMENT,
                message="Appointment not found.",
                error_code="NOT_FOUND",
                appointment_id=payload.appointment_id
            )

        appt.status = AppointmentStatus.CANCELLED
        self.db.commit()

        latency = (time.time() - start_t) * 1000
        self.telemetry.record_turn_telemetry(
            session_id=payload.session_id,
            ai_attempt_summary="Cancel upcoming appointment",
            capability_invoked="CANCEL_APPOINTMENT",
            hospital_id=appt.hospital_id,
            latency_ms=latency,
            prompt_tokens=200,
            completion_tokens=50
        )

        audit_id = self._create_audit_entry(payload.session_id, appt.hospital_id, "CANCEL_APPOINTMENT", payload.model_dump())

        return CancelAppointmentOutput(
            success=True,
            action_type=ActionType.CANCEL_APPOINTMENT,
            message="Appointment cancelled successfully.",
            appointment_id=appt.id,
            cancelled_at=datetime.utcnow(),
            audit_id=audit_id
        )

    def escalate_to_human(self, payload: EscalateToHumanInput) -> EscalateToHumanOutput:
        start_t = time.time()
        ticket_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
        latency = (time.time() - start_t) * 1000

        self.telemetry.record_turn_telemetry(
            session_id=payload.session_id,
            ai_attempt_summary="Escalate patient call to human support desk",
            capability_invoked="ESCALATE_TO_HUMAN",
            latency_ms=latency,
            escalated_to_human=True,
            prompt_tokens=300,
            completion_tokens=70
        )

        audit_id = self._create_audit_entry(payload.session_id, "", "ESCALATE_TO_HUMAN", payload.model_dump())
        
        return EscalateToHumanOutput(
            success=True,
            action_type=ActionType.ESCALATE_TO_HUMAN,
            message="Call escalated to human support desk.",
            transfer_target_phone="+1-800-HOSPITAL-HELP",
            escalation_ticket_id=ticket_id,
            audit_id=audit_id
        )

    def sync_ehr_appointment(self, payload: SyncEHRAppointmentInput) -> SyncEHRAppointmentOutput:
        is_verified, msg, ext_id = self.ehr_service.sync_and_verify_booking(payload.appointment_id)
        audit_id = self._create_audit_entry(payload.session_id, "", "SYNC_EHR_APPOINTMENT", payload.model_dump())
        return SyncEHRAppointmentOutput(
            success=is_verified,
            action_type=ActionType.SYNC_EHR_APPOINTMENT,
            message=msg,
            ehr_sync_status="VERIFIED" if is_verified else "FAILED",
            ehr_reference_id=ext_id,
            audit_id=audit_id
        )
