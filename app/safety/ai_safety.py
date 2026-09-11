"""
AI Safety & Clinical Boundaries Engine (Section 18).

Core Principles:
The AI is an administrative and conversational healthcare assistant, NOT a replacement for a clinician.

Allowed Capabilities:
- Appointment discovery
- Scheduling
- Rescheduling
- Cancellation
- Administrative FAQs
- Approved pre-visit questions
- Recording patient responses
- Workflow initiation
- Notifications
- EHR appointment operations
- External-system synchronization
- Escalation

Not Autonomous / Prohibited Capabilities:
- Diagnosis
- Treatment decisions
- Medication changes
- Medical prescriptions
- Independent clinical assessments

Crucial Distinction:
- Patient Input framing: "You reported [symptom]..."
- Diagnosis prohibition framing: Never say "You have [disease]..."
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel


class CapabilitySafetyStatus(str, Enum):
    ALLOWED = "ALLOWED"
    PROHIBITED_CLINICAL = "PROHIBITED_CLINICAL"
    REQUIRES_ESCALATION = "REQUIRES_ESCALATION"


class NonAutonomousClinicalViolation(str, Enum):
    DIAGNOSIS = "DIAGNOSIS"
    TREATMENT_DECISION = "TREATMENT_DECISION"
    MEDICATION_CHANGE = "MEDICATION_CHANGE"
    MEDICAL_PRESCRIPTION = "MEDICAL_PRESCRIPTION"
    INDEPENDENT_CLINICAL_ASSESSMENT = "INDEPENDENT_CLINICAL_ASSESSMENT"


class AISafetyEngine:
    """
    Evaluates requests and responses against Section 18 AI Safety Principles.
    """

    ALLOWED_CAPABILITIES = [
        "appointment_discovery",
        "scheduling",
        "rescheduling",
        "cancellation",
        "administrative_faqs",
        "approved_pre_visit_questions",
        "recording_patient_responses",
        "workflow_initiation",
        "notifications",
        "ehr_appointment_operations",
        "external_system_synchronization",
        "escalation"
    ]

    PROHIBITED_CLINICAL_CAPABILITIES = [
        "diagnosis",
        "treatment_decisions",
        "medication_changes",
        "medical_prescriptions",
        "independent_clinical_assessments"
    ]

    CLINICAL_PATTERNS = [
        (r"\b(diagnose\s+me|what\s+(is\s+my\s+diagnosis|disease\s+do\s+i\s+have))\b", NonAutonomousClinicalViolation.DIAGNOSIS),
        (r"\b(prescribe|give\s+me\s+a\s+prescription|need\s+antibiotics|write\s+prescription)\b", NonAutonomousClinicalViolation.MEDICAL_PRESCRIPTION),
        (r"\b(change\s+(my\s+)?dose|increase\s+(my\s+)?dosage|decrease\s+(my\s+)?dosage|stop\s+taking\s+(my\s+medication|pills)|dosage\s+of)\b", NonAutonomousClinicalViolation.MEDICATION_CHANGE),
        (r"\b(how\s+should\s+i\s+treat|treatment\s+decision|what\s+treatment\s+should\s+i\s+take)\b", NonAutonomousClinicalViolation.TREATMENT_DECISION),
        (r"\b(clinical\s+assessment|evaluate\s+my\s+medical\s+condition\s+independently)\b", NonAutonomousClinicalViolation.INDEPENDENT_CLINICAL_ASSESSMENT)
    ]

    @classmethod
    def evaluate_capability(cls, capability_name: str) -> Dict[str, Any]:
        """
        Validates if a requested capability is allowed as an administrative assistant
        or blocked under non-autonomous clinician rules.
        """
        norm_cap = capability_name.lower().replace(" ", "_").replace("-", "_")

        if norm_cap in cls.ALLOWED_CAPABILITIES:
            return {
                "capability": capability_name,
                "status": CapabilitySafetyStatus.ALLOWED.value,
                "is_allowed": True,
                "reason": "Administrative and operational capability allowed under Section 18 safety principles."
            }

        for prohibited in cls.PROHIBITED_CLINICAL_CAPABILITIES:
            if prohibited in norm_cap:
                return {
                    "capability": capability_name,
                    "status": CapabilitySafetyStatus.PROHIBITED_CLINICAL.value,
                    "is_allowed": False,
                    "violation_type": prohibited.upper(),
                    "reason": (
                        f"The AI is an administrative healthcare assistant, not a clinician. "
                        f"'{capability_name}' requires licensed clinical autonomy and is strictly prohibited."
                    )
                }

        return {
            "capability": capability_name,
            "status": CapabilitySafetyStatus.REQUIRES_ESCALATION.value,
            "is_allowed": False,
            "reason": f"Unrecognized or unsupported capability '{capability_name}' requires human staff escalation."
        }

    @classmethod
    def inspect_patient_query(cls, query_text: str) -> Dict[str, Any]:
        """
        Detects if patient is asking for diagnosis, treatment decisions, prescriptions, or medication changes.
        """
        lowered = query_text.lower()
        for pattern, violation in cls.CLINICAL_PATTERNS:
            if re.search(pattern, lowered):
                return {
                    "is_safe": False,
                    "violation": violation.value,
                    "recommended_escalation": "HUMAN_CLINICIAN_OR_SPECIALIST_SCHEDULING",
                    "safe_response": (
                        "I am an AI administrative assistant, not a doctor. I cannot provide a medical diagnosis, "
                        "prescribe medications, or alter treatment plans. Would you like me to book a consultation "
                        "with one of our physicians who can clinically evaluate your condition?"
                    )
                }

        return {
            "is_safe": True,
            "violation": None,
            "data_category": "PATIENT_REPORTED_INFORMATION",
            "message": "Query belongs to administrative or appointment scheduling domain."
        }

    @classmethod
    def enforce_patient_reported_framing(cls, text: str) -> Dict[str, Any]:
        """
        Strict Section 18 Rule:
        The AI should clearly distinguish:
        'You reported...' from 'You have...'
        The former represents patient input. The latter could incorrectly imply diagnosis.
        """
        # Search for prohibited diagnostic phrasing: "You have <condition/disease>"
        diagnostic_pattern = r"\b(you\s+have\s+(a\s+|an\s+)?(asthma|diabetes|infection|flu|covid|cancer|hypertension|migraine|fracture|pneumonia|[a-z]+\s+disease|[a-z]+\s+syndrome))\b"
        match = re.search(diagnostic_pattern, text, re.IGNORECASE)

        if match:
            prohibited_phrase = match.group(0)
            # Reframe to compliant "You reported..."
            reframed_phrase = re.sub(r"\byou\s+have\b", "you reported", prohibited_phrase, flags=re.IGNORECASE)
            reframed_text = text.replace(prohibited_phrase, reframed_phrase)
            return {
                "is_compliant": False,
                "diagnostic_implication_detected": True,
                "prohibited_phrase": prohibited_phrase,
                "reframed_text": reframed_text,
                "rule": "The AI must frame symptoms as 'You reported...' rather than diagnosing with 'You have...'"
            }

        return {
            "is_compliant": True,
            "diagnostic_implication_detected": False,
            "reframed_text": text,
            "rule": "Framing correctly respects patient-reported attribution."
        }


ai_safety_engine = AISafetyEngine()
