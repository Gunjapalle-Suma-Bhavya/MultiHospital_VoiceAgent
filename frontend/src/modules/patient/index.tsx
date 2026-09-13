import React, { useState, useEffect } from 'react';
import {
  User,
  Calendar,
  SlidersHorizontal,
  Mic,
  Stethoscope,
  ShieldCheck,
} from 'lucide-react';
import { PatientProfile } from './PatientProfile';
import { MyAppointments } from './MyAppointments';
import { PatientPreferences } from './PatientPreferences';
import { VoiceAgentScreen } from './VoiceAgentScreen';
import { DoctorDiscovery } from './DoctorDiscovery';
import { useAuth } from '../../hooks/useAuth';

interface Props {
  initialTab?: string;
}

export const PatientPortal: React.FC<Props> = ({ initialTab = 'profile' }) => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'profile' | 'appointments' | 'preferences' | 'voice' | 'doctors'>(
    (initialTab as any) || 'profile'
  );

  useEffect(() => {
    if (initialTab && ['profile', 'appointments', 'preferences', 'voice', 'doctors'].includes(initialTab)) {
      setActiveTab(initialTab as any);
    }
  }, [initialTab]);

  const handleTabChange = (tab: typeof activeTab) => {
    setActiveTab(tab);
    window.location.hash = `/patient/${tab}`;
  };

  return (
    <div className="space-y-6">
      {/* Patient Header Strip */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shadow-lg">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center font-black text-lg">
            <User className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
              Patient Healthcare Portal
            </div>
            <h2 className="text-xl font-extrabold text-white">
              {user?.name || 'Alex Morgan'}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Verified Caller: <span className="font-mono text-slate-300">{user?.identifier || '+1-555-SHOULDER'}</span> &bull; {user?.hospital_name || 'City Memorial Hospital'}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold px-3 py-1.5 rounded-xl flex items-center space-x-1.5">
            <ShieldCheck className="w-4 h-4" />
            <span>HIPAA Encrypted Profile</span>
          </span>
        </div>
      </div>

      {/* Clean Sub-Page Navigation Tabs */}
      <div className="flex border-b border-slate-800 bg-slate-900/60 p-1 rounded-2xl gap-1.5 text-xs overflow-x-auto">
        <button
          onClick={() => handleTabChange('profile')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'profile'
              ? 'bg-emerald-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <User className="w-4 h-4" />
          <span>Patient Profile</span>
        </button>

        <button
          onClick={() => handleTabChange('appointments')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'appointments'
              ? 'bg-emerald-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Calendar className="w-4 h-4" />
          <span>Appointment History &amp; Visits</span>
        </button>

        <button
          onClick={() => handleTabChange('preferences')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'preferences'
              ? 'bg-emerald-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <SlidersHorizontal className="w-4 h-4" />
          <span>Notification Preferences</span>
        </button>

        <button
          onClick={() => handleTabChange('voice')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'voice'
              ? 'bg-emerald-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Mic className="w-4 h-4" />
          <span>AI Voice Intake &amp; Booking</span>
        </button>

        <button
          onClick={() => handleTabChange('doctors')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'doctors'
              ? 'bg-emerald-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Stethoscope className="w-4 h-4" />
          <span>Find Specialists</span>
        </button>
      </div>

      {/* Uncluttered Dedicated Sub-Page Content */}
      <div>
        {activeTab === 'profile' && <PatientProfile />}
        {activeTab === 'appointments' && (
          <MyAppointments onNavigateToDiscovery={() => handleTabChange('doctors')} />
        )}
        {activeTab === 'preferences' && <PatientPreferences />}
        {activeTab === 'voice' && <VoiceAgentScreen />}
        {activeTab === 'doctors' && (
          <DoctorDiscovery
            onBookingSuccess={() => {
              handleTabChange('appointments');
            }}
          />
        )}
      </div>
    </div>
  );
};
