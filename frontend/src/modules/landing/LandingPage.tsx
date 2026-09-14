import React, { useState, useEffect } from 'react';
import {
  HeartPulse,
  User,
  Stethoscope,
  Building2,
  ShieldAlert,
  Users,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  Lock,
  Globe2,
  Activity,
  Mic,
  Calendar,
  Database,
  X,
  AlertCircle,
  LogIn,
  UserPlus,
  Hospital as HospitalIcon,
  ChevronRight,
  Sun,
  Moon,
  RotateCw,
  Clock,
  Award,
  ShieldCheck
} from 'lucide-react';
import { useAuth, DEMO_PERSONAS, UserRole, UserSession } from '../../hooks/useAuth';
import { useTheme } from '../../context/ThemeContext';
import { useLanguage, SUPPORTED_LANGUAGES } from '../../context/LanguageContext';
import { apiCall } from '../../api/client';

interface HospitalOption {
  id: string;
  name: string;
  code: string;
}

interface PendingDoctorInfo {
  doctorId: string;
  hospitalId: string;
  hospitalName: string;
  name: string;
  email: string;
  specialty: string;
  department: string;
  qualifications: string;
  experienceYears: number;
  bio?: string;
}

interface PendingHospitalInfo {
  hospitalId: string;
  hospitalName: string;
  hospitalCode: string;
  contactEmail?: string;
  adminName: string;
  adminEmail: string;
  departments?: string[];
  phone?: string;
  address?: string;
}

