"""
Database models for Multi-Hospital Voice Agent platform.
Enforces multi-tenant hospital structure, doctor-controlled calendars,
appointment scheduling, persistent patient context, privacy boundaries,
EHR Identity Mappings, Workflow-Driven Operations, Operational Intelligence,
and Self-Service Hospital Registration & Onboarding Lifecycle (Section 5.1).
"""

from datetime import datetime, time, timezone
from enum import Enum
import uuid
from sqlalchemy import (
    Column, String, Boolean, Integer, Float, DateTime, Date, Time, Text, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class HospitalStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    CORRECTION_REQUESTED = "CORRECTION_REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class AppointmentStatus(str, Enum):
    REQUESTED = "REQUESTED"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SCHEDULED = "SCHEDULED"
    RESCHEDULED = "RESCHEDULED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"
    FAILED = "FAILED"
    SYNCHRONIZATION_PENDING = "SYNCHRONIZATION_PENDING"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    PENDING_EHR_VERIFICATION = "PENDING_EHR_VERIFICATION"


class CalendarType(str, Enum):
    HOSPITAL_CONSULTATION = "HOSPITAL_CONSULTATION"
    ONLINE_CONSULTATION = "ONLINE_CONSULTATION"
    FOLLOW_UP = "FOLLOW_UP"
    SPECIALTY_CONSULTATION = "SPECIALTY_CONSULTATION"


class PreferredTimeWindow(str, Enum):
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"
    ANYTIME = "ANYTIME"


class DoctorStatus(str, Enum):
    INVITED = "INVITED"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class ConsultationType(str, Enum):
    IN_PERSON = "IN_PERSON"
    VIDEO = "VIDEO"
    PHONE = "PHONE"
    HYBRID = "HYBRID"


class EHRAdapterType(str, Enum):
    FHIR_R4 = "FHIR_R4"
    HL7_V2 = "HL7_V2"
    EPIC_MYCHART = "EPIC_MYCHART"
    CERNER_MILLENNIUM = "CERNER_MILLENNIUM"
    ATHENA_HEALTH = "ATHENA_HEALTH"
    MOCK_EHR = "MOCK_EHR"


class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ESCALATED = "ESCALATED"


class Hospital(Base):
    """
    Hospital entity maintaining full self-service onboarding configuration (Section 5.1).
    Lifecycle: Draft -> Submitted -> Under Review -> Approved / Rejected.
    Only APPROVED hospitals become active.
    """
    __tablename__ = "hospitals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    organization_info = Column(Text, nullable=True)
    address = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    contact_email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    timezone = Column(String(50), default="UTC")
    
    # Detailed metadata fields
    departments_json = Column(Text, nullable=True)     # JSON list of departments
    specialties_json = Column(Text, nullable=True)       # JSON list of specialties
    operating_hours_json = Column(Text, nullable=True)   # JSON operating hours schedule
    services_json = Column(Text, nullable=True)          # JSON list of services
    
    # Organization Administrator info
    admin_name = Column(String(255), nullable=True)
    admin_email = Column(String(255), nullable=True)
    admin_phone = Column(String(50), nullable=True)
    
    # Verification details
    verification_tax_id = Column(String(100), nullable=True)
    verification_license_id = Column(String(100), nullable=True)
    accreditation_details = Column(Text, nullable=True)
    supported_systems_json = Column(Text, nullable=True)
    
    # Onboarding Lifecycle State
    hospital_status = Column(SQLEnum(HospitalStatus), default=HospitalStatus.APPROVED)
    rejection_reason = Column(Text, nullable=True)
    correction_notes = Column(Text, nullable=True)
    suspension_reason = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    doctors = relationship("Doctor", back_populates="hospital", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="hospital")
    ehr_config = relationship("EHRIntegrationConfig", back_populates="hospital", uselist=False)
    questionnaires = relationship("HospitalQuestionnaire", back_populates="hospital", cascade="all, delete-orphan")
    preferences = relationship("HospitalOperationalPreference", back_populates="hospital", uselist=False)
    staff_members = relationship("HospitalStaff", back_populates="hospital", cascade="all, delete-orphan")


class HospitalQuestionnaire(Base):
    __tablename__ = "hospital_questionnaires"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False)
    title = Column(String(255), nullable=False)
    specialty = Column(String(100), nullable=False)
    questions_json = Column(Text, nullable=False)
    is_approved_by_clinician = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    hospital = relationship("Hospital", back_populates="questionnaires")


