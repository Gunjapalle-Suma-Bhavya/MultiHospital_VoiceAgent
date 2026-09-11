import React from 'react';
import { ObservabilityTracer } from './ObservabilityTracer';
import { CanonicalJourneyRunner } from './CanonicalJourneyRunner';
import { AIEvaluationBoard } from './AIEvaluationBoard';
import { ReconciliationBoard } from './ReconciliationBoard';
import { AuditLogViewer } from './AuditLogViewer';

export const PlatformAdminPortal: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* SRE 4 Golden Signals & 16-Step Canonical Waterfall */}
      <ObservabilityTracer />

      {/* Canonical 27-Stage DoD Journey & 76-Item Audit */}
      <CanonicalJourneyRunner />

      {/* 2-Columns: Unit Economics ROI & Discrepancy Scanner */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6">
          <AIEvaluationBoard />
        </div>

        <div className="lg:col-span-6">
          <ReconciliationBoard />
        </div>
      </div>

      {/* Zero-PHI Cryptographic Audit Log Viewer */}
      <AuditLogViewer />
    </div>
  );
};
