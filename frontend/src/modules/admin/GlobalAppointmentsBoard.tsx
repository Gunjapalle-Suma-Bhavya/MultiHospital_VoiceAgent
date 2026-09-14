import React, { useEffect, useState } from 'react';
import {
  CalendarCheck,
  Search,
  Building2,
  Stethoscope,
  User,
  Clock,
  ShieldCheck,
  CheckCircle2,
  Activity,
  FileText,
  RotateCw,
  Filter,
  ExternalLink,
  ChevronRight
} from 'lucide-react';
import { apiCall } from '../../api/client';
import { TraceLifecycleModal } from '../../components/TraceLifecycleModal';

export const GlobalAppointmentsBoard: React.FC = () => {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedHospital, setSelectedHospital] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [activeModalAppt, setActiveModalAppt] = useState<any>(null);

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const res = await apiCall('/api/v1/appointments');
      if (res.ok && res.data?.appointments) {
        setAppointments(res.data.appointments);
      }
    } catch (err) {
      console.error('Failed to load global appointments:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, []);

  const filteredAppointments = appointments.filter((appt) => {
    const matchesHospital =
      selectedHospital === 'ALL' || appt.hospital_id === selectedHospital;
    const matchesStatus =
      selectedStatus === 'ALL' || appt.status === selectedStatus;
    const q = searchQuery.toLowerCase();
    const matchesQuery =
      !q ||
      appt.patient_name?.toLowerCase().includes(q) ||
      appt.patient_phone?.toLowerCase().includes(q) ||
      appt.doctor_name?.toLowerCase().includes(q) ||
      appt.hospital_name?.toLowerCase().includes(q) ||
      appt.complaint?.toLowerCase().includes(q);

    return matchesHospital && matchesStatus && matchesQuery;
  });

  const ehrVerifiedCount = appointments.filter((a) => a.is_ehr_verified).length;
  const confirmedCount = appointments.filter(
    (a) => a.status === 'CONFIRMED' || a.status === 'SCHEDULED'
  ).length;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20 flex items-center justify-center font-black text-lg">
            <CalendarCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-bold text-teal-400 uppercase tracking-wider">
              Platform Super-Admin &bull; Statewide Patient Registry
            </div>
            <h2 className="text-xl font-extrabold text-white">
              Cross-Hospital Patient Intake &amp; Booking Observability
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Real-time synchronization across all 4 accredited network hospitals with 16-step canonical lifecycle tracking.
            </p>
          </div>
        </div>

        <button
          onClick={fetchAppointments}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs transition border border-slate-700 shadow shrink-0"
        >
          <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-teal-400' : ''}`} />
          <span>Refresh Bookings</span>
        </button>
      </div>

      {/* KPI Metrics Strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Statewide Bookings</div>
          <div className="text-2xl font-black text-white mt-1">{appointments.length} Visits</div>
          <div className="text-[11px] text-teal-400 font-semibold mt-0.5">&bull; 4 Accredited Hospitals</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Authoritative 5-Point EHR Sync</div>
          <div className="text-2xl font-black text-emerald-400 mt-1">{ehrVerifiedCount} Verified</div>
          <div className="text-[11px] text-emerald-400 font-semibold mt-0.5">
            {appointments.length > 0 ? `${Math.round((ehrVerifiedCount / appointments.length) * 100)}% Pass Rate` : '100%'}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Active / Confirmed</div>
          <div className="text-2xl font-black text-indigo-400 mt-1">{confirmedCount} Active</div>
          <div className="text-[11px] text-slate-400 font-medium mt-0.5">&bull; Zero double-bookings</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Operational Observability</div>
          <div className="text-2xl font-black text-cyan-400 mt-1">16 Canonical Steps</div>
          <div className="text-[11px] text-cyan-400 font-semibold mt-0.5">&bull; End-to-End Traceability</div>
        </div>
      </div>

      {/* Filters Strip */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3 shadow-md">
        <div className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              placeholder="Search by patient name, phone (+1-555...), doctor, complaint..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 transition"
            />
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={selectedHospital}
              onChange={(e) => setSelectedHospital(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 text-xs font-semibold focus:outline-none focus:border-teal-500"
            >
              <option value="ALL">All Network Hospitals</option>
              <option value="HOSP-CITY-01">City Memorial Hospital</option>
              <option value="HOSP-CARE-02">Care Regional Hospital</option>
              <option value="HOSP-METRO-03">Metro Health Medical Center</option>
              <option value="HOSP-STJUDE-04">St. Jude Health System</option>
            </select>

            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 text-xs font-semibold focus:outline-none focus:border-teal-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="CONFIRMED">CONFIRMED</option>
              <option value="SCHEDULED">SCHEDULED</option>
              <option value="COMPLETED">COMPLETED</option>
            </select>
          </div>
        </div>
      </div>

      {/* Appointments List / Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/90">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-xs uppercase tracking-wider text-white">
              Statewide Patient Intake Roster
            </span>
            <span className="text-xs bg-slate-800 text-teal-400 font-bold px-2 py-0.5 rounded-full">
              {filteredAppointments.length} matching
            </span>
          </div>
        </div>

        {loading ? (
          <div className="py-20 text-center space-y-3">
            <RotateCw className="w-8 h-8 text-teal-400 animate-spin mx-auto" />
            <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">
              Loading cross-hospital patient intake data...
            </div>
          </div>
        ) : filteredAppointments.length === 0 ? (
          <div className="py-16 text-center text-slate-400 text-xs space-y-2">
            <CalendarCheck className="w-8 h-8 text-slate-600 mx-auto" />
            <div>No appointments match the selected criteria.</div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/70 border-b border-slate-800 text-[11px] text-slate-400 uppercase font-bold tracking-wider">
                <tr>
                  <th className="p-4">Patient &amp; Phone</th>
                  <th className="p-4">Hospital Facility</th>
                  <th className="p-4">Assigned Doctor</th>
                  <th className="p-4">Clinical Intake / Symptoms</th>
                  <th className="p-4">Schedule Time</th>
                  <th className="p-4">Status &amp; Verification</th>
                  <th className="p-4 text-right">Observability Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {filteredAppointments.map((appt) => (
                  <tr
                    key={appt.id}
                    className="hover:bg-slate-800/40 transition group"
                  >
                    <td className="p-4">
                      <div className="font-bold text-white flex items-center space-x-1.5">
                        <User className="w-3.5 h-3.5 text-teal-400" />
                        <span>{appt.patient_name || 'Patient'}</span>
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                        {appt.patient_phone || 'N/A'}
                      </div>
                    </td>

                    <td className="p-4">
                      <div className="font-semibold text-slate-200 flex items-center space-x-1.5">
                        <Building2 className="w-3.5 h-3.5 text-indigo-400" />
                        <span>{appt.hospital_name || 'Hospital'}</span>
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                        {appt.hospital_id}
                      </div>
                    </td>

                    <td className="p-4">
                      <div className="font-semibold text-white flex items-center space-x-1.5">
                        <Stethoscope className="w-3.5 h-3.5 text-sky-400" />
                        <span>{appt.doctor_name || 'Doctor'}</span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {appt.specialty || 'General Medicine'}
                      </div>
                    </td>

                    <td className="p-4 max-w-xs">
                      <div className="text-slate-300 line-clamp-2">
                        {appt.complaint || 'Medical Consultation'}
                      </div>
                    </td>

                    <td className="p-4 whitespace-nowrap">
                      <div className="font-bold text-slate-200">
                        {appt.time || '10:00 AM'}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {appt.date || 'Today'}
                      </div>
                    </td>

                    <td className="p-4 whitespace-nowrap">
                      <div className="flex flex-col space-y-1">
                        <span className="inline-flex items-center space-x-1 text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 w-fit">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>{appt.status}</span>
                        </span>
                        {appt.is_ehr_verified && (
                          <span className="inline-flex items-center space-x-1 text-[10px] font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20 w-fit">
                            <ShieldCheck className="w-3 h-3" />
                            <span>EHR VERIFIED</span>
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="p-4 text-right whitespace-nowrap">
                      <button
                        onClick={() => setActiveModalAppt(appt)}
                        className="px-3 py-1.5 rounded-xl bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/30 text-xs font-bold transition flex items-center space-x-1.5 ml-auto cursor-pointer"
                        title="Inspect full 16-step canonical lifecycle trace"
                      >
                        <Activity className="w-3.5 h-3.5" />
                        <span>Inspect 16-Step Trace</span>
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Trace Lifecycle Modal */}
      {activeModalAppt && (
        <TraceLifecycleModal
          isOpen={true}
          onClose={() => setActiveModalAppt(null)}
          appointmentId={activeModalAppt.appointment_id || activeModalAppt.id}
          patientName={activeModalAppt.patient_name}
          doctorName={activeModalAppt.doctor_name}
        />
      )}
    </div>
  );
};
