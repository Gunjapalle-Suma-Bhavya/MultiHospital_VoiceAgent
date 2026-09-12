# AI Prompts Used in Platform Engineering

This document records the actual prompts, instructions, and system directives utilized across all phases of engineering the **Autonomous Multi-Hospital Patient Intake Platform**.

---

## 1. Frontend Development Prompts

### Prompt 1.1: React 18 + Vite SPA Scaffolding with Dark Clinical Theme
> **Prompt**:
> *"Migrate the frontend to a modern, decoupled Single-Page Application (SPA) using React 18, TypeScript, Vite, and Tailwind CSS. Implement a dark, sleek clinical theme using slate-950, emerald-500, and sky-500 accents. Eliminate all static data and connect every view directly to live FastAPI endpoints. Structure the application into dedicated sub-routes: Voice Intake AI Portal, Doctor Discovery, My Appointments, Pre-Visit Questionnaires, Patient Notifications, Doctor Dashboard, Hospital Admin Portal, Platform Super-Admin, Observability/SRE, and MongoDB Atlas Document Inspector."*
>
> **What It Produced**:
> - Scaffolding in `frontend/src/` with modular components, custom hooks, and React context providers.
> - Responsive layout with persistent navigation, active tab badges, and toast notification system.

### Prompt 1.2: Web Speech API STT/TTS & Animated Waveform Audio Visualizer
> **Prompt**:
> *"Build an interactive Web Speech voice console that supports real-time continuous speech recognition and speech synthesis. Include: 1) An interim transcript buffer that updates as the patient speaks, 2) Automatic submission when the patient stops speaking (silence trigger), 3) A dedicated 'Send to AI' manual button, 4) A 'Test Audio' speaker check button, 5) Utterance keep-alive timers to prevent Chrome speech synthesis freezing on long turns, and 6) An animated bidirectional waveform audio visualizer indicating microphone input and AI speech output."*
>
> **What It Produced**:
> - Implemented `frontend/src/modules/patient/VoiceConsole.tsx` with Web Speech API integration.
> - Added animated SVG waveform bars responding to speech state.

### Prompt 1.3: Doctor Card Consolidation & Time Slot Selection Pills
> **Prompt**:
> *"In the Doctor Discovery portal, group available appointment slots by doctor_id and hospital_id so each physician appears exactly once. Display open appointment times as interactive emerald pill chips (e.g. 08:00 AM, 08:30 AM). Allow the patient to select their preferred time slot and book with one click, eliminating redundant duplicate doctor cards."*
>
> **What It Produced**:
> - Refactored `frontend/src/modules/patient/DoctorDiscovery.tsx` with slot grouping and interactive chip selection.

---

## 2. Backend & Cloud Integration Prompts

### Prompt 2.1: Non-Blocking MongoDB Atlas Cloud Persistence
> **Prompt**:
> *"Implement universal, non-blocking cloud persistence with MongoDB Atlas in app/database/mongodb.py. Connect to the cluster using MONGODB_URI and persist JSON documents for hospitals, doctors, appointments, patients, questionnaires, leaves, and notifications. Crucially, ensure all write operations are executed asynchronously via a Python ThreadPoolExecutor so that cloud network latency or connection drops never block HTTP requests or unit tests. Add REST endpoints to check connection status and inspect collection documents."*
>
> **What It Produced**:
> - Implemented `persist_to_mongodb` and `sync_event_to_mongodb` in `app/database/mongodb.py` with `ThreadPoolExecutor`.
> - Created `app/routers/mongodb_sync.py` exposing `/status`, `/collections`, and `/collection/{name}`.

### Prompt 2.2: Multi-Hospital Provider Registry & 7-Day Calendar Seeding
> **Prompt**:
> *"Seed a comprehensive multi-hospital provider network with 14 board-certified doctors across 4 approved partner hospitals: City Memorial Hospital, Care Regional Medical Center, Metro Health Hospital, and St. Jude Research Hospital. Cover key specialties: Orthopedics, Cardiology, Neurology, Dermatology, Gastroenterology, Pulmonology, Oncology, Pediatrics, and Rheumatology. Configure full 7-day working hours (08:00 to 18:00) with 30-minute consultation slots and primary calendars. Dual-write all seeded data to both SQLite and MongoDB Atlas."*
>
> **What It Produced**:
> - Created database seed scripts in `app/database/config.py` and dual-wrote to MongoDB Atlas.

---

## 3. AI Agent & Clinical Triage Prompts

### Prompt 3.1: Clinical Symptom NLU & Specialist Redirection
> **Prompt**:
> *"Implement SymptomIntentResolver in app/agent/patient_access_agent.py. When a patient describes symptoms through speech or text (e.g. 'terrible migraine', 'knee pain when walking', 'rash on forearm', 'acid reflux after meals'), extract the primary clinical complaints and automatically triage them to the appropriate medical specialty (Neurology, Orthopedics, Dermatology, Gastroenterology). Immediately query matching doctors across partner hospitals and present recommendations. If red-flag symptoms are detected (chest pain, acute shortness of breath, loss of consciousness), immediately halt scheduling and redirect to 911 emergency services."*
>
> **What It Produced**:
> - Implemented clinical entity resolution and emergency safety triage in `app/agent/patient_access_agent.py`.
> - Tested across diverse clinical scenarios with zero medical hallucinations.

### Prompt 3.2: Patient Access Voice Agent System Directive
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
> **What It Produced**:
> - Grounded voice agent behavior in `app/agent/patient_access_agent.py`.

---

## 4. Notification & Event Bus Prompts

### Prompt 4.1: Event-Driven Multi-Channel Notification Pipeline
> **Prompt**:
> *"Wire the notification engine into the platform event bus. When appointments are created, confirmed, or cancelled, or when pre-visit questionnaires are completed, publish structured SystemEvents (APPOINTMENT_BOOKED, APPOINTMENT_CANCELLED, QUESTIONNAIRE_COMPLETED) to the central EventBus. Decoupled consumers in PlatformEventConsumers must automatically dispatch multi-role notifications across SMS, Email, and Voice channels to the patient, the physician, and the hospital administrator. Persist notification records to both SQLite and MongoDB Atlas."*
>
> **What It Produced**:
> - Updated `app/agent/actions.py`, `app/appointments/appointment_management.py`, and `app/events/consumers.py`.
> - Connected real-time notification endpoints `GET /api/v1/notifications/recipient/{role}/{recipient_id}` and `GET /api/v1/notifications/recent`.

---

## 5. Verification & Testing Prompts

### Prompt 5.1: 255-Test Suite Maintenance & Timezone Stabilization
> **Prompt**:
> *"Ensure all 255 automated tests across 59 suites pass with 100% green status. Stabilize any time-dependent tests (such as hospital dashboard slots crossing midnight UTC) by anchoring relative appointment times to midday. Ensure that non-blocking MongoDB Atlas thread pool workers and mock EHR integrations never cause test timeouts or hangs."*
>
> **What It Produced**:
> - Fixed midnight boundary edge case in `test_hospital_dashboard_5_32.py`.
> - Made MongoDB synchronization 100% non-blocking via `ThreadPoolExecutor`.
> - Verified 255 passed tests in 131.93s.
