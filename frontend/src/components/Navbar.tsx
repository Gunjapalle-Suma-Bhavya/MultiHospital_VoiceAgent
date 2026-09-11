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
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { usePlatformEvents } from '../context/PlatformEventContext';

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
      // Fallback if offline
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
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-teal-600 flex items-center justify-center shadow-xs text-white">
              <HeartPulse className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-base tracking-tight text-slate-900 flex items-center space-x-1.5">
                <span>Nexus</span>
                <span className="text-teal-600">Health</span>
              </div>
              <span className="text-[11px] font-medium text-slate-500 block -mt-0.5">
                {user.hospital_name || 'City Memorial Hospital'}
              </span>
            </div>
          </div>

          {/* Role / Portal Switcher */}
          <div className="hidden md:flex items-center space-x-1 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
            <button
              onClick={() => onSelectPortal('patient')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
                activePortal === 'patient' && !isCatalogOpen
                  ? 'bg-white text-teal-700 shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
              }`}
            >
              <User className="w-3.5 h-3.5 text-teal-600" />
              <span>Patient Portal</span>
            </button>

            <button
              onClick={() => onSelectPortal('doctor')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
                activePortal === 'doctor' && !isCatalogOpen
                  ? 'bg-white text-blue-700 shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
              }`}
            >
              <Stethoscope className="w-3.5 h-3.5 text-blue-600" />
              <span>Physician Station</span>
            </button>

            <button
              onClick={() => onSelectPortal('hospital')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
                activePortal === 'hospital' && !isCatalogOpen
                  ? 'bg-white text-indigo-700 shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
              }`}
            >
              <Building2 className="w-3.5 h-3.5 text-indigo-600" />
              <span>Hospital Ops</span>
            </button>

            <button
              onClick={() => onSelectPortal('admin')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
                activePortal === 'admin' && !isCatalogOpen
                  ? 'bg-white text-amber-800 shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
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
                  ? 'bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border-emerald-200'
                  : 'bg-slate-50 hover:bg-slate-100 text-slate-600 border-slate-200'
              }`}
              title="MongoDB Atlas JSON Document Store"
            >
              <Database className="w-3.5 h-3.5 text-emerald-600" />
              <span className="hidden sm:inline font-semibold">MongoDB Atlas</span>
              {mongoStatus?.connected && (
                <span className="text-[10px] bg-emerald-200/60 text-emerald-900 px-1.5 py-0.5 rounded-full font-mono font-bold">
                  {totalMongoDocs} docs
                </span>
              )}
            </button>

            {/* Real-Time Event Pulse Button */}
            <button
              onClick={() => setIsEventDrawerOpen(!isEventDrawerOpen)}
              className="text-xs px-2.5 py-1.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 flex items-center space-x-1.5 transition"
              title="Live Cross-Portal Event Stream"
            >
              <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
              <Activity className="w-3.5 h-3.5 text-teal-600" />
              <span className="hidden sm:inline font-medium text-[11px]">Sync Pulse</span>
              <span className="text-[10px] bg-slate-200 px-1.5 py-0.5 rounded font-mono font-bold text-slate-800">
                {events.length}
              </span>
            </button>

            {/* 49-Page Catalog Explorer Toggle */}
            <button
              onClick={onToggleCatalog}
              className={`text-xs font-semibold px-3 py-1.5 rounded-xl border transition flex items-center space-x-1.5 shadow-xs ${
                isCatalogOpen
                  ? 'bg-teal-600 text-white border-teal-700'
                  : 'bg-slate-50 hover:bg-slate-100 text-teal-800 border-teal-200'
              }`}
              title="49-Page Catalog Explorer"
            >
              <Layers className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">49-Page Catalog</span>
            </button>

            <div className="text-right hidden xl:block pl-1">
              <div className="text-xs font-bold text-slate-900 flex items-center justify-end space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-teal-500" />
                <span>{user.name}</span>
              </div>
              <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                {user.role.replace('_', ' ')}
              </div>
            </div>

            <button
              onClick={logout}
              className="bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 text-xs font-medium px-3 py-1.5 rounded-xl transition flex items-center space-x-1.5"
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
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-white border border-slate-200 rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in duration-150">
            <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/70">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center">
                  <Database className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-bold text-sm text-slate-900">MongoDB Atlas Cloud Store</h3>
                  <p className="text-[11px] text-slate-500">Live JSON documents interconnected across portals</p>
                </div>
              </div>
              <button
                onClick={() => setIsMongoModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-4">
              <div className="flex items-center justify-between p-3 bg-emerald-50/60 border border-emerald-200 rounded-xl">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span className="text-xs font-semibold text-emerald-900">Connected to Cluster</span>
                </div>
                <span className="text-[11px] font-mono text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded font-medium">
                  {mongoStatus?.database || 'nexushealth_hospital_db'}
                </span>
              </div>

              <div>
                <span className="text-xs font-semibold text-slate-700 block mb-2">Live Collections & Documents</span>
                <div className="grid grid-cols-2 gap-2">
                  {mongoStatus?.collections &&
                    Object.entries(mongoStatus.collections).map(([col, count]) => (
                      <div key={col} className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg flex justify-between items-center">
                        <span className="text-xs font-medium text-slate-700 capitalize">{col}</span>
                        <span className="text-xs font-mono font-bold text-teal-700 bg-teal-50 border border-teal-200 px-2 py-0.5 rounded">
                          {count} JSON
                        </span>
                      </div>
                    ))}
                </div>
              </div>

              <div className="pt-2 flex justify-between items-center border-t border-slate-100">
                <button
                  onClick={handleSeedMongo}
                  disabled={isSyncing}
                  className="flex items-center space-x-2 text-xs font-semibold px-3 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl transition disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
                  <span>{isSyncing ? 'Syncing...' : 'Resync Live Baseline Data'}</span>
                </button>
                <button
                  onClick={() => setIsMongoModalOpen(false)}
                  className="text-xs font-medium text-slate-600 hover:text-slate-800 px-3 py-2"
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
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-md bg-white border-l border-slate-200 h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
            <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-teal-600" />
                <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Live Cross-Portal Event Stream
                </span>
              </div>
              <button
                onClick={() => setIsEventDrawerOpen(false)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-lg transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-2.5 text-xs">
              {events.length === 0 ? (
                <div className="py-12 text-center text-slate-400">
                  Zero recent events. Perform an action (book slot, update schedule, submit questionnaire) to observe live cross-role synchronization.
                </div>
              ) : (
                events.map((evt) => (
                  <div
                    key={evt.id}
                    className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1 hover:border-teal-300 transition"
                  >
                    <div className="flex justify-between items-center text-[10px]">
                      <span className="font-bold text-teal-700 uppercase">{evt.type}</span>
                      <span className="text-slate-400">{evt.timestamp}</span>
                    </div>
                    <div className="font-semibold text-slate-900">{evt.title}</div>
                    <div className="text-[11px] text-slate-600">{evt.detail}</div>
                    <div className="text-[10px] text-slate-400 pt-1 font-mono">
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
