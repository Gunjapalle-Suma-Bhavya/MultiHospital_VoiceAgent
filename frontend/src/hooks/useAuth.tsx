import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiCall } from '../api/client';

export type UserRole = 'PATIENT' | 'DOCTOR' | 'HOSPITAL_STAFF' | 'HOSPITAL_ADMIN' | 'PLATFORM_ADMIN';

export interface UserSession {
  access_token: string;
  role: UserRole;
  user_id: string;
  name: string;
  email?: string;
  identifier: string;
  hospital_id?: string;
  hospital_name?: string;
  patient_id?: string;
  doctor_id?: string;
  avatar_url?: string;
  auth_provider?: string;
  permissions?: string[];
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
    description: "Today's patient schedule, pre-visit intake briefs, working hours & calendar blocks.",
    color: 'sky',
    badge: 'Clinical Care',
  },
  {
    role: 'HOSPITAL_STAFF' as UserRole,
    identifier: 'staff@citymemorial.org',
    name: 'Staff Jordan',
    hospital_id: 'HOSP-CITY-01',
    description: 'Patient front desk reception, intake review & operational appointment coordination.',
    color: 'teal',
    badge: 'Hospital Staff',
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

export interface SignUpParams {
  email: string;
  password: string;
  fullName: string;
  role: UserRole;
  hospitalId?: string;
  phoneNumber?: string;
}

export interface GoogleAuthParams {
  googleId: string;
  email: string;
  name: string;
  avatarUrl?: string;
  role: UserRole;
  hospitalId?: string;
}

interface AuthContextType {
  user: UserSession | null;
  login: (
    roleOrIdentifier: string,
    identifierOrPassword?: string,
    defaultNameOrRole?: string,
    hospitalId?: string
  ) => Promise<{ success: boolean; error?: string }>;
  signUp: (params: SignUpParams) => Promise<{ success: boolean; error?: string }>;
  loginWithGoogle: (params: GoogleAuthParams) => Promise<{ success: boolean; error?: string }>;
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
      else if (user.role === 'HOSPITAL_ADMIN' || user.role === 'HOSPITAL_STAFF') setActivePortal('hospital');
      else if (user.role === 'PLATFORM_ADMIN') setActivePortal('admin');
      else setActivePortal('patient');
    }
  }, [user?.role]);

  const saveSession = (session: UserSession) => {
    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
    setUser(session);
  };

  const login = async (
    roleOrIdentifier: string,
    identifierOrPassword?: string,
    defaultNameOrRole?: string,
    hospitalId = 'HOSP-CITY-01'
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      const validRoles = ['PATIENT', 'DOCTOR', 'HOSPITAL_STAFF', 'HOSPITAL_ADMIN', 'PLATFORM_ADMIN'];
      const isLegacyCall = validRoles.includes(roleOrIdentifier);

      let payload: Record<string, any>;
      let expectedRole: UserRole = 'PATIENT';
      let expectedName = '';
      let expectedIdentifier = '';

      if (isLegacyCall) {
        expectedRole = roleOrIdentifier as UserRole;
        expectedIdentifier = identifierOrPassword || '';
        expectedName = defaultNameOrRole || expectedIdentifier;
        payload = {
          role: expectedRole,
          email_or_identifier: expectedIdentifier,
          hospital_id: hospitalId,
        };
      } else {
        expectedIdentifier = roleOrIdentifier;
        expectedRole = (defaultNameOrRole as UserRole) || 'PATIENT';
        payload = {
          email_or_identifier: expectedIdentifier,
          password: identifierOrPassword,
          role: defaultNameOrRole,
          hospital_id: hospitalId,
        };
      }

      const res = await apiCall('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      if (res.ok && res.data) {
        const raw = res.data.session || res.data;
        const assignedRole = (raw.role || expectedRole) as UserRole;
        const session: UserSession = {
          access_token: raw.access_token || `token-${Date.now()}`,
          role: assignedRole,
          user_id: raw.user_id || `user-${expectedIdentifier}`,
          name: raw.full_name || raw.name || raw.doctor_name || expectedName || expectedIdentifier,
          email: raw.email,
          identifier: expectedIdentifier || raw.email || raw.user_id,
          hospital_id: raw.hospital_id || hospitalId,
          hospital_name: raw.hospital_name || (hospitalId === 'HOSP-CARE-02' ? 'St. Jude Care Pavilion' : 'City Memorial Hospital'),
          patient_id: raw.patient_id || (assignedRole === 'PATIENT' ? expectedIdentifier : undefined),
          doctor_id: raw.doctor_id || (assignedRole === 'DOCTOR' ? expectedIdentifier : undefined),
          avatar_url: raw.avatar_url,
          auth_provider: raw.auth_provider || 'LOCAL',
          permissions: raw.permissions || [],
          headers: raw.headers || { 'X-User-Role': assignedRole },
        };
        saveSession(session);
        return { success: true };
      } else {
        const err = res.error || 'Invalid credentials or account not found.';
        console.warn('Authentication rejected by platform:', err);
        return { success: false, error: err };
      }
    } catch (e: any) {
      console.error('Login error:', e);
      return { success: false, error: e?.message || 'Login failed due to a network error.' };
    }
  };

  const signUp = async (params: SignUpParams): Promise<{ success: boolean; error?: string }> => {
    try {
      const res = await apiCall('/api/v1/auth/signup', {
        method: 'POST',
        body: JSON.stringify({
          email: params.email,
          password: params.password,
          full_name: params.fullName,
          role: params.role,
          hospital_id: params.hospitalId,
          phone_number: params.phoneNumber,
        }),
      });

      if (res.ok && res.data) {
        const raw = res.data.session || res.data;
        const session: UserSession = {
          access_token: raw.access_token || `token-${Date.now()}`,
          role: (raw.role || params.role) as UserRole,
          user_id: raw.user_id,
          name: raw.full_name || params.fullName,
          email: raw.email || params.email,
          identifier: raw.email || params.email,
          hospital_id: raw.hospital_id || params.hospitalId,
          hospital_name: raw.hospital_name || 'City Memorial Hospital',
          patient_id: raw.patient_id,
          doctor_id: raw.doctor_id,
          avatar_url: raw.avatar_url,
          auth_provider: 'LOCAL',
          permissions: raw.permissions || [],
          headers: raw.headers || { 'X-User-Role': params.role },
        };
        saveSession(session);
        return { success: true };
      } else {
        const err = res.error || 'Sign up failed. Please try again.';
        return { success: false, error: err };
      }
    } catch (e: any) {
      console.error('Sign up error:', e);
      return { success: false, error: e?.message || 'Network error during sign up.' };
    }
  };

  const loginWithGoogle = async (params: GoogleAuthParams): Promise<{ success: boolean; error?: string }> => {
    try {
      const res = await apiCall('/api/v1/auth/google', {
        method: 'POST',
        body: JSON.stringify({
          google_id: params.googleId,
          email: params.email,
          name: params.name,
          avatar_url: params.avatarUrl,
          role: params.role,
          hospital_id: params.hospitalId,
        }),
      });

      if (res.ok && res.data) {
        const raw = res.data.session || res.data;
        const session: UserSession = {
          access_token: raw.access_token || `token-google-${Date.now()}`,
          role: (raw.role || params.role) as UserRole,
          user_id: raw.user_id,
          name: raw.full_name || params.name,
          email: raw.email || params.email,
          identifier: raw.email || params.email,
          hospital_id: raw.hospital_id || params.hospitalId,
          hospital_name: raw.hospital_name || 'City Memorial Hospital',
          patient_id: raw.patient_id,
          doctor_id: raw.doctor_id,
          avatar_url: raw.avatar_url || params.avatarUrl,
          auth_provider: 'GOOGLE',
          permissions: raw.permissions || [],
          headers: raw.headers || { 'X-User-Role': params.role },
        };
        saveSession(session);
        return { success: true };
      } else {
        const err = res.error || 'Google authentication failed.';
        return { success: false, error: err };
      }
    } catch (e: any) {
      console.error('Google login error:', e);
      return { success: false, error: e?.message || 'Network error during Google login.' };
    }
  };

  const logout = () => {
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        signUp,
        loginWithGoogle,
        logout,
        activePortal,
        setActivePortal,
      }}
    >
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
