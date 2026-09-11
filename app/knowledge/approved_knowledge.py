"""
Approved Knowledge & Information Retrieval Engine (Section 19).

Knowledge system capabilities:
1. Retrieve approved information from verified organizational sources:
   - Hospital visiting hours
   - Department locations
   - Appointment preparation instructions
   - Hospital policies
   - Parking information
   - General administrative FAQs
2. Provide grounded responses backed by citations.
3. Identify the source where appropriate.
4. Avoid unsupported claims.
5. Strict distinction:
   - Administrative information (Allowed & Grounded)
   - Medical advice (Prohibited / Escalated)
"""

import re
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel


class InformationDomain(str, Enum):
    ADMINISTRATIVE = "ADMINISTRATIVE"
    MEDICAL_ADVICE = "MEDICAL_ADVICE"


class KnowledgeCategory(str, Enum):
    VISITING_HOURS = "VISITING_HOURS"
    DEPARTMENT_LOCATIONS = "DEPARTMENT_LOCATIONS"
    APPOINTMENT_PREPARATION = "APPOINTMENT_PREPARATION"
    HOSPITAL_POLICIES = "HOSPITAL_POLICIES"
    PARKING_INFORMATION = "PARKING_INFORMATION"
    ADMINISTRATIVE_FAQS = "ADMINISTRATIVE_FAQS"


class KnowledgeDocument(BaseModel):
    doc_id: str
    hospital_id: str
    category: KnowledgeCategory
    title: str
    content: str
    source_citation: str
    is_approved_by_org: bool = True


