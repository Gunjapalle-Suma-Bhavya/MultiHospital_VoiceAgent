"""
Unit tests for Step 2: Complete Horizontal Platform Flow Pipeline (Stages 1 through 5).
"""

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base
from app.pipeline.orchestrator import HorizontalPlatformPipeline


def test_full_horizontal_pipeline_execution():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    pipeline = HorizontalPlatformPipeline(db)

    # -------------------------------------------------------------------------
    # STAGE 1: HOSPITAL ONBOARDING
    # -------------------------------------------------------------------------
    stg1 = pipeline.execute_stage_1_hospital_onboarding(
        hospital_name="St. Mary Medical Center",
        hospital_code="SMMC",
        doctor_name="Dr. Gregory House",
        specialty="Diagnostics"
    )
    assert stg1["stage"] == "STAGE_1_COMPLETED"
    hospital_id = stg1["hospital_id"]
    doctor_id = stg1["doctor_id"]

    # -------------------------------------------------------------------------
    # STAGE 2: PATIENT ENGAGEMENT
    # -------------------------------------------------------------------------
    stg2 = pipeline.execute_stage_2_patient_engagement(
        phone_number="+1-555-8822",
        patient_name="James Wilson",
        utterance="Find me a diagnostic specialist"
    )
    assert stg2["stage"] == "STAGE_2_COMPLETED"
    patient_id = stg2["patient_id"]
    session_id = stg2["session_id"]
    assert len(stg2["matched_doctors"]) == 1

    # -------------------------------------------------------------------------
    # STAGE 3: SELECTION, SCHEDULING & EHR VERIFICATION
    # -------------------------------------------------------------------------
    appt_time = datetime.utcnow() + timedelta(days=3)
    stg3 = pipeline.execute_stage_3_scheduling_and_ehr_verification(
        session_id=session_id,
        patient_id=patient_id,
        hospital_id=hospital_id,
        doctor_id=doctor_id,
        start_datetime=appt_time,
        patient_name="James Wilson",
        patient_phone="+1-555-8822"
    )
    assert stg3["stage"] == "STAGE_3_COMPLETED"
    assert stg3["ehr_verified"] is True
    appointment_id = stg3["appointment_id"]

    # -------------------------------------------------------------------------
    # STAGE 4: CONFIRMATION, PRE-VISIT & DOCTOR INTAKE REVIEW
    # -------------------------------------------------------------------------
    stg4 = pipeline.execute_stage_4_pre_visit_and_doctor_review(
        appointment_id=appointment_id,
        patient_reported_symptoms="Unexplained leg pain and fatigue for past 3 days."
    )
    assert stg4["stage"] == "STAGE_4_COMPLETED"
    assert stg4["doctor_review_ready"] is True

    # -------------------------------------------------------------------------
    # STAGE 5: OPERATIONAL EVENT & ASYNC LIFECYCLE
    # -------------------------------------------------------------------------
    stg5 = pipeline.execute_stage_5_async_lifecycle(appointment_id=appointment_id)
    assert stg5["stage"] == "STAGE_5_COMPLETED"
    assert stg5["continuous_monitoring_report"]["total_ai_invocations"] > 0
