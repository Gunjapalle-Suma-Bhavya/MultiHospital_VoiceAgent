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
  LayoutDashboard
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
import { apiCall } from '../../api/client';

export type PlatformAdminTab =
  | 'overview'
  | 'users'
  | 'tenants'
  | 'register'
  | 'approval'
  | 'management'
  | 'telemetry'
  | 'mongodb'
  | 'dod'
  | 'audit'
  | 'ai-eval';

interface Props {
  initialTab?: string;
}

export const PlatformAdminPortal: React.FC<Props> = ({ initialTab = 'overview' }) => {
  const getCleanTab = (tab?: string): PlatformAdminTab => {
    if (tab === 'hospitals') return 'approval';
    const validTabs: PlatformAdminTab[] = [
      'overview',
      'users',
      'tenants',
      'register',
      'approval',
      'management',
      'telemetry',
      'mongodb',
      'dod',
      'audit',
      'ai-eval'
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
              Platform Super-Admin &bull; Statewide Governance Suite
            </div>
            <h2 className="text-xl font-extrabold text-white">Multi-Hospital Command &amp; Control</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Production Environment &bull; Tenant Isolation &bull; RBAC &bull; MongoDB Atlas Cloud Mirror Active
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold px-3 py-1.5 rounded-xl flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>All Clusters Operational</span>
          </span>
        </div>
      </div>

      {/* Role-Scoped Navigation Tabs matching user requirements */}
      <div className="flex border-b border-slate-800 bg-slate-900/60 p-1.5 rounded-2xl gap-1 text-xs overflow-x-auto">
        {/* 1. Platform Admin */}
        <button
          onClick={() => handleTabChange('overview')}
          className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'overview'
              ? 'bg-amber-500 text-slate-950 shadow-md font-black'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <LayoutDashboard className="w-3.5 h-3.5" />
          <span>Platform Admin</span>
        </button>

        {/* 2. User Authentication */}
        <button
          onClick={() => handleTabChange('users')}
          className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'users'
              ? 'bg-amber-500 text-slate-950 shadow-md font-black'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Users className="w-3.5 h-3.5" />
          <span>User Authentication</span>
        </button>

        {/* 3. Multi-Tenant Architecture */}
        <button
          onClick={() => handleTabChange('tenants')}
          className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'tenants'
              ? 'bg-amber-500 text-slate-950 shadow-md font-black'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Multi-Tenant Architecture</span>
        </button>

        {/* 4. Hospital Registration */}
        <button
          onClick={() => handleTabChange('register')}
          className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'register'
              ? 'bg-amber-500 text-slate-950 shadow-md font-black'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <PlusCircle className="w-3.5 h-3.5" />
          <span>Hospital Registration</span>
        </button>

        {/* 5. Hospital Approval */}
        <button
          onClick={() => handleTabChange('approval')}
          className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'approval'
              ? 'bg-amber-500 text-slate-950 shadow-md font-black'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Building2 className="w-3.5 h-3.5" />
          <span>Hospital Approval</span>
          {pendingCount > 0 && (
            <span className="ml-1 px-1.5 py-0.5 rounded-full text-[10px] bg-amber-400 text-slate-950 font-black animate-pulse">
              {pendingCount}
            </span>
          )}
        </button>

        {/* 6. Hospital Management */}
        <button
          onClick={() => handleTabChange('management')}
          className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'management'
              ? 'bg-amber-500 text-slate-950 shadow-md font-black'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Building2 className="w-3.5 h-3.5" />
          <span>Hospital Management</span>
        </button>

        {/* Separator */}
        <div className="h-6 w-px bg-slate-800 my-auto mx-1" />

        {/* Extended SRE & Operations Suite */}
        <button
          onClick={() => handleTabChange('telemetry')}
          className={`flex items-center space-x-1.5 px-3 py-2 rounded-xl font-medium transition whitespace-nowrap ${
            activeTab === 'telemetry'
              ? 'bg-slate-800 text-amber-400 font-bold'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          <span>SRE Telemetry</span>
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

        <button
          onClick={() => handleTabChange('audit')}
          className={`flex items-center space-x-1.5 px-3 py-2 rounded-xl font-medium transition whitespace-nowrap ${
            activeTab === 'audit'
              ? 'bg-slate-800 text-amber-400 font-bold'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Lock className="w-3.5 h-3.5" />
          <span>Audit Trail</span>
        </button>

        <button
          onClick={() => handleTabChange('ai-eval')}
          className={`flex items-center space-x-1.5 px-3 py-2 rounded-xl font-medium transition whitespace-nowrap ${
            activeTab === 'ai-eval'
              ? 'bg-slate-800 text-amber-400 font-bold'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <DollarSign className="w-3.5 h-3.5" />
          <span>AI Evaluation</span>
        </button>
      </div>

      {/* Sub-Page Content Routing */}
      <div>
        {activeTab === 'overview' && (
          <PlatformAdminOverview onNavigateTab={handleTabChange} />
        )}

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

        {activeTab === 'audit' && <AuditLogViewer />}

        {activeTab === 'ai-eval' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-6">
              <AIEvaluationBoard />
            </div>
            <div className="lg:col-span-6">
              <ReconciliationBoard />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
