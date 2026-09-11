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
    "workflows_router"
]
