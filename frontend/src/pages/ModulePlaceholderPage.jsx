import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Clock, Sparkles } from 'lucide-react';

export const ModulePlaceholderPage = ({ title, moduleNumber, tech, description, pipelineSteps }) => {
  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      <Link
        to="/dashboard"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-indigo-400 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </Link>

      <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-indigo-500/10 blur-[80px] rounded-full pointer-events-none" />

        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Module {moduleNumber}
            </span>
            <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Scheduled for Phase 2 Implementation
            </span>
          </div>

          <h1 className="text-2xl font-extrabold text-white tracking-tight mt-2">
            {title}
          </h1>
          <p className="text-sm text-slate-300 mt-2 leading-relaxed">
            {description}
          </p>

          <div className="mt-4 p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 inline-block text-xs font-mono text-indigo-300">
            Tech Engine: <span className="text-slate-200">{tech}</span>
          </div>
        </div>

        {/* Pipeline Architecture Preview */}
        {pipelineSteps && (
          <div className="mt-8 pt-6 border-t border-slate-800/80">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              Planned AI Pipeline Architecture
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
              {pipelineSteps.map((step, idx) => (
                <div key={idx} className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
                  <div className="w-6 h-6 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center text-xs font-bold mb-2">
                    {idx + 1}
                  </div>
                  <h4 className="text-xs font-semibold text-slate-200">{step.title}</h4>
                  <p className="text-[11px] text-slate-400 mt-1 leading-normal">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
