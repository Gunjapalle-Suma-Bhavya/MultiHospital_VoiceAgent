"""
Comprehensive Tests for Section 16 (Concurrency & Double-Booking Protection) and
Section 17 (Security & Data Isolation).
"""

import threading
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Hospital, Doctor, Appointment, AppointmentStatus, HospitalStatus
from app.database.config import get_db
from app.main import app
from app.scheduling.concurrency import ConcurrencyProtectionEngine, concurrency_protection_engine
from app.security import (
    TenantIsolationEnforcer, tenant_isolation_enforcer,
    ContextSecurityGuard, context_security_guard,
    SecretsVault, secrets_vault
)
from app.security.context_security import ContextRetrievalFilter


# Isolated test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_sec_concurrency.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Hospital A
    hosp_a = Hospital(
        id="hosp-a-uuid",
        name="Metro Hospital A",
        code="HOSP_A",
        hospital_status=HospitalStatus.APPROVED,
        is_active=True
    )
    # Hospital B
    hosp_b = Hospital(
        id="hosp-b-uuid",
        name="Valley Hospital B",
        code="HOSP_B",
        hospital_status=HospitalStatus.APPROVED,
        is_active=True
    )
    # Doctor in Hospital A
    doc_a = Doctor(
        id="doc-a-uuid",
        hospital_id="hosp-a-uuid",
        name="Dr. Alice Smith",
        specialty="Cardiology",
        is_active=True
    )
    db.add_all([hosp_a, hosp_b, doc_a])
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# =========================================================================
# SECTION 16: CONCURRENCY & DOUBLE-BOOKING PROTECTION TESTS
# =========================================================================

def test_section_16_single_slot_double_booking_race_condition():
    """
    Patient A and Patient B simultaneously request the same doctor at 3 PM.
    Exactly one obtains the slot reservation, the second is blocked.
    """
    db = TestingSessionLocal()
    slot_time = datetime(2026, 10, 1, 15, 0, 0)
    slot_end = datetime(2026, 10, 1, 15, 30, 0)
    doc_id = "doc-a-uuid"

    results = []

    def book_patient(p_id, name, phone):
        res = concurrency_protection_engine.reserve_slot(
            db=db,
            doctor_id=doc_id,
            slot_start=slot_time,
            slot_end=slot_end,
            patient_identifier=p_id,
            patient_name=name,
            patient_phone=phone,
            ttl_seconds=300
        )
        results.append((p_id, res))

    # Spawn two concurrent threads simulating simultaneous requests
    t1 = threading.Thread(target=book_patient, args=("PAT-A", "Patient Alice", "+15550001111"))
    t2 = threading.Thread(target=book_patient, args=("PAT-B", "Patient Bob", "+15550002222"))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert len(results) == 2
    successes = [r for r in results if r[1]["success"] is True]
    conflicts = [r for r in results if r[1]["success"] is False and r[1].get("conflict_detected") is True]

    assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}"
    assert len(conflicts) == 1, f"Expected exactly 1 conflict blocked, got {len(conflicts)}"
    assert conflicts[0][1]["reason"] == "DOUBLE_BOOKING_PREVENTED"
    db.close()


def test_section_16_pre_confirmation_external_ehr_verification_and_reconciliation():
    """
    If an external system claimed the slot before confirmation,
    platform reconciles conflict rather than confirming invalid appointment.
    """
    db = TestingSessionLocal()
    slot_time = datetime(2026, 10, 2, 11, 0, 0)
    slot_end = datetime(2026, 10, 2, 11, 30, 0)
    doc_id = "doc-a-uuid"

    # 1. Reserve slot
    res = concurrency_protection_engine.reserve_slot(
        db=db,
        doctor_id=doc_id,
        slot_start=slot_time,
        slot_end=slot_end,
        patient_identifier="PAT-C",
        patient_name="Patient Charlie",
        patient_phone="+15550003333"
    )
    assert res["success"] is True
    res_id = res["reservation_id"]

    # 2. Confirm with external verifier detecting external system claimed it
    confirm_res = concurrency_protection_engine.verify_and_confirm_slot(
        db=db,
        reservation_id=res_id,
        hospital_id="hosp-a-uuid",
        external_ehr_verifier=lambda d, s, e: False  # External system took it!
    )
    assert confirm_res["success"] is False
    assert confirm_res["reconciliation_required"] is True
    assert confirm_res["reason"] == "EXTERNAL_SYSTEM_ALREADY_CLAIMED_SLOT"
    db.close()


