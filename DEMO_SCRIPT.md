# End-to-End Product Demonstration Guide & Video Script

**Target Evaluator**: Healthcare Technical Evaluators & System Architects  
**Scope**: Complete connected workflow across all 6 required demonstration parts (Section 36.3)  
**Total Estimated Duration**: 10–12 minutes  

---

## Part 1 — Hospital Lifecycle & Onboarding

### Objectives
Demonstrate self-service hospital registration, platform administrator review & approval, hospital operational configuration, doctor onboarding, calendar provisioning, and EHR integration adapter setup.

### Walkthrough Steps & Narration
1. **Hospital Registration (`#tab-onboarding`)**:
   - Navigate to the **Hospital Onboarding & Admin** tab.
   - Enter Hospital Name: `Metropolitan Health System`, Code: `METRO`, Email: `admin@metrohealth.org`, Admin Name: `Dr. Sarah Connor`.
   - Click **Register Draft Hospital**.
   - *Narration*: *"Notice the hospital is provisioned with status `SUBMITTED` and unique UUID. It cannot accept appointments or doctors until vetted by Platform Admin."*
2. **Platform Admin Approval**:
   - Under **Platform Admin Approval & Review (5.2)**, enter the generated Hospital UUID.
   - Click **Review Information** (shows tax ID and licensing accreditation).
   - Click **Approve Hospital**. Status transitions to `APPROVED`, and `is_active` becomes `True`.
3. **Hospital Operational Configuration**:
   - Review operating hours (`08:00 - 18:00`), timezone (`America/New_York`), and clinical departments (`Orthopedics`, `Cardiology`, `Neurology`).
4. **Doctor Creation (`#tab-doctors`)**:
   - Navigate to **Doctor & Calendar Management**.
   - Create doctor: `Dr. Sharma`, Specialty: `Orthopedics`, Duration: `30 minutes`.
   - Click **Register Doctor**. Status is `ACTIVE`.
5. **Calendar Configuration**:
   - Set up `In-Person Consultation Calendar` for Dr. Sharma with default working hours Monday–Friday 9:00 AM – 5:00 PM.
6. **EHR / Healthcare-System Configuration**:
   - Link EHR Adapter: Select `Epic MyChart (SMART-on-FHIR R4)`.
   - Set Endpoint: `https://fhir.metrohealth.org/r4`, Enable `Require External 5-Point Verification`.
   - *Narration*: *"The hospital is now fully onboarded and ready for real-time patient intake."*

---

## Part 2 — Patient Access & AI Booking Journey

### Objectives
Demonstrate patient authentication, conversational voice intake, natural speech symptom description, AI discovery, slot availability calculation, EHR creation, authoritative verification, and confirmation.

### Walkthrough Steps & Narration
1. **Patient Login & Telephony Initiation (`#tab-voice`)**:
   - Navigate to **AI Voice & Chat Access Console**.
   - Enter Patient Name: `Patient A`, Phone: `+1-555-SHOULDER`.
   - Click **Start Voice Session**.
2. **Describing Requirement**:
   - Patient Utterance: *"Hi, I've been having right shoulder pain for the last week and I'd like to see a doctor."*
   - Click **Send Utterance / Stream Voice**.
3. **AI Understanding & Context Resolution**:
   - The AI Recognizer classifies Intent: `BOOK_APPOINTMENT`, Category: `Orthopedics / Shoulder`.
   - Voice agent responds with conversational filler: *"Let me check available orthopedic specialists for you..."*
4. **Doctor Discovery & Availability**:
   - AI queries `check_availability` across network hospitals.
   - Presents options: *"I found two available options: Dr. Sharma at Metropolitan Health tomorrow at 4:00 PM, or Dr. Rao at Care Hospital tomorrow at 5:30 PM. Which would you prefer?"*
5. **Patient Selection**:
   - Patient speaks: *"Dr. Sharma at 4 PM please."*
6. **Appointment Booking & EHR Integration**:
   - AI invokes `create_appointment` with unique `idempotency_key`.
   - Internal appointment `APT-1024` is created in state `PENDING_EHR_VERIFICATION`.
   - Outbound FHIR request generates external appointment `EHR-88421`.
7. **External 5-Point Verification & Confirmation**:
   - Verification engine queries external FHIR server, verifying: Patient ID, Doctor ID, Facility ID, Slot Time, and Status (`booked`).
   - Internal appointment state synchronizes to `CONFIRMED`.
   - AI speaks: *"Your appointment with Dr. Sharma at Metropolitan Health is confirmed for tomorrow at 4:00 PM."*

---

## Part 3 — AI Nuance, Context Handling & Ambiguity

### Objectives
Demonstrate multi-turn memory, follow-up clarification, capability execution, and graceful handling of ambiguous or out-of-scope requests.

### Walkthrough Steps & Narration
1. **Context Handling Without Redundant Questions**:
   - In the same session, ask: *"Can I do this in the afternoon instead?"*
   - AI retains Dr. Sharma, Orthopedics, and Metropolitan Health, querying afternoon slots without asking patient to repeat their symptom or provider choice.
2. **Ambiguous Request Handling**:
   - Patient speaks: *"I feel bad somewhere in my body."*
   - AI recognizes intent ambiguity: *"I want to ensure you see the right specialist. Could you tell me a little more about what you are experiencing, such as joint pain, fever, or breathing discomfort?"*
3. **Unsupported Request Handling & Safety Guardrails**:
   - Patient speaks: *"Can you prescribe me 50mg of tramadol right now?"*
   - AI guardrails trigger policy: *"I cannot prescribe medications over the intake line. I can book an evaluation with a licensed physician who can assess your prescription needs."*
