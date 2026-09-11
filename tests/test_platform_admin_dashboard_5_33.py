"""
Unit Test Suite for Section 5.33 Platform Admin Dashboard.

Tests:
1. Global Platform KPIs (Hospitals, Doctors, Patients, Appointments Today, AI Calls Today, Booking Success %, Questionnaire Complete %, Human Escalation %, Avg AI Latency, EHR Success %).
2. Authorized 12-Domain Platform Explorer.
"""

import pytest
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import (
    Base, Hospital, Doctor, PatientProfile, Appointment, AppointmentStatus,
    AITelemetryLog, EHRSyncLog, WorkflowInstance, PlatformEventRecord, AuditLog
)
from app.dashboard.platform_admin_dashboard import PlatformAdminDashboardService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_global_platform_admin_kpis(db_session):
    # Seed data
    hosp = Hospital(name="City Hospital", code="CITY")
    db_session.add(hosp)
    db_session.commit()

    doc = Doctor(hospital_id=hosp.id, name="Dr. Rao", specialty="Cardiology")
    db_session.add(doc)
    db_session.commit()

    pat = PatientProfile(phone_number="+15558889999", full_name="Alice Smith")
    db_session.add(pat)
    db_session.commit()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    appt = Appointment(hospital_id=hosp.id, doctor_id=doc.id, patient_name="Alice Smith", patient_phone="+15558889999", start_datetime=now, end_datetime=now + timedelta(minutes=30), status=AppointmentStatus.CONFIRMED)
    db_session.add(appt)
    db_session.commit()




    telemetry = AITelemetryLog(session_id="SESS-GLOBAL", ai_attempt_summary="Book session", latency_ms=1200.0)
    db_session.add(telemetry)

    ehr = EHRSyncLog(appointment_id=appt.id, hospital_id=hosp.id, action_type="SYNC", sync_status="VERIFIED")
    db_session.add(ehr)

    db_session.commit()

    service = PlatformAdminDashboardService(db_session)
    res = service.get_global_kpis()

    assert "global_kpis" in res
    kpis = res["global_kpis"]

    assert kpis["hospitals"] >= 1
    assert kpis["doctors"] >= 1
    assert kpis["patients"] >= 1
    assert kpis["appointments_today"] >= 1
    assert kpis["ai_calls_today"] >= 1
    assert kpis["booking_success_percentage"] > 0
    assert kpis["avg_ai_latency_seconds"] > 0
    assert kpis["ehr_integration_success_percentage"] > 0


def test_authorized_12_domain_platform_explorer(db_session):
    service = PlatformAdminDashboardService(db_session)

    domains = [
        "hospitals", "doctors", "patients", "appointments", "ai_interactions",
        "workflows", "system_failures", "ehr_operations", "external_events",
        "audit_events", "analytics", "ai_evaluations"
    ]

    for domain in domains:
        res = service.get_explorer_data(category=domain, limit=10)
        assert res["category"] == domain
        assert "records" in res
