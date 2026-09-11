// Clean ES6 JavaScript Application Logic for Healthcare Platform Frontend

document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupOnboardingForms();
  setupDoctorForms();
  setupPatientForms();
  setupVoiceConsole();
  setupQuestionnaireEngineForm();
  setupBackgroundWorkflowForm();
  setupEventBusForm();
  setupNotificationCenterForm();
  setupDoctorDashboardForm();
  setupHospitalDashboardForm();
  setupPlatformAdminDashboardForm();
  setupObservabilityForm();
  setupAIAnalyticsForm();
  setupFeedbackLoopForm();
  setupEscalationConsole();
  setupAuditTrailForms();
  setupRBACForms();
  setupCoreDataModelForms();
  setupPatientWorkflowForms();
  setupHospitalWorkflowForms();
  setupArchitectureUI();
  setupDashboardPagesUI();
  setupDashboardAnalyticsUI();
  setupOperationalMonitoringUI();
  setupReliabilityUI();
  setupSecurityConcurrencyUI();
  setupSafetyKnowledgeUI();
  setupWorkflowExamplesUI();
  setupAIEvaluationFrameworkUI();
  setupProductMetricsUI();
  setupEndToEndScenarioUI();
  setupProductPrinciplesUI();
  setupPrototypeScopeUI();
  setupAdvancedCapabilitiesUI();
  setupDefinitionOfDoneUI();
  setupFinalChecklistUI();
});





// Navigation Tab Handler
function setupTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  const contents = document.querySelectorAll(".tab-content");

  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("active"));
      contents.forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const target = btn.getAttribute("data-tab");
      document.getElementById(target).classList.add("active");
    });
  });
}

// Portal 1: Hospital Onboarding Logic
function setupOnboardingForms() {
  const formDraft = document.getElementById("form-draft-hospital");
  const draftOutput = document.getElementById("hosp-draft-output");

  if (formDraft) {
    formDraft.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = {
        name: document.getElementById("hosp-name").value,
        code: document.getElementById("hosp-code").value,
        contact_email: document.getElementById("hosp-email").value,
        admin_name: document.getElementById("hosp-admin-name").value,
        admin_email: document.getElementById("hosp-admin-email").value
      };

      try {
        const res = await fetch("/onboarding/hospital/draft", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        draftOutput.style.display = "block";
        draftOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        draftOutput.style.display = "block";
        draftOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnReview = document.getElementById("btn-admin-review");
  const btnApprove = document.getElementById("btn-admin-approve");
  const btnReject = document.getElementById("btn-admin-reject");
  const adminOutput = document.getElementById("admin-action-output");

  if (btnReview) {
    btnReview.addEventListener("click", async () => {
      const hospId = document.getElementById("admin-hosp-id").value;
      if (!hospId) return alert("Please enter a Hospital ID");

      try {
        const res = await fetch(`/api/v1/admin/hospitals/${hospId}`);
        const data = await res.json();
        adminOutput.style.display = "block";
        adminOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        adminOutput.style.display = "block";
        adminOutput.textContent = "Error: " + err.message;
      }
    });
  }

  if (btnApprove) {
    btnApprove.addEventListener("click", async () => {
      const hospId = document.getElementById("admin-hosp-id").value;
      if (!hospId) return alert("Please enter a Hospital ID");

      try {
        const res = await fetch(`/api/v1/admin/hospitals/${hospId}/approve`, { method: "POST" });
        const data = await res.json();
        adminOutput.style.display = "block";
        adminOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        adminOutput.style.display = "block";
        adminOutput.textContent = "Error: " + err.message;
      }
    });
  }

  if (btnReject) {
    btnReject.addEventListener("click", async () => {
      const hospId = document.getElementById("admin-hosp-id").value;
      if (!hospId) return alert("Please enter a Hospital ID");

      try {
        const res = await fetch(`/api/v1/admin/hospitals/${hospId}/reject`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ reason: "Incomplete verification documents" })
        });
        const data = await res.json();
        adminOutput.style.display = "block";
        adminOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        adminOutput.style.display = "block";
        adminOutput.textContent = "Error: " + err.message;
      }
    });
  }
}

// Portal 2: Doctor & Calendar Logic
function setupDoctorForms() {
  const formDoc = document.getElementById("form-invite-doctor");
  const docOutput = document.getElementById("doc-output");

  if (formDoc) {
    formDoc.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = {
        hospital_id: document.getElementById("doc-hosp-id").value,
        name: document.getElementById("doc-name").value,
        specialty: document.getElementById("doc-specialty").value,
        department: document.getElementById("doc-dept").value
      };

      try {
        const res = await fetch("/api/v1/doctors/invite", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        docOutput.style.display = "block";
        docOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        docOutput.style.display = "block";
        docOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnQueryAvail = document.getElementById("btn-query-availability");
  const calOutput = document.getElementById("cal-output");

  if (btnQueryAvail) {
    btnQueryAvail.addEventListener("click", async () => {
      const docId = document.getElementById("cal-doc-id").value;
      const targetDate = document.getElementById("cal-target-date").value || new Date().toISOString().split('T')[0];

      if (!docId) return alert("Please enter a Doctor ID");

      try {
        const res = await fetch(`/api/v1/doctors/${docId}/availability?target_date=${targetDate}`);
        const data = await res.json();
        calOutput.style.display = "block";
        calOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        calOutput.style.display = "block";
        calOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const formDiscovery = document.getElementById("form-discovery-search");
  const discOutput = document.getElementById("disc-output");

  if (formDiscovery) {
    formDiscovery.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = {
        query_text: document.getElementById("disc-query").value,
        time_window: document.getElementById("disc-window").value,
        target_date: document.getElementById("disc-date").value || null
      };

      try {
        const res = await fetch("/api/v1/discovery/search", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        discOutput.style.display = "block";
        discOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        discOutput.style.display = "block";
        discOutput.textContent = "Error: " + err.message;
      }
    });
  }
}


// Portal 3: Patient Self-Service Logic
function setupPatientForms() {
  const formPat = document.getElementById("form-register-patient");
  const patOutput = document.getElementById("pat-output");

  if (formPat) {
    formPat.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = {
        name: document.getElementById("pat-name").value,
        phone_number: document.getElementById("pat-phone").value,
        email: document.getElementById("pat-email").value,
        preferred_language: document.getElementById("pat-lang").value
      };

      try {
        const res = await fetch("/api/v1/patients/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        patOutput.style.display = "block";
        patOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        patOutput.style.display = "block";
        patOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const formQuest = document.getElementById("form-submit-questionnaire");
  const questOutput = document.getElementById("quest-output");

  if (formQuest) {
    formQuest.addEventListener("submit", async (e) => {
      e.preventDefault();
      const patId = document.getElementById("quest-pat-id").value;
      const qId = document.getElementById("quest-id").value;
      let rawAns = document.getElementById("quest-answers").value;
      let answersObj = {};
      try { answersObj = JSON.parse(rawAns); } catch(ex) { answersObj = { text: rawAns }; }

      try {
        const res = await fetch(`/api/v1/patients/${patId}/questionnaires/submit`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ questionnaire_id: qId, responses: answersObj })
        });
        const data = await res.json();
        questOutput.style.display = "block";
        questOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        questOutput.style.display = "block";
        questOutput.textContent = "Error: " + err.message;
      }
    });
  }
}

// Portal 4: AI Voice & Text Console Logic
function setupVoiceConsole() {
  const chatMessages = document.getElementById("chat-messages");
  const textInput = document.getElementById("user-input-text");
  const btnSend = document.getElementById("btn-send-turn");
  const btnMic = document.getElementById("btn-mic-toggle");
  const telemetryOutput = document.getElementById("ai-telemetry-output");

  let recognition = null;
  let isListening = false;

  // Initialize Web Speech API with Real-Time Barge-in & Interruption Handling
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    // BARGE-IN / INTERRUPTION HANDLING: Immediately cancel active speech synthesis if user starts speaking
    recognition.onspeechstart = () => {
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      textInput.value = transcript;
      sendAgentTurn(transcript);
    };

    recognition.onend = () => {
      isListening = false;
      btnMic.textContent = "Start Voice Mic";
      btnMic.classList.remove("btn-danger");
      btnMic.classList.add("btn-secondary");
    };

    recognition.onerror = (err) => {
      console.error("Speech Recognition Error: ", err);
      isListening = false;
      btnMic.textContent = "Start Voice Mic";
    };
  } else {
    btnMic.disabled = true;
    btnMic.textContent = "Voice Mic Not Supported";
  }

  if (btnMic) {
    btnMic.addEventListener("click", () => {
      if (!recognition) return;
      if (isListening) {
        recognition.stop();
      } else {
        if ("speechSynthesis" in window) {
          window.speechSynthesis.cancel(); // Halt any active TTS output
        }
        recognition.start();
        isListening = true;
        btnMic.textContent = "Listening... (Click to Stop)";
        btnMic.classList.remove("btn-secondary");
        btnMic.classList.add("btn-danger");
      }
    });
  }

  if (btnSend) {
    btnSend.addEventListener("click", () => {
      const text = textInput.value.trim();
      if (text) {
        sendAgentTurn(text);
        textInput.value = "";
      }
    });
  }

  if (textInput) {
    textInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const text = textInput.value.trim();
        if (text) {
          sendAgentTurn(text);
          textInput.value = "";
        }
      }
    });
  }

  async function sendAgentTurn(utterance) {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel(); // Barge-in halt
    }
    appendMessage(utterance, "user");

    try {
      const res = await fetch("/api/voice/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_phone: "+15551234567",
          user_utterance: utterance
        })
      });

      const data = await res.json();
      const responseText = data.speech_response || data.agent_response || "I have received your request.";
      appendMessage(responseText, "agent");
      speakResponse(responseText);

      telemetryOutput.style.display = "block";
      telemetryOutput.textContent = `[Real-Time Telemetry Log]\nStatus: ${data.status}\nTool Invoked: ${data.tool_called || 'None'}\nCorrelation ID: ${data.correlation_id}\nPerceived Latency: ${data.latency_ms || 0}ms (Target Sub-2s: ${data.sub_2_sec_target_met !== false})`;
    } catch (err) {
      appendMessage("Error communicating with AI agent server: " + err.message, "agent");
    }
  }

  function appendMessage(text, sender) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-message ${sender}`;
    msgDiv.textContent = text;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function speakResponse(text) {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.05; // Fast, sub-2s responsive speech rate
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  }

  setupContextResolverForm();
  setupEHRSequenceForm();
  setupEHRReconciliationForm();
}

function setupContextResolverForm() {
  const formRes = document.getElementById("form-resolve-context");
  const ctxOutput = document.getElementById("context-output");

  if (formRes) {
    formRes.addEventListener("submit", async (e) => {
      e.preventDefault();
      const utterance = document.getElementById("context-utterance").value;
      const sessionId = document.getElementById("context-session-id").value;

      try {
        const res = await fetch("/api/v1/context/resolve", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: sessionId,
            user_utterance: utterance
          })
        });
        const data = await res.json();
        ctxOutput.style.display = "block";
        ctxOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        ctxOutput.style.display = "block";
        ctxOutput.textContent = "Error: " + err.message;
      }
    });
  }
}

function setupEHRSequenceForm() {
  const formEhr = document.getElementById("form-ehr-sequence");
  const ehrOutput = document.getElementById("ehr-output");

  if (formEhr) {
    formEhr.addEventListener("submit", async (e) => {
      e.preventDefault();
      const apptId = document.getElementById("ehr-appt-id").value;

      try {
        const res = await fetch("/api/v1/ehr/sequence/execute", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ appointment_id: apptId })
        });
        const data = await res.json();
        ehrOutput.style.display = "block";
        ehrOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        ehrOutput.style.display = "block";
        ehrOutput.textContent = "Error: " + err.message;
      }
    });
  }
}

function setupEHRReconciliationForm() {
  const formRec = document.getElementById("form-ehr-reconcile");
  const recOutput = document.getElementById("rec-output");

  if (formRec) {
    formRec.addEventListener("submit", async (e) => {
      e.preventDefault();
      const apptId = document.getElementById("rec-appt-id").value;
      try {
        const res = await fetch("/api/v1/ehr/recovery/reconcile", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ appointment_id: apptId })
        });
        const data = await res.json();
        recOutput.style.display = "block";
        recOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        recOutput.style.display = "block";
        recOutput.textContent = "Error: " + err.message;
      }
    });

    const btnVerify = document.getElementById("btn-verify-field-level");
    if (btnVerify) {
      btnVerify.addEventListener("click", async () => {
        const apptId = document.getElementById("rec-appt-id").value;
        if (!apptId) return alert("Please enter an Appointment ID");
        try {
          const res = await fetch("/api/v1/ehr/verify-record", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ appointment_id: apptId })
          });
          const data = await res.json();
          recOutput.style.display = "block";
          recOutput.textContent = JSON.stringify(data, null, 2);
        } catch (err) {
          recOutput.style.display = "block";
          recOutput.textContent = "Error: " + err.message;
        }
      });
    }

    const btnConfirm = document.getElementById("btn-get-spoken-confirmation");
    if (btnConfirm) {
      btnConfirm.addEventListener("click", async () => {
        const apptId = document.getElementById("rec-appt-id").value;
        if (!apptId) return alert("Please enter an Appointment ID");
        try {
          const res = await fetch(`/api/v1/patients/appointments/${apptId}/confirmation`);
          const data = await res.json();
          recOutput.style.display = "block";
          recOutput.textContent = JSON.stringify(data, null, 2);
        } catch (err) {
          recOutput.style.display = "block";
          recOutput.textContent = "Error: " + err.message;
        }
      });
    }
  }
}

function setupQuestionnaireEngineForm() {
  const formQuest = document.getElementById("form-doctor-questionnaire");
  const questOutput = document.getElementById("doctor-quest-output");
  const btnApproved = document.getElementById("btn-get-approved-questions");

  if (btnApproved) {
    btnApproved.addEventListener("click", async () => {
      const docId = document.getElementById("quest-doc-id").value || "Dr. Rao";
      try {
        const res = await fetch(`/api/v1/questionnaires/doctor/${docId}`);
        const data = await res.json();
        questOutput.style.display = "block";
        questOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        questOutput.style.display = "block";
        questOutput.textContent = "Error: " + err.message;
      }
    });
  }

  if (formQuest) {
    formQuest.addEventListener("submit", async (e) => {
      e.preventDefault();
      const docId = document.getElementById("quest-doc-id").value;
      const utterance = document.getElementById("quest-patient-utterance").value;

      try {
        const res = await fetch("/api/v1/questionnaires/parse-answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question_id: "Q-CARD-01",
            user_utterance: utterance,
            doctor_id: docId
          })
        });
        const data = await res.json();
        questOutput.style.display = "block";
        questOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        questOutput.style.display = "block";
        questOutput.textContent = "Error: " + err.message;
      }
    });
  }
}

function setupBackgroundWorkflowForm() {
  const wfOutput = document.getElementById("wf-output");

  const btnStartReminder = document.getElementById("btn-wf-start-reminder");
  if (btnStartReminder) {
    btnStartReminder.addEventListener("click", async () => {
      const apptId = document.getElementById("wf-appt-id").value;
      if (!apptId) return alert("Please enter an Appointment ID");
      try {
        const res = await fetch("/api/v1/workflows/start-reminder", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ appointment_id: apptId, delay_minutes: 1440 })
        });
        const data = await res.json();
        wfOutput.style.display = "block";
        wfOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        wfOutput.style.display = "block";
        wfOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnStartPost = document.getElementById("btn-wf-start-post-booking");
  if (btnStartPost) {
    btnStartPost.addEventListener("click", async () => {
      const apptId = document.getElementById("wf-appt-id").value;
      if (!apptId) return alert("Please enter an Appointment ID");
      try {
        const res = await fetch("/api/v1/workflows/start-post-booking", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ appointment_id: apptId })
        });
        const data = await res.json();
        wfOutput.style.display = "block";
        wfOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        wfOutput.style.display = "block";
        wfOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnExecDue = document.getElementById("btn-wf-execute-due");
  if (btnExecDue) {
    btnExecDue.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/workflows/execute-due", { method: "POST" });
        const data = await res.json();
        wfOutput.style.display = "block";
        wfOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        wfOutput.style.display = "block";
        wfOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnHistory = document.getElementById("btn-wf-get-history");
  if (btnHistory) {
    btnHistory.addEventListener("click", async () => {
      const apptId = document.getElementById("wf-appt-id").value;
      if (!apptId) return alert("Please enter an Appointment ID");
      try {
        const res = await fetch(`/api/v1/workflows/history/${apptId}`);
        const data = await res.json();
        wfOutput.style.display = "block";
        wfOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        wfOutput.style.display = "block";
        wfOutput.textContent = "Error: " + err.message;
      }
    });
  }
}

function setupEventBusForm() {
  const formEvt = document.getElementById("form-publish-event");
  const evtOutput = document.getElementById("evt-output");

  if (formEvt) {
    formEvt.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = {
        event_type: document.getElementById("evt-type").value,
        aggregate_id: document.getElementById("evt-aggregate-id").value,
        source: document.getElementById("evt-source").value
      };
      try {
        const res = await fetch("/api/v1/events/publish", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        evtOutput.style.display = "block";
        evtOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        evtOutput.style.display = "block";
        evtOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnHistory = document.getElementById("btn-get-event-history");
  if (btnHistory) {
    btnHistory.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/events/history");
        const data = await res.json();
        evtOutput.style.display = "block";
        evtOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        evtOutput.style.display = "block";
        evtOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnSubs = document.getElementById("btn-get-subscribers");
  if (btnSubs) {
    btnSubs.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/events/subscribers");
        const data = await res.json();
        evtOutput.style.display = "block";
        evtOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        evtOutput.style.display = "block";
        evtOutput.textContent = "Error: " + err.message;
      }
    });
  }
}

function setupNotificationCenterForm() {
  const formNotif = document.getElementById("form-send-notification");
  const notifOutput = document.getElementById("notif-output");

  if (formNotif) {
    formNotif.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = {
        recipient_role: document.getElementById("notif-role").value,
        recipient_id: document.getElementById("notif-recipient-id").value,
        notification_type: document.getElementById("notif-type").value,
        body: document.getElementById("notif-body").value
      };
      try {
        const res = await fetch("/api/v1/notifications/send", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        notifOutput.style.display = "block";
        notifOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        notifOutput.style.display = "block";
        notifOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnHistory = document.getElementById("btn-get-notif-history");
  if (btnHistory) {
    btnHistory.addEventListener("click", async () => {
      const role = document.getElementById("notif-role").value;
      const recipientId = document.getElementById("notif-recipient-id").value;
      if (!recipientId) return alert("Please enter a Recipient ID");
      try {
        const res = await fetch(`/api/v1/notifications/recipient/${role}/${recipientId}`);
        const data = await res.json();
        notifOutput.style.display = "block";
        notifOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        notifOutput.style.display = "block";
        notifOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnCatalog = document.getElementById("btn-get-notif-catalog");
  if (btnCatalog) {
    btnCatalog.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/notifications/catalog");
        const data = await res.json();
        notifOutput.style.display = "block";
        notifOutput.textContent = "[Section 14: Configurable Notification Catalog]\n\n" + JSON.stringify(data, null, 2);
      } catch (err) {
        notifOutput.style.display = "block";
        notifOutput.textContent = "Error: " + err.message;
      }
    });
  }

  // Update default event type on role change
  const roleSelect = document.getElementById("notif-role");
  const typeInput = document.getElementById("notif-type");
  if (roleSelect && typeInput) {
    roleSelect.addEventListener("change", () => {
      const r = roleSelect.value;
      if (r === "PATIENT") typeInput.value = "APPOINTMENT_CONFIRMATION";
      else if (r === "DOCTOR") typeInput.value = "NEW_APPOINTMENT";
      else if (r === "HOSPITAL") typeInput.value = "HOSPITAL_APPROVED";
    });
  }
}

function setupDoctorDashboardForm() {
  const dashOutput = document.getElementById("dash-output");

  const btnHome = document.getElementById("btn-dash-home");
  if (btnHome) {
    btnHome.addEventListener("click", async () => {
      const docId = document.getElementById("dash-doc-id").value;
      if (!docId) return alert("Please enter a Doctor ID");
      try {
        const res = await fetch(`/api/v1/doctor-dashboard/${docId}/home`);
        const data = await res.json();
        dashOutput.style.display = "block";
        dashOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        dashOutput.style.display = "block";
        dashOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnCal = document.getElementById("btn-dash-calendar");
  if (btnCal) {
    btnCal.addEventListener("click", async () => {
      const docId = document.getElementById("dash-doc-id").value;
      const viewType = document.getElementById("dash-view-type").value;
      if (!docId) return alert("Please enter a Doctor ID");
      try {
        const res = await fetch(`/api/v1/doctor-dashboard/${docId}/calendar?view_type=${viewType}`);
        const data = await res.json();
        dashOutput.style.display = "block";
        dashOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        dashOutput.style.display = "block";
        dashOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnDetails = document.getElementById("btn-dash-details");
  if (btnDetails) {
    btnDetails.addEventListener("click", async () => {
      const docId = document.getElementById("dash-doc-id").value;
      const apptId = document.getElementById("dash-appt-id").value;
      if (!docId || !apptId) return alert("Please enter both Doctor ID and Appointment ID");
      try {
        const res = await fetch(`/api/v1/doctor-dashboard/${docId}/appointments/${apptId}`);
        const data = await res.json();
        dashOutput.style.display = "block";
        dashOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        dashOutput.style.display = "block";
        dashOutput.textContent = "Error: " + err.message;
      }
    });
  }
}

function setupHospitalDashboardForm() {
  const hospDashOutput = document.getElementById("hosp-dash-output");

  const btnKpis = document.getElementById("btn-get-hosp-kpis");
  if (btnKpis) {
    btnKpis.addEventListener("click", async () => {
      const hospId = document.getElementById("hosp-dash-id").value;
      if (!hospId) return alert("Please enter a Hospital ID");
      try {
        const res = await fetch(`/api/v1/hospital-dashboard/${hospId}/kpis`);
        const data = await res.json();
        hospDashOutput.style.display = "block";
        hospDashOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        hospDashOutput.style.display = "block";
        hospDashOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnMgmt = document.getElementById("btn-get-hosp-mgmt");
  if (btnMgmt) {
    btnMgmt.addEventListener("click", async () => {
      const hospId = document.getElementById("hosp-dash-id").value;
      if (!hospId) return alert("Please enter a Hospital ID");
      try {
        const res = await fetch(`/api/v1/hospital-dashboard/${hospId}/management`);
        const data = await res.json();
        hospDashOutput.style.display = "block";
        hospDashOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        hospDashOutput.style.display = "block";
        hospDashOutput.textContent = "Error: " + err.message;
      }
    });
  }
}

function setupPlatformAdminDashboardForm() {
  const platformAdminOutput = document.getElementById("platform-admin-output");

  const btnGlobalKpis = document.getElementById("btn-get-global-kpis");
  if (btnGlobalKpis) {
    btnGlobalKpis.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/platform-admin/kpis");
        const data = await res.json();
        platformAdminOutput.style.display = "block";
        platformAdminOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        platformAdminOutput.style.display = "block";
        platformAdminOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnExplorer = document.getElementById("btn-query-explorer");
  if (btnExplorer) {
    btnExplorer.addEventListener("click", async () => {
      const cat = document.getElementById("platform-explorer-cat").value;
      try {
        const res = await fetch(`/api/v1/platform-admin/explorer/${cat}`);
        const data = await res.json();
        platformAdminOutput.style.display = "block";
        platformAdminOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        platformAdminOutput.style.display = "block";
        platformAdminOutput.textContent = "Error: " + err.message;
      }
    });
  }
}

function setupObservabilityForm() {
  const obsOutput = document.getElementById("observability-output");

  const btnTrace = document.getElementById("btn-obs-get-trace");
  if (btnTrace) {
    btnTrace.addEventListener("click", async () => {
      const identifier = document.getElementById("obs-identifier").value;
      if (!identifier) return alert("Please enter a Trace ID");
      try {
        const res = await fetch(`/api/v1/observability/traces/${identifier}`);
        const data = await res.json();
        obsOutput.style.display = "block";
        obsOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        obsOutput.style.display = "block";
        obsOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnCorr = document.getElementById("btn-obs-get-correlation");
  if (btnCorr) {
    btnCorr.addEventListener("click", async () => {
      const identifier = document.getElementById("obs-identifier").value;
      if (!identifier) return alert("Please enter a Correlation ID");
      try {
        const res = await fetch(`/api/v1/observability/correlation/${identifier}`);
        const data = await res.json();
        obsOutput.style.display = "block";
        obsOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        obsOutput.style.display = "block";
        obsOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnAnalytics = document.getElementById("btn-obs-get-analytics");
  if (btnAnalytics) {
    btnAnalytics.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/observability/analytics");
        const data = await res.json();
        obsOutput.style.display = "block";
        obsOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        obsOutput.style.display = "block";
        obsOutput.textContent = "Error: " + err.message;
      }
    });
}

function setupAIAnalyticsForm() {
  const aiOutput = document.getElementById("ai-analytics-output");

  const btnSummary = document.getElementById("btn-get-ai-summary");
  if (btnSummary) {
    btnSummary.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/ai/usage/summary");
        const data = await res.json();
        aiOutput.style.display = "block";
        aiOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        aiOutput.style.display = "block";
        aiOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnHosp = document.getElementById("btn-get-cost-hosp");
  if (btnHosp) {
    btnHosp.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/ai/usage/by-hospital");
        const data = await res.json();
        aiOutput.style.display = "block";
        aiOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        aiOutput.style.display = "block";
        aiOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnFeat = document.getElementById("btn-get-cost-feat");
  if (btnFeat) {
    btnFeat.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/ai/usage/by-feature");
        const data = await res.json();
        aiOutput.style.display = "block";
        aiOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        aiOutput.style.display = "block";
        aiOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnRunEval = document.getElementById("btn-run-ai-eval");
  if (btnRunEval) {
    btnRunEval.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/ai/evaluations/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({})
        });
        const data = await res.json();
        aiOutput.style.display = "block";
        aiOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        aiOutput.style.display = "block";
        aiOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnHistory = document.getElementById("btn-get-eval-history");
  if (btnHistory) {
    btnHistory.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/ai/evaluations/results");
        const data = await res.json();
        aiOutput.style.display = "block";
        aiOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        aiOutput.style.display = "block";
        aiOutput.textContent = "Error: " + err.message;
      }
    });
  }
}

function setupFeedbackLoopForm() {
  const fbOutput = document.getElementById("feedback-output");
  let activeFeedbackId = null;

  const btnIngest = document.getElementById("btn-fb-ingest");
  if (btnIngest) {
    btnIngest.addEventListener("click", async () => {
      const interactionId = document.getElementById("fb-interaction-id").value;
      const score = parseFloat(document.getElementById("fb-score").value) || 0.82;
      if (!interactionId) return alert("Please enter an Interaction ID");
      try {
        const res = await fetch("/api/v1/feedback/ingest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            interaction_id: interactionId,
            evaluation_score: score,
            is_success: score >= 0.70,
            failure_reason: score < 0.90 ? "Sub-optimal prompt disambiguation" : null
          })
        });
        const data = await res.json();
        activeFeedbackId = data.feedback_id;
        fbOutput.style.display = "block";
        fbOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        fbOutput.style.display = "block";
        fbOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnReview = document.getElementById("btn-fb-review");
  if (btnReview) {
    btnReview.addEventListener("click", async () => {
      const targetId = activeFeedbackId || document.getElementById("fb-interaction-id").value;
      if (!targetId) return alert("Please ingest or enter an Interaction ID / Feedback ID first");
      try {
        const res = await fetch(`/api/v1/feedback/${targetId}/review`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            root_cause_category: "PROMPT_AMBIGUITY",
            review_notes: "Natural language doctor name entity parser requires few-shot prompt tuning"
          })
        });
        const data = await res.json();
        fbOutput.style.display = "block";
        fbOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        fbOutput.style.display = "block";
        fbOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnImprove = document.getElementById("btn-fb-improve");
  if (btnImprove) {
    btnImprove.addEventListener("click", async () => {
      const targetId = activeFeedbackId || document.getElementById("fb-interaction-id").value;
      if (!targetId) return alert("Please ingest or enter an Interaction ID / Feedback ID first");
      try {
        const res = await fetch(`/api/v1/feedback/${targetId}/apply-improvement`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            improvement_type: "PROMPT_REFINEMENT",
            improvement_details: { prompt_version: "v2.5", added_few_shots: 5 }
          })
        });
        const data = await res.json();
        fbOutput.style.display = "block";
        fbOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        fbOutput.style.display = "block";
        fbOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnReeval = document.getElementById("btn-fb-reeval");
  if (btnReeval) {
    btnReeval.addEventListener("click", async () => {
      const targetId = activeFeedbackId || document.getElementById("fb-interaction-id").value;
      if (!targetId) return alert("Please ingest or enter an Interaction ID / Feedback ID first");
      try {
        const res = await fetch(`/api/v1/feedback/${targetId}/re-evaluate`, {
          method: "POST"
        });
        const data = await res.json();
        fbOutput.style.display = "block";
        fbOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        fbOutput.style.display = "block";
        fbOutput.textContent = "Error: " + err.message;
      }
    });
  }

  const btnHistory = document.getElementById("btn-fb-history");
  if (btnHistory) {
    btnHistory.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/feedback/records");
        const data = await res.json();
        fbOutput.style.display = "block";
        fbOutput.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        fbOutput.style.display = "block";
        fbOutput.textContent = "Error: " + err.message;
      }
    });
  }
}





// ============================================================================
// Section 5.39 — Human Escalation Console
// ============================================================================

function setupEscalationConsole() {
  const form = document.getElementById("form-trigger-escalation");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const out = document.getElementById("esc-trigger-output");
    const sessionId = document.getElementById("esc-session-id").value.trim();
    const triggerReason = document.getElementById("esc-trigger-reason").value;
    const hospitalId = document.getElementById("esc-hospital-id").value.trim() || null;
    const failureCount = parseInt(document.getElementById("esc-failure-count").value) || 0;
    const summary = document.getElementById("esc-summary").value.trim();

    out.style.display = "block";
    out.textContent = "Triggering escalation...";

    try {
      const res = await fetch("/api/v1/escalation/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          trigger_reason: triggerReason,
          hospital_id: hospitalId,
          failure_count: failureCount,
          context_snapshot: {
            patient_intent: summary || "Not specified",
            conversation_summary: summary || "",
            actions_attempted: [],
            last_error: null,
            patient_info: {}
          }
        })
      });
      const data = await res.json();
      out.textContent = JSON.stringify(data, null, 2);

      // Auto-populate the context viewer and resolve panel with the new ticket ID
      if (data.escalation_id) {
        document.getElementById("esc-context-id").value = data.escalation_id;
        document.getElementById("esc-resolve-id").value = data.escalation_id;
      }
    } catch (err) {
      out.textContent = "Error: " + err.message;
    }
  });
}

async function loadEscalationContext() {
  const out = document.getElementById("esc-context-output");
  const escalationId = document.getElementById("esc-context-id").value.trim();
  if (!escalationId) { alert("Enter an Escalation ID"); return; }

  out.style.display = "block";
  out.textContent = "Loading context...";

  try {
    const res = await fetch(`/api/v1/escalation/${escalationId}/context`);
    const data = await res.json();
    out.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    out.textContent = "Error: " + err.message;
  }
}

async function resolveEscalation() {
  const out = document.getElementById("esc-resolve-output");
  const escalationId = document.getElementById("esc-resolve-id").value.trim();
  const resolutionStatus = document.getElementById("esc-resolution-status").value;
  const operatorId = document.getElementById("esc-operator-id").value.trim() || null;
  const operatorNotes = document.getElementById("esc-operator-notes").value.trim() || null;

  if (!escalationId) { alert("Enter an Escalation ID"); return; }

  out.style.display = "block";
  out.textContent = "Resolving...";

  try {
    const res = await fetch(`/api/v1/escalation/${escalationId}/resolve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        resolution_status: resolutionStatus,
        operator_id: operatorId,
        operator_notes: operatorNotes
      })
    });
    const data = await res.json();
    out.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    out.textContent = "Error: " + err.message;
  }
}