4. **Clinical Emergency Red-Flag Interception**:
   - Patient speaks: *"My chest feels tight and my left arm is numb."*
   - AI emergency triage halts booking instantly: *"This may be a medical emergency. Please hang up and immediately dial 911 or proceed to the nearest emergency room."*

---

## Part 4 — Pre-Visit Clinical Questionnaire

### Objectives
Demonstrate conversational questionnaire initiation, structured answer extraction, encrypted persistence, and doctor clinical dashboard review prior to consultation.

### Walkthrough Steps & Narration
1. **Questionnaire Initiation**:
   - AI speaks: *"Dr. Sharma has also configured 3 quick pre-visit questions to prepare for your consultation. Would you like to answer them now?"*
   - Patient speaks: *"Sure, go ahead."*
2. **Conversational Intake**:
   - AI: *"Where exactly is the shoulder pain located?"* $\rightarrow$ Patient: *"Right shoulder, near the rotator cuff."*
   - AI: *"How long have you had this pain?"* $\rightarrow$ Patient: *"About one week."*
   - AI: *"Have you had any previous treatments or surgeries on this shoulder?"* $\rightarrow$ Patient: *"None, just over-the-counter ibuprofen."*
3. **Structured Storage**:
   - Answers are compiled into `PatientIntakeRecord` with `is_patient_reported_only: True` and encrypted at rest (`ENCRYPTED_AT_REST`).
4. **Doctor Clinical Dashboard Review (`#tab-dashboards-step11` $\rightarrow$ Doctor Portal)**:
   - Doctor logs into clinical view.
   - Under **Today's Patients**, clicks on Patient A.
   - Pre-visit intake card renders verified summary: *1-week right shoulder rotator cuff pain, OTC ibuprofen only*. Doctor is fully prepared before patient steps into the clinic.

---

## Part 5 — EHR Integration, Workflows, Failure & Self-Healing

### Objectives
Demonstrate outbound EHR sync, external record verification, background reminder workflows, multi-channel notifications, transient failure recovery, and human escalation.

### Walkthrough Steps & Narration
1. **Booking-Triggered Workflow Execution**:
   - View **Workflow Examples (20)** or **Definition of Done (35)** tab.
   - Shows active `POST_BOOKING_CARE_AND_REMINDER_PIPELINE`.
   - $T-24\text{h}$ SMS questionnaire reminder and $T-2\text{h}$ check-in alerts are queued in the background engine.
2. **Multi-Role Notifications**:
   - Doctor receives in-app alert: *"New Patient: Patient A tomorrow at 4:00 PM with intake questionnaire completed."*
   - Patient receives SMS: *"Your appointment with Dr. Sharma is confirmed for tomorrow at 4:00 PM."*
3. **Failure Scenario 1: Transient EHR Failure & Self-Healing Recovery (`#tab-definition-of-done-step35`)**:
   - Click **Simulate Transient Failure & Self-Healing Recovery**.
   - Watch live progression:
     1. Outbound EHR booking attempt fails with `HTTP 503 Service Unavailable`.
     2. Reliability Engine classifies failure as `TRANSIENT_NETWORK_ERROR` (`is_retryable: True`).
     3. Exponential backoff retry attempt 1 succeeds with `HTTP 201 Created`.
     4. Authoritative EHR query verifies external record `EHR-RETRY-XXXX`.
     5. 5-point verification confirms state; appointment marked `CONFIRMED`.
4. **Failure Scenario 2: Persistent Failure, Reconciliation & Escalation**:
   - Click **Simulate Persistent Failure & Human Escalation**.
   - External system returns persistent HTTP 500 error; retries exhaust (3 of 3).
   - Appointment marked `RECONCILIATION_REQUIRED`.
   - Human Escalation ticket generated with full serialized context for clinic coordinator.
   - SRE dead-letter queue records operational incident.

---

## Part 6 — Platform Admin & Operational Observability

### Objectives
Demonstrate platform executive KPIs, 16-step operation tracing, SRE 4 Golden Signals, audit trails, and systematic AI evaluation benchmarks.

### Walkthrough Steps & Narration
1. **Platform Admin Dashboard (`#tab-operational-monitoring-step13`)**:
   - View global system health: Active Hospitals, Active Doctors, EHR Sync Success Rate (98.2%), Double-Booking Prevention (100%).
2. **16-Step Lifecycle Operation Trace**:
   - Inspect trace `DOD-JOURNEY-XXXX`: step-by-step latency breakdown across Speech Intake, AI Decision, Capability Call, EHR Integration, Verification, and Notifications.
   - Total end-to-end latency: **1,380 ms** ($<2.0\text{s}$ target satisfied).
3. **SRE 4 Golden Signals**:
   - Traffic (RPS), Latency percentiles (p50: 380ms, p95: 1.4s), Error Rate (<0.1%), Circuit Breaker State (`CLOSED`).
4. **Privacy-Sanitized Audit Trail (`#tab-audit`)**:
   - Query immutable audit ledger. Verify `privacy_level: STRUCTURED_NO_PHI`. Names and phone numbers are scrubbed, ensuring HIPAA compliance.
5. **AI Evaluation & Quality Benchmarks (`#tab-ai-evaluation-step21-22`)**:
   - Review automated benchmark metrics: Intent Accuracy (95.4%), Safety Compliance (99.8%), Slot Completeness (94.8%).
6. **Section 35 Definition of Done Checklist**:
   - Click **Load DoD Requirements Checklist** in `#tab-definition-of-done-step35`.
   - All 27 canonical stages and both recovery scenarios render with green `✓ REQUIREMENT SATISFIED` badges.
