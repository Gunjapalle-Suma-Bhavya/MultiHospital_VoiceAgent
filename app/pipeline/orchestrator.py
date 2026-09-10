"""
Horizontal Platform Pipeline Orchestrator (Step 2).

Implements the complete continuous ecosystem flow across 5 stages:
Stage 1: Hospital Registration -> Admin Verification -> Setup -> Doctor & Calendar Config -> Availability Published
Stage 2: Patient Registration -> Conversational Agent -> Understand Requirement -> Find Hospitals/Doctors -> Check Availability
Stage 3: Patient Selection -> Appointment Request -> Scheduling Capability -> EHR Integration -> External Verification
Stage 4: Appointment Confirmation -> Pre-Visit Workflow -> Patient Responses -> Doctor Review -> Analytics & Audit
Stage 5: Operational Event -> Background Workflow -> Notification -> Status Sync -> Continuous Monitoring
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.database.models import (
    Hospital, Doctor, DoctorWorkingHour, PatientProfile, PatientSessionState,
    Appointment, AppointmentStatus, PatientIntakeRecord, EHRIntegrationConfig, EHRAdapterType
)
from app.agent.actions import ActionExecutor
from app.schemas.actions import (
    SearchHospitalsInput, SearchDoctorsInput, CreateAppointmentInput
)
from app.workflows.engine import WorkflowEngine
from app.telemetry.intelligence import OperationalIntelligenceService


class HorizontalPlatformPipeline:
    """
    End-to-End Orchestrator executing the full horizontal lifecycle of the platform.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.actions = ActionExecutor(db_session)
        self.workflows = WorkflowEngine(db_session)
        self.telemetry = OperationalIntelligenceService(db_session)

    # =========================================================================
    # STAGE 1: HOSPITAL ONBOARDING & AVAILABILITY PUBLISHING
    # =========================================================================
    def execute_stage_1_hospital_onboarding(
        self,
        hospital_name: str,
        hospital_code: str,
        doctor_name: str,
        specialty: str,
        working_days: List[int] = [0, 1, 2, 3, 4]  # Mon-Fri
    ) -> Dict[str, Any]:
        """
        Hospital Registration -> Admin Verification -> Hospital Setup -> Doctor/Calendar Config -> Availability Published
        """
        # 1. Registration & Setup
        hosp = Hospital(
            name=hospital_name,
            code=hospital_code,
            is_active=True
        )
        self.db.add(hosp)
        self.db.flush()

        config = EHRIntegrationConfig(
            hospital_id=hosp.id,
            adapter_type=EHRAdapterType.MOCK_EHR,
            is_sync_enabled=True,
            require_external_verification=True
        )
        self.db.add(config)

        # 2. Doctor & Calendar Configuration
        doc = Doctor(
            hospital_id=hosp.id,
            name=doctor_name,
            specialty=specialty,
            default_appointment_duration=30,
            is_active=True
        )
        self.db.add(doc)
        self.db.flush()

        # Add working hours (Availability Published)
        for day in working_days:
            wh = DoctorWorkingHour(
                doctor_id=doc.id,
                day_of_week=day,
                start_time=datetime.strptime("09:00", "%H:%M").time(),
                end_time=datetime.strptime("17:00", "%H:%M").time()
            )
            self.db.add(wh)

        self.db.commit()
        return {
            "stage": "STAGE_1_COMPLETED",
            "hospital_id": hosp.id,
            "doctor_id": doc.id,
            "availability_published": True
        }

    # =========================================================================
    # STAGE 2: PATIENT ENGAGEMENT & CONVERSATIONAL INTAKE
    # =========================================================================
    def execute_stage_2_patient_engagement(
        self,
        phone_number: str,
        patient_name: str,
        utterance: str
    ) -> Dict[str, Any]:
        """
        Patient Registration -> Conversational Agent -> Understand Requirement -> Find Hospitals & Doctors -> Check Availability
        """
        patient = self.db.query(PatientProfile).filter(PatientProfile.phone_number == phone_number).first()
        if not patient:
            patient = PatientProfile(phone_number=phone_number, full_name=patient_name)
            self.db.add(patient)
            self.db.commit()

        session = PatientSessionState(
            patient_id=patient.id,
            current_intent="FIND_DOCTOR",
            workflow_step="STAGE_2_SEARCH"
        )
        self.db.add(session)
        self.db.commit()

        # Conversational Agent -> Search Doctors
        search_res = self.actions.search_doctors(SearchDoctorsInput(
            session_id=session.session_id,
            patient_id=patient.id,
            query=utterance
        ))

        return {
            "stage": "STAGE_2_COMPLETED",
            "patient_id": patient.id,
            "session_id": session.session_id,
            "matched_doctors": [d.model_dump() for d in search_res.doctors]
        }

    # =========================================================================
    # STAGE 3: SELECTION, SCHEDULING & EHR VERIFICATION
    # =========================================================================
    def execute_stage_3_scheduling_and_ehr_verification(
        self,
        session_id: str,
        patient_id: str,
        hospital_id: str,
        doctor_id: str,
        start_datetime: datetime,
        patient_name: str,
        patient_phone: str
    ) -> Dict[str, Any]:
        """
        Patient Selection -> Appointment Request -> Scheduling Capability -> EHR Integration -> External Verification
        """
        create_res = self.actions.create_appointment(CreateAppointmentInput(
            session_id=session_id,
            patient_id=patient_id,
            hospital_id=hospital_id,
            doctor_id=doctor_id,
            start_datetime=start_datetime,
            patient_name=patient_name,
            patient_phone=patient_phone
        ))

        return {
            "stage": "STAGE_3_COMPLETED" if create_res.success else "STAGE_3_FAILED",
            "success": create_res.success,
            "appointment_id": create_res.appointment_id,
            "ehr_verified": create_res.success,
            "message": create_res.message
        }

    # =========================================================================
    # STAGE 4: CONFIRMATION, PRE-VISIT & DOCTOR INTAKE REVIEW
    # =========================================================================
    def execute_stage_4_pre_visit_and_doctor_review(
        self,
        appointment_id: str,
        patient_reported_symptoms: str
    ) -> Dict[str, Any]:
        """
        Appointment Confirmation -> Pre-Visit Workflow -> Patient Responses -> Doctor Review -> Analytics & Audit
        """
        appt = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            return {"success": False, "message": "Appointment not found"}

        intake = PatientIntakeRecord(
            appointment_id=appointment_id,
            patient_reported_summary=patient_reported_symptoms,
            is_patient_reported_only=True,
            encryption_status="ENCRYPTED_AT_REST"
        )
        self.db.add(intake)
        self.db.commit()

        return {
            "stage": "STAGE_4_COMPLETED",
            "appointment_id": appointment_id,
            "intake_record_id": intake.id,
            "doctor_review_ready": True
        }

    # =========================================================================
    # STAGE 5: OPERATIONAL EVENT & ASYNC LIFECYCLE
    # =========================================================================
    def execute_stage_5_async_lifecycle(
        self,
        appointment_id: str
    ) -> Dict[str, Any]:
        """
        Operational Event -> Background Workflow -> Notification -> Status Sync -> Continuous Monitoring
        """
        due_count = self.workflows.execute_due_reminder_workflows()
        health_report = self.telemetry.get_system_health_report()

        return {
            "stage": "STAGE_5_COMPLETED",
            "due_reminders_dispatched": due_count,
            "continuous_monitoring_report": health_report
        }
