"""
Test Suite for Step 12: Dashboard Analytics.
Validates the complete 3-tier analytics breakdown across all 42 metrics:
1. Platform-Level Analytics (21 metrics)
2. Hospital-Level Analytics (14 metrics)
3. Doctor-Level Analytics (7 metrics)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.config import init_db, SessionLocal
from app.analytics.dashboard_analytics_service import (
    DashboardAnalyticsService,
    PlatformAnalyticsResponse,
    HospitalAnalyticsResponse,
    DoctorAnalyticsResponse,
    AnalyticsSummaryResponse
)


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    init_db()
    session = SessionLocal()
    yield session
    session.close()


def test_platform_analytics_21_metrics(db_session):
    """Validates that PlatformAnalyticsResponse produces all 21 canonical metrics."""
    res = DashboardAnalyticsService.get_platform_analytics(db=db_session)
    assert isinstance(res, PlatformAnalyticsResponse)

    # 1. Total hospitals
    assert isinstance(res.total_hospitals, int) and res.total_hospitals >= 0
    # 2. Active hospitals
    assert isinstance(res.active_hospitals, int) and res.active_hospitals >= 0
    # 3. Pending hospitals
    assert isinstance(res.pending_hospitals, int) and res.pending_hospitals >= 0
    # 4. Total doctors
    assert isinstance(res.total_doctors, int) and res.total_doctors >= 0
    # 5. Total patients
    assert isinstance(res.total_patients, int) and res.total_patients >= 0
    # 6. Total appointments
    assert isinstance(res.total_appointments, int) and res.total_appointments >= 0
    # 7. Appointments by hospital
    assert isinstance(res.appointments_by_hospital, dict)
    # 8. Appointment success rate
    assert 0.0 <= res.appointment_success_rate <= 100.0
    # 9. AI call volume
    assert isinstance(res.ai_call_volume, int) and res.ai_call_volume >= 0
    # 10. AI booking rate
    assert 0.0 <= res.ai_booking_rate <= 100.0
    # 11. Human escalation rate
    assert 0.0 <= res.human_escalation_rate <= 100.0
    # 12. Questionnaire completion
    assert 0.0 <= res.questionnaire_completion <= 100.0
    # 13. Average AI latency
    assert res.average_ai_latency >= 0.0
    # 14. EHR integration success rate
    assert 0.0 <= res.ehr_integration_success_rate <= 100.0
    # 15. EHR integration failure rate
    assert 0.0 <= res.ehr_integration_failure_rate <= 100.0
    # 16. EHR verification success
    assert 0.0 <= res.ehr_verification_success <= 100.0
    # 17. Reconciliation rate
    assert 0.0 <= res.reconciliation_rate <= 100.0
    # 18. Workflow success rate
    assert 0.0 <= res.workflow_success_rate <= 100.0
    # 19. Workflow failure rate
    assert 0.0 <= res.workflow_failure_rate <= 100.0
    # 20. Notification delivery rate
    assert 0.0 <= res.notification_delivery_rate <= 100.0
    # 21. AI evaluation score
    assert 0.0 <= res.ai_evaluation_score <= 5.0


def test_hospital_analytics_14_metrics(db_session):
    """Validates that HospitalAnalyticsResponse produces all 14 canonical metrics."""
    res = DashboardAnalyticsService.get_hospital_analytics("STJUDE", db=db_session)
    assert isinstance(res, HospitalAnalyticsResponse)

    assert res.hospital_id == "STJUDE"
    assert len(res.hospital_name) > 0

    # 1. Appointments
    assert isinstance(res.appointments, int) and res.appointments >= 0
    # 2. Doctor utilization
    assert 0.0 <= res.doctor_utilization <= 100.0
    # 3. Available vs booked slots
    assert "available_slots" in res.available_vs_booked_slots
    assert "booked_slots" in res.available_vs_booked_slots
    # 4. Cancellation rate
    assert 0.0 <= res.cancellation_rate <= 100.0
    # 5. Rescheduling rate
    assert 0.0 <= res.rescheduling_rate <= 100.0
    # 6. AI booking percentage
    assert 0.0 <= res.ai_booking_percentage <= 100.0
    # 7. Questionnaire completion
    assert 0.0 <= res.questionnaire_completion <= 100.0
    # 8. Patient volume
    assert isinstance(res.patient_volume, int) and res.patient_volume >= 0
    # 9. Workflow activity
    assert isinstance(res.workflow_activity, int) and res.workflow_activity >= 0
    # 10. Notification activity
    assert isinstance(res.notification_activity, int) and res.notification_activity >= 0
    # 11. EHR integration activity
    assert isinstance(res.ehr_integration_activity, int) and res.ehr_integration_activity >= 0
    # 12. Integration success rate
    assert 0.0 <= res.integration_success_rate <= 100.0
    # 13. Integration failure rate
    assert 0.0 <= res.integration_failure_rate <= 100.0
    # 14. Reconciliation activity
    assert isinstance(res.reconciliation_activity, int) and res.reconciliation_activity >= 0


def test_doctor_analytics_7_metrics(db_session):
    """Validates that DoctorAnalyticsResponse produces all 7 canonical metrics."""
    res = DashboardAnalyticsService.get_doctor_analytics("DOC-101", db=db_session)
    assert isinstance(res, DoctorAnalyticsResponse)

    assert res.doctor_id == "DOC-101"
    assert len(res.doctor_name) > 0
    assert len(res.specialty) > 0

    # 1. Appointments
    assert isinstance(res.appointments, int) and res.appointments >= 0
    # 2. Available slots
    assert isinstance(res.available_slots, int) and res.available_slots >= 0
    # 3. Utilization
    assert 0.0 <= res.utilization <= 100.0
    # 4. Cancellations
    assert isinstance(res.cancellations, int) and res.cancellations >= 0
    # 5. Rescheduling
    assert isinstance(res.rescheduling, int) and res.rescheduling >= 0
    # 6. Questionnaire completion
    assert 0.0 <= res.questionnaire_completion <= 100.0
    # 7. Upcoming workload
    assert isinstance(res.upcoming_workload, int) and res.upcoming_workload >= 0


def test_dashboard_analytics_api_endpoints(client):
    """Validates FastAPI REST endpoints for all 3 analytics tiers and the combined summary."""
    # 1. Platform Analytics Endpoint (21 metrics)
    p_res = client.get("/api/v1/analytics/dashboard/platform")
    assert p_res.status_code == 200
    p_data = p_res.json()
    assert "total_hospitals" in p_data
    assert "ai_evaluation_score" in p_data
    assert "ehr_verification_success" in p_data
    assert len(p_data) >= 21

    # 2. Hospital Analytics Endpoint (14 metrics)
    h_res = client.get("/api/v1/analytics/dashboard/hospital/STJUDE")
    assert h_res.status_code == 200
    h_data = h_res.json()
    assert h_data["hospital_id"] == "STJUDE"
    assert "doctor_utilization" in h_data
    assert "available_vs_booked_slots" in h_data
    assert "reconciliation_activity" in h_data
    assert len(h_data) >= 14

    # 3. Doctor Analytics Endpoint (7 metrics)
    d_res = client.get("/api/v1/analytics/dashboard/doctor/DOC-101")
    assert d_res.status_code == 200
    d_data = d_res.json()
    assert d_data["doctor_id"] == "DOC-101"
    assert "utilization" in d_data
    assert "available_slots" in d_data
    assert "upcoming_workload" in d_data
    assert len(d_data) >= 7

    # 4. Multi-tier Summary Endpoint
    s_res = client.get("/api/v1/analytics/dashboard/summary")
    assert s_res.status_code == 200
    s_data = s_res.json()
    assert "platform" in s_data
    assert len(s_data["hospitals"]) >= 1
    assert len(s_data["doctors"]) >= 1
