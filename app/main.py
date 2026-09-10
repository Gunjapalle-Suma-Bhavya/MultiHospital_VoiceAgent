"""
FastAPI Main Entrypoint for Multi-Hospital Patient Intake, Scheduling & Pre-Visit Voice Agent.

Exposes end-to-end REST endpoints for:
- Self-Service Hospital Registration & Onboarding (Section 5.1)
- 13-Step Platform Admin Journey (Section 4.4)
- 19-Step Patient Journey (Section 4.3)
- 10-Step Doctor Journey (Section 4.2)
- 15-Step Hospital Journey (Section 4.1)
- 5-Stage Horizontal Platform Pipeline (Step 2)
- Product Vision & Executive Summary Quality Metrics (Step 3)
- 16-Step Coordinated Product Vision Engine (Step 4)
- 12-Stage AI-Native Workflow Lifecycle (Step 5)
- AI Capability Dispatching & Operational Intelligence Telemetry
"""

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.database.models import Base, EHRAdapterType, DoctorStatus, ConsultationType, CalendarType, AppointmentStatus
from app.pipeline.orchestrator import HorizontalPlatformPipeline
from app.vision.executive_summary import ProductVisionEngine
from app.agent.coordinator import ProductVision16StepCoordinator
from app.agent.native_workflow import AINativeWorkflowEngine
from app.journeys.hospital_journey import HospitalJourneyEngine
from app.journeys.doctor_journey import DoctorJourneyEngine
from app.journeys.patient_journey import PatientJourneyEngine
from app.journeys.admin_journey import PlatformAdminJourneyEngine
from app.onboarding.hospital_onboarding import HospitalSelfServiceOnboardingService
from app.admin.admin_approval import PlatformAdminApprovalService
from app.admin.hospital_admin import HospitalAdminService
from app.doctors.doctor_management import DoctorManagementService
from app.calendars.doctor_calendar import DoctorCalendarService
from app.scheduling.availability_engine import AvailabilityEngine
from app.appointments.appointment_management import AppointmentService
from app.patients.patient_service import PatientSelfServiceService
from app.agent.patient_access_agent import AIPatientAccessAgent

app = FastAPI(
    title="Autonomous Multi-Hospital Voice Agent Network API",
    version="10.0.0",
    description="Enterprise Multi-Hospital Voice Agent Platform & Self-Service Hospital Onboarding Engine"
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_URL = "sqlite:///./platform_voice_agent.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {
        "status": "ONLINE",
        "platform": "Autonomous Multi-Hospital Patient Intake Voice Platform",
        "step": "Section 5.1: Self-Service Hospital Onboarding Active"
    }


# =========================================================================
# SECTION 5.1: SELF-SERVICE HOSPITAL REGISTRATION & ONBOARDING ENDPOINTS
# =========================================================================

class CreateDraftHospitalInput(BaseModel):
    name: str
    code: str
    contact_email: str
    admin_name: str
    admin_email: str

@app.post("/onboarding/hospital/draft")
def create_draft_hospital(payload: CreateDraftHospitalInput, db: Session = Depends(get_db)):
    onboarding = HospitalSelfServiceOnboardingService(db)
    hosp = onboarding.create_draft_hospital(
        name=payload.name,
        code=payload.code,
        contact_email=payload.contact_email,
        admin_name=payload.admin_name,
        admin_email=payload.admin_email
    )
    return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "is_active": hosp.is_active}


class UpdateDraftMetadataInput(BaseModel):
    organization_info: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    departments: Optional[List[str]] = None
    specialties: Optional[List[str]] = None
    services: Optional[List[str]] = None
    tax_id: Optional[str] = None
    license_id: Optional[str] = None

@app.put("/onboarding/hospital/{hospital_id}/metadata")
def update_draft_metadata(hospital_id: str, payload: UpdateDraftMetadataInput, db: Session = Depends(get_db)):
    onboarding = HospitalSelfServiceOnboardingService(db)
    hosp = onboarding.update_hospital_draft_metadata(
        hospital_id=hospital_id,
        organization_info=payload.organization_info,
        address=payload.address,
        phone=payload.phone,
        website=payload.website,
        departments=payload.departments,
        specialties=payload.specialties,
        services=payload.services,
        tax_id=payload.tax_id,
        license_id=payload.license_id
    )
    return {"hospital_id": hosp.id, "status": hosp.hospital_status.value}


@app.post("/onboarding/hospital/{hospital_id}/submit")
def submit_application(hospital_id: str, db: Session = Depends(get_db)):
    onboarding = HospitalSelfServiceOnboardingService(db)
    hosp = onboarding.submit_application(hospital_id)
    return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "is_active": hosp.is_active}


