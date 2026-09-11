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








