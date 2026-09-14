# Autonomous Multi-Hospital Patient Intake & AI Voice Platform

[![Platform Status](https://img.shields.io/badge/Platform%20Status-Online%20%7C%20Production-success)](https://github.com/Gunjapalle-Suma-Bhavya/MultiHospital_VoiceAgent)
[![Tests Passing](https://img.shields.io/badge/Tests-255%2F255%20Passed-brightgreen)](https://github.com/Gunjapalle-Suma-Bhavya/MultiHospital_VoiceAgent)
[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/Frontend-React%2018%20%7C%20TypeScript%20%7C%20Vite%20%7C%20Tailwind-61dafb)](https://reactjs.org/)
[![Cloud Database](https://img.shields.io/badge/Cloud%20Database-MongoDB%20Atlas%20Dual--Write-47A248)](https://www.mongodb.com/atlas)
[![EHR Interoperability](https://img.shields.io/badge/Interoperability-SMART--on--FHIR%20R4%20%7C%20Epic%20%7C%20Cerner-orange)](https://hl7.org/fhir/)
[![HIPAA Privacy](https://img.shields.io/badge/Privacy-HIPAA%20Compliant%20%7C%20Zero--PHI-blueviolet)](#security--privacy)

An enterprise-grade, event-driven, multi-tenant healthcare access platform that enables autonomous AI voice and chat patient intake, clinical symptom triage with specialist redirection, cross-facility doctor discovery with dedicated time-slot selection, real-time calendar scheduling, bi-directional EHR synchronization with 5-point authoritative verification, conversational doctor-tailored pre-visit questionnaires, multi-channel notification pipelines, non-blocking MongoDB Atlas cloud document persistence, and comprehensive operational observability.

---

## 1. Product Overview

In modern healthcare networks, patient access operations suffer from fragmented appointment systems, long telephony wait times, high human receptionist overhead, and frequent scheduling desynchronizations with hospital Electronic Health Record (EHR) systems.

The **Autonomous Multi-Hospital Patient Intake Platform** solves this by providing:

- **Natural AI Voice Telephony & Web Speech Interaction**: Patients speak or type clinical complaints naturally (*"I have had shoulder pain for the last few weeks"*, *"I have a terrible migraine and light sensitivity"*). The voice agent's `SymptomIntentResolver` triages symptoms into medical specialties, extracts clinical entities, and recommends certified specialists across network hospitals with sub-2-second latency.
- **Immediate Clinical Emergency Redirection**: Critical red-flag complaints (e.g. crushing chest pain, acute shortness of breath, loss of consciousness) trigger instant emergency 911 handoffs with prominent visual and audio alerts, immediately halting normal scheduling.
- **Cross-Hospital Doctor Discovery & Schedule Aggregation**: Multi-tenant scheduling engine indexes board-certified doctors across 4 partner hospitals (`City Memorial Hospital`, `Care Regional Medical Center`, `Metro Health Hospital`, `St. Jude Research Hospital`). Doctors are grouped into unified profile cards (eliminating duplicate listings) with selectable emerald time-slot pills.
- **Doctor-Specific Pre-Visit Intake Questionnaires**: Following appointment confirmation, the agent immediately prompts the patient with pre-visit intake questions configured specifically by that doctor (e.g., shoulder pain duration and past treatment for Dr. Sharma; cardiac symptoms for Dr. Rao). Responses are delivered directly to that doctor's clinical interface and confirmed with the patient.
- **Hybrid Polyglot Persistence (SQL + MongoDB Atlas)**: ACID relational local storage (SQLite/PostgreSQL) coupled with non-blocking, asynchronous dual-write event bus synchronization to cloud **MongoDB Atlas** (`nexushealth_hospital_db`). Provides real-time JSON document persistence for hospitals, doctors, appointments, questionnaires, leaves, notifications, and audit trails.
- **Authoritative 5-Point EHR Verification**: Decouples internal bookings from external EHRs. Outbound bookings are created in external systems (SMART-on-FHIR R4, Epic MyChart, Cerner Millennium) and verified across 5 critical dimensions before internal confirmation.
- **Self-Healing Failure Recovery**: Automated failure classification, exponential backoff retries, thread-safe circuit breakers (`CLOSED`, `OPEN`, `HALF_OPEN`), and discrepancy reconciliation prevent double-booking.
- **Real-Time Dispatched Alerts & Notifications**: Decoupled event consumers listen for `APPOINTMENT_BOOKED`, `APPOINTMENT_CANCELLED`, `QUESTIONNAIRE_COMPLETED`, and `HOSPITAL_APPROVED` events, automatically dispatching SMS, Email, and Voice notifications with a live audit feed and phone search.
- **Modern React 18 + Vite SPA**: Dark, sleek clinical interface featuring real-time audio visualizers with animated waveforms, auto-submit on speech completion, speaker check tests, and a live MongoDB cloud document inspector.

---

## 2. Feature List

- **Multi-Tenant Hospital Network**: 4 accredited network hospitals with complete department coverage:
  - `HOSP-CITY-01`: City Memorial Hospital (Downtown) — Orthopedics, Cardiology, Emergency Medicine.
  - `HOSP-CARE-02`: Care Regional Medical Center (Westside) — Neurology, Dermatology, General Surgery.
  - `HOSP-METRO-03`: Metro Health Hospital (Uptown) — Gastroenterology, Pulmonology, Internal Medicine.
  - `HOSP-STJUDE-04`: St. Jude Research Hospital (South Campus) — Oncology, Pediatrics, Rheumatology.
- **Dynamic Multi-Doctor Voice Booking (PRD Section 24)**: End-to-end voice scenario supporting natural symptom intake, multi-hospital doctor recommendations, patient selection by name, number, slot time, or hospital, slot reservation, and immediate booking confirmation.
- **Doctor-Tailored Intake Questionnaires**: Intake questionnaires dynamically aligned to the selected physician's specialty and custom question set. Answers are recorded in `PatientIntakeRecord`, persisted to MongoDB Atlas, and reflected immediately in the doctor's clinical workstation.
- **Consolidated Doctor Discovery & Slot Pills**: 14 specialists across 10 clinical disciplines. Doctor cards group open appointment slots into dedicated emerald time-slot chips (`08:00 AM`, `08:30 AM`, etc.), eliminating repetitive card duplication.
- **Live LLM Integration**: Pluggable provider architecture powered by `LiveLLMClient` supporting OpenAI, Azure OpenAI, and OpenAI-compatible proxy gateways (e.g. AICredits) with temperature control and token tracking.
- **Web Speech STT/TTS & Audio Visualizer**: Integrated Web Speech API speech recognition and speech synthesis with keep-alive timers, auto-submit buffer triggers, Test Audio speaker buttons, and interactive bidirectional animated waveforms.
- **MongoDB Atlas Cloud Document Inspector**: Interactive visual cloud viewer querying real collections (`hospitals`, `doctors`, `appointments`, `patients`, `questionnaires`, `leaves`, `notifications`, `events`) directly from MongoDB Atlas with JSON syntax formatting and collection counts.
- **EHR Interoperability Catalog**: Pluggable adapter architecture supporting **FHIR R4**, **Epic MyChart**, **Cerner Millennium**, **HL7 v2.x**, and **Mock EHR**.
- **Reliability & Circuit Breaker**: Thread-safe circuit breaker with failure thresholds, cooldown periods, randomized jitter retries, and Dead Letter Queue (DLQ).
- **Automated Reminder Scheduler**: Asynchronous background workflows dispatching $T-24\text{h}$ questionnaire reminders and $T-2\text{h}$ check-in alerts via SMS, Voice, and Email.
- **Role-Based Access Control (RBAC)**: Fine-grained access control for 4 dedicated roles: `PATIENT`, `DOCTOR`, `HOSPITAL_ADMIN`, and `PLATFORM_ADMIN`.
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

For comprehensive architectural specifications, sequence diagrams, failure flows, and reconciliation workflows, refer to [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## 4. Technology Choices

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

## 5. Setup Instructions

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

# 5. Build frontend production assets
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
DEBUG=false

# Relational Core Database (SQLite for local dev, PostgreSQL for production)
DATABASE_URL=sqlite:///./hospital_platform.db

# MongoDB Atlas Cloud Persistence (Optional Document Store)
MONGODB_URI=mongodb+srv://<db_username>:<db_password>@cluster0.scjuj68.mongodb.net/?appName=Cluster0
MONGODB_DB_NAME=nexushealth_hospital_db

# Live AI / LLM Integration (OpenAI or AICredits proxy)
OPENAI_BASE_URL=https://api.aicredits.in/v1
OPENAI_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=512

# Voice Engine Settings
VOICE_SYNTHESIS_ENABLED=true
AUDIO_SAMPLE_RATE=24000
BARGE_IN_THRESHOLD_MS=180
SILENCE_DETECTION_MS=450

# EHR Integration
MOCK_EHR_ENABLED=true
FHIR_BASE_URL=https://fhir.hospital.org/r4
SMART_AUTH_URL=https://fhir.hospital.org/oauth2/token
SMART_CLIENT_ID=your-client-id-here
SMART_CLIENT_SECRET=your-client-secret-here
EHR_DEFAULT_TIMEOUT_SECONDS=5.0
```

---

## 7. Database Setup

The platform uses a hybrid polyglot architecture:
1. **Relational Core (SQLite / PostgreSQL)**:
   - Initialized automatically upon first application start in `app/database/config.py`.
   - Seed data is loaded automatically with 4 network hospitals, 14 board-certified doctors, primary working hour schedules (08:00–18:00), 30-minute consultation slots, and initial appointment records.
   - For manual database re-seeding:
     ```bash
     python -c "from app.database.config import init_db; init_db()"
     ```
2. **MongoDB Atlas Cloud Document Store**:
   - Provide a valid connection string in `MONGODB_URI` in `.env`.
   - The platform will connect asynchronously and establish dual-write replication across `hospitals`, `doctors`, `appointments`, `patients`, `questionnaires`, `leaves`, `notifications`, and `events`.
   - If `MONGODB_URI` is blank or network access is restricted, the platform continues flawlessly using the local relational store with zero disruptions.

---

## 8. AI Configuration

The platform's AI subsystem operates through `LiveLLMClient` and `PatientAccessAgent`:
- **Provider Gateway**: Supports direct OpenAI API endpoints or OpenAI-compatible gateways (such as AICredits: `https://api.aicredits.in/v1`).
- **Model**: Default is `gpt-4o-mini`, providing optimal clinical reasoning, structured function calling, and sub-2s latency.
- **Clinical Prompts & Directives**: System prompts strictly enforce medical triage rules, specialty boundaries, emergency 911 redirection, and conversational brevity.
- **Symptom Intent Resolver**: Maps spoken symptoms (e.g., shoulder pain, migraines, chest tightness) to certified medical specialties.

---

## 9. Voice Setup

The voice interaction subsystem supports browser-native and backend telephony interfaces:
- **Speech Recognition (STT)**: Built using Web Speech API with continuous listening, interim transcript streaming, and a silence auto-submit detector (450ms).
- **Speech Synthesis (TTS)**: Utterance queue manager with keep-alive timers to prevent browser audio stall, and custom voice pitch/rate tuning.
- **Visual Feedback**: Bidirectional animated waveform audio visualizer rendering dynamic frequencies during speech input and AI response.
- **Audio Diagnostics**: Integrated "Test Audio" speaker check button in the voice console for immediate hardware confirmation.

---

## 10. EHR / External Integration Setup

The EHR integration layer (`app/ehr/`) provides vendor-neutral connectivity:
- **Supported Adapters**: SMART-on-FHIR R4, Epic MyChart / Interconnect, Cerner Millennium, HL7 v2.x, and a high-fidelity Mock EHR sandbox.
- **5-Point Verification Protocol**: Verifies Patient Identity, Provider NPI, Facility ID, Slot Availability, and Concurrency Timestamp prior to booking finalization.
- **Circuit Breaker**: `EHRCircuitBreaker` monitors downstream health, tripping to `OPEN` on consecutive failures and failing fast to protect hospital networks.
- **Reconciliation Engine**: Reconciles pending or disconnected transactions against external EHR audit logs to resolve discrepancies.

---

## 11. Workflow Setup

- **Doctor-Specific Pre-Visit Intake Workflow**: Following appointment booking, the workflow engine automatically loads the questions configured by that specific physician (e.g. Dr. Sharma vs. Dr. Rao), collects responses sequentially or in one turn, and publishes them to `PatientIntakeRecord`.
- **Clinical Workstation Delivery**: Persisted responses are immediately dispatched to the physician's clinical portal for pre-consultation review.
- **Automated Reminder Scheduler**: Cron/background workers dispatch reminders at $T-24\text{h}$ and $T-2\text{h}$ prior to scheduled appointment times.
- **Notification Pipeline**: Publishes events (`APPOINTMENT_BOOKED`, `APPOINTMENT_CANCELLED`, `QUESTIONNAIRE_COMPLETED`) to decoupled consumers for SMS, Email, and Voice dispatch.

---

## 12. Running Locally

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
```bash
cd frontend
npm run dev
# Launches Vite dev server at http://localhost:3000 with proxy to backend at :8000
```

---

## 13. Testing

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

# Run End-to-End Multi-Doctor Voice Booking & Intake Test
python tests/test_ai_and_ehr_capabilities_checklist.py
```

**Results**: `255 passed (100% pass rate)`.

---

## 14. Deployment

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

## 15. Demo Credentials & Personas

The platform offers 1-click demo logins and manual authentication for 4 dedicated roles:

| Role | Persona Name | Identifier / Login | Password | Demonstration Action |
| :--- | :--- | :--- | :--- | :--- |
| **Patient** | Marcus Aurelius | `patient@example.com` / `+1-555-SHOULDER` | `password123` | Spoken voice booking for shoulder pain; doctor selection; pre-visit questionnaire intake. |
| **Doctor** | Dr. Sharma | `DOC-SHARMA-01` | `password123` | Reviews daily consultation roster, verifies patient intake questionnaires, manages calendar blocks. |
| **Doctor** | Dr. Rao | `DOC-RAO-02` | `password123` | Reviews cardiology consultations and cardiac pre-visit intake briefs. |
| **Hospital Admin** | Dr. Sarah Connor | `admin@citymemorial.org` | `password123` | Manages facility doctors, doctor rostering, checks EHR sync logs and anti-double-booking. |
| **Platform Admin** | Platform Super-Admin | `admin@hospitalplatform.org` | `password123` | SRE 4 Golden Signals, MongoDB Atlas document inspector, Definition-of-Done runner. |

---

## 16. Known Limitations

1. **Browser Microphone Permissions**: Web Speech API requires explicit user permission to access microphone hardware on Chromium and WebKit browsers.
2. **Offline Speech Recognition**: Web Speech STT on certain operating systems requires an active internet connection to contact browser vendor speech recognition endpoints.
3. **External EHR Sandboxes**: Real Epic Interconnect and Cerner Millennium endpoints require mutual TLS (mTLS) client certificates and VPN tunneling, provided via the built-in Mock EHR sandbox during local development.

---

## 17. Future Improvements

1. **Native WebRTC / SIP Gateway**: Direct integration with Twilio Voice and FreeSWITCH for native PSTN telephony dial-in without browser requirements.
2. **Multilingual Speech Translation**: Real-time multi-lingual voice translation across Spanish, Hindi, Telugu, and Mandarin during live consultation intake.
3. **Automated Insurance Eligibility Verification**: Instant pre-authorization verification against ANSI X12 270/271 clearinghouses prior to appointment confirmation.
4. **HL7 FHIR Subscription Streams**: WebSocket-based push subscriptions for instantaneous external EHR schedule changes.

---

## Documentation Links

- **Architecture Documentation**: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- **AI Tools & Engineering Breakdown**: [`AI_TOOLS.md`](AI_TOOLS.md)
- **AI Prompts & Directives Catalog**: [`AI_PROMPTS.md`](AI_PROMPTS.md)
- **Final Submission Checklist Verification**: [`tests/test_final_checklist_section_41.py`](tests/test_final_checklist_section_41.py)
- **Definition of Done Verification**: [`tests/test_definition_of_done_section_35.py`](tests/test_definition_of_done_section_35.py)

---

**Author / Maintainer**: Gunjapalle Suma Bhavya (`Gunjapallesumabhavya@gmail.com`)  
**GitHub**: [https://github.com/Gunjapalle-Suma-Bhavya/MultiHospital_VoiceAgent](https://github.com/Gunjapalle-Suma-Bhavya/MultiHospital_VoiceAgent)\n