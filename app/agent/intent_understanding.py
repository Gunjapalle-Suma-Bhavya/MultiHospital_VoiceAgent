"""
Patient Intent & Requirement Understanding Engine (Section 5.12).

Maps patient-reported symptoms to relevant medical specialties while maintaining strict non-clinical boundaries:
- "shoulder pain", "back pain", "knee stiffness" -> Orthopedics
- "skin rash", "eczema", "hives" -> Dermatology
- "chest tightness", "palpitations" -> Cardiology (with emergency check)
- "persistent headache", "dizziness" -> Neurology
- "blurred vision", "eye irritation" -> Ophthalmology
- "stomach ache", "acid reflux" -> Gastroenterology

RULE: Strictly distinguishes Patient-Reported Symptom from Medical Diagnosis. Uses cautious scheduling language.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel


SYMPTOM_TO_SPECIALTY_MAP = {
    "dermatologist": "Dermatology",
    "dermatology": "Dermatology",
    "orthopedic": "Orthopedics",
    "orthopedist": "Orthopedics",
    "cardiologist": "Cardiology",
    "neurologist": "Neurology",
    "ophthalmologist": "Ophthalmology",
    "gastroenterologist": "Gastroenterology",
    "shoulder pain": "Orthopedics",
    "back pain": "Orthopedics",
    "knee pain": "Orthopedics",
    "joint stiffness": "Orthopedics",
    "fracture": "Orthopedics",
    "skin rash": "Dermatology",
    "rash": "Dermatology",
    "eczema": "Dermatology",
    "hives": "Dermatology",
    "acne": "Dermatology",
    "itchy": "Dermatology",
    "itching": "Dermatology",
    "chest pain": "Cardiology",
    "palpitations": "Cardiology",
    "shortness of breath": "Cardiology",
    "headache": "Neurology",
    "migraine": "Neurology",
    "dizziness": "Neurology",
    "numbness": "Neurology",
    "blurred vision": "Ophthalmology",
    "eye redness": "Ophthalmology",
    "stomach pain": "Gastroenterology",
    "acid reflux": "Gastroenterology",
    "nausea": "Gastroenterology",
    "toothache": "Dentistry",
    "ear ache": "ENT",
    "sore throat": "ENT"
}



class SymptomInferenceResult(BaseModel):
    has_symptom: bool
    symptom_detected: Optional[str] = None
    inferred_specialty: Optional[str] = None
    requires_clarification: bool = False
    cautious_response: str
    is_patient_reported_only: bool = True
    is_diagnostic: bool = False


class SymptomIntentResolver:
    """
    Engine inferring specialty requirements from informal patient descriptions.
    """

    @staticmethod
    def infer_specialty_from_utterance(utterance: str) -> SymptomInferenceResult:
        lowered = utterance.lower()

        # Emergency trigger check
        if "severe chest pain" in lowered or "crushing chest" in lowered or "cannot breathe" in lowered:
            return SymptomInferenceResult(
                has_symptom=True,
                symptom_detected="severe chest pain",
                inferred_specialty="Emergency Medicine",
                requires_clarification=False,
                cautious_response="EMERGENCY WARNING: Your reported symptoms require urgent medical evaluation. Please call emergency services (911) or visit the nearest emergency room immediately.",
                is_patient_reported_only=True,
                is_diagnostic=False
            )

        matched_symptom = None
        matched_specialty = None

        for symptom, specialty in SYMPTOM_TO_SPECIALTY_MAP.items():
            if symptom in lowered:
                matched_symptom = symptom
                matched_specialty = specialty
                break

        if matched_symptom and matched_specialty:
            cautious_text = (
                f"Based on your reported symptom of {matched_symptom}, I can assist with booking a consultation "
                f"with an {matched_specialty} specialist. Please note that this recommendation is for appointment "
                f"scheduling purposes only and does not constitute a medical diagnosis."
            )
            return SymptomInferenceResult(
                has_symptom=True,
                symptom_detected=matched_symptom,
                inferred_specialty=matched_specialty,
                requires_clarification=False,
                cautious_response=cautious_text,
                is_patient_reported_only=True,
                is_diagnostic=False
            )

        # Ambiguous / General utterance requiring clarification
        return SymptomInferenceResult(
            has_symptom=False,
            requires_clarification=True,
            cautious_response="Could you please provide a few more details about your symptoms or specify which medical department or specialist you would like to see?",
            is_patient_reported_only=True,
            is_diagnostic=False
        )
