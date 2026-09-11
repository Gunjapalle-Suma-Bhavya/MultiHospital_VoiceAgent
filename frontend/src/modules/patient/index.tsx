import React, { useState } from 'react';
import { ShieldCheck } from 'lucide-react';
import { VoiceAgentScreen } from './VoiceAgentScreen';
import { DoctorDiscovery } from './DoctorDiscovery';
import { QuestionnaireForm } from './QuestionnaireForm';
import { MyAppointments } from './MyAppointments';
import { useAuth } from '../../hooks/useAuth';

export const PatientPortal: React.FC = () => {
  const { user } = useAuth();
  const [selectedSpecialty, setSelectedSpecialty] = useState('Orthopedics');
  const [hasBooking, setHasBooking] = useState(false);

  return (
    <div className="space-y-6">
      {/* Welcome Strip */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-lg">
        <div>
          <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Patient Self-Service Access</div>
          <h2 className="text-xl sm:text-2xl font-black text-white mt-0.5">
            Welcome, <span>{user?.name || 'Patient A'}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Phone: <span className="font-mono text-slate-300">{user?.identifier || '+1-555-SHOULDER'}</span> &bull; Preferred Communication: SMS / Voice
          </p>
        </div>
        <div>
          <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold px-3 py-1.5 rounded-xl flex items-center space-x-1.5">
            <ShieldCheck className="w-4 h-4" />
            <span>HIPAA Encrypted Profile</span>
          </span>
        </div>
      </div>

      {/* 2-Column: AI Voice & Chat Console (Left) + Specialist Discovery (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5">
          <VoiceAgentScreen onSpecialtySelected={(s) => setSelectedSpecialty(s)} />
        </div>

        <div className="lg:col-span-7 space-y-4">
          <DoctorDiscovery
            initialSpecialty={selectedSpecialty}
            onBookingSuccess={() => setHasBooking(true)}
          />

          {hasBooking && (
            <QuestionnaireForm />
          )}
        </div>
      </div>

      {/* Real Appointments Table */}
      <MyAppointments />
    </div>
  );
};
