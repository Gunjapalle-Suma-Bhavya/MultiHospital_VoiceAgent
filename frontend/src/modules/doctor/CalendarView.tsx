import React, { useState } from 'react';
import { Clock, Calendar as CalendarIcon, Check, Stethoscope } from 'lucide-react';
import { apiCall } from '../../api/client';
import { usePlatformEvents } from '../../context/PlatformEventContext';

interface CalendarViewProps {
  appointments: any[];
  selectedAppointmentId?: string;
  onSelectAppointment: (appt: any) => void;
  onOpenEncounter?: (appt: any) => void;
  doctorId?: string;
}

export const CalendarView: React.FC<CalendarViewProps> = ({
  appointments,
  selectedAppointmentId,
  onSelectAppointment,
  onOpenEncounter,
  doctorId = 'DOC-SHARMA-01',
}) => {
  const { bookings, blockedSlots, blockSlot, unblockSlot } = usePlatformEvents();

  const [selectedDayIndex, setSelectedDayIndex] = useState(0);

  const weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const today = new Date();
  const currentDayOfWeek = (today.getDay() + 6) % 7; // Monday = 0

  const getDayDate = (dayOffset: number) => {
    const d = new Date();
    d.setDate(today.getDate() - currentDayOfWeek + dayOffset);
    return {
      name: weekDays[dayOffset],
      dateStr: d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
      isToday: dayOffset === currentDayOfWeek,
    };
  };

  const daysInfo = weekDays.map((_, idx) => getDayDate(idx));

  // Extended hourly time slots (8:00 AM to 6:00 PM)
  const baseSlots = [
    '08:00 AM',
    '08:30 AM',
    '09:00 AM',
    '09:30 AM',
    '10:00 AM',
    '10:30 AM',
    '11:00 AM',
    '11:30 AM',
    '12:00 PM',
    '12:30 PM',
    '02:00 PM',
    '02:30 PM',
    '03:00 PM',
    '03:30 PM',
    '04:00 PM',
    '04:30 PM',
    '05:00 PM',
    '05:30 PM',
  ];

  const handleToggleSlot = async (slotTime: string, isBlocked: boolean) => {
    if (isBlocked) {
      unblockSlot(slotTime);
    } else {
      blockSlot(slotTime, `Physician unavailable for ${slotTime}`);
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
    }
  };

  // Merge context bookings with prop appointments
  const allAppointments = [
    ...bookings.map((b) => ({
      id: b.id,
      time: b.slot_time,
      patient_name: b.patient_name,
      patient_phone: b.patient_phone,
      complaint: `${b.specialty} Consultation & Symptoms Examination`,
      intake_status: 'COMPLETED',
      ehr_status: b.status,
      isLive: true,
      raw: b,
    })),
    ...appointments.filter((a) => !bookings.some((b) => b.id === a.id)),
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-md">
      <div className="flex flex-wrap justify-between items-center pb-2 border-b border-slate-800 gap-2">
        <div>
          <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-sky-400" />
            <span>Interactive 7-Day Clinical Schedule (Weekly Grid)</span>
          </h3>
          <p className="text-xs text-slate-400">
            Select a weekday to view scheduled consultations or click slots to lock / unlock capacity
          </p>
        </div>
        <span className="text-xs text-emerald-400 font-mono font-bold flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Living Sync Active</span>
        </span>
      </div>

      {/* 7-Day Weekday Tab Selector (Upgrade 4) */}
      <div className="grid grid-cols-7 gap-1.5 p-1 bg-slate-950/80 rounded-xl border border-slate-800 text-center">
        {daysInfo.map((day, idx) => (
          <button
            key={day.name}
            onClick={() => setSelectedDayIndex(idx)}
            className={`py-1.5 px-1 rounded-lg transition text-xs flex flex-col items-center ${
              selectedDayIndex === idx
                ? 'bg-sky-600 text-white font-bold shadow'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <span className="text-[10px] uppercase font-semibold">{day.name.slice(0, 3)}</span>
            <span className="text-xs">{day.dateStr}</span>
            {day.isToday && (
              <span className="text-[9px] bg-emerald-500/20 text-emerald-400 px-1 rounded font-bold mt-0.5">
                Today
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Visual Time Grid for Selected Day */}
      <div className="space-y-1.5">
        <div className="flex justify-between items-center text-[10px] font-bold text-slate-400 uppercase tracking-wider">
          <span>{daysInfo[selectedDayIndex].name} Hourly Consultation Slots</span>
          <span className="text-slate-500">Click slot to toggle block</span>
        </div>
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 text-xs">
          {baseSlots.map((time) => {
            const bookedAppt = allAppointments.find((a) => a.time === time);
            const isBlocked = blockedSlots.includes(time);
            const isBooked = !!bookedAppt;

            return (
              <div
                key={time}
                onClick={() => {
                  if (isBooked) {
                    onSelectAppointment(bookedAppt);
                  } else {
                    handleToggleSlot(time, isBlocked);
                  }
                }}
                className={`p-2.5 rounded-xl border text-center transition cursor-pointer shadow-sm ${
                  isBooked
                    ? 'bg-sky-950/60 border-sky-500 text-sky-200 hover:border-sky-400'
                    : isBlocked
                    ? 'bg-rose-950/40 border-rose-500/50 text-rose-300 hover:border-rose-400'
                    : 'bg-slate-950/80 border-slate-800 hover:border-emerald-500/60 text-slate-300'
                }`}
              >
                <div className="font-bold text-[11px]">{time}</div>
                <div className="text-[9px] mt-1 truncate font-medium">
                  {isBooked
                    ? `✓ ${bookedAppt.patient_name}`
                    : isBlocked
                    ? '⛔ Blocked'
                    : '🟢 Available'}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Appointment Queue List */}
      <div className="space-y-2 pt-2 border-t border-slate-800">
        <div className="flex justify-between items-center text-[10px] font-bold text-slate-400 uppercase tracking-wider">
          <span>Scheduled Queue ({allAppointments.length} Patients)</span>
          <span>Status &bull; Action</span>
        </div>

        <div className="space-y-2 max-h-60 overflow-y-auto">
          {allAppointments.length === 0 ? (
            <div className="py-6 text-center text-xs text-slate-500 space-y-1">
              <div className="font-bold text-slate-300">No Patient Consultations in Queue</div>
              <p className="text-[11px] text-slate-400">
                Slots marked "🟢 Available" above can be booked by patients or assigned via Voice AI intake.
              </p>
            </div>
          ) : (
            allAppointments.map((appt) => {
              const isSelected = selectedAppointmentId === appt.id;
              const isCompleted = appt.ehr_status === 'COMPLETED';

              return (
                <div
                  key={appt.id}
                  onClick={() => onSelectAppointment(appt)}
                  className={`p-3 rounded-xl border flex items-center justify-between transition cursor-pointer ${
                    isSelected
                      ? 'bg-slate-800/90 border-sky-500/60 shadow'
                      : 'bg-slate-950/60 border-slate-800 hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-lg bg-sky-500/10 text-sky-400 flex items-center justify-center font-bold text-xs">
                      {appt.time.split(' ')[0]}
                    </div>
                  <div>
                    <div className="text-xs font-bold text-white flex items-center gap-1.5">
                      <span>{appt.patient_name}</span>
                      <span className="text-[10px] text-slate-400 font-mono">({appt.id})</span>
                      {appt.isLive && (
                        <span className="text-[9px] bg-emerald-500/20 text-emerald-400 px-1.5 rounded font-semibold">
                          Live Sync
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-400 truncate max-w-xs">{appt.complaint}</div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      isCompleted
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                    }`}
                  >
                    {isCompleted ? '✓ Completed' : appt.ehr_status || 'Confirmed'}
                  </span>

                  {onOpenEncounter && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onOpenEncounter(appt);
                      }}
                      className="bg-sky-600 hover:bg-sky-500 text-white font-bold text-[11px] px-2.5 py-1 rounded-lg transition flex items-center space-x-1 shadow"
                    >
                      <Stethoscope className="w-3 h-3" />
                      <span>{isCompleted ? 'Review Rx' : 'Consult'}</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
        </div>
      </div>
    </div>
  );
};