class HospitalOperationalPreference(Base):
    __tablename__ = "hospital_operational_preferences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, unique=True)
    max_advance_booking_days = Column(Integer, default=30)
    cancellation_notice_hours = Column(Integer, default=24)
    auto_reminders_enabled = Column(Boolean, default=True)
    communication_preference = Column(String(50), default="VOICE_AND_SMS")
    sms_enabled = Column(Boolean, default=True)
    voice_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    hospital = relationship("Hospital", back_populates="preferences")


class HospitalStaff(Base):
    __tablename__ = "hospital_staff"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(100), default="STAFF")
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    hospital = relationship("Hospital", back_populates="staff_members")


class EHRIntegrationConfig(Base):
    __tablename__ = "ehr_integration_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, unique=True)
    adapter_type = Column(SQLEnum(EHRAdapterType), default=EHRAdapterType.MOCK_EHR)
    endpoint_url = Column(String(255), nullable=True)
    api_base_url = Column(String(255), nullable=True)
    auth_credentials_json = Column(Text, nullable=True)
    is_sync_enabled = Column(Boolean, default=True)
    require_external_verification = Column(Boolean, default=True)
    is_active = Column(Boolean, default=False)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    hospital = relationship("Hospital", back_populates="ehr_config")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False)
    name = Column(String(255), nullable=False)
    photo_url = Column(String(255), nullable=True)
    specialty = Column(String(100), nullable=False, index=True)
    department = Column(String(100), nullable=True)
    qualifications = Column(String(255), nullable=True)
    experience_years = Column(Integer, default=0)
    languages_json = Column(Text, nullable=True)  # JSON list of languages
    consultation_type = Column(SQLEnum(ConsultationType), default=ConsultationType.IN_PERSON)
    default_appointment_duration = Column(Integer, default=30)
    
    doctor_status = Column(SQLEnum(DoctorStatus), default=DoctorStatus.ACTIVE)
    is_active = Column(Boolean, default=True)
    external_provider_id = Column(String(100), nullable=True, index=True)
    
    bio = Column(Text, nullable=True)
    professional_info = Column(Text, nullable=True)
    profile_completed = Column(Boolean, default=False)
    special_instructions = Column(Text, nullable=True)

    hospital = relationship("Hospital", back_populates="doctors")
    working_hours = relationship("DoctorWorkingHour", back_populates="doctor", cascade="all, delete-orphan")
    blocked_slots = relationship("BlockedSlot", back_populates="doctor", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="doctor")
    approved_questions = relationship("DoctorApprovedQuestion", back_populates="doctor", cascade="all, delete-orphan")
    calendars = relationship("DoctorCalendar", back_populates="doctor", cascade="all, delete-orphan")
    leaves = relationship("DoctorLeave", back_populates="doctor", cascade="all, delete-orphan")


class DoctorLeave(Base):
    __tablename__ = "doctor_leaves"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    leave_type = Column(String(100), default="ANNUAL_LEAVE")
    reason = Column(Text, nullable=True)
    status = Column(String(50), default="APPROVED")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    doctor = relationship("Doctor", back_populates="leaves")


