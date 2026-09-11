"""
Tests for Section 5.39 — Human Escalation.

Verifies:
1. Trigger escalation — record persisted with ESCALATED status and ESC- ticket ID
2. Get escalation context — authorized_context_json present for operator handoff
3. Resolve escalation — RESOLVED status + resolved_at populated
4. List escalation records — filter by status works correctly
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.config import get_db
from app.database.models import Base


# ---------------------------------------------------------------------------
# Test DB setup (StaticPool pattern)
# ---------------------------------------------------------------------------
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
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
# Helper: trigger a standard escalation
# ---------------------------------------------------------------------------
def _trigger(client, session_id="sess-test-001", trigger_reason="PATIENT_REQUESTED",
             hospital_id=None, failure_count=2):
    payload = {
        "session_id": session_id,
        "trigger_reason": trigger_reason,
        "hospital_id": hospital_id,
        "failure_count": failure_count,
        "context_snapshot": {
            "patient_intent": "Book cardiology appointment",
            "conversation_summary": "Patient asked multiple times and booking failed",
            "actions_attempted": ["SEARCH_DOCTORS", "CHECK_AVAILABILITY", "CREATE_APPOINTMENT"],
            "last_error": "EHR timeout after 3 retries",
            "patient_info": {"name": "John Doe", "phone": "+1-555-0100"}
        }
    }
    return client.post("/api/v1/escalation/trigger", json=payload)


# ---------------------------------------------------------------------------
# Test 1: Trigger escalation — record created with correct fields
# ---------------------------------------------------------------------------
def test_trigger_escalation(client):
    response = _trigger(client)
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["escalation_id"].startswith("ESC-"), f"Unexpected ticket format: {data['escalation_id']}"
    assert data["resolution_status"] == "ESCALATED"
    assert data["trigger_reason"] == "PATIENT_REQUESTED"
    assert data["failure_count"] == 2
    assert data["session_id"] == "sess-test-001"
    assert "Ticket: ESC-" in data["message"]


# ---------------------------------------------------------------------------
# Test 2: Get escalation context — authorized context for operator handoff
# ---------------------------------------------------------------------------
def test_get_escalation_context(client):
    trigger_resp = _trigger(client, session_id="sess-ctx-002", trigger_reason="EHR_INTEGRATION_FAILURE", failure_count=3)
    assert trigger_resp.status_code == 200
    escalation_id = trigger_resp.json()["escalation_id"]

    context_resp = client.get(f"/api/v1/escalation/{escalation_id}/context")
    assert context_resp.status_code == 200, context_resp.text

    ctx = context_resp.json()
    assert ctx["escalation_id"] == escalation_id
    assert ctx["trigger_reason"] == "EHR_INTEGRATION_FAILURE"
    assert ctx["resolution_status"] == "ESCALATED"
    assert ctx["resolved_at"] is None

    # Authorized context for operator must contain patient intent and guidance
    authorized = ctx["authorized_context"]
    assert "patient_intent" in authorized
    assert authorized["patient_intent"] == "Book cardiology appointment"
    assert "operator_guidance" in authorized
    assert "EHR" in authorized["operator_guidance"]


# ---------------------------------------------------------------------------
# Test 3: Resolve escalation — resolved_at populated and status updated
# ---------------------------------------------------------------------------
def test_resolve_escalation(client):
    trigger_resp = _trigger(client, session_id="sess-resolve-003", trigger_reason="BOOKING_SYSTEM_FAILURE")
    assert trigger_resp.status_code == 200
    escalation_id = trigger_resp.json()["escalation_id"]

    resolve_resp = client.post(
        f"/api/v1/escalation/{escalation_id}/resolve",
        json={
            "resolution_status": "RESOLVED",
            "operator_id": "operator-007",
            "operator_notes": "Booked manually via hospital portal."
        }
    )
    assert resolve_resp.status_code == 200, resolve_resp.text

    res = resolve_resp.json()
    assert res["resolution_status"] == "RESOLVED"
    assert res["operator_id"] == "operator-007"
    assert res["resolved_at"] is not None
    assert "RESOLVED" in res["message"]


# ---------------------------------------------------------------------------
# Test 4: List escalation records — filter by status
# ---------------------------------------------------------------------------
def test_list_escalation_records_with_filter(client):
    # Trigger 2 escalations
    r1 = _trigger(client, session_id="sess-list-a", trigger_reason="PATIENT_REQUESTED")
    r2 = _trigger(client, session_id="sess-list-b", trigger_reason="SAFETY_POLICY")
    assert r1.status_code == 200
    assert r2.status_code == 200

    esc_id_b = r2.json()["escalation_id"]

    # Resolve only the second one
    client.post(
        f"/api/v1/escalation/{esc_id_b}/resolve",
        json={"resolution_status": "RESOLVED"}
    )

    # List all — expect 2
    all_resp = client.get("/api/v1/escalation/records")
    assert all_resp.status_code == 200
    all_data = all_resp.json()
    assert all_data["total"] == 2

    # List ESCALATED only — expect 1
    esc_resp = client.get("/api/v1/escalation/records?status=ESCALATED")
    assert esc_resp.status_code == 200
    esc_data = esc_resp.json()
    assert esc_data["total"] == 1
    assert esc_data["escalation_records"][0]["session_id"] == "sess-list-a"

    # List RESOLVED only — expect 1
    res_resp = client.get("/api/v1/escalation/records?status=RESOLVED")
    assert res_resp.status_code == 200
    res_data = res_resp.json()
    assert res_data["total"] == 1
    assert res_data["escalation_records"][0]["session_id"] == "sess-list-b"
