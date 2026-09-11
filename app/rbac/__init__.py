"""
Role-Based Access Control (RBAC) Package (Step 6).

Enforces strict role boundaries across the 4 platform personas:
1. Platform Admin
   - Approve hospitals
   - Suspend hospitals
   - View global analytics
   - Manage platform configuration
   - Review audit events
   - Review operational health
   - Review AI evaluations
   - Review EHR integration health

2. Hospital Admin
   - Manage hospital profile
   - Create doctors
   - Manage calendars
   - Configure availability
   - Manage questionnaires
   - View appointments
   - View hospital analytics
   - Configure approved workflows
   - Manage staff
   - Configure supported healthcare-system integrations
   - Boundary: Cannot access another hospital's private data.

3. Doctor
   - Manage own calendar
   - Block slots
   - Configure approved questionnaires
   - View own appointments
   - View authorized patient responses
   - Boundary: Cannot access other doctors' calendars, slots, or appointments.

4. Patient
   - Manage own profile
   - Book appointments
   - Reschedule
   - Cancel
   - Complete questionnaires
   - View own appointments
   - Manage appropriate preferences
   - Boundary: Cannot access other patients' profiles, appointments, or responses.
"""

from enum import Enum
from typing import Dict, Set, List, Any


class UserRole(str, Enum):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    HOSPITAL_ADMIN = "HOSPITAL_ADMIN"
    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"


class Permission(str, Enum):
    # Platform Admin Permissions (8 operations)
    APPROVE_HOSPITALS = "APPROVE_HOSPITALS"
    SUSPEND_HOSPITALS = "SUSPEND_HOSPITALS"
    VIEW_GLOBAL_ANALYTICS = "VIEW_GLOBAL_ANALYTICS"
    MANAGE_PLATFORM_CONFIG = "MANAGE_PLATFORM_CONFIG"
    REVIEW_AUDIT_EVENTS = "REVIEW_AUDIT_EVENTS"
    REVIEW_OPERATIONAL_HEALTH = "REVIEW_OPERATIONAL_HEALTH"
    REVIEW_AI_EVALUATIONS = "REVIEW_AI_EVALUATIONS"
    REVIEW_EHR_INTEGRATION_HEALTH = "REVIEW_EHR_INTEGRATION_HEALTH"

    # Hospital Admin Permissions (10 operations)
    MANAGE_HOSPITAL_PROFILE = "MANAGE_HOSPITAL_PROFILE"
    CREATE_DOCTORS = "CREATE_DOCTORS"
    MANAGE_CALENDARS = "MANAGE_CALENDARS"
    CONFIGURE_AVAILABILITY = "CONFIGURE_AVAILABILITY"
    MANAGE_QUESTIONNAIRES = "MANAGE_QUESTIONNAIRES"
    VIEW_HOSPITAL_APPOINTMENTS = "VIEW_HOSPITAL_APPOINTMENTS"
    VIEW_HOSPITAL_ANALYTICS = "VIEW_HOSPITAL_ANALYTICS"
    CONFIGURE_APPROVED_WORKFLOWS = "CONFIGURE_APPROVED_WORKFLOWS"
    MANAGE_STAFF = "MANAGE_STAFF"
    CONFIGURE_HEALTHCARE_INTEGRATIONS = "CONFIGURE_HEALTHCARE_INTEGRATIONS"

    # Doctor Permissions (5 operations)
    MANAGE_OWN_CALENDAR = "MANAGE_OWN_CALENDAR"
    BLOCK_SLOTS = "BLOCK_SLOTS"
    CONFIGURE_APPROVED_QUESTIONNAIRES = "CONFIGURE_APPROVED_QUESTIONNAIRES"
    VIEW_OWN_APPOINTMENTS = "VIEW_OWN_APPOINTMENTS"
    VIEW_AUTHORIZED_PATIENT_RESPONSES = "VIEW_AUTHORIZED_PATIENT_RESPONSES"

    # Patient Permissions (7 operations)
    MANAGE_OWN_PROFILE = "MANAGE_OWN_PROFILE"
    BOOK_APPOINTMENTS = "BOOK_APPOINTMENTS"
    RESCHEDULE_APPOINTMENTS = "RESCHEDULE_APPOINTMENTS"
    CANCEL_APPOINTMENTS = "CANCEL_APPOINTMENTS"
    COMPLETE_QUESTIONNAIRES = "COMPLETE_QUESTIONNAIRES"
    VIEW_OWN_PATIENT_APPOINTMENTS = "VIEW_OWN_PATIENT_APPOINTMENTS"
    MANAGE_PREFERENCES = "MANAGE_PREFERENCES"