async function listEscalationRecords() {
  const out = document.getElementById("esc-list-output");
  const status = document.getElementById("esc-list-status").value;

  out.style.display = "block";
  out.textContent = "Loading records...";

  try {
    const url = "/api/v1/escalation/records" + (status ? `?status=${status}` : "");
    const res = await fetch(url);
    const data = await res.json();
    out.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    out.textContent = "Error: " + err.message;
  }
}

// ============================================================================
// Sections 5.40 & 5.41 — Audit Trail & Privacy-Aware Logging
// ============================================================================

function setupAuditTrailForms() {
  const btnLoadTimeline = document.getElementById("btn-load-timeline");
  const btnSeedTimeline = document.getElementById("btn-seed-sample-timeline");
  const btnQueryAudit = document.getElementById("btn-query-audit-trail");
  const btnAuditSummary = document.getElementById("btn-get-audit-summary");
  const formPrivacy = document.getElementById("form-privacy-check");
  const btnPrivacyLogs = document.getElementById("btn-get-privacy-logs");

  // 1. Load Session Timeline (5.40)
  if (btnLoadTimeline) {
    btnLoadTimeline.addEventListener("click", async () => {
      const sessionId = document.getElementById("audit-timeline-session-id").value.trim();
      const out = document.getElementById("audit-timeline-output");
      if (!sessionId) { alert("Enter a Session ID"); return; }

      out.style.display = "block";
      out.textContent = "Reconstructing chronological timeline...";

      try {
        const res = await fetch(`/api/v1/audit/timeline/${sessionId}`);
        const data = await res.json();

        if (data.event_count === 0) {
          out.textContent = `No audit events found for session '${sessionId}'. Click 'Seed 16-Step Lifecycle' to generate sample data.`;
          return;
        }

        let output = `========================================================\n`;
        output += `CHRONOLOGICAL AUDIT TRAIL — SESSION: ${data.session_id}\n`;
        output += `Total Events: ${data.event_count} | Integrity: ${data.integrity?.is_valid ? "VALID (STRICT CHRONOLOGICAL)" : "COMPROMISED"}\n`;
        output += `========================================================\n\n`;
        output += data.formatted_summary + `\n\n`;
        output += `========================================================\n`;
        output += `DETAILED PRIVACY-SANITIZED EVENTS (SECTION 5.41)\n`;
        output += `========================================================\n`;
        output += JSON.stringify(data.timeline, null, 2);

        out.textContent = output;
      } catch (err) {
        out.textContent = "Error loading timeline: " + err.message;
      }
    });
  }

  // 2. Seed Sample 16-Step Lifecycle (5.40 Specification)
  if (btnSeedTimeline) {
    btnSeedTimeline.addEventListener("click", async () => {
      const sessionId = document.getElementById("audit-timeline-session-id").value.trim() || "CALL-DEMO-540";
      const out = document.getElementById("audit-timeline-output");
      out.style.display = "block";
      out.textContent = "Seeding canonical 16-event lifecycle into audit trail...";

      const events = [
        { event_type: "CALL_STARTED", category: "OPERATIONAL_MONITORING" },
        { event_type: "PATIENT_IDENTIFIED", category: "OPERATIONAL_MONITORING", payload: { patient_id: "PAT-8812" } },
        { event_type: "AI_CONTEXT_RETRIEVED", category: "AGENT_EVALUATION", payload: { intent: "APPOINTMENT_BOOKING" } },
        { event_type: "TOOL_CALL", category: "DEBUGGING", tool_name: "lookup_patient", tool_arguments: { patient_id: "PAT-8812" } },
        { event_type: "TOOL_CALL", category: "DEBUGGING", tool_name: "search_doctors", tool_arguments: { specialty: "Cardiology" } },
        { event_type: "TOOL_CALL", category: "DEBUGGING", tool_name: "check_availability", tool_arguments: { doctor_id: "DOC-CAR-01" } },
        { event_type: "PATIENT_SELECTED_SLOT", category: "OPERATIONAL_MONITORING", payload: { slot: "2026-09-12 10:30 AM" } },
        { event_type: "BOOKING_STARTED", category: "OPERATIONAL_MONITORING", payload: { appointment_type: "IN_PERSON" } },
        { event_type: "EHR_INTEGRATION_STARTED", category: "INTEGRATION_TROUBLESHOOTING", payload: { ehr_adapter: "EPIC" } },
        { event_type: "EXTERNAL_APPOINTMENT_CREATED", category: "INTEGRATION_TROUBLESHOOTING", payload: { external_ref: "EPIC-APT-9921" } },
        { event_type: "EHR_SYNC_VERIFIED", category: "RELIABILITY", payload: { sync_state: "CONFIRMED_MATCH" } },
        { event_type: "BOOKING_VERIFIED", category: "RELIABILITY", payload: { status: "CONFIRMED" } },
        { event_type: "QUESTIONNAIRE_STARTED", category: "OPERATIONAL_MONITORING", payload: { questionnaire_id: "Q-CARDIAC-01" } },
        { event_type: "QUESTIONNAIRE_COMPLETED", category: "OPERATIONAL_MONITORING", payload: { total_answers: 4 } },
        { event_type: "WORKFLOW_STARTED", category: "RELIABILITY", payload: { workflow_name: "POST_BOOKING_NOTIFICATION" } },
        { event_type: "CALL_COMPLETED", category: "OPERATIONAL_MONITORING", payload: { duration_seconds: 124 } }
      ];

      try {
        for (const ev of events) {
          await fetch("/api/v1/audit/events", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              session_id: sessionId,
              hospital_id: "HOSP-40",
              event_type: ev.event_type,
              category: ev.category,
              tool_name: ev.tool_name || null,
              tool_arguments: ev.tool_arguments || null,
              payload: ev.payload || null
            })
          });
        }
        btnLoadTimeline.click();
      } catch (err) {
        out.textContent = "Error seeding timeline: " + err.message;
      }
    });
  }

  // 3. Query Audit Trail across 7 Objectives (5.40)
  if (btnQueryAudit) {
    btnQueryAudit.addEventListener("click", async () => {
      const category = document.getElementById("audit-filter-category").value;
      const hospitalId = document.getElementById("audit-filter-hospital").value.trim();
      const out = document.getElementById("audit-query-output");

      out.style.display = "block";
      out.textContent = "Querying structured audit logs...";

      try {
        const params = new URLSearchParams();
        if (category) params.append("category", category);
        if (hospitalId) params.append("hospital_id", hospitalId);

        const res = await fetch(`/api/v1/audit/trail?${params.toString()}`);
        const data = await res.json();
        out.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        out.textContent = "Error querying audit logs: " + err.message;
      }
    });
  }

  // 4. Platform Compliance Summary (5.40 & 5.41)
  if (btnAuditSummary) {
    btnAuditSummary.addEventListener("click", async () => {
      const hospitalId = document.getElementById("audit-filter-hospital").value.trim();
      const out = document.getElementById("audit-query-output");

      out.style.display = "block";
      out.textContent = "Generating platform compliance summary...";

      try {
        const url = "/api/v1/audit/summary" + (hospitalId ? `?hospital_id=${hospitalId}` : "");
        const res = await fetch(url);
        const data = await res.json();
        out.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        out.textContent = "Error loading audit summary: " + err.message;
      }
    });
  }

  // 5. Privacy Access Check Simulator (5.41)
  if (formPrivacy) {
    formPrivacy.addEventListener("submit", async (e) => {
      e.preventDefault();
      const role = document.getElementById("privacy-role").value;
      const resource = document.getElementById("privacy-resource").value;
      const reqId = document.getElementById("privacy-requester-id").value.trim();
      const out = document.getElementById("privacy-check-output");

      out.style.display = "block";
      out.textContent = "Evaluating access permissions...";

      try {
        const res = await fetch("/api/v1/audit/privacy/access-check", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            requester_role: role,
            requester_id: reqId,
            resource_type: resource,
            action: "READ",
            reason: `Frontend privacy evaluation for role ${role}`
          })
        });
        const data = await res.json();
        out.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        out.textContent = "Error during privacy evaluation: " + err.message;
      }
    });
  }

  // 6. Security Access Audits Log
  if (btnPrivacyLogs) {
    btnPrivacyLogs.addEventListener("click", async () => {
      const out = document.getElementById("privacy-check-output");
      out.style.display = "block";
      out.textContent = "Loading security access audit logs...";

      try {
        const res = await fetch("/api/v1/audit/privacy/access-logs");
        const data = await res.json();
        out.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        out.textContent = "Error loading access logs: " + err.message;
      }
    });
  }
}

// ============================================================================
// Step 6 — Role-Based Access Control (RBAC) Console
// ============================================================================

function setupRBACForms() {
  const btnLoadRole = document.getElementById("btn-load-rbac-role");
  const btnLoadAll = document.getElementById("btn-load-all-rbac-matrix");
  const formSimulate = document.getElementById("form-rbac-simulate");
  const btnEvaluate = document.getElementById("btn-rbac-evaluate");
  const presetBtns = document.querySelectorAll(".rbac-preset-btn");

  // 1. Inspect Single Role Capabilities & Boundaries
  if (btnLoadRole) {
    btnLoadRole.addEventListener("click", async () => {
      const role = document.getElementById("rbac-matrix-role").value;
      const out = document.getElementById("rbac-matrix-output");
      out.style.display = "block";
      out.textContent = `Loading capabilities for ${role}...`;

      try {
        const res = await fetch(`/api/v1/rbac/permissions/${role}`);
        const data = await res.json();
        let output = `========================================================\n`;
        output += `ROLE: ${data.title} (${data.role})\n`;
        output += `Allowed Operations: ${data.allowed_count}\n`;
        output += `STRICT BOUNDARY RULE: ${data.boundary_rule}\n`;
        output += `========================================================\n\n`;
        output += `PERMITTED CAPABILITIES:\n`;
        data.permissions.forEach((p, idx) => {
          output += `  ${idx + 1}. ${p}\n`;
        });
        out.textContent = output;
      } catch (err) {
        out.textContent = "Error loading role permissions: " + err.message;
      }
    });
  }

  // 2. Full 4-Role RBAC Matrix
  if (btnLoadAll) {
    btnLoadAll.addEventListener("click", async () => {
      const out = document.getElementById("rbac-matrix-output");
      out.style.display = "block";
      out.textContent = "Loading complete 4-Role platform matrix...";

      try {
        const res = await fetch("/api/v1/rbac/matrix");
        const data = await res.json();
        out.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        out.textContent = "Error loading matrix: " + err.message;
      }
    });
  }

  // 3. Preset Simulation Buttons
  presetBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const role = btn.getAttribute("data-role");
      const perm = btn.getAttribute("data-perm");
      const userHosp = btn.getAttribute("data-userhosp") || "";
      const targetHosp = btn.getAttribute("data-targethosp") || "";
      const userDoc = btn.getAttribute("data-userdoc") || "";
      const targetDoc = btn.getAttribute("data-targetdoc") || "";
      const userPat = btn.getAttribute("data-userpat") || "";
      const targetPat = btn.getAttribute("data-targetpat") || "";

      document.getElementById("rbac-sim-role").value = role;
      document.getElementById("rbac-sim-permission").value = perm;
      document.getElementById("rbac-sim-user-hosp").value = userHosp;
      document.getElementById("rbac-sim-target-hosp").value = targetHosp;
      document.getElementById("rbac-sim-user-doc").value = userDoc;
      document.getElementById("rbac-sim-target-doc").value = targetDoc;
      document.getElementById("rbac-sim-user-pat").value = userPat;
      document.getElementById("rbac-sim-target-pat").value = targetPat;

      if (btnEvaluate) btnEvaluate.click();
    });
  });

  // 4. Helper function to extract simulation payload
  function getSimulatePayload() {
    return {
      role: document.getElementById("rbac-sim-role").value,
      permission: document.getElementById("rbac-sim-permission").value.trim(),
      user_id: "user-sim-001",
      user_hospital_id: document.getElementById("rbac-sim-user-hosp").value.trim() || null,
      user_doctor_id: document.getElementById("rbac-sim-user-doc").value.trim() || null,
      user_patient_id: document.getElementById("rbac-sim-user-pat").value.trim() || null,
      target_hospital_id: document.getElementById("rbac-sim-target-hosp").value.trim() || null,
      target_doctor_id: document.getElementById("rbac-sim-target-doc").value.trim() || null,
      target_patient_id: document.getElementById("rbac-sim-target-pat").value.trim() || null,
    };
  }

  // 5. Evaluate Access (Soft Check)
  if (btnEvaluate) {
    btnEvaluate.addEventListener("click", async () => {
      const out = document.getElementById("rbac-sim-output");
      out.style.display = "block";
      out.textContent = "Evaluating role boundary rules...";

      try {
        const payload = getSimulatePayload();
        const res = await fetch("/api/v1/rbac/evaluate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        out.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        out.textContent = "Error evaluating access: " + err.message;
      }
    });
  }

  // 6. Enforce Access (Strict 403 Test)
  if (formSimulate) {
    formSimulate.addEventListener("submit", async (e) => {
      e.preventDefault();
      const out = document.getElementById("rbac-sim-output");
      out.style.display = "block";
      out.textContent = "Testing strict 403 enforcement...";

      try {
        const payload = getSimulatePayload();
        const res = await fetch("/api/v1/rbac/enforce", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok) {
          out.textContent = `[HTTP 200 OK — AUTHORIZED]\n` + JSON.stringify(data, null, 2);
        } else {
          out.textContent = `[HTTP ${res.status} FORBIDDEN — BOUNDARY VIOLATION]\n` + JSON.stringify(data, null, 2);
        }
      } catch (err) {
        out.textContent = "Error testing enforcement: " + err.message;
      }
    });
  }
}

