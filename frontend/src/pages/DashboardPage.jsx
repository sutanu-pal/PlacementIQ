import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  systemAPI,
  resumeAPI,
  jobMatchAPI,
  dsaAPI,
  interviewAPI,
  roadmapAPI,
  readinessAPI,
} from '../api/client';
import {
  Sparkles,
  FileText,
  Briefcase,
  Code2,
  Mic,
  Compass,
  CheckCircle2,
  ArrowUpRight,
  TrendingUp,
  Brain,
  ShieldCheck,
  Cpu,
  BarChart3,
  Layers,
  AlertTriangle,
  Loader2,
  Clock,
  Target,
  Award,
} from 'lucide-react';

export const DashboardPage = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [engineHealth, setEngineHealth] = useState(null);

  // Live module signals
  const [readiness, setReadiness] = useState(null);
  const [latestResume, setLatestResume] = useState(null);
  const [matches, setMatches] = useState([]);
  const [dsaAnalytics, setDsaAnalytics] = useState(null);
  const [latestInterview, setLatestInterview] = useState(null);
  const [roadmap, setRoadmap] = useState(null);

  useEffect(() => {
    const fetchAllDashboardData = async () => {
      setLoading(true);
      try {
        const [healthRes, readinessRes, resumeRes, matchRes, dsaRes, interviewRes, roadmapRes] =
          await Promise.allSettled([
            systemAPI.getHealth(),
            readinessAPI.getReadiness(),
            resumeAPI.listResumes(),
            jobMatchAPI.listMatches({ limit: 5 }),
            dsaAPI.getAnalytics(),
            interviewAPI.listSessions({ limit: 5 }),
            roadmapAPI.getRoadmap(),
          ]);

        if (healthRes.status === 'fulfilled') setEngineHealth(healthRes.value);
        if (readinessRes.status === 'fulfilled') setReadiness(readinessRes.value);
        if (resumeRes.status === 'fulfilled' && resumeRes.value?.resumes?.length > 0) {
          setLatestResume(resumeRes.value.resumes[0]);
        }
        if (matchRes.status === 'fulfilled') setMatches(matchRes.value?.items || []);
        if (dsaRes.status === 'fulfilled') setDsaAnalytics(dsaRes.value);
        if (interviewRes.status === 'fulfilled' && interviewRes.value?.items?.length > 0) {
          setLatestInterview(interviewRes.value.items[0]);
        }
        if (roadmapRes.status === 'fulfilled') setRoadmap(roadmapRes.value);
      } finally {
        setLoading(false);
      }
    };

    fetchAllDashboardData();
  }, []);

  // Compute live module status cards
  const modules = [
    {
      id: 1,
      title: 'AI Resume Analyzer',
      description: 'PyMuPDF text extraction, section scoring, and explainable ATS skill parsing.',
      icon: FileText,
      color: 'from-blue-500 to-indigo-600',
      badge: latestResume ? `v${latestResume.version} Active` : 'Action Required',
      badgeClass: latestResume ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      href: '/resume',
      metrics: latestResume
        ? `Score: ${Math.round(latestResume.overall_score)}% · ${latestResume.extracted_skills?.length || 0} Skills`
        : 'Upload PDF to analyze',
    },
    {
      id: 2,
      title: 'Intelligent Job Matching',
      description: 'Sentence Transformers (all-MiniLM-L6-v2) semantic similarity and skill gap identification.',
      icon: Briefcase,
      color: 'from-indigo-500 to-purple-600',
      badge: matches.length > 0 ? `${matches.length} Matches` : 'Ready',
      badgeClass: matches.length > 0 ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' : 'bg-slate-800 text-slate-300 border-slate-700',
      href: '/jobs',
      metrics: matches.length > 0
        ? `Top Fit: ${Math.round(matches[0]?.match_score || 0)}% (${matches[0]?.job_title || 'Job'})`
        : 'Run NLP match against jobs',
    },
    {
      id: 3,
      title: 'DSA Assessment Engine',
      description: 'AST-sandboxed Python execution environment evaluating unit tests and complexity.',
      icon: Code2,
      color: 'from-purple-500 to-pink-600',
      badge: dsaAnalytics?.total_solved ? `${dsaAnalytics.total_solved} Solved` : 'Practice Ready',
      badgeClass: dsaAnalytics?.total_solved ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-slate-800 text-slate-300 border-slate-700',
      href: '/dsa',
      metrics: dsaAnalytics
        ? `${dsaAnalytics.total_solved} of ${dsaAnalytics.total_questions} Problems · ${dsaAnalytics.overall_accuracy_pct}% Acc`
        : '10 problems across 8 topics',
    },
    {
      id: 4,
      title: 'AI Mock Interview',
      description: 'Multi-turn STAR interview simulator with rubric evaluation powered by Gemini 2.5 Flash.',
      icon: Mic,
      color: 'from-emerald-500 to-teal-600',
      badge: latestInterview ? `${Math.round(latestInterview.overall_score)}% Score` : 'Ready to Start',
      badgeClass: latestInterview ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-slate-800 text-slate-300 border-slate-700',
      href: '/interview',
      metrics: latestInterview
        ? `Latest: ${latestInterview.role_title} (${latestInterview.status})`
        : 'Behavioral & Technical Practice',
    },
    {
      id: 5,
      title: 'Personalized Learning Roadmap',
      description: 'Cross-module skill harvester compiling automated 4-week milestones with verified URLs.',
      icon: Compass,
      color: 'from-amber-500 to-orange-600',
      badge: roadmap ? `${Math.round(roadmap.completion_pct || 0)}% Done` : 'Ready to Generate',
      badgeClass: roadmap ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-slate-800 text-slate-300 border-slate-700',
      href: '/roadmap',
      metrics: roadmap
        ? `${roadmap.current_streak_days ?? 0} Day Streak · ${roadmap.total_weeks} Week Plan`
        : 'Generate customized curriculum',
    },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* ── Top Hero Banner ── */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/70 to-slate-900 border border-slate-800/80 p-6 sm:p-8">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 blur-[90px] rounded-full pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              <span>7th Semester CSE (AI & ML) Major Project Platform</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Welcome, {user?.full_name || 'Candidate'} 👋
            </h1>
            <p className="text-sm text-slate-400 max-w-2xl leading-relaxed">
              Your placement intelligence dashboard connects all 5 specialized modules to benchmark, analyze, and accelerate your engineering placement readiness.
            </p>
          </div>

          {/* Quick Profile Pill */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 shrink-0 bg-slate-950/60 p-3.5 rounded-xl border border-slate-800">
            <div className="w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-base">
              {user?.full_name?.charAt(0) || 'S'}
            </div>
            <div className="text-xs">
              <p className="font-semibold text-slate-200">{user?.college || 'Engineering Institute'}</p>
              <p className="text-slate-400">
                {user?.branch || 'CSE (AI & ML)'} · Sem {user?.semester || 7}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Central Explainable Placement Readiness Engine ── */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-6 relative">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Brain className="w-5 h-5 text-indigo-400" />
              <h2 className="text-lg font-bold text-white tracking-tight">
                Explainable Placement Readiness Engine
              </h2>
            </div>
            <p className="text-xs text-slate-400">
              Aggregated weighted composite score computed across all 5 active intelligence dimensions
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              {loading ? (
                <div className="flex items-center gap-2 text-slate-400 text-xs">
                  <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                  Calculating...
                </div>
              ) : (
                <>
                  <div className="flex items-baseline justify-end gap-1.5">
                    <span className="text-3xl sm:text-4xl font-black text-indigo-400 tracking-tight">
                      {Math.round(readiness?.overall_score ?? 0)}%
                    </span>
                    {readiness?.is_provisional && (
                      <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        Provisional
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] font-semibold text-emerald-400 flex items-center justify-end gap-1">
                    <TrendingUp className="w-3 h-3" />
                    <span>{readiness?.readiness_tier || 'Evaluating...'}</span>
                  </p>
                </>
              )}
            </div>
          </div>
        </div>

        {/* 5-Dimension Progress Bars */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 my-6">
          {readiness?.dimension_scores
            ? Object.entries(readiness.dimension_scores).map(([dimName, dim]) => (
                <div
                  key={dimName}
                  className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex justify-between items-center text-xs mb-1.5">
                      <span className="font-semibold text-slate-300 truncate max-w-[100px]">{dimName}</span>
                      <span className="font-mono text-indigo-400 font-bold">
                        {Math.round(dim.score || 0)}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${dim.available ? 'bg-gradient-to-r from-indigo-500 to-purple-500' : 'bg-slate-700'}`}
                        style={{ width: `${Math.min(100, Math.max(0, dim.score || 0))}%` }}
                      />
                    </div>
                  </div>
                  <div className="mt-3 flex items-center justify-between text-[10px] text-slate-500">
                    <span>Wt: {Math.round((dim.weight || 0.2) * 100)}%</span>
                    <span className={`font-medium truncate max-w-[80px] ${dim.available ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {dim.available ? dim.metric_summary || 'Active' : 'Pending'}
                    </span>
                  </div>
                </div>
              ))
            : [
                { key: 'Resume Quality', score: latestResume?.overall_score || 0, weight: 0.25, available: !!latestResume },
                { key: 'Job Matching', score: matches[0]?.match_score || 0, weight: 0.25, available: matches.length > 0 },
                { key: 'DSA Assessment', score: dsaAnalytics?.overall_solve_pct || 0, weight: 0.25, available: !!dsaAnalytics },
                { key: 'Mock Interview', score: latestInterview?.overall_score || 0, weight: 0.15, available: !!latestInterview },
                { key: 'Roadmap', score: roadmap?.completion_pct || 0, weight: 0.10, available: !!roadmap },
              ].map((item) => (
                <div
                  key={item.key}
                  className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex justify-between items-center text-xs mb-1.5">
                      <span className="font-semibold text-slate-300">{item.key}</span>
                      <span className="font-mono text-indigo-400 font-bold">{Math.round(item.score)}%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${item.available ? 'bg-gradient-to-r from-indigo-500 to-purple-500' : 'bg-slate-700'}`}
                        style={{ width: `${Math.min(100, Math.max(0, item.score))}%` }}
                      />
                    </div>
                  </div>
                  <div className="mt-3 flex items-center justify-between text-[10px] text-slate-500">
                    <span>Wt: {Math.round(item.weight * 100)}%</span>
                    <span className={item.available ? 'text-emerald-400' : 'text-amber-400'}>
                      {item.available ? 'Active' : 'Pending'}
                    </span>
                  </div>
                </div>
              ))
          }
        </div>

        {/* Explainability Engine Insights & Recommendations */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-indigo-950/20 border border-indigo-500/20 rounded-xl p-4">
            <h3 className="text-xs font-bold text-indigo-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              Verified Candidate Strengths
            </h3>
            <ul className="space-y-1.5">
              {(readiness?.strengths && readiness.strengths.length > 0) ? (
                readiness.strengths.map((note, idx) => (
                  <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{note}</span>
                  </li>
                ))
              ) : (
                <li className="text-xs text-slate-400 flex items-start gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                  <span>Resume and foundational skill profiles detected. Complete assessment modules to unlock granular strengths.</span>
                </li>
              )}
            </ul>
          </div>

          <div className="bg-purple-950/20 border border-purple-500/20 rounded-xl p-4">
            <h3 className="text-xs font-bold text-purple-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Target className="w-3.5 h-3.5 text-purple-400" />
              High-Impact Recommendations
            </h3>
            <ul className="space-y-1.5">
              {(readiness?.recommendations && readiness.recommendations.length > 0) ? (
                readiness.recommendations.map((note, idx) => (
                  <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                    <ArrowUpRight className="w-3.5 h-3.5 text-purple-400 shrink-0 mt-0.5" />
                    <span>{note}</span>
                  </li>
                ))
              ) : (
                <li className="text-xs text-slate-400 flex items-start gap-2">
                  <ArrowUpRight className="w-3.5 h-3.5 text-purple-400 shrink-0 mt-0.5" />
                  <span>Practice 2 Dynamic Programming problems and complete a 5-question AI Mock Interview to raise placement tier.</span>
                </li>
              )}
            </ul>
          </div>
        </div>

        {/* Educational Disclaimer */}
        {readiness?.disclaimer && (
          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-500 flex items-center gap-2">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
            <span>{readiness.disclaimer}</span>
          </div>
        )}
      </div>

      {/* ── All 5 Architecture Modules Grid ── */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">Intelligence Modules</h2>
            <p className="text-xs text-slate-400">Complete full-stack module architecture defined in PlacementIQ</p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400">
            5 Modules Live
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {modules.map((mod) => (
            <Link
              key={mod.id}
              to={mod.href}
              className="group bg-slate-900/50 hover:bg-slate-900/80 border border-slate-800 hover:border-indigo-500/40 p-5 rounded-2xl transition-all duration-200 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className={`w-10 h-10 rounded-xl bg-gradient-to-tr ${mod.color} flex items-center justify-center text-white shadow-lg`}>
                    <mod.icon className="w-5 h-5" />
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${mod.badgeClass}`}>
                    {mod.badge}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-white group-hover:text-indigo-400 transition-colors">
                  {mod.title}
                </h3>
                <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                  {mod.description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
                <span className="text-slate-400 font-medium truncate max-w-[180px]">{mod.metrics}</span>
                <span className="text-indigo-400 font-semibold flex items-center gap-1 group-hover:translate-x-0.5 transition-transform shrink-0">
                  Open Engine <ArrowUpRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </Link>
          ))}

          {/* Module Architecture Summary Card */}
          <div className="bg-gradient-to-br from-indigo-950/40 via-slate-900/40 to-slate-900 border border-indigo-500/20 p-5 rounded-2xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-purple-600 flex items-center justify-center text-white">
                  <Layers className="w-5 h-5" />
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Full Stack
                </span>
              </div>
              <h3 className="text-sm font-bold text-white">
                Tech Stack Architecture
              </h3>
              <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                React 19 + Vite 6 + Tailwind 4, Python FastAPI async backend, PostgreSQL 16 / SQLite with SQLAlchemy 2.0, PyMuPDF, Sentence Transformers (all-MiniLM-L6-v2), and Gemini 2.5 Flash API.
              </p>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800/60 text-[11px] text-indigo-400 font-semibold flex items-center justify-between">
              <span>All 5 Engines Integrated</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
          </div>
        </div>
      </div>

      {/* ── System Status & Live Health ── */}
      <div className="rounded-2xl bg-slate-900/40 border border-slate-800 p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <p className="text-xs font-bold text-slate-200">
              PlacementIQ Core API · Status: {engineHealth?.status || 'Active'}
            </p>
            <p className="text-[11px] text-slate-400">
              Database: {engineHealth?.database || 'SQLite / PostgreSQL Async'} · Auth: PyJWT HS256
            </p>
          </div>
        </div>

        <div className="text-xs text-slate-500 font-mono">
          Last sync: {new Date().toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};
