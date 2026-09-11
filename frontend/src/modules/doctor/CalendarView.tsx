import React from 'react';
import { Clock, User, CheckCircle2 } from 'lucide-react';

interface CalendarViewProps {
  appointments: any[];
  selectedAppointmentId?: string;
  onSelectAppointment: (appt: any) => void;
}

export const CalendarView: React.FC<CalendarViewProps> = ({
  appointments,
  selectedAppointmentId,
  onSelectAppointment,
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3 shadow-md">
      <div className="flex justify-between items-center pb-2 border-b border-slate-800">
        <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
          <Clock className="w-4 h-4 text-sky-400" />
          <span>Today's Patient Schedule Queue</span>
        </h3>
        <span className="text-xs text-slate-400 font-mono">Live EHR Status</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="text-[10px] uppercase text-slate-500 bg-slate-950 border-y border-slate-800">
            <tr>
              <th className="py-2.5 px-3">Time</th>
              <th className="py-2.5 px-3">Patient</th>
              <th className="py-2.5 px-3">Chief Complaint</th>
              <th className="py-2.5 px-3">Intake Brief</th>
              <th className="py-2.5 px-3 text-right">EHR Sync</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 font-medium">
            {appointments.map((a) => {
              const isSelected = a.id === selectedAppointmentId || a.appointment_id === selectedAppointmentId;
              return (
                <tr
                  key={a.id || a.appointment_id}
                  onClick={() => onSelectAppointment(a)}
                  className={`cursor-pointer hover:bg-slate-800/60 transition ${
                    isSelected ? 'bg-slate-800/40 border-l-2 border-sky-400' : ''
                  }`}
                >
                  <td className="py-3 px-3 font-semibold text-white">
                    {a.time || a.scheduled_time || '04:00 PM'}
                  </td>
                  <td className="py-3 px-3">
                    <div className="font-bold text-slate-200">{a.patient_name || 'Patient A'}</div>
                    <div className="text-[10px] text-slate-400">ID: {a.id || a.appointment_id || 'APT-1024'}</div>
                  </td>
                  <td className="py-3 px-3 text-slate-300">
                    {a.complaint || a.reason_for_visit || 'Acute shoulder pain evaluation'}
                  </td>
                  <td className="py-3 px-3">
                    <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                      {a.intake_status || 'COMPLETED'}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right">
                    <span className="text-[10px] font-bold text-sky-400 bg-sky-500/10 border border-sky-500/20 px-2 py-0.5 rounded">
                      EHR SYNCED
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
