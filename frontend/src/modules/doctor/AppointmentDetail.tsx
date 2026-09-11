import React, { useState } from 'react';
import { ClipboardCheck, Check, ShieldAlert } from 'lucide-react';

interface AppointmentDetailProps {
  appointment: any;
}

export const AppointmentDetail: React.FC<AppointmentDetailProps> = ({ appointment }) => {
  const [isReviewed, setIsReviewed] = useState(false);

  const patientName = appointment?.patient_name || 'Patient A';
  const mrn = `MRN-${(appointment?.id || '88421').replace(/\D/g, '') || '88421'}`;
  const symptoms = appointment?.complaint || 'Acute right anterior shoulder pain lasting ~7 days, aggravated by arm abduction and lifting.';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3 shadow-md flex flex-col justify-between">
      <div className="space-y-3">
        <div className="flex justify-between items-center pb-2 border-b border-slate-800">
          <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
            <ClipboardCheck className="w-4 h-4 text-sky-400" />
            <span>Pre-Visit Clinical Brief</span>
          </h3>
          <span className="text-[10px] font-bold bg-sky-500/10 text-sky-400 border border-sky-500/20 px-2 py-0.5 rounded">
            AI Summarized
          </span>
        </div>

        <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 space-y-2.5 text-xs">
          <div className="flex justify-between text-slate-400 border-b border-slate-800 pb-1.5 text-[11px]">
            <span>Patient: <strong className="text-white">{patientName}</strong></span>
            <span>MRN: <strong className="text-slate-200">{mrn}</strong></span>
          </div>

          <div>
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Reported Symptoms:</div>
            <p className="text-slate-200 font-medium mt-0.5 leading-relaxed">
              "{symptoms}"
            </p>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
            <div className="bg-slate-900 p-2 rounded-lg border border-slate-800">
              <span className="text-slate-500">Pain Severity:</span>
              <div className="font-bold text-rose-400">7 / 10 (Severe)</div>
            </div>
            <div className="bg-slate-900 p-2 rounded-lg border border-slate-800">
              <span className="text-slate-500">Known Allergies:</span>
              <div className="font-bold text-slate-200">Penicillin (Severe Rash)</div>
            </div>
          </div>

          <div className="pt-1">
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">AI Safety Triage Assessment:</div>
            <div className="bg-emerald-950/40 border border-emerald-500/20 text-emerald-300 p-2 rounded-lg text-[11px] font-medium mt-0.5 flex items-start gap-1.5">
              <ShieldAlert className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              <span>✓ Non-emergency complaint. Orthopedic evaluation appropriate. Zero medical diagnoses provided to patient.</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end pt-2 border-t border-slate-800">
        <button
          onClick={() => setIsReviewed(true)}
          className={`font-bold text-xs px-3.5 py-1.5 rounded-lg transition shadow flex items-center gap-1.5 ${
            isReviewed
              ? 'bg-slate-800 text-emerald-400 border border-emerald-500/40'
              : 'bg-emerald-600 hover:bg-emerald-500 text-slate-950'
          }`}
        >
          <Check className="w-3.5 h-3.5" />
          <span>{isReviewed ? '✓ Clinician Reviewed & Saved' : 'Mark Brief Reviewed'}</span>
        </button>
      </div>
    </div>
  );
};
