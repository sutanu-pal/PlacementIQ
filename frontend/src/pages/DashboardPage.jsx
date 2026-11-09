import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { systemAPI, resumeAPI } from '../api/client';
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
  Database,
  Check,
} from 'lucide-react';

export const DashboardPage = () => {
  const { user } = useAuth();
  const [engineHealth, setEngineHealth] = useState(null);
  const [latestResume, setLatestResume] = useState(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await systemAPI.getHealth();
        setEngineHealth(res);
      } catch (err) {
        setEngineHealth({ status: 'offline', database: 'error' });
      }
    };
    const fetchLatestResume = async () => {
      try {
        const data = await resumeAPI.listResumes();
        if (data.resumes && data.resumes.length > 0) {
          setLatestResume(data.resumes[0]);
        }
      } catch (err) {
        // No resume yet
      }
    };
    fetchHealth();
    fetchLatestResume();
  }, []);

  // Readiness engine sub-scores demo state (will be connected to Readiness Engine in later phase)
  const readiness = {
    overall: 78,
    tier: 'High Placement Potential',
    breakdown: [
      {
        name: 'Resume Quality',
        score: latestResume ? Math.round(latestResume.overall_score) : 82,
        weight: '15%',
        status: latestResume ? `v${latestResume.version} Live Score` : 'Module 1 Active',
      },
      { name: 'Job Matching Fit', score: 80, weight: '15%', status: 'NLP Cosine Similarity' },
      { name: 'DSA Mastery', score: 75, weight: '30%', status: 'Python Subprocess Sandbox' },
      { name: 'Mock Interview', score: 76, weight: '25%', status: 'Gemini 2.5 Flash' },
      { name: 'Roadmap Progress', score: 77, weight: '15%', status: 'Skill Gap Graph' },
    ],
    explanations: [
      'Strong core CS foundations detected in Operating Systems and Data Structures.',
      'Resume exhibits clear section structure; ATS keyword density can be optimized.',
      'Recommended focus: Practice 2 Medium Dynamic Programming problems to reach 85%+ readiness.',
    ],
  };

  const modules = [
    {
      id: 1,
      title: 'AI Resume Analyzer',
      description: 'PyMuPDF text extraction, section identification, and ATS skill parsing.',
      icon: FileText,
      color: 'from-blue-500 to-indigo-600',
      badge: 'Module 1 · Active',
      isLive: true,
      href: '/resume',
      metrics: latestResume ? `v${latestResume.version} · Score ${Math.round(latestResume.overall_score)}%` : 'Ready to Analyze',
    },
    {
      id: 2,
      title: 'Intelligent Job Matching',
      description: 'Sentence Transformers (all-MiniLM-L6-v2) semantic similarity and skill gap identification.',
      icon: Briefcase,
      color: 'from-indigo-500 to-purple-600',
      badge: 'Module 2',
      href: '/jobs',
      metrics: 'Cosine Similarity & Skill Overlap',
    },
    {
      id: 3,
      title: 'DSA Assessment Engine',
      description: 'Curated problem banks, real-time code execution with testcase evaluation.',
      icon: Code2,
      color: 'from-purple-500 to-pink-600',
      badge: 'Module 3',
      href: '/dsa',
      metrics: 'Python Sandboxed Execution',
    },
    {
      id: 4,
      title: 'AI Mock Interview',
      description: 'Simulated multi-turn technical & behavioral interviews powered by Gemini 2.5 Flash.',
      icon: Mic,
      color: 'from-emerald-500 to-teal-600',
      badge: 'Module 4',
      href: '/interview',
      metrics: 'STAR Method & Live Evaluation',
    },
    {
      id: 5,
      title: 'Personalized Roadmap',
      description: 'Automated gap prioritization and 4-week structured milestones.',
      icon: Compass,
      color: 'from-amber-500 to-orange-600',
      badge: 'Module 5',
      href: '/roadmap',
      metrics: 'Curated Resources & Milestones',
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
              Your placement intelligence dashboard connects all 5 specialized modules to analyze, benchmark, and accelerate your engineering placement readiness.
            </p>
          </div>

          {/* Quick Profile Pill */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 shrink-0 bg-slate-950/60 p-3 rounded-xl border border-slate-800">
            <div className="w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold">
              {user?.full_name?.charAt(0) || 'S'}
            </div>
            <div className="text-xs">
              <p className="font-semibold text-slate-200">{user?.college || 'Engineering Institute'}</p>
              <p className="text-slate-400">
                {user?.branch || 'AI & ML'} · Sem {user?.semester || 7}
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
              Aggregated weighted composite score computed across all 5 intelligence dimensions
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <span className="text-3xl sm:text-4xl font-black text-indigo-400 tracking-tight">
                {readiness.overall}%
              </span>
              <p className="text-[11px] font-semibold text-emerald-400 flex items-center justify-end gap-1">
                <TrendingUp className="w-3 h-3" />
                <span>{readiness.tier}</span>
              </p>
            </div>
          </div>
        </div>

        {/* 5-Dimension Progress Bars */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 my-6">
          {readiness.breakdown.map((item) => (
            <div
              key={item.name}
              className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 flex flex-col justify-between"
            >
              <div>
                <div className="flex justify-between items-center text-xs mb-1.5">
                  <span className="font-semibold text-slate-300">{item.name}</span>
                  <span className="font-mono text-indigo-400 font-bold">{item.score}%</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-indigo-500 to-purple-500 h-full rounded-full transition-all duration-500"
                    style={{ width: `${item.score}%` }}
                  />
                </div>
              </div>
              <div className="mt-3 flex items-center justify-between text-[10px] text-slate-500">
                <span>Weight: {item.weight}</span>
                <span className="text-slate-400 font-medium">{item.status}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Explainability Engine Insights */}
        <div className="bg-indigo-950/20 border border-indigo-500/20 rounded-xl p-4">
          <h3 className="text-xs font-bold text-indigo-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            Explainability Rationale & AI Guidance
          </h3>
          <ul className="space-y-1.5">
            {readiness.explanations.map((note, idx) => (
              <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                <span>{note}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* ── All 5 Architecture Modules Grid ── */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">Intelligence Modules</h2>
            <p className="text-xs text-slate-400">Core functional modules defined in PlacementIQ architecture</p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400">
            5 Modules Built-In
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
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    mod.isLive
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      : 'bg-slate-800 text-slate-300 border-slate-700'
                  }`}>
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
                <span className="text-slate-500 font-medium">{mod.metrics}</span>
                <span className="text-indigo-400 font-semibold flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
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
                React 19 + Vite 6 + Tailwind 4, Python FastAPI async backend, PostgreSQL 16 + SQLAlchemy 2.1, PyMuPDF, Sentence Transformers, Scikit-learn, and Gemini 2.5 Flash API.
              </p>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800/60 text-[11px] text-indigo-400 font-semibold flex items-center justify-between">
              <span>Foundation Active</span>
              <Check className="w-4 h-4 text-emerald-400" />
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
              PlacementIQ Core API · Status: {engineHealth?.status || 'Connecting...'}
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