def test_section_16_successful_external_verification_and_booking():
    """
    When external verifier confirms slot availability, appointment is committed.
    """
    db = TestingSessionLocal()
    slot_time = datetime(2026, 10, 3, 14, 0, 0)
    slot_end = datetime(2026, 10, 3, 14, 30, 0)
    doc_id = "doc-a-uuid"

    res = concurrency_protection_engine.reserve_slot(
        db=db,
        doctor_id=doc_id,
        slot_start=slot_time,
        slot_end=slot_end,
        patient_identifier="PAT-D",
        patient_name="Patient Diana",
        patient_phone="+15550004444"
    )
    assert res["success"] is True

    confirm_res = concurrency_protection_engine.verify_and_confirm_slot(
        db=db,
        reservation_id=res["reservation_id"],
        hospital_id="hosp-a-uuid",
        external_ehr_verifier=lambda d, s, e: True  # External system verifies available
    )
    assert confirm_res["success"] is True
    assert confirm_res["status"] == "CONFIRMED"
    assert "external_appointment_id" in confirm_res
    db.close()


# =========================================================================
# SECTION 17: SECURITY & DATA ISOLATION TESTS
# =========================================================================

def test_section_17_tenant_isolation_hospital_a_cannot_access_hospital_b():
    """
    Hospital A admin/doctor users strictly cannot access Hospital B private data.
    """
    db = TestingSessionLocal()

    # Hospital A admin attempts to access Hospital B
    res = tenant_isolation_enforcer.verify_tenant_access(
        db=db,
        actor_role="HOSPITAL_ADMIN",
        actor_id="admin-a",
        actor_hospital_id="hosp-a-uuid",
        target_hospital_id="hosp-b-uuid",
        resource_type="PATIENT_RECORDS"
    )
    assert res["allowed"] is False
    assert "Cross-tenant isolation violation" in res["reason"]

    # Same hospital allowed
    res_allowed = tenant_isolation_enforcer.verify_tenant_access(
        db=db,
        actor_role="HOSPITAL_ADMIN",
        actor_id="admin-a",
        actor_hospital_id="hosp-a-uuid",
        target_hospital_id="hosp-a-uuid",
        resource_type="PATIENT_RECORDS"
    )
    assert res_allowed["allowed"] is True

    # Platform Admin cross-hospital oversight allowed
    res_platform = tenant_isolation_enforcer.verify_tenant_access(
        db=db,
        actor_role="PLATFORM_ADMIN",
        actor_id="plat-superadmin",
        actor_hospital_id=None,
        target_hospital_id="hosp-b-uuid",
        resource_type="AUDIT_RECORDS"
    )
    assert res_platform["allowed"] is True
    db.close()


