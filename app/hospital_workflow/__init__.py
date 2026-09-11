"""
Complete 23-Stage Hospital Workflow Package (Step 9).

Defines:
1. Canonical 23-stage hospital organizational lifecycle definitions.
2. Schemas and input models for hospital workflow execution.
3. Standard clinical hospital presets.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class HospitalWorkflowStepEnum(str, Enum):
    STAGE_1_HOSPITAL_REGISTERS = "STAGE_1_HOSPITAL_REGISTERS"
    STAGE_2_SUBMITS_DETAILS = "STAGE_2_SUBMITS_DETAILS"
    STAGE_3_PLATFORM_ADMIN_REVIEWS = "STAGE_3_PLATFORM_ADMIN_REVIEWS"
    STAGE_4_HOSPITAL_APPROVED = "STAGE_4_HOSPITAL_APPROVED"
    STAGE_5_HOSPITAL_ADMIN_LOGIN = "STAGE_5_HOSPITAL_ADMIN_LOGIN"
    STAGE_6_CONFIGURE_HOSPITAL = "STAGE_6_CONFIGURE_HOSPITAL"
    STAGE_7_CREATE_DOCTORS = "STAGE_7_CREATE_DOCTORS"
    STAGE_8_DOCTORS_CONFIGURE_CALENDARS = "STAGE_8_DOCTORS_CONFIGURE_CALENDARS"
    STAGE_9_CONFIGURE_AVAILABILITY = "STAGE_9_CONFIGURE_AVAILABILITY"
    STAGE_10_CONFIGURE_BLOCKED_PERIODS = "STAGE_10_CONFIGURE_BLOCKED_PERIODS"
    STAGE_11_CREATE_QUESTIONNAIRES = "STAGE_11_CREATE_QUESTIONNAIRES"
    STAGE_12_CONFIGURE_EHR_INTEGRATION = "STAGE_12_CONFIGURE_EHR_INTEGRATION"
    STAGE_13_CONFIGURE_WORKFLOWS = "STAGE_13_CONFIGURE_WORKFLOWS"
    STAGE_14_PUBLISH_AVAILABILITY = "STAGE_14_PUBLISH_AVAILABILITY"
    STAGE_15_PATIENTS_DISCOVER_HOSPITAL = "STAGE_15_PATIENTS_DISCOVER_HOSPITAL"
    STAGE_16_AI_BOOKS_APPOINTMENTS = "STAGE_16_AI_BOOKS_APPOINTMENTS"
    STAGE_17_EHR_SYNCHRONIZATION = "STAGE_17_EHR_SYNCHRONIZATION"
    STAGE_18_VERIFICATION = "STAGE_18_VERIFICATION"
    STAGE_19_WORKFLOW_EXECUTES = "STAGE_19_WORKFLOW_EXECUTES"
    STAGE_20_NOTIFICATIONS = "STAGE_20_NOTIFICATIONS"
    STAGE_21_DOCTORS_RECEIVE_APPOINTMENTS = "STAGE_21_DOCTORS_RECEIVE_APPOINTMENTS"
    STAGE_22_DOCTORS_REVIEW_PRE_VISIT_INFO = "STAGE_22_DOCTORS_REVIEW_PRE_VISIT_INFO"
    STAGE_23_HOSPITAL_MONITORS_ANALYTICS = "STAGE_23_HOSPITAL_MONITORS_ANALYTICS"


HOSPITAL_WORKFLOW_STEP_TITLES = {
    1: "Hospital Registers",
    2: "Submits Details",
    3: "Platform Admin Reviews",
    4: "Hospital Approved",
    5: "Hospital Admin Login",
    6: "Configure Hospital",
    7: "Create Doctors",
    8: "Doctors Configure Calendars",
    9: "Configure Availability",
    10: "Configure Blocked Periods",
    11: "Create Questionnaires",
    12: "Configure EHR / Healthcare-System Integration",
    13: "Configure Workflows",
    14: "Publish Availability",
    15: "Patients Discover Hospital",
    16: "AI Books Appointments",
    17: "EHR / External System Synchronization",
    18: "Verification",
    19: "Workflow Executes",
    20: "Notifications",
    21: "Doctors Receive Appointments",
    22: "Doctors Review Pre-Visit Information",
    23: "Hospital Monitors Analytics",
}


class HospitalWorkflowExecutionRequest(BaseModel):
    hospital_name: str = Field(default="St. Jude Health System", description="Hospital name")
    hospital_code: str = Field(default="STJUDE", description="Hospital unique uppercase code")
    contact_email: str = Field(default="contact@stjude-health.org", description="Hospital contact email")
    admin_name: str = Field(default="Dr. Marcus Vance", description="Lead Hospital Administrator name")
    admin_email: str = Field(default="marcus.vance@stjude-health.org", description="Lead Administrator email")
    department_name: str = Field(default="Cardiovascular Sciences", description="Primary department")
    specialty_name: str = Field(default="Cardiology", description="Primary specialty")
    doctor_name: str = Field(default="Dr. Olivia Chen", description="Primary doctor name")
    doctor_email: str = Field(default="olivia.chen@stjude-health.org", description="Doctor email")
    ehr_adapter_type: str = Field(default="MOCK_EHR", description="EHR adapter (MOCK_EHR, FHIR_R4, EPIC, CERNER)")


HOSPITAL_WORKFLOW_PRESETS = [
    {
        "id": "PRESET_ST_JUDE",
        "title": "St. Jude Health System (Cardiology & Heart Center)",
        "hospital_name": "St. Jude Health System",
        "hospital_code": "STJUDE",
        "contact_email": "contact@stjude-health.org",
        "admin_name": "Dr. Marcus Vance",
        "admin_email": "marcus.vance@stjude-health.org",
        "department_name": "Cardiovascular Sciences",
        "specialty_name": "Cardiology",
        "doctor_name": "Dr. Olivia Chen",
        "ehr_adapter_type": "MOCK_EHR",
    },
    {
        "id": "PRESET_METRO_GENERAL",
        "title": "Metro General Hospital (Orthopedics & Joint Clinic)",
        "hospital_name": "Metro General Hospital",
        "hospital_code": "METROGEN",
        "contact_email": "admin@metrogen.org",
        "admin_name": "Sarah Jenkins",
        "admin_email": "s.jenkins@metrogen.org",
        "department_name": "Orthopedic Surgery",
        "specialty_name": "Orthopedics",
        "doctor_name": "Dr. Vikram Patel",
        "ehr_adapter_type": "FHIR_R4",
    },
    {
        "id": "PRESET_CARE_REGIONAL",
        "title": "Care Regional Medical Center (Neurology & Spine)",
        "hospital_name": "Care Regional Medical Center",
        "hospital_code": "CAREREG",
        "contact_email": "ops@careregional.com",
        "admin_name": "Robert Sterling",
        "admin_email": "r.sterling@careregional.com",
        "department_name": "Neurological Sciences",
        "specialty_name": "Neurology",
        "doctor_name": "Dr. Fiona Gallagher",
        "ehr_adapter_type": "EPIC",
    }
]
