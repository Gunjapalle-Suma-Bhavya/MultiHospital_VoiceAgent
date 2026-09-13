import React, { useState, useEffect } from 'react';
import {
  Building2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  ShieldCheck,
  Search,
  RefreshCw,
  Phone,
  Mail,
  MapPin,
  Tag,
  ChevronRight,
  Check,
  X,
  Hospital as HospitalIcon,
  Eye,
  AlertTriangle
} from 'lucide-react';
import { apiCall } from '../../api/client';

export interface HospitalApplication {
  hospital_id: string;
  name: string;
  code: string;
  contact_email: string;
  phone?: string;
  address?: string;
  organization_info?: string;
  admin_name?: string;
  admin_email?: string;
  admin_phone?: string;
  hospital_status: 'DRAFT' | 'SUBMITTED' | 'UNDER_REVIEW' | 'APPROVED' | 'REJECTED' | 'SUSPENDED';
  is_active: boolean;
  departments: string[];
  specialties: string[];
  rejection_reason?: string;
  correction_notes?: string;
  suspension_reason?: string;
  created_at?: string;
  updated_at?: string;
}

interface ApplicationCounts {
  pending: number;
  approved: number;
  rejected: number;
  suspended: number;
  total: number;
}

export const HospitalApplicationsBoard: React.FC = () => {
  const [applications, setApplications] = useState<HospitalApplication[]>([]);
  const [counts, setCounts] = useState<ApplicationCounts>({
    pending: 0,
    approved: 0,
    rejected: 0,
    suspended: 0,
    total: 0,
  });
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('PENDING');
  const [searchQuery, setSearchQuery] = useState('');
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Reject Modal State
  const [rejectingHospital, setRejectingHospital] = useState<HospitalApplication | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  // Details Modal State
  const [selectedHospital, setSelectedHospital] = useState<HospitalApplication | null>(null);

  const fetchApplications = async (statusOverride?: string) => {
    setLoading(true);
    try {
      const queryStatus = statusOverride !== undefined ? statusOverride : filterStatus;
      const endpoint = queryStatus && queryStatus !== 'ALL'
        ? `/api/v1/admin/hospitals?status=${queryStatus}`
        : '/api/v1/admin/hospitals';

      const res = await apiCall(endpoint);
      if (res.ok && res.data) {
        setApplications(res.data.applications || []);
        if (res.data.counts) {
          setCounts(res.data.counts);
        }
      }
    } catch (err: any) {
      console.error('Failed to load hospital applications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications(filterStatus);
  }, [filterStatus]);

  const handleApprove = async (hospitalId: string, hospitalName: string) => {
    setActionLoading(hospitalId);
    setFeedback(null);
    try {
      const res = await apiCall(`/api/v1/admin/hospitals/${hospitalId}/approve`, {
        method: 'POST',
      });
      if (res.ok) {
        setFeedback({
          type: 'success',
          text: `"${hospitalName}" has been successfully approved and activated in the healthcare network.`,
        });
        await fetchApplications();
      } else {
        setFeedback({
          type: 'error',
          text: res.error || `Failed to approve hospital "${hospitalName}".`,
        });
      }
    } catch (err: any) {
      setFeedback({ type: 'error', text: err?.message || 'Network error approving hospital.' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleRejectSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectingHospital || !rejectReason.trim()) return;

    setActionLoading(rejectingHospital.hospital_id);
    setFeedback(null);
    try {
      const res = await apiCall(`/api/v1/admin/hospitals/${rejectingHospital.hospital_id}/reject`, {
        method: 'POST',
        body: JSON.stringify({ reason: rejectReason.trim() }),
      });
      if (res.ok) {
        setFeedback({
          type: 'success',
          text: `"${rejectingHospital.name}" has been rejected. Reason recorded in audit ledger.`,
        });
        setRejectingHospital(null);
        setRejectReason('');
        await fetchApplications();
      } else {
        setFeedback({
          type: 'error',
          text: res.error || `Failed to reject hospital.`,
        });
      }
    } catch (err: any) {
      setFeedback({ type: 'error', text: err?.message || 'Network error rejecting hospital.' });
    } finally {
      setActionLoading(null);
    }
  };

  // Filtered by local search query
  const displayedApplications = applications.filter((app) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      app.name.toLowerCase().includes(q) ||
      app.code.toLowerCase().includes(q) ||
      (app.admin_name && app.admin_name.toLowerCase().includes(q)) ||
      (app.contact_email && app.contact_email.toLowerCase().includes(q))
    );
  });

  const getStatusBadge = (status: string, isActive: boolean) => {
    switch (status) {
      case 'APPROVED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3" />
            <span>Approved &amp; Active</span>
          </span>
        );
      case 'SUBMITTED':
      case 'UNDER_REVIEW':
      case 'DRAFT':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 animate-pulse">
            <Clock className="w-3 h-3" />
            <span>Pending Review</span>
          </span>
        );
      case 'REJECTED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <XCircle className="w-3 h-3" />
            <span>Rejected</span>
          </span>
        );
      case 'SUSPENDED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/30">
            <AlertTriangle className="w-3 h-3" />
            <span>Suspended</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-slate-800 text-slate-400">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-black text-white flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-amber-400" />
            <span>Hospital Onboarding &amp; Registration Approval Queue</span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Evaluate, verify, and approve or reject healthcare facility requests submitted by hospital administrators across the platform.
          </p>
        </div>

        <button
          onClick={() => fetchApplications()}
          disabled={loading}
          className="self-start sm:self-auto bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-semibold px-3 py-2 rounded-xl text-slate-300 hover:text-white transition flex items-center space-x-1.5 shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-amber-400' : ''}`} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* KPI Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div
          onClick={() => setFilterStatus('PENDING')}
          className={`p-4 rounded-2xl border cursor-pointer transition ${
            filterStatus === 'PENDING'
              ? 'bg-amber-500/15 border-amber-500/60 shadow-lg shadow-amber-500/10'
              : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Pending Action</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-amber-400 mt-2">{counts.pending}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Awaiting Admin Decision</div>
        </div>

        <div
          onClick={() => setFilterStatus('APPROVED')}
          className={`p-4 rounded-2xl border cursor-pointer transition ${
            filterStatus === 'APPROVED'
              ? 'bg-emerald-500/15 border-emerald-500/60 shadow-lg shadow-emerald-500/10'
              : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Approved Active</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-emerald-400 mt-2">{counts.approved}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Live In Provider Network</div>
        </div>

        <div
          onClick={() => setFilterStatus('REJECTED')}
          className={`p-4 rounded-2xl border cursor-pointer transition ${
            filterStatus === 'REJECTED'
              ? 'bg-rose-500/15 border-rose-500/60 shadow-lg shadow-rose-500/10'
              : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Rejected</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-black text-rose-400 mt-2">{counts.rejected}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Incomplete or Unverified</div>
        </div>

        <div
          onClick={() => setFilterStatus('ALL')}
          className={`p-4 rounded-2xl border cursor-pointer transition ${
            filterStatus === 'ALL'
              ? 'bg-sky-500/15 border-sky-500/60 shadow-lg shadow-sky-500/10'
              : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">All Facilities</span>
            <Building2 className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-black text-white mt-2">{counts.total}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Total System Applications</div>
        </div>
      </div>

      {/* Action Alerts */}
      {feedback && (
        <div
          className={`p-3.5 rounded-2xl text-xs flex items-start space-x-2.5 border ${
            feedback.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}
        >
          {feedback.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />
          )}
          <span>{feedback.text}</span>
        </div>
      )}

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-slate-900/80 p-3 rounded-2xl border border-slate-800">
        <div className="flex items-center space-x-1.5 text-xs overflow-x-auto w-full sm:w-auto">
          <button
            onClick={() => setFilterStatus('PENDING')}
            className={`px-3 py-1.5 rounded-xl font-bold transition whitespace-nowrap ${
              filterStatus === 'PENDING'
                ? 'bg-amber-500 text-slate-950 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            Pending Review ({counts.pending})
          </button>
          <button
            onClick={() => setFilterStatus('APPROVED')}
            className={`px-3 py-1.5 rounded-xl font-bold transition whitespace-nowrap ${
              filterStatus === 'APPROVED'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            Approved ({counts.approved})
          </button>
          <button
            onClick={() => setFilterStatus('REJECTED')}
            className={`px-3 py-1.5 rounded-xl font-bold transition whitespace-nowrap ${
              filterStatus === 'REJECTED'
                ? 'bg-rose-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            Rejected ({counts.rejected})
          </button>
          <button
            onClick={() => setFilterStatus('ALL')}
            className={`px-3 py-1.5 rounded-xl font-bold transition whitespace-nowrap ${
              filterStatus === 'ALL'
                ? 'bg-slate-800 text-white shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            All Applications
          </button>
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search name, code, email..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
          />
        </div>
      </div>

      {/* Applications List */}
      {loading ? (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-12 text-center space-y-3">
          <div className="w-7 h-7 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <div className="text-xs text-slate-400">Loading hospital registration requests...</div>
        </div>
      ) : displayedApplications.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-12 text-center space-y-3">
          <HospitalIcon className="w-10 h-10 text-slate-600 mx-auto" />
          <div className="text-sm font-bold text-slate-300">
            {filterStatus === 'PENDING' ? 'No Pending Requests Awaiting Approval' : 'No Hospitals Found'}
          </div>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {filterStatus === 'PENDING'
              ? 'All hospital registration requests have been reviewed and processed.'
              : 'Try changing the status filter or clearing your search term.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3.5">
          {displayedApplications.map((hosp) => {
            const isPending = hosp.hospital_status === 'SUBMITTED' || hosp.hospital_status === 'UNDER_REVIEW' || hosp.hospital_status === 'DRAFT';
            const isActioning = actionLoading === hosp.hospital_id;

            return (
              <div
                key={hosp.hospital_id}
                className={`bg-slate-900/80 border rounded-2xl p-5 transition flex flex-col lg:flex-row lg:items-center justify-between gap-4 shadow-md ${
                  isPending
                    ? 'border-amber-500/40 hover:border-amber-400/70 bg-gradient-to-r from-slate-900/90 to-amber-950/10'
                    : 'border-slate-800 hover:border-slate-700'
                }`}
              >
                {/* Facility Info */}
                <div className="space-y-2.5 max-w-2xl">
                  <div className="flex flex-wrap items-center gap-2">
                    <h4 className="text-base font-extrabold text-white flex items-center space-x-2">
                      <span>{hosp.name}</span>
                    </h4>
                    <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                      {hosp.code}
                    </span>
                    {getStatusBadge(hosp.hospital_status, hosp.is_active)}
                  </div>

                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-slate-400">
                    {hosp.contact_email && (
                      <span className="flex items-center space-x-1">
                        <Mail className="w-3.5 h-3.5 text-slate-500" />
                        <span>{hosp.contact_email}</span>
                      </span>
                    )}
                    {hosp.phone && (
                      <span className="flex items-center space-x-1">
                        <Phone className="w-3.5 h-3.5 text-slate-500" />
                        <span>{hosp.phone}</span>
                      </span>
                    )}
                    {hosp.admin_name && (
                      <span className="text-slate-300">
                        Admin: <strong className="text-white">{hosp.admin_name}</strong> ({hosp.admin_email || 'No email'})
                      </span>
                    )}
                  </div>

                  {/* Departments / Specialties */}
                  {((hosp.departments && hosp.departments.length > 0) || (hosp.specialties && hosp.specialties.length > 0)) && (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {hosp.departments?.map((dept, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-slate-800/80 text-sky-300 border border-slate-700/60"
                        >
                          {dept}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Rejection reason note if rejected */}
                  {hosp.rejection_reason && (
                    <div className="text-xs text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-xl p-2.5 flex items-start space-x-2">
                      <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
                      <span>Rejection Rationale: {hosp.rejection_reason}</span>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2 shrink-0 pt-2 lg:pt-0 border-t lg:border-t-0 border-slate-800">
                  {isPending ? (
                    <>
                      <button
                        type="button"
                        disabled={isActioning}
                        onClick={() => handleApprove(hosp.hospital_id, hosp.name)}
                        className="bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-extrabold text-xs px-4 py-2 rounded-xl transition flex items-center space-x-1.5 shadow-md shadow-emerald-500/20 disabled:opacity-50 cursor-pointer"
                        title="Approve and activate hospital facility"
                      >
                        {isActioning ? (
                          <span className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <Check className="w-3.5 h-3.5" />
                        )}
                        <span>Approve Facility</span>
                      </button>

                      <button
                        type="button"
                        disabled={isActioning}
                        onClick={() => {
                          setRejectingHospital(hosp);
                          setRejectReason('');
                        }}
                        className="bg-slate-800 hover:bg-rose-950/40 text-rose-400 hover:text-rose-300 border border-slate-700 hover:border-rose-500/40 text-xs font-bold px-3 py-2 rounded-xl transition flex items-center space-x-1.5 cursor-pointer"
                        title="Reject hospital application"
                      >
                        <X className="w-3.5 h-3.5" />
                        <span>Reject</span>
                      </button>
                    </>
                  ) : hosp.hospital_status === 'REJECTED' ? (
                    <button
                      type="button"
                      disabled={isActioning}
                      onClick={() => handleApprove(hosp.hospital_id, hosp.name)}
                      className="bg-slate-800 hover:bg-emerald-950/40 text-emerald-400 hover:text-emerald-300 border border-slate-700 hover:border-emerald-500/40 text-xs font-bold px-3 py-2 rounded-xl transition flex items-center space-x-1.5 cursor-pointer"
                      title="Reconsider and approve hospital"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Re-Approve</span>
                    </button>
                  ) : null}

                  <button
                    type="button"
                    onClick={() => setSelectedHospital(hosp)}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs font-semibold px-2.5 py-2 rounded-xl transition flex items-center space-x-1"
                    title="View complete metadata"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">Details</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Reject Reason Modal */}
      {rejectingHospital && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-lg w-full p-6 space-y-5 shadow-2xl relative">
            <button
              onClick={() => setRejectingHospital(null)}
              className="absolute top-5 right-5 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="space-y-1">
              <div className="flex items-center space-x-2 text-rose-400 text-xs font-bold uppercase tracking-wider">
                <XCircle className="w-4 h-4" />
                <span>Reject Hospital Application</span>
              </div>
              <h3 className="text-lg font-black text-white">
                Reject "{rejectingHospital.name}"
              </h3>
              <p className="text-xs text-slate-400">
                Please provide the audit rationale for rejecting this facility. The reason will be stored in the regulatory audit trail.
              </p>
            </div>

            <form onSubmit={handleRejectSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1.5">
                  Rejection Reason / Missing Documentation:
                </label>
                <textarea
                  required
                  rows={4}
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="e.g. Incomplete clinical licensing, invalid NPI accreditation documentation, or unverified contact."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setRejectingHospital(null)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading !== null}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-rose-600 hover:bg-rose-500 transition shadow-md shadow-rose-600/20 disabled:opacity-50"
                >
                  Confirm Rejection
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Full Details Modal */}
      {selectedHospital && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-2xl w-full p-6 sm:p-8 space-y-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setSelectedHospital(null)}
              className="absolute top-5 right-5 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="space-y-1">
              <span className="font-mono text-xs text-sky-400 font-bold">FACILITY CODE: {selectedHospital.code}</span>
              <h3 className="text-xl font-black text-white">{selectedHospital.name}</h3>
              <div className="pt-1">{getStatusBadge(selectedHospital.hospital_status, selectedHospital.is_active)}</div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1">
                <span className="text-slate-500 font-bold uppercase tracking-wider text-[10px]">Contact Info</span>
                <div className="text-white font-medium">{selectedHospital.contact_email || 'Not specified'}</div>
                <div className="text-slate-400">{selectedHospital.phone || 'No phone'}</div>
                <div className="text-slate-400">{selectedHospital.address || 'No physical address'}</div>
              </div>

              <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1">
                <span className="text-slate-500 font-bold uppercase tracking-wider text-[10px]">Facility Administrator</span>
                <div className="text-white font-medium">{selectedHospital.admin_name || 'Not assigned'}</div>
                <div className="text-slate-400">{selectedHospital.admin_email || 'No admin email'}</div>
              </div>
            </div>

            {selectedHospital.departments && selectedHospital.departments.length > 0 && (
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-300">Departments &amp; Specialties:</span>
                <div className="flex flex-wrap gap-2">
                  {selectedHospital.departments.map((d, i) => (
                    <span key={i} className="text-xs font-semibold bg-slate-800 text-sky-300 px-2.5 py-1 rounded-lg border border-slate-700">
                      {d}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-4 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedHospital(null)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 transition"
              >
                Close Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
