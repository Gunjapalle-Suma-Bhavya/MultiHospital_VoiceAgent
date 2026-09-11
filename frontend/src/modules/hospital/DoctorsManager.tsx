import React from 'react';
import { Building2, Plus } from 'lucide-react';
import { apiCall } from '../../api/client';

interface DoctorsManagerProps {
  facilities: any[];
  onFacilityRegistered: () => void;
}

export const DoctorsManager: React.FC<DoctorsManagerProps> = ({
  facilities,
  onFacilityRegistered,
}) => {
  const handleRegisterFacility = async () => {
    const name = prompt('Enter Hospital Name:', "St. Jude Children's Research Center");
    if (!name) return;
    const code = prompt('Enter Hospital Code:', 'SJR-03');
    if (!code) return;

    try {
      await apiCall('/api/v1/onboarding/draft', {
        method: 'POST',
        body: JSON.stringify({
          name,
          code,
          contact_email: `admin@${code.toLowerCase()}.org`,
          admin_name: 'Operations Director',
          admin_email: `ops@${code.toLowerCase()}.org`,
        }),
      });
      alert(`Facility "${name}" (${code}) submitted for Platform Super-Admin review.`);
      onFacilityRegistered();
    } catch (e: any) {
      alert(`Error registering facility: ${e.message}`);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3 shadow-md">
      <div className="flex justify-between items-center pb-2 border-b border-slate-800">
        <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
          <Building2 className="w-4 h-4 text-indigo-400" />
          <span>Network Facilities Roster</span>
        </h3>
        <button
          onClick={handleRegisterFacility}
          className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs px-2.5 py-1.5 rounded-lg transition shadow flex items-center gap-1"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Register Facility</span>
        </button>
      </div>

      <div className="space-y-2.5">
        {facilities.map((f, idx) => (
          <div
            key={idx}
            className="bg-slate-950 border border-slate-800 p-3.5 rounded-xl flex justify-between items-center hover:border-slate-700 transition"
          >
            <div>
              <h4 className="font-bold text-xs text-white">{f.name}</h4>
              <p className="text-[11px] text-slate-400">
                Code: {f.code} &bull; Contact: {f.contact_email || 'admin@hospital.org'}
              </p>
              <div className="text-[10px] text-slate-500 mt-0.5 font-mono">
                Adapter: {f.adapter || 'EPIC_MYCHART (SMART-on-FHIR R4)'}
              </div>
            </div>
            <span className="text-[10px] font-black bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full uppercase">
              Approved
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