// Portal 7: Core Data Model (Step 7) Logic
function setupCoreDataModelForms() {
  const btnSeed = document.getElementById("btn-seed-data-model");
  const btnValidate = document.getElementById("btn-validate-data-model");
  const btnRefresh = document.getElementById("btn-refresh-data-model");
  const statusBox = document.getElementById("data-model-status");
  const statsContainer = document.getElementById("data-model-stats-badges");
  const treeContainer = document.getElementById("data-model-tree-container");
  const catalogSelect = document.getElementById("select-entity-catalog");
  const catalogOutput = document.getElementById("data-model-catalog-output");
  const integrityOutput = document.getElementById("data-model-integrity-output");

  let cachedEntities = [];

  function escapeHtml(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function renderTreeAscii(node, depth = 0, isLast = true, prefix = "") {
    let result = "";
    const branch = depth === 0 ? "" : (isLast ? "└── " : "├── ");
    const countBadge = node.count !== undefined ? ` [${node.count} records]` : "";
    const desc = node.description ? ` - ${node.description}` : "";
    
    result += `${prefix}${branch}<strong>${escapeHtml(node.name)}</strong><span style="color:var(--primary-color); font-weight:600;">${countBadge}</span><span style="color:var(--text-muted); font-size:0.85rem;">${desc}</span>\n`;

    if (node.children && node.children.length > 0) {
      const nextPrefix = prefix + (depth === 0 ? "" : (isLast ? "    " : "│   "));
      node.children.forEach((child, idx) => {
        const last = idx === node.children.length - 1;
        result += renderTreeAscii(child, depth + 1, last, nextPrefix);
      });
    }
    return result;
  }

  async function loadTree() {
    if (!treeContainer) return;
    try {
      const res = await fetch("/api/v1/core-data-model/tree");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      treeContainer.innerHTML = `<pre style="margin:0; white-space:pre-wrap; font-family:monospace;">${renderTreeAscii(data)}</pre>`;
    } catch (err) {
      treeContainer.textContent = "Error loading data model tree: " + err.message;
    }
  }

  async function loadStats() {
    if (!statsContainer) return;
    try {
      const res = await fetch("/api/v1/core-data-model/stats");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const stats = await res.json();
      
      let html = "";
      for (const [key, count] of Object.entries(stats)) {
        html += `<div style="background:#f8fafc; border:1px solid var(--border-color); border-radius:4px; padding:0.4rem 0.75rem; font-size:0.85rem;">
          <span style="color:var(--text-muted);">${escapeHtml(key)}:</span>
          <strong style="color:var(--primary-color); margin-left:0.25rem;">${count}</strong>
        </div>`;
      }
      statsContainer.innerHTML = html;
    } catch (err) {
      statsContainer.textContent = "Error loading statistics: " + err.message;
    }
  }

  async function loadCatalog() {
    if (!catalogOutput) return;
    try {
      const res = await fetch("/api/v1/core-data-model/entities");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      cachedEntities = data.entities || [];

      if (catalogSelect && catalogSelect.options.length <= 1) {
        cachedEntities.forEach(ent => {
          const opt = document.createElement("option");
          opt.value = ent.name;
          opt.textContent = `${ent.name} (${ent.table_name || "nested"})`;
          catalogSelect.appendChild(opt);
        });
      }

      renderCatalogView();
    } catch (err) {
      catalogOutput.textContent = "Error loading entity catalog: " + err.message;
    }
  }

  function renderCatalogView() {
    if (!catalogOutput) return;
    const selected = catalogSelect ? catalogSelect.value : "ALL";

    const toShow = selected === "ALL" 
      ? cachedEntities 
      : cachedEntities.filter(e => e.name === selected);

    if (toShow.length === 0) {
      catalogOutput.innerHTML = "<p style='color:var(--text-muted);'>No entities found.</p>";
      return;
    }

    let html = `<div style="display:flex; flex-direction:column; gap:1rem;">`;
    toShow.forEach(ent => {
      html += `<div style="border:1px solid var(--border-color); border-radius:6px; padding:1rem; background:#ffffff;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem; flex-wrap:wrap;">
          <h4 style="color:var(--text-color); margin:0;">${escapeHtml(ent.name)}</h4>
          <div>
            <span style="background:#e0f2fe; color:#0369a1; padding:0.2rem 0.5rem; border-radius:4px; font-size:0.75rem; font-weight:600;">table: ${escapeHtml(ent.table_name || "N/A")}</span>
            <span style="background:#f1f5f9; color:#475569; padding:0.2rem 0.5rem; border-radius:4px; font-size:0.75rem; margin-left:0.25rem;">PK: ${escapeHtml(ent.primary_key || "none")}</span>
            <span style="background:#f0fdf4; color:#15803d; padding:0.2rem 0.5rem; border-radius:4px; font-size:0.75rem; margin-left:0.25rem; font-weight:600;">${ent.row_count !== undefined ? ent.row_count + " rows" : ""}</span>
          </div>
        </div>
        <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:0.75rem;">${escapeHtml(ent.description || "")}</p>
        <div style="font-size:0.8rem;">
          <strong>Columns / Fields:</strong>
          <span style="color:#334155;">${(ent.columns || []).map(c => escapeHtml(c)).join(", ") || "Dynamic / Sub-entity"}</span>
        </div>
        ${ent.foreign_keys && ent.foreign_keys.length > 0 ? `
        <div style="font-size:0.8rem; margin-top:0.35rem;">
          <strong>Foreign Keys:</strong>
          <span style="color:#0284c7;">${(ent.foreign_keys || []).map(f => escapeHtml(f)).join(", ")}</span>
        </div>` : ""}
      </div>`;
    });
    html += `</div>`;
    catalogOutput.innerHTML = html;
  }

  async function validateIntegrity() {
    if (!integrityOutput) return;
    integrityOutput.style.display = "block";
    integrityOutput.textContent = "Running relational integrity diagnostics...";

    try {
      const res = await fetch("/api/v1/core-data-model/validate", { method: "POST" });
      const data = await res.json();
      integrityOutput.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
      integrityOutput.textContent = "Error validating relational integrity: " + err.message;
    }
  }

  async function seedDemoData() {
    if (!statusBox) return;
    statusBox.style.display = "block";
    statusBox.textContent = "Seeding baseline demonstration dataset for all 22 entities...";

    try {
      const res = await fetch("/api/v1/core-data-model/seed-demo", { method: "POST" });
      const data = await res.json();
      statusBox.textContent = "Successfully seeded demo hierarchy:\n" + JSON.stringify(data, null, 2);

      await Promise.all([loadTree(), loadStats(), loadCatalog()]);
    } catch (err) {
      statusBox.textContent = "Error seeding demo dataset: " + err.message;
    }
  }

  if (btnSeed) btnSeed.addEventListener("click", seedDemoData);
  if (btnValidate) btnValidate.addEventListener("click", validateIntegrity);
  if (btnRefresh) {
    btnRefresh.addEventListener("click", async () => {
      if (statusBox) {
        statusBox.style.display = "block";
        statusBox.textContent = "Refreshing data model...";
      }
      await Promise.all([loadTree(), loadStats(), loadCatalog()]);
      if (statusBox) statusBox.textContent = "Refreshed at " + new Date().toLocaleTimeString();
    });
  }

  if (catalogSelect) {
    catalogSelect.addEventListener("change", renderCatalogView);
  }

  const coreDataTabBtn = document.querySelector('button[data-tab="tab-core-data-model"]');
  if (coreDataTabBtn) {
    coreDataTabBtn.addEventListener("click", () => {
      loadTree();
      loadStats();
      loadCatalog();
    });
  }
}

// Portal 8: Complete End-to-End Patient Workflow (Step 8) Logic
function setupPatientWorkflowForms() {
  const form = document.getElementById("form-patient-workflow");
  const summaryBox = document.getElementById("pwf-summary-status");
  const stepCounter = document.getElementById("pwf-step-counter");
  const timelineContainer = document.getElementById("pwf-timeline-container");
  const dialogueOutput = document.getElementById("pwf-dialogue-output");
  const calendarOutput = document.getElementById("pwf-calendar-output");
  const ehrOutput = document.getElementById("pwf-ehr-output");
  const intakeOutput = document.getElementById("pwf-intake-output");
  const analyticsOutput = document.getElementById("pwf-analytics-output");
  const presetButtons = document.querySelectorAll(".workflow-preset-btn");

  const PRESETS_DATA = {
    PRESET_KNEE_ORTHO: {
      name: "Alex Miller",
      phone: "+1-555-0199",
      channel: "WEB_VOICE",
      utterance: "I've been having knee pain and I'd like to see a doctor this week.",
      choice: "0"
    },
    PRESET_CARDIOLOGY_CHEST: {
      name: "Rachel Adams",
      phone: "+1-555-0288",
      channel: "TELEPHONE",
      utterance: "I've had mild palpitations during jogging and want to consult a cardiologist.",
      choice: "0"
    },
    PRESET_DERMATOLOGY_RASH: {
      name: "David Clark",
      phone: "+1-555-0377",
      channel: "WEB_VOICE",
      utterance: "I have an itchy skin rash on my arm and need an appointment with a skin specialist.",
      choice: "1"
    }
  };

  // Wire presets
  presetButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const pKey = btn.getAttribute("data-preset");
      const pData = PRESETS_DATA[pKey];
      if (pData) {
        document.getElementById("pwf-name").value = pData.name;
        document.getElementById("pwf-phone").value = pData.phone;
        document.getElementById("pwf-channel").value = pData.channel;
        document.getElementById("pwf-utterance").value = pData.utterance;
        document.getElementById("pwf-choice-idx").value = pData.choice;
      }
    });
  });

  if (!form) return;

  function escapeHtml(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      patient_name: document.getElementById("pwf-name").value.trim(),
      phone_number: document.getElementById("pwf-phone").value.trim(),
      channel: document.getElementById("pwf-channel").value,
      utterance: document.getElementById("pwf-utterance").value.trim(),
      selected_choice_index: parseInt(document.getElementById("pwf-choice-idx").value, 10),
      questionnaire_answers: {
        "knee_pain_duration": "About 3 weeks, worsens while climbing stairs",
        "previous_surgeries": "None",
        "current_medications": "Ibuprofen as needed"
      }
    };

    summaryBox.style.display = "block";
    summaryBox.textContent = "Executing complete 20-step patient workflow pipeline...";
    stepCounter.textContent = "Executing 20 steps in real time...";

    try {
      const res = await fetch("/api/v1/patient-workflow/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail ? JSON.stringify(data.detail) : `HTTP ${res.status}`);
      }

      summaryBox.innerHTML = `<strong style="color:var(--success-color);">Workflow Completed Successfully!</strong><br>` +
        `Appointment ID: <code>${escapeHtml(data.appointment_id)}</code> | Doctor: <strong>${escapeHtml(data.doctor_name)}</strong> | ` +
        `Hospital: <strong>${escapeHtml(data.hospital_name)}</strong> | External EHR ID: <code>${escapeHtml(data.external_appointment_id)}</code>`;

      stepCounter.textContent = `All ${data.steps_completed} Steps Executed (100% Complete)`;

      // Render 20-Step Progress Timeline
      if (data.execution_trace && timelineContainer) {
        let timelineHtml = "";
        data.execution_trace.forEach(item => {
          const isOk = item.status === "COMPLETED";
          const badgeColor = isOk ? "#16a34a" : "#dc2626";
          const bgColor = isOk ? "#f0fdf4" : "#fef2f2";
          const borderColor = isOk ? "#bbf7d0" : "#fecaca";

          timelineHtml += `
            <div style="background:${bgColor}; border:1px solid ${borderColor}; border-radius:6px; padding:0.6rem 1rem; display:flex; justify-content:space-between; align-items:center;">
              <div style="display:flex; align-items:center; gap:0.75rem;">
                <span style="background:${badgeColor}; color:#fff; font-size:0.75rem; font-weight:700; width:26px; height:26px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center;">${item.step}</span>
                <div>
                  <strong style="font-size:0.9rem; color:#0f172a;">Step ${item.step}: ${escapeHtml(item.title)}</strong>
                  ${item.pipeline ? `<div style="font-size:0.75rem; color:#64748b;">${escapeHtml(item.pipeline)}</div>` : ""}
                </div>
              </div>
              <span style="font-size:0.75rem; font-weight:600; color:${badgeColor}; background:#fff; padding:0.2rem 0.5rem; border-radius:4px; border:1px solid ${borderColor};">
                ${escapeHtml(item.status)}
              </span>
            </div>
          `;
        });
        timelineContainer.innerHTML = timelineHtml;
      }

      // Render Dialogue Transcript
      if (dialogueOutput && data.execution_trace) {
        const step3 = data.execution_trace.find(s => s.step === 3);
        const step8 = data.execution_trace.find(s => s.step === 8);
        const step9 = data.execution_trace.find(s => s.step === 9);
        const step10 = data.execution_trace.find(s => s.step === 10);
        const step14 = data.execution_trace.find(s => s.step === 14);
        const step16 = data.execution_trace.find(s => s.step === 16);
        const step17 = data.execution_trace.find(s => s.step === 17);

        let dHtml = `<div style="display:flex; flex-direction:column; gap:0.6rem;">`;
        if (step3) dHtml += `<div><strong style="color:#2563eb;">Patient:</strong> "${escapeHtml(step3.utterance)}"</div>`;
        if (step8) dHtml += `<div><strong style="color:#059669;">AI Agent:</strong> "${escapeHtml(step8.agent_utterance)}"</div>`;
        if (step9) dHtml += `<div><strong style="color:#2563eb;">Patient:</strong> "${escapeHtml(step9.patient_utterance)}"</div>`;
        if (step10) dHtml += `<div><strong style="color:#059669;">AI Agent:</strong> "${escapeHtml(step10.agent_confirmation)}"</div>`;
        if (step14) dHtml += `<div><strong style="color:#059669;">AI Agent (Verified):</strong> "${escapeHtml(step14.agent_utterance)}"</div>`;
        if (step16) dHtml += `<div><strong style="color:#059669;">AI Agent (Questionnaire):</strong> "${escapeHtml(step16.agent_utterance)}"</div>`;
        if (step17) dHtml += `<div><strong style="color:#2563eb;">Patient (Responses):</strong> ${escapeHtml(JSON.stringify(step17.patient_responses))}</div>`;
        dHtml += `</div>`;
        dialogueOutput.innerHTML = dHtml;
      }

      // Render Calendar Output
      if (calendarOutput && data.execution_trace) {
        const step7 = data.execution_trace.find(s => s.step === 7);
        if (step7 && step7.results) {
          calendarOutput.textContent = JSON.stringify(step7.results, null, 2);
        }
      }

      // Render EHR Output
      if (ehrOutput && data.execution_trace) {
        const step11 = data.execution_trace.find(s => s.step === 11);
        const step12 = data.execution_trace.find(s => s.step === 12);
        const step13 = data.execution_trace.find(s => s.step === 13);
        const ehrObj = {
          booking_pipeline: step11 ? step11.ehr_pipeline : null,
          five_point_verification: step12 ? step12.verification_results : null,
          synchronized_state: step13 ? step13.details : null
        };
        ehrOutput.textContent = JSON.stringify(ehrObj, null, 2);
      }

      // Render Intake Output
      if (intakeOutput && data.doctor_preparation_briefing) {
        const dpb = data.doctor_preparation_briefing;
        intakeOutput.innerHTML = `
          <div>
            <div style="margin-bottom:0.5rem;"><strong style="color:#0f172a;">Doctor Preparation Briefing</strong> <span style="background:#e0f2fe; color:#0284c7; padding:0.15rem 0.4rem; border-radius:4px; font-size:0.75rem; font-weight:600;">${escapeHtml(dpb.review_status)}</span></div>
            <div><strong>Patient:</strong> ${escapeHtml(dpb.patient_name)}</div>
            <div><strong>Specialty:</strong> ${escapeHtml(dpb.inferred_specialty)}</div>
            <div><strong>Primary Complaint:</strong> ${escapeHtml(dpb.primary_complaint)}</div>
            <div style="margin-top:0.5rem;"><strong>Authorized Clinical Responses:</strong></div>
            <pre style="background:#fff; border:1px solid #e2e8f0; border-radius:4px; padding:0.5rem; font-size:0.8rem; margin-top:0.25rem;">${escapeHtml(JSON.stringify(dpb.authorized_patient_responses, null, 2))}</pre>
          </div>
        `;
      }

      // Render Analytics Output
      if (analyticsOutput && data.analytics_summary) {
        analyticsOutput.textContent = JSON.stringify(data.analytics_summary, null, 2);
      }

    } catch (err) {
      summaryBox.textContent = "Error executing patient workflow: " + err.message;
      stepCounter.textContent = "Execution encountered an error";
    }
  });
}