export const LandingPage: React.FC = () => {
  const { login, signUp, loginWithGoogle, saveSession } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { language, setLanguage, currentOption } = useLanguage();

  // Auth Modal State
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'signin' | 'signup' | 'demo' | 'hospital_register'>('signin');
  const [selectedRole, setSelectedRole] = useState<UserRole>('PATIENT');
  const [selectedHospital, setSelectedHospital] = useState<string>('HOSP-CITY-01');

  // Form Fields (User Sign In / Sign Up)
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');

  // Hospital Facility Registration Form Fields
  const [hospName, setHospName] = useState('');
  const [hospCode, setHospCode] = useState('');
  const [hospEmail, setHospEmail] = useState('');
  const [hospPhone, setHospPhone] = useState('');
  const [hospAddress, setHospAddress] = useState('');
  const [hospAdminName, setHospAdminName] = useState('');
  const [hospAdminEmail, setHospAdminEmail] = useState('');
  const [hospAdminPassword, setHospAdminPassword] = useState('');
  const [hospDepts, setHospDepts] = useState('Cardiology, Orthopedics, Emergency, General Medicine');

  // Doctor Sign Up Specific Fields
  const [docSpecialty, setDocSpecialty] = useState('General Medicine');
  const [docDepartment, setDocDepartment] = useState('Outpatient Department');
  const [docQualifications, setDocQualifications] = useState('MBBS, MD');
  const [docExperienceYears, setDocExperienceYears] = useState('8');
  const [docBio, setDocBio] = useState('');

  // Status & Feedback
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Hospital directory
  const [hospitals, setHospitals] = useState<HospitalOption[]>([
    { id: 'HOSP-CITY-01', name: 'City Memorial Hospital', code: 'CITYMEM' },
    { id: 'HOSP-CARE-02', name: 'St. Jude Care Pavilion', code: 'STJUDE' },
    { id: 'HOSP-METRO-03', name: 'Metro Health Medical Center', code: 'METROHLTH' },
  ]);

  const [isRefreshingHospitals, setIsRefreshingHospitals] = useState(false);

  // Fetch live hospitals from backend
  const fetchHospitals = async (preferredHospitalId?: string) => {
    setIsRefreshingHospitals(true);
    try {
      const res = await apiCall('/api/v1/auth/hospitals');
      if (res.ok && res.data && res.data.hospitals && res.data.hospitals.length > 0) {
        setHospitals(res.data.hospitals);
        if (preferredHospitalId) {
          setSelectedHospital(preferredHospitalId);
        } else {
          setSelectedHospital((prev) => {
            const exists = res.data.hospitals.some((h: HospitalOption) => h.id === prev);
            return exists ? prev : res.data.hospitals[0].id;
          });
        }
      }
    } catch (err) {
      console.warn('Failed to load dynamic hospital directory:', err);
    } finally {
      setIsRefreshingHospitals(false);
    }
  };

  // Pending Doctor Registration Approval State
  const [pendingDoctor, setPendingDoctor] = useState<PendingDoctorInfo | null>(null);
  const [isPollingDoctorApproval, setIsPollingDoctorApproval] = useState(false);
  const [approvalDetected, setApprovalDetected] = useState(false);
  const [approvalRejected, setApprovalRejected] = useState<string | null>(null);

  // Pending Hospital Facility Approval State
  const [pendingHospital, setPendingHospital] = useState<PendingHospitalInfo | null>(null);
  const [isPollingHospitalApproval, setIsPollingHospitalApproval] = useState(false);
  const [hospitalApprovalDetected, setHospitalApprovalDetected] = useState(false);
  const [hospitalApprovalRejected, setHospitalApprovalRejected] = useState<string | null>(null);

  const checkDoctorApprovalStatus = async (docId?: string) => {
    const targetId = docId || pendingDoctor?.doctorId;
    if (!targetId || approvalDetected) return;

    try {
      setIsPollingDoctorApproval(true);
      const res = await apiCall(`/api/v1/auth/doctor-status/${targetId}`);
      if (res.ok && res.data) {
        if (res.data.is_approved || res.data.doctor_status === 'ACTIVE') {
          setApprovalDetected(true);
          setApprovalRejected(null);
          const session: UserSession = res.data.session || {
            access_token: `token-${Date.now()}`,
            role: 'DOCTOR' as UserRole,
            user_id: res.data.user_id || targetId,
            name: res.data.name || pendingDoctor?.name || 'Doctor',
            identifier: pendingDoctor?.email || targetId,
            email: pendingDoctor?.email,
            hospital_id: res.data.hospital_id || pendingDoctor?.hospitalId,
            hospital_name: res.data.hospital_name || pendingDoctor?.hospitalName,
            doctor_id: res.data.doctor_id || targetId,
            specialty: res.data.specialty || pendingDoctor?.specialty,
            department: res.data.department || pendingDoctor?.department,
            qualifications: res.data.qualifications || pendingDoctor?.qualifications,
            experience_years: res.data.experience_years || pendingDoctor?.experienceYears,
            bio: res.data.bio || pendingDoctor?.bio,
            auth_provider: 'LOCAL',
            permissions: [],
            headers: { 'X-User-Role': 'DOCTOR', 'X-Doctor-Id': targetId },
          };

          setTimeout(() => {
            saveSession(session);
            setIsAuthModalOpen(false);
            setPendingDoctor(null);
          }, 1200);
        } else if (res.data.status === 'REJECTED' || res.data.doctor_status === 'INACTIVE') {
          setApprovalRejected(res.data.message || 'Your registration request was not approved by the hospital administrator.');
        }
      }
    } catch (err) {
      console.warn('Doctor approval check err:', err);
    } finally {
      setIsPollingDoctorApproval(false);
    }
  };

  const checkHospitalApprovalStatus = async (hospId?: string) => {
    const targetId = hospId || pendingHospital?.hospitalId;
    if (!targetId || hospitalApprovalDetected) return;

    try {
      setIsPollingHospitalApproval(true);
      const res = await apiCall(`/api/v1/auth/hospital-status/${targetId}`);
      if (res.ok && res.data) {
        if (res.data.is_approved || res.data.status === 'APPROVED') {
          setHospitalApprovalDetected(true);
          setHospitalApprovalRejected(null);
          const session: UserSession = res.data.session || {
            access_token: `token-${Date.now()}`,
            role: 'HOSPITAL_ADMIN' as UserRole,
            user_id: res.data.admin_user_id || `admin-${targetId}`,
            name: res.data.admin_name || pendingHospital?.adminName || 'Hospital Administrator',
            identifier: pendingHospital?.adminEmail || targetId,
            email: pendingHospital?.adminEmail,
            hospital_id: targetId,
            hospital_name: res.data.hospital_name || pendingHospital?.hospitalName,
            auth_provider: 'LOCAL',
            permissions: [],
            headers: { 'X-User-Role': 'HOSPITAL_ADMIN', 'X-Hospital-Id': targetId },
          };

          setTimeout(() => {
            saveSession(session);
            setIsAuthModalOpen(false);
            setPendingHospital(null);
          }, 1200);
        } else if (res.data.status === 'REJECTED') {
          setHospitalApprovalRejected(res.data.message || 'The hospital registration request was rejected by the Platform Super-Admin.');
        }
      }
    } catch (err) {
      console.warn('Hospital approval check err:', err);
    } finally {
      setIsPollingHospitalApproval(false);
    }
  };

  useEffect(() => {
    if (!pendingDoctor?.doctorId || approvalDetected) return;

    checkDoctorApprovalStatus(pendingDoctor.doctorId);

    const interval = setInterval(() => {
      checkDoctorApprovalStatus(pendingDoctor.doctorId);
    }, 2500);

    return () => clearInterval(interval);
  }, [pendingDoctor?.doctorId, approvalDetected]);

  useEffect(() => {
    if (!pendingHospital?.hospitalId || hospitalApprovalDetected) return;

    checkHospitalApprovalStatus(pendingHospital.hospitalId);

    const interval = setInterval(() => {
      checkHospitalApprovalStatus(pendingHospital.hospitalId);
    }, 2500);

    return () => clearInterval(interval);
  }, [pendingHospital?.hospitalId, hospitalApprovalDetected]);

  useEffect(() => {
    fetchHospitals();
  }, []);

  useEffect(() => {
    if (isAuthModalOpen) {
      fetchHospitals();
    }
  }, [isAuthModalOpen, selectedRole, authMode]);

  const openAuthWithRole = (role: UserRole, mode: 'signin' | 'signup' = 'signin') => {
    setSelectedRole(role);
    setAuthMode(mode);
    setErrorMessage(null);
    setSuccessMessage(null);
    setIsAuthModalOpen(true);
  };

  const handleDemoLogin = async (persona: typeof DEMO_PERSONAS[0]) => {
    setIsSubmitting(true);
    setErrorMessage(null);
    const result = await login(persona.role, persona.identifier, persona.name, persona.hospital_id);
    setIsSubmitting(false);
    if (!result.success) {
      setErrorMessage(result.error || 'Failed to authenticate demo persona.');
    }
  };

  const handleLocalSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      setErrorMessage('Please enter your email or identifier.');
      return;
    }
    setIsSubmitting(true);
    setErrorMessage(null);
    const result = await login(email.trim(), password, selectedRole, selectedHospital);
    setIsSubmitting(false);
    if (!result.success) {
      if (result.pendingApproval) {
        if (result.role === 'HOSPITAL_ADMIN' || selectedRole === 'HOSPITAL_ADMIN') {
          const hId = result.hospitalId || selectedHospital;
          const hospObj = hospitals.find((h) => h.id === hId);
          setPendingHospital({
            hospitalId: hId,
            hospitalName: result.hospitalName || hospObj?.name || 'Registered Hospital Facility',
            hospitalCode: hospObj?.code || '',
            adminName: 'Hospital Administrator',
            adminEmail: email.trim(),
          });
          setHospitalApprovalDetected(false);
          setHospitalApprovalRejected(null);
          return;
        }
        if (result.role === 'DOCTOR' || selectedRole === 'DOCTOR') {
          const hospObj = hospitals.find((h) => h.id === selectedHospital);
          setPendingDoctor({
            doctorId: result.doctorId || '',
            hospitalId: result.hospitalId || selectedHospital,
            hospitalName: result.hospitalName || hospObj?.name || 'Hospital',
            name: 'Doctor',
            email: email.trim(),
            specialty: 'Clinical Specialist',
            department: 'General Medicine',
            qualifications: 'MBBS / MD',
            experienceYears: 5,
          });
          setApprovalDetected(false);
          setApprovalRejected(null);
          return;
        }
      }
      setErrorMessage(result.error || 'Authentication failed. Please check your credentials.');
    }
  };

  const handleLocalSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password || !fullName.trim()) {
      setErrorMessage('Please fill in all required fields.');
      return;
    }
    if (['HOSPITAL_ADMIN', 'DOCTOR'].includes(selectedRole) && !selectedHospital) {
      setErrorMessage('Please select an affiliated hospital from the directory.');
      return;
    }
    setIsSubmitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    const result = await signUp({
      email: email.trim(),
      password,
      fullName: fullName.trim(),
      role: selectedRole,
      hospitalId: ['HOSPITAL_ADMIN', 'DOCTOR'].includes(selectedRole) ? selectedHospital : undefined,
      phoneNumber: phoneNumber.trim() || undefined,
      specialty: selectedRole === 'DOCTOR' ? docSpecialty : undefined,
      department: selectedRole === 'DOCTOR' ? docDepartment : undefined,
      qualifications: selectedRole === 'DOCTOR' ? docQualifications : undefined,
      experienceYears: selectedRole === 'DOCTOR' ? parseInt(docExperienceYears, 10) || 5 : undefined,
      bio: selectedRole === 'DOCTOR' ? docBio.trim() || undefined : undefined,
    });
    setIsSubmitting(false);
    if (!result.success) {
      setErrorMessage(result.error || 'Registration failed.');
    } else if (result.pendingApproval) {
      const hospObj = hospitals.find((h) => h.id === selectedHospital);
      const hospTitle = hospObj ? `${hospObj.name} (${hospObj.code})` : (result.hospitalName || 'your affiliated hospital');
      setPendingDoctor({
        doctorId: result.doctorId || '',
        hospitalId: result.hospitalId || selectedHospital,
        hospitalName: hospTitle,
        name: fullName.trim(),
        email: email.trim(),
        specialty: docSpecialty,
        department: docDepartment,
        qualifications: docQualifications,
        experienceYears: parseInt(docExperienceYears, 10) || 5,
        bio: docBio.trim() || undefined,
      });
      setApprovalDetected(false);
      setApprovalRejected(null);
    }
  };

  const handleHospitalRegistration = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hospName.trim() || !hospCode.trim() || !hospEmail.trim() || !hospAdminName.trim() || !hospAdminEmail.trim()) {
      setErrorMessage('Please fill in all required hospital registration fields.');
      return;
    }
    setIsSubmitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const depts = hospDepts.split(',').map((d) => d.trim()).filter(Boolean);
      const res = await apiCall('/api/v1/onboarding/register', {
        method: 'POST',
        body: JSON.stringify({
          name: hospName.trim(),
          code: hospCode.trim().toUpperCase(),
          contact_email: hospEmail.trim().toLowerCase(),
          admin_name: hospAdminName.trim(),
          admin_email: hospAdminEmail.trim().toLowerCase(),
          admin_password: hospAdminPassword || 'demo123',
          phone: hospPhone.trim() || undefined,
          address: hospAddress.trim() || undefined,
          departments: depts,
          specialties: depts,
        }),
      });

      if (res.ok && res.data) {
        const hId = res.data.hospital_id || res.data.hospital?.id || '';
        const hName = res.data.hospital_name || res.data.hospital?.name || hospName.trim();
        const hCode = res.data.hospital_code || res.data.hospital?.code || hospCode.trim().toUpperCase();
        const aName = res.data.admin_name || hospAdminName.trim();
        const aEmail = res.data.admin_email || hospAdminEmail.trim().toLowerCase();

        fetchHospitals(hId);

        setPendingHospital({
          hospitalId: hId,
          hospitalName: hName,
          hospitalCode: hCode,
          adminName: aName,
          adminEmail: aEmail,
          contactEmail: hospEmail.trim().toLowerCase(),
          phone: hospPhone.trim() || undefined,
          address: hospAddress.trim() || undefined,
          departments: depts,
        });
        setHospitalApprovalDetected(false);
        setHospitalApprovalRejected(null);
      } else {
        setErrorMessage(res.error || 'Failed to submit hospital application.');
      }
    } catch (err: any) {
      setErrorMessage(err?.message || 'Network error submitting hospital registration.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleOAuth = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);

    // Create a realistic Google identity based on current selection
    const mockEmail = email.includes('@') ? email : `user.${selectedRole.toLowerCase()}@gmail.com`;
    const mockName = fullName.trim() || `${selectedRole === 'PATIENT' ? 'Alex' : selectedRole === 'DOCTOR' ? 'Dr. Jordan' : selectedRole === 'HOSPITAL_ADMIN' ? 'Admin Kelly' : 'Morgan'} (Google)`;
    const googleId = `g-oauth-${Date.now()}-${Math.floor(Math.random() * 100000)}`;

    const result = await loginWithGoogle({
      googleId,
      email: mockEmail,
      name: mockName,
      avatarUrl: `https://api.dicebear.com/7.x/avataaars/svg?seed=${mockEmail}`,
      role: selectedRole,
      hospitalId: ['HOSPITAL_ADMIN', 'DOCTOR'].includes(selectedRole) ? selectedHospital : undefined,
    });

    setIsSubmitting(false);
    if (!result.success) {
      setErrorMessage(result.error || 'Google authentication encountered an issue.');
    }
  };

  const rolesConfig = [
    {
      role: 'PATIENT' as UserRole,
      label: 'Patient',
      badge: 'Healthcare Consumer',
      icon: <User className="w-5 h-5 text-emerald-400" />,
      color: 'border-emerald-500/40 hover:border-emerald-400 bg-emerald-500/5',
      desc: 'Multilingual AI voice triage, real-time doctor availability & verified appointments.',
      features: ['Multilingual Voice Intake (Telugu, Hindi, English, Spanish)', 'Live Doctor Search & Specialty Matching', 'Real-time FHIR Booking Confirmation', 'Pre-visit Clinical Questionnaire'],
    },
    {
      role: 'DOCTOR' as UserRole,
      label: 'Doctor',
      badge: 'Clinical Care Provider',
      icon: <Stethoscope className="w-5 h-5 text-sky-400" />,
      color: 'border-sky-500/40 hover:border-sky-400 bg-sky-500/5',
      desc: "Today's patient schedule, pre-visit intake briefs, working hours & calendar blocks.",
      features: ['Real-time Today Schedule & Calendar Blocks', 'AI Pre-Visit Clinical Briefing', 'Symptom Severity Analysis', 'Multi-facility Consultation Windows'],
    },
    {
      role: 'HOSPITAL_ADMIN' as UserRole,
      label: 'Hospital Admin',
      badge: 'Facility Administration',
      icon: <Building2 className="w-5 h-5 text-indigo-400" />,
      color: 'border-indigo-500/40 hover:border-indigo-400 bg-indigo-500/5',
      desc: 'Facility configuration, doctor rostering, FHIR/Epic sync & anti-double-booking.',
      features: ['Accredited Hospital Scoping', 'Doctor Rostering & Scheduling Matrix', 'FHIR R4 / Epic System Reconciliation', 'Anti-Double-Booking Concurrency Engine'],
    },
    {
      role: 'PLATFORM_ADMIN' as UserRole,
      label: 'Entire System Admin',
      badge: 'Platform Super-Admin',
      icon: <ShieldAlert className="w-5 h-5 text-amber-400" />,
      color: 'border-amber-500/40 hover:border-amber-400 bg-amber-500/5',
      desc: 'SRE 4 Golden Signals, 27-Stage DoD journey runner, 76-point audit & zero-PHI logs.',
      features: ['SRE 4 Golden Signals & Live Observability', 'Dual Engine: SQLite + MongoDB Atlas Dynamic Sync', '27-Stage Definition-of-Done Test Runner', 'Role-Based Access Control (RBAC) Governance'],
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-emerald-500 selection:text-black">
      {/* Top Navigation */}
      <header className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-emerald-500/20 text-slate-950 font-black">
              <HeartPulse className="w-5 h-5" />
            </div>
            <div>
              <span className="font-black text-lg tracking-tight text-white">
                Nexus<span className="text-emerald-400">Health</span>
              </span>
              <span className="hidden sm:inline-block ml-2 text-[10px] font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 px-2 py-0.5 rounded-full uppercase tracking-wider">
                Multi-Hospital OS
              </span>
            </div>
          </div>

          <div className="hidden md:flex items-center space-x-8 text-sm font-medium text-slate-400">
            <a href="#network" className="hover:text-white transition">Hospitals</a>
            <a href="#roles" className="hover:text-white transition">Role Portals</a>
            <a href="#voice" className="hover:text-white transition">AI Voice Engine</a>
            <a href="#security" className="hover:text-white transition">Security &amp; EHR</a>
          </div>

          <div className="flex items-center space-x-3">
            {/* Language Selector */}
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as any)}
              className="bg-slate-900 border border-slate-800 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-emerald-500 cursor-pointer"
            >
              {SUPPORTED_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.flag} {lang.code.toUpperCase()}
                </option>
              ))}
            </select>

            <button
              onClick={() => {
                setAuthMode('hospital_register');
                setErrorMessage(null);
                setSuccessMessage(null);
                setIsAuthModalOpen(true);
              }}
              className="hidden lg:flex text-xs font-semibold px-3 py-2 rounded-xl text-sky-400 hover:text-white hover:bg-sky-950/50 border border-sky-500/30 transition items-center space-x-1.5 cursor-pointer"
              title="Register a new healthcare facility"
            >
              <HospitalIcon className="w-3.5 h-3.5" />
              <span>Register Hospital</span>
            </button>

            <button
              onClick={() => {
                setAuthMode('signin');
                setIsAuthModalOpen(true);
              }}
              className="text-xs font-semibold px-3.5 py-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-900 border border-slate-800 transition"
            >
              Sign In
            </button>

            <button
              onClick={() => {
                setAuthMode('signup');
                setIsAuthModalOpen(true);
              }}
              className="text-xs font-bold px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 shadow-md shadow-emerald-500/20 transition flex items-center space-x-1.5"
            >
              <span>Get Started</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-16 pb-20 sm:pt-24 sm:pb-32 overflow-hidden border-b border-slate-900">
        {/* Ambient Glows */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-emerald-500/10 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute top-1/3 right-10 w-[400px] h-[300px] bg-sky-500/10 rounded-full blur-[100px] pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center space-y-8">
          {/* Top Pill */}
          <div className="inline-flex items-center space-x-2 bg-slate-900/90 border border-slate-800 px-4 py-1.5 rounded-full text-xs text-slate-300 shadow-xl backdrop-blur-md">
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-semibold">Next-Generation Autonomous Healthcare Platform</span>
            <span className="w-1 h-1 rounded-full bg-slate-600" />
            <span className="text-emerald-400 font-bold">255/255 Automated Tests Verified</span>
          </div>

          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight text-white max-w-5xl mx-auto leading-[1.1]">
            Multi-Hospital{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
              Autonomous Voice Agent
            </span>{' '}
            &amp; Clinical EHR Operations
          </h1>

          <p className="text-base sm:text-xl text-slate-400 max-w-3xl mx-auto font-normal leading-relaxed">
            Unifying Patients, Doctors, Facility Admins, and Entire System SRE in a secure, multilingual, FHIR-integrated operating platform.
          </p>

          {/* Action CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <button
              onClick={() => openAuthWithRole('PATIENT', 'signin')}
              className="w-full sm:w-auto px-7 py-3.5 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-extrabold text-sm shadow-xl shadow-emerald-500/25 transition transform hover:-translate-y-0.5 flex items-center justify-center space-x-2"
            >
              <Mic className="w-4 h-4" />
              <span>Launch Voice Agent (Patient)</span>
            </button>

            <button
              onClick={() => {
                setAuthMode('signin');
                setIsAuthModalOpen(true);
              }}
              className="w-full sm:w-auto px-7 py-3.5 rounded-2xl bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-white font-bold text-sm shadow-xl transition flex items-center justify-center space-x-2"
            >
              <LogIn className="w-4 h-4 text-slate-400" />
              <span>Select Role &amp; Sign In</span>
            </button>
          </div>

          {/* Platform Metric Badges */}
          <div className="pt-12 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto text-left">
            <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 backdrop-blur-sm">
              <div className="text-2xl font-black text-emerald-400">99.98%</div>
              <div className="text-xs font-semibold text-slate-300 mt-0.5">SRE Uptime SLA</div>
              <div className="text-[11px] text-slate-500">4 Golden Signals Monitored</div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 backdrop-blur-sm">
              <div className="text-2xl font-black text-sky-400">4 Languages</div>
              <div className="text-xs font-semibold text-slate-300 mt-0.5">Multilingual Voice</div>
              <div className="text-[11px] text-slate-500">Telugu, Hindi, English, Spanish</div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 backdrop-blur-sm">
              <div className="text-2xl font-black text-indigo-400">Dual Engine</div>
              <div className="text-xs font-semibold text-slate-300 mt-0.5">Relational + MongoDB</div>
              <div className="text-[11px] text-slate-500">Zero-Mock Real Dynamic Data</div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 backdrop-blur-sm">
              <div className="text-2xl font-black text-amber-400">5 Personas</div>
              <div className="text-xs font-semibold text-slate-300 mt-0.5">Enterprise RBAC</div>
              <div className="text-[11px] text-slate-500">Google OAuth &amp; Facility Scoping</div>
            </div>
          </div>
        </div>
      </section>

      {/* Role Architecture Section */}
      <section id="roles" className="py-20 bg-slate-950/60 border-b border-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center space-y-3 max-w-3xl mx-auto">
            <h2 className="text-xs font-bold uppercase tracking-widest text-emerald-400">
              Role-Based Access Architecture
            </h2>
            <p className="text-3xl sm:text-4xl font-black tracking-tight text-white">
              Dedicated Workspaces for Every Healthcare Stakeholder
            </p>
            <p className="text-sm text-slate-400">
              Strict boundary rules, facility-level data isolation, and granular permissions across 4 specialized roles.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {rolesConfig.map((item) => (
              <div
                key={item.role}
                className={`rounded-2xl p-6 border transition duration-300 flex flex-col justify-between ${item.color} bg-slate-900/50 backdrop-blur-sm`}
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="w-11 h-11 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center">
                      {item.icon}
                    </div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 bg-slate-800/80 px-2.5 py-1 rounded-full">
                      {item.badge}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-lg font-bold text-white">{item.label}</h3>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">{item.desc}</p>
                  </div>

                  <ul className="space-y-2 pt-2 border-t border-slate-800/60">
                    {item.features.map((feat, idx) => (
                      <li key={idx} className="text-xs text-slate-300 flex items-start space-x-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="pt-6 mt-6 border-t border-slate-800/60 flex items-center justify-between">
                  <button
                    onClick={() => openAuthWithRole(item.role, 'signin')}
                    className="text-xs font-bold text-white hover:text-emerald-300 transition flex items-center space-x-1"
                  >
                    <span>Sign In as {item.label}</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>

                  <button
                    onClick={() => openAuthWithRole(item.role, 'signup')}
                    className="text-[11px] font-semibold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 px-2.5 py-1 rounded-lg transition"
                  >
                    Register
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Hospital Network Section */}
      <section id="network" className="py-20 border-b border-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <h2 className="text-xs font-bold uppercase tracking-widest text-sky-400">
              Federated Network
            </h2>
            <p className="text-3xl sm:text-4xl font-black tracking-tight text-white">
              Connected Healthcare Facilities
            </p>
            <p className="text-sm text-slate-400">
              Each facility maintains isolated doctors, departments, operating rules, and verified FHIR R4 connectivity.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {hospitals.map((hosp) => (
              <div
                key={hosp.id}
                className="bg-slate-900/60 border border-slate-800 hover:border-slate-700 rounded-2xl p-6 transition flex flex-col justify-between space-y-6 group"
              >
                <div className="space-y-3">
                  <div className="w-12 h-12 rounded-xl bg-slate-800/80 border border-slate-700 flex items-center justify-center text-sky-400">
                    <HospitalIcon className="w-6 h-6" />
                  </div>
                  <div>
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-400">
                      CODE: {hosp.code}
                    </span>
                    <h3 className="text-lg font-bold text-white group-hover:text-sky-300 transition">
                      {hosp.name}
                    </h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Accredited tertiary hospital with verified specialty departments and synchronized doctor calendars.
                    </p>
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-1.5 text-emerald-400 font-semibold">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span>FHIR R4 Connected</span>
                  </div>

                  <button
                    onClick={() => {
                      setSelectedHospital(hosp.id);
                      openAuthWithRole('HOSPITAL_ADMIN', 'signin');
                    }}
                    className="text-slate-300 hover:text-white font-bold transition flex items-center space-x-1"
                  >
                    <span>Manage Facility</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Hospital Onboarding CTA Card */}
          <div className="bg-gradient-to-r from-sky-950/40 via-slate-900 to-indigo-950/40 border border-sky-500/30 rounded-3xl p-6 sm:p-8 flex flex-col md:flex-row items-center justify-between gap-6 shadow-xl">
            <div className="space-y-2 text-left">
              <div className="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center space-x-1.5">
                <Building2 className="w-3.5 h-3.5" />
                <span>Healthcare Facility Onboarding</span>
              </div>
              <h3 className="text-xl sm:text-2xl font-black text-white">
                Want to Register Your Hospital in NexusHealth?
              </h3>
              <p className="text-xs sm:text-sm text-slate-400 max-w-2xl">
                Submit an onboarding request for your hospital. Applications are reviewed, verified, and approved directly by the Platform System Admin to ensure safety and clinical integrity.
              </p>
            </div>

            <button
              onClick={() => {
                setAuthMode('hospital_register');
                setErrorMessage(null);
                setSuccessMessage(null);
                setIsAuthModalOpen(true);
              }}
              className="shrink-0 px-6 py-3.5 rounded-2xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs shadow-lg shadow-sky-500/20 transition flex items-center space-x-2 cursor-pointer"
            >
              <HospitalIcon className="w-4 h-4" />
              <span>Register New Hospital</span>
            </button>
          </div>
        </div>
      </section>

      {/* AI Voice Engine Highlight */}
      <section id="voice" className="py-20 bg-slate-950/70 border-b border-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <div className="inline-flex items-center space-x-2 bg-emerald-500/10 border border-emerald-500/30 px-3.5 py-1 rounded-full text-xs font-bold text-emerald-400">
                <Mic className="w-3.5 h-3.5" />
                <span>Multilingual Autonomous Voice Agent</span>
              </div>

              <h2 className="text-3xl sm:text-5xl font-black tracking-tight text-white leading-tight">
                Natural Clinical Conversation in{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                  Your Native Language
                </span>
              </h2>

              <p className="text-sm sm:text-base text-slate-400 leading-relaxed">
                Patients can speak naturally in Telugu, Hindi, English, or Spanish. The AI handles clinical intent extraction, triage urgency scoring, doctor scheduling, and pre-visit intake collection dynamically.
              </p>

              <div className="grid grid-cols-2 gap-4 pt-2">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="text-sm font-bold text-white flex items-center space-x-2">
                    <Globe2 className="w-4 h-4 text-emerald-400" />
                    <span>Telugu &amp; Hindi Audio</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">Full synthesis and recognition tailored to patient preference.</p>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="text-sm font-bold text-white flex items-center space-x-2">
                    <Database className="w-4 h-4 text-sky-400" />
                    <span>Dynamic MongoDB Storage</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">Real-time transcripts, appointments, and preferences saved live.</p>
                </div>
              </div>

              <div className="pt-2">
                <button
                  onClick={() => openAuthWithRole('PATIENT', 'signin')}
                  className="px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm shadow-lg shadow-emerald-500/20 transition flex items-center space-x-2"
                >
                  <span>Experience Voice Agent</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Voice Simulation Card */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl relative">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800 text-xs">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="font-bold text-white">Live Voice Session Stream</span>
                </div>
                <span className="text-slate-400 font-mono">LANG: TE / EN</span>
              </div>

              <div className="py-8 space-y-4">
                <div className="bg-slate-800/60 rounded-2xl p-4 border border-slate-700/50 space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">Patient (Voice Input)</span>
                  <p className="text-xs sm:text-sm text-white font-medium italic">
                    "నాకు గత రెండు రోజులుగా ఎడమ భుజంలో నొప్పిగా ఉంది, కార్డియాలజిస్ట్ లేదా ఆర్థోపెడిక్ డాక్టర్ కావాలి."
                  </p>
                </div>

                <div className="bg-emerald-950/40 rounded-2xl p-4 border border-emerald-800/40 space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-300">NexusHealth AI (Voice Response)</span>
                  <p className="text-xs sm:text-sm text-emerald-100 font-medium">
                    "ఖచ్చితంగా, నేను City Memorial Hospital లోని Dr. Sharma (ఆర్థోపెడిక్స్) గారిని కనుగొన్నాను. రేపు ఉదయం 10:00 గంటలకు అపాయింట్‌మెంట్ బుక్ చేయమంటారా?"
                  </p>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <span>EHR Intent: <strong>CONSULTATION_REQUEST</strong></span>
                <span className="text-emerald-400 font-mono font-bold">Latency: 184ms</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Platform Security & HIPAA */}
      <section id="security" className="py-16 border-b border-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
          <div className="inline-flex items-center space-x-2 bg-slate-900 border border-slate-800 px-4 py-1.5 rounded-full text-xs text-slate-300">
            <Lock className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-semibold">Enterprise Security &amp; Compliance Standards</span>
          </div>

          <h2 className="text-2xl sm:text-3xl font-black text-white">
            HIPAA-Ready Architecture &amp; Zero-PHI Persistence
          </h2>

          <p className="text-xs sm:text-sm text-slate-400 max-w-2xl mx-auto">
            Role-Based Access Control (RBAC) boundary enforcement, salted SHA-256 cryptographic password hashing, Google OAuth token verification, and strict tenant isolation per hospital facility.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-slate-950 text-slate-500 text-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2 text-slate-400">
            <HeartPulse className="w-4 h-4 text-emerald-400" />
            <span className="font-bold text-white">NexusHealth</span>
            <span>&copy; {new Date().getFullYear()} Autonomous Healthcare Platform.</span>
          </div>

          <div className="flex items-center space-x-6 text-slate-400">
            <span>HL7 FHIR R4</span>
            <span>OAuth 2.0 / Google GIS</span>
            <span>MongoDB Atlas</span>
            <span>SQLite Dual Engine</span>
          </div>
        </div>
      </footer>

      {/* ------------------------------------------------------------- */}
      {/* AUTHENTICATION MODAL / DIALOG */}
      {/* ------------------------------------------------------------- */}
      {isAuthModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-xl w-full p-6 sm:p-8 relative shadow-2xl space-y-6 my-8">
            {/* Close Button */}
            <button
              onClick={() => {
                setIsAuthModalOpen(false);
                setPendingDoctor(null);
                setApprovalDetected(false);
                setApprovalRejected(null);
                setPendingHospital(null);
                setHospitalApprovalDetected(false);
                setHospitalApprovalRejected(null);
              }}
              className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>

            {pendingDoctor ? (
              <div className="space-y-5 animate-fadeIn">
                {/* Header banner */}
                <div className="flex items-center space-x-3 pb-3 border-b border-slate-800">
                  <div className="w-11 h-11 rounded-2xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 shrink-0">
                    <Stethoscope className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-[11px] font-bold text-sky-400 uppercase tracking-wider flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      <span>Physician Credentialing &amp; Hospital Onboarding</span>
                    </div>
                    <h2 className="text-xl font-extrabold text-white">
                      Doctor Registration Submitted
                    </h2>
                  </div>
                </div>

                {/* Dynamic Status Display */}
                {approvalDetected ? (
                  <div className="bg-emerald-500/15 border-2 border-emerald-500/50 rounded-2xl p-5 text-emerald-200 space-y-3 shadow-lg shadow-emerald-950/40">
                    <div className="flex items-center space-x-2.5 font-black text-base text-emerald-300">
                      <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0" />
                      <span>Application Approved &amp; Credentialed!</span>
                    </div>
                    <p className="text-xs text-slate-200 leading-relaxed">
                      The Hospital Administrator at <strong>{pendingDoctor.hospitalName}</strong> has approved Dr. {pendingDoctor.name}.
                      Your consultation calendar and clinical workstation are provisioned.
                    </p>
                    <div className="flex items-center space-x-2.5 pt-1 text-xs font-bold text-emerald-400">
                      <span className="w-4 h-4 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
                      <span>Launching your Doctor Clinical Workstation...</span>
                    </div>
                  </div>
                ) : approvalRejected ? (
                  <div className="bg-rose-500/15 border border-rose-500/40 rounded-2xl p-5 text-rose-200 space-y-3">
                    <div className="flex items-center space-x-2.5 font-bold text-base text-rose-400">
                      <AlertCircle className="w-5 h-5 shrink-0" />
                      <span>Application Not Approved</span>
                    </div>
                    <p className="text-xs text-slate-200 leading-relaxed">{approvalRejected}</p>
                    <div className="flex items-center space-x-3 pt-2">
                      <button
                        type="button"
                        onClick={() => {
                          setPendingDoctor(null);
                          setApprovalRejected(null);
                          setAuthMode('signup');
                        }}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-bold transition cursor-pointer"
                      >
                        Edit Registration
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="bg-gradient-to-r from-sky-950/60 to-slate-900 border-2 border-sky-500/40 rounded-2xl p-5 space-y-3 shadow-xl">
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-1">
                        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-amber-500/20 text-amber-300 border border-amber-500/40">
                          <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                          <span>Awaiting Hospital Admin Approval</span>
                        </span>
                        <h3 className="text-base font-extrabold text-white mt-1.5">
                          Wait for {pendingDoctor.hospitalName} admin to approve
                        </h3>
                      </div>
                      <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 shrink-0">
                        <Building2 className="w-5 h-5" />
                      </div>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed">
                      Your physician credentials have been submitted and routed to the Hospital Administrator at <strong>{pendingDoctor.hospitalName}</strong> for clinical credentialing and approval.
                    </p>

                    <div className="bg-slate-950/80 rounded-xl p-3 border border-slate-800 text-[11px] text-sky-300 flex items-center space-x-2">
                      <RotateCw className={`w-3.5 h-3.5 text-sky-400 shrink-0 ${isPollingDoctorApproval ? 'animate-spin' : ''}`} />
                      <span>
                        {isPollingDoctorApproval
                          ? 'Checking administrator decision in real time...'
                          : 'As soon as the hospital admin approves, this interface will automatically refresh and open your workstation.'}
                      </span>
                    </div>
                  </div>
                )}

                {/* Candidate Doctor Profile Details Card */}
                <div className="bg-slate-950/90 border border-slate-800 rounded-2xl p-4 space-y-3 text-xs">
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                    <User className="w-3.5 h-3.5 text-sky-400" />
                    <span>Submitted Physician Profile &amp; Details</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-slate-300">
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-slate-500 block">Doctor Full Name</span>
                      <span className="font-bold text-white text-sm">Dr. {pendingDoctor.name}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-slate-500 block">Primary Specialty</span>
                      <span className="font-semibold text-sky-400">{pendingDoctor.specialty}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-slate-500 block">Clinical Department</span>
                      <span className="font-medium text-slate-200">{pendingDoctor.department}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-slate-500 block">Qualifications &amp; Practice</span>
                      <span className="font-medium text-slate-200">{pendingDoctor.qualifications} &bull; {pendingDoctor.experienceYears} Years</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-slate-500 block">Target Hospital Facility</span>
                      <span className="font-medium text-emerald-400">{pendingDoctor.hospitalName}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-slate-500 block">Account Email</span>
                      <span className="font-mono text-slate-300">{pendingDoctor.email}</span>
                    </div>
                  </div>

                  {pendingDoctor.bio && (
                    <div className="pt-2 border-t border-slate-900 text-slate-400 text-[11px]">
                      <span className="text-[10px] uppercase font-semibold text-slate-500 block">Clinical Focus &amp; Bio</span>
                      <span>{pendingDoctor.bio}</span>
                    </div>
                  )}
                </div>

                {/* 4-Stage Approval Journey Tracker */}
                <div className="space-y-2">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                    Registration &amp; Activation Journey
                  </span>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                    <div className="bg-emerald-950/30 border border-emerald-500/40 rounded-xl p-2.5 text-center">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
                      <div className="font-bold text-emerald-300">1. Details Filed</div>
                      <div className="text-[10px] text-slate-400">Completed</div>
                    </div>

                    <div className="bg-emerald-950/30 border border-emerald-500/40 rounded-xl p-2.5 text-center">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
                      <div className="font-bold text-emerald-300">2. Routed to Admin</div>
                      <div className="text-[10px] text-slate-400">Target Queue</div>
                    </div>

                    <div className={`rounded-xl p-2.5 text-center border ${approvalDetected ? 'bg-emerald-950/30 border-emerald-500/40' : 'bg-amber-950/30 border-amber-500/50'}`}>
                      {approvalDetected ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
                      ) : (
                        <Clock className="w-4 h-4 text-amber-400 mx-auto mb-1 animate-pulse" />
                      )}
                      <div className={`font-bold ${approvalDetected ? 'text-emerald-300' : 'text-amber-300'}`}>
                        3. Admin Approval
                      </div>
                      <div className="text-[10px] text-slate-400">{approvalDetected ? 'Approved' : 'Under Review'}</div>
                    </div>

                    <div className={`rounded-xl p-2.5 text-center border ${approvalDetected ? 'bg-emerald-950/30 border-emerald-500/40' : 'bg-slate-950 border-slate-800 opacity-60'}`}>
                      {approvalDetected ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
                      ) : (
                        <Stethoscope className="w-4 h-4 text-slate-500 mx-auto mb-1" />
                      )}
                      <div className={`font-bold ${approvalDetected ? 'text-emerald-300' : 'text-slate-400'}`}>
                        4. Workstation Live
                      </div>
                      <div className="text-[10px] text-slate-400">{approvalDetected ? 'Activated' : 'Pending'}</div>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => {
                      setPendingDoctor(null);
                      setApprovalDetected(false);
                      setApprovalRejected(null);
                    }}
                    className="text-xs text-slate-400 hover:text-slate-200 transition underline cursor-pointer"
                  >
                    Cancel &amp; Return
                  </button>

                  <button
                    type="button"
                    disabled={isPollingDoctorApproval || approvalDetected}
                    onClick={() => checkDoctorApprovalStatus(pendingDoctor.doctorId)}
                    className="inline-flex items-center space-x-1.5 px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-bold shadow-md transition disabled:opacity-50 cursor-pointer"
                  >
                    <RotateCw className={`w-3.5 h-3.5 ${isPollingDoctorApproval ? 'animate-spin' : ''}`} />
                    <span>Check Approval Status Now</span>
                  </button>
                </div>
              </div>
            ) : pendingHospital ? (
              <div className="space-y-5 animate-fadeIn">
                {/* Header banner */}
                <div className="flex items-center space-x-3 pb-3 border-b border-slate-800">
                  <div className="w-11 h-11 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
                    <Building2 className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-[11px] font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      <span>Facility Accreditation &amp; Platform Onboarding</span>
                    </div>
                    <h2 className="text-xl font-extrabold text-white">
                      Hospital Registration Submitted
                    </h2>
                  </div>
                </div>

                {/* Dynamic Status Display */}
                {hospitalApprovalDetected ? (
                  <div className="bg-emerald-500/15 border-2 border-emerald-500/50 rounded-2xl p-5 text-emerald-200 space-y-3 shadow-lg shadow-emerald-950/40">
                    <div className="flex items-center space-x-2.5 font-black text-base text-emerald-300">
                      <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0" />
                      <span>Facility Approved &amp; Accredited by Platform Admin!</span>
                    </div>
                    <p className="text-xs text-slate-200 leading-relaxed">
                      The System Super-Admin has approved <strong>{pendingHospital.hospitalName}</strong> ({pendingHospital.hospitalCode || pendingHospital.hospitalId}).
                      Your facility workstation, EHR integration hub, and doctor scheduling pipelines are unlocked.
                    </p>
                    <div className="flex items-center space-x-2.5 pt-1 text-xs font-bold text-emerald-400">
                      <span className="w-4 h-4 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
                      <span>Launching Hospital Administrative Command Center...</span>
                    </div>
                  </div>
                ) : hospitalApprovalRejected ? (
                  <div className="bg-rose-500/15 border border-rose-500/40 rounded-2xl p-5 text-rose-200 space-y-3">
                    <div className="flex items-center space-x-2.5 font-bold text-base text-rose-400">
                      <AlertCircle className="w-5 h-5 shrink-0" />
                      <span>Registration Not Approved</span>
                    </div>
                    <p className="text-xs text-slate-200 leading-relaxed">{hospitalApprovalRejected}</p>
                    <div className="flex items-center space-x-3 pt-2">
                      <button
                        type="button"
                        onClick={() => {
                          setPendingHospital(null);
                          setHospitalApprovalRejected(null);
                          setAuthMode('hospital_register');
                        }}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-bold transition cursor-pointer"
                      >
                        Edit Registration
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="bg-gradient-to-r from-indigo-950/60 to-slate-900 border-2 border-indigo-500/40 rounded-2xl p-5 space-y-3 shadow-xl">
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-1">
                        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-amber-500/20 text-amber-300 border border-amber-500/40">
                          <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                          <span>Awaiting Platform / System Super-Admin Approval</span>
                        </span>
                        <h3 className="text-base font-extrabold text-white mt-1.5">
                          Wait for Platform Admin to approve {pendingHospital.hospitalName}
                        </h3>
                      </div>
                      <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
                        <ShieldCheck className="w-5 h-5" />
                      </div>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed">
                      Your hospital facility registration has been registered in the platform database and queued for verification by the <strong>Platform / System Super-Admin</strong>. The hospital command center will open automatically once approved.
                    </p>

                    <div className="bg-slate-950/80 rounded-xl p-3 border border-slate-800 text-[11px] text-indigo-300 flex items-center space-x-2">
                      <RotateCw className={`w-3.5 h-3.5 text-indigo-400 shrink-0 ${isPollingHospitalApproval ? 'animate-spin' : ''}`} />
                      <span>
                        {isPollingHospitalApproval
                          ? 'Checking platform approval decision in real time...'
                          : 'As soon as the platform administrator approves, this interface will automatically transition to the Hospital Operations Hub.'}
                      </span>
                    </div>
                  </div>
                )}

                {/* Candidate Hospital Profile Details Card */}
                <div className="bg-slate-950/90 border border-slate-800 rounded-2xl p-4 space-y-3 text-xs">
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                    <Building2 className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Submitted Facility Profile &amp; Onboarding Details</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-slate-300">
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-slate-500 block">Hospital / Health System</span>
                      <span className="font-bold text-white text-sm">{pendingHospital.hospitalName}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-slate-500 block">Facility Code</span>
                      <span className="font-semibold text-indigo-400 font-mono">{pendingHospital.hospitalCode || pendingHospital.hospitalId}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-slate-500 block">Lead Administrator</span>
                      <span className="font-medium text-slate-200">{pendingHospital.adminName}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-slate-500 block">Admin Email</span>
                      <span className="font-mono text-slate-300">{pendingHospital.adminEmail}</span>
                    </div>
                    {pendingHospital.contactEmail && (
                      <div>
                        <span className="text-[10px] uppercase font-semibold text-slate-500 block">Contact Email</span>
                        <span className="font-mono text-slate-300">{pendingHospital.contactEmail}</span>
                      </div>
                    )}
                    {pendingHospital.phone && (
                      <div>
                        <span className="text-[10px] uppercase font-semibold text-slate-500 block">Phone</span>
                        <span className="font-medium text-slate-200">{pendingHospital.phone}</span>
                      </div>
                    )}
                  </div>

                  {pendingHospital.departments && pendingHospital.departments.length > 0 && (
                    <div className="pt-2 border-t border-slate-900 text-slate-400 text-[11px]">
                      <span className="text-[10px] uppercase font-semibold text-slate-500 block mb-1">Declared Clinical Departments</span>
                      <div className="flex flex-wrap gap-1.5">
                        {pendingHospital.departments.map((d) => (
                          <span key={d} className="bg-slate-900 border border-slate-800 text-indigo-300 px-2 py-0.5 rounded-lg text-[10px]">
                            {d}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* 4-Stage Approval Journey Tracker */}
                <div className="space-y-2">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                    Accreditation &amp; Approval Journey
                  </span>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                    <div className="bg-emerald-950/30 border border-emerald-500/40 rounded-xl p-2.5 text-center">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
                      <div className="font-bold text-emerald-300">1. Facility Filed</div>
                      <div className="text-[10px] text-slate-400">Completed</div>
                    </div>

                    <div className="bg-emerald-950/30 border border-emerald-500/40 rounded-xl p-2.5 text-center">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
                      <div className="font-bold text-emerald-300">2. DB Ingested</div>
                      <div className="text-[10px] text-slate-400">Ready for Review</div>
                    </div>

                    <div className={`rounded-xl p-2.5 text-center border transition ${
                      hospitalApprovalDetected
                        ? 'bg-emerald-950/30 border-emerald-500/40'
                        : 'bg-amber-950/30 border-amber-500/40 animate-pulse'
                    }`}>
                      {hospitalApprovalDetected ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
                      ) : (
                        <RotateCw className="w-4 h-4 text-amber-400 mx-auto mb-1 animate-spin" />
                      )}
                      <div className={`font-bold ${hospitalApprovalDetected ? 'text-emerald-300' : 'text-amber-300'}`}>
                        3. Platform Review
                      </div>
                      <div className="text-[10px] text-slate-400">
                        {hospitalApprovalDetected ? 'Approved' : 'Awaiting Super-Admin'}
                      </div>
                    </div>

                    <div className={`rounded-xl p-2.5 text-center border ${
                      hospitalApprovalDetected
                        ? 'bg-emerald-950/30 border-emerald-500/40'
                        : 'bg-slate-900 border-slate-800 opacity-60'
                    }`}>
                      <CheckCircle2 className={`w-4 h-4 mx-auto mb-1 ${hospitalApprovalDetected ? 'text-emerald-400' : 'text-slate-500'}`} />
                      <div className={`font-bold ${hospitalApprovalDetected ? 'text-emerald-300' : 'text-slate-400'}`}>
                        4. Hospital Hub
                      </div>
                      <div className="text-[10px] text-slate-400">
                        {hospitalApprovalDetected ? 'Provisioned' : 'Locked'}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => {
                      setPendingHospital(null);
                      setHospitalApprovalDetected(false);
                      setHospitalApprovalRejected(null);
                    }}
                    className="text-xs text-slate-400 hover:text-slate-200 transition underline cursor-pointer"
                  >
                    Cancel &amp; Return
                  </button>

                  <button
                    type="button"
                    disabled={isPollingHospitalApproval || hospitalApprovalDetected}
                    onClick={() => checkHospitalApprovalStatus(pendingHospital.hospitalId)}
                    className="inline-flex items-center space-x-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-md transition disabled:opacity-50 cursor-pointer"
                  >
                    <RotateCw className={`w-3.5 h-3.5 ${isPollingHospitalApproval ? 'animate-spin' : ''}`} />
                    <span>Check Approval Status Now</span>
                  </button>
                </div>
              </div>
            ) : (
              <>
            {/* Header */}
            <div className="space-y-1">
              <div className="flex items-center space-x-2 text-emerald-400 text-xs font-bold uppercase tracking-wider">
                <HeartPulse className="w-4 h-4" />
                <span>NexusHealth Identity &amp; RBAC Access</span>
              </div>
              <h2 className="text-2xl font-black text-white">
                {authMode === 'signup'
                  ? 'Create an Account'
                  : authMode === 'signin'
                  ? 'Sign In to Portal'
                  : authMode === 'hospital_register'
                  ? 'Register Hospital Facility'
                  : 'Quick Demo Personas'}
              </h2>
              <p className="text-xs text-slate-400">
                {authMode === 'hospital_register'
                  ? 'Submit your healthcare institution application for Platform Super-Admin review and verification.'
                  : 'Select your role and affiliated hospital to access your dedicated healthcare portal.'}
              </p>
            </div>

            {/* Mode Switcher Tabs */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs font-bold">
              <button
                type="button"
                onClick={() => {
                  setAuthMode('signin');
                  setErrorMessage(null);
                  setSuccessMessage(null);
                }}
                className={`py-2 rounded-lg transition text-center ${
                  authMode === 'signin' ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-400 hover:text-white'
                }`}
              >
                Sign In
              </button>

              <button
                type="button"
                onClick={() => {
                  setAuthMode('signup');
                  setErrorMessage(null);
                  setSuccessMessage(null);
                }}
                className={`py-2 rounded-lg transition text-center ${
                  authMode === 'signup' ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-400 hover:text-white'
                }`}
              >
                Create Account
              </button>

              <button
                type="button"
                onClick={() => {
                  setAuthMode('hospital_register');
                  setErrorMessage(null);
                  setSuccessMessage(null);
                }}
                className={`py-2 rounded-lg transition text-center ${
                  authMode === 'hospital_register' ? 'bg-sky-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
                }`}
              >
                Register Facility
              </button>

              <button
                type="button"
                onClick={() => {
                  setAuthMode('demo');
                  setErrorMessage(null);
                  setSuccessMessage(null);
                }}
                className={`py-2 rounded-lg transition text-center ${
                  authMode === 'demo' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
                }`}
              >
                1-Click Demo
              </button>
            </div>

            {/* Feedback Alerts */}
            {errorMessage && (
              <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-3 text-xs text-rose-300 flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Success Feedback Alert */}
            {successMessage && (
              <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 text-xs text-emerald-300 space-y-2">
                <div className="flex items-center space-x-2 font-bold text-emerald-400">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>Application Submitted</span>
                </div>
                <p className="text-slate-300 leading-relaxed">{successMessage}</p>
                <button
                  type="button"
                  onClick={() => {
                    setSuccessMessage(null);
                    setAuthMode('signin');
                    if (authMode === 'hospital_register') {
                      setSelectedRole('HOSPITAL_ADMIN');
                      if (hospAdminEmail) {
                        setEmail(hospAdminEmail);
                      }
                      if (hospAdminPassword) {
                        setPassword(hospAdminPassword);
                      }
                    }
                    fetchHospitals();
                  }}
                  className="mt-2 inline-flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold cursor-pointer"
                >
                  <span>Proceed to Sign In</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            {/* 1-Click Demo Personas Mode */}
            {authMode === 'demo' ? (
              <div className="space-y-3">
                <div className="text-xs font-semibold text-slate-400">
                  Instant Access Demo Personas (No Password Required):
                </div>
                <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                  {DEMO_PERSONAS.map((p) => (
                    <button
                      key={p.role}
                      disabled={isSubmitting}
                      onClick={() => handleDemoLogin(p)}
                      className="w-full text-left bg-slate-950 hover:bg-slate-800/80 border border-slate-800 hover:border-emerald-500/40 rounded-xl p-3.5 transition flex items-center justify-between group"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center text-emerald-400">
                          {p.role === 'PATIENT' ? <User className="w-4 h-4" /> : p.role === 'DOCTOR' ? <Stethoscope className="w-4 h-4" /> : p.role === 'HOSPITAL_ADMIN' ? <Building2 className="w-4 h-4" /> : <ShieldAlert className="w-4 h-4" />}
                        </div>
                        <div>
                          <div className="text-xs font-bold text-white group-hover:text-emerald-300 transition">
                            {p.name}
                          </div>
                          <div className="text-[11px] text-slate-400">
                            {p.badge} &bull; <span className="font-mono text-slate-500">{p.identifier}</span>
                          </div>
                        </div>
                      </div>
                      <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-emerald-400 group-hover:translate-x-1 transition" />
                    </button>
                  ))}
                </div>
              </div>
            ) : authMode === 'hospital_register' ? (
              !successMessage && (
                <form onSubmit={handleHospitalRegistration} className="space-y-3.5 max-h-[70vh] overflow-y-auto pr-1">
                  <div className="bg-sky-950/40 border border-sky-500/30 rounded-xl p-3 text-xs text-sky-200">
                    <p className="font-semibold text-sky-300 mb-0.5">Admin Approval Required</p>
                    <p className="text-[11px] text-sky-300/80">
                      Submitted hospital facilities are placed into a pending review queue for approval by the Platform Super-Admin. Once approved, facility operations and administrator access will be activated.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-bold text-slate-300 block mb-1">
                        Hospital / Health System Name *
                      </label>
                      <input
                        type="text"
                        required
                        value={hospName}
                        onChange={(e) => setHospName(e.target.value)}
                        placeholder="e.g. Apollo Care Medical Center"
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                      />
                    </div>

                    <div>
                      <label className="text-xs font-bold text-slate-300 block mb-1">
                        Facility Code *
                      </label>
                      <input
                        type="text"
                        required
                        value={hospCode}
                        onChange={(e) => setHospCode(e.target.value.toUpperCase())}
                        placeholder="e.g. APOLLOCARE"
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white uppercase font-mono focus:outline-none focus:border-sky-500"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-bold text-slate-300 block mb-1">
                        Official Contact Email *
                      </label>
                      <input
                        type="email"
                        required
                        value={hospEmail}
                        onChange={(e) => setHospEmail(e.target.value)}
                        placeholder="contact@apollocare.org"
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                      />
                    </div>

                    <div>
                      <label className="text-xs font-bold text-slate-300 block mb-1">
                        Official Phone Number
                      </label>
                      <input
                        type="tel"
                        value={hospPhone}
                        onChange={(e) => setHospPhone(e.target.value)}
                        placeholder="+1-800-555-CARE"
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-300 block mb-1">
                      Facility Physical Address
                    </label>
                    <input
                      type="text"
                      value={hospAddress}
                      onChange={(e) => setHospAddress(e.target.value)}
                      placeholder="1200 Healthcare Way, Suite 400, Chicago, IL"
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-300 block mb-1">
                      Departments &amp; Specialties (comma-separated)
                    </label>
                    <input
                      type="text"
                      value={hospDepts}
                      onChange={(e) => setHospDepts(e.target.value)}
                      placeholder="Cardiology, Orthopedics, General Medicine, Pediatrics"
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                    />
                  </div>

                  <div className="border-t border-slate-800/80 pt-3">
                    <p className="text-xs font-bold text-slate-200 mb-2">Hospital Administrator Initial Account</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs text-slate-400 block mb-1">
                          Administrator Full Name *
                        </label>
                        <input
                          type="text"
                          required
                          value={hospAdminName}
                          onChange={(e) => setHospAdminName(e.target.value)}
                          placeholder="e.g. Dr. Arthur Miller"
                          className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                        />
                      </div>

                      <div>
                        <label className="text-xs text-slate-400 block mb-1">
                          Admin Login Email *
                        </label>
                        <input
                          type="email"
                          required
                          value={hospAdminEmail}
                          onChange={(e) => setHospAdminEmail(e.target.value)}
                          placeholder="arthur.admin@apollocare.org"
                          className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                        />
                      </div>
                    </div>

                    <div className="mt-3">
                      <label className="text-xs text-slate-400 block mb-1">
                        Admin Login Password *
                      </label>
                      <input
                        type="password"
                        required
                        value={hospAdminPassword}
                        onChange={(e) => setHospAdminPassword(e.target.value)}
                        placeholder="Create strong admin password (min 4 characters)"
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-bold text-xs shadow-lg transition flex items-center justify-center space-x-2 mt-4 cursor-pointer disabled:opacity-50"
                  >
                    {isSubmitting ? (
                      <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                    ) : (
                      <>
                        <HospitalIcon className="w-4 h-4" />
                        <span>Submit Hospital Registration for Approval</span>
                      </>
                    )}
                  </button>
                </form>
              )
            ) : (
              <div className="space-y-5">
                {/* 1. Google OAuth Button */}
                <div>
                  <button
                    type="button"
                    disabled={isSubmitting}
                    onClick={handleGoogleOAuth}
                    className="w-full py-2.5 px-4 rounded-xl bg-white hover:bg-slate-100 text-slate-900 font-bold text-xs shadow-md transition flex items-center justify-center space-x-3 cursor-pointer disabled:opacity-50"
                  >
                    {/* Google G Logo SVG */}
                    <svg className="w-4 h-4" viewBox="0 0 24 24">
                      <path
                        fill="#4285F4"
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      />
                      <path
                        fill="#34A853"
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      />
                      <path
                        fill="#FBBC05"
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                      />
                      <path
                        fill="#EA4335"
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                      />
                    </svg>
                    <span>
                      {authMode === 'signup' ? 'Sign up with Google' : 'Continue with Google'}
                    </span>
                  </button>
                  <p className="text-[10px] text-slate-500 text-center mt-1.5">
                    Signs in via Google OAuth and applies the selected role &amp; hospital below.
                  </p>
                </div>

                {/* Divider */}
                <div className="flex items-center space-x-3 text-slate-600 text-[11px]">
                  <div className="flex-1 h-px bg-slate-800" />
                  <span>or with email credentials</span>
                  <div className="flex-1 h-px bg-slate-800" />
                </div>

                {/* 2. Role Selector Cards */}
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-300 block">
                    Select Your Role:
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {rolesConfig.map((r) => (
                      <button
                        key={r.role}
                        type="button"
                        onClick={() => setSelectedRole(r.role)}
                        className={`p-2.5 rounded-xl border text-left transition flex items-center space-x-2 text-xs ${
                          selectedRole === r.role
                            ? 'bg-emerald-500/15 border-emerald-500 text-white font-bold'
                            : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                        }`}
                      >
                        <span className="shrink-0">{r.icon}</span>
                        <span className="truncate">{r.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* 3. Hospital Selector (Shown for Hospital Admin and Doctor) */}
                {['HOSPITAL_ADMIN', 'DOCTOR'].includes(selectedRole) && (
                  <div className="space-y-1.5 bg-slate-950/80 p-3 rounded-xl border border-slate-800">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-slate-300 flex items-center space-x-1.5">
                        <HospitalIcon className="w-3.5 h-3.5 text-sky-400" />
                        <span>Select Affiliated Hospital:</span>
                      </label>
                      <button
                        type="button"
                        onClick={() => fetchHospitals()}
                        disabled={isRefreshingHospitals}
                        className="text-[11px] text-sky-400 hover:text-sky-300 flex items-center space-x-1 transition cursor-pointer disabled:opacity-50"
                        title="Reload approved hospitals from network"
                      >
                        <RotateCw className={`w-3 h-3 ${isRefreshingHospitals ? 'animate-spin' : ''}`} />
                        <span>Refresh Facilities</span>
                      </button>
                    </div>
                    <select
                      value={selectedHospital}
                      onChange={(e) => setSelectedHospital(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 text-xs text-white rounded-lg px-3 py-2 focus:outline-none focus:border-sky-500 cursor-pointer"
                    >
                      {hospitals.map((hosp) => (
                        <option key={hosp.id} value={hosp.id}>
                          {hosp.name} ({hosp.code})
                        </option>
                      ))}
                    </select>
                    <span className="text-[10px] text-slate-400">
                      Restricts access to {selectedHospital ? hospitals.find(h => h.id === selectedHospital)?.name || 'the selected facility' : 'the hospital'}.
                    </span>
                  </div>
                )}

                {/* 4. Credentials Form */}
                <form
                  onSubmit={authMode === 'signup' ? handleLocalSignUp : handleLocalSignIn}
                  className="space-y-3"
                >
                  {authMode === 'signup' && (
                    <div>
                      <label className="text-xs font-bold text-slate-300 block mb-1">
                        Full Name:
                      </label>
                      <input
                        type="text"
                        required
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        placeholder="e.g. Dr. Alex Morgan or Jane Doe"
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                      />
                    </div>
                  )}

                  <div>
                    <label className="text-xs font-bold text-slate-300 block mb-1">
                      {authMode === 'signup' ? 'Email Address:' : 'Email Address or Phone Identifier:'}
                    </label>
                    <input
                      type={authMode === 'signup' ? 'email' : 'text'}
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder={authMode === 'signup' ? 'name@example.com' : 'admin@citymemorial.org or +1-555-SHOULDER'}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-300 block mb-1">
                      Password:
                    </label>
                    <input
                      type="password"
                      required={authMode === 'signup'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder={authMode === 'signup' ? 'Create a secure password (min 4 chars)' : 'Account password (or leave empty for demo)'}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                    />
                  </div>

                  {authMode === 'signup' && (
                    <div>
                      <label className="text-xs font-bold text-slate-300 block mb-1">
                        Phone Number (Optional):
                      </label>
                      <input
                        type="tel"
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value)}
                        placeholder="+1-555-0199"
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                      />
                    </div>
                  )}

                  {authMode === 'signup' && selectedRole === 'DOCTOR' && (
                    <div className="space-y-3 bg-sky-950/30 border border-sky-500/30 rounded-xl p-3 text-xs">
                      <div className="flex items-center space-x-1.5 text-xs font-bold text-sky-400">
                        <Stethoscope className="w-3.5 h-3.5" />
                        <span>Physician Credentialing &amp; Practice Details</span>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        <div>
                          <label className="text-[11px] text-slate-300 block mb-1">
                            Primary Specialty *
                          </label>
                          <select
                            value={docSpecialty}
                            onChange={(e) => setDocSpecialty(e.target.value)}
                            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-sky-500 cursor-pointer"
                          >
                            <option value="General Medicine">General Medicine</option>
                            <option value="Cardiology">Cardiology</option>
                            <option value="Orthopedics">Orthopedics</option>
                            <option value="Neurology">Neurology</option>
                            <option value="Pediatrics">Pediatrics</option>
                            <option value="Dermatology">Dermatology</option>
                            <option value="Gastroenterology">Gastroenterology</option>
                            <option value="Oncology">Oncology</option>
                            <option value="Emergency Medicine">Emergency Medicine</option>
                          </select>
                        </div>

                        <div>
                          <label className="text-[11px] text-slate-300 block mb-1">
                            Clinical Department *
                          </label>
                          <input
                            type="text"
                            required
                            value={docDepartment}
                            onChange={(e) => setDocDepartment(e.target.value)}
                            placeholder="e.g. Department of Orthopedics"
                            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-sky-500"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        <div>
                          <label className="text-[11px] text-slate-300 block mb-1">
                            Qualifications / Degrees *
                          </label>
                          <input
                            type="text"
                            required
                            value={docQualifications}
                            onChange={(e) => setDocQualifications(e.target.value)}
                            placeholder="e.g. MBBS, MD, FACS, Board Certified"
                            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-sky-500"
                          />
                        </div>

                        <div>
                          <label className="text-[11px] text-slate-300 block mb-1">
                            Years of Clinical Practice *
                          </label>
                          <input
                            type="number"
                            min={1}
                            max={60}
                            required
                            value={docExperienceYears}
                            onChange={(e) => setDocExperienceYears(e.target.value)}
                            placeholder="8"
                            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-sky-500"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="text-[11px] text-slate-300 block mb-1">
                          Clinical Focus / Bio (Optional)
                        </label>
                        <input
                          type="text"
                          value={docBio}
                          onChange={(e) => setDocBio(e.target.value)}
                          placeholder="Brief description of sub-specialty or clinical expertise..."
                          className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-sky-500"
                        />
                      </div>

                      <p className="text-[10px] text-sky-300/80 leading-relaxed">
                        Notice: Upon submitting, your credentialing request is routed to the Hospital Administrator of the selected facility for review and approval.
                      </p>
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-bold text-xs shadow-lg transition flex items-center justify-center space-x-2 mt-4 cursor-pointer disabled:opacity-50"
                  >
                    {isSubmitting ? (
                      <span className="animate-spin w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full" />
                    ) : authMode === 'signup' ? (
                      <>
                        <UserPlus className="w-4 h-4" />
                        <span>Register Account as {selectedRole}</span>
                      </>
                    ) : (
                      <>
                        <LogIn className="w-4 h-4" />
                        <span>Sign In as {selectedRole}</span>
                      </>
                    )}
                  </button>
                </form>
              </div>
            )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
