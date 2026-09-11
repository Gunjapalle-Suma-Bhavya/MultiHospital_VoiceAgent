"""
Tests for Section 18 (AI Safety Principles) and Section 19 (Approved Knowledge & Information Retrieval).
"""

from fastapi.testclient import TestClient
from app.main import app
from app.safety.ai_safety import ai_safety_engine, CapabilitySafetyStatus
from app.knowledge.approved_knowledge import approved_knowledge_engine, InformationDomain, KnowledgeCategory

client = TestClient(app)


# =========================================================================
# SECTION 18: AI SAFETY PRINCIPLES TESTS
# =========================================================================

def test_section_18_allowed_capabilities():
    """
    Verifies all 12 allowed administrative and conversational healthcare capabilities.
    """
    allowed_list = [
        "appointment_discovery",
        "scheduling",
        "rescheduling",
        "cancellation",
        "administrative_faqs",
        "approved_pre_visit_questions",
        "recording_patient_responses",
        "workflow_initiation",
        "notifications",
        "ehr_appointment_operations",
        "external_system_synchronization",
        "escalation"
    ]
    for cap in allowed_list:
        eval_res = ai_safety_engine.evaluate_capability(cap)
        assert eval_res["is_allowed"] is True
        assert eval_res["status"] == CapabilitySafetyStatus.ALLOWED.value


def test_section_18_prohibited_non_autonomous_clinical_capabilities():
    """
    Verifies strict blocking of clinical decision autonomy (diagnosis, prescriptions, treatments).
    """
    prohibited_list = [
        "diagnosis",
        "treatment_decisions",
        "medication_changes",
        "medical_prescriptions",
        "independent_clinical_assessments"
    ]
    for cap in prohibited_list:
        eval_res = ai_safety_engine.evaluate_capability(cap)
        assert eval_res["is_allowed"] is False
        assert eval_res["status"] == CapabilitySafetyStatus.PROHIBITED_CLINICAL.value
        assert "licensed clinical autonomy" in eval_res["reason"]


def test_section_18_patient_query_inspection_and_clinical_redirection():
    """
    Ensures clinical questions are detected and redirected to physician scheduling.
    """
    # Prohibited diagnosis request
    diag_res = ai_safety_engine.inspect_patient_query("Can you diagnose me? I have chest tightness.")
    assert diag_res["is_safe"] is False
    assert diag_res["violation"] == "DIAGNOSIS"
    assert "cannot provide a medical diagnosis" in diag_res["safe_response"]

    # Prohibited prescription request
    rx_res = ai_safety_engine.inspect_patient_query("Please prescribe me amoxicillin for my sore throat.")
    assert rx_res["is_safe"] is False
    assert rx_res["violation"] == "MEDICAL_PRESCRIPTION"

    # Prohibited medication change request
    med_res = ai_safety_engine.inspect_patient_query("Should I increase my dosage of lisinopril?")
    assert med_res["is_safe"] is False
    assert med_res["violation"] == "MEDICATION_CHANGE"

    # Safe administrative scheduling request
    safe_res = ai_safety_engine.inspect_patient_query("I want to book an appointment with Dr. Sharma for Thursday.")
    assert safe_res["is_safe"] is True
    assert safe_res["violation"] is None


def test_section_18_patient_reported_framing_vs_diagnostic_implication():
    """
    Strict Rule: AI must clearly distinguish 'You reported...' from 'You have...'.
    """
    # Diagnostic implication detected and reframed
    bad_phrase = "Based on our conversation, you have asthma and need an inhaler."
    framing_res = ai_safety_engine.enforce_patient_reported_framing(bad_phrase)
    assert framing_res["is_compliant"] is False
    assert framing_res["diagnostic_implication_detected"] is True
    assert "you reported asthma" in framing_res["reframed_text"]

    # Compliant patient-reported statement
    good_phrase = "You reported persistent cough for two weeks."
    framing_good = ai_safety_engine.enforce_patient_reported_framing(good_phrase)
    assert framing_good["is_compliant"] is True
    assert framing_good["diagnostic_implication_detected"] is False


# =========================================================================
# SECTION 19: APPROVED KNOWLEDGE & INFORMATION RETRIEVAL TESTS
# =========================================================================

def test_section_19_approved_knowledge_grounding_and_citations():
    """
    Verifies institutional knowledge retrieval returns grounded facts with citations across 6 categories:
    Visiting hours, department locations, preparation, policies, parking, and FAQs.
    """
    # 1. Visiting hours
    vh_res = approved_knowledge_engine.query_approved_knowledge("What are the hospital visiting hours?")
    assert vh_res["success"] is True
    assert vh_res["grounded"] is True
    assert vh_res["category"] == KnowledgeCategory.VISITING_HOURS.value
    assert len(vh_res["citations"]) > 0
    assert "Source: Hospital Operations Manual" in vh_res["response"]

    # 2. Parking info
    pk_res = approved_knowledge_engine.query_approved_knowledge("Where is the parking garage?")
    assert pk_res["success"] is True
    assert pk_res["grounded"] is True
    assert pk_res["category"] == KnowledgeCategory.PARKING_INFORMATION.value

    # 3. Department location
    loc_res = approved_knowledge_engine.query_approved_knowledge("Where is cardiology department?")
    assert loc_res["success"] is True
    assert loc_res["category"] == KnowledgeCategory.DEPARTMENT_LOCATIONS.value


def test_section_19_distinguish_administrative_info_from_medical_advice():
    """
    Strict Rule: System must distinguish administrative info from medical advice.
    Medical advice queries are rejected with referrals.
    """
    med_query = "What should I take for high fever and is this dangerous?"
    med_res = approved_knowledge_engine.query_approved_knowledge(med_query)
    assert med_res["success"] is False
    assert med_res["is_medical_advice"] is True
    assert "consult a physician" in med_res["response"]


def test_section_19_avoids_unsupported_claims():
    """
    If knowledge is not in approved organizational documents, AI avoids unsupported claims.
    """
    unsupported_query = "Does the hospital cafeteria serve authentic wood-fired Neapolitan pizza at 3 AM?"
    res = approved_knowledge_engine.query_approved_knowledge(unsupported_query)
    assert res["success"] is True
    assert res["grounded"] is False
    assert res.get("unsupported_claim_avoided") is True
    assert "do not have approved organizational documentation" in res["response"]


def test_safety_and_knowledge_api_endpoints():
    """
    Verifies FastAPI REST endpoints for Sections 18 & 19.
    """
    # 1. Evaluate Capability
    c_res = client.post("/api/v1/safety-knowledge/evaluate-capability", json={"capability_name": "medication_changes"})
    assert c_res.status_code == 200
    assert c_res.json()["is_allowed"] is False

    # 2. Inspect Query
    q_res = client.post("/api/v1/safety-knowledge/inspect-query", json={"query_text": "What is my diagnosis for fatigue?"})
    assert q_res.status_code == 200
    assert q_res.json()["is_safe"] is False

    # 3. Check Framing
    f_res = client.post("/api/v1/safety-knowledge/check-patient-framing", json={"statement_text": "You have hypertension."})
    assert f_res.status_code == 200
    assert f_res.json()["diagnostic_implication_detected"] is True

    # 4. Query Knowledge
    k_res = client.post("/api/v1/safety-knowledge/query-knowledge", json={"query": "visiting hours"})
    assert k_res.status_code == 200
    assert k_res.json()["grounded"] is True
