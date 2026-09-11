"""
Routers package initialization.
"""

from app.routers.onboarding import router as onboarding_router, admin_router
from app.routers.doctors import router as doctors_router
from app.routers.patients import router as patients_router
from app.routers.discovery import router as discovery_router
from app.routers.voice import router as voice_router
from app.routers.context import router as context_router
from app.routers.ehr import router as ehr_router
from app.routers.questionnaires import router as questionnaires_router
from app.routers.workflows import router as workflows_router
from app.routers.events import router as events_router
from app.routers.notifications import router as notifications_router
from app.routers.doctor_dashboard import router as doctor_dashboard_router
from app.routers.hospital_dashboard import router as hospital_dashboard_router
from app.routers.platform_admin_dashboard import router as platform_admin_dashboard_router
from app.routers.observability import router as observability_router
from app.routers.ai_analytics import router as ai_analytics_router
from app.routers.feedback import router as feedback_router
from app.routers.escalation import router as escalation_router
from app.routers.audit import router as audit_router
from app.routers.rbac import router as rbac_router
from app.routers.data_model import router as data_model_router
from app.routers.patient_workflow import router as patient_workflow_router
from app.routers.hospital_workflow import router as hospital_workflow_router
from app.routers.platform_architecture import router as architecture_router
from app.routers.dashboard_pages import router as dashboard_pages_router

__all__ = [
    "onboarding_router",
    "admin_router",
    "doctors_router",
    "patients_router",
    "discovery_router",
    "voice_router",
    "context_router",
    "ehr_router",
    "questionnaires_router",
    "workflows_router",
    "events_router",
    "notifications_router",
    "doctor_dashboard_router",
    "hospital_dashboard_router",
    "platform_admin_dashboard_router",
    "observability_router",
    "ai_analytics_router",
    "feedback_router",
    "escalation_router",
    "audit_router",
    "rbac_router",
    "data_model_router",
    "patient_workflow_router",
    "hospital_workflow_router",
    "architecture_router",
    "dashboard_pages_router",
]




