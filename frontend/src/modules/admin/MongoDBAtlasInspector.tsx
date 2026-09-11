import React, { useState, useEffect } from 'react';
import {
  Database,
  RefreshCw,
  Search,
  CheckCircle2,
  Copy,
  Check,
  FileJson,
  Layers,
  ArrowUpRight,
} from 'lucide-react';

interface MongoStatus {
  connected: boolean;
  database: string;
  collections: Record<string, number>;
}

export const MongoDBAtlasInspector: React.FC = () => {
  const [status, setStatus] = useState<MongoStatus | null>(null);
  const [selectedCollection, setSelectedCollection] = useState<string>('appointments');
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/v1/mongodb/status');
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch {
      // Fallback
    }
  };

  const fetchDocuments = async (collectionName: string) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/mongodb/documents/${collectionName}`);
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  useEffect(() => {
    fetchDocuments(selectedCollection);
  }, [selectedCollection]);

  const handleResync = async () => {
    setSyncing(true);
    try {
      await fetch('/api/v1/mongodb/seed', { method: 'POST' });
      await fetchStatus();
      await fetchDocuments(selectedCollection);
    } finally {
      setSyncing(false);
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredDocs = documents.filter((doc) => {
    if (!searchTerm) return true;
    const str = JSON.stringify(doc).toLowerCase();
    return str.includes(searchTerm.toLowerCase());
  });

  return (
    <div className="space-y-6">
      {/* Overview Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="flex items-center space-x-3.5">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center">
              <Database className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold text-emerald-800 uppercase tracking-wider">
                  Live Cloud Database
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-100 text-emerald-900">
                  <CheckCircle2 className="w-3 h-3 mr-1 text-emerald-700" />
                  Cluster Connected
                </span>
              </div>
              <h3 className="text-xl font-bold text-slate-900">MongoDB Atlas Document Store</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Database: <span className="font-mono font-semibold text-slate-800">{status?.database || 'nexushealth_hospital_db'}</span> &bull; Dual-Write Event Sync Active
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleResync}
              disabled={syncing}
              className="flex items-center space-x-1.5 px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-xs transition disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
              <span>{syncing ? 'Syncing...' : 'Resync Clinical Baseline'}</span>
            </button>
          </div>
        </div>

        {/* Collection Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-6">
          {['appointments', 'doctors', 'patients', 'questionnaires', 'hospitals', 'events'].map((col) => {
            const count = status?.collections?.[col] ?? 0;
            const isSelected = selectedCollection === col;
            return (
              <button
                key={col}
                onClick={() => setSelectedCollection(col)}
                className={`p-3 rounded-xl border text-left transition flex flex-col justify-between ${
                  isSelected
                    ? 'bg-teal-50 border-teal-300 ring-2 ring-teal-500/20'
                    : 'bg-slate-50 hover:bg-slate-100 border-slate-200'
                }`}
              >
                <div className="flex items-center justify-between text-[11px] font-medium text-slate-500 capitalize">
                  <span>{col}</span>
                  <Layers className="w-3 h-3 text-slate-400" />
                </div>
                <div className="mt-2 flex items-baseline justify-between">
                  <span className="text-lg font-bold text-slate-900 font-mono">{count}</span>
                  <span className="text-[10px] text-teal-800 font-medium">docs</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Document Explorer */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
        <div className="p-4 border-b border-slate-200 bg-slate-50/70 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div className="flex items-center space-x-2">
            <FileJson className="w-4 h-4 text-teal-700" />
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Collection: <span className="text-teal-700 font-mono">{selectedCollection}</span>
            </h4>
            <span className="text-[11px] text-slate-500">
              ({filteredDocs.length} {filteredDocs.length === 1 ? 'document' : 'documents'})
            </span>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search JSON attributes..."
              className="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-hidden focus:border-teal-500"
            />
          </div>
        </div>

        <div className="p-4">
          {loading ? (
            <div className="py-12 text-center text-slate-400 text-xs">
              <RefreshCw className="w-5 h-5 animate-spin mx-auto text-teal-600 mb-2" />
              Fetching live JSON documents from MongoDB Atlas...
            </div>
          ) : filteredDocs.length === 0 ? (
            <div className="py-12 text-center text-slate-400 text-xs">
              No JSON documents found in <span className="font-mono">{selectedCollection}</span> matching search.
            </div>
          ) : (
            <div className="space-y-4">
              {filteredDocs.map((doc, idx) => {
                const docId = doc._id || doc.appointment_id || doc.doctor_id || doc.patient_id || idx.toString();
                const jsonString = JSON.stringify(doc, null, 2);
                return (
                  <div
                    key={docId}
                    className="border border-slate-200 rounded-xl overflow-hidden bg-slate-50"
                  >
                    <div className="px-4 py-2 bg-slate-100/70 border-b border-slate-200 flex justify-between items-center text-xs">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-[11px] font-bold text-slate-700">
                          _id: {doc._id || 'N/A'}
                        </span>
                        {doc.appointment_id && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-teal-100 text-teal-800 font-mono">
                            {doc.appointment_id}
                          </span>
                        )}
                        {doc.doctor_id && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 font-mono">
                            {doc.doctor_id}
                          </span>
                        )}
                        {doc.status && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                            {doc.status}
                          </span>
                        )}
                      </div>

                      <button
                        onClick={() => handleCopy(docId, jsonString)}
                        className="flex items-center space-x-1 text-[11px] text-slate-600 hover:text-slate-900 font-medium px-2 py-1 rounded hover:bg-slate-200 transition"
                      >
                        {copiedId === docId ? (
                          <>
                            <Check className="w-3 h-3 text-emerald-600" />
                            <span className="text-emerald-600 font-semibold">Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            <span>Copy JSON</span>
                          </>
                        )}
                      </button>
                    </div>

                    <pre className="p-4 text-[11px] font-mono text-slate-800 overflow-x-auto max-h-64 leading-relaxed">
                      {jsonString}
                    </pre>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
