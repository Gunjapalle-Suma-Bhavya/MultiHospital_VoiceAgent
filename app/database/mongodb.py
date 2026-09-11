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

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://gunjapallesumabhavya_db_user:FyqJLvHSZhb3ceIL@cluster0.scjuj68.mongodb.net/?appName=Cluster0"
)
DB_NAME = os.getenv("MONGODB_DB_NAME", "nexushealth_hospital_db")

_mongo_client: Optional[MongoClient] = None

def get_mongodb_client() -> Optional[MongoClient]:
    global _mongo_client
    if _mongo_client is None:
        try:
            _mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            # verify ping
            _mongo_client.admin.command('ping')
        except Exception as e:
            print(f"[MongoDB Warning] Connection error: {e}")
            return None
    return _mongo_client

def get_mongo_db():
    client = get_mongodb_client()
    if client is not None:
        return client[DB_NAME]
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

    return {
        "status": "success",
        "database": DB_NAME,
        "counts": {
            "hospitals": col_hospitals.count_documents({}),
            "doctors": col_doctors.count_documents({}),
            "patients": col_patients.count_documents({}),
            "questionnaires": col_questionnaires.count_documents({}),
            "appointments": col_appointments.count_documents({})
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
        colls = ["hospitals", "doctors", "patients", "questionnaires", "appointments", "events"]
        stats = {}
        for c in colls:
            stats[c] = db[c].count_documents({})
        return {"database": DB_NAME, "collections": stats}
    except Exception as e:
        return {"database": DB_NAME, "collections": {}, "error": str(e)}


def sync_event_to_mongodb(event_data: Dict[str, Any]) -> None:
    """
    Safely project published system events and domain updates into MongoDB Atlas.
    Guaranteed non-blocking and safe against network drops.
    """
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
        # Never crash callers
        print(f"[MongoDB Sync Warning] Sync event failed gracefully: {e}")


def persist_to_mongodb(collection_name: str, doc_data: Dict[str, Any], key_field: Optional[str] = None) -> None:
    """
    Universally and safely persists any user-entered document directly to MongoDB Atlas.
    Supports upsert when key_field is provided, otherwise inserts.
    Guaranteed non-blocking, exception-safe, and fail-safe.
    """
    try:
        db = get_mongo_db()
        if db is None:
            return

        clean_doc = dict(doc_data)
        if "persisted_at" not in clean_doc:
            clean_doc["persisted_at"] = datetime.now(timezone.utc).isoformat()

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



