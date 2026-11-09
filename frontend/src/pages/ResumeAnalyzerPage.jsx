import React, { useState, useEffect, useRef } from 'react';
import { resumeAPI } from '../api/client';
import {
  FileText,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  Trash2,
  Clock,
  Sparkles,
  Layers,
  Code2,
  GraduationCap,
  Briefcase,
  FolderGit2,
  ExternalLink,
  Info,
  Loader2,
  FileCheck,
  ShieldCheck,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';

export const ResumeAnalyzerPage = () => {
  const [resumes, setResumes] = useState([]);
  const [selectedResume, setSelectedResume] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'skills' | 'sections' | 'ai_feedback'

  const fileInputRef = useRef(null);

  useEffect(() => {
    loadResumes();
  }, []);

  const loadResumes = async (selectId = null) => {
    setIsLoading(true);
    setError('');
    try {
      const data = await resumeAPI.listResumes();
      setResumes(data.resumes || []);

      if (data.resumes && data.resumes.length > 0) {
        const targetId = selectId || data.resumes[0].id;
        await loadResumeDetail(targetId);
      } else {
        setSelectedResume(null);
      }
    } catch (err) {
      setError('Unable to load resume history.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadResumeDetail = async (id) => {
    try {
      const detail = await resumeAPI.getResumeAnalysis(id);
      setSelectedResume(detail);
    } catch (err) {
      setError('Failed to fetch detailed analysis for selected resume.');
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  };

  const handleFileSelected = async (file) => {
    setError('');
    setSuccessMsg('');

    // Check extension
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF documents (.pdf) are accepted.');
      return;
    }

    // Check size (5MB max)
    const maxBytes = 5 * 1024 * 1024;
    if (file.size > maxBytes) {
      setError('File size exceeds the 5MB limit.');
      return;
    }

    setIsUploading(true);
    setUploadProgress('Extracting text with PyMuPDF & parsing sections...');

    try {
      setTimeout(() => setUploadProgress('Extracting technical skills & computing scores...'), 1200);
      setTimeout(() => setUploadProgress('Synthesizing placement recommendations...'), 2400);

      const result = await resumeAPI.uploadResume(file);
      setSuccessMsg(`Successfully analyzed ${file.name} (Version ${result.version})`);
      await loadResumes(result.id);
    } catch (err) {
      const detail = err.response?.data?.detail || 'Error uploading and analyzing resume.';
      setError(detail);
    } finally {
      setIsUploading(false);
      setUploadProgress('');
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this resume version?')) return;
    try {
      await resumeAPI.deleteResume(id);
      setSuccessMsg('Resume version removed.');
      await loadResumes();
    } catch (err) {
      setError('Could not delete resume version.');
    }
  };

  const getScoreBadge = (score) => {
    if (score >= 80) {
      return { label: 'High Readiness', bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' };
    }
    if (score >= 60) {
      return { label: 'Moderate Fit', bg: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30' };
    }
    return { label: 'Needs Optimization', bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30' };
  };

  // Group extracted skills by category
  const skillsByCategory = (selectedResume?.extracted_skills || []).reduce((acc, skill) => {
    const cat = skill.category_name || 'Other Skills';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(skill.name);
    return acc;
  }, {});

  return (
    <div className="space-y-6 pb-12">
      {/* ── Page Header ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Module 1 Active
            </span>
            <span className="text-xs text-slate-400">· PyMuPDF + Rule-based Scorer + Gemini 2.5 Flash</span>
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            AI Resume Analyzer & ATS Profiler
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Upload your resume PDF to extract structural sections, benchmark technical skills, calculate placement readiness scores, and receive actionable ATS feedback.
          </p>
        </div>

        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="shrink-0 inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50"
        >
          <UploadCloud className="w-4 h-4" />
          <span>Upload New Version</span>
        </button>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError('')} className="text-rose-400 hover:text-rose-200">×</button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg('')} className="text-emerald-400 hover:text-emerald-200">×</button>
        </div>
      )}

      {/* ── Drag & Drop Upload Zone (Compact or Hero) ── */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        className="hidden"
        onChange={handleFileChange}
      />

      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative cursor-pointer rounded-2xl border-2 border-dashed p-6 sm:p-8 text-center transition-all ${
          dragActive
            ? 'border-indigo-500 bg-indigo-500/10'
            : 'border-slate-800 hover:border-slate-700 bg-slate-900/40 hover:bg-slate-900/60'
        }`}
      >
        <div className="flex flex-col items-center justify-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            {isUploading ? (
              <Loader2 className="w-6 h-6 animate-spin" />
            ) : (
              <UploadCloud className="w-6 h-6" />
            )}
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-200">
              {isUploading ? uploadProgress : 'Drop your resume PDF here, or click to browse'}
            </p>
            <p className="text-[11px] text-slate-400 mt-1">
              Supports standard single/multi-page PDFs up to 5MB. Stored securely and privately.
            </p>
          </div>
        </div>
      </div>

      {/* ── Main Work Area: Version Selector + Active Resume Analysis ── */}
      {isLoading ? (
        <div className="p-16 flex flex-col items-center justify-center text-slate-400 gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
          <p className="text-xs font-medium tracking-wide">Loading resume intelligence...</p>
        </div>
      ) : !selectedResume ? (
        <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800 space-y-3">
          <FileText className="w-10 h-10 text-slate-500 mx-auto" />
          <h3 className="text-sm font-bold text-slate-200">No Resumes Uploaded Yet</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Upload your campus placement resume above. Our PyMuPDF parsing engine will automatically analyze your sections and skills.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Version Selector Tabs & File Meta */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
              <span className="text-xs text-slate-400 font-semibold mr-1 shrink-0">Versions:</span>
              {resumes.map((r) => (
                <button
                  key={r.id}
                  onClick={() => loadResumeDetail(r.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold shrink-0 transition-all flex items-center gap-1.5 ${
                    selectedResume.id === r.id
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <span>v{r.version}</span>
                  <span className="text-[10px] opacity-75 font-mono">({Math.round(r.overall_score)}%)</span>
                </button>
              ))}
            </div>

            <div className="flex items-center gap-3 text-xs text-slate-400 shrink-0">
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                {new Date(selectedResume.created_at).toLocaleDateString()}
              </span>
              <span>·</span>
              <span>{Math.round(selectedResume.file_size_bytes / 1024)} KB</span>
              <span>·</span>
              <button
                onClick={() => handleDelete(selectedResume.id)}
                title="Delete this version"
                className="p-1 rounded text-slate-500 hover:text-rose-400 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* ── Score & KPI Overview Cards ── */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Overall Score */}
            <div className="md:col-span-1 p-6 rounded-2xl bg-gradient-to-br from-indigo-950/60 via-slate-900/60 to-slate-900 border border-indigo-500/30 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Resume Score
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getScoreBadge(selectedResume.overall_score).bg}`}>
                    {getScoreBadge(selectedResume.overall_score).label}
                  </span>
                </div>
                <div className="flex items-baseline gap-2 mt-3">
                  <span className="text-5xl font-black text-white tracking-tight">
                    {Math.round(selectedResume.overall_score)}
                  </span>
                  <span className="text-slate-400 text-sm font-semibold">/ 100</span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
                <span>Weight in PlacementIQ</span>
                <span className="font-mono text-indigo-400 font-bold">15%</span>
              </div>
            </div>

            {/* Component Breakdown Cards */}
            <div className="md:col-span-3 grid grid-cols-2 sm:grid-cols-5 gap-3">
              {[
                { label: 'Structure', score: selectedResume.score_breakdown?.structure_score ?? 0, max: 25, icon: Layers },
                { label: 'Skills', score: selectedResume.score_breakdown?.skills_score ?? 0, max: 25, icon: Code2 },
                { label: 'Projects', score: selectedResume.score_breakdown?.projects_score ?? 0, max: 20, icon: FolderGit2 },
                { label: 'Education', score: selectedResume.score_breakdown?.education_score ?? 0, max: 15, icon: GraduationCap },
                { label: 'Experience', score: selectedResume.score_breakdown?.experience_score ?? 0, max: 15, icon: Briefcase },
              ].map((comp) => (
                <div key={comp.label} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-slate-400 mb-2">
                    <comp.icon className="w-4 h-4 text-indigo-400" />
                    <span className="text-[10px] text-slate-500 font-mono">max {comp.max}</span>
                  </div>
                  <div>
                    <div className="flex items-baseline justify-between text-xs mb-1">
                      <span className="font-semibold text-slate-300">{comp.label}</span>
                      <span className="font-mono font-bold text-white">{comp.score}</span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-indigo-500 h-full rounded-full transition-all"
                        style={{ width: `${(comp.score / comp.max) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ── Sub-Navigation Tabs ── */}
          <div className="flex border-b border-slate-800 space-x-6 text-xs font-semibold">
            {[
              { id: 'overview', label: 'Evaluation & Suggestions', count: selectedResume.strengths?.length },
              { id: 'skills', label: 'Extracted Skills Inventory', count: selectedResume.extracted_skills?.length },
              { id: 'sections', label: 'Detected Sections' },
              { id: 'raw_text', label: 'Raw Extracted Text' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`pb-3 transition-colors flex items-center gap-1.5 ${
                  activeTab === tab.id
                    ? 'border-b-2 border-indigo-500 text-indigo-400 font-bold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <span>{tab.label}</span>
                {tab.count !== undefined && (
                  <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[10px] text-slate-400">
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* ── TAB 1: Evaluation & AI Recommendations ── */}
          {activeTab === 'overview' && (
            <div className="space-y-5">
              {/* Executive Summary */}
              {selectedResume.ai_feedback?.summary && (
                <div className="p-5 rounded-2xl bg-indigo-950/20 border border-indigo-500/20">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-indigo-400" />
                      Advisor Assessment Summary
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
                      {selectedResume.ai_feedback?.model || 'PlacementIQ AI'}
                    </span>
                  </div>
                  <p className="text-xs sm:text-sm text-slate-200 leading-relaxed">
                    {selectedResume.ai_feedback.summary}
                  </p>
                </div>
              )}

              {/* Strengths & Improvement Areas Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Detected Strengths */}
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <h3 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    Identified Strengths ({selectedResume.strengths?.length || 0})
                  </h3>
                  <ul className="space-y-2">
                    {(selectedResume.strengths || []).map((s, idx) => (
                      <li key={idx} className="text-xs text-slate-300 flex items-start gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/80">
                        <span className="text-emerald-400 font-bold shrink-0">✓</span>
                        <span>{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Improvement Areas */}
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    Areas to Refine ({selectedResume.improvement_areas?.length || 0})
                  </h3>
                  <ul className="space-y-2">
                    {(selectedResume.improvement_areas || []).map((imp, idx) => (
                      <li key={idx} className="text-xs text-slate-300 flex items-start gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/80">
                        <span className="text-amber-400 font-bold shrink-0">!</span>
                        <span>{imp}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Actionable Tips & ATS Recommendations */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Actionable Tips */}
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-indigo-400" />
                    Actionable Improvement Tips
                  </h3>
                  <ul className="space-y-2">
                    {(selectedResume.ai_feedback?.actionable_tips || []).map((tip, idx) => (
                      <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                        <ArrowRight className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* ATS Compliance Advice */}
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <h3 className="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-purple-400" />
                    ATS Parser Best Practices
                  </h3>
                  <ul className="space-y-2">
                    {(selectedResume.ai_feedback?.ats_recommendations || []).map((ats, idx) => (
                      <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                        <ArrowRight className="w-3.5 h-3.5 text-purple-400 shrink-0 mt-0.5" />
                        <span>{ats}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Disclaimer */}
              <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/80 flex items-start gap-3 text-slate-400 text-xs">
                <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                <p>{selectedResume.disclaimer}</p>
              </div>
            </div>
          )}

          {/* ── TAB 2: Extracted Skills Inventory ── */}
          {activeTab === 'skills' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white">Extracted Skills Taxonomy</h3>
                  <p className="text-xs text-slate-400">
                    High-precision token-matched technical skills categorized from resume content.
                  </p>
                </div>
                <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  {selectedResume.extracted_skills?.length || 0} Skills Detected
                </span>
              </div>

              {Object.keys(skillsByCategory).length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-400">
                  No skills extracted. Ensure technical terms are clearly listed.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(skillsByCategory).map(([catName, skills]) => (
                    <div key={catName} className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-xs font-bold text-indigo-300 uppercase tracking-wider">{catName}</h4>
                        <span className="text-[10px] font-mono text-slate-500">{skills.length}</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {skills.map((s) => (
                          <span
                            key={s}
                            className="px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-950 border border-slate-800 text-slate-200 shadow-sm"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── TAB 3: Detected Structural Sections ── */}
          {activeTab === 'sections' && (
            <div className="space-y-4">
              {/* Contact Information */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
                <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Contact Information</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs pt-1">
                  <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                    <span className="text-[10px] text-slate-500 block">Email</span>
                    <span className="font-mono text-slate-200">{selectedResume.parsed_data?.contact?.email || 'Not found'}</span>
                  </div>
                  <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                    <span className="text-[10px] text-slate-500 block">Phone</span>
                    <span className="font-mono text-slate-200">{selectedResume.parsed_data?.contact?.phone || 'Not found'}</span>
                  </div>
                  <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                    <span className="text-[10px] text-slate-500 block">GitHub</span>
                    {selectedResume.parsed_data?.contact?.github ? (
                      <a href={selectedResume.parsed_data.contact.github} target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline flex items-center gap-1 font-mono">
                        View Profile <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <span className="text-slate-500 font-mono">Not found</span>
                    )}
                  </div>
                  <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                    <span className="text-[10px] text-slate-500 block">LinkedIn</span>
                    {selectedResume.parsed_data?.contact?.linkedin ? (
                      <a href={selectedResume.parsed_data.contact.linkedin} target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline flex items-center gap-1 font-mono">
                        View Profile <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <span className="text-slate-500 font-mono">Not found</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Education */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Education</h4>
                {selectedResume.parsed_data?.education?.length > 0 ? (
                  <div className="space-y-2">
                    {selectedResume.parsed_data.education.map((edu, idx) => (
                      <div key={idx} className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80 text-xs">
                        <p className="font-bold text-slate-200">{edu.degree}</p>
                        {edu.details && <p className="text-slate-400 mt-1">{edu.details}</p>}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">No education entries segmented.</p>
                )}
              </div>

              {/* Projects */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Projects</h4>
                {selectedResume.parsed_data?.projects?.length > 0 ? (
                  <div className="space-y-2.5">
                    {selectedResume.parsed_data.projects.map((proj, idx) => (
                      <div key={idx} className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80 text-xs">
                        <p className="font-bold text-slate-200">{proj.title}</p>
                        {proj.description && <p className="text-slate-400 mt-1 leading-relaxed">{proj.description}</p>}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">No project entries segmented.</p>
                )}
              </div>

              {/* Experience */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Experience & Internships</h4>
                {selectedResume.parsed_data?.experience?.length > 0 ? (
                  <div className="space-y-2.5">
                    {selectedResume.parsed_data.experience.map((exp, idx) => (
                      <div key={idx} className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80 text-xs">
                        <p className="font-bold text-slate-200">{exp.title}</p>
                        {exp.description && <p className="text-slate-400 mt-1 leading-relaxed">{exp.description}</p>}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">No work or internship entries segmented.</p>
                )}
              </div>
            </div>
          )}

          {/* ── TAB 4: Raw Text ── */}
          {activeTab === 'raw_text' && (
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Raw Text from PyMuPDF
                </h4>
                <span className="text-[10px] text-slate-500 font-mono">
                  {selectedResume.page_count} Page{selectedResume.page_count > 1 ? 's' : ''} · {selectedResume.raw_text?.length || 0} characters
                </span>
              </div>
              <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300 max-h-96 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                {selectedResume.raw_text}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
