import React, { useState, useEffect } from 'react';
import { authAPI } from '../api/client';
import { 
  ShieldCheck, 
  Users, 
  GraduationCap, 
  Building2, 
  Clock, 
  Database, 
  FileCheck2,
  AlertCircle,
  Loader2
} from 'lucide-react';

export const AdminPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const data = await authAPI.getAdminUsers();
        setUsers(data);
      } catch (err) {
        setError('Admin access required or error fetching candidates list.');
      } finally {
        setLoading(false);
      }
    };
    fetchUsers();
  }, []);

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-purple-950/20 border border-purple-500/20">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ShieldCheck className="w-5 h-5 text-purple-400" />
            <h1 className="text-xl font-bold text-white tracking-tight">
              Admin Governance & Platform Telemetry
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Designated for final scope: Multi-candidate analytics, batch administration, and faculty insights.
          </p>
        </div>

        <div className="px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-xs font-semibold self-start sm:self-auto">
          Final Scope Feature
        </div>
      </div>

      {/* Admin Quick Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Total Registered Candidates</span>
            <Users className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-bold text-white mt-2">{loading ? '...' : users.length || 1}</p>
        </div>

        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Target Batch</span>
            <GraduationCap className="w-4 h-4 text-purple-400" />
          </div>
          <p className="text-2xl font-bold text-white mt-2">7th Sem (2026)</p>
        </div>

        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Active Intelligence Engines</span>
            <Database className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold text-white mt-2">5 Modules</p>
        </div>
      </div>

      {/* Candidates List Preview */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-sm font-bold text-white">Registered Candidates Roster</h2>
          <span className="text-xs text-slate-400">Live DB Records</span>
        </div>

        {loading ? (
          <div className="p-8 flex items-center justify-center text-slate-400 text-xs gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
            Loading candidates...
          </div>
        ) : error ? (
          <div className="p-6 text-center text-xs text-slate-400">
            <AlertCircle className="w-5 h-5 text-amber-400 mx-auto mb-2" />
            <p>{error}</p>
            <p className="text-[11px] text-slate-500 mt-1">
              Admin endpoints require an account with <code className="text-purple-400 font-mono">is_admin = True</code> in PostgreSQL/database.
            </p>
          </div>
        ) : users.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-400">
            No candidates registered yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider font-semibold">
                <tr>
                  <th className="px-4 py-3">Candidate</th>
                  <th className="px-4 py-3">College & Branch</th>
                  <th className="px-4 py-3">Semester</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Registered At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-850">
                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-200">{u.full_name}</div>
                      <div className="text-[11px] text-slate-400">{u.email}</div>
                    </td>
                    <td className="px-4 py-3 text-slate-300">
                      {u.college || 'N/A'} · {u.branch || 'CSE'}
                    </td>
                    <td className="px-4 py-3 text-slate-300">Sem {u.semester}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        u.is_admin ? 'bg-purple-500/20 text-purple-400' : 'bg-slate-800 text-slate-300'
                      }`}>
                        {u.is_admin ? 'Admin' : 'Student'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400 font-mono text-[11px]">
                      {new Date(u.created_at).toLocaleDateString()}
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
