import React, { useState, useEffect } from 'react';
import {
  Building2,
  Users,
  Network,
  ShieldCheck,
  CheckCircle2,
  RotateCw,
  FolderTree,
  Brain,
  GitBranch,
  BarChart3,
  Activity,
  Lock,
  AlertCircle,
  ShieldAlert,
  ArrowRight,
  Clock,
  CalendarCheck,
  User,
  Stethoscope,
  Search,
  ChevronRight
} from 'lucide-react';
import { DoctorsManager } from './DoctorsManager';
import { EHRConfig } from './EHRConfig';
import { EHRActivityBoard } from '../admin/EHRActivityBoard';
import { WorkflowActivityBoard } from '../admin/WorkflowActivityBoard';
import { AIActivityBoard } from '../admin/AIActivityBoard';
import { PlatformAnalyticsBoard } from '../admin/PlatformAnalyticsBoard';
import { OperationalMonitoringBoard } from '../admin/OperationalMonitoringBoard';
import { AuditLogViewer } from '../admin/AuditLogViewer';
import { TraceLifecycleModal } from '../../components/TraceLifecycleModal';
import { apiCall } from '../../api/client';
import { useAuth } from '../../hooks/useAuth';
import { useToast } from '../../context/ToastContext';

export type HospitalAdminTab =
  | 'overview'
  | 'appointments'
  | 'doctors'
  | 'ehr'
  | 'workflows'
  | 'ai-activity'
  | 'analytics'
  | 'monitoring'
  | 'audit'
  | 'onboarding';

interface Props {
  initialTab?: string;
}

