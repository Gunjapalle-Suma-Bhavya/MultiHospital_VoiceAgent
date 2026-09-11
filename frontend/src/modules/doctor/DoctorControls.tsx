import React, { useState } from 'react';
import { Calendar, AlertCircle } from 'lucide-react';
import { apiCall } from '../../api/client';

interface DoctorControlsProps {
  doctorId: string;
}

export const DoctorControls: React.FC<DoctorControlsProps> = ({ doctorId }) => {
  const [isBlocking, setIsBlocking] = useState(false);

  const handleBlockSlot = async () => {
    const reason = prompt('Enter reason for emergency calendar block:', 'Surgical theatre assignment');
    if (!reason) return;

    setIsBlocking(true);
    try {
      await apiCall(`/api/v1/doctor-dashboard/${doctorId}/leaves`, {
        method: 'POST',
        body: JSON.stringify({
          start_date: new Date().toISOString().split('T')[0],
          end_date: new Date().toISOString().split('T')[0],
          leave_type: 'BLOCKED_SLOT',
          reason,
        }),
      });
      alert(`Slot successfully blocked on ${doctorId} calendar. Availability engine updated.`);
    } catch (e) {
      console.error('Block slot error:', e);
    } finally {
      setIsBlocking(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm space-y-1.5">
      <div className="text-xs text-slate-400 font-medium">Calendar Control</div>
      <div className="flex items-center space-x-1.5">
        <button
          onClick={() => alert('Consultation Hours: Mon-Fri 09:00 - 17:00 (30-min slots)')}
          className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-2.5 py-1 rounded font-medium"
        >
          Hours: 9am-5pm
        </button>
        <button
          onClick={handleBlockSlot}
          disabled={isBlocking}
          className="text-xs bg-rose-950 hover:bg-rose-900 text-rose-300 border border-rose-800 px-2.5 py-1 rounded font-medium"
        >
          Block Slot
        </button>
      </div>
    </div>
  );
};
