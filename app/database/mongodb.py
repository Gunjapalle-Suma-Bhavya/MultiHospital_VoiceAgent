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

def sync_mongodb_catalog() -> Dict[str, Any]:
    """
    Syncs the active hospital directory and doctor roster from SQLite into MongoDB Atlas.
    Creates indexes on transactional collections for real-time dynamic queries.
    DOES NOT insert mock conversations, mock appointments, or fake patients.
    """
    db = get_mongo_db()
    if db is None:
        return {"status": "error", "message": "MongoDB not connected"}

    from app.database.config import SessionLocal
    from app.database.models import Hospital, Doctor
    import json

    sqlite_db = SessionLocal()
    try:
        # 1. Hospitals Catalog: Dynamic from SQLite
        col_hospitals = db["hospitals"]
        active_hospitals = sqlite_db.query(Hospital).filter(Hospital.is_active == True).all()
        for h in active_hospitals:
            depts = []
            try:
                if h.departments_json:
                    depts = json.loads(h.departments_json) if isinstance(h.departments_json, str) else h.departments_json
            except Exception:
                depts = []
            specs = []
            try:
                if h.specialties_json:
                    specs = json.loads(h.specialties_json) if isinstance(h.specialties_json, str) else h.specialties_json
            except Exception:
                specs = []

            h_doc = {
                "hospital_id": h.id,
                "name": h.name,
                "code": h.code,
                "status": h.hospital_status.value if hasattr(h.hospital_status, "value") else str(h.hospital_status),
                "address": h.address or "Regional Medical Campus",
                "phone": h.phone or "+1-800-NEXUS-CARE",
                "contact_email": h.contact_email,
                "departments": depts,
                "specialties": specs,
                "operating_hours": "Mon-Fri: 08:00 AM - 06:00 PM, Sat: 09:00 AM - 01:00 PM",
                "is_active": bool(h.is_active),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            col_hospitals.update_one({"hospital_id": h.id}, {"$set": h_doc}, upsert=True)

        # 2. Doctors Catalog: Dynamic from SQLite
        col_doctors = db["doctors"]
        active_doctors = sqlite_db.query(Doctor).filter(Doctor.is_active == True).all()
        for d in active_doctors:
            hosp = sqlite_db.query(Hospital).filter(Hospital.id == d.hospital_id).first()
            d_doc = {
                "doctor_id": d.id,
                "hospital_id": d.hospital_id,
                "hospital_name": hosp.name if hosp else "NexusHealth Hospital",
                "name": d.name,
                "specialty": d.specialty,
                "department": d.department or d.specialty,
                "default_appointment_duration": d.default_appointment_duration or 30,
                "status": d.doctor_status.value if hasattr(d.doctor_status, "value") else str(d.doctor_status),
                "is_active": bool(d.is_active),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            col_doctors.update_one({"doctor_id": d.id}, {"$set": d_doc}, upsert=True)

        # 3. Hospital History Profiles (clean counters for dynamic tracking)
        col_hh = db["hospital_history"]
        for h in active_hospitals:
            existing_hh = col_hh.find_one({"hospital_id": h.id})
            if not existing_hh:
                col_hh.insert_one({
                    "hospital_id": h.id,
                    "name": h.name,
                    "code": h.code,
                    "total_appointments_booked": 0,
                    "total_voice_inquiries": 0,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })

        # 4. Create collection indexes for high performance queries
        try:
            db["conversations"].create_index("session_id")
            db["conversations"].create_index("patient_phone")
            db["appointments"].create_index("appointment_id")
            db["appointments"].create_index("patient_phone")
            db["appointments"].create_index("doctor_id")
            db["patient_history"].create_index("phone_number")
            db["patient_preferences"].create_index("phone_number")
            db["patients"].create_index("phone_number")
            db["questionnaires"].create_index("response_id")
        except Exception:
            pass

        return {
            "status": "success",
            "message": f"Synced {len(active_hospitals)} hospitals and {len(active_doctors)} doctors from SQLite to MongoDB Atlas.",
            "synced_hospitals": len(active_hospitals),
            "synced_doctors": len(active_doctors)
        }
    finally:
        sqlite_db.close()

# Backward compatible alias
seed_mongodb_data = sync_mongodb_catalog


def clear_mongodb_dynamic_data() -> Dict[str, Any]:
    """
    Purges all static and mock records from dynamic transactional collections:
    - conversations
    - appointments
    - patient_history
    - patient_preferences
    - patients
    - questionnaires
    - clinical_encounters
    - events
    - notifications
    Resets hospital history counters to 0 so only real incoming patient traffic is tracked.
    """
    db = get_mongo_db()
    if db is None:
        return {"status": "error", "message": "MongoDB not connected"}

    dynamic_collections = [
        "conversations",
        "appointments",
        "patient_history",
        "patient_preferences",
        "patients",
        "questionnaires",
        "clinical_encounters",
        "events",
        "notifications"
    ]
    deleted = {}
    for col in dynamic_collections:
        res = db[col].delete_many({})
        deleted[col] = res.deleted_count

    # Reset hospital counters
    db["hospital_history"].update_many({}, {
        "$set": {
            "total_appointments_booked": 0,
            "total_voice_inquiries": 0,
            "last_appointment_booked_at": None,
            "last_voice_inquiry_at": None,
            "active_patient_phones": []
        }
    })
    return {"status": "success", "cleared": deleted}


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



