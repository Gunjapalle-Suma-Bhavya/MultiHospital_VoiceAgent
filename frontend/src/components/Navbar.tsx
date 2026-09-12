import React, { useState } from 'react';
import {
  HeartPulse,
  User,
  Stethoscope,
  Building2,
  ShieldAlert,
  LogOut,
  Layers,
  Sun,
  Moon,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useTheme } from '../context/ThemeContext';
import { useLanguage, SUPPORTED_LANGUAGES } from '../context/LanguageContext';

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
  const { theme, toggleTheme } = useTheme();
  const { language, setLanguage, currentOption } = useLanguage();
  const [isLangMenuOpen, setIsLangMenuOpen] = useState(false);

  if (!user) return null;

  return (
    <header className="bg-white border-b border-slate-200 dark:bg-slate-900 dark:border-slate-800 sticky top-0 z-40 shadow-md transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo */}
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center shadow-md text-slate-950">
              <HeartPulse className="w-5 h-5 font-black" />
            </div>
            <div>
              <span className="font-extrabold text-base tracking-tight text-slate-900 dark:text-white">
                Nexus<span className="text-emerald-500">Health</span>
              </span>
              <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 block -mt-1">
                {user.hospital_name || 'City Memorial Hospital'}
              </span>
            </div>
          </div>

          {/* Role / Portal Switcher */}
          <div className="hidden md:flex items-center space-x-1 bg-slate-100 dark:bg-slate-800/80 p-1 rounded-xl border border-slate-200 dark:border-slate-700/60 text-xs">
            <button
              onClick={() => onSelectPortal('patient')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition ${
                activePortal === 'patient' && !isCatalogOpen
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-700/60'
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
                  : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-700/60'
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
                  : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-700/60'
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
                  : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-700/60'
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Platform SRE</span>
            </button>
          </div>

          {/* Right Header Actions */}
          <div className="flex items-center space-x-2">
            {/* 49-Page Catalog Explorer Toggle: Restricted to PLATFORM_ADMIN Only */}
            {user.role === 'PLATFORM_ADMIN' && (
              <button
                onClick={onToggleCatalog}
                className={`text-xs font-bold px-3 py-1.5 rounded-xl border transition flex items-center space-x-1.5 shadow-sm ${
                  isCatalogOpen
                    ? 'bg-emerald-500 text-slate-950 border-emerald-400 font-extrabold'
                    : 'bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-emerald-600 dark:text-emerald-400 border-emerald-500/30'
                }`}
                title="Toggle Full 49-Page Dynamic Catalog (SRE Admin)"
              >
                <Layers className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">49-Page Catalog</span>
              </button>
            )}

            {/* Language Selector Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsLangMenuOpen(!isLangMenuOpen)}
                className="text-xs px-2.5 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 flex items-center space-x-1.5 transition shadow-sm"
                title="Change Platform Language"
              >
                <span>{currentOption.flag}</span>
                <span className="hidden sm:inline font-bold">{currentOption.code.toUpperCase()}</span>
              </button>
              {isLangMenuOpen && (
                <div className="absolute right-0 mt-2 w-36 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl py-1 z-50">
                  {SUPPORTED_LANGUAGES.map((lang) => (
                    <button
                      key={lang.code}
                      onClick={() => {
                        setLanguage(lang.code);
                        setIsLangMenuOpen(false);
                      }}
                      className={`w-full text-left px-3 py-1.5 text-xs flex items-center space-x-2 hover:bg-slate-100 dark:hover:bg-slate-800 transition ${
                        language === lang.code
                          ? 'text-emerald-600 dark:text-emerald-400 font-bold bg-slate-50 dark:bg-slate-800/60'
                          : 'text-slate-700 dark:text-slate-300'
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
              className="p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-amber-500 dark:text-amber-300 transition shadow-sm"
              title={`Switch to ${theme === 'dark' ? 'Clinical Light Mode' : 'Dark Mode'}`}
            >
              {theme === 'dark' ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5 text-sky-500" />}
            </button>

            {/* User Session Info */}
            <div className="text-right hidden xl:block pl-1">
              <div className="text-xs font-bold text-slate-900 dark:text-white flex items-center justify-end space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span>{user.name}</span>
              </div>
              <div className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">
                {user.role.replace('_', ' ')}
              </div>
            </div>

            <button
              onClick={logout}
              className="bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white border border-slate-200 dark:border-slate-700 text-xs font-semibold px-3 py-1.5 rounded-lg transition flex items-center space-x-1.5 shadow-sm"
              title="Sign Out / Switch Persona"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Switch</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
