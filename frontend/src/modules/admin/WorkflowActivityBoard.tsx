import React, { useState, useEffect } from 'react';
import {
  GitBranch,
  Play,
  RotateCw,
  Search,
  CheckCircle2,
  Clock,
  AlertCircle,
  ChevronRight,
  Bell,
  Calendar,
  Layers,
  ArrowRight,
  Check
} from 'lucide-react';
import { api } from '../../api/client';
import { useToast } from '../../context/ToastContext';

interface Props {
  hospitalId?: string;
}

export const WorkflowActivityBoard: React.FC<Props> = ({ hospitalId }) => {
  const { showToast } = useToast();
  const [instances, setInstances] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedInstance, setSelectedInstance] = useState<any | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await api.getWorkflowInstances({ hospital_id: hospitalId, limit: 100 });
      if (res.ok && res.data) {
        setInstances(res.data.instances || []);
        setSummary(res.data.status_counts || {});
      }
    } catch (e: any) {
      console.error('Failed to load workflows:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, [hospitalId]);

  const handleProcessDue = async () => {
    setIsProcessing(true);
    try {
      const res = await api.processDueWorkflows();
      if (res.ok) {
        showToast(
          'success',
          'Due Workflows Processed',
          `Executed: ${res.data?.processed_count || 0} due step(s) processed successfully.`
        );
        loadData();
      } else {
        showToast('error', 'Processing Failed', res.error || 'Unable to execute due workflows.');
      }
    } catch (e: any) {
      showToast('error', 'Execution Error', e.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleTriggerStep = async (instanceId: string) => {
    try {
      const res = await api.triggerWorkflowStep(instanceId);
      if (res.ok) {
        showToast('success', 'Step Triggered', `Advanced workflow ${instanceId} to next step.`);
        loadData();
        if (selectedInstance && selectedInstance.id === instanceId) {
          setSelectedInstance({ ...selectedInstance, status: res.data?.status || 'RUNNING' });
        }
      } else {
        showToast('error', 'Trigger Failed', res.error || 'Failed to advance workflow step.');
      }
    } catch (e: any) {
      showToast('error', 'Trigger Error', e.message);
    }
  };

  const filteredInstances = instances.filter((inst) => {
    const q = searchTerm.toLowerCase();
    return (
      (inst.id || '').toLowerCase().includes(q) ||
      (inst.workflow_type || '').toLowerCase().includes(q) ||
      (inst.status || '').toLowerCase().includes(q) ||
      (inst.patient_name || '').toLowerCase().includes(q) ||
      (inst.doctor_name || '').toLowerCase().includes(q) ||
      (inst.hospital_name || '').toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header Strip */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-lg">
        <div className="flex items-center space-x-3.5">
          <div className="w-11 h-11 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20 flex items-center justify-center font-bold">
            <GitBranch className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-bold text-teal-400 uppercase tracking-wider">
              {hospitalId ? `Hospital Scoped (${hospitalId})` : 'Statewide Multi-Tenant'} Orchestration
            </div>
            <h2 className="text-lg font-black text-white">Workflow Engine &amp; Background Lifecycle</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Part 5: Booking-triggered workflows, reminders, notifications, and retry state machines
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleProcessDue}
            disabled={isProcessing}
            className="text-xs bg-teal-600 hover:bg-teal-500 text-white font-bold px-3.5 py-1.5 rounded-xl transition flex items-center space-x-1.5 shadow"
          >
            <Play className={`w-3.5 h-3.5 ${isProcessing ? 'animate-spin' : ''}`} />
            <span>{isProcessing ? 'Processing...' : 'Execute Due Workflows'}</span>
          </button>
          <button
            onClick={loadData}
            disabled={loading}
            className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold px-3 py-1.5 rounded-xl border border-slate-700 transition flex items-center space-x-1.5"
          >
            <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Booking-Triggered Canonical Workflow Chain */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <h3 className="font-extrabold text-xs text-white uppercase tracking-wider flex items-center gap-2">
            <Layers className="w-4 h-4 text-teal-400" />
            <span>Part 5 Booking-Triggered Background Workflow Lifecycle</span>
          </h3>
          <span className="text-[11px] font-bold text-teal-400 bg-teal-500/10 border border-teal-500/20 px-2 py-0.5 rounded">
            Automated State Machine
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 pt-1">
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-teal-300">Phase 1: Verification</span>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Creates external record, verifies bilateral sync, locks doctor slot.
            </div>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-teal-300">Phase 2: Notification</span>
              <Bell className="w-3.5 h-3.5 text-indigo-400" />
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Dispatches SMS &amp; email confirmation to patient with slot instructions.
            </div>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-teal-300">Phase 3: 24h Reminder</span>
              <Clock className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Schedules automated pre-appointment notification 24 hours prior.
            </div>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-teal-300">Phase 4: Resilience</span>
              <CheckCircle2 className="w-3.5 h-3.5 text-purple-400" />
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Exponential retry on network glitch; falls back to human escalation.
            </div>
          </div>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-slate-400 font-semibold">Total Workflow Instances</div>
          <div className="text-2xl font-black text-white mt-1">
            {summary.total !== undefined ? summary.total : instances.length}
          </div>
          <div className="text-[11px] text-teal-400 mt-0.5 font-medium">&bull; Booking &amp; clinical flows</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-slate-400 font-semibold">Waiting / Scheduled</div>
          <div className="text-2xl font-black text-amber-400 mt-1">
            {summary.waiting !== undefined ? summary.waiting : 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">&bull; 24h Pre-visit reminders</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-slate-400 font-semibold">Completed Successfully</div>
          <div className="text-2xl font-black text-emerald-400 mt-1">
            {summary.completed !== undefined ? summary.completed : instances.length}
          </div>
          <div className="text-[11px] text-emerald-500 mt-0.5">&bull; End-to-end executed</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-slate-400 font-semibold">Failed / Escalated</div>
          <div className="text-2xl font-black text-rose-400 mt-1">
            {summary.failed !== undefined ? summary.failed + (summary.escalated || 0) : 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">Auto-escalated to human</div>
        </div>
      </div>

      {/* Workflows Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-md">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div>
            <h3 className="font-extrabold text-sm text-white flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-teal-400" />
              <span>Real-Time Workflow Activity Ledger</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Inspecting state machine execution steps, schedule queues, and audit traces
            </p>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search workflow ID, patient, doctor..."
              className="w-full bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-xl pl-8 pr-3 py-1.5 focus:outline-none focus:border-teal-500 placeholder-slate-600"
            />
          </div>
        </div>

        <div className="overflow-x-auto max-h-[480px] overflow-y-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] border-y border-slate-800 sticky top-0">
              <tr>
                <th className="py-2.5 px-3">Workflow ID</th>
                <th className="py-2.5 px-3">Type</th>
                <th className="py-2.5 px-3">Hospital / Facility</th>
                <th className="py-2.5 px-3">Patient &amp; Doctor</th>
                <th className="py-2.5 px-3">Current Step</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-medium">
              {filteredInstances.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No workflow instances found.
                  </td>
                </tr>
              ) : (
                filteredInstances.map((inst, idx) => (
                  <tr
                    key={inst.id || idx}
                    onClick={() => setSelectedInstance(inst)}
                    className="hover:bg-slate-850 cursor-pointer transition"
                  >
                    <td className="py-2.5 px-3 font-mono text-teal-300">
                      {inst.id?.substring(0, 16)}...
                    </td>
                    <td className="py-2.5 px-3 text-slate-300 font-semibold">
                      {inst.workflow_type || 'booking_lifecycle'}
                    </td>
                    <td className="py-2.5 px-3 text-indigo-300 font-medium">
                      {inst.hospital_name || inst.hospital_id || 'Facility'}
                    </td>
                    <td className="py-2.5 px-3 text-slate-200">
                      <div>{inst.patient_name || 'Patient'}</div>
                      <div className="text-[10px] text-slate-500">Dr. {inst.doctor_name || 'Doctor'}</div>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-400">
                      {inst.current_step || 'schedule_reminder_24h'}
                    </td>
                    <td className="py-2.5 px-3">
                      {inst.status === 'COMPLETED' ? (
                        <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded text-[10px] font-black flex items-center w-max gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>COMPLETED</span>
                        </span>
                      ) : inst.status === 'WAITING' ? (
                        <span className="bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded text-[10px] font-black flex items-center w-max gap-1">
                          <Clock className="w-3 h-3" />
                          <span>WAITING (REMINDER)</span>
                        </span>
                      ) : (
                        <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded text-[10px] font-black">
                          {inst.status || 'RUNNING'}
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <ChevronRight className="w-4 h-4 text-slate-500 inline-block hover:text-white" />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Workflow Step Inspector Modal */}
      {selectedInstance && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full p-6 space-y-4 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <h3 className="font-extrabold text-sm text-white flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-teal-400" />
                <span>Workflow Execution Trace: <span className="font-mono text-teal-300">{selectedInstance.id}</span></span>
              </h3>
              <button
                onClick={() => setSelectedInstance(null)}
                className="text-slate-400 hover:text-white text-xs font-bold px-2 py-1"
              >
                Close
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div className="text-[10px] font-bold uppercase text-slate-500">Workflow Type</div>
                <div className="text-sm font-bold text-white mt-0.5">{selectedInstance.workflow_type || 'booking_lifecycle'}</div>
                <div className="text-[10px] text-slate-400 mt-1">Status: {selectedInstance.status}</div>
              </div>

              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div className="text-[10px] font-bold uppercase text-slate-500">Facility &amp; Participants</div>
                <div className="text-sm font-bold text-indigo-300 mt-0.5">{selectedInstance.hospital_name || 'Hospital'}</div>
                <div className="text-[10px] text-slate-400 mt-1">
                  {selectedInstance.patient_name} &bull; Dr. {selectedInstance.doctor_name}
                </div>
              </div>
            </div>

            {/* Step execution logs */}
            <div>
              <div className="text-xs font-bold text-slate-300 mb-2">Step Execution Trace:</div>
              <div className="space-y-2">
                {Array.isArray(selectedInstance.steps) && selectedInstance.steps.length > 0 ? (
                  selectedInstance.steps.map((st: any, sIdx: number) => (
                    <div key={sIdx} className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex items-center justify-between text-xs">
                      <div>
                        <div className="font-bold text-white flex items-center gap-1.5">
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                          <span>{st.step_name || st.name}</span>
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                          {st.executed_at || st.timestamp || 'Executed successfully'}
                        </div>
                      </div>
                      <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded text-[10px] font-bold">
                        {st.status || 'COMPLETED'}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 space-y-1 text-xs">
                    <div className="flex items-center justify-between text-emerald-400 font-semibold">
                      <span>1. create_appointment &amp; ehr_integration</span>
                      <span>COMPLETED</span>
                    </div>
                    <div className="flex items-center justify-between text-emerald-400 font-semibold">
                      <span>2. create_external_appointment_id &amp; verify_record</span>
                      <span>COMPLETED</span>
                    </div>
                    <div className="flex items-center justify-between text-emerald-400 font-semibold">
                      <span>3. synchronize_status (CONFIRMED)</span>
                      <span>COMPLETED</span>
                    </div>
                    <div className="flex items-center justify-between text-amber-400 font-semibold">
                      <span>4. schedule_reminder_24h</span>
                      <span>{selectedInstance.status === 'COMPLETED' ? 'COMPLETED' : 'SCHEDULED'}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Actions in drawer */}
            <div className="flex justify-between items-center pt-2 border-t border-slate-800">
              <span className="text-[11px] text-slate-500 font-mono">
                Created: {selectedInstance.created_at ? new Date(selectedInstance.created_at).toLocaleString() : 'Recent'}
              </span>
              <button
                onClick={() => handleTriggerStep(selectedInstance.id)}
                className="px-3.5 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-xs font-bold text-white transition flex items-center gap-1.5 shadow"
              >
                <Play className="w-3 h-3" />
                <span>Trigger Next Step</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