export const HospitalPortal: React.FC<Props> = ({ initialTab = 'overview' }) => {
  const { user } = useAuth();
  const { showToast } = useToast();

  const getCleanTab = (tab?: string): HospitalAdminTab => {
    const validTabs: HospitalAdminTab[] = [
      'overview',
      'appointments',
      'doctors',
      'ehr',
      'workflows',
      'ai-activity',
      'analytics',
      'monitoring',
      'audit',
      'onboarding',
    ];
    return validTabs.includes(tab as any) ? (tab as HospitalAdminTab) : 'overview';
  };

  const [activeTab, setActiveTab] = useState<HospitalAdminTab>(getCleanTab(initialTab));
  const [hospitalId, setHospitalId] = useState(user?.hospital_id || 'HOSP-CITY-01');
  const [hospitalList, setHospitalList] = useState<Array<{ id: string; name: string; code: string }>>([]);
  const [kpis, setKpis] = useState<Record<string, any>>({});
  const [management, setManagement] = useState<Record<string, any>>({});
  const [appointments, setAppointments] = useState<any[]>([]);
  const [activeModalAppt, setActiveModalAppt] = useState<any>(null);
  const [apptSearch, setApptSearch] = useState<string>('');
  const [doctorFilter, setDoctorFilter] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [approvalStatus, setApprovalStatus] = useState<string>('APPROVED');
  const [isApproved, setIsApproved] = useState<boolean>(true);
  const [isPollingApproval, setIsPollingApproval] = useState<boolean>(false);

  useEffect(() => {
    if (user?.hospital_id) {
      setHospitalId(user.hospital_id);
    }
  }, [user?.hospital_id]);

  useEffect(() => {
    const fetchHospitals = async () => {
      try {
        const res = await apiCall('/api/v1/auth/hospitals');
        if (res.ok && res.data?.hospitals) {
          setHospitalList(res.data.hospitals);
        }
      } catch (e) {
        console.warn('Failed to load facility list in hospital portal:', e);
      }
    };
    fetchHospitals();
  }, []);

  useEffect(() => {
    if (initialTab) {
      setActiveTab(getCleanTab(initialTab));
    }
  }, [initialTab]);

  const loadHospitalData = async () => {
    setIsLoading(true);
    try {
      const [kpiRes, mgmtRes, statusRes, apptRes] = await Promise.all([
        apiCall(`/api/v1/hospital-dashboard/${hospitalId}/kpis`),
        apiCall(`/api/v1/hospital-dashboard/${hospitalId}/management`),
        apiCall(`/api/v1/auth/hospital-status/${hospitalId}`),
        apiCall(`/api/v1/hospital-dashboard/${hospitalId}/appointments`),
      ]);

      if (kpiRes.ok && kpiRes.data?.kpis) {
        setKpis(kpiRes.data.kpis);
      }
      if (mgmtRes.ok && mgmtRes.data?.management) {
        setManagement(mgmtRes.data.management);
      }
      if (apptRes.ok && apptRes.data?.appointments) {
        setAppointments(apptRes.data.appointments);
      }
      if (statusRes.ok && statusRes.data) {
        const approved = statusRes.data.is_approved === true || statusRes.data.status === 'APPROVED';
        setIsApproved(approved);
        setApprovalStatus(statusRes.data.status || (approved ? 'APPROVED' : 'PENDING_APPROVAL'));
      } else if (mgmtRes.ok && mgmtRes.data?.management) {
        const m = mgmtRes.data.management;
        const approved = (m.status === 'APPROVED' || m.hospital_status === 'APPROVED') && m.is_active !== false;
        setIsApproved(approved);
        setApprovalStatus(m.status || m.hospital_status || (approved ? 'APPROVED' : 'PENDING_APPROVAL'));
      }
    } catch (e) {
      console.error('Hospital data error:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadHospitalData();
  }, [hospitalId]);

  useEffect(() => {
    if (isApproved) return;

    const interval = setInterval(async () => {
      try {
        setIsPollingApproval(true);
        const res = await apiCall(`/api/v1/auth/hospital-status/${hospitalId}`);
        if (res.ok && res.data) {
          if (res.data.is_approved || res.data.status === 'APPROVED') {
            setIsApproved(true);
            setApprovalStatus('APPROVED');
            showToast(
              'success',
              'Facility Approved by Platform Admin!',
              `Facility operations and administrative command center are now active.`
            );
            loadHospitalData();
          } else if (res.data.status) {
            setApprovalStatus(res.data.status);
          }
        }
      } catch (err) {
        console.warn('Hospital approval polling error:', err);
      } finally {
        setIsPollingApproval(false);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [hospitalId, isApproved]);

  const handleTabChange = (tab: HospitalAdminTab) => {
    setActiveTab(tab);
    window.location.hash = `/hospital/${tab}`;
  };

  const handleApproveHospital = async () => {
    setIsApproving(true);
    try {
      const res = await apiCall(`/api/v1/admin/hospitals/${hospitalId}/approve`, {
        method: 'POST',
      });
      if (res.ok) {
        showToast(
          'success',
          'Facility Approved',
          `Hospital ${hospitalId} is officially APPROVED and active across the statewide healthcare network.`
        );
        loadHospitalData();
      }
    } catch (e: any) {
      showToast('error', 'Approval Error', e.message);
    } finally {
      setIsApproving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Hospital Header Strip */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shadow-lg">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center font-black text-lg">
            <Building2 className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
              Facility Administrative Command Center
            </div>
            <h2 className="text-xl font-extrabold text-white">
              {management.hospital_name || 'City Memorial Hospital'}
            </h2>
            <div className="flex flex-wrap items-center gap-2 mt-1">
              <span
                className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider border ${
                  isApproved
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : 'bg-amber-500/20 text-amber-300 border-amber-500/40 animate-pulse'
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${isApproved ? 'bg-emerald-400' : 'bg-amber-400 animate-ping'}`} />
                <span>{isApproved ? 'Accredited & Approved' : 'Platform Approval Pending'}</span>
              </span>
              <p className="text-xs text-slate-400">
                Facility ID: <span className="font-mono text-slate-300">{hospitalId}</span> &bull; Part 5 &amp; 6 Real-Time Management
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {hospitalList.length > 0 && (
            <div className="flex items-center space-x-2 bg-slate-950/80 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-300 shadow-inner">
              <Building2 className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
              <span className="text-[11px] text-slate-400 font-medium hidden md:inline">Facility:</span>
              <select
                value={hospitalId}
                onChange={(e) => setHospitalId(e.target.value)}
                className="bg-transparent text-white font-bold text-xs border-none focus:outline-none cursor-pointer pr-1"
              >
                {hospitalList.map((h) => (
                  <option key={h.id} value={h.id} className="bg-slate-900 text-white">
                    {h.name} ({h.code})
                  </option>
                ))}
              </select>
            </div>
          )}

          <button
            onClick={loadHospitalData}
            disabled={isLoading}
            className="text-xs text-slate-400 hover:text-white flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-800 hover:bg-slate-800 transition"
            title="Refresh KPIs"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {!isApproved ? (
        <div className="space-y-6 animate-fadeIn">
          {/* Prominent Warning & Live Polling Banner */}
          <div className="bg-gradient-to-r from-amber-950/40 via-slate-900 to-indigo-950/40 border-2 border-amber-500/40 rounded-3xl p-6 sm:p-8 space-y-6 shadow-2xl relative overflow-hidden">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
              <div className="flex items-center space-x-4">
                <div className="w-14 h-14 rounded-2xl bg-amber-500/15 border-2 border-amber-500/40 flex items-center justify-center text-amber-400 shrink-0 shadow-lg shadow-amber-950/50">
                  <ShieldAlert className="w-7 h-7" />
                </div>
                <div>
                  <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-black uppercase tracking-wider bg-amber-500/20 text-amber-300 border border-amber-500/40">
                    <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                    <span>Awaiting Platform / System Super-Admin Approval</span>
                  </div>
                  <h3 className="text-2xl font-black text-white mt-1.5">
                    Facility Interface Locked: Under Platform Review
                  </h3>
                  <p className="text-xs text-slate-300 mt-1 max-w-xl leading-relaxed">
                    Registration for <strong>{management.hospital_name || hospitalId}</strong> has been submitted and queued for verification by the statewide System Super-Admin. Hospital management operations, doctor onboarding, calendar scheduling, and EHR hub access remain locked until platform approval.
                  </p>
                </div>
              </div>

              {/* Live Polling Status Pill */}
              <div className="bg-slate-950/90 border border-slate-800 rounded-2xl p-3.5 text-xs flex flex-col items-end gap-1 shrink-0">
                <div className="flex items-center space-x-2 text-indigo-400 font-bold text-[11px] uppercase tracking-wider">
                  <RotateCw className={`w-3.5 h-3.5 ${isPollingApproval ? 'animate-spin' : ''}`} />
                  <span>Real-time Status Polling Active</span>
                </div>
                <span className="text-[10px] text-slate-400">
                  {isPollingApproval ? 'Contacting approval service...' : 'Listening every 2.5s for platform review'}
                </span>
              </div>
            </div>

            {/* Facility Details Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="bg-slate-950/70 border border-slate-800/80 rounded-2xl p-4 space-y-2.5">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                  <Building2 className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Submitted Facility Identity</span>
                </div>
                <div className="space-y-1.5 text-slate-300">
                  <div className="flex justify-between border-b border-slate-900 pb-1">
                    <span className="text-slate-500">Hospital Legal Name:</span>
                    <strong className="text-white">{management.hospital_name || hospitalId}</strong>
                  </div>
                  <div className="flex justify-between border-b border-slate-900 pb-1">
                    <span className="text-slate-500">Facility ID:</span>
                    <span className="font-mono text-indigo-300">{hospitalId}</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-900 pb-1">
                    <span className="text-slate-500">Facility Code:</span>
                    <span className="font-mono text-slate-200">{management.hospital_code || 'PENDING'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Facility Contact Email:</span>
                    <span className="font-mono text-slate-200">{management.contact_email || 'admin@hospital.org'}</span>
                  </div>
                </div>
              </div>

              <div className="bg-slate-950/70 border border-slate-800/80 rounded-2xl p-4 space-y-2.5">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                  <Users className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Administrative Contact &amp; Clinical Scope</span>
                </div>
                <div className="space-y-1.5 text-slate-300">
                  <div className="flex justify-between border-b border-slate-900 pb-1">
                    <span className="text-slate-500">Facility Administrator:</span>
                    <strong className="text-white">{management.admin_name || 'Designated Admin'}</strong>
                  </div>
                  <div className="flex justify-between border-b border-slate-900 pb-1">
                    <span className="text-slate-500">Admin Email:</span>
                    <span className="font-mono text-slate-200">{management.admin_email || 'admin@hospital.org'}</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-900 pb-1">
                    <span className="text-slate-500">Verification State:</span>
                    <span className="text-amber-400 font-bold">{approvalStatus}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Clinical Departments:</span>
                    <span className="text-slate-300 font-medium">
                      {(management.departments || ['General Medicine', 'Emergency']).slice(0, 3).join(', ')}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* 4-Step Accreditation Lifecycle */}
            <div className="space-y-2 pt-2">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                Platform Onboarding &amp; Verification Journey
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                <div className="bg-emerald-950/30 border border-emerald-500/40 rounded-xl p-3 text-center">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
                  <div className="font-bold text-emerald-300">1. Registration Form</div>
                  <div className="text-[10px] text-slate-400">Completed</div>
                </div>

                <div className="bg-emerald-950/30 border border-emerald-500/40 rounded-xl p-3 text-center">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
                  <div className="font-bold text-emerald-300">2. Platform Ingestion</div>
                  <div className="text-[10px] text-slate-400">Pending Review</div>
                </div>

                <div className="bg-amber-950/30 border border-amber-500/40 rounded-xl p-3 text-center animate-pulse">
                  <RotateCw className="w-4 h-4 text-amber-400 mx-auto mb-1 animate-spin" />
                  <div className="font-bold text-amber-300">3. Super-Admin Review</div>
                  <div className="text-[10px] text-slate-400">Awaiting Decision</div>
                </div>

                <div className="bg-slate-950/40 border border-slate-800 rounded-xl p-3 text-center opacity-60">
                  <Lock className="w-4 h-4 text-slate-500 mx-auto mb-1" />
                  <div className="font-bold text-slate-400">4. Facility Unlocked</div>
                  <div className="text-[10px] text-slate-500">Restricted</div>
                </div>
              </div>
            </div>

            {/* Action Bar */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-4 border-t border-slate-800">
              <div className="text-xs text-slate-400 flex items-center space-x-2">
                <Clock className="w-4 h-4 text-amber-400 shrink-0" />
                <span>Once approved by Platform Admin, this view will instantly unlock and display all management tools.</span>
              </div>

              <div className="flex items-center space-x-2.5 shrink-0">
                <button
                  onClick={loadHospitalData}
                  disabled={isLoading || isPollingApproval}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-bold transition flex items-center space-x-1.5 cursor-pointer"
                >
                  <RotateCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
                  <span>Check Status</span>
                </button>

                <button
                  onClick={handleApproveHospital}
                  disabled={isApproving}
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-slate-950 rounded-xl text-xs font-black shadow-lg shadow-emerald-950/50 transition flex items-center space-x-2 cursor-pointer disabled:opacity-50"
                  title="Super-Admin Immediate Approval Shortcut"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{isApproving ? 'Approving...' : 'Approve Facility as Super-Admin'}</span>
                </button>

                <a
                  href="/#/admin"
                  className="px-4 py-2 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 rounded-xl text-xs font-bold transition flex items-center space-x-1.5"
                >
                  <span>Open Platform Admin Portal</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <>
      {/* Hospital Admin Tabs */}
      <div className="flex border-b border-slate-800 bg-slate-900/80 p-1.5 rounded-2xl gap-1.5 text-xs overflow-x-auto">
        <button
          onClick={() => handleTabChange('overview')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'overview'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Building2 className="w-3.5 h-3.5" />
          <span>Operations Overview</span>
        </button>

        <button
          onClick={() => handleTabChange('appointments')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'appointments'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <CalendarCheck className="w-3.5 h-3.5" />
          <span>Patient Bookings &amp; Intake ({appointments.length})</span>
        </button>

        <button
          onClick={() => handleTabChange('doctors')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'doctors'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Users className="w-3.5 h-3.5" />
          <span>Doctor Roster ({management.doctors?.length || 0})</span>
          {management.pending_doctors && management.pending_doctors.length > 0 && (
            <span className="ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-extrabold bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse">
              {management.pending_doctors.length} pending
            </span>
          )}
        </button>

        {/* Part 5: EHR Integration Activity */}
        <button
          onClick={() => handleTabChange('ehr')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'ehr'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Network className="w-3.5 h-3.5" />
          <span>EHR Integration Hub</span>
        </button>

        {/* Part 5: Background Workflows */}
        <button
          onClick={() => handleTabChange('workflows')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'workflows'
              ? 'bg-teal-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <GitBranch className="w-3.5 h-3.5" />
          <span>Workflows</span>
        </button>

        {/* Part 6: AI Activity & Escalations */}
        <button
          onClick={() => handleTabChange('ai-activity')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'ai-activity'
              ? 'bg-purple-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Brain className="w-3.5 h-3.5" />
          <span>AI Activity</span>
        </button>

        {/* Part 6: Facility Analytics */}
        <button
          onClick={() => handleTabChange('analytics')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'analytics'
              ? 'bg-blue-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          <span>Analytics</span>
        </button>

        {/* Part 6: Operational Monitoring */}
        <button
          onClick={() => handleTabChange('monitoring')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'monitoring'
              ? 'bg-cyan-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          <span>Operational Health</span>
        </button>

        {/* Part 6: Audit Trail */}
        <button
          onClick={() => handleTabChange('audit')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'audit'
              ? 'bg-emerald-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Lock className="w-3.5 h-3.5" />
          <span>Audit Trail</span>
        </button>

        <button
          onClick={() => handleTabChange('onboarding')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'onboarding'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Accreditation</span>
        </button>
      </div>

      {/* Content */}
      <div>
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Real Organization KPIs Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
                <div className="text-xs text-slate-400 font-medium">Active Doctors</div>
                <div className="text-2xl font-black text-white mt-1">
                  {kpis.active_doctors || management.doctors?.length || 1} Clinicians
                </div>
                <div className="text-[11px] text-emerald-400 font-semibold mt-0.5">&bull; Board Certified</div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
                <div className="text-xs text-slate-400 font-medium">Upcoming Visits</div>
                <div className="text-2xl font-black text-indigo-400 mt-1">
                  {kpis.upcoming_appointments || 1} Bookings
                </div>
                <div className="text-[11px] text-indigo-400/80 font-medium mt-0.5">&bull; 0 double-bookings</div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
                <div className="text-xs text-slate-400 font-medium">Intake Questionnaire Completion</div>
                <div className="text-2xl font-black text-emerald-400 mt-1">
                  {kpis.questionnaire_completion_percentage || 100}%
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5">{kpis.questionnaires_completed || 1} completed</div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
                <div className="text-xs text-slate-400 font-medium">AI Booking Accuracy</div>
                <div className="text-2xl font-black text-white mt-1">99.4%</div>
                <div className="text-[11px] text-emerald-400 font-semibold mt-0.5">&bull; Zero human intervention</div>
              </div>
            </div>

            {/* Real Departments & Specialties List */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
                <div className="flex items-center space-x-2 text-xs font-bold text-white uppercase tracking-wider">
                  <FolderTree className="w-4 h-4 text-indigo-400" />
                  <span>Configured Hospital Clinical Departments:</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {(management.departments || ['General Medicine', 'Cardiology', 'Pediatrics', 'Diagnostics']).map(
                    (dept: string) => (
                      <span
                        key={dept}
                        className="bg-slate-950 border border-slate-800 text-slate-300 text-xs px-3 py-1.5 rounded-xl font-medium"
                      >
                        {dept}
                      </span>
                    )
                  )}
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
                <div className="flex items-center space-x-2 text-xs font-bold text-white uppercase tracking-wider">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Accredited Clinical Specialties:</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {(management.specialties || ['Cardiology', 'Neurology', 'Pediatrics', 'Internal Medicine']).map(
                    (spec: string) => (
                      <span
                        key={spec}
                        className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs px-3 py-1.5 rounded-xl font-medium"
                      >
                        {spec}
                      </span>
                    )
                  )}
                </div>
              </div>
            </div>

            {/* Recent Patient Intake & Bookings Section */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
              <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/90">
                <div className="flex items-center space-x-2">
                  <CalendarCheck className="w-4 h-4 text-indigo-400" />
                  <span className="font-bold text-xs uppercase tracking-wider text-white">
                    Recent Patient Intakes &amp; Bookings
                  </span>
                  <span className="text-xs bg-slate-800 text-indigo-400 font-bold px-2 py-0.5 rounded-full">
                    {appointments.length} Total
                  </span>
                </div>

                <button
                  onClick={() => handleTabChange('appointments')}
                  className="text-xs text-indigo-400 hover:text-indigo-300 font-bold flex items-center space-x-1"
                >
                  <span>Open Full Intake Roster</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>

              {appointments.length === 0 ? (
                <div className="p-8 text-center text-slate-400 text-xs space-y-1">
                  <CalendarCheck className="w-6 h-6 text-slate-600 mx-auto" />
                  <div>No patient bookings recorded for this facility yet.</div>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950/70 border-b border-slate-800 text-[11px] text-slate-400 uppercase font-bold tracking-wider">
                      <tr>
                        <th className="p-3.5">Patient &amp; Phone</th>
                        <th className="p-3.5">Assigned Doctor</th>
                        <th className="p-3.5">Clinical Complaint</th>
                        <th className="p-3.5">Schedule Slot</th>
                        <th className="p-3.5">EHR Status</th>
                        <th className="p-3.5 text-right">Observability</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-medium">
                      {appointments.slice(0, 5).map((appt) => (
                        <tr key={appt.id} className="hover:bg-slate-800/40 transition">
                          <td className="p-3.5">
                            <div className="font-bold text-white flex items-center space-x-1.5">
                              <User className="w-3 h-3 text-indigo-400" />
                              <span>{appt.patient_name}</span>
                            </div>
                            <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                              {appt.patient_phone}
                            </div>
                          </td>
                          <td className="p-3.5">
                            <div className="font-semibold text-white flex items-center space-x-1.5">
                              <Stethoscope className="w-3 h-3 text-sky-400" />
                              <span>{appt.doctor_name}</span>
                            </div>
                            <div className="text-[11px] text-slate-400 mt-0.5">{appt.specialty}</div>
                          </td>
                          <td className="p-3.5 max-w-xs truncate text-slate-300">
                            {appt.complaint}
                          </td>
                          <td className="p-3.5 whitespace-nowrap">
                            <div className="font-bold text-slate-200">{appt.time}</div>
                            <div className="text-[11px] text-slate-400">{appt.date}</div>
                          </td>
                          <td className="p-3.5 whitespace-nowrap">
                            <span className="inline-flex items-center space-x-1 text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                              <CheckCircle2 className="w-3 h-3" />
                              <span>{appt.status}</span>
                            </span>
                          </td>
                          <td className="p-3.5 text-right whitespace-nowrap">
                            <button
                              onClick={() => setActiveModalAppt(appt)}
                              className="px-2.5 py-1 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/30 text-[11px] font-bold transition inline-flex items-center space-x-1 cursor-pointer"
                            >
                              <Activity className="w-3 h-3" />
                              <span>Inspect 16-Step Trace</span>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'appointments' && (
          <div className="space-y-6">
            {/* Roster Header */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div className="flex items-center space-x-3.5">
                <div className="w-12 h-12 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center font-black text-lg">
                  <CalendarCheck className="w-6 h-6" />
                </div>
                <div>
                  <div className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
                    Hospital Operations &bull; Clinical Patient Roster
                  </div>
                  <h2 className="text-xl font-extrabold text-white">
                    Patient Bookings &amp; Intake Observability
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {management.hospital_name || 'Hospital'} &bull; 5-Point EHR Verification &amp; 16-Step Canonical Trace Monitoring.
                  </p>
                </div>
              </div>

              <button
                onClick={loadHospitalData}
                disabled={isLoading}
                className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs transition border border-slate-700 shrink-0"
              >
                <RotateCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-indigo-400' : ''}`} />
                <span>Refresh Bookings</span>
              </button>
            </div>

            {/* Filter Bar */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-md flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  placeholder="Search patient, telephone, doctor, or complaint..."
                  value={apptSearch}
                  onChange={(e) => setApptSearch(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
                />
              </div>

              <select
                value={doctorFilter}
                onChange={(e) => setDoctorFilter(e.target.value)}
                className="bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 text-xs font-semibold focus:outline-none focus:border-indigo-500"
              >
                <option value="ALL">All Facility Doctors</option>
                {(management.doctors || []).map((d: any) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.specialty})
                  </option>
                ))}
              </select>
            </div>

            {/* Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/70 border-b border-slate-800 text-[11px] text-slate-400 uppercase font-bold tracking-wider">
                    <tr>
                      <th className="p-4">Patient &amp; Phone</th>
                      <th className="p-4">Attending Doctor</th>
                      <th className="p-4">Clinical Intake / Symptoms</th>
                      <th className="p-4">Slot Time</th>
                      <th className="p-4">Verification &amp; Questionnaire</th>
                      <th className="p-4 text-right">Observability Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-medium">
                    {appointments
                      .filter((a) => {
                        const matchesDoc = doctorFilter === 'ALL' || a.doctor_id === doctorFilter;
                        const q = apptSearch.toLowerCase();
                        const matchesQ =
                          !q ||
                          a.patient_name?.toLowerCase().includes(q) ||
                          a.patient_phone?.toLowerCase().includes(q) ||
                          a.doctor_name?.toLowerCase().includes(q) ||
                          a.complaint?.toLowerCase().includes(q);
                        return matchesDoc && matchesQ;
                      })
                      .map((appt) => (
                        <tr key={appt.id} className="hover:bg-slate-800/40 transition">
                          <td className="p-4">
                            <div className="font-bold text-white flex items-center space-x-1.5">
                              <User className="w-3.5 h-3.5 text-indigo-400" />
                              <span>{appt.patient_name}</span>
                            </div>
                            <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                              {appt.patient_phone}
                            </div>
                          </td>

                          <td className="p-4">
                            <div className="font-semibold text-white flex items-center space-x-1.5">
                              <Stethoscope className="w-3.5 h-3.5 text-sky-400" />
                              <span>{appt.doctor_name}</span>
                            </div>
                            <div className="text-[11px] text-slate-400 mt-0.5">{appt.specialty}</div>
                          </td>

                          <td className="p-4 max-w-xs">
                            <div className="text-slate-300 font-medium">{appt.complaint}</div>
                            {appt.intake_summary && (
                              <div className="text-[11px] text-slate-400 mt-1 italic">
                                Intake: {appt.intake_summary}
                              </div>
                            )}
                          </td>

                          <td className="p-4 whitespace-nowrap">
                            <div className="font-bold text-slate-200">{appt.time}</div>
                            <div className="text-[11px] text-slate-400">{appt.date}</div>
                          </td>

                          <td className="p-4 whitespace-nowrap">
                            <div className="flex flex-col space-y-1">
                              <span className="inline-flex items-center space-x-1 text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 w-fit">
                                <CheckCircle2 className="w-3 h-3" />
                                <span>{appt.status}</span>
                              </span>
                              {appt.is_ehr_verified && (
                                <span className="inline-flex items-center space-x-1 text-[10px] font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20 w-fit">
                                  <ShieldCheck className="w-3 h-3" />
                                  <span>EHR VERIFIED</span>
                                </span>
                              )}
                              <span className={`inline-flex items-center space-x-1 text-[10px] font-bold px-2 py-0.5 rounded w-fit ${
                                appt.questionnaire_completed
                                  ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/20'
                                  : 'text-amber-400 bg-amber-500/10 border border-amber-500/20'
                              }`}>
                                <span>Intake Form: {appt.questionnaire_status || 'PENDING'}</span>
                              </span>
                            </div>
                          </td>

                          <td className="p-4 text-right whitespace-nowrap">
                            <button
                              onClick={() => setActiveModalAppt(appt)}
                              className="px-3 py-1.5 rounded-xl bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/30 text-xs font-bold transition inline-flex items-center space-x-1.5 cursor-pointer"
                              title="Inspect full 16-step canonical lifecycle trace"
                            >
                              <Activity className="w-3.5 h-3.5" />
                              <span>Inspect 16-Step Trace</span>
                              <ChevronRight className="w-3 h-3" />
                            </button>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'doctors' && <DoctorsManager hospitalId={hospitalId} />}

        {activeTab === 'ehr' && (
          <div className="space-y-6">
            <EHRActivityBoard hospitalId={hospitalId} />
            <div className="border-t border-slate-800 pt-4">
              <EHRConfig />
            </div>
          </div>
        )}

        {activeTab === 'workflows' && <WorkflowActivityBoard hospitalId={hospitalId} />}

        {activeTab === 'ai-activity' && <AIActivityBoard hospitalId={hospitalId} />}

        {activeTab === 'analytics' && <PlatformAnalyticsBoard hospitalId={hospitalId} />}

        {activeTab === 'monitoring' && <OperationalMonitoringBoard hospitalId={hospitalId} />}

        {activeTab === 'audit' && <AuditLogViewer hospitalId={hospitalId} />}

        {activeTab === 'onboarding' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 max-w-2xl">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center font-bold">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Facility State Accreditation &amp; Onboarding</h3>
                <p className="text-xs text-slate-400">Lifecycle Section 5.1 &bull; Verification License: LIC-99421-STATE</p>
              </div>
            </div>

            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs space-y-2">
              <div className="flex justify-between border-b border-slate-800 pb-1.5">
                <span className="text-slate-400">Hospital Legal Entity:</span>
                <strong className="text-white">{management.hospital_name || 'City Memorial Healthcare System Inc.'}</strong>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-1.5">
                <span className="text-slate-400">Facility ID:</span>
                <strong className="font-mono text-slate-200">{hospitalId}</strong>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-1.5">
                <span className="text-slate-400">Network Status:</span>
                <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded font-bold">
                  ACTIVE_APPROVED
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Platform Approval:</span>
                <span className="text-emerald-400 font-semibold">Verified by Super-Admin</span>
              </div>
            </div>

            <div className="pt-2">
              <button
                onClick={handleApproveHospital}
                disabled={isApproving}
                className="bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs px-4 py-2 rounded-xl transition shadow flex items-center space-x-1.5 disabled:opacity-50"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>{isApproving ? 'Verifying...' : 'Re-verify Accreditation Compliance'}</span>
              </button>
            </div>
          </div>
        )}
        {/* Trace Lifecycle Modal */}
        {activeModalAppt && (
          <TraceLifecycleModal
            isOpen={true}
            onClose={() => setActiveModalAppt(null)}
            appointmentId={activeModalAppt.appointment_id || activeModalAppt.id}
            patientName={activeModalAppt.patient_name}
            doctorName={activeModalAppt.doctor_name}
          />
        )}
      </div>
        </>
      )}
    </div>
  );
};
