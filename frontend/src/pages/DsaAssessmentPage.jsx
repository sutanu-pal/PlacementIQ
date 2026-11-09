import React, { useState, useEffect, useCallback } from 'react';
import { dsaAPI } from '../api/client';
import {
  Code2,
  Terminal,
  Play,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Cpu,
  BarChart2,
  Search,
  Filter,
  RefreshCw,
  ChevronRight,
  ArrowLeft,
  Check,
  RotateCcw,
  BookOpen,
  Award,
  Zap,
} from 'lucide-react';

const CATEGORIES = [
  'All',
  'Arrays',
  'Strings',
  'Linked Lists',
  'Dynamic Programming',
  'Greedy',
  'Recursion',
];

function difficultyColor(diff) {
  if (diff === 'Easy') return 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60';
  if (diff === 'Medium') return 'text-amber-400 bg-amber-950/60 border-amber-800/60';
  return 'text-rose-400 bg-rose-950/60 border-rose-800/60';
}

function statusBadge(status) {
  if (status === 'Accepted') {
    return (
      <span className="flex items-center gap-1 text-emerald-400 bg-emerald-950/70 border border-emerald-800/60 px-2 py-0.5 rounded text-xs font-semibold">
        <CheckCircle size={12} /> Accepted
      </span>
    );
  }
  if (status === 'Wrong Answer') {
    return (
      <span className="flex items-center gap-1 text-rose-400 bg-rose-950/70 border border-rose-800/60 px-2 py-0.5 rounded text-xs font-semibold">
        <XCircle size={12} /> Wrong Answer
      </span>
    );
  }
  if (status === 'Time Limit Exceeded') {
    return (
      <span className="flex items-center gap-1 text-amber-400 bg-amber-950/70 border border-amber-800/60 px-2 py-0.5 rounded text-xs font-semibold">
        <Clock size={12} /> TLE
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1 text-red-400 bg-red-950/70 border border-red-800/60 px-2 py-0.5 rounded text-xs font-semibold">
      <AlertTriangle size={12} /> {status}
    </span>
  );
}

export function DsaAssessmentPage() {
  const [activeTab, setActiveTab] = useState('problems'); // 'problems' | 'analytics'
  const [questions, setQuestions] = useState([]);
  const [questionsLoading, setQuestionsLoading] = useState(true);
  const [questionsError, setQuestionsError] = useState(null);

  // Filters
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedDifficulty, setSelectedDifficulty] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Selected question & workspace
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [code, setCode] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [activeTestTab, setActiveTestTab] = useState(0);

  // Submissions history for this question
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Analytics data
  const [analytics, setAnalytics] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

  // 1. Fetch Questions
  const fetchQuestions = useCallback(async () => {
    setQuestionsLoading(true);
    setQuestionsError(null);
    try {
      const params = {};
      if (selectedCategory !== 'All') params.category = selectedCategory;
      if (selectedDifficulty) params.difficulty = selectedDifficulty;
      if (searchQuery.trim()) params.search = searchQuery.trim();

      const res = await dsaAPI.listQuestions(params);
      setQuestions(res.items || []);
    } catch (err) {
      setQuestionsError(err.response?.data?.detail || 'Failed to load DSA problems.');
    } finally {
      setQuestionsLoading(false);
    }
  }, [selectedCategory, selectedDifficulty, searchQuery]);

  useEffect(() => {
    fetchQuestions();
  }, [fetchQuestions]);

  // 2. Fetch Question Detail
  const handleSelectQuestion = async (qItem) => {
    try {
      const detail = await dsaAPI.getQuestion(qItem.slug || qItem.id);
      setSelectedQuestion(detail);
      setCode(detail.starter_code?.python || '# Write solution here\nclass Solution:\n    pass\n');
      setSubmissionResult(null);
      setActiveTestTab(0);
      loadQuestionHistory(detail.id);
    } catch (err) {
      alert('Could not open problem details.');
    }
  };

  // 3. Load Submissions for Question
  const loadQuestionHistory = async (qid) => {
    setHistoryLoading(true);
    try {
      const res = await dsaAPI.listSubmissions({ question_id: qid, limit: 10 });
      setHistory(res.items || []);
    } catch {
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  // 4. Submit Solution
  const handleSubmitCode = async () => {
    if (!selectedQuestion) return;
    setIsSubmitting(true);
    setSubmissionResult(null);
    try {
      const res = await dsaAPI.submitSolution(selectedQuestion.id, {
        code,
        language: 'python',
      });
      setSubmissionResult(res);
      loadQuestionHistory(selectedQuestion.id);
      // Refresh list to update solved checkmark
      fetchQuestions();
    } catch (err) {
      setSubmissionResult({
        status: 'Runtime Error',
        passed_count: 0,
        total_count: 0,
        error_message: err.response?.data?.detail || 'Failed to communicate with execution sandbox.',
        test_results: [],
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // 5. Fetch Analytics
  const fetchAnalytics = async () => {
    setAnalyticsLoading(true);
    try {
      const data = await dsaAPI.getAnalytics();
      setAnalytics(data);
    } catch {
      setAnalytics(null);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'analytics') {
      fetchAnalytics();
    }
  }, [activeTab]);

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Code2 className="text-indigo-400" size={26} />
            DSA Assessment Engine
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">
            Industry coding curriculum evaluated via isolated AST security sandbox & telemetry
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 p-1 rounded-xl self-start md:self-auto">
          <button
            onClick={() => {
              setActiveTab('problems');
              setSelectedQuestion(null);
            }}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'problems' && !selectedQuestion
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Question Bank
          </button>
          <button
            onClick={() => {
              setActiveTab('analytics');
              setSelectedQuestion(null);
            }}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'analytics'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <BarChart2 size={13} />
            Topic Mastery & Analytics
          </button>
        </div>
      </div>

      {/* VIEW 1: Problem Solver Workspace */}
      {selectedQuestion ? (
        <div className="space-y-4">
          <button
            onClick={() => setSelectedQuestion(null)}
            className="flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
          >
            <ArrowLeft size={14} /> Back to Question Bank
          </button>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[680px]">
            {/* Left 5 Cols: Problem Description & Test cases */}
            <div className="lg:col-span-5 bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between overflow-y-auto max-h-[780px]">
              <div className="space-y-4">
                <div className="flex items-center justify-between gap-2">
                  <h2 className="text-lg font-bold text-white">{selectedQuestion.title}</h2>
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full border font-semibold ${difficultyColor(
                      selectedQuestion.difficulty
                    )}`}
                  >
                    {selectedQuestion.difficulty}
                  </span>
                </div>

                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <span className="bg-slate-800 px-2 py-0.5 rounded text-slate-300 font-medium">
                    {selectedQuestion.category}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock size={12} /> {selectedQuestion.time_limit_ms}ms limit
                  </span>
                  <span className="flex items-center gap-1">
                    <Cpu size={12} /> {selectedQuestion.memory_limit_mb}MB limit
                  </span>
                </div>

                {/* Description */}
                <div className="prose prose-invert prose-sm text-slate-300 text-xs leading-relaxed whitespace-pre-line border-t border-slate-800 pt-3">
                  {selectedQuestion.description}
                </div>

                {/* Examples */}
                {selectedQuestion.examples?.length > 0 && (
                  <div className="space-y-3 pt-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Examples
                    </h3>
                    {selectedQuestion.examples.map((ex, idx) => (
                      <div
                        key={idx}
                        className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-3 text-xs font-mono space-y-1"
                      >
                        <p className="text-slate-400">
                          <strong className="text-slate-300">Input:</strong> {ex.input}
                        </p>
                        <p className="text-slate-400">
                          <strong className="text-slate-300">Output:</strong> {ex.output}
                        </p>
                        {ex.explanation && (
                          <p className="text-slate-500 font-sans text-[11px] pt-1">
                            <em>Explanation:</em> {ex.explanation}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Constraints */}
                {selectedQuestion.constraints?.length > 0 && (
                  <div className="space-y-1.5 pt-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Constraints
                    </h3>
                    <ul className="list-disc list-inside text-xs text-slate-400 space-y-1 font-mono">
                      {selectedQuestion.constraints.map((c, i) => (
                        <li key={i}>{c}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Submissions drawer summary */}
              <div className="border-t border-slate-800 pt-4 mt-6">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Recent Submissions
                </h4>
                {historyLoading ? (
                  <p className="text-xs text-slate-500">Loading history...</p>
                ) : history.length === 0 ? (
                  <p className="text-xs text-slate-500">No submissions yet for this problem.</p>
                ) : (
                  <div className="space-y-1.5">
                    {history.slice(0, 3).map((sub) => (
                      <div
                        key={sub.id}
                        className="flex items-center justify-between text-xs bg-slate-950/50 p-2 rounded-lg border border-slate-800/50"
                      >
                        <span className="font-semibold">{statusBadge(sub.status)}</span>
                        <span className="text-slate-400 font-mono text-[11px]">
                          {sub.passed_count}/{sub.total_count} passed ({sub.execution_time_ms}ms)
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Right 7 Cols: Code Editor & Execution Results */}
            <div className="lg:col-span-7 flex flex-col space-y-4">
              {/* Editor Pane */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col flex-1 shadow-xl">
                <div className="flex items-center justify-between pb-3 mb-2 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <Terminal size={14} className="text-emerald-400" />
                    <span className="text-xs font-bold text-slate-300 font-mono">
                      solution.py (Python 3.13)
                    </span>
                  </div>
                  <button
                    onClick={() => setCode(selectedQuestion.starter_code?.python || '')}
                    className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    <RotateCcw size={11} /> Reset Code
                  </button>
                </div>

                {/* Editor Textarea */}
                <textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="w-full flex-1 min-h-[340px] bg-slate-950 text-emerald-300 font-mono text-xs p-4 rounded-xl border border-slate-800 focus:outline-none focus:border-indigo-500/80 leading-relaxed resize-none selection:bg-indigo-900 selection:text-white"
                  spellCheck="false"
                  placeholder="# Write your Python solution here"
                />

                {/* Run & Action Footer */}
                <div className="flex items-center justify-between pt-3 mt-2 border-t border-slate-800">
                  <span className="text-[11px] text-slate-500">
                    Press Submit to execute against full validation test suites
                  </span>
                  <button
                    onClick={handleSubmitCode}
                    disabled={isSubmitting}
                    className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-bold px-5 py-2.5 rounded-xl shadow-lg shadow-emerald-600/20 transition-all cursor-pointer"
                  >
                    {isSubmitting ? (
                      <>
                        <RefreshCw size={13} className="animate-spin" /> Evaluating...
                      </>
                    ) : (
                      <>
                        <Play size={13} /> Submit Solution
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Execution Output Panel */}
              {submissionResult && (
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                        Verdict:
                      </span>
                      {statusBadge(submissionResult.status)}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
                      <span>
                        Passed: {submissionResult.passed_count}/{submissionResult.total_count}
                      </span>
                      <span>Latency: {submissionResult.execution_time_ms}ms</span>
                    </div>
                  </div>

                  {/* Error Message if failed */}
                  {submissionResult.error_message && (
                    <div className="bg-rose-950/40 border border-rose-800/60 text-rose-300 p-3 rounded-xl text-xs font-mono whitespace-pre-wrap">
                      {submissionResult.error_message}
                    </div>
                  )}

                  {/* Visible Test Case Inspection */}
                  {submissionResult.test_results?.length > 0 && (
                    <div className="space-y-2 pt-2 border-t border-slate-800">
                      <div className="flex gap-1.5 overflow-x-auto pb-1">
                        {submissionResult.test_results.map((tr, idx) => (
                          <button
                            key={idx}
                            onClick={() => setActiveTestTab(idx)}
                            className={`px-3 py-1 rounded-lg text-xs font-mono font-semibold transition-all ${
                              activeTestTab === idx
                                ? 'bg-indigo-600 text-white'
                                : tr.status === 'Passed'
                                ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-900/50'
                                : 'bg-rose-950/40 text-rose-400 border border-rose-900/50'
                            }`}
                          >
                            Case {idx + 1}
                          </button>
                        ))}
                      </div>

                      {submissionResult.test_results[activeTestTab] && (
                        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80 font-mono text-xs space-y-1.5 text-slate-300">
                          <div>
                            <span className="text-slate-500">Input: </span>
                            {JSON.stringify(submissionResult.test_results[activeTestTab].input)}
                          </div>
                          <div>
                            <span className="text-slate-500">Expected: </span>
                            <span className="text-emerald-400">
                              {JSON.stringify(submissionResult.test_results[activeTestTab].expected)}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500">Actual Output: </span>
                            <span
                              className={
                                submissionResult.test_results[activeTestTab].status === 'Passed'
                                  ? 'text-emerald-400'
                                  : 'text-rose-400 font-bold'
                              }
                            >
                              {JSON.stringify(submissionResult.test_results[activeTestTab].actual)}
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-500 pt-1">
                            Status: {submissionResult.test_results[activeTestTab].status} (
                            {submissionResult.test_results[activeTestTab].time_ms}ms)
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : activeTab === 'analytics' ? (
        /* VIEW 2: Topic Mastery & Analytics */
        <div className="space-y-6">
          {analyticsLoading ? (
            <div className="text-center py-12 text-slate-400 flex justify-center items-center gap-2">
              <RefreshCw className="animate-spin" size={18} />
              Loading your DSA competency profiles...
            </div>
          ) : analytics ? (
            <div className="space-y-6">
              {/* Stat Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl shadow-lg">
                  <div className="flex items-center justify-between text-slate-400 mb-2">
                    <span className="text-xs font-semibold uppercase">Problems Solved</span>
                    <Award className="text-indigo-400" size={18} />
                  </div>
                  <div className="text-3xl font-extrabold text-white">
                    {analytics.total_solved}{' '}
                    <span className="text-xs text-slate-500 font-normal">
                      / {analytics.total_questions}
                    </span>
                  </div>
                  <div className="text-[11px] text-emerald-400 mt-1 font-semibold">
                    {analytics.overall_solve_pct}% curriculum coverage
                  </div>
                </div>

                <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl shadow-lg">
                  <div className="flex items-center justify-between text-slate-400 mb-2">
                    <span className="text-xs font-semibold uppercase">Submissions Accuracy</span>
                    <Zap className="text-amber-400" size={18} />
                  </div>
                  <div className="text-3xl font-extrabold text-white">
                    {analytics.overall_accuracy_pct}%
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Across {analytics.total_submissions} total code runs
                  </div>
                </div>

                <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl shadow-lg sm:col-span-2">
                  <div className="flex items-center justify-between text-slate-400 mb-2">
                    <span className="text-xs font-semibold uppercase">Weakness Identification</span>
                    <AlertTriangle className="text-rose-400" size={18} />
                  </div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {analytics.weakness_areas?.length > 0 ? (
                      analytics.weakness_areas.map((w, i) => (
                        <span
                          key={i}
                          className="bg-rose-950/60 border border-rose-800/60 text-rose-300 text-xs px-2.5 py-1 rounded-lg font-semibold"
                        >
                          {w}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-emerald-400 font-semibold">
                        No critical weakness patterns detected! Keep up the momentum.
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Topic Breakdown Bars */}
              <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-2xl shadow-xl space-y-4">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <BookOpen className="text-indigo-400" size={18} />
                  Topic-wise Proficiency Breakdown
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  {analytics.topic_breakdown?.map((topic, idx) => {
                    const pct =
                      topic.total_questions > 0
                        ? Math.round((topic.solved_questions / topic.total_questions) * 100)
                        : 0;
                    return (
                      <div
                        key={idx}
                        className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/80 space-y-2"
                      >
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-bold text-white">{topic.category}</span>
                          <span className="text-slate-400 font-mono">
                            {topic.solved_questions}/{topic.total_questions} ({pct}%)
                          </span>
                        </div>
                        {/* Progress Bar */}
                        <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              pct >= 70
                                ? 'bg-emerald-500'
                                : pct >= 40
                                ? 'bg-amber-500'
                                : 'bg-indigo-500'
                            }`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <div className="flex justify-between text-[11px] text-slate-500">
                          <span>Accuracy: {topic.accuracy_pct}%</span>
                          <span>{pct === 100 ? 'Mastered' : 'In Progress'}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Actionable Recommendations */}
              {analytics.recommendations?.length > 0 && (
                <div className="bg-indigo-950/30 border border-indigo-800/40 p-5 rounded-2xl space-y-3">
                  <h4 className="text-sm font-bold text-indigo-300 flex items-center gap-2">
                    <Award size={16} /> Targeted Placement Recommendations
                  </h4>
                  <ul className="space-y-2">
                    {analytics.recommendations.map((rec, i) => (
                      <li key={i} className="text-xs text-indigo-200/90 flex items-start gap-2">
                        <ChevronRight size={14} className="mt-0.5 text-indigo-400 shrink-0" />
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <p className="text-slate-400 text-sm">Failed to load analytics data.</p>
          )}
        </div>
      ) : (
        /* VIEW 3: Question Bank List */
        <div className="space-y-5">
          {/* Filters Bar */}
          <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-2xl flex flex-col md:flex-row gap-4 justify-between items-stretch md:items-center">
            {/* Search */}
            <div className="relative flex-1 max-w-md">
              <Search
                size={16}
                className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
              />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search coding problems by name or concept..."
                className="w-full bg-slate-950 text-slate-200 text-xs pl-10 pr-4 py-2.5 rounded-xl border border-slate-800 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* Category Dropdown & Difficulty Filter */}
            <div className="flex flex-wrap items-center gap-2.5">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="bg-slate-950 text-slate-300 text-xs px-3 py-2 rounded-xl border border-slate-800 focus:outline-none focus:border-indigo-500"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>

              <select
                value={selectedDifficulty}
                onChange={(e) => setSelectedDifficulty(e.target.value)}
                className="bg-slate-950 text-slate-300 text-xs px-3 py-2 rounded-xl border border-slate-800 focus:outline-none focus:border-indigo-500"
              >
                <option value="">All Difficulties</option>
                <option value="Easy">Easy</option>
                <option value="Medium">Medium</option>
                <option value="Hard">Hard</option>
              </select>
            </div>
          </div>

          {/* Questions Grid / Table */}
          {questionsLoading ? (
            <div className="text-center py-16 text-slate-500 flex justify-center items-center gap-2">
              <RefreshCw className="animate-spin" size={18} />
              Loading question bank...
            </div>
          ) : questionsError ? (
            <div className="bg-rose-950/40 border border-rose-800 p-4 rounded-2xl text-rose-300 text-sm">
              {questionsError}
            </div>
          ) : questions.length === 0 ? (
            <div className="text-center py-16 text-slate-500">
              No questions found matching your filter criteria.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {questions.map((q) => (
                <div
                  key={q.id}
                  onClick={() => handleSelectQuestion(q)}
                  className="bg-slate-900/70 border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-900 p-5 rounded-2xl transition-all duration-200 cursor-pointer flex flex-col justify-between group shadow-lg"
                >
                  <div className="space-y-2.5">
                    <div className="flex items-start justify-between gap-2">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${difficultyColor(
                          q.difficulty
                        )}`}
                      >
                        {q.difficulty}
                      </span>
                      {q.is_solved && (
                        <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-semibold bg-emerald-950/40 border border-emerald-900/60 px-2 py-0.5 rounded-full">
                          <Check size={11} /> Solved
                        </span>
                      )}
                    </div>
                    <h3 className="text-sm font-bold text-white group-hover:text-indigo-400 transition-colors">
                      {q.title}
                    </h3>
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-500 pt-4 mt-2 border-t border-slate-800/60">
                    <span className="bg-slate-800/80 px-2 py-0.5 rounded text-slate-400 text-[11px]">
                      {q.category}
                    </span>
                    <span className="text-indigo-400 font-semibold flex items-center gap-1 text-xs group-hover:translate-x-1 transition-transform">
                      Solve <ChevronRight size={14} />
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default DsaAssessmentPage;
