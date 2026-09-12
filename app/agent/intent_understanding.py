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
    # Orthopedics & Musculoskeletal
    "orthopedic": "Orthopedics",
    "orthopedist": "Orthopedics",
    "ortho": "Orthopedics",
    "shoulder pain": "Orthopedics",
    "back pain": "Orthopedics",
    "knee pain": "Orthopedics",
    "joint pain": "Orthopedics",
    "joint stiffness": "Orthopedics",
    "leg pain": "Orthopedics",
    "arm pain": "Orthopedics",
    "foot pain": "Orthopedics",
    "hand pain": "Orthopedics",
    "neck pain": "Orthopedics",
    "hip pain": "Orthopedics",
    "bone pain": "Orthopedics",
    "ankle pain": "Orthopedics",
    "wrist pain": "Orthopedics",
    "fracture": "Orthopedics",
    "sprain": "Orthopedics",
    "arthritis": "Orthopedics",
    "spine": "Orthopedics",
    "knee": "Orthopedics",
    "shoulder": "Orthopedics",
    "bone": "Orthopedics",
    "joint": "Orthopedics",

    # Cardiology & Cardiovascular
    "cardiologist": "Cardiology",
    "cardiology": "Cardiology",
    "cardio": "Cardiology",
    "cardiac": "Cardiology",
    "chest pain": "Cardiology",
    "chest tightness": "Cardiology",
    "chest pressure": "Cardiology",
    "palpitations": "Cardiology",
    "shortness of breath": "Cardiology",
    "breathless": "Cardiology",
    "heart": "Cardiology",
    "heart problem": "Cardiology",
    "blood pressure": "Cardiology",
    "hypertension": "Cardiology",
    "cholesterol": "Cardiology",

    # Dermatology & Skin
    "dermatologist": "Dermatology",
    "dermatology": "Dermatology",
    "derma": "Dermatology",
    "skin rash": "Dermatology",
    "rash": "Dermatology",
    "eczema": "Dermatology",
    "hives": "Dermatology",
    "acne": "Dermatology",
    "itchy": "Dermatology",
    "itching": "Dermatology",
    "skin": "Dermatology",
    "skin problem": "Dermatology",
    "allergy": "Dermatology",
    "allergies": "Dermatology",
    "mole": "Dermatology",
    "lesion": "Dermatology",
    "psoriasis": "Dermatology",

    # Neurology
    "neurologist": "Neurology",
    "neurology": "Neurology",
    "neuro": "Neurology",
    "headache": "Neurology",
    "migraine": "Neurology",
    "head pain": "Neurology",
    "head hurts": "Neurology",
    "dizziness": "Neurology",
    "dizzy": "Neurology",
    "vertigo": "Neurology",
    "numbness": "Neurology",
    "tingling": "Neurology",

    # Gastroenterology & Digestive
    "gastroenterologist": "Gastroenterology",
    "gastroenterology": "Gastroenterology",
    "gastro": "Gastroenterology",
    "stomach pain": "Gastroenterology",
    "stomach ache": "Gastroenterology",
    "stomach": "Gastroenterology",
    "belly pain": "Gastroenterology",
    "abdominal pain": "Gastroenterology",
    "acid reflux": "Gastroenterology",
    "heartburn": "Gastroenterology",
    "nausea": "Gastroenterology",
    "vomiting": "Gastroenterology",
    "vomit": "Gastroenterology",
    "diarrhea": "Gastroenterology",
    "constipation": "Gastroenterology",
    "digestive": "Gastroenterology",

    # General Medicine / Internal Medicine
    "fever": "General Medicine",
    "cough": "General Medicine",
    "cold": "General Medicine",
    "flu": "General Medicine",
    "infection": "General Medicine",
    "sick": "General Medicine",
    "unwell": "General Medicine",
    "not feeling well": "General Medicine",
    "body ache": "General Medicine",
    "chills": "General Medicine",
    "high temperature": "General Medicine",
    "fatigue": "General Medicine",
    "internal medicine": "General Medicine",
    "general physician": "General Medicine",

    # Ophthalmology & Eye Care
    "ophthalmologist": "Ophthalmology",
    "ophthalmology": "Ophthalmology",
    "blurred vision": "Ophthalmology",
    "eye redness": "Ophthalmology",
    "eye pain": "Ophthalmology",
    "eye problem": "Ophthalmology",
    "vision": "Ophthalmology",

    # ENT (Ear, Nose, Throat)
    "ear ache": "ENT",
    "ear pain": "ENT",
    "sore throat": "ENT",
    "throat infection": "ENT",
    "throat": "ENT",
    "sinus": "ENT",
    "runny nose": "ENT",
    "ent": "ENT",

    # Dentistry
    "toothache": "Dentistry",
    "tooth pain": "Dentistry",
    "dentist": "Dentistry",
    "dentistry": "Dentistry",
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
        lowered = utterance.lower().strip()

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

        # General health / illness / problem expressions
        general_health_words = [
            "problem", "issue", "trouble", "pain", "hurt", "hurting", "ache", "sick", "unwell",
            "ill", "condition", "suffering", "discomfort", "symptom", "disease", "feeling bad",
            "not well", "not feeling good", "medical", "doctor"
        ]
        if any(w in lowered for w in general_health_words):
            return SymptomInferenceResult(
                has_symptom=True,
                symptom_detected="general medical concern",
                inferred_specialty="General Medicine",
                requires_clarification=False,
                cautious_response="I understand you are experiencing health symptoms. I can assist you with scheduling a consultation with our General Medicine and Internal Care team.",
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
