"""
MongoDB Atlas Cloud Document Store Integration.
Provides JSON document persistence for Patients, Doctors, Appointments,
Questionnaires, Audit Trails, and Hospital Organizations.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import pymongo
from pymongo import MongoClient

def get_effective_mongo_uri() -> str:
    uri = os.getenv("MONGODB_URI", "").strip()
    return uri if uri else "mongodb://localhost:27017"

MONGODB_URI = get_effective_mongo_uri()
DB_NAME = os.getenv("MONGODB_DB_NAME", "nexushealth_hospital_db")

from concurrent.futures import ThreadPoolExecutor
import time

_mongo_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mongo_sync")
_mongo_client: Optional[MongoClient] = None
_last_connection_failure: float = 0.0
_FAILURE_COOLDOWN_SECONDS: float = 10.0

def get_mongodb_client() -> Optional[MongoClient]:
    global _mongo_client, _last_connection_failure
    uri = get_effective_mongo_uri()
    if _mongo_client is not None:
        return _mongo_client
    if time.time() - _last_connection_failure < _FAILURE_COOLDOWN_SECONDS:
        return None
    try:
        _mongo_client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        # verify ping
        _mongo_client.admin.command('ping')
        return _mongo_client
    except Exception as e:
        _last_connection_failure = time.time()
        _mongo_client = None
        print(f"[MongoDB Warning] Connection error: {e}")
        return None

def get_mongo_db():
    client = get_mongodb_client()
    if client is not None:
        db_name = os.getenv("MONGODB_DB_NAME", "nexushealth_hospital_db").strip() or "nexushealth_hospital_db"
        return client[db_name]
    return None

# Collections accessors
def get_collection(name: str):
    db = get_mongo_db()
    if db is not None:
        return db[name]
    return None

def seed_mongodb_data() -> Dict[str, Any]:
    """
    Seeds comprehensive, realistic clinical data into MongoDB Atlas:
    - Hospitals (City Memorial Hospital, St. Jude Medical, Architecture General)
    - Doctors (Dr. Sharma, Dr. Rao, Dr. Emily Watson, Dr. Lisa Chen)
    - Patients (Marcus Aurelius, Elena Rostova, Sarah Connor)
    - Questionnaires (Orthopedic, Cardiology, General)
    - Real Appointments with 5-Point Verification
    """
    db = get_mongo_db()
    if db is None:
        return {"status": "error", "message": "MongoDB not connected"}

    # 1. Hospitals Collection
    col_hospitals = db["hospitals"]
    hospitals_data = [
        {
            "hospital_id": "HOSP-CITY-01",
            "name": "City Memorial Hospital",
            "code": "CITYHOSP",
            "status": "APPROVED",
            "address": "1000 Healthcare Way, Suite 400, Metro City",
            "phone": "+1-800-CITY-HOSP",
            "departments": ["Orthopedic Surgery", "Cardiology", "Emergency Medicine", "Pediatrics", "Diagnostic Imaging"],
            "specialties": ["Orthopedic Surgery", "Cardiology", "Dermatology", "Neurology", "Pediatrics"],
            "operating_hours": "Mon-Fri: 08:00 AM - 06:00 PM, Sat: 09:00 AM - 01:00 PM",
            "ehr_adapter": "EPIC_MYCHART",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "hospital_id": "HOSP-CARE-02",
            "name": "St. Jude Care Pavilion",
            "code": "STJUDE",
            "status": "APPROVED",
            "address": "250 Wellness Blvd, Pavilion West",
            "phone": "+1-888-ST-JUDE",
            "departments": ["Cardiovascular Medicine", "Thoracic Surgery", "General Practice"],
            "specialties": ["Cardiology", "Internal Medicine", "Oncology"],
            "operating_hours": "Mon-Fri: 09:00 AM - 05:00 PM",
            "ehr_adapter": "FHIR_R4",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    for h in hospitals_data:
        col_hospitals.update_one({"hospital_id": h["hospital_id"]}, {"$set": h}, upsert=True)

    # 2. Doctors Collection
    col_doctors = db["doctors"]
    doctors_data = [
        {
            "doctor_id": "DOC-SHARMA-01",
            "hospital_id": "HOSP-CITY-01",
            "hospital_name": "City Memorial Hospital",
            "name": "Dr. Sharma",
            "specialty": "Orthopedic Surgery",
            "department": "Orthopedic Surgery",
            "qualifications": "MD, FACS, Board Certified Orthopedic Surgeon",
            "experience_years": 15,
            "languages": ["English", "Hindi"],
            "consultation_type": "IN_PERSON",
            "default_appointment_duration": 30,
            "status": "ACTIVE",
            "rating": 4.9,
            "bio": "Specializes in joint preservation, arthroscopy, and sports trauma rehabilitation.",
            "working_hours": "09:00 AM - 05:00 PM",
            "available_slots": [
                "09:00 AM", "09:30 AM", "10:30 AM", "11:00 AM", 
                "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM"
            ],
            "npi": "198234812",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "doctor_id": "DOC-RAO-02",
            "hospital_id": "HOSP-CITY-01",
            "hospital_name": "City Memorial Hospital",
            "name": "Dr. Rao",
            "specialty": "Cardiology",
            "department": "Cardiology",
            "qualifications": "MD, FACC, Board Certified Cardiologist",
            "experience_years": 12,
            "languages": ["English", "Telugu", "Spanish"],
            "consultation_type": "HYBRID",
            "default_appointment_duration": 30,
            "status": "ACTIVE",
            "rating": 4.8,
            "bio": "Specializing in preventive cardiology, coronary interventions, and arrhythmia management.",
            "working_hours": "09:00 AM - 05:00 PM",
            "available_slots": [
                "10:00 AM", "11:00 AM", "02:00 PM", "04:00 PM", "04:30 PM"
            ],
            "npi": "174829103",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "doctor_id": "DOC-CHEN-03",
            "hospital_id": "HOSP-CITY-01",
            "hospital_name": "City Memorial Hospital",
            "name": "Dr. Lisa Chen",
            "specialty": "Dermatology",
            "department": "Dermatology",
            "qualifications": "MD, FAAD, Dermatology Fellow",
            "experience_years": 9,
            "languages": ["English", "Mandarin"],
            "consultation_type": "VIDEO",
            "default_appointment_duration": 20,
            "status": "ACTIVE",
            "rating": 4.95,
            "bio": "Expert in inflammatory skin pathologies, clinical dermoscopy, and tele-dermatology.",
            "working_hours": "08:30 AM - 04:30 PM",
            "available_slots": ["09:00 AM", "10:00 AM", "01:00 PM", "02:00 PM"],
            "npi": "189204910",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "doctor_id": "DOC-WATSON-04",
            "hospital_id": "HOSP-CARE-02",
            "hospital_name": "St. Jude Care Pavilion",
            "name": "Dr. Emily Watson",
            "specialty": "Neurology",
            "department": "Neurosciences",
            "qualifications": "MD, PhD, Clinical Neurophysiology",
            "experience_years": 14,
            "languages": ["English"],
            "consultation_type": "IN_PERSON",
            "default_appointment_duration": 45,
            "status": "ACTIVE",
            "rating": 4.9,
            "bio": "Comprehensive neurological evaluations, migraine clinics, and neuromuscular disorders.",
            "working_hours": "09:00 AM - 05:00 PM",
            "available_slots": ["10:30 AM", "11:30 AM", "02:30 PM", "03:30 PM"],
            "npi": "149204859",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    for d in doctors_data:
        col_doctors.update_one({"doctor_id": d["doctor_id"]}, {"$set": d}, upsert=True)

    # 3. Patients Collection
    col_patients = db["patients"]
    patients_data = [
        {
            "patient_id": "PAT-MARCUS-01",
            "phone_number": "+1-555-SHOULDER",
            "full_name": "Marcus Aurelius",
            "email": "marcus.aurelius@healthcare.net",
            "date_of_birth": "1984-04-26",
            "preferred_language": "English",
            "communication_preference": "VOICE_AND_SMS",
            "insurance": {
                "carrier": "Blue Cross Blue Shield (PPO)",
                "policy_number": "BCBS-994218-A",
                "copay": "$25.00",
                "is_verified": True
            },
            "allergies": ["Penicillin (Severe Rash)"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "patient_id": "PAT-ELENA-02",
            "phone_number": "+1-555-KNEE-99",
            "full_name": "Elena Rostova",
            "email": "elena.rostova@healthcare.net",
            "date_of_birth": "1991-08-14",
            "preferred_language": "English",
            "communication_preference": "SMS",
            "insurance": {
                "carrier": "Aetna Choice POS II",
                "policy_number": "AET-338291",
                "copay": "$20.00",
                "is_verified": True
            },
            "allergies": ["Sulfa Drugs"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    for p in patients_data:
        col_patients.update_one({"phone_number": p["phone_number"]}, {"$set": p}, upsert=True)

    # 4. Questionnaires Collection
    col_questionnaires = db["questionnaires"]
    questionnaires_data = [
        {
            "questionnaire_id": "Q-ORTHO-01",
            "title": "Orthopedic Surgery Pre-Consultation Survey",
            "specialty": "Orthopedic Surgery",
            "version": "v2.1",
            "status": "ACTIVE",
            "questions": [
                {"question_id": "Q-1", "question_text": "How long have you had this joint or musculoskeletal pain?", "response_type": "SHORT_TEXT", "is_required": True},
                {"question_id": "Q-2", "question_text": "Rate your current pain severity from 1 (Mild) to 10 (Debilitating):", "response_type": "SHORT_TEXT", "is_required": True},
                {"question_id": "Q-3", "question_text": "Have you had prior orthopedic surgery or joint injections?", "response_type": "YES_NO", "is_required": True},
                {"question_id": "Q-4", "question_text": "Are you currently taking any prescription pain or blood-thinning medications?", "response_type": "YES_NO", "is_required": True}
            ],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "questionnaire_id": "Q-CARDIO-02",
            "title": "Cardiology Consultation & Vitals Questionnaire",
            "specialty": "Cardiology",
            "version": "v1.4",
            "status": "ACTIVE",
            "questions": [
                {"question_id": "QC-1", "question_text": "Do you experience heart palpitations, dizziness, or lightheadedness?", "response_type": "YES_NO", "is_required": True},
                {"question_id": "QC-2", "question_text": "Do you have a personal or family history of high blood pressure or heart disease?", "response_type": "YES_NO", "is_required": True},
                {"question_id": "QC-3", "question_text": "Please list your current daily blood pressure or cardiovascular medications:", "response_type": "SHORT_TEXT", "is_required": True}
            ],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    for q in questionnaires_data:
        col_questionnaires.update_one({"questionnaire_id": q["questionnaire_id"]}, {"$set": q}, upsert=True)

    # 5. Real Appointments Collection
    col_appointments = db["appointments"]
    appts_data = [
        {
            "appointment_id": "APT-1024",
            "patient_name": "Marcus Aurelius",
            "patient_phone": "+1-555-SHOULDER",
            "doctor_id": "DOC-SHARMA-01",
            "doctor_name": "Dr. Sharma",
            "specialty": "Orthopedic Surgery",
            "hospital_id": "HOSP-CITY-01",
            "hospital_name": "City Memorial Hospital",
            "scheduled_time": "Today, 10:00 AM",
            "slot_time": "10:00 AM",
            "status": "CONFIRMED",
            "is_ehr_verified": True,
            "external_ehr_id": "EHR-EPIC-88421",
            "intake_status": "COMPLETED",
            "chief_complaint": "Acute right anterior shoulder pain lasting ~7 days",
            "vitals": {"bp": "120/80", "hr": 74, "spo2": 98, "temp": 98.6},
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "appointment_id": "APT-1025",
            "patient_name": "Elena Rostova",
            "patient_phone": "+1-555-KNEE-99",
            "doctor_id": "DOC-SHARMA-01",
            "doctor_name": "Dr. Sharma",
            "specialty": "Orthopedic Surgery",
            "hospital_id": "HOSP-CITY-01",
            "hospital_name": "City Memorial Hospital",
            "scheduled_time": "Today, 11:30 AM",
            "slot_time": "11:30 AM",
            "status": "CONFIRMED",
            "is_ehr_verified": True,
            "external_ehr_id": "EHR-EPIC-88422",
            "intake_status": "PENDING",
            "chief_complaint": "Right knee post-op swelling following lateral meniscus repair",
            "vitals": {"bp": "118/76", "hr": 70, "spo2": 99, "temp": 98.4},
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    for a in appts_data:
        col_appointments.update_one({"appointment_id": a["appointment_id"]}, {"$set": a}, upsert=True)

    # 6. Conversations Collection
    col_conversations = db["conversations"]
    conversations_data = [
        {
            "session_id": "SES-MARCUS-001",
            "patient_phone": "+1-555-SHOULDER",
            "patient_name": "Marcus Aurelius",
            "user_utterance": "I've had severe anterior right shoulder pain for 7 days after playing tennis.",
            "agent_response": "I can help with that. Based on your acute shoulder pain symptoms, I recommend an evaluation with our Orthopedic Surgery specialist, Dr. Sharma at City Memorial Hospital. We have consultation slots available tomorrow morning at 10:00 AM. Would you like to reserve this slot?",
            "language": "en",
            "intent": "BOOK_APPOINTMENT",
            "extracted_symptoms": ["anterior right shoulder pain", "acute", "duration 7 days"],
            "doctor_id": "DOC-SHARMA-01",
            "hospital_id": "HOSP-CITY-01",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "session_id": "SES-MARCUS-001",
            "patient_phone": "+1-555-SHOULDER",
            "patient_name": "Marcus Aurelius",
            "user_utterance": "Yes, please confirm the 10:00 AM consultation with Dr. Sharma.",
            "agent_response": "Excellent. Your appointment with Dr. Sharma at City Memorial Hospital is confirmed for tomorrow at 10:00 AM. Your verification code is APT-1024. A confirmation SMS with directions has been sent to your phone.",
            "language": "en",
            "intent": "CONFIRM_SLOT",
            "appointment_id": "APT-1024",
            "verification_code": "APT-1024",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    ]
    for c in conversations_data:
        col_conversations.insert_one(c)

    # 7. Patient History Collection
    col_patient_history = db["patient_history"]
    history_data = [
        {
            "phone_number": "+1-555-SHOULDER",
            "patient_name": "Marcus Aurelius",
            "date_of_birth": "1984-04-26",
            "medical_history": [
                "Mild asthma (controlled with Albuterol PRN)",
                "Previous right rotator cuff strain (resolved in 2023)"
            ],
            "allergies": ["Penicillin (Severe Rash)"],
            "recent_conversations": [
                {
                    "session_id": "SES-MARCUS-001",
                    "user_utterance": "I've had severe anterior right shoulder pain for 7 days after playing tennis.",
                    "agent_response": "Recommended Orthopedic consultation with Dr. Sharma.",
                    "language": "en",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            ],
            "appointments": [
                {
                    "appointment_id": "APT-1024",
                    "doctor_name": "Dr. Sharma",
                    "specialty": "Orthopedic Surgery",
                    "hospital_name": "City Memorial Hospital",
                    "scheduled_time": "Today, 10:00 AM",
                    "status": "CONFIRMED"
                }
            ],
            "questionnaire_records": [
                {
                    "questionnaire_id": "Q-ORTHO-01",
                    "specialty": "Orthopedic Surgery",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "answers": {
                        "pain_duration": "7 days",
                        "pain_severity": "7/10",
                        "prior_injections": "None",
                        "taking_medications": "Ibuprofen 400mg"
                    }
                }
            ],
            "last_interaction": datetime.now(timezone.utc).isoformat()
        },
        {
            "phone_number": "+1-555-KNEE-99",
            "patient_name": "Elena Rostova",
            "date_of_birth": "1991-08-14",
            "medical_history": [
                "Right knee arthroscopy & lateral meniscus repair (completed 4 weeks ago)"
            ],
            "allergies": ["Sulfa Drugs"],
            "appointments": [
                {
                    "appointment_id": "APT-1025",
                    "doctor_name": "Dr. Sharma",
                    "specialty": "Orthopedic Surgery",
                    "hospital_name": "City Memorial Hospital",
                    "scheduled_time": "Today, 11:30 AM",
                    "status": "CONFIRMED"
                }
            ],
            "last_interaction": datetime.now(timezone.utc).isoformat()
        }
    ]
    for h in history_data:
        col_patient_history.update_one({"phone_number": h["phone_number"]}, {"$set": h}, upsert=True)

    # 8. Patient Preferences Collection
    col_patient_preferences = db["patient_preferences"]
    preferences_data = [
        {
            "phone_number": "+1-555-SHOULDER",
            "patient_id": "PAT-MARCUS-01",
            "full_name": "Marcus Aurelius",
            "preferred_language": "English",
            "preferred_hospital_id": "HOSP-CITY-01",
            "preferred_hospital_name": "City Memorial Hospital",
            "preferred_doctor_id": "DOC-SHARMA-01",
            "preferred_doctor_name": "Dr. Sharma",
            "preferred_time_window": "MORNING",
            "communication_preference": "VOICE_AND_SMS",
            "notification_channels": {
                "sms": True,
                "email": True,
                "whatsapp": True,
                "voice_call": False
            },
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "phone_number": "+1-555-KNEE-99",
            "patient_id": "PAT-ELENA-02",
            "full_name": "Elena Rostova",
            "preferred_language": "English",
            "preferred_hospital_id": "HOSP-CITY-01",
            "preferred_hospital_name": "City Memorial Hospital",
            "preferred_doctor_id": "DOC-SHARMA-01",
            "preferred_doctor_name": "Dr. Sharma",
            "preferred_time_window": "AFTERNOON",
            "communication_preference": "SMS",
            "notification_channels": {
                "sms": True,
                "email": True,
                "whatsapp": False,
                "voice_call": False
            },
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    for pr in preferences_data:
        col_patient_preferences.update_one({"phone_number": pr["phone_number"]}, {"$set": pr}, upsert=True)

    # 9. Hospital History Collection
    col_hospital_history = db["hospital_history"]
    hospital_history_data = [
        {
            "hospital_id": "HOSP-CITY-01",
            "name": "City Memorial Hospital",
            "code": "CITYHOSP",
            "onboarding_status": "APPROVED",
            "established_year": 1985,
            "accreditation": "Joint Commission Accredited Healthcare Institution",
            "total_licensed_beds": 450,
            "trauma_center_level": "Level I Trauma Center",
            "departments": [
                "Orthopedic Surgery & Sports Medicine",
                "Cardiology & Interventional Catheterization",
                "Emergency Medicine (24/7)",
                "Diagnostic Imaging & MRI Center",
                "Dermatology & Laser Surgery"
            ],
            "visiting_hours": "08:00 AM - 08:00 PM Daily (ICU: 10:00 AM - 12:00 PM)",
            "parking_guide": "Garage A adjacent to main clinical pavilion; complimentary 30-min patient dropoff.",
            "policies": "Masking required in oncology units; cancellation permitted up to 24h before visit without fee.",
            "active_doctors_count": 3,
            "total_appointments_booked": 1420,
            "total_voice_inquiries": 3840,
            "ehr_system": "Epic MyChart (SMART-on-FHIR R4)",
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "hospital_id": "HOSP-CARE-02",
            "name": "St. Jude Care Pavilion",
            "code": "STJUDE",
            "onboarding_status": "APPROVED",
            "established_year": 1998,
            "accreditation": "Statewide Healthcare Quality Gold Seal",
            "total_licensed_beds": 280,
            "trauma_center_level": "Level II Trauma Center",
            "departments": [
                "Cardiovascular Medicine",
                "Thoracic Surgery",
                "Neurology & Stroke Unit",
                "Family Medicine & Preventive Care"
            ],
            "visiting_hours": "09:00 AM - 07:00 PM Daily",
            "active_doctors_count": 2,
            "total_appointments_booked": 890,
            "total_voice_inquiries": 2150,
            "ehr_system": "HL7 FHIR R4 Connector",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    for hh in hospital_history_data:
        col_hospital_history.update_one({"hospital_id": hh["hospital_id"]}, {"$set": hh}, upsert=True)

    # 10. Clinical Encounters Collection
    col_encounters = db["clinical_encounters"]
    encounters_data = [
        {
            "encounter_id": "ENC-1024-SOAP",
            "appointment_id": "APT-1024",
            "patient_name": "Marcus Aurelius",
            "patient_phone": "+1-555-SHOULDER",
            "doctor_id": "DOC-SHARMA-01",
            "doctor_name": "Dr. Sharma",
            "specialty": "Orthopedic Surgery",
            "soap_notes": {
                "subjective": "Patient reports acute pain in right anterior shoulder after tennis overhead smash. No numbness.",
                "objective": "Positive Hawkins-Kennedy test. Moderate impingement tenderness. Active forward flexion limited to 130 deg.",
                "assessment": "Acute right subacromial bursitis and supraspinatus impingement syndrome.",
                "plan": "Short-course oral NSAID therapy, physical therapy referral for rotator cuff strengthening, follow-up in 3 weeks."
            },
            "prescriptions": [
                {"medication": "Meloxicam", "dosage": "15 mg", "frequency": "Once daily with food", "duration": "14 days"}
            ],
            "status": "COMPLETED",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    for enc in encounters_data:
        col_encounters.update_one({"encounter_id": enc["encounter_id"]}, {"$set": enc}, upsert=True)

    return {
        "status": "success",
        "database": DB_NAME,
        "counts": {
            "conversations": col_conversations.count_documents({}),
            "patient_history": col_patient_history.count_documents({}),
            "patient_preferences": col_patient_preferences.count_documents({}),
            "hospital_history": col_hospital_history.count_documents({}),
            "appointments": col_appointments.count_documents({}),
            "patients": col_patients.count_documents({}),
            "doctors": col_doctors.count_documents({}),
            "hospitals": col_hospitals.count_documents({}),
            "questionnaires": col_questionnaires.count_documents({}),
            "clinical_encounters": col_encounters.count_documents({})
        }
    }


def check_mongodb_connection() -> Dict[str, Any]:
    """Check connectivity to MongoDB Atlas cluster."""
    client = get_mongodb_client()
    if client is None:
        return {"connected": False, "database": DB_NAME, "error": "Connection could not be established"}
    try:
        client.admin.command('ping')
        return {"connected": True, "database": DB_NAME, "error": None}
    except Exception as e:
        return {"connected": False, "database": DB_NAME, "error": str(e)}


def get_mongodb_collections_stats() -> Dict[str, Any]:
    """Return document count per collection in MongoDB Atlas."""
    db = get_mongo_db()
    if db is None:
        return {"database": DB_NAME, "collections": {}}
    try:
        colls = [
            "conversations",
            "patient_history",
            "patient_preferences",
            "hospital_history",
            "appointments",
            "patients",
            "doctors",
            "hospitals",
            "questionnaires",
            "clinical_encounters",
            "events"
        ]
        # Dynamically include all collections found in the database
        try:
            existing = db.list_collection_names()
            for ex in existing:
                if ex not in colls and not ex.startswith("system."):
                    colls.append(ex)
        except Exception:
            pass

        stats = {}
        for c in colls:
            try:
                stats[c] = db[c].count_documents({})
            except Exception:
                stats[c] = 0
        return {"database": DB_NAME, "collections": stats}
    except Exception as e:
        return {"database": DB_NAME, "collections": {}, "error": str(e)}


def _exec_sync_event(event_data: Dict[str, Any]) -> None:
    try:
        db = get_mongo_db()
        if db is None:
            return

        # 1. Store event record
        db["events"].insert_one({
            "event_type": event_data.get("event_type"),
            "aggregate_id": event_data.get("aggregate_id"),
            "source": event_data.get("source"),
            "payload": event_data.get("payload", {}),
            "timestamp": event_data.get("timestamp") or datetime.now(timezone.utc).isoformat()
        })

        event_type = event_data.get("event_type")
        payload = event_data.get("payload", {})
        aggregate_id = event_data.get("aggregate_id")

        # 2. Domain Projection for Appointments
        if "APPOINTMENT" in str(event_type):
            db["appointments"].update_one(
                {"appointment_id": aggregate_id},
                {
                    "$set": {
                        "appointment_id": aggregate_id,
                        "status": payload.get("status", "CONFIRMED"),
                        "doctor_id": payload.get("doctor_id"),
                        "patient_name": payload.get("patient_name") or payload.get("patient_id"),
                        "slot_time": payload.get("slot_time"),
                        "hospital_id": payload.get("hospital_id", "HOSP-CITY-01"),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                },
                upsert=True
            )

        # 3. Domain Projection for Questionnaires / Intake
        if "INTAKE" in str(event_type) or "QUESTIONNAIRE" in str(event_type):
            db["questionnaires"].update_one(
                {"intake_id": aggregate_id},
                {
                    "$set": {
                        "intake_id": aggregate_id,
                        "responses": payload,
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }
                },
                upsert=True
            )
    except Exception as e:
        print(f"[MongoDB Sync Warning] Sync event failed gracefully: {e}")


def sync_event_to_mongodb(event_data: Dict[str, Any]) -> None:
    """
    Safely project published system events and domain updates into MongoDB Atlas.
    Guaranteed non-blocking and safe against network drops.
    """
    try:
        _mongo_pool.submit(_exec_sync_event, dict(event_data))
    except Exception:
        pass


def _exec_persist(collection_name: str, clean_doc: Dict[str, Any], key_field: Optional[str]) -> None:
    try:
        db = get_mongo_db()
        if db is None:
            return

        coll = db[collection_name]
        if key_field and key_field in clean_doc and clean_doc[key_field]:
            coll.update_one(
                {key_field: clean_doc[key_field]},
                {"$set": clean_doc},
                upsert=True
            )
        else:
            coll.insert_one(clean_doc)
    except Exception as e:
        print(f"[MongoDB Persist Warning] Failed to persist to {collection_name}: {e}")


def persist_to_mongodb(collection_name: str, doc_data: Dict[str, Any], key_field: Optional[str] = None) -> None:
    """
    Universally and safely persists any user-entered document directly to MongoDB Atlas.
    Supports upsert when key_field is provided, otherwise inserts.
    Guaranteed non-blocking, exception-safe, and fail-safe.
    """
    try:
        clean_doc = dict(doc_data)
        if "persisted_at" not in clean_doc:
            clean_doc["persisted_at"] = datetime.now(timezone.utc).isoformat()
        _mongo_pool.submit(_exec_persist, collection_name, clean_doc, key_field)
    except Exception:
        pass


def _exec_persist_conversation(
    session_id: str,
    patient_phone: str,
    user_utterance: str,
    agent_response: str,
    language: str,
    intent: Optional[str],
    hospital_id: Optional[str],
    doctor_id: Optional[str],
    metadata: Optional[Dict[str, Any]]
) -> None:
    try:
        db = get_mongo_db()
        if db is None:
            return

        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Store conversation record in `conversations`
        conv_doc = {
            "session_id": session_id or "default_session",
            "patient_phone": patient_phone,
            "user_utterance": user_utterance,
            "agent_response": agent_response,
            "language": language,
            "intent": intent,
            "hospital_id": hospital_id,
            "doctor_id": doctor_id,
            "metadata": metadata or {},
            "timestamp": now_iso
        }
        db["conversations"].insert_one(conv_doc)

        # 2. Update patient history (conversation trace and symptoms reported)
        patient_key = patient_phone or "ANONYMOUS"
        db["patient_history"].update_one(
            {"phone_number": patient_key},
            {
                "$setOnInsert": {
                    "phone_number": patient_key,
                    "created_at": now_iso
                },
                "$set": {
                    "last_interaction": now_iso,
                    "last_utterance": user_utterance,
                    "last_intent": intent
                },
                "$push": {
                    "recent_conversations": {
                        "$each": [{
                            "session_id": session_id,
                            "user_utterance": user_utterance,
                            "agent_response": agent_response,
                            "language": language,
                            "timestamp": now_iso
                        }],
                        "$slice": -50  # Keep last 50 turns
                    }
                }
            },
            upsert=True
        )

        # 3. Update patient preferences if language or doctor/hospital indicated
        pref_update: Dict[str, Any] = {
            "phone_number": patient_key,
            "preferred_language": language,
            "updated_at": now_iso
        }
        if hospital_id:
            pref_update["last_hospital_id"] = hospital_id
        if doctor_id:
            pref_update["last_doctor_id"] = doctor_id

        db["patient_preferences"].update_one(
            {"phone_number": patient_key},
            {"$set": pref_update},
            upsert=True
        )

        # 4. Update hospital history inquiry counter if hospital is known
        if hospital_id:
            db["hospital_history"].update_one(
                {"hospital_id": hospital_id},
                {
                    "$inc": {"total_voice_inquiries": 1},
                    "$set": {"last_voice_inquiry_at": now_iso}
                },
                upsert=True
            )
    except Exception as e:
        print(f"[MongoDB Conversation Warning] Failed to persist conversation: {e}")


def persist_conversation_turn(
    session_id: str,
    patient_phone: str,
    user_utterance: str,
    agent_response: str,
    language: str = "en",
    intent: Optional[str] = None,
    hospital_id: Optional[str] = None,
    doctor_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Non-blocking, thread-pooled conversation turn persistence to MongoDB."""
    try:
        _mongo_pool.submit(
            _exec_persist_conversation,
            session_id, patient_phone, user_utterance, agent_response,
            language, intent, hospital_id, doctor_id, metadata
        )
    except Exception:
        pass


