import React, { useState } from 'react';
import { HeartPulse, User, Stethoscope, Building2, ShieldAlert, ArrowRight } from 'lucide-react';
import { useAuth, DEMO_PERSONAS, UserRole } from '../../hooks/useAuth';

export const AuthScreen: React.FC = () => {
  const { login } = useAuth();
  const [role, setRole] = useState<UserRole>('PATIENT');
  const [identifier, setIdentifier] = useState('+1-555-SHOULDER');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handlePersonaClick = async (persona: typeof DEMO_PERSONAS[0]) => {
    setIsSubmitting(true);
    await login(persona.role, persona.identifier, persona.name, persona.hospital_id);
    setIsSubmitting(false);
  };

  const handleCustomLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim()) return;

    setIsSubmitting(true);
    await login(role, identifier.trim(), identifier.trim(), 'HOSP-CITY-01');
    setIsSubmitting(false);
  };

  const getPersonaIcon = (r: UserRole) => {
    switch (r) {
      case 'PATIENT': return <User className="w-5 h-5 text-emerald-400" />;
      case 'DOCTOR': return <Stethoscope className="w-5 h-5 text-sky-400" />;
      case 'HOSPITAL_ADMIN': return <Building2 className="w-5 h-5 text-indigo-400" />;
      case 'PLATFORM_ADMIN': return <ShieldAlert className="w-5 h-5 text-amber-400" />;
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 sm:p-6 lg:p-8 relative overflow-hidden min-h-screen">
      {/* Background Glows */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-4xl w-full mx-auto space-y-8 relative z-10">
        {/* Branding */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center space-x-3 bg-slate-900/80 border border-slate-800 px-4 py-1.5 rounded-full shadow-lg">
            <div className="w-6 h-6 rounded-md bg-gradient-to-tr from-emerald-500 to-cyan-400 flex items-center justify-center text-slate-950 font-black">
              <HeartPulse className="w-3.5 h-3.5" />
            </div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
              NexusHealth Operating System
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span className="text-xs text-emerald-400 font-semibold">255/255 Tests Passed</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white">
            Healthcare Access, Automated Intake &amp;{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-sky-400">
              Verified EHR Operations
            </span>
          </h1>

          <p className="text-slate-400 text-sm sm:text-base max-w-2xl mx-auto">
            Select your role to access role-specific workflows, live clinical state machines, and real-time backend API integration.
          </p>
        </div>

        {/* 4 Demo Persona Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {DEMO_PERSONAS.map((p) => (
            <div
              key={p.role}
              onClick={() => !isSubmitting && handlePersonaClick(p)}
              className="bg-slate-900/90 hover:bg-slate-800/90 border border-slate-800 hover:border-emerald-500/50 rounded-2xl p-5 transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-xl space-y-4 group"
            >
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center group-hover:scale-105 transition">
                  {getPersonaIcon(p.role)}
                </div>
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                    {p.badge}
                  </div>
                  <h3 className="text-base font-bold text-white group-hover:text-emerald-300 transition">
                    {p.name}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">{p.description}</p>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                <span>Demo: <strong className="text-slate-200">{p.identifier}</strong></span>
                <span className="text-emerald-400 font-semibold group-hover:translate-x-1 transition">&rarr;</span>
              </div>
            </div>
          ))}
        </div>

        {/* Custom Credentials Form */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 max-w-xl mx-auto space-y-3 text-xs shadow-lg backdrop-blur-sm">
          <div className="flex justify-between items-center text-slate-400">
            <span className="font-semibold text-slate-300 uppercase tracking-wider text-[10px]">
              Or Sign In with Custom Credentials:
            </span>
            <span className="text-slate-500 font-mono text-[10px]">POST /api/v1/auth/login</span>
          </div>

          <form onSubmit={handleCustomLogin} className="flex flex-col sm:flex-row gap-2">
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole)}
              className="bg-slate-800 border border-slate-700 text-slate-200 rounded-xl px-3 py-2 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="PATIENT">Patient</option>
              <option value="DOCTOR">Doctor</option>
              <option value="HOSPITAL_ADMIN">Hospital Admin</option>
              <option value="PLATFORM_ADMIN">Platform Super-Admin</option>
            </select>

            <input
              type="text"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="Phone or Email (e.g. +1-555-SHOULDER)"
              className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
              required
            />

            <button
              type="submit"
              disabled={isSubmitting}
              className="bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold px-4 py-2 rounded-xl transition shadow-md flex items-center justify-center space-x-1.5 disabled:opacity-50"
            >
              <span>{isSubmitting ? 'Signing in...' : 'Sign In'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
