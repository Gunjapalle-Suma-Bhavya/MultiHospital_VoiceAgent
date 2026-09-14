"""
Comprehensive Verification Test Suite for:
1. Questionnaire (5 items)
   - Doctor-created questions
   - Question flow
   - Voice-based answers
   - Structured response storage
   - Doctor response viewing
2. Workflow (7 items)
   - Appointment confirmation workflow
   - Questionnaire workflow
   - Reminder workflow
   - Failure/retry workflow
   - Notification workflow
   - EHR synchronization workflow
   - Workflow status tracking
3. Analytics (8 items)
   - Appointments
   - AI calls
   - Booking success
   - Questionnaire completion
   - Workflow activity
   - EHR integration activity
   - Basic operational metrics
   - Audit logs
4. AI Operations (7 items)
   - AI usage metrics
   - Capability execution tracking
   - EHR integration tracking
   - Basic evaluation
   - Latency measurement
   - Failure tracking
   - Traceable operations
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.database.config import get_db, SessionLocal
from app.database.models import (
    Hospital, Doctor, PatientProfile, Appointment, AppointmentStatus, HospitalStatus,
    DoctorApprovedQuestion, PatientQuestionnaireResponse, WorkflowInstance,
    WorkflowStatus, AIUsageRecord, EHRSyncLog
)

client = TestClient(app)


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture(scope="module")
def setup_test_entities():
    db = SessionLocal()
    uid = uuid.uuid4().hex[:6]
    hosp_id = f"HOSP-TEST-{uid}"
    doc_id = f"DOC-TEST-{uid}"
    pat_id = f"PAT-TEST-{uid}"
    phone = f"+1-555-{uid}"
    apt_id = f"APT-TEST-{uid}"

    hosp = Hospital(
        id=hosp_id,
        name=f"Memorial Hospital {uid}",
        code=f"MH-{uid}",
        is_active=True,
        hospital_status=HospitalStatus.APPROVED
    )
    db.add(hosp)

    doc = Doctor(
        id=doc_id,
        name=f"Dr. Test Specialist {uid}",
        specialty="Orthopedics",
        hospital_id=hosp_id,
        is_active=True
    )
    db.add(doc)

    pat = PatientProfile(
        id=pat_id,
        phone_number=phone,
        full_name=f"Patient {uid}",
        date_of_birth=datetime(1985, 5, 15).date(),
        communication_preference="SMS"
    )
    db.add(pat)


    apt = Appointment(
        id=apt_id,
        doctor_id=doc_id,
        hospital_id=hosp_id,
        patient_name=pat.full_name,
        patient_phone=phone,
        start_datetime=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2),
        end_datetime=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2, minutes=30),
        status=AppointmentStatus.CONFIRMED
    )
    db.add(apt)
    db.commit()


    yield {
        "hosp_id": hosp_id,
        "doc_id": doc_id,
        "pat_id": pat_id,
        "phone": phone,
        "apt_id": apt_id
    }

    db.close()


# =============================================================================
# PILLAR 1: QUESTIONNAIRE (5 ITEMS)
# =============================================================================
class TestQuestionnairePillar:
    def test_01_doctor_created_questions(self, setup_test_entities):
        doc_id = setup_test_entities["doc_id"]
        resp = client.post("/api/v1/questionnaires/configure-doctor-question", json={
            "doctor_id": doc_id,
            "question_text": "Do you feel tingling or numbness in your fingertips?",
            "question_type": "YES_NO"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["doctor_id"] == doc_id
        assert data["question_text"] == "Do you feel tingling or numbness in your fingertips?"
        assert data["question_type"] == "YES_NO"

    def test_02_question_flow_resolution(self):
        resp = client.get("/api/v1/questionnaires/applicable?specialty=Orthopedics")
        assert resp.status_code == 200
        data = resp.json()
        assert "questionnaire" in data
        assert "conversational_intro" in data
        assert len(data["questionnaire"]["questions"]) > 0

    def test_03_voice_based_answers_parsing(self):
        # Spoken natural conversational response should parse into structured YES/NO (boolean True)
        resp = client.post("/api/v1/questionnaires/parse-response", json={
            "question_id": "q-rotator-1",
            "question_text": "Does it hurt when you raise your arm overhead?",
            "response_type": "YES_NO",
            "user_utterance": "Yeah absolutely, it hurts really bad"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["parsed_value"] is True

    def test_04_structured_response_storage(self, setup_test_entities):
        pat_id = setup_test_entities["pat_id"]
        apt_id = setup_test_entities["apt_id"]
        resp = client.post(f"/api/v1/patients/{pat_id}/questionnaires/submit", json={
            "questionnaire_id": "Q-ORTHO-TEST",
            "appointment_id": apt_id,
            "answers": {
                "q-rotator-1": "Yes",
                "pain_level": "8",
                "onset": "3 days ago"
            }
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "response_id" in data
        assert data["patient_id"] == pat_id

        # Verify retrieval via appointment responses endpoint
        apt_resp = client.get(f"/api/v1/questionnaires/appointments/{apt_id}/responses")
        assert apt_resp.status_code == 200
        apt_data = apt_resp.json()
        assert apt_data["has_responses"] is True
        assert apt_data["answers"]["q-rotator-1"] == "Yes"
        assert apt_data["answers"]["pain_level"] == "8"

    def test_05_doctor_response_viewing(self, setup_test_entities):
        doc_id = setup_test_entities["doc_id"]
        apt_id = setup_test_entities["apt_id"]
        # Clinician 360-degree appointment details view
        resp = client.get(f"/api/v1/doctor-dashboard/{doc_id}/appointments/{apt_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["appointment_id"] == apt_id
        assert data["pre_visit_questionnaire"]["has_submitted"] is True
        assert "q-rotator-1" in data["pre_visit_questionnaire"]["intake_answers"]

    def test_06_in_session_conversational_questionnaire_flow(self, setup_test_entities):
        from app.agent.patient_access_agent import AIPatientAccessAgent
        from app.database.config import SessionLocal
        from app.database.models import Appointment

        db = SessionLocal()
        hosp_id = setup_test_entities["hosp_id"]
        doc_id = setup_test_entities["doc_id"]
        phone = setup_test_entities["phone"]

        # Ensure doctor has an approved question configured
        client.post("/api/v1/questionnaires/configure-doctor-question", json={
            "doctor_id": doc_id,
            "question_text": "Do you experience knee stiffness in the morning?",
            "question_type": "YES_NO"
        })
        db.expire_all()

        agent = AIPatientAccessAgent(db)

        # Turn 1: Patient requests to book consultation
        res1 = agent.process_patient_turn(
            channel="web_voice",
            patient_identifier=phone,
            user_utterance="I want to book an appointment with my doctor tomorrow morning",
            hospital_id=hosp_id,
            doctor_id=doc_id
        )

        assert res1["status"] == "SUCCESS"
        assert "QUESTIONNAIRE_PROMPTED" in res1["capabilities_invoked"]
        assert any(q in res1["speech_response"] for q in [
            "Do you feel tingling or numbness in your fingertips?",
            "Do you experience knee stiffness in the morning?"
        ])

        # Find the created appointment
        created_appt = db.query(Appointment).filter(
            Appointment.patient_phone == phone,
            Appointment.doctor_id == doc_id
        ).order_by(Appointment.created_at.desc()).first()
        assert created_appt is not None

        # Turn 2: Patient speaks their answer to the doctor's questionnaire question
        res2 = agent.process_patient_turn(
            channel="web_voice",
            patient_identifier=phone,
            user_utterance="No tingling, but my fingers feel slightly stiff in cold weather",
            hospital_id=hosp_id,
            doctor_id=doc_id
        )

        assert res2["status"] == "SUCCESS"
        assert "QUESTIONNAIRE_PARSED" in res2["capabilities_invoked"]
        assert "STRUCTURED_RESPONSE_STORED" in res2["capabilities_invoked"]
        assert "recorded" in res2["speech_response"].lower()

        # Doctor 360-degree review: Doctor views the submitted response attached to the appointment
        resp_doc = client.get(f"/api/v1/doctor-dashboard/{doc_id}/appointments/{created_appt.id}")
        assert resp_doc.status_code == 200
        doc_data = resp_doc.json()
        assert doc_data["pre_visit_questionnaire"]["has_submitted"] is True
        answers = doc_data["pre_visit_questionnaire"]["intake_answers"]
        assert len(answers) > 0
        db.close()


# =============================================================================
# PILLAR 2: WORKFLOW (7 ITEMS)
# =============================================================================
class TestWorkflowPillar:
    def test_01_appointment_confirmation_workflow(self, setup_test_entities):
        apt_id = setup_test_entities["apt_id"]
        resp = client.post("/api/v1/workflows/trigger", json={
            "workflow_name": "POST_BOOKING_WORKFLOW",
            "appointment_id": apt_id
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["workflow_name"] == "POST_BOOKING_WORKFLOW"
        assert data["status"] in ["COMPLETED", "RUNNING"]
        assert "workflow_id" in data

    def test_02_questionnaire_workflow(self, setup_test_entities):
        apt_id = setup_test_entities["apt_id"]
        resp = client.post("/api/v1/workflows/trigger", json={
            "workflow_name": "QUESTIONNAIRE_REMINDER_WORKFLOW",
            "appointment_id": apt_id,
            "questionnaire_id": "Q-ORTHO-TEST"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["workflow_name"] == "QUESTIONNAIRE_REMINDER_WORKFLOW"
        assert data["status"] == "WAITING"

    def test_03_reminder_workflow_and_execution(self, setup_test_entities):
        apt_id = setup_test_entities["apt_id"]
        resp = client.post("/api/v1/workflows/trigger", json={
            "workflow_name": "APPOINTMENT_REMINDER_WORKFLOW",
            "appointment_id": apt_id,
            "delay_minutes": -1  # due immediately
        })
        assert resp.status_code == 200
        wf_id = resp.json()["workflow_id"]

        # Trigger execution of due scheduled workflows
        exec_resp = client.post("/api/v1/workflows/execute-due")
        assert exec_resp.status_code == 200
        assert "executed_due_workflows" in exec_resp.json()

        # Verify status moved to COMPLETED
        hist_resp = client.get(f"/api/v1/workflows/instances/{wf_id}")
        assert hist_resp.status_code == 200
        assert hist_resp.json()["status"] == "COMPLETED"

    def test_04_failure_and_retry_workflow(self, setup_test_entities):
        apt_id = setup_test_entities["apt_id"]
        resp = client.post("/api/v1/workflows/trigger", json={
            "workflow_name": "FAILED_BOOKING_RECOVERY_WORKFLOW",
            "appointment_id": apt_id,
            "error_reason": "FHIR Endpoint 503 Service Unavailable"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["workflow_name"] == "FAILED_BOOKING_RECOVERY_WORKFLOW"
        assert data["status"] in ["COMPLETED", "ESCALATED"]

    def test_05_notification_workflow_logs(self, setup_test_entities):
        apt_id = setup_test_entities["apt_id"]
        # Trigger post booking workflow which contains notification dispatch
        resp = client.post("/api/v1/workflows/trigger", json={
            "workflow_name": "POST_BOOKING_WORKFLOW",
            "appointment_id": apt_id
        })
        wf_id = resp.json()["workflow_id"]
        hist_resp = client.get(f"/api/v1/workflows/instances/{wf_id}")
        assert hist_resp.status_code == 200
        step_names = [s["step_name"] for s in hist_resp.json()["step_logs"]]
        assert "NOTIFY_DOCTOR" in step_names

    def test_06_ehr_synchronization_workflow_step(self, setup_test_entities):
        apt_id = setup_test_entities["apt_id"]
        resp = client.post("/api/v1/workflows/trigger", json={
            "workflow_name": "POST_BOOKING_WORKFLOW",
            "appointment_id": apt_id
        })
        wf_id = resp.json()["workflow_id"]
        hist_resp = client.get(f"/api/v1/workflows/instances/{wf_id}")
        step_names = [s["step_name"] for s in hist_resp.json()["step_logs"]]
        assert "SYNCHRONIZE_EHR" in step_names

    def test_07_workflow_status_tracking(self):
        # Test listing workflow instances
        resp = client.get("/api/v1/workflows/instances?limit=20")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "instances" in data
        assert len(data["instances"]) > 0


# =============================================================================
# PILLAR 3: ANALYTICS (8 ITEMS)
# =============================================================================
class TestAnalyticsPillar:
    def test_01_to_07_platform_dashboard_metrics(self):
        resp = client.get("/api/v1/analytics/dashboard/platform")
        assert resp.status_code == 200
        data = resp.json()

        # 1. Appointments
        assert "total_appointments" in data
        assert "appointments_by_hospital" in data
        assert isinstance(data["total_appointments"], int)

        # 2. AI calls
        assert "ai_call_volume" in data
        assert isinstance(data["ai_call_volume"], int)

        # 3. Booking success
        assert "appointment_success_rate" in data
        assert "ai_booking_rate" in data
        assert isinstance(data["appointment_success_rate"], (int, float))

        # 4. Questionnaire completion
        assert "questionnaire_completion" in data
        assert isinstance(data["questionnaire_completion"], (int, float))

        # 5. Workflow activity
        assert "workflow_success_rate" in data
        assert "workflow_failure_rate" in data

        # 6. EHR integration activity
        assert "ehr_integration_success_rate" in data
        assert "ehr_integration_failure_rate" in data
        assert "ehr_verification_success" in data

        # 7. Basic operational metrics
        assert "total_hospitals" in data
        assert "active_hospitals" in data
        assert "total_doctors" in data
        assert "total_patients" in data

    def test_08_audit_logs(self):
        # Record an auditable event
        ev_resp = client.post("/api/v1/audit/events", json={
            "event_type": "CALL_STARTED",
            "category": "OPERATIONAL_MONITORING",
            "actor_role": "SYSTEM",
            "payload": {"test": True, "note": "Verified intake flow"}
        })
        assert ev_resp.status_code in [200, 201]

        # Retrieve audit trail
        trail_resp = client.get("/api/v1/audit/trail?limit=10")
        assert trail_resp.status_code == 200
        trail_data = trail_resp.json()
        assert "events" in trail_data
        assert len(trail_data["events"]) > 0

        # Retrieve audit summary
        sum_resp = client.get("/api/v1/audit/summary")
        assert sum_resp.status_code == 200
        assert "total_audit_events" in sum_resp.json()


# =============================================================================
# PILLAR 4: AI OPERATIONS (7 ITEMS)
# =============================================================================
class TestAIOperationsPillar:
    def test_01_ai_usage_metrics(self):
        # Record AI usage
        rec_resp = client.post("/api/v1/ai/usage/record", json={
            "session_id": "SES-AI-OPS-TEST",
            "model_name": "gemini-2.0-flash",
            "prompt_tokens": 120,
            "completion_tokens": 45,
            "processing_duration_ms": 148.5,
            "intent_name": "schedule_appointment",
            "estimated_cost_usd": 0.00015
        })
        assert rec_resp.status_code in [200, 201]

        # Retrieve usage summary
        sum_resp = client.get("/api/v1/ai/usage/summary")
        assert sum_resp.status_code == 200
        data = sum_resp.json()
        assert "total_ai_requests" in data
        assert "total_input_tokens" in data
        assert "total_output_tokens" in data
        assert "total_tokens" in data

    def test_02_capability_execution_tracking(self):
        resp = client.get("/api/v1/ai/capabilities")
        assert resp.status_code == 200
        caps = resp.json()["registered_capabilities"]
        assert len(caps) >= 15
        # Execute capability and track result
        exec_resp = client.post("/api/v1/capabilities/execute", json={
            "capability_name": "search_hospitals",
            "arguments": {"query": "Memorial"}
        })
        assert exec_resp.status_code == 200
        assert exec_resp.json()["capability_name"] == "search_hospitals"

    def test_03_ehr_integration_tracking(self):
        resp = client.get("/api/v1/ehr/sync-logs?limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert "sync_logs" in data and len(data["sync_logs"]) > 0

    def test_04_basic_evaluation(self):
        eval_resp = client.post("/api/v1/ai/evaluations/run", json={})
        assert eval_resp.status_code == 200
        data = eval_resp.json()
        assert "evaluation_id" in data

        res_resp = client.get("/api/v1/ai/evaluations/results?limit=5")
        assert res_resp.status_code == 200

    def test_05_latency_measurement(self):
        # Observability latency telemetry breakdown
        analytics_resp = client.get("/api/v1/observability/analytics")
        assert analytics_resp.status_code == 200
        data = analytics_resp.json()
        assert "p50_latency_seconds" in data or "total_traces" in data

    def test_06_failure_tracking(self, setup_test_entities):
        apt_id = setup_test_entities["apt_id"]
        # Trigger failed recovery workflow and track failure classification
        rec_resp = client.post("/api/v1/workflows/trigger", json={
            "workflow_name": "FAILED_BOOKING_RECOVERY_WORKFLOW",
            "appointment_id": apt_id,
            "error_reason": "SocketTimeout: HL7 Bridge Unreachable"
        })
        assert rec_resp.status_code == 200
        wf_id = rec_resp.json()["workflow_id"]
        hist_resp = client.get(f"/api/v1/workflows/instances/{wf_id}")
        assert hist_resp.status_code == 200
        assert hist_resp.json()["workflow_name"] == "FAILED_BOOKING_RECOVERY_WORKFLOW"

    def test_07_traceable_operations(self):
        # Trace lifecycle start
        start_resp = client.post("/api/v1/observability/traces/start", json={
            "session_id": f"SES-TRACE-{uuid.uuid4().hex[:6]}",
            "operation_name": "VOICE_CONSULTATION_LIFECYCLE",
            "metadata": {"source": "unit_test"}
        })

        assert start_resp.status_code == 200
        t_data = start_resp.json()
        trace_id = t_data["trace_id"]
        assert "correlation_id" in t_data

        # Trace details retrieval
        g_resp = client.get(f"/api/v1/observability/traces/{trace_id}")
        assert g_resp.status_code == 200
        assert g_resp.json()["trace_id"] == trace_id