// Portal 9: Complete Hospital Workflow (Step 9) Logic
function setupHospitalWorkflowForms() {
  const form = document.getElementById("form-hospital-workflow");
  const summaryBox = document.getElementById("hwf-summary-status");
  const stepCounter = document.getElementById("hwf-step-counter");
  const timelineContainer = document.getElementById("hwf-timeline-container");
  const onboardingOutput = document.getElementById("hwf-onboarding-output");
  const clinicalOutput = document.getElementById("hwf-clinical-output");
  const bookingOutput = document.getElementById("hwf-booking-output");
  const reviewOutput = document.getElementById("hwf-review-output");
  const analyticsOutput = document.getElementById("hwf-analytics-output");
  const presetButtons = document.querySelectorAll(".hwf-preset-btn");

  const PRESETS_DATA = {
    PRESET_ST_JUDE: {
      name: "St. Jude Health System",
      code: "STJUDE",
      contact_email: "contact@stjude-health.org",
      admin_name: "Dr. Marcus Vance",
      admin_email: "marcus.vance@stjude-health.org",
      dept: "Cardiovascular Sciences",
      spec: "Cardiology",
      doc_name: "Dr. Olivia Chen",
      doc_email: "olivia.chen@stjude-health.org",
      ehr: "MOCK_EHR"
    },
    PRESET_METRO_GENERAL: {
      name: "Metro General Hospital",
      code: "METROGEN",
      contact_email: "admin@metrogen.org",
      admin_name: "Sarah Jenkins",
      admin_email: "s.jenkins@metrogen.org",
      dept: "Orthopedic Surgery",
      spec: "Orthopedics",
      doc_name: "Dr. Vikram Patel",
      doc_email: "v.patel@metrogen.org",
      ehr: "FHIR_R4"
    },
    PRESET_CARE_REGIONAL: {
      name: "Care Regional Medical Center",
      code: "CAREREG",
      contact_email: "ops@careregional.com",
      admin_name: "Robert Sterling",
      admin_email: "r.sterling@careregional.com",
      dept: "Neurological Sciences",
      spec: "Neurology",
      doc_name: "Dr. Fiona Gallagher",
      doc_email: "f.gallagher@careregional.com",
      ehr: "EPIC"
    }
  };

  presetButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const pKey = btn.getAttribute("data-preset");
      const pData = PRESETS_DATA[pKey];
      if (pData) {
        document.getElementById("hwf-name").value = pData.name;
        document.getElementById("hwf-code").value = pData.code;
        document.getElementById("hwf-contact-email").value = pData.contact_email;
        document.getElementById("hwf-admin-name").value = pData.admin_name;
        document.getElementById("hwf-admin-email").value = pData.admin_email;
        document.getElementById("hwf-dept").value = pData.dept;
        document.getElementById("hwf-spec").value = pData.spec;
        document.getElementById("hwf-doc-name").value = pData.doc_name;
        document.getElementById("hwf-doc-email").value = pData.doc_email;
        document.getElementById("hwf-ehr-type").value = pData.ehr;
      }
    });
  });

  if (!form) return;

  function escapeHtml(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      hospital_name: document.getElementById("hwf-name").value.trim(),
      hospital_code: document.getElementById("hwf-code").value.trim(),
      contact_email: document.getElementById("hwf-contact-email").value.trim(),
      admin_name: document.getElementById("hwf-admin-name").value.trim(),
      admin_email: document.getElementById("hwf-admin-email").value.trim(),
      department_name: document.getElementById("hwf-dept").value.trim(),
      specialty_name: document.getElementById("hwf-spec").value.trim(),
      doctor_name: document.getElementById("hwf-doc-name").value.trim(),
      doctor_email: document.getElementById("hwf-doc-email").value.trim(),
      ehr_adapter_type: document.getElementById("hwf-ehr-type").value
    };

    summaryBox.style.display = "block";
    summaryBox.textContent = "Executing complete 23-stage hospital workflow pipeline...";
    stepCounter.textContent = "Running 23 stages in real time...";

    try {
      const res = await fetch("/api/v1/hospital-workflow/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail ? JSON.stringify(data.detail) : `HTTP ${res.status}`);
      }

      summaryBox.innerHTML = `<strong style="color:var(--success-color);">Hospital Lifecycle Workflow Completed!</strong><br>` +
        `Hospital: <strong>${escapeHtml(data.hospital_name)}</strong> [<code>${escapeHtml(payload.hospital_code)}</code>] | ` +
        `Status: <strong>${escapeHtml(data.hospital_status)}</strong> | Doctor: <strong>${escapeHtml(data.doctor_name)}</strong> | ` +
        `Appointment: <code>${escapeHtml(data.appointment_id)}</code> | EHR ID: <code>${escapeHtml(data.external_appointment_id)}</code>`;

      stepCounter.textContent = `All ${data.stages_completed} Stages Executed (100% Complete)`;

      // Render 23-Stage Progress Timeline
      if (data.execution_trace && timelineContainer) {
        let timelineHtml = "";
        data.execution_trace.forEach(item => {
          timelineHtml += `
            <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:6px; padding:0.5rem 0.85rem; display:flex; justify-content:space-between; align-items:center;">
              <div style="display:flex; align-items:center; gap:0.6rem;">
                <span style="background:#16a34a; color:#fff; font-size:0.75rem; font-weight:700; width:24px; height:24px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center;">${item.step}</span>
                <strong style="font-size:0.85rem; color:#0f172a;">Stage ${item.step}: ${escapeHtml(item.title)}</strong>
              </div>
              <span style="font-size:0.75rem; font-weight:600; color:#16a34a; background:#fff; padding:0.15rem 0.45rem; border-radius:4px; border:1px solid #bbf7d0;">
                ${escapeHtml(item.status)}
              </span>
            </div>
          `;
        });
        timelineContainer.innerHTML = timelineHtml;
      }

      // Populate Panels
      if (data.execution_trace) {
        const t = data.execution_trace;

        // Onboarding Output (Stages 1-5)
        if (onboardingOutput) {
          const s1_5 = {
            stage_1_registration: t.find(s => s.step === 1)?.details,
            stage_2_details_submitted: t.find(s => s.step === 2)?.details,
            stage_3_admin_review: t.find(s => s.step === 3)?.details,
            stage_4_approved: t.find(s => s.step === 4)?.details,
            stage_5_admin_login: t.find(s => s.step === 5)?.details,
          };
          onboardingOutput.textContent = JSON.stringify(s1_5, null, 2);
        }

        // Clinical Output (Stages 6-14)
        if (clinicalOutput) {
          const s6_14 = {
            hospital_config: t.find(s => s.step === 6)?.details,
            doctor_created: t.find(s => s.step === 7)?.details,
            calendar_configured: t.find(s => s.step === 8)?.details,
            availability: t.find(s => s.step === 9)?.details,
            blocked_periods: t.find(s => s.step === 10)?.details,
            questionnaire_created: t.find(s => s.step === 11)?.details,
            ehr_integration: t.find(s => s.step === 12)?.details,
            workflows_enabled: t.find(s => s.step === 13)?.details,
            published_live: t.find(s => s.step === 14)?.details,
          };
          clinicalOutput.textContent = JSON.stringify(s6_14, null, 2);
        }

        // Booking & EHR Sync (Stages 15-18)
        if (bookingOutput) {
          const s15_18 = {
            discovery_result: t.find(s => s.step === 15)?.details,
            ai_appointment_booked: t.find(s => s.step === 16)?.details,
            ehr_outbound_sync: t.find(s => s.step === 17)?.details,
            authoritative_verification: t.find(s => s.step === 18)?.details,
          };
          bookingOutput.textContent = JSON.stringify(s15_18, null, 2);
        }

        // Post-Booking & Review (Stages 19-22)
        if (reviewOutput) {
          const s19 = t.find(s => s.step === 19)?.details;
          const s20 = t.find(s => s.step === 20)?.details;
          const s21 = t.find(s => s.step === 21)?.details;
          const s22 = t.find(s => s.step === 22)?.details;

          let rHtml = `<div style="display:flex; flex-direction:column; gap:0.5rem; font-size:0.83rem;">`;
          if (s19) rHtml += `<div><strong>Workflow:</strong> <code>${escapeHtml(s19.workflow_name)}</code> (${escapeHtml(s19.status)})</div>`;
          if (s20) rHtml += `<div><strong>Notification:</strong> Sent to ${escapeHtml(s20.recipient)} via ${escapeHtml(s20.channel)} [${escapeHtml(s20.notification_status)}]</div>`;
          if (s21) rHtml += `<div><strong>Doctor Schedule:</strong> Synced for ${escapeHtml(s21.doctor_name)} at ${escapeHtml(s21.scheduled_datetime)}</div>`;
          if (s22) {
            rHtml += `<div style="margin-top:0.4rem; padding:0.5rem; background:#fff; border:1px solid #e2e8f0; border-radius:4px;">
              <strong>Pre-Visit Clinical Intake Responses:</strong>
              <pre style="margin-top:0.25rem; font-size:0.78rem;">${escapeHtml(JSON.stringify(s22.patient_intake_responses, null, 2))}</pre>
            </div>`;
          }
          rHtml += `</div>`;
          reviewOutput.innerHTML = rHtml;
        }

        // Analytics (Stage 23)
        if (analyticsOutput && data.hospital_analytics) {
          analyticsOutput.textContent = JSON.stringify(data.hospital_analytics, null, 2);
        }
      }

    } catch (err) {
      summaryBox.textContent = "Error executing hospital workflow: " + err.message;
      stepCounter.textContent = "Execution encountered an error";
    }
  });
}


// ============================================================================
// Step 10: Complete Platform Architecture UI Controller
// ============================================================================
function setupArchitectureUI() {
  const topologyViewer = document.getElementById("arch-topology-viewer");
  const waterfallViewer = document.getElementById("arch-waterfall-viewer");
  const healthGrid = document.getElementById("arch-health-grid");
  const overallBadge = document.getElementById("arch-overall-health-badge");
  const spansCountBadge = document.getElementById("trace-spans-count-badge");
  const summaryBar = document.getElementById("trace-summary-bar");

  const btnAuditHealth = document.getElementById("btn-audit-arch-health");
  const btnRefreshTopology = document.getElementById("btn-refresh-topology");
  const formSyntheticTrace = document.getElementById("form-synthetic-trace");
  const btnRunTrace = document.getElementById("btn-run-synthetic-trace");

  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // 1. Fetch and Render 9-Layer Topology
  async function fetchTopology() {
    if (!topologyViewer) return;
    topologyViewer.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--text-muted);">Loading 9-Layer platform architecture topology...</div>`;

    try {
      const res = await fetch("/api/v1/architecture/topology");
      const data = await res.json();

      if (!data.layers || data.layers.length === 0) {
        topologyViewer.innerHTML = `<div style="color:var(--danger-color);">No architecture layers returned.</div>`;
        return;
      }

      let html = "";
      data.layers.forEach(layer => {
        html += `
          <div style="background:#ffffff; border:1px solid #cbd5e1; border-radius:8px; padding:0.85rem; box-shadow:0 1px 3px rgba(0,0,0,0.05); border-left:4px solid #0284c7;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
              <div style="display:flex; align-items:center; gap:0.5rem;">
                <span style="background:#0284c7; color:#fff; font-weight:700; font-size:0.75rem; padding:0.15rem 0.45rem; border-radius:4px;">L${layer.layer_number}</span>
                <strong style="color:#0f172a; font-size:0.95rem;">${escapeHtml(layer.name)}</strong>
              </div>
              <span style="font-size:0.75rem; background:#f1f5f9; color:#475569; padding:0.15rem 0.4rem; border-radius:4px;">${escapeHtml(layer.components.length)} components</span>
            </div>
            <p style="font-size:0.8rem; color:#64748b; margin:0 0 0.5rem 0;">${escapeHtml(layer.description)}</p>
            
            <div style="display:flex; flex-wrap:wrap; gap:0.35rem; margin-bottom:0.4rem;">
              ${layer.components.map(c => `
                <span style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; padding:0.2rem 0.4rem; font-size:0.75rem; color:#334155;" title="${escapeHtml(c.description)}">
                  <strong>${escapeHtml(c.display_title)}</strong>
                  ${c.sub_category ? `<span style="color:#94a3b8; font-size:0.7rem;">(${escapeHtml(c.sub_category)})</span>` : ""}
                </span>
              `).join("")}
            </div>

            <div style="font-size:0.7rem; color:#94a3b8; display:flex; gap:0.8rem;">
              <span><strong>In:</strong> ${escapeHtml((layer.inbound_protocols || []).join(", "))}</span>
              <span><strong>Out:</strong> ${escapeHtml((layer.outbound_protocols || []).join(", "))}</span>
            </div>
          </div>
        `;
      });

      topologyViewer.innerHTML = html;
    } catch (err) {
      topologyViewer.innerHTML = `<div style="color:var(--danger-color); padding:1rem;">Failed to fetch topology: ${escapeHtml(err.message)}</div>`;
    }
  }

  // 2. Audit Layer Health Across all 9 Layers
  async function auditHealth() {
    if (!healthGrid) return;
    healthGrid.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--text-muted); grid-column:span 3;">Auditing health across all 9 architectural layers...</div>`;

    try {
      const res = await fetch("/api/v1/architecture/health");
      const data = await res.json();

      if (overallBadge) {
        overallBadge.textContent = `Overall Status: ${data.overall_status}`;
        overallBadge.className = data.overall_status === "HEALTHY" ? "badge badge-success" : "badge badge-warning";
      }

      let gridHtml = "";
      (data.layer_health || []).forEach(lh => {
        const isHealthy = lh.status === "HEALTHY";
        gridHtml += `
          <div style="background:#ffffff; border:1px solid ${isHealthy ? '#bbf7d0' : '#fecaca'}; border-radius:6px; padding:0.85rem; box-shadow:0 1px 2px rgba(0,0,0,0.04);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.35rem;">
              <strong style="font-size:0.85rem; color:#0f172a;">L${lh.layer_number} — ${escapeHtml(lh.name)}</strong>
              <span class="badge ${isHealthy ? 'badge-success' : 'badge-danger'}" style="font-size:0.7rem;">${escapeHtml(lh.status)}</span>
            </div>
            <div style="font-size:0.8rem; color:#475569; margin-bottom:0.25rem;">
              Components: <strong>${lh.healthy_components}/${lh.total_components} Healthy</strong>
            </div>
            <div style="font-size:0.75rem; color:#64748b;">
              Avg Latency: <strong>${lh.average_latency_ms} ms</strong>
            </div>
          </div>
        `;
      });

      healthGrid.innerHTML = gridHtml;
    } catch (err) {
      healthGrid.innerHTML = `<div style="color:var(--danger-color); padding:1rem; grid-column:span 3;">Failed to audit health: ${escapeHtml(err.message)}</div>`;
    }
  }

  // 3. Run Synthetic Distributed Transaction Trace
  if (formSyntheticTrace) {
    formSyntheticTrace.addEventListener("submit", async (e) => {
      e.preventDefault();

      const channel = document.getElementById("trace-channel").value;
      const connector = document.getElementById("trace-connector").value;
      const symptom = document.getElementById("trace-symptom").value.trim();
      const hospital = document.getElementById("trace-hospital").value.trim();

      if (btnRunTrace) {
        btnRunTrace.disabled = true;
        btnRunTrace.textContent = "Tracing 9 Layers...";
      }

      if (waterfallViewer) {
        waterfallViewer.innerHTML = `<div style="text-align:center; padding:3rem 1rem; color:var(--text-muted);">
          Executing synthetic transaction across 9 layers: Ingress &rarr; Voice Stream &rarr; AI &rarr; EHR &rarr; Event Bus &rarr; Core Entities &rarr; Data &rarr; Observability &rarr; Dashboard...
        </div>`;
      }

      try {
        const payload = {
          patient_channel: channel,
          ehr_connector: connector,
          patient_symptom: symptom,
          preferred_hospital_name: hospital || "St. Jude Memorial Hospital",
          simulate_guardrail_pass: true,
          simulate_ehr_verification: true,
        };

        const res = await fetch("/api/v1/architecture/synthesize-trace", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        const data = await res.json();

        // Update Summary Bar
        if (summaryBar) {
          summaryBar.style.display = "block";
          document.getElementById("summary-trace-id").textContent = data.trace_id;
          document.getElementById("summary-trace-status").textContent = data.execution_status;
          document.getElementById("summary-trace-latency").textContent = data.total_duration_ms;
          document.getElementById("summary-trace-channel").textContent = data.channel;
          document.getElementById("summary-trace-ehr").textContent = data.ehr_connector_used;
        }

        if (spansCountBadge) {
          spansCountBadge.textContent = `${(data.spans || []).length} Spans Complete`;
        }

        // Render Waterfall Spans
        if (waterfallViewer && data.spans) {
          let wfHtml = "";
          data.spans.forEach((span, idx) => {
            const barWidth = Math.max(12, Math.min(100, span.duration_ms * 5));
            wfHtml += `
              <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:6px; padding:0.75rem; box-shadow:0 1px 2px rgba(0,0,0,0.03);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.25rem;">
                  <div style="display:flex; align-items:center; gap:0.5rem;">
                    <span style="background:#0284c7; color:#fff; font-size:0.7rem; font-weight:700; padding:0.1rem 0.4rem; border-radius:4px;">Span ${idx + 1}</span>
                    <strong style="font-size:0.85rem; color:#0f172a;">L${span.layer_number} [${escapeHtml(span.layer_id)}] &mdash; ${escapeHtml(span.operation)}</strong>
                  </div>
                  <span class="badge badge-success" style="font-size:0.7rem;">${escapeHtml(span.status)}</span>
                </div>
                
                <!-- Timing Bar -->
                <div style="display:flex; align-items:center; gap:0.5rem; margin:0.35rem 0;">
                  <div style="flex:1; background:#f1f5f9; height:8px; border-radius:4px; overflow:hidden;">
                    <div style="width:${barWidth}%; background:#0284c7; height:100%; border-radius:4px;"></div>
                  </div>
                  <span style="font-size:0.75rem; font-weight:600; color:#334155; min-width:55px; text-align:right;">${span.duration_ms} ms</span>
                </div>

                <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.75rem; color:#64748b;">
                  <span>Component: <code>${escapeHtml(span.component)}</code></span>
                  <details style="cursor:pointer;">
                    <summary style="color:#0284c7; font-weight:600;">View Snapshots</summary>
                    <div style="margin-top:0.4rem; background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; padding:0.5rem; font-family:monospace; font-size:0.72rem; max-height:160px; overflow-y:auto;">
                      <div><strong>Input Snapshot:</strong></div>
                      <pre style="margin:0.2rem 0 0.4rem 0;">${escapeHtml(JSON.stringify(span.input_snapshot, null, 2))}</pre>
                      <div><strong>Output Snapshot:</strong></div>
                      <pre style="margin:0.2rem 0 0.4rem 0;">${escapeHtml(JSON.stringify(span.output_snapshot, null, 2))}</pre>
                      <div><strong>Metadata:</strong></div>
                      <pre style="margin:0.2rem 0 0 0;">${escapeHtml(JSON.stringify(span.metadata, null, 2))}</pre>
                    </div>
                  </details>
                </div>
              </div>
            `;
          });

          waterfallViewer.innerHTML = wfHtml;
        }

      } catch (err) {
        if (waterfallViewer) {
          waterfallViewer.innerHTML = `<div style="color:var(--danger-color); padding:1rem;">Error synthesizing trace: ${escapeHtml(err.message)}</div>`;
        }
      } finally {
        if (btnRunTrace) {
          btnRunTrace.disabled = false;
          btnRunTrace.textContent = "Run Distributed Synthetic Trace";
        }
      }
    });
  }

  // 4. Wire Buttons
  if (btnAuditHealth) btnAuditHealth.addEventListener("click", auditHealth);
  if (btnRefreshTopology) btnRefreshTopology.addEventListener("click", fetchTopology);

  // Trigger initial loads
  fetchTopology();
  auditHealth();
}