def _exec_persist_patient_profile(patient_data: Dict[str, Any]) -> None:
    try:
        db = get_mongo_db()
        if db is None:
            return

        now_iso = datetime.now(timezone.utc).isoformat()
        phone = patient_data.get("phone_number")
        if not phone:
            return

        clean_data = dict(patient_data)
        clean_data["updated_at"] = now_iso

        # 1. Patients collection
        db["patients"].update_one({"phone_number": phone}, {"$set": clean_data}, upsert=True)

        # 2. Patient preferences collection
        pref_doc = {
            "phone_number": phone,
            "patient_id": clean_data.get("id") or clean_data.get("patient_id"),
            "full_name": clean_data.get("full_name") or clean_data.get("name"),
            "preferred_language": clean_data.get("preferred_language", "English"),
            "communication_preference": clean_data.get("communication_preference", "VOICE_AND_SMS"),
            "preferred_time_window": clean_data.get("preferred_time_window", "ANYTIME"),
            "updated_at": now_iso
        }
        db["patient_preferences"].update_one({"phone_number": phone}, {"$set": pref_doc}, upsert=True)

        # 3. Patient history collection
        history_init = {
            "phone_number": phone,
            "patient_id": clean_data.get("id") or clean_data.get("patient_id"),
            "full_name": clean_data.get("full_name") or clean_data.get("name"),
            "email": clean_data.get("email"),
            "date_of_birth": str(clean_data.get("date_of_birth")),
            "updated_at": now_iso
        }
        db["patient_history"].update_one(
            {"phone_number": phone},
            {"$set": history_init},
            upsert=True
        )
    except Exception as e:
        print(f"[MongoDB Patient Profile Warning] Failed to persist patient: {e}")


