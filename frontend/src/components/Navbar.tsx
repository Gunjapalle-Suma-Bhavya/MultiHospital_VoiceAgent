import React from 'react';
import { HeartPulse, User, Stethoscope, Building2, ShieldAlert, LogOut, Layers } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

interface NavbarProps {
  isCatalogOpen: boolean;
  onToggleCatalog: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ isCatalogOpen, onToggleCatalog }) => {
  const { user, logout, activePortal, setActivePortal } = useAuth();

  if (!user) return null;

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-40 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center shadow-md text-slate-950">
              <HeartPulse className="w-5 h-5 font-black" />
            </div>
            <div>
              <span className="font-extrabold text-base tracking-tight text-white">
                Nexus<span className="text-emerald-400">Health</span>
              </span>
              <span className="text-[10px] font-bold text-slate-400 block -mt-1">
                {user.hospital_name || 'City Memorial Hospital'}
              </span>
            </div>
          </div>

          {/* Role / Portal Switcher */}
          <div className="hidden md:flex items-center space-x-1 bg-slate-800/80 p-1 rounded-xl border border-slate-700/60 text-xs">
            <button
              onClick={() => setActivePortal('patient')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition ${
                activePortal === 'patient'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/60'
              }`}
            >
              <User className="w-3.5 h-3.5" />
              <span>Patient</span>
            </button>

            <button
              onClick={() => setActivePortal('doctor')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition ${
                activePortal === 'doctor'
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/60'
              }`}
            >
              <Stethoscope className="w-3.5 h-3.5" />
              <span>Doctor</span>
            </button>

            <button
              onClick={() => setActivePortal('hospital')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition ${
                activePortal === 'hospital'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/60'
              }`}
            >
              <Building2 className="w-3.5 h-3.5" />
              <span>Hospital</span>
            </button>

            <button
              onClick={() => setActivePortal('admin')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition ${
                activePortal === 'admin'
                  ? 'bg-amber-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/60'
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Platform SRE</span>
            </button>
          </div>

          {/* 49-Page Catalog Toggle & User Session */}
          <div className="flex items-center space-x-2.5">
            <button
              onClick={onToggleCatalog}
              className={`text-xs font-bold px-3 py-1.5 rounded-xl border transition flex items-center space-x-1.5 shadow-sm ${
                isCatalogOpen
                  ? 'bg-emerald-500 text-slate-950 border-emerald-400 font-extrabold'
                  : 'bg-slate-800 hover:bg-slate-700 text-emerald-400 border-emerald-500/30'
              }`}
              title="Toggle Full 49-Page Dynamic Catalog"
            >
              <Layers className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">49-Page Catalog</span>
              <span className="text-[10px] font-mono bg-slate-900/60 px-1 py-0.2 rounded">49</span>
            </button>

            <div className="text-right hidden lg:block">
              <div className="text-xs font-bold text-white flex items-center justify-end space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span>{user.name}</span>
              </div>
              <div className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider">
                {user.role.replace('_', ' ')}
              </div>
            </div>

            <button
              onClick={logout}
              className="bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs font-semibold px-3 py-1.5 rounded-lg transition flex items-center space-x-1.5 shadow-sm"
              title="Sign Out / Switch Persona"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Switch Role</span>
            </button>
          </div>

        </div>
      </div>
    </header>
  );
};
