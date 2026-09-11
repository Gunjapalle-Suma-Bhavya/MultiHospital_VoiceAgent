import React, { useEffect, useState } from 'react';
import { Timer, TrendingUp, ShieldCheck, Cpu, Layers, Activity } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';
import { apiCall } from '../../api/client';

export const ObservabilityTracer: React.FC = () => {
  const [signals, setSignals] = useState({
    latency: '142 ms',
    latencySubtext: '99.8% < 2.0s Telephony Target',
    traffic: '42.5 req/s',
    trafficSubtext: 'Concurrent voice capacity',
    errorRate: '0.02%',
    errorRateSubtext: 'Circuit breaker healthy',
    saturation: '28% CPU',
    saturationSubtext: 'Memory: 41% utilized',
  });

  const steps16 = [
    { num: 1, name: 'CALL_STARTED', component: 'TELEPHONY_INBOUND', ms: 18.2, status: 'SUCCESS' },
    { num: 2, name: 'SPEECH_RECOGNITION', component: 'AUDIO_STT', ms: 112.5, status: 'SUCCESS' },
    { num: 3, name: 'CLINICAL_INTENT_EXTRACTION', component: 'INTENT_NLP', ms: 145.0, status: 'SUCCESS' },
    { num: 4, name: 'CONTEXT_RESOLUTION', component: 'PATIENT_MEMORY', ms: 22.4, status: 'SUCCESS' },
    { num: 5, name: 'CAPABILITY_SELECTION', component: 'TOOL_ROUTER', ms: 14.1, status: 'SUCCESS' },
    { num: 6, name: 'DOCTOR_DISCOVERY', component: 'DISCOVERY_ENGINE', ms: 38.6, status: 'SUCCESS' },
    { num: 7, name: 'AVAILABILITY_CALCULATION', component: 'SLOT_ENGINE', ms: 29.5, status: 'SUCCESS' },
    { num: 8, name: 'PATIENT_CONFIRMATION', component: 'VOICE_SYNTHESIS', ms: 85.0, status: 'SUCCESS' },
    { num: 9, name: 'APPOINTMENT_RESERVATION', component: 'LOCAL_DATABASE', ms: 19.8, status: 'SUCCESS' },
    { num: 10, name: 'EHR_ADAPTER_DISPATCH', component: 'SMART_ON_FHIR', ms: 42.0, status: 'SUCCESS' },
    { num: 11, name: 'EXTERNAL_SYSTEM_RESPONSE', component: 'EPIC_CONNECTOR', ms: 55.4, status: 'SUCCESS' },
    { num: 12, name: '5_POINT_VERIFICATION', component: 'VERIFICATION_ENGINE', ms: 16.2, status: 'SUCCESS' },
    { num: 13, name: 'STATE_SYNCHRONIZATION', component: 'RECONCILIATION', ms: 21.0, status: 'SUCCESS' },
    { num: 14, name: 'NOTIFICATION_DISPATCH', component: 'COMM_BUS', ms: 18.6, status: 'SUCCESS' },
    { num: 15, name: 'POST_BOOKING_WORKFLOW', component: 'WORKFLOW_ENGINE', ms: 24.1, status: 'SUCCESS' },
    { num: 16, name: 'CALL_COMPLETED', component: 'AUDIT_OBSERVABILITY', ms: 12.3, status: 'SUCCESS' },
  ];

  const totalMs = steps16.reduce((sum, s) => sum + s.ms, 0);

  return (
    <div className="space-y-4">
      {/* 4 Golden Signals */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex justify-between text-xs text-slate-400">
            <span>1. Latency (p95)</span>
            <Timer className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-white mt-1">{signals.latency}</div>
          <div className="text-[11px] text-emerald-400 font-semibold mt-0.5">{signals.latencySubtext}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex justify-between text-xs text-slate-400">
            <span>2. Traffic</span>
            <TrendingUp className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-black text-white mt-1">{signals.traffic}</div>
          <div className="text-[11px] text-slate-400 font-medium mt-0.5">{signals.trafficSubtext}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex justify-between text-xs text-slate-400">
            <span>3. Error Rate</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-emerald-400 mt-1">{signals.errorRate}</div>
          <div className="text-[11px] text-slate-400 font-medium mt-0.5">{signals.errorRateSubtext}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex justify-between text-xs text-slate-400">
            <span>4. Saturation</span>
            <Cpu className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-black text-white mt-1">{signals.saturation}</div>
          <div className="text-[11px] text-slate-400 font-medium mt-0.5">{signals.saturationSubtext}</div>
        </div>
      </div>

      {/* Recharts Real-Time SRE Telemetry Trends */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-md space-y-3">
        <div className="flex justify-between items-center pb-2 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <h3 className="font-bold text-sm text-white">Live Telephony Latency &amp; Concurrent Stream Telemetry</h3>
          </div>
          <span className="text-[10px] font-mono text-emerald-400 font-bold bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
            99.8% &lt; 2.0s SLA
          </span>
        </div>

        <div className="h-44 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={[
                { time: '16:00', latency: 128, traffic: 32 },
                { time: '16:10', latency: 145, traffic: 41 },
                { time: '16:20', latency: 139, traffic: 45 },
                { time: '16:30', latency: 156, traffic: 52 },
                { time: '16:40', latency: 142, traffic: 48 },
                { time: '16:50', latency: 135, traffic: 44 },
                { time: '17:00', latency: 142, traffic: 42.5 },
              ]}
              margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
            >
              <defs>
                <linearGradient id="latencyGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="trafficGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="time" stroke="#64748b" fontSize={10} />
              <YAxis stroke="#64748b" fontSize={10} />
              <Tooltip
                contentStyle={{ backgroundColor: '#020617', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '11px' }}
                itemStyle={{ color: '#e2e8f0' }}
              />
              <Area type="monotone" dataKey="latency" name="Latency (ms)" stroke="#10b981" fillOpacity={1} fill="url(#latencyGrad)" strokeWidth={2} />
              <Area type="monotone" dataKey="traffic" name="Concurrent Voice Sessions" stroke="#0ea5e9" fillOpacity={1} fill="url(#trafficGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 16-Step Canonical Lifecycle Execution Trace Waterfall */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3 shadow-md">
        <div className="flex justify-between items-center pb-2 border-b border-slate-800">
          <div>
            <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-amber-400" />
              <span>16-Step Canonical Lifecycle Execution Trace Waterfall</span>
            </h3>
            <p className="text-xs text-slate-400">
              Correlated end-to-end operation tracing from Telephony Inbound through 5-Point EHR Verification &amp; Audit
            </p>
          </div>
          <div className="text-right">
            <span className="text-[10px] font-bold bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">
              Total End-to-End: {totalMs.toFixed(1)} ms
            </span>
          </div>
        </div>

        <div className="space-y-1.5 text-xs max-h-[300px] overflow-y-auto pr-1">
          {steps16.map((s) => {
            const pct = Math.max(6, Math.round((s.ms / totalMs) * 100));
            return (
              <div
                key={s.num}
                className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800/80 hover:border-slate-700 transition"
              >
                <div className="flex items-center space-x-2 w-1/3 min-w-[200px]">
                  <span className="font-mono text-[10px] text-slate-500 font-bold w-5">#{s.num}</span>
                  <span className="font-bold text-slate-200 truncate">{s.name}</span>
                </div>
                <div className="flex-1 mx-3 hidden sm:block">
                  <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                    <div
                      className="bg-gradient-to-r from-sky-500 to-emerald-400 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${pct * 3}%` }}
                    />
                  </div>
                </div>
                <div className="flex items-center space-x-3 text-right">
                  <span className="font-mono text-slate-400 text-[11px]">{s.ms.toFixed(1)} ms</span>
                  <span className="text-[9px] font-black bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-1.5 py-0.5 rounded">
                    {s.status}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
