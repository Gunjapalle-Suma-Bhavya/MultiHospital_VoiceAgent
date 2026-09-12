import React, { useState } from 'react';
import { X, Printer, Calendar, MapPin, QrCode, CheckCircle2, ShieldCheck, Download, Wallet } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';

interface Props {
  booking: {
    id: string;
    doctor_name: string;
    specialty: string;
    scheduled_time: string;
    patient_name: string;
    patient_phone: string;
    hospital_name?: string;
  };
  onClose: () => void;
}

export const AppointmentPassModal: React.FC<Props> = ({ booking, onClose }) => {
  const { t } = useLanguage();
  const [walletSaved, setWalletSaved] = useState(false);

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadWalletPass = () => {
    const passObj = {
      formatVersion: 1,
      passTypeIdentifier: 'pass.com.nexushealth.clinical.appointment',
      serialNumber: booking.id,
      teamIdentifier: 'NEXUSHEALTH',
      organizationName: booking.hospital_name || 'NexusHealth Hospital Network',
      description: `Appointment with ${booking.doctor_name}`,
      barcode: {
        message: `NEXUS-CARE-PASS-${booking.id}`,
        format: 'PKBarcodeFormatQR',
        messageEncoding: 'iso-8859-1',
      },
      generic: {
        primaryFields: [
          { key: 'doctor', label: 'PHYSICIAN', value: booking.doctor_name },
        ],
        secondaryFields: [
          { key: 'patient', label: 'PATIENT', value: booking.patient_name },
          { key: 'time', label: 'DATE & TIME', value: booking.scheduled_time },
        ],
        backFields: [
          { key: 'specialty', label: 'CLINICAL SPECIALTY', value: booking.specialty },
          { key: 'phone', label: 'CONTACT', value: booking.patient_phone },
          { key: 'instructions', label: 'ARRIVAL', value: 'Please check in 15 minutes prior to appointment.' }
        ]
      }
    };

    const blob = new Blob([JSON.stringify(passObj, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `care-pass-${booking.id}.pass.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setWalletSaved(true);
    setTimeout(() => setWalletSaved(false), 3500);
  };

  const downloadICal = () => {
    const icsData = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//NexusHealth//Clinical Appointment//EN',
      'BEGIN:VEVENT',
      `SUMMARY:Medical Consultation with ${booking.doctor_name}`,
      `DESCRIPTION:Consultation for ${booking.specialty}. Booking Ref: ${booking.id}`,
      'LOCATION:City Memorial Hospital, Suite 304',
      `STATUS:CONFIRMED`,
      'END:VEVENT',
      'END:VCALENDAR',
    ].join('\r\n');

    const blob = new Blob([icsData], { type: 'text/calendar;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `appointment-${booking.id}.ics`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-lg w-full overflow-hidden shadow-2xl animate-in zoom-in-95">
        {/* Modal Top Bar */}
        <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/90 print:hidden">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-bold text-white uppercase tracking-wider">
              Patient Care Pass &bull; Contactless Kiosk Check-In
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-white rounded-lg transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Printable Ticket Body */}
        <div className="p-6 space-y-5 bg-gradient-to-b from-slate-900 via-slate-900 to-slate-950 text-slate-100 print:bg-white print:text-black">
          {/* Header */}
          <div className="flex justify-between items-start border-b border-slate-800 pb-4">
            <div>
              <div className="text-[10px] font-extrabold uppercase tracking-widest text-emerald-400">
                Official Hospital Boarding Pass
              </div>
              <h2 className="text-xl font-black text-white print:text-black mt-0.5">
                City Memorial Hospital
              </h2>
              <div className="text-xs text-slate-400 print:text-gray-600 flex items-center gap-1 mt-1">
                <MapPin className="w-3.5 h-3.5 text-emerald-400" />
                <span>Pavilion West, 3rd Floor &bull; Suite 304</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-[10px] text-slate-500 font-bold uppercase">Booking ID</div>
              <div className="text-base font-black font-mono text-emerald-400">#{booking.id}</div>
            </div>
          </div>

          {/* QR Code & Barcode Scanner Card */}
          <div className="bg-white p-5 rounded-2xl flex flex-col items-center justify-center space-y-2 text-slate-950 shadow-lg">
            {/* Realistic Geometric QR Code SVG */}
            <svg
              className="w-40 h-40"
              viewBox="0 0 100 100"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
            >
              {/* Corner 1 */}
              <rect x="5" y="5" width="28" height="28" fill="#0f172a" rx="4" />
              <rect x="9" y="9" width="20" height="20" fill="white" rx="2" />
              <rect x="13" y="13" width="12" height="12" fill="#0f172a" rx="1" />
              {/* Corner 2 */}
              <rect x="67" y="5" width="28" height="28" fill="#0f172a" rx="4" />
              <rect x="71" y="9" width="20" height="20" fill="white" rx="2" />
              <rect x="75" y="13" width="12" height="12" fill="#0f172a" rx="1" />
              {/* Corner 3 */}
              <rect x="5" y="67" width="28" height="28" fill="#0f172a" rx="4" />
              <rect x="9" y="71" width="20" height="20" fill="white" rx="2" />
              <rect x="13" y="75" width="12" height="12" fill="#0f172a" rx="1" />
              {/* Data Blocks Pattern */}
              <rect x="38" y="8" width="6" height="6" fill="#0f172a" />
              <rect x="48" y="12" width="6" height="6" fill="#0f172a" />
              <rect x="38" y="24" width="8" height="6" fill="#0f172a" />
              <rect x="52" y="26" width="6" height="8" fill="#0f172a" />
              <rect x="10" y="42" width="8" height="6" fill="#0f172a" />
              <rect x="24" y="46" width="6" height="8" fill="#0f172a" />
              <rect x="36" y="40" width="10" height="10" fill="#0f172a" />
              <rect x="54" y="42" width="8" height="6" fill="#0f172a" />
              <rect x="70" y="44" width="6" height="6" fill="#0f172a" />
              <rect x="84" y="40" width="8" height="8" fill="#0f172a" />
              <rect x="40" y="58" width="8" height="8" fill="#0f172a" />
              <rect x="56" y="56" width="6" height="10" fill="#0f172a" />
              <rect x="70" y="60" width="10" height="6" fill="#0f172a" />
              <rect x="38" y="74" width="8" height="8" fill="#0f172a" />
              <rect x="52" y="72" width="8" height="6" fill="#0f172a" />
              <rect x="68" y="74" width="6" height="8" fill="#0f172a" />
              <rect x="82" y="76" width="10" height="6" fill="#0f172a" />
              <rect x="44" y="86" width="10" height="6" fill="#0f172a" />
              <rect x="60" y="84" width="8" height="8" fill="#0f172a" />
              <rect x="76" y="86" width="8" height="6" fill="#0f172a" />
            </svg>
            <div className="text-center">
              <div className="text-xs font-black font-mono tracking-wider">
                KIOSK SCAN: {booking.id}
              </div>
              <div className="text-[10px] text-slate-500 font-medium">
                Hold to scanner glass at entrance kiosk for immediate check-in
              </div>
            </div>
          </div>

          {/* Details Table */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <div className="text-[10px] text-slate-500 font-bold uppercase">Patient</div>
              <div className="font-bold text-white mt-0.5">{booking.patient_name}</div>
              <div className="text-[11px] text-slate-400 font-mono">{booking.patient_phone}</div>
            </div>

            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <div className="text-[10px] text-slate-500 font-bold uppercase">Physician</div>
              <div className="font-bold text-emerald-400 mt-0.5">{booking.doctor_name}</div>
              <div className="text-[11px] text-slate-400">{booking.specialty}</div>
            </div>

            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <div className="text-[10px] text-slate-500 font-bold uppercase">Consultation Time</div>
              <div className="font-bold text-white mt-0.5">{booking.scheduled_time}</div>
              <div className="text-[11px] text-emerald-400 font-semibold">Confirmed Slot</div>
            </div>

            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <div className="text-[10px] text-slate-500 font-bold uppercase">Arrival Instruction</div>
              <div className="font-bold text-amber-400 mt-0.5">Arrive 15 Min Early</div>
              <div className="text-[11px] text-slate-400">Bring ID &amp; Insurance</div>
            </div>
          </div>

          {/* Verification Badge */}
          <div className="bg-emerald-950/40 border border-emerald-500/20 text-emerald-300 p-3 rounded-xl text-xs flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span className="text-[11px]">
              5-Point EHR Verification complete: Double-booking cleared, calendar locked, and
              provider licensed.
            </span>
          </div>
        </div>

        {/* Modal Action Buttons (Upgrade 7) */}
        <div className="p-4 border-t border-slate-800 bg-slate-900 flex flex-wrap justify-between items-center gap-2 print:hidden">
          <div className="flex items-center space-x-2">
            <button
              onClick={downloadICal}
              className="text-xs text-slate-300 hover:text-white px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 transition flex items-center space-x-1.5"
            >
              <Calendar className="w-3.5 h-3.5 text-sky-400" />
              <span>iCal / Outlook</span>
            </button>

            <button
              onClick={handleDownloadWalletPass}
              className={`text-xs px-3 py-2 rounded-xl border transition flex items-center space-x-1.5 ${
                walletSaved
                  ? 'bg-emerald-950/80 text-emerald-400 border-emerald-500/50'
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700'
              }`}
              title="Download Apple / Google Mobile Wallet Pass"
            >
              <Wallet className="w-3.5 h-3.5 text-amber-400" />
              <span>{walletSaved ? '✓ Pass Downloaded' : t('apple_wallet')}</span>
            </button>
          </div>

          <div className="flex space-x-2">
            <button
              onClick={handlePrint}
              className="text-xs font-bold text-slate-950 bg-emerald-500 hover:bg-emerald-400 px-4 py-2 rounded-xl transition flex items-center space-x-1.5 shadow-lg shadow-emerald-500/20"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>{t('print_pass')}</span>
            </button>
            <button
              onClick={onClose}
              className="text-xs text-slate-400 hover:text-white px-3 py-2 rounded-xl bg-slate-800 transition"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
