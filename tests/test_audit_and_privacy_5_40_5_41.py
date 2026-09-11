"""
Tests for Section 5.40 Audit Trail and Section 5.41 Privacy-Aware Logging.

Verifies:
1. Canonical 16-step call audit trail reconstruction and chronological formatting.
2. The 7 audit objectives filtering (DEBUGGING, RELIABILITY, OPERATIONAL_MONITORING,
   DISPUTE_INVESTIGATION, AGENT_EVALUATION, SECURITY_REVIEW, INTEGRATION_TROUBLESHOOTING).
3. Automatic privacy-aware sanitization (zero raw PHI/transcripts stored in operational logs).
4. Permission-controlled access for the 6 protected healthcare resource types.
5. Security audit logging of access grants, denials, and cross-tenant violations.
6. REST API endpoints for events, timelines, summaries, and privacy access checks.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.config import get_db
from app.database.models import Base, AuditLog, PrivacyAccessAudit
from app.audit import (
    AuditCategory, AuditEventType, ProtectedResource,
    ROLE_PERMISSIONS, PrivacyLevel, AccessDecision
)
from app.audit.audit_service import AuditService
from app.audit.privacy_sanitizer import PrivacySanitizer
from app.audit.privacy_access_controller import PrivacyAccessController


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
# 1. Section 5.40: Canonical 16-Event Audit Trail & Timeline Reconstruction
# ---------------------------------------------------------------------------
def test_canonical_16_event_audit_trail_reconstruction(setup_db):
    """
    Verifies that the entire 16-event sequence from Section 5.40 specification
    produces a structured, chronological, auditable event timeline.
    """
    db = setup_db
    svc = AuditService(db)
    session_id = "CALL-SESSION-540-001"
    hosp_id = "HOSP-40"
    base_time = datetime(2026, 9, 11, 15, 42, 1)

    # 16-event sequence matching Section 5.40 specification
    canonical_sequence = [
        ("CALL_STARTED", None, None, 0),
        ("PATIENT_IDENTIFIED", None, {"patient_id": "P-101"}, 4),
        ("AI_CONTEXT_RETRIEVED", None, {"intent": "BOOKING"}, 8),
        ("TOOL_CALL", "lookup_patient", {"patient_id": "P-101"}, 10),
        ("TOOL_CALL", "search_doctors", {"specialty": "Cardiology"}, 11),
        ("TOOL_CALL", "check_availability", {"doctor_id": "DOC-1"}, 13),
        ("PATIENT_SELECTED_SLOT", None, {"slot": "10:00 AM"}, 17),
        ("BOOKING_STARTED", None, {"appointment_id": "APT-77"}, 19),
        ("EHR_INTEGRATION_STARTED", None, {"ehr_system": "EPIC"}, 21),
        ("EXTERNAL_APPOINTMENT_CREATED", None, {"external_id": "EXT-99"}, 26),
        ("EHR_SYNC_VERIFIED", None, {"verified": True}, 29),
        ("BOOKING_VERIFIED", None, {"status": "CONFIRMED"}, 31),
        ("QUESTIONNAIRE_STARTED", None, {"questionnaire_id": "Q-1"}, 34),
        ("QUESTIONNAIRE_COMPLETED", None, {"responses_count": 5}, 120),
        ("WORKFLOW_STARTED", None, {"workflow": "POST_INTAKE"}, 124),
        ("CALL_COMPLETED", None, {"duration_seconds": 124}, 124),
    ]

    for event_type, tool_name, payload, sec_offset in canonical_sequence:
        event_time = base_time + timedelta(seconds=sec_offset)
        svc.record_event(
            session_id=session_id,
            hospital_id=hosp_id,
            event_type=event_type,
            tool_name=tool_name,
            payload=payload,
            timestamp=event_time,
        )

    # Reconstruct timeline
    timeline_res = svc.get_session_timeline(session_id)
    assert timeline_res["session_id"] == session_id
    assert timeline_res["event_count"] == 16

    formatted = timeline_res["formatted_summary"]
    # Verify expected formatted output lines from spec
    assert "15:42:01 CALL_STARTED" in formatted
    assert "15:42:05 PATIENT_IDENTIFIED" in formatted
    assert "15:42:09 AI_CONTEXT_RETRIEVED" in formatted
    assert "15:42:11 TOOL_CALL: lookup_patient" in formatted
    assert "15:42:12 TOOL_CALL: search_doctors" in formatted
    assert "15:42:14 TOOL_CALL: check_availability" in formatted
    assert "15:42:18 PATIENT_SELECTED_SLOT" in formatted
    assert "15:42:20 BOOKING_STARTED" in formatted
    assert "15:42:22 EHR_INTEGRATION_STARTED" in formatted
    assert "15:42:27 EXTERNAL_APPOINTMENT_CREATED" in formatted
    assert "15:42:30 EHR_SYNC_VERIFIED" in formatted
    assert "15:42:32 BOOKING_VERIFIED" in formatted
    assert "15:42:35 QUESTIONNAIRE_STARTED" in formatted
    assert "15:44:01 QUESTIONNAIRE_COMPLETED" in formatted
    assert "15:44:05 WORKFLOW_STARTED" in formatted
    assert "15:44:05 CALL_COMPLETED" in formatted

    # Verify integrity
    integrity = svc.verify_trail_integrity(session_id)
    assert integrity["is_valid"] is True
    assert integrity["is_chronological"] is True
    assert integrity["has_call_start"] is True
    assert integrity["has_patient_identified"] is True
    assert integrity["has_call_complete"] is True


# ---------------------------------------------------------------------------
# 2. Section 5.40: The 7 Core Audit Objectives Filtering
# ---------------------------------------------------------------------------
def test_seven_audit_objectives_filtering(setup_db):
    """
    Verifies that the audit trail supports filtering across all 7 specified objectives:
    Debugging, Reliability, Operational monitoring, Dispute investigation,
    Agent evaluation, Security review, and Integration troubleshooting.
    """
    db = setup_db
    svc = AuditService(db)

    # Seed events covering all 7 categories
    objectives = [
        (AuditCategory.DEBUGGING.value, "TOOL_CALL"),
        (AuditCategory.RELIABILITY.value, "EHR_SYNC_VERIFIED"),
        (AuditCategory.OPERATIONAL_MONITORING.value, "APPOINTMENT_SEARCHED"),
        (AuditCategory.DISPUTE_INVESTIGATION.value, "APPOINTMENT_BOOKED"),
        (AuditCategory.AGENT_EVALUATION.value, "AI_CONTEXT_RETRIEVED"),
        (AuditCategory.SECURITY_REVIEW.value, "SECURITY_ACCESS_CHECK"),
        (AuditCategory.INTEGRATION_TROUBLESHOOTING.value, "EHR_INTEGRATION_STARTED"),
    ]

    for cat, ev_type in objectives:
        svc.record_event(
            event_type=ev_type,
            category=cat,
            session_id="SESS-OBJECTIVES",
            hospital_id="HOSP-OBJ",
        )

    # Filter and verify each objective category
    for cat, ev_type in objectives:
        results = svc.query_audit_logs(category=cat, session_id="SESS-OBJECTIVES")
        assert len(results) >= 1
        assert results[0]["category"] == cat
        assert results[0]["event_type"] == ev_type

    # Summary metrics verification
    summary = svc.get_audit_summary()
    assert summary["total_audit_events"] == 7
    for cat in AuditCategory:
        assert summary["categories"][cat.value] >= 1


# ---------------------------------------------------------------------------
# 3. Section 5.41: Privacy-Aware Logging & Automatic Redaction
# ---------------------------------------------------------------------------
def test_privacy_aware_logging_phi_redaction(setup_db):
    """
    Verifies that raw conversational content and sensitive health data (PHI)
    are strictly stripped and sanitized before audit persistence.
    """
    db = setup_db
    svc = AuditService(db)

    # Payload with sensitive healthcare information
    sensitive_payload = {
        "patient_id": "P-999",
        "raw_transcript": "Patient stated: 'I have severe chest pressure and high blood pressure.'",
        "symptoms": ["chest pain", "shortness of breath"],
        "medical_history": "History of cardiac bypass in 2021",
        "ssn": "123-45-6789",
        "email": "john.doe@hospital.org",
        "phone": "555-123-4567",
        "selected_doctor_id": "DOC-77",
    }

    log_entry = svc.record_event(
        event_type="PATIENT_IDENTIFIED",
        session_id="SESS-PRIVACY-01",
        payload=sensitive_payload,
    )

    assert log_entry.privacy_level == PrivacyLevel.REDACTED_PHI.value

    # Verify persisted payload in DB has NO raw clinical PHI or SSN
    retrieved = db.query(AuditLog).filter(AuditLog.id == log_entry.id).first()
    assert "severe chest pressure" not in retrieved.payload_json
    assert "History of cardiac bypass" not in retrieved.payload_json
    assert "123-45-6789" not in retrieved.payload_json

    # Check that structured non-sensitive data is preserved
    import json
    parsed_payload = json.loads(retrieved.payload_json)
    assert parsed_payload["patient_id"] == "P-999"
    assert parsed_payload["selected_doctor_id"] == "DOC-77"
    assert parsed_payload["symptoms"] == "[REDACTED_SENSITIVE_HEALTH_INFO]"
    assert parsed_payload["raw_transcript"] == "[REDACTED_SENSITIVE_HEALTH_INFO]"
    assert parsed_payload["ssn"] == "[REDACTED_IDENTIFIER]"


def test_structured_event_without_phi_remains_structured(setup_db):
    """
    Verifies that clean operational structured events are saved as STRUCTURED_NO_PHI.
    """
    db = setup_db
    svc = AuditService(db)

    clean_payload = {
        "hospital_id": "HOSP-1",
        "doctor_id": "DOC-2",
        "slot_time": "2026-09-15T10:00:00",
        "duration_minutes": 30,
    }

    log_entry = svc.record_event(
        event_type="APPOINTMENT_BOOKED",
        session_id="SESS-CLEAN-01",
        payload=clean_payload,
    )

    assert log_entry.privacy_level == PrivacyLevel.STRUCTURED_NO_PHI.value


# ---------------------------------------------------------------------------
# 4. Section 5.41: Permission-Controlled Access to 6 Protected Resources
# ---------------------------------------------------------------------------
def test_permission_controlled_access_for_six_protected_resources(setup_db):
    """
    Verifies RBAC rules and security audit logging across the 6 protected resources:
    PATIENT_INFO, TRANSCRIPTS, QUESTIONNAIRE_RESPONSES, RECORDINGS,
    OPERATIONAL_DETAILS, and INTEGRATION_DETAILS.
    """
    db = setup_db

    # 1. DOCTOR accessing PATIENT_INFO (Granted)
    grant_res = PrivacyAccessController.evaluate_access(
        db=db,
        requester_role="DOCTOR",
        requester_id="DOC-DR-SMITH",
        resource_type=ProtectedResource.PATIENT_INFO.value,
        resource_id="PAT-123",
        hospital_id="HOSP-A",
        user_hospital_id="HOSP-A",
        reason="Assigned clinical consultation",
    )
    assert grant_res["authorized"] is True
    assert grant_res["decision"] == AccessDecision.GRANTED.value

    # 2. PATIENT attempting to access INTEGRATION_DETAILS (Denied)
    denied_res = PrivacyAccessController.evaluate_access(
        db=db,
        requester_role="PATIENT",
        requester_id="PAT-123",
        resource_type=ProtectedResource.INTEGRATION_DETAILS.value,
        reason="Unauthorized backend probe",
    )
    assert denied_res["authorized"] is False
    assert denied_res["decision"] == AccessDecision.DENIED.value

    # 3. CALL_OPERATOR accessing TRANSCRIPTS (Granted)
    operator_grant = PrivacyAccessController.evaluate_access(
        db=db,
        requester_role="CALL_OPERATOR",
        requester_id="OP-55",
        resource_type=ProtectedResource.TRANSCRIPTS.value,
        resource_id="SESSION-HANDOFF-1",
        reason="Human escalation context review",
    )
    assert operator_grant["authorized"] is True

    # 4. DOCTOR attempting to access RECORDINGS (Denied by default without specific compliance release)
    doctor_recording_denied = PrivacyAccessController.evaluate_access(
        db=db,
        requester_role="DOCTOR",
        requester_id="DOC-DR-SMITH",
        resource_type=ProtectedResource.RECORDINGS.value,
    )
    assert doctor_recording_denied["authorized"] is False
    assert doctor_recording_denied["decision"] == AccessDecision.DENIED.value

    # 5. Multi-tenant isolation violation check: HOSPITAL_ADMIN of Hosp A trying to access Hosp B
    cross_tenant_denied = PrivacyAccessController.evaluate_access(
        db=db,
        requester_role="HOSPITAL_ADMIN",
        requester_id="ADMIN-HOSP-A",
        resource_type=ProtectedResource.QUESTIONNAIRE_RESPONSES.value,
        hospital_id="HOSP-B",
        user_hospital_id="HOSP-A",
        reason="Cross-tenant access attempt",
    )
    assert cross_tenant_denied["authorized"] is False
    assert "Cross-tenant violation" in cross_tenant_denied["reason"]

    # Verify security audit records in DB
    audits = db.query(PrivacyAccessAudit).all()
    assert len(audits) == 5

    # Denied attempts must produce a SECURITY_REVIEW event in general AuditLog
    sec_logs = db.query(AuditLog).filter(AuditLog.category == AuditCategory.SECURITY_REVIEW.value).all()
    assert len(sec_logs) >= 3


# ---------------------------------------------------------------------------
# 5. REST API Endpoints Testing via TestClient
# ---------------------------------------------------------------------------
def test_audit_rest_api_lifecycle(client):
    """
    Verifies the full REST API suite for audit recording, querying, and privacy checks.
    """
    session_id = "API-CALL-777"

    # 1. POST /api/v1/audit/events
    post_res = client.post(
        "/api/v1/audit/events",
        json={
            "event_type": "CALL_STARTED",
            "session_id": session_id,
            "hospital_id": "HOSP-METRO",
            "category": "OPERATIONAL_MONITORING",
            "payload": {"call_sid": "CA12345", "caller": "+15550001111"},
        },
    )
    assert post_res.status_code == 201
    data = post_res.json()
    assert data["status"] == "success"
    assert data["event_type"] == "CALL_STARTED"

    # Post tool call event
    client.post(
        "/api/v1/audit/events",
        json={
            "event_type": "TOOL_CALL",
            "session_id": session_id,
            "hospital_id": "HOSP-METRO",
            "category": "DEBUGGING",
            "tool_name": "lookup_patient",
            "tool_arguments": {"patient_id": "P-456"},
        },
    )

    # 2. GET /api/v1/audit/trail
    trail_res = client.get(f"/api/v1/audit/trail?session_id={session_id}")
    assert trail_res.status_code == 200
    trail_data = trail_res.json()
    assert trail_data["count"] == 2

    # 3. GET /api/v1/audit/timeline/{session_id}
    timeline_res = client.get(f"/api/v1/audit/timeline/{session_id}")
    assert timeline_res.status_code == 200
    tl = timeline_res.json()
    assert tl["event_count"] == 2
    assert "CALL_STARTED" in tl["formatted_summary"]
    assert "TOOL_CALL: lookup_patient" in tl["formatted_summary"]

    # 4. GET /api/v1/audit/summary
    summary_res = client.get("/api/v1/audit/summary?hospital_id=HOSP-METRO")
    assert summary_res.status_code == 200
    assert summary_res.json()["total_audit_events"] == 2

    # 5. POST /api/v1/audit/privacy/access-check (Authorized)
    auth_check = client.post(
        "/api/v1/audit/privacy/access-check",
        json={
            "requester_role": "DOCTOR",
            "requester_id": "DOC-99",
            "resource_type": "PATIENT_INFO",
            "hospital_id": "HOSP-METRO",
            "user_hospital_id": "HOSP-METRO",
            "reason": "Chart review",
        },
    )
    assert auth_check.status_code == 200
    assert auth_check.json()["authorized"] is True

    # 6. POST /api/v1/audit/privacy/access-check (Forbidden)
    forbid_check = client.post(
        "/api/v1/audit/privacy/access-check",
        json={
            "requester_role": "PATIENT",
            "requester_id": "PAT-99",
            "resource_type": "RECORDINGS",
            "reason": "Direct audio extract",
        },
    )
    assert forbid_check.status_code == 403
    assert forbid_check.json()["detail"]["authorized"] is False

    # 7. GET /api/v1/audit/privacy/access-logs
    access_logs = client.get("/api/v1/audit/privacy/access-logs")
    assert access_logs.status_code == 200
    assert access_logs.json()["count"] >= 2

    # 8. GET /api/v1/audit/privacy/permissions
    perm_res = client.get("/api/v1/audit/privacy/permissions")
    assert perm_res.status_code == 200
    assert "PATIENT_INFO" in perm_res.json()["protected_resources"]

    # 9. GET /api/v1/audit/categories
    cat_res = client.get("/api/v1/audit/categories")
    assert cat_res.status_code == 200
    assert "DISPUTE_INVESTIGATION" in cat_res.json()["audit_objectives"]
