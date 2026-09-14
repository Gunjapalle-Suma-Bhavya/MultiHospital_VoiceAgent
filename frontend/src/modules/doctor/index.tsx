import React, { useState, useEffect } from 'react';
import {
  Clock,
  Users,
  Calendar,
  Stethoscope,
  Ban,
  ClipboardList,
  User,
  CheckCircle2,
  CalendarCheck,
} from 'lucide-react';
import { DoctorProfile } from './DoctorProfile';
import { CalendarView } from './CalendarView';
import { AppointmentDetail } from './AppointmentDetail';
import { DoctorAvailability } from './DoctorAvailability';
import { DoctorBlockedSlots } from './DoctorBlockedSlots';
import { DoctorQuestionnaireBuilder } from './DoctorQuestionnaireBuilder';
import { EncounterModal } from './EncounterModal';
import { apiCall } from '../../api/client';
import { useAuth } from '../../hooks/useAuth';
import { usePlatformEvents } from '../../context/PlatformEventContext';

interface Props {
  initialTab?: string;
}

export const DoctorPortal: React.FC<Props> = ({ initialTab = 'profile' }) => {
  const { user } = useAuth();
  const { bookings } = usePlatformEvents();

  const [activeTab, setActiveTab] = useState<
    'profile' | 'calendar' | 'hours' | 'availability' | 'blocked_slots' | 'appointments' | 'questionnaires'
  >((initialTab as any) || 'profile');

  const [doctorId, setDoctorId] = useState(user?.doctor_id || 'DOC-SHARMA-01');
  const [doctorList, setDoctorList] = useState<any[]>([]);
  const [appointments, setAppointments] = useState<any[]>([]);
  const [selectedAppt, setSelectedAppt] = useState<any>(null);
  const [encounterAppt, setEncounterAppt] = useState<any>(null);
  const [homeMetrics, setHomeMetrics] = useState({
    todayCount: 0,
    upcomingCount: 0,
    totalCount: 0,
    pendingQuestionnaires: 0,
    completedQuestionnaires: 0,
  });

  useEffect(() => {
    const fetchDoctors = async () => {
      try {
        const res = await apiCall('/api/v1/doctors');
        let list: any[] = res.ok && Array.isArray(res.data) ? res.data : [];

        if (user?.doctor_id) {
          const found = list.find((d: any) => (d.doctor_id || d.id) === user.doctor_id);
          if (!found) {
            try {
              const myRes = await apiCall(`/api/v1/doctors/${user.doctor_id}`);
              if (myRes.ok && myRes.data) {
                list = [myRes.data, ...list];
              } else {
                list = [{
                  doctor_id: user.doctor_id,
                  id: user.doctor_id,
                  name: user.name,
                  specialty: user.specialty || 'General Medicine',
                  department: user.department || 'Clinical Practice',
                  hospital_name: user.hospital_name || 'Affiliated Hospital',
                  qualifications: user.qualifications || 'MBBS, MD',
                  experience_years: user.experience_years || 5,
                  bio: user.bio || '',
                  default_appointment_duration: 30,
                }, ...list];
              }
            } catch {
              list = [{
                doctor_id: user.doctor_id,
                id: user.doctor_id,
                name: user.name,
                specialty: user.specialty || 'General Medicine',
                department: user.department || 'Clinical Practice',
                hospital_name: user.hospital_name || 'Affiliated Hospital',
                qualifications: user.qualifications || 'MBBS, MD',
                experience_years: user.experience_years || 5,
                bio: user.bio || '',
                default_appointment_duration: 30,
              }, ...list];
            }
          }
          setDoctorId(user.doctor_id);
        } else if (list.length > 0) {
          setDoctorId(list[0].doctor_id || list[0].id || 'DOC-SHARMA-01');
        }

        setDoctorList(list);
      } catch (err) {
        console.error('Failed to load doctors catalog:', err);
      }
    };
    fetchDoctors();
  }, [user?.doctor_id]);

  useEffect(() => {
    if (
      initialTab &&
      [
        'profile',
        'calendar',
        'hours',
        'availability',
        'blocked_slots',
        'appointments',
        'questionnaires',
      ].includes(initialTab)
    ) {
      setActiveTab(initialTab as any);
    }
  }, [initialTab]);

  const loadDoctorData = async (docId: string) => {
    try {
      let list: any[] = [];
      // 1. Fetch full live appointments for this doctor
      const apptRes = await apiCall(`/api/v1/doctor-dashboard/${docId}/appointments`);
      if (apptRes.ok && apptRes.data) {
        if (Array.isArray(apptRes.data)) {
          list = apptRes.data;
        } else if (Array.isArray(apptRes.data.appointments)) {
          list = apptRes.data.appointments;
        }
      }

      // 2. Fetch live summary metrics and appointments from dynamic backend
      const homeRes = await apiCall(`/api/v1/doctor-dashboard/${docId}/home`);
      if (homeRes.ok && homeRes.data) {
        if (list.length === 0) {
          list = homeRes.data.all_appointments || homeRes.data.upcoming_appointments || homeRes.data.today_appointments || [];
        }
        const summary = homeRes.data.summary_counts || {};
        setHomeMetrics({
          todayCount: summary.today_appointments_count ?? homeRes.data.today_appointments?.length ?? 0,
          upcomingCount: summary.upcoming_appointments_count ?? homeRes.data.upcoming_appointments?.length ?? 0,
          totalCount: (summary.total_appointments_count ?? homeRes.data.all_appointments?.length ?? list.length) + bookings.length,
          pendingQuestionnaires: summary.pending_questionnaires_count ?? homeRes.data.pending_questionnaires?.length ?? 0,
          completedQuestionnaires: summary.completed_questionnaires_count ?? homeRes.data.recently_completed_questionnaires?.length ?? 0,
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
    const interval = setInterval(() => {
      loadDoctorData(doctorId);
    }, 4000);
    return () => clearInterval(interval);
  }, [doctorId, activeTab, bookings.length]);

  const handleTabChange = (tab: typeof activeTab) => {
    setActiveTab(tab);
    window.location.hash = `/doctor/${tab}`;
    loadDoctorData(doctorId);
  };

  const currentDoctor =
    doctorList.find((d) => (d.doctor_id || d.id) === doctorId) ||
    (user?.doctor_id === doctorId
      ? {
          doctor_id: user.doctor_id,
          id: user.doctor_id,
          name: user.name,
          specialty: (user as any).specialty || 'Physician',
          department: (user as any).department || 'Clinical Practice',
          hospital_name: user.hospital_name || 'Affiliated Hospital',
          qualifications: (user as any).qualifications || 'MBBS, MD',
          experience_years: (user as any).experience_years || 5,
          default_appointment_duration: 30,
        }
      : undefined);

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
              Doctor Clinical Workstation
            </div>
            <h2 className="text-xl font-extrabold text-white">
              {currentDoctor ? `${currentDoctor.name} — ${currentDoctor.specialty || 'Physician'}` : (doctorId === 'DOC-RAO-02' ? 'Dr. Rao — Cardiology' : 'Dr. Sharma — Orthopedic Surgery')}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              {currentDoctor?.hospital_name || 'City Memorial Hospital'} &bull; Consultation: {currentDoctor?.default_appointment_duration || 30} Mins &bull; ID #{doctorId}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400 font-medium">Doctor Account:</span>
          <select
            value={doctorId}
            onChange={(e) => setDoctorId(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 font-medium focus:ring-2 focus:ring-sky-500 cursor-pointer"
          >
            {doctorList.map((doc) => (
              <option key={doc.doctor_id || doc.id} value={doc.doctor_id || doc.id}>
                {doc.name} ({doc.specialty || 'Physician'})
              </option>
            ))}
            {doctorList.length === 0 && (
              <>
                <option value="DOC-SHARMA-01">Dr. Sharma (Orthopedic Surgery)</option>
                <option value="DOC-RAO-02">Dr. Rao (Cardiology)</option>
              </>
            )}
          </select>
        </div>
      </div>

      {/* Dynamic Statistical Telemetry Cards Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 shadow-sm">
          <div className="text-[10px] uppercase font-bold text-slate-400 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-sky-400" />
            <span>Today's Appts</span>
          </div>
          <div className="text-xl font-extrabold text-white mt-1">
            {homeMetrics.todayCount}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">Scheduled for today</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 shadow-sm">
          <div className="text-[10px] uppercase font-bold text-slate-400 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-indigo-400" />
            <span>Upcoming Appts</span>
          </div>
          <div className="text-xl font-extrabold text-indigo-400 mt-1">
            {homeMetrics.upcomingCount}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">Next 7 days</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 shadow-sm">
          <div className="text-[10px] uppercase font-bold text-slate-400 flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-emerald-400" />
            <span>Total Schedule</span>
          </div>
          <div className="text-xl font-extrabold text-emerald-400 mt-1">
            {homeMetrics.totalCount}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">EHR synchronized</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 shadow-sm">
          <div className="text-[10px] uppercase font-bold text-slate-400 flex items-center gap-1.5">
            <ClipboardList className="w-3.5 h-3.5 text-amber-400" />
            <span>Pending Questions</span>
          </div>
          <div className="text-xl font-extrabold text-amber-400 mt-1">
            {homeMetrics.pendingQuestionnaires}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">Patient voice intake</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 shadow-sm col-span-2 sm:col-span-1">
          <div className="text-[10px] uppercase font-bold text-slate-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
            <span>Completed Intakes</span>
          </div>
          <div className="text-xl font-extrabold text-teal-400 mt-1">
            {homeMetrics.completedQuestionnaires}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">Ready for review</div>
        </div>
      </div>

      {/* Clean Sub-Page Navigation Tabs */}
      <div className="flex border-b border-slate-800 bg-slate-900/60 p-1 rounded-2xl gap-1.5 text-xs overflow-x-auto">
        <button
          onClick={() => handleTabChange('profile')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'profile'
              ? 'bg-sky-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <User className="w-4 h-4" />
          <span>Doctor Profile</span>
        </button>

        <button
          onClick={() => handleTabChange('calendar')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'calendar'
              ? 'bg-sky-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Calendar className="w-4 h-4" />
          <span>Calendar</span>
        </button>

        <button
          onClick={() => handleTabChange('hours')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'hours'
              ? 'bg-sky-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Clock className="w-4 h-4" />
          <span>Working Hours</span>
        </button>

        <button
          onClick={() => handleTabChange('availability')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'availability'
              ? 'bg-sky-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <CalendarCheck className="w-4 h-4" />
          <span>Availability Rules</span>
        </button>

        <button
          onClick={() => handleTabChange('blocked_slots')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'blocked_slots'
              ? 'bg-sky-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Ban className="w-4 h-4" />
          <span>Blocked Slots &amp; Leaves</span>
        </button>

        <button
          onClick={() => handleTabChange('appointments')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'appointments'
              ? 'bg-sky-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Appointment View ({homeMetrics.totalCount})</span>
        </button>

        <button
          onClick={() => handleTabChange('questionnaires')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-bold transition whitespace-nowrap ${
            activeTab === 'questionnaires'
              ? 'bg-sky-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <ClipboardList className="w-4 h-4" />
          <span>Questionnaire Creation</span>
        </button>
      </div>

      {/* Uncluttered Dedicated Sub-Page Content */}
      <div>
        {activeTab === 'profile' && <DoctorProfile doctorId={doctorId} />}

        {activeTab === 'calendar' && (
          <CalendarView
            appointments={appointments}
            selectedAppointmentId={selectedAppt?.id || selectedAppt?.appointment_id}
            onSelectAppointment={(a) => {
              setSelectedAppt(a);
              handleTabChange('appointments');
            }}
            onOpenEncounter={(a) => setEncounterAppt(a)}
            doctorId={doctorId}
          />
        )}

        {activeTab === 'hours' && <DoctorAvailability doctorId={doctorId} />}

        {activeTab === 'availability' && <DoctorAvailability doctorId={doctorId} />}

        {activeTab === 'blocked_slots' && <DoctorBlockedSlots doctorId={doctorId} />}

        {activeTab === 'appointments' && (
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

        {activeTab === 'questionnaires' && <DoctorQuestionnaireBuilder doctorId={doctorId} />}
      </div>

      {/* Active Clinical Encounter & E-Prescription Modal */}
      {encounterAppt && (
        <EncounterModal
          booking={{
            id: encounterAppt.id || 'APT-1024',
            doctor_id: doctorId,
            doctor_name: currentDoctor?.name || (doctorId === 'DOC-RAO-02' ? 'Dr. Rao' : 'Dr. Sharma'),
            patient_name: encounterAppt.patient_name || 'Patient',
            patient_phone: encounterAppt.patient_phone || 'N/A',
            scheduled_time: encounterAppt.time || encounterAppt.scheduled_time || '10:00 AM',
            slot_time: encounterAppt.time || '10:00 AM',
            specialty: currentDoctor?.specialty || (doctorId === 'DOC-RAO-02' ? 'Cardiology' : 'General Medicine'),
            status: encounterAppt.ehr_status || 'CONFIRMED',
            is_ehr_verified: true,
          }}
          onClose={() => setEncounterAppt(null)}
        />
      )}
    </div>
  );
};
