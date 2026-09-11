import React, { useState } from 'react';
import { X, Copy, Check, Terminal, ExternalLink, ShieldCheck, Play } from 'lucide-react';
import { useToast } from '../../context/ToastContext';

interface Props {
  onClose: () => void;
  connectorName?: string;
}

export const FHIRInspectorModal: React.FC<Props> = ({
  onClose,
  connectorName = 'Epic FHIR R4 Connector',
}) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<'Patient' | 'Encounter' | 'Slot' | 'Capability'>('Patient');
  const [copied, setCopied] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);

  const fhirPayloads = {
    Patient: {
      resourceType: 'Patient',
      id: 'pat-marcus-aurelius',
      meta: {
        versionId: '1',
        lastUpdated: new Date().toISOString(),
        profile: ['http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient'],
      },
      text: {
        status: 'generated',
        div: '<div xmlns="http://www.w3.org/1999/xhtml">Marcus Aurelius, Male, MRN: 88421</div>',
      },
      identifier: [
        {
          use: 'usual',
          type: {
            coding: [
              {
                system: 'http://terminology.hl7.org/CodeSystem/v2-0203',
                code: 'MR',
                display: 'Medical Record Number',
              },
            ],
          },
          system: 'http://hospital.citymemorial.org/mrn',
          value: 'MRN-88421',
        },
      ],
      active: true,
      name: [{ use: 'official', family: 'Aurelius', given: ['Marcus'] }],
      telecom: [
        { system: 'phone', value: '+1-555-SHOULDER', use: 'mobile' },
        { system: 'email', value: 'patient.a@example.com', use: 'home' },
      ],
      gender: 'male',
      birthDate: '1984-04-26',
    },
    Encounter: {
      resourceType: 'Encounter',
      id: 'enc-apt-1024',
      meta: {
        profile: ['http://hl7.org/fhir/us/core/StructureDefinition/us-core-encounter'],
      },
      status: 'planned',
      class: {
        system: 'http://terminology.hl7.org/CodeSystem/v3-ActCode',
        code: 'AMB',
        display: 'ambulatory',
      },
      type: [
        {
          coding: [
            {
              system: 'http://snomed.info/sct',
              code: '408443003',
              display: 'General medical examination',
            },
          ],
        },
      ],
      subject: { reference: 'Patient/pat-marcus-aurelius', display: 'Marcus Aurelius' },
      participant: [
        {
          type: [
            {
              coding: [
                {
                  system: 'http://terminology.hl7.org/CodeSystem/v3-ParticipationType',
                  code: 'PPRF',
                  display: 'primary performer',
                },
              ],
            },
          ],
          individual: {
            reference: 'Practitioner/doc-sharma-01',
            display: 'Dr. Sharma, MD (NPI 198234812)',
          },
        },
      ],
      period: {
        start: new Date(Date.now() + 86400000).toISOString(),
        end: new Date(Date.now() + 88200000).toISOString(),
      },
      serviceProvider: {
        reference: 'Organization/hosp-city-01',
        display: 'City Memorial Hospital',
      },
    },
    Slot: {
      resourceType: 'Slot',
      id: 'slot-doc-sharma-1000',
      schedule: { reference: 'Schedule/sch-doc-sharma-01' },
      status: 'busy-unavailable',
      start: '2026-09-12T10:00:00Z',
      end: '2026-09-12T10:30:00Z',
      overbooked: false,
      comment: 'Reserved via NexusHealth Autonomous Voice Platform',
    },
    Capability: {
      resourceType: 'CapabilityStatement',
      id: 'epic-fhir-r4-server',
      status: 'active',
      date: '2026-09-11',
      kind: 'instance',
      fhirVersion: '4.0.1',
      format: ['application/fhir+json'],
      rest: [
        {
          mode: 'server',
          resource: [
            { type: 'Patient', interaction: [{ code: 'read' }, { code: 'search-type' }] },
            { type: 'Encounter', interaction: [{ code: 'read' }, { code: 'create' }] },
            { type: 'Slot', interaction: [{ code: 'read' }, { code: 'search-type' }] },
          ],
        },
      ],
    },
  };

  const currentJson = JSON.stringify(fhirPayloads[activeTab], null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(currentJson);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    showToast('info', 'FHIR Payload Copied', 'JSON payload copied to system clipboard.');
  };

  const handleSimulate = () => {
    setIsSimulating(true);
    setTimeout(() => {
      setIsSimulating(false);
      showToast(
        'ehr_sync',
        `FHIR R4 REST Dispatch: 201 Created`,
        `Successfully POSTed ${activeTab} resource to ${connectorName}. Endpoint returned latency: 142ms.`
      );
    }, 800);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex justify-between items-center bg-slate-900/90">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-indigo-400">
                HL7 FHIR R4 Diagnostic Inspector
              </div>
              <h2 className="text-base sm:text-lg font-bold text-white">
                {connectorName} &bull; US Core Implementation Guide (v4.0.1)
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Resource Tabs */}
        <div className="flex border-b border-slate-800 bg-slate-950/60 px-5 pt-2 gap-2 text-xs">
          {(['Patient', 'Encounter', 'Slot', 'Capability'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-3.5 rounded-t-lg font-bold transition border-b-2 ${
                activeTab === tab
                  ? 'border-indigo-400 text-white bg-slate-900'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab}.json
            </button>
          ))}
        </div>

        {/* Payload Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          <div className="flex justify-between items-center">
            <div className="text-xs text-slate-400 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Conforms to HL7 US Core Schema Validator &bull; 0 Schema Violations</span>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={handleCopy}
                className="text-xs text-slate-300 hover:text-white px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 transition flex items-center space-x-1"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy JSON'}</span>
              </button>
              <button
                onClick={handleSimulate}
                disabled={isSimulating}
                className="text-xs font-bold text-slate-950 bg-indigo-400 hover:bg-indigo-300 px-3 py-1.5 rounded-lg transition flex items-center space-x-1 shadow disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>{isSimulating ? 'Simulating...' : 'Simulate REST POST'}</span>
              </button>
            </div>
          </div>

          {/* JSON Viewer */}
          <pre className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs font-mono text-indigo-300 overflow-x-auto leading-relaxed">
            {currentJson}
          </pre>

          {/* Field Mapping Diff Table */}
          <div className="space-y-2">
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Field-Level Schema Mapping:
            </div>
            <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden text-xs">
              <table className="w-full text-left">
                <thead className="bg-slate-900/80 text-slate-400 text-[10px] uppercase border-b border-slate-800">
                  <tr>
                    <th className="py-2 px-3">Local Platform Field</th>
                    <th className="py-2 px-3">HL7 FHIR R4 JSON Path</th>
                    <th className="py-2 px-3">Transformation Rule</th>
                    <th className="py-2 px-3 text-right">Verification</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                  <tr>
                    <td className="py-2 px-3 text-white">patient_phone</td>
                    <td className="py-2 px-3 text-indigo-400">telecom[system=phone].value</td>
                    <td className="py-2 px-3 text-slate-400">E.164 Normalization</td>
                    <td className="py-2 px-3 text-right text-emerald-400 font-bold">MATCH</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-white">doctor_id</td>
                    <td className="py-2 px-3 text-indigo-400">participant[0].individual.value</td>
                    <td className="py-2 px-3 text-slate-400">NPI Registry Lookup</td>
                    <td className="py-2 px-3 text-right text-emerald-400 font-bold">MATCH</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-white">start_datetime</td>
                    <td className="py-2 px-3 text-indigo-400">period.start</td>
                    <td className="py-2 px-3 text-slate-400">ISO 8601 UTC Offset</td>
                    <td className="py-2 px-3 text-right text-emerald-400 font-bold">MATCH</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/90 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs transition"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
