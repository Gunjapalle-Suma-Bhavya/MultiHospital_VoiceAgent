import React, { useState, useEffect } from 'react';
import { Bell, Send, RotateCw, CheckCircle2, MessageSquare, Mail, PhoneCall } from 'lucide-react';
import { apiCall } from '../../api/client';
import { useAuth } from '../../hooks/useAuth';
import { useToast } from '../../context/ToastContext';

interface NotificationRecord {
  id: string;
  notification_type: string;
  channel: string;
  subject?: string;
  body: string;
  status: string;
  sent_at?: string;
}

export const PatientNotifications: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [notifications, setNotifications] = useState<NotificationRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);

  const recipientId = user?.identifier || '+1-555-SHOULDER';

  const fetchNotifications = async () => {
    setIsLoading(true);
    try {
      const res = await apiCall(
        `/api/v1/notifications/recipient/PATIENT/${encodeURIComponent(recipientId)}`
      );
      if (res.ok && res.data?.notifications) {
        setNotifications(res.data.notifications);
      }
    } catch (e) {
      console.error('Fetch notifications error:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [recipientId]);

  const handleSendTestAlert = async () => {
    setIsSending(true);
    try {
      const res = await apiCall('/api/v1/notifications/send', {
        method: 'POST',
        body: JSON.stringify({
          recipient_role: 'PATIENT',
          recipient_id: recipientId,
          notification_type: 'APPOINTMENT_REMINDER',
          subject: 'Appointment Confirmation - City Memorial Hospital',
          body: 'Your medical consultation is confirmed. Please arrive 15 minutes prior with your photo ID.',
          channel: 'SMS',
          metadata: { priority: 'HIGH', automated: true },
        }),
      });

      if (res.ok) {
        showToast(
          'success',
          'SMS Alert Dispatched',
          `Notification dispatched to ${recipientId} via live notification engine.`
        );
        fetchNotifications();
      }
    } catch (e: any) {
      showToast('error', 'Dispatch Error', e.message);
    } finally {
      setIsSending(false);
    }
  };

  const getChannelIcon = (channel: string) => {
    switch (channel.toUpperCase()) {
      case 'EMAIL':
        return <Mail className="w-4 h-4 text-sky-400" />;
      case 'VOICE':
        return <PhoneCall className="w-4 h-4 text-emerald-400" />;
      default:
        return <MessageSquare className="w-4 h-4 text-indigo-400" />;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-md">
      <div className="flex flex-wrap justify-between items-center pb-2 border-b border-slate-800 gap-2">
        <div>
          <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
            <Bell className="w-4 h-4 text-emerald-400" />
            <span>Real-Time Dispatched Alerts &amp; Notifications</span>
          </h3>
          <p className="text-xs text-slate-400">
            Audit log of SMS, Email, and Voice automated alerts from{' '}
            <code className="text-emerald-400 font-mono text-[11px]">
              GET /api/v1/notifications/recipient/PATIENT/&#123;phone&#125;
            </code>
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={fetchNotifications}
            disabled={isLoading}
            className="text-xs text-slate-400 hover:text-white flex items-center gap-1 p-1.5 rounded-lg hover:bg-slate-800 transition"
            title="Refresh logs"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={handleSendTestAlert}
            disabled={isSending}
            className="bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs px-3 py-1.5 rounded-lg transition shadow flex items-center space-x-1 disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{isSending ? 'Sending...' : 'Dispatch Test Alert'}</span>
          </button>
        </div>
      </div>

      {notifications.length === 0 ? (
        <div className="py-12 text-center text-xs text-slate-500 space-y-2">
          <div className="w-10 h-10 rounded-full bg-slate-800 text-slate-400 mx-auto flex items-center justify-center">
            <Bell className="w-5 h-5" />
          </div>
          <div className="font-bold text-slate-300">No Notifications on Record Yet</div>
          <p className="max-w-sm mx-auto">
            Automated notifications are dispatched upon appointment booking, reminder intervals, and
            physician schedule adjustments.
          </p>
          <button
            onClick={handleSendTestAlert}
            className="text-emerald-400 font-bold hover:underline inline-block pt-1"
          >
            Dispatch a sample SMS reminder now &rarr;
          </button>
        </div>
      ) : (
        <div className="space-y-2.5">
          {notifications.map((n) => (
            <div
              key={n.id}
              className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 space-y-1.5 hover:border-slate-700 transition"
            >
              <div className="flex justify-between items-center text-[10px]">
                <span className="flex items-center gap-1.5 font-bold text-emerald-400 uppercase">
                  {getChannelIcon(n.channel)}
                  <span>{n.channel} &bull; {n.notification_type}</span>
                </span>
                <span className="text-slate-500 font-mono">
                  {n.sent_at ? new Date(n.sent_at).toLocaleString() : 'Just now'}
                </span>
              </div>
              {n.subject && (
                <div className="text-xs font-bold text-white">{n.subject}</div>
              )}
              <div className="text-xs text-slate-300 leading-relaxed">{n.body}</div>
              <div className="flex justify-between items-center pt-1 text-[10px] text-slate-500">
                <span>Status: <strong className="text-emerald-400 font-mono">{n.status}</strong></span>
                <span className="font-mono text-[10px] text-slate-600">ID: {n.id}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
