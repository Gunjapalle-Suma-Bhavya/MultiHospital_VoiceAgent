import React from 'react';
import { useAuth } from './hooks/useAuth';
import { Navbar } from './components/Navbar';
import { AuthScreen } from './modules/auth/AuthScreen';
import { PatientPortal } from './modules/patient';
import { DoctorPortal } from './modules/doctor';
import { HospitalPortal } from './modules/hospital';
import { PlatformAdminPortal } from './modules/admin';

export const App: React.FC = () => {
  const { user, activePortal } = useAuth();

  if (!user) {
    return <AuthScreen />;
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {activePortal === 'patient' && <PatientPortal />}
        {activePortal === 'doctor' && <DoctorPortal />}
        {activePortal === 'hospital' && <HospitalPortal />}
        {activePortal === 'admin' && <PlatformAdminPortal />}
      </main>
    </div>
  );
};
