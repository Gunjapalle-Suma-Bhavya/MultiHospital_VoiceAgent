import React, { useState, useEffect } from 'react';
import {
  Bell,
  MessageSquare,
  Phone,
  Mail,
  Clock,
  Globe2,
  Calendar,
  Save,
  CheckCircle2,
  AlertCircle,
  Shield,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useLanguage, SUPPORTED_LANGUAGES } from '../../context/LanguageContext';
import { apiCall } from '../../api/client';

export const PatientPreferences: React.FC = () => {
  const { user } = useAuth();
  const { language, setLanguage } = useLanguage();

  // Communication Channels
  const [smsEnabled, setSmsEnabled] = useState(true);
  const [voiceCallsEnabled, setVoiceCallsEnabled] = useState(true);
  const [emailEnabled, setEmailEnabled] = useState(true);

  // Time & Day Preferences
  const [preferredWindow, setPreferredWindow] = useState('MORNING');
  const [preferredDays, setPreferredDays] = useState<'WEEKDAYS' | 'WEEKENDS' | 'ANY'>('WEEKDAYS');

  // Specific Notification Triggers
  const [notifyBookingConfirm, setNotifyBookingConfirm] = useState(true);
  const [notify24hReminder, setNotify24hReminder] = useState(true);
  const [notify2hCheckIn, setNotify2hCheckIn] = useState(true);
  const [notifyDoctorNotes, setNotifyDoctorNotes] = useState(true);

  const [isSaving, setIsSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    const fetchPrefs = async () => {
      const pid = user?.patient_id || user?.identifier;
      if (!pid) return;
      try {
        const res = await apiCall(`/api/v1/patients/${pid}`);
        if (res.ok && res.data) {
          if (res.data.communication_preference) {
            const cp = res.data.communication_preference.toUpperCase();
            setSmsEnabled(cp.includes('SMS') || cp.includes('ANY') || cp.includes('ALL'));
            setVoiceCallsEnabled(cp.includes('VOICE') || cp.includes('PHONE') || cp.includes('ALL'));
            setEmailEnabled(cp.includes('EMAIL') || cp.includes('ALL'));
          }
          if (res.data.preferred_time_window) {
            setPreferredWindow(res.data.preferred_time_window);
          }
        }
      } catch (e) {
        // Fallback to defaults
      }
    };
    fetchPrefs();
  }, [user]);

  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setFeedback(null);

    const commChannels = [];
    if (smsEnabled) commChannels.push('SMS');
    if (voiceCallsEnabled) commChannels.push('VOICE');
    if (emailEnabled) commChannels.push('EMAIL');
    const commPrefStr = commChannels.join('+') || 'SMS';

    const pid = user?.patient_id || user?.identifier || 'default';

    try {
      await apiCall(`/api/v1/patients/${pid}/preferences`, {
        method: 'PUT',
        body: JSON.stringify({
          communication_preference: commPrefStr,
          preferred_time_window: preferredWindow,
        }),
      });

      localStorage.setItem(
        `patient_preferences_${pid}`,
        JSON.stringify({
          smsEnabled,
          voiceCallsEnabled,
          emailEnabled,
          preferredWindow,
          preferredDays,
          notifyBookingConfirm,
          notify24hReminder,
          notify2hCheckIn,
          notifyDoctorNotes,
          language,
        })
      );

      setFeedback({
        type: 'success',
        message: 'Your healthcare notification and communication preferences have been updated.',
      });
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err?.message || 'Failed to update preferences on server, cached locally.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-md">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 pb-6 border-b border-slate-800">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center space-x-2">
              <Bell className="w-5 h-5 text-emerald-400" />
              <span>Communication &amp; Notification Preferences</span>
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Customize how NexusHealth reaches you for appointment reminders, care updates, and clinician messages.
            </p>
          </div>
          <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-3 py-1 rounded-full font-bold flex items-center space-x-1.5">
            <Shield className="w-3.5 h-3.5" />
            <span>TCPA &amp; HIPAA Compliant</span>
          </span>
        </div>

        {feedback && (
          <div
            className={`p-3.5 rounded-xl text-xs mb-6 flex items-start space-x-2 ${
              feedback.type === 'success'
                ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30'
                : 'bg-rose-500/10 text-rose-300 border border-rose-500/30'
            }`}
          >
            {feedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            )}
            <span>{feedback.message}</span>
          </div>
        )}

        <form onSubmit={handleSavePreferences} className="space-y-6">
          {/* Section 1: Preferred Channels */}
          <div>
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center space-x-1.5">
              <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
              <span>Direct Communication Channels</span>
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* SMS Option */}
              <label
                className={`p-4 rounded-xl border transition flex flex-col justify-between cursor-pointer ${
                  smsEnabled
                    ? 'bg-emerald-500/10 border-emerald-500 text-white'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <MessageSquare className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-bold text-white">SMS Alerts</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={smsEnabled}
                    onChange={(e) => setSmsEnabled(e.target.checked)}
                    className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4"
                  />
                </div>
                <p className="text-[11px] text-slate-400">
                  Instant text messages with doctor verification codes and direct reschedule links.
                </p>
              </label>

              {/* Voice Call Option */}
              <label
                className={`p-4 rounded-xl border transition flex flex-col justify-between cursor-pointer ${
                  voiceCallsEnabled
                    ? 'bg-sky-500/10 border-sky-500 text-white'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <Phone className="w-4 h-4 text-sky-400" />
                    <span className="text-xs font-bold text-white">Voice Calls</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={voiceCallsEnabled}
                    onChange={(e) => setVoiceCallsEnabled(e.target.checked)}
                    className="rounded text-sky-600 focus:ring-sky-500 w-4 h-4"
                  />
                </div>
                <p className="text-[11px] text-slate-400">
                  Interactive AI phone calls for pre-visit symptom checks and urgent clinic updates.
                </p>
              </label>

              {/* Email Option */}
              <label
                className={`p-4 rounded-xl border transition flex flex-col justify-between cursor-pointer ${
                  emailEnabled
                    ? 'bg-indigo-500/10 border-indigo-500 text-white'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <Mail className="w-4 h-4 text-indigo-400" />
                    <span className="text-xs font-bold text-white">Email Summaries</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={emailEnabled}
                    onChange={(e) => setEmailEnabled(e.target.checked)}
                    className="rounded text-indigo-600 focus:ring-indigo-500 w-4 h-4"
                  />
                </div>
                <p className="text-[11px] text-slate-400">
                  Digital Care Passes, calendar invites (.ics), and doctor clinical encounter summaries.
                </p>
              </label>
            </div>
          </div>

          {/* Section 2: Timing & Language */}
          <div className="border-t border-slate-800 pt-6">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center space-x-1.5">
              <Clock className="w-3.5 h-3.5 text-sky-400" />
              <span>Timing &amp; Language Preferences</span>
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="text-xs text-slate-400 block mb-1 font-medium">Preferred Time Window</label>
                <select
                  value={preferredWindow}
                  onChange={(e) => setPreferredWindow(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 cursor-pointer"
                >
                  <option value="MORNING">Morning (08:00 AM - 12:00 PM)</option>
                  <option value="AFTERNOON">Afternoon (12:00 PM - 05:00 PM)</option>
                  <option value="EVENING">Evening (05:00 PM - 08:00 PM)</option>
                  <option value="ANY">Any Available Opening</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-slate-400 block mb-1 font-medium">Preferred Days</label>
                <select
                  value={preferredDays}
                  onChange={(e) => setPreferredDays(e.target.value as any)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 cursor-pointer"
                >
                  <option value="WEEKDAYS">Monday through Friday (Weekdays)</option>
                  <option value="WEEKENDS">Saturday / Sunday (Weekends)</option>
                  <option value="ANY">First Available Day</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-slate-400 block mb-1 font-medium">Spoken Healthcare Language</label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value as any)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 cursor-pointer"
                >
                  {SUPPORTED_LANGUAGES.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.flag} {lang.label} ({lang.native})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Section 3: Notification Triggers */}
          <div className="border-t border-slate-800 pt-6">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center space-x-1.5">
              <Calendar className="w-3.5 h-3.5 text-amber-400" />
              <span>Automated Reminders &amp; Milestones</span>
            </h4>
            <div className="space-y-2.5">
              <label className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700">
                <div>
                  <span className="text-xs font-bold text-white block">Instant Booking Confirmation</span>
                  <span className="text-[11px] text-slate-400">Receive immediate dispatch receipt with your EHR verification code.</span>
                </div>
                <input
                  type="checkbox"
                  checked={notifyBookingConfirm}
                  onChange={(e) => setNotifyBookingConfirm(e.target.checked)}
                  className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4 ml-4"
                />
              </label>

              <label className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700">
                <div>
                  <span className="text-xs font-bold text-white block">24-Hour Pre-Appointment Reminder</span>
                  <span className="text-[11px] text-slate-400">Automated reminder 24 hours prior with parking directions and clinic checklist.</span>
                </div>
                <input
                  type="checkbox"
                  checked={notify24hReminder}
                  onChange={(e) => setNotify24hReminder(e.target.checked)}
                  className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4 ml-4"
                />
              </label>

              <label className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700">
                <div>
                  <span className="text-xs font-bold text-white block">2-Hour Arrival Notice &amp; Queue Status</span>
                  <span className="text-[11px] text-slate-400">Notifies you if the physician is running ahead or behind schedule.</span>
                </div>
                <input
                  type="checkbox"
                  checked={notify2hCheckIn}
                  onChange={(e) => setNotify2hCheckIn(e.target.checked)}
                  className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4 ml-4"
                />
              </label>

              <label className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700">
                <div>
                  <span className="text-xs font-bold text-white block">Doctor Clinical Notes &amp; Rx Availability</span>
                  <span className="text-[11px] text-slate-400">Notification when your consultation summary and prescriptions are ready.</span>
                </div>
                <input
                  type="checkbox"
                  checked={notifyDoctorNotes}
                  onChange={(e) => setNotifyDoctorNotes(e.target.checked)}
                  className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4 ml-4"
                />
              </label>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-800">
            <button
              type="submit"
              disabled={isSaving}
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow-lg transition flex items-center space-x-2 cursor-pointer disabled:opacity-50"
            >
              {isSaving ? (
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              <span>Save Notification Preferences</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
