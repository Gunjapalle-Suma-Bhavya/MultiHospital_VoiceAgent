"""
Section 15: Reliability & Failure Handling Package.

Comprehensive real-world failure handling across all 5 domains:
1. Voice Failures (Noisy audio, patient interruption, silence, unclear speech, call drop)
2. Agent Failures (Capability failure, missing information, ambiguous request, unsupported request, long-running operation, context resolution failure)
3. Scheduling Failures (Slot becomes unavailable, double-booking attempt, calendar conflict, doctor becomes unavailable)
4. EHR / External Integration Failures (API timeout, auth failure, authorization failure, expired credentials, rate limit, network error, EHR unavailable, schema mismatch, mapping failure, patient not found, provider not found, appointment conflict, duplicate request, partial success, unknown external result, state inconsistency)
5. Workflow Failures (Execution timeout, external service failure, notification failure, duplicate execution, dependency unavailable)

Enforces:
- 15.1 Controlled Retry & Recovery Policies with strict anti-duplicate guarantees
- 15.2 Idempotency for critical operations (create, cancel, reschedule, notifications, workflows, EHR sync)
- 15.3 Strict Booking Verification (Never tell patient "Your appointment is booked" without verified external state)
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class FailureDomain(str, Enum):
    VOICE = "VOICE"
    AGENT = "AGENT"
    SCHEDULING = "SCHEDULING"
    EHR_INTEGRATION = "EHR_INTEGRATION"
    WORKFLOW = "WORKFLOW"


class VoiceFailureType(str, Enum):
    NOISY_AUDIO = "NOISY_AUDIO"
    PATIENT_INTERRUPTION = "PATIENT_INTERRUPTION"
    SILENCE = "SILENCE"
    UNCLEAR_SPEECH = "UNCLEAR_SPEECH"
    CALL_DROP = "CALL_DROP"


class AgentFailureType(str, Enum):
    CAPABILITY_FAILURE = "CAPABILITY_FAILURE"
    MISSING_INFORMATION = "MISSING_INFORMATION"
    AMBIGUOUS_REQUEST = "AMBIGUOUS_REQUEST"
    UNSUPPORTED_REQUEST = "UNSUPPORTED_REQUEST"
    LONG_RUNNING_OPERATION = "LONG_RUNNING_OPERATION"
    CONTEXT_RESOLUTION_FAILURE = "CONTEXT_RESOLUTION_FAILURE"


class SchedulingFailureType(str, Enum):
    SLOT_BECOMES_UNAVAILABLE = "SLOT_BECOMES_UNAVAILABLE"
    DOUBLE_BOOKING_ATTEMPT = "DOUBLE_BOOKING_ATTEMPT"
    CALENDAR_CONFLICT = "CALENDAR_CONFLICT"
    DOCTOR_BECOMES_UNAVAILABLE = "DOCTOR_BECOMES_UNAVAILABLE"


class EHRFailureType(str, Enum):
    API_TIMEOUT = "API_TIMEOUT"
    AUTHENTICATION_FAILURE = "AUTHENTICATION_FAILURE"
    AUTHORIZATION_FAILURE = "AUTHORIZATION_FAILURE"
    EXPIRED_CREDENTIALS = "EXPIRED_CREDENTIALS"
    RATE_LIMIT = "RATE_LIMIT"
    NETWORK_ERROR = "NETWORK_ERROR"
    EHR_UNAVAILABLE = "EHR_UNAVAILABLE"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    MAPPING_FAILURE = "MAPPING_FAILURE"
    PATIENT_NOT_FOUND = "PATIENT_NOT_FOUND"
    PROVIDER_NOT_FOUND = "PROVIDER_NOT_FOUND"
    APPOINTMENT_CONFLICT = "APPOINTMENT_CONFLICT"
    DUPLICATE_REQUEST = "DUPLICATE_REQUEST"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    UNKNOWN_EXTERNAL_RESULT = "UNKNOWN_EXTERNAL_RESULT"
    STATE_INCONSISTENCY = "STATE_INCONSISTENCY"


class WorkflowFailureType(str, Enum):
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"
    EXTERNAL_SERVICE_FAILURE = "EXTERNAL_SERVICE_FAILURE"
    NOTIFICATION_FAILURE = "NOTIFICATION_FAILURE"
    DUPLICATE_EXECUTION = "DUPLICATE_EXECUTION"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"


class FailureHandlingStrategy(str, Enum):
    RETRY_WITH_BACKOFF = "RETRY_WITH_BACKOFF"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"
    QUERY_EXTERNAL_STATE = "QUERY_EXTERNAL_STATE"
    CLARIFY_WITH_PATIENT = "CLARIFY_WITH_PATIENT"
    OFFER_ALTERNATIVE_SLOT = "OFFER_ALTERNATIVE_SLOT"
    RECONCILIATION = "RECONCILIATION"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"
    TERMINATE_SAFE = "TERMINATE_SAFE"


class FailureResolutionPlan(BaseModel):
    failure_domain: FailureDomain
    failure_type: str
    is_retryable: bool
    recommended_strategy: FailureHandlingStrategy
    patient_facing_message: str
    anti_duplicate_guarantees: List[str]
    technical_action: str
    retry_limit: int = 3
