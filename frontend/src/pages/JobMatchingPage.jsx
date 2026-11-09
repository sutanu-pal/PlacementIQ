import React, { useState, useEffect, useCallback } from 'react';
import { jobAPI, jobMatchAPI, resumeAPI } from '../api/client';
import {
  Briefcase,
  MapPin,
  Clock,
  Search,
  Filter,
  Zap,
  CheckCircle,
  XCircle,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  History,
  Star,
  ArrowLeft,
  RefreshCw,
  TrendingUp,
  BookOpen,
  Target,
} from 'lucide-react';

// ─── Utility helpers ─────────────────────────────────────────────────────────

function scoreColor(score) {
  if (score >= 75) return 'text-emerald-400';
  if (score >= 50) return 'text-amber-400';
  return 'text-rose-400';
}

function scoreBarColor(score) {
  if (score >= 75) return 'bg-emerald-500';
  if (score >= 50) return 'bg-amber-500';
  return 'bg-rose-500';
}

function ScoreBar({ label, score, weight }) {
  return (
    <div className="mb-3">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-slate-400">{label} <span className="text-slate-600">({(weight * 100).toFixed(0)}% weight)</span></span>
        <span className={`font-bold ${scoreColor(score)}`}>{score.toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${scoreBarColor(score)}`}
          style={{ width: `${Math.min(100, score)}%` }}
        />
      </div>
    </div>
  );
}

function SkillPill({ skill, variant }) {
  const styles = {
    matched: 'bg-emerald-900/50 text-emerald-300 border border-emerald-700/50',
    missing_req: 'bg-rose-900/50 text-rose-300 border border-rose-700/50',
    missing_pref: 'bg-amber-900/50 text-amber-300 border border-amber-700/50',
    neutral: 'bg-slate-800 text-slate-300 border border-slate-700',
  };
  return (
    <span className={`inline-block text-xs px-2 py-0.5 rounded-full mr-1 mb-1 ${styles[variant] || styles.neutral}`}>
      {skill}
    </span>
  );
}

// ─── Job Card ─────────────────────────────────────────────────────────────────

function JobCard({ job, onSelect, isSelected }) {
  return (
    <button
      onClick={() => onSelect(job)}
      className={`w-full text-left p-4 rounded-xl border transition-all duration-150 ${
        isSelected
          ? 'border-indigo-500 bg-indigo-900/20'
          : 'border-slate-700 bg-slate-800/60 hover:border-slate-600 hover:bg-slate-800'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="font-semibold text-sm text-slate-100 truncate">{job.title}</h3>
          <p className="text-xs text-slate-400 mt-0.5">{job.company}</p>
        </div>
        {job.is_synthetic && (
          <span className="flex-shrink-0 text-xs bg-slate-700 text-slate-400 px-2 py-0.5 rounded-full">Synthetic</span>
        )}
      </div>
      <div className="flex flex-wrap gap-2 mt-2 text-xs text-slate-500">
        <span className="flex items-center gap-1"><MapPin size={11} />{job.location}</span>
        <span className="flex items-center gap-1"><Clock size={11} />{job.employment_type}</span>
        <span className="flex items-center gap-1"><Briefcase size={11} />{job.experience_level}</span>
      </div>
      {job.required_skills?.length > 0 && (
        <div className="mt-2 flex flex-wrap">
          {job.required_skills.slice(0, 4).map((s) => (
            <SkillPill key={s} skill={s} variant="neutral" />
          ))}
          {job.required_skills.length > 4 && (
            <span className="text-xs text-slate-500 self-center">+{job.required_skills.length - 4} more</span>
          )}
        </div>
      )}
    </button>
  );
}

// ─── Match Result Panel ───────────────────────────────────────────────────────

function MatchResultPanel({ matchData, jobTitle }) {
  const [openSection, setOpenSection] = useState('breakdown');

  return (
    <div className="mt-6 rounded-xl border border-slate-700 bg-slate-800/50 overflow-hidden">
      {/* Score Header */}
      <div className="p-4 bg-gradient-to-r from-indigo-900/30 to-slate-800 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400 uppercase tracking-wide">Match Score</p>
            <p className={`text-4xl font-bold mt-0.5 ${scoreColor(matchData.match_score)}`}>
              {matchData.match_score.toFixed(1)}%
            </p>
          </div>
          <div className="text-right text-xs text-slate-500">
            <p>Algorithm: {matchData.algorithm_version}</p>
            <p className="mt-1 max-w-xs text-slate-600 italic">
              Educational indicator only — not a recruitment guarantee.
            </p>
          </div>
        </div>
      </div>

      {/* Section Tabs */}
      <div className="flex border-b border-slate-700 text-xs">
        {[
          { id: 'breakdown', label: 'Score Breakdown' },
          { id: 'skills', label: 'Skills' },
          { id: 'projects', label: 'Projects' },
          { id: 'recommendations', label: 'Recommendations' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setOpenSection(tab.id)}
            className={`px-4 py-2 font-medium transition-colors ${
              openSection === tab.id
                ? 'text-indigo-400 border-b-2 border-indigo-500 -mb-px'
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="p-4">
        {/* Score Breakdown */}
        {openSection === 'breakdown' && (
          <div>
            <p className="text-xs text-slate-500 mb-4">
              Formula: 50% Skill Coverage + 30% Semantic Similarity + 20% Project Relevance
            </p>
            <ScoreBar label="Skill Coverage" score={matchData.skill_score} weight={0.5} />
            <ScoreBar label="Semantic Similarity" score={matchData.semantic_score} weight={0.3} />
            <ScoreBar label="Project Relevance" score={matchData.project_score} weight={0.2} />

            {matchData.score_breakdown && (
              <div className="mt-4 p-3 bg-slate-900/50 rounded-lg text-xs space-y-1 text-slate-400">
                <p>Required skills matched: {matchData.score_breakdown.required_matched_count}/{matchData.score_breakdown.required_skills_count} ({matchData.score_breakdown.required_coverage_pct}%)</p>
                <p>Preferred skills matched: {matchData.score_breakdown.preferred_matched_count}/{matchData.score_breakdown.preferred_skills_count} ({matchData.score_breakdown.preferred_coverage_pct}%)</p>
                <p>Cosine similarity: {(matchData.score_breakdown.raw_cosine_similarity * 100).toFixed(1)}%</p>
                <p>Projects analysed: {matchData.score_breakdown.projects_analyzed}</p>
              </div>
            )}

            {matchData.explanations?.length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">Explanations</p>
                <ul className="space-y-2">
                  {matchData.explanations.map((exp, i) => (
                    <li key={i} className="flex gap-2 text-xs text-slate-300">
                      <TrendingUp size={13} className="text-indigo-400 flex-shrink-0 mt-0.5" />
                      <span>{exp}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Skills */}
        {openSection === 'skills' && (
          <div className="space-y-4">
            {matchData.matched_skills?.length > 0 && (
              <div>
                <p className="flex items-center gap-1 text-xs font-semibold text-emerald-400 mb-2">
                  <CheckCircle size={12} /> Matched Skills ({matchData.matched_skills.length})
                </p>
                <div className="flex flex-wrap">
                  {matchData.matched_skills.map((s) => <SkillPill key={s} skill={s} variant="matched" />)}
                </div>
              </div>
            )}
            {matchData.missing_required_skills?.length > 0 && (
              <div>
                <p className="flex items-center gap-1 text-xs font-semibold text-rose-400 mb-2">
                  <XCircle size={12} /> Missing Required ({matchData.missing_required_skills.length})
                </p>
                <div className="flex flex-wrap">
                  {matchData.missing_required_skills.map((s) => <SkillPill key={s} skill={s} variant="missing_req" />)}
                </div>
              </div>
            )}
            {matchData.missing_preferred_skills?.length > 0 && (
              <div>
                <p className="flex items-center gap-1 text-xs font-semibold text-amber-400 mb-2">
                  <AlertCircle size={12} /> Missing Preferred ({matchData.missing_preferred_skills.length})
                </p>
                <div className="flex flex-wrap">
                  {matchData.missing_preferred_skills.map((s) => <SkillPill key={s} skill={s} variant="missing_pref" />)}
                </div>
              </div>
            )}
            {!matchData.matched_skills?.length && !matchData.missing_required_skills?.length && (
              <p className="text-sm text-slate-500">No skill data available.</p>
            )}
          </div>
        )}

        {/* Projects */}
        {openSection === 'projects' && (
          <div>
            {matchData.project_relevance ? (
              <>
                <p className="text-xs text-slate-400 mb-3">{matchData.project_relevance.summary}</p>
                {matchData.project_relevance.details?.length > 0 ? (
                  <ul className="space-y-2">
                    {matchData.project_relevance.details.map((p, i) => (
                      <li key={i} className="flex items-center justify-between p-2 bg-slate-900/40 rounded-lg text-xs">
                        <span className="text-slate-300">{p.title}</span>
                        <span className={`font-bold ${scoreColor(p.relevance_similarity * 100)}`}>
                          {(p.relevance_similarity * 100).toFixed(1)}% aligned
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-500">No project records found in resume. Add projects to improve this score.</p>
                )}
              </>
            ) : (
              <p className="text-sm text-slate-500">Project relevance data not available.</p>
            )}
          </div>
        )}

        {/* Recommendations */}
        {openSection === 'recommendations' && (
          <div>
            {matchData.recommendations?.length > 0 ? (
              <ul className="space-y-3">
                {matchData.recommendations.map((rec, i) => (
                  <li key={i} className="flex gap-3 p-3 bg-slate-900/40 rounded-lg text-sm">
                    <BookOpen size={15} className="text-indigo-400 flex-shrink-0 mt-0.5" />
                    <span className="text-slate-300">{rec}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-500">No recommendations generated.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Job Detail View ──────────────────────────────────────────────────────────

function JobDetailView({ job, hasResume, onMatch, matchLoading, matchResult, matchError, onBack }) {
  return (
    <div>
      {/* Back button (mobile) */}
      <button onClick={onBack} className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 mb-4 lg:hidden">
        <ArrowLeft size={13} /> Back to listings
      </button>

      {/* Job header */}
      <div className="p-4 rounded-xl border border-slate-700 bg-slate-800/60">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-slate-100">{job.title}</h2>
            <p className="text-sm text-slate-400 mt-0.5">{job.company}</p>
            {job.is_synthetic && (
              <span className="text-xs bg-slate-700 text-slate-400 px-2 py-0.5 rounded-full mt-1 inline-block">
                Synthetic Benchmark — not a real vacancy
              </span>
            )}
          </div>
          <div className="text-right text-xs text-slate-500 flex-shrink-0">
            {job.salary_range && <p className="text-emerald-400 font-semibold">{job.salary_range}</p>}
          </div>
        </div>

        <div className="flex flex-wrap gap-3 mt-3 text-xs text-slate-400">
          <span className="flex items-center gap-1"><MapPin size={12} />{job.location}</span>
          <span className="flex items-center gap-1"><Clock size={12} />{job.employment_type}</span>
          <span className="flex items-center gap-1"><Briefcase size={12} />{job.experience_level}</span>
        </div>

        <p className="text-sm text-slate-300 mt-3 leading-relaxed">{job.description}</p>

        {job.responsibilities?.length > 0 && (
          <div className="mt-3">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">Responsibilities</p>
            <ul className="space-y-1">
              {job.responsibilities.map((r, i) => (
                <li key={i} className="flex gap-2 text-xs text-slate-300">
                  <ChevronRight size={12} className="text-indigo-400 flex-shrink-0 mt-0.5" />
                  {r}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Skills summary */}
        <div className="mt-3 grid grid-cols-2 gap-3">
          {job.required_skills?.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-rose-400 mb-1">Required</p>
              <div className="flex flex-wrap">
                {job.required_skills.map((s) => <SkillPill key={s} skill={s} variant="missing_req" />)}
              </div>
            </div>
          )}
          {job.preferred_skills?.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-amber-400 mb-1">Preferred</p>
              <div className="flex flex-wrap">
                {job.preferred_skills.map((s) => <SkillPill key={s} skill={s} variant="missing_pref" />)}
              </div>
            </div>
          )}
        </div>

        {/* Match button */}
        <div className="mt-4 pt-4 border-t border-slate-700">
          {!hasResume && (
            <p className="text-xs text-amber-400 mb-2 flex items-center gap-1">
              <AlertCircle size={12} /> Upload a resume in the Resume Analyzer first to enable matching.
            </p>
          )}
          <button
            onClick={onMatch}
            disabled={!hasResume || matchLoading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 disabled:cursor-not-allowed text-white transition-colors"
          >
            {matchLoading ? (
              <><RefreshCw size={14} className="animate-spin" /> Running Match…</>
            ) : (
              <><Zap size={14} /> Run Match with My Resume</>
            )}
          </button>
          {matchError && (
            <p className="text-xs text-rose-400 mt-2 flex items-center gap-1">
              <XCircle size={12} /> {matchError}
            </p>
          )}
        </div>
      </div>

      {/* Match result */}
      {matchResult && <MatchResultPanel matchData={matchResult} jobTitle={job.title} />}
    </div>
  );
}

// ─── Match History ────────────────────────────────────────────────────────────

function MatchHistoryPanel({ matches, loading, onSelectMatch, selectedMatchId }) {
  if (loading) {
    return (
      <div className="flex items-center gap-2 text-slate-500 py-6 text-sm">
        <RefreshCw size={14} className="animate-spin" /> Loading history…
      </div>
    );
  }
  if (!matches.length) {
    return (
      <div className="text-center py-10 text-slate-500 text-sm">
        <History size={28} className="mx-auto mb-2 opacity-40" />
        <p>No match evaluations yet. Select a job and run a match to get started.</p>
      </div>
    );
  }
  return (
    <div className="space-y-3">
      {matches.map((m) => (
        <button
          key={m.id}
          onClick={() => onSelectMatch(m)}
          className={`w-full text-left p-3 rounded-xl border transition-all ${
            selectedMatchId === m.id
              ? 'border-indigo-500 bg-indigo-900/20'
              : 'border-slate-700 bg-slate-800/60 hover:border-slate-600'
          }`}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="text-sm font-semibold text-slate-200 truncate">
                {m.job_title || 'Job'}
              </p>
              <p className="text-xs text-slate-500">{m.job_company} · {m.job_location}</p>
              <p className="text-xs text-slate-600 mt-0.5">
                {new Date(m.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
            <div className="flex-shrink-0 text-right">
              <p className={`text-lg font-bold ${scoreColor(m.match_score)}`}>{m.match_score.toFixed(0)}%</p>
              <p className="text-xs text-slate-600">v{m.resume_version}</p>
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export function JobMatchingPage() {
  const [jobs, setJobs] = useState([]);
  const [jobsLoading, setJobsLoading] = useState(true);
  const [jobsError, setJobsError] = useState(null);
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState({ employment_type: '', location: '', skill: '' });
  const [selectedJob, setSelectedJob] = useState(null);

  const [hasResume, setHasResume] = useState(false);
  const [resumeCheckDone, setResumeCheckDone] = useState(false);

  const [matchLoading, setMatchLoading] = useState(false);
  const [matchResult, setMatchResult] = useState(null);
  const [matchError, setMatchError] = useState(null);

  const [activeTab, setActiveTab] = useState('browse'); // 'browse' | 'history'
  const [matches, setMatches] = useState([]);
  const [matchesLoading, setMatchesLoading] = useState(false);
  const [selectedHistoryMatch, setSelectedHistoryMatch] = useState(null);

  const [showMobileDetail, setShowMobileDetail] = useState(false);

  // ── Load jobs ──
  const loadJobs = useCallback(async () => {
    setJobsLoading(true);
    setJobsError(null);
    try {
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (filters.employment_type) params.employment_type = filters.employment_type;
      if (filters.location) params.location = filters.location;
      if (filters.skill) params.skill = filters.skill;
      const data = await jobAPI.listJobs(params);
      setJobs(data.items || []);
    } catch (err) {
      setJobsError(err.response?.data?.detail || 'Failed to load job listings.');
    } finally {
      setJobsLoading(false);
    }
  }, [search, filters]);

  useEffect(() => {
    if (activeTab === 'browse') loadJobs();
  }, [activeTab, loadJobs]);

  // ── Check resume availability ──
  useEffect(() => {
    resumeAPI.listResumes().then((data) => {
      const list = data.resumes || data.items || [];
      const analyzed = list.filter((r) => r.status === 'analyzed');
      setHasResume(analyzed.length > 0);
    }).catch(() => {
      setHasResume(false);
    }).finally(() => setResumeCheckDone(true));
  }, []);

  // ── Load match history ──
  const loadHistory = useCallback(async () => {
    setMatchesLoading(true);
    try {
      const data = await jobMatchAPI.listMatches();
      setMatches(data.items || []);
    } catch {
      setMatches([]);
    } finally {
      setMatchesLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'history') loadHistory();
  }, [activeTab, loadHistory]);

  // ── Run match ──
  const handleRunMatch = async () => {
    if (!selectedJob) return;
    setMatchLoading(true);
    setMatchResult(null);
    setMatchError(null);
    try {
      const result = await jobAPI.matchJob(selectedJob.id);
      setMatchResult(result);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setMatchError(detail || 'Match failed. Please try again.');
    } finally {
      setMatchLoading(false);
    }
  };

  const handleSelectJob = (job) => {
    setSelectedJob(job);
    setMatchResult(null);
    setMatchError(null);
    setShowMobileDetail(true);
  };

  const handleSelectHistoryMatch = (m) => {
    setSelectedHistoryMatch(m);
  };

  // Unique filter values
  const employmentTypes = [...new Set(jobs.map((j) => j.employment_type).filter(Boolean))];
  const locations = [...new Set(jobs.map((j) => j.location?.split('(')[0]?.trim()).filter(Boolean))];

  return (
    <div className="min-h-screen">
      {/* Page header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <div className="p-2 rounded-lg bg-indigo-600/20 border border-indigo-500/30">
            <Target size={20} className="text-indigo-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-100">Intelligent Job Matching</h1>
            <p className="text-xs text-slate-500">Semantic NLP matching using all-MiniLM-L6-v2 · 384-dim dense vectors</p>
          </div>
        </div>
        {!hasResume && resumeCheckDone && (
          <div className="mt-3 p-3 rounded-lg border border-amber-700/50 bg-amber-900/20 flex items-center gap-2 text-sm text-amber-300">
            <AlertCircle size={15} className="flex-shrink-0" />
            Upload and analyse a resume in the <a href="/resume" className="underline font-semibold">Resume Analyzer</a> first to enable job matching.
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-5 border-b border-slate-700 pb-0">
        {[
          { id: 'browse', label: 'Browse Jobs', icon: Briefcase },
          { id: 'history', label: 'Match History', icon: History },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => { setActiveTab(id); setShowMobileDetail(false); }}
            className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-t transition-colors ${
              activeTab === id
                ? 'text-indigo-400 border-b-2 border-indigo-500 -mb-px'
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            <Icon size={14} />{label}
          </button>
        ))}
      </div>

      {/* ── Browse Jobs Tab ── */}
      {activeTab === 'browse' && (
        <div className="flex gap-5">
          {/* Left: listings (hide on mobile when detail is shown) */}
          <div className={`w-full lg:w-80 xl:w-96 flex-shrink-0 ${showMobileDetail ? 'hidden lg:block' : ''}`}>
            {/* Search */}
            <div className="relative mb-3">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="Search jobs, companies…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* Filters row */}
            <div className="flex gap-2 mb-3 flex-wrap">
              <select
                value={filters.employment_type}
                onChange={(e) => setFilters((f) => ({ ...f, employment_type: e.target.value }))}
                className="text-xs bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-slate-300 focus:outline-none focus:border-indigo-500"
              >
                <option value="">All Types</option>
                {employmentTypes.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
              <select
                value={filters.location}
                onChange={(e) => setFilters((f) => ({ ...f, location: e.target.value }))}
                className="text-xs bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-slate-300 focus:outline-none focus:border-indigo-500"
              >
                <option value="">All Locations</option>
                {locations.map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
              <button
                onClick={() => { setSearch(''); setFilters({ employment_type: '', location: '', skill: '' }); }}
                className="text-xs text-slate-500 hover:text-slate-300 px-2"
              >
                Clear
              </button>
            </div>

            {/* Job list */}
            {jobsLoading ? (
              <div className="flex items-center gap-2 text-slate-500 py-6 text-sm">
                <RefreshCw size={14} className="animate-spin" /> Loading jobs…
              </div>
            ) : jobsError ? (
              <div className="p-3 rounded-lg border border-rose-800/50 bg-rose-900/20 text-rose-400 text-sm">
                {jobsError}
              </div>
            ) : jobs.length === 0 ? (
              <div className="text-center py-10 text-slate-500 text-sm">
                <Briefcase size={28} className="mx-auto mb-2 opacity-40" />
                <p>No jobs found. Try a different search.</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-[70vh] overflow-y-auto pr-1">
                {jobs.map((job) => (
                  <JobCard
                    key={job.id}
                    job={job}
                    onSelect={handleSelectJob}
                    isSelected={selectedJob?.id === job.id}
                  />
                ))}
                <p className="text-xs text-center text-slate-600 pt-2">{jobs.length} listings</p>
              </div>
            )}
          </div>

          {/* Right: job detail */}
          <div className={`flex-1 min-w-0 ${!showMobileDetail && !selectedJob ? 'hidden lg:flex items-center justify-center' : ''}`}>
            {!selectedJob ? (
              <div className="text-center text-slate-600">
                <Star size={36} className="mx-auto mb-3 opacity-30" />
                <p className="text-sm">Select a job from the list to view details and run a match.</p>
              </div>
            ) : (
              <JobDetailView
                job={selectedJob}
                hasResume={hasResume}
                onMatch={handleRunMatch}
                matchLoading={matchLoading}
                matchResult={matchResult}
                matchError={matchError}
                onBack={() => setShowMobileDetail(false)}
              />
            )}
          </div>
        </div>
      )}

      {/* ── History Tab ── */}
      {activeTab === 'history' && (
        <div className="flex gap-5">
          <div className={`w-full lg:w-80 xl:w-96 flex-shrink-0 ${selectedHistoryMatch ? 'hidden lg:block' : ''}`}>
            <MatchHistoryPanel
              matches={matches}
              loading={matchesLoading}
              onSelectMatch={handleSelectHistoryMatch}
              selectedMatchId={selectedHistoryMatch?.id}
            />
          </div>
          <div className="flex-1 min-w-0">
            {selectedHistoryMatch ? (
              <>
                <button
                  onClick={() => setSelectedHistoryMatch(null)}
                  className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 mb-4 lg:hidden"
                >
                  <ArrowLeft size={13} /> Back to history
                </button>
                <div className="p-3 rounded-xl border border-slate-700 bg-slate-800/60 mb-3">
                  <p className="text-sm font-semibold text-slate-200">{selectedHistoryMatch.job_title}</p>
                  <p className="text-xs text-slate-500">{selectedHistoryMatch.job_company}</p>
                </div>
                <MatchResultPanel matchData={selectedHistoryMatch} />
              </>
            ) : (
              <div className="hidden lg:flex items-center justify-center h-full text-slate-600 text-sm">
                <div className="text-center">
                  <History size={36} className="mx-auto mb-3 opacity-30" />
                  <p>Select a match from the list to view its detailed report.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default JobMatchingPage;
