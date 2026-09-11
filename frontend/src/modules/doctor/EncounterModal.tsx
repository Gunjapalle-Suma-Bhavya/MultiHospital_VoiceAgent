import React, { useState } from 'react';
import {
  X,
  Stethoscope,
  FileText,
  Pill,
  Activity,
  CheckCircle2,
  ShieldAlert,
  Plus,
  Trash2,
  Lock,
} from 'lucide-react';
import { usePlatformEvents, LiveBooking } from '../../context/PlatformEventContext';

interface Props {
  booking: LiveBooking;
  onClose: () => void;
}

export const EncounterModal: React.FC<Props> = ({ booking, onClose }) => {
  const { completeEncounter } = usePlatformEvents();

  const [soap, setSoap] = useState({
    subjective: `Patient reports: ${booking.specialty || 'General'} consultation. Chief complaint: Severe pain and discomfort worsening over 5-7 days. Denies fever or chills.`,
    objective:
      'Vitals stable: BP 120/80 mmHg, HR 74 bpm, SpO2 98%, Temp 98.6°F. Localized joint tenderness on palpation. Moderate reduction in active range of motion.',
    assessment: `Acute exacerbation - ${booking.specialty} pathology. ICD-10: M75.10 (Clinical impression verified). Low immediate surgical risk.`,
    plan: 'Conservative management: E-prescribed anti-inflammatory regimen. Physical rehabilitation referral. Scheduled 2-week reassessment.',
  });

  const [prescriptions, setPrescriptions] = useState<
    Array<{ medication: string; dosage: string; frequency: string; duration: string }>
  >([
    {
      medication: 'Ibuprofen (Oral)',
      dosage: '600 mg',
      frequency: 'Every 8 hours with meals',
      duration: '10 days',
    },
    {
      medication: 'Cyclobenzaprine HCl',
      dosage: '10 mg',
      frequency: 'Once at bedtime PRN muscle spasm',
      duration: '7 days',
    },
  ]);

  const [newMed, setNewMed] = useState({
    medication: '',
    dosage: '',
    frequency: 'Twice daily',
    duration: '14 days',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAddMed = () => {
    if (!newMed.medication.trim()) return;
    setPrescriptions((prev) => [...prev, { ...newMed }]);
    setNewMed({ medication: '', dosage: '', frequency: 'Twice daily', duration: '14 days' });
  };

  const handleRemoveMed = (idx: number) => {
    setPrescriptions((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleSignEncounter = () => {
    setIsSubmitting(true);
    completeEncounter(booking.id, soap, prescriptions);
    setTimeout(() => {
      setIsSubmitting(false);
      onClose();
    }, 400);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex justify-between items-center bg-slate-900/90">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400 flex items-center justify-center">
              <Stethoscope className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-sky-400">
                Clinician Encounter Console &bull; Ref: {booking.id}
              </div>
              <h2 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
                <span>{booking.patient_name}</span>
                <span className="text-xs font-normal text-slate-400 font-mono">
                  ({booking.patient_phone})
                </span>
                <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded font-bold">
                  EHR Synchronized
                </span>
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Patient Vitals Ribbon */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">
              <div className="text-[10px] text-slate-400 font-bold uppercase">Blood Pressure</div>
              <div className="text-sm font-black text-white mt-1">120 / 80</div>
              <div className="text-[10px] text-emerald-400">Normal</div>
            </div>
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">
              <div className="text-[10px] text-slate-400 font-bold uppercase">Heart Rate</div>
              <div className="text-sm font-black text-white mt-1">74 bpm</div>
              <div className="text-[10px] text-emerald-400">Resting</div>
            </div>
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">
              <div className="text-[10px] text-slate-400 font-bold uppercase">SpO2 (Pulse-Ox)</div>
              <div className="text-sm font-black text-white mt-1">98%</div>
              <div className="text-[10px] text-emerald-400">Ambient Air</div>
            </div>
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">
              <div className="text-[10px] text-slate-400 font-bold uppercase">Temperature</div>
              <div className="text-sm font-black text-white mt-1">98.6 &deg;F</div>
              <div className="text-[10px] text-slate-400">Oral</div>
            </div>
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">
              <div className="text-[10px] text-slate-400 font-bold uppercase">AI Risk Score</div>
              <div className="text-sm font-black text-amber-400 mt-1">Tier-1 Mild</div>
              <div className="text-[10px] text-slate-400">Low Acuity</div>
            </div>
          </div>

          {/* SOAP Clinical Notes */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-xs font-bold text-white uppercase tracking-wider">
              <FileText className="w-4 h-4 text-sky-400" />
              <span>SOAP Clinical Documentation (HL7 FHIR ClinicalImpression)</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[11px] font-bold text-slate-400 uppercase">
                  Subjective (Patient History &amp; Chief Complaint)
                </label>
                <textarea
                  rows={3}
                  value={soap.subjective}
                  onChange={(e) => setSoap({ ...soap, subjective: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-400"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-bold text-slate-400 uppercase">
                  Objective (Clinical Examination &amp; Diagnostics)
                </label>
                <textarea
                  rows={3}
                  value={soap.objective}
                  onChange={(e) => setSoap({ ...soap, objective: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-400"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-bold text-slate-400 uppercase">
                  Assessment (Diagnostic Impression &amp; ICD-10)
                </label>
                <textarea
                  rows={3}
                  value={soap.assessment}
                  onChange={(e) => setSoap({ ...soap, assessment: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-400"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-bold text-slate-400 uppercase">
                  Plan (Therapy, Follow-up &amp; Disposition)
                </label>
                <textarea
                  rows={3}
                  value={soap.plan}
                  onChange={(e) => setSoap({ ...soap, plan: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-400"
                />
              </div>
            </div>
          </div>

          {/* E-Prescriptions Module */}
          <div className="space-y-3 bg-slate-950 border border-slate-800 rounded-xl p-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-2 text-xs font-bold text-white uppercase tracking-wider">
                <Pill className="w-4 h-4 text-emerald-400" />
                <span>E-Prescriptions &bull; Medication Orders (FHIR MedicationRequest)</span>
              </div>
              <span className="text-[10px] text-slate-400">
                {prescriptions.length} Active Orders
              </span>
            </div>

            <div className="space-y-2">
              {prescriptions.map((p, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between bg-slate-900 border border-slate-800 p-3 rounded-xl text-xs"
                >
                  <div>
                    <span className="font-bold text-white">{p.medication}</span>{' '}
                    <span className="text-emerald-400 font-mono">({p.dosage})</span>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      Instructions: {p.frequency} &bull; Duration: {p.duration}
                    </div>
                  </div>
                  <button
                    onClick={() => handleRemoveMed(idx)}
                    className="text-slate-500 hover:text-rose-400 p-1 rounded transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>

            {/* Add Medication Row */}
            <div className="pt-2 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-4 gap-2 text-xs">
              <input
                type="text"
                placeholder="Medication name (e.g. Amoxicillin)"
                value={newMed.medication}
                onChange={(e) => setNewMed({ ...newMed, medication: e.target.value })}
                className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none"
              />
              <input
                type="text"
                placeholder="Dosage (e.g. 500mg)"
                value={newMed.dosage}
                onChange={(e) => setNewMed({ ...newMed, dosage: e.target.value })}
                className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none"
              />
              <input
                type="text"
                placeholder="Frequency & Instructions"
                value={newMed.frequency}
                onChange={(e) => setNewMed({ ...newMed, frequency: e.target.value })}
                className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none"
              />
              <button
                onClick={handleAddMed}
                disabled={!newMed.medication.trim()}
                className="bg-slate-800 hover:bg-slate-700 text-emerald-400 font-bold px-3 py-1.5 rounded-lg transition flex items-center justify-center space-x-1 disabled:opacity-40"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Rx</span>
              </button>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-5 border-t border-slate-800 bg-slate-900/90 flex justify-between items-center">
          <div className="flex items-center space-x-1.5 text-[11px] text-slate-400">
            <Lock className="w-3.5 h-3.5 text-emerald-400" />
            <span>Encrypted with Physician NPI &amp; SHA-256 Audit Seal</span>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs transition"
            >
              Cancel
            </button>
            <button
              onClick={handleSignEncounter}
              disabled={isSubmitting}
              className="px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-xs transition shadow-lg shadow-emerald-500/20 flex items-center space-x-1.5 disabled:opacity-50"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>{isSubmitting ? 'Signing Encounter...' : 'Sign & Complete Consultation'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
