import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiCall } from '../api/client';

export type UserRole = 'PATIENT' | 'DOCTOR' | 'HOSPITAL_ADMIN' | 'PLATFORM_ADMIN';

export interface UserSession {
  access_token: string;
  role: UserRole;
  user_id: string;
  name: string;
  identifier: string;
  hospital_id?: string;
  hospital_name?: string;
  patient_id?: string;
  doctor_id?: string;
  headers?: Record<string, string>;
}

export const DEMO_PERSONAS = [
  {
    role: 'PATIENT' as UserRole,
    identifier: '+1-555-SHOULDER',
    name: 'Patient A',
    hospital_id: 'HOSP-CITY-01',
    description: 'AI voice intake, clinical symptom triage, doctor search & verified booking.',
    color: 'emerald',
    badge: 'Patient Access',
  },
  {
    role: 'DOCTOR' as UserRole,
    identifier: 'DOC-SHARMA-01',
    name: 'Dr. Sharma',
    hospital_id: 'HOSP-CITY-01',
    description: 'Today\'s patient schedule, pre-visit intake briefs, working hours & calendar blocks.',
    color: 'sky',
    badge: 'Clinical Care',
  },
  {
    role: 'HOSPITAL_ADMIN' as UserRole,
    identifier: 'admin@citymemorial.org',
    name: 'Admin Connor',
    hospital_id: 'HOSP-CITY-01',
    description: 'Facility management, doctor rostering, FHIR/Epic connectors & anti-double-booking.',
    color: 'indigo',
    badge: 'Facility Ops',
  },
  {
    role: 'PLATFORM_ADMIN' as UserRole,
    identifier: 'admin@hospitalplatform.org',
    name: 'Platform Super-Admin',
    description: 'SRE 4 Golden Signals, 27-Stage DoD journey runner, 76-item audit & zero-PHI logs.',
    color: 'amber',
    badge: 'Platform Governance',
  },
];

interface AuthContextType {
  user: UserSession | null;
  login: (role: UserRole, identifier: string, defaultName?: string, hospitalId?: string) => Promise<boolean>;
  logout: () => void;
  activePortal: string;
  setActivePortal: (portal: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const SESSION_STORAGE_KEY = 'nexus_health_session';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserSession | null>(() => {
    try {
      const raw = sessionStorage.getItem(SESSION_STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });

  const [activePortal, setActivePortal] = useState<string>('patient');

  useEffect(() => {
    if (user) {
      if (user.role === 'DOCTOR') setActivePortal('doctor');
      else if (user.role === 'HOSPITAL_ADMIN') setActivePortal('hospital');
      else if (user.role === 'PLATFORM_ADMIN') setActivePortal('admin');
      else setActivePortal('patient');
    }
  }, [user?.role]);

  const login = async (role: UserRole, identifier: string, defaultName?: string, hospitalId = 'HOSP-CITY-01') => {
    try {
      const res = await apiCall('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          role,
          email_or_identifier: identifier,
          hospital_id: hospitalId,
        }),
      });

      if (res.ok && res.data) {
        const session: UserSession = {
          access_token: res.data.access_token || `token-${Date.now()}`,
          role,
          user_id: res.data.user_id || `user-${identifier}`,
          name: res.data.doctor_name || res.data.full_name || defaultName || identifier,
          identifier,
          hospital_id: res.data.hospital_id || hospitalId,
          hospital_name: res.data.hospital_name || 'City Memorial Hospital',
          patient_id: res.data.patient_id || identifier,
          doctor_id: res.data.doctor_id || identifier,
          headers: res.data.headers || { 'X-User-Role': role },
        };
        sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
        setUser(session);
        return true;
      } else {
        console.warn('Authentication rejected by platform:', res.error);
        return false;
      }
    } catch (e) {
      console.error('Login error:', e);
      return false;
    }
  };

  const logout = () => {
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, activePortal, setActivePortal }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