def persist_patient_profile(patient_data: Dict[str, Any]) -> None:
    """Non-blocking, thread-pooled patient profile & history persistence to MongoDB."""
    try:
        _mongo_pool.submit(_exec_persist_patient_profile, dict(patient_data))
    except Exception:
        pass


def _exec_persist_appointment(appointment_data: Dict[str, Any]) -> None:
    try:
        db = get_mongo_db()
        if db is None:
            return

        now_iso = datetime.now(timezone.utc).isoformat()
        appt_id = appointment_data.get("appointment_id") or appointment_data.get("id")
        if not appt_id:
            return

        clean_appt = dict(appointment_data)
        clean_appt["appointment_id"] = appt_id
        clean_appt["updated_at"] = now_iso

        # 1. Appointments collection
        db["appointments"].update_one({"appointment_id": appt_id}, {"$set": clean_appt}, upsert=True)

        # 2. Append to Patient History
        phone = clean_appt.get("patient_phone")
        if phone:
            db["patient_history"].update_one(
                {"phone_number": phone},
                {
                    "$set": {"last_appointment_id": appt_id, "last_appointment_at": now_iso},
                    "$addToSet": {
                        "appointments": {
                            "appointment_id": appt_id,
                            "doctor_name": clean_appt.get("doctor_name"),
                            "specialty": clean_appt.get("specialty"),
                            "hospital_name": clean_appt.get("hospital_name"),
                            "scheduled_time": clean_appt.get("scheduled_time") or str(clean_appt.get("start_datetime")),
                            "status": clean_appt.get("status", "CONFIRMED")
                        }
                    }
                },
                upsert=True
            )

        # 3. Append to Hospital History
        hosp_id = clean_appt.get("hospital_id")
        if hosp_id:
            db["hospital_history"].update_one(
                {"hospital_id": hosp_id},
                {
                    "$inc": {"total_appointments_booked": 1},
                    "$set": {"last_appointment_booked_at": now_iso},
                    "$addToSet": {"active_patient_phones": phone} if phone else {}
                },
                upsert=True
            )
    except Exception as e:
        print(f"[MongoDB Appointment Warning] Failed to persist appointment: {e}")


