import React, { useState } from 'react';
import {
  HeartPulse,
  User,
  Stethoscope,
  Building2,
  ShieldAlert,
  LogOut,
  Layers,
  Activity,
  X,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { usePlatformEvents } from '../context/PlatformEventContext';

interface NavbarProps {
  isCatalogOpen: boolean;
  onToggleCatalog: () => void;
  activePortal: string;
  onSelectPortal: (portal: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  isCatalogOpen,
  onToggleCatalog,
  activePortal,
  onSelectPortal,
}) => {
  const { user, logout } = useAuth();
  const { events } = usePlatformEvents();
  const [isEventDrawerOpen, setIsEventDrawerOpen] = useState(false);

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
              onClick={() => onSelectPortal('patient')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition ${
                activePortal === 'patient' && !isCatalogOpen
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/60'
              }`}
            >
              <User className="w-3.5 h-3.5" />
              <span>Patient</span>
            </button>

            <button
              onClick={() => onSelectPortal('doctor')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition ${
                activePortal === 'doctor' && !isCatalogOpen
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/60'
              }`}
            >
              <Stethoscope className="w-3.5 h-3.5" />
              <span>Doctor</span>
            </button>

            <button
              onClick={() => onSelectPortal('hospital')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition ${
                activePortal === 'hospital' && !isCatalogOpen
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/60'
              }`}
            >
              <Building2 className="w-3.5 h-3.5" />
              <span>Hospital</span>
            </button>

            <button
              onClick={() => onSelectPortal('admin')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition ${
                activePortal === 'admin' && !isCatalogOpen
                  ? 'bg-amber-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/60'
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Platform SRE</span>
            </button>
          </div>

          {/* Living Event Pulse + 49-Page Catalog Toggle & User Session */}
          <div className="flex items-center space-x-2.5">
            {/* Real-Time Event Pulse Button */}
            <button
              onClick={() => setIsEventDrawerOpen(!isEventDrawerOpen)}
              className="text-xs px-2.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700/80 text-slate-300 hover:text-white flex items-center space-x-1.5 transition"
              title="Live Cross-Portal Event Stream"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <Activity className="w-3.5 h-3.5 text-emerald-400" />
              <span className="hidden sm:inline text-[11px] font-bold">Event Pulse</span>
              <span className="text-[10px] bg-slate-900 px-1.5 py-0.2 rounded font-mono text-emerald-400 font-bold">
                {events.length}
              </span>
            </button>

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

      {/* Live Event Stream Modal / Drawer */}
      {isEventDrawerOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-md bg-slate-900 border-l border-slate-800 h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
            <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/90">
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Live Cross-Portal Event Stream
                </span>
              </div>
              <button
                onClick={() => setIsEventDrawerOpen(false)}
                className="p-1 text-slate-400 hover:text-white rounded-lg transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-2.5 text-xs">
              {events.length === 0 ? (
                <div className="py-12 text-center text-slate-500">
                  Zero recent events. Perform an action (book slot, sign encounter, block slot) to
                  observe live cross-role synchronization.
                </div>
              ) : (
                events.map((evt) => (
                  <div
                    key={evt.id}
                    className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1 hover:border-emerald-500/30 transition"
                  >
                    <div className="flex justify-between items-center text-[10px]">
                      <span className="font-bold text-emerald-400 uppercase">{evt.type}</span>
                      <span className="text-slate-500">{evt.timestamp}</span>
                    </div>
                    <div className="font-bold text-white">{evt.title}</div>
                    <div className="text-[11px] text-slate-400">{evt.detail}</div>
                    <div className="text-[9px] text-slate-500 pt-1 font-mono">
                      Actor: {evt.actorRole}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