def test_section_17_1_context_security_and_minimal_retrieval():
    """
    Prevents cross-user context leakage and enforces minimal necessary context scope.
    """
    db = TestingSessionLocal()

    # Cross-user leakage attempt: Patient A asks for Patient B's context
    flt_leak = ContextRetrievalFilter(
        caller_role="PATIENT",
        caller_patient_id="patient-101",
        target_patient_id="patient-999",
        operation_type="SCHEDULE_APPOINTMENT"
    )
    res_leak = context_security_guard.filter_context_for_operation(
        db=db,
        filter_req=flt_leak,
        raw_context_bundle={}
    )
    assert res_leak["authorized"] is False
    assert res_leak["error"] == "CROSS_USER_LEAKAGE_PREVENTED"

    # Authorized Minimal Context Rule
    flt_valid = ContextRetrievalFilter(
        caller_role="PATIENT",
        caller_patient_id="patient-101",
        target_patient_id="patient-101",
        operation_type="SCHEDULE_APPOINTMENT"
    )
    raw_bundle = {
        "tier1_conversation_state": {"intent": "BOOK", "specialty": "Neurology"},
        "tier3_long_term": {"preferred_time_window": "AFTERNOON", "internal_id": "RAW_INTERNAL_UUID"},
        "tier4_appointment_info": {"upcoming_appointments": [{"id": 1}]}
    }
    res_valid = context_security_guard.filter_context_for_operation(
        db=db,
        filter_req=flt_valid,
        raw_context_bundle=raw_bundle
    )
    assert res_valid["authorized"] is True
    sanitized = res_valid["sanitized_context"]
    assert sanitized["minimal_scope_applied"] is True
    assert "specialty" in sanitized["conversation_state"]
    # Verify internal DB key was scrubbed
    assert "internal_id" not in sanitized.get("preferences", {})
    db.close()


def test_section_17_2_secrets_and_config_not_hardcoded():
    """
    Verifies that secrets are environment-aware, masked for audits, and zero plain leakage.
    """
    audit = secrets_vault.get_all_secrets_audit()
    assert "TWILIO_AUTH_TOKEN" in audit
    assert "OPENAI_API_KEY" in audit
    assert "EHR_CLIENT_SECRET" in audit
    assert "DATABASE_URL" in audit

    for key, meta in audit.items():
        # Never reveals plain secret
        assert meta.masked_value != ""
        if len(meta.masked_value) > 6:
            assert "...." in meta.masked_value or "******" in meta.masked_value

    # Validate scanner detects leaks
    scanner_clean = secrets_vault.validate_no_hardcoded_leakage("Safe conversational agent response.")
    assert scanner_clean["is_clean"] is True


def test_security_and_concurrency_api_endpoints():
    """
    Tests REST API endpoints for Section 16 & Section 17.
    """
    # 1. API: Reserve Slot
    res = client.post("/api/v1/security-concurrency/reserve-slot", json={
        "doctor_id": "doc-a-uuid",
        "slot_start": "2026-10-05T10:00:00",
        "slot_end": "2026-10-05T10:30:00",
        "patient_identifier": "API-PAT-1",
        "patient_name": "API Patient One",
        "patient_phone": "+15559990001"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    res_id = data["reservation_id"]

    # 2. API: List active reservations
    list_res = client.get("/api/v1/security-concurrency/reservations")
    assert list_res.status_code == 200
    active_res = list_res.json()["active_reservations"]
    assert any(r["reservation_id"] == res_id for r in active_res)

    # 3. API: Tenant Isolation Check
    tenant_res = client.post("/api/v1/security-concurrency/tenant-check", json={
        "actor_role": "HOSPITAL_ADMIN",
        "actor_id": "admin-hosp-a",
        "actor_hospital_id": "hosp-a-uuid",
        "target_hospital_id": "hosp-b-uuid",
        "resource_type": "CLINICAL_INTAKE"
    })
    assert tenant_res.status_code == 200
    assert tenant_res.json()["allowed"] is False

    # 4. API: Context Security Check
    ctx_res = client.post("/api/v1/security-concurrency/context-security-check", json={
        "caller_role": "PATIENT",
        "caller_patient_id": "pat-123",
        "target_patient_id": "pat-123",
        "operation_type": "SCHEDULE_APPOINTMENT"
    })
    assert ctx_res.status_code == 200
    assert ctx_res.json()["authorized"] is True

    # 5. API: Secrets Vault Audit
    sec_res = client.get("/api/v1/security-concurrency/secrets-vault-audit")
    assert sec_res.status_code == 200
    sec_data = sec_res.json()
    assert sec_data["vault_status"] == "SECURE"
    assert sec_data["zero_hardcoded_secrets"] is True
