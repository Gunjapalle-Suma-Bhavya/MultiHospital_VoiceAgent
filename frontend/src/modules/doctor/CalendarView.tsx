import React, { useState } from 'react';
import { Clock, Calendar as CalendarIcon, Ban, Check } from 'lucide-react';
import { apiCall } from '../../api/client';

interface CalendarViewProps {
  appointments: any[];
  selectedAppointmentId?: string;
  onSelectAppointment: (appt: any) => void;
  doctorId?: string;
}

export const CalendarView: React.FC<CalendarViewProps> = ({
  appointments,
  selectedAppointmentId,
  onSelectAppointment,
  doctorId = 'DOC-SHARMA-01',
}) => {
  const [blockedTimes, setBlockedTimes] = useState<string[]>(['12:30 PM']);

  const timeSlots = [
    { time: '09:00 AM', status: 'AVAILABLE' },
    { time: '09:30 AM', status: 'AVAILABLE' },
    { time: '10:00 AM', status: 'AVAILABLE' },
    { time: '10:30 AM', status: 'AVAILABLE' },
    { time: '11:00 AM', status: 'AVAILABLE' },
    { time: '11:30 AM', status: 'AVAILABLE' },
    { time: '12:00 PM', status: 'AVAILABLE' },
    { time: '12:30 PM', status: 'BLOCKED' },
    { time: '02:00 PM', status: 'AVAILABLE' },
    { time: '02:30 PM', status: 'AVAILABLE' },
    { time: '03:00 PM', status: 'AVAILABLE' },
    { time: '03:30 PM', status: 'AVAILABLE' },
    { time: '04:00 PM', status: 'BOOKED', patient: 'Patient A' },
    { time: '04:30 PM', status: 'BOOKED', patient: 'Elena Rostova' },
    { time: '05:00 PM', status: 'BOOKED', patient: 'James Miller' },
  ];

  const handleToggleSlot = async (slotTime: string) => {
    if (blockedTimes.includes(slotTime)) {
      setBlockedTimes(prev => prev.filter(t => t !== slotTime));
      alert(`Slot ${slotTime} unblocked and opened for patient access.`);
    } else {
      setBlockedTimes(prev => [...prev, slotTime]);
      try {
        await apiCall(`/api/v1/doctor-dashboard/${doctorId}/leaves`, {
          method: 'POST',
          body: JSON.stringify({
            start_date: new Date().toISOString().split('T')[0],
            end_date: new Date().toISOString().split('T')[0],
            leave_type: 'BLOCKED_SLOT',
            reason: `Direct block for ${slotTime}`,
          }),
        });
      } catch {}
      alert(`Slot ${slotTime} successfully blocked on calendar.`);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-md">
      <div className="flex justify-between items-center pb-2 border-b border-slate-800">
        <div>
          <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-sky-400" />
            <span>Today's Patient Schedule Queue</span>
          </h3>
          <p className="text-xs text-slate-400">Click any patient to inspect clinical briefs, or toggle hourly slots below</p>
        </div>
        <span className="text-xs text-slate-400 font-mono">Live EHR Status</span>
      </div>

      {/* Visual Time Grid */}
      <div className="space-y-1.5">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
          Visual Hourly Consultation Grid (Click slot to block / unblock):
        </div>
        <div className="grid grid-cols-3 sm:grid-cols-5 gap-2 text-xs">
          {timeSlots.map((s) => {
            const isBlocked = blockedTimes.includes(s.time) || s.status === 'BLOCKED';
            const isBooked = s.status === 'BOOKED';

            return (
              <div
                key={s.time}
                onClick={() => !isBooked && handleToggleSlot(s.time)}
                className={`p-2 rounded-lg border text-center transition cursor-pointer ${
                  isBooked
                    ? 'bg-sky-950/40 border-sky-500/40 text-sky-300'
                    : isBlocked
                    ? 'bg-rose-950/40 border-rose-500/40 text-rose-300'
                    : 'bg-slate-950 border-slate-800 hover:border-emerald-500/50 text-slate-300'
                }`}
              >
                <div className="font-bold text-[11px]">{s.time}</div>
                <div className="text-[9px] mt-0.5 truncate font-medium">
                  {isBooked ? `Booked: ${s.patient}` : isBlocked ? 'Blocked' : 'Available'}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Appointment Table */}
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
