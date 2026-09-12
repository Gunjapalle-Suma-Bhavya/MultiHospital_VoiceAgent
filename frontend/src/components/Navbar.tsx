import React, { useState, useEffect } from 'react';
import {
  HeartPulse,
  User,
  Stethoscope,
  Building2,
  ShieldAlert,
  LogOut,
  Layers,
  Activity,
  Database,
  RefreshCw,
  X,
  CheckCircle2,
  Sun,
  Moon,
  Globe,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { usePlatformEvents } from '../context/PlatformEventContext';
import { useTheme } from '../context/ThemeContext';
import { useLanguage, SUPPORTED_LANGUAGES } from '../context/LanguageContext';

interface NavbarProps {
  isCatalogOpen: boolean;
  onToggleCatalog: () => void;
  activePortal: string;
  onSelectPortal: (portal: string) => void;
}

interface MongoStatus {
  connected: boolean;
  database: string;
  collections: Record<string, number>;
}

export const Navbar: React.FC<NavbarProps> = ({
  isCatalogOpen,
  onToggleCatalog,
  activePortal,
  onSelectPortal,
}) => {
  const { user, logout } = useAuth();
  const { events } = usePlatformEvents();
  const { theme, toggleTheme } = useTheme();
  const { language, setLanguage, currentOption } = useLanguage();
  const [isLangMenuOpen, setIsLangMenuOpen] = useState(false);
  const [isEventDrawerOpen, setIsEventDrawerOpen] = useState(false);
  const [isMongoModalOpen, setIsMongoModalOpen] = useState(false);
  const [mongoStatus, setMongoStatus] = useState<MongoStatus | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);

  const fetchMongoStatus = async () => {
    try {
      const res = await fetch('/api/v1/mongodb/status');
      if (res.ok) {
        const data = await res.json();
        setMongoStatus(data);
      }
    } catch {
      // Fallback
    }
  };

  useEffect(() => {
    fetchMongoStatus();
    const interval = setInterval(fetchMongoStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleSeedMongo = async () => {
    setIsSyncing(true);
    try {
      await fetch('/api/v1/mongodb/seed', { method: 'POST' });
      await fetchMongoStatus();
    } finally {
      setIsSyncing(false);
    }
  };

  if (!user) return null;

  const totalMongoDocs = mongoStatus?.collections
    ? Object.values(mongoStatus.collections).reduce((a, b) => a + b, 0)
    : 0;

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

          {/* MongoDB Atlas Sync + Event Pulse + User Session */}
          <div className="flex items-center space-x-2">
            {/* MongoDB Atlas Live Badge */}
            <button
              onClick={() => setIsMongoModalOpen(true)}
              className={`text-xs px-2.5 py-1.5 rounded-xl border flex items-center space-x-1.5 transition ${
                mongoStatus?.connected
                  ? 'bg-emerald-950/60 hover:bg-emerald-900/60 text-emerald-400 border-emerald-500/40'
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700'
              }`}
              title="MongoDB Atlas JSON Document Store"
            >
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              <span className="hidden sm:inline font-bold">MongoDB Atlas</span>
              {mongoStatus?.connected && (
                <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-1.5 py-0.2 rounded-full font-mono font-bold border border-emerald-500/30">
                  {totalMongoDocs} docs
                </span>
              )}
            </button>

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

            {/* 49-Page Catalog Explorer Toggle */}
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
            </button>

            {/* Language Selector Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsLangMenuOpen(!isLangMenuOpen)}
                className="text-xs px-2.5 py-1.5 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 flex items-center space-x-1.5 transition shadow-sm"
                title="Change Platform Language"
              >
                <span>{currentOption.flag}</span>
                <span className="hidden sm:inline font-bold">{currentOption.code.toUpperCase()}</span>
              </button>
              {isLangMenuOpen && (
                <div className="absolute right-0 mt-2 w-36 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl py-1 z-50">
                  {SUPPORTED_LANGUAGES.map((lang) => (
                    <button
                      key={lang.code}
                      onClick={() => {
                        setLanguage(lang.code);
                        setIsLangMenuOpen(false);
                      }}
                      className={`w-full text-left px-3 py-1.5 text-xs flex items-center space-x-2 hover:bg-slate-800 transition ${
                        language === lang.code ? 'text-emerald-400 font-bold bg-slate-800/60' : 'text-slate-300'
                      }`}
                    >
                      <span>{lang.flag}</span>
                      <span>{lang.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Clinical Light / Dark Mode Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-amber-400 hover:text-amber-300 transition shadow-sm"
              title={`Switch to ${theme === 'dark' ? 'Clinical Light Mode' : 'Dark Mode'}`}
            >
              {theme === 'dark' ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5 text-sky-400" />}
            </button>

            <div className="text-right hidden xl:block pl-1">
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
              <span className="hidden sm:inline">Switch</span>
            </button>
          </div>
        </div>
      </div>

      {/* MongoDB Atlas Modal */}
      {isMongoModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-150">
            <div className="p-5 border-b border-slate-800 flex justify-between items-center bg-slate-900/90">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center">
                  <Database className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-bold text-sm text-white">MongoDB Atlas Cloud Store</h3>
                  <p className="text-[11px] text-slate-400">Live JSON documents interconnected across all portals</p>
                </div>
              </div>
              <button
                onClick={() => setIsMongoModalOpen(false)}
                className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-4">
              <div className="flex items-center justify-between p-3 bg-slate-950 border border-emerald-500/30 rounded-xl">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-semibold text-white">Connected to Cluster</span>
                </div>
                <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 rounded font-medium">
                  {mongoStatus?.database || 'nexushealth_hospital_db'}
                </span>
              </div>

              <div>
                <span className="text-xs font-semibold text-slate-300 block mb-2">Live Collections & Documents</span>
                <div className="grid grid-cols-2 gap-2">
                  {mongoStatus?.collections &&
                    Object.entries(mongoStatus.collections).map(([col, count]) => (
                      <div key={col} className="p-2.5 bg-slate-950 border border-slate-800 rounded-lg flex justify-between items-center">
                        <span className="text-xs font-medium text-slate-300 capitalize">{col}</span>
                        <span className="text-xs font-mono font-bold text-emerald-400 bg-slate-900 border border-slate-700 px-2 py-0.5 rounded">
                          {count} JSON
                        </span>
                      </div>
                    ))}
                </div>
              </div>

              <div className="pt-2 flex justify-between items-center border-t border-slate-800">
                <button
                  onClick={handleSeedMongo}
                  disabled={isSyncing}
                  className="flex items-center space-x-2 text-xs font-semibold px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl transition disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
                  <span>{isSyncing ? 'Syncing...' : 'Resync Live Baseline Data'}</span>
                </button>
                <button
                  onClick={() => setIsMongoModalOpen(false)}
                  className="text-xs font-medium text-slate-400 hover:text-white px-3 py-2"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

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
                  Zero recent events. Perform an action (book slot, update schedule, submit questionnaire) to observe live cross-role synchronization.
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
