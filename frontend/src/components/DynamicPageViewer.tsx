import React, { useState, useEffect } from 'react';
import { api, PageDataResponse, CatalogPage } from '../api/client';
import {
  Sparkles,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  Table,
  Info,
  Play,
  Clock,
  ArrowRight,
} from 'lucide-react';

interface DynamicPageViewerProps {
  role: string;
  page: CatalogPage;
  context: {
    hospital_id?: string;
    doctor_id?: string;
    patient_id?: string;
  };
  onBackToWorkspace: () => void;
}

export const DynamicPageViewer: React.FC<DynamicPageViewerProps> = ({
  role,
  page,
  context,
  onBackToWorkspace,
}) => {
  const [data, setData] = useState<PageDataResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setActionFeedback(null);
    const res = await api.getPageData(role, page.page_id, context);
    if (res.ok && res.data) {
      setData(res.data);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [role, page.page_id]);

  const handleExecuteAction = async (actionName: string) => {
    setActionLoading(actionName);
    const res = await api.executePageAction(role, page.page_id, actionName);
    if (res.ok) {
      setActionFeedback(`Action "${actionName}" completed successfully.`);
      await loadData();
    } else {
      setActionFeedback(`Action failed: ${res.error || 'Server error'}`);
    }
    setActionLoading(null);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Top Banner & Context Info */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400">
            <span className="uppercase tracking-wider font-bold text-emerald-400">{role.toUpperCase()} WORKSPACE</span>
            <span>&bull;</span>
            <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded text-[10px] font-mono">
              Page #{page.page_number} / 49
            </span>
            <span>&bull;</span>
            <span className="text-slate-500">{page.category}</span>
          </div>
          <h1 className="text-2xl font-black text-white mt-1 flex items-center space-x-2">
            <span>{page.title}</span>
            <Sparkles className="w-5 h-5 text-emerald-400" />
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">{page.description}</p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={loadData}
            disabled={loading}
            className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold px-3 py-2 rounded-xl border border-slate-700 transition flex items-center space-x-1.5"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Data</span>
          </button>
          <button
            onClick={onBackToWorkspace}
            className="bg-emerald-600 hover:bg-emerald-500 text-slate-950 text-xs font-bold px-4 py-2 rounded-xl transition shadow flex items-center space-x-1.5"
          >
            <span>Primary Workspace</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {actionFeedback && (
        <div className="p-3.5 rounded-xl border text-xs font-semibold flex items-center space-x-2 bg-emerald-950/40 border-emerald-500/30 text-emerald-300 animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{actionFeedback}</span>
        </div>
      )}

      {loading ? (
        <div className="py-16 text-center text-xs text-slate-400 space-y-2">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p>Querying dynamic endpoint /api/v1/dashboard-pages/data/{role}/{page.page_id}...</p>
        </div>
      ) : !data ? (
        <div className="p-8 rounded-2xl bg-slate-900 border border-slate-800 text-center text-rose-400 text-xs">
          Unable to fetch page data.
        </div>
      ) : (
        <>
          {/* KPI Metrics Row */}
          {data.kpis && data.kpis.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {data.kpis.map((kpi, idx) => (
                <div
                  key={idx}
                  className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm space-y-1 hover:border-slate-700 transition"
                >
                  <div className="text-xs text-slate-400 font-medium truncate">{kpi.label}</div>
                  <div className="text-2xl font-black text-white">{kpi.value}</div>
                  <div
                    className={`text-[11px] font-semibold flex items-center space-x-1 ${
                      kpi.status === 'good'
                        ? 'text-emerald-400'
                        : kpi.status === 'warning'
                        ? 'text-amber-400'
                        : 'text-slate-400'
                    }`}
                  >
                    <span>&bull;</span>
                    <span className="truncate">{kpi.trend}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Contextual Actions Bar */}
          {data.available_actions && data.available_actions.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <div className="flex items-center space-x-2">
                <Play className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Page Actions:
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {data.available_actions.map((act) => (
                  <button
                    key={act}
                    disabled={actionLoading === act}
                    onClick={() => handleExecuteAction(act)}
                    className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 hover:text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition flex items-center space-x-1.5"
                  >
                    {actionLoading === act ? (
                      <Clock className="w-3 h-3 animate-spin" />
                    ) : (
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                    )}
                    <span className="capitalize">{act.replace(/_/g, ' ')}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Main Content: Records Table & Details Card */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Records Table (8 cols if details exist, otherwise 12) */}
            <div
              className={`${
                data.details && Object.keys(data.details).length > 0 ? 'lg:col-span-8' : 'col-span-12'
              } bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-md`}
            >
              <div className="flex justify-between items-center pb-2 border-b border-slate-800">
                <div className="flex items-center space-x-2">
                  <Table className="w-4 h-4 text-sky-400" />
                  <h3 className="font-bold text-sm text-white">Live Records &amp; Entities</h3>
                </div>
                <span className="text-[10px] font-mono text-slate-400">
                  {data.records?.length || 0} Records Loaded
                </span>
              </div>

              {data.records && data.records.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="text-[10px] uppercase text-slate-400 bg-slate-950 border-y border-slate-800">
                      <tr>
                        {data.table_headers?.map((h, i) => (
                          <th key={i} className="py-2.5 px-3 whitespace-nowrap">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 font-medium">
                      {data.records.map((row, rIdx) => (
                        <tr key={rIdx} className="hover:bg-slate-800/50 transition">
                          {data.table_headers?.map((h, cIdx) => (
                            <td key={cIdx} className="py-3 px-3 text-slate-200">
                              {typeof row[h] === 'object'
                                ? JSON.stringify(row[h])
                                : String(row[h] ?? '—')}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-8 text-center text-xs text-slate-500 bg-slate-950/40 rounded-xl border border-dashed border-slate-800">
                  Zero active records for this context. Use page actions above to trigger new events.
                </div>
              )}
            </div>

            {/* Details Card (4 cols) */}
            {data.details && Object.keys(data.details).length > 0 && (
              <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3 shadow-md flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center space-x-2 pb-2 border-b border-slate-800">
                    <Info className="w-4 h-4 text-emerald-400" />
                    <h3 className="font-bold text-sm text-white">Contextual Insights</h3>
                  </div>

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 space-y-2 text-xs">
                    {Object.entries(data.details).map(([key, value], idx) => (
                      <div key={idx} className="space-y-0.5 border-b border-slate-900 pb-1.5 last:border-none">
                        <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                          {key.replace(/_/g, ' ')}
                        </div>
                        <div className="text-slate-200 font-medium break-words">
                          {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-800 text-[10px] text-slate-500 font-mono">
                  Timestamp: {data.retrieved_at}
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};