@app.post("/onboarding/hospital/{hospital_id}/approve")
def approve_hospital(hospital_id: str, db: Session = Depends(get_db)):
    onboarding = HospitalSelfServiceOnboardingService(db)
    hosp = onboarding.approve_hospital(hospital_id)
    return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "is_active": hosp.is_active}


class RejectHospitalInput(BaseModel):
    reason: str

@app.post("/onboarding/hospital/{hospital_id}/reject")
def reject_hospital(hospital_id: str, payload: RejectHospitalInput, db: Session = Depends(get_db)):
    onboarding = HospitalSelfServiceOnboardingService(db)
    hosp = onboarding.reject_hospital(hospital_id, payload.reason)
    return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "is_active": hosp.is_active, "rejection_reason": hosp.rejection_reason}


# =========================================================================
# SECTION 5.2: PLATFORM ADMIN APPROVAL ENDPOINTS
# =========================================================================

class RequestCorrectionsInput(BaseModel):
    notes: str

class SuspendHospitalInput(BaseModel):
    reason: str

@app.get("/api/v1/admin/hospitals/{hospital_id}")
def admin_review_hospital_info(hospital_id: str, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        return admin_service.review_hospital_info(hospital_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/v1/admin/hospitals/{hospital_id}/approve")
def admin_approve_hospital(hospital_id: str, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        hosp = admin_service.approve_hospital(hospital_id)
        return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "is_active": hosp.is_active}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/admin/hospitals/{hospital_id}/reject")
def admin_reject_hospital(hospital_id: str, payload: RejectHospitalInput, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        hosp = admin_service.reject_hospital(hospital_id, payload.reason)
        return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "is_active": hosp.is_active, "rejection_reason": hosp.rejection_reason}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/admin/hospitals/{hospital_id}/request-corrections")
def admin_request_corrections(hospital_id: str, payload: RequestCorrectionsInput, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        hosp = admin_service.request_corrections(hospital_id, payload.notes)
        return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "is_active": hosp.is_active, "correction_notes": hosp.correction_notes}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/admin/hospitals/{hospital_id}/suspend")
def admin_suspend_hospital(hospital_id: str, payload: SuspendHospitalInput, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        hosp = admin_service.suspend_hospital(hospital_id, payload.reason)
        return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "is_active": hosp.is_active, "suspension_reason": hosp.suspension_reason}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/admin/hospitals/{hospital_id}/reactivate")
def admin_reactivate_hospital(hospital_id: str, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        hosp = admin_service.reactivate_hospital(hospital_id)
        return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "is_active": hosp.is_active}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/admin/hospitals/{hospital_id}/activity")
def admin_view_hospital_activity(hospital_id: str, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        return admin_service.view_hospital_activity(hospital_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/v1/admin/hospitals/{hospital_id}/ehr-config")
def admin_review_ehr_config(hospital_id: str, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        return admin_service.review_ehr_integration_config(hospital_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/v1/admin/hospitals/{hospital_id}/ehr-config/activate")
def admin_activate_ehr_config(hospital_id: str, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        config = admin_service.activate_ehr_integration(hospital_id)
        return {"hospital_id": hospital_id, "config_id": config.id, "is_active": config.is_active}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================================
# SECTION 5.3: HOSPITAL ADMINISTRATION ENDPOINTS
# =========================================================================

class UpdateHospitalProfileInput(BaseModel):
    name: Optional[str] = None
    organization_info: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    contact_email: Optional[str] = None
    website: Optional[str] = None
    timezone: Optional[str] = None

class UpdateDepartmentsSpecialtiesInput(BaseModel):
    departments: Optional[List[str]] = None
    specialties: Optional[List[str]] = None
    services: Optional[List[str]] = None

class UpdateAppointmentSettingsInput(BaseModel):
    max_advance_booking_days: int = 30
    cancellation_notice_hours: int = 24
    auto_reminders_enabled: bool = True

class AddStaffInput(BaseModel):
    name: str
    email: str
    role: str = "STAFF"
    phone: Optional[str] = None

class UpdateCommunicationPrefInput(BaseModel):
    communication_preference: str = "VOICE_AND_SMS"
    sms_enabled: bool = True
    voice_enabled: bool = True

class CreateQuestionnaireInput(BaseModel):
    title: str
    specialty: str
    questions: List[str]

class ConfigureEHRInput(BaseModel):
    adapter_type: EHRAdapterType
    endpoint_url: Optional[str] = None
    api_base_url: Optional[str] = None
    is_sync_enabled: bool = True

@app.get("/api/v1/hospital-admin/{hospital_id}/profile")
def get_hospital_admin_profile(hospital_id: str, db: Session = Depends(get_db)):
    service = HospitalAdminService(db)
    try:
        return service.get_hospital_profile(hospital_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/api/v1/hospital-admin/{hospital_id}/profile")
def update_hospital_admin_profile(hospital_id: str, payload: UpdateHospitalProfileInput, db: Session = Depends(get_db)):
    service = HospitalAdminService(db)
    try:
        hosp = service.update_hospital_profile(
            hospital_id=hospital_id, name=payload.name, organization_info=payload.organization_info,
            address=payload.address, phone=payload.phone, contact_email=payload.contact_email,
            website=payload.website, timezone=payload.timezone
        )
        return {"hospital_id": hosp.id, "name": hosp.name, "updated": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/v1/hospital-admin/{hospital_id}/departments-specialties")
def update_departments_specialties(hospital_id: str, payload: UpdateDepartmentsSpecialtiesInput, db: Session = Depends(get_db)):
    service = HospitalAdminService(db)
    try:
        hosp = service.update_departments_and_specialties(
            hospital_id=hospital_id, departments=payload.departments, specialties=payload.specialties, services=payload.services
        )
        return {"hospital_id": hosp.id, "updated": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/v1/hospital-admin/{hospital_id}/appointment-settings")
def update_appointment_settings(hospital_id: str, payload: UpdateAppointmentSettingsInput, db: Session = Depends(get_db)):
    service = HospitalAdminService(db)
    try:
        pref = service.update_appointment_settings(
            hospital_id=hospital_id, max_advance_booking_days=payload.max_advance_booking_days,
            cancellation_notice_hours=payload.cancellation_notice_hours, auto_reminders_enabled=payload.auto_reminders_enabled
        )
        return {"hospital_id": hospital_id, "max_advance_days": pref.max_advance_booking_days, "updated": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/hospital-admin/{hospital_id}/staff")
def add_hospital_staff(hospital_id: str, payload: AddStaffInput, db: Session = Depends(get_db)):
    service = HospitalAdminService(db)
    try:
        staff = service.add_staff_member(hospital_id=hospital_id, name=payload.name, email=payload.email, role=payload.role, phone=payload.phone)
        return {"staff_id": staff.id, "hospital_id": hospital_id, "name": staff.name, "role": staff.role}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/hospital-admin/{hospital_id}/staff")
def list_hospital_staff(hospital_id: str, db: Session = Depends(get_db)):
    service = HospitalAdminService(db)
    try:
        return service.list_staff_members(hospital_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/api/v1/hospital-admin/{hospital_id}/communication-preferences")
def update_comm_preferences(hospital_id: str, payload: UpdateCommunicationPrefInput, db: Session = Depends(get_db)):
    service = HospitalAdminService(db)
    try:
        pref = service.update_communication_preferences(
            hospital_id=hospital_id, communication_preference=payload.communication_preference,
            sms_enabled=payload.sms_enabled, voice_enabled=payload.voice_enabled
        )
        return {"hospital_id": hospital_id, "communication_preference": pref.communication_preference, "updated": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/hospital-admin/{hospital_id}/questionnaires")
def create_hospital_questionnaire(hospital_id: str, payload: CreateQuestionnaireInput, db: Session = Depends(get_db)):
    service = HospitalAdminService(db)
    try:
        q = service.create_questionnaire(hospital_id=hospital_id, title=payload.title, specialty=payload.specialty, questions=payload.questions)
        return {"questionnaire_id": q.id, "hospital_id": hospital_id, "title": q.title}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/hospital-admin/{hospital_id}/questionnaires")
def list_hospital_questionnaires(hospital_id: str, db: Session = Depends(get_db)):
    service = HospitalAdminService(db)
    try:
        return service.list_questionnaires(hospital_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/api/v1/hospital-admin/{hospital_id}/ehr-integration")
def configure_hospital_ehr(hospital_id: str, payload: ConfigureEHRInput, db: Session = Depends(get_db)):
    service = HospitalAdminService(db)
    try:
        config = service.configure_ehr_integration(
            hospital_id=hospital_id, adapter_type=payload.adapter_type,
            endpoint_url=payload.endpoint_url, api_base_url=payload.api_base_url, is_sync_enabled=payload.is_sync_enabled
        )
        return {"config_id": config.id, "hospital_id": hospital_id, "adapter_type": config.adapter_type.value, "updated": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/hospital-admin/{hospital_id}/analytics")
def get_hospital_analytics(hospital_id: str, db: Session = Depends(get_db)):
    service = HospitalAdminService(db)
    try:
        return service.get_isolated_hospital_analytics(hospital_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =========================================================================
# SECTION 5.4: DOCTOR MANAGEMENT ENDPOINTS
# =========================================================================

class InviteDoctorInput(BaseModel):
    hospital_id: str
    name: str
    specialty: str
    department: Optional[str] = None
    qualifications: Optional[str] = None
    experience_years: int = 0
    languages: Optional[List[str]] = None
    consultation_type: ConsultationType = ConsultationType.IN_PERSON
    default_appointment_duration: int = 30
    external_provider_id: Optional[str] = None

class SuspendDoctorInput(BaseModel):
    reason: Optional[str] = None

class UpdateDoctorProfileInput(BaseModel):
    name: Optional[str] = None
    photo_url: Optional[str] = None
    specialty: Optional[str] = None
    department: Optional[str] = None
    qualifications: Optional[str] = None
    experience_years: Optional[int] = None
    languages: Optional[List[str]] = None
    consultation_type: Optional[ConsultationType] = None
    default_appointment_duration: Optional[int] = None
    external_provider_id: Optional[str] = None
    bio: Optional[str] = None
    professional_info: Optional[str] = None
    special_instructions: Optional[str] = None

@app.post("/api/v1/doctors/invite")
def invite_doctor(payload: InviteDoctorInput, db: Session = Depends(get_db)):
    service = DoctorManagementService(db)
    try:
        doc = service.invite_doctor(
            hospital_id=payload.hospital_id, name=payload.name, specialty=payload.specialty,
            department=payload.department, qualifications=payload.qualifications,
            experience_years=payload.experience_years, languages=payload.languages,
            consultation_type=payload.consultation_type, default_appointment_duration=payload.default_appointment_duration,
            external_provider_id=payload.external_provider_id
        )
        return {"doctor_id": doc.id, "status": doc.doctor_status.value, "is_active": doc.is_active}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/doctors/{doctor_id}/activate")
def activate_doctor(doctor_id: str, db: Session = Depends(get_db)):
    service = DoctorManagementService(db)
    try:
        doc = service.activate_doctor(doctor_id)
        return {"doctor_id": doc.id, "status": doc.doctor_status.value, "is_active": doc.is_active}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/doctors/{doctor_id}/deactivate")
def deactivate_doctor(doctor_id: str, db: Session = Depends(get_db)):
    service = DoctorManagementService(db)
    try:
        doc = service.deactivate_doctor(doctor_id)
        return {"doctor_id": doc.id, "status": doc.doctor_status.value, "is_active": doc.is_active}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/doctors/{doctor_id}/suspend")
def suspend_doctor(doctor_id: str, payload: SuspendDoctorInput, db: Session = Depends(get_db)):
    service = DoctorManagementService(db)
    try:
        doc = service.suspend_doctor(doctor_id, payload.reason)
        return {"doctor_id": doc.id, "status": doc.doctor_status.value, "is_active": doc.is_active}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/v1/doctors/{doctor_id}/profile")
def update_doctor_profile(doctor_id: str, payload: UpdateDoctorProfileInput, db: Session = Depends(get_db)):
    service = DoctorManagementService(db)
    try:
        doc = service.update_doctor_profile(
            doctor_id=doctor_id, name=payload.name, photo_url=payload.photo_url, specialty=payload.specialty,
            department=payload.department, qualifications=payload.qualifications, experience_years=payload.experience_years,
            languages=payload.languages, consultation_type=payload.consultation_type, default_appointment_duration=payload.default_appointment_duration,
            external_provider_id=payload.external_provider_id, bio=payload.bio, professional_info=payload.professional_info,
            special_instructions=payload.special_instructions
        )
        return {"doctor_id": doc.id, "updated": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/doctors/{doctor_id}")
def get_doctor_profile(doctor_id: str, db: Session = Depends(get_db)):
    service = DoctorManagementService(db)
    try:
        return service.get_doctor_profile(doctor_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/v1/hospitals/{hospital_id}/doctors")
def list_doctors_for_hospital(hospital_id: str, status: Optional[DoctorStatus] = None, db: Session = Depends(get_db)):
    service = DoctorManagementService(db)
    try:
        return service.list_doctors_for_hospital(hospital_id=hospital_id, status_filter=status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =========================================================================
# SECTION 5.5: DOCTOR CALENDAR MANAGEMENT ENDPOINTS
# =========================================================================

class CreateDoctorCalendarInput(BaseModel):
    doctor_id: str
    calendar_name: str
    calendar_type: CalendarType = CalendarType.HOSPITAL_CONSULTATION

@app.post("/api/v1/calendars")
def create_doctor_calendar(payload: CreateDoctorCalendarInput, db: Session = Depends(get_db)):
    service = DoctorCalendarService(db)
    try:
        cal = service.create_doctor_calendar(doctor_id=payload.doctor_id, calendar_name=payload.calendar_name, calendar_type=payload.calendar_type)
        return {"calendar_id": cal.id, "doctor_id": cal.doctor_id, "calendar_name": cal.calendar_name, "calendar_type": cal.calendar_type.value}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/doctors/{doctor_id}/calendars")
def list_doctor_calendars(doctor_id: str, db: Session = Depends(get_db)):
    service = DoctorCalendarService(db)
    try:
        return service.list_doctor_calendars(doctor_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/v1/doctors/{doctor_id}/calendar-view")
def get_calendar_aggregated_view(doctor_id: str, target_date: str, calendar_id: Optional[str] = None, db: Session = Depends(get_db)):
    service = DoctorCalendarService(db)
    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d").date()
        return service.get_calendar_aggregated_view(doctor_id=doctor_id, target_date=dt, calendar_id=calendar_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================================
# SECTION 5.6: AVAILABILITY & SLOT ENGINE ENDPOINTS
# =========================================================================

class EvaluateSlotInput(BaseModel):
    doctor_id: str
    slot_start: datetime
    slot_end: datetime
    calendar_id: Optional[str] = None
    appointment_type: Optional[str] = None

@app.post("/api/v1/availability/evaluate-slot")
def evaluate_slot_pipeline(payload: EvaluateSlotInput, db: Session = Depends(get_db)):
    engine = AvailabilityEngine(db)
    return engine.evaluate_slot_pipeline(
        doctor_id=payload.doctor_id, slot_start=payload.slot_start, slot_end=payload.slot_end,
        calendar_id=payload.calendar_id, appointment_type=payload.appointment_type
    )

@app.get("/api/v1/doctors/{doctor_id}/availability")
def query_actual_availability(doctor_id: str, target_date: str, calendar_id: Optional[str] = None, time_window: str = "ANYTIME", db: Session = Depends(get_db)):
    engine = AvailabilityEngine(db)
    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d").date()
        return engine.query_actual_availability(doctor_id=doctor_id, target_date=dt, calendar_id=calendar_id, time_window=time_window)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================================
# SECTION 5.7: APPOINTMENT MANAGEMENT ENDPOINTS
# =========================================================================

class RequestAppointmentInput(BaseModel):
    hospital_id: str
    doctor_id: str
    patient_name: str
    patient_phone: str
    start_datetime: datetime
    calendar_id: Optional[str] = None
    patient_email: Optional[str] = None
    patient_id: Optional[str] = None

class RescheduleAppointmentInput(BaseModel):
    new_start_datetime: datetime
    reason: Optional[str] = None

class CancelAppointmentInput(BaseModel):
    reason: Optional[str] = None

@app.post("/api/v1/appointments/request")
def request_appointment(payload: RequestAppointmentInput, db: Session = Depends(get_db)):
    service = AppointmentService(db)
    try:
        appt = service.create_appointment_request(
            hospital_id=payload.hospital_id, doctor_id=payload.doctor_id, patient_name=payload.patient_name,
            patient_phone=payload.patient_phone, start_datetime=payload.start_datetime, calendar_id=payload.calendar_id,
            patient_email=payload.patient_email, patient_id=payload.patient_id
        )
        return {"appointment_id": appt.id, "status": appt.status.value, "external_status": appt.external_status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/appointments/{appointment_id}/confirm")
def confirm_appointment(appointment_id: str, db: Session = Depends(get_db)):
    service = AppointmentService(db)
    try:
        appt = service.confirm_appointment(appointment_id)
        return {"appointment_id": appt.id, "status": appt.status.value, "external_status": appt.external_status, "is_ehr_verified": appt.is_ehr_verified}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/appointments/{appointment_id}/reschedule")
def reschedule_appointment(appointment_id: str, payload: RescheduleAppointmentInput, db: Session = Depends(get_db)):
    service = AppointmentService(db)
    try:
        appt = service.reschedule_appointment(appointment_id=appointment_id, new_start_datetime=payload.new_start_datetime, reason=payload.reason)
        return {"appointment_id": appt.id, "new_start_datetime": appt.start_datetime.isoformat(), "status": appt.status.value}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/appointments/{appointment_id}/cancel")
def cancel_appointment(appointment_id: str, payload: CancelAppointmentInput, db: Session = Depends(get_db)):
    service = AppointmentService(db)
    try:
        appt = service.cancel_appointment(appointment_id=appointment_id, reason=payload.reason)
        return {"appointment_id": appt.id, "status": appt.status.value, "external_status": appt.external_status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/appointments/{appointment_id}/complete")
def complete_appointment(appointment_id: str, db: Session = Depends(get_db)):
    service = AppointmentService(db)
    try:
        appt = service.complete_appointment(appointment_id)
        return {"appointment_id": appt.id, "status": appt.status.value}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/appointments/{appointment_id}/no-show")
def mark_appointment_no_show(appointment_id: str, db: Session = Depends(get_db)):
    service = AppointmentService(db)
    try:
        appt = service.mark_no_show(appointment_id)
        return {"appointment_id": appt.id, "status": appt.status.value}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/appointments/{appointment_id}/history")
def get_appointment_history(appointment_id: str, db: Session = Depends(get_db)):
    service = AppointmentService(db)
    try:
        return service.get_appointment_history(appointment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =========================================================================
# SECTION 4.4: PLATFORM ADMIN JOURNEY ENDPOINTS
# =========================================================================

class ExecuteAdminJourneyInput(BaseModel):
    admin_email: str

@app.post("/journeys/admin/execute")
def execute_admin_journey(payload: ExecuteAdminJourneyInput, db: Session = Depends(get_db)):
    journey = PlatformAdminJourneyEngine(db)
    return journey.execute_full_admin_journey(admin_email=payload.admin_email)


# =========================================================================
# SECTION 4.3: PATIENT JOURNEY ENDPOINTS
# =========================================================================

class ExecutePatientJourneyInput(BaseModel):
    phone_number: str
    patient_name: str
    utterance: str
    intake_symptoms: Optional[str] = "Experiencing mild discomfort for past 4 days."

@app.post("/journeys/patient/execute")
def execute_patient_journey(payload: ExecutePatientJourneyInput, db: Session = Depends(get_db)):
    journey = PatientJourneyEngine(db)
    return journey.execute_full_patient_journey(
        phone_number=payload.phone_number,
        patient_name=payload.patient_name,
        utterance=payload.utterance,
        intake_symptoms=payload.intake_symptoms
    )


# =========================================================================
# SECTION 4.2: DOCTOR JOURNEY ENDPOINTS
# =========================================================================

class ExecuteDoctorJourneyInput(BaseModel):
    hospital_id: str
    doctor_name: str
    specialty: str
    bio: str
    special_instructions: str
    approved_questions: List[str]
    blocked_leave_start: Optional[datetime] = None
    blocked_leave_end: Optional[datetime] = None

@app.post("/journeys/doctor/execute")
def execute_doctor_journey(payload: ExecuteDoctorJourneyInput, db: Session = Depends(get_db)):
    journey = DoctorJourneyEngine(db)
    return journey.execute_full_doctor_journey(
        hospital_id=payload.hospital_id,
        doctor_name=payload.doctor_name,
        specialty=payload.specialty,
        bio=payload.bio,
        special_instructions=payload.special_instructions,
        approved_questions=payload.approved_questions,
        blocked_leave_start=payload.blocked_leave_start,
        blocked_leave_end=payload.blocked_leave_end
    )


@app.get("/journeys/doctor/{doctor_id}/dashboard")
def get_doctor_dashboard(doctor_id: str, db: Session = Depends(get_db)):
    journey = DoctorJourneyEngine(db)
    res = journey.get_doctor_dashboard(doctor_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


# =========================================================================
# SECTION 4.1: HOSPITAL JOURNEY ENDPOINTS
# =========================================================================

class ExecuteHospitalJourneyInput(BaseModel):
    name: str
    code: str
    address: str
    contact_email: str
    doctor_name: str
    specialty: str
    questionnaire_title: str
    questions: List[Dict[str, Any]]
    ehr_adapter_type: Optional[str] = "MOCK_EHR"

@app.post("/journeys/hospital/execute")
def execute_hospital_journey(payload: ExecuteHospitalJourneyInput, db: Session = Depends(get_db)):
    journey = HospitalJourneyEngine(db)
    adapter_enum = EHRAdapterType.FHIR_R4 if payload.ehr_adapter_type == "FHIR_R4" else EHRAdapterType.MOCK_EHR
    return journey.execute_full_hospital_journey(
        name=payload.name,
        code=payload.code,
        address=payload.address,
        contact_email=payload.contact_email,
        doctor_name=payload.doctor_name,
        specialty=payload.specialty,
        questionnaire_title=payload.questionnaire_title,
        questions=payload.questions,
        ehr_adapter_type=adapter_enum
    )


@app.get("/journeys/hospital/{hospital_id}/analytics")
def get_hospital_analytics(hospital_id: str, db: Session = Depends(get_db)):
    journey = HospitalJourneyEngine(db)
    return journey.get_hospital_analytics(hospital_id)


# =========================================================================
# STEP 5: AI-NATIVE WORKFLOW LIFECYCLE ENDPOINT
# =========================================================================

class NativeWorkflowInput(BaseModel):
    phone_number: str
    patient_name: str
    utterance: str

@app.post("/agent/native-workflow-lifecycle")
def native_workflow_lifecycle(payload: NativeWorkflowInput, db: Session = Depends(get_db)):
    native_engine = AINativeWorkflowEngine(db)
    return native_engine.execute_native_ai_lifecycle(
        phone_number=payload.phone_number,
        patient_name=payload.patient_name,
        utterance=payload.utterance
    )


# =========================================================================
# STEP 4: 16-STEP COORDINATED PRODUCT VISION ENDPOINT
# =========================================================================

class Coordinate16StepsInput(BaseModel):
    phone_number: str
    patient_name: str
    utterance: str
    pre_visit_symptoms: Optional[str] = None

@app.post("/vision/coordinate-16-steps")
def coordinate_16_steps(payload: Coordinate16StepsInput, db: Session = Depends(get_db)):
    coordinator = ProductVision16StepCoordinator(db)
    return coordinator.execute_16_step_coordination(
        phone_number=payload.phone_number,
        patient_name=payload.patient_name,
        utterance=payload.utterance,
        pre_visit_symptoms=payload.pre_visit_symptoms
    )


# =========================================================================
# STEP 3 PRODUCT VISION & EXECUTIVE SUMMARY ENDPOINTS
# =========================================================================

@app.get("/vision/executive-summary")
def get_executive_summary_vision(db: Session = Depends(get_db)):
    vision_engine = ProductVisionEngine(db)
    return vision_engine.evaluate_ai_quality_metrics()


@app.get("/vision/doctor-prep-briefing/{appointment_id}")
def get_doctor_prep_briefing(appointment_id: str, db: Session = Depends(get_db)):
    vision_engine = ProductVisionEngine(db)
    res = vision_engine.generate_doctor_preparation_briefing(appointment_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


# =========================================================================
# STEP 2 HORIZONTAL PIPELINE ENDPOINTS
# =========================================================================

class Stage1OnboardInput(BaseModel):
    hospital_name: str
    hospital_code: str
    doctor_name: str
    specialty: str

@app.post("/pipeline/stage-1/hospital-onboard")
def onboard_hospital(payload: Stage1OnboardInput, db: Session = Depends(get_db)):
    pipeline = HorizontalPlatformPipeline(db)
    return pipeline.execute_stage_1_hospital_onboarding(
        hospital_name=payload.hospital_name,
        hospital_code=payload.hospital_code,
        doctor_name=payload.doctor_name,
        specialty=payload.specialty
    )


class Stage2EngagementInput(BaseModel):
    phone_number: str
    patient_name: str
    utterance: str

@app.post("/pipeline/stage-2/patient-engagement")
def patient_engagement(payload: Stage2EngagementInput, db: Session = Depends(get_db)):
    pipeline = HorizontalPlatformPipeline(db)
    return pipeline.execute_stage_2_patient_engagement(
        phone_number=payload.phone_number,
        patient_name=payload.patient_name,
        utterance=payload.utterance
    )


class Stage3SchedulingInput(BaseModel):
    session_id: str
    patient_id: str
    hospital_id: str
    doctor_id: str
    start_datetime: datetime
    patient_name: str
    patient_phone: str

@app.post("/pipeline/stage-3/schedule-and-verify")
def schedule_and_verify(payload: Stage3SchedulingInput, db: Session = Depends(get_db)):
    pipeline = HorizontalPlatformPipeline(db)
    return pipeline.execute_stage_3_scheduling_and_ehr_verification(
        session_id=payload.session_id,
        patient_id=payload.patient_id,
        hospital_id=payload.hospital_id,
        doctor_id=payload.doctor_id,
        start_datetime=payload.start_datetime,
        patient_name=payload.patient_name,
        patient_phone=payload.patient_phone
    )


class Stage4PreVisitInput(BaseModel):
    appointment_id: str
    patient_reported_symptoms: str

@app.post("/pipeline/stage-4/pre-visit-intake")
def pre_visit_intake(payload: Stage4PreVisitInput, db: Session = Depends(get_db)):
    pipeline = HorizontalPlatformPipeline(db)
    return pipeline.execute_stage_4_pre_visit_and_doctor_review(
        appointment_id=payload.appointment_id,
        patient_reported_symptoms=payload.patient_reported_symptoms
    )


@app.post("/pipeline/stage-5/async-lifecycle/{appointment_id}")
def async_lifecycle(appointment_id: str, db: Session = Depends(get_db)):
    pipeline = HorizontalPlatformPipeline(db)
    return pipeline.execute_stage_5_async_lifecycle(appointment_id=appointment_id)


@app.get("/telemetry/health-report")
def get_health_report(db: Session = Depends(get_db)):
    pipeline = HorizontalPlatformPipeline(db)
    return pipeline.telemetry.get_system_health_report()


# =========================================================================
# SECTION 5.8: PATIENT REGISTRATION & PROFILE ENDPOINTS
# =========================================================================

class RegisterPatientInput(BaseModel):
    name: str
    phone_number: str
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    preferred_language: str = "en"
    emergency_contact: Optional[Dict[str, Any]] = None
    external_patient_id: Optional[str] = None
    saved_preferences: Optional[Dict[str, Any]] = None

class UpdatePatientProfileInput(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact: Optional[Dict[str, Any]] = None
    external_patient_id: Optional[str] = None
    saved_preferences: Optional[Dict[str, Any]] = None

class PatientRescheduleInput(BaseModel):
    new_start_datetime: datetime
    reason: Optional[str] = None

class PatientCancelInput(BaseModel):
    reason: Optional[str] = None

class SubmitQuestionnaireInput(BaseModel):
    questionnaire_id: str
    appointment_id: Optional[str] = None
    responses: Dict[str, Any]

@app.post("/api/v1/patients/register")
def register_patient(payload: RegisterPatientInput, db: Session = Depends(get_db)):
    service = PatientSelfServiceService(db)
    try:
        patient = service.register_patient(
            name=payload.name, phone_number=payload.phone_number, email=payload.email,
            date_of_birth=payload.date_of_birth, preferred_language=payload.preferred_language,
            emergency_contact=payload.emergency_contact, external_patient_id=payload.external_patient_id,
            saved_preferences=payload.saved_preferences
        )
        return {"patient_id": patient.id, "name": patient.name, "phone_number": patient.phone_number, "external_patient_id": patient.external_patient_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/patients/{patient_id}")
def get_patient_profile(patient_id: str, db: Session = Depends(get_db)):
    service = PatientSelfServiceService(db)
    try:
        return service.get_patient_profile(patient_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/api/v1/patients/{patient_id}")
def update_patient_profile(patient_id: str, payload: UpdatePatientProfileInput, db: Session = Depends(get_db)):
    service = PatientSelfServiceService(db)
    try:
        patient = service.update_patient_profile(
            patient_id=patient_id, name=payload.name, email=payload.email,
            date_of_birth=payload.date_of_birth, preferred_language=payload.preferred_language,
            emergency_contact=payload.emergency_contact, external_patient_id=payload.external_patient_id,
            saved_preferences=payload.saved_preferences
        )
        return {"patient_id": patient.id, "updated": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/patients/{patient_id}/appointments")
def list_patient_appointments(patient_id: str, db: Session = Depends(get_db)):
    service = PatientSelfServiceService(db)
    try:
        return service.list_patient_appointments(patient_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/v1/patients/{patient_id}/appointments/{appointment_id}/cancel")
def patient_cancel_appointment(patient_id: str, appointment_id: str, payload: PatientCancelInput, db: Session = Depends(get_db)):
    service = PatientSelfServiceService(db)
    try:
        appt = service.cancel_appointment_self_service(patient_id=patient_id, appointment_id=appointment_id, reason=payload.reason)
        return {"appointment_id": appt.id, "status": appt.status.value, "cancelled_by": "PATIENT"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/patients/{patient_id}/appointments/{appointment_id}/reschedule-request")
def patient_reschedule_appointment(patient_id: str, appointment_id: str, payload: PatientRescheduleInput, db: Session = Depends(get_db)):
    service = PatientSelfServiceService(db)
    try:
        appt = service.request_reschedule_self_service(patient_id=patient_id, appointment_id=appointment_id, new_start_datetime=payload.new_start_datetime, reason=payload.reason)
        return {"appointment_id": appt.id, "status": appt.status.value, "new_start_datetime": appt.start_datetime.isoformat()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/patients/{patient_id}/questionnaires/submit")
def submit_questionnaire_response(patient_id: str, payload: SubmitQuestionnaireInput, db: Session = Depends(get_db)):
    service = PatientSelfServiceService(db)
    try:
        resp = service.submit_questionnaire_response(
            patient_id=patient_id, questionnaire_id=payload.questionnaire_id,
            responses=payload.responses, appointment_id=payload.appointment_id
        )
        return {"response_id": resp.id, "patient_id": patient_id, "submitted": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/patients/{patient_id}/questionnaires/responses")
def get_patient_questionnaire_responses(patient_id: str, db: Session = Depends(get_db)):
    service = PatientSelfServiceService(db)
    try:
        return service.get_patient_questionnaire_responses(patient_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =========================================================================
# SECTION 5.9: AI PATIENT ACCESS AGENT ENDPOINTS
# =========================================================================

class ProcessAgentTurnInput(BaseModel):
    channel: str = "web_voice"
    patient_identifier: str
    user_utterance: str
    session_id: Optional[str] = None
    context_override: Optional[Dict[str, Any]] = None
    hospital_id: Optional[str] = None
    doctor_id: Optional[str] = None

@app.post("/api/v1/ai-agent/turn")
def process_ai_agent_turn(payload: ProcessAgentTurnInput, db: Session = Depends(get_db)):
    agent = AIPatientAccessAgent(db)
    try:
        res = agent.process_patient_turn(
            channel=payload.channel,
            patient_identifier=payload.patient_identifier,
            user_utterance=payload.user_utterance,
            session_id=payload.session_id,
            context_override=payload.context_override,
            hospital_id=payload.hospital_id,
            doctor_id=payload.doctor_id
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