def persist_appointment_record(appointment_data: Dict[str, Any]) -> None:
    """Non-blocking, thread-pooled appointment record persistence to MongoDB."""
    try:
        _mongo_pool.submit(_exec_persist_appointment, dict(appointment_data))
    except Exception:
        pass


def _exec_persist_questionnaire(intake_data: Dict[str, Any]) -> None:
    try:
        db = get_mongo_db()
        if db is None:
            return

        now_iso = datetime.now(timezone.utc).isoformat()
        q_id = intake_data.get("response_id") or intake_data.get("id") or intake_data.get("questionnaire_id")
        clean_q = dict(intake_data)
        clean_q["updated_at"] = now_iso

        # 1. Questionnaires collection
        if q_id:
            db["questionnaires"].update_one({"response_id": q_id}, {"$set": clean_q}, upsert=True)
        else:
            db["questionnaires"].insert_one(clean_q)

        # 2. Append to Patient History
        patient_id = clean_q.get("patient_id") or clean_q.get("phone_number")
        if patient_id:
            db["patient_history"].update_one(
                {"$or": [{"patient_id": patient_id}, {"phone_number": patient_id}]},
                {
                    "$set": {"last_questionnaire_completed_at": now_iso},
                    "$addToSet": {
                        "questionnaire_records": {
                            "questionnaire_id": clean_q.get("questionnaire_id"),
                            "specialty": clean_q.get("specialty", "General"),
                            "completed_at": now_iso,
                            "answers": clean_q.get("answers", {})
                        }
                    }
                },
                upsert=True
            )
    except Exception as e:
        print(f"[MongoDB Questionnaire Warning] Failed to persist questionnaire: {e}")


