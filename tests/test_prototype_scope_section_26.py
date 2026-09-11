"""
Test Suite for Section 26: Prototype Scope & Full End-to-End Verification.

Validates:
1. Complete 9-domain prototype scope specification metadata
2. Real-time verification across all 9 Must-Have domains:
   - Platform
   - Doctor
   - Patient
   - AI
   - EHR / Healthcare-System Integration
   - Questionnaire
   - Workflow
   - Analytics
   - AI Operations
3. REST API endpoints:
   - GET /api/v1/prototype/scope
   - POST /api/v1/prototype/scope/verify
   - POST /api/v1/auth/login (PLATFORM_ADMIN, HOSPITAL_ADMIN, DOCTOR, PATIENT)
   - POST /api/v1/patients/login
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.config import SessionLocal, engine
from app.database.models import (
    Base, Hospital, Doctor, DoctorCalendar, BlockedSlot, Appointment,
    PatientProfile, HospitalQuestionnaire, PatientQuestionnaireResponse,
    WorkflowInstance, AuditLog, EHRSyncLog, AIEvaluationRecord, HospitalStatus
)
from app.vision.prototype_scope_service import (
    PrototypeScopeService, PROTOTYPE_SCOPE_SPECIFICATION
)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed test hospital if none exists
        if not db.query(Hospital).first():
            hosp = Hospital(
                name="Scope St. Jude General",
                code="STJUDE",
                hospital_status=HospitalStatus.APPROVED,
                is_active=True,
                admin_email="admin@stjude.org",
                admin_name="Dr. Gregory House"
            )
            db.add(hosp)
            db.commit()
            db.refresh(hosp)

            doc = Doctor(
                hospital_id=hosp.id,
                name="Dr. Lisa Cuddy",
                specialty="Endocrinology",
                department="Internal Medicine",
                consultation_fee=180.0,
                is_active=True
            )
            db.add(doc)
            db.commit()
        yield db
    finally:
        db.close()


def test_prototype_scope_specification_catalog():
    """Validates that all 9 Must-Have Prototype Scope domains and 60+ features are documented."""
    spec = PrototypeScopeService.get_scope_specification()
    assert spec["total_domains"] == 9
    assert spec["total_features"] >= 60

    expected_domains = {
        "platform", "doctor", "patient", "ai", "ehr_integration",
        "questionnaire", "workflow", "analytics", "ai_operations"
    }
    actual_domains = {d["domain_id"] for d in spec["domains"]}
    assert expected_domains == actual_domains

    # Check key features exist in specific domains
    domain_map = {d["domain_id"]: {f["id"]: f for f in d["features"]} for d in spec["domains"]}
    
    # Platform
    assert "user_authentication" in domain_map["platform"]
    assert "multi_tenant_architecture" in domain_map["platform"]
    assert "hospital_approval" in domain_map["platform"]

    # Doctor
    assert "doctor_profile" in domain_map["doctor"]
    assert "calendar" in domain_map["doctor"]
    assert "availability" in domain_map["doctor"]
    assert "blocked_slots" in domain_map["doctor"]

    # Patient
    assert "registration" in domain_map["patient"]
    assert "login" in domain_map["patient"]
    assert "appointment_history" in domain_map["patient"]

    # AI
    assert "web_realtime_voice" in domain_map["ai"]
    assert "inbound_phone" in domain_map["ai"]
    assert "intent_understanding" in domain_map["ai"]
    assert "human_escalation" in domain_map["ai"]

    # EHR Integration
    assert "mock_ehr_healthcare_system" in domain_map["ehr_integration"]
    assert "patient_lookup" in domain_map["ehr_integration"]
    assert "idempotency" in domain_map["ehr_integration"]

    # Questionnaire
    assert "doctor_created_questions" in domain_map["questionnaire"]
    assert "voice_based_answers" in domain_map["questionnaire"]

    # Workflow
    assert "appointment_confirmation_workflow" in domain_map["workflow"]
    assert "reminder_workflow" in domain_map["workflow"]
    assert "workflow_status_tracking" in domain_map["workflow"]

    # Analytics
    assert "appointments" in domain_map["analytics"]
    assert "ai_calls" in domain_map["analytics"]
    assert "audit_logs" in domain_map["analytics"]

    # AI Operations
    assert "ai_usage_metrics" in domain_map["ai_operations"]
    assert "latency_measurement" in domain_map["ai_operations"]
    assert "traceable_operations" in domain_map["ai_operations"]


def test_prototype_scope_live_verification_all_domains(db_session: Session):
    """Executes live verification tests across all 9 domains and verifies 100% completion."""
    res = PrototypeScopeService.verify_all_domains(db_session)
    assert res["all_passed"] is True
    assert res["overall_status"] == "VERIFIED_PASSED"
    assert res["total_domains"] == 9
    assert res["verified_domains"] == 9
    assert res["completion_percentage"] == 100.0
    assert res["total_assertions_checked"] >= 60

    # Ensure each domain's result is passed
    for domain_id in ["platform", "doctor", "patient", "ai", "ehr_integration", "questionnaire", "workflow", "analytics", "ai_operations"]:
        domain_res = res["domain_results"].get(domain_id)
        assert domain_res is not None, f"Domain {domain_id} missing from results"
        assert domain_res["passed"] is True, f"Domain {domain_id} failed verification"
        assert domain_res["assertions_checked"] > 0


def test_prototype_scope_api_spec_and_verify(client: TestClient):
    """Tests GET /api/v1/prototype/scope and POST /api/v1/prototype/scope/verify."""
    # GET specification
    resp = client.get("/api/v1/prototype/scope")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_domains"] == 9
    assert len(data["domains"]) == 9

    # POST verify
    verify_resp = client.post("/api/v1/prototype/scope/verify", json={})
    assert verify_resp.status_code == 200
    v_data = verify_resp.json()
    assert v_data["all_passed"] is True
    assert v_data["completion_percentage"] == 100.0
    assert v_data["verified_domains"] == 9


def test_prototype_auth_login_all_personas(client: TestClient):
    """Tests unified platform user login for Platform Admin, Hospital Admin, Doctor, and Patient."""
    # 1. Platform Admin Login
    p_admin_resp = client.post("/api/v1/auth/login", json={
        "email_or_identifier": "superadmin@voiceplatform.com",
        "role": "PLATFORM_ADMIN"
    })
    assert p_admin_resp.status_code == 200
    p_data = p_admin_resp.json()
    assert p_data["role"] == "PLATFORM_ADMIN"
    assert "access_token" in p_data
    assert p_data["headers"]["X-User-Role"] == "PLATFORM_ADMIN"

    # 2. Hospital Admin Login
    h_admin_resp = client.post("/api/v1/auth/login", json={
        "email_or_identifier": "admin@stjude.org",
        "role": "HOSPITAL_ADMIN"
    })
    assert h_admin_resp.status_code == 200
    h_data = h_admin_resp.json()
    assert h_data["role"] == "HOSPITAL_ADMIN"
    assert "access_token" in h_data
    assert h_data["headers"]["X-User-Role"] == "HOSPITAL_ADMIN"
    assert "X-Hospital-Id" in h_data["headers"]

    # 3. Doctor Login
    doc_resp = client.post("/api/v1/auth/login", json={
        "email_or_identifier": "Dr. Lisa Cuddy",
        "role": "DOCTOR"
    })
    assert doc_resp.status_code == 200
    doc_data = doc_resp.json()
    assert doc_data["role"] == "DOCTOR"
    assert "access_token" in doc_data
    assert doc_data["headers"]["X-User-Role"] == "DOCTOR"
    assert "X-Doctor-Id" in doc_data["headers"]

    # 4. Patient Login
    pat_resp = client.post("/api/v1/auth/login", json={
        "email_or_identifier": "+15552345678",
        "role": "PATIENT"
    })
    assert pat_resp.status_code == 200
    pat_data = pat_resp.json()
    assert pat_data["role"] == "PATIENT"
    assert "access_token" in pat_data
    assert pat_data["headers"]["X-User-Role"] == "PATIENT"

    # 5. Invalid role rejection
    inv_resp = client.post("/api/v1/auth/login", json={
        "email_or_identifier": "test@test.com",
        "role": "UNKNOWN_ROLE"
    })
    assert inv_resp.status_code == 400


def test_patient_self_service_login(client: TestClient):
    """Tests POST /api/v1/patients/login for patient self-service portal."""
    resp = client.post("/api/v1/patients/login", json={
        "phone_number": "+15559871122",
        "full_name": "Elena Rostova",
        "email": "elena@example.com"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["phone_number"] == "+15559871122"
    assert data["full_name"] == "Elena Rostova"
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["headers"]["X-User-Role"] == "PATIENT"
    assert data["headers"]["X-Patient-Id"] == data["patient_id"]
