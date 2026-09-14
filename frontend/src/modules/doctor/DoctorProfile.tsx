import React, { useState, useEffect } from 'react';
import {
  Stethoscope,
  Building2,
  Clock,
  DollarSign,
  Award,
  Save,
  CheckCircle2,
  AlertCircle,
  FileText,
  User,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { apiCall } from '../../api/client';

interface Props {
  doctorId?: string;
}

export const DoctorProfile: React.FC<Props> = ({ doctorId = 'DOC-SHARMA-01' }) => {
  const { user } = useAuth();

  const isRao = doctorId === 'DOC-RAO-02';

  const [name, setName] = useState(isRao ? 'Dr. Rajesh Rao, MD' : 'Dr. Ananya Sharma, MD, FACS');
  const [specialty, setSpecialty] = useState(isRao ? 'Cardiology' : 'Orthopedic Surgery');
  const [licenseNumber, setLicenseNumber] = useState(isRao ? 'MD-LIC-448291' : 'MD-LIC-889102');
  const [npiNumber, setNpiNumber] = useState(isRao ? 'NPI-199482012' : 'NPI-198234812');
  const [department, setDepartment] = useState('Outpatient Department');
  const [experienceYears, setExperienceYears] = useState('8');
  const [hospitalName, setHospitalName] = useState('City Memorial Hospital');
  const [consultDuration, setConsultDuration] = useState('30');
  const [consultFee, setConsultFee] = useState(isRao ? '180' : '150');
  const [roomNumber, setRoomNumber] = useState(isRao ? 'Pavilion B, Room 304' : 'Ortho Wing, Suite 410');
  const [bio, setBio] = useState(
    isRao
      ? 'Board-certified clinical cardiologist with 14 years of experience in preventative cardiology, cardiac rehabilitation, and non-invasive electrophysiology diagnostics.'
      : 'Board-certified orthopedic surgeon specializing in arthroscopic shoulder stabilization, rotator cuff repair, and sports medicine injury recovery.'
  );
  const [clinicalInstructions, setClinicalInstructions] = useState(
    isRao
      ? 'Please bring recent lipid panels, ECG recordings, and list of current blood pressure medications.'
      : 'Please wear loose clothing and bring prior MRI or X-ray imaging CDs on disk if taken outside City Memorial Hospital.'
  );

  const [isSaving, setIsSaving] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await apiCall(`/api/v1/doctors/${doctorId}`);
        if (res.ok && res.data) {
          setName(res.data.name || '');
          setSpecialty(res.data.specialty || '');
          if (res.data.department) setDepartment(res.data.department);
          if (res.data.experience_years) setExperienceYears(String(res.data.experience_years));
          setLicenseNumber(res.data.qualifications || res.data.external_provider_id || `LIC-${doctorId}`);
          setNpiNumber(res.data.external_provider_id || `NPI-${doctorId}`);
          setHospitalName(res.data.hospital_name || 'City Memorial Hospital');
          setConsultDuration(String(res.data.default_appointment_duration || '30'));
          if (res.data.bio) setBio(res.data.bio);
          if (res.data.special_instructions) setClinicalInstructions(res.data.special_instructions);
          return;
        }
      } catch (err) {}

      const isDoctorRao = doctorId === 'DOC-RAO-02';
      setName(isDoctorRao ? 'Dr. Rajesh Rao, MD' : 'Dr. Ananya Sharma, MD, FACS');
      setSpecialty(isDoctorRao ? 'Cardiology' : 'Orthopedic Surgery');
      setLicenseNumber(isDoctorRao ? 'MD-LIC-448291' : 'MD-LIC-889102');
      setNpiNumber(isDoctorRao ? 'NPI-199482012' : 'NPI-198234812');
      setConsultFee(isDoctorRao ? '180' : '150');
      setRoomNumber(isDoctorRao ? 'Pavilion B, Room 304' : 'Ortho Wing, Suite 410');
      setBio(
        isDoctorRao
          ? 'Board-certified clinical cardiologist with 14 years of experience in preventative cardiology, cardiac rehabilitation, and non-invasive electrophysiology diagnostics.'
          : 'Board-certified orthopedic surgeon specializing in arthroscopic shoulder stabilization, rotator cuff repair, and sports medicine injury recovery.'
      );
      setClinicalInstructions(
        isDoctorRao
          ? 'Please bring recent lipid panels, ECG recordings, and list of current blood pressure medications.'
          : 'Please wear loose clothing and bring prior MRI or X-ray imaging CDs on disk if taken outside City Memorial Hospital.'
      );
    };
    fetchProfile();
  }, [doctorId]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setFeedback(null);

    try {
      await apiCall(`/api/v1/doctors/${doctorId}/profile`, {
        method: 'PUT',
        body: JSON.stringify({
          name,
          specialty,
          department,
          qualifications: licenseNumber,
          experience_years: parseInt(experienceYears) || 5,
          default_appointment_duration: parseInt(consultDuration) || 30,
          bio,
          special_instructions: clinicalInstructions,
        }),
      });
    } catch {}

    localStorage.setItem(
      `doctor_profile_${doctorId}`,
      JSON.stringify({
        name,
        specialty,
        department,
        experienceYears,
        licenseNumber,
        npiNumber,
        hospitalName,
        consultDuration,
        consultFee,
        roomNumber,
        bio,
        clinicalInstructions,
      })
    );

    setIsSaving(false);
    setFeedback('Clinician credentials and consultation parameters updated successfully.');
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-md">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 pb-6 border-b border-slate-800">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center space-x-2">
              <Stethoscope className="w-5 h-5 text-sky-400" />
              <span>Doctor Practice Profile &amp; Credentials</span>
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Configure your clinical identity, consultation duration, room location, and preparation instructions seen by patients.
            </p>
          </div>
          <span className="text-xs bg-sky-500/10 text-sky-400 border border-sky-500/30 px-3 py-1 rounded-full font-bold flex items-center space-x-1.5">
            <Award className="w-3.5 h-3.5" />
            <span>Active Board Certification</span>
          </span>
        </div>

        {feedback && (
          <div className="bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 p-3.5 rounded-xl text-xs mb-6 flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{feedback}</span>
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs text-slate-400 block mb-1 font-medium">Physician Full Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1 font-medium">Primary Clinical Specialty</label>
              <input
                type="text"
                required
                value={specialty}
                onChange={(e) => setSpecialty(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1 font-medium">Clinical Department</label>
              <input
                type="text"
                required
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1 font-medium">Years of Clinical Practice</label>
              <input
                type="number"
                min={1}
                max={60}
                required
                value={experienceYears}
                onChange={(e) => setExperienceYears(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1 font-medium">Medical License / Registration</label>
              <input
                type="text"
                required
                value={licenseNumber}
                onChange={(e) => setLicenseNumber(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-sky-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1 font-medium">National Provider Identifier (NPI)</label>
              <input
                type="text"
                required
                value={npiNumber}
                onChange={(e) => setNpiNumber(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-sky-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1 font-medium">Affiliated Hospital / Campus</label>
              <input
                type="text"
                value={hospitalName}
                onChange={(e) => setHospitalName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1 font-medium">Exam Room / Office Location</label>
              <input
                type="text"
                value={roomNumber}
                onChange={(e) => setRoomNumber(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1 font-medium">Standard Slot Duration</label>
              <select
                value={consultDuration}
                onChange={(e) => setConsultDuration(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500 cursor-pointer"
              >
                <option value="15">15 Minutes (Express Follow-up)</option>
                <option value="30">30 Minutes (Standard Consultation)</option>
                <option value="45">45 Minutes (Comprehensive Assessment)</option>
                <option value="60">60 Minutes (New Patient In-Depth)</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1 font-medium">Base Consultation Fee (USD)</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500 text-xs font-bold">$</span>
                <input
                  type="number"
                  value={consultFee}
                  onChange={(e) => setConsultFee(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-7 pr-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1 font-medium">Professional Biography &amp; Background</label>
            <textarea
              rows={3}
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-sky-500"
            />
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1 font-medium">Patient Pre-Visit Preparation &amp; Intake Instructions</label>
            <textarea
              rows={2}
              value={clinicalInstructions}
              onChange={(e) => setClinicalInstructions(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-sky-500"
            />
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-800">
            <button
              type="submit"
              disabled={isSaving}
              className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-bold shadow-lg transition flex items-center space-x-2 cursor-pointer disabled:opacity-50"
            >
              {isSaving ? (
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              <span>Save Doctor Profile</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
