"""
Unit tests for Step 3: Product Vision & Executive Summary Engine.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, Doctor, Appointment, AppointmentStatus, PatientIntakeRecord
from app.vision.executive_summary import ProductVisionEngine, VALUE_PILLARS


def test_executive_vision_and_pillars_evaluation():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    vision = ProductVisionEngine(db)
    res = vision.evaluate_ai_quality_metrics()

    assert res["executive_vision"] == "Unified Multi-Hospital Access & Operational Layer"
    assert res["value_pillars_count"] == 13
    assert len(res["value_pillars"]) == 13
    assert "Reduce healthcare access friction" in res["value_pillars"]
    assert "Improve doctor preparation" in res["value_pillars"]
    assert res["quality_metrics"]["ehr_authoritative_reliability_rate_pct"] == 100.0


def test_doctor_preparation_briefing_generation():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    hosp = Hospital(id="h-v1", name="General Hospital", code="GH")
    doc = Doctor(id="d-v1", hospital_id="h-v1", name="Dr. Stephen Strange", specialty="Surgeon", special_instructions="Review patient hand mobility notes.")
    appt = Appointment(
        id="a-v1",
        hospital_id="h-v1",
        doctor_id="d-v1",
        patient_name="Tony Stark",
        patient_phone="+1-555-3000",
        start_datetime=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1),
        end_datetime=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1, hours=1),
        status=AppointmentStatus.SCHEDULED,
        external_appointment_id="EXT-EHR-9988",
        is_ehr_verified=True
    )
    intake = PatientIntakeRecord(
        appointment_id="a-v1",
        patient_reported_summary="Experiencing joint discomfort in left wrist after tremor episode.",
        is_patient_reported_only=True
    )
    db.add_all([hosp, doc, appt, intake])
    db.commit()

    vision = ProductVisionEngine(db)
    briefing = vision.generate_doctor_preparation_briefing("a-v1")

    assert briefing["patient_name"] == "Tony Stark"
    assert briefing["doctor_name"] == "Dr. Stephen Strange"
    assert briefing["is_ehr_verified"] is True
    assert briefing["pre_visit_intake"]["has_completed_intake"] is True
    assert briefing["pre_visit_intake"]["data_category"] == "PATIENT_REPORTED_INFORMATION_ONLY"
    assert briefing["pre_visit_intake"]["is_clinical_diagnosis"] is False
    assert "joint discomfort" in briefing["pre_visit_intake"]["patient_reported_summary"]
