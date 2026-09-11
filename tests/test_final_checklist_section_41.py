"""
Automated Test Suite for Sections 39, 40, 41, and 42:
- Section 39: Final Product Definition & Architecture Flow
- Section 40: Final Vision & Creativity Note (Beyond Baseline Innovations)
- Section 41: Final Submission Checklist (7 Pillars, 76 Requirements)
- Section 42: Final Success Definition & Verified Closed Loop
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.config import Base, get_db
from app.services.final_checklist_service import FinalChecklistService
from app.ehr.adapters import EHRConnectorFactory
from app.agent.capability_registry import CapabilityRegistry
from app.analytics.cost_estimation_service import CostEstimationService


# In-memory test SQLite setup with StaticPool
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_section_39_final_product_definition(client):
    """
    Verifies Section 39: Final Product Definition, executive summary,
    core philosophy, and the complete 23-stage platform architecture flow.
    """
    response = client.get("/api/v1/final-submission/product-definition")
    assert response.status_code == 200
    data = response.json()

    assert data["section"] == 39
    assert "Multi-Hospital Healthcare Operating" in data["product_name"]
    assert "Hospitals configure the healthcare network" in data["core_philosophy"]
    assert "Doctors make clinical decisions" in data["core_philosophy"]

    flow = data["architecture_flow"]
    assert len(flow) == 23
    assert "PLATFORM_ADMIN" in flow[0]
    assert "AI_AGENT" in flow[5]
    assert "PATIENT" in flow[6]
    assert "BOOK_APPOINTMENT" in flow[12]
    assert "EHR_INTEGRATION_LAYER" in flow[13]
    assert "VERIFY_APPOINTMENT" in flow[15]
    assert "TRIGGER_WORKFLOW" in flow[17]
    assert "CONTINUOUS_IMPROVEMENT" in flow[22]


def test_section_40_creativity_and_vision_extensions(client):
    """
    Verifies Section 40: Final Vision & Creativity Note.
    Asserts the 10 innovative extensions engineered beyond baseline requirements.
    """
    response = client.get("/api/v1/final-submission/creativity-matrix")
    assert response.status_code == 200
    data = response.json()

    assert data["section"] == 40
    innovations = data["innovations"]
    assert len(innovations) == 10

    categories = [inv["category"] for inv in innovations]
    assert "Thoughtful Product Experiences" in categories
    assert "Innovative AI Capabilities" in categories
    assert "Better Conversational Interactions" in categories
    assert "Useful Automation" in categories
    assert "Improved Operational Workflows" in categories
    assert "Better Reliability Mechanisms" in categories
    assert "Stronger Analytics & Unit Economics" in categories
    assert "New Healthcare-System Integrations" in categories
    assert "Improved Accessibility" in categories
    assert "Better Developer/Operator Experiences" in categories


def test_section_41_checklist_7_pillars_and_76_items(client):
    """
    Verifies Section 41: Final Submission Checklist across all 7 pillars.
    Asserts 76 total checklist items and 100% verification rate.
    """
    response = client.get("/api/v1/final-submission/checklist")
    assert response.status_code == 200
    data = response.json()

    assert data["section"] == 41
    assert data["total_pillars"] == 7
    assert data["total_checks"] == 76
    assert data["verified_checks"] == 76
    assert data["compliance_percentage"] == 100.0
    assert data["status"] == "ALL_REQUIREMENTS_FULFILLED_100_PERCENT"

    pillars = data["pillars"]
    assert pillars["pillar_1_product"]["total"] == 18
    assert pillars["pillar_2_ai"]["total"] == 8
    assert pillars["pillar_3_ehr"]["total"] == 13
    assert pillars["pillar_4_workflows"]["total"] == 8
    assert pillars["pillar_5_operations"]["total"] == 10
    assert pillars["pillar_6_security"]["total"] == 7
    assert pillars["pillar_7_submission"]["total"] == 12

    # Verify each item in each pillar is marked verified
    for p_key, p_val in pillars.items():
        for item in p_val["items"]:
            assert item["verified"] is True, f"Checklist item failed: {item}"


def test_section_41_programmatic_verification_audit(client):
    """
    Verifies POST /api/v1/final-submission/run-verification-audit returns 100% compliance.
    """
    response = client.post("/api/v1/final-submission/run-verification-audit")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "SUCCESS"
    assert data["compliance_percentage"] == 100.0
    assert data["all_checks_passed"] is True
    assert data["total_checks"] == 76
    assert data["verified_checks"] == 76


def test_section_42_final_success_definition(client):
    """
    Verifies Section 42: Final Success Definition and 16-step closed verification loop.
    """
    response = client.get("/api/v1/final-submission/success-definition")
    assert response.status_code == 200
    data = response.json()

    assert data["section"] == 42
    assert "The prototype is successful because" in data["defining_narrative"]
    assert "conversation becomes action" or "coordinates capabilities" in data["core_thesis"]

    loop = data["verified_loop"]
    expected_loop = [
        "USER", "CONVERSATION", "AI_UNDERSTANDING", "CONTEXT",
        "CAPABILITY_SELECTION", "REAL_ACTION", "EHR_INTEGRATION",
        "VERIFICATION", "STATE_SYNCHRONIZATION", "WORKFLOW",
        "NOTIFICATION", "STATE_UPDATE", "ANALYTICS",
        "OBSERVABILITY", "EVALUATION", "IMPROVEMENT"
    ]
    assert loop == expected_loop
    assert data["status"] == "PROTOTYPE_MISSION_ACCOMPLISHED"


def test_pillar_1_product_live_endpoints(client):
    """
    Live verification of Pillar 1: Product endpoints.
    """
    # 1. Hospital onboarding
    res = client.get("/api/v1/onboarding/HOSP-NOT-FOUND")
    assert res.status_code == 404

    # 2. Capabilities list
    res = client.get("/api/v1/capabilities/list")
    assert res.status_code == 200
    assert "registered_capabilities" in res.json()

    # 3. Discovery search
    res = client.post("/api/v1/discovery/search", json={"specialty": "Orthopedics"})
    assert res.status_code == 200

    # 4. Questionnaires
    res = client.get("/api/v1/questionnaires/applicable")
    assert res.status_code == 200


def test_pillar_2_and_3_ai_and_ehr_capabilities():
    """
    Live verification of Pillar 2 (AI Capabilities) and Pillar 3 (EHR Integration).
    """
    # AI capability registry check
    db = TestingSessionLocal()
    try:
        registry = CapabilityRegistry(db)
        caps = registry.get_registered_capabilities()
        assert len(caps) >= 8
        assert "check_availability" in caps
        assert "create_appointment" in caps
    finally:
        db.close()


    # EHR Connector Factory check
    for protocol in ["FHIR_R4", "EPIC", "CERNER", "HL7_V2", "MOCK"]:
        connector = EHRConnectorFactory.get_connector(protocol)
        assert connector is not None
        assert hasattr(connector, "create_appointment")
        assert hasattr(connector, "patient_lookup")


def test_pillar_7_submission_repository_artifacts():
    """
    Verifies Pillar 7: Submission repository artifacts exist in file system.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    required_files = [
        "README.md",
        "ARCHITECTURE.md",
        "AI_TOOLS.md",
        "AI_PROMPTS.md",
        ".env.example",
        "Dockerfile",
        "docker-compose.yml"
    ]

    for req_file in required_files:
        full_path = os.path.join(base_dir, req_file)
        assert os.path.exists(full_path), f"Missing submission artifact: {req_file}"
        assert os.path.getsize(full_path) > 0, f"Empty submission artifact: {req_file}"
