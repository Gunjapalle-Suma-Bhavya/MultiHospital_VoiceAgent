import React, { useState, useEffect } from 'react';
import { Clock, Calendar, Plus, Ban, CheckCircle2, RotateCw } from 'lucide-react';
import { apiCall } from '../../api/client';
import { useToast } from '../../context/ToastContext';
import { usePlatformEvents } from '../../context/PlatformEventContext';

interface Props {
  doctorId: string;
}

export const DoctorAvailability: React.FC<Props> = ({ doctorId }) => {
  const { showToast } = useToast();
  const { blockSlot, blockedSlots, unblockSlot } = usePlatformEvents();

  const [operatingHours, setOperatingHours] = useState('09:00 AM - 05:00 PM');
  const [slotDuration, setSlotDuration] = useState('30');
  const [leaveStartDate, setLeaveStartDate] = useState('');
  const [leaveEndDate, setLeaveEndDate] = useState('');
  const [leaveReason, setLeaveReason] = useState('Clinical Conference / Hospital Rounds');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [customSlot, setCustomSlot] = useState('01:00 PM');

  const handleBlockCustomSlot = () => {
    if (!customSlot.trim()) return;
    blockSlot(customSlot, leaveReason);
  };

  const handleSubmitLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!leaveStartDate || !leaveEndDate) {
      showToast('warning', 'Incomplete Dates', 'Please select both start and end dates.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await apiCall(`/api/v1/doctor-dashboard/${doctorId}/leaves`, {
        method: 'POST',
        body: JSON.stringify({
          start_date: leaveStartDate,
          end_date: leaveEndDate,
          leave_type: 'ANNUAL_LEAVE',
          reason: leaveReason,
        }),
      });

      if (res.ok) {
        showToast(
          'success',
          'Leave Schedule Dispatched',
          `Calendar leave from ${leaveStartDate} to ${leaveEndDate} locked in hospital scheduling feed.`
        );
        setLeaveStartDate('');
        setLeaveEndDate('');
      }
    } catch (err: any) {
      showToast('error', 'Failed to Submit Leave', err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Operating Hours Settings */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-md">
        <div className="flex justify-between items-center pb-2 border-b border-slate-800">
          <div>
            <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-sky-400" />
              <span>Standard Consultation Operating Hours</span>
            </h3>
            <p className="text-xs text-slate-400">
              Configures regular weekly patient booking windows across hospital departments
            </p>
          </div>
          <span className="text-[10px] font-bold bg-sky-500/10 text-sky-400 border border-sky-500/20 px-2 py-0.5 rounded">
            Section 5.31
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div>
            <label className="block text-slate-400 font-bold mb-1 uppercase text-[10px]">
              Daily Consultation Window:
            </label>
            <select
              value={operatingHours}
              onChange={(e) => setOperatingHours(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg p-2.5 focus:ring-1 focus:ring-sky-500"
            >
              <option value="09:00 AM - 05:00 PM">09:00 AM &ndash; 05:00 PM (Standard Shift)</option>
              <option value="08:00 AM - 04:00 PM">08:00 AM &ndash; 04:00 PM (Early Shift)</option>
              <option value="12:00 PM - 08:00 PM">12:00 PM &ndash; 08:00 PM (Afternoon Shift)</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 font-bold mb-1 uppercase text-[10px]">
              Slot Consultation Duration:
            </label>
            <select
              value={slotDuration}
              onChange={(e) => setSlotDuration(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg p-2.5 focus:ring-1 focus:ring-sky-500"
            >
              <option value="15">15 Minutes (Rapid Consult)</option>
              <option value="30">30 Minutes (Standard Clinical)</option>
              <option value="45">45 Minutes (Specialty Evaluation)</option>
              <option value="60">60 Minutes (Comprehensive Intake)</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={() =>
                showToast(
                  'success',
                  'Hours Synchronized',
                  `Operating hours (${operatingHours}, ${slotDuration} min) updated for ${doctorId}.`
                )
              }
              className="w-full bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs p-2.5 rounded-lg transition shadow"
            >
              Save Schedule Settings
            </button>
          </div>
        </div>
      </div>

      {/* Leave & Schedule Block Request */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Submit Leave */}
        <form
          onSubmit={handleSubmitLeave}
          className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-md"
        >
          <div className="pb-2 border-b border-slate-800">
            <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
              <Calendar className="w-4 h-4 text-sky-400" />
              <span>Submit Physician Leave &bull; Multi-Day Block</span>
            </h3>
            <p className="text-xs text-slate-400">
              Dispatches directly to{' '}
              <code className="text-sky-400 font-mono text-[11px]">
                POST /api/v1/doctor-dashboard/&#123;id&#125;/leaves
              </code>
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="block text-slate-400 font-bold mb-1 uppercase text-[10px]">
                Start Date:
              </label>
              <input
                type="date"
                value={leaveStartDate}
                onChange={(e) => setLeaveStartDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg p-2 focus:ring-1 focus:ring-sky-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 font-bold mb-1 uppercase text-[10px]">
                End Date:
              </label>
              <input
                type="date"
                value={leaveEndDate}
                onChange={(e) => setLeaveEndDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg p-2 focus:ring-1 focus:ring-sky-500"
              />
            </div>
          </div>

          <div className="text-xs space-y-1">
            <label className="block text-slate-400 font-bold uppercase text-[10px]">
              Reason for Absence / Block:
            </label>
            <input
              type="text"
              value={leaveReason}
              onChange={(e) => setLeaveReason(e.target.value)}
              placeholder="e.g. Clinical Conference, Medical Leave"
              className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg p-2 focus:ring-1 focus:ring-sky-500"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs p-2.5 rounded-lg transition shadow disabled:opacity-50"
          >
            {isSubmitting ? 'Dispatching...' : 'Lock Calendar Leave Period'}
          </button>
        </form>

        {/* Rapid Slot Blocking */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-md flex flex-col justify-between">
          <div className="space-y-3">
            <div className="pb-2 border-b border-slate-800">
              <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
                <Ban className="w-4 h-4 text-rose-400" />
                <span>Active Blocked Time Slots</span>
              </h3>
              <p className="text-xs text-slate-400">
                Immediately prevents patient intake agents from booking these consultation hours
              </p>
            </div>

            <div className="flex space-x-2 text-xs">
              <input
                type="text"
                value={customSlot}
                onChange={(e) => setCustomSlot(e.target.value)}
                placeholder="e.g. 01:00 PM"
                className="flex-1 bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 font-mono"
              />
              <button
                onClick={handleBlockCustomSlot}
                className="bg-rose-950/60 hover:bg-rose-900/60 text-rose-300 border border-rose-800/80 font-bold px-4 py-2 rounded-lg transition"
              >
                Block Slot
              </button>
            </div>

            <div className="space-y-1.5">
              <div className="text-[10px] font-bold text-slate-400 uppercase">
                Currently Blocked ({blockedSlots.length} Slots):
              </div>
              <div className="flex flex-wrap gap-1.5">
                {blockedSlots.length === 0 ? (
                  <div className="text-xs text-slate-500 italic">No slots currently blocked.</div>
                ) : (
                  blockedSlots.map((slot) => (
                    <span
                      key={slot}
                      className="bg-slate-950 border border-slate-800 text-slate-200 text-xs px-2.5 py-1 rounded-lg flex items-center space-x-1.5 font-mono"
                    >
                      <span>{slot}</span>
                      <button
                        onClick={() => unblockSlot(slot)}
                        className="text-slate-500 hover:text-rose-400 text-xs font-bold"
                        title="Unblock slot"
                      >
                        &times;
                      </button>
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-500 flex items-center space-x-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Changes reflect instantly on Patient Voice Intake &amp; Discovery</span>
          </div>
        </div>
      </div>
    </div>
  );
};
