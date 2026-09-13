import React, { useState } from 'react';
import {
  Building2,
  CheckCircle2,
  AlertCircle,
  Mail,
  Phone,
  MapPin,
  Shield,
  KeyRound,
  Plus,
  X,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import { apiCall } from '../../api/client';

interface Props {
  onSuccess?: () => void;
}

const COMMON_DEPARTMENTS = [
  'Emergency Medicine',
  'Cardiology',
  'Neurology',
  'Pediatrics',
  'Orthopedics',
  'Oncology',
  'Internal Medicine',
  'Dermatology',
  'Psychiatry',
  'Radiology',
  'Surgery'
];

export const HospitalRegistrationBoard: React.FC<Props> = ({ onSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    contact_email: '',
    phone: '',
    address: '',
    organization_info: '',
    admin_name: '',
    admin_email: '',
    admin_password: 'HospitalAdmin2026!'
  });

  const [departments, setDepartments] = useState<string[]>([
    'Cardiology',
    'Internal Medicine',
    'Emergency Medicine'
  ]);
  const [customDept, setCustomDept] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: field === 'code' ? value.toUpperCase().replace(/[^A-Z0-9]/g, '') : value
    }));
  };

  const toggleDepartment = (dept: string) => {
    if (departments.includes(dept)) {
      setDepartments(departments.filter(d => d !== dept));
    } else {
      setDepartments([...departments, dept]);
    }
  };

  const addCustomDept = () => {
    if (customDept.trim() && !departments.includes(customDept.trim())) {
      setDepartments([...departments, customDept.trim()]);
      setCustomDept('');
    }
  };

  const prefillSample = (sample: 'metro' | 'valley') => {
    if (sample === 'metro') {
      const codeSuffix = Math.floor(100 + Math.random() * 900);
      setFormData({
        name: `Metro Health University Medical Center`,
        code: `METRO${codeSuffix}`,
        contact_email: `contact.metro${codeSuffix}@metrohealth.org`,
        phone: '+1 (555) 234-5678',
        address: '100 University Plaza, Metropolis, NY 10001',
        organization_info: 'Tertiary academic medical center with Level 1 trauma and 450 acute care beds.',
        admin_name: 'Dr. Sarah Lin',
        admin_email: `sarah.lin${codeSuffix}@metrohealth.org`,
        admin_password: 'HospitalAdmin2026!'
      });
      setDepartments(['Cardiology', 'Emergency Medicine', 'Neurology', 'Oncology']);
    } else {
      const codeSuffix = Math.floor(100 + Math.random() * 900);
      setFormData({
        name: `Valley Regional Community Hospital`,
        code: `VALLEY${codeSuffix}`,
        contact_email: `info.valley${codeSuffix}@valleyregional.health`,
        phone: '+1 (555) 876-5432',
        address: '750 Mountain View Way, Pleasant Valley, CA 94025',
        organization_info: 'Community health system providing comprehensive primary and specialized acute care.',
        admin_name: 'Marcus Vance',
        admin_email: `marcus.vance${codeSuffix}@valleyregional.health`,
        admin_password: 'HospitalAdmin2026!'
      });
      setDepartments(['Internal Medicine', 'Pediatrics', 'Orthopedics']);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!formData.name.trim() || !formData.code.trim() || !formData.contact_email.trim()) {
      setErrorMessage('Hospital name, facility code, and contact email are required.');
      return;
    }

    if (!formData.admin_name.trim() || !formData.admin_email.trim()) {
      setErrorMessage('Facility administrator name and email are required.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await apiCall('/api/v1/onboarding/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name.trim(),
          code: formData.code.trim(),
          contact_email: formData.contact_email.trim(),
          phone: formData.phone.trim() || undefined,
          address: formData.address.trim() || undefined,
          organization_info: formData.organization_info.trim() || undefined,
          admin_name: formData.admin_name.trim(),
          admin_email: formData.admin_email.trim(),
          admin_password: formData.admin_password || 'demo123',
          departments: departments,
          specialties: departments
        })
      });

      if (res.ok) {
        setSuccessMessage(
          `Registration submitted successfully for "${formData.name}". Application is now in the Platform Approval Queue.`
        );
        setFormData({
          name: '',
          code: '',
          contact_email: '',
          phone: '',
          address: '',
          organization_info: '',
          admin_name: '',
          admin_email: '',
          admin_password: 'HospitalAdmin2026!'
        });
        if (onSuccess) {
          setTimeout(onSuccess, 1500);
        }
      } else {
        setErrorMessage(res.error || 'Failed to submit hospital registration.');
      }
    } catch (err: any) {
      setErrorMessage(err?.message || 'Error communicating with registration server.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold text-amber-400 uppercase tracking-widest">
            <Building2 className="w-4 h-4" />
            <span>Healthcare System Onboarding &bull; Tenant Provisioning</span>
          </div>
          <h2 className="text-2xl font-black text-white mt-1">Hospital Registration</h2>
          <p className="text-sm text-slate-400">
            Submit a new hospital facility application for statewide platform enrollment and tenant database isolation.
          </p>
        </div>

        {/* Quick Demo Pre-fill */}
        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400 font-semibold hidden sm:inline">1-Click Demo:</span>
          <button
            type="button"
            onClick={() => prefillSample('metro')}
            className="px-3 py-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/20 text-xs font-bold transition flex items-center space-x-1"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Metro Health</span>
          </button>
          <button
            type="button"
            onClick={() => prefillSample('valley')}
            className="px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 text-xs font-bold transition flex items-center space-x-1"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Valley Regional</span>
          </button>
        </div>
      </div>

      {/* Notifications */}
      {successMessage && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 flex items-center space-x-3 text-emerald-300 text-sm font-semibold shadow-lg">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 flex items-center space-x-3 text-rose-300 text-sm font-semibold shadow-lg">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Registration Form */}
      <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        {/* Section 1: Facility Information */}
        <div>
          <h3 className="text-base font-bold text-white mb-3 flex items-center space-x-2">
            <Building2 className="w-4 h-4 text-amber-400" />
            <span>Facility Information</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Hospital / Health System Name *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. St. Jude Regional Medical Center"
                value={formData.name}
                onChange={e => handleInputChange('name', e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-amber-500 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Facility Short Code (Tenant Identifier) *
              </label>
              <input
                type="text"
                required
                maxLength={10}
                placeholder="e.g. STJUDE (Uppercase, Letters & Numbers)"
                value={formData.code}
                onChange={e => handleInputChange('code', e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white font-mono uppercase focus:outline-none focus:border-amber-500 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Facility Contact Email *
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  placeholder="admin@stjudehealth.org"
                  value={formData.contact_email}
                  onChange={e => handleInputChange('contact_email', e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-amber-500 transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Facility Phone Number
              </label>
              <div className="relative">
                <Phone className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="tel"
                  placeholder="+1 (555) 000-0000"
                  value={formData.phone}
                  onChange={e => handleInputChange('phone', e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-amber-500 transition"
                />
              </div>
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Physical Campus Address
              </label>
              <div className="relative">
                <MapPin className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="text"
                  placeholder="123 Hospital Way, Suite 100, City, State ZIP"
                  value={formData.address}
                  onChange={e => handleInputChange('address', e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-amber-500 transition"
                />
              </div>
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Organization Description &amp; Scope
              </label>
              <textarea
                rows={2}
                placeholder="Details on emergency services, bed capacity, trauma designation, academic affiliations..."
                value={formData.organization_info}
                onChange={e => handleInputChange('organization_info', e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-amber-500 transition"
              />
            </div>
          </div>
        </div>

        {/* Section 2: Facility Administrator Account */}
        <div className="border-t border-slate-800 pt-6">
          <h3 className="text-base font-bold text-white mb-3 flex items-center space-x-2">
            <Shield className="w-4 h-4 text-indigo-400" />
            <span>Designated Hospital Administrator Account</span>
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            An initial administrator account will be provisioned in a pending state and activated immediately upon platform approval.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Admin Full Name *
              </label>
              <input
                type="text"
                required
                placeholder="Dr. Jane Doe, Chief Medical Officer"
                value={formData.admin_name}
                onChange={e => handleInputChange('admin_name', e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-amber-500 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Admin Work Email *
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  placeholder="jane.doe@stjudehealth.org"
                  value={formData.admin_email}
                  onChange={e => handleInputChange('admin_email', e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-amber-500 transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Initial Master Password
              </label>
              <div className="relative">
                <KeyRound className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={formData.admin_password}
                  onChange={e => handleInputChange('admin_password', e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-amber-500 transition"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Section 3: Clinical Departments & Specialties */}
        <div className="border-t border-slate-800 pt-6">
          <h3 className="text-base font-bold text-white mb-2">Clinical Departments &amp; Service Lines</h3>
          <p className="text-xs text-slate-400 mb-3">
            Select departments offered by this hospital to auto-configure doctor intake routing and specialty questionnaires:
          </p>

          <div className="flex flex-wrap gap-2 mb-4">
            {COMMON_DEPARTMENTS.map(dept => {
              const selected = departments.includes(dept);
              return (
                <button
                  type="button"
                  key={dept}
                  onClick={() => toggleDepartment(dept)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center space-x-1.5 ${
                    selected
                      ? 'bg-amber-500 text-slate-950 font-bold shadow'
                      : 'bg-slate-950 border border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <span>{dept}</span>
                  {selected && <X className="w-3 h-3" />}
                </button>
              );
            })}
          </div>

          <div className="flex items-center space-x-2 max-w-md">
            <input
              type="text"
              placeholder="Add other department..."
              value={customDept}
              onChange={e => setCustomDept(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addCustomDept();
                }
              }}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
            />
            <button
              type="button"
              onClick={addCustomDept}
              className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition flex items-center space-x-1"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add</span>
            </button>
          </div>
        </div>

        {/* Submit Action */}
        <div className="border-t border-slate-800 pt-6 flex justify-end">
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-black text-xs transition shadow-xl flex items-center space-x-2"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                <span>Submitting Registration...</span>
              </>
            ) : (
              <>
                <span>Submit Hospital Registration</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
