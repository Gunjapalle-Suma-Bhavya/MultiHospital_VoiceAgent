import React, { useState, useEffect } from 'react';
import {
  Mic,
  Stethoscope,
  Calendar,
  ClipboardList,
  Bell,
  ShieldCheck,
  User,
} from 'lucide-react';
import { VoiceAgentScreen } from './VoiceAgentScreen';
import { DoctorDiscovery } from './DoctorDiscovery';
import { QuestionnaireForm } from './QuestionnaireForm';
import { MyAppointments } from './MyAppointments';
import { PatientNotifications } from './PatientNotifications';
import { useAuth } from '../../hooks/useAuth';

interface Props {
  initialTab?: string;
}

export const PatientPortal: React.FC<Props> = ({ initialTab = 'voice' }) => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'voice' | 'doctors' | 'appointments' | 'intake' | 'notifications'>(
    (initialTab as any) || 'voice'
  );

  useEffect(() => {
    if (initialTab && ['voice', 'doctors', 'appointments', 'intake', 'notifications'].includes(initialTab)) {
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
              Patient Self-Service Workspace
            </div>
            <h2 className="text-xl font-extrabold text-white">
              {user?.name || 'Marcus Aurelius'}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Verified Caller: <span className="font-mono text-slate-300">{user?.identifier || '+1-555-SHOULDER'}</span> &bull; City Memorial Hospital
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold px-3 py-1.5 rounded-xl flex items-center space-x-1.5">
            <ShieldCheck className="w-4 h-4" />
            <span>HIPAA Verified Record</span>
          </span>
        </div>
      </div>

      {/* Clean Sub-Page Navigation Tabs */}
      <div className="flex border-b border-slate-800 bg-slate-900/60 p-1 rounded-2xl gap-1.5 text-xs overflow-x-auto">
        <button
          onClick={() => handleTabChange('voice')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'voice'
              ? 'bg-emerald-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Mic className="w-4 h-4" />
          <span>AI Voice Intake</span>
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

        <button
          onClick={() => handleTabChange('appointments')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'appointments'
              ? 'bg-emerald-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Calendar className="w-4 h-4" />
          <span>My Visits &amp; Care Pass</span>
        </button>

        <button
          onClick={() => handleTabChange('intake')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'intake'
              ? 'bg-emerald-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <ClipboardList className="w-4 h-4" />
          <span>Intake Form</span>
        </button>

        <button
          onClick={() => handleTabChange('notifications')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'notifications'
              ? 'bg-emerald-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Bell className="w-4 h-4" />
          <span>Dispatched Alerts</span>
        </button>
      </div>

      {/* Uncluttered Dedicated Sub-Page Content */}
      <div>
        {activeTab === 'voice' && <VoiceAgentScreen />}
        {activeTab === 'doctors' && (
          <DoctorDiscovery
            onBookingSuccess={() => {
              handleTabChange('appointments');
            }}
          />
        )}
        {activeTab === 'appointments' && (
          <MyAppointments onNavigateToDiscovery={() => handleTabChange('doctors')} />
        )}
        {activeTab === 'intake' && <QuestionnaireForm />}
        {activeTab === 'notifications' && <PatientNotifications />}
      </div>
    </div>
  );
};
