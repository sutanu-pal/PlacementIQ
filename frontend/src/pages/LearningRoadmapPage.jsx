import React, { useState, useEffect } from 'react';
import { roadmapAPI } from '../api/client';
import {
  Compass,
  CheckCircle2,
  Circle,
  ExternalLink,
  Flame,
  Clock,
  Sparkles,
  RefreshCw,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Target,
  BookOpen,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';

const ROLES = [
  'Full Stack Software Engineer',
  'Backend Developer (Python/FastAPI)',
  'Frontend Engineer (React/TypeScript)',
  'Associate AI & ML Research Engineer',
  'DevOps & Cloud Associate',
];

function priorityBadge(p) {
  if (p === 'High') return 'text-rose-400 bg-rose-950/60 border-rose-800/60';
  if (p === 'Medium') return 'text-amber-400 bg-amber-950/60 border-amber-800/60';
  return 'text-slate-400 bg-slate-800/60 border-slate-700';
}

export function LearningRoadmapPage() {
  const [roadmap, setRoadmap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Regeneration state
  const [targetRole, setTargetRole] = useState(ROLES[0]);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [expandedMilestones, setExpandedMilestones] = useState({ 1: true, 2: true, 3: true, 4: true });

  const fetchRoadmap = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await roadmapAPI.getRoadmap();
      setRoadmap(data);
      if (data.target_role) setTargetRole(data.target_role);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load personalized roadmap.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoadmap();
  }, []);

  const handleToggleTask = async (taskId) => {
    try {
      const updated = await roadmapAPI.toggleTask(taskId);
      setRoadmap(updated);
    } catch (err) {
      alert('Could not update task status.');
    }
  };

  const handleRegenerate = async (e) => {
    e?.preventDefault();
    setIsRegenerating(true);
    try {
      const data = await roadmapAPI.generateRoadmap({ target_role: targetRole });
      setRoadmap(data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to regenerate roadmap.');
    } finally {
      setIsRegenerating(false);
    }
  };

  const toggleMilestone = (weekNum) => {
    setExpandedMilestones((prev) => ({
      ...prev,
      [weekNum]: !prev[weekNum],
    }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Compass className="text-indigo-400" size={26} />
            Personalized Learning Roadmap
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">
            Adaptive 4-week milestone curriculum synthesized from resume gaps, job matches & DSA telemetry
          </p>
        </div>

        {/* Learning Streak Badge */}
        <div className="flex items-center gap-2 bg-gradient-to-r from-amber-950/40 to-slate-900 border border-amber-800/40 px-3.5 py-1.5 rounded-xl self-start md:self-auto shadow-md">
          <Flame className="text-amber-400" size={18} />
          <span className="text-xs font-bold text-amber-200">
            {roadmap?.current_streak_days || 1} Day Streak
          </span>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-20 text-slate-500 flex justify-center items-center gap-2">
          <RefreshCw className="animate-spin" size={20} />
          Synthesizing your personalized roadmap...
        </div>
      ) : error ? (
        <div className="bg-rose-950/40 border border-rose-800 p-5 rounded-2xl text-rose-300 text-sm">
          {error}
        </div>
      ) : roadmap ? (
        <div className="space-y-6">
          {/* Progress & Target Role Card */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            {/* Left 8: Overview and Progress */}
            <div className="lg:col-span-8 bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <span className="text-[11px] font-bold text-indigo-400 uppercase tracking-widest bg-indigo-950/60 border border-indigo-800/40 px-2 py-0.5 rounded">
                    Curriculum Target
                  </span>
                  <h2 className="text-lg font-bold text-white mt-1">{roadmap.title}</h2>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-extrabold text-indigo-400 font-mono">
                    {roadmap.completion_pct}%
                  </span>
                  <p className="text-[11px] text-slate-500">Milestone Progress</p>
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden border border-slate-800">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 transition-all duration-700 rounded-full"
                  style={{ width: `${roadmap.completion_pct}%` }}
                />
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">{roadmap.description}</p>
            </div>

            {/* Right 4: Target Role Selector & Regenerate */}
            <div className="lg:col-span-4 bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl flex flex-col justify-between space-y-4">
              <div>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Target Career Track
                </span>
                <select
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  className="w-full mt-2 bg-slate-950 text-slate-200 text-xs p-2.5 rounded-xl border border-slate-800 focus:outline-none focus:border-indigo-500"
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleRegenerate}
                disabled={isRegenerating}
                className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-lg shadow-indigo-600/20 transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                {isRegenerating ? (
                  <>
                    <RefreshCw className="animate-spin" size={14} /> Recomputing Signals...
                  </>
                ) : (
                  <>
                    <Sparkles size={14} /> Regenerate Roadmap
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Explainability Signal Banner */}
          {roadmap.signals_summary && (
            <div className="bg-slate-900/50 border border-slate-800/80 p-4 rounded-2xl flex flex-wrap gap-4 items-center text-xs text-slate-400">
              <div className="flex items-center gap-1.5 text-indigo-300 font-semibold">
                <Target size={14} /> Active Signals:
              </div>
              {roadmap.signals_summary.missing_required_skills?.length > 0 && (
                <div>
                  <strong className="text-slate-300">Job Skill Gaps:</strong>{' '}
                  {roadmap.signals_summary.missing_required_skills.join(', ')}
                </div>
              )}
              {roadmap.signals_summary.dsa_weaknesses?.length > 0 && (
                <div>
                  <strong className="text-slate-300">DSA Needs:</strong>{' '}
                  {roadmap.signals_summary.dsa_weaknesses.join(', ')}
                </div>
              )}
            </div>
          )}

          {/* 4-Week Milestone Accordion / Timeline */}
          <div className="space-y-4">
            {roadmap.milestones?.map((milestone) => {
              const completedCount = milestone.tasks?.filter((t) => t.is_completed).length || 0;
              const totalCount = milestone.tasks?.length || 0;
              const isDone = totalCount > 0 && completedCount === totalCount;
              const isExpanded = !!expandedMilestones[milestone.week_number];

              return (
                <div
                  key={milestone.id}
                  className="bg-slate-900/80 border border-slate-800 rounded-3xl overflow-hidden shadow-xl transition-all"
                >
                  {/* Milestone Header */}
                  <div
                    onClick={() => toggleMilestone(milestone.week_number)}
                    className="p-5 flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-9 h-9 rounded-2xl flex items-center justify-center font-bold text-sm shrink-0 border ${
                          isDone
                            ? 'bg-emerald-950/70 text-emerald-400 border-emerald-800/60'
                            : 'bg-indigo-950/60 text-indigo-300 border-indigo-800/50'
                        }`}
                      >
                        W{milestone.week_number}
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                          {milestone.title}
                          {isDone && (
                            <span className="text-[10px] bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 px-2 py-0.5 rounded-full font-semibold">
                              Completed
                            </span>
                          )}
                        </h3>
                        <p className="text-xs text-slate-400 mt-0.5">{milestone.objective}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <span className="text-xs font-mono text-slate-400 hidden sm:inline">
                        {completedCount}/{totalCount} tasks
                      </span>
                      {isExpanded ? (
                        <ChevronUp size={18} className="text-slate-500" />
                      ) : (
                        <ChevronDown size={18} className="text-slate-500" />
                      )}
                    </div>
                  </div>

                  {/* Task List */}
                  {isExpanded && (
                    <div className="border-t border-slate-800/80 bg-slate-950/40 p-5 space-y-3">
                      {milestone.tasks?.map((task) => (
                        <div
                          key={task.id}
                          className={`p-4 rounded-2xl border transition-all flex flex-col md:flex-row md:items-center justify-between gap-3 ${
                            task.is_completed
                              ? 'bg-slate-950/40 border-slate-800/60 opacity-75'
                              : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                          }`}
                        >
                          {/* Left: Checkbox & Task details */}
                          <div className="flex items-start gap-3">
                            <button
                              onClick={() => handleToggleTask(task.id)}
                              className="mt-0.5 text-slate-400 hover:text-emerald-400 transition-colors shrink-0 cursor-pointer"
                            >
                              {task.is_completed ? (
                                <CheckCircle2 size={19} className="text-emerald-400" />
                              ) : (
                                <Circle size={19} />
                              )}
                            </button>
                            <div className="space-y-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <h4
                                  className={`text-xs font-bold ${
                                    task.is_completed
                                      ? 'line-through text-slate-500'
                                      : 'text-white'
                                  }`}
                                >
                                  {task.title}
                                </h4>
                                <span
                                  className={`text-[10px] font-bold px-2 py-0.5 rounded border ${priorityBadge(
                                    task.priority
                                  )}`}
                                >
                                  {task.priority} Priority
                                </span>
                              </div>
                              <p className="text-xs text-slate-400 leading-relaxed">
                                {task.description}
                              </p>

                              {/* Explainability Tag */}
                              {task.triggered_by && (
                                <div className="text-[11px] text-indigo-400 flex items-center gap-1 pt-1">
                                  <span>🔍 <em>Why:</em> {task.triggered_by}</span>
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Right: Resources & Hours */}
                          <div className="flex items-center gap-3 pl-8 md:pl-0 shrink-0">
                            <span className="text-[11px] text-slate-500 flex items-center gap-1">
                              <Clock size={11} /> {task.estimated_hours}h
                            </span>
                            {task.resource_url && (
                              <a
                                href={task.resource_url}
                                target="_blank"
                                rel="noreferrer"
                                className="flex items-center gap-1 text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 bg-indigo-950/50 border border-indigo-900/60 px-2.5 py-1 rounded-lg transition-colors"
                              >
                                Resource <ExternalLink size={10} />
                              </a>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default LearningRoadmapPage;