# Mapping from UserRole to exact permitted operations
ROLE_PERMISSIONS_MAP: Dict[UserRole, Set[Permission]] = {
    UserRole.PLATFORM_ADMIN: {
        Permission.APPROVE_HOSPITALS,
        Permission.SUSPEND_HOSPITALS,
        Permission.VIEW_GLOBAL_ANALYTICS,
        Permission.MANAGE_PLATFORM_CONFIG,
        Permission.REVIEW_AUDIT_EVENTS,
        Permission.REVIEW_OPERATIONAL_HEALTH,
        Permission.REVIEW_AI_EVALUATIONS,
        Permission.REVIEW_EHR_INTEGRATION_HEALTH,
    },
    UserRole.HOSPITAL_ADMIN: {
        Permission.MANAGE_HOSPITAL_PROFILE,
        Permission.CREATE_DOCTORS,
        Permission.MANAGE_CALENDARS,
        Permission.CONFIGURE_AVAILABILITY,
        Permission.MANAGE_QUESTIONNAIRES,
        Permission.VIEW_HOSPITAL_APPOINTMENTS,
        Permission.VIEW_HOSPITAL_ANALYTICS,
        Permission.CONFIGURE_APPROVED_WORKFLOWS,
        Permission.MANAGE_STAFF,
        Permission.CONFIGURE_HEALTHCARE_INTEGRATIONS,
    },
    UserRole.DOCTOR: {
        Permission.MANAGE_OWN_CALENDAR,
        Permission.BLOCK_SLOTS,
        Permission.CONFIGURE_APPROVED_QUESTIONNAIRES,
        Permission.VIEW_OWN_APPOINTMENTS,
        Permission.VIEW_AUTHORIZED_PATIENT_RESPONSES,
    },
    UserRole.PATIENT: {
        Permission.MANAGE_OWN_PROFILE,
        Permission.BOOK_APPOINTMENTS,
        Permission.RESCHEDULE_APPOINTMENTS,
        Permission.CANCEL_APPOINTMENTS,
        Permission.COMPLETE_QUESTIONNAIRES,
        Permission.VIEW_OWN_PATIENT_APPOINTMENTS,
        Permission.MANAGE_PREFERENCES,
    },
}

# Role Boundary Rules Descriptions
ROLE_BOUNDARY_RULES: Dict[UserRole, Dict[str, Any]] = {
    UserRole.PLATFORM_ADMIN: {
        "title": "Platform Administrator",
        "description": "Global operational oversight and platform governance without unredacted clinical PHI exposure.",
        "allowed_count": 8,
        "boundary_rule": "Global authority across platform configuration, approval, and health metrics.",
    },
    UserRole.HOSPITAL_ADMIN: {
        "title": "Hospital Administrator",
        "description": "Multi-tenant administration of hospital staff, doctors, calendars, availability, questionnaires, and analytics.",
        "allowed_count": 10,
        "boundary_rule": "Strict multi-tenant data isolation: Cannot access or mutate another hospital's private data.",
    },
    UserRole.DOCTOR: {
        "title": "Doctor",
        "description": "Clinical practitioner managing assigned appointments, personal calendar availability, and patient intake answers.",
        "allowed_count": 5,
        "boundary_rule": "Doctor boundary isolation: Cannot access or modify other doctors' calendars, blocked slots, or appointments.",
    },
    UserRole.PATIENT: {
        "title": "Patient",
        "description": "Self-service consumer booking visits, managing profile/preferences, and completing clinical questionnaires.",
        "allowed_count": 7,
        "boundary_rule": "Patient boundary isolation: Cannot access or modify appointments, profiles, or questionnaires of other patients.",
    },
}
