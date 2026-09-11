"""
Main FastAPI Application Entrypoint.

Clean, modular application configuration mounting sub-routers:
- onboarding_router & admin_router
- doctors_router
- patients_router
- discovery_router
- voice_router
- context_router
- ehr_router
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.database.config import init_db
from app.routers import (
    onboarding_router, admin_router, doctors_router, patients_router,
    discovery_router, voice_router, context_router, ehr_router,
    questionnaires_router, workflows_router, events_router, notifications_router,
    doctor_dashboard_router, hospital_dashboard_router, platform_admin_dashboard_router,
    observability_router, ai_analytics_router, feedback_router, escalation_router,
    audit_router, rbac_router, data_model_router, patient_workflow_router,
    hospital_workflow_router, architecture_router, dashboard_pages_router,
    dashboard_analytics_router, operational_monitoring_router
)

app = FastAPI(
    title="Multi-Hospital Autonomous Voice Agent Platform",
    description="Enterprise Multi-Hospital Patient Intake, Doctor Discovery & EHR Integration Platform",
    version="1.0.0"
)

# Initialize Database Schema
init_db()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Sub-Routers
app.include_router(onboarding_router)
app.include_router(admin_router)
app.include_router(doctors_router)
app.include_router(patients_router)
app.include_router(discovery_router)
app.include_router(voice_router)
app.include_router(context_router)
app.include_router(ehr_router)
app.include_router(questionnaires_router)
app.include_router(workflows_router)
app.include_router(events_router)
app.include_router(notifications_router)
app.include_router(doctor_dashboard_router)
app.include_router(hospital_dashboard_router)
app.include_router(platform_admin_dashboard_router)
app.include_router(observability_router)
app.include_router(ai_analytics_router)
app.include_router(feedback_router)
app.include_router(escalation_router, prefix="/api/v1/escalation")
app.include_router(audit_router)
app.include_router(rbac_router)
app.include_router(data_model_router)
app.include_router(patient_workflow_router)
app.include_router(hospital_workflow_router)
app.include_router(architecture_router, prefix="/api/v1")
app.include_router(dashboard_pages_router, prefix="/api/v1")
app.include_router(dashboard_analytics_router, prefix="/api/v1")
app.include_router(operational_monitoring_router)






# Mount Static Assets & Web Frontend UI
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "status": "online",
        "service": "Autonomous Multi-Hospital Patient Intake Platform API",
        "docs_url": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
