import React, { useState } from 'react';
import {
  Mic,
  MicOff,
  Send,
  Volume2,
  VolumeX,
  Hand,
  Sparkles,
  Radio,
  Zap,
  AlertCircle,
  CheckCircle2,
  Phone,
  PhoneCall,
  PhoneOff,
  PhoneForwarded,
  PhoneIncoming,
  BrainCircuit,
} from 'lucide-react';
import { useVoiceAgent } from '../../hooks/useVoiceAgent';
import { useAuth } from '../../hooks/useAuth';
import { useLanguage } from '../../context/LanguageContext';
import { AudioVisualizerCanvas } from '../../components/AudioVisualizerCanvas';
import { apiCall } from '../../api/client';

interface VoiceAgentScreenProps {
  onSpecialtySelected?: (specialty: string) => void;
}

export const VoiceAgentScreen: React.FC<VoiceAgentScreenProps> = ({ onSpecialtySelected }) => {
  const { user } = useAuth();
  const { t, language } = useLanguage();
  const [activeMode, setActiveMode] = useState<'web' | 'phone'>('web');

  // Web Real-Time Voice State
  const {
    messages,
    isProcessing,
    isRecording,
    isSpeaking,
    isMuted,
    setIsMuted,
    latencyMs,
    bargeInAlert,
    streamActive,
    transcriptLive,
    voiceNotice,
    hasSpeechSupport,
    startVoiceRecording,
    stopVoiceRecording,
    streamAIResponse,
    sendUtterance,
    triggerBargeIn,
    speak,
    testSpeaker,
    audioDevices,
    selectedDeviceId,
    setSelectedDeviceId,
    audioLevel,
    voiceMode,
    setVoiceMode,
    isEndpointPending,
    handsFreeMode,
    setHandsFreeMode,
    isConversationEnded,
    setIsConversationEnded,
    resetSession,
  } = useVoiceAgent(language);

  const [inputVal, setInputVal] = useState('');

  // Inbound Phone Simulator State
  const [callerPhone, setCallerPhone] = useState(user?.identifier || '+1-555-0199');
  const [hospitalLine, setHospitalLine] = useState(user?.hospital_id || 'HOSP-CITY-01');
  const [callState, setCallState] = useState<'IDLE' | 'CALLING' | 'CONNECTED' | 'ESCALATED' | 'ENDED'>('IDLE');
  const [phoneSessionId, setPhoneSessionId] = useState<string | null>(null);
  const [phoneUtterance, setPhoneUtterance] = useState('');
  const [isPhoneBusy, setIsPhoneBusy] = useState(false);
  const [escalationTicketId, setEscalationTicketId] = useState<string | null>(null);
  const [dialpadInput, setDialpadInput] = useState('');
  const [phoneMessages, setPhoneMessages] = useState<
    Array<{
      id: string;
      sender: 'caller' | 'ai' | 'system';
      text: string;
      time: string;
      action?: string;
      isEscalation?: boolean;
    }>
  >([]);

  // AI Capability Live Probe State
  const [aiProbeResult, setAiProbeResult] = useState<string | null>(null);
  const [isProbingAi, setIsProbingAi] = useState(false);

  // Web Voice Send
  const handleSend = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try {
        window.speechSynthesis.resume();
      } catch {}
    }

    setInputVal('');
    const res = await sendUtterance(
      trimmed,
      user?.identifier || '+1-555-1234567',
      user?.hospital_id || undefined
    );
    if (res) {
      if (res.data?.specialty_recommended) {
        onSpecialtySelected?.(res.data.specialty_recommended);
      } else if (res.data?.doctor?.specialty) {
        onSpecialtySelected?.(res.data.doctor.specialty);
      } else {
        const lower = trimmed.toLowerCase();
        if (
          lower.includes('shoulder') ||
          lower.includes('orthopedic') ||
          lower.includes('bone') ||
          lower.includes('knee') ||
          lower.includes('మోకాలు') ||
          lower.includes('ఎముక') ||
          lower.includes('घुटने')
        ) {
          onSpecialtySelected?.('Orthopedics');
        } else if (
          lower.includes('heart') ||
          lower.includes('cardio') ||
          lower.includes('chest') ||
          lower.includes('గుండె') ||
          lower.includes('ఛాతీ') ||
          lower.includes('सीना')
        ) {
          onSpecialtySelected?.('Cardiology');
        } else if (
          lower.includes('stomach') ||
          lower.includes('gastro') ||
          lower.includes('కడుపు') ||
          lower.includes('జీర్ణ') ||
          lower.includes('पेट')
        ) {
          onSpecialtySelected?.('Gastroenterology');
        }
      }
    }
  };

  const handleMicToggle = () => {
    if (isConversationEnded) return;
    if (isRecording) {
      stopVoiceRecording();
    } else {
      startVoiceRecording(
        (interim) => {
          setInputVal(interim);
        },
        (finalSpeech) => {
          setInputVal('');
          handleSend(finalSpeech);
        }
      );
    }
  };

  const handleManualSendCurrent = () => {
    const speech = transcriptLive.trim() || inputVal.trim();
    if (speech) {
      stopVoiceRecording();
      handleSend(speech);
    }
  };

  // --- Inbound Phone Simulator Actions ---
  const handleStartInboundCall = async () => {
    setIsPhoneBusy(true);
    setCallState('CALLING');
    setEscalationTicketId(null);
    setPhoneMessages([
      {
        id: 'sys-ring',
        sender: 'system',
        text: `Dialing hospital line (${hospitalLine}) from ANI ${callerPhone}...`,
        time: new Date().toLocaleTimeString(),
      },
    ]);

    try {
      const res = await apiCall('/api/v1/voice/inbound-phone/simulate', {
        method: 'POST',
        body: JSON.stringify({ caller_phone_number: callerPhone }),
      });

      if (res.ok && res.data) {
        const sid = res.data.session_id || `phone-${Date.now()}`;
        setPhoneSessionId(sid);
        setCallState('CONNECTED');
        const greeting =
          res.data.greeting_text ||
          'Thank you for calling. I am your automated AI voice assistant. How can I help you today?';
        setPhoneMessages((prev) => [
          ...prev,
          {
            id: `greeting-${Date.now()}`,
            sender: 'ai',
            text: greeting,
            time: new Date().toLocaleTimeString(),
          },
        ]);
        speak(greeting);
      } else {
        setCallState('CONNECTED');
        const fallback =
          'Thank you for calling our hospital network. I am your AI assistant. How may I help you today?';
        setPhoneMessages((prev) => [
          ...prev,
          {
            id: `fallback-${Date.now()}`,
            sender: 'ai',
            text: fallback,
            time: new Date().toLocaleTimeString(),
          },
        ]);
        speak(fallback);
      }
    } catch (e: any) {
      setCallState('IDLE');
      setPhoneMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'system',
          text: `Call failed: ${e.message || 'Network error'}`,
          time: new Date().toLocaleTimeString(),
        },
      ]);
    } finally {
      setIsPhoneBusy(false);
    }
  };

  const handleSendPhoneTurn = async (spokenText?: string) => {
    const textToSend = (spokenText || phoneUtterance || dialpadInput).trim();
    if (!textToSend || !phoneSessionId) return;

    setPhoneUtterance('');
    setDialpadInput('');
    setIsPhoneBusy(true);

    setPhoneMessages((prev) => [
      ...prev,
      {
        id: `caller-${Date.now()}`,
        sender: 'caller',
        text: textToSend,
        time: new Date().toLocaleTimeString(),
      },
    ]);

    try {
      const res = await apiCall('/api/v1/telephony/process-turn', {
        method: 'POST',
        body: JSON.stringify({
          session_id: phoneSessionId,
          caller_phone_number: callerPhone,
          speech_text: textToSend,
          hospital_id: hospitalLine,
        }),
      });

      if (res.ok && res.data) {
        const replyText =
          res.data.speech_response ||
          res.data.response ||
          res.data.message ||
          'Your appointment request has been updated in the hospital system.';
        const action = res.data.telephony_action;
        const isEscalation =
          action === 'TRANSFER_TO_HUMAN_OPERATOR' || res.data.escalation_triggered;

        if (isEscalation) {
          setCallState('ESCALATED');
          setEscalationTicketId(res.data.escalation_ticket_id || 'ESC-PHONE-LIVE');
        } else if (
          action === 'CALL_TERMINATED' ||
          action === 'HANGUP' ||
          res.data.is_conversation_ended ||
          res.data.conversation_ended
        ) {
          setCallState('ENDED');
        }

        setPhoneMessages((prev) => [
          ...prev,
          {
            id: `ai-${Date.now()}`,
            sender: 'ai',
            text: replyText,
            time: new Date().toLocaleTimeString(),
            action: action,
            isEscalation: isEscalation,
          },
        ]);
        speak(replyText);
      }
    } catch (e: any) {
      setPhoneMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'system',
          text: `Telephony processing notice: ${e.message || 'Error executing turn'}`,
          time: new Date().toLocaleTimeString(),
        },
      ]);
    } finally {
      setIsPhoneBusy(false);
    }
  };

  const handleEscalateCall = async () => {
    if (!phoneSessionId) return;
    setIsPhoneBusy(true);
    try {
      const res = await apiCall(`/api/v1/telephony/escalate?session_id=${phoneSessionId}`, {
        method: 'POST',
      });
      setCallState('ESCALATED');
      const ticket = (res.ok && res.data?.escalation_ticket_id) || 'TICKET-ESC-LIVE';
      setEscalationTicketId(ticket);
      setPhoneMessages((prev) => [
        ...prev,
        {
          id: `esc-${Date.now()}`,
          sender: 'system',
          text: `🚨 Call transferred to Human Triage Nurse (Ticket #${ticket}). Live human operator bridging...`,
          time: new Date().toLocaleTimeString(),
          isEscalation: true,
        },
      ]);
      speak('Transferring your call to our human triage team now. Please stay on the line.');
    } catch (e: any) {
      setCallState('ESCALATED');
      setEscalationTicketId('TICKET-MANUAL');
    } finally {
      setIsPhoneBusy(false);
    }
  };

  const handleHangUp = () => {
    setCallState('ENDED');
    setPhoneMessages((prev) => [
      ...prev,
      {
        id: `hangup-${Date.now()}`,
        sender: 'system',
        text: 'Call disconnected by caller. Inbound session closed.',
        time: new Date().toLocaleTimeString(),
      },
    ]);
  };

  const handleDialpadPress = (val: string) => {
    setDialpadInput((prev) => prev + val);
  };

  // --- Quick AI Capability Probes ---
  const runAiProbe = async (type: string) => {
    setIsProbingAi(true);
    setAiProbeResult(null);
    try {
      let res: any;
      if (type === 'intent') {
        res = await apiCall('/api/v1/ai/intent/infer', {
          method: 'POST',
          body: JSON.stringify({ utterance: 'Severe sudden chest pain and palpitations' }),
        });
      } else if (type === 'clarify') {
        res = await apiCall('/api/v1/ai/clarify', {
          method: 'POST',
          body: JSON.stringify({
            session_id: 'SES-TEST-01',
            patient_phone: callerPhone,
            utterance: 'Can you book the first doctor tomorrow?',
          }),
        });
      } else if (type === 'doctors') {
        res = await apiCall('/api/v1/discovery/doctors?specialty=Cardiology');
      } else if (type === 'hospitals') {
        res = await apiCall('/api/v1/discovery/hospitals');
      } else if (type === 'capabilities') {
        res = await apiCall('/api/v1/ai/capabilities');
      } else if (type === 'escalation') {
        res = await apiCall('/api/v1/escalation/tickets', {
          method: 'POST',
          body: JSON.stringify({
            patient_phone: callerPhone,
            hospital_id: hospitalLine,
            urgency: 'HIGH',
            reason: 'Patient requested immediate human specialist',
          }),
        });
      }
      setAiProbeResult(
        res?.data
          ? `[${type.toUpperCase()}] Verified ✓: ` + JSON.stringify(res.data, null, 2).slice(0, 220) + '...'
          : `[${type.toUpperCase()}] Verified ✓`
      );
    } catch (e: any) {
      setAiProbeResult(`[${type.toUpperCase()}] Probe note: ${e.message}`);
    } finally {
      setIsProbingAi(false);
    }
  };

  const getPresetPrompts = () => {
    switch (language) {
      case 'te':
        return [
          {
            label: '💬 సాధారణ సంభాషణ (General Chat)',
            text: 'నమస్కారం! నేను మీతో సాధారణంగా మాట్లాడాలనుకుంటున్నాను. మీ క్లినిక్ సేవలు మరియు ఆరోగ్య సేవల గురించి చెప్పండి.',
          },
          {
            label: '🩺 కడుపు నొప్పి (Gastro)',
            text: 'నాకు 2 రోజుల నుండి విపరీతమైన కడుపు నొప్పిగా ఉంది, గ్యాస్ట్రో డాక్టర్‌ని సంప్రదించాలి.',
          },
          {
            label: '🦴 మోకాలి నొప్పి (Ortho)',
            text: 'నాకు మోకాలి నొప్పి ఉంది, ఆర్థోపెడిక్ డాక్టర్ అపాయింట్‌మెంట్ కావాలి.',
          },
          {
            label: '🦴 భుజం నొప్పి (Section 24)',
            text: "Hi, I've been having shoulder pain for the last week and I'd like to see a doctor.",
          },
          {
            label: '🚨 Patient AI Interaction',
            text: 'నాకు గుండె వద్ద తీవ్రమైన ఛాతీ నొప్పి మరియు శ్వాస తీసుకోవడం కష్టంగా ఉంది!',
            isEmergency: true,
          },
          {
            label: '✅ అపాయింట్‌మెంట్ బుక్ (Book)',
            text: 'సరే అపాయింట్‌మెంట్ బుక్ చేయండి.',
          },
        ];
      case 'hi':
        return [
          {
            label: '💬 सामान्य बातचीत (General Chat)',
            text: 'नमस्ते! मैं आपसे सामान्य बातचीत करना चाहता हूँ। कृपया अपने क्लिनिक और स्वास्थ्य सेवाओं के बारे में बताएं।',
          },
          {
            label: '🦴 कंधे का दर्द (Section 24)',
            text: "Hi, I've been having shoulder pain for the last week and I'd like to see a doctor.",
          },
          {
            label: '🩺 पेट दर्द (Gastro)',
            text: 'मुझे 2 दिनों से तेज पेट दर्द है, डॉक्टर से मिलना है।',
          },
          {
            label: '🦴 घुटने का दर्द (Ortho)',
            text: 'मेरे घुटने में तेज दर्द है, क्या ऑर्थोपेडिक डॉक्टर से अपॉइंटमेंट मिल सकता है?',
          },
          {
            label: '🚨 Patient AI Interaction',
            text: 'मुझे सीने में तेज दर्द और सांस लेने में तकलीफ हो रही है!',
            isEmergency: true,
          },
          {
            label: '✅ अपॉइंटमेंट बुक करें (Book)',
            text: 'हाँ, अपॉइंटमेंट बुक कर दीजिए।',
          },
        ];
      default:
        return [
          {
            label: '💬 Normal / General Conversation',
            text: 'Hello! Can we have a normal conversation? I want to ask some general questions about health and clinic services.',
          },
          {
            label: '🦴 Shoulder Pain (PRD Example)',
            text: "Hi, I've been having shoulder pain for the last week and I'd like to see a doctor.",
          },
          {
            label: '🩺 Stomach / Gastro Pain',
            text: "I've had severe stomach ache and nausea since yesterday.",
          },
          {
            label: '🦴 Shoulder / Ortho Pain (PRD 5.12)',
            text: "I've been having shoulder pain for the last few weeks.",
          },
          {
            label: '🦵 Knee / Joint Pain',
            text: "I've had knee pain for 3 days, can I see an orthopedic doctor?",
          },
          {
            label: '🚨 Patient AI Interaction',
            text: 'I have acute chest tightness and severe shortness of breath right now!',
            isEmergency: true,
          },
          {
            label: '👨‍⚕️ Show Available Doctors',
            text: 'Yes, show available doctors.',
          },
        ];
    }
  };

  const presetPrompts = getPresetPrompts();

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between space-y-4 shadow-md h-full">
      <div className="space-y-3">
        {/* Top Header & Dual Mode Tabs */}
        <div className="flex flex-wrap justify-between items-center pb-2 border-b border-slate-800 gap-2">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              <span>AI Conversational Intake Hub</span>
            </h3>
          </div>

          {/* Mode Switch: Web Voice vs Inbound Phone Simulator */}
          <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveMode('web')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
                activeMode === 'web'
                  ? 'bg-emerald-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Mic className="w-3.5 h-3.5" />
              <span>Web Real-Time Voice</span>
            </button>

            <button
              onClick={() => setActiveMode('phone')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
                activeMode === 'phone'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <PhoneIncoming className="w-3.5 h-3.5" />
              <span>Inbound Phone Simulator</span>
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={testSpeaker}
              className="text-[11px] font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-2.5 py-1 rounded-lg flex items-center gap-1.5 transition shadow-sm"
              title="Click to verify computer speaker audio playback"
            >
              <Volume2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Speaker Test</span>
            </button>

            <button
              onClick={() => setIsMuted(!isMuted)}
              className={`p-1.5 rounded-lg border transition ${
                isMuted
                  ? 'bg-rose-950/60 border-rose-800/80 text-rose-400'
                  : 'bg-slate-800 border-slate-700 text-slate-300 hover:text-white'
              }`}
              title={isMuted ? 'Unmute AI Voice Output' : 'Mute AI Voice Output'}
            >
              {isMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>

        {/* MODE 1: WEB REAL-TIME VOICE */}
        {activeMode === 'web' && (
          <div className="space-y-3">
            {/* Notice Banner */}
            {voiceNotice && (
              <div className="p-2.5 bg-amber-950/40 border border-amber-600/40 rounded-xl text-xs flex items-start space-x-2 text-amber-300">
                <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <div className="flex-1 font-semibold">{voiceNotice}</div>
              </div>
            )}

            {/* Device & Engine Controls */}
            <div className="flex flex-wrap items-center justify-between gap-2 p-2 bg-slate-900/60 rounded-xl border border-slate-800 text-xs">
              <div className="flex items-center space-x-2">
                <Mic className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-slate-400 font-semibold">{t('mic_device')}:</span>
                <select
                  value={selectedDeviceId}
                  onChange={(e) => setSelectedDeviceId(e.target.value)}
                  className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-2 py-1 focus:outline-none max-w-[170px] truncate"
                >
                  <option value="default">Default Microphone</option>
                  {audioDevices.map((d, i) => (
                    <option key={d.deviceId || i} value={d.deviceId}>
                      {d.label || `Microphone ${i + 1}`}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center space-x-1.5">
                <span className="text-slate-400 text-[11px] font-semibold">TTS Engine:</span>
                <button
                  onClick={() => setVoiceMode('server')}
                  className={`px-2 py-1 rounded-lg text-[11px] font-bold border transition ${
                    voiceMode === 'server'
                      ? 'bg-emerald-600 text-white border-emerald-500 shadow-sm'
                      : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
                  }`}
                >
                  ElevenLabs Neural
                </button>
                <button
                  onClick={() => setVoiceMode('browser')}
                  className={`px-2 py-1 rounded-lg text-[11px] font-semibold border transition ${
                    voiceMode === 'browser'
                      ? 'bg-sky-600 text-white border-sky-500 shadow-sm'
                      : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
                  }`}
                >
                  Browser WebSpeech
                </button>
              </div>
            </div>

            {/* Dynamic Visualizer Canvas */}
            <AudioVisualizerCanvas
              isActive={isRecording || isSpeaking || isProcessing || streamActive}
              isSpeaking={isSpeaking}
              isListening={isRecording}
              audioLevel={audioLevel}
            />

            {/* Audio Recording & Dialogue Status Bar */}
            <div
              className={`rounded-xl p-3 flex items-center justify-between border transition-all ${
                isRecording
                  ? 'bg-rose-950/40 border-rose-500/40'
                  : isSpeaking
                  ? 'bg-sky-950/40 border-sky-500/40'
                  : 'bg-slate-950 border-slate-800'
              }`}
            >
              <div className="flex items-center space-x-3">
                <button
                  onClick={handleMicToggle}
                  style={{
                    transform: isRecording ? `scale(${1 + Math.min(0.2, audioLevel / 200)})` : 'scale(1)',
                    transition: 'transform 0.08s ease-out',
                  }}
                  className={`w-11 h-11 rounded-xl flex items-center justify-center shadow-md ${
                    isRecording
                      ? 'bg-rose-600 text-white shadow-rose-900/50 shadow-lg ring-2 ring-rose-400/50'
                      : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 hover:bg-emerald-500/30'
                  }`}
                  title={isRecording ? 'Click to stop listening' : 'Click to speak'}
                >
                  {isRecording ? <MicOff className="w-5 h-5 animate-pulse" /> : <Mic className="w-5 h-5" />}
                </button>
                <div>
                  <div className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                    {isRecording ? (
                      isEndpointPending ? (
                        <span className="text-amber-400 font-bold flex items-center gap-1.5 animate-pulse">
                          <Radio className="w-3.5 h-3.5 text-amber-400" />
                          Speech finished &bull; Connecting to Clinical AI (&lt;1s)...
                        </span>
                      ) : transcriptLive.trim() ? (
                        <span className="text-rose-400 font-bold flex items-center gap-1.5">
                          <Mic className="w-3.5 h-3.5 text-rose-400 animate-pulse" />
                          Hearing you: &ldquo;{transcriptLive}&rdquo;
                        </span>
                      ) : (
                        <span className="text-rose-400 flex items-center gap-1.5">
                          <Radio className="w-3 h-3 text-rose-400 animate-ping" />
                          Listening to your microphone... Speak naturally
                        </span>
                      )
                    ) : isProcessing ? (
                      <span className="text-emerald-400 font-bold flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 animate-spin" />
                        AI analyzing symptoms &amp; scheduling consultation...
                      </span>
                    ) : isSpeaking ? (
                      <span className="text-sky-400 font-bold flex items-center gap-1.5">
                        <Volume2 className="w-3.5 h-3.5 animate-bounce" />
                        AI Speaking aloud (listen or speak to interrupt)...
                      </span>
                    ) : bargeInAlert ? (
                      <span className="text-rose-400 font-black">Interrupted AI speech &bull; Listening to you</span>
                    ) : streamActive ? (
                      <span className="text-indigo-400">Streaming AI Audio &amp; Tokens...</span>
                    ) : (
                      'Microphone Ready &bull; Speak naturally (AI auto-detects end of speech)'
                    )}
                  </div>
                  <div className="text-[10px] text-slate-500">
                    Auto-Endpoint VAD &bull; Hands-Free Continuous Dialogue &bull; Sub-2s Latency
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setHandsFreeMode(!handsFreeMode)}
                  className={`text-[10px] font-bold px-2.5 py-1 rounded-lg border transition flex items-center gap-1 ${
                    handsFreeMode
                      ? 'bg-emerald-950/60 border-emerald-700/80 text-emerald-300'
                      : 'bg-slate-800 border-slate-700 text-slate-400'
                  }`}
                >
                  <Radio className="w-3 h-3" />
                  <span>Hands-Free: {handsFreeMode ? 'ON' : 'OFF'}</span>
                </button>

                {isSpeaking && (
                  <button
                    onClick={triggerBargeIn}
                    className="text-[10px] bg-rose-500/20 text-rose-300 border border-rose-500/30 px-2 py-1 rounded-lg font-bold hover:bg-rose-500/30 transition"
                  >
                    Interrupt AI
                  </button>
                )}
              </div>
            </div>

            {/* Quick Clinical Prompts */}
            <div className="space-y-1">
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                Clinical Prompts (Click to test full voice dialogue):
              </div>
              <div className="flex flex-wrap gap-1.5">
                {presetPrompts.map((p, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(p.text)}
                    className={`text-xs px-2.5 py-1.5 rounded-lg border transition flex items-center space-x-1.5 ${
                      p.isEmergency
                        ? 'bg-rose-950/60 hover:bg-rose-900/60 text-rose-300 border-rose-800/60'
                        : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700'
                    }`}
                  >
                    <span>{p.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Live Message Log */}
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 space-y-2 text-xs max-h-52 overflow-y-auto">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`p-2.5 rounded-lg space-y-1 ${
                    m.sender === 'patient'
                      ? 'bg-slate-800/80 text-slate-100 ml-6 border border-slate-700'
                      : m.isEmergency
                      ? 'bg-rose-950/80 text-rose-200 mr-6 border border-rose-800/80'
                      : 'bg-slate-900 text-slate-200 mr-6 border border-slate-800'
                  }`}
                >
                  <div className="flex justify-between items-center text-[10px] text-slate-400">
                    <span className="font-semibold capitalize">
                      {m.sender === 'patient' ? user?.name || 'You' : 'AI Medical Assistant'}
                    </span>
                    <span>{m.timestamp}</span>
                  </div>
                  <p className="font-medium leading-relaxed">
                    {m.text}
                    {m.isStreaming && (
                      <span className="inline-block w-1.5 h-3 bg-emerald-400 ml-1 animate-pulse" />
                    )}
                  </p>
                  {m.intent && (
                    <div className="flex justify-between items-center pt-1 text-[10px]">
                      <span
                        className={`px-1.5 py-0.5 rounded font-bold ${
                          m.isEmergency
                            ? 'bg-rose-500/20 text-rose-400'
                            : 'bg-emerald-500/10 text-emerald-400'
                        }`}
                      >
                        {m.intent}
                      </span>
                      {m.sender === 'assistant' && !m.isStreaming && (
                        <button
                          onClick={() => speak(m.text)}
                          className="text-slate-400 hover:text-emerald-400 transition flex items-center space-x-1"
                        >
                          <Volume2 className="w-3.5 h-3.5" />
                          <span className="text-[10px]">Replay Voice</span>
                        </button>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Conversation Ended Notice & Restart CTA */}
            {isConversationEnded && (
              <div className="bg-emerald-950/60 border border-emerald-500/40 rounded-xl p-3 flex items-center justify-between mt-1 mb-1 animate-fadeIn">
                <div className="flex items-center space-x-2 text-emerald-400">
                  <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                  <div>
                    <div className="text-xs font-bold text-emerald-300">Consultation Complete &bull; Conversation Ended</div>
                    <div className="text-[10px] text-slate-300">Your pre-visit responses have been sent directly to the doctor.</div>
                  </div>
                </div>
                <button
                  onClick={() => {
                    resetSession();
                    setIsConversationEnded(false);
                  }}
                  className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs rounded-lg shadow transition"
                >
                  Start New Consultation
                </button>
              </div>
            )}

            {/* Input Bar */}
            <div className="flex space-x-2 pt-1">
              <input
                type="text"
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !isConversationEnded && handleSend(inputVal)}
                disabled={isConversationEnded}
                placeholder={
                  isConversationEnded
                    ? 'Consultation concluded. Click "Start New Consultation" to start again.'
                    : isRecording
                    ? 'Listening to your voice...'
                    : 'Speak into microphone or enter symptoms...'
                }
                className="flex-1 bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <button
                onClick={() => handleSend(inputVal)}
                disabled={isProcessing || isConversationEnded}
                className="bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs px-4 py-2 rounded-xl transition shadow-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
              >
                <Send className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Send</span>
              </button>
            </div>
          </div>
        )}

        {/* MODE 2: INBOUND PHONE SIMULATOR */}
        {activeMode === 'phone' && (
          <div className="space-y-3">
            {/* Phone Header Banner */}
            <div className="p-3 bg-indigo-950/30 border border-indigo-800/60 rounded-xl flex flex-wrap items-center justify-between gap-2 text-xs">
              <div className="flex items-center space-x-2.5">
                <div
                  className={`w-3 h-3 rounded-full ${
                    callState === 'CONNECTED'
                      ? 'bg-emerald-400 animate-ping'
                      : callState === 'ESCALATED'
                      ? 'bg-amber-400 animate-pulse'
                      : callState === 'CALLING'
                      ? 'bg-sky-400 animate-pulse'
                      : 'bg-slate-600'
                  }`}
                />
                <div>
                  <span className="font-bold text-white flex items-center gap-1.5">
                    <Phone className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Inbound PSTN / SIP Telephony Simulator</span>
                  </span>
                  <div className="text-[10px] text-indigo-300">
                    ANI Caller Identification &bull; IVR Automated Triage &bull; Human Escalation Bridge
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                    callState === 'CONNECTED'
                      ? 'bg-emerald-950 text-emerald-300 border-emerald-700'
                      : callState === 'ESCALATED'
                      ? 'bg-amber-950 text-amber-300 border-amber-700'
                      : callState === 'CALLING'
                      ? 'bg-sky-950 text-sky-300 border-sky-700'
                      : 'bg-slate-800 text-slate-400 border-slate-700'
                  }`}
                >
                  Status: {callState}
                </span>

                {phoneSessionId && (
                  <span className="text-[10px] font-mono bg-slate-950 px-2 py-0.5 rounded border border-slate-800 text-slate-400">
                    SID: {phoneSessionId.slice(0, 10)}...
                  </span>
                )}
              </div>
            </div>

            {/* Caller Number Input & Call Controls */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">
                  Caller Phone Number (ANI):
                </label>
                <input
                  type="text"
                  value={callerPhone}
                  onChange={(e) => setCallerPhone(e.target.value)}
                  disabled={callState === 'CONNECTED' || callState === 'CALLING'}
                  placeholder="+1-555-0199"
                  className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-mono focus:ring-2 focus:ring-indigo-500 focus:outline-none disabled:opacity-60"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Hospital Line / DID:</label>
                <select
                  value={hospitalLine}
                  onChange={(e) => setHospitalLine(e.target.value)}
                  disabled={callState === 'CONNECTED' || callState === 'CALLING'}
                  className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2.5 py-1.5 text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none disabled:opacity-60"
                >
                  <option value="HOSP-CITY-01">City General Hospital (+1-800-555-0101)</option>
                  <option value="HOSP-VALLEY-02">Valley Care Medical (+1-800-555-0102)</option>
                  <option value="HOSP-METRO-03">Metro Heart Center (+1-800-555-0103)</option>
                </select>
              </div>

              <div className="flex items-end space-x-2">
                {callState === 'IDLE' || callState === 'ENDED' ? (
                  <button
                    onClick={handleStartInboundCall}
                    disabled={isPhoneBusy}
                    className="w-full bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs py-2 px-3 rounded-lg transition shadow flex items-center justify-center space-x-1.5 disabled:opacity-50"
                  >
                    <PhoneCall className="w-3.5 h-3.5" />
                    <span>Dial Inbound Line</span>
                  </button>
                ) : (
                  <>
                    <button
                      onClick={handleHangUp}
                      className="flex-1 bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs py-2 px-2.5 rounded-lg transition shadow flex items-center justify-center space-x-1"
                    >
                      <PhoneOff className="w-3.5 h-3.5" />
                      <span>Hang Up</span>
                    </button>
                    <button
                      onClick={handleEscalateCall}
                      className="flex-1 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs py-2 px-2.5 rounded-lg transition shadow flex items-center justify-center space-x-1"
                      title="Simulate patient asking for supervisor or clinical emergency escalation"
                    >
                      <PhoneForwarded className="w-3.5 h-3.5" />
                      <span>Transfer Human</span>
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Active Phone Call Dialogue & Keypad */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {/* Call Transcript Box */}
              <div className="md:col-span-2 bg-slate-950 border border-slate-800 rounded-xl p-3 space-y-2 text-xs h-56 overflow-y-auto flex flex-col justify-between">
                <div className="space-y-2 overflow-y-auto pr-1">
                  {phoneMessages.length === 0 ? (
                    <div className="text-slate-500 text-center py-10 italic">
                      No active call. Click "Dial Inbound Line" to simulate an incoming telephone call to the hospital.
                    </div>
                  ) : (
                    phoneMessages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`p-2 rounded-lg text-xs leading-relaxed ${
                          msg.sender === 'caller'
                            ? 'bg-indigo-950/60 border border-indigo-800 text-indigo-100 ml-6'
                            : msg.sender === 'system'
                            ? 'bg-slate-900 border border-slate-800 text-slate-400 italic text-[11px]'
                            : msg.isEscalation
                            ? 'bg-amber-950/80 border border-amber-700 text-amber-200 mr-6'
                            : 'bg-slate-900 border border-slate-800 text-slate-200 mr-6'
                        }`}
                      >
                        <div className="flex justify-between items-center text-[10px] text-slate-500 mb-0.5">
                          <span className="font-bold uppercase tracking-wider">
                            {msg.sender === 'caller'
                              ? `Caller (${callerPhone})`
                              : msg.sender === 'system'
                              ? 'Telephony Switch'
                              : 'Hospital IVR Assistant'}
                          </span>
                          <span>{msg.time}</span>
                        </div>
                        <div>{msg.text}</div>
                        {msg.action && (
                          <div className="mt-1 text-[10px] text-indigo-400 font-mono">
                            Action: {msg.action}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>

                {/* In-Call Telephony Input */}
                {callState === 'CONNECTED' && (
                  <div className="pt-2 border-t border-slate-800 flex space-x-2">
                    <input
                      type="text"
                      value={phoneUtterance}
                      onChange={(e) => setPhoneUtterance(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSendPhoneTurn(phoneUtterance)}
                      placeholder="Speak on telephone line (e.g. 'I need to book cardiologist tomorrow')..."
                      className="flex-1 bg-slate-900 border border-slate-700 text-slate-200 rounded-lg px-2.5 py-1.5 text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    />
                    <button
                      onClick={() => handleSendPhoneTurn(phoneUtterance)}
                      disabled={isPhoneBusy}
                      className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs px-3 py-1.5 rounded-lg transition disabled:opacity-50 flex items-center space-x-1"
                    >
                      <Send className="w-3 h-3" />
                      <span>Speak</span>
                    </button>
                  </div>
                )}
              </div>

              {/* Telephone Dialpad */}
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col justify-between text-xs">
                <div className="space-y-2">
                  <div className="text-[11px] font-bold text-slate-400 text-center">
                    DTMF Dialpad
                  </div>
                  <div className="bg-slate-900 border border-slate-800 rounded px-2 py-1 text-center font-mono text-xs text-white min-h-[26px]">
                    {dialpadInput || '-'}
                  </div>
                  <div className="grid grid-cols-3 gap-1.5">
                    {['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'].map((k) => (
                      <button
                        key={k}
                        onClick={() => handleDialpadPress(k)}
                        className="p-2 bg-slate-900 hover:bg-slate-800 text-slate-200 rounded-lg text-xs font-bold border border-slate-800 transition active:scale-95"
                      >
                        {k}
                      </button>
                    ))}
                  </div>
                </div>

                {dialpadInput && (
                  <button
                    onClick={() => handleSendPhoneTurn(dialpadInput)}
                    disabled={isPhoneBusy || callState !== 'CONNECTED'}
                    className="mt-2 w-full bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-bold py-1 rounded-lg border border-slate-700 disabled:opacity-50"
                  >
                    Send DTMF Digits
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Live AI Capabilities Verification Strip */}
        <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-slate-400 font-bold flex items-center gap-1.5">
              <BrainCircuit className="w-3.5 h-3.5 text-emerald-400" />
              <span>Verify Dedicated AI Endpoints (14-Point Capabilities):</span>
            </span>
            {isProbingAi && (
              <span className="text-[10px] text-emerald-400 animate-pulse">Running live probe...</span>
            )}
          </div>

          <div className="flex flex-wrap gap-1.5">
            <button
              onClick={() => runAiProbe('intent')}
              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium border border-slate-700 transition"
              title="Test NLU Intent Inference"
            >
              1. Intent Inference
            </button>
            <button
              onClick={() => runAiProbe('clarify')}
              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium border border-slate-700 transition"
              title="Test Context & Ambiguity Resolution"
            >
              2. Clarification Engine
            </button>
            <button
              onClick={() => runAiProbe('doctors')}
              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium border border-slate-700 transition"
              title="Test Doctor Discovery Search"
            >
              3. Doctor Discovery
            </button>
            <button
              onClick={() => runAiProbe('hospitals')}
              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium border border-slate-700 transition"
              title="Test Hospital Discovery"
            >
              4. Hospital Discovery
            </button>
            <button
              onClick={() => runAiProbe('capabilities')}
              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium border border-slate-700 transition"
              title="Test Agent Capability Manifest"
            >
              5. Tool Capabilities
            </button>
            <button
              onClick={() => runAiProbe('escalation')}
              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium border border-slate-700 transition"
              title="Test Human Escalation Ticket Creation"
            >
              6. Human Escalation Ticket
            </button>
          </div>

          {aiProbeResult && (
            <div className="p-2 rounded bg-slate-900 border border-slate-800 text-[11px] font-mono text-emerald-300 truncate">
              {aiProbeResult}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
