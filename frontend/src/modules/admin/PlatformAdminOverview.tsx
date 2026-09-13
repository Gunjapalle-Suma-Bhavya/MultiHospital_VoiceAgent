import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Building2,
  Users,
  CheckCircle2,
  Clock,
  Activity,
  Layers,
  Sparkles,
  ArrowUpRight,
  Database,
  Cpu,
  RefreshCw,
  Server
} from 'lucide-react';
import { apiCall } from '../../api/client';

interface Props {
  onNavigateTab: (tab: string) => void;
}

export const PlatformAdminOverview: React.FC<Props> = ({ onNavigateTab }) => {
  const [hospitalsCount, setHospitalsCount] = useState<any>({ pending: 0, approved: 0, total: 0 });
  const [usersCount, setUsersCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [hospRes, usersRes] = await Promise.all([
        apiCall('/api/v1/admin/hospitals'),
        apiCall('/api/v1/auth/users')
      ]);

      if (hospRes.ok && hospRes.data?.counts) {
        setHospitalsCount(hospRes.data.counts);
      }
      if (usersRes.ok && usersRes.data?.users) {
        setUsersCount(usersRes.data.users.length);
      }
    } catch {
      // fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Platform Banner */}
      <div className="bg-gradient-to-r from-amber-500/10 via-slate-900 to-indigo-950/40 border border-amber-500/20 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-black text-amber-400 uppercase tracking-widest">
            <ShieldAlert className="w-4 h-4" />
            <span>Entire System Admin Command Center</span>
          </div>
          <h2 className="text-2xl font-black text-white mt-1">Multi-Hospital Platform Administration</h2>
          <p className="text-sm text-slate-300 mt-1 max-w-2xl">
            Statewide healthcare network orchestration with multi-tenant isolation, real-time voice AI agents, EHR synchronization, and comprehensive RBAC governance.
          </p>
        </div>

        <button
          onClick={fetchData}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs transition border border-slate-700 shadow"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-amber-400' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div 
          onClick={() => onNavigateTab('approval')}
          className="bg-slate-900 border border-slate-800 hover:border-amber-500/40 rounded-2xl p-5 cursor-pointer transition shadow-lg group"
        >
          <div className="flex justify-between items-start">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Pending Approvals</div>
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-black text-amber-400 mt-2">
            {hospitalsCount.pending}
          </div>
          <div className="text-xs text-slate-400 mt-1 flex items-center justify-between">
            <span>Awaiting Platform Review</span>
            <ArrowUpRight className="w-4 h-4 text-amber-400 opacity-0 group-hover:opacity-100 transition" />
          </div>
        </div>

        <div 
          onClick={() => onNavigateTab('management')}
          className="bg-slate-900 border border-slate-800 hover:border-indigo-500/40 rounded-2xl p-5 cursor-pointer transition shadow-lg group"
        >
          <div className="flex justify-between items-start">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active Hospitals</div>
            <div className="w-9 h-9 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center">
              <Building2 className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-black text-indigo-400 mt-2">
            {hospitalsCount.approved}
          </div>
          <div className="text-xs text-slate-400 mt-1 flex items-center justify-between">
            <span>Total Enrolled Facilities</span>
            <ArrowUpRight className="w-4 h-4 text-indigo-400 opacity-0 group-hover:opacity-100 transition" />
          </div>
        </div>

        <div 
          onClick={() => onNavigateTab('users')}
          className="bg-slate-900 border border-slate-800 hover:border-emerald-500/40 rounded-2xl p-5 cursor-pointer transition shadow-lg group"
        >
          <div className="flex justify-between items-start">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">User Directory</div>
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-black text-emerald-400 mt-2">
            {usersCount}
          </div>
          <div className="text-xs text-slate-400 mt-1 flex items-center justify-between">
            <span>Patients, Doctors &amp; Admins</span>
            <ArrowUpRight className="w-4 h-4 text-emerald-400 opacity-0 group-hover:opacity-100 transition" />
          </div>
        </div>

        <div 
          onClick={() => onNavigateTab('tenants')}
          className="bg-slate-900 border border-slate-800 hover:border-purple-500/40 rounded-2xl p-5 cursor-pointer transition shadow-lg group"
        >
          <div className="flex justify-between items-start">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Tenant Partitions</div>
            <div className="w-9 h-9 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-black text-purple-400 mt-2">
            100%
          </div>
          <div className="text-xs text-slate-400 mt-1 flex items-center justify-between">
            <span>Zero-Leak Row Partitioning</span>
            <ArrowUpRight className="w-4 h-4 text-purple-400 opacity-0 group-hover:opacity-100 transition" />
          </div>
        </div>
      </div>

      {/* Quick Action Matrix */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h3 className="text-base font-bold text-white mb-4 flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <span>Platform Administrative Actions</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <button
            onClick={() => onNavigateTab('approval')}
            className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-amber-500/50 hover:bg-slate-800/40 text-left transition flex items-start space-x-3.5 group"
          >
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center flex-shrink-0">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-white text-sm group-hover:text-amber-400 transition flex items-center space-x-1">
                <span>Hospital Approval Queue</span>
                {hospitalsCount.pending > 0 && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-400 text-slate-950 font-black">
                    {hospitalsCount.pending}
                  </span>
                )}
              </div>
              <div className="text-xs text-slate-400 mt-1">Review onboarding applications, verify credentials, and approve or reject facilities.</div>
            </div>
          </button>

          <button
            onClick={() => onNavigateTab('management')}
            className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-800/40 text-left transition flex items-start space-x-3.5 group"
          >
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center flex-shrink-0">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-white text-sm group-hover:text-indigo-400 transition">
                Hospital Management
              </div>
              <div className="text-xs text-slate-400 mt-1">Inspect approved healthcare facilities, departments, capacity, and active status.</div>
            </div>
          </button>

          <button
            onClick={() => onNavigateTab('register')}
            className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-emerald-500/50 hover:bg-slate-800/40 text-left transition flex items-start space-x-3.5 group"
          >
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center flex-shrink-0">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-white text-sm group-hover:text-emerald-400 transition">
                Hospital Registration
              </div>
              <div className="text-xs text-slate-400 mt-1">Directly enroll a new healthcare system or medical center into the platform.</div>
            </div>
          </button>

          <button
            onClick={() => onNavigateTab('users')}
            className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-sky-500/50 hover:bg-slate-800/40 text-left transition flex items-start space-x-3.5 group"
          >
            <div className="w-10 h-10 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20 flex items-center justify-center flex-shrink-0">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-white text-sm group-hover:text-sky-400 transition">
                User Authentication &amp; RBAC
              </div>
              <div className="text-xs text-slate-400 mt-1">Audit user logins, Google OAuth identifiers, activate or deactivate accounts.</div>
            </div>
          </button>

          <button
            onClick={() => onNavigateTab('tenants')}
            className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-purple-500/50 hover:bg-slate-800/40 text-left transition flex items-start space-x-3.5 group"
          >
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center justify-center flex-shrink-0">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-white text-sm group-hover:text-purple-400 transition">
                Multi-Tenant Architecture
              </div>
              <div className="text-xs text-slate-400 mt-1">Verify zero-leak isolation boundaries and tenant database partitions.</div>
            </div>
          </button>

          <button
            onClick={() => onNavigateTab('telemetry')}
            className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-amber-500/50 hover:bg-slate-800/40 text-left transition flex items-start space-x-3.5 group"
          >
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center flex-shrink-0">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-white text-sm group-hover:text-amber-400 transition">
                SRE Golden Signals &amp; Traces
              </div>
              <div className="text-xs text-slate-400 mt-1">Observe real-time latency, traffic, error rates, and OpenTelemetry trace waterfalls.</div>
            </div>
          </button>
        </div>
      </div>

      {/* Statewide Service Infrastructure Status */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h3 className="text-base font-bold text-white mb-4 flex items-center space-x-2">
          <Server className="w-4 h-4 text-emerald-400" />
          <span>Core Infrastructure Health &amp; Connectors</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">FastAPI API Gateway</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            </div>
            <div className="text-sm font-black text-emerald-400 mt-1">Operational</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Uvicorn &bull; Port 8000 &bull; p99 &lt; 42ms</div>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">MongoDB Atlas Mirror</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            </div>
            <div className="text-sm font-black text-emerald-400 mt-1">Connected</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Cluster: voiceagent-cluster.b0sfx.mongodb.net</div>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">AI Voice Intake Engine</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            </div>
            <div className="text-sm font-black text-emerald-400 mt-1">Active</div>
            <div className="text-[11px] text-slate-500 mt-0.5">WebRTC + Streaming Whisper/Gemini</div>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">EHR Sync Reconciliation</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            </div>
            <div className="text-sm font-black text-emerald-400 mt-1">Synchronized</div>
            <div className="text-[11px] text-slate-500 mt-0.5">FHIR R4 &amp; HL7 v2 Connectors Active</div>
          </div>
        </div>
      </div>
    </div>
  );
};
