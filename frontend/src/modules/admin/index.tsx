import React, { useState, useEffect } from 'react';
import {
  Activity,
  CheckCircle2,
  Lock,
  DollarSign,
  ShieldAlert,
  Database,
  Building2,
  Users,
  Layers,
  PlusCircle,
  LayoutDashboard,
  Brain,
  Network,
  GitBranch,
  BarChart3,
  Server
} from 'lucide-react';
import { PlatformAdminOverview } from './PlatformAdminOverview';
import { UserAuthenticationBoard } from './UserAuthenticationBoard';
import { MultiTenantArchitectureBoard } from './MultiTenantArchitectureBoard';
import { HospitalRegistrationBoard } from './HospitalRegistrationBoard';
import { HospitalApplicationsBoard } from './HospitalApplicationsBoard';
import { HospitalManagementBoard } from './HospitalManagementBoard';
import { ObservabilityTracer } from './ObservabilityTracer';
import { CanonicalJourneyRunner } from './CanonicalJourneyRunner';
import { AIEvaluationBoard } from './AIEvaluationBoard';
import { ReconciliationBoard } from './ReconciliationBoard';
import { AuditLogViewer } from './AuditLogViewer';
import { MongoDBAtlasInspector } from './MongoDBAtlasInspector';
import { AIActivityBoard } from './AIActivityBoard';
import { EHRActivityBoard } from './EHRActivityBoard';
import { WorkflowActivityBoard } from './WorkflowActivityBoard';
import { OperationalMonitoringBoard } from './OperationalMonitoringBoard';
import { PlatformAnalyticsBoard } from './PlatformAnalyticsBoard';
import { GlobalAppointmentsBoard } from './GlobalAppointmentsBoard';
import { CalendarCheck } from 'lucide-react';
import { apiCall } from '../../api/client';

export type PlatformAdminTab =
  | 'overview'
  | 'appointments'
  | 'ai-activity'
  | 'ehr-activity'
  | 'workflows'
  | 'analytics'
  | 'monitoring'
  | 'audit'
  | 'ai-eval'
  | 'users'
  | 'tenants'
  | 'register'
  | 'approval'
  | 'management'
  | 'telemetry'
  | 'mongodb'
  | 'dod';

interface Props {
  initialTab?: string;
}

