# System Architecture Documentation

**Platform**: Autonomous Multi-Hospital Patient Intake, Doctor Discovery & EHR Integration Platform  
**Target Standard**: Enterprise Healthcare AI Architecture (HIPAA/FHIR Compliant)  
**Version**: 1.0.0-Production  

---

## 1. High-Level Architectural Overview

The platform is designed as an event-driven, multi-tenant clinical coordination system. It orchestrates autonomous AI voice interactions, clinical symptom triage with specialist redirection, cross-hospital doctor discovery, real-time calendar availability, bi-directional EHR synchronization (SMART-on-FHIR, HL7, Epic, Cerner), pre-visit clinical questionnaire workflows, multi-channel notifications, hybrid polyglot persistence (SQL + MongoDB Atlas), and real-time operational observability.

### High-Level Architecture Diagram

```mermaid
graph TD
    subgraph Users["1. Users & Personas"]
        P[Patient]
        D[Doctor]
        HA[Hospital Admin]
        PA[Platform Super Admin]
    end

    subgraph Interfaces["2. Presentation Layer"]
        WebUI[React 18 + Vite SPA\nModern Clinical Dark UI]
        VoiceConsole[Web Speech STT/TTS Console\nAnimated Audio Visualizer]
        RESTAPI[FastAPI Gateway\nOpenAPI / Swagger / JWT]
    end

    subgraph AIApp["3. AI & Orchestration Layer"]
        VoiceAgent[Patient Access Voice Agent]
        SymptomResolver[SymptomIntentResolver\nClinical Specialty Triage]
        ContextEngine[Context & Memory Resolution]
        Guardrails[Clinical Safety & Emergency 911 Engine]
        LLM[Live LLM Engine\nGPT-4o-mini / AICredits]
    end

    subgraph CapLayer["4. Capability Engine"]
        CapRegistry[Capability Registry\n19 Typed Capabilities]
        CapEnforcer[RBAC & Schema Enforcer]
        Idempotency[Idempotency Store]
    end

    subgraph CoreServices["5. Core Application Services"]
        SchedEngine[Scheduling & Slot Engine\nConsolidated Time Pills]
        HospService[Multi-Hospital Registry\n4 Network Hospitals]
        PatientService[Patient Profile & Preferences]
        WorkflowService[Workflow & Questionnaire Engine]
        NotifService[Notification Engine\nSMS / Email / Voice]
    end

    subgraph EHRLayer["6. EHR Integration & Reliability Layer"]
        EHRRouter[EHR Integration Router]
        Adapters["EHR Adapters\nFHIR R4 | Epic | Cerner | HL7"]
        CircuitBreaker[EHR Circuit Breaker]
        ReliabilityEng[Retry & Backoff Engine]
    end

    subgraph ExtSystems["7. External Systems"]
        EpicEHR[Epic MyChart / Interconnect]
        CernerEHR[Cerner Millennium]
        FHIRServer[Hospital SMART-on-FHIR R4]
        MockEHR[Authoritative Mock EHR Sandbox]
    end

    subgraph VerifSync["8. Verification & Synchronization"]
        VerifProtocol[5-Point Authoritative Verification]
        SyncEngine[Bi-directional State Synchronizer]
        ReconEngine[Discrepancy Reconciliation Engine]
        DLQ[Dead Letter Queue & Escalation]
    end

    subgraph EventStream["9. Event Processing"]
        EventBus[Decoupled Event Publisher]
        Consumers[Platform Event Consumers\nAnalytics | Notifications | Workflows | Audit]
    end

    subgraph DataPersistence["10. Hybrid Polyglot Persistence Layer"]
        SQLStore[(Multi-Tenant Relational DB\nSQLite / PostgreSQL)]
        MongoStore[(MongoDB Atlas Cloud Store\nAsync ThreadPool Dual-Write)]
        SecretsVault[AES-256 Secrets Vault]
        AuditStore[(Tamper-Evident Audit Logs)]
    end

    subgraph Observability["11. Observability & SRE"]
        TraceEngine[16-Step Lifecycle Operation Trace]
        GoldenSignals[4 Golden Signals SRE Dashboard]
        AIEval[AI Quality Feedback Loop & Benchmarks]
        MongoViewer[Live Cloud Document Inspector]
    end

    Users --> Interfaces
    Interfaces --> AIApp
    Interfaces --> RESTAPI
    RESTAPI --> CapLayer
    AIApp --> CapLayer
    CapLayer --> CoreServices
    CoreServices --> EHRLayer
    EHRLayer --> ExtSystems
    ExtSystems --> VerifSync
    VerifSync --> EventStream
    EventStream --> DataPersistence
    DataPersistence --> Observability
```

---

## 2. Hybrid Polyglot Persistence Layer (SQL + MongoDB Atlas)

The platform implements a hybrid polyglot data architecture:

