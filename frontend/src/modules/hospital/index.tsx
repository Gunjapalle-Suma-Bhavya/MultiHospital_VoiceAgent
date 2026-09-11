import React, { useState, useEffect } from 'react';
import { Building2 } from 'lucide-react';
import { DoctorsManager } from './DoctorsManager';
import { EHRConfig } from './EHRConfig';
import { apiCall } from '../../api/client';

export const HospitalPortal: React.FC = () => {
  const [facilities, setFacilities] = useState<any[]>([
    {
      name: 'City Memorial Hospital',
      code: 'CMH-01',
      contact_email: 'admin@citymemorial.org',
      adapter: 'EPIC_MYCHART (SMART-on-FHIR R4)',
    },
    {
      name: 'Metro Health Center',
      code: 'MHC-02',
      contact_email: 'admin@metrohealth.org',
      adapter: 'CERNER (Ignite API)',
    },
  ]);

  const loadFacilities = async () => {
    try {
      const res = await apiCall('/api/v1/capabilities/execute', {
        method: 'POST',
        body: JSON.stringify({
          capability_name: 'search_hospitals',
          caller_role: 'HOSPITAL_ADMIN',
          arguments: {},
        }),
      });

      if (res.ok && res.data?.data?.hospitals) {
        setFacilities(res.data.data.hospitals);
      }
    } catch (e) {
      console.error('Error fetching facilities:', e);
    }
  };

  useEffect(() => {
    loadFacilities();
  }, []);

  return (
    <div className="space-y-6">
      {/* Hospital Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shadow-lg">
        <div>
          <div className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
            Hospital Administration &amp; Interoperability
          </div>
          <h2 className="text-xl font-black text-white mt-0.5">City Memorial Hospital (CMH-01)</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Status: <span className="text-emerald-400 font-bold">APPROVED &amp; ACTIVE</span> &bull; Active Doctors: 8 &bull; EHR Adapter: Epic MyChart
          </p>
        </div>
      </div>

      {/* 2 Columns: Facilities List & EHR Interoperability Hub */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6">
          <DoctorsManager facilities={facilities} onFacilityRegistered={loadFacilities} />
        </div>

        <div className="lg:col-span-6">
          <EHRConfig />
        </div>
      </div>
    </div>
  );
};
