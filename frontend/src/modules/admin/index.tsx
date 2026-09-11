import React, { useState, useEffect } from 'react';
import {
  Activity,
  CheckCircle2,
  Lock,
  DollarSign,
  ShieldAlert,
  Database,
} from 'lucide-react';
import { ObservabilityTracer } from './ObservabilityTracer';
import { CanonicalJourneyRunner } from './CanonicalJourneyRunner';
import { AIEvaluationBoard } from './AIEvaluationBoard';
import { ReconciliationBoard } from './ReconciliationBoard';
import { AuditLogViewer } from './AuditLogViewer';
import { MongoDBAtlasInspector } from './MongoDBAtlasInspector';

interface Props {
  initialTab?: string;
}

export const PlatformAdminPortal: React.FC<Props> = ({ initialTab = 'telemetry' }) => {
  const [activeTab, setActiveTab] = useState<'telemetry' | 'dod' | 'audit' | 'ai-eval' | 'mongodb'>(
    (initialTab as any) || 'telemetry'
  );

  useEffect(() => {
    if (initialTab && ['telemetry', 'dod', 'audit', 'ai-eval', 'mongodb'].includes(initialTab)) {
      setActiveTab(initialTab as any);
    }
  }, [initialTab]);

  const handleTabChange = (tab: typeof activeTab) => {
    setActiveTab(tab);
    window.location.hash = `/admin/${tab}`;
  };

  return (
    <div className="space-y-6">
      {/* SRE Admin Header Strip */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shadow-xs">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-700 border border-amber-200 flex items-center justify-center font-bold text-lg">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-semibold text-amber-800 uppercase tracking-wider">
              Platform SRE &amp; Governance Suite
            </div>
            <h2 className="text-xl font-bold text-slate-900">Statewide Autonomous Cluster Telemetry</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Production Environment &bull; 4 Golden Signals &bull; MongoDB Atlas Cloud Mirror Active
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold px-3 py-1.5 rounded-xl flex items-center space-x-1.5 shadow-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>All Clusters Operational</span>
          </span>
        </div>
      </div>

      {/* Clean Sub-Page Navigation Tabs */}
      <div className="flex border-b border-slate-200 bg-white p-1 rounded-2xl gap-1.5 text-xs overflow-x-auto shadow-xs">
        <button
          onClick={() => handleTabChange('telemetry')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-semibold transition whitespace-nowrap ${
            activeTab === 'telemetry'
              ? 'bg-teal-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>SRE Golden Signals &amp; Trace</span>
        </button>

        <button
          onClick={() => handleTabChange('mongodb')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-semibold transition whitespace-nowrap ${
            activeTab === 'mongodb'
              ? 'bg-emerald-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Database className="w-4 h-4" />
          <span>MongoDB Atlas Cloud Store</span>
        </button>

        <button
          onClick={() => handleTabChange('dod')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-semibold transition whitespace-nowrap ${
            activeTab === 'dod'
              ? 'bg-teal-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <CheckCircle2 className="w-4 h-4" />
          <span>27-Stage DoD Readiness</span>
        </button>

        <button
          onClick={() => handleTabChange('audit')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-semibold transition whitespace-nowrap ${
            activeTab === 'audit'
              ? 'bg-teal-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Lock className="w-4 h-4" />
          <span>Cryptographic Audit Trail</span>
        </button>

        <button
          onClick={() => handleTabChange('ai-eval')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-semibold transition whitespace-nowrap ${
            activeTab === 'ai-eval'
              ? 'bg-teal-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <DollarSign className="w-4 h-4" />
          <span>AI Evaluation &amp; ROI</span>
        </button>
      </div>

      {/* Dedicated Sub-Page Content */}
      <div>
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
