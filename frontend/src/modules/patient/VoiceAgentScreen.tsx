import React, { useState } from 'react';
import { Mic, MicOff, Send, Volume2, VolumeX, Hand, Sparkles, Radio, Zap, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useVoiceAgent } from '../../hooks/useVoiceAgent';
import { useAuth } from '../../hooks/useAuth';
import { useLanguage } from '../../context/LanguageContext';
import { AudioVisualizerCanvas } from '../../components/AudioVisualizerCanvas';

interface VoiceAgentScreenProps {
  onSpecialtySelected?: (specialty: string) => void;
}

export const VoiceAgentScreen: React.FC<VoiceAgentScreenProps> = ({ onSpecialtySelected }) => {
  const { user } = useAuth();
  const { t } = useLanguage();
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
  } = useVoiceAgent();

  const [inputVal, setInputVal] = useState('');

  const handleSend = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    setInputVal('');
    const res = await sendUtterance(
      trimmed,
      user?.identifier || '+1-555-1234567',
      user?.hospital_id || 'HOSP-CITY-01'
    );
    if (res) {
      const lower = trimmed.toLowerCase();
      if (lower.includes('shoulder') || lower.includes('orthopedic') || lower.includes('bone') || lower.includes('knee')) {
        onSpecialtySelected?.('Orthopedics');
      } else if (lower.includes('heart') || lower.includes('cardio') || lower.includes('chest')) {
        onSpecialtySelected?.('Cardiology');
      }
    }
  };

  const handleMicToggle = () => {
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

  const presetPrompts = [
    {
      label: '🦴 Knee / Joint Pain',
      text: "I've had knee pain for 3 days, can I book an appointment with an orthopedic doctor?",
    },
    {
      label: '🚨 Chest Tightness (Emergency)',
      text: 'I have acute chest tightness and severe shortness of breath right now!',
      isEmergency: true,
    },
    {
      label: '🫀 Cardiology Consult',
      text: 'I need a routine annual cardiology checkup with Dr. Rao.',
    },
    {
      label: '🩺 Schedule with Dr. Sharma',
      text: 'Can I see Dr. Sharma tomorrow morning at 10:00 AM?',
    },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between space-y-4 shadow-md h-full">
      <div className="space-y-3">
        {/* Header */}
        <div className="flex flex-wrap justify-between items-center pb-2 border-b border-slate-800 gap-2">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              <span>AI Voice &amp; Chat Intake</span>
            </h3>
          </div>

          <div className="flex items-center space-x-2">
            {/* Direct Speaker Test Button */}
            <button
              onClick={testSpeaker}
              className="text-[11px] font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-2.5 py-1 rounded-lg flex items-center gap-1.5 transition shadow-sm"
              title="Click to verify computer speaker audio playback"
            >
              <Volume2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Test Speaker</span>
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

            <button
              onClick={() => streamAIResponse(inputVal || "I've had knee pain for 3 days")}
              disabled={streamActive}
              className="text-[10px] font-bold bg-indigo-950 text-indigo-300 border border-indigo-800 px-2 py-1 rounded flex items-center gap-1 hover:bg-indigo-900 transition disabled:opacity-50"
              title="Test Real-Time Server-Sent Events (SSE) stream"
            >
              <Zap className="w-3 h-3 text-indigo-400" />
              <span>SSE Stream</span>
            </button>

            <span className="text-[10px] font-semibold bg-slate-800 text-slate-300 px-2 py-1 rounded border border-slate-700">
              {latencyMs ? `${latencyMs}ms` : '<2.0s'}
            </span>
          </div>
        </div>

        {/* Notice Banner if mic blocked or browser lacks recognition */}
        {voiceNotice && (
          <div className="p-3 bg-amber-950/40 border border-amber-600/40 rounded-xl text-xs flex items-start space-x-2 text-amber-300 animate-in fade-in duration-150">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="font-semibold">{voiceNotice}</span>
            </div>
          </div>
        )}

        {/* Device Selection & Engine Mode Strip (Upgrades 1 & 8) */}
        <div className="flex flex-wrap items-center justify-between gap-2 p-2 bg-slate-900/60 rounded-xl border border-slate-800 text-xs">
          <div className="flex items-center space-x-2">
            <Mic className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-slate-400 font-semibold">{t('mic_device')}:</span>
            <select
              value={selectedDeviceId}
              onChange={(e) => setSelectedDeviceId(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-2 py-1 focus:outline-none max-w-[190px] truncate"
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
              className={`px-2.5 py-1 rounded-lg text-[11px] font-bold border transition flex items-center space-x-1.5 ${
                voiceMode === 'server'
                  ? 'bg-emerald-600 text-white border-emerald-500 shadow-sm ring-1 ring-emerald-400/40'
                  : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
              }`}
              title="High-definition ElevenLabs Neural Voice Synthesis"
            >
              <span className={`w-1.5 h-1.5 rounded-full ${voiceMode === 'server' ? 'bg-emerald-300 animate-pulse' : 'bg-slate-500'}`} />
              <span>ElevenLabs Neural</span>
            </button>
            <button
              onClick={() => setVoiceMode('browser')}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition ${
                voiceMode === 'browser'
                  ? 'bg-sky-600 text-white border-sky-500 shadow-sm'
                  : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
              }`}
              title="Browser WebSpeech native robot voice"
            >
              Browser Local
            </button>
          </div>
        </div>

        {/* Real Dynamic Audio Visualizer Canvas */}
        <AudioVisualizerCanvas
          isActive={isRecording || isSpeaking || isProcessing || streamActive}
          isSpeaking={isSpeaking}
          isListening={isRecording}
          audioLevel={audioLevel}
        />

        {/* Audio Status Strip */}
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
              className={`w-11 h-11 rounded-xl flex items-center justify-center transition shadow-md ${
                isRecording
                  ? 'bg-rose-600 text-white animate-pulse'
                  : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 hover:bg-emerald-500/30'
              }`}
              title={isRecording ? 'Click to stop & send voice' : 'Click to start speaking into microphone'}
            >
              {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>
            <div>
              <div className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                {isRecording ? (
                  <span className="text-rose-400 flex items-center gap-1">
                    <Radio className="w-3 h-3 animate-ping" />
                    Listening... (speak now, then pause or click Send)
                  </span>
                ) : isSpeaking ? (
                  <span className="text-sky-400 flex items-center gap-1">
                    <Volume2 className="w-3 h-3 animate-bounce" />
                    Speaking via Audio Synthesizer (TTS)...
                  </span>
                ) : bargeInAlert ? (
                  <span className="text-rose-400 font-black">Barge-In Interruption Executed (&lt;180ms)</span>
                ) : streamActive ? (
                  <span className="text-indigo-400">Streaming AI Audio &amp; Tokens...</span>
                ) : isProcessing ? (
                  'Processing Clinical Intake NLP...'
                ) : (
                  'Microphone Ready &bull; Click mic icon or select scenario'
                )}
              </div>
              <div className="text-[10px] text-slate-500">
                Natural Web Speech Synthesizer &bull; Sub-180ms Interruption Active
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {isRecording && (
              <button
                onClick={handleManualSendCurrent}
                className="text-xs bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold px-3 py-1.5 rounded-lg transition shadow-md flex items-center space-x-1"
                title="Send current spoken words to AI"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Send to AI</span>
              </button>
            )}

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

        {/* Live Transcript Bubble */}
        {(transcriptLive || (isRecording && inputVal)) && (
          <div className="p-3 bg-slate-950 border border-rose-500/50 rounded-xl text-xs flex items-center justify-between space-x-2 animate-in fade-in duration-100 shadow-inner">
            <div className="flex items-center space-x-2 flex-1 overflow-hidden">
              <Radio className="w-3.5 h-3.5 text-rose-400 animate-pulse shrink-0" />
              <span className="text-slate-400 text-[11px] shrink-0">Hearing:</span>
              <span className="text-white font-medium italic truncate">
                "{transcriptLive || inputVal}"
              </span>
            </div>
            <button
              onClick={handleManualSendCurrent}
              className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-[11px] rounded-lg transition shrink-0"
            >
              Send to AI
            </button>
          </div>
        )}

        {/* Test Clinical Scenarios */}
        <div className="space-y-1">
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            Quick Clinical Scenarios (Click to test full voice dialogue):
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

        {/* Message Log */}
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 space-y-2 text-xs max-h-56 overflow-y-auto">
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
                        : m.intent === 'SSE_STREAMING'
                        ? 'bg-indigo-500/20 text-indigo-300'
                        : 'bg-emerald-500/10 text-emerald-400'
                    }`}
                  >
                    {m.intent}
                  </span>
                  {m.sender === 'assistant' && !m.isStreaming && (
                    <button
                      onClick={() => speak(m.text)}
                      className="text-slate-400 hover:text-emerald-400 transition flex items-center space-x-1"
                      title="Speak Response Aloud via TTS"
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
      </div>

      {/* Input Controls */}
      <div className="space-y-2 pt-2 border-t border-slate-800">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend(inputVal)}
            placeholder={
              isRecording ? 'Listening to your voice...' : 'Speak into microphone or enter symptoms...'
            }
            className="flex-1 bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <button
            onClick={() => handleSend(inputVal)}
            disabled={isProcessing}
            className="bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs px-4 py-2 rounded-xl transition shadow-md disabled:opacity-50 flex items-center space-x-1"
          >
            <Send className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>

        <div className="flex justify-between items-center text-[11px] text-slate-500">
          <button
            onClick={triggerBargeIn}
            className="text-rose-400 hover:text-rose-300 font-semibold flex items-center space-x-1"
          >
            <Hand className="w-3.5 h-3.5" />
            <span>Test Barge-In (&lt;180ms)</span>
          </button>
          <span>Active Patient: {user?.identifier || '+1-555-1234567'}</span>
        </div>
      </div>
    </div>
  );
};
