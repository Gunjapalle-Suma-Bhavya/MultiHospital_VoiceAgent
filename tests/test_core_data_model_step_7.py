"""
Tests for Step 7 — Core Data Model.

Verifies:
1. Canonical 22-entity hierarchical domain tree structure matching Step 7 specifications.
2. Live database count population across all entity nodes.
3. Entity schema catalog introspection (tables, columns, primary/foreign keys).
4. Relational integrity diagnostics & orphan detection (valid vs. corrupted relationships).
5. Baseline demonstration dataset seeding across the full hierarchy.
6. All Core Data Model REST API endpoints (/tree, /entities, /stats, /validate, /seed-demo).
"""

import pytest
from datetime import datetime, timezone, timedelta, time
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.config import get_db
from app.database.models import Base, Hospital, Doctor, Appointment, DoctorCalendar, BlockedSlot
from app.core_models import CORE_DATA_MODEL_TREE
from app.core_models.data_model_service import DataModelService


# ---------------------------------------------------------------------------
# Test Database Setup
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


# ---------------------------------------------------------------------------
# 1. Structural Verification: 22 Canonical Entities in Hierarchy
# ---------------------------------------------------------------------------
def test_core_data_model_tree_structure():
    """Verify root Platform and primary branches match the specification."""
    assert CORE_DATA_MODEL_TREE["name"] == "Platform"
    assert CORE_DATA_MODEL_TREE["entity"] == "Platform"

    child_names = [c["name"] for c in CORE_DATA_MODEL_TREE["children"]]
    expected_primary = [
        "Hospital",
        "Patient",
        "Appointment",
        "Questionnaire",
        "Questionnaire Response",
        "AI Conversation",
        "AI Context",
        "Capability",
        "Capability Execution",
        "EHR Integration Operation",
        "Integration Verification",
        "Reconciliation Record",
        "Workflow",
        "Workflow Execution",
        "Notification",
        "AI Evaluation",
        "Audit Event",
        "Operational Event",
    ]
    for name in expected_primary:
        assert name in child_names, f"Expected primary entity '{name}' not found in root children."


def test_hospital_and_doctor_sub_hierarchy():
    """Verify Hospital sub-nodes (Admin, Dept, Specialty, Doctor, EHR, Appts)."""
    hospital_node = next(c for c in CORE_DATA_MODEL_TREE["children"] if c["name"] == "Hospital")
    hosp_child_names = [c["name"] for c in hospital_node["children"]]

    expected_hosp_children = [
        "Hospital Admin",
        "Department",
        "Specialty",
        "Doctor",
        "Healthcare System Connection",
        "Appointments",
    ]
    for ch in expected_hosp_children:
        assert ch in hosp_child_names, f"Missing Hospital sub-node '{ch}'"

    # Verify Doctor sub-nodes
    doc_node = next(c for c in hospital_node["children"] if c["name"] == "Doctor")
    doc_child_names = [c["name"] for c in doc_node["children"]]
    expected_doc_children = ["Calendar", "Availability", "Blocked Slots", "Questionnaire"]
    for ch in expected_doc_children:
        assert ch in doc_child_names, f"Missing Doctor sub-node '{ch}'"

    # Verify Healthcare System Connection sub-nodes
    conn_node = next(c for c in hospital_node["children"] if c["name"] == "Healthcare System Connection")
    conn_child_names = [c["name"] for c in conn_node["children"]]
    expected_conn_children = ["Connector", "Configuration", "Identifier Mappings", "Integration Status"]
    for ch in expected_conn_children:
        assert ch in conn_child_names, f"Missing Connection sub-node '{ch}'"


def test_patient_and_appointment_sub_hierarchy():
    """Verify Patient and Appointment sub-nodes."""
    patient_node = next(c for c in CORE_DATA_MODEL_TREE["children"] if c["name"] == "Patient")
    pat_child_names = [c["name"] for c in patient_node["children"]]
    assert "External Patient Mapping" in pat_child_names
    assert "User Context" in pat_child_names

    ctx_node = next(c for c in patient_node["children"] if c["name"] == "User Context")
    ctx_child_names = [c["name"] for c in ctx_node["children"]]
    expected_ctx = ["Preferences", "Conversation Summaries", "Relevant Interaction Context"]
    for ch in expected_ctx:
        assert ch in ctx_child_names, f"Missing User Context sub-node '{ch}'"

    appt_node = next(c for c in CORE_DATA_MODEL_TREE["children"] if c["name"] == "Appointment")
    appt_child_names = [c["name"] for c in appt_node["children"]]
    expected_appt = ["Doctor", "Hospital", "Calendar", "Slot", "External Appointment ID", "Questionnaire Responses"]
    for ch in expected_appt:
        assert ch in appt_child_names, f"Missing Appointment sub-node '{ch}'"


# ---------------------------------------------------------------------------
# 2. Service Layer: Live Tree, Catalog, Stats & Seeding
# ---------------------------------------------------------------------------
def test_data_model_service_live_counts(setup_db):
    """Verify live count annotation across entities."""
    svc = DataModelService(setup_db)
    initial_tree = svc.get_hierarchical_tree()
    assert initial_tree["name"] == "Platform"
    assert initial_tree["live_count"] == 0

    # Seed baseline demo
    seed_res = svc.seed_demo_hierarchy()
    assert seed_res["status"] == "success"

    # Tree should now reflect seeded records
    updated_tree = svc.get_hierarchical_tree()
    assert updated_tree["live_count"] >= 1  # Platform record seeded

    hosp_node = next(c for c in updated_tree["children"] if c["name"] == "Hospital")
    assert hosp_node["live_count"] >= 1

    doc_node = next(c for c in hosp_node["children"] if c["name"] == "Doctor")
    assert doc_node["live_count"] >= 1


