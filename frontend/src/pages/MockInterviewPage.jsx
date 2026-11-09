import React, { useState, useEffect, useRef } from 'react';
import { interviewAPI } from '../api/client';
import {
  Bot,
  User,
  Send,
  Sparkles,
  History,
  Award,
  AlertCircle,
  CheckCircle2,
  TrendingUp,
  Clock,
  RotateCcw,
  BookOpen,
  HelpCircle,
  RefreshCw,
  Target,
} from 'lucide-react';

const COMMON_ROLES = [
  'Backend Developer (Python/FastAPI)',
  'Frontend Engineer (React/TypeScript)',
  'Associate AI & ML Research Engineer',
  'Full Stack Software Engineer',
  'DevOps & Cloud Associate',
];

function scoreColor(score) {
  if (score >= 75) return 'text-emerald-400';
  if (score >= 50) return 'text-amber-400';
  return 'text-rose-400';
}

function scoreBg(score) {
  if (score >= 75) return 'bg-emerald-500';
  if (score >= 50) return 'bg-amber-500';
  return 'bg-rose-500';
}

export function MockInterviewPage() {
  const [activeTab, setActiveTab] = useState('interview'); // 'interview' | 'history'

  // Setup state
  const [roleTitle, setRoleTitle] = useState(COMMON_ROLES[0]);
  const [interviewType, setInterviewType] = useState('Technical');
  const [totalQuestions, setTotalQuestions] = useState(4);
  const [isStarting, setIsStarting] = useState(false);

  // Active session state
  const [currentSession, setCurrentSession] = useState(null);
  const [answerInput, setAnswerInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [turnEvaluation, setTurnEvaluation] = useState(null);

  // History state
  const [historyList, setHistoryList] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const messagesEndRef = useRef(null);

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentSession?.messages, turnEvaluation]);

  // Load history on tab switch
  useEffect(() => {
    if (activeTab === 'history') {
      loadHistory();
    }
  }, [activeTab]);

  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      const data = await interviewAPI.listSessions();
      setHistoryList(data.items || []);
    } catch {
      setHistoryList([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  // Start Session
  const handleStartInterview = async (e) => {
    e?.preventDefault();
    setIsStarting(true);
    setTurnEvaluation(null);
    try {
      const session = await interviewAPI.startSession({
        role_title: roleTitle,
        interview_type: interviewType,
        total_questions: totalQuestions,
      });
      setCurrentSession(session);
      setAnswerInput('');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to initialize interview session.');
    } finally {
      setIsStarting(false);
    }
  };

  // Submit Answer
  const handleSubmitAnswer = async () => {
    if (!currentSession || !answerInput.trim()) return;
    setIsSubmitting(true);
    setTurnEvaluation(null);
    try {
      const turn = await interviewAPI.submitAnswer(currentSession.id, {
        answer_text: answerInput.trim(),
      });
      setTurnEvaluation(turn.evaluation);
      setCurrentSession(turn.session);
      setAnswerInput('');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to submit answer.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Re-inspect past session
  const handleInspectPastSession = async (sessId) => {
    try {
      const full = await interviewAPI.getSession(sessId);
      setCurrentSession(full);
      setActiveTab('interview');
    } catch (err) {
      alert('Could not load session transcript.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Bot className="text-indigo-400" size={26} />
            AI Mock Interview
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">
            Adaptive multi-turn interview simulator with structured rubric scoring & STAR feedback
          </p>
        </div>

        {/* Tab switch */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 p-1 rounded-xl self-start md:self-auto">
          <button
            onClick={() => setActiveTab('interview')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'interview'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Live Session
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'history'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <History size={13} />
            Session History
          </button>
        </div>
      </div>

      {activeTab === 'history' ? (
        /* History View */
        <div className="space-y-4">
          <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider">
            Past Interview Evaluations
          </h2>
          {historyLoading ? (
            <div className="text-center py-12 text-slate-500 flex justify-center items-center gap-2">
              <RefreshCw className="animate-spin" size={16} /> Loading sessions...
            </div>
          ) : historyList.length === 0 ? (
            <div className="text-center py-12 text-slate-500 bg-slate-900/40 rounded-2xl border border-slate-800 p-8">
              No interview sessions completed yet. Start your first session to practice!
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {historyList.map((h) => (
                <div
                  key={h.id}
                  onClick={() => handleInspectPastSession(h.id)}
                  className="bg-slate-900/80 border border-slate-800 hover:border-indigo-500/50 p-5 rounded-2xl cursor-pointer transition-all shadow-lg space-y-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-xs bg-indigo-950/70 border border-indigo-800/60 text-indigo-300 px-2 py-0.5 rounded font-medium">
                      {h.interview_type}
                    </span>
                    <span
                      className={`text-sm font-extrabold font-mono ${scoreColor(h.overall_score)}`}
                    >
                      {h.overall_score.toFixed(0)}%
                    </span>
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white line-clamp-1">{h.role_title}</h3>
                    <p className="text-[11px] text-slate-500 mt-1">
                      {new Date(h.created_at).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}{' '}
                      · {h.total_questions} Questions
                    </p>
                  </div>
                  <div className="text-xs text-indigo-400 font-semibold flex items-center justify-end">
                    Review Transcript →
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : !currentSession ? (
        /* Setup / Start Interview Screen */
        <div className="max-w-2xl mx-auto bg-slate-900/80 border border-slate-800 rounded-3xl p-8 shadow-2xl space-y-6">
          <div>
            <span className="text-xs font-bold text-indigo-400 uppercase tracking-widest bg-indigo-950/60 border border-indigo-800/50 px-2.5 py-1 rounded-full">
              Configuration
            </span>
            <h2 className="text-xl font-bold text-white mt-3">Prepare Your Mock Interview</h2>
            <p className="text-xs text-slate-400 mt-1">
              Questions adapt in real time to your answers and integrate details from your uploaded
              resume projects.
            </p>
          </div>

          <form onSubmit={handleStartInterview} className="space-y-5">
            {/* Role Title */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">Target Role Title</label>
              <select
                value={roleTitle}
                onChange={(e) => setRoleTitle(e.target.value)}
                className="w-full bg-slate-950 text-slate-200 text-xs px-3.5 py-3 rounded-xl border border-slate-800 focus:outline-none focus:border-indigo-500"
              >
                {COMMON_ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>

            {/* Interview Track */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">Interview Mode</label>
              <div className="grid grid-cols-3 gap-2.5">
                {['Technical', 'Behavioral', 'System Design'].map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setInterviewType(type)}
                    className={`py-2.5 px-3 rounded-xl text-xs font-semibold border transition-all text-center cursor-pointer ${
                      interviewType === type
                        ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-600/30'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>

            {/* Total Questions */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Question Count ({totalQuestions} Turns)
              </label>
              <div className="flex gap-3">
                {[3, 4, 5].map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setTotalQuestions(num)}
                    className={`flex-1 py-2 rounded-xl text-xs font-bold border transition-all cursor-pointer ${
                      totalQuestions === num
                        ? 'bg-slate-800 border-slate-600 text-white'
                        : 'bg-slate-950 border-slate-800 text-slate-500 hover:text-slate-300'
                    }`}
                  >
                    {num} Questions
                  </button>
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={isStarting}
              className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs uppercase tracking-wider rounded-xl shadow-xl shadow-indigo-600/25 transition-all flex justify-center items-center gap-2 cursor-pointer mt-4"
            >
              {isStarting ? (
                <>
                  <RefreshCw className="animate-spin" size={16} /> Initializing Interview Session...
                </>
              ) : (
                <>
                  <Sparkles size={16} /> Begin Mock Interview
                </>
              )}
            </button>
          </form>
        </div>
      ) : (
        /* Active Interview & Report Workspace */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[640px]">
          {/* Left Column: Dialog & Messages */}
          <div className="lg:col-span-8 flex flex-col bg-slate-900/80 border border-slate-800 rounded-3xl p-5 shadow-xl">
            {/* Session Top Bar */}
            <div className="flex items-center justify-between pb-3.5 mb-3 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs font-bold text-white">{currentSession.role_title}</span>
                <span className="text-[11px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded">
                  {currentSession.interview_type}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-slate-400">
                  Turn {Math.min(currentSession.current_question_index + 1, currentSession.total_questions)} of{' '}
                  {currentSession.total_questions}
                </span>
                <button
                  onClick={() => setCurrentSession(null)}
                  className="text-[11px] text-slate-500 hover:text-slate-300"
                >
                  New Session
                </button>
              </div>
            </div>

            {/* Conversation Messages */}
            <div className="flex-1 overflow-y-auto space-y-4 pr-1 max-h-[500px]">
              {currentSession.messages?.map((msg, idx) => (
                <div key={idx} className="space-y-3">
                  {/* Interviewer Message */}
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-xl bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center shrink-0 text-indigo-300">
                      <Bot size={18} />
                    </div>
                    <div className="bg-slate-950 border border-slate-800/90 rounded-2xl rounded-tl-none p-4 max-w-[85%] text-xs text-slate-200 leading-relaxed shadow-sm">
                      <p className="font-semibold text-indigo-300 mb-1 text-[11px]">Interviewer</p>
                      {msg.question_text}
                    </div>
                  </div>

                  {/* Student Answer */}
                  {msg.answer_text && (
                    <div className="flex items-start justify-end gap-3">
                      <div className="bg-indigo-950/50 border border-indigo-800/40 rounded-2xl rounded-tr-none p-4 max-w-[85%] text-xs text-slate-200 leading-relaxed shadow-sm">
                        <p className="font-semibold text-slate-400 mb-1 text-[11px] text-right">You</p>
                        {msg.answer_text}
                      </div>
                      <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0 text-slate-300">
                        <User size={16} />
                      </div>
                    </div>
                  )}

                  {/* Per-Turn Rubric Card */}
                  {msg.evaluation?.overall_score && (
                    <div className="ml-11 bg-slate-950/70 border border-slate-800 p-3.5 rounded-xl space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-300">Answer Evaluation</span>
                        <span
                          className={`font-extrabold font-mono ${scoreColor(
                            msg.evaluation.overall_score
                          )}`}
                        >
                          Score: {msg.evaluation.overall_score}%
                        </span>
                      </div>
                      <p className="text-slate-400 text-[11px] leading-relaxed">
                        {msg.evaluation.feedback}
                      </p>
                      {msg.evaluation.model_answer_hint && (
                        <p className="text-indigo-400/90 text-[11px] bg-indigo-950/30 p-2 rounded border border-indigo-900/30">
                          💡 <em>Key tip:</em> {msg.evaluation.model_answer_hint}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Answer Box (If session is active) */}
            {currentSession.status === 'in_progress' ? (
              <div className="pt-3 mt-3 border-t border-slate-800 space-y-2">
                <textarea
                  value={answerInput}
                  onChange={(e) => setAnswerInput(e.target.value)}
                  placeholder="Type your response... (Use the STAR framework: Situation, Task, Action, Result)"
                  rows={4}
                  className="w-full bg-slate-950 text-slate-200 text-xs p-3.5 rounded-2xl border border-slate-800 focus:outline-none focus:border-indigo-500 leading-relaxed resize-none"
                />
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-slate-500 font-mono">
                    {answerInput.trim().split(/\s+/).filter(Boolean).length} words
                  </span>
                  <button
                    onClick={handleSubmitAnswer}
                    disabled={isSubmitting || !answerInput.trim()}
                    className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-xs font-bold px-4 py-2 rounded-xl transition-all cursor-pointer shadow-lg shadow-indigo-600/20"
                  >
                    {isSubmitting ? (
                      <>
                        <RefreshCw className="animate-spin" size={13} /> Analyzing...
                      </>
                    ) : (
                      <>
                        <Send size={13} /> Submit Response
                      </>
                    )}
                  </button>
                </div>
              </div>
            ) : (
              <div className="pt-4 mt-3 border-t border-slate-800 flex items-center justify-between">
                <span className="text-xs text-emerald-400 font-bold flex items-center gap-1.5">
                  <CheckCircle2 size={15} /> Interview Session Completed
                </span>
                <button
                  onClick={() => setCurrentSession(null)}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold px-4 py-2 rounded-xl"
                >
                  Start New Session
                </button>
              </div>
            )}
          </div>

          {/* Right Column: Multi-Dimensional Performance Summary */}
          <div className="lg:col-span-4 bg-slate-900/80 border border-slate-800 rounded-3xl p-5 shadow-xl space-y-5">
            <div>
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Performance Rubric
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                <span
                  className={`text-3xl font-extrabold font-mono ${scoreColor(
                    currentSession.overall_score || 70
                  )}`}
                >
                  {currentSession.overall_score > 0
                    ? `${currentSession.overall_score}%`
                    : 'In Progress'}
                </span>
                {currentSession.overall_score > 0 && (
                  <span className="text-[11px] text-slate-500">Overall Rating</span>
                )}
              </div>
            </div>

            {/* Rubric Breakdown Progress Bars */}
            <div className="space-y-3 pt-2">
              {[
                {
                  label: 'Technical Accuracy & Depth',
                  score: currentSession.technical_score || 70,
                },
                {
                  label: 'Communication & Structure',
                  score: currentSession.communication_score || 75,
                },
                {
                  label: 'Problem Solving & Scale',
                  score: currentSession.problem_solving_score || 65,
                },
                {
                  label: 'Relevance to Role',
                  score: currentSession.relevance_score || 80,
                },
              ].map((dim, i) => (
                <div key={i} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400 text-[11px]">{dim.label}</span>
                    <span className="font-mono font-bold text-slate-300 text-[11px]">
                      {currentSession.status === 'completed' ? `${dim.score}%` : '—'}
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${scoreBg(
                        dim.score
                      )}`}
                      style={{
                        width: currentSession.status === 'completed' ? `${dim.score}%` : '0%',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Strengths & Weaknesses (when completed) */}
            {currentSession.status === 'completed' && (
              <div className="space-y-4 pt-3 border-t border-slate-800">
                {currentSession.strengths?.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold text-emerald-400 flex items-center gap-1.5 mb-2">
                      <CheckCircle2 size={13} /> Key Strengths
                    </h4>
                    <ul className="space-y-1.5 text-[11px] text-slate-300">
                      {currentSession.strengths.map((s, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-emerald-400">•</span>
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {currentSession.improvement_areas?.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold text-amber-400 flex items-center gap-1.5 mb-2">
                      <TrendingUp size={13} /> Recommended Growth Areas
                    </h4>
                    <ul className="space-y-1.5 text-[11px] text-slate-300">
                      {currentSession.improvement_areas.map((a, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-amber-400">•</span>
                          {a}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default MockInterviewPage;