def persist_questionnaire_response(intake_data: Dict[str, Any]) -> None:
    """Non-blocking, thread-pooled questionnaire response persistence to MongoDB."""
    try:
        _mongo_pool.submit(_exec_persist_questionnaire, dict(intake_data))
    except Exception:
        pass


def _exec_persist_encounter(encounter_data: Dict[str, Any]) -> None:
    try:
        db = get_mongo_db()
        if db is None:
            return

        now_iso = datetime.now(timezone.utc).isoformat()
        enc_id = encounter_data.get("encounter_id") or encounter_data.get("booking_id") or encounter_data.get("id")
        clean_enc = dict(encounter_data)
        clean_enc["encounter_id"] = enc_id
        clean_enc["created_at"] = now_iso

        # 1. Clinical Encounters collection
        db["clinical_encounters"].update_one({"encounter_id": enc_id}, {"$set": clean_enc}, upsert=True)

        # 2. Update Patient History
        phone = clean_enc.get("patient_phone")
        if phone:
            db["patient_history"].update_one(
                {"phone_number": phone},
                {
                    "$set": {"last_clinical_encounter_at": now_iso},
                    "$addToSet": {
                        "clinical_encounters": {
                            "encounter_id": enc_id,
                            "doctor_name": clean_enc.get("doctor_name"),
                            "specialty": clean_enc.get("specialty"),
                            "soap_notes": clean_enc.get("soap_notes", {}),
                            "prescriptions": clean_enc.get("prescriptions", []),
                            "date": now_iso
                        }
                    }
                },
                upsert=True
            )
    except Exception as e:
        print(f"[MongoDB Encounter Warning] Failed to persist clinical encounter: {e}")


