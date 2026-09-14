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
  specialty?: string;
  department?: string;
  qualifications?: string;
  experience_years?: number;
  bio?: string;
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
  specialty?: string;
  department?: string;
  qualifications?: string;
  experienceYears?: number;
  bio?: string;
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
  ) => Promise<{
    success: boolean;
    error?: string;
    pendingApproval?: boolean;
    role?: string;
    hospitalId?: string;
    hospitalName?: string;
    doctorId?: string;
  }>;
  signUp: (params: SignUpParams) => Promise<{
    success: boolean;
    error?: string;
    pendingApproval?: boolean;
    message?: string;
    doctorId?: string;
    hospitalId?: string;
    hospitalName?: string;
    doctorData?: {
      name: string;
      email: string;
      specialty?: string;
      department?: string;
      qualifications?: string;
      experienceYears?: number;
      bio?: string;
    };
  }>;
  loginWithGoogle: (params: GoogleAuthParams) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  saveSession: (session: UserSession) => void;
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
  ): Promise<{
    success: boolean;
    error?: string;
    pendingApproval?: boolean;
    role?: string;
    hospitalId?: string;
    hospitalName?: string;
    doctorId?: string;
  }> => {
    try {
      const validRoles = ['PATIENT', 'DOCTOR', 'HOSPITAL_STAFF', 'HOSPITAL_ADMIN', 'PLATFORM_ADMIN'];
      const isLegacyCall = validRoles.includes(roleOrIdentifier);

      let payload: Record<string, any>;
      let expectedRole: UserRole = 'PATIENT';
      let expectedIdentifier = '';
      let expectedName = '';

      if (isLegacyCall) {
        expectedRole = roleOrIdentifier as UserRole;
        expectedIdentifier = identifierOrPassword || `user-${Date.now()}`;
        expectedName = defaultNameOrRole || expectedIdentifier;
        payload = {
          role: expectedRole,
          identifier: expectedIdentifier,
          name: expectedName,
          hospital_id: hospitalId,
        };
      } else {
        const inputId = roleOrIdentifier.trim();
        expectedIdentifier = inputId;
        const password = identifierOrPassword || '';
        const role = defaultNameOrRole as UserRole | undefined;

        payload = {
          email_or_identifier: inputId,
          identifier: inputId,
          password: password,
          hospital_id: hospitalId,
        };
        if (role) {
          payload.role = role;
          expectedRole = role;
        }
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
        const errObj = (typeof err === 'object' && err !== null ? err : {}) as Record<string, any>;
        const errStr = typeof err === 'string' ? err : (errObj.message || JSON.stringify(err));
        const isPending =
          res.status === 403 ||
          Boolean(errObj.is_pending_approval) ||
          errStr.includes('awaiting approval') ||
          errStr.includes('credentialing and approval') ||
          errStr.includes('inactive');

        console.warn('Authentication rejected by platform:', errStr);
        return {
          success: false,
          error: errStr,
          pendingApproval: isPending,
          role: errObj.role || expectedRole,
          hospitalId: errObj.hospital_id || hospitalId,
          hospitalName: errObj.hospital_name,
          doctorId: errObj.doctor_id,
        };
      }
    } catch (e: any) {
      console.error('Login error:', e);
      return { success: false, error: e?.message || 'Login failed due to a network error.' };
    }
  };

  const signUp = async (params: SignUpParams): Promise<{
    success: boolean;
    error?: string;
    pendingApproval?: boolean;
    message?: string;
    doctorId?: string;
    hospitalId?: string;
    hospitalName?: string;
    doctorData?: {
      name: string;
      email: string;
      specialty?: string;
      department?: string;
      qualifications?: string;
      experienceYears?: number;
      bio?: string;
    };
  }> => {
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
          specialty: params.specialty,
          department: params.department,
          qualifications: params.qualifications,
          experience_years: params.experienceYears,
          bio: params.bio,
        }),
      });

      if (res.ok && res.data) {
        if (res.data.is_pending_approval) {
          return {
            success: true,
            pendingApproval: true,
            message: res.data.message || 'Registration submitted and pending administrator approval.',
            doctorId: res.data.doctor_id,
            hospitalId: res.data.hospital_id,
            hospitalName: res.data.hospital_name,
            doctorData: {
              name: params.fullName,
              email: params.email,
              specialty: params.specialty || res.data.specialty,
              department: params.department || res.data.department,
              qualifications: params.qualifications || res.data.qualifications,
              experienceYears: params.experienceYears || res.data.experience_years,
              bio: params.bio || res.data.bio,
            },
          };
        }

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
        saveSession,
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