def test_data_model_service_catalog(setup_db):
    """Verify entity schema introspection returns table and column definitions."""
    svc = DataModelService(setup_db)
    catalog = svc.get_entity_catalog()
    assert len(catalog) > 10

    entity_names = [e["name"] for e in catalog]
    model_names = [e["model"] for e in catalog]
    assert "Platform" in entity_names
    assert "Hospital" in entity_names
    assert "Doctor" in entity_names
    assert "Appointment" in model_names
    assert "Department" in entity_names
    assert "Specialty" in entity_names

    # Check Doctor entity details
    doc_meta = next(e for e in catalog if e["name"] == "Doctor")
    assert doc_meta["table"] == "doctors"
    col_names = [col["name"] for col in doc_meta["columns"]]
    assert "id" in col_names
    assert "hospital_id" in col_names
    assert "name" in col_names
    assert "specialty" in col_names


def test_data_model_service_stats(setup_db):
    """Verify flat database statistics dictionary."""
    svc = DataModelService(setup_db)
    stats_before = svc.get_database_stats()
    assert stats_before["total_entities_tracked"] >= 20

    svc.seed_demo_hierarchy()
    stats_after = svc.get_database_stats()
    assert stats_after["stats"]["Hospital"]["count"] >= 1
    assert stats_after["stats"]["Doctor"]["count"] >= 1
    assert stats_after["stats"]["Patient"]["count"] >= 1
    assert stats_after["stats"]["Appointment"]["count"] >= 1


# ---------------------------------------------------------------------------
# 3. Relational Integrity & Orphan Diagnostics
# ---------------------------------------------------------------------------
def test_relational_integrity_clean_database(setup_db):
    """A clean or properly seeded database should pass all integrity checks."""
    svc = DataModelService(setup_db)
    svc.seed_demo_hierarchy()

    res = svc.validate_relational_integrity()
    assert res["is_valid"] is True
    assert res["issues_count"] == 0
    assert len(res["issues"]) == 0
    assert len(res["checks_run"]) == 4


def test_relational_integrity_detects_orphan_doctor(setup_db):
    """An orphan doctor pointing to an invalid hospital must trigger diagnostic error."""
    orphan_doc = Doctor(
        hospital_id="NON-EXISTENT-HOSPITAL-UUID",
        name="Dr. Rogue Orphan",
        specialty="General Medicine",
        is_active=True,
    )
    setup_db.add(orphan_doc)
    setup_db.commit()

    svc = DataModelService(setup_db)
    res = svc.validate_relational_integrity()
    assert res["is_valid"] is False
    assert res["issues_count"] >= 1
    assert any("doctor(s) referencing non-existent hospital IDs" in err for err in res["issues"])


def test_relational_integrity_detects_orphan_calendar(setup_db):
    """An orphan calendar referencing a fake doctor ID must trigger diagnostic error."""
    orphan_cal = DoctorCalendar(
        doctor_id="FAKE-DOC-999",
        calendar_name="Phantom Calendar",
    )
    setup_db.add(orphan_cal)
    setup_db.commit()

    svc = DataModelService(setup_db)
    res = svc.validate_relational_integrity()
    assert res["is_valid"] is False
    assert any("calendar(s) referencing non-existent doctor IDs" in err for err in res["issues"])


# ---------------------------------------------------------------------------
# 4. REST API Endpoint Tests
# ---------------------------------------------------------------------------
def test_api_get_tree(client):
    """GET /api/v1/core-data-model/tree returns full hierarchy."""
    res = client.get("/api/v1/core-data-model/tree")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Platform"
    assert "children" in data
    assert len(data["children"]) >= 15


def test_api_get_entities(client):
    """GET /api/v1/core-data-model/entities returns entity schemas."""
    res = client.get("/api/v1/core-data-model/entities")
    assert res.status_code == 200
    data = res.json()
    assert "count" in data
    assert "entities" in data
    assert data["count"] > 10


def test_api_get_stats(client):
    """GET /api/v1/core-data-model/stats returns tracked entity statistics."""
    res = client.get("/api/v1/core-data-model/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_entities_tracked" in data
    assert "stats" in data


def test_api_validate(client):
    """POST /api/v1/core-data-model/validate runs integrity diagnostics."""
    res = client.post("/api/v1/core-data-model/validate")
    assert res.status_code == 200
    data = res.json()
    assert "is_valid" in data
    assert "checks_run" in data


def test_api_seed_demo_and_verify_tree(client):
    """POST /api/v1/core-data-model/seed-demo seeds entities and updates tree counts."""
    res = client.post("/api/v1/core-data-model/seed-demo")
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "success"
    assert "hospital_id" in data
    assert "doctor_id" in data

    # Verify counts in tree
    tree_res = client.get("/api/v1/core-data-model/tree")
    assert tree_res.status_code == 200
    tree_data = tree_res.json()
    assert tree_data["live_count"] >= 1