class DoctorCalendar(Base):
    __tablename__ = "doctor_calendars"


    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=False)
    calendar_name = Column(String(255), nullable=False)
    calendar_type = Column(SQLEnum(CalendarType), default=CalendarType.HOSPITAL_CONSULTATION)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    doctor = relationship("Doctor", back_populates="calendars")
    appointments = relationship("Appointment", back_populates="calendar")


class DoctorApprovedQuestion(Base):
    __tablename__ = "doctor_approved_questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="TEXT")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    doctor = relationship("Doctor", back_populates="approved_questions")


class DoctorWorkingHour(Base):
    __tablename__ = "doctor_working_hours"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    break_start = Column(Time, nullable=True)
    break_end = Column(Time, nullable=True)

    doctor = relationship("Doctor", back_populates="working_hours")


class BlockedSlot(Base):
    __tablename__ = "blocked_slots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    reason = Column(String(255), nullable=True)

    doctor = relationship("Doctor", back_populates="blocked_slots")


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    preferred_language = Column(String(50), default="English")
    emergency_contact_json = Column(Text, nullable=True)
    external_patient_id = Column(String(100), nullable=True, index=True)
    saved_preferences_json = Column(Text, nullable=True)
    
    last_hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=True)
    last_doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=True)
    preferred_time_window = Column(SQLEnum(PreferredTimeWindow), default=PreferredTimeWindow.ANYTIME)
    communication_preference = Column(String(50), default="VOICE_AND_SMS")
    interaction_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    sessions = relationship("PatientSessionState", back_populates="patient", cascade="all, delete-orphan")
    questionnaire_responses = relationship("PatientQuestionnaireResponse", back_populates="patient", cascade="all, delete-orphan")

    @property
    def name(self):
        return self.full_name or ""

    @name.setter
    def name(self, value):
        self.full_name = value



class PatientQuestionnaireResponse(Base):
    __tablename__ = "patient_questionnaire_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient_profiles.id"), nullable=False)
    questionnaire_id = Column(String(36), ForeignKey("hospital_questionnaires.id"), nullable=False)
    appointment_id = Column(String(36), ForeignKey("appointments.id"), nullable=True)
    answers_json = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    patient = relationship("PatientProfile", back_populates="questionnaire_responses")