class ApprovedKnowledgeEngine:
    """
    RAG & Knowledge Retrieval for Approved Institutional Healthcare Sources.
    """

    def __init__(self):
        self._knowledge_base: Dict[str, List[KnowledgeDocument]] = {}
        self._seed_default_knowledge()

    def _seed_default_knowledge(self):
        default_docs = [
            KnowledgeDocument(
                doc_id="KB-VH-01",
                hospital_id="ALL_HOSPITALS",
                category=KnowledgeCategory.VISITING_HOURS,
                title="General Inpatient Visiting Hours",
                content="Standard visiting hours are 8:00 AM to 8:00 PM daily. ICU visiting is restricted to immediate family from 10:00 AM to 12:00 PM and 5:00 PM to 7:00 PM.",
                source_citation="Hospital Operations Manual 2026, Section 3.1"
            ),
            KnowledgeDocument(
                doc_id="KB-LOC-01",
                hospital_id="ALL_HOSPITALS",
                category=KnowledgeCategory.DEPARTMENT_LOCATIONS,
                title="Cardiology & Outpatient Clinics",
                content="The Cardiology Department is located on Floor 2, Wing B. The Diagnostic Imaging Center is on the Ground Floor.",
                source_citation="Hospital Directory & Campus Map, Updated August 2026"
            ),
            KnowledgeDocument(
                doc_id="KB-PREP-01",
                hospital_id="ALL_HOSPITALS",
                category=KnowledgeCategory.APPOINTMENT_PREPARATION,
                title="Appointment Preparation & Fasting Guidelines",
                content="Please arrive 15 minutes before your scheduled appointment with government-issued photo ID and insurance card. Fasting blood work requires 8 hours of water-only fasting.",
                source_citation="Patient Intake Protocol, Clinical Administrative Guidelines"
            ),
            KnowledgeDocument(
                doc_id="KB-POL-01",
                hospital_id="ALL_HOSPITALS",
                category=KnowledgeCategory.HOSPITAL_POLICIES,
                title="Cancellation & Visitor Masking Policy",
                content="Appointments may be rescheduled or cancelled up to 24 hours in advance without fee. Masks are required in all oncology and immunocompromised patient wings.",
                source_citation="Infection Control Policy 2026-B"
            ),
            KnowledgeDocument(
                doc_id="KB-PARK-01",
                hospital_id="ALL_HOSPITALS",
                category=KnowledgeCategory.PARKING_INFORMATION,
                title="Visitor & Patient Parking Facilities",
                content="Multi-level parking is available in Garage A adjacent to the Main Entrance. The first 30 minutes are complimentary, with validated flat-rate parking for clinic patients.",
                source_citation="Facilities & Campus Logistics Guide"
            ),
            KnowledgeDocument(
                doc_id="KB-FAQ-01",
                hospital_id="ALL_HOSPITALS",
                category=KnowledgeCategory.ADMINISTRATIVE_FAQS,
                title="Health Insurance & Billing Assistance",
                content="We accept major PPO, HMO, and Medicare plans. Financial counseling and estimate inquiries are available at the Central Billing Desk on Floor 1.",
                source_citation="Patient Accounts & Billing Department"
            )
        ]
        self._knowledge_base["ALL_HOSPITALS"] = default_docs

    def classify_information_domain(self, query: str) -> InformationDomain:
        """
        Crucial Section 19 Requirement:
        The system must distinguish Administrative Information from Medical Advice.
        """
        lowered = query.lower()
        medical_advice_indicators = [
            "should i take", "cure", "remedy", "what is wrong with me",
            "is this dangerous", "side effects of my medication", "how to treat",
            "clinical advice", "dose"
        ]
        for ind in medical_advice_indicators:
            if ind in lowered:
                return InformationDomain.MEDICAL_ADVICE

        return InformationDomain.ADMINISTRATIVE

    def query_approved_knowledge(
        self,
        query: str,
        hospital_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves approved institutional knowledge, grounds the response,
        identifies sources, and rejects medical advice queries.
        """
        domain = self.classify_information_domain(query)

        # 1. Distinguish: If Medical Advice, reject and refer to doctor
        if domain == InformationDomain.MEDICAL_ADVICE:
            return {
                "success": False,
                "domain": domain.value,
                "is_medical_advice": True,
                "grounded": False,
                "response": (
                    "This inquiry pertains to medical advice or clinical evaluation. "
                    "As an administrative assistant, I can only provide approved hospital logistics and appointment scheduling. "
                    "Please consult a physician for clinical recommendations."
                ),
                "citations": []
            }

        # 2. Administrative search in approved knowledge base
        lowered_q = query.lower()
        stopwords = {"what", "are", "the", "is", "where", "for", "a", "an", "at", "in", "to", "and", "does", "do", "hospital"}
        query_tokens = [w for w in re.findall(r"\w+", lowered_q) if w not in stopwords and len(w) > 2]

        hosp_key = hospital_id or "ALL_HOSPITALS"
        docs = self._knowledge_base.get("ALL_HOSPITALS", []) + self._knowledge_base.get(hosp_key, [])

        scored_docs = []
        for doc in docs:
            score = 0
            cat_words = doc.category.value.lower().split("_")
            title_lower = doc.title.lower()
            content_lower = doc.content.lower()

            for token in query_tokens:
                if token in cat_words:
                    score += 5
                if token in title_lower:
                    score += 4
                if token in content_lower:
                    score += 2

            # Only consider relevant if score meets threshold
            if score >= 3:
                scored_docs.append((score, doc))

        # Sort by relevance score descending
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        if not scored_docs:
            # Avoid unsupported claims (Hallucination safeguard)
            return {
                "success": True,
                "domain": domain.value,
                "is_medical_advice": False,
                "grounded": False,
                "response": (
                    "I do not have approved organizational documentation regarding that administrative request. "
                    "I will connect you with our hospital information desk so they can assist you directly."
                ),
                "citations": [],
                "unsupported_claim_avoided": True
            }

        # 3. Grounded response with explicit citations
        best_doc = scored_docs[0][1]
        response_text = f"{best_doc.content} (Source: {best_doc.source_citation})"

        return {
            "success": True,
            "domain": domain.value,
            "is_medical_advice": False,
            "grounded": True,
            "category": best_doc.category.value,
            "response": response_text,
            "source_document": best_doc.title,
            "citations": [best_doc.source_citation]
        }


approved_knowledge_engine = ApprovedKnowledgeEngine()
