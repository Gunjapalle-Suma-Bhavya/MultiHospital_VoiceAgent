# AI Prompts Used in Platform Engineering

This document records the actual prompts, instructions, and system directives utilized across all phases of engineering the **Autonomous Multi-Hospital Patient Intake Platform**.

---

## 1. Frontend Development Prompts

### Prompt 1.1: Responsive 49-Page Dashboard Scaffolding
> **Prompt**:
> *"Design a clean, modern, responsive multi-portal healthcare frontend using vanilla CSS Grid and Flexbox with tab-based navigation. Support four distinct personas: Patient Self-Service, Doctor Clinical Dashboard, Hospital Administrator, and Platform Super-Admin. Include operational observability dashboards, real-time KPI status boxes, and interactive forms for all 16 canonical operation lifecycle steps. Ensure loading states, error states, and empty states are rendered with semantic status pills."*
>
> **What It Produced**:
> - Generated `static/index.html` with 49 specialized views, multi-tab switching, and responsive layout.
> - Engineered `static/css/styles.css` with a clinical color system (navy, emerald, slate, red alerts).

### Prompt 1.2: Interactive Pipeline & Voice Streaming Console
> **Prompt**:
> *"Add an interactive voice console in JavaScript that supports Server-Sent Events (SSE) streaming for real-time speech interaction. Include a barge-in interruption button that immediately halts playback and flushes audio buffers in under 180ms. Also, build a live 27-stage progression visualizer for Section 35 Definition of Done that dynamically renders stage completion pills and JSON diagnostic inspection."*
>
> **What It Produced**:
> - Added `setupDefinitionOfDoneUI()` and `setupAdvancedCapabilitiesUI()` in `static/js/app.js`.
> - Rendered the interactive 27-stage pipeline visualizer in `#tab-definition-of-done-step35`.

---

## 2. Backend Development Prompts

### Prompt 2.1: Multi-Tenant Schema & Isolation Model
> **Prompt**:
> *"Create SQLAlchemy relational models for an enterprise multi-tenant hospital platform. Models must include Hospital (with onboarding lifecycle: DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED), Doctor, DoctorCalendar, DoctorWorkingHour, BlockedSlot, PatientProfile, Appointment, EHRSyncLog, PatientIntakeRecord, AuditLog, and OperationTrace. Ensure strict foreign key constraints and isolate patient records by hospital_id to support tenant boundaries."*
>
> **What It Produced**:
> - Created `app/database/models.py` with 30+ relational entities and lifecycle status enumerations.

### Prompt 2.2: Capability Registry & Typed Tools
> **Prompt**:
> *"Define a centralized CapabilityRegistry cataloging 19 typed healthcare tools. Each capability must specify: name, purpose, input schema, output schema, required RBAC roles, retry policy, verification requirements, and idempotency behavior. Expose check_availability and create_appointment with explicit idempotency key enforcement and anti-double-booking locks."*
>
> **What It Produced**:
> - Implemented `app/discovery/capability_registry.py` and `app/scheduling/appointment_service.py` with database-level row locking (`with_for_update`).

---

## 3. AI Agent Prompts

### Prompt 3.1: Patient Access Agent System Directive
> **Prompt (Actual System Prompt configured in `LiveLLMClient` & `PatientAccessAgent`)**:
> ```
> You are the Autonomous Patient Access Voice Agent for a Multi-Hospital Healthcare Network.
> Your role is to assist patients in discovering suitable doctors, checking real-time availability,
> and scheduling verified clinical consultations across network hospitals.
> 
> Strict Operating Rules:
> 1. Safety First: If the patient mentions chest pain, severe shortness of breath, acute weakness/stroke symptoms,
>    or profuse bleeding, halt booking immediately and direct them to dial 911 or visit the nearest Emergency Room.
> 2. Clinical Precision: Map patient symptoms to appropriate specialties (e.g., shoulder pain -> Orthopedics)
>    and provide verified rationale.
> 3. Context Retention: Use existing patient preferences (preferred hospital, preferred time of day)
>    without asking redundant questions.
> 4. Voice Brevity: Keep conversational turns under 2 sentences for natural voice telephony delivery.
> 5. Capability Grounding: Never make up availability. Always query check_availability.
> ```
>
> **What It Produced**:
> - Grounded voice agent behavior in `app/agent/patient_access_agent.py` and eliminated medical hallucinations.

---

## 4. Voice Prompts

### Prompt 4.1: Natural Conversational Filler & Telephony Optimization
> **Prompt**:
> *"Implement conversational fillers and voice latency masking for patient interactions. When the AI is querying database availability or contacting the external EHR, inject natural speech fillers such as 'Let me check Dr. Sharma's calendar for tomorrow...' so the patient perceives zero dead air. Constrain end-to-end token generation to sub-2-second response latency."*
>
> **What It Produced**:
> - Engineered `app/voice/streaming_service.py` with conversational filler injection and low-latency audio chunking.

---

## 5. EHR Integration Prompts

