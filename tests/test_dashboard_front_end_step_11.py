"""
Test Suite for Step 11: Platform Dashboard — Front-End Feature Breakdown.
Validates the complete 4-role, 49-page frontend catalog and data retrieval:
- 11.1 Platform Admin Dashboard (16 pages)
- 11.2 Hospital Dashboard (15 pages)
- 11.3 Doctor Dashboard (9 pages)
- 11.4 Patient Dashboard (9 pages)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.config import init_db, SessionLocal
from app.dashboard.dashboard_pages_service import (
    DashboardPagesService,
    PLATFORM_ADMIN_PAGES,
    HOSPITAL_DASHBOARD_PAGES,
    DOCTOR_DASHBOARD_PAGES,
    PATIENT_DASHBOARD_PAGES,
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


def test_dashboard_catalog_structure():
    """Validates the exact 4-role breakdown and 49 canonical pages matching the prompt specifications."""
    catalog = DashboardPagesService.get_catalog()

    assert catalog["total_roles"] == 4
    assert catalog["total_pages"] == 49
    assert catalog["breakdown"]["platform_admin_pages"] == 16
    assert catalog["breakdown"]["hospital_dashboard_pages"] == 15
    assert catalog["breakdown"]["doctor_dashboard_pages"] == 9
    assert catalog["breakdown"]["patient_dashboard_pages"] == 9

    roles_dict = {r["role_id"]: r for r in catalog["roles"]}
    assert "platform_admin" in roles_dict
    assert "hospital_admin" in roles_dict
    assert "doctor" in roles_dict
    assert "patient" in roles_dict

    # 11.1 Platform Admin: 16 Pages
    pa_pages = [p["page_id"] for p in roles_dict["platform_admin"]["pages"]]
    assert len(pa_pages) == 16
    expected_pa = [
        "overview", "hospital_applications", "hospitals", "doctors", "patients",
        "appointments", "ai_activity", "ehr_activity", "workflows", "notifications",
        "analytics", "ai_evaluation", "operational_health", "audit_logs",
        "users_access", "settings"
    ]
    assert pa_pages == expected_pa

    # 11.2 Hospital Dashboard: 15 Pages
    hosp_pages = [p["page_id"] for p in roles_dict["hospital_admin"]["pages"]]
    assert len(hosp_pages) == 15
    expected_hosp = [
        "overview", "appointments", "doctors", "calendars", "availability",
        "questionnaires", "patients", "ai_activity", "ehr_activity", "workflows",
        "notifications", "analytics", "hospital_settings", "ehr_integrations",
        "staff_access"
    ]
    assert hosp_pages == expected_hosp

    # 11.3 Doctor Dashboard: 9 Pages
    doc_pages = [p["page_id"] for p in roles_dict["doctor"]["pages"]]
    assert len(doc_pages) == 9
    expected_doc = [
        "overview", "my_calendar", "appointments", "availability", "blocked_time",
        "questionnaires", "patient_responses", "profile", "settings"
    ]
    assert doc_pages == expected_doc

    # 11.4 Patient Dashboard: 9 Pages
    pat_pages = [p["page_id"] for p in roles_dict["patient"]["pages"]]
    assert len(pat_pages) == 9
    expected_pat = [
        "home", "ai_assistant", "my_appointments", "upcoming_appointment",
        "questionnaire", "appointment_history", "preferences", "profile", "settings"
    ]
    assert pat_pages == expected_pat


def test_platform_admin_pages_data(db_session):
    """Verifies that Platform Admin pages return structured live data."""
    # 1. Overview
    d_overview = DashboardPagesService.get_page_data("platform_admin", "overview", db=db_session)
    assert d_overview.role_id == "platform_admin"
    assert d_overview.page_id == "overview"
    assert len(d_overview.kpis) >= 4
    assert len(d_overview.records) > 0

    # 2. Hospital Applications
    d_apps = DashboardPagesService.get_page_data("platform_admin", "hospital_applications", db=db_session)
    assert d_apps.page_title == "Hospital Applications"
    assert "approve" in d_apps.available_actions

    # 3. AI Activity
    d_ai = DashboardPagesService.get_page_data("platform_admin", "ai_activity", db=db_session)
    assert len(d_ai.records) >= 1

    # 4. Audit Logs
    d_audit = DashboardPagesService.get_page_data("platform_admin", "audit_logs", db=db_session)
    assert len(d_audit.table_headers) > 0


def test_hospital_dashboard_pages_data(db_session):
    """Verifies that Hospital Dashboard pages return structured live data."""
    # 1. Overview
    d_overview = DashboardPagesService.get_page_data("hospital_admin", "overview", hospital_id="STJUDE", db=db_session)
    assert d_overview.role_id == "hospital_admin"
    assert len(d_overview.kpis) >= 3

    # 2. Appointments
    d_appts = DashboardPagesService.get_page_data("hospital_admin", "appointments", hospital_id="STJUDE", db=db_session)
    assert "Appt ID" in d_appts.table_headers
    assert len(d_appts.records) > 0

    # 3. Availability
    d_avail = DashboardPagesService.get_page_data("hospital_admin", "availability", hospital_id="STJUDE", db=db_session)
    assert len(d_avail.records) == 5  # Mon - Fri

    # 4. Staff & Access
    d_staff = DashboardPagesService.get_page_data("hospital_admin", "staff_access", hospital_id="STJUDE", db=db_session)
    assert "Role" in d_staff.table_headers


def test_doctor_dashboard_pages_data(db_session):
    """Verifies that Doctor Dashboard pages return structured live data."""
    # 1. Overview
    d_overview = DashboardPagesService.get_page_data("doctor", "overview", doctor_id="DOC-101", db=db_session)
    assert d_overview.role_id == "doctor"
    assert len(d_overview.kpis) >= 2

    # 2. My Calendar
    d_cal = DashboardPagesService.get_page_data("doctor", "my_calendar", doctor_id="DOC-101", db=db_session)
    assert "Slot Time" in d_cal.table_headers

    # 3. Patient Pre-Visit Responses
    d_resp = DashboardPagesService.get_page_data("doctor", "patient_responses", doctor_id="DOC-101", db=db_session)
    assert len(d_resp.records) > 0
    assert "Primary Complaint" in d_resp.table_headers


def test_patient_dashboard_pages_data(db_session):
    """Verifies that Patient Dashboard pages return structured live data."""
    # 1. Home
    d_home = DashboardPagesService.get_page_data("patient", "home", patient_id="PAT-501", db=db_session)
    assert d_home.role_id == "patient"
    assert len(d_home.kpis) >= 1

    # 2. Upcoming Appointment
    d_up = DashboardPagesService.get_page_data("patient", "upcoming_appointment", patient_id="PAT-501", db=db_session)
    assert "doctor" in d_up.details
    assert "facility_address" in d_up.details

    # 3. Questionnaire
    d_quest = DashboardPagesService.get_page_data("patient", "questionnaire", patient_id="PAT-501", db=db_session)
    assert "submitted_answers" in d_quest.details


def test_dashboard_pages_api_endpoints(client):
    """Validates FastAPI REST endpoints for the 49 dashboard pages."""
    # 1. GET /catalog
    cat_res = client.get("/api/v1/dashboard-pages/catalog")
    assert cat_res.status_code == 200
    cat_data = cat_res.json()
    assert cat_data["total_pages"] == 49
    assert len(cat_data["roles"]) == 4

    # 2. GET /data/platform_admin/overview
    p_res = client.get("/api/v1/dashboard-pages/data/platform_admin/overview")
    assert p_res.status_code == 200
    p_data = p_res.json()
    assert p_data["page_title"] == "Overview"
    assert len(p_data["kpis"]) > 0

    # 3. GET /data/doctor/my_calendar
    doc_res = client.get("/api/v1/dashboard-pages/data/doctor/my_calendar?doctor_id=DOC-101")
    assert doc_res.status_code == 200
    doc_data = doc_res.json()
    assert doc_data["role_id"] == "doctor"

    # 4. POST /action
    act_res = client.post(
        "/api/v1/dashboard-pages/action/platform_admin/hospital_applications",
        json={"action_name": "approve_application", "action_payload": {"application_id": "APP-901"}}
    )
    assert act_res.status_code == 200
    assert act_res.json()["status"] == "SUCCESS"
