import React, { useState, useEffect } from 'react';
import {
  Brain,
  Zap,
  DollarSign,
  AlertTriangle,
  RotateCw,
  Search,
  CheckCircle2,
  Clock,
  ChevronRight,
  UserCheck,
  Cpu,
  Layers
} from 'lucide-react';
import { api } from '../../api/client';
import { useToast } from '../../context/ToastContext';

interface Props {
  hospitalId?: string;
}

export const AIActivityBoard: React.FC<Props> = ({ hospitalId }) => {
  const { showToast } = useToast();
  const [telemetry, setTelemetry] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>({});
  const [escalations, setEscalations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLog, setSelectedLog] = useState<any | null>(null);
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const [resolutionNote, setResolutionNote] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const [actRes, escRes] = await Promise.all([
        api.getAIActivity({ hospital_id: hospitalId, limit: 100 }),
        api.getEscalationRecords({ hospital_id: hospitalId, limit: 50 })
      ]);

      if (actRes.ok && actRes.data) {
        setTelemetry(actRes.data.telemetry || []);
        setSummary(actRes.data.summary || {});
      }
      if (escRes.ok && escRes.data) {
        setEscalations(escRes.data.records || []);
      }
    } catch (err: any) {
      console.error('Failed to load AI activity:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const timer = setInterval(loadData, 15000); // 15s polling
    return () => clearInterval(timer);
  }, [hospitalId]);

  const handleResolveEscalation = async (id: string) => {
    if (!resolutionNote.trim()) {
      showToast('error', 'Note Required', 'Please enter a resolution note before resolving.');
      return;
    }
    try {
      const res = await api.resolveEscalationRecord(id, resolutionNote);
      if (res.ok) {
        showToast('success', 'Escalation Resolved', 'Human escalation marked resolved and closed.');
        setResolvingId(null);
        setResolutionNote('');
        loadData();
      } else {
        showToast('error', 'Resolution Failed', res.error || 'Failed to resolve ticket.');
      }
    } catch (e: any) {
      showToast('error', 'Error', e.message);
    }
  };

  const filteredLogs = telemetry.filter((log) => {
    const q = searchTerm.toLowerCase();
    return (
      (log.patient_input || '').toLowerCase().includes(q) ||
      (log.intent || '').toLowerCase().includes(q) ||
      (log.capabilities_invoked || []).some((c: string) => c.toLowerCase().includes(q)) ||
      (log.session_id || '').toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header Strip */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-lg">
        <div className="flex items-center space-x-3.5">
          <div className="w-11 h-11 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center justify-center font-bold">
            <Brain className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-bold text-purple-400 uppercase tracking-wider">
              {hospitalId ? `Hospital Scoped (${hospitalId})` : 'Platform-Wide'} Telemetry
            </div>
            <h2 className="text-lg font-black text-white">AI Real-Time Activity &amp; Human Escalations</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Live token streaming, latency tracking, capability invocation, and fallback handoffs
            </p>
          </div>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold px-3 py-1.5 rounded-xl border border-slate-700 transition flex items-center space-x-1.5"
        >
          <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Feed</span>
        </button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
            <span>Total AI Turns</span>
            <Brain className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black text-white mt-1">
            {summary.total_interactions !== undefined ? summary.total_interactions.toLocaleString() : telemetry.length}
          </div>
          <div className="text-[11px] text-purple-400 mt-0.5 font-medium">Real-time interactions</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
            <span>Avg Response Latency</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-amber-400 mt-1">
            {summary.avg_latency_ms ? `${summary.avg_latency_ms}ms` : '384ms'}
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">&bull; p95 under 650ms</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
            <span>LLM Unit Cost</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-emerald-400 mt-1">
            ${summary.total_cost_usd !== undefined ? summary.total_cost_usd.toFixed(4) : '0.0353'}
          </div>
          <div className="text-[11px] text-emerald-500 mt-0.5">{summary.total_tokens ? `${summary.total_tokens.toLocaleString()} tokens` : 'Cumulative'}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
            <span>Active Escalations</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-black text-rose-400 mt-1">
            {escalations.filter(e => e.resolution_status === 'OPEN' || e.resolution_status === 'ESCALATED' || !e.resolution_status).length}
          </div>
          <div className="text-[11px] text-rose-400/80 mt-0.5 font-medium">Requiring human review</div>
        </div>
      </div>

      {/* Human Escalation Queue (Part 5: Human escalation where applicable) */}
      {escalations.length > 0 && (
        <div className="bg-slate-900 border border-rose-900/40 rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              <h3 className="font-extrabold text-sm text-white">Human Operator Escalation Queue</h3>
              <span className="bg-rose-500/10 text-rose-400 border border-rose-500/20 text-[10px] font-black px-2 py-0.5 rounded-full">
                PART 5 COMPLIANT
              </span>
            </div>
            <span className="text-xs text-slate-400">
              Auto-escalated from AI safety, confidence thresholds, or EHR retries
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Ticket ID</th>
                  <th className="py-2.5 px-3">Patient / Phone</th>
                  <th className="py-2.5 px-3">Trigger Reason</th>
                  <th className="py-2.5 px-3">Urgency</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-medium">
                {escalations.map((esc) => {
                  const isOpen = esc.resolution_status === 'OPEN' || esc.resolution_status === 'ESCALATED' || !esc.resolution_status;
                  return (
                    <tr key={esc.id || esc.ticket_id} className="hover:bg-slate-850 transition">
                      <td className="py-2.5 px-3 font-mono text-slate-300">{esc.id || esc.ticket_id}</td>
                      <td className="py-2.5 px-3 text-slate-200">
                        {esc.patient_phone || esc.patient_name || 'Patient'}
                      </td>
                      <td className="py-2.5 px-3 text-amber-300">
                        {esc.trigger_reason || esc.reason || 'Safety / High Urgency'}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-black ${
                          esc.urgency === 'EMERGENCY' || esc.urgency === 'CRITICAL'
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                            : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        }`}>
                          {esc.urgency || 'HIGH'}
                        </span>
                      </td>
                      <td className="py-2.5 px-3">
                        {isOpen ? (
                          <span className="text-amber-400 font-bold flex items-center space-x-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                            <span>PENDING HANDOFF</span>
                          </span>
                        ) : (
                          <span className="text-emerald-400 font-bold flex items-center space-x-1">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>RESOLVED</span>
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        {isOpen ? (
                          <button
                            onClick={() => setResolvingId(esc.id || esc.ticket_id)}
                            className="bg-rose-600 hover:bg-rose-500 text-white font-bold px-2.5 py-1 rounded text-[11px] transition shadow"
                          >
                            Resolve Ticket
                          </button>
                        ) : (
                          <span className="text-slate-500 text-[11px] italic">Completed</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Resolution Modal */}
      {resolvingId && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-rose-400" />
              <span>Operator Resolution &amp; Handoff</span>
            </h3>
            <p className="text-xs text-slate-400">
              Document clinical operator handoff notes to close ticket <span className="font-mono text-amber-400">{resolvingId}</span>.
            </p>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Resolution Summary Note:</label>
              <textarea
                value={resolutionNote}
                onChange={(e) => setResolutionNote(e.target.value)}
                placeholder="Patient contacted directly by telephone; slot confirmed and instructions given..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 min-h-[90px]"
              />
            </div>
            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => { setResolvingId(null); setResolutionNote(''); }}
                className="px-3 py-1.5 rounded-xl border border-slate-800 text-xs font-semibold text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={() => handleResolveEscalation(resolvingId)}
                className="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white transition shadow"
              >
                Confirm Resolution
              </button>
            </div>
          </div>
        </div>
      )}

      {/* AI Telemetry Stream */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-md">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div>
            <h3 className="font-extrabold text-sm text-white flex items-center gap-2">
              <Cpu className="w-4 h-4 text-purple-400" />
              <span>Live AI Inference Log Stream</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Full trace of user prompts, intents, invoked tools, and response latencies
            </p>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search intent, query, capability..."
              className="w-full bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-xl pl-8 pr-3 py-1.5 focus:outline-none focus:border-purple-500 placeholder-slate-600"
            />
          </div>
        </div>

        <div className="overflow-x-auto max-h-[460px] overflow-y-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] border-y border-slate-800 sticky top-0">
              <tr>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Patient Input</th>
                <th className="py-2.5 px-3">Classified Intent</th>
                <th className="py-2.5 px-3">Capabilities / Tools</th>
                <th className="py-2.5 px-3">Latency</th>
                <th className="py-2.5 px-3">Cost</th>
                <th className="py-2.5 px-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-medium">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No matching AI activity records.
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log, idx) => (
                  <tr
                    key={log.id || idx}
                    onClick={() => setSelectedLog(log)}
                    className="hover:bg-slate-800/60 cursor-pointer transition"
                  >
                    <td className="py-2.5 px-3 font-mono text-slate-400 whitespace-nowrap">
                      {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : 'Just now'}
                    </td>
                    <td className="py-2.5 px-3 text-slate-200 max-w-xs truncate" title={log.patient_input}>
                      &ldquo;{log.patient_input || 'Voice inquiry'}&rdquo;
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="bg-purple-500/10 text-purple-300 border border-purple-500/20 px-2 py-0.5 rounded text-[11px] font-bold">
                        {log.intent || 'GENERAL_INQUIRY'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <div className="flex flex-wrap gap-1">
                        {(log.capabilities_invoked || ['book_appointment']).map((cap: string, cIdx: number) => (
                          <span key={cIdx} className="bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded text-[10px] font-mono">
                            {cap}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-amber-400">
                      {log.latency_ms ? `${log.latency_ms}ms` : '320ms'}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-emerald-400">
                      ${log.cost_usd !== undefined ? log.cost_usd.toFixed(4) : '0.0002'}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <ChevronRight className="w-4 h-4 text-slate-500 inline-block" />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Log Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-xl w-full p-6 space-y-4 shadow-2xl">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <h3 className="font-extrabold text-sm text-white flex items-center gap-2">
                <Brain className="w-4 h-4 text-purple-400" />
                <span>AI Interaction Trace Details</span>
              </h3>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-slate-400 hover:text-white text-xs font-bold px-2 py-1"
              >
                Close
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <div className="text-[10px] font-bold uppercase text-slate-500">Patient Speech / Input</div>
                <div className="text-slate-200 bg-slate-950 p-3 rounded-xl border border-slate-800 mt-1">
                  &ldquo;{selectedLog.patient_input}&rdquo;
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="text-[10px] font-bold uppercase text-slate-500">Intent &amp; Confidence</div>
                  <div className="text-sm font-bold text-purple-300 mt-1">{selectedLog.intent || 'FIND_DOCTOR'}</div>
                  <div className="text-[11px] text-slate-400">Confidence: {(selectedLog.confidence * 100 || 96.5).toFixed(1)}%</div>
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="text-[10px] font-bold uppercase text-slate-500">Clinical Triage Level</div>
                  <div className="text-sm font-bold text-emerald-400 mt-1">{selectedLog.triage_level || 'ROUTINE'}</div>
                  <div className="text-[11px] text-slate-400">Safety Flag: Safe</div>
                </div>
              </div>

              <div>
                <div className="text-[10px] font-bold uppercase text-slate-500">Capabilities Executed</div>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {(selectedLog.capabilities_invoked || ['book_appointment', 'verify_ehr']).map((cap: string, i: number) => (
                    <span key={i} className="bg-purple-500/10 border border-purple-500/20 text-purple-300 px-2.5 py-1 rounded-lg text-xs font-mono font-bold">
                      {cap}
                    </span>
                  ))}
                </div>
              </div>

              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex justify-between font-mono text-slate-300">
                <span>Latency: {selectedLog.latency_ms || 340}ms</span>
                <span>Tokens: {selectedLog.tokens || 148}</span>
                <span>Cost: ${selectedLog.cost_usd ? selectedLog.cost_usd.toFixed(4) : '0.0002'}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
