import React, { useState, useEffect } from 'react';
import {
  Clock,
  Users,
  ShieldAlert,
  Calendar,
  Stethoscope,
  CheckCircle2,
} from 'lucide-react';
import { CalendarView } from './CalendarView';
import { AppointmentDetail } from './AppointmentDetail';
import { TriageDesk } from './TriageDesk';
import { DoctorAvailability } from './DoctorAvailability';
import { EncounterModal } from './EncounterModal';
import { apiCall } from '../../api/client';
import { useAuth } from '../../hooks/useAuth';
import { usePlatformEvents } from '../../context/PlatformEventContext';

interface Props {
  initialTab?: string;
}

export const DoctorPortal: React.FC<Props> = ({ initialTab = 'schedule' }) => {
  const { user } = useAuth();
  const { bookings } = usePlatformEvents();

  const [activeTab, setActiveTab] = useState<'schedule' | 'queue' | 'triage' | 'availability'>(
    (initialTab as any) || 'schedule'
  );
  const [doctorId, setDoctorId] = useState(user?.doctor_id || 'DOC-SHARMA-01');
  const [appointments, setAppointments] = useState<any[]>([]);
  const [selectedAppt, setSelectedAppt] = useState<any>(null);
  const [encounterAppt, setEncounterAppt] = useState<any>(null);
  const [homeMetrics, setHomeMetrics] = useState({
    appointmentsCount: 0,
    pendingQuestionnaires: 0,
    upcomingCount: 0,
  });

  useEffect(() => {
    if (initialTab && ['schedule', 'queue', 'triage', 'availability'].includes(initialTab)) {
      setActiveTab(initialTab as any);
    }
  }, [initialTab]);

  const loadDoctorData = async (docId: string) => {
    try {
      const res = await apiCall(`/api/v1/doctor-dashboard/${docId}/home`);
      let list: any[] = [];
      if (res.ok && res.data) {
        list = res.data.today_appointments || [];
        setHomeMetrics({
          appointmentsCount: list.length + bookings.length,
          pendingQuestionnaires: res.data.pending_questionnaires_count || 0,
          upcomingCount: res.data.upcoming_appointments_count || 0,
        });
      }
      setAppointments(list);
      if (list.length > 0) {
        setSelectedAppt(list[0]);
      }
    } catch (e) {
      console.error('Doctor data error:', e);
    }
  };

  useEffect(() => {
    loadDoctorData(doctorId);
  }, [doctorId, bookings.length]);

  const handleTabChange = (tab: typeof activeTab) => {
    setActiveTab(tab);
    window.location.hash = `/doctor/${tab}`;
  };

  return (
    <div className="space-y-6">
      {/* Clinician Header Strip */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shadow-lg">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20 flex items-center justify-center font-black text-lg">
            <Stethoscope className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-bold text-sky-400 uppercase tracking-wider">
              Clinical Practice Workstation
            </div>
            <h2 className="text-xl font-extrabold text-white">
              {doctorId === 'DOC-RAO-02' ? 'Dr. Rao — Cardiology' : 'Dr. Sharma — Orthopedic Surgery'}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              City Memorial Hospital &bull; Consultation: 30 Mins &bull; NPI #198234812
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400 font-medium">Doctor Account:</span>
          <select
            value={doctorId}
            onChange={(e) => setDoctorId(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 font-medium focus:ring-2 focus:ring-sky-500"
          >
            <option value="DOC-SHARMA-01">Dr. Sharma (Orthopedic Surgery)</option>
            <option value="DOC-RAO-02">Dr. Rao (Cardiology)</option>
          </select>
        </div>
      </div>

      {/* Clean Sub-Page Navigation Tabs */}
      <div className="flex border-b border-slate-800 bg-slate-900/60 p-1 rounded-2xl gap-1.5 text-xs overflow-x-auto">
        <button
          onClick={() => handleTabChange('schedule')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'schedule'
              ? 'bg-sky-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Calendar className="w-4 h-4" />
          <span>Today's Schedule &amp; Slots</span>
        </button>

        <button
          onClick={() => handleTabChange('queue')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'queue'
              ? 'bg-sky-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Patient Consultations ({homeMetrics.appointmentsCount})</span>
        </button>

        <button
          onClick={() => handleTabChange('triage')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'triage'
              ? 'bg-sky-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          <span>Emergency Triage Desk</span>
        </button>

        <button
          onClick={() => handleTabChange('availability')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'availability'
              ? 'bg-sky-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Clock className="w-4 h-4" />
          <span>Working Hours &amp; Leaves</span>
        </button>
      </div>

      {/* Uncluttered Dedicated Sub-Page Content */}
      <div>
        {activeTab === 'schedule' && (
          <CalendarView
            appointments={appointments}
            selectedAppointmentId={selectedAppt?.id || selectedAppt?.appointment_id}
            onSelectAppointment={(a) => {
              setSelectedAppt(a);
              handleTabChange('queue');
            }}
            onOpenEncounter={(a) => setEncounterAppt(a)}
            doctorId={doctorId}
          />
        )}

        {activeTab === 'queue' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-7">
              <CalendarView
                appointments={appointments}
                selectedAppointmentId={selectedAppt?.id || selectedAppt?.appointment_id}
                onSelectAppointment={(a) => setSelectedAppt(a)}
                onOpenEncounter={(a) => setEncounterAppt(a)}
                doctorId={doctorId}
              />
            </div>
            <div className="lg:col-span-5">
              <AppointmentDetail
                appointment={selectedAppt}
                onOpenEncounter={() => setEncounterAppt(selectedAppt)}
              />
            </div>
          </div>
        )}

        {activeTab === 'triage' && <TriageDesk />}

        {activeTab === 'availability' && <DoctorAvailability doctorId={doctorId} />}
      </div>

      {/* Active Clinical Encounter & E-Prescription Modal */}
      {encounterAppt && (
        <EncounterModal
          booking={{
            id: encounterAppt.id || 'APT-1024',
            doctor_id: doctorId,
            doctor_name: doctorId === 'DOC-RAO-02' ? 'Dr. Rao' : 'Dr. Sharma',
            patient_name: encounterAppt.patient_name || 'Marcus Aurelius',
            patient_phone: encounterAppt.patient_phone || '+1-555-SHOULDER',
            scheduled_time: encounterAppt.time || encounterAppt.scheduled_time || '10:00 AM',
            slot_time: encounterAppt.time || '10:00 AM',
            specialty: doctorId === 'DOC-RAO-02' ? 'Cardiology' : 'Orthopedic Surgery',
            status: encounterAppt.ehr_status || 'CONFIRMED',
            is_ehr_verified: true,
          }}
          onClose={() => setEncounterAppt(null)}
        />
      )}
    </div>
  );
};
