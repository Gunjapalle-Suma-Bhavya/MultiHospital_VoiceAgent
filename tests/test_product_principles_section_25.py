"""
Unit Test Suite for Section 25: Product Principles.
Validates all 16 canonical principles, metadata, compliance targets, and evaluation endpoints.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database.models import Base
from app.vision import ProductPrinciplesService, PRODUCT_PRINCIPLES_REGISTRY
from app.main import app
from app.database.config import get_db

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
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


def test_25_all_16_principles_present():
    registry = ProductPrinciplesService.get_principles_registry()
    assert len(registry) == 16

    expected_titles = [
        "Real availability over AI assumptions",
        "Ask rather than guess",
        "AI coordinates; clinicians decide",
        "Hospitals own their configuration",
        "Doctors control their time",
        "Patient experience should be conversational",
        "External healthcare-system actions must be verifiable",
        "Every important action should be traceable",
        "Tenant isolation is mandatory",
        "Clinician-approved questions",
        "Context should improve the experience",
        "Background work should not block conversations unnecessarily",
        "Failures should be recoverable",
        "AI actions should be measurable",
        "Operational visibility is part of the product",
        "External state should be treated as authoritative where applicable"
    ]

    registry_titles = [p["title"] for p in registry]
    for exp in expected_titles:
        assert exp in registry_titles

    for p in registry:
        assert "id" in p and 1 <= p["id"] <= 16
        assert "description" in p and len(p["description"]) > 0
        assert "subsystems" in p and len(p["subsystems"]) > 0
        assert "compliance_target" in p


def test_25_compliance_evaluation_service(setup_db):
    db = setup_db
    audit = ProductPrinciplesService.evaluate_all_principles(db)
    assert audit["title"] == "PLATFORM PRODUCT PRINCIPLES COMPLIANCE AUDIT (SECTION 25)"
    assert audit["principles_count"] == 16
    assert audit["all_principles_compliant"] is True
    assert audit["overall_compliance_score_percent"] >= 95.0

    for p in audit["principles"]:
        assert p["status"] == "COMPLIANT"
        assert p["verified"] is True
        assert p["compliance_score_percent"] >= 90.0


def test_25_rest_api_endpoints(client, setup_db):
    # 1. GET /api/v1/principles
    get_resp = client.get("/api/v1/principles")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["count"] == 16
    assert len(data["principles"]) == 16

    # 2. POST /api/v1/principles/audit
    post_resp = client.post("/api/v1/principles/audit")
    assert post_resp.status_code == 200
    audit_data = post_resp.json()
    assert audit_data["principles_count"] == 16
    assert audit_data["all_principles_compliant"] is True