export const PlatformAdminPortal: React.FC<Props> = ({ initialTab = 'overview' }) => {
  const getCleanTab = (tab?: string): PlatformAdminTab => {
    if (tab === 'hospitals') return 'approval';
    const validTabs: PlatformAdminTab[] = [
      'overview',
      'appointments',
      'ai-activity',
      'ehr-activity',
      'workflows',
      'analytics',
      'monitoring',
      'audit',
      'ai-eval',
      'users',
      'tenants',
      'register',
      'approval',
      'management',
      'telemetry',
      'mongodb',
      'dod'
    ];
    return validTabs.includes(tab as any) ? (tab as PlatformAdminTab) : 'overview';
  };

  const [activeTab, setActiveTab] = useState<PlatformAdminTab>(getCleanTab(initialTab));
  const [pendingCount, setPendingCount] = useState<number>(0);

  useEffect(() => {
    const fetchPending = async () => {
      try {
        const res = await apiCall('/api/v1/admin/hospitals?status=PENDING');
        if (res.ok && res.data?.counts?.pending !== undefined) {
          setPendingCount(res.data.counts.pending);
        }
      } catch {}
    };
    fetchPending();
  }, [activeTab]);

  useEffect(() => {
    if (initialTab) {
      setActiveTab(getCleanTab(initialTab));
    }
  }, [initialTab]);

  const handleTabChange = (tab: PlatformAdminTab) => {
    setActiveTab(tab);
    window.location.hash = `/admin/${tab}`;
  };

  return (
    <div className="space-y-6">
      {/* Platform Governance Header Strip */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shadow-lg">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center font-black text-lg">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-bold text-amber-400 uppercase tracking-wider">
              Platform Super-Admin &bull; Statewide Governance &amp; Operations Suite
            </div>
            <h2 className="text-xl font-extrabold text-white">Multi-Hospital Command &amp; Control</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Production Environment &bull; Part 5 EHR Workflows &bull; Part 6 Admin Intelligence &bull; Real-Time Data
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold px-3 py-1.5 rounded-xl flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>All Clusters &amp; Connectors Active</span>
          </span>
        </div>
      </div>

      {/* Part 6 Primary Admin Tabs */}
      <div className="flex border-b border-slate-800 bg-slate-900/80 p-1.5 rounded-2xl gap-1 text-xs overflow-x-auto">
        {/* Platform Dashboard */}
        <button
          onClick={() => handleTabChange('overview')}
          className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'overview'
              ? 'bg-amber-500 text-slate-950 shadow-md font-black'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <LayoutDashboard className="w-3.5 h-3.5" />
          <span>Platform Dashboard</span>
        </button>

        {/* Global Appointments & Intake Observability */}
        <button
          onClick={() => handleTabChange('appointments')}
          className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'appointments'
              ? 'bg-teal-600 text-white shadow-md font-black'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <CalendarCheck className="w-3.5 h-3.5" />
          <span>Appointments &amp; Intakes</span>
        </button>

        {/* AI Activity */}
        <button
          onClick={() => handleTabChange('ai-activity')}
          className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'ai-activity'
              ? 'bg-purple-600 text-white shadow-md font-black'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Brain className="w-3.5 h-3.5" />
          <span>AI Activity</span>
        </button>

        {/* EHR Integration Activity */}
        <button
          onClick={() => handleTabChange('ehr-activity')}
          className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'ehr-activity'
              ? 'bg-indigo-600 text-white shadow-md font-black'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Network className="w-3.5 h-3.5" />
          <span>EHR Integration Activity</span>
        </button>

        {/* Workflow Activity */}
        <button
          onClick={() => handleTabChange('workflows')}
          className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'workflows'
              ? 'bg-teal-600 text-white shadow-md font-black'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <GitBranch className="w-3.5 h-3.5" />
          <span>Workflow Activity</span>
        </button>

        {/* Analytics */}
        <button
          onClick={() => handleTabChange('analytics')}
          className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'analytics'
              ? 'bg-blue-600 text-white shadow-md font-black'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          <span>Analytics</span>
        </button>

        {/* Operational Monitoring */}
        <button
          onClick={() => handleTabChange('monitoring')}
          className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'monitoring'
              ? 'bg-cyan-600 text-white shadow-md font-black'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          <span>Operational Monitoring</span>
        </button>

        {/* Audit Trail */}
        <button
          onClick={() => handleTabChange('audit')}
          className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'audit'
              ? 'bg-emerald-600 text-white shadow-md font-black'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Lock className="w-3.5 h-3.5" />
          <span>Audit Trail</span>
        </button>

        {/* AI Evaluation */}
        <button
          onClick={() => handleTabChange('ai-eval')}
          className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'ai-eval'
              ? 'bg-purple-600 text-white shadow-md font-black'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <DollarSign className="w-3.5 h-3.5" />
          <span>AI Evaluation</span>
        </button>

        {/* Separator */}
        <div className="h-6 w-px bg-slate-800 my-auto mx-1" />

        {/* Additional Management Sub-Tabs */}
        <button
          onClick={() => handleTabChange('approval')}
          className={`flex items-center space-x-1.5 px-3 py-2 rounded-xl font-medium transition whitespace-nowrap ${
            activeTab === 'approval'
              ? 'bg-slate-800 text-amber-400 font-bold'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Building2 className="w-3.5 h-3.5" />
          <span>Hospital Approvals</span>
          {pendingCount > 0 && (
            <span className="ml-1 px-1.5 py-0.5 rounded-full text-[10px] bg-amber-400 text-slate-950 font-black animate-pulse">
              {pendingCount}
            </span>
          )}
        </button>

        <button
          onClick={() => handleTabChange('management')}
          className={`flex items-center space-x-1.5 px-3 py-2 rounded-xl font-medium transition whitespace-nowrap ${
            activeTab === 'management'
              ? 'bg-slate-800 text-amber-400 font-bold'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Building2 className="w-3.5 h-3.5" />
          <span>Hospitals</span>
        </button>

        <button
          onClick={() => handleTabChange('users')}
          className={`flex items-center space-x-1.5 px-3 py-2 rounded-xl font-medium transition whitespace-nowrap ${
            activeTab === 'users'
              ? 'bg-slate-800 text-amber-400 font-bold'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Users className="w-3.5 h-3.5" />
          <span>Users</span>
        </button>

        <button
          onClick={() => handleTabChange('tenants')}
          className={`flex items-center space-x-1.5 px-3 py-2 rounded-xl font-medium transition whitespace-nowrap ${
            activeTab === 'tenants'
              ? 'bg-slate-800 text-amber-400 font-bold'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Tenancy</span>
        </button>

        <button
          onClick={() => handleTabChange('mongodb')}
          className={`flex items-center space-x-1.5 px-3 py-2 rounded-xl font-medium transition whitespace-nowrap ${
            activeTab === 'mongodb'
              ? 'bg-slate-800 text-emerald-400 font-bold'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          <span>MongoDB Atlas</span>
        </button>

        <button
          onClick={() => handleTabChange('dod')}
          className={`flex items-center space-x-1.5 px-3 py-2 rounded-xl font-medium transition whitespace-nowrap ${
            activeTab === 'dod'
              ? 'bg-slate-800 text-amber-400 font-bold'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>DoD Runner</span>
        </button>
      </div>

      {/* Content View Switching */}
      <div>
        {activeTab === 'overview' && (
          <PlatformAdminOverview onNavigateTab={handleTabChange} />
        )}

        {activeTab === 'appointments' && <GlobalAppointmentsBoard />}

        {activeTab === 'ai-activity' && <AIActivityBoard />}

        {activeTab === 'ehr-activity' && <EHRActivityBoard />}

        {activeTab === 'workflows' && <WorkflowActivityBoard />}

        {activeTab === 'analytics' && <PlatformAnalyticsBoard />}

        {activeTab === 'monitoring' && <OperationalMonitoringBoard />}

        {activeTab === 'audit' && <AuditLogViewer />}

        {activeTab === 'ai-eval' && <AIEvaluationBoard />}

        {activeTab === 'users' && <UserAuthenticationBoard />}

        {activeTab === 'tenants' && <MultiTenantArchitectureBoard />}

        {activeTab === 'register' && (
          <HospitalRegistrationBoard onSuccess={() => handleTabChange('approval')} />
        )}

        {activeTab === 'approval' && <HospitalApplicationsBoard />}

        {activeTab === 'management' && <HospitalManagementBoard />}

        {activeTab === 'telemetry' && <ObservabilityTracer />}

        {activeTab === 'mongodb' && <MongoDBAtlasInspector />}

        {activeTab === 'dod' && <CanonicalJourneyRunner />}
      </div>
    </div>
  );
};
