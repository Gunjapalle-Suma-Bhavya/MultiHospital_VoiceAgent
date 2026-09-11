"""
Complete 20-Step End-to-End Patient Workflow Package (Step 8).

Defines:
1. Canonical 20-step workflow lifecycle definitions and schemas.
2. Channels (Web Voice, Telephone).
3. Clinical intent, symptom, and calendar validation models.
4. 5-point authoritative EHR verification models.
5. Standard simulation presets.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class WorkflowChannel(str, Enum):
    WEB_VOICE = "WEB_VOICE"
    TELEPHONE = "TELEPHONE"


class WorkflowStepEnum(str, Enum):
    STEP_1_REGISTRATION = "STEP_1_REGISTRATION"
    STEP_2_START_CONVERSATION = "STEP_2_START_CONVERSATION"
    STEP_3_DESCRIBE_REQUIREMENT = "STEP_3_DESCRIBE_REQUIREMENT"
    STEP_4_UNDERSTAND_INTENT = "STEP_4_UNDERSTAND_INTENT"
    STEP_5_RESOLVE_CONTEXT = "STEP_5_RESOLVE_CONTEXT"
    STEP_6_FIND_DOCTORS = "STEP_6_FIND_DOCTORS"
    STEP_7_CHECK_CALENDARS = "STEP_7_CHECK_CALENDARS"
    STEP_8_PRESENT_CHOICES = "STEP_8_PRESENT_CHOICES"
    STEP_9_PATIENT_CHOOSES = "STEP_9_PATIENT_CHOOSES"
    STEP_10_CONFIRM_BEFORE_BOOKING = "STEP_10_CONFIRM_BEFORE_BOOKING"
    STEP_11_BOOK_APPOINTMENT = "STEP_11_BOOK_APPOINTMENT"
    STEP_12_VERIFY_EXTERNAL_EHR = "STEP_12_VERIFY_EXTERNAL_EHR"
    STEP_13_SYNCHRONIZE_STATE = "STEP_13_SYNCHRONIZE_STATE"
    STEP_14_CONFIRM_TO_PATIENT = "STEP_14_CONFIRM_TO_PATIENT"
    STEP_15_TRIGGER_FOLLOW_UP = "STEP_15_TRIGGER_FOLLOW_UP"
    STEP_16_PRE_VISIT_QUESTIONNAIRE = "STEP_16_PRE_VISIT_QUESTIONNAIRE"
    STEP_17_PATIENT_RESPONDS = "STEP_17_PATIENT_RESPONDS"
    STEP_18_STORE_RESPONSES = "STEP_18_STORE_RESPONSES"
    STEP_19_DOCTOR_REVIEWS = "STEP_19_DOCTOR_REVIEWS"
    STEP_20_ANALYTICS_AND_AUDIT = "STEP_20_ANALYTICS_AND_AUDIT"


WORKFLOW_STEP_TITLES = {
    1: "Patient Registration",
    2: "Start Conversation",
    3: "Describe Requirement",
    4: "Understand Intent",
    5: "Resolve Context",
    6: "Find Doctors",
    7: "Check Calendars",
    8: "Present Choices",
    9: "Patient Chooses",
    10: "Confirm Before Booking",
    11: "Book (EHR Integrated)",
    12: "Verify (5-Point Authoritative Match)",
    13: "Synchronize State",
    14: "Confirm to Patient",
    15: "Trigger Follow-Up Workflow",
    16: "Pre-Visit Questionnaire",
    17: "Patient Responds",
    18: "Store Responses",
    19: "Doctor Reviews",
    20: "Analytics & Audit Trail",
}


class WorkflowExecutionRequest(BaseModel):
    phone_number: str = Field(default="+1-555-0199", description="Patient phone number")
    patient_name: str = Field(default="Alex Miller", description="Patient full name")
    channel: WorkflowChannel = Field(default=WorkflowChannel.WEB_VOICE, description="Access channel")
    utterance: str = Field(
        default="I've been having knee pain and I'd like to see a doctor this week.",
        description="Patient spoken requirement"
    )
    selected_choice_index: int = Field(default=0, description="0 for first doctor/slot, 1 for second")
    questionnaire_answers: Optional[Dict[str, str]] = Field(
        default_factory=lambda: {
            "knee_pain_duration": "About 3 weeks, worsens while climbing stairs",
            "previous_surgeries": "None",
            "current_medications": "Ibuprofen as needed"
        },
        description="Responses to pre-visit clinical questionnaire"
    )


# Standard Clinical Presets for Testing and Demo
CLINICAL_WORKFLOW_PRESETS = [
    {
        "id": "PRESET_KNEE_ORTHO",
        "title": "Knee Pain / Orthopedics (Step 8 Example)",
        "description": "Patient experiencing knee pain seeking an orthopedic specialist this week.",
        "utterance": "I've been having knee pain and I'd like to see a doctor this week.",
        "channel": "WEB_VOICE",
        "patient_name": "Alex Miller",
        "phone_number": "+1-555-0199",
        "inferred_specialty": "Orthopedics",
        "time_preference": "THIS_WEEK",
    },
    {
        "id": "PRESET_CARDIOLOGY_CHEST",
        "title": "Mild Palpitations / Cardiology",
        "description": "Patient describing mild palpitations after exercise looking for cardiologist consult.",
        "utterance": "I've had mild palpitations during jogging and want to consult a cardiologist.",
        "channel": "TELEPHONE",
        "patient_name": "Rachel Adams",
        "phone_number": "+1-555-0288",
        "inferred_specialty": "Cardiology",
        "time_preference": "NEXT_AVAILABLE",
    },
    {
        "id": "PRESET_DERMATOLOGY_RASH",
        "title": "Skin Rash / Dermatology",
        "description": "Patient reporting an itchy skin rash needing dermatologist assessment.",
        "utterance": "I have an itchy skin rash on my arm and need an appointment with a skin specialist.",
        "channel": "WEB_VOICE",
        "patient_name": "David Clark",
        "phone_number": "+1-555-0377",
        "inferred_specialty": "Dermatology",
        "time_preference": "THIS_WEEK",
    }
]
