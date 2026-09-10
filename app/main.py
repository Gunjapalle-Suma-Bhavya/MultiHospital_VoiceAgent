"""
FastAPI Main Entrypoint for Multi-Hospital Patient Intake, Scheduling & Pre-Visit Voice Agent.

Exposes end-to-end REST endpoints for:
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

from app.database.models import Base, EHRAdapterType
from app.pipeline.orchestrator import HorizontalPlatformPipeline
from app.vision.executive_summary import ProductVisionEngine
from app.agent.coordinator import ProductVision16StepCoordinator
from app.agent.native_workflow import AINativeWorkflowEngine
from app.journeys.hospital_journey import HospitalJourneyEngine
from app.journeys.doctor_journey import DoctorJourneyEngine
from app.journeys.patient_journey import PatientJourneyEngine
from app.journeys.admin_journey import PlatformAdminJourneyEngine

app = FastAPI(
    title="Autonomous Multi-Hospital Voice Agent Network API",
    version="9.0.0",
    description="Enterprise Multi-Hospital Voice Agent Platform, Hospital, Doctor, Patient & Admin Journey Engines"
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
        "step": "Section 4.4: Platform Admin Journey Ecosystem Active"
    }


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
