"""
Non-Clinical Safety Guardrails for Patient Intake Voice Agent.

Strict boundaries enforced:
1. Cannot diagnose diseases.
2. Cannot prescribe or alter medications.
3. Cannot make independent clinical assessments.
4. Categorizes all incoming patient inputs as "Patient-Reported Information".
"""

from typing import Tuple, Dict, Any


CLINICAL_DIAGNOSIS_KEYWORDS = [
    "diagnose me", "what disease do i have", "do i have cancer",
    "is this tumor", "prescribe", "give me prescription", "what medication should i take",
    "change my dose", "increase my dosage", "stop taking my medication"
]


class NonClinicalGuardrail:
    """
    Intercepts patient utterances to ensure the agent operates strictly as an intake/scheduling interface.
    """

    @staticmethod
    def inspect_utterance(utterance: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Inspects utterance for clinical boundary violations.
        Returns:
            (is_safe: bool, sanitized_or_response: str, metadata: dict)
        """
        lowered = utterance.lower()

        # Check for forbidden clinical triggers
        for kw in CLINICAL_DIAGNOSIS_KEYWORDS:
            if kw in lowered:
                return (
                    False,
                    "I am an AI administrative assistant for hospital scheduling and pre-visit intake. "
                    "I cannot provide medical diagnoses, prescribe medications, or offer clinical advice. "
                    "Would you like me to schedule an appointment with a specialist who can evaluate your symptoms?",
                    {"flagged_keyword": kw, "type": "CLINICAL_BOUNDARY_VIOLATION"}
                )

        return (
            True,
            utterance,
            {
                "data_category": "PATIENT_REPORTED_INFORMATION",
                "is_clinician_approved": False,
                "is_diagnostic": False
            }
        )
