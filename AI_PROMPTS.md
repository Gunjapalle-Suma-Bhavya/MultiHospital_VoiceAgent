# AI Prompts Used in Platform Engineering

This document records the actual prompts, instructions, and system directives utilized across all phases of engineering the **Autonomous Multi-Hospital Patient Intake Platform**, organized by functional category.

---

## 1. Frontend Development Prompts

### Prompt 1.1: React 18 + Vite SPA Scaffolding with Dark Clinical Theme
> **Prompt**:
> *"Migrate the frontend to a modern, decoupled Single-Page Application (SPA) using React 18, TypeScript, Vite, and Tailwind CSS. Implement a dark, sleek clinical theme using slate-950, emerald-500, and sky-500 accents. Eliminate all static data and connect every view directly to live FastAPI endpoints. Structure the application into dedicated sub-routes: Voice Intake AI Portal, Doctor Discovery, My Appointments, Pre-Visit Questionnaires, Patient Notifications, Doctor Dashboard, Hospital Admin Portal, Platform Super-Admin, Observability/SRE, and MongoDB Atlas Document Inspector."*
>
> **What It Produced / Changed**:
> - Scaffolding in `frontend/src/` with modular components, custom hooks, and React context providers.
> - Responsive layout with persistent navigation, active tab badges, and toast notification system.

### Prompt 1.2: Web Speech API STT/TTS & Animated Waveform Audio Visualizer
> **Prompt**:
> *"Build an interactive Web Speech voice console that supports real-time continuous speech recognition and speech synthesis. Include: 1) An interim transcript buffer that updates as the patient speaks, 2) Automatic submission when the patient stops speaking (silence trigger), 3) A dedicated 'Send to AI' manual button, 4) A 'Test Audio' speaker check button, 5) Utterance keep-alive timers to prevent Chrome speech synthesis freezing on long turns, and 6) An animated bidirectional waveform audio visualizer indicating microphone input and AI speech output."*
>
> **What It Produced / Changed**:
> - Implemented `frontend/src/modules/patient/VoiceAgentScreen.tsx` with Web Speech API integration.
> - Added animated SVG waveform bars responding to speech state.

### Prompt 1.3: Doctor Card Consolidation & Time Slot Selection Pills
> **Prompt**:
> *"In the Doctor Discovery portal, group available appointment slots by doctor_id and hospital_id so each physician appears exactly once. Display open appointment times as interactive emerald pill chips (e.g. 08:00 AM, 08:30 AM). Allow the patient to select their preferred time slot and book with one click, eliminating redundant duplicate doctor cards."*
>
> **What It Produced / Changed**:
> - Refactored `frontend/src/modules/patient/DoctorDiscovery.tsx` with slot grouping and interactive chip selection.

---

## 2. Backend Development Prompts

### Prompt 2.1: Non-Blocking MongoDB Atlas Cloud Persistence
> **Prompt**:
> *"Implement universal, non-blocking cloud persistence with MongoDB Atlas in app/database/mongodb.py. Connect to the cluster using MONGODB_URI and persist JSON documents for hospitals, doctors, appointments, patients, questionnaires, leaves, and notifications. Crucially, ensure all write operations are executed asynchronously via a Python ThreadPoolExecutor so that cloud network latency or connection drops never block HTTP requests or unit tests. Add REST endpoints to check connection status and inspect collection documents."*
>
> **What It Produced / Changed**:
> - Implemented `persist_to_mongodb` and `sync_event_to_mongodb` in `app/database/mongodb.py` with `ThreadPoolExecutor`.
> - Created `app/routers/mongodb_sync.py` exposing `/status`, `/collections`, and `/collection/{name}`.

### Prompt 2.2: Multi-Hospital Provider Registry & 7-Day Calendar Seeding
> **Prompt**:
> *"Seed a comprehensive multi-hospital provider network with 14 board-certified doctors across 4 approved partner hospitals: City Memorial Hospital, Care Regional Medical Center, Metro Health Hospital, and St. Jude Research Hospital. Cover key specialties: Orthopedics, Cardiology, Neurology, Dermatology, Gastroenterology, Pulmonology, Oncology, Pediatrics, and Rheumatology. Configure full 7-day working hours (08:00 to 18:00) with 30-minute consultation slots and primary calendars. Dual-write all seeded data to both SQLite and MongoDB Atlas."*
>
> **What It Produced / Changed**:
> - Created database seed scripts in `app/database/config.py` and dual-wrote to MongoDB Atlas.

---

## 3. AI Agent Prompts

### Prompt 3.1: Patient Access Voice Agent System Directive
> **Prompt (Configured in `LiveLLMClient` & `PatientAccessAgent`)**:
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
> **What It Produced / Changed**:
> - Grounded voice agent behavior in `app/agent/patient_access_agent.py`.

### Prompt 3.2: Multi-Doctor Voice Booking & Context Resolution (PRD Section 24)
> **Prompt**:
> *"Update app/agent/resolver.py and app/agent/patient_access_agent.py to handle multi-doctor recommendations and accurate selection resolution. When the user says 'Dr. Sharma at 4 PM' or 'first doctor' or 'option 2' or '5:30 PM', resolve the selected physician and slot without falling back to a default doctor. Confirm the appointment, immediately trigger that doctor's pre-visit questionnaire, record responses in the doctor's clinical workstation, and conclude with a confirmation that responses have been shared directly with the doctor."*
>
> **What It Produced / Changed**:
> - Advanced multi-modal resolution in `app/agent/resolver.py`.
> - Guaranteed selection accuracy matching PRD Section 24 flow.

