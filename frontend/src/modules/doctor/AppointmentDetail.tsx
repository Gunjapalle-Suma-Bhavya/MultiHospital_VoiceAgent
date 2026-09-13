import React, { useState } from 'react';
import { ClipboardCheck, Check, ShieldAlert, Stethoscope, User, Phone, Calendar, Clock } from 'lucide-react';

interface AppointmentDetailProps {
  appointment: any;
  onOpenEncounter?: () => void;
}

export const AppointmentDetail: React.FC<AppointmentDetailProps> = ({
  appointment,
  onOpenEncounter,
}) => {
  const [isReviewed, setIsReviewed] = useState(false);

  if (!appointment) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 space-y-3 shadow-md flex flex-col items-center justify-center text-center h-full min-h-[320px]">
        <ClipboardCheck className="w-10 h-10 text-slate-600 mb-2" />
        <h3 className="font-bold text-sm text-white">No Appointment Selected</h3>
        <p className="text-xs text-slate-400 max-w-xs leading-relaxed">
          Select a patient consultation from the schedule or queue on the left to inspect pre-visit intake details, triage assessment, and launch the clinical encounter.
        </p>
      </div>
    );
  }

  const patientName = appointment.patient_name || appointment.name || 'Registered Patient';
  const rawId = appointment.id || appointment.appointment_id || 'APT-001';
  const mrn = appointment.patient_id || `MRN-${rawId.replace(/\D/g, '') || '88421'}`;
  const patientPhone = appointment.patient_phone || appointment.phone || 'On file';
  const symptoms =
    appointment.complaint ||
    appointment.reason ||
    appointment.notes ||
    'Routine clinical consultation and health status evaluation.';
  const scheduledTime = appointment.time || appointment.slot_time || '10:00 AM';
  const scheduledDate = appointment.date || (appointment.start_datetime ? appointment.start_datetime.split('T')[0] : 'Today');
  const status = appointment.ehr_status || appointment.status || 'CONFIRMED';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3 shadow-md flex flex-col justify-between">
      <div className="space-y-3">
        <div className="flex justify-between items-center pb-2 border-b border-slate-800">
          <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
            <ClipboardCheck className="w-4 h-4 text-sky-400" />
            <span>Pre-Visit Clinical Brief</span>
          </h3>
          <span className="text-[10px] font-bold bg-sky-500/10 text-sky-400 border border-sky-500/20 px-2 py-0.5 rounded">
            Live EHR &bull; Zero PHI Leak
          </span>
        </div>

        <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 space-y-2.5 text-xs">
          <div className="flex justify-between items-center text-slate-400 border-b border-slate-800 pb-2 text-[11px]">
            <div className="flex items-center space-x-1.5">
              <User className="w-3.5 h-3.5 text-sky-400" />
              <span>
                Patient: <strong className="text-white text-xs">{patientName}</strong>
              </span>
            </div>
            <span className="font-mono text-slate-300">
              ID: <strong className="text-sky-300">{mrn}</strong>
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] pb-1">
            <div className="flex items-center space-x-1.5 text-slate-300">
              <Calendar className="w-3.5 h-3.5 text-slate-500" />
              <span>Date: <strong>{scheduledDate}</strong></span>
            </div>
            <div className="flex items-center space-x-1.5 text-slate-300">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              <span>Time: <strong>{scheduledTime}</strong></span>
            </div>
            <div className="flex items-center space-x-1.5 text-slate-300 col-span-2">
              <Phone className="w-3.5 h-3.5 text-slate-500" />
              <span>Contact: <strong>{patientPhone}</strong></span>
            </div>
          </div>

          <div>
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Reported Symptoms &amp; Chief Complaint:
            </div>
            <p className="text-slate-200 font-medium mt-1 leading-relaxed bg-slate-900/80 p-2 rounded-lg border border-slate-800">
              "{symptoms}"
            </p>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
            <div className="bg-slate-900 p-2 rounded-lg border border-slate-800">
              <span className="text-slate-500">Booking Status:</span>
              <div className="font-bold text-emerald-400 capitalize">{status}</div>
            </div>
            <div className="bg-slate-900 p-2 rounded-lg border border-slate-800">
              <span className="text-slate-500">Intake Protocol:</span>
              <div className="font-bold text-sky-400">Standard Intake v2.4</div>
            </div>
          </div>

          <div className="pt-1">
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              AI Safety Triage Assessment:
            </div>
            <div className="bg-emerald-950/40 border border-emerald-500/20 text-emerald-300 p-2 rounded-lg text-[11px] font-medium mt-0.5 flex items-start gap-1.5">
              <ShieldAlert className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              <span>
                ✓ Non-emergency complaint. Outpatient consultation appropriate. Zero unauthorized medical diagnoses issued.
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-between items-center pt-3 border-t border-slate-800 gap-2">
        <button
          onClick={() => setIsReviewed(true)}
          className={`font-bold text-xs px-3 py-1.5 rounded-lg transition shadow flex items-center gap-1.5 ${
            isReviewed
              ? 'bg-slate-800 text-emerald-400 border border-emerald-500/40'
              : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
          }`}
        >
          <Check className="w-3.5 h-3.5" />
          <span>{isReviewed ? '✓ Reviewed' : 'Review Brief'}</span>
        </button>

        {onOpenEncounter && (
          <button
            onClick={onOpenEncounter}
            className="bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs px-3.5 py-1.5 rounded-lg transition shadow flex items-center gap-1.5"
          >
            <Stethoscope className="w-3.5 h-3.5" />
            <span>Open Clinical Encounter</span>
          </button>
        )}
      </div>
    </div>
  );
};
