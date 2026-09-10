// Clean ES6 JavaScript Application Logic for Healthcare Platform Frontend

document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupOnboardingForms();
  setupDoctorForms();
  setupPatientForms();
  setupVoiceConsole();
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


