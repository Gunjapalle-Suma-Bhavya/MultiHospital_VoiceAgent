"""
Tests for Step 6 — Role-Based Access Control (RBAC).

Verifies strict role boundaries across the 4 platform personas:
1. Platform Admin (8 operations, global authority)
2. Hospital Admin (10 operations, multi-tenant isolation strictly enforced)
3. Doctor (5 operations, doctor boundary isolation strictly enforced)
4. Patient (7 operations, patient boundary isolation strictly enforced)
5. Security audit logging on access denial and boundary violations.
6. RBAC REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.config import get_db
from app.database.models import Base, AuditLog
from app.audit import AuditCategory
from app.rbac import (
    UserRole, Permission, ROLE_PERMISSIONS_MAP, ROLE_BOUNDARY_RULES
)
from app.rbac.access_guard import UserContext, AccessGuard


# ---------------------------------------------------------------------------
# Test DB setup
# ---------------------------------------------------------------------------
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 1. Platform Admin Role Tests (8 Operations)
# ---------------------------------------------------------------------------
def test_platform_admin_role_boundaries(setup_db):
    """
    Platform Admin:
    Can: Approve hospitals, Suspend hospitals, View global analytics,
         Manage platform configuration, Review audit events, Review operational health,
         Review AI evaluations, Review EHR integration health.
    """
    db = setup_db
    ctx = UserContext(user_id="admin-01", role="PLATFORM_ADMIN")

    expected_ops = [
        Permission.APPROVE_HOSPITALS.value,
        Permission.SUSPEND_HOSPITALS.value,
        Permission.VIEW_GLOBAL_ANALYTICS.value,
        Permission.MANAGE_PLATFORM_CONFIG.value,
        Permission.REVIEW_AUDIT_EVENTS.value,
        Permission.REVIEW_OPERATIONAL_HEALTH.value,
        Permission.REVIEW_AI_EVALUATIONS.value,
        Permission.REVIEW_EHR_INTEGRATION_HEALTH.value,
    ]

    # Verify all 8 operations are allowed
    for op in expected_ops:
        res = AccessGuard.evaluate(ctx, op, db=db)
        assert res["authorized"] is True
        assert res["decision"] == "GRANTED"

    # Verify unauthorized operation outside Platform Admin scope
    denied = AccessGuard.evaluate(ctx, Permission.MANAGE_OWN_PROFILE.value, db=db)
    assert denied["authorized"] is False
    assert denied["decision"] == "DENIED"


# ---------------------------------------------------------------------------
# 2. Hospital Admin Role & Tenant Isolation Tests (10 Operations)
# ---------------------------------------------------------------------------
def test_hospital_admin_operations_and_tenant_isolation(setup_db):
    """
    Hospital Admin:
    Can: Manage hospital profile, Create doctors, Manage calendars,
         Configure availability, Manage questionnaires, View appointments,
         View hospital analytics, Configure approved workflows, Manage staff,
         Configure supported healthcare-system integrations.
    Cannot: Access another hospital's private data.
    """
    db = setup_db
    ctx = UserContext(user_id="hosp-admin-01", role="HOSPITAL_ADMIN", hospital_id="HOSP-A")

    expected_ops = [
        Permission.MANAGE_HOSPITAL_PROFILE.value,
        Permission.CREATE_DOCTORS.value,
        Permission.MANAGE_CALENDARS.value,
        Permission.CONFIGURE_AVAILABILITY.value,
        Permission.MANAGE_QUESTIONNAIRES.value,
        Permission.VIEW_HOSPITAL_APPOINTMENTS.value,
        Permission.VIEW_HOSPITAL_ANALYTICS.value,
        Permission.CONFIGURE_APPROVED_WORKFLOWS.value,
        Permission.MANAGE_STAFF.value,
        Permission.CONFIGURE_HEALTHCARE_INTEGRATIONS.value,
    ]

    # All 10 operations allowed within own hospital
    for op in expected_ops:
        res = AccessGuard.evaluate(ctx, op, target_hospital_id="HOSP-A", db=db)
        assert res["authorized"] is True
        assert res["decision"] == "GRANTED"

    # Multi-Tenant Violation: Accessing another hospital's private data
    cross_tenant = AccessGuard.evaluate(
        ctx,
        Permission.VIEW_HOSPITAL_ANALYTICS.value,
        target_hospital_id="HOSP-B",
        db=db
    )
    assert cross_tenant["authorized"] is False
    assert cross_tenant["decision"] == "DENIED"
    assert "Tenant isolation violation" in cross_tenant["reason"]

    # Verify cannot approve hospitals (Platform Admin only)
    unauthorized_op = AccessGuard.evaluate(ctx, Permission.APPROVE_HOSPITALS.value, db=db)
    assert unauthorized_op["authorized"] is False
    assert unauthorized_op["decision"] == "DENIED"


# ---------------------------------------------------------------------------
# 3. Doctor Role & Doctor Scope Isolation Tests (5 Operations)
# ---------------------------------------------------------------------------
def test_doctor_operations_and_boundary_isolation(setup_db):
    """
    Doctor:
    Can: Manage own calendar, Block slots, Configure approved questionnaires,
         View own appointments, View authorized patient responses.
    Cannot: Access other doctors' calendars, slots, or appointments.
    """
    db = setup_db
    ctx = UserContext(user_id="doc-usr-01", role="DOCTOR", doctor_id="DOC-DR-HOUSE")

    expected_ops = [
        Permission.MANAGE_OWN_CALENDAR.value,
        Permission.BLOCK_SLOTS.value,
        Permission.CONFIGURE_APPROVED_QUESTIONNAIRES.value,
        Permission.VIEW_OWN_APPOINTMENTS.value,
        Permission.VIEW_AUTHORIZED_PATIENT_RESPONSES.value,
    ]

    # All 5 operations allowed for own doctor identity
    for op in expected_ops:
        res = AccessGuard.evaluate(ctx, op, target_doctor_id="DOC-DR-HOUSE", db=db)
        assert res["authorized"] is True
        assert res["decision"] == "GRANTED"

    # Doctor Boundary Violation: Accessing another doctor's slots
    doc_violation = AccessGuard.evaluate(
        ctx,
        Permission.BLOCK_SLOTS.value,
        target_doctor_id="DOC-OTHER-DOCTOR",
        db=db
    )
    assert doc_violation["authorized"] is False
    assert doc_violation["decision"] == "DENIED"
    assert "Doctor boundary violation" in doc_violation["reason"]

    # Verify cannot manage hospital profile
    unauthorized_op = AccessGuard.evaluate(ctx, Permission.MANAGE_HOSPITAL_PROFILE.value, db=db)
    assert unauthorized_op["authorized"] is False


# ---------------------------------------------------------------------------
# 4. Patient Role & Patient Scope Isolation Tests (7 Operations)
# ---------------------------------------------------------------------------
def test_patient_operations_and_boundary_isolation(setup_db):
    """
    Patient:
    Can: Manage own profile, Book appointments, Reschedule, Cancel,
         Complete questionnaires, View own appointments, Manage appropriate preferences.
    Cannot: Access other patients' profiles, appointments, or responses.
    """
    db = setup_db
    ctx = UserContext(user_id="pat-usr-01", role="PATIENT", patient_id="PAT-ALICE")

    expected_ops = [
        Permission.MANAGE_OWN_PROFILE.value,
        Permission.BOOK_APPOINTMENTS.value,
        Permission.RESCHEDULE_APPOINTMENTS.value,
        Permission.CANCEL_APPOINTMENTS.value,
        Permission.COMPLETE_QUESTIONNAIRES.value,
        Permission.VIEW_OWN_PATIENT_APPOINTMENTS.value,
        Permission.MANAGE_PREFERENCES.value,
    ]

    # All 7 operations allowed for own patient identity
    for op in expected_ops:
        res = AccessGuard.evaluate(ctx, op, target_patient_id="PAT-ALICE", db=db)
        assert res["authorized"] is True
        assert res["decision"] == "GRANTED"

    # Patient Boundary Violation: Canceling another patient's appointment
    pat_violation = AccessGuard.evaluate(
        ctx,
        Permission.CANCEL_APPOINTMENTS.value,
        target_patient_id="PAT-BOB",
        db=db
    )
    assert pat_violation["authorized"] is False
    assert pat_violation["decision"] == "DENIED"
    assert "Patient boundary violation" in pat_violation["reason"]

    # Verify cannot create doctors
    unauthorized_op = AccessGuard.evaluate(ctx, Permission.CREATE_DOCTORS.value, db=db)
    assert unauthorized_op["authorized"] is False


# ---------------------------------------------------------------------------
# 5. Security Audit Logging on Access Denial
# ---------------------------------------------------------------------------
def test_security_audit_logging_on_violations(setup_db):
    """
    Verifies that denied access attempts produce security review audit events.
    """
    db = setup_db
    ctx = UserContext(user_id="hosp-admin-bad", role="HOSPITAL_ADMIN", hospital_id="HOSP-X")

    # Trigger cross-tenant violation
    AccessGuard.evaluate(
        ctx,
        Permission.VIEW_HOSPITAL_ANALYTICS.value,
        target_hospital_id="HOSP-Y",
        db=db
    )

    # Check security audit log in DB
    sec_logs = (
        db.query(AuditLog)
        .filter(AuditLog.category == AuditCategory.SECURITY_REVIEW.value)
        .all()
    )
    assert len(sec_logs) >= 1
    assert sec_logs[0].event_type == "RBAC_AUTHORIZATION_CHECK"
    assert sec_logs[0].status == "DENIED"
    assert "HOSP-Y" in sec_logs[0].payload_json


# ---------------------------------------------------------------------------
# 6. REST API Endpoints Verification
# ---------------------------------------------------------------------------
def test_rbac_rest_api_suite(client):
    """
    Verifies /api/v1/rbac REST API endpoints: matrix, permissions, evaluate, enforce, and me.
    """
    # 1. GET /api/v1/rbac/matrix
    matrix_res = client.get("/api/v1/rbac/matrix")
    assert matrix_res.status_code == 200
    data = matrix_res.json()
    assert data["total_roles"] == 4
    assert "PLATFORM_ADMIN" in data["matrix"]
    assert "HOSPITAL_ADMIN" in data["matrix"]
    assert "DOCTOR" in data["matrix"]
    assert "PATIENT" in data["matrix"]
    assert data["matrix"]["PLATFORM_ADMIN"]["allowed_count"] == 8
    assert data["matrix"]["HOSPITAL_ADMIN"]["allowed_count"] == 10
    assert data["matrix"]["DOCTOR"]["allowed_count"] == 5
    assert data["matrix"]["PATIENT"]["allowed_count"] == 7

    # 2. GET /api/v1/rbac/permissions/DOCTOR
    doc_res = client.get("/api/v1/rbac/permissions/DOCTOR")
    assert doc_res.status_code == 200
    assert doc_res.json()["allowed_count"] == 5
    assert "MANAGE_OWN_CALENDAR" in doc_res.json()["permissions"]

    # 3. POST /api/v1/rbac/evaluate (Soft check - Allowed)
    eval_allow = client.post(
        "/api/v1/rbac/evaluate",
        json={
            "role": "HOSPITAL_ADMIN",
            "permission": "MANAGE_HOSPITAL_PROFILE",
            "user_hospital_id": "HOSP-1",
            "target_hospital_id": "HOSP-1",
        }
    )
    assert eval_allow.status_code == 200
    assert eval_allow.json()["authorized"] is True

    # 4. POST /api/v1/rbac/evaluate (Soft check - Denied)
    eval_deny = client.post(
        "/api/v1/rbac/evaluate",
        json={
            "role": "HOSPITAL_ADMIN",
            "permission": "VIEW_HOSPITAL_ANALYTICS",
            "user_hospital_id": "HOSP-1",
            "target_hospital_id": "HOSP-2",
        }
    )
    assert eval_deny.status_code == 200
    assert eval_deny.json()["authorized"] is False
    assert eval_deny.json()["decision"] == "DENIED"

    # 5. POST /api/v1/rbac/enforce (Strict 403 on violation)
    enforce_res = client.post(
        "/api/v1/rbac/enforce",
        json={
            "role": "PATIENT",
            "permission": "CANCEL_APPOINTMENTS",
            "user_patient_id": "PAT-1",
            "target_patient_id": "PAT-2",
        }
    )
    assert enforce_res.status_code == 403
    assert enforce_res.json()["detail"]["authorized"] is False
    assert "Patient boundary violation" in enforce_res.json()["detail"]["reason"]

    # 6. GET /api/v1/rbac/me
    me_res = client.get(
        "/api/v1/rbac/me",
        headers={
            "X-User-Role": "DOCTOR",
            "X-User-Id": "doc-me",
            "X-Doctor-Id": "DOC-ME-1",
        }
    )
    assert me_res.status_code == 200
    assert me_res.json()["context"]["role"] == "DOCTOR"
    assert me_res.json()["granted_permissions_count"] == 5
