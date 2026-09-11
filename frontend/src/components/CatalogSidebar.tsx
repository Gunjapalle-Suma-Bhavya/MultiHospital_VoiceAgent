import React, { useState, useEffect } from 'react';
import { api, CatalogResponse, CatalogPage } from '../api/client';
import {
  Layers,
  Search,
  ChevronDown,
  ChevronRight,
  Shield,
  Building2,
  Stethoscope,
  User,
  Sparkles,
  ExternalLink,
} from 'lucide-react';

interface CatalogSidebarProps {
  currentRole: string;
  selectedPage: { role: string; page_id: string } | null;
  onSelectPage: (role: string, page: CatalogPage) => void;
  onBackToDashboard: () => void;
}

export const CatalogSidebar: React.FC<CatalogSidebarProps> = ({
  currentRole,
  selectedPage,
  onSelectPage,
  onBackToDashboard,
}) => {
  const [catalog, setCatalog] = useState<CatalogResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedRoles, setExpandedRoles] = useState<Record<string, boolean>>({
    admin: true,
    hospital: true,
    doctor: true,
    patient: true,
  });

  useEffect(() => {
    async function loadCatalog() {
      setLoading(true);
      const res = await api.getCatalog();
      if (res.ok && res.data) {
        setCatalog(res.data);
      }
      setLoading(false);
    }
    loadCatalog();
  }, []);

  const toggleRole = (roleId: string) => {
    setExpandedRoles((prev) => ({ ...prev, [roleId]: !prev[roleId] }));
  };

  const getRoleIcon = (roleId: string) => {
    switch (roleId) {
      case 'admin':
        return <Shield className="w-4 h-4 text-amber-400" />;
      case 'hospital':
        return <Building2 className="w-4 h-4 text-indigo-400" />;
      case 'doctor':
        return <Stethoscope className="w-4 h-4 text-sky-400" />;
      case 'patient':
        return <User className="w-4 h-4 text-emerald-400" />;
      default:
        return <Layers className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <aside className="w-80 bg-slate-900 border-r border-slate-800 flex flex-col h-[calc(100vh-4rem)] sticky top-16 select-none">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 space-y-3 bg-slate-950/60">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-white tracking-wide">49-Page Platform Catalog</h3>
              <p className="text-[10px] text-slate-400">Canonical Section 11 Specification</p>
            </div>
          </div>
          <button
            onClick={onBackToDashboard}
            className="text-[10px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded font-semibold border border-slate-700 transition flex items-center space-x-1"
            title="Return to primary role portal"
          >
            <span>Workspace</span>
            <ExternalLink className="w-3 h-3" />
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search all 49 pages..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
        </div>
      </div>

      {/* Catalog Tree */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar">
        {loading ? (
          <div className="py-8 text-center text-xs text-slate-500 animate-pulse">
            Loading 49-page catalog schema...
          </div>
        ) : !catalog ? (
          <div className="py-8 text-center text-xs text-rose-400">Failed to load catalog.</div>
        ) : (
          catalog.roles.map((role) => {
            const filteredPages = role.pages.filter(
              (p) =>
                p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                p.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                p.category.toLowerCase().includes(searchQuery.toLowerCase())
            );

            if (searchQuery && filteredPages.length === 0) return null;

            const isExpanded = expandedRoles[role.role_id] ?? true;
            const isCurrentActiveRole =
              currentRole.toLowerCase().includes(role.role_id) ||
              (currentRole === 'PLATFORM_ADMIN' && role.role_id === 'admin') ||
              (currentRole === 'HOSPITAL_ADMIN' && role.role_id === 'hospital');

            return (
              <div key={role.role_id} className="space-y-1">
                {/* Role Group Accordion Button */}
                <button
                  onClick={() => toggleRole(role.role_id)}
                  className={`w-full flex items-center justify-between p-2 rounded-lg text-xs font-bold transition ${
                    isCurrentActiveRole
                      ? 'bg-slate-800/80 text-white'
                      : 'hover:bg-slate-800/40 text-slate-300'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    {getRoleIcon(role.role_id)}
                    <span className="truncate">{role.display_title}</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <span className="text-[10px] font-mono font-semibold text-slate-400 bg-slate-900 px-1.5 py-0.2 rounded border border-slate-800">
                      {role.total_pages}
                    </span>
                    {isExpanded ? (
                      <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                    ) : (
                      <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                    )}
                  </div>
                </button>

                {/* Role Pages List */}
                {isExpanded && (
                  <div className="pl-3 space-y-0.5 border-l border-slate-800/60 ml-3">
                    {filteredPages.map((page) => {
                      const isSelected =
                        selectedPage?.role === role.role_id &&
                        selectedPage?.page_id === page.page_id;

                      return (
                        <button
                          key={page.page_id}
                          onClick={() => onSelectPage(role.role_id, page)}
                          className={`w-full text-left p-1.5 rounded-lg text-xs transition flex items-center justify-between group ${
                            isSelected
                              ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-bold'
                              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                          }`}
                        >
                          <div className="flex items-center space-x-2 truncate">
                            <span className="text-[10px] font-mono text-slate-500 w-4">
                              #{page.page_number}
                            </span>
                            <span className="truncate">{page.title}</span>
                          </div>
                          <span className="text-[9px] uppercase tracking-wider text-slate-500 font-semibold group-hover:text-slate-400">
                            {page.category}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Catalog Footer Stats */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/80 text-[11px] text-slate-400 flex items-center justify-between">
        <div className="flex items-center space-x-1.5">
          <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
          <span>49 Dynamic Endpoints</span>
        </div>
        <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded">
          100% LIVE
        </span>
      </div>
    </aside>
  );
};
