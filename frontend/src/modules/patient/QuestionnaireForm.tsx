import React, { useState } from 'react';
import { ClipboardList, CheckCircle2 } from 'lucide-react';
import { apiCall } from '../../api/client';
import { useAuth } from '../../hooks/useAuth';

export const QuestionnaireForm: React.FC = () => {
  const { user } = useAuth();
  const [duration, setDuration] = useState('Approximately 7 days after lifting heavy objects');
  const [severity, setSeverity] = useState('7');
  const [allergies, setAllergies] = useState('No prior surgeries. Allergic to Penicillin.');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const patientId = user?.patient_id || user?.identifier || '+1-555-SHOULDER';
      await apiCall(`/api/v1/patients/${encodeURIComponent(patientId)}/questionnaires/submit`, {
        method: 'POST',
        body: JSON.stringify({
          questionnaire_id: 'q-ortho-01',
          responses_json: {
            symptom_duration: duration,
            pain_severity_scale: severity,
            drug_allergies: allergies,
          },
        }),
      });
      setIsSubmitted(true);
    } catch (e) {
      console.error('Submit questionnaire error:', e);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="bg-emerald-950/40 border border-emerald-500/30 rounded-xl p-4 text-center space-y-2">
        <div className="w-8 h-8 rounded-full bg-emerald-500 text-slate-950 mx-auto flex items-center justify-center font-bold">
          <CheckCircle2 className="w-5 h-5" />
        </div>
        <h4 className="text-xs font-bold text-emerald-300">Clinical Intake Answers Encrypted &amp; Synchronized</h4>
        <p className="text-[11px] text-slate-300">
          Dr. Sharma has received your pain assessment ({severity}/10) and reported Penicillin allergy.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3">
      <div className="flex justify-between items-center pb-2 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <ClipboardList className="w-4 h-4 text-emerald-400" />
          <h4 className="text-xs font-bold text-white">Pre-Visit Clinical Intake Questionnaire</h4>
        </div>
        <span className="text-[10px] font-bold bg-slate-800 text-slate-400 px-2 py-0.5 rounded">
          Dr. Sharma Approved
        </span>
      </div>

      <div className="space-y-2.5 text-xs">
        <div>
          <label className="block text-slate-400 font-medium mb-1">
            1. How long have you experienced this shoulder pain?
          </label>
          <input
            type="text"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 text-xs focus:ring-1 focus:ring-emerald-500"
          />
        </div>

        <div>
          <label className="block text-slate-400 font-medium mb-1">
            2. Rate your pain severity on a scale of 1 to 10:
          </label>
          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 text-xs"
          >
            <option value="6">6 - Moderate pain interfering with daily activities</option>
            <option value="7">7 - Severe pain preventing arm abduction</option>
            <option value="8">8 - Very severe disabling pain</option>
          </select>
        </div>

        <div>
          <label className="block text-slate-400 font-medium mb-1">
            3. Any prior surgeries or drug allergies?
          </label>
          <input
            type="text"
            value={allergies}
            onChange={(e) => setAllergies(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 text-xs"
          />
        </div>
      </div>

      <div className="flex justify-end pt-1">
        <button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs px-3.5 py-1.5 rounded-lg transition shadow disabled:opacity-50"
        >
          {isSubmitting ? 'Saving...' : 'Submit Encrypted Clinical Answers'}
        </button>
      </div>
    </div>
  );
};