---

## 4. Voice Prompts

### Prompt 4.1: Natural Conversational Voice Turn Shaping
> **Prompt**:
> *"Ensure all voice responses generated by the agent follow natural telephony cadence: keep responses concise (1 to 2 sentences), avoid Markdown syntax or symbols in spoken text, speak slot times in natural language (e.g., 'tomorrow at 4 PM' instead of '2026-09-15T16:00:00Z'), and provide an immediate audible confirmation before initiating questionnaires."*
>
> **What It Produced / Changed**:
> - Clean text normalization and TTS formatting in `PatientAccessAgent`.

### Prompt 4.2: ElevenLabs Neural Voice Integration
> **Prompt**:
> *"Integrate ElevenLabs neural text-to-speech API in app/routers/voice.py using model eleven_flash_v2_5 for ultra-low latency voice streaming. Provide automatic fallback to Web Speech synthesis if network quota or rate limits are reached."*
>
> **What It Produced / Changed**:
> - Implemented `/api/v1/voice/speak` audio streaming endpoint with error resilience.

---

## 5. EHR Integration Prompts

### Prompt 5.1: 5-Point Authoritative Verification & Circuit Breaker
> **Prompt**:
> *"Implement a resilient EHR integration layer with a 5-point verification protocol and thread-safe EHRCircuitBreaker. Outbound booking calls must verify: 1) Patient Identity, 2) Provider NPI, 3) Facility ID, 4) Slot Availability, and 5) Concurrency Timestamp against SMART-on-FHIR R4 or Mock EHR before setting is_ehr_verified=True. On 5 consecutive timeouts or connection errors, trip the circuit breaker to OPEN to protect downstream hospital infrastructure."*
>
> **What It Produced / Changed**:
> - Implemented `app/ehr/integration_layer.py` and `app/ehr/adapters.py`.

---

## 6. Workflow Prompts

### Prompt 6.1: Doctor-Specific Pre-Visit Questionnaire Intake
> **Prompt**:
> *"When a booking is confirmed, look up the custom questionnaire configured for that selected doctor (e.g. shoulder pain duration and past treatments for Dr. Sharma; chest discomfort and BP for Dr. Rao). Ask questions sequentially, persist responses in PatientIntakeRecord and PatientQuestionnaireResponse, dual-write to MongoDB Atlas, and display them in the doctor's clinical workstation under Patient Pre-Visit Briefings."*
>
> **What It Produced / Changed**:
> - Dynamic questionnaire execution in `app/agent/patient_access_agent.py` and doctor portal integration.

---

## 7. Testing Prompts

### Prompt 7.1: Comprehensive Unit & Integration Test Suite Generation
> **Prompt**:
> *"Write comprehensive pytest test suites covering: 1) Multi-hospital doctor discovery, 2) Slot booking concurrency with anti-double-booking locks, 3) Symptom intent resolution, 4) Emergency 911 guardrails, 5) 5-point EHR verification, 6) Section 35 Definition of Done, and 7) Section 41 final submission checklist. Ensure 100% test pass rate with isolated SQLite StaticPool databases."*
>
> **What It Produced / Changed**:
> - 59 test suites containing 255 passing tests in `tests/`.

---

## 8. Debugging Prompts

### Prompt 8.1: Fixing Doctor Selection Fallback & Collisions
> **Prompt**:
> *"Fix the bug where selecting 'Dr. Sharma at 4 PM' or 'Dr. Rao at 5:30 PM' mistakenly fell back to the first available doctor in the database. Ensure the resolver checks the active recommended doctors list first, parses slot times and ordinals, and binds the chosen provider ID to the appointment draft."*
>
> **What It Produced / Changed**:
> - Overhauled `resolve_doctor_reference` in `app/agent/resolver.py` with multi-modal scoring.

---

## 9. UI / Design Prompts

### Prompt 9.1: Role Refinement & Hospital Staff Removal
> **Prompt**:
> *"Remove 'Hospital Staff' from both Sign In and Create Account interfaces, 1-click demo personas, and the landing page role explorer. Streamline the platform to 4 distinct healthcare roles: Patient, Doctor, Hospital Admin, and Entire System Admin (Platform Super-Admin). Arrange the auth role selector in a clean 2x2 grid."*
>
> **What It Produced / Changed**:
> - Updated `frontend/src/modules/landing/LandingPage.tsx` and `frontend/src/hooks/useAuth.tsx`.

---

## 10. Documentation Prompts

### Prompt 10.1: Architecture & README Standardization
> **Prompt**:
> *"Update README.md, ARCHITECTURE.md, AI_TOOLS.md, and AI_PROMPTS.md to strictly fulfill all requirements of Sections 36.2, 36.4, 36.5, 36.6, and 36.7. Fix all Mermaid diagram syntax errors by quoting node labels, removing direct subgraph-to-subgraph connections, using valid alphanumeric entity names in ER diagrams, and documenting the full multi-hospital voice booking architecture."*
>
> **What It Produced / Changed**:
> - Completely valid, error-free Markdown documentation files.

---

## 11. Evaluation Prompts

### Prompt 11.1: Automated AI Quality Evaluation Framework
> **Prompt**:
> *"Build an automated AI evaluation framework in app/evaluation/ai_evaluation_framework.py that executes standardized benchmark scenarios across Intent Accuracy, Slot Completeness, Safety Compliance, and Latency. Expose metrics through GET /api/v1/observability/ai-eval and render them in the Platform Admin SRE dashboard."*
>
> **What It Produced / Changed**:
> - AI evaluation pipeline generating quality scores and latency percentiles.\n