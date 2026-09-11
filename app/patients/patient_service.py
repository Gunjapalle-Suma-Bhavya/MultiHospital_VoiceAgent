"""
Patient Self-Service & Profile Management Service (Section 5.8).

Manages patient registration, profile, self-service appointment viewing, cancellation, rescheduling, questionnaire responses, and communication preferences.

STRICT DATA MINIMIZATION: Patient profile root stores non-clinical administrative data only. Clinical responses are stored separately in encrypted intake records.
"""
import json
from datetime import datetime, date, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.database.models import (
    PatientProfile, Appointment, AppointmentStatus, PatientQuestionnaireResponse,
    Hospital, Doctor
)
from app.appointments.appointment_management import AppointmentService
from app.agent.context_manager import ContextBoundaryGuard


class PatientSelfServiceService:
    """
    Service managing patient registration, profile self-service, and questionnaire submissions.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.appointment_service = AppointmentService(db_session)

    def register_or_update_patient(
        self,
        phone_number: str,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        preferred_language: str = "English",
        communication_preference: str = "VOICE_AND_SMS",
        emergency_contact: Optional[Dict[str, str]] = None,
        external_patient_id: Optional[str] = None,
        saved_preferences: Optional[Dict[str, Any]] = None
    ) -> PatientProfile:
        patient = self.db.query(PatientProfile).filter(PatientProfile.phone_number == phone_number).first()
        if not patient:
            patient = PatientProfile(
                phone_number=phone_number,
                full_name=full_name,
                email=email,
                date_of_birth=date_of_birth,
                preferred_language=preferred_language,
                communication_preference=communication_preference,
                emergency_contact_json=json.dumps(emergency_contact) if emergency_contact else None,
                external_patient_id=external_patient_id,
                saved_preferences_json=json.dumps(saved_preferences) if saved_preferences else None
            )
            self.db.add(patient)
        else:
            if full_name: patient.full_name = full_name
            if email: patient.email = email
            if date_of_birth: patient.date_of_birth = date_of_birth
            if preferred_language: patient.preferred_language = preferred_language
            if communication_preference: patient.communication_preference = communication_preference
            if emergency_contact: patient.emergency_contact_json = json.dumps(emergency_contact)
            if external_patient_id: patient.external_patient_id = external_patient_id
            if saved_preferences: patient.saved_preferences_json = json.dumps(saved_preferences)

        self.db.commit()
        return patient

    def get_patient_profile(self, patient_id_or_phone: str) -> Dict[str, Any]:
        patient = self.db.query(PatientProfile).filter(
            (PatientProfile.id == patient_id_or_phone) | (PatientProfile.phone_number == patient_id_or_phone)
        ).first()

        if not patient:
            raise ValueError("Patient profile not found")

        emergency_contact = json.loads(patient.emergency_contact_json) if patient.emergency_contact_json else {}
        saved_preferences = json.loads(patient.saved_preferences_json) if patient.saved_preferences_json else {}

        # DATA MINIMIZATION: Clean non-clinical view
        return {
            "patient_id": patient.id,
            "phone_number": patient.phone_number,
            "full_name": patient.full_name,
            "name": patient.full_name or "",
            "email": patient.email,
            "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "preferred_language": patient.preferred_language,
            "communication_preference": patient.communication_preference,
            "emergency_contact": emergency_contact,
            "external_patient_id": patient.external_patient_id,
            "saved_preferences": saved_preferences
        }

    def get_patient_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        patient = self.db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
        if not patient:
            raise ValueError("Patient not found")

        appts = self.db.query(Appointment).filter(
            (Appointment.patient_id == patient_id) | (Appointment.patient_phone == patient.phone_number)
        ).order_by(Appointment.start_datetime.desc()).all()

        results = []
        for a in appts:
            hosp = self.db.query(Hospital).filter(Hospital.id == a.hospital_id).first()
            doc = self.db.query(Doctor).filter(Doctor.id == a.doctor_id).first()
            results.append({
                "appointment_id": a.id,
                "hospital_id": a.hospital_id,
                "hospital_name": hosp.name if hosp else "Hospital",
                "doctor_id": a.doctor_id,
                "doctor_name": doc.name if doc else "Doctor",
                "specialty": doc.specialty if doc else "Specialty",
                "start_datetime": a.start_datetime.isoformat(),
                "end_datetime": a.end_datetime.isoformat(),
                "status": a.status.value if a.status else None,
                "external_status": a.external_status,
                "is_ehr_verified": a.is_ehr_verified
            })
        return results

    def cancel_patient_appointment(self, patient_id: str, appointment_id: str, reason: str = "Cancelled by patient") -> Dict[str, Any]:
        appt = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            raise ValueError("Appointment not found")

        cancelled = self.appointment_service.cancel_appointment(appointment_id, changed_by="PATIENT", reason=reason)
        return {
            "appointment_id": cancelled.id,
            "status": cancelled.status.value,
            "message": "Appointment cancelled successfully"
        }

    def request_reschedule_patient_appointment(
        self,
        patient_id: str,
        appointment_id: str,
        new_start_datetime: datetime,
        reason: str = "Rescheduled by patient"
    ) -> Dict[str, Any]:
        rescheduled = self.appointment_service.reschedule_appointment(
            appointment_id, new_start_datetime=new_start_datetime, changed_by="PATIENT", reason=reason
        )
        return {
            "appointment_id": rescheduled.id,
            "new_start_datetime": rescheduled.start_datetime.isoformat(),
            "status": rescheduled.status.value,
            "message": "Appointment rescheduled successfully"
        }

    def submit_questionnaire_response(
        self,
        patient_id: str,
        questionnaire_id: str,
        answers: Optional[Dict[str, Any]] = None,
        responses: Optional[Dict[str, Any]] = None,
        appointment_id: Optional[str] = None
    ) -> PatientQuestionnaireResponse:
        patient = self.db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
        if not patient:
            raise ValueError("Patient not found")

        payload = responses or answers or {}
        clean_answers = ContextBoundaryGuard.sanitize_for_telemetry(payload)

        resp = PatientQuestionnaireResponse(
            patient_id=patient_id,
            questionnaire_id=questionnaire_id,
            appointment_id=appointment_id,
            answers_json=json.dumps(clean_answers)
        )
        self.db.add(resp)
        self.db.commit()
        return resp


    def register_patient(
        self,
        name: str,
        phone_number: str,
        email: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        preferred_language: str = "en",
        emergency_contact: Optional[Dict[str, Any]] = None,
        external_patient_id: Optional[str] = None,
        saved_preferences: Optional[Dict[str, Any]] = None
    ) -> PatientProfile:
        dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date() if isinstance(date_of_birth, str) and date_of_birth else None
        return self.register_or_update_patient(
            phone_number=phone_number,
            full_name=name,
            email=email,
            date_of_birth=dob,
            preferred_language=preferred_language,
            emergency_contact=emergency_contact,
            external_patient_id=external_patient_id,
            saved_preferences=saved_preferences
        )

    def update_patient_profile(
        self,
        patient_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        preferred_language: Optional[str] = None,
        emergency_contact: Optional[Dict[str, Any]] = None,
        external_patient_id: Optional[str] = None,
        saved_preferences: Optional[Dict[str, Any]] = None
    ) -> PatientProfile:
        patient = self.db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
        if not patient:
            raise ValueError("Patient profile not found")
        if name:
            patient.full_name = name
        if email:
            patient.email = email
        if date_of_birth:
            patient.date_of_birth = datetime.strptime(date_of_birth, "%Y-%m-%d").date() if isinstance(date_of_birth, str) else date_of_birth
        if preferred_language:
            patient.preferred_language = preferred_language
        if emergency_contact:
            patient.emergency_contact_json = json.dumps(emergency_contact)
        if external_patient_id:
            patient.external_patient_id = external_patient_id
        if saved_preferences:
            patient.saved_preferences_json = json.dumps(saved_preferences)
        self.db.commit()
        return patient

    def list_patient_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        return self.get_patient_appointments(patient_id)

    def cancel_appointment_self_service(self, patient_id: str, appointment_id: str, reason: str = "Cancelled by patient"):
        return self.appointment_service.cancel_appointment(appointment_id, changed_by="PATIENT", reason=reason)

    def request_reschedule_self_service(self, patient_id: str, appointment_id: str, new_start_datetime: datetime, reason: str = "Rescheduled by patient"):
        return self.appointment_service.reschedule_appointment(appointment_id, new_start_datetime=new_start_datetime, changed_by="PATIENT", reason=reason)

    def get_patient_questionnaire_responses(self, patient_id: str) -> List[Dict[str, Any]]:
        resps = self.db.query(PatientQuestionnaireResponse).filter(PatientQuestionnaireResponse.patient_id == patient_id).all()
        results = []
        for r in resps:
            results.append({
                "response_id": r.id,
                "questionnaire_id": r.questionnaire_id,
                "appointment_id": r.appointment_id,
                "responses": json.loads(r.answers_json) if r.answers_json else {}
            })
        return results

    def update_communication_preferences(self, patient_id: str, preference_channel: str) -> PatientProfile:
        patient = self.db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
        if not patient:
            raise ValueError("Patient not found")

        patient.communication_preference = preference_channel
        self.db.commit()
        return patient

    def set_granular_notification_preferences(
        self,
        patient_id: str,
        channels: Dict[str, bool],
        preferred_time_window: Optional[str] = "ANYTIME"
    ) -> Dict[str, Any]:
        patient = self.db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
        if not patient:
            raise ValueError("Patient not found")

        current_prefs = json.loads(patient.saved_preferences_json) if patient.saved_preferences_json else {}
        current_prefs["notification_channels"] = channels
        current_prefs["preferred_time_window"] = preferred_time_window
        patient.saved_preferences_json = json.dumps(current_prefs)
        patient.preferred_time_window = preferred_time_window
        self.db.commit()

        return {
            "patient_id": patient.id,
            "notification_channels": channels,
            "preferred_time_window": preferred_time_window,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }



from pydantic import BaseModel

class PatientRegistrationInput(BaseModel):
    name: str
    phone_number: str
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    preferred_language: str = "en"
    emergency_contact: Optional[Dict[str, Any]] = None
    external_patient_id: Optional[str] = None
    saved_preferences: Optional[Dict[str, Any]] = None

class QuestionnaireSubmissionInput(BaseModel):
    questionnaire_id: str
    answers: Optional[Dict[str, Any]] = None
    responses: Optional[Dict[str, Any]] = None
    appointment_id: Optional[str] = None