### Prompt 5.1: 5-Point Authoritative Verification Protocol
> **Prompt**:
> *"Build an authoritative external state verification engine for EHR bookings. Before marking an internal appointment as CONFIRMED, execute an authoritative query against the external FHIR R4 server and verify 5 critical data points: 1) Patient ID match, 2) Practitioner ID match, 3) Facility ID match, 4) Slot/Time match, and 5) EHR status == 'booked'. If any check fails, do not confirm the internal appointment and flag for reconciliation."*
>
> **What It Produced**:
> - Created `IntegrationVerificationRecord` model and verification logic in `app/ehr/verification_service.py`.

### Prompt 5.2: EHR Circuit Breaker & Retry with Exponential Backoff
> **Prompt**:
> *"Implement a thread-safe EHRCircuitBreaker with CLOSED, OPEN, and HALF_OPEN states. Configure failure threshold of 3 consecutive errors with a 60-second cooldown period. For transient network errors (HTTP 503 or timeouts), implement exponential backoff retry with jitter. For persistent errors, route the request to a Dead Letter Queue and create a Human Escalation record."*
>
> **What It Produced**:
> - Implemented `app/ehr/circuit_breaker.py` and `app/ehr/reliability_service.py`.

---

## 6. Workflow Prompts

### Prompt 6.1: Automated Care & Reminder Pipeline
> **Prompt**:
> *"Create an asynchronous workflow service triggered upon APPOINTMENT_CONFIRMED. The workflow must automatically: 1) Schedule a T-24h pre-visit questionnaire reminder via SMS, 2) Schedule a T-2h arrival reminder via Voice/SMS, 3) Assign hospital pre-visit intake questions to the appointment, and 4) Dispatch an in-app notification to the doctor with patient details."*
>
> **What It Produced**:
> - Implemented `app/workflows/automated_reminder_scheduler.py` and `WorkflowInstance` tracking.

---

## 7. Testing Prompts

### Prompt 7.1: Comprehensive Unit & Integration Test Generation
> **Prompt**:
> *"Write comprehensive pytest suites validating Section 30 (Technical Architecture), Section 31 (API & Capability Design), Section 32 (State Management), Section 33 (Security Expectations), Section 34 (Testing Expectations), and Section 35 (Definition of Done). Use SQLite in-memory database with StaticPool to ensure thread-safe isolated execution. Assert 100% pass rate across all 27 canonical stages and both failure recovery scenarios."*
>
> **What It Produced**:
> - Generated `tests/test_definition_of_done_section_35.py`, `tests/test_security_expectations_section_33.py`, `tests/test_state_management_section_32.py`, etc., achieving 238 passing tests.

---

## 8. Debugging Prompts

### Prompt 8.1: SQLite In-Memory Multi-Threaded Table Isolation
> **Prompt**:
> *"Fix the OperationalError 'no such table: audit_logs' occurring during TestClient execution in pytest. The issue is caused by SQLite in-memory database (:memory:) dropping tables across separate connection threads opened by FastAPI TestClient. Configure create_engine with poolclass=StaticPool and use an autouse setup_db fixture."*
>
> **What It Produced**:
> - Resolved test fixture isolation in `tests/test_definition_of_done_section_35.py`, converting all 7 tests from error to clean PASS.

---

## 9. UI / Design Prompts

### Prompt 9.1: Clinical Dashboard Aesthetics & Color System
> **Prompt**:
> *"Refine the frontend CSS styles to deliver an enterprise healthcare aesthetic. Use deep slate (#0f172a) for primary text, emerald (#10b981) for confirmed/verified states, amber (#f59e0b) for pending/reconciliation states, and rose (#ef4444) for clinical escalations. Card borders should be subtle (1px solid #e2e8f0) with soft border-radii (6px-8px) and accessible font sizes."*
>
> **What It Produced**:
> - Polished `static/css/styles.css` with WCAG AA compliant typography and accessible contrast ratios.

---

## 10. Documentation Prompts

### Prompt 10.1: Architecture Specification with Mermaid Diagrams
> **Prompt**:
> *"Generate comprehensive architecture documentation detailing all 18 layers of the multi-hospital platform. Include Mermaid diagrams for: 1) High-level component architecture, 2) End-to-end booking sequence flow with EHR verification, 3) Entity Relationship data model, 4) Failure and retry recovery flow, and 5) Discrepancy reconciliation flow."*
>
> **What It Produced**:
> - Generated `ARCHITECTURE.md` with complete technical narratives and diagrams.

---

## 11. Evaluation Prompts

### Prompt 11.1: Automated AI Quality Evaluation Benchmark
> **Prompt**:
> *"Build an evaluation benchmark suite running synthetic patient transcripts through the Patient Access Agent across 4 key evaluation domains: Conversational AI, Scheduling Accuracy, EHR Integration, and Questionnaire Intake. Compute quantitative metrics for Intent Accuracy, Slot Completeness, Safety Compliance, and Latency, storing results in AIEvaluationRecord."*
>
> **What It Produced**:
> - Implemented `app/evaluation/ai_evaluation_framework.py` and verified quality scores across all benchmark datasets.