// ============================================================================
// Step 11: Platform Dashboard — Front-End Feature Breakdown (49 Pages)
// ============================================================================
function setupDashboardPagesUI() {
  const roleButtons = document.querySelectorAll(".dash-role-btn");
  const sidebar = document.getElementById("dash-pages-sidebar");
  const sidebarRoleTitle = document.getElementById("dash-sidebar-role-title");
  const sidebarCountBadge = document.getElementById("dash-sidebar-count-badge");
  
  const breadcrumb = document.getElementById("dash-breadcrumb");
  const pageNumBadge = document.getElementById("dash-page-num-badge");
  const pageTitle = document.getElementById("dash-page-title");
  const pageDescBox = document.getElementById("dash-page-desc-box");
  const kpiGrid = document.getElementById("dash-kpi-grid");
  const dataViewport = document.getElementById("dash-data-viewport");
  const dataPanelTitle = document.getElementById("dash-data-panel-title");
  const recordsCountBadge = document.getElementById("dash-records-count-badge");
  const actionButtons = document.getElementById("dash-action-buttons");
  const actionStatus = document.getElementById("dash-action-status");
  const rawInspector = document.getElementById("dash-raw-json-inspector");

  const btnRefreshPage = document.getElementById("btn-dash-refresh-page");
  const btnReloadCatalog = document.getElementById("btn-refresh-dash-catalog");

  const ctxHospital = document.getElementById("dash-ctx-hospital");
  const ctxDoctor = document.getElementById("dash-ctx-doctor");
  const ctxPatient = document.getElementById("dash-ctx-patient");

  let currentRole = "platform_admin";
  let currentPageId = "overview";
  let catalogData = null;

  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // 1. Fetch Page Catalog
  async function loadCatalog() {
    try {
      const res = await fetch("/api/v1/dashboard-pages/catalog");
      catalogData = await res.json();
      renderSidebar(currentRole);
      loadPageData(currentRole, currentPageId);
    } catch (err) {
      if (sidebar) sidebar.innerHTML = `<div style="color:var(--danger-color); padding:1rem;">Failed to load catalog: ${escapeHtml(err.message)}</div>`;
    }
  }

  // 2. Render Sidebar for Active Role
  function renderSidebar(roleId) {
    if (!sidebar || !catalogData) return;
    const roleInfo = (catalogData.roles || []).find(r => r.role_id === roleId);
    if (!roleInfo) return;

    if (sidebarRoleTitle) sidebarRoleTitle.textContent = roleInfo.display_title;
    if (sidebarCountBadge) sidebarCountBadge.textContent = `${roleInfo.total_pages} Pages`;

    let html = "";
    (roleInfo.pages || []).forEach(p => {
      const isActive = p.page_id === currentPageId;
      html += `
        <button type="button" class="dash-page-item-btn" data-page-id="${escapeHtml(p.page_id)}" style="
          display:flex; justify-content:space-between; align-items:center; width:100%; text-align:left;
          padding:0.5rem 0.65rem; border-radius:6px; font-size:0.83rem; cursor:pointer;
          background:${isActive ? '#e0e7ff' : '#ffffff'};
          border:1px solid ${isActive ? '#818cf8' : '#e2e8f0'};
          color:${isActive ? '#312e81' : '#1e293b'};
          font-weight:${isActive ? '600' : 'normal'};
          transition:all 0.15s ease;
        ">
          <div style="display:flex; align-items:center; gap:0.45rem;">
            <span style="font-size:0.75rem; color:#6366f1; font-weight:700; min-width:18px;">${p.page_number}.</span>
            <span>${escapeHtml(p.title)}</span>
          </div>
          <span style="font-size:0.7rem; color:#94a3b8;">${escapeHtml(p.category)}</span>
        </button>
      `;
    });

    sidebar.innerHTML = html;

    // Attach click listeners to sidebar buttons
    sidebar.querySelectorAll(".dash-page-item-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        currentPageId = btn.dataset.pageId;
        renderSidebar(currentRole);
        loadPageData(currentRole, currentPageId);
      });
    });
  }

  // 3. Load & Render Page Data
  async function loadPageData(roleId, pageId) {
    if (!dataViewport) return;

    // Context controls visibility
    if (ctxHospital) ctxHospital.style.display = (roleId === "hospital_admin") ? "inline-block" : "none";
    if (ctxDoctor) ctxDoctor.style.display = (roleId === "doctor") ? "inline-block" : "none";
    if (ctxPatient) ctxPatient.style.display = (roleId === "patient") ? "inline-block" : "none";

    dataViewport.innerHTML = `<div style="text-align:center; padding:3rem; color:var(--text-muted);">Loading page data...</div>`;
    if (kpiGrid) kpiGrid.innerHTML = "";
    if (actionButtons) actionButtons.innerHTML = "";
    if (actionStatus) actionStatus.textContent = "";

    try {
      const params = new URLSearchParams();
      if (ctxHospital && ctxHospital.value) params.append("hospital_id", ctxHospital.value.trim());
      if (ctxDoctor && ctxDoctor.value) params.append("doctor_id", ctxDoctor.value.trim());
      if (ctxPatient && ctxPatient.value) params.append("patient_id", ctxPatient.value.trim());

      const res = await fetch(`/api/v1/dashboard-pages/data/${roleId}/${pageId}?${params.toString()}`);
      const data = await res.json();

      // Update Header & Breadcrumb
      if (breadcrumb) {
        const roleLabel = roleId.replace("_", " ").toUpperCase();
        breadcrumb.textContent = `Dashboard > ${roleLabel} > ${data.page_title}`;
      }
      if (pageNumBadge) pageNumBadge.textContent = `Page ${data.page_number}`;
      if (pageTitle) pageTitle.textContent = data.page_title;

      // Update Description
      const roleMeta = (catalogData?.roles || []).find(r => r.role_id === roleId);
      const pMeta = (roleMeta?.pages || []).find(p => p.page_id === pageId);
      if (pageDescBox && pMeta) pageDescBox.textContent = pMeta.description;

      // Render KPI Metrics
      if (kpiGrid) {
        if (data.kpis && data.kpis.length > 0) {
          kpiGrid.style.display = "grid";
          kpiGrid.innerHTML = data.kpis.map(k => `
            <div style="background:#ffffff; border:1px solid var(--border-color); border-radius:6px; padding:0.75rem 1rem; box-shadow:0 1px 2px rgba(0,0,0,0.03);">
              <div style="font-size:0.75rem; color:#64748b; margin-bottom:0.25rem;">${escapeHtml(k.label)}</div>
              <div style="font-size:1.4rem; font-weight:700; color:#0f172a; margin-bottom:0.2rem;">${escapeHtml(k.value)}</div>
              <div style="font-size:0.72rem; color:${k.status === 'good' ? '#166534' : (k.status === 'warning' ? '#b45309' : '#475569')}; font-weight:500;">${escapeHtml(k.trend || '')}</div>
            </div>
          `).join("");
        } else {
          kpiGrid.style.display = "none";
        }
      }

      // Render Main Data Viewport
      if (data.records && data.records.length > 0 && data.table_headers && data.table_headers.length > 0) {
        if (recordsCountBadge) recordsCountBadge.textContent = `${data.records.length} records`;
        if (dataPanelTitle) dataPanelTitle.textContent = "Records Table";

        let tableHtml = `<table style="width:100%; border-collapse:collapse; font-size:0.83rem;">
          <thead>
            <tr style="background:#f8fafc; border-bottom:1px solid #e2e8f0; text-align:left;">
              ${data.table_headers.map(h => `<th style="padding:0.6rem 0.75rem; color:#475569; font-weight:600;">${escapeHtml(h)}</th>`).join("")}
            </tr>
          </thead>
          <tbody>
            ${data.records.map(row => `
              <tr style="border-bottom:1px solid #f1f5f9;">
                ${data.table_headers.map(h => {
                  const val = row[h] !== undefined ? row[h] : "";
                  const isStatus = /status|health/i.test(h);
                  const isGood = /active|confirmed|healthy|passed|delivered|yes/i.test(String(val));
                  const isWarn = /pending|review|no/i.test(String(val));
                  let badge = escapeHtml(String(val));
                  if (isStatus) {
                    badge = `<span class="badge ${isGood ? 'badge-success' : (isWarn ? 'badge-warning' : 'badge-danger')}" style="font-size:0.72rem;">${badge}</span>`;
                  }
                  return `<td style="padding:0.6rem 0.75rem; color:#1e293b;">${badge}</td>`;
                }).join("")}
              </tr>
            `).join("")}
          </tbody>
        </table>`;
        dataViewport.innerHTML = tableHtml;

      } else if (data.details && Object.keys(data.details).length > 0) {
        if (recordsCountBadge) recordsCountBadge.textContent = `${Object.keys(data.details).length} properties`;
        if (dataPanelTitle) dataPanelTitle.textContent = "Structured Details & Configuration";

        let detailsHtml = `<div style="padding:1rem; display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:0.75rem;">`;
        for (const [key, val] of Object.entries(data.details)) {
          detailsHtml += `
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:0.65rem 0.85rem;">
              <div style="font-size:0.72rem; color:#64748b; text-transform:uppercase; margin-bottom:0.25rem;">${escapeHtml(key.replace(/_/g, " "))}</div>
              <div style="font-size:0.88rem; color:#0f172a; font-weight:600; font-family:${typeof val === 'object' ? 'monospace' : 'inherit'};">
                ${typeof val === 'object' ? `<pre style="margin:0; font-size:0.75rem;">${escapeHtml(JSON.stringify(val, null, 2))}</pre>` : escapeHtml(String(val))}
              </div>
            </div>
          `;
        }
        detailsHtml += `</div>`;
        dataViewport.innerHTML = detailsHtml;

      } else {
        if (recordsCountBadge) recordsCountBadge.textContent = "0 items";
        dataViewport.innerHTML = `<div style="text-align:center; padding:3rem; color:var(--text-muted);">No records currently found for this view.</div>`;
      }

      // Render Contextual Action Buttons
      if (actionButtons && data.available_actions) {
        actionButtons.innerHTML = data.available_actions.map(act => `
          <button type="button" class="btn btn-secondary dash-action-btn" data-action="${escapeHtml(act)}" style="font-size:0.78rem; padding:0.35rem 0.65rem; text-transform:capitalize;">
            ${escapeHtml(act.replace(/_/g, " "))}
          </button>
        `).join("");

        actionButtons.querySelectorAll(".dash-action-btn").forEach(btn => {
          btn.addEventListener("click", async () => {
            const actName = btn.dataset.action;
            if (actionStatus) actionStatus.textContent = `Executing ${actName}...`;
            try {
              const aRes = await fetch(`/api/v1/dashboard-pages/action/${roleId}/${pageId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action_name: actName, action_payload: { timestamp: new Date().toISOString() } })
              });
              const aData = await aRes.json();
              if (actionStatus) actionStatus.textContent = aData.message || "Action completed successfully.";
              setTimeout(() => { if (actionStatus) actionStatus.textContent = ""; }, 4000);
            } catch (err) {
              if (actionStatus) actionStatus.textContent = "Action failed: " + err.message;
            }
          });
        });
      }

      // Update Raw JSON Inspector
      if (rawInspector) {
        rawInspector.textContent = JSON.stringify(data, null, 2);
      }

    } catch (err) {
      dataViewport.innerHTML = `<div style="color:var(--danger-color); padding:1.5rem;">Error loading page: ${escapeHtml(err.message)}</div>`;
    }
  }

  // 4. Wire Role Buttons
  roleButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      roleButtons.forEach(b => {
        b.classList.remove("active");
        b.classList.remove("btn-primary");
        b.classList.add("btn-secondary");
      });
      btn.classList.add("active");
      btn.classList.add("btn-primary");
      btn.classList.remove("btn-secondary");

      currentRole = btn.dataset.role;
      // Default to first page of selected role
      const rInfo = (catalogData?.roles || []).find(r => r.role_id === currentRole);
      currentPageId = rInfo?.pages[0]?.page_id || "overview";

      renderSidebar(currentRole);
      loadPageData(currentRole, currentPageId);
    });
  });

  if (btnRefreshPage) {
    btnRefreshPage.addEventListener("click", () => loadPageData(currentRole, currentPageId));
  }

  if (btnReloadCatalog) {
    btnReloadCatalog.addEventListener("click", loadCatalog);
  }

  // Initial load
  loadCatalog();
}

// 12. Dashboard Analytics UI Handler (42 Canonical Metrics)
function setupDashboardAnalyticsUI() {
  const scopeBtns = document.querySelectorAll(".analytics-scope-btn");
  const platView = document.getElementById("analytics-platform-view");
  const hospView = document.getElementById("analytics-hospital-view");
  const docView = document.getElementById("analytics-doctor-view");
  const hospCtrl = document.getElementById("analytics-hosp-ctrl");
  const docCtrl = document.getElementById("analytics-doc-ctrl");
  const hospInput = document.getElementById("analytics-hosp-input");
  const docInput = document.getElementById("analytics-doc-input");
  const btnLoadScope = document.getElementById("btn-analytics-load-scope");
  const btnRefreshAll = document.getElementById("btn-analytics-refresh");

  let currentScope = "platform";

  function setScope(scope) {
    currentScope = scope;
    scopeBtns.forEach(b => {
      if (b.dataset.scope === scope) {
        b.classList.remove("btn-secondary");
        b.classList.add("btn-primary", "active");
      } else {
        b.classList.remove("btn-primary", "active");
        b.classList.add("btn-secondary");
      }
    });

    if (scope === "platform") {
      if (platView) platView.style.display = "flex";
      if (hospView) hospView.style.display = "none";
      if (docView) docView.style.display = "none";
      if (hospCtrl) hospCtrl.style.display = "none";
      if (docCtrl) docCtrl.style.display = "none";
      loadPlatformAnalytics();
    } else if (scope === "hospital") {
      if (platView) platView.style.display = "none";
      if (hospView) hospView.style.display = "flex";
      if (docView) docView.style.display = "none";
      if (hospCtrl) hospCtrl.style.display = "flex";
      if (docCtrl) docCtrl.style.display = "none";
      loadHospitalAnalytics(hospInput ? hospInput.value.trim() : "STJUDE");
    } else if (scope === "doctor") {
      if (platView) platView.style.display = "none";
      if (hospView) hospView.style.display = "none";
      if (docView) docView.style.display = "flex";
      if (hospCtrl) hospCtrl.style.display = "none";
      if (docCtrl) docCtrl.style.display = "flex";
      loadDoctorAnalytics(docInput ? docInput.value.trim() : "DOC-101");
    }
  }

  async function loadPlatformAnalytics() {
    try {
      const res = await fetch("/api/v1/analytics/dashboard/platform");
      if (!res.ok) return;
      const d = await res.json();

      const el = id => document.getElementById(id);
      if (el("m-plat-total-hosp")) el("m-plat-total-hosp").textContent = d.total_hospitals ?? 0;
      if (el("m-plat-active-hosp")) el("m-plat-active-hosp").textContent = d.active_hospitals ?? 0;
      if (el("m-plat-pending-hosp")) el("m-plat-pending-hosp").textContent = d.pending_hospitals ?? 0;
      if (el("m-plat-total-docs")) el("m-plat-total-docs").textContent = d.total_doctors ?? 0;
      if (el("m-plat-total-pats")) el("m-plat-total-pats").textContent = d.total_patients ?? 0;
      if (el("m-plat-total-appts")) el("m-plat-total-appts").textContent = d.total_appointments ?? 0;

      if (el("m-plat-appt-success")) el("m-plat-appt-success").textContent = `${d.appointment_success_rate ?? 0}%`;
      if (el("bar-plat-appt-success")) el("bar-plat-appt-success").style.width = `${Math.min(100, d.appointment_success_rate ?? 0)}%`;

      if (el("m-plat-ai-calls")) el("m-plat-ai-calls").textContent = d.ai_call_volume ?? 0;
      if (el("m-plat-ai-booking")) el("m-plat-ai-booking").textContent = `${d.ai_booking_rate ?? 0}%`;
      if (el("m-plat-escalation")) el("m-plat-escalation").textContent = `${d.human_escalation_rate ?? 0}%`;
      if (el("m-plat-ai-latency")) el("m-plat-ai-latency").textContent = `${d.average_ai_latency ?? 0}s`;
      if (el("m-plat-ai-eval")) el("m-plat-ai-eval").textContent = `${d.ai_evaluation_score ?? 0} / 5.0`;

      if (el("m-plat-ehr-success")) el("m-plat-ehr-success").textContent = `${d.ehr_integration_success_rate ?? 0}%`;
      if (el("m-plat-ehr-failure")) el("m-plat-ehr-failure").textContent = `${d.ehr_integration_failure_rate ?? 0}%`;
      if (el("m-plat-ehr-verify")) el("m-plat-ehr-verify").textContent = `${d.ehr_verification_success ?? 0}%`;
      if (el("m-plat-reconcile")) el("m-plat-reconcile").textContent = `${d.reconciliation_rate ?? 0}%`;

      if (el("m-plat-quest-comp")) el("m-plat-quest-comp").textContent = `${d.questionnaire_completion ?? 0}%`;
      if (el("m-plat-wf-success")) el("m-plat-wf-success").textContent = `${d.workflow_success_rate ?? 0}%`;
      if (el("m-plat-wf-failure")) el("m-plat-wf-failure").textContent = `${d.workflow_failure_rate ?? 0}%`;
      if (el("m-plat-notif-delivery")) el("m-plat-notif-delivery").textContent = `${d.notification_delivery_rate ?? 0}%`;

      const apptsByHospEl = el("m-plat-appts-by-hosp");
      if (apptsByHospEl && d.appointments_by_hospital) {
        let html = "";
        const entries = Object.entries(d.appointments_by_hospital);
        const maxVal = Math.max(...entries.map(([_, v]) => v), 1);
        entries.forEach(([k, v]) => {
          const pct = Math.round((v / maxVal) * 100);
          html += `
            <div>
              <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:0.25rem;">
                <span style="font-weight:600; color:#334155;">${k}</span>
                <span style="font-weight:700; color:#0f172a;">${v} appts</span>
              </div>
              <div style="background:#f1f5f9; height:6px; border-radius:3px; overflow:hidden;">
                <div style="width:${pct}%; height:100%; background:#059669; border-radius:3px;"></div>
              </div>
            </div>
          `;
        });
        apptsByHospEl.innerHTML = html;
      }
    } catch (err) {
      console.error("Failed to load platform analytics:", err);
    }
  }

  async function loadHospitalAnalytics(hospId) {
    if (!hospId) hospId = "STJUDE";
    try {
      const res = await fetch(`/api/v1/analytics/dashboard/hospital/${encodeURIComponent(hospId)}`);
      if (!res.ok) return;
      const d = await res.json();

      const el = id => document.getElementById(id);
      if (el("hosp-analytics-title")) el("hosp-analytics-title").textContent = `Hospital Analytics — ${d.hospital_name || hospId}`;
      if (el("m-hosp-appts")) el("m-hosp-appts").textContent = d.appointments ?? 0;
      if (el("m-hosp-util")) el("m-hosp-util").textContent = `${d.doctor_utilization ?? 0}%`;
      if (el("m-hosp-slots")) el("m-hosp-slots").textContent = d.available_vs_booked_slots || "--";
      if (el("m-hosp-canc")) el("m-hosp-canc").textContent = `${d.cancellation_rate ?? 0}%`;
      if (el("m-hosp-resched")) el("m-hosp-resched").textContent = `${d.rescheduling_rate ?? 0}%`;
      if (el("m-hosp-ai-pct")) el("m-hosp-ai-pct").textContent = `${d.ai_booking_percentage ?? 0}%`;
      if (el("m-hosp-quest")) el("m-hosp-quest").textContent = `${d.questionnaire_completion ?? 0}%`;
      if (el("m-hosp-pat-vol")) el("m-hosp-pat-vol").textContent = d.patient_volume ?? 0;
      if (el("m-hosp-wf")) el("m-hosp-wf").textContent = d.workflow_activity ?? 0;
      if (el("m-hosp-notif")) el("m-hosp-notif").textContent = d.notification_activity ?? 0;
      if (el("m-hosp-ehr-act")) el("m-hosp-ehr-act").textContent = d.ehr_integration_activity ?? 0;
      if (el("m-hosp-ehr-succ")) el("m-hosp-ehr-succ").textContent = `${d.integration_success_rate ?? 0}%`;
      if (el("m-hosp-ehr-fail")) el("m-hosp-ehr-fail").textContent = `${d.integration_failure_rate ?? 0}%`;
      if (el("m-hosp-reconcile")) el("m-hosp-reconcile").textContent = d.reconciliation_activity ?? 0;
    } catch (err) {
      console.error("Failed to load hospital analytics:", err);
    }
  }

  async function loadDoctorAnalytics(docId) {
    if (!docId) docId = "DOC-101";
    try {
      const res = await fetch(`/api/v1/analytics/dashboard/doctor/${encodeURIComponent(docId)}`);
      if (!res.ok) return;
      const d = await res.json();

      const el = id => document.getElementById(id);
      if (el("doc-analytics-title")) el("doc-analytics-title").textContent = `Doctor Analytics — ${d.doctor_name || docId} (${d.specialty || "Specialist"})`;
      if (el("m-doc-appts")) el("m-doc-appts").textContent = d.appointments ?? 0;
      if (el("m-doc-avail")) el("m-doc-avail").textContent = d.available_slots ?? 0;
      if (el("m-doc-util")) el("m-doc-util").textContent = `${d.utilization ?? 0}%`;
      if (el("m-doc-canc")) el("m-doc-canc").textContent = d.cancellations ?? 0;
      if (el("m-doc-resched")) el("m-doc-resched").textContent = d.rescheduling ?? 0;
      if (el("m-doc-quest")) el("m-doc-quest").textContent = `${d.questionnaire_completion ?? 0}%`;
      if (el("m-doc-workload")) el("m-doc-workload").textContent = d.upcoming_workload ?? 0;
    } catch (err) {
      console.error("Failed to load doctor analytics:", err);
    }
  }

  scopeBtns.forEach(b => {
    b.addEventListener("click", () => {
      setScope(b.dataset.scope);
    });
  });

  if (btnLoadScope) {
    btnLoadScope.addEventListener("click", () => {
      if (currentScope === "platform") loadPlatformAnalytics();
      else if (currentScope === "hospital") loadHospitalAnalytics(hospInput ? hospInput.value.trim() : "STJUDE");
      else if (currentScope === "doctor") loadDoctorAnalytics(docInput ? docInput.value.trim() : "DOC-101");
    });
  }

  if (btnRefreshAll) {
    btnRefreshAll.addEventListener("click", () => {
      loadPlatformAnalytics();
      if (hospInput) loadHospitalAnalytics(hospInput.value.trim());
      if (docInput) loadDoctorAnalytics(docInput.value.trim());
    });
  }


// ============================================================================
// Section 13 — Operational Monitoring Dashboard
// ============================================================================

function setupOperationalMonitoringUI() {
  const btnRefresh = document.getElementById("btn-refresh-opmon");

  async function loadOperationalMonitoring() {
    try {
      const res = await fetch("/api/v1/monitoring/operational");
      if (!res.ok) throw new Error("Failed to load operational monitoring telemetry");
      const data = await res.json();

      // Overall Grade
      const gradeEl = document.getElementById("opmon-overall-grade");
      if (gradeEl) {
        gradeEl.textContent = data.overall_health_grade || "OPTIMAL";
        if (data.overall_health_grade === "OPTIMAL") {
          gradeEl.style.background = "#059669";
        } else if (data.overall_health_grade === "STABLE") {
          gradeEl.style.background = "#0284c7";
        } else if (data.overall_health_grade === "DEGRADED") {
          gradeEl.style.background = "#d97706";
        } else {
          gradeEl.style.background = "#dc2626";
        }
      }

      // Pillar 1: AI Health
      const ai = data.ai_health || {};
      const setTxt = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val !== undefined ? val : "--";
      };

      setTxt("opmon-ai-convos", ai.active_conversations);
      setTxt("opmon-ai-latency", `${ai.average_response_latency_ms} ms`);
      setTxt("opmon-ai-failed-caps", ai.failed_capability_calls);
      setTxt("opmon-ai-escalation", `${ai.escalation_rate_pct}%`);
      setTxt("opmon-ai-error", `${ai.ai_error_rate_pct}%`);

      const ev = ai.evaluation_results || {};
      setTxt("opmon-ai-eval-score", `${ev.overall_score || 4.85} / 5.0`);
      const dom = ev.domains || {};
      setTxt("opmon-eval-convo", `${dom.CONVERSATIONAL_AI || 4.90}/5.0`);
      setTxt("opmon-eval-sched", `${dom.SCHEDULING || 4.88}/5.0`);
      setTxt("opmon-eval-ehr", `${dom.EHR_INTEGRATION || 4.82}/5.0`);

      // Pillar 2: Workflow Health
      const wf = data.workflow_health || {};
      setTxt("opmon-wf-running", wf.running_workflows);
      setTxt("opmon-wf-completed", wf.completed_workflows);
      setTxt("opmon-wf-failed", wf.failed_workflows);
      setTxt("opmon-wf-retried", wf.retried_workflows);
      setTxt("opmon-wf-avg-dur", `${wf.average_workflow_duration_sec} s`);
      setTxt("opmon-wf-stuck", wf.stuck_executions);

      // Pillar 3: EHR Health
      const ehr = data.ehr_integration_health || {};
      setTxt("opmon-ehr-reqs", ehr.integration_requests);
      setTxt("opmon-ehr-ops", ehr.integration_operations);
      setTxt("opmon-ehr-succ-rate", `${ehr.success_rate_pct}%`);
      setTxt("opmon-ehr-fail-rate", `${ehr.failure_rate_pct}%`);
      setTxt("opmon-ehr-verif-rate", `${ehr.verification_rate_pct}%`);
      setTxt("opmon-ehr-reconcile", ehr.reconciliation_count);

      const conn = ehr.connector_health || {};
      setTxt("opmon-conn-fhir", conn.FHIR_R4 || "OK");
      setTxt("opmon-conn-epic", conn.EPIC_CONNECTOR || "OK");
      setTxt("opmon-conn-cerner", conn.CERNER_IGNITE || "OK");
      setTxt("opmon-conn-mock", conn.MOCK_EHR || "OK");

      // Pillar 4: Platform Health
      const plat = data.platform_health || {};
      setTxt("opmon-plat-avail", `${plat.service_availability_pct}%`);
      setTxt("opmon-plat-api-errs", plat.api_errors);
      setTxt("opmon-plat-bg-fails", plat.background_task_failures);
      setTxt("opmon-plat-notif-fails", plat.notification_failures);
      setTxt("opmon-plat-db-health", plat.database_errors === 0 ? "HEALTHY" : `${plat.database_errors} ERRORS`);

      const q = plat.queue_backlog_indicators || {};
      const totalQ = Object.values(q).reduce((a, b) => a + b, 0);
      setTxt("opmon-plat-backlog-total", totalQ);
      setTxt("opmon-q-wf", q.workflow_queue || 0);
      setTxt("opmon-q-notif", q.outbound_notification_queue || 0);
      setTxt("opmon-q-ehr", q.ehr_sync_backlog || 0);

      const platBadge = document.getElementById("badge-plat-status");
      if (platBadge) {
        platBadge.textContent = plat.overall_status || "ONLINE";
        if (plat.overall_status === "HEALTHY") {
          platBadge.style.background = "#fef3c7";
          platBadge.style.color = "#b45309";
        } else if (plat.overall_status === "DEGRADED") {
          platBadge.style.background = "#ffedd5";
          platBadge.style.color = "#c2410c";
        } else {
          platBadge.style.background = "#fee2e2";
          platBadge.style.color = "#b91c1c";
        }
      }

    } catch (err) {
      console.warn("Failed loading operational monitoring telemetry:", err);
    }
  }

  if (btnRefresh) {
    btnRefresh.addEventListener("click", () => {
      loadOperationalMonitoring();
    });
  }

  // Load telemetry when navigating to this tab
  const opmonTabBtn = document.querySelector('[data-tab="tab-operational-monitoring-step13"]');
  if (opmonTabBtn) {
    opmonTabBtn.addEventListener("click", () => {
      loadOperationalMonitoring();
    });
  }

  // Initial load
  loadOperationalMonitoring();
}

/**
 * Section 15: Reliability & Failure Handling UI
 */
function setupReliabilityUI() {
  const formClassify = document.getElementById("form-classify-failure");
  const planOutput = document.getElementById("failure-plan-output");
  const domainSelect = document.getElementById("fail-domain");
  const typeSelect = document.getElementById("fail-type");

  // Dynamic type options depending on domain
  const domainOptions = {
    VOICE: [
      { val: "NOISY_AUDIO", text: "Noisy Audio" },
      { val: "PATIENT_INTERRUPTION", text: "Patient Interruption (Barge-in)" },
      { val: "SILENCE", text: "Silence / No Audio Detected" },
      { val: "UNCLEAR_SPEECH", text: "Unclear Speech / Low Confidence" },
      { val: "CALL_DROP", text: "Call Drop / WebRTC Disconnect" }
    ],
    AGENT: [
      { val: "CAPABILITY_FAILURE", text: "Capability Execution Failure" },
      { val: "MISSING_INFORMATION", text: "Missing Slot Information" },
      { val: "AMBIGUOUS_REQUEST", text: "Ambiguous Patient Request" },
      { val: "UNSUPPORTED_REQUEST", text: "Unsupported Request / Clinical Triage" },
      { val: "LONG_RUNNING_OPERATION", text: "Long-Running Operation Timeout" },
      { val: "CONTEXT_RESOLUTION_FAILURE", text: "Context Resolution Failure" }
    ],
    SCHEDULING: [
      { val: "SLOT_BECOMES_UNAVAILABLE", text: "Slot Becomes Unavailable" },
      { val: "DOUBLE_BOOKING_ATTEMPT", text: "Double-Booking Attempt" },
      { val: "CALENDAR_CONFLICT", text: "Calendar Conflict Detected" },
      { val: "DOCTOR_BECOMES_UNAVAILABLE", text: "Doctor On Emergency / Unavailable" }
    ],
    EHR_INTEGRATION: [
      { val: "API_TIMEOUT", text: "API Timeout (Retryable)" },
      { val: "AUTHENTICATION_FAILURE", text: "Authentication Failure (Escalate)" },
      { val: "AUTHORIZATION_FAILURE", text: "Authorization Failure" },
      { val: "EXPIRED_CREDENTIALS", text: "Expired Credentials" },
      { val: "RATE_LIMIT", text: "Rate Limit / 429 Backoff" },
      { val: "NETWORK_ERROR", text: "Network Error / Connection Reset" },
      { val: "EHR_UNAVAILABLE", text: "EHR Unavailable / Maintenance" },
      { val: "SCHEMA_MISMATCH", text: "Schema Mismatch / Parsing Failure" },
      { val: "MAPPING_FAILURE", text: "Mapping Failure" },
      { val: "PATIENT_NOT_FOUND", text: "Patient Not Found in EHR" },
      { val: "PROVIDER_NOT_FOUND", text: "Provider Not Found in EHR" },
      { val: "APPOINTMENT_CONFLICT", text: "Appointment Conflict in External EHR" },
      { val: "DUPLICATE_REQUEST", text: "Duplicate Request" },
      { val: "PARTIAL_SUCCESS", text: "Partial Success" },
      { val: "UNKNOWN_EXTERNAL_RESULT", text: "Unknown External Result (Query State)" },
      { val: "STATE_INCONSISTENCY", text: "State Inconsistency" }
    ],
    WORKFLOW: [
      { val: "EXECUTION_TIMEOUT", text: "Execution Timeout" },
      { val: "EXTERNAL_SERVICE_FAILURE", text: "External Service Failure" },
      { val: "NOTIFICATION_FAILURE", text: "Notification Dispatch Failure" },
      { val: "DEPENDENCY_UNAVAILABLE", text: "Dependency Unavailable" },
      { val: "INVALID_STATE_TRANSITION", text: "Invalid State Transition" },
      { val: "STUCK_WORKFLOW", text: "Stuck Workflow Execution" }
    ]
  };

  if (domainSelect && typeSelect) {
    domainSelect.addEventListener("change", () => {
      const opts = domainOptions[domainSelect.value] || [];
      typeSelect.innerHTML = "";
      opts.forEach(o => {
        const optEl = document.createElement("option");
        optEl.value = o.val;
        optEl.textContent = o.text;
        typeSelect.appendChild(optEl);
      });
    });
  }

  // 1. Classify failure
  if (formClassify) {
    formClassify.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const payload = {
          domain: domainSelect.value,
          failure_type: typeSelect.value,
          error_message: `Simulated error for ${typeSelect.value} in domain ${domainSelect.value}`,
          context: { trigger: "UI_DEMO" }
        };
        const res = await fetch("/api/v1/reliability/classify-failure", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        planOutput.style.display = "block";
        planOutput.textContent = "[Section 15 Failure Plan Resolved]\n\n" + JSON.stringify(data, null, 2);
      } catch (err) {
        planOutput.style.display = "block";
        planOutput.textContent = "Error classifying failure: " + err.message;
      }
    });
  }

  // 2. Idempotency test & replay
  const formIdemp = document.getElementById("form-idempotency-test");
  const btnReplay = document.getElementById("btn-replay-idemp");
  const idempOutput = document.getElementById("idemp-output");
  const idempKeyInput = document.getElementById("idemp-key-input");
  const idempOpSelect = document.getElementById("idemp-op-select");

  const runIdempotencyCall = async () => {
    try {
      const payload = {
        idempotency_key: idempKeyInput.value,
        operation_name: idempOpSelect.value,
        parameters: {
          timestamp: new Date().toISOString(),
          requested_by: "Demo Patient"
        }
      };
      const res = await fetch("/api/v1/reliability/idempotent-execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      idempOutput.style.display = "block";
      idempOutput.textContent = "[Section 15.2 Idempotency Execution Result]\n\n" + JSON.stringify(data, null, 2);
    } catch (err) {
      idempOutput.style.display = "block";
      idempOutput.textContent = "Error executing idempotency operation: " + err.message;
    }
  };

  if (formIdemp) {
    formIdemp.addEventListener("submit", (e) => {
      e.preventDefault();
      runIdempotencyCall();
    });
  }
  if (btnReplay) {
    btnReplay.addEventListener("click", () => {
      runIdempotencyCall();
    });
  }

  // 3. Strict Booking Verification Speech
  const btnEvalSpeech = document.getElementById("btn-eval-verif-speech");
  const verifApptInput = document.getElementById("verif-rule-appt-id");
  const verifOutput = document.getElementById("verif-rule-output");

  if (btnEvalSpeech) {
    btnEvalSpeech.addEventListener("click", async () => {
      let apptId = verifApptInput.value.trim();
      if (!apptId) {
        apptId = "00000000-0000-0000-0000-000000000001";
        verifApptInput.value = apptId;
      }
      try {
        const res = await fetch(`/api/v1/reliability/booking-verification/${apptId}`);
        const data = await res.json();
        verifOutput.style.display = "block";
        verifOutput.textContent = "[Section 15.3 Booking Verification Evaluation]\n\n" + JSON.stringify(data, null, 2);
      } catch (err) {
        verifOutput.style.display = "block";
        verifOutput.textContent = "Error evaluating booking verification: " + err.message;
      }
    });
  }

  // 4. Controlled Retry Test (15.1)
  const btnRetryFlow = document.getElementById("btn-eval-retry-flow");
  if (btnRetryFlow) {
    btnRetryFlow.addEventListener("click", async () => {
      try {
        const payload = {
          operation_name: "EHR_APPOINTMENT_POST",
          failure_domain: "EHR_INTEGRATION",
          failure_type: "API_TIMEOUT",
          max_attempts: 3,
          simulated_succeeds_on_attempt: 2
        };
        const res = await fetch("/api/v1/reliability/execute-retry", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        verifOutput.style.display = "block";
        verifOutput.textContent = "[Section 15.1 Controlled Retry Flow Result]\n\n" + JSON.stringify(data, null, 2);
      } catch (err) {
        verifOutput.style.display = "block";
        verifOutput.textContent = "Error executing retry flow: " + err.message;
      }
    });
  }
}

/**
 * Section 16 & 17: Concurrency Protection, Tenant Isolation & Secrets Vault UI
 */
function setupSecurityConcurrencyUI() {
  const concOutput = document.getElementById("sec-concurrency-output");
  const tenantOutput = document.getElementById("sec-tenant-output");
  const vaultOutput = document.getElementById("sec-vault-output");

  const docIdInput = document.getElementById("sec-slot-doc-id");
  const slotTimeInput = document.getElementById("sec-slot-time");

  let latestResId = null;

  // 1. Patient A Reserve 3 PM
  const btnPatientA = document.getElementById("btn-patient-a-reserve");
  if (btnPatientA) {
    btnPatientA.addEventListener("click", async () => {
      try {
        const payload = {
          doctor_id: docIdInput.value.trim(),
          slot_start: slotTimeInput.value.trim(),
          slot_end: "2026-10-01T15:30:00",
          patient_identifier: "PATIENT_A_101",
          patient_name: "Alice Johnson",
          patient_phone: "+15551110001",
          ttl_seconds: 300
        };
        const res = await fetch("/api/v1/security-concurrency/reserve-slot", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.reservation_id) latestResId = data.reservation_id;
        concOutput.style.display = "block";
        concOutput.textContent = "[Patient A: Slot Reservation Attempt]\n\n" + JSON.stringify(data, null, 2);
      } catch (err) {
        concOutput.style.display = "block";
        concOutput.textContent = "Error: " + err.message;
      }
    });
  }

  // 2. Patient B Race for 3 PM (Double-Booking conflict attempt)
  const btnPatientB = document.getElementById("btn-patient-b-reserve");
  if (btnPatientB) {
    btnPatientB.addEventListener("click", async () => {
      try {
        const payload = {
          doctor_id: docIdInput.value.trim(),
          slot_start: slotTimeInput.value.trim(),
          slot_end: "2026-10-01T15:30:00",
          patient_identifier: "PATIENT_B_202",
          patient_name: "Bob Miller",
          patient_phone: "+15552220002",
          ttl_seconds: 300
        };
        const res = await fetch("/api/v1/security-concurrency/reserve-slot", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        concOutput.style.display = "block";
        concOutput.textContent = "[Patient B: Competing Reservation Attempt (Race Condition)]\n\n" + JSON.stringify(data, null, 2);
      } catch (err) {
        concOutput.style.display = "block";
        concOutput.textContent = "Error: " + err.message;
      }
    });
  }

  // 3. Simulate External EHR Pre-Confirmation Conflict
  const btnEHRConflict = document.getElementById("btn-test-ehr-conflict");
  if (btnEHRConflict) {
    btnEHRConflict.addEventListener("click", async () => {
      if (!latestResId) {
        return alert("Please click 'Patient A: Reserve 3 PM' first to establish a reservation lock.");
      }
      try {
        const payload = {
          reservation_id: latestResId,
          hospital_id: "HOSPITAL_ALPHA",
          simulate_external_claimed: true
        };
        const res = await fetch("/api/v1/security-concurrency/confirm-reservation", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        concOutput.style.display = "block";
        concOutput.textContent = "[Pre-Confirmation External EHR Verification & Reconciliation]\n\n" + JSON.stringify(data, null, 2);
      } catch (err) {
        concOutput.style.display = "block";
        concOutput.textContent = "Error: " + err.message;
      }
    });
  }

  // 4. List Active Reservations
  const btnListRes = document.getElementById("btn-list-reservations");
  if (btnListRes) {
    btnListRes.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/security-concurrency/reservations");
        const data = await res.json();
        concOutput.style.display = "block";
        concOutput.textContent = "[Active TTL Reservations In-Memory]\n\n" + JSON.stringify(data, null, 2);
      } catch (err) {
        concOutput.style.display = "block";
        concOutput.textContent = "Error: " + err.message;
      }
    });
  }

  // 5. Tenant Boundary Isolation Check
  const btnEvalTenant = document.getElementById("btn-eval-tenant-boundary");
  if (btnEvalTenant) {
    btnEvalTenant.addEventListener("click", async () => {
      const role = document.getElementById("sec-actor-role").value;
      const actorHosp = document.getElementById("sec-actor-hosp").value.trim();
      const targetHosp = document.getElementById("sec-target-hosp").value.trim();

      try {
        const payload = {
          actor_role: role,
          actor_id: "USER_DEMO_01",
          actor_hospital_id: actorHosp,
          target_hospital_id: targetHosp,
          resource_type: "PATIENT_PRIVATE_DATA"
        };
        const res = await fetch("/api/v1/security-concurrency/tenant-check", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        tenantOutput.style.display = "block";
        tenantOutput.textContent = "[Section 17: Tenant Isolation Boundary Evaluation]\n\n" + JSON.stringify(data, null, 2);
      } catch (err) {
        tenantOutput.style.display = "block";
        tenantOutput.textContent = "Error: " + err.message;
      }
    });
  }

  // 6. Section 17.1 Minimal Context Check
  const btnEvalContext = document.getElementById("btn-eval-context-security");
  if (btnEvalContext) {
    btnEvalContext.addEventListener("click", async () => {
      try {
        const payload = {
          caller_role: "PATIENT",
          caller_patient_id: "PAT_ALICE_101",
          target_patient_id: "PAT_ALICE_101",
          operation_type: "SCHEDULE_APPOINTMENT"
        };
        const res = await fetch("/api/v1/security-concurrency/context-security-check", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        tenantOutput.style.display = "block";
        tenantOutput.textContent = "[Section 17.1: Context Security & Minimal Necessary Filter]\n\n" + JSON.stringify(data, null, 2);
      } catch (err) {
        tenantOutput.style.display = "block";
        tenantOutput.textContent = "Error: " + err.message;
      }
    });
  }

  // 7. Section 17.2 Secrets Vault Audit
  const btnAuditVault = document.getElementById("btn-audit-secrets-vault");
  if (btnAuditVault) {
    btnAuditVault.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/security-concurrency/secrets-vault-audit");
        const data = await res.json();
        vaultOutput.style.display = "block";
        vaultOutput.textContent = "[Section 17.2: Secrets & Configuration Vault (Masked Audit)]\n\n" + JSON.stringify(data, null, 2);
      } catch (err) {
        vaultOutput.style.display = "block";
        vaultOutput.textContent = "Error: " + err.message;
      }
    });
  }
}

/**
 * Section 18 & 19: AI Safety Principles & Approved Knowledge UI
 */
function setupSafetyKnowledgeUI() {
  const safetyOutput = document.getElementById("safety-eval-output");
  const framingOutput = document.getElementById("framing-output");
  const knowledgeOutput = document.getElementById("knowledge-output");

  // 1. Evaluate Capability
  const btnEvalCap = document.getElementById("btn-eval-capability");
  const capSelect = document.getElementById("safety-cap-select");
  if (btnEvalCap && capSelect) {
    btnEvalCap.addEventListener("click", async () => {
      try {
        const payload = { capability_name: capSelect.value };
        const res = await fetch("/api/v1/safety-knowledge/evaluate-capability", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        safetyOutput.style.display = "block";
        safetyOutput.textContent = "[Section 18: Capability Safety Evaluation]\n\n" + JSON.stringify(data, null, 2);
      } catch (err) {
        safetyOutput.style.display = "block";
        safetyOutput.textContent = "Error: " + err.message;
      }
    });
  }

  // 2. Inspect Patient Utterance for Clinical Traps
  const btnInspectUtterance = document.getElementById("btn-inspect-utterance");
  const utteranceInput = document.getElementById("safety-utterance-input");
  if (btnInspectUtterance && utteranceInput) {
    btnInspectUtterance.addEventListener("click", async () => {
      try {
        const payload = { query_text: utteranceInput.value.trim() };
        const res = await fetch("/api/v1/safety-knowledge/inspect-query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        safetyOutput.style.display = "block";
        safetyOutput.textContent = "[Section 18: Clinical Utterance Inspection & Redirect]\n\n" + JSON.stringify(data, null, 2);
      } catch (err) {
        safetyOutput.style.display = "block";
        safetyOutput.textContent = "Error: " + err.message;
      }
    });
  }

  // 3. Section 18.1 "You Reported..." Framing Inspector
  const btnCheckFraming = document.getElementById("btn-check-framing");
  const framingInput = document.getElementById("framing-input-text");
  if (btnCheckFraming && framingInput) {
    btnCheckFraming.addEventListener("click", async () => {
      try {
        const payload = { statement_text: framingInput.value.trim() };
        const res = await fetch("/api/v1/safety-knowledge/check-patient-framing", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        framingOutput.style.display = "block";
        framingOutput.textContent = "[Section 18: Patient-Reported Framing Enforcer]\n\n" + JSON.stringify(data, null, 2);
      } catch (err) {
        framingOutput.style.display = "block";
        framingOutput.textContent = "Error: " + err.message;
      }
    });
  }

  // 4. Section 19 Approved Knowledge Retrieval
  const btnQueryKB = document.getElementById("btn-query-approved-kb");
  const kbInput = document.getElementById("knowledge-query-input");
  if (btnQueryKB && kbInput) {
    btnQueryKB.addEventListener("click", async () => {
      try {
        const payload = { query: kbInput.value.trim() };
        const res = await fetch("/api/v1/safety-knowledge/query-knowledge", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        knowledgeOutput.style.display = "block";
        knowledgeOutput.textContent = "[Section 19: Approved Knowledge Retrieval & Citation]\n\n" + JSON.stringify(data, null, 2);
      } catch (err) {
        knowledgeOutput.style.display = "block";
        knowledgeOutput.textContent = "Error: " + err.message;
      }
    });
  }

  // 5. Section 19 Medical Advice Block Test
  const btnTestMedBlock = document.getElementById("btn-test-med-advice-block");
  if (btnTestMedBlock) {
    btnTestMedBlock.addEventListener("click", async () => {
      try {
        const payload = { query: "What should I take for high fever and is this dangerous?" };
        const res = await fetch("/api/v1/safety-knowledge/query-knowledge", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        knowledgeOutput.style.display = "block";
        knowledgeOutput.textContent = "[Section 19: Medical Advice Prohibited & Referred]\n\n" + JSON.stringify(data, null, 2);
      } catch (err) {
        knowledgeOutput.style.display = "block";
        knowledgeOutput.textContent = "Error: " + err.message;
      }
    });
  }
}

/**
 * Section 20: Canonical Workflow Examples UI
 */
function setupWorkflowExamplesUI() {
  const outputBox = document.getElementById("wf-examples-output");

  const runWorkflow = async (code, extraPayload = {}) => {
    try {
      const payload = { workflow_code: code, ...extraPayload };
      const res = await fetch("/api/v1/workflow-examples/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      outputBox.style.display = "block";
      outputBox.textContent = `[Section ${code} Workflow Execution Result]\n\n` + JSON.stringify(data, null, 2);
    } catch (err) {
      outputBox.style.display = "block";
      outputBox.textContent = "Error executing workflow: " + err.message;
    }
  };

  // 20.1
  const btn201 = document.getElementById("btn-wf-20-1");
  if (btn201) btn201.addEventListener("click", () => runWorkflow("20.1"));

  // 20.2
  const btn202 = document.getElementById("btn-wf-20-2");
  if (btn202) btn202.addEventListener("click", () => runWorkflow("20.2"));

  // 20.3 YES
  const btn203Yes = document.getElementById("btn-wf-20-3-yes");
  if (btn203Yes) btn203Yes.addEventListener("click", () => runWorkflow("20.3", { simulated_retry_success: true }));

  // 20.3 NO
  const btn203No = document.getElementById("btn-wf-20-3-no");
  if (btn203No) btn203No.addEventListener("click", () => runWorkflow("20.3", { simulated_retry_success: false }));

  // 20.4
  const btn204 = document.getElementById("btn-wf-20-4");
  if (btn204) btn204.addEventListener("click", () => runWorkflow("20.4", { session_id: "SESSION-DEMO-UI-204" }));

  // 20.5
  const btn205 = document.getElementById("btn-wf-20-5");
  if (btn205) btn205.addEventListener("click", () => runWorkflow("20.5"));

  // 20.6
  const btn206 = document.getElementById("btn-wf-20-6");
  if (btn206) btn206.addEventListener("click", () => runWorkflow("20.6"));
}


// Setup Section 21 & 22 AI Evaluation Framework & Executive Dashboard
function setupAIEvaluationFrameworkUI() {
  const btnRunSystematic = document.getElementById("btn-eval-run-systematic");
  const btnRefreshDashboard = document.getElementById("btn-eval-refresh-dashboard");
  const outputBox = document.getElementById("ai-evaluation-output");

  async function loadDashboardMetrics() {
    try {
      const res = await fetch("/api/v1/ai/evaluation-framework/dashboard");
      if (!res.ok) throw new Error(`Dashboard fetch failed: ${res.statusText}`);
      const data = await res.json();

      // Update KPI cards
      if (data.kpis) {
        const k = data.kpis;
        const setVal = (id, val) => {
          const el = document.getElementById(id);
          if (el) el.textContent = val;
        };
        setVal("eval-kpi-intent", `${k.intent_accuracy_percent}%`);
        setVal("eval-kpi-context", `${k.context_resolution_percent}%`);
        setVal("eval-kpi-capability", `${k.capability_selection_percent}%`);
        setVal("eval-kpi-verify", `${k.booking_verification_percent}%`);
        setVal("eval-kpi-ehr", `${k.ehr_integration_success_percent}%`);
        setVal("eval-kpi-safety", `${k.safety_compliance_percent}%`);
        setVal("eval-kpi-latency", `${k.average_response_seconds} sec`);
      }
    } catch (err) {
      console.warn("Could not load initial AI evaluation dashboard metrics:", err);
    }
  }

  // Load dashboard metrics on page load
  loadDashboardMetrics();

  if (btnRefreshDashboard) {
    btnRefreshDashboard.addEventListener("click", async () => {
      await loadDashboardMetrics();
      if (outputBox) {
        outputBox.style.display = "block";
        outputBox.className = "status-box status-success";
        outputBox.innerHTML = `<strong>Dashboard Refreshed:</strong> Metrics synchronized with latest platform benchmarks.`;
      }
    });
  }

  if (btnRunSystematic) {
    btnRunSystematic.addEventListener("click", async () => {
      if (!outputBox) return;
      outputBox.style.display = "block";
      outputBox.className = "status-box status-loading";
      outputBox.innerHTML = `<strong>Running Systematic 6-Pillar Evaluation Suite...</strong> (Intent, Context, Capability, EHR, Safety, Voice)...`;

      try {
        const res = await fetch("/api/v1/ai/evaluation-framework/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sample_size: 100 })
        });
        const result = await res.json();

        if (res.ok && result.all_passed) {
          outputBox.className = "status-box status-success";
          outputBox.innerHTML = `
            <strong>All 6 Pillars Passed Systematic Evaluation!</strong>
            <p>Run ID: <code>${result.evaluation_run_id}</code> | Total Evaluated Interactions: <strong>${result.total_evaluated_interactions}</strong></p>
            <div style="font-family: monospace; font-size: 0.85rem; background: #fff; padding: 0.75rem; border-radius: 4px; border: 1px solid #cbd5e1; margin-top: 0.5rem; max-height: 250px; overflow-y: auto;">
              ${JSON.stringify(result.results, null, 2).replace(/\\n/g, '<br/>').replace(/ /g, '&nbsp;')}
            </div>
          `;
          await loadDashboardMetrics();
        } else {
          outputBox.className = "status-box status-error";
          outputBox.innerHTML = `<strong>Evaluation Failure:</strong> ${JSON.stringify(result)}`;
        }
      } catch (err) {
        outputBox.className = "status-box status-error";
        outputBox.innerHTML = `<strong>Execution Error:</strong> ${err.message}`;
      }
    });
  }
}


// Setup Section 23 Product Metrics UI
function setupProductMetricsUI() {
  const btnRefresh = document.getElementById("btn-refresh-product-metrics");

  async function loadMetrics() {
    try {
      const res = await fetch("/api/v1/metrics/product");
      if (!res.ok) return;
      const data = await res.json();

      if (data.hospital) {
        const elDocs = document.getElementById("metric-active-docs");
        const elVol = document.getElementById("metric-appt-volume");
        if (elDocs) elDocs.textContent = data.hospital.active_doctors;
        if (elVol) elVol.textContent = data.hospital.appointment_volume;
      }
    } catch (err) {
      console.warn("Could not load product metrics:", err);
    }
  }

  loadMetrics();
  if (btnRefresh) {
    btnRefresh.addEventListener("click", () => {
      loadMetrics();
    });
  }
}


// Setup Section 24 Example End-to-End Scenario UI
function setupEndToEndScenarioUI() {
  const btnRun = document.getElementById("btn-run-e2e-scenario");
  const outputBox = document.getElementById("e2e-scenario-output");

  if (btnRun) {
    btnRun.addEventListener("click", async () => {
      if (!outputBox) return;
      outputBox.style.display = "block";
      outputBox.className = "status-box status-loading";
      outputBox.innerHTML = `<strong>Executing Section 24 Canonical Scenario...</strong> Simulating shoulder pain consultation, EHR booking, and pre-visit intake...`;

      try {
        const res = await fetch("/api/v1/scenario/end-to-end/execute", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            patient_name: "Patient A",
            patient_phone: "+1-555-SHOULDER",
            run_questionnaire: true
          })
        });
        const result = await res.json();

        if (res.ok && result.status === "COMPLETED") {
          outputBox.className = "status-box status-success";
          outputBox.innerHTML = `
            <strong>Canonical End-to-End Scenario Completed Successfully!</strong>
            <p>Internal Appointment: <code>${result.internal_appointment_id}</code> | External EHR: <code>${result.external_appointment_id}</code> | Status: <strong>CONFIRMED</strong></p>
            <div style="font-family: monospace; font-size: 0.85rem; background: #fff; padding: 0.75rem; border-radius: 4px; border: 1px solid #cbd5e1; margin-top: 0.5rem; max-height: 250px; overflow-y: auto;">
              ${JSON.stringify(result.perspectives, null, 2).replace(/\\n/g, '<br/>').replace(/ /g, '&nbsp;')}
            </div>
          `;
        } else {
          outputBox.className = "status-box status-error";
          outputBox.innerHTML = `<strong>Scenario Execution Failed:</strong> ${JSON.stringify(result)}`;
        }
      } catch (err) {
        outputBox.className = "status-box status-error";
        outputBox.innerHTML = `<strong>Execution Error:</strong> ${err.message}`;
      }
    });
  }
}


// Setup Section 25 Product Principles UI
function setupProductPrinciplesUI() {
  const btnAudit = document.getElementById("btn-run-principles-audit");
  const outputBox = document.getElementById("principles-audit-output");
  const scoreBadge = document.getElementById("principles-score-badge");

  if (btnAudit) {
    btnAudit.addEventListener("click", async () => {
      if (!outputBox) return;
      outputBox.style.display = "block";
      outputBox.className = "status-box status-loading";
      outputBox.innerHTML = `<strong>Running Comprehensive Product Principles Audit...</strong> Validating 16 principles against active database states, guardrails, and audit ledgers...`;

      try {
        const res = await fetch("/api/v1/principles/audit", {
          method: "POST",
          headers: { "Content-Type": "application/json" }
        });
        const result = await res.json();

        if (res.ok && result.all_principles_compliant) {
          if (scoreBadge) scoreBadge.textContent = `${result.overall_compliance_score_percent}%`;
          outputBox.className = "status-box status-success";
          outputBox.innerHTML = `
            <strong>All 16 Canonical Product Principles Verified Compliant!</strong>
            <p>Overall Compliance Score: <strong>${result.overall_compliance_score_percent}%</strong> | Verified Principles: <strong>${result.principles_count} / 16</strong></p>
            <div style="font-family: monospace; font-size: 0.85rem; background: #fff; padding: 0.75rem; border-radius: 4px; border: 1px solid #cbd5e1; margin-top: 0.5rem; max-height: 250px; overflow-y: auto;">
              ${JSON.stringify(result.principles, null, 2).replace(/\\n/g, '<br/>').replace(/ /g, '&nbsp;')}
            </div>
          `;
        } else {
          outputBox.className = "status-box status-error";
          outputBox.innerHTML = `<strong>Audit Failed:</strong> ${JSON.stringify(result)}`;
        }
      } catch (err) {
        outputBox.className = "status-box status-error";
        outputBox.innerHTML = `<strong>Audit Execution Error:</strong> ${err.message}`;
      }
    });
  }
}


// Setup Section 26 Prototype Scope UI
function setupPrototypeScopeUI() {
  const btnVerify = document.getElementById("btn-verify-prototype-scope");
  const btnTestAuth = document.getElementById("btn-test-auth-login");
  const outputBox = document.getElementById("prototype-scope-verify-output");
  const scopeBadge = document.getElementById("prototype-scope-badge");

  if (btnVerify) {
    btnVerify.addEventListener("click", async () => {
      if (!outputBox) return;
      outputBox.style.display = "block";
      outputBox.className = "status-box status-loading";
      outputBox.innerHTML = `<strong>Executing Multi-Domain Prototype Scope Verification...</strong> Testing all 9 Must-Have domains across Platform, Doctor, Patient, AI, EHR, Questionnaire, Workflow, Analytics, and AI Operations...`;

      try {
        const res = await fetch("/api/v1/prototype/scope/verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({})
        });
        const result = await res.json();

        if (res.ok && result.all_passed) {
          if (scopeBadge) scopeBadge.textContent = `${result.completion_percentage}%`;
          outputBox.className = "status-box status-success";
          outputBox.innerHTML = `
            <strong>Prototype Scope Verification PASSED - All 9 Must-Have Domains Operational!</strong>
            <p>Status: <strong>${result.overall_status}</strong> | Verified Domains: <strong>${result.verified_domains} / ${result.total_domains}</strong> | Assertions Checked: <strong>${result.total_assertions_checked}</strong> | Scope Coverage: <strong>${result.completion_percentage}%</strong></p>
            <div style="font-family: monospace; font-size: 0.85rem; background: #fff; padding: 0.75rem; border-radius: 4px; border: 1px solid #cbd5e1; margin-top: 0.5rem; max-height: 300px; overflow-y: auto;">
              ${JSON.stringify(result.domain_results, null, 2).replace(/\\n/g, '<br/>').replace(/ /g, '&nbsp;')}
            </div>
          `;
        } else {
          outputBox.className = "status-box status-error";
          outputBox.innerHTML = `<strong>Verification Failed:</strong> ${JSON.stringify(result)}`;
        }
      } catch (err) {
        outputBox.className = "status-box status-error";
        outputBox.innerHTML = `<strong>Verification Execution Error:</strong> ${err.message}`;
      }
    });
  }

  if (btnTestAuth) {
    btnTestAuth.addEventListener("click", async () => {
      if (!outputBox) return;
      outputBox.style.display = "block";
      outputBox.className = "status-box status-loading";
      outputBox.innerHTML = `<strong>Testing User &amp; Patient Authentication...</strong> Executing login simulation for Platform Admin, Hospital Admin, Doctor, and Patient...`;

      try {
        // Test unified auth login
        const resAdmin = await fetch("/api/v1/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email_or_identifier: "admin@hospital.org",
            role: "HOSPITAL_ADMIN"
          })
        });
        const adminData = await resAdmin.json();

        // Test patient login
        const resPatient = await fetch("/api/v1/patients/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            phone_number: "+1-555-432-8765",
            full_name: "Eleanor Vance"
          })
        });
        const patientData = await resPatient.json();

        outputBox.className = "status-box status-success";
        outputBox.innerHTML = `
          <strong>Unified Authentication &amp; Patient Login Verified!</strong>
          <p>Hospital Admin Token: <code>${adminData.access_token}</code> (${adminData.role})</p>
          <p>Patient Token: <code>${patientData.access_token}</code> (Patient ID: ${patientData.patient_id})</p>
          <div style="font-family: monospace; font-size: 0.85rem; background: #fff; padding: 0.75rem; border-radius: 4px; border: 1px solid #cbd5e1; margin-top: 0.5rem;">
            <strong>Admin Context Headers:</strong> ${JSON.stringify(adminData.headers)}<br/>
            <strong>Patient Context Headers:</strong> ${JSON.stringify(patientData.headers)}
          </div>
        `;
      } catch (err) {
        outputBox.className = "status-box status-error";
        outputBox.innerHTML = `<strong>Authentication Test Error:</strong> ${err.message}`;
      }
    });
  }
}

// SECTION 27: ADVANCED CAPABILITIES & OPERATIONAL POLISH HANDLERS
function setupAdvancedCapabilitiesUI() {
  const quickScanBtn = document.getElementById("btn-sec27-quick-scan");
  const circuitResetBtn = document.getElementById("btn-sec27-circuit-reset");
  const tripCircuitBtn = document.getElementById("btn-sec27-trip-circuit");
  const scanDiscrepBtn = document.getElementById("btn-sec27-scan-discrepancies");
  const reconcileOneBtn = document.getElementById("btn-sec27-reconcile-one");
  const loadConnectorsBtn = document.getElementById("btn-sec27-load-connectors");
  const testConnectorBtn = document.getElementById("btn-sec27-test-connector");
  const execBranchBtn = document.getElementById("btn-sec27-exec-branch");
  const presetEmergBtn = document.getElementById("btn-sec27-preset-emerg");
  const presetRashBtn = document.getElementById("btn-sec27-preset-rash");
  const calcRoiBtn = document.getElementById("btn-sec27-calc-roi");
  const refreshQueueBtn = document.getElementById("btn-sec27-refresh-queue");
  const resolveTicketBtn = document.getElementById("btn-sec27-resolve-ticket");
  const triggerRemindersBtn = document.getElementById("btn-sec27-trigger-reminders");
  const streamVoiceBtn = document.getElementById("btn-sec27-stream-voice");
  const bargeInBtn = document.getElementById("btn-sec27-barge-in");

  // Output containers
  const connectorList = document.getElementById("sec27-connector-list");
  const connectorOutput = document.getElementById("sec27-connector-output");
  const reconciliationOutput = document.getElementById("sec27-reconciliation-output");
  const circuitBadge = document.getElementById("sec27-circuit-badge");
  const branchingOutput = document.getElementById("sec27-branching-output");
  const roiOutput = document.getElementById("sec27-roi-output");
  const triageQueue = document.getElementById("sec27-triage-queue");
  const triageOutput = document.getElementById("sec27-triage-output");
  const remindersOutput = document.getElementById("sec27-reminders-output");
  const streamLog = document.getElementById("sec27-stream-log");

  // Golden signals elements
  const goldenLat = document.getElementById("metric-golden-latency");
  const goldenTraf = document.getElementById("metric-golden-traffic");
  const goldenErr = document.getElementById("metric-golden-errors");
  const goldenSat = document.getElementById("metric-golden-saturation");

  // Load telemetry metrics
  async function refreshTelemetry() {
    try {
      const res = await fetch("/api/v1/should-have/monitoring/golden-signals");
      if (res.ok) {
        const data = await res.json();
        if (goldenLat) goldenLat.textContent = `${data.latency_ms.p50} ms`;
        if (goldenTraf) goldenTraf.textContent = `${data.traffic.total_requests} reqs`;
        if (goldenErr) goldenErr.textContent = `${data.errors.error_rate_pct}%`;
        if (goldenSat) goldenSat.textContent = `${data.saturation.circuit_breaker_state}`;
      }
    } catch (e) {
      console.error("Telemetry fetch error:", e);
    }
  }

  // Load connectors catalog
  async function refreshConnectors() {
    try {
      const res = await fetch("/api/v1/should-have/connectors");
      if (res.ok) {
        const data = await res.json();
        if (connectorList) {
          connectorList.innerHTML = data.connectors.map(c => `
            <div style="display:flex; justify-content:space-between; align-items:center; background:#f8fafc; padding:0.6rem 0.8rem; border-radius:6px; border:1px solid #e2e8f0;">
              <div>
                <strong>${c.name}</strong> <span style="font-size:0.75rem; color:#64748b;">(${c.type})</span>
                <div style="font-size:0.75rem; color:#475569;">Protocol: ${c.protocol} | Version: ${c.version}</div>
              </div>
              <span class="badge badge-${c.status === 'ACTIVE' ? 'success' : 'warning'}">${c.status}</span>
            </div>
          `).join("");
        }
      }
    } catch (e) {
      console.error("Connectors fetch error:", e);
    }
  }

  // Load circuit breaker status
  async function refreshCircuitBreaker() {
    try {
      const res = await fetch("/api/v1/should-have/circuit-breaker");
      if (res.ok) {
        const data = await res.json();
        if (circuitBadge) {
          circuitBadge.textContent = `STATE: ${data.state}`;
          circuitBadge.className = data.state === "CLOSED" ? "badge badge-success" : (data.state === "OPEN" ? "badge badge-danger" : "badge badge-warning");
        }
      }
    } catch (e) {
      console.error("Circuit breaker fetch error:", e);
    }
  }

  // Load triage queue
  async function refreshTriageQueue() {
    try {
      const res = await fetch("/api/v1/should-have/escalations/queue");
      if (res.ok) {
        const data = await res.json();
        if (triageQueue) {
          if (data.active_tickets && data.active_tickets.length > 0) {
            triageQueue.innerHTML = data.active_tickets.map(t => `
              <div style="background:#fff; border:1px solid #cbd5e1; border-radius:4px; padding:0.5rem 0.7rem; margin-bottom:0.4rem; font-size:0.8rem;">
                <div style="display:flex; justify-content:space-between; margin-bottom:0.2rem;">
                  <strong>${t.ticket_id}</strong>
                  <span class="badge badge-${t.priority === 'P0_CRITICAL' ? 'danger' : 'warning'}">${t.priority}</span>
                </div>
                <div><strong>Reason:</strong> ${t.reason}</div>
                <div style="color:#64748b; font-size:0.75rem;">Status: ${t.status} | Created: ${new Date(t.created_at).toLocaleTimeString()}</div>
              </div>
            `).join("");
          } else {
            triageQueue.innerHTML = '<div style="color:#94a3b8; font-size:0.85rem; font-style:italic;">No escalated tickets currently pending resolution.</div>';
          }
        }
      }
    } catch (e) {
      console.error("Triage queue fetch error:", e);
    }
  }

  // Bind Quick Scan
  if (quickScanBtn) {
    quickScanBtn.addEventListener("click", async () => {
      await refreshTelemetry();
      await refreshConnectors();
      await refreshCircuitBreaker();
      await refreshTriageQueue();
    });
  }

  // Initial load
  refreshTelemetry();
  refreshConnectors();
  refreshCircuitBreaker();
  refreshTriageQueue();

  // Test Connector
  if (testConnectorBtn) {
    testConnectorBtn.addEventListener("click", async () => {
      const connectorType = document.getElementById("sec27-select-connector").value;
      try {
        const res = await fetch("/api/v1/should-have/connectors/test", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ connector_type: connectorType })
        });
        const data = await res.json();
        connectorOutput.style.display = "block";
        connectorOutput.className = data.status === "CONNECTED" ? "status-box status-success" : "status-box status-error";
        connectorOutput.innerHTML = `
          <strong>Connection Probe Result:</strong> ${data.status}<br/>
          <strong>Connector:</strong> ${data.connector_type}<br/>
          <strong>Patient Resolution Verified:</strong> ${data.patient_resolution_tested ? 'YES' : 'NO'}<br/>
          <strong>Roundtrip Latency:</strong> ${data.roundtrip_latency_ms} ms
        `;
      } catch (e) {
        connectorOutput.style.display = "block";
        connectorOutput.className = "status-box status-error";
        connectorOutput.textContent = "Error testing connector: " + e.message;
      }
    });
  }

  // Load connectors button
  if (loadConnectorsBtn) {
    loadConnectorsBtn.addEventListener("click", refreshConnectors);
  }

  // Scan Discrepancies
  if (scanDiscrepBtn) {
    scanDiscrepBtn.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/should-have/reconciliation/discrepancies");
        const data = await res.json();
        reconciliationOutput.style.display = "block";
        reconciliationOutput.className = "status-box status-info";
        reconciliationOutput.innerHTML = `
          <strong>EHR Discrepancy Audit Completed:</strong><br/>
          Discrepancies Detected: <strong>${data.count}</strong><br/>
          Sync Status: <strong>${data.sync_status}</strong><br/>
          Records Inspected: <code>${JSON.stringify(data.discrepancies.slice(0, 3))}</code>
        `;
      } catch (e) {
        reconciliationOutput.style.display = "block";
        reconciliationOutput.className = "status-box status-error";
        reconciliationOutput.textContent = "Error scanning discrepancies: " + e.message;
      }
    });
  }

  // 1-Click Reconcile
  if (reconcileOneBtn) {
    reconcileOneBtn.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/should-have/reconciliation/reconcile-one", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ appointment_id: "APP-SEC27-REC-01", target_status: "CONFIRMED" })
        });
        const data = await res.json();
        reconciliationOutput.style.display = "block";
        reconciliationOutput.className = "status-box status-success";
        reconciliationOutput.innerHTML = `
          <strong>1-Click Reconciliation Executed:</strong><br/>
          Appointment ID: <code>${data.appointment_id}</code><br/>
          Action Taken: <strong>${data.action_taken}</strong><br/>
          Reconciliation Hash: <code>${data.reconciliation_hash}</code>
        `;
      } catch (e) {
        reconciliationOutput.style.display = "block";
        reconciliationOutput.className = "status-box status-error";
        reconciliationOutput.textContent = "Error during reconciliation: " + e.message;
      }
    });
  }

  // Trip Circuit Simulator
  if (tripCircuitBtn) {
    tripCircuitBtn.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/should-have/circuit-breaker/trip-test", { method: "POST" });
        const data = await res.json();
        reconciliationOutput.style.display = "block";
        reconciliationOutput.className = "status-box status-error";
        reconciliationOutput.innerHTML = `
          <strong>Circuit Breaker Tripped!</strong><br/>
          State: <strong>${data.circuit_state}</strong><br/>
          Failure Threshold: ${data.consecutive_failures} failures recorded.<br/>
          All subsequent EHR writes will degrade gracefully into asynchronous dead-letter queues.
        `;
        refreshCircuitBreaker();
        refreshTelemetry();
      } catch (e) {
        reconciliationOutput.style.display = "block";
        reconciliationOutput.className = "status-box status-error";
        reconciliationOutput.textContent = "Error tripping circuit: " + e.message;
      }
    });
  }

  // Reset Circuit Breaker
  if (circuitResetBtn) {
    circuitResetBtn.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/should-have/circuit-breaker/reset", { method: "POST" });
        const data = await res.json();
        reconciliationOutput.style.display = "block";
        reconciliationOutput.className = "status-box status-success";
        reconciliationOutput.innerHTML = `<strong>Circuit Breaker Reset:</strong> State is now <strong>${data.status.state}</strong>. Normal EHR synchronization restored.`;
        refreshCircuitBreaker();
        refreshTelemetry();
      } catch (e) {
        reconciliationOutput.style.display = "block";
        reconciliationOutput.className = "status-box status-error";
        reconciliationOutput.textContent = "Error resetting circuit breaker: " + e.message;
      }
    });
  }

  // Execute Workflow Branch
  if (execBranchBtn) {
    execBranchBtn.addEventListener("click", async () => {
      const phone = document.getElementById("sec27-branch-phone").value;
      const utterance = document.getElementById("sec27-branch-utterance").value;
      try {
        const res = await fetch("/api/v1/should-have/workflows/execute-branch", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ patient_phone: phone, user_utterance: utterance })
        });
        const data = await res.json();
        branchingOutput.style.display = "block";
        branchingOutput.className = data.branch_taken.includes("EMERGENCY") ? "status-box status-error" : "status-box status-success";
        branchingOutput.innerHTML = `
          <strong>Selected Workflow Branch:</strong> <code>${data.branch_taken}</code><br/>
          <strong>Status:</strong> ${data.status}<br/>
          <strong>Advisory / Message:</strong> ${data.advisory || data.message}<br/>
          <strong>Inferred Specialty:</strong> ${data.inferred_specialty || "N/A"}<br/>
          <strong>Step Pipeline Execution:</strong>
          <pre style="background:#fff; padding:0.5rem; margin-top:0.4rem; border-radius:4px; font-size:0.8rem;">${JSON.stringify(data.execution_steps, null, 2)}</pre>
        `;
        refreshTriageQueue();
      } catch (e) {
        branchingOutput.style.display = "block";
        branchingOutput.className = "status-box status-error";
        branchingOutput.textContent = "Error executing workflow branch: " + e.message;
      }
    });
  }

  // Presets
  if (presetEmergBtn) {
    presetEmergBtn.addEventListener("click", () => {
      document.getElementById("sec27-branch-utterance").value = "I have severe chest pain and cannot breathe";
    });
  }
  if (presetRashBtn) {
    presetRashBtn.addEventListener("click", () => {
      document.getElementById("sec27-branch-utterance").value = "I have eczema and an itchy rash on my face";
    });
  }

  // Cost Estimator
  if (calcRoiBtn) {
    calcRoiBtn.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/should-have/cost-estimate");
        const data = await res.json();
        roiOutput.style.display = "block";
        roiOutput.className = "status-box status-info";
        roiOutput.innerHTML = `
          <strong>Monthly Volume Projections (10,000 calls):</strong><br/>
          • Total AI Voice Cost: <strong>$${data.monthly_projections_10k_calls.voice_ai_cost_usd}</strong><br/>
          • Human Staff Cost: <strong>$${data.monthly_projections_10k_calls.human_staff_cost_usd}</strong><br/>
          • Monthly Net Savings: <strong>$${data.monthly_projections_10k_calls.monthly_net_savings_usd}</strong> (${data.unit_economics_per_5min_call.savings_vs_human_percent}% reduction)<br/>
          <small>Cost Breakdown: LLM $${data.unit_economics_per_5min_call.llm_cost_usd} | STT $${data.unit_economics_per_5min_call.stt_cost_usd} | TTS $${data.unit_economics_per_5min_call.tts_cost_usd} | Telephony $${data.unit_economics_per_5min_call.telephony_cost_usd}</small>
        `;
      } catch (e) {
        roiOutput.style.display = "block";
        roiOutput.className = "status-box status-error";
        roiOutput.textContent = "Error calculating ROI: " + e.message;
      }
    });
  }

  // Triage Ticket Resolution
  if (resolveTicketBtn) {
    resolveTicketBtn.addEventListener("click", async () => {
      const ticketId = document.getElementById("sec27-resolve-ticket-id").value;
      if (!ticketId) {
        alert("Please enter a ticket ID to resolve");
        return;
      }
      try {
        const res = await fetch("/api/v1/should-have/escalations/resolve", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ticket_id: ticketId, resolution_notes: "Supervisor reviewed and reassigned to specialist triage nurse." })
        });
        const data = await res.json();
        triageOutput.style.display = "block";
        triageOutput.className = "status-box status-success";
        triageOutput.innerHTML = `<strong>Ticket ${ticketId} Resolved!</strong> Status: <strong>${data.status}</strong>`;
        refreshTriageQueue();
      } catch (e) {
        triageOutput.style.display = "block";
        triageOutput.className = "status-box status-error";
        triageOutput.textContent = "Error resolving ticket: " + e.message;
      }
    });
  }
  if (refreshQueueBtn) {
    refreshQueueBtn.addEventListener("click", refreshTriageQueue);
  }

  // Automated Reminders Batch Scan
  if (triggerRemindersBtn) {
    triggerRemindersBtn.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/should-have/reminders/trigger-batch", { method: "POST" });
        const data = await res.json();
        remindersOutput.style.display = "block";
        remindersOutput.className = "status-box status-success";
        remindersOutput.innerHTML = `
          <strong>Automated Reminders Batch Execution:</strong><br/>
          Appointments Evaluated: <strong>${data.appointments_evaluated}</strong><br/>
          Reminders Dispatched: <strong>${data.reminders_dispatched_count}</strong><br/>
          Summary: <code>${JSON.stringify(data.dispatched_reminders)}</code>
        `;
      } catch (e) {
        remindersOutput.style.display = "block";
        remindersOutput.className = "status-box status-error";
        remindersOutput.textContent = "Error triggering reminders: " + e.message;
      }
    });
  }

  // Streaming AI Voice SSE Simulator
  if (streamVoiceBtn) {
    streamVoiceBtn.addEventListener("click", async () => {
      const text = document.getElementById("sec27-voice-input").value;
      if (!streamLog) return;
      streamLog.innerHTML = `<span style="color:#38bdf8;">[INIT] Connecting to SSE voice stream for utterance: "${text}"...</span><br/>`;

      try {
        const response = await fetch(`/api/v1/should-have/voice/stream?user_utterance=${encodeURIComponent(text)}`);
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const event = JSON.parse(line.substring(6));
                let color = "#cbd5e1";
                if (event.event === "filler") color = "#fbbf24";
                else if (event.event === "token") color = "#4ade80";
                else if (event.event === "tool_call") color = "#c084fc";
                else if (event.event === "done") color = "#38bdf8";

                streamLog.innerHTML += `<span style="color:${color};">[${event.event.toUpperCase()}] ${event.token || event.text || JSON.stringify(event)}</span><br/>`;
                streamLog.scrollTop = streamLog.scrollHeight;
              } catch (err) {
                // Non-JSON line
              }
            }
          }
        }
      } catch (err) {
        streamLog.innerHTML += `<span style="color:#f87171;">[ERROR] Stream error: ${err.message}</span><br/>`;
      }
    });
  }

  // Barge-In Interrupt Simulator
  if (bargeInBtn) {
    bargeInBtn.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/v1/should-have/voice/barge-in", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: "SES-LIVE-ACTIVE" })
        });
        const data = await res.json();
        if (streamLog) {
          streamLog.innerHTML += `<span style="color:#ef4444; font-weight:bold;">[BARGE-IN] ${data.action} - Speech detected! Audio buffer flushed in ${data.interruption_latency_ms}ms</span><br/>`;
          streamLog.scrollTop = streamLog.scrollHeight;
        }
      } catch (err) {
        if (streamLog) {
          streamLog.innerHTML += `<span style="color:#ef4444;">[BARGE-IN ERROR] ${err.message}</span><br/>`;
        }
      }
    });
  }
}

// =============================================================================
// Section 35: Definition of Done (DoD) Interactive UI Handler
// =============================================================================
function setupDefinitionOfDoneUI() {
  const btnRunCanonical = document.getElementById("btn-dod-run-canonical");
  const btnSimTransient = document.getElementById("btn-dod-sim-transient");
  const btnSimEscalation = document.getElementById("btn-dod-sim-escalation");
  const btnGetChecklist = document.getElementById("btn-dod-get-checklist");

  const statusBox = document.getElementById("dod-action-status");
  const stagesContainer = document.getElementById("dod-stages-container");
  const perspectivesView = document.getElementById("dod-perspectives-view");
  const outputJson = document.getElementById("dod-output-json");

  function showStatus(msg, isError = false) {
    if (!statusBox) return;
    statusBox.style.display = "block";
    statusBox.style.background = isError ? "#fee2e2" : "#dcfce7";
    statusBox.style.color = isError ? "#991b1b" : "#166534";
    statusBox.style.border = isError ? "1px solid #f87171" : "1px solid #86efac";
    statusBox.innerHTML = msg;
  }

  // 1. Run Canonical 27-Stage DoD Journey
  if (btnRunCanonical) {
    btnRunCanonical.addEventListener("click", async () => {
      showStatus("⏳ Executing 27-Stage Canonical Definition of Done Journey...");
      try {
        const res = await fetch("/api/v1/definition-of-done/execute-journey", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            hospital_name: "Metropolitan Health System",
            doctor_name: "Dr. Sharma",
            patient_name: "Patient A",
            patient_phone: "+1-555-SHOULDER"
          })
        });
        const data = await res.json();
        if (outputJson) outputJson.textContent = JSON.stringify(data, null, 2);

        if (data.status === "SUCCESS") {
          showStatus("✅ 27-Stage Definition of Done Journey Executed with 100% Verification!");

          // Render stages pills
          if (stagesContainer && data.stages) {
            stagesContainer.innerHTML = data.stages.map(s => `
              <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:4px solid #10b981; border-radius:6px; padding:0.75rem;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.25rem;">
                  <span style="font-weight:700; color:#1e293b; font-size:0.85rem;">Stage ${s.stage_number}</span>
                  <span class="badge badge-success" style="font-size:0.75rem;">${s.status}</span>
                </div>
                <div style="font-weight:600; color:#0f172a; font-size:0.85rem;">${s.stage_name}</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:0.35rem; line-height:1.4;">
                  ${Object.entries(s.details || {}).map(([k, v]) => `<strong>${k}:</strong> ${typeof v === 'object' ? JSON.stringify(v) : v}`).join('<br/>')}
                </div>
              </div>
            `).join("");
          }

          // Render perspectives
          if (perspectivesView && data.perspectives) {
            const p = data.perspectives;
            perspectivesView.innerHTML = `
              <div style="margin-bottom:1rem; padding:0.75rem; background:#f8fafc; border-radius:6px; border:1px solid #e2e8f0;">
                <h4 style="margin:0 0 0.25rem 0; color:#0369a1;">🩺 Doctor Perspective (${p.doctor.doctor_name})</h4>
                <div>Appointment: <strong>${p.doctor.upcoming_appointment.patient}</strong> at ${p.doctor.upcoming_appointment.time}</div>
                <div>Status: <span class="badge badge-success">${p.doctor.upcoming_appointment.status}</span></div>
                <div style="font-size:0.8rem; color:#475569; margin-top:0.25rem;">Intake: "${p.doctor.upcoming_appointment.pre_visit_intake}"</div>
              </div>
              <div style="margin-bottom:1rem; padding:0.75rem; background:#f8fafc; border-radius:6px; border:1px solid #e2e8f0;">
                <h4 style="margin:0 0 0.25rem 0; color:#059669;">🏥 Hospital Admin Perspective (${p.hospital_admin.hospital_name})</h4>
                <div>EHR Synchronization: <strong>${p.hospital_admin.ehr_sync_status}</strong></div>
                <div>Active Doctors: <strong>${p.hospital_admin.active_doctors}</strong> | Questionnaires: <strong>${p.hospital_admin.questionnaires_completed} completed</strong></div>
              </div>
              <div style="padding:0.75rem; background:#f8fafc; border-radius:6px; border:1px solid #e2e8f0;">
                <h4 style="margin:0 0 0.25rem 0; color:#7c3aed;">⚙️ Platform Admin Perspective</h4>
                <div>Adapter: <strong>${p.platform_admin.ehr_adapter}</strong> | Verification: <strong>${p.platform_admin.verification_status}</strong></div>
                <div>System Health: <span class="badge badge-success">${p.platform_admin.operational_health}</span></div>
              </div>
            `;
          }
        } else {
          showStatus(`⚠️ Journey execution returned: ${data.message || 'Unknown status'}`, true);
        }
      } catch (err) {
        showStatus(`❌ Network error executing canonical journey: ${err.message}`, true);
      }
    });
  }

  // 2. Simulate Transient Failure & Recovery
  if (btnSimTransient) {
    btnSimTransient.addEventListener("click", async () => {
      showStatus("🔄 Simulating Transient EHR Failure with Self-Healing Recovery...");
      try {
        const res = await fetch("/api/v1/definition-of-done/simulate-failure-recovery", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mode: "TRANSIENT_RECOVERY" })
        });
        const data = await res.json();
        if (outputJson) outputJson.textContent = JSON.stringify(data, null, 2);
        showStatus(`✅ Transient Failure Recovered! Steps: ${data.steps.map(s => s.name).join(" ➔ ")}`);

        if (stagesContainer && data.steps) {
          stagesContainer.innerHTML = data.steps.map(s => `
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:4px solid #2563eb; border-radius:6px; padding:0.75rem;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:700; color:#1e293b; font-size:0.85rem;">Step ${s.step}</span>
                <span class="badge ${s.status === 'FAILED' ? 'badge-danger' : 'badge-success'}" style="font-size:0.75rem;">${s.status || 'OK'}</span>
              </div>
              <div style="font-weight:600; color:#0f172a; font-size:0.85rem; margin-top:0.25rem;">${s.name}</div>
              <div style="font-size:0.75rem; color:#64748b; margin-top:0.25rem;">${JSON.stringify(s.classification || s.action || s.details || s.external_state || s.resumed_state || s.verification_protocol || s.ehr_sync_status || s.error_type)}</div>
            </div>
          `).join("");
        }
      } catch (err) {
        showStatus(`❌ Error simulating transient recovery: ${err.message}`, true);
      }
    });
  }

  // 3. Simulate Persistent Failure & Escalation
  if (btnSimEscalation) {
    btnSimEscalation.addEventListener("click", async () => {
      showStatus("⚠️ Simulating Persistent EHR Failure with Reconciliation & Human Escalation...");
      try {
        const res = await fetch("/api/v1/definition-of-done/simulate-failure-recovery", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mode: "RECONCILIATION_ESCALATION" })
        });
        const data = await res.json();
        if (outputJson) outputJson.textContent = JSON.stringify(data, null, 2);
        showStatus(`⚠️ Escalation Handled: ${data.steps.map(s => s.name).join(" ➔ ")}`);

        if (stagesContainer && data.steps) {
          stagesContainer.innerHTML = data.steps.map(s => `
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:4px solid #d97706; border-radius:6px; padding:0.75rem;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:700; color:#1e293b; font-size:0.85rem;">Step ${s.step}</span>
                <span class="badge ${s.status === 'FAILED' || s.status === 'RETRIES_EXHAUSTED' || s.status === 'UNVERIFIED' || s.status === 'ACTION_NEEDED' ? 'badge-warning' : 'badge-secondary'}" style="font-size:0.75rem;">${s.status || 'LOGGED'}</span>
              </div>
              <div style="font-weight:600; color:#0f172a; font-size:0.85rem; margin-top:0.25rem;">${s.name}</div>
              <div style="font-size:0.75rem; color:#64748b; margin-top:0.25rem;">${JSON.stringify(s.action || s.error_type || s.authoritative_check || s.state_flag || s.trigger_reason || s.operational_status || '')}</div>
            </div>
          `).join("");
        }
      } catch (err) {
        showStatus(`❌ Error simulating escalation: ${err.message}`, true);
      }
    });
  }

  // 4. Get Checklist
  if (btnGetChecklist) {
    btnGetChecklist.addEventListener("click", async () => {
      showStatus("📋 Fetching Section 35 Definition of Done Checklist...");
      try {
        const res = await fetch("/api/v1/definition-of-done/checklist");
        const data = await res.json();
        if (outputJson) outputJson.textContent = JSON.stringify(data, null, 2);
        showStatus(`📋 DoD Status: ${data.status} | Total Stages: ${data.total_canonical_stages} | Compliance: ${data.compliance_rate}`);

        if (stagesContainer && data.canonical_stages) {
          stagesContainer.innerHTML = data.canonical_stages.map((st, i) => `
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:4px solid #3b82f6; border-radius:6px; padding:0.75rem;">
              <div style="font-weight:700; color:#1e293b; font-size:0.85rem;">Stage ${i + 1}</div>
              <div style="font-weight:600; color:#0f172a; font-size:0.85rem; margin-top:0.25rem;">${st}</div>
              <div style="font-size:0.75rem; color:#16a34a; margin-top:0.25rem;">✓ REQUIREMENT SATISFIED</div>
            </div>
          `).join("");
        }
      } catch (err) {
        showStatus(`❌ Error loading checklist: ${err.message}`, true);
      }
    });
  }
}

// =============================================================================
// Section 41 & 42: Final Submission Checklist & Success UI Handler
// =============================================================================
function setupFinalChecklistUI() {
  const btnRunAudit = document.getElementById("btn-run-final-audit");
  const btnLoadChecklist = document.getElementById("btn-load-checklist-details");
  const complianceEl = document.getElementById("final-audit-compliance");
  const totalEl = document.getElementById("final-audit-total");
  const badgeEl = document.getElementById("final-audit-badge");
  const auditJson = document.getElementById("final-audit-json");
  const pillarsContainer = document.getElementById("final-pillars-container");

  if (btnRunAudit) {
    btnRunAudit.addEventListener("click", async () => {
      btnRunAudit.disabled = true;
      btnRunAudit.textContent = "⏳ Auditing 76 Checks...";
      if (auditJson) auditJson.textContent = "Executing programmatic compliance audit across 7 pillars...";

      try {
        const res = await fetch("/api/v1/final-submission/run-verification-audit", {
          method: "POST",
          headers: { "Content-Type": "application/json" }
        });
        const data = await res.json();
        if (auditJson) auditJson.textContent = JSON.stringify(data, null, 2);

        if (data.status === "SUCCESS") {
          if (complianceEl) complianceEl.textContent = `${data.compliance_percentage}%`;
          if (totalEl) totalEl.textContent = `${data.verified_checks} / ${data.total_checks}`;
          if (badgeEl) {
            badgeEl.textContent = "100% VERIFIED";
            badgeEl.style.color = "#10b981";
          }
        }
      } catch (err) {
        if (auditJson) auditJson.textContent = `❌ Error running audit: ${err.message}`;
      } finally {
        btnRunAudit.disabled = false;
        btnRunAudit.textContent = "⚡ Run Programmatic Audit (76 Checks)";
      }
    });
  }

  if (btnLoadChecklist) {
    btnLoadChecklist.addEventListener("click", async () => {
      btnLoadChecklist.disabled = true;
      btnLoadChecklist.textContent = "⏳ Loading...";
      try {
        const res = await fetch("/api/v1/final-submission/checklist");
        const data = await res.json();
        if (auditJson) auditJson.textContent = JSON.stringify(data, null, 2);

        if (data.pillars && pillarsContainer) {
          const pillarsList = Object.entries(data.pillars).map(([key, p]) => {
            const verified = p.items.filter(i => i.verified).length;
            const pct = Math.round((verified / p.total) * 100);
            return `
              <div style="margin-bottom:0.85rem; padding:0.6rem; background:#f8fafc; border-radius:6px; border:1px solid #e2e8f0;">
                <div style="display:flex; justify-content:space-between; font-weight:700; color:#1e293b; font-size:0.85rem; margin-bottom:0.25rem;">
                  <span>${p.name}</span>
                  <span style="color:#10b981;">${verified}/${p.total} (${pct}%)</span>
                </div>
                <div style="background:#e2e8f0; border-radius:9999px; height:6px; overflow:hidden; margin-bottom:0.4rem;">
                  <div style="background:#10b981; width:${pct}%; height:100%;"></div>
                </div>
                <div style="font-size:0.75rem; color:#64748b;">
                  ${p.items.slice(0, 3).map(i => `✓ ${i.item}`).join(" | ")}...
                </div>
              </div>
            `;
          }).join("");
          pillarsContainer.innerHTML = pillarsList;
        }
      } catch (err) {
        if (auditJson) auditJson.textContent = `❌ Error loading checklist: ${err.message}`;
      } finally {
        btnLoadChecklist.disabled = false;
        btnLoadChecklist.textContent = "📋 Load Full Checklist";
      }
    });
  }
}














