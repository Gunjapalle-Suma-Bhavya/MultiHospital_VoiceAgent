import React, { useState, useEffect } from 'react';
import {
  Users,
  Shield,
  Search,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Lock,
  Mail,
  Building2,
  Filter,
  UserCheck,
  UserX,
  KeyRound
} from 'lucide-react';
import { apiCall } from '../../api/client';

interface UserAccountItem {
  id: string;
  email: string;
  full_name: string;
  role: string;
  hospital_id?: string;
  hospital_name?: string;
  auth_provider: string;
  is_active: boolean;
  created_at?: string;
}

export const UserAuthenticationBoard: React.FC = () => {
  const [users, setUsers] = useState<UserAccountItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [roleFilter, setRoleFilter] = useState<string>('ALL');
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchUsers = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const url = roleFilter !== 'ALL' 
        ? `/api/v1/auth/users?role=${roleFilter}` 
        : '/api/v1/auth/users';
      const res = await apiCall(url);
      if (res.ok && res.data?.users) {
        setUsers(res.data.users);
      } else {
        setError(res.error || 'Failed to fetch user accounts');
      }
    } catch (err: any) {
      setError(err?.message || 'Error communicating with authentication server');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [roleFilter]);

  const handleToggleActive = async (user: UserAccountItem) => {
    setTogglingId(user.id);
    setSuccessMessage(null);
    try {
      const res = await apiCall(`/api/v1/auth/users/${user.id}/toggle-active`, {
        method: 'POST'
      });
      if (res.ok) {
        setUsers(prev =>
          prev.map(u => (u.id === user.id ? { ...u, is_active: !u.is_active } : u))
        );
        setSuccessMessage(`Account for ${user.full_name} (${user.email}) successfully ${!user.is_active ? 'activated' : 'deactivated'}.`);
        setTimeout(() => setSuccessMessage(null), 4000);
      } else {
        alert(res.error || 'Failed to update account status');
      }
    } catch (err: any) {
      alert(err?.message || 'Network error updating user account');
    } finally {
      setTogglingId(null);
    }
  };

  const filteredUsers = users.filter(user => {
    const q = searchQuery.toLowerCase();
    return (
      (user.full_name && user.full_name.toLowerCase().includes(q)) ||
      (user.email && user.email.toLowerCase().includes(q)) ||
      (user.hospital_name && user.hospital_name.toLowerCase().includes(q)) ||
      (user.role && user.role.toLowerCase().includes(q))
    );
  });

  const counts = {
    total: users.length,
    patient: users.filter(u => u.role === 'PATIENT').length,
    doctor: users.filter(u => u.role === 'DOCTOR').length,
    hospitalStaff: users.filter(u => u.role === 'HOSPITAL_ADMIN' || u.role === 'HOSPITAL_STAFF').length,
    platformAdmin: users.filter(u => u.role === 'PLATFORM_ADMIN').length,
    active: users.filter(u => u.is_active).length,
    inactive: users.filter(u => !u.is_active).length
  };

  const getRoleBadge = (role: string) => {
    switch (role.toUpperCase()) {
      case 'PATIENT':
        return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
      case 'DOCTOR':
        return 'bg-sky-500/10 text-sky-400 border border-sky-500/20';
      case 'HOSPITAL_ADMIN':
        return 'bg-purple-500/10 text-purple-400 border border-purple-500/20';
      case 'HOSPITAL_STAFF':
        return 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20';
      case 'PLATFORM_ADMIN':
        return 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
      default:
        return 'bg-slate-700 text-slate-300';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold text-amber-400 uppercase tracking-widest">
            <KeyRound className="w-4 h-4" />
            <span>Platform Governance &bull; RBAC &bull; Identity Protection</span>
          </div>
          <h2 className="text-2xl font-black text-white mt-1">User Authentication Directory</h2>
          <p className="text-sm text-slate-400">
            Real-time identity verification, role-based access control, Google OAuth &amp; local account administration.
          </p>
        </div>
        <button
          onClick={fetchUsers}
          disabled={isLoading}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs transition border border-slate-700"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-amber-400' : ''}`} />
          <span>Refresh Users</span>
        </button>
      </div>

      {/* Success Notification */}
      {successMessage && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 flex items-center space-x-3 text-emerald-300 text-sm font-semibold">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-slate-400 font-semibold">Total Accounts</div>
          <div className="text-2xl font-black text-white mt-1">{counts.total}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Across all roles</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-emerald-400 font-semibold">Patients</div>
          <div className="text-2xl font-black text-emerald-300 mt-1">{counts.patient}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Consumer profiles</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-sky-400 font-semibold">Doctors</div>
          <div className="text-2xl font-black text-sky-300 mt-1">{counts.doctor}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Clinical providers</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-purple-400 font-semibold">Hospital Admins</div>
          <div className="text-2xl font-black text-purple-300 mt-1">{counts.hospitalStaff}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Facility operators</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-amber-400 font-semibold">Platform Admins</div>
          <div className="text-2xl font-black text-amber-300 mt-1">{counts.platformAdmin}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">System engineers</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-slate-400 font-semibold">Account Status</div>
          <div className="text-sm font-bold text-white mt-1">
            <span className="text-emerald-400">{counts.active} Active</span> /{' '}
            <span className="text-rose-400">{counts.inactive} Inactive</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">RBAC access state</div>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        {/* Role Filters */}
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 md:pb-0">
          <Filter className="w-4 h-4 text-slate-500 mr-1 flex-shrink-0" />
          {['ALL', 'PATIENT', 'DOCTOR', 'HOSPITAL_ADMIN', 'HOSPITAL_STAFF', 'PLATFORM_ADMIN'].map(role => (
            <button
              key={role}
              onClick={() => setRoleFilter(role)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap ${
                roleFilter === role
                  ? 'bg-amber-500 text-slate-950 shadow'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {role === 'ALL' ? 'All Roles' : role.replace('_', ' ')}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative min-w-[280px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by name, email, or hospital..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white focus:outline-none focus:border-amber-500 transition"
          />
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-2xl p-5 text-rose-300 text-sm flex items-center space-x-3">
          <XCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Users Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {isLoading ? (
          <div className="p-12 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
            <RefreshCw className="w-8 h-8 animate-spin text-amber-400" />
            <p className="text-sm font-semibold">Loading registered authentication records...</p>
          </div>
        ) : filteredUsers.length === 0 ? (
          <div className="p-12 text-center text-slate-400 flex flex-col items-center justify-center space-y-2">
            <Users className="w-10 h-10 text-slate-600 mb-1" />
            <p className="text-base font-bold text-slate-200">No user accounts found</p>
            <p className="text-xs text-slate-500">
              {searchQuery ? `No matches for query "${searchQuery}".` : 'No users registered under this filter yet.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-950/80 border-b border-slate-800 text-[11px] uppercase tracking-wider text-slate-400 font-bold">
                  <th className="py-3.5 px-4">User</th>
                  <th className="py-3.5 px-4">Role</th>
                  <th className="py-3.5 px-4">Affiliation / Facility</th>
                  <th className="py-3.5 px-4">Auth Provider</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs">
                {filteredUsers.map(user => (
                  <tr key={user.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-4 px-4">
                      <div className="font-bold text-white text-sm">{user.full_name || 'Unnamed User'}</div>
                      <div className="text-slate-400 flex items-center space-x-1 mt-0.5">
                        <Mail className="w-3 h-3 text-slate-500" />
                        <span>{user.email}</span>
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-bold ${getRoleBadge(user.role)}`}>
                        <Shield className="w-3 h-3 mr-1" />
                        {user.role.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-slate-300">
                      {user.hospital_name ? (
                        <div className="flex items-center space-x-1.5 font-medium">
                          <Building2 className="w-3.5 h-3.5 text-indigo-400" />
                          <span>{user.hospital_name}</span>
                        </div>
                      ) : (
                        <span className="text-slate-500 italic">Statewide / Not Hospital-Bound</span>
                      )}
                    </td>
                    <td className="py-4 px-4">
                      {user.auth_provider === 'GOOGLE' ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20 text-[11px] font-bold">
                          Google OAuth
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700 text-[11px] font-semibold">
                          Local Password
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-4">
                      {user.is_active ? (
                        <span className="inline-flex items-center space-x-1 text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20 text-[11px]">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Active</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 text-rose-400 font-bold bg-rose-500/10 px-2 py-0.5 rounded-md border border-rose-500/20 text-[11px]">
                          <XCircle className="w-3 h-3" />
                          <span>Suspended</span>
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-4 text-right">
                      <button
                        onClick={() => handleToggleActive(user)}
                        disabled={togglingId === user.id}
                        className={`px-3 py-1.5 rounded-lg text-[11px] font-bold transition inline-flex items-center space-x-1.5 ${
                          user.is_active
                            ? 'bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30'
                            : 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        }`}
                      >
                        {togglingId === user.id ? (
                          <RefreshCw className="w-3 h-3 animate-spin" />
                        ) : user.is_active ? (
                          <>
                            <UserX className="w-3 h-3" />
                            <span>Deactivate</span>
                          </>
                        ) : (
                          <>
                            <UserCheck className="w-3 h-3" />
                            <span>Activate</span>
                          </>
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
