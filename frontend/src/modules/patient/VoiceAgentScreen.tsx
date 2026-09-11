import React, { useState } from 'react';
import { Mic, Send, Volume2, Hand, Activity, Sparkles, AlertCircle } from 'lucide-react';
import { useVoiceAgent } from '../../hooks/useVoiceAgent';
import { useAuth } from '../../hooks/useAuth';

interface VoiceAgentScreenProps {
  onSpecialtySelected?: (specialty: string) => void;
}

export const VoiceAgentScreen: React.FC<VoiceAgentScreenProps> = ({ onSpecialtySelected }) => {
  const { user } = useAuth();
  const {
    messages,
    isProcessing,
    latencyMs,
    detectedIntent,
    bargeInAlert,
    sendUtterance,
    triggerBargeIn,
    speak,
  } = useVoiceAgent();

  const [inputVal, setInputVal] = useState('');

  const handleSend = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    setInputVal('');
    const res = await sendUtterance(trimmed, user?.identifier || '+1-555-SHOULDER', user?.hospital_id || 'HOSP-CITY-01');
    if (res) {
      const lower = trimmed.toLowerCase();
      if (lower.includes('shoulder') || lower.includes('orthopedic') || lower.includes('bone')) {
        onSpecialtySelected?.('Orthopedics');
      } else if (lower.includes('heart') || lower.includes('cardio') || lower.includes('chest')) {
        onSpecialtySelected?.('Cardiology');
      }
    }
  };

  const presetPrompts = [
    { label: '🦴 Shoulder Pain (Orthopedics)', text: "I've been experiencing acute right shoulder pain for a week, can I book an orthopedic doctor?" },
    { label: '🚨 Chest Tightness (Emergency)', text: 'I have acute chest tightness and severe shortness of breath right now!', isEmergency: true },
    { label: '🫀 Cardiology Consult', text: 'I need a routine annual cardiology checkup with Dr. Rao.' },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between space-y-4 shadow-md h-full">
      <div className="space-y-3">
        {/* Header */}
        <div className="flex justify-between items-center pb-2 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              <span>AI Voice &amp; Chat Intake</span>
            </h3>
          </div>
          <span className="text-[10px] font-semibold bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">
            {latencyMs ? `${latencyMs}ms Telephony Roundtrip` : '<2.0s Telephony Target'}
          </span>
        </div>

        {/* Audio Waveform & Status */}
        <div className="bg-slate-950 rounded-xl p-3.5 flex items-center justify-between border border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <Mic className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-200">
                {bargeInAlert ? 'Barge-In Interruption Triggered' : (isProcessing ? 'Processing Speech...' : 'Listening Channel Ready')}
              </div>
              <div className="text-[10px] text-slate-500">&lt;180ms Telephony Barge-In Enabled</div>
            </div>
          </div>

          {/* Animated Waveform */}
          <div className="flex items-center space-x-1 h-6">
            <span className={`w-1 bg-emerald-500 rounded-full transition-all ${isProcessing ? 'h-5 animate-pulse' : 'h-2'}`} />
            <span className={`w-1 bg-emerald-500 rounded-full transition-all ${isProcessing ? 'h-6 animate-pulse' : 'h-3'}`} />
            <span className={`w-1 bg-emerald-500 rounded-full transition-all ${isProcessing ? 'h-4 animate-pulse' : 'h-1'}`} />
            <span className={`w-1 bg-emerald-500 rounded-full transition-all ${isProcessing ? 'h-5 animate-pulse' : 'h-4'}`} />
          </div>
        </div>

        {/* Test Scenarios */}
        <div className="space-y-1">
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Test Scenario Prompts:</div>
          <div className="flex flex-wrap gap-1.5">
            {presetPrompts.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(p.text)}
                className={`text-xs px-2.5 py-1 rounded-lg border transition ${
                  p.isEmergency
                    ? 'bg-rose-950/60 hover:bg-rose-900/60 text-rose-300 border-rose-800/60'
                    : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700'
                }`}
              >
                {p.label}
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
                <span className="font-semibold capitalize">{m.sender === 'patient' ? (user?.name || 'You') : 'AI Assistant'}</span>
                <span>{m.timestamp}</span>
              </div>
              <p className="font-medium leading-relaxed">{m.text}</p>
              {m.intent && (
                <div className="flex justify-between items-center pt-1 text-[10px]">
                  <span className={`px-1.5 py-0.5 rounded font-bold ${m.isEmergency ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                    {m.intent}
                  </span>
                  {m.sender === 'assistant' && (
                    <button
                      onClick={() => speak(m.text)}
                      className="text-slate-400 hover:text-emerald-400 transition"
                      title="Speak Response"
                    >
                      <Volume2 className="w-3.5 h-3.5" />
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
            placeholder="Type clinical complaint or question..."
            className="flex-1 bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <button
            onClick={() => handleSend(inputVal)}
            disabled={isProcessing}
            className="bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs px-4 py-2 rounded-xl transition shadow-md disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5" />
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
          <span>Caller: {user?.identifier || '+1-555-SHOULDER'}</span>
        </div>
      </div>
    </div>
  );
};
