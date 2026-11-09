import React, { useState, useEffect } from 'react';
import { adminAPI, jobAPI, dsaAPI } from '../api/client';
import {
  ShieldCheck,
  Users,
  Briefcase,
  Code2,
  Mic,
  Compass,
  FileText,
  BarChart3,
  TrendingUp,
  AlertCircle,
  Loader2,
  Plus,
  Trash2,
  Search,
  CheckCircle2,
  XCircle,
  Filter,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  Sparkles,
} from 'lucide-react';

export const AdminPage = () => {
  const [activeTab, setActiveTab] = useState('telemetry'); // 'telemetry' | 'users' | 'jobs' | 'dsa'
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState(null);

  // Users state
  const [users, setUsers] = useState([]);
  const [userSearch, setUserSearch] = useState('');
  const [actionLoadingUser, setActionLoadingUser] = useState(null);

  // Jobs state
  const [jobs, setJobs] = useState([]);
  const [jobSearch, setJobSearch] = useState('');
  const [showAddJobModal, setShowAddJobModal] = useState(false);
  const [submittingJob, setSubmittingJob] = useState(false);
  const [newJob, setNewJob] = useState({
    title: '',
    company: '',
    description: '',
    responsibilities: '',
    required_skills: '',
    preferred_skills: '',
    experience_level: 'Fresher / Entry Level',
    location: 'Bengaluru / Hybrid',
    employment_type: 'Full-time',
    salary_range: '₹8,00,000 - ₹14,00,000 PA',
    is_active: true,
    is_synthetic: true,
  });

  // DSA Questions state
  const [dsaQuestions, setDsaQuestions] = useState([]);
  const [dsaSearch, setDsaSearch] = useState('');
  const [showAddDsaModal, setShowAddDsaModal] = useState(false);
  const [submittingDsa, setSubmittingDsa] = useState(false);
  const [newDsa, setNewDsa] = useState({
    title: '',
    slug: '',
    category: 'Arrays',
    difficulty: 'Easy',
    description: '',
    constraints: '1 <= nums.length <= 10^5\n-10^9 <= nums[i] <= 10^9',
    starter_code: 'def solution(nums):\n    # Write your solution here\n    pass',
    test_case_input: '[1, 2, 3]',
    test_case_expected: '3',
  });

  const fetchAllAdminData = async () => {
    setLoading(true);
    setError('');
    try {
      const [statsData, usersData, jobsData, dsaData] = await Promise.all([
        adminAPI.getStats().catch(() => null),
        adminAPI.getUsers().catch(() => []),
        jobAPI.listJobs({ limit: 100 }).catch(() => ({ items: [] })),
        dsaAPI.listQuestions({ limit: 100 }).catch(() => ({ items: [] })),
      ]);

      if (statsData) setStats(statsData);
      setUsers(usersData || []);
      setJobs(jobsData.items || jobsData.jobs || []);
      setDsaQuestions(dsaData.items || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load administrative platform data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllAdminData();
  }, []);

  // User status toggle
  const handleToggleUserStatus = async (userId) => {
    setActionLoadingUser(userId);
    try {
      const updated = await adminAPI.toggleUserStatus(userId);
      setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, is_active: updated.is_active } : u)));
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update user account status.');
    } finally {
      setActionLoadingUser(null);
    }
  };

  // Job creation
  const handleCreateJob = async (e) => {
    e.preventDefault();
    setSubmittingJob(true);
    try {
      const reqSkills = newJob.required_skills
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      const prefSkills = newJob.preferred_skills
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      const resps = newJob.responsibilities
        .split('\n')
        .map((r) => r.trim())
        .filter(Boolean);

      const payload = {
        title: newJob.title,
        company: newJob.company,
        description: newJob.description,
        responsibilities: resps.length > 0 ? resps : ['Collaborate with engineering team to build scalable software.'],
        required_skills: reqSkills,
        preferred_skills: prefSkills,
        experience_level: newJob.experience_level,
        location: newJob.location,
        employment_type: newJob.employment_type,
        salary_range: newJob.salary_range,
        is_active: newJob.is_active,
        is_synthetic: newJob.is_synthetic,
      };

      const created = await jobAPI.createJob(payload);
      setJobs((prev) => [created, ...prev]);
      setShowAddJobModal(false);
      setNewJob({
        title: '',
        company: '',
        description: '',
        responsibilities: '',
        required_skills: '',
        preferred_skills: '',
        experience_level: 'Fresher / Entry Level',
        location: 'Bengaluru / Hybrid',
        employment_type: 'Full-time',
        salary_range: '₹8,00,000 - ₹14,00,000 PA',
        is_active: true,
        is_synthetic: true,
      });
      // Refresh stats
      const newStats = await adminAPI.getStats().catch(() => null);
      if (newStats) setStats(newStats);
    } catch (err) {
      alert(err.response?.data?.detail || 'Error creating job posting.');
    } finally {
      setSubmittingJob(false);
    }
  };

  // Job deletion
  const handleDeleteJob = async (jobId) => {
    if (!window.confirm('Are you sure you want to delete this job posting?')) return;
    try {
      await jobAPI.deleteJob(jobId);
      setJobs((prev) => prev.filter((j) => j.id !== jobId));
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete job.');
    }
  };

  // DSA creation
  const handleCreateDsa = async (e) => {
    e.preventDefault();
    setSubmittingDsa(true);
    try {
      const slugVal =
        newDsa.slug.trim() ||
        newDsa.title
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/(^-|-$)+/g, '');

      let parsedInput, parsedExpected;
      try {
        parsedInput = JSON.parse(newDsa.test_case_input);
      } catch {
        parsedInput = newDsa.test_case_input;
      }
      try {
        parsedExpected = JSON.parse(newDsa.test_case_expected);
      } catch {
        parsedExpected = newDsa.test_case_expected;
      }

      const payload = {
        title: newDsa.title,
        slug: slugVal,
        category: newDsa.category,
        difficulty: newDsa.difficulty,
        description: newDsa.description,
        constraints: newDsa.constraints.split('\n').filter(Boolean),
        examples: [
          {
            input: newDsa.test_case_input,
            output: newDsa.test_case_expected,
            explanation: 'Sample visible execution case.',
          },
        ],
        starter_code: {
          python: newDsa.starter_code,
        },
        test_cases: [
          {
            input: parsedInput,
            expected_output: parsedExpected,
            is_hidden: false,
          },
        ],
        time_limit_ms: 2000,
        memory_limit_mb: 128,
        is_active: true,
      };

      const created = await dsaAPI.createQuestion(payload);
      setDsaQuestions((prev) => [created, ...prev]);
      setShowAddDsaModal(false);
      setNewDsa({
        title: '',
        slug: '',
        category: 'Arrays',
        difficulty: 'Easy',
        description: '',
        constraints: '1 <= nums.length <= 10^5',
        starter_code: 'def solution(nums):\n    # Write your solution here\n    pass',
        test_case_input: '[1, 2, 3]',
        test_case_expected: '3',
      });
      // Refresh stats
      const newStats = await adminAPI.getStats().catch(() => null);
      if (newStats) setStats(newStats);
    } catch (err) {
      alert(err.response?.data?.detail || 'Error creating DSA question.');
    } finally {
      setSubmittingDsa(false);
    }
  };

  // DSA deletion
  const handleDeleteDsa = async (questionId) => {
    if (!window.confirm('Are you sure you want to delete this DSA question?')) return;
    try {
      await dsaAPI.deleteQuestion(questionId);
      setDsaQuestions((prev) => prev.filter((q) => q.id !== questionId));
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete DSA question.');
    }
  };

  const filteredUsers = users.filter((u) => {
    const q = userSearch.toLowerCase();
    return (
      u.full_name?.toLowerCase().includes(q) ||
      u.email?.toLowerCase().includes(q) ||
      u.college?.toLowerCase().includes(q) ||
      u.branch?.toLowerCase().includes(q)
    );
  });

  const filteredJobs = jobs.filter((j) => {
    const q = jobSearch.toLowerCase();
    return (
      j.title?.toLowerCase().includes(q) ||
      j.company?.toLowerCase().includes(q) ||
      j.location?.toLowerCase().includes(q)
    );
  });

  const filteredDsa = dsaQuestions.filter((d) => {
    const q = dsaSearch.toLowerCase();
    return (
      d.title?.toLowerCase().includes(q) ||
      d.category?.toLowerCase().includes(q) ||
      d.difficulty?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6 pb-12">
      {/* ── Top Governance Banner ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-purple-950/40 via-indigo-950/30 to-slate-900 border border-purple-500/20">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ShieldCheck className="w-6 h-6 text-purple-400" />
            <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              Admin Governance & Platform Telemetry
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Institutional management panel: Student roster, curriculum opportunities, and full-stack placement telemetry.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchAllAdminData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 text-xs font-semibold transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <span className="px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-xs font-semibold">
            Institutional Admin
          </span>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* ── Navigation Tabs ── */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab('telemetry')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all shrink-0 ${
            activeTab === 'telemetry'
              ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          <span>Platform Telemetry</span>
        </button>

        <button
          onClick={() => setActiveTab('users')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all shrink-0 ${
            activeTab === 'users'
              ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Candidate Roster ({users.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('jobs')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all shrink-0 ${
            activeTab === 'jobs'
              ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <Briefcase className="w-4 h-4" />
          <span>Job Postings ({jobs.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('dsa')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all shrink-0 ${
            activeTab === 'dsa'
              ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <Code2 className="w-4 h-4" />
          <span>DSA Questions ({dsaQuestions.length})</span>
        </button>
      </div>

      {/* ════════════════ TAB 1: TELEMETRY ════════════════ */}
      {activeTab === 'telemetry' && (
        <div className="space-y-6">
          {/* Key Metric Tiles */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[11px] font-medium">Students</span>
                <Users className="w-3.5 h-3.5 text-indigo-400" />
              </div>
              <p className="text-xl font-bold text-white">{stats ? stats.total_students : users.length}</p>
              <p className="text-[10px] text-slate-500 mt-1">Total Registered</p>
            </div>

            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[11px] font-medium">Resumes</span>
                <FileText className="w-3.5 h-3.5 text-blue-400" />
              </div>
              <p className="text-xl font-bold text-white">{stats?.total_resumes ?? 0}</p>
              <p className="text-[10px] text-slate-500 mt-1">Avg Score: {stats?.avg_resume_score ?? 0}%</p>
            </div>

            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[11px] font-medium">Job Matches</span>
                <Briefcase className="w-3.5 h-3.5 text-purple-400" />
              </div>
              <p className="text-xl font-bold text-white">{stats?.total_matches ?? 0}</p>
              <p className="text-[10px] text-slate-500 mt-1">Avg Match: {stats?.avg_match_score ?? 0}%</p>
            </div>

            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[11px] font-medium">DSA Accuracy</span>
                <Code2 className="w-3.5 h-3.5 text-pink-400" />
              </div>
              <p className="text-xl font-bold text-white">{stats?.dsa_accuracy_pct ?? 0}%</p>
              <p className="text-[10px] text-slate-500 mt-1">{stats?.total_dsa_submissions ?? 0} Submissions</p>
            </div>

            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[11px] font-medium">Interviews</span>
                <Mic className="w-3.5 h-3.5 text-emerald-400" />
              </div>
              <p className="text-xl font-bold text-white">{stats?.total_interviews ?? 0}</p>
              <p className="text-[10px] text-slate-500 mt-1">Avg Score: {stats?.avg_interview_score ?? 0}%</p>
            </div>

            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[11px] font-medium">Roadmaps</span>
                <Compass className="w-3.5 h-3.5 text-amber-400" />
              </div>
              <p className="text-xl font-bold text-white">{stats?.total_roadmaps ?? 0}</p>
              <p className="text-[10px] text-slate-500 mt-1">Active Plans</p>
            </div>
          </div>

          {/* Readiness Distribution Analytics */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  Candidate Placement Readiness Distribution
                </h3>
                <p className="text-xs text-slate-400">Institutional tier breakdown computed by PlacementReadinessEngine</p>
              </div>
              <span className="text-[11px] text-slate-500 font-mono">Live Aggregation</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/20">
                <div className="flex justify-between items-center text-xs mb-2">
                  <span className="font-semibold text-emerald-400">Tier 1: Placement Ready (&gt;= 75%)</span>
                  <span className="font-bold text-white">{stats?.readiness_distribution?.tier1_ready ?? 0}</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-emerald-500 h-full rounded-full transition-all"
                    style={{
                      width: `${
                        ((stats?.readiness_distribution?.tier1_ready ?? 0) /
                          Math.max(1, (stats?.total_students ?? 1))) *
                        100
                      }%`,
                    }}
                  />
                </div>
                <p className="text-[10px] text-slate-400 mt-2">Qualified for top-tier product and high-volume placement drives.</p>
              </div>

              <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/20">
                <div className="flex justify-between items-center text-xs mb-2">
                  <span className="font-semibold text-indigo-400">Tier 2: Approaching (50% - 74%)</span>
                  <span className="font-bold text-white">{stats?.readiness_distribution?.tier2_approaching ?? 0}</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-indigo-500 h-full rounded-full transition-all"
                    style={{
                      width: `${
                        ((stats?.readiness_distribution?.tier2_approaching ?? 0) /
                          Math.max(1, (stats?.total_students ?? 1))) *
                        100
                      }%`,
                    }}
                  />
                </div>
                <p className="text-[10px] text-slate-400 mt-2">Needs 1-2 weeks of focused DSA problem solving and mock interview practice.</p>
              </div>

              <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-500/20">
                <div className="flex justify-between items-center text-xs mb-2">
                  <span className="font-semibold text-amber-400">Tier 3: Needs Prep (&lt; 50%)</span>
                  <span className="font-bold text-white">{stats?.readiness_distribution?.tier3_needs_prep ?? 0}</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-amber-500 h-full rounded-full transition-all"
                    style={{
                      width: `${
                        ((stats?.readiness_distribution?.tier3_needs_prep ?? 0) /
                          Math.max(1, (stats?.total_students ?? 1))) *
                        100
                      }%`,
                    }}
                  />
                </div>
                <p className="text-[10px] text-slate-400 mt-2">Requires foundational project enhancement and core skill curriculum review.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ════════════════ TAB 2: CANDIDATE ROSTER ════════════════ */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="text"
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
                placeholder="Search candidates by name, email, college, or branch..."
                className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500"
              />
            </div>
            <span className="text-xs text-slate-400">
              Showing {filteredUsers.length} of {users.length} candidates
            </span>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider font-semibold">
                  <tr>
                    <th className="px-4 py-3">Candidate</th>
                    <th className="px-4 py-3">College & Branch</th>
                    <th className="px-4 py-3">Semester</th>
                    <th className="px-4 py-3">Role</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Registered At</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {filteredUsers.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-8 text-center text-slate-500 text-xs">
                        No candidates match the search criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredUsers.map((u) => (
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
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                              u.is_admin ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30' : 'bg-slate-800 text-slate-300'
                            }`}
                          >
                            {u.is_admin ? 'Admin' : 'Student'}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-semibold flex items-center gap-1 w-max ${
                              u.is_active
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            }`}
                          >
                            {u.is_active ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                            <span>{u.is_active ? 'Active' : 'Disabled'}</span>
                          </span>
                        </td>
                        <td className="px-4 py-3 text-slate-400 font-mono text-[11px]">
                          {new Date(u.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => handleToggleUserStatus(u.id)}
                            disabled={actionLoadingUser === u.id}
                            className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                              u.is_active
                                ? 'bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/40'
                                : 'bg-emerald-950/40 hover:bg-emerald-900/60 text-emerald-300 border border-emerald-800/40'
                            }`}
                          >
                            {actionLoadingUser === u.id ? 'Updating...' : u.is_active ? 'Disable' : 'Enable'}
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ════════════════ TAB 3: JOB MANAGEMENT ════════════════ */}
      {activeTab === 'jobs' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="text"
                value={jobSearch}
                onChange={(e) => setJobSearch(e.target.value)}
                placeholder="Search job postings by title, company, or location..."
                className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500"
              />
            </div>
            <button
              onClick={() => setShowAddJobModal(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-lg shadow-purple-600/20 transition-all shrink-0"
            >
              <Plus className="w-4 h-4" />
              <span>Add Job Opportunity</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredJobs.length === 0 ? (
              <div className="col-span-2 p-8 text-center text-slate-500 text-xs bg-slate-900/40 border border-slate-800 rounded-2xl">
                No job postings found matching search.
              </div>
            ) : (
              filteredJobs.map((job) => (
                <div
                  key={job.id}
                  className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between hover:border-slate-700 transition-all"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div>
                        <h4 className="text-sm font-bold text-white">{job.title}</h4>
                        <p className="text-xs text-indigo-400 font-medium">{job.company}</p>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {job.is_synthetic && (
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                            Synthetic
                          </span>
                        )}
                        <button
                          onClick={() => handleDeleteJob(job.id)}
                          className="p-1 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 transition-all"
                          title="Delete Job"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <p className="text-xs text-slate-400 line-clamp-2 mb-3">{job.description}</p>

                    <div className="flex flex-wrap gap-1.5 mb-3">
                      {(job.required_skills || []).slice(0, 5).map((s, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-medium"
                        >
                          {s}
                        </span>
                      ))}
                      {(job.required_skills || []).length > 5 && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-500">
                          +{(job.required_skills || []).length - 5}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                    <span>{job.location} · {job.employment_type}</span>
                    <span className="text-indigo-300 font-semibold">{job.salary_range}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* ════════════════ TAB 4: DSA QUESTION BANK ════════════════ */}
      {activeTab === 'dsa' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="text"
                value={dsaSearch}
                onChange={(e) => setDsaSearch(e.target.value)}
                placeholder="Search DSA challenges by title, category, difficulty..."
                className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500"
              />
            </div>
            <button
              onClick={() => setShowAddDsaModal(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-lg shadow-purple-600/20 transition-all shrink-0"
            >
              <Plus className="w-4 h-4" />
              <span>Add DSA Challenge</span>
            </button>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider font-semibold">
                <tr>
                  <th className="px-4 py-3">Title & Slug</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Difficulty</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {filteredDsa.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-slate-500 text-xs">
                      No DSA questions found.
                    </td>
                  </tr>
                ) : (
                  filteredDsa.map((q) => (
                    <tr key={q.id} className="hover:bg-slate-850">
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-200">{q.title}</div>
                        <div className="text-[11px] text-slate-500 font-mono">{q.slug}</div>
                      </td>
                      <td className="px-4 py-3 text-slate-300">{q.category}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            q.difficulty === 'Easy'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : q.difficulty === 'Medium'
                              ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}
                        >
                          {q.difficulty}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                          Active
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleDeleteDsa(q.id)}
                          className="p-1 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 transition-all"
                          title="Delete Question"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ════════════════ ADD JOB MODAL ════════════════ */}
      {showAddJobModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl p-6 space-y-4 my-8">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-purple-400" />
                Add Institutional Placement Opportunity
              </h3>
              <button
                onClick={() => setShowAddJobModal(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateJob} className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Job Title *</label>
                  <input
                    type="text"
                    required
                    value={newJob.title}
                    onChange={(e) => setNewJob({ ...newJob, title: e.target.value })}
                    placeholder="e.g. SDE-1 / AI Engineer"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Company Name *</label>
                  <input
                    type="text"
                    required
                    value={newJob.company}
                    onChange={(e) => setNewJob({ ...newJob, company: e.target.value })}
                    placeholder="e.g. CloudTech Systems"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Description *</label>
                <textarea
                  rows={3}
                  required
                  value={newJob.description}
                  onChange={(e) => setNewJob({ ...newJob, description: e.target.value })}
                  placeholder="Overview of the vacancy, engineering domain, and deliverables..."
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Required Skills (comma-separated) *
                </label>
                <input
                  type="text"
                  required
                  value={newJob.required_skills}
                  onChange={(e) => setNewJob({ ...newJob, required_skills: e.target.value })}
                  placeholder="Python, FastAPI, PostgreSQL, Docker, Data Structures"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Preferred Skills (comma-separated)
                </label>
                <input
                  type="text"
                  value={newJob.preferred_skills}
                  onChange={(e) => setNewJob({ ...newJob, preferred_skills: e.target.value })}
                  placeholder="Kubernetes, Machine Learning, Redis, AWS"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Location</label>
                  <input
                    type="text"
                    value={newJob.location}
                    onChange={(e) => setNewJob({ ...newJob, location: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Salary Range</label>
                  <input
                    type="text"
                    value={newJob.salary_range}
                    onChange={(e) => setNewJob({ ...newJob, salary_range: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddJobModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingJob}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold disabled:opacity-50"
                >
                  {submittingJob && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save Job Opportunity</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ════════════════ ADD DSA MODAL ════════════════ */}
      {showAddDsaModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl p-6 space-y-4 my-8">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Code2 className="w-5 h-5 text-purple-400" />
                Add DSA Coding Assessment Challenge
              </h3>
              <button
                onClick={() => setShowAddDsaModal(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateDsa} className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Title *</label>
                  <input
                    type="text"
                    required
                    value={newDsa.title}
                    onChange={(e) => setNewDsa({ ...newDsa, title: e.target.value })}
                    placeholder="e.g. Reverse Linked List"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Category *</label>
                  <select
                    value={newDsa.category}
                    onChange={(e) => setNewDsa({ ...newDsa, category: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-purple-500"
                  >
                    <option value="Arrays">Arrays</option>
                    <option value="Strings">Strings</option>
                    <option value="Linked Lists">Linked Lists</option>
                    <option value="Trees">Trees</option>
                    <option value="Graphs">Graphs</option>
                    <option value="Dynamic Programming">Dynamic Programming</option>
                    <option value="Greedy">Greedy</option>
                    <option value="Recursion">Recursion</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Difficulty *</label>
                  <select
                    value={newDsa.difficulty}
                    onChange={(e) => setNewDsa({ ...newDsa, difficulty: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-purple-500"
                  >
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Slug (optional)</label>
                  <input
                    type="text"
                    value={newDsa.slug}
                    onChange={(e) => setNewDsa({ ...newDsa, slug: e.target.value })}
                    placeholder="auto-generated from title"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-purple-500 font-mono text-[11px]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Description *</label>
                <textarea
                  rows={3}
                  required
                  value={newDsa.description}
                  onChange={(e) => setNewDsa({ ...newDsa, description: e.target.value })}
                  placeholder="Problem description, expected time/space complexity, constraints..."
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Starter Code (Python) *</label>
                <textarea
                  rows={3}
                  required
                  value={newDsa.starter_code}
                  onChange={(e) => setNewDsa({ ...newDsa, starter_code: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white font-mono text-[11px] focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Sample Input (JSON/str) *</label>
                  <input
                    type="text"
                    required
                    value={newDsa.test_case_input}
                    onChange={(e) => setNewDsa({ ...newDsa, test_case_input: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white font-mono text-[11px] focus:outline-none focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Expected Output *</label>
                  <input
                    type="text"
                    required
                    value={newDsa.test_case_expected}
                    onChange={(e) => setNewDsa({ ...newDsa, test_case_expected: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white font-mono text-[11px] focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddDsaModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingDsa}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold disabled:opacity-50"
                >
                  {submittingDsa && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save DSA Challenge</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
