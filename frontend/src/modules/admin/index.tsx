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
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shadow-lg">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center font-black text-lg">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-bold text-amber-400 uppercase tracking-wider">
              Platform SRE &amp; Platform Governance Suite
            </div>
            <h2 className="text-xl font-extrabold text-white">Statewide Autonomous Cluster Telemetry</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Production Environment &bull; 4 Golden Signals &bull; MongoDB Atlas Cloud Mirror Active
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

      {/* Clean Sub-Page Navigation Tabs */}
      <div className="flex border-b border-slate-800 bg-slate-900/60 p-1 rounded-2xl gap-1.5 text-xs overflow-x-auto">
        <button
          onClick={() => handleTabChange('telemetry')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'telemetry'
              ? 'bg-amber-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>SRE Golden Signals &amp; Trace Waterfall</span>
        </button>

        <button
          onClick={() => handleTabChange('mongodb')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'mongodb'
              ? 'bg-emerald-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Database className="w-4 h-4" />
          <span>MongoDB Atlas Cloud Store</span>
        </button>

        <button
          onClick={() => handleTabChange('dod')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'dod'
              ? 'bg-amber-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <CheckCircle2 className="w-4 h-4" />
          <span>27-Stage DoD Readiness Runner</span>
        </button>

        <button
          onClick={() => handleTabChange('audit')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'audit'
              ? 'bg-amber-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Lock className="w-4 h-4" />
          <span>Zero-PHI Cryptographic Audit Trail</span>
        </button>

        <button
          onClick={() => handleTabChange('ai-eval')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'ai-eval'
              ? 'bg-amber-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <DollarSign className="w-4 h-4" />
          <span>AI Evaluation &amp; ROI Scorecard</span>
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
