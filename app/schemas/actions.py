"""
Input and Output schemas for Action-Oriented AI capabilities (Section 1.4).
Each action has strict Pydantic schemas, validation rules, and audit requirements.
"""

from datetime import datetime, date, time
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    SEARCH_HOSPITALS = "SEARCH_HOSPITALS"
    SEARCH_DOCTORS = "SEARCH_DOCTORS"
    CHECK_AVAILABILITY = "CHECK_AVAILABILITY"
    GET_APPOINTMENT_INFO = "GET_APPOINTMENT_INFO"
    CREATE_APPOINTMENT = "CREATE_APPOINTMENT"
    RESCHEDULE_APPOINTMENT = "RESCHEDULE_APPOINTMENT"
    CANCEL_APPOINTMENT = "CANCEL_APPOINTMENT"
    GET_QUESTIONNAIRE = "GET_QUESTIONNAIRE"
    SUBMIT_QUESTIONNAIRE_RESPONSE = "SUBMIT_QUESTIONNAIRE_RESPONSE"
    SEND_NOTIFICATION = "SEND_NOTIFICATION"
    INITIATE_WORKFLOW = "INITIATE_WORKFLOW"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"
    SYNC_EHR_APPOINTMENT = "SYNC_EHR_APPOINTMENT"


class ActionBaseInput(BaseModel):
    session_id: str
    patient_id: str
    idempotency_key: Optional[str] = None


class ActionBaseOutput(BaseModel):
    success: bool
    action_type: ActionType
    message: str
    error_code: Optional[str] = None
    audit_id: Optional[str] = None


# --- 1. Search Hospitals ---
class SearchHospitalsInput(ActionBaseInput):
    query: Optional[str] = None
    location_near: Optional[str] = None

class HospitalDTO(BaseModel):
    id: str
    name: str
    code: str
    timezone: str

class SearchHospitalsOutput(ActionBaseOutput):
    hospitals: List[HospitalDTO] = []


# --- 2. Search Doctors ---
class SearchDoctorsInput(ActionBaseInput):
    hospital_id: Optional[str] = None
    specialty: Optional[str] = None
    doctor_name: Optional[str] = None

class DoctorDTO(BaseModel):
    id: str
    hospital_id: str
    hospital_name: str
    name: str
    specialty: str
    appointment_duration: int

class SearchDoctorsOutput(ActionBaseOutput):
    doctors: List[DoctorDTO] = []


# --- 3. Check Availability ---
class CheckAvailabilityInput(ActionBaseInput):
    doctor_id: str
    target_date: date
    time_window: Optional[str] = "ANYTIME"  # MORNING, AFTERNOON, EVENING, ANYTIME

class TimeSlotDTO(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    is_available: bool

class CheckAvailabilityOutput(ActionBaseOutput):
    doctor_id: str
    target_date: date
    available_slots: List[TimeSlotDTO] = []


# --- 4. Get Appointment Info ---
class GetAppointmentInfoInput(ActionBaseInput):
    appointment_id: Optional[str] = None

class GetAppointmentInfoOutput(ActionBaseOutput):
    appointment_id: Optional[str] = None
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None
    start_datetime: Optional[datetime] = None
    status: Optional[str] = None


# --- 5. Create Appointment ---
class CreateAppointmentInput(ActionBaseInput):
    hospital_id: str
    doctor_id: str
    start_datetime: datetime
    patient_name: str
    patient_phone: str
    patient_email: Optional[str] = None

class CreateAppointmentOutput(ActionBaseOutput):
    appointment_id: Optional[str] = None
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None
    start_datetime: Optional[datetime] = None


# --- 6. Reschedule Appointment ---
class RescheduleAppointmentInput(ActionBaseInput):
    appointment_id: str
    new_start_datetime: datetime

class RescheduleAppointmentOutput(ActionBaseOutput):
    appointment_id: str
    old_start_datetime: Optional[datetime] = None
    new_start_datetime: Optional[datetime] = None


# --- 7. Cancel Appointment ---
class CancelAppointmentInput(ActionBaseInput):
    appointment_id: str
    reason: Optional[str] = None

class CancelAppointmentOutput(ActionBaseOutput):
    appointment_id: str
    cancelled_at: datetime = Field(default_factory=datetime.utcnow)


# --- 8. Get Questionnaire & 9. Submit Questionnaire ---
class GetQuestionnaireInput(ActionBaseInput):
    hospital_id: str
    specialty: str

class QuestionnaireDTO(BaseModel):
    questionnaire_id: str
    questions: List[Dict[str, Any]]

class GetQuestionnaireOutput(ActionBaseOutput):
    questionnaire: Optional[QuestionnaireDTO] = None

class SubmitQuestionnaireInput(ActionBaseInput):
    appointment_id: str
    patient_reported_summary: str
    answers: Dict[str, Any]

class SubmitQuestionnaireOutput(ActionBaseOutput):
    intake_record_id: Optional[str] = None


# --- 10. Send Notification ---
class SendNotificationInput(ActionBaseInput):
    recipient_phone: str
    channel: str = "SMS"  # SMS, VOICE, EMAIL
    message_text: str

class SendNotificationOutput(ActionBaseOutput):
    notification_id: Optional[str] = None


# --- 11. Escalate to Human ---
class EscalateToHumanInput(ActionBaseInput):
    reason: str
    priority: str = "NORMAL"  # URGENT, NORMAL

class EscalateToHumanOutput(ActionBaseOutput):
    transfer_target_phone: Optional[str] = None
    escalation_ticket_id: Optional[str] = None


# --- 12. Sync EHR ---
class SyncEHRAppointmentInput(ActionBaseInput):
    appointment_id: str

class SyncEHRAppointmentOutput(ActionBaseOutput):
    ehr_sync_status: str
    ehr_reference_id: Optional[str] = None