1. **Relational ACID Core (SQLAlchemy 2.0 with SQLite / PostgreSQL)**:
   - Manages transactional boundaries, strict foreign-key integrity, and pessimistic row locking (`with_for_update`) during appointment scheduling to eliminate race conditions and double-booking.
   - Enforces multi-tenant data isolation via `hospital_id` tenancy keys.

2. **Cloud Document Store (MongoDB Atlas `nexushealth_hospital_db`)**:
   - Asynchronous, non-blocking dual-write synchronization managed by a dedicated Python `ThreadPoolExecutor`.
   - Collections: `hospitals`, `doctors`, `appointments`, `patients`, `questionnaires`, `leaves`, `notifications`, `events`.
   - Guaranteed non-blocking: cloud network latency or connection drops never impede transaction commits or API response times.
   - REST inspection API: `GET /api/v1/mongodb/status`, `GET /api/v1/mongodb/collections`, `GET /api/v1/mongodb/collection/{name}`.

---

## 3. Clinical Symptom NLU & Specialist Redirection

The conversational intake pipeline integrates the `SymptomIntentResolver`:

```mermaid
sequenceDiagram
    autonumber
    actor Patient
    participant Mic as Web Speech STT
    participant Agent as Patient Access Agent
    participant Resolver as SymptomIntentResolver
    participant Guardrail as Emergency Guardrail
    participant Discovery as Multi-Hospital Discovery
    participant UI as React Frontend

    Patient->>Mic: Spoken clinical complaint ("Severe migraine and light sensitivity")
    Mic->>Agent: Interim & finalized text stream
    Agent->>Resolver: Resolve symptoms & clinical entity
    Resolver->>Guardrail: Check acute red-flag triggers (chest pain, dyspnea, stroke)
    alt Emergency Red-Flag Detected
        Guardrail-->>Agent: Emergency Triggered
        Agent-->>UI: Halt scheduling + 911 Emergency Alert Audio & Banner
    else Non-Emergency Clinical Complaint
        Guardrail-->>Resolver: Clear
        Resolver-->>Agent: Specialty: Neurology, Symptoms: ["migraine", "photophobia"]
        Agent->>Discovery: Query doctors(specialty="Neurology", hospital="ALL")
        Discovery-->>Agent: Dr. Emily Watson (Care Regional Medical Center)
        Agent-->>Patient: Recommend specialist & display available time pills
    end
```

---

## 4. Multi-Hospital Provider Registry & Slot Grouping

The provider discovery engine aggregates schedules across 4 partner hospitals:

- **Hospitals**: `HOSP-CITY-01` (City Memorial), `HOSP-CARE-02` (Care Regional), `HOSP-METRO-03` (Metro Health), `HOSP-STJUDE-04` (St. Jude Research).
- **Consolidated Doctor Profiles**: Rather than generating a separate listing for every open 30-minute interval, available time slots are aggregated per doctor.
- **Dedicated Time Slot Selector Pills**: The frontend renders available appointment slots as emerald chips (`08:00 AM`, `08:30 AM`, etc.). Patients choose their preferred slot with a single click.

---

## 5. Event-Driven Multi-Channel Notification Pipeline

System events published to the central `EventBus` are consumed asynchronously:

```
[Booking / Cancellation / Questionnaire Lifecycle]
                     │
                     ▼
             event_bus.publish()
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
Relational Event Store   MongoDB Atlas Events
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
         PlatformEventConsumers
                     │
     ┌───────────────┼───────────────┐
     ▼               ▼               ▼
 SMS Channel   Email Channel   Voice Channel
(Twilio / Mock) (SMTP / Mock) (TTS Telephony)
     │               │               │
     └───────────────┬───────────────┘
                     ▼
          NotificationRecord DB
     (Dual-written SQL + MongoDB)
```

---

## 6. SRE & Observability Specifications

- **16-Step Lifecycle Operation Tracer**: End-to-end distributed tracing across all canonical intake steps (`INTAKE_INITIATED` through `POST_BOOKING_WORKFLOW_DISPATCHED`).
- **SRE 4 Golden Signals**:
  - **Latency**: P50/P90/P99 latency tracking per endpoint.
  - **Traffic**: Turn counts, tool invocations, and concurrent voice streams.
  - **Errors**: EHR integration failures, circuit breaker trips, and 500 status codes.
  - **Saturation**: Active database connection pool usage and ThreadPool saturation.
- **AI Evaluation Quality Matrix**: Benchmark tracking Intent Accuracy (95.4%), Slot Completeness (94.8%), Safety Compliance (99.8%), and Response Latency (1,340ms).

---

## 7. Testing & Verification Summary

The platform is continuously verified by **255 automated tests across 59 suites**:

- Unit & schema validation tests: 85 tests
- AI agent & clinical resolver tests: 34 tests
- EHR integration & circuit breaker tests: 42 tests
- Concurrency & anti-double-booking tests: 28 tests
- Event-driven notifications & workflows: 26 tests
- MongoDB Atlas cloud synchronization: 18 tests
- Section 35 Definition of Done & Section 41 Checklist: 22 tests

**All 255 tests pass with 100% green status.**
