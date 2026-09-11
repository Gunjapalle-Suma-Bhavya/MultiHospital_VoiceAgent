"""
Core Data Model Package (Step 7).

Defines the complete canonical entity catalog and hierarchical tree structure for the platform:
- Platform (Root)
  - Hospital (Admin, Department, Specialty, Doctor [Calendar, Availability, Blocked Slots, Questionnaire], Healthcare System Connection [Connector, Config, Mappings, Status], Appointments)
  - Patient (External Patient Mapping, User Context [Preferences, Conversation Summaries, Interaction Context])
  - Appointment (Doctor, Hospital, Calendar, Slot, External ID, Questionnaire Responses)
  - Questionnaire & Questionnaire Response
  - AI Conversation & AI Context
  - Capability & Capability Execution
  - EHR Integration Operation & Verification & Reconciliation Record
  - Workflow & Workflow Execution
  - Notification
  - AI Evaluation
  - Audit Event & Operational Event
"""

from typing import Dict, Any, List

# Complete hierarchical entity tree specification matching Step 7
CORE_DATA_MODEL_TREE: Dict[str, Any] = {
    "name": "Platform",
    "entity": "Platform",
    "model": "PlatformRecord",
    "table": "platform_records",
    "description": "Root platform operating entity, global system settings, and status.",
    "children": [
        {
            "name": "Hospital",
            "entity": "Hospital",
            "model": "Hospital",
            "table": "hospitals",
            "description": "Multi-tenant hospital organization with onboarding and configuration.",
            "children": [
                {
                    "name": "Hospital Admin",
                    "entity": "HospitalAdmin",
                    "model": "HospitalStaff",
                    "table": "hospital_staff",
                    "description": "Administrative personnel managing hospital resources."
                },
                {
                    "name": "Department",
                    "entity": "Department",
                    "model": "HospitalDepartment",
                    "table": "hospital_departments",
                    "description": "Clinical and operational departments within the hospital."
                },
                {
                    "name": "Specialty",
                    "entity": "Specialty",
                    "model": "HospitalSpecialty",
                    "table": "hospital_specialties",
                    "description": "Medical specialties offered by the hospital."
                },
                {
                    "name": "Doctor",
                    "entity": "Doctor",
                    "model": "Doctor",
                    "table": "doctors",
                    "description": "Practicing physicians affiliated with the hospital.",
                    "children": [
                        {
                            "name": "Calendar",
                            "entity": "Calendar",
                            "model": "DoctorCalendar",
                            "table": "doctor_calendars",
                            "description": "Doctor's consult and visit calendars."
                        },
                        {
                            "name": "Availability",
                            "entity": "Availability",
                            "model": "DoctorWorkingHour",
                            "table": "doctor_working_hours",
                            "description": "Weekly working shifts and appointment slots."
                        },
                        {
                            "name": "Blocked Slots",
                            "entity": "BlockedSlot",
                            "model": "BlockedSlot",
                            "table": "blocked_slots",
                            "description": "Periods reserved or blocked from patient booking."
                        },
                        {
                            "name": "Questionnaire",
                            "entity": "DoctorQuestionnaire",
                            "model": "DoctorApprovedQuestion",
                            "table": "doctor_approved_questions",
                            "description": "Doctor-approved specialty clinical intake questions."
                        }
                    ]
                },
                {
                    "name": "Healthcare System Connection",
                    "entity": "HealthcareSystemConnection",
                    "model": "EHRIntegrationConfig",
                    "table": "ehr_integration_configs",
                    "description": "EHR/EMR integration layer connector and configuration.",
                    "children": [
                        {
                            "name": "Connector",
                            "entity": "Connector",
                            "model": "EHRIntegrationConfig",
                            "table": "ehr_integration_configs",
                            "description": "Adapter driver (FHIR R4, Epic, Cerner, HL7)."
                        },
                        {
                            "name": "Configuration",
                            "entity": "Configuration",
                            "model": "EHRIntegrationConfig",
                            "table": "ehr_integration_configs",
                            "description": "Base URLs, sync rules, and auth credentials."
                        },
                        {
                            "name": "Identifier Mappings",
                            "entity": "IdentifierMapping",
                            "model": "EHRMapping",
                            "table": "ehr_mappings",
                            "description": "Internal UUID to external EHR ID cross-walks."
                        },
                        {
                            "name": "Integration Status",
                            "entity": "IntegrationStatus",
                            "model": "EHRSyncLog",
                            "table": "ehr_sync_logs",
                            "description": "Real-time sync logs and heartbeat verification."
                        }
                    ]
                },
                {
                    "name": "Appointments",
                    "entity": "HospitalAppointments",
                    "model": "Appointment",
                    "table": "appointments",
                    "description": "All clinical appointments booked for this hospital."
                }
            ]
        },
        {
            "name": "Patient",
            "entity": "Patient",
            "model": "PatientProfile",
            "table": "patient_profiles",
            "description": "Patient identity, contact details, and self-service profile.",
            "children": [
                {
                    "name": "External Patient Mapping",
                    "entity": "ExternalPatientMapping",
                    "model": "EHRMapping",
                    "table": "ehr_mappings",
                    "description": "Mapping from patient phone/profile to EHR MRN."
                },
                {
                    "name": "User Context",
                    "entity": "UserContext",
                    "model": "PatientSessionState",
                    "table": "patient_session_states",
                    "description": "Conversational state and multi-tier memory.",
                    "children": [
                        {
                            "name": "Preferences",
                            "entity": "PatientPreferences",
                            "model": "PatientProfile",
                            "table": "patient_profiles",
                            "description": "Time window, language, and channel preferences."
                        },
                        {
                            "name": "Conversation Summaries",
                            "entity": "ConversationSummaries",
                            "model": "PatientProfile",
                            "table": "patient_profiles",
                            "description": "Summarized interactions from previous sessions."
                        },
                        {
                            "name": "Relevant Interaction Context",
                            "entity": "InteractionContext",
                            "model": "PatientIntakeRecord",
                            "table": "patient_intake_records",
                            "description": "Intake notes and active session memory."
                        }
                    ]
                }
            ]
        },
        {
            "name": "Appointment",
            "entity": "Appointment",
            "model": "Appointment",
            "table": "appointments",
            "description": "Scheduled clinical consultation linking doctor, hospital, and patient.",
            "children": [
                {
                    "name": "Doctor",
                    "entity": "AppointmentDoctor",
                    "model": "Doctor",
                    "table": "doctors",
                    "description": "Assigned doctor for consultation."
                },
                {
                    "name": "Hospital",
                    "entity": "AppointmentHospital",
                    "model": "Hospital",
                    "table": "hospitals",
                    "description": "Location facility for the visit."
                },
                {
                    "name": "Calendar",
                    "entity": "AppointmentCalendar",
                    "model": "DoctorCalendar",
                    "table": "doctor_calendars",
                    "description": "Specific calendar holding the booking."
                },
                {
                    "name": "Slot",
                    "entity": "AppointmentSlot",
                    "model": "Appointment",
                    "table": "appointments",
                    "description": "Specific start and end datetime window."
                },
                {
                    "name": "External Appointment ID",
                    "entity": "ExternalAppointmentId",
                    "model": "Appointment",
                    "table": "appointments",
                    "description": "Verified external EHR appointment identifier."
                },
                {
                    "name": "Questionnaire Responses",
                    "entity": "AppointmentQuestionnaireResponses",
                    "model": "PatientQuestionnaireResponse",
                    "table": "patient_questionnaire_responses",
                    "description": "Pre-visit clinical intake questionnaire submissions."
                }
            ]
        },
        {
            "name": "Questionnaire",
            "entity": "Questionnaire",
            "model": "HospitalQuestionnaire",
            "table": "hospital_questionnaires",
            "description": "Clinician-approved specialty intake questionnaire forms."
        },
        {
            "name": "Questionnaire Response",
            "entity": "QuestionnaireResponse",
            "model": "PatientQuestionnaireResponse",
            "table": "patient_questionnaire_responses",
            "description": "Submitted patient answers to clinical questionnaires."
        },
        {
            "name": "AI Conversation",
            "entity": "AIConversation",
            "model": "AIConversationRecord",
            "table": "ai_conversations",
            "description": "End-to-end voice or chat patient intake conversation session."
        },
        {
            "name": "AI Context",
            "entity": "AIContext",
            "model": "AIContextRecord",
            "table": "ai_context_records",
            "description": "Extracted slots, intent state, and conversational context snapshots."
        },
        {
            "name": "Capability",
            "entity": "Capability",
            "model": "CapabilityRecord",
            "table": "capabilities",
            "description": "Registered platform capability tools callable by AI agents."
        },
        {
            "name": "Capability Execution",
            "entity": "CapabilityExecution",
            "model": "CapabilityExecutionRecord",
            "table": "capability_executions",
            "description": "Audit record of capability invocations and execution results."
        },
        {
            "name": "EHR Integration Operation",
            "entity": "EHRIntegrationOperation",
            "model": "EHRSyncLog",
            "table": "ehr_sync_logs",
            "description": "Outbound and inbound sync operations with external EHR systems."
        },
        {
            "name": "Integration Verification",
            "entity": "IntegrationVerification",
            "model": "IntegrationVerificationRecord",
            "table": "integration_verification_records",
            "description": "Authoritative field-level verification against external health systems."
        },
        {
            "name": "Reconciliation Record",
            "entity": "ReconciliationRecord",
            "model": "ReconciliationRecord",
            "table": "reconciliation_records",
            "description": "Safe anti-double-booking and status mismatch resolution ledger."
        },
        {
            "name": "Workflow",
            "entity": "Workflow",
            "model": "WorkflowInstance",
            "table": "workflow_instances",
            "description": "Event-driven asynchronous operational workflows."
        },
        {
            "name": "Workflow Execution",
            "entity": "WorkflowExecution",
            "model": "WorkflowStepLog",
            "table": "workflow_step_logs",
            "description": "Granular execution steps and status logs for running workflows."
        },
        {
            "name": "Notification",
            "entity": "Notification",
            "model": "NotificationRecord",
            "table": "notification_records",
            "description": "Multi-role communications dispatched via SMS, email, and voice."
        },
        {
            "name": "AI Evaluation",
            "entity": "AIEvaluation",
            "model": "AIEvaluationRecord",
            "table": "ai_evaluation_records",
            "description": "Automated AI benchmark evaluations across conversational domains."
        },
        {
            "name": "Audit Event",
            "entity": "AuditEvent",
            "model": "AuditLog",
            "table": "audit_logs",
            "description": "Immutable operational audit events supporting the 7 audit objectives."
        },
        {
            "name": "Operational Event",
            "entity": "OperationalEvent",
            "model": "PlatformEventRecord",
            "table": "platform_event_records",
            "description": "Decoupled system domain events published on the internal event bus."
        }
    ]
}
