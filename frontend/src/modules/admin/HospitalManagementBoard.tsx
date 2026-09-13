import React, { useState, useEffect } from 'react';
import {
  Building2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Search,
  Filter,
  MapPin,
  Mail,
  Phone,
  Shield,
  Layers,
  PauseCircle,
  PlayCircle,
  Eye,
  Info
} from 'lucide-react';
import { apiCall } from '../../api/client';
import { HospitalApplication } from './HospitalApplicationsBoard';

export const HospitalManagementBoard: React.FC = () => {
  const [hospitals, setHospitals] = useState<HospitalApplication[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'APPROVED' | 'SUSPENDED'>('ALL');
  const [selectedHospital, setSelectedHospital] = useState<HospitalApplication | null>(null);
  
  // Suspend modal state
  const [suspendTarget, setSuspendTarget] = useState<HospitalApplication | null>(null);
  const [suspendReason, setSuspendReason] = useState<string>('');
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const fetchHospitals = async () => {
    setIsLoading(true);
    try {
      const res = await apiCall('/api/v1/admin/hospitals');
      if (res.ok && res.data?.applications) {
        setHospitals(res.data.applications);
      }
    } catch {
      // fallback
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHospitals();
  }, []);

  const handleSuspend = async () => {
    if (!suspendTarget || !suspendReason.trim()) return;
    setActionLoading(true);
    try {
      const res = await apiCall(`/api/v1/admin/hospitals/${suspendTarget.hospital_id}/suspend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: suspendReason.trim() })
      });
      if (res.ok) {
        setHospitals(prev =>
          prev.map(h =>
            h.hospital_id === suspendTarget.hospital_id
              ? { ...h, hospital_status: 'SUSPENDED', is_active: false, suspension_reason: suspendReason.trim() }
              : h
          )
        );
        setFeedbackMessage(`Hospital "${suspendTarget.name}" has been suspended.`);
        setSuspendTarget(null);
        setSuspendReason('');
      } else {
        alert(res.error || 'Failed to suspend hospital');
      }
    } catch (err: any) {
      alert(err?.message || 'Error suspending hospital');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReactivate = async (hospital: HospitalApplication) => {
    setActionLoading(true);
    try {
      const res = await apiCall(`/api/v1/admin/hospitals/${hospital.hospital_id}/reactivate`, {
        method: 'POST'
      });
      if (res.ok) {
        setHospitals(prev =>
          prev.map(h =>
            h.hospital_id === hospital.hospital_id
              ? { ...h, hospital_status: 'APPROVED', is_active: true, suspension_reason: undefined }
              : h
          )
        );
        setFeedbackMessage(`Hospital "${hospital.name}" has been successfully reactivated.`);
      } else {
        alert(res.error || 'Failed to reactivate hospital');
      }
    } catch (err: any) {
      alert(err?.message || 'Error reactivating hospital');
    } finally {
      setActionLoading(false);
    }
  };

  const filteredHospitals = hospitals.filter(h => {
    // Filter status
    if (statusFilter === 'APPROVED' && h.hospital_status !== 'APPROVED') return false;
    if (statusFilter === 'SUSPENDED' && h.hospital_status !== 'SUSPENDED') return false;

    // Search query
    const q = searchQuery.toLowerCase();
    return (
      (h.name && h.name.toLowerCase().includes(q)) ||
      (h.code && h.code.toLowerCase().includes(q)) ||
      (h.contact_email && h.contact_email.toLowerCase().includes(q)) ||
      (h.address && h.address.toLowerCase().includes(q))
    );
  });

  const activeCount = hospitals.filter(h => h.hospital_status === 'APPROVED' || h.is_active).length;
  const suspendedCount = hospitals.filter(h => h.hospital_status === 'SUSPENDED').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold text-amber-400 uppercase tracking-widest">
            <Building2 className="w-4 h-4" />
            <span>Statewide Network Directory &bull; Facility Operations</span>
          </div>
          <h2 className="text-2xl font-black text-white mt-1">Hospital Management</h2>
          <p className="text-sm text-slate-400">
            Oversee active hospital tenants, verify clinical capacity, review compliance, and manage operational status.
          </p>
        </div>

        <button
          onClick={fetchHospitals}
          disabled={isLoading}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs transition border border-slate-700 shadow"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-amber-400' : ''}`} />
          <span>Refresh Directory</span>
        </button>
      </div>

      {/* Feedback Banner */}
      {feedbackMessage && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 flex items-center space-x-3 text-emerald-300 text-sm font-semibold">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          <span>{feedbackMessage}</span>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Enrolled Facilities</div>
          <div className="text-3xl font-black text-white mt-1">{hospitals.length}</div>
          <div className="text-xs text-slate-500 mt-1">All registered health systems</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Active &amp; Operational</div>
          <div className="text-3xl font-black text-emerald-300 mt-1">{activeCount}</div>
          <div className="text-xs text-slate-500 mt-1">Accepting appointments &amp; intake</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="text-xs font-bold text-rose-400 uppercase tracking-wider">Suspended Facilities</div>
          <div className="text-3xl font-black text-rose-400 mt-1">{suspendedCount}</div>
          <div className="text-xs text-slate-500 mt-1">Routing temporarily paused</div>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        <div className="flex items-center space-x-1.5">
          <Filter className="w-4 h-4 text-slate-500 mr-1 flex-shrink-0" />
          <button
            onClick={() => setStatusFilter('ALL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
              statusFilter === 'ALL' ? 'bg-amber-500 text-slate-950 shadow' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            All ({hospitals.length})
          </button>
          <button
            onClick={() => setStatusFilter('APPROVED')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
              statusFilter === 'APPROVED' ? 'bg-amber-500 text-slate-950 shadow' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Operational ({activeCount})
          </button>
          <button
            onClick={() => setStatusFilter('SUSPENDED')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
              statusFilter === 'SUSPENDED' ? 'bg-amber-500 text-slate-950 shadow' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Suspended ({suspendedCount})
          </button>
        </div>

        <div className="relative min-w-[280px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by hospital name, code, city..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white focus:outline-none focus:border-amber-500 transition"
          />
        </div>
      </div>

      {/* Hospitals Grid */}
      {isLoading ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin text-amber-400" />
          <p className="text-sm font-semibold">Loading statewide hospital directory...</p>
        </div>
      ) : filteredHospitals.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
          <Building2 className="w-10 h-10 text-slate-600 mx-auto mb-2" />
          <p className="text-base font-bold text-slate-200">No hospitals found</p>
          <p className="text-xs text-slate-500 mt-1">
            {searchQuery ? `No matches for "${searchQuery}".` : 'No hospital records in this category.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredHospitals.map(hospital => (
            <div
              key={hospital.hospital_id}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4 hover:border-slate-700 transition"
            >
              {/* Card Header */}
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="font-bold text-white text-base">{hospital.name}</h3>
                    <span className="font-mono text-[11px] font-bold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                      {hospital.code}
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 flex items-center space-x-1.5 mt-1">
                    <Mail className="w-3.5 h-3.5 text-slate-500" />
                    <span>{hospital.contact_email}</span>
                    {hospital.phone && (
                      <>
                        <span>&bull;</span>
                        <Phone className="w-3.5 h-3.5 text-slate-500" />
                        <span>{hospital.phone}</span>
                      </>
                    )}
                  </div>
                </div>

                <div>
                  {hospital.hospital_status === 'APPROVED' || hospital.is_active ? (
                    <span className="inline-flex items-center space-x-1 text-[11px] font-bold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>Operational</span>
                    </span>
                  ) : hospital.hospital_status === 'SUSPENDED' ? (
                    <span className="inline-flex items-center space-x-1 text-[11px] font-bold px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
                      <XCircle className="w-3 h-3" />
                      <span>Suspended</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center space-x-1 text-[11px] font-bold px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                      <AlertTriangle className="w-3 h-3" />
                      <span>{hospital.hospital_status}</span>
                    </span>
                  )}
                </div>
              </div>

              {/* Address */}
              {hospital.address && (
                <div className="text-xs text-slate-400 flex items-center space-x-1.5 bg-slate-950/60 p-2.5 rounded-xl">
                  <MapPin className="w-4 h-4 text-slate-500 flex-shrink-0" />
                  <span className="truncate">{hospital.address}</span>
                </div>
              )}

              {/* Suspension Notice */}
              {hospital.suspension_reason && (
                <div className="text-xs bg-rose-500/10 border border-rose-500/20 text-rose-300 p-2.5 rounded-xl flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  <span>Suspension Note: {hospital.suspension_reason}</span>
                </div>
              )}

              {/* Departments Chips */}
              {hospital.departments && hospital.departments.length > 0 && (
                <div>
                  <div className="text-[11px] text-slate-400 font-semibold mb-1">Clinical Departments:</div>
                  <div className="flex flex-wrap gap-1">
                    {hospital.departments.map((dept, i) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {dept}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions Footer */}
              <div className="border-t border-slate-800/80 pt-3 flex justify-between items-center text-xs">
                <button
                  onClick={() => setSelectedHospital(hospital)}
                  className="text-amber-400 hover:text-amber-300 font-bold flex items-center space-x-1 transition"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>View Details</span>
                </button>

                <div className="flex items-center space-x-2">
                  {hospital.hospital_status === 'APPROVED' || hospital.is_active ? (
                    <button
                      onClick={() => setSuspendTarget(hospital)}
                      disabled={actionLoading}
                      className="px-3 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 font-bold text-xs transition flex items-center space-x-1"
                    >
                      <PauseCircle className="w-3.5 h-3.5" />
                      <span>Suspend</span>
                    </button>
                  ) : hospital.hospital_status === 'SUSPENDED' ? (
                    <button
                      onClick={() => handleReactivate(hospital)}
                      disabled={actionLoading}
                      className="px-3 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 font-bold text-xs transition flex items-center space-x-1"
                    >
                      <PlayCircle className="w-3.5 h-3.5" />
                      <span>Reactivate</span>
                    </button>
                  ) : null}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Suspend Confirmation Modal */}
      {suspendTarget && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center space-x-3 text-rose-400">
              <AlertTriangle className="w-6 h-6" />
              <h3 className="text-lg font-bold text-white">Suspend Hospital Facility</h3>
            </div>
            <p className="text-xs text-slate-300">
              You are about to suspend <span className="font-bold text-white">{suspendTarget.name}</span>. This will immediately disable voice intake routing and appointment scheduling for this facility.
            </p>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Reason for Suspension *
              </label>
              <textarea
                rows={3}
                required
                placeholder="e.g. Scheduled EHR migration, emergency audit, compliance review..."
                value={suspendReason}
                onChange={e => setSuspendReason(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-rose-500"
              />
            </div>
            <div className="flex justify-end space-x-3 pt-2">
              <button
                onClick={() => {
                  setSuspendTarget(null);
                  setSuspendReason('');
                }}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold transition"
              >
                Cancel
              </button>
              <button
                onClick={handleSuspend}
                disabled={!suspendReason.trim() || actionLoading}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition disabled:opacity-50"
              >
                {actionLoading ? 'Suspending...' : 'Confirm Suspension'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View Details Modal */}
      {selectedHospital && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-bold text-white">{selectedHospital.name}</h3>
                <span className="font-mono text-xs text-indigo-400 font-bold">{selectedHospital.code}</span>
              </div>
              <button
                onClick={() => setSelectedHospital(null)}
                className="text-slate-400 hover:text-white text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs text-slate-300">
              <div className="bg-slate-950 p-3 rounded-xl space-y-1">
                <div className="text-[11px] text-slate-500 font-semibold uppercase">Tenant Identifier</div>
                <div className="font-mono text-slate-300">{selectedHospital.hospital_id}</div>
              </div>

              <div>
                <span className="text-slate-500 font-semibold">Contact Email:</span> {selectedHospital.contact_email}
              </div>
              {selectedHospital.phone && (
                <div>
                  <span className="text-slate-500 font-semibold">Phone:</span> {selectedHospital.phone}
                </div>
              )}
              {selectedHospital.address && (
                <div>
                  <span className="text-slate-500 font-semibold">Address:</span> {selectedHospital.address}
                </div>
              )}
              {selectedHospital.organization_info && (
                <div>
                  <span className="text-slate-500 font-semibold">Organization Info:</span>
                  <p className="mt-1 text-slate-400">{selectedHospital.organization_info}</p>
                </div>
              )}
              {selectedHospital.admin_name && (
                <div>
                  <span className="text-slate-500 font-semibold">Facility Admin:</span> {selectedHospital.admin_name} ({selectedHospital.admin_email})
                </div>
              )}
            </div>

            <div className="flex justify-end pt-3">
              <button
                onClick={() => setSelectedHospital(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
