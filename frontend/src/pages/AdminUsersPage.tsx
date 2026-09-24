import React, { useState, useEffect, useCallback } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Filter,
  RefreshCw,
  Search,
  Shield,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
  UserX,
  Users,
} from 'lucide-react';
import { Button } from '../components/common/Button';
import { getAdminUsers, updateUserRole } from '../services/api';
import { UserAdminRead, UserRole } from '../types';

export const AdminUsersPage: React.FC = () => {
  const [users, setUsers] = useState<UserAdminRead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<'ALL' | 'USER' | 'MODERATOR' | 'ADMIN'>('ALL');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Modal / Confirm state for role update
  const [pendingAction, setPendingAction] = useState<{
    user: UserAdminRead;
    targetRole: 'USER' | 'MODERATOR';
  } | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await getAdminUsers({
        search: searchQuery.trim() || undefined,
        role: roleFilter !== 'ALL' ? roleFilter : undefined,
      });
      setUsers(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load user management list.');
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, roleFilter]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleRoleChangeConfirm = async () => {
    if (!pendingAction) return;
    setIsUpdating(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const updated = await updateUserRole(pendingAction.user.id, pendingAction.targetRole);
      setSuccessMessage(
        `Successfully updated ${updated.name || updated.email} to ${updated.role}.`
      );
      setPendingAction(null);
      await fetchUsers();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to update user role.');
    } finally {
      setIsUpdating(false);
    }
  };

  const getRoleBadge = (role: UserRole) => {
    switch (role) {
      case 'ADMIN':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <ShieldAlert className="w-3 h-3" />
            ADMIN
          </span>
        );
      case 'MODERATOR':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <ShieldCheck className="w-3 h-3" />
            MODERATOR
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-zinc-800 text-zinc-300 border border-zinc-700">
            USER
          </span>
        );
    }
  };

  return (
    <div className="py-8 px-4 max-w-5xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-zinc-800/80">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <Users className="w-4 h-4" />
            </div>
            <h1 className="text-xl font-semibold tracking-tight text-zinc-100">
              User Management
            </h1>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            Grant and revoke moderator permissions across registered platform accounts.
          </p>
        </div>

        <button
          onClick={() => fetchUsers()}
          disabled={isLoading}
          className="self-start sm:self-auto px-3 py-1.5 rounded-md border border-zinc-800 bg-zinc-900/60 hover:bg-zinc-800 text-xs font-medium text-zinc-300 transition-colors flex items-center gap-1.5 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Messages */}
      {errorMessage && (
        <div className="p-3 rounded-md bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
          <span>{errorMessage}</span>
        </div>
      )}

      {successMessage && (
        <div className="p-3 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-start gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400 mt-0.5" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Filter / Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            placeholder="Search users by name, username, or email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-md bg-zinc-900/60 border border-zinc-800 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors"
          />
        </div>

        <div className="flex items-center gap-1 bg-zinc-900/60 p-1 rounded-md border border-zinc-800 self-start sm:self-auto">
          <Filter className="w-3.5 h-3.5 text-zinc-500 ml-2 mr-1" />
          {(['ALL', 'USER', 'MODERATOR', 'ADMIN'] as const).map((r) => (
            <button
              key={r}
              onClick={() => setRoleFilter(r)}
              className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
                roleFilter === r
                  ? 'bg-zinc-800 text-white shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              {r === 'ALL' ? 'All Roles' : r}
            </button>
          ))}
        </div>
      </div>

      {/* Users Table */}
      <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-900/60 border-b border-zinc-800 text-zinc-400 font-mono">
              <tr>
                <th className="py-3 px-4 font-medium">User Profile</th>
                <th className="py-3 px-4 font-medium">Role</th>
                <th className="py-3 px-4 font-medium">Status</th>
                <th className="py-3 px-4 font-medium">Joined</th>
                <th className="py-3 px-4 font-medium text-right">Moderator Access</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {isLoading && users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-zinc-500 font-mono">
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-4 h-4 border-2 border-zinc-400 border-t-transparent rounded-full animate-spin" />
                      Loading user accounts...
                    </div>
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-zinc-500">
                    No users found matching your search filters.
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id} className="hover:bg-zinc-900/30 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-medium text-zinc-100">{u.name || u.username}</div>
                      <div className="text-[11px] text-zinc-400 font-mono">{u.email}</div>
                    </td>
                    <td className="py-3 px-4">{getRoleBadge(u.role)}</td>
                    <td className="py-3 px-4">
                      {u.is_active ? (
                        <span className="text-emerald-400 font-medium">Active</span>
                      ) : (
                        <span className="text-rose-400 font-medium">Inactive</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-zinc-400 font-mono">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {u.role === 'ADMIN' ? (
                        <span className="text-[11px] text-purple-400/80 font-mono italic">
                          Protected System Admin
                        </span>
                      ) : u.role === 'MODERATOR' ? (
                        <button
                          onClick={() =>
                            setPendingAction({ user: u, targetRole: 'USER' })
                          }
                          className="px-2.5 py-1 rounded border border-rose-500/20 bg-rose-500/10 text-rose-300 hover:bg-rose-500/20 text-xs font-medium transition-colors inline-flex items-center gap-1.5"
                        >
                          <UserX className="w-3.5 h-3.5 text-rose-400" />
                          Revoke Moderator
                        </button>
                      ) : (
                        <button
                          onClick={() =>
                            setPendingAction({ user: u, targetRole: 'MODERATOR' })
                          }
                          className="px-2.5 py-1 rounded border border-emerald-500/20 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20 text-xs font-medium transition-colors inline-flex items-center gap-1.5"
                        >
                          <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
                          Grant Moderator
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Confirmation Modal */}
      {pendingAction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div
                className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                  pendingAction.targetRole === 'MODERATOR'
                    ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                    : 'bg-rose-500/10 border border-rose-500/20 text-rose-400'
                }`}
              >
                <Shield className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-white">
                  {pendingAction.targetRole === 'MODERATOR'
                    ? 'Grant Moderator Permissions'
                    : 'Revoke Moderator Permissions'}
                </h3>
                <p className="text-xs text-zinc-400">
                  Confirm role change for this platform user.
                </p>
              </div>
            </div>

            <div className="p-3 bg-zinc-950/60 rounded-lg border border-zinc-800/80 text-xs font-mono space-y-1">
              <div>User: <span className="text-zinc-200">{pendingAction.user.name || pendingAction.user.username}</span></div>
              <div>Email: <span className="text-zinc-200">{pendingAction.user.email}</span></div>
              <div>Current Role: <span className="text-zinc-300">{pendingAction.user.role}</span></div>
              <div>New Role: <span className="text-emerald-400 font-bold">{pendingAction.targetRole}</span></div>
            </div>

            <p className="text-xs text-zinc-300 leading-relaxed">
              {pendingAction.targetRole === 'MODERATOR'
                ? 'This user will immediately be granted access to view reports, inspect evidence files, and post timeline status updates.'
                : 'This user will immediately lose access to moderator queues and status update endpoints.'}
            </p>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setPendingAction(null)}
                disabled={isUpdating}
                className="px-3 py-1.5 rounded-lg border border-zinc-700 hover:bg-zinc-800 text-xs font-medium text-zinc-300 transition-colors"
              >
                Cancel
              </button>
              <Button
                variant={pendingAction.targetRole === 'MODERATOR' ? 'primary' : 'danger'}
                size="sm"
                isLoading={isUpdating}
                onClick={handleRoleChangeConfirm}
              >
                Confirm Role Change
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
