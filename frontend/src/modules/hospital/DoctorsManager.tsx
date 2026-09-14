import React, { useState, useEffect } from 'react';
import {
  Stethoscope,
  UserPlus,
  CheckCircle2,
  RotateCw,
  ShieldCheck,
  Ban,
  Check,
  X,
  Clock,
  AlertCircle,
  Award,
  Briefcase
} from 'lucide-react';
import { apiCall } from '../../api/client';
import { useToast } from '../../context/ToastContext';

interface DoctorItem {
  id: string;
  name: string;
  specialty: string;
  department?: string;
  qualifications?: string;
  experience_years?: number;
  consultation_type?: string;
  bio?: string;
  status: string;
  is_active?: boolean;
  created_at?: string;
}

interface Props {
  hospitalId?: string;
}

export const DoctorsManager: React.FC<Props> = ({ hospitalId = 'HOSP-CITY-01' }) => {
  const { showToast } = useToast();
  const [doctors, setDoctors] = useState<DoctorItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInviting, setIsInviting] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  const [newDoctor, setNewDoctor] = useState({
    name: '',
    specialty: 'Orthopedics',
    department: 'General Surgery',
    qualifications: 'MD, FACS, Board Certified',
    experience_years: 10,
    languages: ['English', 'Spanish'],
    consultation_type: 'IN_PERSON',
    default_appointment_duration: 30,
    bio: 'Dedicated clinician specializing in comprehensive patient care.',
  });

  const fetchDoctors = async () => {
    setIsLoading(true);
    try {
      const res = await apiCall(`/api/v1/hospital-dashboard/${hospitalId}/management`);
      if (res.ok && res.data?.management?.doctors) {
        setDoctors(res.data.management.doctors);
      }
    } catch (e) {
      console.error('Fetch doctors error:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDoctors();
  }, [hospitalId]);

  const handleApproveDoctor = async (doc: DoctorItem) => {
    setActionLoadingId(doc.id);
    try {
      const res = await apiCall(`/api/v1/hospitals/${hospitalId}/doctors/${doc.id}/approve`, {
        method: 'POST',
      });
      if (res.ok) {
        showToast(
          'success',
          'Doctor Approved & Credentialed',
          `Dr. ${doc.name} (${doc.specialty}) is now officially approved and activated for clinical practice.`
        );
        fetchDoctors();
      } else {
        showToast('error', 'Approval Error', res.error || 'Failed to approve doctor registration.');
      }
    } catch (e: any) {
      showToast('error', 'Network Error', e.message);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleRejectDoctor = async (doc: DoctorItem) => {
    setActionLoadingId(doc.id);
    try {
      const res = await apiCall(`/api/v1/hospitals/${hospitalId}/doctors/${doc.id}/reject`, {
        method: 'POST',
        body: JSON.stringify({ reason: 'Administrative review' })
      });
      if (res.ok) {
        showToast(
          'info',
          'Doctor Application Rejected',
          `Application for Dr. ${doc.name} was rejected.`
        );
        fetchDoctors();
      } else {
        showToast('error', 'Rejection Error', res.error || 'Failed to reject doctor.');
      }
    } catch (e: any) {
      showToast('error', 'Network Error', e.message);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleInviteDoctor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDoctor.name.trim()) return;

    setIsInviting(true);
    try {
      const res = await apiCall(`/api/v1/hospitals/${hospitalId}/doctors/invite`, {
        method: 'POST',
        body: JSON.stringify(newDoctor),
      });

      if (res.ok) {
        showToast(
          'success',
          'Physician Invited Successfully',
          `${newDoctor.name} (${newDoctor.specialty}) has been added to the medical staff roster.`
        );
        setShowInviteModal(false);
        setNewDoctor({
          name: '',
          specialty: 'Orthopedics',
          department: 'General Surgery',
          qualifications: 'MD, FACS, Board Certified',
          experience_years: 10,
          languages: ['English', 'Spanish'],
          consultation_type: 'IN_PERSON',
          default_appointment_duration: 30,
          bio: 'Dedicated clinician specializing in comprehensive patient care.',
        });
        fetchDoctors();
      }
    } catch (err: any) {
      showToast('error', 'Invitation Failed', err.message);
    } finally {
      setIsInviting(false);
    }
  };

  const handleToggleDoctorStatus = async (doctor: DoctorItem) => {
    const isActivating = doctor.status !== 'ACTIVE';
    const endpoint = isActivating
      ? `/api/v1/hospitals/${hospitalId}/doctors/${doctor.id}/approve`
      : `/api/v1/doctors/${doctor.id}/deactivate`;

    try {
      const res = await apiCall(endpoint, { method: 'POST' });
      if (res.ok) {
        showToast(
          'info',
          `Doctor ${isActivating ? 'Activated' : 'Deactivated'}`,
          `${doctor.name} scheduling state is now ${isActivating ? 'ACTIVE' : 'INACTIVE'}.`
        );
        fetchDoctors();
      }
    } catch (e: any) {
      showToast('error', 'Status Update Error', e.message);
    }
  };

  const pendingDoctors = doctors.filter(
    (d) => d.status === 'PENDING_APPROVAL' || d.status === 'INVITED' || !d.is_active
  );
  const activeDoctors = doctors.filter(
    (d) => d.status === 'ACTIVE' && d.is_active
  );

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-6 shadow-md">
      <div className="flex flex-wrap justify-between items-center pb-2 border-b border-slate-800 gap-2">
        <div>
          <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
            <Stethoscope className="w-4 h-4 text-indigo-400" />
            <span>Hospital Medical Staff &amp; Physician Credentialing</span>
          </h3>
          <p className="text-xs text-slate-400">
            Real physician directory retrieved via{' '}
            <code className="text-indigo-400 font-mono text-[11px]">
              GET /api/v1/hospital-dashboard/&#123;id&#125;/management
            </code>
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={fetchDoctors}
            disabled={isLoading}
            className="text-xs text-slate-400 hover:text-white flex items-center gap-1 p-1.5 rounded-lg hover:bg-slate-800 transition cursor-pointer"
            title="Refresh doctors"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={() => setShowInviteModal(true)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs px-3 py-1.5 rounded-lg transition shadow flex items-center space-x-1 cursor-pointer"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Invite New Physician</span>
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-xs text-slate-400 space-y-2">
          <RotateCw className="w-5 h-5 animate-spin mx-auto text-indigo-400" />
          <span>Loading medical staff directory...</span>
        </div>
      ) : (
        <div className="space-y-6">
          {/* SECTION 1: PENDING DOCTOR REGISTRATION & CREDENTIALING REQUESTS */}
          {pendingDoctors.length > 0 && (
            <div className="bg-amber-950/20 border border-amber-500/40 rounded-2xl p-4 space-y-3.5">
              <div className="flex items-center justify-between pb-2 border-b border-amber-500/20">
                <div className="flex items-center space-x-2">
                  <div className="w-7 h-7 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center">
                    <Clock className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
                      <span>Pending Doctor Registration Requests</span>
                      <span className="px-2 py-0.5 rounded-full bg-amber-500/30 text-amber-200 text-[10px] font-mono">
                        {pendingDoctors.length}
                      </span>
                    </h4>
                    <p className="text-[11px] text-amber-200/70">
                      The following physicians submitted registration requests for this hospital and require administrative review and approval.
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {pendingDoctors.map((doc) => (
                  <div
                    key={doc.id}
                    className="bg-slate-950/90 border border-amber-500/30 hover:border-amber-500/60 rounded-xl p-4 space-y-3 transition shadow-sm"
                  >
                    <div className="flex justify-between items-start gap-2">
                      <div className="flex items-start space-x-3">
                        <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center font-bold text-sm shrink-0">
                          {doc.name.replace(/^Dr\.\s*/i, '').slice(0, 2).toUpperCase() || 'DR'}
                        </div>
                        <div>
                          <h4 className="text-sm font-bold text-white flex items-center gap-1.5">
                            <span>{doc.name}</span>
                          </h4>
                          <p className="text-xs text-sky-400 font-semibold">{doc.specialty}</p>
                          <div className="text-[10px] text-slate-400 mt-0.5">
                            Dept: <span className="text-slate-300 font-medium">{doc.department || 'Clinical Practice'}</span>
                          </div>
                        </div>
                      </div>

                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30 shrink-0">
                        {doc.status}
                      </span>
                    </div>

                    <div className="bg-slate-900/60 rounded-lg p-2.5 text-[11px] text-slate-300 space-y-1">
                      {doc.qualifications && (
                        <div className="flex items-center space-x-1.5 text-slate-300">
                          <Award className="w-3 h-3 text-amber-400 shrink-0" />
                          <span className="truncate">{doc.qualifications}</span>
                        </div>
                      )}
                      {doc.experience_years && (
                        <div className="flex items-center space-x-1.5 text-slate-400">
                          <Briefcase className="w-3 h-3 text-indigo-400 shrink-0" />
                          <span>{doc.experience_years} Years Clinical Practice</span>
                        </div>
                      )}
                      {doc.bio && (
                        <p className="text-[10px] text-slate-400 italic line-clamp-2 pt-0.5">
                          "{doc.bio}"
                        </p>
                      )}
                    </div>

                    <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between gap-2">
                      <span className="text-[10px] font-mono text-slate-500">
                        ID: {doc.id}
                      </span>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleRejectDoctor(doc)}
                          disabled={actionLoadingId === doc.id}
                          className="px-2.5 py-1.5 rounded-lg border border-slate-700 hover:border-rose-500/50 hover:bg-rose-950/40 text-slate-400 hover:text-rose-300 text-xs font-semibold transition cursor-pointer disabled:opacity-50 flex items-center space-x-1"
                        >
                          <X className="w-3.5 h-3.5" />
                          <span>Reject</span>
                        </button>

                        <button
                          onClick={() => handleApproveDoctor(doc)}
                          disabled={actionLoadingId === doc.id}
                          className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs shadow transition cursor-pointer disabled:opacity-50 flex items-center space-x-1.5"
                        >
                          {actionLoadingId === doc.id ? (
                            <RotateCw className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Check className="w-3.5 h-3.5" />
                          )}
                          <span>Approve &amp; Credential</span>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SECTION 2: ACTIVE & CREDENTIALED MEDICAL STAFF ROSTER */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <span>Active &amp; Credentialed Medical Staff</span>
                <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 text-[10px] font-mono">
                  {activeDoctors.length}
                </span>
              </h4>
            </div>

            {activeDoctors.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500 space-y-2 bg-slate-950/40 border border-slate-800 rounded-xl p-4">
                <div className="w-9 h-9 rounded-full bg-slate-800 text-slate-400 mx-auto flex items-center justify-center">
                  <Stethoscope className="w-4 h-4" />
                </div>
                <div className="font-bold text-slate-300">No Active Doctors on Roster</div>
                <p className="max-w-xs mx-auto text-[11px]">
                  Approve pending applications above or invite doctors to join this hospital.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {activeDoctors.map((doc) => (
                  <div
                    key={doc.id}
                    className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3 hover:border-indigo-500/30 transition"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center font-bold text-sm">
                          {doc.name.replace(/^Dr\.\s*/i, '').slice(0, 2).toUpperCase() || 'DR'}
                        </div>
                        <div>
                          <h4 className="text-sm font-bold text-white">{doc.name}</h4>
                          <p className="text-xs text-indigo-400 font-medium">{doc.specialty}</p>
                          <div className="text-[10px] text-slate-400 font-mono mt-0.5">ID: {doc.id}</div>
                        </div>
                      </div>

                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        ACTIVE
                      </span>
                    </div>

                    <div className="pt-2 border-t border-slate-900 flex justify-between items-center text-xs">
                      <span className="text-slate-400 text-[11px]">
                        Department: <strong className="text-slate-200">{doc.department || 'General'}</strong>
                      </span>

                      <button
                        onClick={() => handleToggleDoctorStatus(doc)}
                        className="px-2.5 py-1 rounded-lg font-bold text-[11px] transition bg-slate-800 hover:bg-rose-950/50 text-slate-300 hover:text-rose-300 cursor-pointer"
                      >
                        Deactivate
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Invite Doctor Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl animate-in zoom-in-95">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <h3 className="font-bold text-base text-white flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-indigo-400" />
                <span>Invite New Physician to Staff Roster</span>
              </h3>
              <button
                onClick={() => setShowInviteModal(false)}
                className="text-slate-400 hover:text-white"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleInviteDoctor} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-bold mb-1 uppercase text-[10px]">
                  Doctor Full Name:
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Dr. Emily Watson, MD"
                  value={newDoctor.name}
                  onChange={(e) => setNewDoctor({ ...newDoctor, name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-bold mb-1 uppercase text-[10px]">
                    Specialty:
                  </label>
                  <select
                    value={newDoctor.specialty}
                    onChange={(e) => setNewDoctor({ ...newDoctor, specialty: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="Orthopedics">Orthopedic Surgery</option>
                    <option value="Cardiology">Cardiology</option>
                    <option value="Dermatology">Dermatology</option>
                    <option value="Neurology">Neurology</option>
                    <option value="Pediatrics">Pediatrics</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 font-bold mb-1 uppercase text-[10px]">
                    Department:
                  </label>
                  <input
                    type="text"
                    value={newDoctor.department}
                    onChange={(e) => setNewDoctor({ ...newDoctor, department: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-bold mb-1 uppercase text-[10px]">
                  Qualifications &amp; Credentials:
                </label>
                <input
                  type="text"
                  value={newDoctor.qualifications}
                  onChange={(e) => setNewDoctor({ ...newDoctor, qualifications: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isInviting}
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold shadow disabled:opacity-50"
                >
                  {isInviting ? 'Registering...' : 'Invite Physician'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
