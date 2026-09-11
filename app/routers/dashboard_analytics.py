"""
Dashboard Analytics REST API Router (Step 12).
Exposes endpoints for:
- Platform-Level Analytics (21 metrics)
- Hospital-Level Analytics (14 metrics)
- Doctor-Level Analytics (7 metrics)
- Multi-tier Analytics Summary
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.analytics.dashboard_analytics_service import (
    DashboardAnalyticsService,
    PlatformAnalyticsResponse,
    HospitalAnalyticsResponse,
    DoctorAnalyticsResponse,
    AnalyticsSummaryResponse
)

router = APIRouter(prefix="/analytics/dashboard", tags=["Dashboard Analytics (Step 12)"])


@router.get("/platform", response_model=PlatformAnalyticsResponse)
def get_platform_level_analytics(db: Session = Depends(get_db)):
    """
    Returns all 21 Platform-Level Analytics metrics:
    total_hospitals, active_hospitals, pending_hospitals, total_doctors, total_patients,
    total_appointments, appointments_by_hospital, appointment_success_rate, ai_call_volume,
    ai_booking_rate, human_escalation_rate, questionnaire_completion, average_ai_latency,
    ehr_integration_success_rate, ehr_integration_failure_rate, ehr_verification_success,
    reconciliation_rate, workflow_success_rate, workflow_failure_rate,
    notification_delivery_rate, ai_evaluation_score.
    """
    return DashboardAnalyticsService.get_platform_analytics(db=db)


@router.get("/hospital/{hospital_id}", response_model=HospitalAnalyticsResponse)
def get_hospital_level_analytics(hospital_id: str, db: Session = Depends(get_db)):
    """
    Returns all 14 Hospital-Level Analytics metrics for the specified facility:
    appointments, doctor_utilization, available_vs_booked_slots, cancellation_rate,
    rescheduling_rate, ai_booking_percentage, questionnaire_completion, patient_volume,
    workflow_activity, notification_activity, ehr_integration_activity,
    integration_success_rate, integration_failure_rate, reconciliation_activity.
    """
    return DashboardAnalyticsService.get_hospital_analytics(hospital_id=hospital_id, db=db)


@router.get("/doctor/{doctor_id}", response_model=DoctorAnalyticsResponse)
def get_doctor_level_analytics(doctor_id: str, db: Session = Depends(get_db)):
    """
    Returns all 7 Doctor-Level Analytics metrics for the specified physician:
    appointments, available_slots, utilization, cancellations, rescheduling,
    questionnaire_completion, upcoming_workload.
    """
    return DashboardAnalyticsService.get_doctor_analytics(doctor_id=doctor_id, db=db)


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(db: Session = Depends(get_db)):
    """
    Returns combined summary across Platform, sample hospitals, and sample doctors.
    """
    return DashboardAnalyticsService.get_summary(db=db)
