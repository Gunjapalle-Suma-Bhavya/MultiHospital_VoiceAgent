# Autonomous Multi-Hospital Patient Intake & AI Voice Platform

[![Platform Status](https://img.shields.io/badge/Platform%20Status-Online%20%7C%20Production-success)](https://github.com/Gunjapalle-Suma-Bhavya/MultiHospital_VoiceAgent)
[![Tests Passing](https://img.shields.io/badge/Tests-255%2F255%20Passed-brightgreen)](https://github.com/Gunjapalle-Suma-Bhavya/MultiHospital_VoiceAgent)
[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/Frontend-React%2018%20%7C%20TypeScript%20%7C%20Vite%20%7C%20Tailwind-61dafb)](https://reactjs.org/)
[![Cloud Database](https://img.shields.io/badge/Cloud%20Database-MongoDB%20Atlas%20Dual--Write-47A248)](https://www.mongodb.com/atlas)
[![EHR Interoperability](https://img.shields.io/badge/Interoperability-SMART--on--FHIR%20R4%20%7C%20Epic%20%7C%20Cerner-orange)](https://hl7.org/fhir/)
[![HIPAA Privacy](https://img.shields.io/badge/Privacy-HIPAA%20Compliant%20%7C%20Zero--PHI-blueviolet)](#security--privacy)

An enterprise-grade, event-driven, multi-tenant healthcare access platform that enables autonomous AI voice and chat patient intake, clinical symptom triage with specialist redirection, cross-facility doctor discovery with dedicated time-slot selection, real-time calendar scheduling, bi-directional EHR synchronization with 5-point authoritative verification, conversational pre-visit questionnaires, multi-channel notification pipelines, non-blocking MongoDB Atlas cloud document persistence, and comprehensive operational observability.

---

## 1. Product Overview

In modern healthcare networks, patient access operations suffer from fragmented appointment systems, long telephony wait times, high human receptionist overhead, and frequent scheduling desynchronizations with hospital Electronic Health Record (EHR) systems.

The **Autonomous Multi-Hospital Patient Intake Platform** solves this by providing:

- **Natural AI Voice Telephony & Web Speech Interaction**: Patients speak or type clinical complaints naturally (*"I have a terrible migraine and light sensitivity"*, *"my knee hurts when climbing stairs"*, *"severe tightness in my chest"*). The voice agent's `SymptomIntentResolver` triages symptoms into medical specialties, extracts clinical entities, and recommends certified specialists across network hospitals with sub-2-second latency.
- **Immediate Clinical Emergency Redirection**: Critical red-flag complaints (e.g. crushing chest pain, acute shortness of breath, loss of consciousness) trigger instant emergency 911 handoffs with prominent visual and audio alerts, immediately halting normal scheduling.
- **Cross-Hospital Doctor Discovery & Schedule Aggregation**: Multi-tenant scheduling engine indexes 14 board-certified doctors across 4 partner hospitals (`City Memorial Hospital`, `Care Regional Medical Center`, `Metro Health Hospital`, `St. Jude Research Hospital`). Doctors are grouped into unified profile cards (eliminating duplicate listings) with selectable emerald time-slot pills.
- **Hybrid Polyglot Persistence (SQL + MongoDB Atlas)**: ACID relational local storage (SQLite/PostgreSQL) coupled with non-blocking, asynchronous dual-write event bus synchronization to cloud **MongoDB Atlas** (`nexushealth_hospital_db`). Provides real-time JSON document persistence for hospitals, doctors, appointments, questionnaires, leaves, notifications, and audit trails.
- **Authoritative 5-Point EHR Verification**: Decouples internal bookings from external EHRs. Outbound bookings are created in external systems (SMART-on-FHIR R4, Epic MyChart, Cerner Millennium) and verified across 5 critical dimensions before internal confirmation.
- **Self-Healing Failure Recovery**: Automated failure classification, exponential backoff retries, thread-safe circuit breakers (`CLOSED`, `OPEN`, `HALF_OPEN`), and discrepancy reconciliation prevent double-booking.
- **Clinical Pre-Visit Questionnaires**: Pre-visit clinical intake forms are delivered conversationally or via interactive forms. Structured answers are encrypted at rest and dual-written to MongoDB Atlas for immediate physician review.
- **Real-Time Dispatched Alerts & Notifications**: Decoupled event consumers listen for `APPOINTMENT_BOOKED`, `APPOINTMENT_CANCELLED`, `QUESTIONNAIRE_COMPLETED`, and `HOSPITAL_APPROVED` events, automatically dispatching SMS, Email, and Voice notifications with a live audit feed and phone search.
- **Modern React 18 + Vite SPA**: Dark, sleek clinical interface featuring real-time audio visualizers with animated waveforms, auto-submit on speech completion, speaker check tests, and a live MongoDB cloud document inspector.

---

## 2. Key Features & Capabilities

- **Multi-Tenant Hospital Network**: 4 accredited network hospitals with complete department coverage:
  - `HOSP-CITY-01`: City Memorial Hospital (Downtown) — Orthopedics, Cardiology, Emergency Medicine.
  - `HOSP-CARE-02`: Care Regional Medical Center (Westside) — Neurology, Dermatology, General Surgery.
  - `HOSP-METRO-03`: Metro Health Hospital (Uptown) — Gastroenterology, Pulmonology, Internal Medicine.
  - `HOSP-STJUDE-04`: St. Jude Research Hospital (South Campus) — Oncology, Pediatrics, Rheumatology.
- **Consolidated Doctor Discovery & Slot Pills**: 14 specialists across 10 clinical disciplines. Doctor cards group open appointment slots into dedicated emerald time-slot chips (`08:00 AM`, `08:30 AM`, etc.), eliminating repetitive card duplication.
- **Live LLM Integration**: Pluggable provider architecture powered by `LiveLLMClient` supporting OpenAI, Azure OpenAI, and OpenAI-compatible proxy gateways (e.g. AICredits) with temperature control and token tracking.
- **Web Speech STT/TTS & Audio Visualizer**: Integrated Web Speech API speech recognition and speech synthesis with keep-alive timers, auto-submit buffer triggers, Test Audio speaker buttons, and interactive bidirectional animated waveforms.
- **MongoDB Atlas Cloud Document Inspector**: Interactive visual cloud viewer querying real collections (`hospitals`, `doctors`, `appointments`, `patients`, `questionnaires`, `leaves`, `notifications`, `events`) directly from MongoDB Atlas with JSON syntax formatting and collection counts.
- **EHR Interoperability Catalog**: Pluggable adapter architecture supporting **FHIR R4**, **Epic MyChart**, **Cerner Millennium**, **HL7 v2.x**, and **Mock EHR**.
- **Reliability & Circuit Breaker**: Thread-safe circuit breaker with failure thresholds, cooldown periods, randomized jitter retries, and Dead Letter Queue (DLQ).
- **Automated Reminder Scheduler**: Asynchronous background workflows dispatching $T-24\text{h}$ questionnaire reminders and $T-2\text{h}$ check-in alerts via SMS, Voice, and Email.
- **Role-Based Access Control (RBAC)**: Fine-grained access control for `PATIENT`, `DOCTOR`, `HOSPITAL_ADMIN`, and `PLATFORM_ADMIN`.
- **Operational Observability (SRE)**: 16-step lifecycle operation tracer, SRE 4 Golden Signals (Latency, Traffic, Errors, Saturation), and tamper-evident privacy-safe audit trails.
- **100% Test Suite Verification**: 255 unit and integration tests across 59 test suites with 100% pass rate.

---

## 3. Architecture Overview

```
Users (Patients, Doctors, Hospital Admins, Platform Admins)
   ↓
Presentation Layer (React 18 + TypeScript + Vite + Tailwind CSS Single-Page Application)
   ↓
API Gateway (FastAPI REST Endpoints + OpenAPI / Swagger Documentation)
   ↓
AI & Conversational Layer (Patient Access Agent, SymptomIntentResolver, Guardrails, Live LLM)
   ↓
Capability Engine (19 Typed Tools, RBAC Guards, Idempotency Enforcer)
   ↓
Core Application Services (Scheduling & Slot Engine, Multi-Hospital Registry, Questionnaires)
   ↓
EHR Integration Layer (Circuit Breaker, Reliability Retry, SMART-on-FHIR / Epic Adapters)
   ↓
External Healthcare Systems (Authoritative EHRs & Hospital Infrastructure)
   ↓
Verification & Synchronization (5-Point Authoritative Verification, State Sync, DLQ)
   ↓
Event Bus & Decoupled Consumers (Analytics, Multi-Channel Notifications, Workflows, Audit)
   ↓
Hybrid Persistence Layer:
   ├── Relational Store: SQLAlchemy 2.0 (SQLite / PostgreSQL) with Row Locking
   └── Cloud Document Store: MongoDB Atlas (Non-blocking Asynchronous Thread Pool Dual-Write)
   ↓
Operational Observability (16-Step Operation Tracer, 4 Golden Signals, AI Benchmarks)
```

For comprehensive architectural specifications, sequence diagrams, and failure flows, refer to [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## 4. Technology Stack & Justification

| Layer / Concern | Selected Technology | Why Was This Selected? |
| :--- | :--- | :--- |
| **Backend Framework** | **FastAPI (Python 3.11+)** | Asynchronous non-blocking I/O for thousands of concurrent voice/chat streams, strict Pydantic v2 data validation compiled to C, and native OpenAPI generation. |
| **Frontend UI** | **React 18 + TypeScript + Vite + Tailwind CSS** | Lightning-fast HMR, strict type safety, modular component architecture, and responsive dark clinical UI theme with sub-50ms component transitions. |
| **Cloud Document Store** | **MongoDB Atlas Cloud Database** | Non-blocking dual-write persistence of JSON documents (appointments, questionnaires, notifications, leaves), accessible globally with live JSON inspection. |
| **Relational Database** | **SQLAlchemy 2.0 + SQLite / PostgreSQL** | ACID transactional guarantees with pessimistic row locks (`with_for_update`) to prevent double-booking race conditions, with hard multi-tenant isolation. |
| **Voice & Speech** | **Web Speech API + Web Audio Visualizer** | Zero-latency browser-native speech recognition (STT) and speech synthesis (TTS) with real-time waveform visualizers and keep-alive timers. |
| **Runtime LLM** | **GPT-4o-mini (OpenAI / AICredits)** | High clinical reasoning accuracy at sub-1.4s turnaround latency, paired with 96.67% unit economics cost reduction ($0.125/call vs $3.75 human). |
| **Clinical NLU** | **SymptomIntentResolver** | Deterministic and LLM-guided mapping of spoken clinical symptoms (*migraine, chest pain, rash, acid reflux*) to medical specialties with emergency safety checks. |
| **Healthcare Standard** | **HL7 FHIR R4 & SMART-on-FHIR** | Legally mandated USCDI interoperability standard enabling vendor-neutral scheduling across Epic, Cerner, and modern clinical servers. |
| **Resilience & Reliability** | **Circuit Breaker + Exponential Backoff** | Thread-safe `EHRCircuitBreaker` preventing cascading EHR outage failures, plus automated self-healing retry with randomized jitter. |
| **Testing Framework** | **Pytest + SQLite StaticPool** | 100% deterministic test execution across 255 tests spanning 59 test suites with zero cross-test state pollution. |
| **Containerization** | **Docker & Docker Compose** | Cloud-agnostic deployment runnable on Render, Railway, AWS ECS, or local workstations with 1 command. |

---

## 5. Setup & Installation Instructions

### Prerequisites
- Python 3.11, 3.12, or 3.13
- Node.js 18+ & `npm`
- Git
- `pip` package manager

### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/Gunjapalle-Suma-Bhavya/MultiHospital_VoiceAgent.git
cd MultiHospital_VoiceAgent

# 2. Create and activate Python virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env

# 5. Build frontend production assets (optional if pre-built)
cd frontend
npm install
npm run build
cd ..
```

---

## 6. Environment Variables

Configure your `.env` file based on `.env.example`:

```ini
# Server Configuration
PORT=8000
HOST=0.0.0.0
ENVIRONMENT=production

# Database Configuration (Relational Core)
DATABASE_URL=sqlite:///./hospital_platform.db

# MongoDB Atlas Cloud Persistence (Optional Document Store)
MONGODB_URI=mongodb+srv://<db_username>:<db_password>@cluster0.scjuj68.mongodb.net/?appName=Cluster0
MONGODB_DB_NAME=nexushealth_hospital_db

# Live AI / LLM Integration
OPENAI_BASE_URL=https://api.aicredits.in/v1
OPENAI_API_KEY=sk-live-your-key-here
LLM_MODEL=gpt-4o-mini

# Voice Engine Settings
VOICE_SYNTHESIS_ENABLED=true
BARGE_IN_THRESHOLD_MS=180
SILENCE_DETECTION_MS=450

# EHR Integration
MOCK_EHR_ENABLED=true
FHIR_BASE_URL=https://fhir.hospital.org/r4
```

---

## 7. Running Locally

### Start Backend Application
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Once running, access:
- **Web Application Portal**: [http://localhost:8000/](http://localhost:8000/)
- **Swagger Interactive API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Interactive Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **MongoDB Atlas REST Status**: [http://localhost:8000/api/v1/mongodb/status](http://localhost:8000/api/v1/mongodb/status)
- **Health Check Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

### Running Frontend in Development Mode (Optional)
If modifying the React source code in `frontend/src`:
```bash
cd frontend
npm run dev
# Launches Vite dev server at http://localhost:5173 with proxy to backend
```

---

## 8. Clinical Symptom NLU & Specialist Redirection

The voice agent features deep clinical understanding through the `SymptomIntentResolver`:

1. **Speech Intake**: The patient speaks into the microphone (*"I have had a throbbing headache on one side for three days and blurry vision"*).
2. **Clinical Entity Extraction**: The engine identifies:
   - Primary Symptom: `Throbbing headache, light sensitivity, blurry vision`
   - Clinical Specialty: `Neurology`
   - Urgency Tier: `Standard Clinical / Non-Emergency`
3. **Specialist Redirection**: The agent queries doctors matching `Neurology` across partner hospitals (`Care Regional Medical Center`), presents Dr. Emily Watson, and prompts the patient for a preferred time slot.
4. **Emergency Guardrail**: If the patient describes acute red-flag symptoms (*"Crushing chest pain radiating down my left arm"*, *"I can't breathe and feeling faint"*), the agent immediately halts scheduling and directs the patient to call 911 or visit the nearest emergency room.

---

## 9. Multi-Hospital Provider Registry & Scheduling

The platform provides a consolidated multi-hospital directory:

| Hospital ID | Hospital Name | Campus / Region | Featured Specialties | Doctors Seeded |
| :--- | :--- | :--- | :--- | :--- |
| `HOSP-CITY-01` | City Memorial Hospital | Downtown Campus | Orthopedics, Cardiology, Emergency Medicine | Dr. Sharma, Dr. Marcus Vance, Dr. Sophia Bennett |
| `HOSP-CARE-02` | Care Regional Medical Center | Westside Pavilion | Neurology, Dermatology, General Surgery | Dr. Emily Watson, Dr. Elena Rostova, Dr. Julian Hayes, Dr. Sarah Connor |
| `HOSP-METRO-03` | Metro Health Hospital | Uptown Medical Tower | Gastroenterology, Pulmonology, Internal Medicine | Dr. Lisa Chen, Dr. Michael Chang, Dr. Rachel Green |
| `HOSP-STJUDE-04` | St. Jude Research Hospital | South Campus | Oncology, Pediatrics, Rheumatology | Dr. David Kim, Dr. Olivia Taylor, Dr. Arthur Dent, Dr. Jennifer Aniston |

- **Zero-Duplicate Doctor Listings**: Doctors are consolidated into a single card per hospital with full credentials, specialty tags, consultation fees, and ratings.
- **Dedicated Time Slot Selector Pills**: Available slots are rendered as interactive chips (`08:00 AM`, `08:30 AM`, `09:00 AM`, etc.). Selecting a pill highlights it in emerald and enables 1-click booking.

---

## 10. Multi-Channel Notification Pipeline

An event-driven notification engine connects booking, cancellation, and clinical questionnaires:

- **Supported Channels**: `SMS`, `EMAIL`, and `VOICE`.
- **Event Bus Triggers**:
  - `APPOINTMENT_BOOKED`: Automatically dispatches SMS confirmation to patient, new appointment notification to physician portal, and intake alert to hospital admin.
  - `APPOINTMENT_CANCELLED`: Dispatches immediate cancellation notice with rescheduled slot recommendations.
  - `QUESTIONNAIRE_COMPLETED`: Alerts physician that pre-visit intake is ready for clinical review.
  - `HOSPITAL_APPROVED`: Notifies hospital administrator of network onboarding completion.
- **Live Dispatched Feed**: Accessible in the Patient Portal under **Notifications**, supporting telephone-based filtering, recent dispatch audits, and 1-click sample alert dispatching.

---

## 11. Testing & Verification

The platform maintains a comprehensive test suite of **255 automated tests across 59 suites**:

```bash
# Run the complete test suite
python -m pytest

# Run specific domain suites
python -m pytest tests/test_event_driven_platform_5_29.py -v
python -m pytest tests/test_notification_system_5_30.py -v
python -m pytest tests/test_hospital_dashboard_5_32.py -v
python -m pytest tests/test_definition_of_done_section_35.py -v
python -m pytest tests/test_final_checklist_section_41.py -v
```

**Results**: `255 passed in 131.93s (100% pass rate)`.

---

## 12. Deployment Options

### Docker Deployment
```bash
# Build Docker image
docker build -t multi-hospital-voice-agent .

# Run container with environment file
docker run -p 8000:8000 --env-file .env multi-hospital-voice-agent

# Or via Docker Compose
docker-compose up -d
```

### Cloud Deployment (Render / Railway / AWS ECS)
1. Link your GitHub repository to Render or Railway.
2. Select **Web Service** with Python environment.
3. Build Command: `pip install -r requirements.txt && cd frontend && npm install && npm run build && cd ..`
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
5. Configure environment variables (`MONGODB_URI`, `DATABASE_URL`, `OPENAI_API_KEY`).

---

## 13. Demonstration Personas & Test Credentials

| Role | Persona Name | Identifier / Login | Demonstration Action |
| :--- | :--- | :--- | :--- |
| **Patient** | Marcus Aurelius | `+1-555-SHOULDER` | Spoken voice booking for shoulder pain; pre-visit questionnaire intake. |
| **Doctor** | Dr. Sharma | `DOC-SHARMA-01` | Reviews daily consultation roster, verifies patient intake questionnaires. |
| **Doctor** | Dr. Emily Watson | `DOC-WATSON-03` | Reviews neurology appointments referred by AI symptom resolver. |
| **Hospital Admin** | Dr. Sarah Connor | `admin@metrohealth.org` | Manages facility doctors, approves intake templates, checks EHR sync logs. |
| **Platform Admin** | Super Admin | `admin@hospitalplatform.org` | Approves onboarding hospitals, inspects MongoDB Atlas documents, monitors SRE signals. |

---

## Documentation Links

- **Architecture Documentation**: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- **AI Tools & Engineering Breakdown**: [`AI_TOOLS.md`](AI_TOOLS.md)
- **AI Prompts & Directives Catalog**: [`AI_PROMPTS.md`](AI_PROMPTS.md)
- **Final Submission Checklist Verification**: [`tests/test_final_checklist_section_41.py`](tests/test_final_checklist_section_41.py)
- **Definition of Done Verification**: [`tests/test_definition_of_done_section_35.py`](tests/test_definition_of_done_section_35.py)

---

**Author / Maintainer**: Gunjapalle Suma Bhavya (`Gunjapallesumabhavya@gmail.com`)  
**GitHub**: [https://github.com/Gunjapalle-Suma-Bhavya/MultiHospital_VoiceAgent](https://github.com/Gunjapalle-Suma-Bhavya/MultiHospital_VoiceAgent)
