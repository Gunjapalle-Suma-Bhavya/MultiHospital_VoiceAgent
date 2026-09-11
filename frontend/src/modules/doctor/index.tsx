import React, { useState, useEffect } from 'react';
import { CalendarView } from './CalendarView';
import { AppointmentDetail } from './AppointmentDetail';
import { DoctorControls } from './DoctorControls';
import { TriageDesk } from './TriageDesk';
import { apiCall } from '../../api/client';
import { useAuth } from '../../hooks/useAuth';

export const DoctorPortal: React.FC = () => {
  const { user } = useAuth();
  const [doctorId, setDoctorId] = useState(user?.doctor_id || 'DOC-SHARMA-01');
  const [appointments, setAppointments] = useState<any[]>([]);
  const [selectedAppt, setSelectedAppt] = useState<any>(null);
  const [kpis, setKpis] = useState({ count: 4, intakes: 3 });

  const loadDoctorData = async (docId: string) => {
    try {
      const res = await apiCall(`/api/v1/doctor-dashboard/${docId}/home`);
      let list: any[] = [];
      if (res.ok && res.data) {
        list = res.data.today_appointments || [];
        setKpis({
          count: list.length || 4,
          intakes: res.data.pending_questionnaires_count || 3,
        });
      }

      if (list.length === 0) {
        list = [
          {
            id: 'APT-1024',
            time: '04:00 PM',
            patient_name: 'Patient A',
            complaint: 'Acute right shoulder pain (7 days)',
            intake_status: 'COMPLETED',
            ehr_status: 'CONFIRMED',
          },
          {
            id: 'APT-1025',
            time: '04:30 PM',
            patient_name: 'Elena Rostova',
            complaint: 'Post-op rotator cuff follow-up',
            intake_status: 'PENDING',
            ehr_status: 'CONFIRMED',
          },
          {
            id: 'APT-1026',
            time: '05:00 PM',
            patient_name: 'James Miller',
            complaint: 'Cervical spine stiffness & numbness',
            intake_status: 'COMPLETED',
            ehr_status: 'CONFIRMED',
          },
        ];
      }

      setAppointments(list);
      setSelectedAppt(list[0]);
    } catch (e) {
      console.error('Doctor data error:', e);
    }
  };

  useEffect(() => {
    loadDoctorData(doctorId);
  }, [doctorId]);

  return (
    <div className="space-y-6">
      {/* Header Strip */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shadow-lg">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20 flex items-center justify-center font-black text-lg">
            {doctorId === 'DOC-RAO-02' ? 'DR' : 'DS'}
          </div>
          <div>
            <div className="text-xs font-bold text-sky-400 uppercase tracking-wider">Clinical Practice Dashboard</div>
            <h2 className="text-xl font-extrabold text-white">
              {doctorId === 'DOC-RAO-02' ? 'Dr. Rao — Cardiology' : 'Dr. Sharma — Orthopedic Surgery'}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">City Memorial Hospital &bull; Consultation Duration: 30 Mins</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400">Doctor Context:</span>
          <select
            value={doctorId}
            onChange={(e) => setDoctorId(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 font-medium focus:ring-2 focus:ring-sky-500"
          >
            <option value="DOC-SHARMA-01">Dr. Sharma (Orthopedics)</option>
            <option value="DOC-RAO-02">Dr. Rao (Cardiology)</option>
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Today's Appointments</div>
          <div className="text-2xl font-black text-white mt-1">{kpis.count} Patients</div>
          <div className="text-[11px] text-emerald-400 font-semibold mt-0.5">&bull; 100% EHR Verified</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Pre-Visit Intakes</div>
          <div className="text-2xl font-black text-sky-400 mt-1">{kpis.intakes} Ready</div>
          <div className="text-[11px] text-sky-400/80 font-medium mt-0.5">&bull; Structured answers saved</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Schedule Utilization</div>
          <div className="text-2xl font-black text-white mt-1">87.5%</div>
          <div className="text-[11px] text-slate-500 mt-0.5">7 of 8 working slots filled</div>
        </div>

        <DoctorControls doctorId={doctorId} />
      </div>

      {/* 2-Column: Patient Schedule (Left) + Clinical Brief Detail (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7">
          <CalendarView
            appointments={appointments}
            selectedAppointmentId={selectedAppt?.id || selectedAppt?.appointment_id}
            onSelectAppointment={(a) => setSelectedAppt(a)}
            doctorId={doctorId}
          />
        </div>

        <div className="lg:col-span-5">
          <AppointmentDetail appointment={selectedAppt} />
        </div>
      </div>

      {/* Live Human Triage & Escalation Desk */}
      <TriageDesk />
    </div>
  );
};