class PatientSessionState(Base):
    __tablename__ = "patient_session_states"

    session_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient_profiles.id"), nullable=False)
    
    current_intent = Column(String(100), nullable=True)
    workflow_step = Column(String(100), nullable=True)
    active_draft_booking_json = Column(Text, nullable=True)
    completed_workflow_steps_json = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    patient = relationship("PatientProfile", back_populates="sessions")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False)
    doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=False)
    calendar_id = Column(String(36), ForeignKey("doctor_calendars.id"), nullable=True)
    patient_id = Column(String(36), ForeignKey("patient_profiles.id"), nullable=True)
    patient_name = Column(String(255), nullable=False)
    patient_phone = Column(String(50), nullable=False)
    patient_email = Column(String(255), nullable=True)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    status = Column(SQLEnum(AppointmentStatus), default=AppointmentStatus.PENDING_EHR_VERIFICATION)
    external_status = Column(String(100), nullable=True)
    external_appointment_id = Column(String(255), nullable=True)
    is_ehr_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    hospital = relationship("Hospital", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    calendar = relationship("DoctorCalendar", back_populates="appointments")
    intake_record = relationship("PatientIntakeRecord", back_populates="appointment", uselist=False)
    workflows = relationship("WorkflowInstance", back_populates="appointment", cascade="all, delete-orphan")
    state_history = relationship("AppointmentStateHistory", back_populates="appointment", cascade="all, delete-orphan")


class AppointmentStateHistory(Base):
    __tablename__ = "appointment_state_histories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id = Column(String(36), ForeignKey("appointments.id"), nullable=False)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by = Column(String(100), default="SYSTEM")
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    appointment = relationship("Appointment", back_populates="state_history")


class WorkflowInstance(Base):
    __tablename__ = "workflow_instances"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id = Column(String(36), ForeignKey("appointments.id"), nullable=True)
    workflow_name = Column(String(100), nullable=False)
    trigger_event = Column(String(100), nullable=False)
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.PENDING)
    payload_json = Column(Text, nullable=True)
    scheduled_for = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    appointment = relationship("Appointment", back_populates="workflows")
    step_logs = relationship("WorkflowStepLog", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowStepLog(Base):
    __tablename__ = "workflow_step_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), ForeignKey("workflow_instances.id"), nullable=False)
    step_name = Column(String(100), nullable=False)
    step_status = Column(String(50), nullable=False)
    attempt_count = Column(Integer, default=1)
    message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    workflow = relationship("WorkflowInstance", back_populates="step_logs")


class AITelemetryLog(Base):
    __tablename__ = "ai_telemetry_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), nullable=False, index=True)
    hospital_id = Column(String(36), nullable=True)
    
    ai_attempt_summary = Column(String(255), nullable=False)
    capability_invoked = Column(String(100), nullable=True)
    model_name = Column(String(100), default="gemini-3.6-flash")
    
    ehr_system_contacted = Column(String(100), nullable=True)
    ehr_connector_used = Column(String(100), nullable=True)
    
    latency_ms = Column(Float, default=0.0)
    failure_location = Column(String(255), nullable=True)
    retries_triggered = Column(Integer, default=0)
    verification_succeeded = Column(Boolean, default=True)
    reconciliation_required = Column(Boolean, default=False)
    recovery_succeeded = Column(Boolean, default=True)
    escalated_to_human = Column(Boolean, default=False)
    
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0000)
    
    workflow_health_status = Column(String(50), default="HEALTHY")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class EHRMapping(Base):
    __tablename__ = "ehr_mappings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False)
    entity_type = Column(String(50), nullable=False)
    internal_id = Column(String(255), nullable=False, index=True)
    external_ehr_id = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class EHRSyncLog(Base):
    __tablename__ = "ehr_sync_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id = Column(String(36), ForeignKey("appointments.id"), nullable=False)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False)
    action_type = Column(String(50), nullable=False)
    sync_status = Column(String(50), nullable=False)
    external_reference_id = Column(String(255), nullable=True)
    details_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class PatientIntakeRecord(Base):
    __tablename__ = "patient_intake_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id = Column(String(36), ForeignKey("appointments.id"), nullable=False)
    patient_reported_summary = Column(Text, nullable=False)
    intake_answers_json = Column(Text, nullable=True)
    is_patient_reported_only = Column(Boolean, default=True)
    encryption_status = Column(String(50), default="ENCRYPTED_AT_REST")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    appointment = relationship("Appointment", back_populates="intake_record")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), nullable=True)
    hospital_id = Column(String(36), nullable=True)
    correlation_id = Column(String(100), nullable=True, index=True)
    event_type = Column(String(100), nullable=False)
    tool_invocation_json = Column(Text, nullable=True)
    payload_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class EventType(str, Enum):
    HOSPITAL_APPROVED = "HOSPITAL_APPROVED"
    DOCTOR_CREATED = "DOCTOR_CREATED"
    APPOINTMENT_REQUESTED = "APPOINTMENT_REQUESTED"
    APPOINTMENT_BOOKED = "APPOINTMENT_BOOKED"
    APPOINTMENT_CANCELLED = "APPOINTMENT_CANCELLED"
    APPOINTMENT_RESCHEDULED = "APPOINTMENT_RESCHEDULED"
    QUESTIONNAIRE_ASSIGNED = "QUESTIONNAIRE_ASSIGNED"
    QUESTIONNAIRE_COMPLETED = "QUESTIONNAIRE_COMPLETED"
    AI_CONVERSATION_STARTED = "AI_CONVERSATION_STARTED"
    AI_TOOL_EXECUTED = "AI_TOOL_EXECUTED"
    EHR_INTEGRATION_STARTED = "EHR_INTEGRATION_STARTED"
    EHR_INTEGRATION_COMPLETED = "EHR_INTEGRATION_COMPLETED"
    EHR_INTEGRATION_FAILED = "EHR_INTEGRATION_FAILED"
    EHR_SYNC_VERIFIED = "EHR_SYNC_VERIFIED"
    EHR_RECONCILIATION_REQUIRED = "EHR_RECONCILIATION_REQUIRED"
    WORKFLOW_STARTED = "WORKFLOW_STARTED"
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"
    WORKFLOW_FAILED = "WORKFLOW_FAILED"
    HUMAN_ESCALATION_TRIGGERED = "HUMAN_ESCALATION_TRIGGERED"


