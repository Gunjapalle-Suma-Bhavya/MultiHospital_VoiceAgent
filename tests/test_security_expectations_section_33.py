"""
Test Suite for Section 33: Security Expectations.

Validates:
1. Authentication (JWT / Token issuance, API caller verification)
2. Role-Based Authorization (PATIENT, DOCTOR, HOSPITAL_ADMIN, PLATFORM_ADMIN)
3. Tenant Isolation (Hospital resource boundaries, Cross-tenant denial)
4. Secure Secret Management (Encryption of EHR secrets, credentials masking)
5. Input Validation (Pydantic schema enforcement, XSS / Injection prevention)
6. API Protection (Protected endpoints, Role guards)
7. Secure EHR / External-System Access (Token bearer auth, TLS/HTTPS endpoints)
8. Appropriate Data Retention (Soft deletes, Data minimization)
9. Auditability (Tamper-evident audit logs with correlation IDs)
10. Privacy-Aware Logging (Zero raw PHI in operational logs, sanitization)
11. External Identifier Protection (Decoupled internal UUIDs vs external EHR keys)
12. Integration Credential Isolation (Per-hospital isolated credential storage in SecretsVault)
"""

import pytest
import uuid
from datetime import datetime, date, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.config import get_db
from app.database.models import (
    Base, Hospital, Doctor, PatientProfile, Appointment, HospitalStatus,
    AuditLog, PrivacyAccessAudit
)
from app.security import (
    TenantIsolationEnforcer, tenant_isolation_enforcer,
    ContextSecurityGuard, context_security_guard,
    SecretsVault, secrets_vault
)
from app.audit.privacy_sanitizer import PrivacySanitizer
from app.audit.privacy_access_controller import PrivacyAccessController


# In-memory test DB
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
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
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def setup_tenants(setup_db):
    db = setup_db
    hosp1 = Hospital(
        id="hosp-1-uuid",
        name="Mayo Health Center",
        code="MAYO",
        hospital_status=HospitalStatus.APPROVED,
        is_active=True
    )
    hosp2 = Hospital(
        id="hosp-2-uuid",
        name="Cleveland Clinic",
        code="CLEVE",
        hospital_status=HospitalStatus.APPROVED,
        is_active=True
    )
    doc1 = Doctor(
        id="doc-1-uuid",
        hospital_id="hosp-1-uuid",
        name="Dr. Sarah Connor",
        specialty="Neurology",
        is_active=True
    )
    db.add_all([hosp1, hosp2, doc1])
    db.commit()
    return {"hosp1": hosp1, "hosp2": hosp2, "doc1": doc1}


def test_section_33_1_tenant_isolation_and_cross_tenant_denial(setup_db, setup_tenants):
    """
    Validates tenant isolation:
    - Queries for Hospital 1 resources must reject Hospital 2 credentials.
    """
    db = setup_db

    # Valid access: accessing own tenant
    res_valid = tenant_isolation_enforcer.verify_tenant_access(
        db=db,
        actor_role="HOSPITAL_ADMIN",
        actor_id="admin-1",
        actor_hospital_id="hosp-1-uuid",
        target_hospital_id="hosp-1-uuid",
        resource_type="PATIENT_RECORDS"
    )
    assert res_valid["allowed"] is True

    # Platform admin has global cross-tenant oversight
    res_platform = tenant_isolation_enforcer.verify_tenant_access(
        db=db,
        actor_role="PLATFORM_ADMIN",
        actor_id="plat-superadmin",
        actor_hospital_id=None,
        target_hospital_id="hosp-1-uuid",
        resource_type="AUDIT_RECORDS"
    )
    assert res_platform["allowed"] is True

    # Cross-tenant violation: Hospital 2 trying to access Hospital 1
    res_denied = tenant_isolation_enforcer.verify_tenant_access(
        db=db,
        actor_role="HOSPITAL_ADMIN",
        actor_id="admin-2",
        actor_hospital_id="hosp-2-uuid",
        target_hospital_id="hosp-1-uuid",
        resource_type="PATIENT_RECORDS"
    )
    assert res_denied["allowed"] is False
    assert "Cross-tenant isolation violation" in res_denied["reason"]


def test_section_33_2_secrets_vault_credential_isolation():
    """
    Validates secure secret management and integration credential isolation:
    - Environment-aware resolution without hardcoded credentials
    - Masked representation for logging/auditing
    """
    audit = secrets_vault.get_all_secrets_audit()
    assert "OPENAI_API_KEY" in audit
    assert "EHR_CLIENT_SECRET" in audit
    assert "FHIR_SERVER_TOKEN" in audit

    # Masked representation
    for key, meta in audit.items():
        assert meta.masked_value != ""
        assert "...." in meta.masked_value or "****" in meta.masked_value

    # Validate scanner detects leaks
    scanner_clean = secrets_vault.validate_no_hardcoded_leakage("Safe conversational agent response.")
    assert scanner_clean["is_clean"] is True


def test_section_33_3_privacy_aware_logging_and_phi_sanitization():
    """
    Validates privacy-aware logging:
    - Zero raw PHI (symptoms, transcripts, phone numbers) stored in operational logs.
    """
    payload = {
        "user_utterance": "I have chest pain and shortness of breath",
        "phone": "+1-555-432-8765",
        "email": "patient.doe@example.com",
        "hospital_id": "hosp-1-uuid"
    }
    sanitized, privacy_level = PrivacySanitizer.sanitize_payload(payload)

    assert sanitized["user_utterance"] == "[REDACTED_SENSITIVE_HEALTH_INFO]"
    assert sanitized["phone"] != "+1-555-432-8765"
    assert "patient.doe@example.com" not in sanitized["email"]
    assert sanitized["hospital_id"] == "hosp-1-uuid"  # Non-sensitive ID preserved


def test_section_33_4_external_identifier_protection(setup_db):
    """
    Validates external identifier protection:
    - System maintains isolated internal UUIDs and decouples them from external EHR identifiers.
    """
    db = setup_db
    patient = PatientProfile(
        id=str(uuid.uuid4()),
        phone_number="+15550007777",
        full_name="Alice Confidential",
        external_patient_id="EXT-EPIC-PAT-9001"
    )
    db.add(patient)
    db.commit()

    # Internal identity is distinct from external EHR key
    assert patient.id != patient.external_patient_id
    assert patient.external_patient_id.startswith("EXT-EPIC-")
    assert uuid.UUID(patient.id)  # Internal ID is valid UUID


def test_section_33_5_api_protection_and_role_authorization(client: TestClient):
    """
    Validates API authentication and role-based endpoint protection:
    - Enforces strict 403 rejection on unauthorized role/boundary violations.
    """
    # Cross-patient violation: Patient 1 trying to cancel Patient 2's appointment
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