def persist_clinical_encounter(encounter_data: Dict[str, Any]) -> None:
    """Non-blocking, thread-pooled clinical encounter persistence to MongoDB."""
    try:
        _mongo_pool.submit(_exec_persist_encounter, dict(encounter_data))
    except Exception:
        pass


def _exec_persist_hospital(hospital_data: Dict[str, Any]) -> None:
    try:
        db = get_mongo_db()
        if db is None:
            return

        hosp_id = hospital_data.get("hospital_id") or hospital_data.get("id")
        if not hosp_id:
            return

        clean_hosp = dict(hospital_data)
        clean_hosp["hospital_id"] = hosp_id
        clean_hosp["updated_at"] = datetime.now(timezone.utc).isoformat()

        db["hospital_history"].update_one({"hospital_id": hosp_id}, {"$set": clean_hosp}, upsert=True)
        db["hospitals"].update_one({"hospital_id": hosp_id}, {"$set": clean_hosp}, upsert=True)
    except Exception as e:
        print(f"[MongoDB Hospital History Warning] Failed to persist hospital: {e}")


def persist_hospital_history(hospital_data: Dict[str, Any]) -> None:
    """Non-blocking, thread-pooled hospital profile & history persistence to MongoDB."""
    try:
        _mongo_pool.submit(_exec_persist_hospital, dict(hospital_data))
    except Exception:
        pass



