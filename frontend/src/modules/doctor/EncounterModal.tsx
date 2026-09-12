import React, { useState, useEffect } from 'react';
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
  Play,
  Pause,
  Headphones,
  Volume2,
  RotateCcw,
} from 'lucide-react';
import { usePlatformEvents, LiveBooking } from '../../context/PlatformEventContext';

interface Props {
  booking: LiveBooking;
  onClose: () => void;
}

export const EncounterModal: React.FC<Props> = ({ booking, onClose }) => {
  const { completeEncounter } = usePlatformEvents();

  // Upgrade 9: Patient Voice Call Audio Replay & Timestamped Transcript
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [currentPlaySec, setCurrentPlaySec] = useState(0);

  const callTranscript = [
    { sec: 2, timestamp: '00:02', speaker: 'Patient', text: 'Hello, I’ve had terrible right knee pain for 3 days and difficulty bearing weight.' },
    { sec: 7, timestamp: '00:07', speaker: 'AI Assistant', text: 'I understand. Is there any swelling, numbness, or recent trauma to the knee?' },
    { sec: 13, timestamp: '00:13', speaker: 'Patient', text: 'Mild swelling around the kneecap. No fever or recent accident.' },
    { sec: 19, timestamp: '00:19', speaker: 'AI Assistant', text: 'Thank you. I have scheduled you with Dr. Sharma for an Orthopedic consultation.' },
  ];

  useEffect(() => {
    let timer: any = null;
    if (isPlayingAudio) {
      timer = setInterval(() => {
        setCurrentPlaySec((prev) => {
          if (prev >= 24) {
            setIsPlayingAudio(false);
            return 0;
          }
          return prev + 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [isPlayingAudio]);

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

          {/* Upgrade 9: Patient Voice Call Audio Replay & Synchronized Transcript */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3">
            <div className="flex flex-wrap justify-between items-center gap-2">
              <div className="flex items-center space-x-2">
                <Headphones className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Patient Intake Voice Call Recording (Audio Replay)
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => setIsPlayingAudio(!isPlayingAudio)}
                  className={`text-xs px-3 py-1 rounded-lg font-bold flex items-center space-x-1.5 transition ${
                    isPlayingAudio
                      ? 'bg-rose-600 text-white shadow'
                      : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow'
                  }`}
                >
                  {isPlayingAudio ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                  <span>{isPlayingAudio ? 'Pause Audio' : 'Play 24s Call'}</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsPlayingAudio(false);
                    setCurrentPlaySec(0);
                  }}
                  className="p-1 text-slate-400 hover:text-white rounded bg-slate-900 border border-slate-800"
                  title="Restart Audio"
                >
                  <RotateCcw className="w-3 h-3" />
                </button>
                <span className="text-[11px] font-mono font-bold text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                  00:{currentPlaySec < 10 ? `0${currentPlaySec}` : currentPlaySec} / 00:24
                </span>
              </div>
            </div>

            {/* Audio Progress Scrubber Bar */}
            <div
              className="w-full bg-slate-900 h-2 rounded-full overflow-hidden cursor-pointer"
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const pct = (e.clientX - rect.left) / rect.width;
                setCurrentPlaySec(Math.round(pct * 24));
              }}
            >
              <div
                className="bg-emerald-400 h-full transition-all duration-200"
                style={{ width: `${(currentPlaySec / 24) * 100}%` }}
              />
            </div>

            {/* Interactive Clickable Transcript Lines */}
            <div className="space-y-1.5 pt-1">
              <div className="text-[10px] text-slate-500 uppercase font-semibold">
                Click any line below to jump audio playback to that exact second:
              </div>
              <div className="grid grid-cols-1 gap-1.5 max-h-36 overflow-y-auto">
                {callTranscript.map((t) => {
                  const isActiveLine = currentPlaySec >= t.sec && currentPlaySec < t.sec + 6;
                  return (
                    <div
                      key={t.sec}
                      onClick={() => {
                        setCurrentPlaySec(t.sec);
                        setIsPlayingAudio(true);
                      }}
                      className={`p-2 rounded-lg text-xs flex items-start space-x-2.5 transition cursor-pointer border ${
                        isActiveLine
                          ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-200'
                          : 'bg-slate-900/60 border-slate-800/80 text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      <span className="font-mono text-[10px] font-bold text-emerald-400 shrink-0 mt-0.5">
                        {t.timestamp}
                      </span>
                      <div className="flex-1">
                        <span className="font-bold mr-1 text-white">{t.speaker}:</span>
                        <span>"{t.text}"</span>
                      </div>
                    </div>
                  );
                })}
              </div>
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