class NotificationRecipientRole(str, Enum):
    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    HOSPITAL = "HOSPITAL"


class NotificationChannel(str, Enum):
    SMS = "SMS"
    EMAIL = "EMAIL"
    IN_APP = "IN_APP"
    VOICE_CALL = "VOICE_CALL"
    WEBHOOK = "WEBHOOK"


class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


class PlatformEventRecord(Base):
    """
    Structured System Event Persistence (Section 5.29).
    Stores published platform events for decoupled analytics, workflows, audit, and monitoring consumers.
    """
    __tablename__ = "platform_event_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(100), nullable=False, index=True)
    source = Column(String(100), nullable=False)
    aggregate_id = Column(String(255), nullable=True, index=True)
    payload_json = Column(Text, nullable=True)
    published_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class NotificationRecord(Base):
    """
    Multi-Role Notification Log (Section 5.30).
    Stores notifications dispatched to Patients, Doctors, and Hospitals.
    """
    __tablename__ = "notification_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_role = Column(String(50), nullable=False, index=True)
    recipient_id = Column(String(255), nullable=False, index=True)
    notification_type = Column(String(100), nullable=False)
    channel = Column(String(50), default="SMS")
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    status = Column(String(50), default="SENT")
    metadata_json = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class OperationTrace(Base):
    """
    Operational Observability & Lifecycle Tracing (Section 5.34 & 5.35).
    Tracks end-to-end user operations across all 16 canonical steps and 10 platform component layers.
    """
    __tablename__ = "operation_traces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id = Column(String(100), unique=True, index=True, nullable=False)
    correlation_id = Column(String(100), nullable=False, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    hospital_id = Column(String(36), nullable=True)
    patient_id = Column(String(36), nullable=True)
    appointment_id = Column(String(36), nullable=True)
    operation_name = Column(String(100), default="PATIENT_ACCESS_BOOKING_LIFECYCLE")
    status = Column(String(50), default="IN_PROGRESS")  # STARTED, IN_PROGRESS, COMPLETED, FAILED, ESCALATED
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    completed_at = Column(DateTime, nullable=True)
    total_latency_ms = Column(Float, default=0.0)
    
    # Detailed Diagnostics
    failure_location = Column(String(255), nullable=True)
    failed_action = Column(String(100), nullable=True)
    failed_external_system = Column(String(100), nullable=True)
    retries_triggered = Column(Integer, default=0)
    recovery_succeeded = Column(Boolean, default=False)
    reconciliation_occurred = Column(Boolean, default=False)
    escalated_to_human = Column(Boolean, default=False)
    metadata_json = Column(Text, nullable=True)

    steps = relationship("OperationTraceStep", back_populates="trace", cascade="all, delete-orphan", order_by="OperationTraceStep.step_number")


class OperationTraceStep(Base):
    """
    Granular Step Record in the 16-Step Canonical Operation Lifecycle (Section 5.34).
    """
    __tablename__ = "operation_trace_steps"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id = Column(String(36), ForeignKey("operation_traces.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(100), nullable=False)
    component_type = Column(String(50), nullable=False)  # CONVERSATION, AI_DECISION, CAPABILITY_CALL, SCHEDULING, EHR_INTEGRATION, VERIFICATION, SYNCHRONIZATION, WORKFLOW, NOTIFICATION, AUDIT_EVENT
    status = Column(String(50), default="SUCCESS")  # SUCCESS, FAILED, RETRYING, SKIPPED
    latency_ms = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    external_system_name = Column(String(100), nullable=True)
    retry_count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    details_json = Column(Text, nullable=True)

    trace = relationship("OperationTrace", back_populates="steps")


class AIUsageRecord(Base):
    """
    AI Usage & Cost Tracking Ledger (Section 5.36).
    Tracks request counts, token consumption, voice duration, latency, and estimated cost
    aggregated by hospital, feature, conversation, and workflow.
    """
    __tablename__ = "ai_usage_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(100), nullable=True, index=True)
    hospital_id = Column(String(36), nullable=True, index=True)
    workflow_id = Column(String(36), nullable=True, index=True)
    feature_name = Column(String(100), default="VOICE_PATIENT_INTAKE", index=True)
    model_name = Column(String(100), default="gemini-3.6-flash")
    
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    voice_duration_seconds = Column(Float, default=0.0)
    processing_duration_ms = Column(Float, default=0.0)
    estimated_cost_usd = Column(Float, default=0.0000)
    
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class AIEvaluationRecord(Base):
    """
    Internal AI Benchmark Evaluation Persistence (Section 5.37).
    Stores measurable and reviewable evaluation metrics across 4 domains:
    Conversational AI, Scheduling, EHR Integration, and Questionnaires.
    """
    __tablename__ = "ai_evaluation_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evaluation_id = Column(String(100), nullable=False, index=True)
    hospital_id = Column(String(36), nullable=True, index=True)
    session_id = Column(String(100), nullable=True)
    domain = Column(String(50), nullable=False, index=True)  # CONVERSATIONAL_AI, SCHEDULING, EHR_INTEGRATION, QUESTIONNAIRE
    test_case_name = Column(String(255), nullable=False)
    overall_score = Column(Float, default=1.0)
    passed = Column(Boolean, default=True)
    metrics_json = Column(Text, nullable=True)  # JSON dictionary of detailed sub-metrics
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class AIQualityFeedbackRecord(Base):
    """
    AI Quality Feedback Loop & Continuous Improvement Ledger (Section 5.38).
    Tracks the continuous engineering lifecycle:
    AI Interaction -> Outcome -> Evaluation -> Classification -> Review -> Improvement -> Re-Evaluation
    """
    __tablename__ = "ai_quality_feedback_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interaction_id = Column(String(100), nullable=False, index=True)
    hospital_id = Column(String(36), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    trace_id = Column(String(100), nullable=True, index=True)
    
    classification = Column(String(50), default="SUCCESS")  # SUCCESS, MINOR_FAILURE, CRITICAL_FAILURE, ESCALATED
    evaluation_score = Column(Float, default=1.0)
    root_cause_category = Column(String(100), nullable=True)  # PROMPT_AMBIGUITY, WORKFLOW_TIMEOUT, CAPABILITY_MISCONFIG, EHR_SCHEMA_MISMATCH, GUARDRAIL_TRIGGER, UNSUPPORTED_INTENT
    review_notes = Column(Text, nullable=True)
    
    improvement_type = Column(String(100), nullable=True)  # PROMPT_REFINEMENT, WORKFLOW_SCHEDULE_ADJUSTMENT, CAPABILITY_REGISTRATION, EHR_ADAPTER_MAPPING, GUARDRAIL_RULE
    improvement_details_json = Column(Text, nullable=True)
    improvement_status = Column(String(50), default="IDENTIFIED")  # IDENTIFIED, UNDER_REVIEW, IMPROVEMENT_APPLIED, VERIFIED_IN_RE_EVALUATION
    re_evaluation_id = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))





